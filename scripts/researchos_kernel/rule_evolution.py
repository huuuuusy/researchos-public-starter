"""Pure contracts for governed Rule candidates, bounded trials, and review proposals.

This owner never activates a Rule globally and never applies a human disposition.
It only constructs reviewable records and derives fail-closed lifecycle views.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Sequence

from .ledger import digest as _stable_hash


SCHEMA_ID = "researchos-rule-evolution-v1"
CLAIM_BOUNDARY = "governed_rule_evolution_not_human_ai_coevolution"
OBJECT_KINDS = ("rule_candidate", "bounded_trial", "disposition_proposal", "rule_version")
DISPOSITIONS = ("retain", "revise", "retire", "defer", "supersede")
RULE_STABILITIES = ("provisional", "stable")
RUNTIME_SCOPES = ("private", "public_starter", "personal_vault")


@dataclass(frozen=True)
class RuleEvolutionError(ValueError):
    code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


def _text(value: object, *, field: str, limit: int = 1024) -> str:
    if not isinstance(value, str):
        raise RuleEvolutionError("invalid_rule_field", f"{field} must be a string")
    text = value.strip()
    if not text:
        raise RuleEvolutionError("missing_rule_field", field)
    if len(text) > limit:
        raise RuleEvolutionError("rule_field_too_large", field)
    return text


def _strings(value: object, *, field: str, minimum: int = 1, maximum: int = 64) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RuleEvolutionError("invalid_rule_field", f"{field} must be a list")
    items = [_text(item, field=field) for item in value]
    items = list(dict.fromkeys(items))
    if len(items) < minimum:
        raise RuleEvolutionError("missing_rule_field", field)
    if len(items) > maximum:
        raise RuleEvolutionError("rule_field_too_large", field)
    return items


def _time(value: object, *, field: str) -> str:
    text = _text(value, field=field, limit=64)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuleEvolutionError("invalid_rule_time", field) from error
    if parsed.tzinfo is None:
        raise RuleEvolutionError("invalid_rule_time", f"{field} must include timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _scope(value: object) -> dict[str, list[str]]:
    if not isinstance(value, Mapping):
        raise RuleEvolutionError("invalid_rule_scope", "scope must be an object")
    unknown = set(value) - {"task_types", "profile_ids", "project_refs"}
    if unknown:
        raise RuleEvolutionError("unknown_rule_field", f"scope: {', '.join(sorted(unknown))}")
    scope = {
        key: _strings(value.get(key, []), field=f"scope.{key}", minimum=0, maximum=32)
        for key in ("task_types", "profile_ids", "project_refs")
    }
    if not any(scope.values()):
        raise RuleEvolutionError("empty_rule_scope", "at least one scope dimension is required")
    return scope


def _counterevidence(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise RuleEvolutionError("invalid_counterevidence", "counterevidence must be an object")
    unknown = set(value) - {"status", "refs", "assessment"}
    if unknown:
        raise RuleEvolutionError("unknown_rule_field", f"counterevidence: {', '.join(sorted(unknown))}")
    status = _text(value.get("status"), field="counterevidence.status", limit=32)
    if status not in {"observed", "searched_none_found", "unknown"}:
        raise RuleEvolutionError("invalid_counterevidence", status)
    refs = _strings(value.get("refs", []), field="counterevidence.refs", minimum=0)
    assessment = _text(value.get("assessment"), field="counterevidence.assessment", limit=2048)
    if status == "observed" and not refs:
        raise RuleEvolutionError("missing_counterexample", "observed counterevidence requires refs")
    return {"status": status, "refs": refs, "assessment": assessment}


def build_rule_candidate(payload: Mapping[str, object]) -> dict[str, object]:
    allowed = {
        "statement", "scope", "source_episodes", "counterevidence", "version",
        "review_date", "retire_trigger", "rollback_target", "created_at",
    }
    unknown = set(payload) - allowed
    if unknown:
        raise RuleEvolutionError("unknown_rule_field", ", ".join(sorted(unknown)))
    statement = _text(payload.get("statement"), field="statement", limit=8192)
    scope = _scope(payload.get("scope"))
    episodes = _strings(payload.get("source_episodes"), field="source_episodes")
    counterevidence = _counterevidence(payload.get("counterevidence"))
    version = payload.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise RuleEvolutionError("invalid_rule_version", str(version))
    review_date = _time(payload.get("review_date"), field="review_date")
    created_at = _time(payload.get("created_at"), field="created_at")
    record = {
        "schema_id": SCHEMA_ID,
        "object_kind": "rule_candidate",
        "state": "candidate",
        "statement": statement,
        "scope": scope,
        "source_episodes": episodes,
        "counterevidence": counterevidence,
        "version": version,
        "review_date": review_date,
        "retire_trigger": _text(payload.get("retire_trigger"), field="retire_trigger", limit=2048),
        "rollback_target": _text(payload.get("rollback_target"), field="rollback_target"),
        "created_at": created_at,
        "authority": "candidate_only",
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return {**record, "rule_id": f"rule-{_stable_hash(record)[:20]}"}


def build_bounded_trial(
    candidate: Mapping[str, object],
    *,
    scope: Mapping[str, object],
    begins_at: str,
    expires_at: str,
) -> dict[str, object]:
    if candidate.get("schema_id") != SCHEMA_ID or candidate.get("object_kind") != "rule_candidate":
        raise RuleEvolutionError("invalid_rule_candidate", "bounded trials require a v1 Rule candidate")
    trial_scope = _scope(scope)
    candidate_scope = _scope(candidate.get("scope"))
    for key, values in trial_scope.items():
        if not set(values).issubset(candidate_scope[key]):
            raise RuleEvolutionError("trial_scope_expansion", key)
    start = _time(begins_at, field="begins_at")
    expiry = _time(expires_at, field="expires_at")
    if _parse_time(expiry) <= _parse_time(start):
        raise RuleEvolutionError("invalid_trial_window", "expires_at must follow begins_at")
    seed = {"candidate_ref": candidate.get("rule_id"), "scope": trial_scope, "begins_at": start, "expires_at": expiry}
    return {
        "schema_id": SCHEMA_ID,
        "object_kind": "bounded_trial",
        "trial_id": f"trial-{_stable_hash(seed)[:20]}",
        "candidate_ref": _text(candidate.get("rule_id"), field="candidate.rule_id"),
        "state": "planned",
        "scope": trial_scope,
        "begins_at": start,
        "expires_at": expiry,
        "activation": "explicit_scope_only",
        "authority": "trial_only",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def evaluate_trial(
    trial: Mapping[str, object],
    *,
    runtime_scope: str,
    task_type: str = "",
    profile_id: str = "",
    project_ref: str = "",
    now: str,
) -> dict[str, object]:
    if trial.get("schema_id") != SCHEMA_ID or trial.get("object_kind") != "bounded_trial":
        raise RuleEvolutionError("invalid_rule_trial", "expected bounded_trial")
    if runtime_scope not in RUNTIME_SCOPES:
        raise RuleEvolutionError("invalid_runtime_scope", runtime_scope)
    if runtime_scope == "public_starter":
        return {"view": "inactive", "eligible": False, "reason": "public_starter_never_activates_rules"}
    current = _parse_time(_time(now, field="now"))
    if current < _parse_time(_time(trial.get("begins_at"), field="begins_at")):
        return {"view": "inactive", "eligible": False, "reason": "trial_not_started"}
    if current >= _parse_time(_time(trial.get("expires_at"), field="expires_at")):
        return {"view": "inactive_expired", "eligible": False, "reason": "trial_expired"}
    scope = _scope(trial.get("scope"))
    actual = {"task_types": task_type, "profile_ids": profile_id, "project_refs": project_ref}
    for key, allowed in scope.items():
        if allowed and actual[key] not in allowed:
            return {"view": "inactive", "eligible": False, "reason": f"outside_{key}"}
    return {"view": "eligible", "eligible": True, "reason": "exact_scope_and_time_match"}


def normalize_evidence(payload: Mapping[str, object]) -> dict[str, object]:
    allowed = {"episode_refs", "counterexample_refs", "primary_outcome", "guardrails", "burden", "sufficiency"}
    unknown = set(payload) - allowed
    forbidden = {"acceptance_rate", "rule_count"} & set(payload)
    if forbidden:
        raise RuleEvolutionError("forbidden_rule_metric", ", ".join(sorted(forbidden)))
    if unknown:
        raise RuleEvolutionError("unknown_rule_field", f"evidence: {', '.join(sorted(unknown))}")
    primary = payload.get("primary_outcome")
    if not isinstance(primary, Mapping):
        raise RuleEvolutionError("invalid_rule_evidence", "primary_outcome is required")
    primary_allowed = {"name", "definition", "baseline", "observation_window", "owner", "missing_data_policy", "observation"}
    if set(primary) - primary_allowed or set(primary) != primary_allowed:
        raise RuleEvolutionError("invalid_rule_evidence", "primary_outcome fields are incomplete or unknown")
    primary_record = {key: _text(primary.get(key), field=f"primary_outcome.{key}", limit=2048) for key in primary_allowed}
    guardrails_raw = payload.get("guardrails")
    if not isinstance(guardrails_raw, Sequence) or isinstance(guardrails_raw, (str, bytes)) or not guardrails_raw:
        raise RuleEvolutionError("invalid_rule_evidence", "at least one guardrail is required")
    guardrails: list[dict[str, object]] = []
    for item in guardrails_raw:
        if not isinstance(item, Mapping) or set(item) != {"name", "critical", "threshold", "action", "observation", "breached"}:
            raise RuleEvolutionError("invalid_rule_evidence", "guardrail fields are incomplete or unknown")
        if not isinstance(item.get("critical"), bool) or not isinstance(item.get("breached"), bool):
            raise RuleEvolutionError("invalid_rule_evidence", "guardrail critical/breached must be booleans")
        guardrails.append({
            "name": _text(item.get("name"), field="guardrail.name"),
            "critical": item["critical"],
            "threshold": _text(item.get("threshold"), field="guardrail.threshold"),
            "action": _text(item.get("action"), field="guardrail.action"),
            "observation": _text(item.get("observation"), field="guardrail.observation", limit=2048),
            "breached": item["breached"],
        })
    sufficiency = payload.get("sufficiency")
    if not isinstance(sufficiency, Mapping) or set(sufficiency) != {"required_episode_count", "counterevidence_reviewed"}:
        raise RuleEvolutionError("invalid_rule_evidence", "sufficiency contract is required")
    required_count = sufficiency.get("required_episode_count")
    if not isinstance(required_count, int) or isinstance(required_count, bool) or required_count < 1:
        raise RuleEvolutionError("invalid_rule_evidence", "required_episode_count must be positive")
    if not isinstance(sufficiency.get("counterevidence_reviewed"), bool):
        raise RuleEvolutionError("invalid_rule_evidence", "counterevidence_reviewed must be boolean")
    episodes = _strings(payload.get("episode_refs"), field="evidence.episode_refs")
    counterexamples = _strings(payload.get("counterexample_refs", []), field="evidence.counterexample_refs", minimum=0)
    burden = payload.get("burden")
    if not isinstance(burden, Mapping) or set(burden) != {"definition", "observation", "acceptable"} or not isinstance(burden.get("acceptable"), bool):
        raise RuleEvolutionError("invalid_rule_evidence", "burden fields are incomplete")
    sufficient = (
        len(episodes) >= required_count
        and sufficiency["counterevidence_reviewed"] is True
        and not any(item["critical"] and item["breached"] for item in guardrails)
    )
    return {
        "episode_refs": episodes,
        "counterexample_refs": counterexamples,
        "primary_outcome": primary_record,
        "guardrails": guardrails,
        "burden": {
            "definition": _text(burden.get("definition"), field="burden.definition"),
            "observation": _text(burden.get("observation"), field="burden.observation", limit=2048),
            "acceptable": burden["acceptable"],
        },
        "sufficiency": {
            "required_episode_count": required_count,
            "counterevidence_reviewed": sufficiency["counterevidence_reviewed"],
            "sufficient_for_proposal": sufficient,
        },
    }


def build_disposition_proposal(
    candidate: Mapping[str, object],
    *,
    proposed: str,
    evidence: Mapping[str, object],
    created_at: str,
    replacement_candidate_ref: str = "",
) -> dict[str, object]:
    if candidate.get("schema_id") != SCHEMA_ID or candidate.get("object_kind") != "rule_candidate":
        raise RuleEvolutionError("invalid_rule_candidate", "disposition proposals require a v1 candidate")
    if proposed not in DISPOSITIONS:
        raise RuleEvolutionError("invalid_rule_disposition", proposed)
    normalized_evidence = normalize_evidence(evidence)
    effective = proposed if normalized_evidence["sufficiency"]["sufficient_for_proposal"] else "defer"
    replacement = ""
    if effective == "supersede":
        replacement = _text(replacement_candidate_ref, field="replacement_candidate_ref")
    seed = {"rule_id": candidate.get("rule_id"), "proposed": effective, "evidence": normalized_evidence, "created_at": created_at}
    return {
        "schema_id": SCHEMA_ID,
        "object_kind": "disposition_proposal",
        "proposal_id": f"proposal-{_stable_hash(seed)[:20]}",
        "rule_ref": _text(candidate.get("rule_id"), field="candidate.rule_id"),
        "proposed": effective,
        "requested_proposal": proposed,
        "replacement_candidate_ref": replacement,
        "evidence": normalized_evidence,
        "created_at": _time(created_at, field="created_at"),
        "authority": "proposal_only_human_disposition_required",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def normalize_rule_version(payload: Mapping[str, object]) -> dict[str, object]:
    allowed = {
        "schema_id", "object_kind", "rule_version_ref", "rule_id", "version", "statement", "scope",
        "source_episodes", "counterevidence", "review_date", "retire_trigger", "rollback_target",
        "stability", "expires_at", "supersedes", "human_disposition_ref", "claim_boundary",
    }
    unknown = set(payload) - allowed
    if unknown:
        raise RuleEvolutionError("unknown_rule_field", f"rule_version: {', '.join(sorted(unknown))}")
    if payload.get("schema_id") != SCHEMA_ID or payload.get("object_kind") != "rule_version":
        raise RuleEvolutionError("invalid_rule_version_record", "expected rule_version")
    if payload.get("claim_boundary") != CLAIM_BOUNDARY:
        raise RuleEvolutionError("invalid_rule_claim_boundary", str(payload.get("claim_boundary")))
    stability = payload.get("stability")
    if stability not in RULE_STABILITIES:
        raise RuleEvolutionError("invalid_rule_stability", str(stability))
    version = payload.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise RuleEvolutionError("invalid_rule_version", str(version))
    expires_at = ""
    if stability == "provisional":
        expires_at = _time(payload.get("expires_at"), field="expires_at")
    elif payload.get("expires_at") not in (None, ""):
        raise RuleEvolutionError("stable_rule_expiry_forbidden", "stable Rules use review_due, not auto expiry")
    return {
        "schema_id": SCHEMA_ID,
        "object_kind": "rule_version",
        "rule_version_ref": _text(payload.get("rule_version_ref"), field="rule_version_ref"),
        "rule_id": _text(payload.get("rule_id"), field="rule_id"),
        "version": version,
        "statement": _text(payload.get("statement"), field="statement", limit=8192),
        "scope": _scope(payload.get("scope")),
        "source_episodes": _strings(payload.get("source_episodes"), field="source_episodes"),
        "counterevidence": _counterevidence(payload.get("counterevidence")),
        "review_date": _time(payload.get("review_date"), field="review_date"),
        "retire_trigger": _text(payload.get("retire_trigger"), field="retire_trigger", limit=2048),
        "rollback_target": _text(payload.get("rollback_target"), field="rollback_target"),
        "stability": stability,
        "expires_at": expires_at,
        "supersedes": _strings(payload.get("supersedes", []), field="supersedes", minimum=0),
        "human_disposition_ref": _text(payload.get("human_disposition_ref"), field="human_disposition_ref"),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def lifecycle_view(rule: Mapping[str, object], *, now: str) -> dict[str, object]:
    rule = normalize_rule_version(rule)
    stability = rule["stability"]
    current = _parse_time(_time(now, field="now"))
    review_date = _parse_time(_time(rule.get("review_date"), field="review_date"))
    if stability == "stable":
        return {
            "view": "review_due" if current >= review_date else "eligible",
            "active": True,
            "requires_human_disposition": current >= review_date,
            "reason": "stable_review_due_never_auto_degrades" if current >= review_date else "stable_within_review_window",
        }
    expiry = _parse_time(_time(rule.get("expires_at"), field="expires_at"))
    if current >= expiry:
        return {"view": "inactive_expired", "active": False, "requires_human_disposition": False, "reason": "authorized_provisional_expiry"}
    return {"view": "eligible", "active": True, "requires_human_disposition": False, "reason": "provisional_within_explicit_expiry"}


def build_transition_proposal(
    current_rule: Mapping[str, object],
    *,
    action: str,
    target_ref: str,
    evidence_refs: Sequence[str],
    created_at: str,
) -> dict[str, object]:
    current_rule = normalize_rule_version(current_rule)
    if action not in {"supersede", "rollback"}:
        raise RuleEvolutionError("invalid_rule_transition", action)
    current_ref = _text(current_rule.get("rule_version_ref"), field="rule_version_ref")
    target = _text(target_ref, field="target_ref")
    rollback_target = _text(current_rule.get("rollback_target"), field="rollback_target")
    if action == "rollback" and target != rollback_target:
        raise RuleEvolutionError("rollback_target_mismatch", target)
    seed = {"current_ref": current_ref, "action": action, "target_ref": target, "evidence_refs": list(evidence_refs)}
    return {
        "schema_id": SCHEMA_ID,
        "object_kind": "disposition_proposal",
        "proposal_id": f"proposal-{_stable_hash(seed)[:20]}",
        "rule_ref": current_ref,
        "proposed": action,
        "target_ref": target,
        "supersedes": [current_ref] if action == "supersede" else [],
        "rollback_target": rollback_target,
        "history_refs": list(dict.fromkeys([current_ref, rollback_target, target])),
        "evidence_refs": _strings(evidence_refs, field="evidence_refs"),
        "created_at": _time(created_at, field="created_at"),
        "authority": "proposal_only_human_disposition_required",
        "claim_boundary": CLAIM_BOUNDARY,
    }
