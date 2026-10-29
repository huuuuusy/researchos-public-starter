# ResearchOS maintenance header.
# 中文：ResearchOS dashboard 样式 owner manifest；集中声明样式层、入口 import 顺序和 owner 归属。
# English: ResearchOS dashboard style owner manifest; centralizes style layers, entry imports, and owner boundaries.

"""Machine-readable style owner manifest for ResearchOS dashboard refactors."""

from __future__ import annotations

from typing import Any


STYLE_LAYER_IMPORTS: tuple[dict[str, str], ...] = (
    {"id": "tokens", "path": "./styles/tokens.css", "layer": "tokens", "owner": "style-token"},
    {"id": "base", "path": "./styles/base.css", "layer": "reset", "owner": "style-base"},
    {"id": "shell", "path": "./styles/shell.css", "layer": "shell", "owner": "style-shell"},
    {"id": "shell-topbar", "path": "./styles/shell/topbar.css", "layer": "shell", "owner": "style-shell"},
    {"id": "shell-workspace", "path": "./styles/shell/workspace.css", "layer": "shell", "owner": "style-shell"},
    {"id": "component-panels", "path": "./styles/components/panels.css", "layer": "components", "owner": "style-component"},
    {"id": "component-empty-state", "path": "./styles/components/empty-state.css", "layer": "components", "owner": "style-component"},
    {"id": "component-badges", "path": "./styles/components/badges.css", "layer": "components", "owner": "style-component"},
    {"id": "component-cards", "path": "./styles/components/cards.css", "layer": "components", "owner": "style-component"},
    {"id": "component-drawers", "path": "./styles/components/drawers.css", "layer": "components", "owner": "style-component"},
    {"id": "component-forms", "path": "./styles/components/forms.css", "layer": "components", "owner": "style-component"},
    {"id": "component-progress", "path": "./styles/components/progress.css", "layer": "components", "owner": "style-component"},
    {"id": "component-buttons", "path": "./styles/components/buttons.css", "layer": "components", "owner": "style-component"},
    {"id": "view-work-session", "path": "./styles/views/work-session.css", "layer": "views", "owner": "style-view"},
    {"id": "view-today-review", "path": "./styles/views/today-review.css", "layer": "views", "owner": "style-view"},
    {"id": "view-research-portfolio", "path": "./styles/views/research-portfolio.css", "layer": "views", "owner": "style-view"},
    {"id": "view-maintenance", "path": "./styles/views/maintenance.css", "layer": "views", "owner": "style-view"},
    {"id": "view-asset-overview", "path": "./styles/views/asset-overview.css", "layer": "views", "owner": "style-view"},
    {"id": "view-onboarding", "path": "./styles/views/onboarding.css", "layer": "views", "owner": "style-view"},
    {"id": "view-unified-inbox", "path": "./styles/views/unified-inbox.css", "layer": "views", "owner": "style-view"},
    {"id": "view-unified-inbox-sources", "path": "./styles/views/unified-inbox/sources.css", "layer": "views", "owner": "style-view"},
    {"id": "view-unified-inbox-ledger", "path": "./styles/views/unified-inbox/ledger.css", "layer": "views", "owner": "style-view"},
    {"id": "view-unified-inbox-tones", "path": "./styles/views/unified-inbox/tones.css", "layer": "views", "owner": "style-view"},
    {"id": "view-external-evidence", "path": "./styles/views/external-evidence.css", "layer": "views", "owner": "style-view"},
    {"id": "view-unified-desk", "path": "./styles/unified-desk.css", "layer": "views", "owner": "style-view"},
    {"id": "preview", "path": "./styles/preview.css", "layer": "preview", "owner": "style-preview"},
    {"id": "preview-markdown", "path": "./styles/preview/markdown.css", "layer": "preview", "owner": "style-preview"},
    {"id": "preview-pdf", "path": "./styles/preview/pdf.css", "layer": "preview", "owner": "style-preview"},
    {"id": "utilities", "path": "./styles/utilities.css", "layer": "utilities", "owner": "style-utility"},
    {"id": "responsive", "path": "./styles/responsive.css", "layer": "responsive", "owner": "style-responsive"},
)

STYLE_OWNER_GROUPS: tuple[dict[str, object], ...] = (
    {"id": "style-token", "owns": ("semantic tokens", "color/radius/shadow/type tokens"), "must_not_own": ("layout selectors",)},
    {"id": "style-base", "owns": ("reset rules", "base element behavior"), "must_not_own": ("view layout",)},
    {"id": "style-shell", "owns": ("dashboard shell layout", "topbar chrome", "workspace chrome"), "must_not_own": ("view-specific cards",)},
    {"id": "style-component", "owns": ("shared visual primitives", "component-local responsive rules"), "must_not_own": ("view-specific layout",)},
    {"id": "style-view", "owns": ("view-specific layout", "view-local states"), "must_not_own": ("global tokens",)},
    {"id": "style-preview", "owns": ("preview chrome", "Markdown preview content", "PDF preview frame", "preview-local responsive rules"), "must_not_own": ("dashboard shell layout",)},
    {"id": "style-utility", "owns": ("small cross-view helpers",), "must_not_own": ("semantic tokens",)},
    {"id": "style-responsive", "owns": ("global base/shell breakpoints", "unresolved responsive scaffolding"), "must_not_own": ("owner-local breakpoints",)},
)


