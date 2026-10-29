from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from plan_context import as_text, route_for, route_payload  # noqa: E402


class PlanContextContractTest(unittest.TestCase):
    def test_conversation_entrypoint_does_not_import_projection_builder(self) -> None:
        source = (ROOT / "scripts" / "plan_context.py").read_text(encoding="utf-8")
        imported_modules = {
            node.module
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertIn("researchos_data.public_conversation_catalog", imported_modules)
        self.assertNotIn("build_public_starter_data", imported_modules)

    def test_public_routes_expose_language_and_authority_contract(self) -> None:
        route = route_for("material_intake", "en")
        self.assertIsNotNone(route)
        payload = route_payload(route, "en", "quick")
        self.assertEqual(payload["active_language"], "en")
        self.assertEqual(payload["template_policy"], "active_language_only")
        self.assertEqual(payload["inactive_language_behavior"], "reference_only_do_not_read_by_agent")
        self.assertEqual(payload["default_result_mode"], "answer")
        self.assertEqual(payload["sensitivity_default"], "local_only")
        self.assertIn("never authority", payload["confirmation_boundary"])

    def test_chinese_text_route_freezes_english_templates(self) -> None:
        route = route_for("material_intake", "zh-CN")
        self.assertIsNotNone(route)
        payload = route_payload(route, "zh-CN", "quick")
        text = as_text(payload, "zh-CN")
        self.assertIn("当前模板语言: zh-CN", text)
        self.assertIn("非当前语言模板: reference_only_do_not_read_by_agent", text)
        self.assertIn("确认边界: 长期记忆", text)

    def test_help_names_task_id_and_natural_language_boundary(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "plan_context.py"), "--help"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("TASK_ID", completed.stdout)
        self.assertIn("--list", completed.stdout)
        self.assertIn("natural-language research requests", completed.stdout)

    def test_unknown_task_points_to_list_and_agent_route(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "plan_context.py"),
                "Read one paper and compare it with my project",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        message = completed.stdout + completed.stderr
        self.assertIn("Unknown task ID", message)
        self.assertIn("plan_context.py --list", message)
        self.assertIn("file-aware agent", message)


if __name__ == "__main__":
    unittest.main()
