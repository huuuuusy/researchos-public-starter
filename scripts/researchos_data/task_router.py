"""Deterministic, non-effectful TaskIntent router for the public starter."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from researchos_data.capability_registry import grouped_capability_ids


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "09_templates/data_contracts/researchos-task-routing-contract-v1.json"
VALID_EFFECTS = {"answer", "artifact", "durable_change", "external_action"}
VALID_DESTINATIONS = {"conversation", "local_project", "researchos_review", "external"}
VALID_CURRENTNESS = {"historical", "current", "latest", "unknown"}
VALID_SENSITIVITY = {"public", "public_safe", "internal", "sensitive", "private", "local_only", "unknown"}


class TaskIntentError(ValueError):
    """Raised when a TaskIntent candidate violates the public contract."""


def load_task_routing_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _string_list(intent: dict[str, Any], key: str) -> list[str]:
    value = intent.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TaskIntentError(f"{key} must be a list of strings")
    return [item.strip() for item in value if item.strip()]


def normalize_task_intent(intent: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(intent, dict):
        raise TaskIntentError("TaskIntent must be a JSON object")
    terminal_job = str(intent.get("terminal_job", "")).strip()
    if not terminal_job:
        raise TaskIntentError("terminal_job is required")
    requested_effect = str(intent.get("requested_effect", "answer"))
    destination = str(intent.get("destination", "conversation"))
    currentness = str(intent.get("claimed_currentness", "unknown"))
    sensitivity = str(intent.get("sensitivity", "unknown"))
    if requested_effect not in VALID_EFFECTS:
        raise TaskIntentError(f"invalid requested_effect: {requested_effect}")
    if destination not in VALID_DESTINATIONS:
        raise TaskIntentError(f"invalid destination: {destination}")
    if currentness not in VALID_CURRENTNESS:
        raise TaskIntentError(f"invalid claimed_currentness: {currentness}")
    if sensitivity not in VALID_SENSITIVITY:
        raise TaskIntentError(f"invalid sensitivity: {sensitivity}")
    exact_targets = _string_list(intent, "exact_targets")
    for target in exact_targets:
        path = Path(target)
        if path.is_absolute() or ".." in path.parts:
            raise TaskIntentError(f"exact_targets must stay inside the active public or personal vault: {target}")
        candidate = ROOT / path
        if not candidate.resolve().is_relative_to(ROOT.resolve()):
            raise TaskIntentError(f"exact_targets resolves outside the active vault: {target}")
        if not candidate.is_file():
            raise TaskIntentError(f"exact_targets source does not exist: {target}")
    return {
        "terminal_job": terminal_job,
        "current_commitment_id": str(intent.get("current_commitment_id", "")).strip() or None,
        "exact_targets": exact_targets,
        "source_modalities": [_text(item) for item in _string_list(intent, "source_modalities")],
        "requested_effect": requested_effect,
        "destination": destination,
        "claimed_currentness": currentness,
        "sensitivity": sensitivity,
        "constraints": _string_list(intent, "constraints"),
        "known_unknowns": _string_list(intent, "known_unknowns"),
        "primary_family_candidate": str(intent.get("primary_family_candidate", "")).strip() or None,
        "secondary_family_candidates": _string_list(intent, "secondary_family_candidates"),
        "authority_owner": str(intent.get("authority_owner", "")).strip() or None,
        "thread_id": str(intent.get("thread_id", "")).strip() or None,
    }


def _family_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in contract["families"]}


def _classify(intent: dict[str, Any], families: dict[str, dict[str, Any]]) -> tuple[str | None, list[str], str]:
    candidate = intent["primary_family_candidate"]
    if candidate:
        if candidate not in families:
            raise TaskIntentError(f"unknown primary_family_candidate: {candidate}")
        return candidate, [candidate], "model_candidate_validated"
    scores = {
        family_id: sum(1 for keyword in family["keywords"] if _text(keyword) in _text(intent["terminal_job"]))
        for family_id, family in families.items()
    }
    scores = {family_id: score for family_id, score in scores.items() if score}
    if not scores:
        return None, [], "bounded_ambiguity"
    best = max(scores.values())
    winners = sorted(family_id for family_id, score in scores.items() if score == best)
    return (winners[0], winners, "deterministic_keyword_fallback") if len(winners) == 1 else (None, winners, "bounded_ambiguity")


def _status(intent: dict[str, Any], family_id: str | None) -> tuple[str, list[str], list[str]]:
    confirmations: list[str] = []
    stops = [
        "route_receipt_does_not_authorize_mutation_or_external_effect",
        "public_runtime_is_copy_only",
    ]
    if family_id is None:
        return "needs_clarification", ["choose_one_primary_family"], stops
    if intent["sensitivity"] == "unknown":
        confirmations.append("confirm_sensitivity_before_expanding_context")
    if intent["destination"] == "external" and intent["sensitivity"] in {"sensitive", "private", "local_only", "internal"}:
        stops.append("non_public_content_must_not_leave_local_authority")
        return "blocked", confirmations, stops
    if intent["requested_effect"] == "external_action" or intent["destination"] == "external":
        confirmations.append("explicit_external_effect_authorization_required")
        stops.append("public_starter_cannot_send_submit_publish_or_release")
    if intent["requested_effect"] == "durable_change":
        confirmations.append("human_review_required_before_personal_vault_writeback")
        stops.append("public_starter_cannot_write_canonical_state")
    if intent["sensitivity"] == "unknown":
        return "needs_clarification", confirmations, stops
    return ("hold_for_confirmation" if confirmations else "ready"), confirmations, stops


def _episode_id(intent: dict[str, Any], family_id: str | None, owner: str) -> str:
    anchor = (
        f"commitment:{_text(intent['current_commitment_id'])}"
        if intent["current_commitment_id"]
        else f"unbound:{_text(intent['terminal_job'])}"
    )
    payload = {
        "anchor": anchor,
        "family": family_id or "ambiguous",
        "targets": sorted(_text(item) for item in intent["exact_targets"]),
        "effect": intent["requested_effect"],
        "destination": intent["destination"],
        "sensitivity": intent["sensitivity"],
        "owner": owner,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"ep_{digest[:16]}"


def route_task_intent(
    raw_intent: dict[str, Any],
    *,
    prior_receipt: dict[str, Any] | None = None,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = contract or load_task_routing_contract()
    intent = normalize_task_intent(raw_intent)
    families = _family_map(contract)
    family_id, candidates, resolution = _classify(intent, families)
    family = families.get(family_id) if family_id else None
    for secondary in intent["secondary_family_candidates"]:
        if secondary not in families:
            raise TaskIntentError(f"unknown secondary_family_candidate: {secondary}")
    secondaries = [item for item in intent["secondary_family_candidates"] if item != family_id]
    capabilities = list((family or {}).get("capabilities", []))
    for secondary in secondaries:
        capabilities.extend(families[secondary].get("capabilities", []))
    capabilities = list(dict.fromkeys(capabilities))
    owner = intent["authority_owner"] or (family or {}).get("authority_owner", "unknown")
    episode_id = _episode_id(intent, family_id, owner)
    prior_identity = (prior_receipt or {}).get("identity", {})
    prior_route = (prior_receipt or {}).get("route", {})
    drift: list[str] = []
    if prior_receipt and prior_route.get("primary_family") != family_id:
        drift.append("primary_family_changed")
    if prior_receipt and prior_identity.get("episode_id") != episode_id:
        drift.append("bounded_intent_or_authority_changed")
    status, confirmations, stops = _status(intent, family_id)
    effect = contract["effects"][intent["requested_effect"]]
    adapters = list((family or {}).get("default_adapters", []))
    adapters.extend(
        contract["modality_adapters"][item]
        for item in intent["source_modalities"]
        if item in contract["modality_adapters"]
    )
    return {
        "schema_id": "researchos-execution-route-receipt-v1",
        "contract_version": contract["version"],
        "status": status,
        "intent": intent,
        "identity": {
            "commitment_id": intent["current_commitment_id"],
            "episode_id": episode_id,
            "run_id": None,
            "run_id_state": "assigned_at_execution",
            "continued_from_prior": bool(prior_receipt and prior_identity.get("episode_id") == episode_id),
            "drift_reasons": drift,
            "thread_id": intent["thread_id"],
            "thread_title_used_for_identity": False,
        },
        "route": {
            "primary_family": family_id,
            "candidate_families": candidates,
            "family_resolution": resolution,
            "secondary_families": secondaries,
            "secondary_capabilities": capabilities,
            "capability_groups": grouped_capability_ids(ROOT, capabilities),
            "phases": effect["phases"],
            "result_mode": effect["result_mode"],
            "risk_profile": effect["risk_profile"],
            "authority": {
                "owner": owner,
                "router_is_authority": False,
                "mutation_allowed_by_receipt": False,
                "external_effect_allowed_by_receipt": False,
            },
        },
        "context": {
            "tier": (family or {}).get("default_tier", "quick"),
            "context_route_id": (family or {}).get("context_route_id"),
            "fallback_context_route_id": (family or {}).get("fallback_context_route_id"),
            "read_now": list(intent["exact_targets"]),
            "excluded": ["unselected_local_files", "private_sibling_repositories", "credentials", "runtime_logs"],
        },
        "execution": {
            "adapters": list(dict.fromkeys(adapters)),
            "confirmation_points": list(dict.fromkeys(confirmations)),
            "validation_profile": list((family or {}).get("validation_profile", [])),
            "stop_conditions": list(dict.fromkeys(stops)),
        },
        "runtime": {
            "scope": "public_starter",
            "execution": "copy_only",
            "canonical_write": False,
            "network": False,
            "command": False,
            "dashboard_required": False,
        },
        "next_safe_action": {
            "ready": "produce_an_answer_or_artifact_within_the_receipt_boundary",
            "needs_clarification": "ask_one_bounded_question",
            "hold_for_confirmation": "return_a_candidate_and_request_the_named_confirmation",
            "blocked": "keep_content_local_and_resolve_the_boundary",
        }[status],
    }


__all__ = [
    "CONTRACT_PATH",
    "TaskIntentError",
    "load_task_routing_contract",
    "normalize_task_intent",
    "route_task_intent",
]
