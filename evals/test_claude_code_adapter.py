# ResearchOS maintenance header.
# 中文：Claude Code CLI 本地参考适配器的边界测试：无工具、无用户设置、不转发 API key、公开版拒绝、未登录与缺失 CLI 作为明确失败。
# English: Boundary tests for the local Claude Code CLI adapter: no tools, no user settings, no forwarded API key, public refusal, and not-logged-in or missing CLI as explicit failures.

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

from researchos_adapters.claude_code_adapter import (  # noqa: E402
    ClaudeCodeExtension,
    ClaudeCodeProviderAdapter,
    answer_from_claude_output,
    isolated_claude_config,
    resolve_claude_executable,
)
from researchos_adapters.provider_adapter import (  # noqa: E402
    ExecutionRequest,
    ProviderAdapterError,
    claude_code_adapter,
    provider_adapter_status,
)
from researchos_adapters.provider_config import load_runtime_config, provider_status  # noqa: E402
from researchos_adapters.runtime_profile import project_runtime_profile, runtime_profiles_from_config  # noqa: E402


def result_json(text: str, *, is_error: bool = False) -> str:
    return json.dumps({"type": "result", "subtype": "success", "is_error": is_error, "result": text,
                       "session_id": "fixture", "total_cost_usd": 0, "num_turns": 1})


