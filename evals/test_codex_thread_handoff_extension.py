from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_data.task_extensions import validate_descriptor
from researchos_data.plugin_docs import public_documentation_leaks


EXAMPLE = ROOT / "config/extensions/codex-thread-handoff.example.json"


class CodexThreadHandoffExtensionTest(unittest.TestCase):
    def descriptor(self) -> dict[str, object]:
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_public_private_semantics_are_exact_and_read_only(self) -> None:
        descriptor = validate_descriptor(self.descriptor(), root=ROOT, source=EXAMPLE)
        self.assertEqual(
            ["private", "public_starter", "personal_vault"], descriptor["available_in"]
        )
        self.assertTrue(descriptor["public_safe"])
        self.assertEqual("local_only", descriptor["sensitivity_default"])
        self.assertEqual("exact", descriptor["governance"]["distribution"]["parity_policy"])
        self.assertEqual("read_only", descriptor["governance"]["effects"]["default_effect"])
        self.assertNotIn("writeback", descriptor["task"]["result_modes"])

    def test_contract_names_required_tools_and_forbidden_surfaces(self) -> None:
        contract = (ROOT / "docs/plugins/codex-thread-handoff/BRIDGE_CONTRACT.md").read_text(
            encoding="utf-8"
        )
        for required in ("list_codex_threads", "read_codex_thread", "user and assistant"):
            self.assertIn(required, contract)
        for forbidden in ("System/developer", "reasoning", "tool calls", "tool output"):
            self.assertIn(forbidden, contract)

    def test_public_docs_contain_no_private_deployment_values(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "docs/plugins/codex-thread-handoff").glob("*.md"))
        )
        self.assertEqual([], public_documentation_leaks(text))
        self.assertNotIn("019fff41-", text)
        self.assertNotIn("trycloudflare.com", text)
        self.assertNotIn("BRIDGE_AUTH_TOKEN=", text)


if __name__ == "__main__":
    unittest.main()
