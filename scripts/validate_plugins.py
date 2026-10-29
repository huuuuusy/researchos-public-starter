#!/usr/bin/env python3
"""Validate ResearchOS plugin manifests, compatibility, and ownership overlays."""

from __future__ import annotations

import json
from pathlib import Path

from plan_context import ALIASES, task_routes
from researchos_data.plugins import (
    load_plugin_registry,
    ownership_overlay_failures,
    ownership_registry_summary,
    validate_plugin_files,
)
from researchos_data.task_extensions import load_task_extensions, validate_extension_files
from validate_plugin_standard import validate_repository as validate_plugin_standard_repository


ROOT = Path(__file__).resolve().parents[1]


def _base_route_ids() -> set[str]:
    route_ids = {
        str(item.get("id", ""))
        for language in ("en", "zh-CN")
        for item in task_routes(language)
        if not item.get("extension_id")
    }
    return route_ids | set(ALIASES)


def _contribution_identity_failures(key: str, registry: dict[str, object]) -> list[str]:
    """Keep every projected contribution owned by its declaring plugin."""
    failures: list[str] = []
    contributions = registry.get("contributions", {})
    if not isinstance(contributions, dict):
        return [f"{key} contributions must be an object"]
    owned: dict[str, dict[str, dict[str, object]]] = {}
    for contribution_type, items in contributions.items():
        if not isinstance(items, list):
            failures.append(f"{key} contribution family {contribution_type} must be a list")
            continue
        family: dict[str, dict[str, object]] = {}
        for item in items:
            if not isinstance(item, dict):
                failures.append(f"{key} contribution family {contribution_type} contains a non-object")
                continue
            plugin_id = str(item.get("plugin_id", ""))
            contribution_id = str(item.get("id", ""))
            contribution_key = str(item.get("contribution_key", ""))
            expected = f"{plugin_id}:{contribution_id}"
            if contribution_key != expected:
                failures.append(f"{key} {contribution_type} contribution key drifted: {expected}")
            if contribution_key in family:
                failures.append(f"{key} duplicate {contribution_type} contribution key: {contribution_key}")
            family[contribution_key] = item
        owned[str(contribution_type)] = family

    for slot in owned.get("ui_slots", {}).values():
        plugin_id = str(slot.get("plugin_id", ""))
        for field, contribution_type in (("action_ids", "actions"), ("projection_ids", "projections")):
            for contribution_id in slot.get(field, []):
                expected = f"{plugin_id}:{contribution_id}"
                if expected not in owned.get(contribution_type, {}):
                    failures.append(f"{key} UI slot reference escaped plugin namespace: {expected}")
    for provider in owned.get("work_item_providers", {}).values():
        expected = f"{provider.get('plugin_id', '')}:{provider.get('projection_id', '')}"
        if expected not in owned.get("projections", {}):
            failures.append(f"{key} work-item projection escaped plugin namespace: {expected}")
    return failures


def main() -> int:
    standard_failures, _ = validate_plugin_standard_repository(ROOT)
    failures = [
        *standard_failures,
        *validate_plugin_files(ROOT),
        *validate_extension_files(ROOT),
        *ownership_overlay_failures(ROOT),
    ]
    base_route_ids = _base_route_ids()
    registries: dict[str, dict[str, object]] = {}
    for runtime_scope in ("private", "public_starter", "personal_vault"):
        for language in ("en", "zh-CN"):
            key = f"{runtime_scope}:{language}"
            try:
                registry = load_plugin_registry(
                    ROOT,
                    runtime_scope=runtime_scope,
                    language=language,
                    base_task_ids=base_route_ids,
                )
                registries[key] = registry
                failures.extend(_contribution_identity_failures(key, registry))
                legacy = load_task_extensions(
                    ROOT,
                    runtime_scope=runtime_scope,
                    language=language,
                    base_task_ids=base_route_ids,
                )
                compatible = [
                    {
                        field: value
                    for field, value in task.items()
                        if field not in {"plugin_id", "plugin_version", "plugin_origin", "plugin_tier"}
                    }
                    for task in registry["tasks"]
                    if task.get("plugin_origin") == "task_extension_v1"
                ]
                if compatible != legacy["tasks"]:
                    failures.append(f"{key} task-extension compatibility output drifted")
                safe_summary = json.dumps(registry["loaded"], ensure_ascii=False)
                if "config/" in safe_summary or str(ROOT) in safe_summary or "read_paths" in safe_summary:
                    failures.append(f"{key} registry summary exposes source paths or permissions")
            except Exception as error:  # Host validation must fail closed for any assembly error.
                failures.append(f"{key} registry assembly failed: {error}")

    if failures:
        print("ResearchOS plugin validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    ownership = ownership_registry_summary(ROOT)
    print("OK: ResearchOS plugin host v1 and task-extension compatibility satisfy the stable core contract")
    for key, registry in registries.items():
        print(
            f"- {key}: {registry['loaded_count']} loaded, "
            f"{registry['disabled_count']} disabled, {len(registry['tasks'])} contributed tasks, "
            f"tiers={registry['product_tier_counts']}"
        )
    for plane in ("frontend", "style", "data"):
        report = ownership[plane]
        print(
            f"- {plane}: {report['active_owner_count']} active owners, "
            f"{report['logical_owner_count']} logical owners, "
            f"change radius {report['change_radius_by_owner']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
