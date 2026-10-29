"""Headless public plugin portfolio derived from declarative contributions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from researchos_data.capability_registry import capability_group_map, load_capability_registry


def build_plugin_portfolio(root: Path, loaded: list[dict[str, Any]]) -> dict[str, Any]:
    group_by_claim = capability_group_map(root)
    group_order = [str(item["id"]) for item in load_capability_registry(root).get("capability_groups", [])]
    groups: dict[str, list[str]] = {group_id: [] for group_id in group_order}
    optional: list[dict[str, Any]] = []
    for plugin in loaded:
        claim_ids = plugin.get("capability_claim_ids", []) if plugin.get("enabled", True) else []
        for claim_id in claim_ids:
            group_id = group_by_claim.get(str(claim_id))
            if group_id and plugin["id"] not in groups[group_id]:
                groups[group_id].append(plugin["id"])
        if plugin.get("product_tier") == "optional_extension":
            comparison = str(plugin.get("comparison_status") or "not_evaluated")
            optional.append({
                "id": plugin["id"],
                "enabled": bool(plugin.get("enabled", True)),
                "disposition": "instrumented_optional",
                "user_install_item": True,
                "comparison_status": comparison,
                "route_eligible": bool(plugin.get("enabled", True)) and comparison == "evaluated",
                "route_gate": "disabled" if not plugin.get("enabled", True) else (
                    "exact_trigger_required" if comparison == "evaluated" else "comparison_not_evaluated"
                ),
            })
    return {
        "schema_id": "researchos-headless-plugin-portfolio-v1",
        "owner_semantics": "grouping_only_manifest_and_claim_owners_remain_distinct",
        "runtime_scope": "public_starter",
        "headless_default": True,
        "legacy_ui_fields_consumed": False,
        "execution": "copy_only",
        "canonical_write": False,
        "groups": [{"id": group_id, "plugin_ids": groups[group_id]} for group_id in group_order],
        "optional_extensions": optional,
        "optional_route_policy": "installed_enabled_exact_trigger_and_evaluated_comparison_only",
    }


def _entry(plugin: dict[str, Any]) -> dict[str, Any]:
    governance = plugin["governance"]
    task_contract = governance.get("task_contract") or {}
    comparison = governance.get("comparison") or {}
    return {
        "id": plugin["id"],
        "enabled": plugin["enabled"],
        "product_tier": plugin["product_tier"],
        "capability_claim_ids": sorted({
            claim_id
            for binding in governance.get("capability_bindings", [])
            for claim_id in binding.get("claim_ids", [])
        }),
        "comparison_status": task_contract.get("comparison_status") or comparison.get("status") or "not_evaluated",
    }


def current_plugin_portfolio(root: Path, *, runtime_scope: str = "public_starter") -> dict[str, Any]:
    from researchos_data.plugins import PluginManifestError, validated_plugin_manifests

    if runtime_scope not in {"public_starter", "personal_vault"}:
        raise PluginManifestError(f"unsupported runtime scope: {runtime_scope}")
    entries = [
        _entry(plugin) for plugin in validated_plugin_manifests(root)
        if runtime_scope in plugin["available_in"]
    ]
    return {**build_plugin_portfolio(root, entries), "runtime_scope": runtime_scope}


__all__ = ["build_plugin_portfolio", "current_plugin_portfolio"]
