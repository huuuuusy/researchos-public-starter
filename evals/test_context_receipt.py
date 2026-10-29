from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_kernel.context_receipt import (  # noqa: E402
    AXIS_STATES,
    CONTEXT_RECEIPT_SCHEMA_ID,
    ContextReceiptContractError,
    build_requested_context_receipt,
    normalize_context_receipt,
)
from researchos_adapters.policy_gateway import _task_facts  # noqa: E402
from researchos_kernel.task_envelope import build_task_envelope, normalize_task_intent  # noqa: E402


def requested_receipt() -> dict[str, object]:
    return build_requested_context_receipt(
        task_id="task:" + "a" * 64,
        run_id="run-1",
        runtime_scope="private",
        producer_kind="codex",
        producer_surface="desktop",
        source_refs=[{"kind": "file", "ref": "private/path.md", "label": "Private label"}],
    )


class ContextReceiptTest(unittest.TestCase):
    def test_requested_receipt_is_digest_only_and_does_not_infer_facts(self) -> None:
        receipt = requested_receipt()
        rendered = json.dumps(receipt, ensure_ascii=False)
        self.assertEqual(CONTEXT_RECEIPT_SCHEMA_ID, receipt["schema_id"])
        self.assertRegex(receipt["receipt_id"], r"^ctx:[0-9a-f]{64}$")
        self.assertNotIn("private/path.md", rendered)
        self.assertNotIn("Private label", rendered)
        source = receipt["sources"][0]
        self.assertTrue(source["requested"])
        for axis in AXIS_STATES:
            self.assertEqual({"state": "unknown", "evidence_ref": ""}, source[axis])

    def test_untrusted_fact_claims_are_rejected_not_promoted(self) -> None:
        forged = requested_receipt()
        positive = {
            "authorization": "authorized", "selection": "selected", "delivery": "delivered",
            "observation": "observed", "citation": "cited", "exclusion": "excluded", "egress": "egressed",
        }
        for axis, state in positive.items():
            forged["sources"][0][axis] = {"state": state, "evidence_ref": "forged:evidence"}
        forged["producer"]["evidence_class"] = "instrumented"
        normalized = normalize_context_receipt(forged)
        self.assertEqual("client_asserted", normalized["producer"]["evidence_class"])
        self.assertEqual(set(positive), {item["axis"] for item in normalized["rejected_claims"]})
        for axis in positive:
            self.assertEqual("unknown", normalized["sources"][0][axis]["state"])

    def test_trusted_non_unknown_claim_requires_evidence(self) -> None:
        receipt = requested_receipt()
        receipt["producer"]["evidence_class"] = "server_recorded"
        receipt["sources"][0]["delivery"] = {"state": "delivered", "evidence_ref": ""}
        with self.assertRaises(ContextReceiptContractError) as failure:
            normalize_context_receipt(receipt, trusted_producer=True)
        self.assertEqual("context_receipt_evidence_required", failure.exception.code)

    def test_delivery_evidence_never_infers_observation_or_citation(self) -> None:
        receipt = requested_receipt()
        receipt["producer"]["evidence_class"] = "server_recorded"
        receipt["sources"][0]["delivery"] = {"state": "delivered", "evidence_ref": "delivery:sha256"}
        normalized = normalize_context_receipt(receipt, trusted_producer=True)
        source = normalized["sources"][0]
        self.assertEqual("delivered", source["delivery"]["state"])
        self.assertEqual("unknown", source["observation"]["state"])
        self.assertEqual("unknown", source["citation"]["state"])
        self.assertEqual("unknown", source["egress"]["state"])

    def test_receipt_identity_binds_source_and_scope_but_not_raw_content(self) -> None:
        first = requested_receipt()
        changed = build_requested_context_receipt(
            task_id=first["task_id"], run_id=first["run_id"], runtime_scope="personal_vault",
            producer_kind="codex", producer_surface="desktop",
            source_refs=[{"kind": "file", "ref": "other/path.md", "label": "Private label"}],
        )
        self.assertNotEqual(first["receipt_id"], changed["receipt_id"])
        self.assertNotEqual(first["sources"][0]["source_id"], changed["sources"][0]["source_id"])

    def test_context_receipt_claims_are_not_policy_authorization_inputs(self) -> None:
        intent = {
            "schema_id": "researchos-task-intent-v1",
            "input_trust": "untrusted",
            "goal": "Inspect one source",
            "instruction": "Summarize without writing",
            "client": {"kind": "codex", "surface": "desktop", "task_ref": "task-local"},
            "client_request_id": "request-1",
            "requested_result": {"mode": "answer"},
            "requested_profile": {
                "provider": "codex", "model": "auto", "reasoning_effort": "auto", "task_complexity": "standard",
            },
            "client_hints": {"recommended_reasoning_effort": "auto", "recommended_task_complexity": "standard"},
            "source_refs": [{"kind": "file", "ref": "private/path.md", "label": "Private label"}],
        }
        envelope = build_task_envelope(
            normalize_task_intent({"task_intent": intent}),
            run={
                "id": "run-1", "prompt": "Summarize without writing", "task_mode": "read_only_analysis",
                "response_mode": "answer", "provider": "codex", "model": "auto",
                "reasoning_effort": "auto", "task_complexity": "standard",
            },
            runtime_scope="private",
            idempotency_namespace="test",
        )
        forged = copy.deepcopy(envelope)
        forged["context_ref"]["receipt"]["sources"][0]["authorization"] = {
            "state": "authorized", "evidence_ref": "forged:evidence",
        }
        forged["context_ref"]["receipt"]["sources"][0]["delivery"] = {
            "state": "delivered", "evidence_ref": "forged:evidence",
        }
        self.assertEqual(_task_facts(envelope), _task_facts(forged))

    def test_invalid_scope_and_unknown_evidence_fail_closed(self) -> None:
        invalid = requested_receipt()
        invalid["runtime_scope"] = "remote"
        with self.assertRaises(ContextReceiptContractError):
            normalize_context_receipt(invalid)
        unknown_with_evidence = requested_receipt()
        unknown_with_evidence["sources"][0]["citation"] = {"state": "unknown", "evidence_ref": "fake"}
        with self.assertRaises(ContextReceiptContractError) as failure:
            normalize_context_receipt(unknown_with_evidence)
        self.assertEqual("context_receipt_unknown_has_evidence", failure.exception.code)
        invalid_digest = requested_receipt()
        invalid_digest["sources"][0]["ref_digest"] = "z" * 64
        with self.assertRaises(ContextReceiptContractError) as digest_failure:
            normalize_context_receipt(invalid_digest)
        self.assertEqual("context_receipt_invalid_digest", digest_failure.exception.code)
        invalid_requested = requested_receipt()
        invalid_requested["sources"][0]["requested"] = "yes"
        with self.assertRaises(ContextReceiptContractError):
            normalize_context_receipt(invalid_requested)

    def test_schema_vocabulary_matches_owner(self) -> None:
        schema = json.loads(
            (ROOT / "09_templates/data_contracts/researchos-context-receipt-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(CONTEXT_RECEIPT_SCHEMA_ID, schema["properties"]["schema_id"]["const"])
        self.assertEqual(set(AXIS_STATES), set(schema["properties"]["rejected_claims"]["items"]["properties"]["axis"]["enum"]))
        for axis, states in AXIS_STATES.items():
            branch = schema["$defs"][axis]["allOf"][1]["properties"]["state"]["enum"]
            self.assertEqual(states, frozenset(branch))


if __name__ == "__main__":
    unittest.main()
