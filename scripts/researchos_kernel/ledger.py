"""Requirement ledger U and trajectory H, stored in the context-impact review ledger.

Refactor v5, D1: the scheduler no longer keeps its own store. Requirements and
their history live in the single context-impact review ledger family owned by
``researchos_server.context_impact_store`` (private) and configured by
``requirement_ledger`` (public starter and demos):

* ``<ledger>.json`` keeps its ``researchos-context-impact-review-ledger-v1`` shape.
  The kernel adds a ``coordination_series`` header and one observation cursor
  under ``observation_cursors`` (key ``CURSOR_KEY``); every other key is preserved.
* ``<ledger>.coordination.jsonl`` is the append-only record stream in the
  ``researchos_coordination_series_v1`` vocabulary (collections ``trajectory``,
  ``observations``, ``decision_points``, ``episodes``). Trajectory kinds are
  issue_transition / decision / attempt / effect / check / feedback; issue states
  are open / deferred / waiting / resolved / cancelled; check results are
  met / unmet / unknown.
* ``<ledger>.snapshot-cache.json`` is a rebuildable stat cache, never state.
* ``.<ledger>.json.lock`` is the same advisory lock the store takes: both open it through
  ``atomic_files.runtime_state_transaction(lock_path=lock_path_for(ledger))``, and both replace
  files through ``atomic_files.atomic_write_text``.

Issue transitions and checks carry the occurrence binding
``issue_id + occurrence_id + generation + attempt_id + rule_version +
purpose_version + source_version_vector``. Requirement state is never stored;
``derive_states`` replays the stream. The cursor is written last, so a crash
replays from the previous complete boundary.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .atomic_files import append_text, atomic_write_text, lock_path_for, runtime_state_transaction

SERIES_SCHEMA = "researchos_coordination_series_v1"
LEDGER_SCHEMA_ID = "researchos-context-impact-review-ledger-v1"
CURSOR_KEY = "researchos_kernel_boundary"
COLLECTIONS = {"trajectory", "observations", "decision_points", "episodes"}
TRAJECTORY_KINDS = {"issue_transition", "decision", "attempt", "effect", "check", "feedback", "ask"}
ISSUE_STATES = {"open", "deferred", "waiting", "resolved", "cancelled"}
# Report D5, judged in this order; the order is the priority. Same enum as the obligations contract.
CAUSES = ("initial", "miss", "scope", "src", "ver", "evid", "time")
CHECK_RESULTS = {"met", "unmet", "unknown", "not_evaluated"}
OPERATIONS = {"inspect", "clarify", "defer", "revise_with_sources", "retain_if_consistent", "compose", "retire", "admit", "rollback", "ask"}
OPEN_STATUSES = {"open", "deferred", "waiting"}
ORIGIN = "researchos_kernel"
SCOPE_INTENT = "scope"  # a session whose intent is the whole frozen scope, not one commitment


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def digest(value) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def is_sha256(value: object) -> bool:
    """Whether ``value`` is a lowercase hex SHA-256 string, the form ``digest`` returns."""
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def landed_or_undone(payload: dict) -> str:
    """Whether a candidate already went through admission, read off the admission axes (HJ-2:
    no merged `confirmed` state). A legacy record from before the axes carries `admitted`."""
    mutation = (payload.get("admission_state") or {}).get("mutation_state", "")
    if mutation in {"applied", "rolled_back"}:
        return mutation
    return "applied" if payload.get("admitted") else ""


def binding(issue_id: str = "", generation: int = 0, attempt_id: str = "", rule_version: str = "",
            purpose_version: str = "", source_version_vector: str = "") -> dict:
    return {"issue_id": issue_id, "occurrence_id": digest([issue_id, generation]) if issue_id else "",
            "generation": generation, "attempt_id": attempt_id, "rule_version": rule_version,
            "purpose_version": purpose_version, "source_version_vector": source_version_vector}


def requirement_binding(issue_id: str, state: dict, registration: dict) -> dict:
    """The binding of a requirement's current generation, as its state and registration record it."""
    return binding(issue_id, state["generation"], rule_version=registration.get("rule_version", ""),
                   purpose_version=registration.get("purpose_version", ""), source_version_vector=state["read_digest"])


