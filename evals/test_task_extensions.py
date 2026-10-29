from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_data.task_extensions import TaskExtensionError, load_task_extensions, validate_extension_files


EXAMPLE = ROOT / "config" / "extensions" / "method-comparison.example.json"


class TaskExtensionContractTest(unittest.TestCase):
    def descriptor(self) -> dict[str, object]:
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        # Exercise the v1 compatibility adapter; repository examples themselves
        # are covered by the explicit v1.1 governance tests.
        data.pop("governance", None)
        data.pop("documentation", None)
        data["enabled"] = True
        return data

    def fixture_root(self, descriptor: dict[str, object]) -> tempfile.TemporaryDirectory[str]:
        context = tempfile.TemporaryDirectory()
        root = Path(context.name)
        read_groups = [descriptor["task"]["read"]]
        read_groups.extend(descriptor["task"].get("read_locales", {}).values())
        for relative in {path for tiers in read_groups for tier in tiers.values() for path in tier}:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("---\nsensitivity: public\n---\nfixture\n", encoding="utf-8")
        extension = root / "config" / "extensions" / "method-comparison.json"
        extension.parent.mkdir(parents=True, exist_ok=True)
        extension.write_text(json.dumps(descriptor, ensure_ascii=False), encoding="utf-8")
        return context

    def test_repository_example_is_valid_but_inactive(self) -> None:
        self.assertEqual(validate_extension_files(ROOT), [])
        result = load_task_extensions(ROOT, runtime_scope="public_starter", language="zh-CN")
        self.assertEqual(result["tasks"], [])

    def test_enabled_extension_freezes_task_copy_to_selected_language(self) -> None:
        descriptor = self.descriptor()
        with self.fixture_root(descriptor) as directory:
            result = load_task_extensions(Path(directory), runtime_scope="public_starter", language="zh-CN")
        task = result["tasks"][0]
        self.assertEqual(task["read_first"], descriptor["task"]["read"]["quick"])
        self.assertEqual(task["name"], "研究方法对比")
        self.assertNotIn("Compare research methods", json.dumps(task, ensure_ascii=False))

    def test_public_extension_rejects_sensitive_markdown_read_target(self) -> None:
        descriptor = self.descriptor()
        with self.fixture_root(descriptor) as directory:
            root = Path(directory)
            quick = root / descriptor["task"]["read"]["quick"][0]
            quick.write_text("---\nsensitivity: private\n---\nfixture\n", encoding="utf-8")
            with self.assertRaises(TaskExtensionError):
                load_task_extensions(root, runtime_scope="public_starter", language="en")

    def test_public_extension_rejects_read_target_without_sensitivity(self) -> None:
        descriptor = self.descriptor()
        with self.fixture_root(descriptor) as directory:
            root = Path(directory)
            quick = root / descriptor["task"]["read"]["quick"][0]
            quick.write_text("fixture without frontmatter\n", encoding="utf-8")
            with self.assertRaisesRegex(TaskExtensionError, "must declare public/public_safe"):
                load_task_extensions(root, runtime_scope="public_starter", language="en")

    def test_v1_read_shape_remains_supported_without_locale_overrides(self) -> None:
        descriptor = self.descriptor()
        descriptor["task"].pop("read_locales", None)
        with self.fixture_root(descriptor) as directory:
            result = load_task_extensions(Path(directory), runtime_scope="public_starter", language="zh-CN")
        self.assertEqual(result["tasks"][0]["read_first"], descriptor["task"]["read"]["quick"])

    def test_one_descriptor_adds_a_route_without_core_code(self) -> None:
        descriptor = self.descriptor()
        with self.fixture_root(descriptor) as directory:
            result = load_task_extensions(Path(directory), runtime_scope="private", language="zh-CN")
        self.assertEqual([task["id"] for task in result["tasks"]], ["method_comparison"])
        task = result["tasks"][0]
        self.assertEqual(task["workspace"], "agent")
        self.assertEqual(task["default_result_mode"], "answer")
        self.assertNotIn("Compare research methods", json.dumps(task, ensure_ascii=False))

    def test_public_scope_fails_closed_for_unsafe_pack(self) -> None:
        descriptor = self.descriptor()
        descriptor["public_safe"] = False
        with self.fixture_root(descriptor) as directory:
            with self.assertRaises(TaskExtensionError):
                load_task_extensions(Path(directory), runtime_scope="public_starter", language="en")

    def test_extension_cannot_disable_core_confirmation(self) -> None:
        descriptor = self.descriptor()
        descriptor["authority"]["requires_human_confirmation"] = False
        with self.fixture_root(descriptor) as directory:
            with self.assertRaises(TaskExtensionError):
                load_task_extensions(Path(directory), runtime_scope="private", language="en")

    def test_descriptor_symlink_cannot_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "config" / "extensions" / "escaped.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(EXAMPLE)
            failures = validate_extension_files(root)
        self.assertTrue(any("descriptor must stay inside the repository" in failure for failure in failures))

    def test_task_id_cannot_shadow_core_route(self) -> None:
        descriptor = self.descriptor()
        descriptor["id"] = "material_intake"
        descriptor["task"]["aliases"] = []
        with self.fixture_root(descriptor) as directory:
            with self.assertRaises(TaskExtensionError):
                load_task_extensions(
                    Path(directory),
                    runtime_scope="private",
                    language="en",
                    base_task_ids={"material_intake"},
                )

    def test_alias_cannot_shadow_reserved_core_route(self) -> None:
        descriptor = self.descriptor()
        descriptor["task"]["aliases"] = ["material"]
        with self.fixture_root(descriptor) as directory:
            with self.assertRaises(TaskExtensionError):
                load_task_extensions(
                    Path(directory),
                    runtime_scope="private",
                    language="en",
                    base_task_ids={"material"},
                )

    def test_empty_read_tier_fails_during_validation(self) -> None:
        descriptor = self.descriptor()
        descriptor["task"]["read"]["quick"] = []
        with self.fixture_root(descriptor) as directory:
            with self.assertRaises(TaskExtensionError):
                load_task_extensions(Path(directory), runtime_scope="private", language="en")

    def test_read_path_cannot_escape_through_symlink(self) -> None:
        descriptor = self.descriptor()
        descriptor["task"]["read"] = {
            "quick": ["linked.md"],
            "standard": ["linked.md"],
            "evidence": ["linked.md"],
        }
        with tempfile.TemporaryDirectory() as outside, self.fixture_root(descriptor) as directory:
            root = Path(directory)
            link = root / "linked.md"
            link.unlink()
            external = Path(outside) / "outside.md"
            external.write_text("outside\n", encoding="utf-8")
            link.symlink_to(external)
            with self.assertRaises(TaskExtensionError):
                load_task_extensions(root, runtime_scope="private", language="en")

    def test_two_real_descriptors_cannot_share_an_alias(self) -> None:
        descriptor = self.descriptor()
        with self.fixture_root(descriptor) as directory:
            root = Path(directory)
            second = self.descriptor()
            second["id"] = "second_comparison"
            target = root / "config" / "extensions" / "second-comparison.json"
            target.write_text(json.dumps(second, ensure_ascii=False), encoding="utf-8")
            failures = validate_extension_files(root)
        self.assertTrue(any("route compare_methods already belongs" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
