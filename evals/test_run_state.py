import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters.run_state import (  # noqa: E402
    RUN_STATE_SCHEMA_ID,
    RunStateError,
    RunStateLedger,
    run_lease_expired,
)


def run_record(run_id: str = "run-1", request_id: str = "request-1", *, status: str = "queued") -> dict[str, object]:
    return {
        "id": run_id,
        "status": status,
        "created_at": "2026-08-13T10:00:00+00:00",
        "updated_at": "2026-08-13T10:00:00+00:00",
        "task_envelope": {
            "schema_id": "researchos-task-envelope-v1",
            "task_id": "task:" + "a" * 64,
            "run_id": run_id,
            "idempotency_key": "idem:" + "b" * 64,
            "client": {"request_id": request_id},
        },
    }


class RunStateTest(unittest.TestCase):
    def ledger(self, root: Path, scope: str = "private") -> RunStateLedger:
        return RunStateLedger(root / "state.jsonl", root / "events.jsonl", scope)

    def test_reservation_replays_same_execution_and_rejects_request_rebinding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = self.ledger(root)
            kind, first = ledger.reserve(run_record())
            self.assertEqual("reserved", kind)
            self.assertEqual("submitted", first["state"])
            kind, replay = ledger.reserve(run_record("run-2"))
            self.assertEqual("replay", kind)
            self.assertEqual("run-1", replay["run_id"])
            forged = run_record("run-3")
            forged["task_envelope"]["idempotency_key"] = "idem:" + "c" * 64  # type: ignore[index]
            with self.assertRaisesRegex(RunStateError, "run_request_conflict"):
                ledger.reserve(forged)

    def test_claim_is_single_dispatch_and_terminal_state_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = self.ledger(root)
            ledger.reserve(run_record())
            ledger.observe(run_record(status="queued"))
            self.assertTrue(ledger.claim_dispatch("run-1"))
            self.assertFalse(ledger.claim_dispatch("run-1"))
            completed = run_record(status="completed")
            completed["updated_at"] = "2026-08-13T10:00:01+00:00"
            ledger.observe(completed)
            with self.assertRaisesRegex(RunStateError, "run_state_transition_invalid"):
                ledger.observe({**completed, "status": "running", "updated_at": "2026-08-13T10:00:02+00:00"})

    def test_exact_reconcile_survives_restart_and_scope_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = self.ledger(root, "personal_vault")
            run = run_record()
            ledger.reserve(run)
            ledger.observe(run)
            restarted = self.ledger(root, "personal_vault")
            result = restarted.reconcile(client_request_id="request-1")
            self.assertEqual("matched", result["state"])
            self.assertEqual("run-1", result["run_id"])
            self.assertEqual("not_found", restarted.reconcile(client_request_id="missing")["state"])
            with self.assertRaisesRegex(RunStateError, "run_ledger_corrupt"):
                self.ledger(root, "private").reconcile(client_request_id="request-1")

    def test_corrupt_or_symlinked_ledger_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            ledger = self.ledger(root)
            ledger.path.write_text("not-json\n", encoding="utf-8")
            with self.assertRaisesRegex(RunStateError, "run_ledger_corrupt"):
                ledger.reconcile(client_request_id="request-1")
            ledger.path.unlink()
            target = Path(outside) / "state.jsonl"
            target.write_text("", encoding="utf-8")
            ledger.path.symlink_to(target)
            with self.assertRaisesRegex(RunStateError, "run_ledger_path_invalid"):
                ledger.reconcile(client_request_id="request-1")

    def test_events_without_an_idempotency_identity_never_reach_the_state_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = self.ledger(root)
            older = {"id": "run-old", "status": "completed", "created_at": "2026-08-03T10:00:00+00:00"}
            ledger.event_log.write_text(json.dumps(older) + "\n", encoding="utf-8")
            ledger.reserve(run_record())
            self.assertTrue(ledger.claim_dispatch("run-1"), "the next strict read must accept what reserve wrote")
            self.assertNotIn("run-old", ledger.path.read_text(encoding="utf-8"))

    def test_ambiguous_or_missing_correlation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = self.ledger(root)
            first = run_record()
            second = run_record("run-2")
            second["task_envelope"]["idempotency_key"] = "idem:" + "c" * 64  # type: ignore[index]
            ledger.path.write_text("\n".join(json.dumps({
                "schema_id": RUN_STATE_SCHEMA_ID, "runtime_scope": "private",
                "client_request_id": "request-1", "idempotency_key": value["task_envelope"]["idempotency_key"],
                "run_id": value["id"], "task_id": "task:" + "a" * 64, "state": "queued",
                "side_effects": "none", "created_at": value["created_at"], "updated_at": value["updated_at"],
            }) for value in (first, second)) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RunStateError, "run_reconcile_ambiguous"):
                ledger.reconcile(client_request_id="request-1")
            with self.assertRaisesRegex(RunStateError, "run_reconcile_invalid"):
                ledger.reconcile()

    def test_lease_expiry_is_observation_not_terminal_mutation(self) -> None:
        run = {"status": "running", "updated_at": "2026-08-13T10:00:00+00:00"}
        now = datetime(2026, 8, 13, 10, 3, tzinfo=timezone.utc)
        self.assertTrue(run_lease_expired(run, 60, grace_seconds=60, now=now))
        self.assertFalse(run_lease_expired({**run, "status": "completed"}, 60, now=now))

    def test_schema_matches_ledger_vocabulary(self) -> None:
        schema = json.loads((ROOT / "09_templates/data_contracts/researchos-run-state-v1.schema.json").read_text())
        self.assertEqual(RUN_STATE_SCHEMA_ID, schema["properties"]["schema_id"]["const"])
        self.assertEqual({"private", "personal_vault"}, set(schema["properties"]["runtime_scope"]["enum"]))
        self.assertEqual({"submitted", "queued", "running", "completed", "failed"}, set(schema["properties"]["state"]["enum"]))


if __name__ == "__main__":
    unittest.main()
