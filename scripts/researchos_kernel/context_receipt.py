# ResearchOS maintenance header.
# 中文：ContextReceipt v1 的唯一归一化 owner；记录上下文证据轴，不把客户端声明升级为事实或授权。
# English: Sole ContextReceipt v1 normalization owner; records context-evidence axes without promoting client claims into facts or authority.

"""Client-agnostic, digest-only context receipts for ResearchOS."""

from __future__ import annotations

from typing import Any

from .ledger import digest as _digest, is_sha256


CONTEXT_RECEIPT_SCHEMA_ID = "researchos-context-receipt-v1"
RUNTIME_SCOPES = frozenset({"private", "public_starter", "personal_vault"})
EVIDENCE_CLASSES = frozenset({"client_asserted", "server_recorded", "instrumented", "human_attested"})
AXIS_STATES = {
    "authorization": frozenset({"unknown", "unauthorized", "authorized"}),
    "selection": frozenset({"unknown", "not_selected", "selected"}),
    "delivery": frozenset({"unknown", "not_delivered", "delivered"}),
    "observation": frozenset({"unknown", "not_observed", "observed"}),
    "citation": frozenset({"unknown", "not_cited", "cited"}),
    "exclusion": frozenset({"unknown", "not_excluded", "excluded"}),
    "egress": frozenset({"unknown", "not_egressed", "egressed"}),
}
_AXES = tuple(AXIS_STATES)
_TOP_KEYS = {
    "schema_id", "receipt_id", "task_id", "run_id", "runtime_scope",
    "producer", "sources", "rejected_claims",
}
_PRODUCER_KEYS = {"kind", "surface", "evidence_class"}
_SOURCE_KEYS = {"source_id", "kind", "ref_digest", "label_digest", "requested", *_AXES}
_AXIS_KEYS = {"state", "evidence_ref"}


class ContextReceiptContractError(ValueError):
    """Stable contract failure that never echoes source content."""

    def __init__(self, code: str, field: str) -> None:
        super().__init__(code)
        self.code = code
        self.field = field


def _fail(code: str, field: str) -> ContextReceiptContractError:
    return ContextReceiptContractError(code, field)


def source_identity(kind: str, ref: str) -> str:
    """Return the digest-only source identity used by ContextReceipt without exposing the reference."""
    clean_kind = _text(kind, "source.kind", 80, nonempty=True)
    clean_ref = _text(ref, "source.ref", 2048, nonempty=True)
    return f"src:{_digest([clean_kind, _digest(clean_ref)])}"


def _text(value: object, field: str, maximum: int, *, nonempty: bool = False) -> str:
    if not isinstance(value, str) or "\x00" in value or len(value) > maximum:
        raise _fail("context_receipt_invalid_value", field)
    if nonempty and not value.strip():
        raise _fail("context_receipt_invalid_value", field)
    return value


