import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_server.work_session_upload import (  # noqa: E402
    WorkSessionUploadError,
    WorkSessionUploadStore,
    upload_request_metadata,
)


class WorkSessionUploadStoreTest(unittest.TestCase):
    def test_binary_request_metadata_decodes_filename_without_a_size_quota(self) -> None:
        filename, size = upload_request_metadata({
            "Content-Length": str(2 * 1024 * 1024 * 1024),
            "X-ResearchOS-Filename": "%E8%AE%BA%E6%96%87.pdf",
        })
        self.assertEqual(filename, "论文.pdf")
        self.assertEqual(size, 2 * 1024 * 1024 * 1024)

    def test_upload_is_saved_under_ignored_runtime_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = WorkSessionUploadStore(root=root)
            result = store.save_stream("paper.pdf", io.BytesIO(b"fixture-pdf"), 11)
            self.assertTrue(result["ok"])
            self.assertTrue(str(result["path"]).startswith("06_active_context/work_state/uploads/"))
            self.assertEqual((root / str(result["path"])).read_bytes(), b"fixture-pdf")
            self.assertEqual(result["ownership"], "user_controlled_session_material")
            self.assertFalse(result["storage"]["auto_delete"])

    def test_upload_creates_a_new_personal_vault_root_without_relaxing_path_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "personal_vault"
            store = WorkSessionUploadStore(root=root)
            result = store.save_stream("paper.pdf", io.BytesIO(b"fixture"), 7)
            self.assertEqual((root / str(result["path"])).read_bytes(), b"fixture")

    def test_filename_is_bounded_and_path_components_are_removed(self) -> None:
        self.assertEqual(WorkSessionUploadStore.safe_filename("../../private paper.pdf"), "private paper.pdf")

    def test_arbitrary_research_file_types_are_preserved_as_local_material(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = WorkSessionUploadStore(root=root)
            for filename in (
                "analysis.ipynb", "metadata.json", "code.py", "archive.zip",
                "slides.pptx", "table.csv", "figure.png", "paper.tex", "references.bib",
            ):
                with self.subTest(filename=filename):
                    result = store.save_stream(filename, io.BytesIO(b"fixture"), 7)
                    self.assertTrue((root / str(result["path"])).is_file())

    def test_unicode_and_long_filenames_remain_identifiable(self) -> None:
        self.assertEqual(WorkSessionUploadStore.safe_filename("论文与实验记录.pdf"), "论文与实验记录.pdf")
        long_name = f"{'很长的研究标题' * 30}.ipynb"
        bounded = WorkSessionUploadStore.safe_filename(long_name)
        self.assertLessEqual(len(bounded), 140)
        self.assertTrue(bounded.endswith(".ipynb"))

    def test_upload_has_no_arbitrary_product_size_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = WorkSessionUploadStore(root=root)
            content = b"x" * (30 * 1024 * 1024 + 1)
            result = store.save_stream("large-paper.pdf", io.BytesIO(content), len(content))
            self.assertEqual((root / str(result["path"])).stat().st_size, len(content))

    def test_cleanup_removes_only_owner_generated_temporary_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = WorkSessionUploadStore(root=root)
            store.upload_dir.mkdir(parents=True)
            attachments = [store.upload_dir / f"material-{index}.pdf" for index in range(30)]
            for path in attachments:
                path.write_bytes(b"user material")
            orphan = store.upload_dir / "material.pdf.atomic.tmp"
            orphan.write_bytes(b"partial")
            result = store.cleanup_generated_temporaries()
            self.assertEqual(result["removed_files"], 1)
            self.assertFalse(orphan.exists())
            self.assertTrue(all(path.exists() for path in attachments))

    def test_existing_symlinked_upload_directory_fails_closed_at_construction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as outside_dir:
            root = Path(temp_dir)
            work_state = root / "06_active_context" / "work_state"
            work_state.mkdir(parents=True)
            (work_state / "uploads").symlink_to(Path(outside_dir), target_is_directory=True)
            with self.assertRaises(WorkSessionUploadError) as caught:
                WorkSessionUploadStore(root=root)
            self.assertEqual(caught.exception.error_type, "unsafe_upload_path")

    def test_symlinked_runtime_root_fails_closed_before_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as outside_dir:
            root = Path(temp_dir) / "personal_vault"
            root.symlink_to(Path(outside_dir), target_is_directory=True)
            with self.assertRaises(WorkSessionUploadError) as caught:
                WorkSessionUploadStore(root=root)
            self.assertEqual(caught.exception.error_type, "unsafe_upload_path")

    def test_symlink_escape_added_after_construction_cannot_write_or_cleanup_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as outside_dir:
            root = Path(temp_dir)
            outside = Path(outside_dir)
            store = WorkSessionUploadStore(root=root)
            active_context = root / "06_active_context"
            active_context.mkdir()
            (active_context / "work_state").symlink_to(outside, target_is_directory=True)
            outside_temporary = outside / "outside.atomic.tmp"
            outside_temporary.write_bytes(b"must remain")

            with self.assertRaises(WorkSessionUploadError) as save_error:
                store.save_stream("paper.pdf", io.BytesIO(b"fixture"), 7)
            self.assertEqual(save_error.exception.error_type, "unsafe_upload_path")
            self.assertEqual(outside_temporary.read_bytes(), b"must remain")
            self.assertEqual(sorted(path.name for path in outside.iterdir()), ["outside.atomic.tmp"])

            with self.assertRaises(WorkSessionUploadError) as cleanup_error:
                store.cleanup_generated_temporaries()
            self.assertEqual(cleanup_error.exception.error_type, "unsafe_upload_path")
            self.assertEqual(outside_temporary.read_bytes(), b"must remain")

    def test_storage_notice_is_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = WorkSessionUploadStore(root=root, working_copy_notice_bytes=1, low_disk_notice_bytes=0)
            result = store.save_stream("paper.pdf", io.BytesIO(b"fixture"), 7)
            self.assertEqual(result["storage"]["notice_code"], "working_copies_large")
            self.assertFalse(result["storage"]["auto_delete"])


if __name__ == "__main__":
    unittest.main()
