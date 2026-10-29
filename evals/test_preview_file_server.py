from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_server.preview_file_server import PreviewFileServer  # noqa: E402
from researchos_server.runtime_read_boundary import RuntimeReadBoundary  # noqa: E402


class PreviewFileServerTest(unittest.TestCase):
    @staticmethod
    def write_public_manifest(root: Path, files: list[str]) -> None:
        manifest = root / "config" / "public-runtime-read-manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({
            "schema_id": "researchos-public-runtime-read-manifest-v1",
            "version": "fixture",
            "files": files,
        }), encoding="utf-8")

    def test_preview_paths_stay_inside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            root = base / "repo"
            root.mkdir()
            (root / "inside.md").write_text("inside", encoding="utf-8")
            (root / "corpus").mkdir()
            (root / "corpus" / "private.md").write_text("private", encoding="utf-8")
            outside = base / "outside.md"
            outside.write_text("outside", encoding="utf-8")
            (root / "escape.md").symlink_to(outside)
            self.write_public_manifest(root, ["08_exports/public_starter/inside.md"])
            server = PreviewFileServer(root=root, read_boundary=RuntimeReadBoundary.public_starter(root))

            self.assertIsNone(server.markdown_target("inside.md"))
            self.assertIsNone(server.resolve_markdown_path("../outside.md"))
            self.assertIsNone(server.resolve_markdown_path(str(outside)))
            self.assertIsNone(server.resolve_markdown_path("escape.md"))
            self.assertIsNone(server.resolve_markdown_path("corpus/private.md"))

            (root / "08_exports" / "public_starter").mkdir(parents=True)
            public_note = root / "08_exports" / "public_starter" / "inside.md"
            public_note.write_text("public", encoding="utf-8")
            self.assertEqual(public_note.resolve(), server.markdown_target("08_exports/public_starter/inside.md"))

    def test_pdf_paths_reject_traversal_and_wrong_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "inside.pdf").write_bytes(b"%PDF-test")
            (root / "APPENDIX.PDF").write_bytes(b"%PDF-test")
            (root / "corpus").mkdir()
            (root / "corpus" / "private.pdf").write_bytes(b"%PDF-private")
            self.write_public_manifest(root, ["08_exports/public_starter/inside.pdf"])
            server = PreviewFileServer(root=root, read_boundary=RuntimeReadBoundary.public_starter(root))

            self.assertIsNone(server.pdf_target("inside.pdf"))
            self.assertIsNone(server.pdf_target("APPENDIX.PDF"))
            self.assertIsNone(server.resolve_pdf_path("corpus/private.pdf"))
            self.assertIsNone(server.resolve_pdf_path("../outside.pdf"))
            self.assertIsNone(server.resolve_pdf_path("inside.md"))

            (root / "08_exports" / "public_starter").mkdir(parents=True)
            public_pdf = root / "08_exports" / "public_starter" / "inside.pdf"
            public_pdf.write_bytes(b"%PDF-public")
            self.assertEqual(public_pdf.resolve(), server.pdf_target("08_exports/public_starter/inside.pdf"))


if __name__ == "__main__":
    unittest.main()