class CapturingCommandRunner:
    def __init__(self, result: dict[str, object] | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self.result = result or {"ok": True, "returncode": 0, "seconds": 0.3, "stdout": result_json("Draft answer")}

    def run(self, args, *, timeout, input_text, env=None):
        self.calls.append({"args": list(args), "timeout": timeout, "input_text": input_text, "env": dict(env or {})})
        return dict(self.result)


class ClaudeCodeAdapterTest(unittest.TestCase):
    def dispatch(self, root: Path, **overrides) -> ExecutionRequest:
        fields = dict(prompt="Draft at most one judgment.", timeout=42, model="claude-fixture", run_id="run-1",
                      extension=ClaudeCodeExtension(cwd=root / "workspace", config_dir=root / "config", effort="medium"))
        fields.update(overrides)
        return ExecutionRequest(**fields)

    def test_dispatch_is_bare_toolless_and_credential_free(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "claude"
            executable.write_text("fixture", encoding="utf-8")
            executable.chmod(0o700)
            command = CapturingCommandRunner()
            adapter = ClaudeCodeProviderAdapter(root, command, "private", command=str(executable))
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "secret", "CODEX_HOME": "/elsewhere", "PATH": "/usr/bin"}, clear=False):
                result = adapter.execute(self.dispatch(root))
        self.assertTrue(result.ok)
        self.assertEqual("claude_code", result.provider)
        self.assertEqual("Draft answer", result.stdout, "only the final answer enters the candidate path")
        call = command.calls[0]
        args = call["args"]
        self.assertEqual(str(executable), args[0])
        for flag in ("--print", "--restricted", "--disable-slash-commands", "--strict-mcp-config",
                     "--no-session-persistence"):
            self.assertIn(flag, args)
        self.assertNotIn("--bare", args, "--bare accepts only an API key and never reads a subscription login")
        self.assertEqual("", args[args.index("--tools") + 1], "no tools: the context pack is already in the prompt")
        self.assertEqual("json", args[args.index("--output-format") + 1])
        self.assertEqual("medium", args[args.index("--effort") + 1])
        self.assertEqual("claude-fixture", args[args.index("--model") + 1])
        self.assertEqual("Draft at most one judgment.", call["input_text"], "the prompt goes through stdin")
        self.assertEqual(str(root / "config"), call["env"]["CLAUDE_CONFIG_DIR"])
        self.assertNotIn("ANTHROPIC_API_KEY", call["env"])
        self.assertNotIn("CODEX_HOME", call["env"])
        self.assertEqual(42, call["timeout"])

    def test_shared_config_leaves_the_config_dir_unset_and_forwards_the_user_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "claude"
            executable.write_text("fixture", encoding="utf-8")
            executable.chmod(0o700)
            command = CapturingCommandRunner()
            adapter = ClaudeCodeProviderAdapter(root, command, "private", command=str(executable))
            shared = ClaudeCodeExtension(cwd=root / "workspace", config_dir=None)
            with patch.dict(os.environ, {"USER": "researcher", "CLAUDE_CONFIG_DIR": "/elsewhere"}, clear=False):
                self.assertTrue(adapter.execute(self.dispatch(root, extension=shared)).ok)
        env = command.calls[0]["env"]
        self.assertNotIn("CLAUDE_CONFIG_DIR", env, "setting it, even to the default, hides a keychain login")
        self.assertEqual("researcher", env["USER"], "the keychain login is looked up by user name")

    def test_not_logged_in_and_missing_cli_are_explicit_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "claude"
            executable.write_text("fixture", encoding="utf-8")
            executable.chmod(0o700)
            command = CapturingCommandRunner({"ok": True, "returncode": 0, "seconds": 0.1,
                                              "stdout": result_json("Not logged in · Please run /login", is_error=True)})
            adapter = ClaudeCodeProviderAdapter(root, command, "private", command=str(executable))
            result = adapter.execute(self.dispatch(root))
            self.assertFalse(result.ok)
            self.assertEqual("claude_code_not_logged_in", result.error_type)
            missing = ClaudeCodeProviderAdapter(root, CapturingCommandRunner(), "private", command=str(root / "absent"))
            with patch("researchos_adapters.claude_code_adapter.shutil.which", return_value=None), \
                    patch("researchos_adapters.claude_code_adapter.Path.home", return_value=root):
                result = missing.execute(self.dispatch(root))
        self.assertFalse(result.ok)
        self.assertEqual("claude_code_cli_missing", result.error_type)

    def test_public_scope_and_invalid_dispatch_fail_closed_without_a_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = CapturingCommandRunner()
            public = ClaudeCodeProviderAdapter(root, command, "public_starter")
            with self.assertRaises(ProviderAdapterError) as refused:
                public.execute(self.dispatch(root))
            self.assertEqual("public_starter_copy_only", refused.exception.code)
            status = public.status()
            self.assertEqual("none", status["adapter_family"])
            executable = root / "claude"
            executable.write_text("fixture", encoding="utf-8")
            executable.chmod(0o700)
            private = ClaudeCodeProviderAdapter(root, command, "private", command=str(executable))
            with self.assertRaises(ProviderAdapterError):
                private.execute(self.dispatch(root, extension=None))
            with self.assertRaises(ProviderAdapterError) as effort:
                private.execute(self.dispatch(root, extension=ClaudeCodeExtension(root / "w", root / "c", effort="ultra-high")))
            self.assertEqual("unsupported_reasoning_effort", effort.exception.code)
        self.assertEqual([], command.calls)

    def test_output_parser_keeps_only_the_result_field(self) -> None:
        self.assertEqual(("Final", ""), answer_from_claude_output(result_json("Final")))
        self.assertEqual(("", "runner_output_unparseable"), answer_from_claude_output("plain text, no json"))
        mixed = "tool noise\n" + result_json("Last")
        self.assertEqual(("Last", ""), answer_from_claude_output(mixed))
        failed = answer_from_claude_output(result_json("Some API failure", is_error=True))
        self.assertEqual("runner_execution_failed", failed[1])

    def test_executable_resolution_prefers_configured_then_path_then_desktop_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            bundle = home / "Library/Application Support/Claude/claude-code"
            for version in ("2.1.293", "2.1.295", "2.1.9"):
                target = bundle / version / "abc" / "claude.app/Contents/MacOS"
                target.mkdir(parents=True)
                (target / "claude").write_text("fixture", encoding="utf-8")
                (target / "claude").chmod(0o700)
            with patch("researchos_adapters.claude_code_adapter.shutil.which", return_value=None), \
                    patch("researchos_adapters.claude_code_adapter.Path.home", return_value=home):
                resolved = resolve_claude_executable(None)
                self.assertIn("2.1.295", str(resolved), "the newest bundled CLI wins")
                configured = home / "custom-claude"
                configured.write_text("fixture", encoding="utf-8")
                configured.chmod(0o700)
                self.assertEqual(configured, resolve_claude_executable(str(configured)))
                self.assertIsNone(resolve_claude_executable(str(home / "missing")))

    def test_isolated_config_directory_links_only_a_file_login(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "dot-claude"
            source.mkdir()
            (source / "settings.json").write_text("{}", encoding="utf-8")
            (source / "CLAUDE.md").write_text("user memory", encoding="utf-8")
            (source / ".credentials.json").write_text("{}", encoding="utf-8")
            with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(source)}), isolated_claude_config() as isolated:
                self.assertNotEqual(source, isolated)
                self.assertEqual({".credentials.json"}, {p.name for p in isolated.iterdir()})
                self.assertTrue((isolated / ".credentials.json").is_symlink())

    def test_registry_status_and_profile_treat_claude_code_as_an_answer_only_local_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("researchos_adapters.claude_code_adapter.shutil.which", return_value=None), \
                    patch("researchos_adapters.claude_code_adapter.Path.home", return_value=root):
                status = provider_adapter_status("claude_code", root=root, command_runner=CapturingCommandRunner(),
                                                 runtime_scope="private")
        self.assertEqual("local_claude_code", status["adapter_family"])
        self.assertEqual("claude_code_cli_missing", status["error_type"])
        self.assertEqual(claude_code_adapter("claude_code", root=root, command_runner=CapturingCommandRunner(),
                                             runtime_scope="private").status()["selected_adapter"], "cli_print")
        self.assertTrue(provider_status("claude_code")["ok"])
        profiles = runtime_profiles_from_config(load_runtime_config(include_local=False))
        profile = profiles["claude_code"]
        self.assertEqual("local_claude_code", profile["adapter_family"])
        self.assertEqual(("answer",), tuple(profile["capabilities"]["result_modes"]))
        self.assertEqual("local_unmetered", profile["cost_policy"]["mode"])
        projection = project_runtime_profile({**profile, "enabled": True}, runtime_scope="private", execution_available=False)
        self.assertEqual("answer_only", projection["execution_scope"])
        self.assertEqual("local_probe_failed", projection["verification_state"])
        public = provider_adapter_status("claude_code", root=Path("."), command_runner=CapturingCommandRunner(),
                                         runtime_scope="public_starter")
        self.assertEqual("public_starter_copy_only", public["error_type"])


if __name__ == "__main__":
    unittest.main()
