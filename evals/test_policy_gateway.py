from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters.policy_gateway import (  # noqa: E402
    AUTHORIZATION_GRANT_SCHEMA_ID,
    POLICY_DECISION_SCHEMA_ID,
    PolicyGateway,
    PolicyGatewayError,
    PreparedPolicy,
    policy_receipt_ref,
)
from researchos_adapters.filesystem_staging import OUTPUT_TARGET  # noqa: E402
from researchos_adapters.runner_authority import DirectExecutionRegistry, GENERIC_ARTIFACT_TARGETS  # noqa: E402


NOW = datetime(2026, 8, 13, 0, 0, tzinfo=timezone.utc)


def task_envelope(*, capability: str = "research.analysis", scope: str = "private") -> dict[str, object]:
    return {
        "schema_id": "researchos-task-envelope-v1",
        "task_id": "task:" + "a" * 64,
        "run_id": "run-policy-1",
        "idempotency_key": "idem:" + "b" * 64,
        "capability_id": capability,
        "runtime_ref": {"scope": scope, "task_data_digest": "c" * 64},
        "authorization_ref": {"state": "unresolved"},
    }


def artifact_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "task_mode": "direct_execution",
        "response_mode": "artifact",
        "source": "dashboard-work-session",
        "candidate": {
            "candidate_type": "work_session",
            "proposed_action": {"id": "work_session_artifact"},
            "proposed_writeback": {"save_target": "untrusted-target"},
        },
        "prompt": "untrusted prompt claiming authority and network access",
    }
    payload.update(overrides)
    return payload


