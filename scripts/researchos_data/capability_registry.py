"""Headless access to canonical capability claims and non-owning capability groups."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path("09_templates/data_contracts/researchos-capability-registry-v1.json")


def load_capability_registry(root: Path) -> dict[str, Any]:
    """Load only the canonical registry owner; callers choose the fields they consume."""
    return json.loads((root / REGISTRY_PATH).read_text(encoding="utf-8"))


def capability_group_map(root: Path) -> dict[str, str]:
    """Map claim ids to display-only groups without changing claim ownership."""
    registry = load_capability_registry(root)
    mapping: dict[str, str] = {}
    for group in registry.get("capability_groups", []):
        group_id = str(group.get("id") or "").strip()
        for claim_id in group.get("claim_ids", []):
            claim = str(claim_id)
            if claim in mapping:
                raise ValueError(f"capability claim belongs to multiple groups: {claim}")
            mapping[claim] = group_id
    return mapping


def grouped_capability_ids(root: Path, capability_ids: list[str]) -> list[str]:
    """Return stable user-surface groups for registered claims and existing group ids."""
    registry = load_capability_registry(root)
    groups = {str(item["id"]) for item in registry.get("capability_groups", [])}
    mapping = capability_group_map(root)
    result: list[str] = []
    for capability_id in capability_ids:
        group_id = mapping.get(capability_id)
        if group_id and group_id not in result:
            result.append(group_id)
        elif capability_id in groups and capability_id not in result:
            result.append(capability_id)
    return result


__all__ = [
    "REGISTRY_PATH",
    "capability_group_map",
    "grouped_capability_ids",
    "load_capability_registry",
]
