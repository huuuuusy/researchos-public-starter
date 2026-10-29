from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_server.local_file_bridge import LocalFileBridge  # noqa: E402
from researchos_server.source_tree_store import SourceTreeStore  # noqa: E402


class _Result:
    returncode = 0
    stderr = ""


class LocalFileBridgeTest(unittest.TestCase):
    def bridge(self, root: Path) -> LocalFileBridge:
        return LocalFileBridge(root=root, source_tree=SourceTreeStore(root))

    def test_macos_reveal_uses_finder_reveal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "note.md").write_text("test", encoding="utf-8")
            with patch("platform.system", return_value="Darwin"), patch("subprocess.run", return_value=_Result()) as run:
                result = self.bridge(root).reveal_file("note.md")
            self.assertTrue(result["ok"])
            self.assertEqual(run.call_args.args[0], ["open", "-R", str((root / "note.md").resolve())])

    def test_linux_without_opener_returns_structured_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "note.md").write_text("test", encoding="utf-8")
            with patch("platform.system", return_value="Linux"), patch("shutil.which", return_value=None):
                result = self.bridge(root).open_file("note.md")
            self.assertFalse(result["ok"])
            self.assertEqual(result["error_type"], "unsupported_platform")

    def test_scripts_are_revealed_but_never_opened(self) -> None:
        # Opening hands a file to its default app; for a script that can mean running it.
        from researchos_server.source_tree_store import SourceTreeError

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "tool.py").write_text("print('x')", encoding="utf-8")
            with patch("platform.system", return_value="Darwin"), patch("subprocess.run", return_value=_Result()) as run:
                with self.assertRaises(SourceTreeError):
                    self.bridge(root).open_file("tool.py")
                run.assert_not_called()
                self.assertTrue(self.bridge(root).reveal_file("tool.py")["ok"])
            self.assertEqual(run.call_args.args[0], ["open", "-R", str((root / "tool.py").resolve())])

    def test_windows_open_uses_startfile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "note.md").write_text("test", encoding="utf-8")
            with patch("platform.system", return_value="Windows"), patch("os.startfile", create=True) as startfile:
                result = self.bridge(root).open_file("note.md")
            self.assertTrue(result["ok"])
            startfile.assert_called_once_with(str((root / "note.md").resolve()))


if __name__ == "__main__":
    unittest.main()
