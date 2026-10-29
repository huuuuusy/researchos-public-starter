# ResearchOS maintenance header.
# 中文：TaskIntent v1 的内核归一化与 TaskEnvelope v1 的唯一 owner；客户端请求永远不直接成为运行事实或授权。
# English: Sole kernel owner for TaskIntent v1 normalization and TaskEnvelope v1; client requests never become runtime facts or authorization directly.

"""Kernel-owned task envelopes for client-agnostic ResearchOS execution."""

from __future__ import annotations

import copy
from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from .context_receipt import build_requested_context_receipt
from .ledger import digest as _digest

TASK_INTENT_SCHEMA_ID = "researchos-task-intent-v1"
TASK_ENVELOPE_SCHEMA_ID = "researchos-task-envelope-v1"
RESULT_MODES = frozenset({"answer", "artifact", "writeback"})
REASONING_EFFORTS = frozenset({"auto", "low", "medium", "high", "xhigh", "max", "ultra"})
TASK_COMPLEXITIES = frozenset({"auto", "economy", "standard", "deep"})
RUNTIME_SCOPES = frozenset({"private", "public_starter", "personal_vault"})
MAX_SOURCE_REFS = 20
MAX_NESTED_INSTRUCTION_LENGTH = 65536
MAX_LEGACY_INSTRUCTION_LENGTH = 120000

_INTENT_KEYS = {
    "schema_id", "input_trust", "goal", "instruction", "client_request_id", "client",
    "requested_result", "requested_profile", "client_hints", "source_refs",
}
_CLIENT_KEYS = {"kind", "surface", "task_ref"}
_RESULT_KEYS = {"mode"}
_PROFILE_KEYS = {"provider", "model", "reasoning_effort", "task_complexity"}
_HINT_KEYS = {"recommended_reasoning_effort", "recommended_task_complexity"}
_SOURCE_KEYS = {"kind", "ref", "label"}
_CAPABILITIES = {
    "read_only_analysis": "research.analysis",
    "candidate_patch_plan": "research.candidate_plan",
    "direct_execution": "research.execution",
}


class TaskEnvelopeContractError(ValueError):
    """Stable, public-safe contract failure without echoing private input."""

    def __init__(self, code: str, field: str) -> None:
        super().__init__(code)
        self.code = code
        self.field = field


@dataclass(frozen=True)
class NormalizedTaskIntent(Mapping[str, object]):
    """Typed server-normalized input; an arbitrary mapping cannot bypass normalization."""

    value: dict[str, object]
    origin: str

    def __getitem__(self, key: str) -> object:
        return self.value[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.value)

    def __len__(self) -> int:
        return len(self.value)

    def as_dict(self) -> dict[str, object]:
        return copy.deepcopy(self.value)


def _error(code: str, field: str) -> TaskEnvelopeContractError:
    return TaskEnvelopeContractError(code, field)


