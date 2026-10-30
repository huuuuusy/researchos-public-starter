from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_release_metadata", ROOT / "scripts" / "validate_release_metadata.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ReleaseMetadataTest(unittest.TestCase):
    def test_current_release_metadata_is_aligned(self) -> None:
        # The checkout is either a release candidate (no date) or a final release (its CITATION date).
        detected_date, stage_failures = MODULE.detect_release_stage(ROOT)
        self.assertEqual(stage_failures, [])
        self.assertEqual(MODULE.validate(release_date=detected_date), [])
        snapshot = MODULE.validation_snapshot(ROOT)
        self.assertGreater(snapshot["python_tests"], 0)
        self.assertGreater(snapshot["public_safety_files"], 0)
        self.assertGreater(snapshot["markdown_files"], 0)
        self.assertGreater(snapshot["bilingual_pairs"], 0)
        self.assertEqual(snapshot["frontend_source_modules"], snapshot["active_frontend_modules"])
        self.assertGreater(snapshot["active_frontend_modules"], 0)
        self.assertGreater(snapshot["reachable_server_modules"], 0)

        original_read = MODULE.read
        stale_count = snapshot["reachable_server_modules"] - 1

        def read_with_stale_server_count(root: Path, relative: str) -> str:
            text = original_read(root, relative)
            if relative == "docs/releases/v1.0.3.md":
                return text.replace(
                    f"`{snapshot['reachable_server_modules']}` reachable public-server modules",
                    f"`{stale_count}` reachable public-server modules",
                )
            if relative == "docs/releases/v1.0.3.zh.md":
                return text.replace(
                    f"`{snapshot['reachable_server_modules']}` 个可达 public server 模块",
                    f"`{stale_count}` 个可达 public server 模块",
                )
            return text

        with mock.patch.object(MODULE, "read", side_effect=read_with_stale_server_count):
            failures = MODULE.validate(release_date=detected_date)
        self.assertTrue(any("server graph" in failure for failure in failures))

    def test_unknown_version_fails_closed(self) -> None:
        self.assertTrue(MODULE.validate(version="9.9.9", release_date="2099-01-01"))

    def test_candidate_metadata_cannot_pass_as_final_release(self) -> None:
        self.assertTrue(MODULE.validate(release_date="2026-08-12"))
        self.assertTrue(MODULE.validate(release_date="2026-02-30"))
        detected_date, failures = MODULE.detect_release_stage(ROOT)
        self.assertTrue(detected_date is None or MODULE.valid_iso_date(detected_date))
        self.assertEqual(failures, [])
        if detected_date:
            # A final release cannot pass as the candidate it replaced.
            self.assertTrue(MODULE.validate())
        self.assertTrue(
            MODULE.invocation_failures(
                release_date="2026-08-20",
                expected_commit=None,
                require_clean=False,
            )
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "CITATION.cff").write_text(
                'cff-version: 1.2.0\nversion: "1.0.3"\ndate-released: "2026-08-20"\n',
                encoding="utf-8",
            )
            detected_date, failures = MODULE.detect_release_stage(root)
            self.assertEqual(detected_date, "2026-08-20")
            self.assertEqual(failures, [])

            (root / "CITATION.cff").write_text(
                'cff-version: 1.2.0\nversion: "1.0.3"\ndate-released: "2026-02-30"\n',
                encoding="utf-8",
            )
            detected_date, failures = MODULE.detect_release_stage(root)
            self.assertIsNone(detected_date)
            self.assertTrue(any("real ISO date" in failure for failure in failures))

    def test_release_artifact_hash_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (
                "CITATION.cff",
                "CHANGELOG.md",
                "README.md",
                "README.zh.md",
                "LICENSE.md",
                "dashboard/index.html",
                "docs/releases/v1.0.3.md",
                "docs/releases/v1.0.3.zh.md",
                *MODULE.RELEASE_ARTIFACTS,
            ):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            (root / "evals").mkdir()
            (root / "dashboard/src").mkdir(parents=True)
            for notes_relative in ("docs/releases/v1.0.3.md", "docs/releases/v1.0.3.zh.md"):
                notes = root / notes_relative
                text = notes.read_text(encoding="utf-8")
                declared = MODULE.declared_artifact_hashes(text)
                for artifact_relative in MODULE.RELEASE_ARTIFACTS:
                    actual = MODULE.sha256(root / artifact_relative)
                    text = text.replace(declared[artifact_relative], actual)
                notes.write_text(text, encoding="utf-8")
            self.assertFalse(any("artifact hash" in failure for failure in MODULE.validate(root=root)))
            artifact = root / MODULE.RELEASE_ARTIFACTS[-1]
            artifact.write_text(artifact.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertTrue(any("artifact hash" in failure for failure in MODULE.validate(root=root)))


if __name__ == "__main__":
    unittest.main()
