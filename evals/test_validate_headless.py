from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ValidateHeadlessTests(unittest.TestCase):
    def test_require_absent_rejects_real_dashboard_tree(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_headless.py", "--require-dashboard-absent"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dashboard directory is present", result.stdout)

    def test_dashboard_absent_clean_copy_passes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="researchos-public-headless-") as temp_dir:
            copied_root = Path(temp_dir) / "researchos-public-starter"
            shutil.copytree(
                ROOT,
                copied_root,
                ignore=shutil.ignore_patterns(
                    ".git",
                    "dashboard",
                    "personal_vault",
                    "__pycache__",
                    "*.pyc",
                ),
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_headless.py",
                    "--require-dashboard-absent",
                ],
                cwd=copied_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("public zero-dashboard profile validated", result.stdout)


if __name__ == "__main__":
    unittest.main()
