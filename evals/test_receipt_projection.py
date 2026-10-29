from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))  # the handoff fixture lives in evals/test_handoff_receipt.py

from evals.test_handoff_receipt import handoff  # noqa: E402
from researchos_server.receipt_projection import HANDOFF_PROJECTION_SCHEMA_ID, handoff_projection  # noqa: E402


class ReceiptProjectionTest(unittest.TestCase):
    def test_private_projection_is_allowlisted_and_contains_no_evidence_or_transcript(self) -> None:
        projection = handoff_projection(handoff(), include_content=True, trusted_source=True)
        rendered = json.dumps(projection, ensure_ascii=False)
        self.assertEqual(HANDOFF_PROJECTION_SCHEMA_ID, projection["schema_id"])
        self.assertEqual("included", projection["content_state"])
        self.assertIn("The claim still needs source-level verification.", rendered)
        for forbidden in ('"evidence_ref"', "revision:local-git", "result:run-1", '"transcript":', '"prompt":', '"history":'):
            self.assertNotIn(forbidden, rendered)
        self.assertEqual(
            ["projection_not_authority", "target_not_delivery", "no_transcript"], projection["limitations"]
        )

    def test_suppressed_projection_keeps_states_but_removes_semantic_content(self) -> None:
        projection = handoff_projection(handoff(), include_content=False, trusted_source=True)
        rendered = json.dumps(projection, ensure_ascii=False)
        self.assertEqual("suppressed", projection["content_state"])
        self.assertEqual("candidate", projection["last_judgment"]["state"])
        self.assertEqual("", projection["last_judgment"]["text"])
        self.assertEqual([], projection["forbidden_actions"]["items"])
        self.assertNotIn("external-validity", rendered)
        self.assertNotIn("canonical memory", rendered)

    def test_projection_rejects_untrusted_claim_remainders(self) -> None:
        with self.assertRaisesRegex(ValueError, "handoff_projection_rejected_claims"):
            handoff_projection(handoff(), include_content=True, trusted_source=False)

    def test_projection_does_not_turn_requested_target_into_delivery(self) -> None:
        projection = handoff_projection(handoff(), include_content=True, trusted_source=True)
        self.assertEqual("requested", projection["target_client"]["binding_state"])
        self.assertNotIn("delivery", projection["target_client"])
        self.assertNotIn("authority", projection["target_client"])


if __name__ == "__main__":
    unittest.main()
