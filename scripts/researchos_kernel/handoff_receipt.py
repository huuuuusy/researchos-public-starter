# ResearchOS maintenance header.
# 中文：HandoffReceipt v1 的唯一归一化 owner；从来源版本与既有回执生成语义交接，不复制聊天或产生 authority。
# English: Sole HandoffReceipt v1 normalization owner; derives semantic handoffs from source revisions and receipts without copying chat or creating authority.

"""Deterministic, client-agnostic handoff receipts for ResearchOS."""

from __future__ import annotations

from typing import Any

from .context_receipt import CONTEXT_RECEIPT_SCHEMA_ID, RUNTIME_SCOPES, normalize_context_receipt
from .ledger import digest as _digest, is_sha256


HANDOFF_RECEIPT_SCHEMA_ID = "researchos-handoff-receipt-v1"
EVIDENCE_CLASSES = frozenset({"client_asserted", "server_recorded", "tool_recorded", "human_attested"})
REVISION_SCHEMES = frozenset({"sha256", "git_commit", "etag", "version"})
_TOP_KEYS = {
    "schema_id", "handoff_id", "task_id", "runtime_scope", "producer", "source_revision",
    "context_receipt_ref", "last_judgment", "open_boundary", "next_safe_action",
    "forbidden_actions", "target_client", "rejected_claims",
}
_PRODUCER_KEYS = {"kind", "surface", "evidence_class"}
_REVISION_KEYS = {"state", "source_id", "scheme", "value_digest", "evidence_ref"}
_CONTEXT_REF_KEYS = {"schema_id", "receipt_id", "receipt_digest", "binding_state"}
_STATEMENT_KEYS = {"state", "text", "evidence_ref"}
_FORBIDDEN_KEYS = {"state", "items", "evidence_ref"}
_TARGET_KEYS = {"kind", "surface", "binding_state"}
_STATEMENT_STATES = {
    "last_judgment": frozenset({"unknown", "candidate", "human_recorded"}),
    "open_boundary": frozenset({"unknown", "recorded"}),
    "next_safe_action": frozenset({"unknown", "recommended"}),
}


class HandoffReceiptContractError(ValueError):
    """Stable contract failure that never echoes research content."""

    def __init__(self, code: str, field: str) -> None:
        super().__init__(code)
        self.code = code
        self.field = field


def _fail(code: str, field: str) -> HandoffReceiptContractError:
    return HandoffReceiptContractError(code, field)


def _text(value: object, field: str, maximum: int, *, nonempty: bool = False) -> str:
    if not isinstance(value, str) or "\x00" in value or len(value) > maximum:
        raise _fail("handoff_receipt_invalid_value", field)
    if nonempty and not value.strip():
        raise _fail("handoff_receipt_invalid_value", field)
    return value


