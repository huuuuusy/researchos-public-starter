# ResearchOS maintenance header.
# 中文：Dashboard semantic receipt 的唯一安全投影 owner；只投影已归一化字段，不复制证据引用、路径或 transcript。
# English: Sole safe Dashboard semantic-receipt projection owner; projects normalized fields without evidence refs, paths, or transcripts.

"""Safe, read-only HandoffReceipt projections for dashboard clients."""

from __future__ import annotations

from researchos_kernel.handoff_receipt import HANDOFF_RECEIPT_SCHEMA_ID, normalize_handoff_receipt


HANDOFF_PROJECTION_SCHEMA_ID = "researchos-handoff-projection-v1"


def handoff_projection(receipt: object, *, include_content: bool, trusted_source: bool) -> dict[str, object]:
    """Project one normalized HandoffReceipt; content is explicit and never inferred public-safe."""
    normalized = normalize_handoff_receipt(receipt, trusted_producer=trusted_source)
    if normalized["rejected_claims"]:
        raise ValueError("handoff_projection_rejected_claims")
    source = normalized["source_revision"]

    def statement(name: str) -> dict[str, str]:
        value = normalized[name]
        return {
            "state": str(value["state"]),
            "text": str(value["text"]) if include_content else "",
        }

    forbidden = normalized["forbidden_actions"]
    projection = {
        "schema_id": HANDOFF_PROJECTION_SCHEMA_ID,
        "source_schema_id": HANDOFF_RECEIPT_SCHEMA_ID,
        "handoff_id": normalized["handoff_id"],
        "task_id": normalized["task_id"],
        "runtime_scope": normalized["runtime_scope"],
        "content_state": "included" if include_content else "suppressed",
        "source_revision": {
            "state": source["state"], "source_id": source["source_id"], "value_digest": source["value_digest"],
        },
        "last_judgment": statement("last_judgment"),
        "open_boundary": statement("open_boundary"),
        "next_safe_action": statement("next_safe_action"),
        "forbidden_actions": {
            "state": forbidden["state"], "items": list(forbidden["items"]) if include_content else [],
        },
        "target_client": dict(normalized["target_client"]),
        "limitations": ["projection_not_authority", "target_not_delivery", "no_transcript"],
    }
    return projection
