from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_kernel.task_envelope import (  # noqa: E402
    MAX_LEGACY_INSTRUCTION_LENGTH,
    MAX_NESTED_INSTRUCTION_LENGTH,
    MAX_SOURCE_REFS,
    REASONING_EFFORTS,
    RESULT_MODES,
    TASK_COMPLEXITIES,
    TASK_ENVELOPE_SCHEMA_ID,
    TASK_INTENT_SCHEMA_ID,
    TaskEnvelopeContractError,
    build_task_envelope,
    normalize_task_intent,
    normalize_task_intent_result,
    task_envelope_ref,
)


def assert_schema_shape(test: unittest.TestCase, value: object, schema: dict[str, object], path: str = "$") -> None:
    if "const" in schema:
        test.assertEqual(schema["const"], value, path)
    if "enum" in schema:
        test.assertIn(value, schema["enum"], path)
    kind = schema.get("type")
    if kind == "object":
        test.assertIsInstance(value, dict, path)
        assert isinstance(value, dict)
        properties = schema.get("properties", {})
        test.assertTrue(set(schema.get("required", [])).issubset(value), path)
        if schema.get("additionalProperties") is False:
            test.assertEqual(set(value), set(properties), path)
        for key, item in value.items():
            assert_schema_shape(test, item, properties[key], f"{path}.{key}")
    elif kind == "array":
        test.assertIsInstance(value, list, path)
        assert isinstance(value, list)
        test.assertLessEqual(len(value), int(schema.get("maxItems", len(value))), path)
        for index, item in enumerate(value):
            assert_schema_shape(test, item, schema["items"], f"{path}[{index}]")
    elif kind == "string":
        test.assertIsInstance(value, str, path)
        assert isinstance(value, str)
        test.assertGreaterEqual(len(value), int(schema.get("minLength", 0)), path)
        test.assertLessEqual(len(value), int(schema.get("maxLength", len(value))), path)
        if "pattern" in schema:
            test.assertRegex(value, re.compile(str(schema["pattern"])), path)


def canonical_intent(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_id": TASK_INTENT_SCHEMA_ID,
        "input_trust": "untrusted",
        "goal": "Audit one claim",
        "instruction": "Read evidence, then explain the boundary.",
        "client_request_id": "request-1",
        "client": {"kind": "codex", "surface": "desktop", "task_ref": "client-task-42"},
        "requested_result": {"mode": "answer"},
        "requested_profile": {
            "provider": "openai_compatible", "model": "requested-model",
            "reasoning_effort": "high", "task_complexity": "deep",
        },
        "client_hints": {
            "recommended_reasoning_effort": "medium", "recommended_task_complexity": "standard",
        },
        "source_refs": [{"kind": "object", "ref": "notes/two  spaces.md", "label": "Evidence"}],
    }
    value.update(overrides)
    return value


def trusted_run(run_id: str = "run-1", **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": run_id,
        "task_mode": "read_only_analysis",
        "response_mode": "answer",
        "work_session_id": "session-1",
        "provider": "codex",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "medium",
        "task_complexity": "standard",
        "prompt": "Exact provider prompt",
    }
    value.update(overrides)
    return value