def _record(value: object, field: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise _fail("handoff_receipt_invalid_shape", field)
    return value


def _statement(
    value: object, *, field: str, trusted: bool, rejected: list[dict[str, str]], maximum: int = 2000,
) -> dict[str, str]:
    record = _record(value, field, _STATEMENT_KEYS)
    state = _text(record.get("state"), f"{field}.state", 40, nonempty=True)
    text = _text(record.get("text"), f"{field}.text", maximum)
    evidence_ref = _text(record.get("evidence_ref"), f"{field}.evidence_ref", 160)
    if state not in _STATEMENT_STATES[field]:
        raise _fail("handoff_receipt_invalid_state", f"{field}.state")
    if state == "unknown" and (text or evidence_ref):
        raise _fail("handoff_receipt_unknown_has_content", field)
    if state != "unknown" and not trusted:
        rejected.append({"field": field, "code": "untrusted_claim_rejected"})
        return {"state": "unknown", "text": "", "evidence_ref": ""}
    if state != "unknown" and (not text.strip() or not evidence_ref):
        raise _fail("handoff_receipt_evidence_required", field)
    if field == "last_judgment" and state == "human_recorded" and not evidence_ref.startswith("decision:"):
        raise _fail("handoff_receipt_human_decision_required", field)
    return {"state": state, "text": text, "evidence_ref": evidence_ref}


def _forbidden(
    value: object, *, trusted: bool, rejected: list[dict[str, str]],
) -> dict[str, object]:
    record = _record(value, "forbidden_actions", _FORBIDDEN_KEYS)
    state = _text(record.get("state"), "forbidden_actions.state", 40, nonempty=True)
    items = record.get("items")
    evidence_ref = _text(record.get("evidence_ref"), "forbidden_actions.evidence_ref", 160)
    if state not in {"unknown", "recorded"} or not isinstance(items, list) or len(items) > 8:
        raise _fail("handoff_receipt_invalid_state", "forbidden_actions")
    normalized_items = [_text(item, f"forbidden_actions.items[{index}]", 500, nonempty=True) for index, item in enumerate(items)]
    if state == "unknown" and (normalized_items or evidence_ref):
        raise _fail("handoff_receipt_unknown_has_content", "forbidden_actions")
    if state == "recorded" and not trusted:
        rejected.append({"field": "forbidden_actions", "code": "untrusted_claim_rejected"})
        return {"state": "unknown", "items": [], "evidence_ref": ""}
    if state == "recorded" and (not normalized_items or not evidence_ref):
        raise _fail("handoff_receipt_evidence_required", "forbidden_actions")
    return {"state": state, "items": normalized_items, "evidence_ref": evidence_ref}


def normalize_handoff_receipt(value: object, *, trusted_producer: bool = False) -> dict[str, object]:
    """Normalize one handoff; untrusted factual or judgment claims become explicit unknowns."""
    record = _record(value, "receipt", _TOP_KEYS)
    if record.get("schema_id") != HANDOFF_RECEIPT_SCHEMA_ID:
        raise _fail("handoff_receipt_schema_mismatch", "schema_id")
    task_id = _text(record.get("task_id"), "task_id", 80, nonempty=True)
    if not task_id.startswith("task:") or not is_sha256(task_id.removeprefix("task:")):
        raise _fail("handoff_receipt_invalid_task", "task_id")
    runtime_scope = _text(record.get("runtime_scope"), "runtime_scope", 40, nonempty=True)
    if runtime_scope not in RUNTIME_SCOPES:
        raise _fail("handoff_receipt_invalid_scope", "runtime_scope")
    producer = _record(record.get("producer"), "producer", _PRODUCER_KEYS)
    evidence_class = _text(producer.get("evidence_class"), "producer.evidence_class", 40, nonempty=True)
    if evidence_class not in EVIDENCE_CLASSES:
        raise _fail("handoff_receipt_invalid_evidence_class", "producer.evidence_class")
    if not trusted_producer:
        evidence_class = "client_asserted"
    normalized_producer = {
        "kind": _text(producer.get("kind"), "producer.kind", 120, nonempty=True),
        "surface": _text(producer.get("surface"), "producer.surface", 120, nonempty=True),
        "evidence_class": evidence_class,
    }
    rejected: list[dict[str, str]] = []
    revision = _record(record.get("source_revision"), "source_revision", _REVISION_KEYS)
    revision_state = _text(revision.get("state"), "source_revision.state", 40, nonempty=True)
    source_id = _text(revision.get("source_id"), "source_revision.source_id", 68)
    scheme = _text(revision.get("scheme"), "source_revision.scheme", 40)
    value_digest = _text(revision.get("value_digest"), "source_revision.value_digest", 64)
    revision_evidence = _text(revision.get("evidence_ref"), "source_revision.evidence_ref", 160)
    if revision_state not in {"unknown", "verified"}:
        raise _fail("handoff_receipt_invalid_state", "source_revision.state")
    if revision_state == "unknown" and any((source_id, scheme, value_digest, revision_evidence)):
        raise _fail("handoff_receipt_unknown_has_content", "source_revision")
    if revision_state == "verified" and not trusted_producer:
        rejected.append({"field": "source_revision", "code": "untrusted_claim_rejected"})
        normalized_revision = {"state": "unknown", "source_id": "", "scheme": "", "value_digest": "", "evidence_ref": ""}
    else:
        if revision_state == "verified" and (
            not source_id.startswith("src:") or not is_sha256(source_id.removeprefix("src:"))
            or scheme not in REVISION_SCHEMES or not is_sha256(value_digest) or not revision_evidence
        ):
            raise _fail("handoff_receipt_revision_unverified", "source_revision")
        normalized_revision = {
            "state": revision_state, "source_id": source_id, "scheme": scheme,
            "value_digest": value_digest, "evidence_ref": revision_evidence,
        }
    context_ref = _record(record.get("context_receipt_ref"), "context_receipt_ref", _CONTEXT_REF_KEYS)
    if context_ref.get("schema_id") != CONTEXT_RECEIPT_SCHEMA_ID:
        raise _fail("handoff_receipt_context_mismatch", "context_receipt_ref.schema_id")
    context_id = _text(context_ref.get("receipt_id"), "context_receipt_ref.receipt_id", 68, nonempty=True)
    context_digest = _text(context_ref.get("receipt_digest"), "context_receipt_ref.receipt_digest", 64, nonempty=True)
    binding_state = _text(context_ref.get("binding_state"), "context_receipt_ref.binding_state", 40, nonempty=True)
    if not context_id.startswith("ctx:") or not is_sha256(context_id.removeprefix("ctx:")) or not is_sha256(context_digest):
        raise _fail("handoff_receipt_context_mismatch", "context_receipt_ref")
    if binding_state not in {"claimed", "verified"}:
        raise _fail("handoff_receipt_invalid_state", "context_receipt_ref.binding_state")
    if binding_state == "verified" and not trusted_producer:
        rejected.append({"field": "context_receipt_ref", "code": "untrusted_claim_rejected"})
        binding_state = "claimed"
    target = _record(record.get("target_client"), "target_client", _TARGET_KEYS)
    if target.get("binding_state") != "requested":
        raise _fail("handoff_receipt_invalid_state", "target_client.binding_state")
    normalized: dict[str, object] = {
        "schema_id": HANDOFF_RECEIPT_SCHEMA_ID, "handoff_id": "", "task_id": task_id,
        "runtime_scope": runtime_scope, "producer": normalized_producer,
        "source_revision": normalized_revision,
        "context_receipt_ref": {
            "schema_id": CONTEXT_RECEIPT_SCHEMA_ID, "receipt_id": context_id,
            "receipt_digest": context_digest, "binding_state": binding_state,
        },
        "last_judgment": _statement(record.get("last_judgment"), field="last_judgment", trusted=trusted_producer, rejected=rejected),
        "open_boundary": _statement(record.get("open_boundary"), field="open_boundary", trusted=trusted_producer, rejected=rejected),
        "next_safe_action": _statement(record.get("next_safe_action"), field="next_safe_action", trusted=trusted_producer, rejected=rejected),
        "forbidden_actions": _forbidden(record.get("forbidden_actions"), trusted=trusted_producer, rejected=rejected),
        "target_client": {
            "kind": _text(target.get("kind"), "target_client.kind", 120, nonempty=True),
            "surface": _text(target.get("surface"), "target_client.surface", 120, nonempty=True),
            "binding_state": "requested",
        },
        "rejected_claims": rejected,
    }
    normalized["handoff_id"] = f"handoff:{_digest({key: item for key, item in normalized.items() if key != 'handoff_id'})}"
    return normalized


def build_handoff_receipt(
    *, context_receipt: object, source_id: str, revision_scheme: str, revision_value: str,
    revision_evidence_ref: str, producer_kind: str, producer_surface: str, evidence_class: str,
    last_judgment: dict[str, str], open_boundary: dict[str, str], next_safe_action: dict[str, str],
    forbidden_actions: dict[str, object], target_client: dict[str, str],
) -> dict[str, object]:
    """Build a trusted handoff from one exact ContextReceipt and one verified source revision."""
    context = normalize_context_receipt(context_receipt, trusted_producer=True)
    source_ids = {str(item.get("source_id", "")) for item in context["sources"] if isinstance(item, dict)}
    if source_id not in source_ids:
        raise _fail("handoff_receipt_source_not_in_context", "source_revision.source_id")
    revision_value = _text(revision_value, "source_revision.value", 2048, nonempty=True)
    return normalize_handoff_receipt({
        "schema_id": HANDOFF_RECEIPT_SCHEMA_ID, "handoff_id": "", "task_id": context["task_id"],
        "runtime_scope": context["runtime_scope"],
        "producer": {"kind": producer_kind, "surface": producer_surface, "evidence_class": evidence_class},
        "source_revision": {
            "state": "verified", "source_id": source_id, "scheme": revision_scheme,
            "value_digest": _digest(revision_value), "evidence_ref": revision_evidence_ref,
        },
        "context_receipt_ref": {
            "schema_id": CONTEXT_RECEIPT_SCHEMA_ID, "receipt_id": context["receipt_id"],
            "receipt_digest": _digest(context), "binding_state": "verified",
        },
        "last_judgment": last_judgment, "open_boundary": open_boundary,
        "next_safe_action": next_safe_action, "forbidden_actions": forbidden_actions,
        "target_client": {**target_client, "binding_state": "requested"}, "rejected_claims": [],
    }, trusted_producer=True)
