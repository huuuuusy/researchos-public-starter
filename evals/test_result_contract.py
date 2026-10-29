from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_kernel.result_contract import (  # noqa: E402
    ERROR_ENVELOPE_SCHEMA_ID,
    RESULT_ENVELOPE_SCHEMA_ID,
    build_error_envelope,
    build_result_envelope,
    failure_response,
    normalize_error_envelope,
    result_projection,
)


def run_fixture(**overrides: object) -> dict[str, object]:
    run: dict[str, object] = {
        "id": "run-1",
        "status": "completed",
        "response_mode": "answer",
        "answer": "Grounded answer",
        "provider": "codex",
        "model": "gpt-test",
        "reasoning_effort": "medium",
        "task_complexity": "standard",
        "created_at": "2026-08-12T10:00:00+08:00",
        "started_at": "2026-08-12T10:00:01+08:00",
        "finished_at": "2026-08-12T10:00:02+08:00",
        "seconds": 1,
        "usage": {"input_tokens": 5, "output_tokens": 2},
        "task_envelope": {
            "schema_id": "researchos-task-envelope-v1",
            "task_id": "task:" + "a" * 64,
            "run_id": "run-1",
            "client": {"request_id": "request-1"},
        },
    }
    run.update(overrides)
    return run


class ResultContractTest(unittest.TestCase):
    def assert_exact_schema_keys(self, value: dict[str, object], schema: dict[str, object]) -> None:
        self.assertEqual(set(schema["required"]), set(value))

    def test_error_is_public_safe_and_retry_requires_proven_zero_effects(self) -> None:
        secret = "sensitive-diagnostic::token=secret"
        envelope = build_error_envelope(
            "transport_delivery_unknown", run={"id": ""}, retryable=True,
            side_effects="unknown", recovery_action="retry_same",
        )
        self.assertEqual(ERROR_ENVELOPE_SCHEMA_ID, envelope["schema_id"])
        self.assertRegex(envelope["error_id"], r"^error:server:[0-9a-f]{64}$")
        self.assertFalse(envelope["retryable"])
        self.assertEqual("unknown", envelope["side_effects"])
        self.assertNotIn(secret, json.dumps(envelope))

        safe_retry = build_error_envelope(
            "client_request_invalid", retryable=True, side_effects="none", recovery_action="retry_same"
        )
        self.assertTrue(safe_retry["retryable"])

    def test_failure_adapter_drops_raw_message_and_preserves_safe_legacy_refs(self) -> None:
        response = failure_response({
            "error_type": "unknown_provider",
            "message": "secret path sensitive-diagnostic::private",
            "field": "requested_profile.provider",
            "provider_status": {"error_type": "unknown_provider", "provider": "missing"},
        })
        serialized = json.dumps(response)
        self.assertFalse(response["ok"])
        self.assertEqual("unknown_provider", response["error_type"])
        self.assertEqual("requested_profile.provider", response["field"])
        self.assertNotIn("sensitive-diagnostic::private", serialized)
        self.assertEqual("unknown_provider", response["provider_status"]["error_type"])

    def test_completed_modes_are_discriminated_and_never_admit_authority(self) -> None:
        cases = {
            "answer": run_fixture(),
            "artifact": run_fixture(
                response_mode="artifact",
                artifacts=[{"kind": "file", "path": "06_active_context/work_state/outputs/a.md"}],
            ),
            "writeback": run_fixture(
                response_mode="writeback", candidate={"candidate_id": "candidate:one"}
            ),
        }
        for mode, run in cases.items():
            with self.subTest(mode=mode):
                envelope = build_result_envelope(run, runtime_scope="private")
                assert envelope is not None
                self.assertEqual(RESULT_ENVELOPE_SCHEMA_ID, envelope["schema_id"])
                self.assertEqual("completed", envelope["status"])
                self.assertEqual(mode, envelope["result_mode"])
                self.assertEqual(mode, envelope["result"]["kind"])
                serialized = json.dumps(envelope)
                for forbidden in ("authority", "approved", "validated", "applied", "confirmed"):
                    self.assertNotIn(forbidden, serialized)
        artifact = build_result_envelope(cases["artifact"], runtime_scope="private")
        assert artifact is not None
        self.assertEqual("reported", artifact["result"]["reported_refs"][0]["state"])
        writeback = build_result_envelope(cases["writeback"], runtime_scope="private")
        assert writeback is not None
        self.assertEqual("reported", writeback["result"]["candidate_refs"][0]["state"])

    def test_nonterminal_and_failed_runs_do_not_become_machine_results(self) -> None:
        for status in ("submitted", "queued", "running", "failed"):
            with self.subTest(status=status):
                self.assertIsNone(build_result_envelope(run_fixture(status=status), runtime_scope="private"))
        with self.assertRaisesRegex(ValueError, "handoff"):
            build_result_envelope(run_fixture(response_mode="copy_ready"), runtime_scope="private")

    def test_failed_projection_strips_raw_result_and_emits_error(self) -> None:
        projected = result_projection(run_fixture(
            status="failed", error_type="runner_execution_failed",
            answer="secret answer", output="secret output", artifacts=["secret.md"],
        ), runtime_scope="private")
        self.assertEqual("", projected["answer"])
        self.assertEqual("", projected["output"])
        self.assertEqual([], projected["artifacts"])
        self.assertNotIn("result_envelope", projected)
        self.assertEqual("runner_execution_failed", projected["error_envelope"]["error_type"])

    def test_projection_warning_does_not_erase_primary_result(self) -> None:
        envelope = build_result_envelope(run_fixture(
            post_run_refresh={"ok": False, "error_type": "post_run_refresh_failed", "output": "secret"}
        ), runtime_scope="personal_vault")
        assert envelope is not None
        self.assertEqual("Grounded answer", envelope["result"]["text"])
        self.assertEqual("post_run_refresh_failed", envelope["warnings"][0]["error_type"])
        self.assertEqual(envelope["warnings"][0]["error_id"], envelope["error_ref"])
        self.assertNotIn("secret", json.dumps(envelope))

    def test_normalizer_rebuilds_invariants_instead_of_trusting_serialized_claims(self) -> None:
        crafted = build_error_envelope("transport_delivery_unknown")
        crafted.update({"retryable": True, "message": "secret", "recovery_action": "retry_same"})
        normalized = normalize_error_envelope(crafted)
        assert normalized is not None
        self.assertFalse(normalized["retryable"])
        self.assertEqual("inspect", normalized["recovery_action"])
        self.assertEqual("unknown", normalized["side_effects"])
        self.assertNotIn("secret", json.dumps(normalized))

    def test_serialized_high_risk_error_cannot_downgrade_policy(self) -> None:
        crafted = build_error_envelope("transport_delivery_unknown", run={"id": "run-1"})
        crafted.update({"side_effects": "none", "recovery_action": "retry_same", "retryable": True})
        normalized = normalize_error_envelope(crafted)
        assert normalized is not None
        self.assertEqual("unknown", normalized["side_effects"])
        self.assertEqual("inspect", normalized["recovery_action"])
        self.assertFalse(normalized["retryable"])

    def test_schemas_close_unknown_fields_and_result_union_is_explicit(self) -> None:
        error_schema = json.loads((ROOT / "09_templates/data_contracts/researchos-error-envelope-v1.schema.json").read_text())
        result_schema = json.loads((ROOT / "09_templates/data_contracts/researchos-result-envelope-v1.schema.json").read_text())
        self.assertIs(False, error_schema["additionalProperties"])
        self.assertIs(False, result_schema["additionalProperties"])
        self.assertEqual("completed", result_schema["properties"]["status"]["const"])
        kinds = {branch["properties"]["kind"]["const"] for branch in result_schema["properties"]["result"]["oneOf"]}
        self.assertEqual({"answer", "artifact", "writeback"}, kinds)
        self.assertTrue(error_schema["allOf"], "retry and side-effect invariants must be machine-readable")
        self.assertEqual("researchos-error-envelope-v1.schema.json", result_schema["properties"]["warnings"]["items"]["$ref"])
        linked_modes = {
            rule["if"]["properties"]["result_mode"]["const"]
            for rule in result_schema["allOf"]
        }
        self.assertEqual({"answer", "artifact", "writeback"}, linked_modes)
        self.assert_exact_schema_keys(build_error_envelope("unknown_provider"), error_schema)
        result = build_result_envelope(run_fixture(), runtime_scope="private")
        assert result is not None
        self.assert_exact_schema_keys(result, result_schema)


if __name__ == "__main__":
    unittest.main()
