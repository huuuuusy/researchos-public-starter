#!/usr/bin/env python3
"""Validate client-agnostic ContextReceipt and HandoffReceipt owner/schema alignment."""

from __future__ import annotations

import json
from pathlib import Path

from researchos_kernel.context_receipt import AXIS_STATES, CONTEXT_RECEIPT_SCHEMA_ID
from researchos_kernel.handoff_receipt import HANDOFF_RECEIPT_SCHEMA_ID, REVISION_SCHEMES
from researchos_server.receipt_projection import HANDOFF_PROJECTION_SCHEMA_ID


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_SCHEMA = ROOT / "09_templates/data_contracts/researchos-context-receipt-v1.schema.json"
HANDOFF_SCHEMA = ROOT / "09_templates/data_contracts/researchos-handoff-receipt-v1.schema.json"
HANDOFF_PROJECTION_SCHEMA = ROOT / "09_templates/data_contracts/researchos-handoff-projection-v1.schema.json"


def failures() -> list[str]:
    problems: list[str] = []
    context = json.loads(CONTEXT_SCHEMA.read_text(encoding="utf-8"))
    handoff = json.loads(HANDOFF_SCHEMA.read_text(encoding="utf-8"))
    projection = json.loads(HANDOFF_PROJECTION_SCHEMA.read_text(encoding="utf-8"))
    if context.get("properties", {}).get("schema_id", {}).get("const") != CONTEXT_RECEIPT_SCHEMA_ID:
        problems.append("ContextReceipt owner/schema id mismatch")
    context_axes = set(context.get("properties", {}).get("rejected_claims", {}).get("items", {}).get("properties", {}).get("axis", {}).get("enum", []))
    if context_axes != set(AXIS_STATES):
        problems.append("ContextReceipt axis vocabulary mismatch")
    if handoff.get("properties", {}).get("schema_id", {}).get("const") != HANDOFF_RECEIPT_SCHEMA_ID:
        problems.append("HandoffReceipt owner/schema id mismatch")
    revision_schemes = set(
        handoff.get("properties", {}).get("source_revision", {}).get("allOf", [{}, {}])[1]
        .get("then", {}).get("properties", {}).get("scheme", {}).get("enum", [])
    )
    if revision_schemes != set(REVISION_SCHEMES):
        problems.append("HandoffReceipt revision vocabulary mismatch")
    if handoff.get("properties", {}).get("target_client", {}).get("properties", {}).get("binding_state", {}).get("const") != "requested":
        problems.append("HandoffReceipt target client must remain routing-only")
    if projection.get("properties", {}).get("schema_id", {}).get("const") != HANDOFF_PROJECTION_SCHEMA_ID:
        problems.append("HandoffReceipt projection owner/schema id mismatch")
    limitations = projection.get("properties", {}).get("limitations", {}).get("prefixItems", [])
    if [item.get("const") for item in limitations] != [
        "projection_not_authority", "target_not_delivery", "no_transcript"
    ]:
        problems.append("HandoffReceipt projection limitations must remain explicit and ordered")
    return problems


def main() -> int:
    problems = failures()
    if problems:
        print("Semantic receipt validation failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("OK: ContextReceipt and HandoffReceipt semantic contracts are aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