def _record(value: object, field: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise _fail("context_receipt_invalid_shape", field)
    return value


def _axis(
    value: object,
    *,
    axis: str,
    source_id: str,
    trusted: bool,
    rejected: list[dict[str, str]],
) -> dict[str, str]:
    record = _record(value, axis, _AXIS_KEYS)
    state = _text(record.get("state"), f"{axis}.state", 40, nonempty=True)
    evidence_ref = _text(record.get("evidence_ref"), f"{axis}.evidence_ref", 160)
    if state not in AXIS_STATES[axis]:
        raise _fail("context_receipt_invalid_state", f"{axis}.state")
    if state == "unknown" and evidence_ref:
        raise _fail("context_receipt_unknown_has_evidence", f"{axis}.evidence_ref")
    if state != "unknown" and not trusted:
        rejected.append({"source_id": source_id, "axis": axis, "code": "untrusted_claim_rejected"})
        return {"state": "unknown", "evidence_ref": ""}
    if state != "unknown" and not evidence_ref:
        raise _fail("context_receipt_evidence_required", f"{axis}.evidence_ref")
    return {"state": state, "evidence_ref": evidence_ref}


def normalize_context_receipt(value: object, *, trusted_producer: bool = False) -> dict[str, object]:
    """Normalize one receipt; untrusted positive/negative fact claims become explicit rejections."""
    record = _record(value, "receipt", _TOP_KEYS)
    if record.get("schema_id") != CONTEXT_RECEIPT_SCHEMA_ID:
        raise _fail("context_receipt_schema_mismatch", "schema_id")
    runtime_scope = _text(record.get("runtime_scope"), "runtime_scope", 40, nonempty=True)
    if runtime_scope not in RUNTIME_SCOPES:
        raise _fail("context_receipt_invalid_scope", "runtime_scope")
    task_id = _text(record.get("task_id"), "task_id", 80, nonempty=True)
    if not task_id.startswith("task:") or not is_sha256(task_id.removeprefix("task:")):
        raise _fail("context_receipt_invalid_task", "task_id")
    run_id = _text(record.get("run_id"), "run_id", 160, nonempty=True)
    producer = _record(record.get("producer"), "producer", _PRODUCER_KEYS)
    evidence_class = _text(producer.get("evidence_class"), "producer.evidence_class", 40, nonempty=True)
    if evidence_class not in EVIDENCE_CLASSES:
        raise _fail("context_receipt_invalid_evidence_class", "producer.evidence_class")
    if not trusted_producer:
        evidence_class = "client_asserted"
    normalized_producer = {
        "kind": _text(producer.get("kind"), "producer.kind", 120, nonempty=True),
        "surface": _text(producer.get("surface"), "producer.surface", 120, nonempty=True),
        "evidence_class": evidence_class,
    }
    if not isinstance(record.get("sources"), list) or len(record["sources"]) > 20:
        raise _fail("context_receipt_invalid_sources", "sources")
    rejected: list[dict[str, str]] = []
    sources: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, item in enumerate(record["sources"]):
        source = _record(item, f"sources[{index}]", _SOURCE_KEYS)
        kind = _text(source.get("kind"), f"sources[{index}].kind", 80, nonempty=True)
        ref_digest = _text(source.get("ref_digest"), f"sources[{index}].ref_digest", 64, nonempty=True)
        label_digest = _text(source.get("label_digest"), f"sources[{index}].label_digest", 64, nonempty=True)
        if not is_sha256(ref_digest) or not is_sha256(label_digest):
            raise _fail("context_receipt_invalid_digest", f"sources[{index}]")
        if not isinstance(source.get("requested"), bool):
            raise _fail("context_receipt_invalid_value", f"sources[{index}].requested")
        source_id = f"src:{_digest([kind, ref_digest])}"
        if source_id in seen:
            continue
        seen.add(source_id)
        normalized: dict[str, object] = {
            "source_id": source_id,
            "kind": kind,
            "ref_digest": ref_digest,
            "label_digest": label_digest,
            "requested": source["requested"],
        }
        for axis in _AXES:
            normalized[axis] = _axis(
                source.get(axis), axis=axis, source_id=source_id,
                trusted=trusted_producer, rejected=rejected,
            )
        sources.append(normalized)
    normalized_receipt: dict[str, object] = {
        "schema_id": CONTEXT_RECEIPT_SCHEMA_ID,
        "receipt_id": "",
        "task_id": task_id,
        "run_id": run_id,
        "runtime_scope": runtime_scope,
        "producer": normalized_producer,
        "sources": sources,
        "rejected_claims": rejected,
    }
    normalized_receipt["receipt_id"] = f"ctx:{_digest({key: value for key, value in normalized_receipt.items() if key != 'receipt_id'})}"
    return normalized_receipt


def build_requested_context_receipt(
    *, task_id: str, run_id: str, runtime_scope: str,
    producer_kind: str, producer_surface: str, source_refs: object,
) -> dict[str, object]:
    """Record only that untrusted source references were requested; all factual axes remain unknown."""
    if not isinstance(source_refs, list):
        raise _fail("context_receipt_invalid_sources", "source_refs")
    unknown = lambda: {"state": "unknown", "evidence_ref": ""}
    sources = []
    for index, source in enumerate(source_refs):
        if not isinstance(source, dict):
            raise _fail("context_receipt_invalid_sources", f"source_refs[{index}]")
        kind = _text(source.get("kind"), f"source_refs[{index}].kind", 80, nonempty=True)
        ref = _text(source.get("ref"), f"source_refs[{index}].ref", 2048, nonempty=True)
        label = _text(source.get("label"), f"source_refs[{index}].label", 240)
        sources.append({
            "source_id": "",
            "kind": kind,
            "ref_digest": _digest(ref),
            "label_digest": _digest(label),
            "requested": True,
            **{axis: unknown() for axis in _AXES},
        })
    return normalize_context_receipt({
        "schema_id": CONTEXT_RECEIPT_SCHEMA_ID,
        "receipt_id": "",
        "task_id": task_id,
        "run_id": run_id,
        "runtime_scope": runtime_scope,
        "producer": {"kind": producer_kind, "surface": producer_surface, "evidence_class": "client_asserted"},
        "sources": sources,
        "rejected_claims": [],
    })
