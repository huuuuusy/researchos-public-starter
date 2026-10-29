# ResearchOS maintenance header.
# 中文：Admit 的正交状态与合法组合唯一 owner；机器结果、provider、plugin 与 UI 不得自行晋升这些轴。
# English: Sole owner for orthogonal Admit states and legal combinations; results, providers, plugins, and UI cannot promote them.

"""Orthogonal admission-state vocabulary and fail-closed transition rules."""

from __future__ import annotations

from typing import Mapping


ADMISSION_STATE_SCHEMA_ID = "researchos-admission-state-v1"
DECISION_STATES = ("unproposed", "proposed", "accepted", "revised", "rejected", "deferred")
MUTATION_STATES = ("not_requested", "staged", "applied", "rolled_back")
VALIDATION_STATES = ("unvalidated", "pending", "passed", "failed")
AUTHORITY_ROLES = ("none", "informative", "interpretive", "normative")
AXES = ("decision_state", "mutation_state", "validation_state", "authority_role")


def initial_admission_state(*, authority_role: str = "none") -> dict[str, str]:
    return normalize_admission_state({
        "schema_id": ADMISSION_STATE_SCHEMA_ID,
        "decision_state": "unproposed",
        "mutation_state": "not_requested",
        "validation_state": "unvalidated",
        "authority_role": authority_role,
    })


def normalize_admission_state(value: object, *, trusted_producer: bool = True) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"schema_id", *AXES}:
        raise ValueError("admission_state_shape_invalid")
    normalized = {key: str(value[key]) for key in ("schema_id", *AXES)}
    if normalized["schema_id"] != ADMISSION_STATE_SCHEMA_ID:
        raise ValueError("admission_state_schema_invalid")
    vocabularies = {
        "decision_state": DECISION_STATES,
        "mutation_state": MUTATION_STATES,
        "validation_state": VALIDATION_STATES,
        "authority_role": AUTHORITY_ROLES,
    }
    if any(normalized[key] not in values for key, values in vocabularies.items()):
        raise ValueError("admission_state_value_invalid")
    if not trusted_producer and any(
        normalized[key] != baseline for key, baseline in (
            ("decision_state", "unproposed"), ("mutation_state", "not_requested"),
            ("validation_state", "unvalidated"), ("authority_role", "none"),
        )
    ):
        raise ValueError("untrusted_admission_claim")
    _validate_combination(normalized)
    return normalized


def _validate_combination(value: Mapping[str, str]) -> None:
    decision, mutation, validation = (
        value["decision_state"], value["mutation_state"], value["validation_state"]
    )
    if decision not in {"accepted", "revised"} and mutation != "not_requested":
        raise ValueError("mutation_without_human_decision")
    if mutation == "not_requested" and validation != "unvalidated":
        raise ValueError("validation_without_mutation")
    if mutation == "staged" and validation not in {"unvalidated", "pending"}:
        raise ValueError("staged_mutation_validation_invalid")
    if mutation == "applied" and validation not in {"pending", "passed", "failed"}:
        raise ValueError("applied_mutation_validation_invalid")
    if mutation == "rolled_back" and validation not in {"unvalidated", "pending", "passed", "failed"}:
        raise ValueError("rollback_validation_invalid")


def transition_admission_state(value: object, *, axis: str, target: str) -> dict[str, str]:
    current = normalize_admission_state(value)
    if axis not in {"decision_state", "mutation_state", "validation_state"}:
        raise ValueError("admission_transition_axis_invalid")
    transitions = {
        "decision_state": {
            "unproposed": {"proposed"},
            "proposed": {"accepted", "revised", "rejected", "deferred"},
            "deferred": {"proposed"},
        },
        "mutation_state": {
            "not_requested": {"staged"}, "staged": {"applied", "rolled_back"}, "applied": {"rolled_back"},
        },
        "validation_state": {"unvalidated": {"pending"}, "pending": {"passed", "failed"}},
    }
    if target not in transitions[axis].get(current[axis], set()):
        raise ValueError("admission_transition_invalid")
    candidate = {**current, axis: target}
    return normalize_admission_state(candidate)


def admission_view(value: object) -> dict[str, object]:
    state = normalize_admission_state(value)
    admitted = (
        state["decision_state"] in {"accepted", "revised"}
        and state["mutation_state"] == "applied"
        and state["validation_state"] == "passed"
    )
    return {
        "schema_id": "researchos-admission-view-v1",
        **{axis: state[axis] for axis in AXES},
        "admitted": admitted,
        "display_state": "admitted" if admitted else "not_admitted",
        "limitations": ["derived_view_not_authority", "result_mode_not_admission"],
    }
