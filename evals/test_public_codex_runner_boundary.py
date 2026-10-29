from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_server.codex_runner import CodexRunner  # noqa: E402
from researchos_adapters.command_runner import CommandRunner  # noqa: E402
from researchos_adapters.provider_config import provider_status, public_provider_status  # noqa: E402


class CapturingCommandRunner:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.calls: list[dict[str, object]] = []

    def run(self, args: list[str], timeout: int = 90, input_text: str | None = None, env=None) -> dict[str, object]:
        self.calls.append({"args": list(args), "timeout": timeout, "input_text": input_text, "env": env})
        return {"ok": True, "returncode": 0, "seconds": 0, "stdout": "", "output": ""}


class PublicCodexRunnerBoundaryTest(unittest.TestCase):
    def make_runner(self, root: Path, command_runner: object | None = None, codex_path: Path | None = None) -> CodexRunner:
        return CodexRunner(
            root=root,
            command_runner=command_runner or CommandRunner(root=root),
            log_jsonl=root / "runner.jsonl",
            log_md=root / "runner.md",
            codex_path=codex_path or (root / "codex"),
            public_starter=True,
            runtime_scope="public_starter",
        )

    def test_public_submission_rejects_inbox_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = self.make_runner(Path(directory))
            result = runner.submit({
                "prompt": "Apply inbox changes",
                "task_mode": "direct_execution",
                "entries": [{"type": "writeback", "actionId": "candidate-1"}],
            })
        self.assertFalse(result["ok"])
        self.assertEqual("public_starter_copy_only", result["error_type"])

    def test_public_unknown_provider_fails_before_internal_lookups(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = self.make_runner(root)
            with patch.object(CodexRunner, "direct_execution_registry") as authority, patch.object(
                CodexRunner, "codex_executable"
            ) as executable, patch.object(CodexRunner, "append_event") as append_event, patch(
                "researchos_server.codex_runner.threading.Thread"
            ) as thread, patch("researchos_adapters.provider_config.get_provider_spec") as provider_lookup, patch(
                "researchos_server.codex_runner.normalize_task_intent_result"
            ) as task_intent:
                result = runner.submit({
                    "provider": "not-registered",
                    "prompt": "Do not inspect the registry.",
                    "task_mode": "direct_execution",
                })
                status = provider_status("not-registered", public_starter=True)

        for failure in (result, status):
            self.assertFalse(failure["ok"])
            self.assertEqual("public_starter_copy_only", failure["error_type"])
        provider_lookup.assert_not_called()
        task_intent.assert_not_called()
        authority.assert_not_called()
        executable.assert_not_called()
        append_event.assert_not_called()
        thread.assert_not_called()

    def test_private_unknown_provider_status_is_structured(self) -> None:
        status = provider_status("not-registered", public_starter=False)

        self.assertFalse(status["ok"])
        self.assertEqual("unknown_provider", status["error_type"])
        self.assertEqual("not-registered", status["provider"])
        self.assertFalse(status["execution_available"])
        self.assertEqual("none", status["execution_scope"])

    def test_public_submission_rejects_artifact_requests_without_starting_thread(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_path = root / "codex"
            codex_path.write_text("", encoding="utf-8")
            runner = self.make_runner(root, codex_path=codex_path)
            model_config = {
                "task_complexity": "standard",
                "model": "auto",
                "model_mode": "auto_catalog",
                "reasoning_effort": "medium",
            }
            with patch.object(CodexRunner, "model_config", return_value=model_config) as model_config_call, patch.object(
                CodexRunner, "append_event"
            ) as append_event, patch("researchos_server.codex_runner.threading.Thread") as thread:
                result = runner.submit({
                    "prompt": "Create an artifact",
                    "response_mode": "artifact",
                    "task_mode": "direct_execution",
                })
        self.assertFalse(result["ok"])
        self.assertEqual("public_starter_copy_only", result["error_type"])
        model_config_call.assert_not_called()
        append_event.assert_not_called()
        thread.assert_not_called()

    def test_public_submission_never_invokes_command_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_path = root / "codex"
            codex_path.write_text("", encoding="utf-8")
            command_runner = CapturingCommandRunner(root)
            runner = self.make_runner(root, command_runner=command_runner, codex_path=codex_path)
            with patch.object(CodexRunner, "append_event") as append_event, patch(
                "researchos_server.codex_runner.threading.Thread"
            ) as thread:
                result = runner.submit({
                    "id": "crafted",
                    "task_mode": "direct_execution",
                    "response_mode": "artifact",
                    "prompt": "Try to write",
                    "reasoning_effort": "low",
                })
        self.assertFalse(result["ok"])
        self.assertEqual("public_starter_copy_only", result["error_type"])
        self.assertEqual([], command_runner.calls)
        append_event.assert_not_called()
        thread.assert_not_called()

    def test_public_internal_run_fails_before_permission_profile_or_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_path = root / "codex"
            codex_path.write_text("", encoding="utf-8")
            command_runner = CapturingCommandRunner(root)
            runner = self.make_runner(root, command_runner=command_runner, codex_path=codex_path)
            with patch.object(CodexRunner, "append_event") as append_event, patch(
                "researchos_server.codex_runner.runner_launch_permissions"
            ) as permission_profile, patch.object(CodexRunner, "codex_executable") as executable:
                result = runner.run_codex({"id": "internal-crafted", "prompt": "run"})
        self.assertEqual("failed", result["status"])
        self.assertEqual("public_starter_copy_only", result["error_type"])
        permission_profile.assert_not_called()
        executable.assert_not_called()
        self.assertEqual([], command_runner.calls)
        append_event.assert_called_once()

    def test_public_provider_status_and_missing_cli_fail_closed(self) -> None:
        remote = provider_status("claude_code", public_starter=True)
        self.assertFalse(remote["ok"])
        self.assertEqual("public_starter_copy_only", remote["error_type"])
        self.assertNotIn("key_status", remote)
        self.assertNotIn("api_key_env", remote)
        self.assertNotIn("fix_zh", remote)
        self.assertNotIn("fix_en", remote)
        projected = public_provider_status({
            **remote,
            "key_status": "configured",
            "api_key_env": "OPENAI_API_KEY",
            "fix_en": "Set OPENAI_API_KEY",
        })
        self.assertNotIn("key_status", projected)
        self.assertNotIn("api_key_env", projected)
        self.assertNotIn("fix_en", projected)
        private_projection = public_provider_status(
            {"key_status": "configured", "fix_en": "Private setup guidance"},
            public_starter=False,
        )
        self.assertEqual("configured", private_projection["key_status"])
        self.assertNotIn("fix_en", private_projection)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = self.make_runner(root, codex_path=root / "missing-codex")
            with patch("researchos_adapters.provider_adapter.resolve_codex_executable") as executable:
                status = runner.executor_provider_status("codex")
        executable.assert_not_called()
        self.assertFalse(status["execution_available"])
        self.assertEqual("public_starter_copy_only", status["error_type"])
        self.assertEqual("copy_only", status["runtime_profile"]["status"])
        self.assertEqual("candidate_off", status["runtime_profile"]["selector_state"])
        serialized = json.dumps(status, sort_keys=True)
        for forbidden in ("endpoint_ref", "credential_ref", "api_key_env", "budget_ref", "source_ref"):
            self.assertNotIn(forbidden, serialized)

    def test_public_provider_status_never_loads_local_runtime_config(self) -> None:
        config = {
            "default_provider": "codex",
            "providers": {"codex": {"default_model": "auto"}},
            "public_starter": {"allow_local_codex": False, "allow_real_api": False},
        }
        with patch("researchos_adapters.provider_config.load_runtime_config", return_value=config) as loader:
            status = provider_status("codex", public_starter=True)
        loader.assert_called_once_with(include_local=False)
        self.assertFalse(status["ok"])
        self.assertEqual("public_starter_copy_only", status["error_type"])
        self.assertNotIn("api_key_env", status)
        self.assertNotIn("key_status", status)

    def test_public_result_hides_workstation_absolute_paths(self) -> None:
        user_prefix = str(Path("/") / "Users" / "example")
        root = Path(user_prefix) / "researchos-public-starter"
        runner = self.make_runner(root)
        raw_output = json.dumps({
            "type": "item.completed",
            "item": {"type": "agent_message", "text": f"See {root}/docs/example.md"},
        })
        result = runner.public_run({
            "id": "public-path",
            "status": "completed",
            "output": raw_output,
            "message": f"Log: {user_prefix}/Library/secret.log",
            "candidate": {"summary": f"private at {user_prefix}/private.md"},
            "artifacts": [f"{root}/docs/example.md"],
            "changed_files": [f"{root}/docs/example.md"],
            "preview_anchors": [f"{root}/docs/example.md#heading"],
            "change_summary": [f"changed {root}/docs/example.md"],
            "task_envelope": {
                "schema_id": "researchos-task-envelope-v1",
                "idempotency_key": "idem:private",
                "runtime_ref": {"scope": "private"},
            },
        })

        self.assertNotIn(user_prefix, result["answer"])
        self.assertNotIn(user_prefix, result["message"])
        self.assertIn("./docs/example.md", result["answer"])
        for private_key in ("output", "candidate", "authority_policy", "policy_decision", "authorization_grant", "policy_decision_ref", "authorization_grant_ref", "artifacts", "changed_files", "preview_anchors", "change_summary", "task_envelope", "task_envelope_ref"):
            self.assertNotIn(private_key, result)


if __name__ == "__main__":
    unittest.main()
