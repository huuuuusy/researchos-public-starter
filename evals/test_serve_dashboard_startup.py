"""Public dashboard server startup: only the two known projections are served (a typo must not switch the
server into the writable personal-vault mode), and a plain `kill` removes the temporary read copy."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "scripts" / "serve_dashboard.py"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ServeDashboardStartupTest(unittest.TestCase):
    def command(self, *args: str) -> list[str]:
        return [sys.executable, str(SERVER), "--port", str(free_port()), *args]

    def test_unknown_or_missing_data_file_refuses_to_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TMPDIR": tmp}
            typo = subprocess.run(self.command("--data-file", "dashboard/data/researchos-locl.json"),
                                  capture_output=True, text=True, timeout=60, env=env)
            self.assertNotEqual(typo.returncode, 0)
            self.assertIn("--data-file must be", typo.stderr)
            if not (ROOT / "dashboard" / "data" / "researchos-local.json").exists():
                missing = subprocess.run(self.command("--data-file", "dashboard/data/researchos-local.json"),
                                         capture_output=True, text=True, timeout=60, env=env)
                self.assertNotEqual(missing.returncode, 0)
                self.assertIn("does not exist", missing.stderr)
            self.assertEqual(list(Path(tmp).glob("researchos-public-read-*")), [])

    def test_sigterm_removes_the_temporary_read_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            port = free_port()
            server = subprocess.Popen([sys.executable, str(SERVER), "--port", str(port)], env={**os.environ, "TMPDIR": tmp},
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    with socket.socket() as sock:
                        if sock.connect_ex(("127.0.0.1", port)) == 0:
                            break
                    time.sleep(0.2)
                else:
                    self.fail("server did not start")
                self.assertTrue(list(Path(tmp).glob("researchos-public-read-*")))
                server.send_signal(signal.SIGTERM)
                server.wait(timeout=30)
            finally:
                if server.poll() is None:
                    server.kill()
            self.assertEqual(list(Path(tmp).glob("researchos-public-read-*")), [])


if __name__ == "__main__":
    unittest.main()
