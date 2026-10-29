from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_kernel.context_receipt import build_requested_context_receipt  # noqa: E402
from researchos_kernel.handoff_receipt import (  # noqa: E402
    HANDOFF_RECEIPT_SCHEMA_ID,
    HandoffReceiptContractError,
    REVISION_SCHEMES,
    build_handoff_receipt,
    normalize_handoff_receipt,
)


def context_receipt() -> dict[str, object]:
    return build_requested_context_receipt(
        task_id="task:" + "a" * 64,
        run_id="run-1",
        runtime_scope="private",
        producer_kind="codex",
        producer_surface="desktop",
        source_refs=[{"kind": "file", "ref": "private/path.md", "label": "Private label"}],
    )


def handoff(**overrides: object) -> dict[str, object]:
    context = context_receipt()
    source_id = str(context["sources"][0]["source_id"])  # type: ignore[index]
    arguments: dict[str, object] = {
        "context_receipt": context,
        "source_id": source_id,
        "revision_scheme": "git_commit",
        "revision_value": "abc123-private-revision",
        "revision_evidence_ref": "revision:local-git",
        "producer_kind": "researchos",
        "producer_surface": "local_command",
        "evidence_class": "server_recorded",
        "last_judgment": {
            "state": "candidate", "text": "The claim still needs source-level verification.",
            "evidence_ref": "result:run-1",
        },
        "open_boundary": {
            "state": "recorded", "text": "The external-validity boundary remains unresolved.",
            "evidence_ref": "ctx:boundary",
        },
        "next_safe_action": {
            "state": "recommended", "text": "Inspect the exact source revision before editing.",
            "evidence_ref": "ctx:next-action",
        },
        "forbidden_actions": {
            "state": "recorded", "items": ["Do not promote the candidate to canonical memory."],
            "evidence_ref": "policy:admission-boundary",
        },
        "target_client": {"kind": "codex", "surface": "desktop"},
    }
    arguments.update(overrides)
    return build_handoff_receipt(**arguments)  # type: ignore[arg-type]


