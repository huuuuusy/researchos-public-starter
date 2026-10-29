from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_docs_bilingual", ROOT / "scripts" / "validate_docs_bilingual.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class BilingualDocumentationTest(unittest.TestCase):
    def test_current_public_document_pairs_are_valid(self) -> None:
        self.assertEqual(MODULE.validate(), [])

    def test_missing_chinese_pair_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.en.md").write_text("# Guide\n", encoding="utf-8")
            self.assertIn(
                "missing Chinese pair for docs/guide.en.md: docs/guide.zh.md",
                MODULE.validate(root),
            )

    def test_related_tools_url_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reference = root / "docs" / "reference"
            reference.mkdir(parents=True)
            links = "\n".join(
                f"- [Tool {index}](https://example.org/tool-{index})"
                for index in range(MODULE.MIN_RELATED_TOOL_LINKS)
            )
            english = (
                '<a href="RELATED_RESEARCH_TOOLS.zh.md">中文</a>\n'
                "last reviewed on **2026-07-25**\n"
                f"{MODULE.EN_SNAPSHOT_BOUNDARY}\n{links}\n"
            )
            chinese = (
                '<a href="RELATED_RESEARCH_TOOLS.md">English</a>\n'
                "最后核查于 **2026-07-25**\n"
                f"{MODULE.ZH_SNAPSHOT_BOUNDARY}\n{links}\n"
            )
            (reference / "RELATED_RESEARCH_TOOLS.md").write_text(english, encoding="utf-8")
            (reference / "RELATED_RESEARCH_TOOLS.zh.md").write_text(chinese, encoding="utf-8")

            self.assertEqual(MODULE.validate(root), [])

            chinese = chinese.replace(
                "https://example.org/tool-19",
                "https://example.org/drifted-tool",
            )
            (reference / "RELATED_RESEARCH_TOOLS.zh.md").write_text(chinese, encoding="utf-8")
            self.assertIn(
                "related-tools English/Chinese project names, URLs, or ordering have drifted",
                MODULE.validate(root),
            )

    def test_related_tools_snapshot_date_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reference = root / "docs" / "reference"
            reference.mkdir(parents=True)
            links = "\n".join(
                f"- [Tool {index}](https://example.org/tool-{index})"
                for index in range(MODULE.MIN_RELATED_TOOL_LINKS)
            )
            (reference / "RELATED_RESEARCH_TOOLS.md").write_text(
                '<a href="RELATED_RESEARCH_TOOLS.zh.md">中文</a>\n'
                "last reviewed on **2026-07-25**\n"
                f"{MODULE.EN_SNAPSHOT_BOUNDARY}\n{links}\n",
                encoding="utf-8",
            )
            (reference / "RELATED_RESEARCH_TOOLS.zh.md").write_text(
                '<a href="RELATED_RESEARCH_TOOLS.md">English</a>\n'
                "最后核查于 **2026-07-24**\n"
                f"{MODULE.ZH_SNAPSHOT_BOUNDARY}\n{links}\n",
                encoding="utf-8",
            )

            self.assertTrue(
                any(
                    "snapshot dates do not match" in failure
                    for failure in MODULE.validate(root)
                )
            )

    def test_retired_reader_document_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            retired = root / "docs" / "user-journeys.en.md"
            retired.parent.mkdir(parents=True)
            retired.write_text("# Retired\n", encoding="utf-8")
            self.assertIn(
                "retired reader document must not return: docs/user-journeys.en.md",
                MODULE.validate_document_ownership(root),
            )

    def test_reference_to_retired_reader_document_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            docs = root / "docs"
            docs.mkdir()
            (docs / "README.md").write_text(
                "Read docs/releases/v1.0.0-validation-receipt.md\n",
                encoding="utf-8",
            )
            failures = MODULE.validate_document_ownership(root)
            self.assertTrue(
                any("still references retired reader document" in failure for failure in failures)
            )


if __name__ == "__main__":
    unittest.main()