def _record(value: object, field: str, keys: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or {str(key) for key in value} != keys:
        raise _error("task_intent_invalid_shape", field)
    return value


def _text(
    value: object,
    field: str,
    maximum: int,
    *,
    nonempty: bool = False,
    normalize_newlines: bool = False,
    strict: bool = True,
) -> str:
    if strict and not isinstance(value, str):
        raise _error("task_intent_invalid_shape", field)
    text = "" if value is None else str(value)
    if "\x00" in text:
        raise _error("task_intent_invalid_character", field)
    if normalize_newlines:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
    if len(text) > maximum:
        raise _error("task_intent_input_too_large", field)
    if nonempty and not text.strip():
        raise _error("task_intent_invalid_value", field)
    return text


def _source_refs(values: object, *, strict: bool, maximum: int) -> list[dict[str, str]]:
    if not isinstance(values, list):
        raise _error("task_intent_invalid_shape", "source_refs")
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, value in enumerate(values):
        field = f"source_refs[{index}]"
        if strict:
            record = _record(value, field, _SOURCE_KEYS)
        elif isinstance(value, str):
            record = {"kind": "session_source", "ref": value, "label": ""}
        elif isinstance(value, dict):
            record = {
                "kind": value.get("kind", value.get("type", "session_source")),
                "ref": value.get("ref", value.get("path", value.get("url", value.get("id", value.get("value", ""))))),
                "label": value.get("label", value.get("title", "")),
            }
        else:
            raise _error("task_intent_invalid_shape", field)
        item = {
            "kind": _text(record.get("kind"), f"{field}.kind", 80, nonempty=True, strict=strict),
            "ref": _text(record.get("ref"), f"{field}.ref", 2048, nonempty=True, strict=strict),
            "label": _text(record.get("label"), f"{field}.label", 240, strict=strict),
        }
        identity = (item["kind"], item["ref"], item["label"])
        if identity not in seen:
            seen.add(identity)
            normalized.append(item)
    if len(normalized) > maximum:
        raise _error("task_intent_input_too_large", "source_refs")
    return normalized


def _check_requested_values(intent: dict[str, object]) -> None:
    result = intent["requested_result"]
    profile = intent["requested_profile"]
    hints = intent["client_hints"]
    assert isinstance(result, dict) and isinstance(profile, dict) and isinstance(hints, dict)
    if result["mode"] not in RESULT_MODES:
        raise _error("unsupported_result_mode", "requested_result.mode")
    for field, value in (
        ("requested_profile.reasoning_effort", profile["reasoning_effort"]),
        ("client_hints.recommended_reasoning_effort", hints["recommended_reasoning_effort"]),
    ):
        if value not in REASONING_EFFORTS:
            raise _error("unsupported_reasoning_effort", field)
    for field, value in (
        ("requested_profile.task_complexity", profile["task_complexity"]),
        ("client_hints.recommended_task_complexity", hints["recommended_task_complexity"]),
    ):
        if value not in TASK_COMPLEXITIES:
            raise _error("unsupported_task_complexity", field)


def _normalize_nested(
    value: object,
    *,
    origin: str = "nested",
    instruction_limit: int = MAX_NESTED_INSTRUCTION_LENGTH,
    source_limit: int = MAX_SOURCE_REFS,
) -> NormalizedTaskIntent:
    record = _record(value, "task_intent", _INTENT_KEYS)
    if record.get("schema_id") != TASK_INTENT_SCHEMA_ID:
        raise _error("task_intent_schema_mismatch", "schema_id")
    if record.get("input_trust") != "untrusted":
        raise _error("task_intent_invalid_trust", "input_trust")
    client = _record(record.get("client"), "client", _CLIENT_KEYS)
    result = _record(record.get("requested_result"), "requested_result", _RESULT_KEYS)
    profile = _record(record.get("requested_profile"), "requested_profile", _PROFILE_KEYS)
    hints = _record(record.get("client_hints"), "client_hints", _HINT_KEYS)
    normalized: dict[str, object] = {
        "schema_id": TASK_INTENT_SCHEMA_ID,
        "input_trust": "untrusted",
        "goal": _text(record.get("goal"), "goal", 4000, normalize_newlines=True),
        "instruction": _text(record.get("instruction"), "instruction", instruction_limit, normalize_newlines=True),
        "client_request_id": _text(record.get("client_request_id"), "client_request_id", 160),
        "client": {
            "kind": _text(client.get("kind"), "client.kind", 120, nonempty=True),
            "surface": _text(client.get("surface"), "client.surface", 120, nonempty=True),
            "task_ref": _text(client.get("task_ref"), "client.task_ref", 240),
        },
        "requested_result": {"mode": _text(result.get("mode"), "requested_result.mode", 80, nonempty=True)},
        "requested_profile": {
            "provider": _text(profile.get("provider"), "requested_profile.provider", 120, nonempty=True),
            "model": _text(profile.get("model"), "requested_profile.model", 240, nonempty=True),
            "reasoning_effort": _text(profile.get("reasoning_effort"), "requested_profile.reasoning_effort", 80, nonempty=True),
            "task_complexity": _text(profile.get("task_complexity"), "requested_profile.task_complexity", 80, nonempty=True),
        },
        "client_hints": {
            "recommended_reasoning_effort": _text(hints.get("recommended_reasoning_effort"), "client_hints.recommended_reasoning_effort", 80, nonempty=True),
            "recommended_task_complexity": _text(hints.get("recommended_task_complexity"), "client_hints.recommended_task_complexity", 80, nonempty=True),
        },
        "source_refs": _source_refs(record.get("source_refs"), strict=True, maximum=source_limit),
    }
    _check_requested_values(normalized)
    return NormalizedTaskIntent(normalized, origin)


def _legacy_intent(payload: dict[str, object]) -> NormalizedTaskIntent:
    candidate = payload.get("candidate") if isinstance(payload.get("candidate"), dict) else {}
    assert isinstance(candidate, dict)
    sources = candidate.get("source_refs") if isinstance(candidate.get("source_refs"), list) else []
    raw = {
        "schema_id": TASK_INTENT_SCHEMA_ID,
        "input_trust": "untrusted",
        "goal": str(payload.get("title", "") or ""),
        "instruction": str(payload.get("prompt", "") or candidate.get("summary", "") or candidate.get("claim_or_task", "") or ""),
        "client_request_id": str(payload.get("client_request_id", "") or ""),
        "client": {"kind": "legacy", "surface": "codex_runner", "task_ref": str(payload.get("work_session_id", "") or "")},
        "requested_result": {"mode": str(payload.get("response_mode", "answer") or "answer")},
        "requested_profile": {
            "provider": str(payload.get("provider", "auto") or "auto"),
            "model": str(payload.get("model", "auto") or "auto"),
            "reasoning_effort": str(payload.get("reasoning_effort", "auto") or "auto"),
            "task_complexity": str(payload.get("task_complexity", "auto") or "auto"),
        },
        "client_hints": {
            "recommended_reasoning_effort": str(payload.get("recommended_reasoning_effort", "auto") or "auto"),
            "recommended_task_complexity": str(payload.get("recommended_task_complexity", "standard") or "standard"),
        },
        "source_refs": _source_refs(sources, strict=False, maximum=MAX_SOURCE_REFS),
    }
    return _normalize_nested(
        raw, origin="legacy", instruction_limit=MAX_LEGACY_INSTRUCTION_LENGTH, source_limit=MAX_SOURCE_REFS
    )


def normalize_task_intent(payload: object) -> NormalizedTaskIntent:
    """Strictly normalize nested v1 or adapt one legacy flat request without fallback."""
    if not isinstance(payload, dict):
        raise _error("task_intent_invalid_shape", "payload")
    return _normalize_nested(payload["task_intent"]) if "task_intent" in payload else _legacy_intent(payload)


def normalize_task_intent_result(
    payload: object,
) -> tuple[NormalizedTaskIntent | None, dict[str, object] | None]:
    try:
        return normalize_task_intent(payload), None
    except TaskEnvelopeContractError as exc:
        return None, {
            "ok": False, "error_type": exc.code, "field": exc.field,
            "contract": TASK_INTENT_SCHEMA_ID, "message": "Task intent failed the server contract.",
        }


def build_task_envelope(
    intent: NormalizedTaskIntent,
    *,
    run: dict[str, object],
    runtime_scope: str,
    idempotency_namespace: str,
) -> dict[str, object]:
    """Build an immutable pre-policy envelope from request evidence and trusted run facts."""
    if not isinstance(intent, NormalizedTaskIntent):
        raise _error("task_envelope_untrusted_intent", "intent")
    intent = _normalize_nested(
        intent.as_dict(), origin=intent.origin,
        instruction_limit=MAX_LEGACY_INSTRUCTION_LENGTH if intent.origin == "legacy" else MAX_NESTED_INSTRUCTION_LENGTH,
        source_limit=MAX_SOURCE_REFS,
    )
    if runtime_scope not in RUNTIME_SCOPES:
        raise _error("task_envelope_invalid_runtime_scope", "runtime_ref.scope")
    if not idempotency_namespace:
        raise _error("task_envelope_invalid_namespace", "idempotency_key")
    run_id = _text(run.get("id"), "run_id", 160, nonempty=True, strict=False)
    task_mode = _text(run.get("task_mode"), "capability_id", 80, nonempty=True, strict=False)
    if task_mode not in _CAPABILITIES:
        raise _error("task_envelope_unknown_capability", "capability_id")
    capability_id = _CAPABILITIES[task_mode]
    result_mode = _text(run.get("response_mode", "answer"), "result_mode", 80, nonempty=True, strict=False)
    if result_mode not in RESULT_MODES:
        raise _error("unsupported_result_mode", "result_mode")
    runtime_ref = {
        "scope": runtime_scope,
        "profile_id": _text(run.get("runtime_profile_id", run.get("provider", "codex")), "runtime_ref.profile_id", 64, nonempty=True, strict=False),
        "provider": _text(run.get("provider", "codex"), "runtime_ref.provider", 120, nonempty=True, strict=False),
        "model": _text(run.get("model", "auto"), "runtime_ref.model", 240, nonempty=True, strict=False),
        "reasoning_effort": _text(run.get("reasoning_effort", "auto"), "runtime_ref.reasoning_effort", 80, nonempty=True, strict=False),
        "task_complexity": _text(run.get("task_complexity", "standard"), "runtime_ref.task_complexity", 80, nonempty=True, strict=False),
        "task_data_digest": _digest({
            "work_session_id": run.get("work_session_id", ""), "title": run.get("title", ""),
            "source": run.get("source", ""), "candidate": run.get("candidate", {}), "prompt": run.get("prompt", ""),
        }),
    }
    normalized = intent.as_dict()
    request_id = str(intent["client_request_id"] or "")
    execution_fingerprint = _digest({
        "intent": normalized, "capability_id": capability_id, "result_mode": result_mode, "runtime_ref": runtime_ref,
    })
    idempotency_anchor = request_id or run_id
    idempotency_key = f"idem:{_digest([idempotency_namespace, runtime_scope, idempotency_anchor, execution_fingerprint])}"
    task_id = f"task:{_digest([idempotency_namespace, runtime_scope, idempotency_key])}"
    profile = intent["requested_profile"]
    client = intent["client"]
    assert isinstance(profile, dict) and isinstance(client, dict)
    return {
        "schema_id": TASK_ENVELOPE_SCHEMA_ID,
        "task_id": task_id,
        "run_id": run_id,
        "idempotency_key": idempotency_key,
        "capability_id": capability_id,
        "intent": {
            "schema_id": TASK_INTENT_SCHEMA_ID,
            "input_trust": "untrusted",
            "digest": _digest(normalized),
            "goal": str(intent["goal"]),
            "instruction": str(intent["instruction"]),
        },
        "request_ref": {
            "result_mode": str(intent["requested_result"]["mode"]),  # type: ignore[index]
            "profile_id": _text(run.get("requested_runtime_profile_id", profile["provider"]), "request_ref.profile_id", 64, nonempty=True, strict=False),
            "provider": str(profile["provider"]),
            "model": str(profile["model"]),
            "reasoning_effort": str(profile["reasoning_effort"]),
            "task_complexity": str(profile["task_complexity"]),
            "client_hints": copy.deepcopy(intent["client_hints"]),
        },
        "result_mode": result_mode,
        "context_ref": {
            "source_state": "requested",
            "source_refs": copy.deepcopy(intent["source_refs"]),
            "receipt": build_requested_context_receipt(
                task_id=task_id, run_id=run_id, runtime_scope=runtime_scope,
                producer_kind=str(client["kind"]), producer_surface=str(client["surface"]),
                source_refs=intent["source_refs"],
            ),
        },
        "runtime_ref": runtime_ref,
        "authorization_ref": {"state": "unresolved"},
        "client": {
            "kind": str(client["kind"]), "surface": str(client["surface"]),
            "task_ref": str(client["task_ref"]), "request_id": request_id,
        },
    }


def task_envelope_ref(envelope: object) -> dict[str, str]:
    """Build a digest-only internal retention reference, not another TaskEnvelope state."""
    if not isinstance(envelope, dict) or envelope.get("schema_id") != TASK_ENVELOPE_SCHEMA_ID:
        return {}
    return {
        "client_request_id": str(envelope.get("client", {}).get("request_id", "")) if isinstance(envelope.get("client"), dict) else "",
        "task_id": str(envelope.get("task_id", "")),
        "run_id": str(envelope.get("run_id", "")),
        "idempotency_key": str(envelope.get("idempotency_key", "")),
        "envelope_digest": _digest(envelope),
    }


EPISODE_SPEC_SCHEMA_ID = "researchos-episode-spec-v1"
EPISODE_SPEC_DECLARED = ("purpose", "context", "scope_declaration", "rules", "preserve", "authorization", "budget",
                         "ask_cap")


def build_episode_spec(
    *, purpose: Mapping[str, object], context: str, scope: Mapping[str, object], rules: Mapping[str, object],
    preserve: object, authorization: Mapping[str, object], budget: Mapping[str, object],
    source_version_digest: str, cutoff: str, ask_cap: Mapping[str, object] | None = None, decision_point: str = "",
) -> dict[str, object]:
    """Φ_ε of one bounded goal (report D1, CC-6), frozen at its start.

    Φ = (q, κ, Sc, Ver, P^keep, α, β, sv): purpose and its version, the context it serves, the frozen
    scope, the rule and check versions, the preserved conditions, the authorization in force, the
    budget, and the source versions with the decision cutoff. The declared part is everything a
    caller chooses; the scope's extension and the source versions are what the world was at the start.
    Any change to the declared part forms a new episode: a running one keeps the spec it froze."""
    declared = {
        "purpose": dict(purpose),
        "context": _text(context, "context", maximum=240),
        "scope_declaration": {"node": scope.get("scope_node", ""), "cross": scope.get("cross_scope_keys", []),
                              "narrowed_by": scope.get("narrowed_by", "")},
        "rules": {str(key): str(value) for key, value in sorted(dict(rules).items())},
        "preserve": sorted({str(item) for item in (preserve or [])}),
        "authorization": dict(authorization),
        "budget": dict(budget),
        "ask_cap": dict(ask_cap or {"declared": False}),
    }
    return {
        "schema_id": EPISODE_SPEC_SCHEMA_ID,
        **declared,
        "scope_extension": {"member_digest": scope.get("scope_member_digest", ""),
                            "member_count": scope.get("scope_member_count", 0),
                            "frozen_at": scope.get("scope_frozen_at", "")},
        "source_versions": {"digest": _text(source_version_digest, "source_version_digest", maximum=128),
                            "cutoff": _text(cutoff, "cutoff", maximum=64),
                            "decision_point": _text(decision_point, "decision_point", maximum=128)},
        "declared_digest": _digest(declared),
    }


def episode_spec_changes(frozen: Mapping[str, object], proposed: Mapping[str, object]) -> list[str]:
    """Which declared components differ; a non-empty answer means the proposed spec is a new episode."""
    return [key for key in EPISODE_SPEC_DECLARED if frozen.get(key) != proposed.get(key)]
