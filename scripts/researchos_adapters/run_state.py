# ResearchOS maintenance header.
# 中文：运行状态、幂等保留、精确恢复与五轴合法组合的唯一 owner，与执行后端无关；不拥有 provider、结果内容或长期 authority。
# English: Sole owner of run state, idempotent reservation, exact reconciliation and legal five-axis combinations, independent of the executing backend; owns neither providers, result content, nor durable authority.

"""Durable local run-state and idempotency ledger."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from researchos_kernel.atomic_files import atomic_write_text, lock_path_for, runtime_state_transaction


RUN_STATE_SCHEMA_ID = "researchos-run-state-v1"
RUN_STATES = frozenset({"submitted", "queued", "running", "completed", "failed"})
TERMINAL_STATES = frozenset({"completed", "failed"})
_TRANSITIONS = {
    "submitted": frozenset({"submitted", "queued", "running", "failed"}),
    "queued": frozenset({"queued", "running", "failed"}),
    "running": frozenset({"running", "completed", "failed"}),
    "completed": frozenset({"completed"}),
    "failed": frozenset({"failed"}),
}
_STATE_RANK = {"submitted": 0, "queued": 1, "running": 2, "completed": 3, "failed": 3}
STATE_FILE = "run-state-current.jsonl"
LEGACY_STATE_FILE = "codex-runner-state-current.jsonl"  # read while it is the only copy; never written

# Five run axes (Kernel §2.1; Interaction Semantics Contract `state_axes`). A user-facing task state
# is only ever derived from a legal combination; no client keeps its own copy of these rules.
SESSION_STATES = ("none", "open", "ended")
RUN_AXIS_STATES = ("none", "submitted", "queued", "running", "completed", "failed")
OBSERVATION_STATES = ("none", "fresh", "delivery_unknown", "lease_expired", "reconcile_failed")
RESULT_STATES = ("none", "answer", "artifact", "writeback", "invalid")
ADMISSION_AXES = {
    "decision_state": ("unproposed", "proposed", "accepted", "revised", "rejected", "deferred"),
    "mutation_state": ("not_requested", "staged", "applied", "rolled_back"),
    "validation_state": ("unvalidated", "pending", "passed", "failed"),
    "authority_role": ("none", "informative", "interpretive", "normative"),
}
DERIVED_TASK_STATES = ("no_task", "ready", "running", "verify_delivery", "verify_run", "failed_retryable",
                       "failed_needs_impact_check", "result_ready", "late_result_ready", "ended",
                       "ended_with_run_tracking", "invalid")
ACTIVE_RUN = ("submitted", "queued", "running")
UNCERTAIN_OBSERVATION = ("delivery_unknown", "lease_expired", "reconcile_failed")
RESULT_ACTIONS = {
    "answer": ("finish_session", "add_followup", "copy_result", "propose_artifact", "propose_writeback"),
    "artifact": ("open_artifact", "finish_session", "copy_result", "propose_writeback"),
    "writeback": ("open_review", "finish_session", "copy_result"),
}


def _admission(snapshot: dict) -> dict:
    return {"decision_state": "unproposed", "mutation_state": "not_requested", "validation_state": "unvalidated",
            "authority_role": "none", **(snapshot.get("admission") or {})}


def validate_lifecycle(snapshot: dict) -> tuple:
    """Every rule a combination of the five axes breaks; empty means legal."""
    errors = []
    session, run = str(snapshot.get("session") or "none"), str(snapshot.get("run") or "none")
    observation, result = str(snapshot.get("observation") or "none"), str(snapshot.get("result") or "none")
    admission = _admission(snapshot)
    for axis, value, allowed in (("session", session, SESSION_STATES), ("run", run, RUN_AXIS_STATES),
                                 ("observation", observation, OBSERVATION_STATES), ("result", result, RESULT_STATES)):
        if value not in allowed:
            errors.append(f"unknown_{axis}:{value}")
    for dimension, allowed in ADMISSION_AXES.items():
        if admission[dimension] not in allowed:
            errors.append(f"unknown_admission_{dimension}:{admission[dimension]}")
    if session == "none" and (run != "none" or observation != "none" or result != "none"):
        errors.append("run_requires_session")
    if run == "none" and (observation != "none" or result != "none"):
        errors.append("observation_or_result_requires_run")
    if run in ACTIVE_RUN and observation not in ("fresh",) + UNCERTAIN_OBSERVATION:
        errors.append("active_run_requires_observation")
    if run in ACTIVE_RUN and result != "none":
        errors.append("active_run_cannot_have_result")
    if run in ("completed", "failed") and observation in UNCERTAIN_OBSERVATION:
        errors.append("terminal_run_cannot_have_uncertain_observation")
    if result not in ("none", "invalid") and run != "completed":
        errors.append("result_requires_completed_run")
    if run == "completed" and result == "none":
        errors.append("completed_run_requires_result")
    if run == "failed" and result not in ("none", "invalid"):
        errors.append("failed_run_cannot_have_valid_result")
    if result == "writeback" and admission["decision_state"] == "unproposed":
        errors.append("writeback_requires_proposed_admission")
    if result in ("answer", "artifact") and admission["decision_state"] != "unproposed":
        errors.append("non_writeback_result_cannot_claim_admission")
    if admission["decision_state"] not in ("accepted", "revised") and admission["mutation_state"] != "not_requested":
        errors.append("mutation_requires_accept_or_revise")
    if admission["mutation_state"] == "not_requested" and admission["validation_state"] != "unvalidated":
        errors.append("validation_requires_mutation")
    if admission["mutation_state"] == "staged" and admission["validation_state"] not in ("unvalidated", "pending"):
        errors.append("staged_validation_invalid")
    if admission["mutation_state"] == "applied" and admission["validation_state"] not in ("pending", "passed", "failed"):
        errors.append("applied_validation_invalid")
    return tuple(errors)


def derive_task_state(snapshot: dict) -> dict:
    """The one user-facing state of a legal combination, with its primary and allowed actions.

    A finished run does not end the session; a writeback result is not admission; an unknown or
    expired observation only offers checking, never resubmitting (Kernel §2.1, recovery_rules)."""
    errors = validate_lifecycle(snapshot)

    def present(state, primary, allowed=None, retry=False):
        return {"state": state, "primary_action": primary, "allowed_actions": list(dict.fromkeys(allowed or [primary])),
                "retry_allowed": retry, "errors": list(errors)}
    if errors:
        return present("invalid", "inspect_contract")
    session, run = str(snapshot.get("session") or "none"), str(snapshot.get("run") or "none")
    observation, result = str(snapshot.get("observation") or "none"), str(snapshot.get("result") or "none")
    if session == "none":
        return present("no_task", "create_or_bind_task")
    if session == "ended" and (run in ACTIVE_RUN or observation in UNCERTAIN_OBSERVATION):
        return present("ended_with_run_tracking", "check_run_receipt")
    if result == "invalid":
        return present("failed_needs_impact_check", "inspect_result_contract",
                       ["inspect_result_contract", "finish_session_keep_receipt"])
    if session == "ended" and result != "none":
        late = {"artifact": "open_artifact", "writeback": "open_review"}.get(result, "view_late_result_receipt")
        return present("late_result_ready", late, [late, "view_late_result_receipt", "copy_result"])
    if result != "none":
        return present("result_ready", RESULT_ACTIONS[result][0], list(RESULT_ACTIONS[result]))
    if session == "ended":
        return present("ended", "view_receipt")
    if observation == "delivery_unknown":
        return present("verify_delivery", "reconcile_by_client_request_id", ["reconcile_by_client_request_id", "finish_session_keep_tracking"])
    if observation in ("lease_expired", "reconcile_failed"):
        return present("verify_run", "check_run_status", ["check_run_status", "finish_session_keep_tracking"])
    if run in ACTIVE_RUN:
        return present("running", "view_progress")
    if run == "failed":
        if snapshot.get("side_effects") == "none":
            return present("failed_retryable", "retry_same_request", ["retry_same_request", "finish_session_keep_receipt"], True)
        return present("failed_needs_impact_check", "check_effects", ["check_effects", "finish_session_keep_receipt"])
    return present("ready", "choose_execution_location", ["choose_execution_location", "finish_session"])


class RunStateError(ValueError):
    """Stable fail-closed error from the local run-state owner."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _text(value: object, maximum: int = 240) -> str:
    return str(value or "").strip()[:maximum]


