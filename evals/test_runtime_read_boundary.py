from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_server.preview_file_server import PreviewFileServer  # noqa: E402
from researchos_server.runtime_read_boundary import (  # noqa: E402
    PUBLIC_READ_MANIFEST,
    PUBLIC_READ_MANIFEST_SCHEMA,
    RuntimeReadBoundary,
    RuntimeReadBoundaryError,
)
from researchos_server.source_tree_store import SourceTreeError, SourceTreeStore  # noqa: E402


FIXTURE_ALLOWED_FILES = (
    "08_exports/public_starter/demo.md",
    "docs/reference/SAFE_EXPORT_POLICY.md",
    "09_templates/person-template.md",
    "05_workflows/research_management/material-intake-workflow.md",
    "scripts/plan_context.py",
)
UNREGISTERED_PUBLIC_FILES = (
    "08_exports/public_starter/future-sensitive.md",
    "docs/reference/future-sensitive.yml",
    "09_templates/future-sensitive.pdf",
)


class RuntimeReadBoundaryTest(unittest.TestCase):
    def write_manifest(self, root: Path, files: object = FIXTURE_ALLOWED_FILES) -> None:
        manifest = root / PUBLIC_READ_MANIFEST
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps(
                {
                    "schema_id": PUBLIC_READ_MANIFEST_SCHEMA,
                    "version": "test-v1",
                    "files": files,
                }
            ),
            encoding="utf-8",
        )

    def fixture(self, root: Path) -> None:
        text_files = {
            "08_exports/public_starter/demo.md": "demo",
            "docs/reference/SAFE_EXPORT_POLICY.md": "policy",
            "09_templates/person-template.md": "template",
            "05_workflows/research_management/material-intake-workflow.md": "workflow",
            "scripts/plan_context.py": "print('safe')",
            "08_exports/public_starter/future-sensitive.md": "unregistered",
            "docs/reference/future-sensitive.yml": "unregistered: true",
            "personal_vault/06_active_context/research-portfolio.md": "private",
            "config/researchos.runtime.local.json": '{"api_key":"secret"}',
            "06_active_context/work_state/runner-logs/private.md": "secret",
        }
        for relative, text in text_files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        pdf = root / "09_templates/future-sensitive.pdf"
        pdf.parent.mkdir(parents=True, exist_ok=True)
        pdf.write_bytes(b"%PDF-unregistered")
        self.write_manifest(root)

    def test_public_boundary_allows_exact_files_and_ancestors_but_blocks_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            boundary = RuntimeReadBoundary.public_starter(root)

            for relative in FIXTURE_ALLOWED_FILES:
                self.assertEqual((root / relative).resolve(), boundary.resolve(relative))
            for ancestor in (
                "",
                "08_exports",
                "08_exports/public_starter",
                "docs",
                "docs/reference",
                "09_templates",
            ):
                self.assertEqual((root / ancestor).resolve(), boundary.resolve(ancestor))
            for relative in (
                *UNREGISTERED_PUBLIC_FILES,
                "08_exports/public_starter/unregistered-child",
                "personal_vault",
                "personal_vault/06_active_context/research-portfolio.md",
                "config",
                "config/researchos.runtime.local.json",
                "06_active_context",
                "06_active_context/work_state/runner-logs/private.md",
            ):
                with self.subTest(relative=relative):
                    with self.assertRaises(RuntimeReadBoundaryError):
                        boundary.resolve(relative)

            alias = root / "08_exports/public_starter/unregistered-alias.md"
            alias.symlink_to(root / "08_exports/public_starter/demo.md")
            self.assertFalse(boundary.allows_path(alias))
            with self.assertRaises(RuntimeReadBoundaryError):
                boundary.resolve("08_exports/public_starter/unregistered-alias.md")

            self.assertFalse(boundary.public_dashboard_data_blocked("/data/researchos-dashboard.json", True))
            self.assertTrue(boundary.public_dashboard_data_blocked("/data/researchos-local.json", True))
            self.assertTrue(boundary.public_dashboard_data_blocked("/data/../data/researchos-local.json", True))
            self.assertTrue(boundary.public_dashboard_data_blocked("/DATA/researchos-local.json", True))
            self.assertFalse(boundary.public_dashboard_data_blocked("/data/researchos-local.json", False))

    def test_unregistered_md_yaml_and_pdf_are_hidden_from_preview_tree_and_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            root.mkdir()
            self.fixture(root)
            boundary = RuntimeReadBoundary.public_starter(root)
            preview = PreviewFileServer(root, read_boundary=boundary)
            store = SourceTreeStore(root, read_boundary=boundary)

            self.assertIsNone(preview.markdown_target(UNREGISTERED_PUBLIC_FILES[0]))
            self.assertIsNone(preview.markdown_target(UNREGISTERED_PUBLIC_FILES[1]))
            self.assertIsNone(preview.pdf_target(UNREGISTERED_PUBLIC_FILES[2]))
            for relative in UNREGISTERED_PUBLIC_FILES:
                with self.subTest(relative=relative):
                    with self.assertRaises(SourceTreeError):
                        store.info(relative)

            starter_names = {
                node["name"]
                for node in store.tree("08_exports/public_starter")["node"]["children"]
            }
            reference_names = {
                node["name"]
                for node in store.tree("docs/reference")["node"]["children"]
            }
            template_names = {
                node["name"]
                for node in store.tree("09_templates")["node"]["children"]
            }
            self.assertNotIn("future-sensitive.md", starter_names)
            self.assertNotIn("future-sensitive.yml", reference_names)
            self.assertNotIn("future-sensitive.pdf", template_names)

            destination = base / "runtime"
            boundary.materialize(destination)
            for relative in UNREGISTERED_PUBLIC_FILES:
                self.assertFalse((destination / relative).exists())

    def test_public_source_tree_shows_only_manifest_ancestors_and_exact_children(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            store = SourceTreeStore(root, read_boundary=RuntimeReadBoundary.public_starter(root))

            names = {node["name"] for node in store.tree()["node"]["children"]}
            self.assertIn("08_exports", names)
            self.assertIn("docs", names)
            self.assertIn("09_templates", names)
            self.assertNotIn("personal_vault", names)
            self.assertNotIn("config", names)
            self.assertNotIn("06_active_context", names)
            with self.assertRaises(SourceTreeError):
                store.info("personal_vault/06_active_context/research-portfolio.md")

    def test_personal_vault_keeps_vault_directory_and_public_exact_files_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            boundary = RuntimeReadBoundary.personal_vault(root, root / "personal_vault")
            store = SourceTreeStore(root, read_boundary=boundary)

            private_note = boundary.resolve("personal_vault/06_active_context/research-portfolio.md")
            self.assertEqual((root / "personal_vault/06_active_context/research-portfolio.md").resolve(), private_note)
            self.assertEqual("private", store.info("personal_vault/06_active_context/research-portfolio.md")["node"]["sensitivity"])
            self.assertEqual((root / "09_templates/person-template.md").resolve(), boundary.resolve("09_templates/person-template.md"))
            with self.assertRaises(RuntimeReadBoundaryError):
                boundary.resolve("09_templates/future-sensitive.pdf")
            with self.assertRaises(RuntimeReadBoundaryError):
                boundary.resolve("config/researchos.runtime.local.json")

    def test_codex_runtime_injects_public_or_personal_scope_instead_of_client_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            boundary = RuntimeReadBoundary.private(root)
            factory = lambda **kwargs: kwargs
            command_factory = lambda **kwargs: kwargs
            model_factory = lambda **kwargs: kwargs
            common = {
                "write_root": root / "vault",
                "public_codex_root": root / "public-runtime",
                "codex_factory": factory,
                "command_runner_factory": command_factory,
                "model_catalog_factory": model_factory,
                "log_jsonl": root / "runner.jsonl",
                "log_md": root / "runner.md",
                "post_run_refresh": lambda: {"ok": True},
            }

            public = boundary.codex_runtime(public_starter=True, **common)
            vault = boundary.codex_runtime(public_starter=False, **common)
            missing_refresh = {**common, "post_run_refresh": None}
            with self.assertRaisesRegex(ValueError, "post-run refresh"):
                boundary.codex_runtime(public_starter=False, **missing_refresh)

        self.assertEqual("public_starter", public["runtime_scope"])
        self.assertTrue(public["public_starter"])
        self.assertIsNone(public["post_run_refresh"])
        self.assertEqual("personal_vault", vault["runtime_scope"])
        self.assertFalse(vault["public_starter"])
        self.assertIsNotNone(vault["post_run_refresh"])

    def test_missing_and_malformed_public_manifests_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeReadBoundaryError):
                RuntimeReadBoundary.public_starter(Path(directory))

        malformed_files: tuple[object, ...] = (
            [],
            "safe.md",
            ["safe.md", "safe.md"],
            ["/tmp/safe.md"],
            ["../safe.md"],
            ["safe.md/"],
            ["safe*.md"],
            [" safe.md"],
            ["safe\\file.md"],
            ["safe-directory"],
            ["safe-link.md"],
        )
        for files in malformed_files:
            with self.subTest(files=files), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "safe.md").write_text("safe", encoding="utf-8")
                (root / "safe-directory").mkdir()
                outside = root.parent / f"outside-{root.name}.md"
                outside.write_text("outside", encoding="utf-8")
                (root / "safe-link.md").symlink_to(outside)
                self.write_manifest(root, files)
                with self.assertRaises(RuntimeReadBoundaryError):
                    RuntimeReadBoundary.public_starter(root)
                outside.unlink()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / PUBLIC_READ_MANIFEST
            manifest.parent.mkdir(parents=True)
            manifest.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(RuntimeReadBoundaryError):
                RuntimeReadBoundary.public_starter(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / PUBLIC_READ_MANIFEST
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps({"schema_id": "wrong", "version": 1, "files": ["safe.md"]}),
                encoding="utf-8",
            )
            with self.assertRaises(RuntimeReadBoundaryError):
                RuntimeReadBoundary.public_starter(root)

    def test_materialize_copies_exact_files_and_rejects_nonempty_or_in_repo_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            root.mkdir()
            self.fixture(root)
            boundary = RuntimeReadBoundary.public_starter(root)

            destination = base / "runtime"
            destination.mkdir()
            boundary.materialize(destination)
            self.assertTrue((destination / "08_exports/public_starter/demo.md").is_file())
            self.assertTrue((destination / "09_templates/person-template.md").is_file())
            for relative in UNREGISTERED_PUBLIC_FILES:
                self.assertFalse((destination / relative).exists())
            self.assertFalse(any(path.is_symlink() for path in destination.rglob("*")))
            with self.assertRaises(RuntimeReadBoundaryError):
                boundary.materialize(destination)

            stale_destination = base / "stale-runtime"
            stale_destination.mkdir()
            stale = stale_destination / "stale.md"
            stale.write_text("stale", encoding="utf-8")
            with self.assertRaises(RuntimeReadBoundaryError):
                boundary.materialize(stale_destination)
            self.assertEqual("stale", stale.read_text(encoding="utf-8"))
            with self.assertRaises(RuntimeReadBoundaryError):
                boundary.materialize(root / "runtime")


if __name__ == "__main__":
    unittest.main()
