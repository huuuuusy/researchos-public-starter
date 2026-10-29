from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_public_safety", ROOT / "scripts" / "validate_public_safety.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
LINK_SPEC = importlib.util.spec_from_file_location("check_all_links", ROOT / "scripts" / "check_all_links.py")
LINK_MODULE = importlib.util.module_from_spec(LINK_SPEC)
assert LINK_SPEC and LINK_SPEC.loader
LINK_SPEC.loader.exec_module(LINK_MODULE)


class PublicSafetyTest(unittest.TestCase):
    def test_exact_public_citation_does_not_hide_unlinked_private_residue(self):
        for title, url in MODULE.PUBLIC_REPORT_CITATIONS.items():
            markers = frozenset({hashlib.sha256(title.lower().encode("utf-8")).hexdigest()})
            citation = f"{title} [{title}]({url})"
            self.assertEqual([], MODULE.scan_text(MODULE.public_report_citation_view(citation), markers))
            self.assertIn("private semantic marker", MODULE.scan_text(citation, markers))
            self.assertIn("private semantic marker", MODULE.scan_text(MODULE.public_report_citation_view(citation + " private notes about " + title), markers))
            self.assertIn("private semantic marker", MODULE.scan_text(MODULE.public_report_citation_view(f"[{title}](https://example.invalid)"), markers))
        self.assertIn("macOS user path", MODULE.scan_text(MODULE.public_report_citation_view("/" + "Users/example/private")))

    def test_detects_private_semantic_residue(self) -> None:
        marker = "hidden-private-suite"
        marker_hashes = frozenset({hashlib.sha256(marker.encode("utf-8")).hexdigest()})
        failures = MODULE.scan_text(f"Example copied from {marker}", marker_hashes)
        self.assertIn("private semantic marker", failures)

    def test_no_private_name_list_is_published(self) -> None:
        self.assertEqual(MODULE.PRIVATE_SEMANTIC_MARKER_HASHES, frozenset())

    def test_detects_paths_and_secrets(self) -> None:
        local_path = "/" + "Users/example/private"
        key_assignment = "OPENAI_API_KEY" + "=secret"
        failures = MODULE.scan_text(f"{local_path}\n{key_assignment}")
        self.assertIn("macOS user path", failures)
        self.assertIn("API-key assignment", failures)

    def test_generic_public_copy_is_allowed(self) -> None:
        self.assertEqual(MODULE.scan_text("User-provided materials and evidence boundaries."), [])

    def test_transient_test_and_browser_artifacts_are_not_release_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / ".pytest_cache").mkdir()
            (root / ".pytest_cache" / "README.md").write_text("cache", encoding="utf-8")
            (root / ".playwright-cli").mkdir()
            (root / ".playwright-cli" / "page.yml").write_text("snapshot", encoding="utf-8")
            runtime_log = root / "06_active_context" / "work_state" / "runner-logs" / "current.md"
            runtime_log.parent.mkdir(parents=True)
            runtime_log.write_text("[local only](missing.md)", encoding="utf-8")
            public_note = root / "README.md"
            public_note.write_text("public release", encoding="utf-8")
            self.assertEqual(MODULE.text_files(root), [public_note])
            self.assertNotIn(runtime_log, LINK_MODULE.iter_markdown_files(root=root))

    def test_public_dashboard_service_link_uses_public_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dashboard = root / "dashboard"
            dashboard.mkdir()
            index = dashboard / "index.html"
            index.write_text('<a href="http://127.0.0.1:8878/">Open</a>', encoding="utf-8")
            self.assertIn(
                "dashboard/index.html: public service link must use port 8880",
                MODULE.validate(root),
            )
            index.write_text('<a href="http://127.0.0.1:8880/">Open</a>', encoding="utf-8")
            self.assertEqual(MODULE.validate(root), [])

    def test_rejects_private_integration_runtime_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            scripts = root / "scripts"
            scripts.mkdir()
            bridge = scripts / "bridge.py"
            bridge.write_text("mode = 'federation'\n", encoding="utf-8")
            self.assertIn(
                "scripts/bridge.py: private integration runtime surface is not public-safe",
                MODULE.validate(root),
            )

    def test_rejects_actor_bound_runtime_owners(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dashboard = root / "dashboard"
            dashboard.mkdir()
            runtime = dashboard / "actor.js"
            runtime.write_text("const field = 'relation_to_shiyu';\n", encoding="utf-8")
            self.assertIn(
                "dashboard/actor.js: actor-bound runtime owner is not public-safe",
                MODULE.validate(root),
            )

    def test_public_docs_state_private_integration_absence(self) -> None:
        overview = (ROOT / "docs" / "system-reference.en.md").read_text(encoding="utf-8")
        overview_zh = (ROOT / "docs" / "system-reference.zh.md").read_text(encoding="utf-8")
        self.assertIn("no sibling private-repository discovery", overview)
        self.assertIn("不发现其他私人仓库", overview_zh)


if __name__ == "__main__":
    unittest.main()
