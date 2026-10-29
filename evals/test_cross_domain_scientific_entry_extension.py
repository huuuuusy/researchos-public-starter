from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_data.plugin_lifecycle import apply_action, catalog  # noqa: E402
from researchos_data.task_extensions import load_task_extensions, validate_descriptor  # noqa: E402


EXAMPLE = ROOT / "config/extensions/cross-domain-scientific-entry.example.json"
PUBLIC_RUNTIME_MANIFEST = ROOT / "config/public-runtime-read-manifest.json"


class CrossDomainScientificEntryExtensionTest(unittest.TestCase):
    def descriptor(self) -> dict[str, object]:
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def fixture(self) -> tempfile.TemporaryDirectory[str]:
        context = tempfile.TemporaryDirectory()
        root = Path(context.name)
        descriptor = self.descriptor()
        target = root / "config/extensions/cross-domain-scientific-entry.example.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(descriptor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        readme_source = ROOT / descriptor["documentation"]["readme"]
        readme_target = root / descriptor["documentation"]["readme"]
        readme_target.parent.mkdir(parents=True, exist_ok=True)
        readme_target.write_text(readme_source.read_text(encoding="utf-8"), encoding="utf-8")
        read_groups = [descriptor["task"]["read"]]
        read_groups.extend(descriptor["task"]["read_locales"].values())
        for relative in {path for tiers in read_groups for paths in tiers.values() for path in paths}:
            source = ROOT / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        return context

    def test_example_is_public_safe_and_uses_repository_relative_reads(self) -> None:
        descriptor = self.descriptor()
        validated = validate_descriptor(descriptor, root=ROOT, source=EXAMPLE)
        self.assertTrue(validated["public_safe"])
        self.assertEqual(["private", "public_starter", "personal_vault"], validated["available_in"])
        read_groups = [descriptor["task"]["read"]]
        read_groups.extend(descriptor["task"]["read_locales"].values())
        for relative in {path for tiers in read_groups for paths in tiers.values() for path in paths}:
            self.assertFalse(Path(relative).is_absolute())
            self.assertNotIn("..", Path(relative).parts)

    def test_selected_language_loads_only_its_public_safe_case_pack(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            installed = apply_action(root, "cross_domain_scientific_entry", "install", rebuild=False)
            self.assertTrue(installed["enabled"])
            result = load_task_extensions(root, runtime_scope="public_starter", language="zh-CN")
        task = result["tasks"][0]
        self.assertEqual("cross_domain_scientific_entry", task["id"])
        self.assertEqual("跨域科研入域", task["name"])
        self.assertEqual("artifact", task["default_result_mode"])
        self.assertTrue(all(path.endswith(".zh.md") for path in task["read_tiers"][1]["read"]))

    def test_install_disable_enable_uninstall_is_reversible(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            listing = {item["id"]: item for item in catalog(root)}
            self.assertFalse(listing["cross_domain_scientific_entry"]["installed"])
            self.assertTrue(apply_action(root, "cross_domain_scientific_entry", "install", rebuild=False)["enabled"])
            self.assertFalse(apply_action(root, "cross_domain_scientific_entry", "disable", rebuild=False)["enabled"])
            self.assertTrue(apply_action(root, "cross_domain_scientific_entry", "enable", rebuild=False)["enabled"])
            self.assertFalse(apply_action(root, "cross_domain_scientific_entry", "uninstall", rebuild=False)["installed"])

    def test_public_runtime_manifest_allows_every_public_read_target(self) -> None:
        manifest = json.loads(PUBLIC_RUNTIME_MANIFEST.read_text(encoding="utf-8"))
        allowed = set(manifest["files"])
        descriptor = self.descriptor()
        read_groups = [descriptor["task"]["read"]]
        read_groups.extend(descriptor["task"]["read_locales"].values())
        targets = {path for tiers in read_groups for paths in tiers.values() for path in paths}
        self.assertEqual(set(), targets - allowed)

    def test_public_kernel_and_case_pack_declare_public_safe_frontmatter(self) -> None:
        paths = (
            ROOT / "05_workflows/research_management/cross-domain-scientific-entry-workflow.md",
            ROOT / "05_workflows/research_management/cross-domain-scientific-entry-workflow.zh.md",
            ROOT / "09_templates/cross-domain-scientific-entry-case-pack.md",
            ROOT / "09_templates/cross-domain-scientific-entry-case-pack.zh.md",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), path)
            self.assertIn("\nsensitivity: public_safe\n", text, path)


if __name__ == "__main__":
    unittest.main()