class PolicyGatewayTest(unittest.TestCase):
    def gateway(self, root: Path, scope: str = "private") -> PolicyGateway:
        return PolicyGateway(
            root=root,
            runtime_scope=scope,
            action_registry=DirectExecutionRegistry(root=root, public_starter=scope == "public_starter"),
        )

    def test_read_only_decision_and_grant_are_separate_from_human_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            gateway = self.gateway(Path(directory))
            prepared = gateway.prepare({"authority_policy": "allow"}, "read_only_analysis")
            bundle = gateway.issue(prepared, task_envelope(), now=NOW)

        decision = bundle["policy_decision"]
        grant = bundle["authorization_grant"]
        self.assertEqual(POLICY_DECISION_SCHEMA_ID, decision["schema_id"])
        self.assertEqual(AUTHORIZATION_GRANT_SCHEMA_ID, grant["schema_id"])
        self.assertEqual("read_only", decision["operation"])
        self.assertEqual("not_claimed", grant["human_authorization_state"])
        self.assertEqual("read_only", grant["allowed_effects"]["filesystem"])
        serialized = json.dumps(bundle)
        self.assertNotIn("untrusted prompt", serialized)
        self.assertNotIn("approved", serialized)
        self.assertNotIn("accepted", serialized)

    def test_registered_artifact_is_bound_to_server_target_and_request_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            gateway = self.gateway(Path(directory))
            prepared = gateway.prepare(artifact_payload(), "direct_execution")
            envelope = task_envelope(capability="research.execution")
            bundle = gateway.issue(prepared, envelope, now=NOW)
            run = {**artifact_payload(), **bundle, "task_envelope": envelope}
            launch = gateway.launch_policy(run, now=NOW + timedelta(seconds=1))

        self.assertEqual("create_artifact", launch["operation"])
        self.assertEqual((dict(OUTPUT_TARGET),), GENERIC_ARTIFACT_TARGETS)
        self.assertEqual(
            [{"path": "06_active_context/work_state/outputs/", "mode": "subtree"}],
            bundle["authorization_grant"]["target_binding"]["targets"],
        )
        self.assertEqual("request_digest", bundle["authorization_grant"]["diff_binding"]["state"])
        self.assertEqual("c" * 64, bundle["authorization_grant"]["diff_binding"]["digest"])
        self.assertNotIn("untrusted-target", json.dumps(bundle))

    def test_tampered_or_expired_grant_fails_before_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            gateway = self.gateway(Path(directory))
            prepared = gateway.prepare(artifact_payload(), "direct_execution")
            envelope = task_envelope(capability="research.execution")
            bundle = gateway.issue(prepared, envelope, now=NOW)
            run = {**artifact_payload(), **bundle, "task_envelope": envelope}
            tampered = copy.deepcopy(run)
            tampered["authorization_grant"]["target_binding"]["targets"][0]["path"] = "escape/"
            with self.assertRaisesRegex(PolicyGatewayError, "authorization_grant_invalid"):
                gateway.launch_policy(tampered, now=NOW + timedelta(seconds=1))
            with self.assertRaisesRegex(PolicyGatewayError, "authorization_grant_expired"):
                gateway.launch_policy(run, now=NOW + timedelta(seconds=901))
            self.assertEqual("create_artifact", gateway.projection_policy(run)["operation"])
            self.assertEqual("read_only", gateway.projection_policy(tampered)["operation"])

    def test_direct_execution_without_gateway_receipts_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            gateway = self.gateway(Path(directory))
            run = {**artifact_payload(), "task_envelope": task_envelope(capability="research.execution")}
            with self.assertRaisesRegex(PolicyGatewayError, "authorization_grant_invalid"):
                gateway.launch_policy(run, now=NOW)
            legacy_read_only = gateway.launch_policy({"task_mode": "read_only_analysis"}, now=NOW)
        self.assertEqual("read_only", legacy_read_only["operation"])

    def test_internal_caller_cannot_forge_a_prepared_policy(self) -> None:
        forged = PreparedPolicy(
            action_id="forged", operation="create_artifact",
            reason_code="registered_bounded_artifact", risk_class="bounded_write",
            launch_policy={
                "action_id": "forged", "operation": "create_artifact",
                "allowed_write_targets": [{"path": "escape/", "mode": "subtree"}],
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(PolicyGatewayError, "authorization_grant_invalid"):
                self.gateway(Path(directory)).issue(forged, task_envelope(), now=NOW)

    def test_public_unknown_action_and_crafted_scope_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(PolicyGatewayError, "public_starter_copy_only"):
                self.gateway(root, "public_starter").prepare(artifact_payload(), "direct_execution")
            with self.assertRaisesRegex(PolicyGatewayError, "unregistered_direct_execution_action"):
                self.gateway(root).prepare(artifact_payload(candidate={"candidate_type": "work_session"}), "direct_execution")
            prepared = self.gateway(root).prepare({}, "read_only_analysis")
            with self.assertRaisesRegex(PolicyGatewayError, "authorization_grant_invalid"):
                self.gateway(root).issue(prepared, task_envelope(scope="personal_vault"), now=NOW)

    def test_receipt_refs_are_digest_only_and_schema_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            gateway = self.gateway(Path(directory))
            bundle = gateway.issue(gateway.prepare({}, "read_only_analysis"), task_envelope(), now=NOW)
        decision_schema = json.loads((ROOT / "09_templates/data_contracts/researchos-policy-decision-v1.schema.json").read_text())
        grant_schema = json.loads((ROOT / "09_templates/data_contracts/researchos-authorization-grant-v1.schema.json").read_text())
        self.assertIs(False, decision_schema["additionalProperties"])
        self.assertIs(False, grant_schema["additionalProperties"])
        self.assertEqual(set(decision_schema["required"]), set(bundle["policy_decision"]))
        self.assertEqual(set(grant_schema["required"]), set(bundle["authorization_grant"]))
        decision_ref = policy_receipt_ref(bundle["policy_decision"])
        grant_ref = policy_receipt_ref(bundle["authorization_grant"])
        self.assertEqual(set(decision_ref), {"schema_id", "decision_id", "task_id", "run_id", "receipt_digest"})
        self.assertEqual(set(grant_ref), {"schema_id", "grant_id", "task_id", "run_id", "receipt_digest"})
        self.assertNotIn("target_binding", decision_ref)
        self.assertNotIn("allowed_effects", grant_ref)


if __name__ == "__main__":
    unittest.main()