class Ledger:
    def __init__(self, ledger_path: Path):
        self.path = Path(ledger_path)
        stem = self.path.name[:-5] if self.path.name.endswith(".json") else self.path.name
        self.records_path = self.path.with_name(f"{stem}.coordination.jsonl")
        self.cache_path = self.path.with_name(f"{stem}.snapshot-cache.json")
        self.candidates_path = self.path.with_name(f"{stem}.candidates.jsonl")
        self.lock_path = lock_path_for(self.path)

    def family(self) -> set:
        """Every file the kernel may create; used by the no-second-store check."""
        return {self.path, self.records_path, self.cache_path, self.candidates_path, self.lock_path}

    def lock(self):
        """Exclusive lock on the sibling lock file the context-impact store also takes (fails closed
        without a cross-process lock)."""
        return runtime_state_transaction(lock_path=self.lock_path)

    # -- ledger JSON (shared with the store) -------------------------------------------------
    def read_ledger(self) -> dict:
        if not self.path.exists():
            return {"schema_id": LEDGER_SCHEMA_ID, "updated_at": "", "events": {}, "notifications": {},
                    "observation_cursors": {}}
        ledger = json.loads(self.path.read_text(encoding="utf-8"))
        if (not isinstance(ledger, dict) or ledger.get("schema_id") != LEDGER_SCHEMA_ID
                or not isinstance(ledger.get("events"), dict) or not isinstance(ledger.get("notifications"), dict)):
            raise ValueError(f"{self.path.name}: not a context-impact review ledger")
        if not isinstance(ledger.setdefault("observation_cursors", {}), dict):
            raise ValueError(f"{self.path.name}: invalid observation_cursors")
        return ledger

    def _write_ledger(self, ledger: dict) -> None:
        ledger.setdefault("coordination_series", {
            "schema": SERIES_SCHEMA, "series_id": uuid.uuid4().hex, "origin": ORIGIN,
            "use": "requirement_ledger", "clock": "utc_recorded_seconds",
            "records_file": self.records_path.name,
            "coverage": "scheduler rule requirements; legacy review kinds keep their notification records",
        })
        ledger["updated_at"] = now_iso()
        atomic_write_text(self.path, json.dumps(ledger, ensure_ascii=False, indent=2) + "\n")

    # -- record stream -------------------------------------------------------------------------
    def records(self, collection: str | None = None) -> list:
        if not self.records_path.exists():
            return []
        rows = []
        lines = self.records_path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                if number == len(lines):
                    break  # a torn last line is an interrupted append, not a damaged ledger
                raise ValueError(f"{self.records_path.name}:{number}: corrupt record") from error
            if collection is None or row.get("collection") == collection:
                rows.append(row)
        return rows

    def trajectory(self) -> list:
        return self.records("trajectory")

    def _append(self, rows: list) -> list:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._drop_torn_tail()
        append_text(self.records_path, "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))
        return rows

    def _drop_torn_tail(self) -> None:
        """A last line without its newline is an append that was interrupted before it was written
        (`records` already reads it as absent). Appending after it would bury it mid-file and make
        the ledger unreadable, so the unwritten fragment is cut before the next record."""
        try:
            with open(self.records_path, "rb+") as handle:
                size = handle.seek(0, os.SEEK_END)
                if size == 0:
                    return
                handle.seek(size - 1)
                if handle.read(1) == b"\n":
                    return
                handle.seek(0)
                keep = handle.read().rfind(b"\n") + 1
                handle.truncate(keep)
                handle.flush()
                os.fsync(handle.fileno())
        except FileNotFoundError:
            return

    def append(self, collection: str, fields: dict, *, record_id: str = "", at: str = "") -> dict:
        if collection not in COLLECTIONS:
            raise ValueError(f"unknown collection: {collection}")
        row = {"collection": collection, "id": record_id or uuid.uuid4().hex, **fields}
        if collection == "trajectory":
            if row.get("kind") not in TRAJECTORY_KINDS:
                raise ValueError(f"unknown trajectory kind: {row.get('kind')}")
            stamp = at or now_iso()
            row = {"episode_id": "", "point_id": "", "at": stamp, "available_at": stamp,
                   "availability_reason": "recorded_by_runtime", "origin": ORIGIN, "evidence_ids": [],
                   "measurements": {}, **row}
        return self._append([row])[0]

    def _trajectory(self, kind: str, payload: dict, *, point_id: str = "", episode_id: str = "",
                    evidence_ids: list | None = None) -> dict:
        return self.append("trajectory", {"kind": kind, "point_id": point_id, "episode_id": episode_id,
                                          "evidence_ids": evidence_ids or [], "payload": payload})

    def transition(self, bound: dict, to: str, reason: str, *, point_id: str = "", requirement: dict | None = None,
                   summary: str = "", read_set: list | None = None, until: str = "", check_ids: list | None = None,
                   previous_transition_id: str = "", reopen_trigger: str = "", cause: str = "",
                   miss_status: str = "") -> dict:
        """``cause`` is the one attribution (report D5) of a transition that creates work: a first
        registration, a new generation or a reopening. Moves made by a decision carry none."""
        if to not in ISSUE_STATES:
            raise ValueError(f"unknown issue state: {to}")
        if cause and cause not in CAUSES:
            raise ValueError(f"unknown cause: {cause}")
        payload = {"issue_id": bound["issue_id"], "requirement_id": (requirement or {}).get("rule_id", ""),
                   "scope_object_ids": list(read_set or []), "to": to, "reason": reason,
                   "check_ids": list(check_ids or []), "previous_transition_id": previous_transition_id,
                   "binding": bound, "summary": summary, "reopen_trigger": reopen_trigger,
                   "cause": cause, "miss_status": miss_status if cause else ""}
        if requirement:
            payload["requirement"] = requirement
        if until:
            payload["until"] = until
        return self._trajectory("issue_transition", payload, point_id=point_id)

    def decision(self, operation: str, *, bound: dict | None = None, read_set: list | None = None,
                 candidate_ids: list | None = None, permission_state: str = "not_required", detail: dict | None = None,
                 episode_id: str = "") -> dict:
        if operation not in OPERATIONS:
            raise ValueError(f"unknown operation: {operation}")
        bound = bound or binding()
        return self._trajectory("decision", {"issue_id": bound["issue_id"], "operation": operation, "bindings": bound,
                                             "read_set": list(read_set or []), "candidate_ids": list(candidate_ids or []),
                                             "permission_state": permission_state, "detail": detail or {}},
                                episode_id=episode_id)

    def ask(self, ask_id: str, *, class_key: str, issue_ids: list, check_id: str, basis_version: str, options: list,
            state: str, answer: str = "", reopen_trigger: str = "", detail: dict | None = None,
            point_id: str = "") -> dict:
        """One bounded question (report D3). Append-only: the latest row per ask_id is its state."""
        return self._trajectory("ask", {"ask_id": ask_id, "class_key": class_key, "issue_ids": list(issue_ids),
                                        "check_id": check_id, "basis_version": basis_version, "options": list(options),
                                        "state": state, "answer": answer, "reopen_trigger": reopen_trigger,
                                        "detail": detail or {}}, point_id=point_id)

    def restate_ask(self, ask_id: str, question: dict, issue_id: str, state: str, **changes) -> dict:
        """Record a question's next state (answered, withdrawn), keeping what identifies it."""
        return self.ask(ask_id, class_key=question.get("class_key", ""), issue_ids=[issue_id],
                        check_id=question.get("check_id", ""), basis_version=question.get("basis_version", ""),
                        options=question.get("options", []), state=state, **changes)

    def asks(self, trajectory: list | None = None) -> dict:
        found = {}
        for row in trajectory if trajectory is not None else self.trajectory():
            if row.get("kind") == "ask":
                found[row["payload"]["ask_id"]] = dict(row["payload"], at=row.get("at", ""))
        return found

    def attempt(self, decision_id: str, status: str, output_ids: list, detail: dict | None = None) -> dict:
        return self._trajectory("attempt", {"decision_id": decision_id, "status": status,
                                            "output_ids": list(output_ids), "detail": detail or {}})

    def effect(self, attempt_id: str, changes: list, *, knowledge: str = "observed", unchanged: list | None = None,
               detail: dict | None = None, record_id: str = "") -> dict:
        return self.append("trajectory", {"kind": "effect", "point_id": "", "episode_id": "", "evidence_ids": [],
                                          "payload": {"attempt_id": attempt_id, "knowledge": knowledge,
                                                      "changes": changes, "unchanged_object_ids": list(unchanged or []),
                                                      "detail": detail or {}}},
                           record_id=record_id)

    def check(self, result: str, *, requirement_id: str, attempt_id: str = "", bound: dict | None = None,
              checked_state_ids: list | None = None, supports_effect_ids: list | None = None, basis: str = "",
              point_id: str = "", evidence_ids: list | None = None, reason_code: str = "") -> dict:
        """``reason_code`` says which kind of unknown this is (report CC-11), so the kind is on the
        record rather than parsed back out of the basis prose."""
        if result not in CHECK_RESULTS:
            raise ValueError(f"unknown check result: {result}")
        return self._trajectory("check", {"attempt_id": attempt_id, "requirement_id": requirement_id, "result": result,
                                          "checked_state_ids": list(checked_state_ids or []),
                                          "supports_effect_ids": list(supports_effect_ids or []), "basis": basis,
                                          "reason_code": reason_code,
                                          "binding": bound or binding()}, point_id=point_id,
                                evidence_ids=evidence_ids)

    def observation(self, *, changed_state_ids: list, state_count: int, source_version_vector: str,
                    detail: dict | None = None) -> dict:
        return self.append("observations", {"time": now_iso(), "unknown_times": [], "state_ids": [],
                                            "state_count": state_count, "changed_state_ids": changed_state_ids,
                                            "causal_parents": [], "evidence_ids": [],
                                            "source_version_vector": source_version_vector, "detail": detail or {}})

    def decision_point(self, *, cutoff: str, point_id: str = "", episode_id: str = "", context_id: str = "") -> dict:
        return self.append("decision_points", {"episode_id": episode_id, "context_id": context_id,
                                               "cutoff": cutoff, "origin": ORIGIN}, record_id=point_id)

    def episode(self, episode_id: str, *, start: str = "", end: str = "", object_ids: list | None = None,
                detail: dict | None = None, outcome: str = "", held: list | None = None, asked: int = 0) -> dict:
        """``outcome`` is Out_ε (complete / complete_with_held / budget_stopped / human_stopped), set at the end."""
        return self.append("episodes", {"episode_id": episode_id, "boundary_basis": "ros_session",
                                        "object_ids": list(object_ids or []), "start": start, "end": end,
                                        "outcome": outcome, "held": list(held or []), "asked": asked,
                                        "detail": detail or {}})

    # -- candidates (CandidateEnvelope records live in this family, not in a second store) ----
    def record_candidate(self, envelope: dict, payload: dict | None = None) -> dict:
        row = {"candidate_id": envelope["candidate_id"], "envelope": envelope, "payload": payload or {},
               "recorded_at": now_iso()}
        append_text(self.candidates_path, json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row

    def candidates(self) -> dict:
        """Latest record per candidate id; the file is append-only, so a later row supersedes."""
        found = {}
        if not self.candidates_path.exists():
            return found
        for line in self.candidates_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # a torn last line is an interrupted append
            found[row.get("candidate_id", "")] = row
        return found

    # -- cursor ------------------------------------------------------------------------------------
    def read_cursor(self) -> dict:
        try:
            cursor = dict(self.read_ledger()["observation_cursors"].get(CURSOR_KEY) or {})
        except (OSError, ValueError, json.JSONDecodeError):
            return {}
        try:
            cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cache = {}
        if cache.get("digest") == cursor.get("digest"):
            cursor.update(versions=cache.get("versions", {}), cache=cache.get("cache"), spec=cache.get("spec"))
        return cursor  # a missing or mismatched cache only costs a full rescan

    def write_cursor(self, cursor: dict) -> None:
        # The frozen spec of this boundary rides with the versions: the next boundary recomputes
        # `miss` against it. Losing this file costs a rescan and makes `miss` undefined once (D5).
        atomic_write_text(self.cache_path, json.dumps({"digest": cursor["digest"], "versions": cursor.get("versions", {}),
                                                  "cache": cursor.get("cache"), "spec": cursor.get("spec")},
                                                 ensure_ascii=False))
        ledger = self.read_ledger()
        saved = {"digest": cursor["digest"], "at": cursor.get("at", ""), "point_id": cursor.get("point_id", ""),
                 "records": len(self.records())}
        previous = ledger["observation_cursors"].get(CURSOR_KEY) or {}
        if {k: previous.get(k) for k in ("digest", "at")} != {k: saved[k] for k in ("digest", "at")} \
                or "coordination_series" not in ledger:
            ledger["observation_cursors"][CURSOR_KEY] = saved
            self._write_ledger(ledger)

    # -- derived state -------------------------------------------------------------------------------
    def sessions(self) -> dict:
        """The Session axis, a projection of the episodes: id -> intent, day, start, ended."""
        found: dict = {}
        for row in self.records("episodes"):
            sid = row.get("episode_id", "")
            if row.get("start") and sid not in found:
                found[sid] = {"intent": (row.get("object_ids") or [SCOPE_INTENT])[0],
                              "day": row.get("detail", {}).get("day", ""), "start": row["start"], "ended": False}
            if row.get("end") and sid in found:
                found[sid]["ended"] = True
        return found

    def session_start(self, session_id: str) -> dict:
        """The row that opened a session ({} if none); its detail holds the frozen spec and scope."""
        return next((row for row in self.records("episodes")
                     if row.get("episode_id") == session_id and row.get("start")), {})

    def dispatches(self) -> tuple:
        """(dispatch decisions by run id, attempts by decision id)."""
        runs, attempts = {}, {}
        for row in self.trajectory():
            payload = row.get("payload", {})
            if row.get("kind") == "decision" and payload.get("detail", {}).get("action") == "run_dispatched":
                runs[payload["detail"]["run_id"]] = row
            elif row.get("kind") == "attempt" and payload.get("decision_id"):
                attempts.setdefault(payload["decision_id"], []).append(payload)
        return runs, attempts

    def open_runs(self, session_id: str = "") -> list:
        """Runs dispatched (in ``session_id``, or anywhere) that have not returned a usable result."""
        runs, attempts = self.dispatches()
        return [run_id for run_id, row in sorted(runs.items())
                if (not session_id or row.get("episode_id") == session_id)
                and not any(a.get("status") in {"returned", "failed", "invalid", "abandoned"}
                            and not a.get("detail", {}).get("retryable")
                            for a in attempts.get(row["id"], []))]

    def unresolved_runs(self, session_id: str) -> list:
        """CC-11: runs whose observation is unknown — we do not know whether the work happened. A run is
        resolved when it returned a usable result, when it failed before launch (nothing happened, side
        effects `none`), or when the researcher abandoned it and the unknown was recorded as such. A
        post-launch failure leaves side effects unknown and stays here: that is the run-observation
        unknown, and reading it as "nothing happened" is exactly the substitution CC-11 forbids."""
        runs, attempts = self.dispatches()
        unresolved = []
        for run_id, row in sorted(runs.items()):
            if session_id and row.get("episode_id") != session_id:
                continue
            resolved = False
            for attempt in attempts.get(row["id"], []):
                detail = attempt.get("detail", {})
                if detail.get("retryable"):
                    continue  # a corrected answer is still expected
                status = attempt.get("status")
                if status in {"returned", "abandoned"} or (status in {"failed", "invalid"}
                                                           and detail.get("side_effects") == "none"):
                    resolved = True
            if not resolved:
                unresolved.append(run_id)
        return unresolved

    def unadmitted_field_changes(self, field_changes: list, session_id: str) -> list:
        """Subtract only the exact field delta covered by successful admissions since this session's start.

        Replay field hashes, not just admitted judgment ids: an intervening hand edit breaks the chain.
        Missing receipts fail closed; rolled-back or incompletely recorded admissions grant no coverage.
        """
        if not field_changes:
            return []
        records = self.records()
        start = next((i for i, row in enumerate(records) if row.get("collection") == "episodes"
                      and row.get("episode_id") == session_id and row.get("start")), None)
        if start is None:
            return field_changes
        trajectory = [row for row in records[start + 1:] if row.get("collection") == "trajectory"]
        decisions = {row["id"]: row["payload"] for row in trajectory if row.get("kind") == "decision"
                     and row["payload"].get("operation") == "admit"
                     and row["payload"].get("detail", {}).get("how") == "admit_candidate"}
        attempts = {row["id"]: row["payload"] for row in trajectory if row.get("kind") == "attempt"
                    and row["payload"].get("status") == "applied"}
        candidates = self.candidates()
        expected = {(row["commitment_id"], row["field"]): digest(row["before"]) for row in field_changes}
        covered = set()
        for row in trajectory:
            if row.get("kind") != "effect":
                continue
            effect = row["payload"]
            detail = effect.get("detail", {})
            attempt = attempts.get(effect.get("attempt_id"), {})
            decision = decisions.get(attempt.get("decision_id"), {})
            candidate_id = detail.get("candidate_id")
            stored = candidates.get(candidate_id, {}).get("payload", {})
            if (not decision or candidate_id not in decision.get("candidate_ids", [])
                    or landed_or_undone(stored) != "applied"
                    or not detail.get("receipt_id") or detail["receipt_id"] != stored.get("receipt_id")
                    or detail.get("how") != "admit_candidate"):
                continue
            change = detail.get("commitment_field_change", {})
            key = (change.get("commitment_id"), change.get("field"))
            if key not in expected or change.get("before_digest") != expected[key]:
                continue
            expected[key] = change.get("after_digest")
            covered.add(key)
        return [row for row in field_changes if (row["commitment_id"], row["field"]) not in covered
                or digest(row["after"]) != expected[(row["commitment_id"], row["field"])]]

    def closure_receipts(self, trajectory: list | None = None) -> dict:
        """Episode closure receipts by id -> {"identity", "revoked", "record"}. A rollback of the
        transaction that wrote a closure revokes its receipt; the record stays as history."""
        rows = trajectory if trajectory is not None else self.trajectory()
        rolled_back = {row.get("payload", {}).get("detail", {}).get("transaction_id")
                       for row in rows if row.get("kind") == "effect"
                       and any(c.get("change") == "writeback_rolled_back" for c in row.get("payload", {}).get("changes", []))}
        found = {}
        for row in rows:
            payload = row.get("payload", {})
            changes = [c for c in payload.get("changes", []) if c.get("change") == "episode_closed"]
            if row.get("kind") == "effect" and changes:
                found[row["id"]] = {"identity": changes[0].get("episode_identity", ""), "record": row,
                                    "revoked": payload.get("detail", {}).get("transaction_id") in rolled_back}
        return found

    def requirements(self, trajectory: list | None = None) -> dict:
        found = {}
        for row in trajectory if trajectory is not None else self.trajectory():
            payload = row.get("payload", {})
            if row.get("kind") == "issue_transition" and payload.get("requirement"):
                found.setdefault(payload["issue_id"], payload["requirement"])
        return found

    def derive_states(self, trajectory: list | None = None) -> dict:
        """Replay the trajectory into per-requirement state. Pure and deterministic."""
        states, admitted, confirmed = {}, {}, {}
        decisions = {}
        rows = trajectory if trajectory is not None else self.trajectory()
        # A rolled-back admission is not an admission: the same block pasted back needs confirming.
        rolled_back = {row.get("payload", {}).get("detail", {}).get("transaction_id") for row in rows
                       if row.get("kind") == "effect"
                       and any(c.get("change") == "writeback_rolled_back" for c in row.get("payload", {}).get("changes", []))}
        rolled_back.discard(None)
        rolled_back.discard("")
        for row in rows:
            kind, payload = row.get("kind"), row.get("payload", {})
            if kind == "decision":
                decisions[payload.get("issue_id", "")] = payload
            elif kind == "issue_transition":
                bound = payload.get("binding", {})
                state = states.setdefault(payload["issue_id"], {"status": "open", "generation": 0, "read_digest": "",
                                                                "deferred_until": "", "history": 0})
                # Only the decision bound to this transition can justify its waiting state.
                # Consume it once: a later executor transition must not inherit human permission.
                decision = decisions.pop(payload["issue_id"], {})
                state["decision"] = decision if decision.get("bindings") == bound else {}
                state["history"] += 1
                state["status"] = payload["to"]
                state["generation"] = bound.get("generation", state["generation"])
                state["read_digest"] = bound.get("source_version_vector", state["read_digest"])
                state["deferred_until"] = payload.get("until", "") if payload["to"] == "deferred" else ""
                state["reopen_trigger"] = payload.get("reopen_trigger", "") if payload["to"] == "waiting" else ""
                state["last_at"] = row.get("at", "")
                if payload.get("cause") and payload.get("reason") in {"opened", "reopened", "refreshed"}:
                    # a new generation derived by a rule: the version that derived it
                    state["rule_version"] = str(bound.get("rule_version", ""))
                    state["opened_at"] = row.get("at", "")
                state["summary"] = payload.get("summary") or state.get("summary", "")
            elif kind == "effect" and payload.get("detail", {}).get("transaction_id") not in rolled_back:
                for change in payload.get("changes", []):
                    # Soul §3: a change confirmed after the fact (break-glass) closes its confirmation
                    # requirement and nothing more; it is never an admission. Older records say so
                    # through the `how` they were written with.
                    post_hoc = change.get("change") == "direct_change_confirmed" or (
                        change.get("change") == "judgment_admitted"
                        and payload.get("detail", {}).get("how") in {"confirm_existing_block", "reconfirm_confirmed"})
                    if post_hoc:
                        confirmed.setdefault(change.get("object_id", ""), set()).add(change.get("content_id", ""))
                    elif change.get("change") == "judgment_admitted":
                        admitted.setdefault(change.get("object_id", ""), set()).add(change.get("content_id", ""))
        return {"issues": states, "admitted_judgments": admitted, "confirmed_judgments": confirmed}