STYLE_PLUGIN_OWNER_IDS: dict[str, tuple[str, ...]] = {
    "system_stewardship": ("view-maintenance", "view-external-evidence"),
    "material_pipeline": ("view-onboarding",),
    "research_assets": ("view-asset-overview",),
    "research_portfolio": ("view-research-portfolio",),
    "unified_research_desk": ("view-unified-desk",),
}

STYLE_CORE_OWNER_IDS: dict[str, tuple[str, ...]] = {
    "work_session_kernel": ("view-work-session",),
    "review_kernel": (
        "view-today-review",
        "view-unified-inbox",
        "view-unified-inbox-sources",
        "view-unified-inbox-ledger",
        "view-unified-inbox-tones",
    ),
    "application_shell": ("shell", "shell-topbar", "shell-workspace"),
}

def _logical_style_owner(entry: dict[str, str]) -> dict[str, str]:
    entry_id = entry["id"]
    for plugin_id, entry_ids in STYLE_PLUGIN_OWNER_IDS.items():
        if entry_id in entry_ids:
            return {
                "logical_owner": plugin_id,
                "owner_kind": "plugin",
                "plugin_id": plugin_id,
                "payload_contract": f"researchos-{plugin_id.replace('_', '-')}-plugin-view-v1",
                "render_target_or_slot": {
                    "system_stewardship": "utility",
                    "material_pipeline": "workbench|library",
                    "research_assets": "library|review",
                    "research_portfolio": "workbench",
                    "unified_research_desk": "workbench|library|review",
                }[plugin_id],
                "public_mode": "shared_code_policy_gated",
                "behavior_test": "evals/test_frontend_contract.py",
                "migration_state": "native_plugin_adapter",
                "removal_phase": "not_applicable",
            }
    for owner_id, entry_ids in STYLE_CORE_OWNER_IDS.items():
        if entry_id in entry_ids:
            return {
                "logical_owner": owner_id,
                "owner_kind": "core",
                "plugin_id": "",
                "payload_contract": f"researchos-{owner_id.replace('_', '-')}-view-v1",
                "render_target_or_slot": "workbench|library|review",
                "public_mode": "shared_contract",
                "behavior_test": "evals/test_frontend_contract.py",
                "migration_state": "current",
                "removal_phase": "not_applicable",
            }
    return {
        "logical_owner": "style_platform",
        "owner_kind": "platform",
        "plugin_id": "",
        "payload_contract": "researchos-style-platform-v1",
        "render_target_or_slot": "shared_style|preview",
        "public_mode": "shared_contract",
        "behavior_test": "evals/test_frontend_contract.py",
        "migration_state": "current",
        "removal_phase": "not_applicable",
    }


def style_logical_ownership() -> tuple[dict[str, str], ...]:
    """Assign every active stylesheet to one logical owner without moving files."""
    return tuple(
        {"owner_path": entry["path"], **_logical_style_owner(entry)}
        for entry in STYLE_LAYER_IMPORTS
    )


def style_ownership_report() -> dict[str, Any]:
    """Return style ownership change radius grouped by logical owner."""
    ownership = style_logical_ownership()
    owner_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    for entry in ownership:
        owner_counts[entry["logical_owner"]] = owner_counts.get(entry["logical_owner"], 0) + 1
        kind_counts[entry["owner_kind"]] = kind_counts.get(entry["owner_kind"], 0) + 1
    return {
        "version": "researchos-style-logical-ownership-v1",
        "active_owner_count": len(ownership),
        "logical_owner_count": len(owner_counts),
        "owner_kind_counts": kind_counts,
        "change_radius_by_owner": dict(sorted(owner_counts.items())),
    }


def style_import_statement(entry: dict[str, str]) -> str:
    """Return the import statement for a style manifest entry."""
    return f'@import url("{entry["path"]}") layer({entry["layer"]});'


def ordered_style_imports() -> tuple[str, ...]:
    """Return dashboard/style.css imports in canonical cascade order."""
    return tuple(style_import_statement(entry) for entry in STYLE_LAYER_IMPORTS)


def style_owner_summary() -> dict[str, Any]:
    """Return a compact style owner summary for validators."""
    return {
        "version": "researchos-style-owner-v1",
        "import_count": len(STYLE_LAYER_IMPORTS),
        "logical_ownership": style_ownership_report(),
        "owners": [group["id"] for group in STYLE_OWNER_GROUPS],
        "imports": [
            {
                "id": entry["id"],
                "path": entry["path"],
                "layer": entry["layer"],
                "owner": entry["owner"],
            }
            for entry in STYLE_LAYER_IMPORTS
        ],
    }
