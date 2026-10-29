# ResearchOS maintenance header.
# 中文：ResearchOS 数据 owner 的插件逻辑归属 overlay；不移动文件，只声明唯一 owner 与迁移阶段。
# English: Plugin logical-ownership overlay for ResearchOS data owners; declares one owner and migration phase without moving files.

"""Logical ownership manifest for active ResearchOS data modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any


DATA_PLUGIN_OWNER_MODULES: dict[str, tuple[str, ...]] = {
    "system_stewardship": (
        "context_freshness.py",
        "health.py",
        "maintenance_pipeline.py",
    ),
    "material_pipeline": (
        "materials.py",
        "paper_scoring.py",
        "paper_stage.py",
        "paper_status.py",
        "understanding.py",
    ),
    "research_assets": (
        "asset_graph.py",
        "card_states.py",
        "asset_hierarchy.py",
        "asset_intelligence.py",
        "asset_relations.py",
        "collaboration_routes.py",
        "dynamic_graph.py",
        "experience.py",
        "material_catalog.py",
        "network_diagnostics.py",
        "paper_assets.py",
        "papers.py",
        "people.py",
        "person_relations.py",
        "relations.py",
        "talks.py",
    ),
    "research_portfolio": (
        "action_hub.py",
        "home.py",
        "mainlines.py",
        "person_actions.py",
        "project_actions.py",
        "projects.py",
        "research_actions.py",
        "research_portfolio.py",
    ),
}

DATA_CORE_OWNER_MODULES: dict[str, tuple[str, ...]] = {
    "stable_kernel": (
        "capability_registry.py",
        "contracts.py",
        "conversation_contract.py",
        "plugin_ownership.py",
        "plugin_lifecycle.py",
        "plugins.py",
        "repository_layout.py",
        "task_extensions.py",
    ),
}

def _logical_data_owner(module_name: str) -> dict[str, str]:
    for plugin_id, modules in DATA_PLUGIN_OWNER_MODULES.items():
        if module_name in modules:
            return {
                "logical_owner": plugin_id,
                "owner_kind": "plugin",
                "plugin_id": plugin_id,
                "payload_contract": f"researchos-{plugin_id.replace('_', '-')}-plugin-projection-v1",
                "render_target_or_slot": "projection|workbench|library|review",
                "public_mode": "shared_code_policy_gated",
                "behavior_test": "scripts/validate_agent_architecture.py",
                "migration_state": "native_plugin_adapter",
                "removal_phase": "not_applicable",
            }
    for owner_id, modules in DATA_CORE_OWNER_MODULES.items():
        if module_name in modules:
            return {
                "logical_owner": owner_id,
                "owner_kind": "core",
                "plugin_id": "",
                "payload_contract": f"researchos-{owner_id.replace('_', '-')}-data-v1",
                "render_target_or_slot": "kernel_port",
                "public_mode": "shared_contract",
                "behavior_test": "scripts/validate_agent_architecture.py",
                "migration_state": "current",
                "removal_phase": "not_applicable",
            }
    return {
        "logical_owner": "data_platform",
        "owner_kind": "platform",
        "plugin_id": "",
        "payload_contract": "researchos-data-platform-v1",
        "render_target_or_slot": "projection_adapter",
        "public_mode": "shared_contract",
        "behavior_test": "scripts/validate_agent_architecture.py",
        "migration_state": "current",
        "removal_phase": "not_applicable",
    }


def data_logical_ownership(root: Path) -> tuple[dict[str, str], ...]:
    """Assign every active researchos_data module to one logical owner."""
    data_dir = root / "scripts" / "researchos_data"
    return tuple(
        {
            "owner_path": path.relative_to(root).as_posix(),
            **_logical_data_owner(path.name),
        }
        for path in sorted(data_dir.glob("*.py"))
    )


def data_ownership_report(root: Path) -> dict[str, Any]:
    """Return data-owner change radius grouped by logical owner."""
    ownership = data_logical_ownership(root)
    owner_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    for entry in ownership:
        owner_counts[entry["logical_owner"]] = owner_counts.get(entry["logical_owner"], 0) + 1
        kind_counts[entry["owner_kind"]] = kind_counts.get(entry["owner_kind"], 0) + 1
    return {
        "version": "researchos-data-logical-ownership-v1",
        "active_owner_count": len(ownership),
        "logical_owner_count": len(owner_counts),
        "owner_kind_counts": kind_counts,
        "change_radius_by_owner": dict(sorted(owner_counts.items())),
    }