class HandoffReceiptTest(unittest.TestCase):
    def test_build_is_deterministic_and_omits_transcript_and_raw_source_identity(self) -> None:
        first = handoff()
        second = handoff()
        rendered = json.dumps(first, ensure_ascii=False)
        self.assertEqual(first, second)
        self.assertEqual(HANDOFF_RECEIPT_SCHEMA_ID, first["schema_id"])
        self.assertRegex(first["handoff_id"], r"^handoff:[0-9a-f]{64}$")
        self.assertNotIn("private/path.md", rendered)
        self.assertNotIn("Private label", rendered)
        self.assertNotIn("abc123-private-revision", rendered)
        self.assertFalse({"transcript", "history", "messages", "prompt"} & set(first))

    def test_revision_or_semantic_change_changes_handoff_identity(self) -> None:
        baseline = handoff()
        revised = handoff(revision_value="different-revision")
        changed_action = handoff(next_safe_action={
            "state": "recommended", "text": "Inspect the counterexample first.",
            "evidence_ref": "ctx:next-action",
        })
        self.assertNotEqual(baseline["handoff_id"], revised["handoff_id"])
        self.assertNotEqual(baseline["handoff_id"], changed_action["handoff_id"])

    def test_source_revision_must_belong_to_exact_context_receipt(self) -> None:
        with self.assertRaises(HandoffReceiptContractError) as failure:
            handoff(source_id="src:" + "f" * 64)
        self.assertEqual("handoff_receipt_source_not_in_context", failure.exception.code)

    def test_untrusted_claims_degrade_to_unknown_without_gaining_authority(self) -> None:
        forged = handoff()
        forged["producer"]["evidence_class"] = "human_attested"  # type: ignore[index]
        normalized = normalize_handoff_receipt(forged)
        self.assertEqual("client_asserted", normalized["producer"]["evidence_class"])  # type: ignore[index]
        self.assertEqual("unknown", normalized["source_revision"]["state"])  # type: ignore[index]
        self.assertEqual("claimed", normalized["context_receipt_ref"]["binding_state"])  # type: ignore[index]
        self.assertEqual("unknown", normalized["last_judgment"]["state"])  # type: ignore[index]
        self.assertEqual("unknown", normalized["open_boundary"]["state"])  # type: ignore[index]
        self.assertEqual("unknown", normalized["next_safe_action"]["state"])  # type: ignore[index]
        self.assertEqual("unknown", normalized["forbidden_actions"]["state"])  # type: ignore[index]
        self.assertEqual(6, len(normalized["rejected_claims"]))

    def test_target_client_is_only_a_request_not_delivery_or_adoption_proof(self) -> None:
        receipt = handoff(target_client={"kind": "editor", "surface": "extension"})
        target = receipt["target_client"]
        self.assertEqual({"kind": "editor", "surface": "extension", "binding_state": "requested"}, target)
        rendered = json.dumps(target)
        self.assertNotIn("delivered", rendered)
        self.assertNotIn("observed", rendered)
        self.assertNotIn("accepted", rendered)

    def test_unknown_or_recorded_content_without_evidence_fails_closed(self) -> None:
        unknown_with_text = handoff()
        unknown_with_text["open_boundary"] = {"state": "unknown", "text": "forged", "evidence_ref": ""}
        with self.assertRaises(HandoffReceiptContractError) as unknown_failure:
            normalize_handoff_receipt(unknown_with_text, trusted_producer=True)
        self.assertEqual("handoff_receipt_unknown_has_content", unknown_failure.exception.code)
        missing_evidence = handoff()
        missing_evidence["next_safe_action"]["evidence_ref"] = ""  # type: ignore[index]
        with self.assertRaises(HandoffReceiptContractError) as evidence_failure:
            normalize_handoff_receipt(missing_evidence, trusted_producer=True)
        self.assertEqual("handoff_receipt_evidence_required", evidence_failure.exception.code)

    def test_human_recorded_judgment_is_explicit_and_never_inferred(self) -> None:
        candidate = handoff()
        human = handoff(last_judgment={
            "state": "human_recorded", "text": "Keep this as a candidate until replication.",
            "evidence_ref": "decision:human-1",
        })
        self.assertEqual("candidate", candidate["last_judgment"]["state"])  # type: ignore[index]
        self.assertEqual("human_recorded", human["last_judgment"]["state"])  # type: ignore[index]
        self.assertNotEqual(candidate["handoff_id"], human["handoff_id"])
        with self.assertRaises(HandoffReceiptContractError) as missing_decision:
            handoff(last_judgment={
                "state": "human_recorded", "text": "Pretend this was confirmed.",
                "evidence_ref": "result:agent-only",
            })
        self.assertEqual("handoff_receipt_human_decision_required", missing_decision.exception.code)

    def test_all_runtime_scopes_are_explicit_and_do_not_change_source_identity(self) -> None:
        receipts = []
        for scope in ("private", "public_starter", "personal_vault"):
            context = build_requested_context_receipt(
                task_id="task:" + "a" * 64, run_id="run-1", runtime_scope=scope,
                producer_kind="cli", producer_surface="terminal",
                source_refs=[{"kind": "file", "ref": "bounded/source.md", "label": "Source"}],
            )
            receipts.append(handoff(context_receipt=context, source_id=context["sources"][0]["source_id"]))  # type: ignore[index]
        self.assertEqual(["private", "public_starter", "personal_vault"], [item["runtime_scope"] for item in receipts])
        self.assertEqual(1, len({item["source_revision"]["source_id"] for item in receipts}))  # type: ignore[index]
        self.assertEqual(3, len({item["handoff_id"] for item in receipts}))

    def test_schema_vocabulary_and_owner_shape_match(self) -> None:
        schema = json.loads(
            (ROOT / "09_templates/data_contracts/researchos-handoff-receipt-v1.schema.json").read_text(encoding="utf-8")
        )
        receipt = handoff()
        self.assertEqual(HANDOFF_RECEIPT_SCHEMA_ID, schema["properties"]["schema_id"]["const"])
        self.assertEqual(set(schema["required"]), set(receipt))
        self.assertEqual(REVISION_SCHEMES, frozenset(
            schema["properties"]["source_revision"]["allOf"][1]["then"]["properties"]["scheme"]["enum"]
        ))
        self.assertEqual("requested", schema["properties"]["target_client"]["properties"]["binding_state"]["const"])

    def test_extra_fields_cannot_smuggle_authority_or_transcript(self) -> None:
        forged = copy.deepcopy(handoff())
        forged["authorization"] = {"state": "granted"}
        with self.assertRaises(HandoffReceiptContractError) as authority_failure:
            normalize_handoff_receipt(forged, trusted_producer=True)
        self.assertEqual("handoff_receipt_invalid_shape", authority_failure.exception.code)
        forged = copy.deepcopy(handoff())
        forged["transcript"] = ["secret"]
        with self.assertRaises(HandoffReceiptContractError):
            normalize_handoff_receipt(forged, trusted_producer=True)


if __name__ == "__main__":
    unittest.main()
