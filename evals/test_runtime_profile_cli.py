from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/runtime_profile_cli.py"
sys.path.insert(0, str(ROOT / "scripts"))
from researchos_adapters import provider_config  # noqa: E402
import runtime_profile_cli  # noqa: E402


class RuntimeProfileCliTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, text=True, capture_output=True)

    def test_list_validate_and_show_are_serverless_and_redacted(self) -> None:
        for args in (("validate",), ("list",), ("show", "--profile", "claude_code")):
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("credential_ref", result.stdout)
            self.assertNotIn("endpoint_ref", result.stdout)
        self.assertEqual(json.loads(self.run_cli("validate").stdout)["network"], "not_used")

    def test_public_is_copy_only_and_cannot_select_or_resolve(self) -> None:
        listing = json.loads(self.run_cli("list", "--scope", "public_starter").stdout)
        self.assertEqual(len(listing["profiles"]), 1)
        self.assertTrue(all(item["status"] == "copy_only" for item in listing["profiles"]))
        result = self.run_cli("select", "--profile", "codex", "--scope", "public_starter", "--write")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["error_type"], "public_starter_copy_only")

    def test_resolve_validates_model_and_reasoning_without_dispatch(self) -> None:
        ok = self.run_cli("resolve", "--profile", "codex", "--model", "auto", "--reasoning", "auto")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["dispatch"], "not_started")
        bad = self.run_cli("resolve", "--profile", "codex", "--reasoning", "root")
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(json.loads(bad.stdout)["error_type"], "runtime_profile_reasoning_not_allowed")

    def test_select_defaults_to_dry_run_and_atomic_write_is_private_mode(self) -> None:
        dry = self.run_cli("select", "--profile", "codex")
        self.assertEqual(dry.returncode, 0)
        self.assertFalse(json.loads(dry.stdout)["write"])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "researchos.runtime.local.json"
            with patch.object(runtime_profile_cli, "LOCAL_CONFIG", target), patch.object(
                provider_config, "LOCAL_CONFIG", target
            ), redirect_stdout(StringIO()):
                self.assertEqual(runtime_profile_cli.main(["select", "--profile", "codex", "--write"]), 0)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(target.read_text())["default_runtime_profile"], "codex")

    def test_write_rejects_symlink_target_without_overwriting_victim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            victim = root / "victim.json"; victim.write_text('{"safe": true}\n')
            target = root / "researchos.runtime.local.json"; target.symlink_to(victim)
            with patch.object(runtime_profile_cli, "LOCAL_CONFIG", target), patch.object(
                provider_config, "LOCAL_CONFIG", target
            ), redirect_stdout(StringIO()):
                self.assertEqual(runtime_profile_cli.main(["select", "--profile", "codex", "--write"]), 2)
            self.assertEqual(victim.read_text(), '{"safe": true}\n')


if __name__ == "__main__":
    unittest.main()