class TaskEnvelopeContractTest(unittest.TestCase):
    def test_nested_intent_is_strict_lossless_and_deterministic(self) -> None:
        raw = canonical_intent(
            instruction="Line one\r\n```python\r\n  x =  1\r\n```",
            source_refs=[
                {"kind": "object", "ref": "notes/two  spaces.md", "label": "Evidence"},
                {"kind": "object", "ref": "notes/two  spaces.md", "label": "Evidence"},
            ],
        )
        normalized = normalize_task_intent({"task_intent": raw, "prompt": "must not replace nested"})

        self.assertEqual(normalized, normalize_task_intent({"task_intent": raw}))
        self.assertEqual("nested", normalized.origin)
        self.assertEqual("Line one\n```python\n  x =  1\n```", normalized["instruction"])
        self.assertEqual("notes/two  spaces.md", normalized["source_refs"][0]["ref"])
        self.assertEqual(1, len(normalized["source_refs"]))

    def test_nested_invalid_never_falls_back_and_unsupported_values_are_visible(self) -> None:
        invalid = canonical_intent()
        invalid["authorization_ref"] = {"state": "granted"}
        normalized, error = normalize_task_intent_result({"task_intent": invalid, "prompt": "legacy fallback"})
        self.assertIsNone(normalized)
        self.assertEqual("task_intent_invalid_shape", error["error_type"])
        self.assertNotIn("legacy fallback", json.dumps(error))

        unsupported = canonical_intent(
            requested_profile={
                "provider": "auto", "model": "auto", "reasoning_effort": "root", "task_complexity": "standard",
            }
        )
        _, error = normalize_task_intent_result({"task_intent": unsupported})
        self.assertEqual("unsupported_reasoning_effort", error["error_type"])
        self.assertEqual("requested_profile.reasoning_effort", error["field"])

    def test_nested_code_point_limit_matches_schema_and_rejects_nul(self) -> None:
        accepted = normalize_task_intent({"task_intent": canonical_intent(instruction="😀" * 40000)})
        self.assertEqual(40000, len(accepted["instruction"]))
        for instruction, code in (
            ("x" * (MAX_NESTED_INSTRUCTION_LENGTH + 1), "task_intent_input_too_large"),
            ("before\x00after", "task_intent_invalid_character"),
        ):
            with self.subTest(code=code):
                _, error = normalize_task_intent_result({"task_intent": canonical_intent(instruction=instruction)})
                self.assertEqual(code, error["error_type"])

    def test_legacy_adapter_preserves_previous_prompt_and_twenty_source_refs(self) -> None:
        prompt = "x" * MAX_LEGACY_INSTRUCTION_LENGTH
        source_refs = [
            {"kind": "object", "value": f"source-{index}", "title": f"Source {index}"}
            for index in range(MAX_SOURCE_REFS)
        ]
        normalized = normalize_task_intent({
            "prompt": prompt,
            "response_mode": "answer",
            "work_session_id": "legacy-session",
            "candidate": {"source_refs": source_refs},
        })

        self.assertEqual("legacy", normalized.origin)
        self.assertEqual(prompt, normalized["instruction"])
        self.assertEqual(MAX_SOURCE_REFS, len(normalized["source_refs"]))
        self.assertEqual("source-19", normalized["source_refs"][-1]["ref"])

    def test_build_requires_typed_normalized_input_and_revalidates_it(self) -> None:
        with self.assertRaises(TaskEnvelopeContractError) as untrusted:
            build_task_envelope(
                canonical_intent(), run=trusted_run(), runtime_scope="private", idempotency_namespace="fixture"  # type: ignore[arg-type]
            )
        self.assertEqual("task_envelope_untrusted_intent", untrusted.exception.code)

        normalized = normalize_task_intent({"task_intent": canonical_intent()})
        normalized.value["requested_result"] = {"mode": "delete"}
        with self.assertRaises(TaskEnvelopeContractError) as mutated:
            build_task_envelope(
                normalized, run=trusted_run(), runtime_scope="private", idempotency_namespace="fixture"
            )
        self.assertEqual("unsupported_result_mode", mutated.exception.code)

    def test_envelope_separates_requested_values_from_trusted_runtime_facts(self) -> None:
        envelope = build_task_envelope(
            normalize_task_intent({"task_intent": canonical_intent()}),
            run=trusted_run(),
            runtime_scope="private",
            idempotency_namespace="fixture-private-runtime",
        )

        self.assertEqual(TASK_ENVELOPE_SCHEMA_ID, envelope["schema_id"])
        self.assertEqual("researchos-task-intent-v1", envelope["intent"]["schema_id"])
        self.assertEqual("untrusted", envelope["intent"]["input_trust"])
        self.assertRegex(envelope["intent"]["digest"], r"^[0-9a-f]{64}$")
        self.assertEqual("openai_compatible", envelope["request_ref"]["provider"])
        self.assertEqual("openai_compatible", envelope["request_ref"]["profile_id"])
        self.assertEqual("requested-model", envelope["request_ref"]["model"])
        self.assertEqual("codex", envelope["runtime_ref"]["provider"])
        self.assertEqual("codex", envelope["runtime_ref"]["profile_id"])
        self.assertEqual("gpt-5.6-sol", envelope["runtime_ref"]["model"])
        self.assertEqual("private", envelope["runtime_ref"]["scope"])
        self.assertRegex(envelope["runtime_ref"]["task_data_digest"], r"^[0-9a-f]{64}$")
        self.assertEqual("requested", envelope["context_ref"]["source_state"])
        self.assertEqual("researchos-context-receipt-v1", envelope["context_ref"]["receipt"]["schema_id"])
        self.assertEqual(envelope["task_id"], envelope["context_ref"]["receipt"]["task_id"])
        self.assertEqual("unknown", envelope["context_ref"]["receipt"]["sources"][0]["delivery"]["state"])
        self.assertEqual({"state": "unresolved"}, envelope["authorization_ref"])
        self.assertNotIn("idempotency_state", envelope)

    def test_task_and_idempotency_identity_are_stable_only_for_same_execution(self) -> None:
        intent = normalize_task_intent({"task_intent": canonical_intent()})
        first = build_task_envelope(
            intent, run=trusted_run("run-1"), runtime_scope="private", idempotency_namespace="fixture"
        )
        retry = build_task_envelope(
            intent, run=trusted_run("run-2"), runtime_scope="private", idempotency_namespace="fixture"
        )
        self.assertEqual(first["task_id"], retry["task_id"])
        self.assertEqual(first["idempotency_key"], retry["idempotency_key"])
        self.assertNotEqual(first["run_id"], retry["run_id"])

        for changed_run in (
            trusted_run("run-3", provider="different"),
            trusted_run("run-4", model="different-model"),
            trusted_run("run-5", reasoning_effort="high"),
            trusted_run("run-6", task_complexity="deep"),
            trusted_run("run-7", prompt="Different provider prompt"),
            trusted_run("run-8", candidate={"summary": "Different candidate"}),
        ):
            changed = build_task_envelope(
                intent, run=changed_run, runtime_scope="private", idempotency_namespace="fixture"
            )
            self.assertNotEqual(first["task_id"], changed["task_id"])
            self.assertNotEqual(first["idempotency_key"], changed["idempotency_key"])

        without_request = normalize_task_intent({"task_intent": canonical_intent(client_request_id="")})
        no_key_first = build_task_envelope(
            without_request, run=trusted_run("run-1"), runtime_scope="private", idempotency_namespace="fixture"
        )
        no_key_retry = build_task_envelope(
            without_request, run=trusted_run("run-2"), runtime_scope="private", idempotency_namespace="fixture"
        )
        self.assertNotEqual(no_key_first["task_id"], no_key_retry["task_id"])

    def test_scope_is_server_fact_and_client_fields_cannot_override_it(self) -> None:
        crafted = canonical_intent(runtime_scope="private", authority_policy={"allow": True})
        normalized, error = normalize_task_intent_result({"task_intent": crafted})
        self.assertIsNone(normalized)
        self.assertEqual("task_intent_invalid_shape", error["error_type"])

        intent = normalize_task_intent({"task_intent": canonical_intent()})
        for scope in ("private", "public_starter", "personal_vault"):
            envelope = build_task_envelope(
                intent, run=trusted_run(), runtime_scope=scope, idempotency_namespace=f"fixture-{scope}"
            )
            self.assertEqual(scope, envelope["runtime_ref"]["scope"])
        with self.assertRaises(TaskEnvelopeContractError):
            build_task_envelope(intent, run=trusted_run(), runtime_scope="", idempotency_namespace="fixture")

    def test_retention_reference_is_not_a_second_envelope_state(self) -> None:
        envelope = build_task_envelope(
            normalize_task_intent({"task_intent": canonical_intent()}),
            run=trusted_run(),
            runtime_scope="private",
            idempotency_namespace="fixture",
        )
        reference = task_envelope_ref(envelope)
        self.assertEqual("request-1", reference["client_request_id"])
        self.assertEqual(envelope["task_id"], reference["task_id"])
        self.assertEqual(envelope["run_id"], reference["run_id"])
        self.assertRegex(reference["envelope_digest"], r"^[0-9a-f]{64}$")
        self.assertNotIn("schema_id", reference)
        self.assertNotIn("intent", reference)

    def test_schema_and_python_vocabulary_stay_aligned(self) -> None:
        schema = json.loads(
            (ROOT / "09_templates/data_contracts/researchos-task-envelope-v1.schema.json").read_text(encoding="utf-8")
        )
        properties = schema["properties"]
        self.assertEqual(TASK_ENVELOPE_SCHEMA_ID, properties["schema_id"]["const"])
        self.assertEqual(MAX_LEGACY_INSTRUCTION_LENGTH, properties["intent"]["properties"]["instruction"]["maxLength"])
        self.assertEqual(RESULT_MODES, frozenset(properties["result_mode"]["enum"]))
        self.assertEqual(REASONING_EFFORTS, frozenset(properties["request_ref"]["properties"]["reasoning_effort"]["enum"]))
        self.assertEqual(TASK_COMPLEXITIES, frozenset(properties["request_ref"]["properties"]["task_complexity"]["enum"]))
        self.assertEqual(MAX_SOURCE_REFS, properties["context_ref"]["properties"]["source_refs"]["maxItems"])
        self.assertEqual("unresolved", properties["authorization_ref"]["properties"]["state"]["const"])
        self.assertEqual(set(schema["required"]), set(properties))
        envelope = build_task_envelope(
            normalize_task_intent({"task_intent": canonical_intent()}),
            run=trusted_run(),
            runtime_scope="private",
            idempotency_namespace="schema-fixture",
        )
        assert_schema_shape(self, envelope, schema)

    def test_server_canonical_digests_are_the_kernel_digest(self) -> None:
        # Envelopes, receipts, plans and staging bind each other by these digests; one algorithm, pinned.
        from researchos_kernel.ledger import digest
        from researchos_adapters import filesystem_staging, policy_gateway
        from researchos_kernel import context_receipt, handoff_receipt, result_contract, rule_evolution, task_envelope
        from researchos_server import evolution_planner
        value = {"b": [1, 2.5, True, None], "a": "研究 é", "c": {"z": 1, "y": "x"}}
        expected = "925a92c996b51f2b4e3738d935e0a420f0ce7fe319770fab87937ca38e57e031"
        self.assertEqual(expected, digest(value))
        for helper in (context_receipt._digest, evolution_planner.stable_hash, filesystem_staging._json_digest,
                       handoff_receipt._digest, policy_gateway._digest, result_contract._digest,
                       rule_evolution._stable_hash, task_envelope._digest):
            self.assertEqual(expected, helper(value))


if __name__ == "__main__":
    unittest.main()
