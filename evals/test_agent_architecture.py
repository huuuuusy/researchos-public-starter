from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "validate_agent_architecture",
    ROOT / "scripts" / "validate_agent_architecture.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class AgentArchitectureTest(unittest.TestCase):
    def test_public_code_routes_match_agent_map(self) -> None:
        failures, counts = MODULE.validate(ROOT)
        self.assertEqual(failures, [])
        self.assertGreater(counts["frontend_modules"], 0)
        self.assertGreater(counts["reachable_kernel_modules"], 0)
        self.assertGreater(counts["reachable_adapter_modules"], 0)
        self.assertGreater(counts["reachable_server_modules"], 0)
        self.assertEqual(counts["removed_python_reintroduced"], 0)
        self.assertEqual(counts["legacy_cases_reintroduced"], 0)

    def test_dependency_direction_rejects_inward_violations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scripts = Path(directory) / "scripts"
            for package in ("researchos_kernel", "researchos_adapters", "researchos_server"):
                (scripts / package).mkdir(parents=True)
                (scripts / package / "__init__.py").write_text("", encoding="utf-8")
            (scripts / "ros.py").write_text("", encoding="utf-8")
            (scripts / "researchos_kernel" / "rules.py").write_text(
                "def late():\n    from researchos_adapters import dispatch\n    import ros\n", encoding="utf-8")
            (scripts / "researchos_adapters" / "dispatch.py").write_text(
                "from researchos_kernel import rules\nfrom researchos_server.codex_runner import CodexRunner\n",
                encoding="utf-8")
            failures = MODULE.validate_dependency_direction(Path(directory))
        self.assertEqual(3, len(failures), failures)
        self.assertTrue(any("researchos_kernel/rules.py: imports researchos_adapters" in item for item in failures))
        self.assertTrue(any("researchos_kernel/rules.py: imports ros;" in item for item in failures))
        self.assertTrue(any("researchos_adapters/dispatch.py: imports researchos_server.codex_runner" in item
                            for item in failures))


class FrontendLayeringTest(unittest.TestCase):
    def test_layering_rule_rejects_upward_references(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "dashboard" / "src"
            files = {
                "core/state.js": "global.ResearchOSState = {}; global.ResearchOSPreviewService.load();",
                "services/preview.js": "global.ResearchOSPreviewService = {}; global.ResearchOSCardView.render();",
                "services/preview-workbench.js": "global.ResearchOSPreviewWorkbench = {}; global.ResearchOSCardView.render();",
                "views/card.js": "global.ResearchOSCardView = {}; global.ResearchOSPreviewService.load(); global.ResearchOSCardModel.build();",
                "plugins/card-model.js": "global.ResearchOSCardModel = {};",
            }
            for relative, text in files.items():
                (src / relative).parent.mkdir(parents=True, exist_ok=True)
                (src / relative).write_text(text, encoding="utf-8")
            failures = MODULE.validate_frontend_layering(Path(directory))
        self.assertEqual(len(failures), 3, failures)
        self.assertTrue(any("core/state.js: core must not reference services global ResearchOSPreviewService" in item for item in failures))
        self.assertTrue(any("views/card.js: views may reference only" in item and "ResearchOSPreviewService" in item for item in failures))
        self.assertTrue(any("services/preview.js: only controller services" in item for item in failures))

    def test_shipped_dashboard_respects_layering(self) -> None:
        self.assertEqual(MODULE.validate_frontend_layering(ROOT), [])


if __name__ == "__main__":
    unittest.main()
