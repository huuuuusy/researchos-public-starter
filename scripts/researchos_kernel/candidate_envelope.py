# ResearchOS maintenance header.
# 中文：ResearchOS Review CandidateEnvelope v1 的内核规范化边界；兼容读取历史字段，但只输出统一合同。
# English: Kernel normalization boundary for Review CandidateEnvelope v1; reads historical fields compatibly but emits only the unified contract.

"""Normalize candidate handoffs before persistence or local execution."""

from __future__ import annotations

from .admission_state import ADMISSION_STATE_SCHEMA_ID, normalize_admission_state


def _candidate_admission_state(
    candidate: dict[str, object], validation: dict[str, object], proposed_writeback: dict[str, object]
) -> dict[str, str]:
    canonical = candidate.get("admission_state")
    if isinstance(canonical, dict):
        try:
            return normalize_admission_state({**canonical, "authority_role": "none"})
        except ValueError:
            pass
    legacy_authority = str(
        validation.get("authority_state", "") or candidate.get("authority_state", "")
    ).strip().lower()
    mapped = {
        "schema_id": ADMISSION_STATE_SCHEMA_ID,
        "decision_state": "proposed",
        "mutation_state": "not_requested",
        "validation_state": "unvalidated",
        "authority_role": "none",
    }
    if legacy_authority == "approved":
        mapped["decision_state"] = "accepted"
    elif legacy_authority == "written_back":
        mapped.update(decision_state="accepted", mutation_state="applied", validation_state="pending")
    elif legacy_authority == "validated":
        mapped.update(decision_state="accepted", mutation_state="applied", validation_state="passed")
    elif legacy_authority == "reverted":
        mapped.update(decision_state="accepted", mutation_state="rolled_back")
    legacy_validation = str(
        proposed_writeback.get("validation_state", "") or validation.get("state", "")
    ).strip().lower()
    if legacy_validation in {"pending", "passed", "failed"} and mapped["mutation_state"] in {"applied", "rolled_back"}:
        mapped["validation_state"] = legacy_validation
    try:
        return normalize_admission_state(mapped)
    except ValueError:
        return normalize_admission_state({
            "schema_id": ADMISSION_STATE_SCHEMA_ID,
            "decision_state": "proposed",
            "mutation_state": "not_requested",
            "validation_state": "unvalidated",
            "authority_role": "none",
        })


def normalize_candidate_envelope(candidate: object) -> dict[str, object]:
    if not isinstance(candidate, dict):
        return {}
    legacy_object_ref = candidate.get("object_ref", {})
    if not isinstance(legacy_object_ref, dict):
        legacy_object_ref = {}
    proposed_action = candidate.get("proposed_action", {})
    if not isinstance(proposed_action, dict):
        proposed_action = {}
    proposed_writeback = candidate.get("proposed_writeback", {})
    if not isinstance(proposed_writeback, dict):
        proposed_writeback = {}
    validation = candidate.get("validation", {})
    if not isinstance(validation, dict):
        validation = {}
    admission_state = _candidate_admission_state(candidate, validation, proposed_writeback)
    source_refs = candidate.get("source_refs", [])
    if not isinstance(source_refs, list):
        source_refs = []
    safe_source_refs = [
        {
            "kind": str(source_ref.get("kind", "")).strip()[:80],
            "path": str(source_ref.get("path", "")).strip()[:500],
            "value": str(source_ref.get("value", "")).strip()[:500],
        }
        for source_ref in source_refs[:20]
        if isinstance(source_ref, dict)
    ]
    return {
        "candidate_id": str(candidate.get("candidate_id", "") or candidate.get("id", "")).strip()[:240],
        "plugin_id": str(candidate.get("plugin_id", "researchos_core")).strip()[:80],
        "candidate_type": str(candidate.get("candidate_type", "candidate")).strip()[:80],
        "source_refs": safe_source_refs,
        "summary": str(candidate.get("summary", "") or candidate.get("claim_or_task", "")).strip()[:800],
        "proposed_action": {
            "id": str(proposed_action.get("id", "review_candidate")).strip()[:80],
            "target_agent": str(proposed_action.get("target_agent", "") or candidate.get("target_agent", "")).strip()[:80],
        },
        "proposed_writeback": {
            "save_target": str(proposed_writeback.get("save_target", "") or candidate.get("save_target", "")).strip()[:400],
            "object_type": str(proposed_writeback.get("object_type", "") or legacy_object_ref.get("type", "")).strip()[:80],
            "object_id": str(proposed_writeback.get("object_id", "") or legacy_object_ref.get("id", "")).strip()[:240],
            "object_path": str(proposed_writeback.get("object_path", "") or legacy_object_ref.get("path", "")).strip()[:400],
            "current_state": str(proposed_writeback.get("current_state", "")).strip()[:400],
            "proposed_state": str(proposed_writeback.get("proposed_state", "")).strip()[:400],
            "decision_rationale": str(proposed_writeback.get("decision_rationale", "")).strip()[:800],
            "impact_scope": str(proposed_writeback.get("impact_scope", "")).strip()[:800],
            "rollback_ref": str(proposed_writeback.get("rollback_ref", "")).strip()[:400],
            "validation_state": admission_state["validation_state"],
        },
        "sensitivity": str(candidate.get("sensitivity", "")).strip()[:80],
        "required_confirmation": str(candidate.get("required_confirmation", "")).strip()[:80],
        "validation": {
            "workflow_status": str(validation.get("workflow_status", "") or candidate.get("workflow_status", "") or candidate.get("status", "")).strip()[:80],
            "evidence_state": str(validation.get("evidence_state", "") or candidate.get("evidence_state", "")).strip()[:80],
        },
        "admission_state": admission_state,
    }
