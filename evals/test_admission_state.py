from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_kernel.admission_state import (  # noqa: E402
    ADMISSION_STATE_SCHEMA_ID,
    AUTHORITY_ROLES,
    DECISION_STATES,
    MUTATION_STATES,
    VALIDATION_STATES,
    admission_view,
    initial_admission_state,
    normalize_admission_state,
    transition_admission_state,
)
from researchos_kernel.candidate_envelope import normalize_candidate_envelope  # noqa: E402


class AdmissionStateTest(unittest.TestCase):
    def accepted(self) -> dict[str, str]:
        state = initial_admission_state(authority_role="interpretive")
        state = transition_admission_state(state, axis="decision_state", target="proposed")
        return transition_admission_state(state, axis="decision_state", target="accepted")

    def test_only_exact_applied_and_passed_human_decision_derives_admitted_view(self) -> None:
        state = self.accepted()
        state = transition_admission_state(state, axis="mutation_state", target="staged")
        state = transition_admission_state(state, axis="validation_state", target="pending")
        state = transition_admission_state(state, axis="mutation_state", target="applied")
        self.assertFalse(admission_view(state)["admitted"])
        state = transition_admission_state(state, axis="validation_state", target="passed")
        view = admission_view(state)
        self.assertTrue(view["admitted"])
        self.assertEqual("interpretive", view["authority_role"])
        self.assertNotIn("confirmed", json.dumps(view))

    def test_machine_result_and_untrusted_claims_cannot_promote_any_axis(self) -> None:
        for forged in (
            {**initial_admission_state(), "decision_state": "accepted"},
            {**initial_admission_state(), "mutation_state": "applied", "validation_state": "passed"},
            {**initial_admission_state(), "authority_role": "normative"},
        ):
            with self.assertRaises((ValueError,), msg=forged):
                normalize_admission_state(forged, trusted_producer=False)
        with self.assertRaisesRegex(ValueError, "shape"):
            normalize_admission_state({**initial_admission_state(), "result_mode": "writeback"})
        with self.assertRaisesRegex(ValueError, "shape"):
            normalize_admission_state({**initial_admission_state(), "confirmed": True})

    def test_illegal_cross_axis_combinations_fail_closed(self) -> None:
        base = initial_admission_state()
        attacks = (
            {**base, "mutation_state": "staged"},
            {**base, "validation_state": "passed"},
            {**base, "decision_state": "accepted", "mutation_state": "applied", "validation_state": "unvalidated"},
            {**base, "decision_state": "rejected", "mutation_state": "rolled_back", "validation_state": "failed"},
        )
        for attack in attacks:
            with self.assertRaises(ValueError, msg=attack):
                normalize_admission_state(attack)

    def test_transition_matrix_requires_human_decision_before_mutation(self) -> None:
        with self.assertRaisesRegex(ValueError, "mutation_without_human_decision"):
            transition_admission_state(initial_admission_state(), axis="mutation_state", target="staged")
        with self.assertRaisesRegex(ValueError, "axis"):
            transition_admission_state(initial_admission_state(), axis="authority_role", target="normative")
        rejected = transition_admission_state(
            transition_admission_state(initial_admission_state(), axis="decision_state", target="proposed"),
            axis="decision_state", target="rejected",
        )
        self.assertEqual("not_requested", rejected["mutation_state"])

    def test_schema_id_and_initial_state_are_stable(self) -> None:
        state = initial_admission_state()
        self.assertEqual(ADMISSION_STATE_SCHEMA_ID, state["schema_id"])
        self.assertEqual(
            ("unproposed", "not_requested", "unvalidated", "none"),
            tuple(state[key] for key in ("decision_state", "mutation_state", "validation_state", "authority_role")),
        )

    def test_schema_and_interaction_projection_share_one_vocabulary(self) -> None:
        schema_path = "09_templates/data_contracts/researchos-admission-state-v1.schema.json"
        properties = json.loads((ROOT / schema_path).read_text(encoding="utf-8")).get("properties", {})
        interaction = json.loads(
            (ROOT / "09_templates/data_contracts/researchos-interaction-semantics-v1.json").read_text(encoding="utf-8")
        )
        expected = {
            "decision_state": DECISION_STATES, "mutation_state": MUTATION_STATES,
            "validation_state": VALIDATION_STATES, "authority_role": AUTHORITY_ROLES,
        }
        self.assertEqual(ADMISSION_STATE_SCHEMA_ID, properties.get("schema_id", {}).get("const"))
        for axis, values in expected.items():
            self.assertEqual(tuple(values), tuple(properties.get(axis, {}).get("enum", [])), axis)
        projected = interaction.get("state_axes", {}).get("admission", {})
        self.assertEqual(ADMISSION_STATE_SCHEMA_ID, projected.get("schema_id"))
        self.assertEqual(schema_path, projected.get("owner"), "the admission schema is the sole vocabulary owner")
        for axis, values in expected.items():
            self.assertEqual(tuple(values), tuple(projected.get(axis, [])), axis)
        self.assertNotIn("confirmed", properties, "the schema must not persist confirmed shorthand")

    def test_candidate_envelope_migrates_legacy_status_without_becoming_an_owner(self) -> None:
        migrated = normalize_candidate_envelope({
            "candidate_id": "legacy-validated",
            "authority_state": "validated",
            "authority_role": "normative",
            "validation": {"workflow_status": "processed", "evidence_state": "supported"},
        })
        self.assertEqual({"workflow_status": "processed", "evidence_state": "supported"}, migrated["validation"])
        self.assertEqual(
            {
                "schema_id": ADMISSION_STATE_SCHEMA_ID,
                "decision_state": "accepted",
                "mutation_state": "applied",
                "validation_state": "passed",
                "authority_role": "none",
            },
            migrated["admission_state"],
        )
        self.assertNotIn("authority_state", migrated)
        self.assertEqual("passed", migrated["proposed_writeback"]["validation_state"])


if __name__ == "__main__":
    unittest.main()