def now_iso() -> str:
    """Local wall-clock time for run records; run_lease_expired compares these naive stamps."""
    return datetime.now().isoformat(timespec="seconds")


def _timestamp(value: object) -> float:
    try:
        return datetime.fromisoformat(_text(value, 80).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return 0.0


def run_lease_expired(
    run: dict[str, object], timeout: int, grace_seconds: int = 60, *, now: datetime | None = None,
) -> bool:
    """Report an observation lease expiry without inventing a terminal state."""
    if _text(run.get("status"), 40) in TERMINAL_STATES:
        return False
    updated_at = _text(run.get("updated_at") or run.get("created_at"), 80)
    if not updated_at:
        return False
    try:
        parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        current = now or (datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now())
    except (TypeError, ValueError):
        return False
    return (current - parsed).total_seconds() > max(1, int(timeout)) + max(0, int(grace_seconds))


def _correlation(record: dict[str, object]) -> dict[str, str]:
    envelope = record.get("task_envelope") if isinstance(record.get("task_envelope"), dict) else {}
    reference = record.get("task_envelope_ref") if isinstance(record.get("task_envelope_ref"), dict) else {}
    client = envelope.get("client") if isinstance(envelope.get("client"), dict) else {}
    return {
        "client_request_id": _text(client.get("request_id") or reference.get("client_request_id"), 160),
        "idempotency_key": _text(envelope.get("idempotency_key") or reference.get("idempotency_key"), 80),
        "run_id": _text(record.get("id") or envelope.get("run_id") or reference.get("run_id"), 160),
        "task_id": _text(envelope.get("task_id") or reference.get("task_id"), 80),
    }


def _state_record(record: dict[str, object], runtime_scope: str) -> dict[str, object] | None:
    correlation = _correlation(record)
    state = _text(record.get("status"), 40)
    if not correlation["run_id"] or state not in RUN_STATES:
        return None
    error = record.get("error_envelope") if isinstance(record.get("error_envelope"), dict) else {}
    side_effects = _text(error.get("side_effects"), 40)
    if side_effects not in {"none", "unknown", "confirmed"}:
        side_effects = "none" if state in {"submitted", "queued"} else "unknown"
    updated_at = _text(record.get("updated_at") or record.get("created_at"), 80) or now_iso()
    return {
        "schema_id": RUN_STATE_SCHEMA_ID,
        "runtime_scope": runtime_scope,
        **correlation,
        "state": state,
        "side_effects": side_effects,
        "created_at": _text(record.get("created_at"), 80) or updated_at,
        "updated_at": updated_at,
    }


def _validate_record(value: object, runtime_scope: str) -> dict[str, object]:
    record = value if isinstance(value, dict) else {}
    required = ("schema_id", "runtime_scope", "run_id", "task_id", "idempotency_key", "state", "side_effects")
    if (
        record.get("schema_id") != RUN_STATE_SCHEMA_ID
        or record.get("runtime_scope") != runtime_scope
        or any(not _text(record.get(key), 240) for key in required)
        or record.get("state") not in RUN_STATES
        or record.get("side_effects") not in {"none", "unknown", "confirmed"}
    ):
        raise RunStateError("run_ledger_corrupt")
    return {key: record.get(key, "") for key in (
        "schema_id", "runtime_scope", "client_request_id", "idempotency_key", "run_id", "task_id",
        "state", "side_effects", "created_at", "updated_at",
    )}


@dataclass(frozen=True)
class RunStateLedger:
    """Atomic, private-runtime ledger for one logical request and its server attempt."""

    path: Path
    event_log: Path
    runtime_scope: str
    max_records: int = 1000
    legacy_path: Path | None = None  # the backend-named file this one replaced; read, never written

    def __post_init__(self) -> None:
        if self.runtime_scope not in {"private", "personal_vault"}:
            raise RunStateError("run_ledger_scope_invalid")
        if self.path == self.event_log:
            raise RunStateError("run_ledger_path_invalid")

    def _lock_path(self) -> Path:
        """One lock for both names: a process still using the legacy name serialises with this one."""
        base = self.legacy_path if self.legacy_path is not None else self.path
        return lock_path_for(base)

    def _read_lines(self, path: Path, *, strict: bool) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        if path.is_symlink() or not path.is_file():
            raise RunStateError("run_ledger_path_invalid")
        values: list[dict[str, Any]] = []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise RunStateError("run_ledger_unavailable") from exc
        for line in lines:
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                if strict:
                    raise RunStateError("run_ledger_corrupt") from exc
                continue
            if isinstance(value, dict):
                values.append(value)
            elif strict:
                raise RunStateError("run_ledger_corrupt")
        return values

    def _records(self) -> dict[str, dict[str, object]]:
        records: dict[str, dict[str, object]] = {}
        # Dual read on every read, newest record per run wins: a process started before the rename may
        # still be writing the legacy file, and ignoring it would split the idempotency ledger.
        sources = [path for path in (self.legacy_path, self.path) if path is not None and path != self.event_log]
        for source in sources:
            for value in self._read_lines(source, strict=True):
                record = _validate_record(value, self.runtime_scope)
                previous = records.get(str(record["run_id"]))
                order = (_timestamp(record["updated_at"]), _STATE_RANK[str(record["state"])])
                if previous is None or order >= (_timestamp(previous["updated_at"]), _STATE_RANK[str(previous["state"])]):
                    records[str(record["run_id"])] = record
        for event in self._read_lines(self.event_log, strict=False):
            observed = _state_record(event, self.runtime_scope)
            # The same rule as observe(): an event without a task and idempotency identity (older runner
            # events) is not a ledger record. Merging it would let the next write persist a record that
            # every later strict read rejects as corrupt.
            if not observed or not observed["task_id"] or not observed["idempotency_key"]:
                continue
            previous = records.get(str(observed["run_id"]))
            observed_order = (_timestamp(observed["updated_at"]), _STATE_RANK[str(observed["state"])])
            previous_order = (_timestamp(previous["updated_at"]), _STATE_RANK[str(previous["state"])]) if previous else (-1, -1)
            if observed_order >= previous_order:
                records[str(observed["run_id"])] = observed
        return records

    def _write(self, records: dict[str, dict[str, object]]) -> None:
        ordered = sorted(records.values(), key=lambda value: _timestamp(value.get("updated_at")))[-self.max_records :]
        text = "".join(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n" for value in ordered)
        try:
            atomic_write_text(self.path, text)
        except (OSError, UnicodeError) as exc:
            raise RunStateError("run_ledger_unavailable") from exc

    def reserve(self, run: dict[str, object]) -> tuple[str, dict[str, object]]:
        """Reserve an idempotency key before queueing; replay never creates a second attempt."""
        submitted = _state_record({**run, "status": "submitted"}, self.runtime_scope)
        if not submitted or not submitted["task_id"] or not submitted["idempotency_key"]:
            raise RunStateError("run_reservation_invalid")
        with runtime_state_transaction(lock_path=self._lock_path()):
            records = self._records()
            for record in records.values():
                if submitted["client_request_id"] and record["client_request_id"] == submitted["client_request_id"]:
                    if record["idempotency_key"] != submitted["idempotency_key"]:
                        raise RunStateError("run_request_conflict")
                if record["idempotency_key"] == submitted["idempotency_key"]:
                    return "replay", record
            records[str(submitted["run_id"])] = submitted
            self._write(records)
            return "reserved", submitted

    def observe(self, run: dict[str, object]) -> dict[str, object] | None:
        """Persist a valid monotonic transition after its event log record is durable."""
        observed = _state_record(run, self.runtime_scope)
        if not observed or not observed["idempotency_key"]:
            return None
        with runtime_state_transaction(lock_path=self._lock_path()):
            records = self._records()
            previous = records.get(str(observed["run_id"]))
            self._validate_transition(previous, observed)
            records[str(observed["run_id"])] = observed
            self._write(records)
        return observed

    def validate_observation(self, run: dict[str, object]) -> None:
        observed = _state_record(run, self.runtime_scope)
        if not observed or not observed["idempotency_key"]:
            return
        with runtime_state_transaction(lock_path=self._lock_path()):
            self._validate_transition(self._records().get(str(observed["run_id"])), observed)

    @staticmethod
    def _validate_transition(previous: dict[str, object] | None, observed: dict[str, object]) -> None:
        if previous and observed["state"] not in _TRANSITIONS[str(previous["state"])]:
            raise RunStateError("run_state_transition_invalid")

    def claim_dispatch(self, run_id: object) -> bool:
        """Allow at most one local worker to cross the provider-dispatch boundary."""
        requested = _text(run_id, 160)
        with runtime_state_transaction(lock_path=self._lock_path()):
            records = self._records()
            record = records.get(requested)
            if not record:
                raise RunStateError("run_reservation_missing")
            if record["state"] in {"running", "completed", "failed"}:
                return False
            record = {**record, "state": "running", "side_effects": "unknown", "updated_at": now_iso()}
            records[requested] = record
            self._write(records)
            return True

    def recovery(self, run_id: object, *, observation: str = "fresh") -> dict[str, object]:
        """What may happen next to a run (recovery_rules): an uncertain run is reconciled, never
        resubmitted; a failed run is retried only when it is known to have had no side effects."""
        requested = _text(run_id, 160)
        with runtime_state_transaction(lock_path=self._lock_path()):
            record = self._records().get(requested)
        if not record:
            return {"run_id": requested, "action": "not_found", "retry_allowed": True}
        state, effects = str(record["state"]), str(record["side_effects"])
        if observation in UNCERTAIN_OBSERVATION and state not in TERMINAL_STATES:
            action = "reconcile_by_client_request_id" if observation == "delivery_unknown" else "verify_ledger"
            return {"run_id": requested, "action": action, "retry_allowed": False, "state": state}
        if state == "failed":
            allowed = effects == "none"
            return {"run_id": requested, "action": "retry_same_request" if allowed else "check_effects",
                    "retry_allowed": allowed, "state": state}
        return {"run_id": requested, "action": "none" if state in TERMINAL_STATES else "wait",
                "retry_allowed": False, "state": state}

    def reconcile(self, *, client_request_id: object = "", idempotency_key: object = "") -> dict[str, object]:
        request_id = _text(client_request_id, 160)
        idem = _text(idempotency_key, 80)
        if not request_id and not idem:
            raise RunStateError("run_reconcile_invalid")
        with runtime_state_transaction(lock_path=self._lock_path()):
            records = self._records()
        matches = [record for record in records.values() if (
            (not request_id or record["client_request_id"] == request_id)
            and (not idem or record["idempotency_key"] == idem)
        )]
        identities = {(record["run_id"], record["idempotency_key"]) for record in matches}
        if len(identities) > 1:
            raise RunStateError("run_reconcile_ambiguous")
        if not matches:
            return {"state": "not_found", "client_request_id": request_id, "idempotency_key": idem}
        record = matches[0]
        return {**record, "run_state": record["state"], "state": "matched"}


def run_state_ledger(log_jsonl: Path, runtime_scope: str) -> RunStateLedger:
    return RunStateLedger(
        path=log_jsonl.with_name(STATE_FILE),
        event_log=log_jsonl,
        runtime_scope=runtime_scope,
        legacy_path=log_jsonl.with_name(LEGACY_STATE_FILE),
    )


def run_for_id(runs: list[dict[str, object]], run_id: object) -> dict[str, object] | None:
    requested = _text(run_id, 160)
    return next((run for run in runs if run.get("id") == requested), None)


def reconciled_run_record(record: dict[str, object]) -> dict[str, object]:
    return {
        "id": record.get("run_id", ""), "status": record.get("run_state") or record.get("state", "submitted"),
        "created_at": record.get("created_at", ""), "updated_at": record.get("updated_at", ""),
        "task_envelope_ref": {
            "client_request_id": record.get("client_request_id", ""),
            "idempotency_key": record.get("idempotency_key", ""),
            "run_id": record.get("run_id", ""), "task_id": record.get("task_id", ""),
        },
    }


def claim_run_dispatch(ledger: RunStateLedger, run: dict[str, object]) -> bool:
    try:
        return ledger.claim_dispatch(run.get("id"))
    except RunStateError as exc:
        if exc.code != "run_reservation_missing":
            raise
        ledger.reserve(run)
        return ledger.claim_dispatch(run.get("id"))


def reconcile_runs(
    ledger: RunStateLedger,
    runs: list[dict[str, object]],
    *, client_request_id: str = "", idempotency_key: str = "",
) -> tuple[list[dict[str, object]], dict[str, object]]:
    reconciliation = ledger.reconcile(
        client_request_id=client_request_id, idempotency_key=idempotency_key)
    if reconciliation["state"] == "not_found":
        return [], reconciliation
    matched = run_for_id(runs, reconciliation["run_id"])
    return [matched or reconciled_run_record(reconciliation)], reconciliation


def runner_status(
    *, ledger: RunStateLedger | None, runs: list[dict[str, object]], limit: int,
    client_request_id: str, idempotency_key: str, log_path: str,
    provider_status: dict[str, object],
) -> dict[str, object]:
    reconciliation: dict[str, object] = {}
    if (client_request_id or idempotency_key) and ledger:
        runs, reconciliation = reconcile_runs(
            ledger, runs, client_request_id=client_request_id, idempotency_key=idempotency_key)
        runs = [run if "status" in run else {**run, "status": run.get("run_state", "submitted")} for run in runs]
    safe_limit = max(1, min(int(limit or 20), 80))
    return {
        "ok": True, "runs": runs[:safe_limit], "count": len(runs), "log_path": log_path,
        "provider_status": provider_status,
        **({"reconciliation": reconciliation} if reconciliation else {}),
    }
