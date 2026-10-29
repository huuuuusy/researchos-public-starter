from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters.command_runner import CommandRunner, codex_cli_env  # noqa: E402


class CommandRunnerSecurityTest(unittest.TestCase):
    def test_codex_environment_keeps_runtime_basics_and_drops_credentials(self) -> None:
        fixture_root = Path("runtime-fixture").resolve()
        env = codex_cli_env({
            "PATH": "/bin",
            "HOME": str(fixture_root),
            "CODEX_HOME": str(fixture_root / ".codex"),
            "TMPDIR": str(fixture_root / "tmp"),
            "LANG": "en_US.UTF-8",
            "LC_ALL": "en_US.UTF-8",
            "TZ": "UTC",
            "SSL_CERT_FILE": str(fixture_root / "cert.pem"),
            "OPENAI_API_KEY": "secret",
            "ANTHROPIC_TOKEN": "secret",
            "AWS_SECRET_ACCESS_KEY": "secret",
            "SSH_AUTH_SOCK": str(fixture_root / "ssh.sock"),
            "HTTPS_PROXY": "http://proxy",
        })
        self.assertEqual(env["PATH"], "/bin")
        self.assertEqual(env["CODEX_HOME"], str(fixture_root / ".codex"))
        self.assertEqual(env["LC_ALL"], "en_US.UTF-8")
        for blocked in ("OPENAI_API_KEY", "ANTHROPIC_TOKEN", "AWS_SECRET_ACCESS_KEY", "SSH_AUTH_SOCK", "HTTPS_PROXY"):
            self.assertNotIn(blocked, env)

    def test_command_runner_passes_explicit_environment_and_defaults_to_inheritance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = CommandRunner(root=Path(directory))
            completed = type("Completed", (), {"returncode": 0, "stdout": "ok"})()
            with patch("researchos_adapters.command_runner.subprocess.run", return_value=completed) as subprocess_run:
                runner.run(["tool"], env={"PATH": "/bin"})
                self.assertEqual(subprocess_run.call_args.kwargs["env"], {"PATH": "/bin"})
                runner.run(["tool"])
                self.assertIsNone(subprocess_run.call_args.kwargs["env"])


if __name__ == "__main__":
    unittest.main()
