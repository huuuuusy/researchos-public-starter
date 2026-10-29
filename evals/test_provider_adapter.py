from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters.provider_adapter import (  # noqa: E402
    CodexProviderAdapter,
    ProviderAdapterError,
    ProviderCancellation,
    ProviderDispatch,
    codex_adapter,
    provider_adapter_status,
)


class CapturingCommandRunner:
    def __init__(self, result: dict[str, object] | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self.result = result or {"ok": True, "returncode": 0, "seconds": 0.25, "stdout": "done"}

    def run(self, args, *, timeout, input_text, env=None):
        self.calls.append({"args": args, "timeout": timeout, "input_text": input_text, "env": env})
        return dict(self.result)


class ProviderAdapterTest(unittest.TestCase):
    CONFIG_ARGS = (
        "--disable", "memories", "-c", 'default_permissions="researchos-runner-v1"',
        "-c", 'permissions.researchos-runner-v1={network={enabled=false}}',
    )

    def test_codex_adapter_builds_ephemeral_credential_free_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "codex"
            executable.write_text("fixture", encoding="utf-8")
            command = CapturingCommandRunner()
            adapter = CodexProviderAdapter(root, command, "private", codex_path=executable)
            dispatch = ProviderDispatch(
                cwd=root / "outputs", config_args=self.CONFIG_ARGS,
                codex_home=root / "isolated-home", model="gpt-test", reasoning_effort="medium",
                prompt="Do one bounded task", timeout=42,
            )
            with patch.dict(os.environ, {"OPENAI_API_KEY": "secret", "PATH": "/usr/bin"}, clear=False):
                result = adapter.execute(dispatch)
        self.assertTrue(result.ok)
        self.assertEqual("codex", result.provider)
        call = command.calls[0]
        self.assertEqual(42, call["timeout"])
        self.assertEqual("Do one bounded task", call["input_text"])
        self.assertIn("--ignore-user-config", call["args"])
        self.assertIn("--strict-config", call["args"])
        self.assertIn("gpt-test", call["args"])
        self.assertEqual(str(dispatch.extension.codex_home), call["env"]["CODEX_HOME"])
        self.assertNotIn("OPENAI_API_KEY", call["env"])
        self.assertNotIn("authorization_grant", json.dumps(result.to_dict()))
        self.assertNotIn("authority", json.dumps(result.to_dict()))

    def test_execution_result_is_bounded_and_drops_unknown_runner_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "codex"
            executable.write_text("fixture", encoding="utf-8")
            adapter = CodexProviderAdapter(
                root, CapturingCommandRunner({
                    "ok": False, "returncode": 9, "seconds": 1, "stdout": "abcdef",
                    "secret": "provider diagnostic",
                }), "private", codex_path=executable, output_limit=4,
            )
            result = adapter.execute(ProviderDispatch(root, self.CONFIG_ARGS, root / "home", "auto", "low", "task", 30))
        self.assertEqual("cdef", result.stdout)
        self.assertEqual("runner_execution_failed", result.error_type)
        self.assertNotIn("secret", result.to_dict())

    def test_public_unknown_and_invalid_profiles_fail_closed_without_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = CapturingCommandRunner()
            public = CodexProviderAdapter(root, command, "public_starter")
            with self.assertRaisesRegex(ProviderAdapterError, "public_starter_copy_only"):
                public.execute(ProviderDispatch(root, self.CONFIG_ARGS, root / "home", "auto", "low", "task", 30))
            with self.assertRaisesRegex(ProviderAdapterError, "provider_call_not_implemented"):
                codex_adapter("not-registered", root=root, command_runner=command, runtime_scope="private")
            executable = root / "codex"
            executable.write_text("fixture", encoding="utf-8")
            private = CodexProviderAdapter(root, command, "private", codex_path=executable)
            with self.assertRaisesRegex(ProviderAdapterError, "unsupported_reasoning_effort"):
                private.execute(ProviderDispatch(root, self.CONFIG_ARGS, root / "home", "auto", "root", "task", 30))
            with self.assertRaisesRegex(ProviderAdapterError, "provider_dispatch_invalid"):
                private.execute(ProviderDispatch(
                    root, ("--dangerously-bypass-approvals-and-sandbox",), root / "home",
                    "auto", "low", "task", 30,
                ))
        self.assertEqual([], command.calls)

    def test_status_keeps_non_codex_providers_status_only_and_public_copy_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = CapturingCommandRunner()
            with patch("researchos_adapters.provider_adapter.provider_execution_status") as status:
                status.return_value = {"ok": False, "error_type": "provider_call_not_implemented"}
                other = provider_adapter_status(
                    "not-registered", root=root, command_runner=command, runtime_scope="private"
                )
                status.assert_called_once_with(
                    "not-registered", public_starter=False, executable_available=False, runtime_scope="private"
                )
            public = provider_adapter_status(
                "codex", root=root, command_runner=command, runtime_scope="public_starter"
            )
        self.assertEqual("provider_call_not_implemented", other["error_type"])
        self.assertEqual("public_starter_copy_only", public["error_type"])
        self.assertEqual("none", public["adapter_family"])
        self.assertEqual("unsupported", public["cancel"])
        self.assertEqual([], command.calls)

    def test_local_status_and_cancel_are_explicit_without_command_or_server(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "codex"
            executable.write_text("fixture", encoding="utf-8")
            command = CapturingCommandRunner()
            adapter = CodexProviderAdapter(root, command, "private", codex_path=executable)
            status = adapter.status()
            cancellation = adapter.cancel("run:local-one")
        self.assertTrue(status["execution_available"])
        self.assertEqual("local_codex", status["adapter_family"])
        self.assertEqual("unsupported", status["cancel"])
        self.assertEqual("local_probe_passed", status["runtime_profile"]["verification_state"])
        self.assertEqual("candidate_off", status["runtime_profile"]["selector_state"])
        serialized = json.dumps(status["runtime_profile"], sort_keys=True)
        for forbidden in ("endpoint_ref", "credential_ref", "api_key_env", "budget_ref"):
            self.assertNotIn(forbidden, serialized)
        self.assertIsInstance(cancellation, ProviderCancellation)
        self.assertEqual({
            "provider": "codex", "accepted": False, "status": "unsupported",
            "error_type": "provider_cancel_unsupported",
        }, cancellation.to_dict())
        self.assertEqual([], command.calls)

    def test_public_cancel_and_invalid_run_reference_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = CapturingCommandRunner()
            with self.assertRaisesRegex(ProviderAdapterError, "public_starter_copy_only"):
                CodexProviderAdapter(root, command, "public_starter").cancel("run:one")
            executable = root / "codex"
            executable.write_text("fixture", encoding="utf-8")
            adapter = CodexProviderAdapter(root, command, "private", codex_path=executable)
            with self.assertRaisesRegex(ProviderAdapterError, "provider_dispatch_invalid"):
                adapter.cancel("")
        self.assertEqual([], command.calls)


if __name__ == "__main__":
    unittest.main()
