# ResearchOS maintenance header.
# 中文：ResearchOS dashboard 前端 classic-script 与 surface manifest；集中声明 index.html 的脚本集合、owner 分层和稳定承载面。
# English: ResearchOS dashboard frontend classic-script and surface manifest; centralizes index.html scripts, owner layers, and stable surfaces.

"""Machine-readable frontend manifest for ResearchOS dashboard refactors."""

from __future__ import annotations

from typing import Any


FRONTEND_SCRIPT_GROUPS: tuple[dict[str, object], ...] = (
    {
        "id": "core",
        "owner": "dashboard/src/core",
        "scripts": (
            "src/core/edition-profile.js",
            "src/core/contracts.js",
            "src/core/state.js",
            "src/core/storage-contract.js",
            "src/core/surface-contract.js",
            "src/core/view-state.js",
            "src/core/ui-preferences.js",
            "src/core/service-mode.js",
            "src/core/ui.js",
            "src/core/interactions.js",
            "src/core/ui-copy-profile.js",
            "src/core/i18n.js",
            "src/core/ui-copy-work-session.js",
            "src/core/ui-copy.js",
            "src/core/i18n-runtime.js",
            "src/core/theme.js",
            "src/core/workspace-routing.js",
            "src/core/preview-state.js",
        ),
    },
    {
        "id": "services",
        "owner": "dashboard/src/services",
        "scripts": (
            "src/services/action-gateway.js",
            "src/services/request-auth.js",
            "src/services/clipboard-workbench.js",
            "src/services/app-copy-actions.js",
            "src/services/confirmation-state.js",
            "src/services/confirmation-client.js",
            "src/services/inbox.js",
            "src/services/runtime-profile-projection.js",
            "src/services/result-envelope.js",
            "src/services/codex-runner-client.js",
            "src/services/model-catalog.js",
            "src/services/preview.js",
            "src/services/preview-content-client.js",
            "src/services/preview-markdown.js",
            "src/services/preview-feedback.js",
            "src/services/feedback-client.js",
            "src/services/preview-feedback-workflow.js",
            "src/services/preview-documents.js",
            "src/services/preview-session-state.js",
            "src/services/preview-surface-workbench.js",
            "src/services/preview-pdf-workbench.js",
            "src/services/maintenance-workbench.js",
            "src/services/maintenance-client.js",
            "src/services/command-list-workbench.js",
            "src/services/markdown-preview-workbench.js",
            "src/services/preview-workbench.js",
            "src/services/material-intake-workbench.js",
            "src/services/onboarding-workbench.js",
            "src/services/action-inbox-state.js",
            "src/services/queue-sync.js",
            "src/services/doing-board-state.js",
            "src/services/codex-run-router.js",
            "src/services/task-intent.js",
            "src/services/handoff-receipt-projection.js",
            "src/services/handoff-admit-surface.js",
            "src/services/work-session-router.js",
            "src/services/work-session-client.js",
            "src/services/work-session-state.js",
            "src/services/context-pack-projection.js",
            "src/services/work-session-workbench.js",
            "src/services/asset-overview-model.js",
            "src/services/item-composition-model.js",
            "src/services/codex-thread-router.js",
            "src/services/handoff-composer.js",
            "src/services/asset-overview-workbench.js",
            "src/services/paper-field-rules.js",
            "src/services/workspace-shell-workbench.js",
            "src/services/plugin-runtime.js",
            "src/services/plugin-host.js",
            "src/services/dashboard-render-plan.js",
            "src/services/dashboard-lifecycle-adapter.js",
            "src/services/dashboard-data-client.js",
            "src/services/daily-profile-refresh-client.js",
            "src/services/agent-prompt.js",
            "src/services/card-group-seeds.js",
            "src/services/card-groups.js",
            "src/services/card-group-state.js",
            "src/services/unified-inbox-workbench.js",
        ),
    },
    {
        "id": "components",
        "owner": "dashboard/src/components",
        "scripts": (
            "src/components/buttons.js",
            "src/components/empty-state.js",
            "src/components/preview-links.js",
            "src/components/metric-primitives.js",
            "src/components/segmented-control.js",
        ),
    },
    {
        "id": "views",
        "owner": "dashboard/src/views",
        "scripts": (
            "src/views/error-page.js",
            "src/views/markdown-preview.js",
            "src/views/pdf-preview.js",
            "src/views/maintenance.js",
            "src/views/handoff-receipt.js",
            "src/views/handoff-admit-surface.js",
            "src/views/work-session.js",
            "src/views/home-command-center.js",
            "src/views/external-evidence.js",
            "src/views/material-intake.js",
            "src/views/onboarding.js",
            "src/views/asset-overview.js",
            "src/views/runtime-profile.js",
            "src/views/unified-inbox.js",
        ),
    },
    {
        "id": "plugins",
        "owner": "dashboard/src/plugins",
        "scripts": (
            "src/plugins/system-stewardship.js",
            "src/plugins/material-pipeline.js",
            "src/plugins/research-assets.js",
            "src/plugins/research-portfolio-copy.js",
            "src/plugins/research-portfolio-model.js",
            "src/plugins/research-portfolio-view.js",
            "src/plugins/research-portfolio-workbench.js",
            "src/plugins/research-portfolio.js",
            "src/plugins/unified-desk-calendar.js",
            "src/plugins/unified-desk-handoff.js",
            "src/plugins/unified-research-desk.js",
        ),
    },
)

APP_SCRIPT = "app.js"

# index.html references every asset without a ?v= cache query: serve_dashboard.py sends
# Cache-Control: no-store, so there is no cache epoch to maintain by hand.

FRONTEND_SCRIPT_ORDER_CONSTRAINTS: tuple[dict[str, str], ...] = (
    *(
        {
            "before": "src/core/edition-profile.js",
            "after": reader,
            "reason": "edition defaults (client profile, default language, server URL) are read from the runtime profile at load time",
        }
        for reader in ("src/core/surface-contract.js", "src/core/ui-preferences.js", "src/core/service-mode.js")
    ),
    *(
        {
            "before": "src/core/ui-copy-profile.js",
            "after": reader,
            "reason": "edition-specific copy entries come from the copy profile, which must exist before the shared catalogs and prompt builder load",
        }
        for reader in (
            "src/core/ui-copy.js",
            "src/services/agent-prompt.js",
            "src/plugins/research-portfolio-copy.js",
        )
    ),
    {
        "before": "src/core/contracts.js",
        "after": "src/core/state.js",
        "reason": "state policy derives durable-state boundaries from the primitive contracts",
    },
    {
        "before": "src/core/storage-contract.js",
        "after": "src/core/surface-contract.js",
        "reason": "surface contract loads after base storage/core setup",
    },
    {
        "before": "src/core/surface-contract.js",
        "after": "src/core/view-state.js",
        "reason": "view-state derives workspace and asset-panel choices from the surface contract",
    },
    {
        "before": "src/core/surface-contract.js",
        "after": "src/core/workspace-routing.js",
        "reason": "workspace routing derives target routes from the surface contract",
    },
    {
        "before": "src/core/ui.js",
        "after": "src/services/clipboard-workbench.js",
        "reason": "clipboard workbench injects core UI helpers",
    },
    {
        "before": "src/services/confirmation-state.js",
        "after": "src/services/confirmation-client.js",
        "reason": "confirmation client receives state-owned payloads before app orchestration",
    },
    {
        "before": "src/services/preview.js",
        "after": "src/services/preview-content-client.js",
        "reason": "preview content client loads beside the preview path service before workbench orchestration",
    },
    {
        "before": "src/services/preview.js",
        "after": "src/services/preview-markdown.js",
        "reason": "preview Markdown rendering needs preview path helpers",
    },
    {
        "before": "src/services/preview-markdown.js",
        "after": "src/services/preview-feedback.js",
        "reason": "preview feedback depends on rendered Markdown context",
    },
    {
        "before": "src/services/preview-feedback.js",
        "after": "src/services/feedback-client.js",
        "reason": "feedback client receives owner-built feedback payloads before workbench submission",
    },
    {
        "before": "src/services/preview-feedback.js",
        "after": "src/services/preview-feedback-workflow.js",
        "reason": "preview feedback workflow builds on record and storage rules",
    },
    {
        "before": "src/services/feedback-client.js",
        "after": "src/services/preview-feedback-workflow.js",
        "reason": "preview feedback workflow submits owner-built payloads through the shared feedback client",
    },
    {
        "before": "src/services/preview-content-client.js",
        "after": "src/services/preview-workbench.js",
        "reason": "preview workbench loads Markdown preview content through the content client",
    },
    {
        "before": "src/services/preview-feedback-workflow.js",
        "after": "src/services/preview-workbench.js",
        "reason": "preview workbench delegates feedback submission and inbox state to the workflow owner",
    },
    {
        "before": "src/services/preview.js",
        "after": "src/services/preview-documents.js",
        "reason": "preview document lookup needs preview path helpers",
    },
    {
        "before": "src/services/preview.js",
        "after": "src/core/preview-state.js",
        "reason": "preview state derives path defaults from preview helpers",
    },
    {
        "before": "src/core/preview-state.js",
        "after": "src/services/preview-session-state.js",
        "reason": "preview session state persists selected/open/history state through the core preview state helper",
    },
    {
        "before": "src/services/preview.js",
        "after": "src/services/preview-session-state.js",
        "reason": "preview session state delegates history normalization and navigation to preview path helpers",
    },
    {
        "before": "src/services/preview.js",
        "after": "src/services/preview-surface-workbench.js",
        "reason": "preview surface workbench needs path helpers",
    },
    {
        "before": "src/services/preview-surface-workbench.js",
        "after": "src/services/preview-pdf-workbench.js",
        "reason": "preview PDF workbench delegates close-button selectors to the surface workbench",
    },
    {
        "before": "src/services/preview-pdf-workbench.js",
        "after": "src/services/preview-workbench.js",
        "reason": "preview orchestration delegates PDF floating-frame state to the PDF workbench",
    },
    {
        "before": "src/services/preview-session-state.js",
        "after": "src/services/preview-workbench.js",
        "reason": "preview workbench delegates local session state and history transitions to preview session state",
    },
    {
        "before": "src/services/markdown-preview-workbench.js",
        "after": "src/services/preview-workbench.js",
        "reason": "preview orchestration binds markdown preview workbench",
    },
    {
        "before": "src/services/asset-overview-model.js",
        "after": "src/services/asset-overview-workbench.js",
        "reason": "asset overview workbench binds model-owned projections",
    },
    {
        "before": "src/services/asset-overview-model.js",
        "after": "src/services/item-composition-model.js",
        "reason": "Unified Desk composition projects registered asset cards into exact item-component relations",
    },
    {
        "before": "src/services/runtime-profile-projection.js",
        "after": "src/services/result-envelope.js",
        "reason": "result normalization delegates selected runtime profile state to the strict browser projection owner",
    },
    {
        "before": "src/services/inbox.js",
        "after": "src/services/result-envelope.js",
        "reason": "result contract normalizes public-safe machine results and failures after inbox data is available",
    },
    {
        "before": "src/services/result-envelope.js",
        "after": "src/services/codex-runner-client.js",
        "reason": "Codex runner client delegates transport result and failure normalization to the result contract",
    },
    {
        "before": "src/services/codex-runner-client.js",
        "after": "src/services/model-catalog.js",
        "reason": "model catalog controller delegates runtime discovery to the Codex runner client",
    },
    {
        "before": "src/services/task-intent.js",
        "after": "src/services/work-session-router.js",
        "reason": "work-session routing projects untrusted client requests through the TaskIntent v1 owner",
    },
    {
        "before": "src/services/work-session-state.js",
        "after": "src/services/context-pack-projection.js",
        "reason": "Library context composition consumes only the normalized Work Session shape",
    },
    {
        "before": "src/views/runtime-profile.js",
        "after": "src/views/unified-inbox.js",
        "reason": "the review surface composes the read-only runtime profile view without owning profile semantics",
    },
    {
        "before": "src/services/handoff-receipt-projection.js",
        "after": "src/views/handoff-receipt.js",
        "reason": "the HandoffReceipt view only renders a strictly normalized server-safe projection",
    },
    {
        "before": "src/services/handoff-admit-surface.js",
        "after": "src/views/handoff-admit-surface.js",
        "reason": "the default-off Handoff/Admit candidate view renders one deterministic surface-mode projection",
    },
    {
        "before": "src/views/handoff-receipt.js",
        "after": "src/views/handoff-admit-surface.js",
        "reason": "the Handoff/Admit candidate composes the read-only receipt view without re-deriving receipt semantics",
    },
    {
        "before": "src/views/handoff-admit-surface.js",
        "after": "src/views/work-session.js",
        "reason": "the legacy Work Session view delegates the reversible third-surface candidate to its dedicated view",
    },
    {
        "before": "src/services/card-group-seeds.js",
        "after": "src/services/card-groups.js",
        "reason": "card-group service delegates seed assembly rules to the seed owner",
    },
    {
        "before": "src/services/workspace-shell-workbench.js",
        "after": "src/services/dashboard-render-plan.js",
        "reason": "dashboard render plan runs after surface shell helpers are available",
    },
    {
        "before": "src/services/dashboard-lifecycle-adapter.js",
        "after": "src/services/dashboard-data-client.js",
        "reason": "dashboard data client loads with the app lifecycle adapters before app startup",
    },
    {
        "before": "src/services/dashboard-render-plan.js",
        "after": "src/services/dashboard-lifecycle-adapter.js",
        "reason": "dashboard lifecycle adapter builds callback sources after render-plan callback names are available",
    },
    {
        "before": "src/services/plugin-runtime.js",
        "after": "src/plugins/system-stewardship.js",
        "reason": "reviewed plugin adapters self-register through the generic runtime",
    },
    {
        "before": "src/services/plugin-runtime.js",
        "after": "src/plugins/material-pipeline.js",
        "reason": "material candidate adapters self-register through the generic plugin runtime",
    },
    {
        "before": "src/services/plugin-runtime.js",
        "after": "src/plugins/research-assets.js",
        "reason": "asset Library and composition candidate adapters self-register through the generic plugin runtime",
    },
    {
        "before": "src/services/plugin-runtime.js",
        "after": "src/plugins/research-portfolio-copy.js",
        "reason": "portfolio-owned language loads through the reviewed plugin layer",
    },
    {
        "before": "src/plugins/research-portfolio-copy.js",
        "after": "src/plugins/research-portfolio-model.js",
        "reason": "portfolio domain projection loads after plugin-owned language and before the reviewed adapter",
    },
    {
        "before": "src/plugins/research-portfolio-model.js",
        "after": "src/plugins/research-portfolio-view.js",
        "reason": "portfolio view receives the plugin-owned responsibility model shape",
    },
    {
        "before": "src/plugins/research-portfolio-view.js",
        "after": "src/plugins/research-portfolio-workbench.js",
        "reason": "portfolio interaction layer loads after its domain view",
    },
    {
        "before": "src/plugins/research-portfolio-workbench.js",
        "after": "src/plugins/research-portfolio.js",
        "reason": "portfolio adapter composes the plugin-owned model, view, and workbench",
    },
    {
        "before": "src/plugins/research-portfolio.js",
        "after": "src/plugins/unified-research-desk.js",
        "reason": "Public-safe Unified Desk composes the reviewed portfolio projection after compatibility adapters register",
    },
    {
        "before": "src/plugins/unified-desk-calendar.js",
        "after": "src/plugins/unified-research-desk.js",
        "reason": "Unified Desk reads its calendar arithmetic when it loads",
    },
    {
        "before": "src/plugins/unified-desk-handoff.js",
        "after": "src/plugins/unified-research-desk.js",
        "reason": "Unified Desk creates its handoff assembly when it loads",
    },
)

FRONTEND_CLIENT_PROFILE_ID = "public_explanatory_v1"

FRONTEND_SURFACE_SCOPES: tuple[dict[str, str], ...] = (
    {
        "id": "now",
        "legacy_id": "agent",
        "kind": "workspace",
        "root_id": "",
        "parent_surface": "",
        "primary_question": "which_commitments_need_attention_and_how_should_each_be_disposed",
        "tab_i18n": "workspace.now",
        "role": "project a public-safe multi-commitment attention portfolio with one disposition and next step per item",
    },
    {
        "id": "library",
        "legacy_id": "assets",
        "kind": "workspace",
        "root_id": "",
        "parent_surface": "",
        "primary_question": "what_context_is_included_excluded_and_allowed_to_leave",
        "tab_i18n": "workspace.assets",
        "role": "use one or a few commitments as a lens over public-safe research objects and context",
    },
    {
        "id": "utility",
        "kind": "slot_host",
        "root_id": "pluginUtilitySlots",
        "parent_surface": "library",
        "primary_question": "",
        "tab_i18n": "",
        "role": "maintenance and validation drawer",
    },
    {
        "id": "preview",
        "kind": "aside",
        "root_id": "markdownPreviewPanel",
        "parent_surface": "any",
        "primary_question": "",
        "tab_i18n": "",
        "role": "markdown preview surface",
    },
)

FRONTEND_ASSET_DETAIL_PANELS: tuple[dict[str, str], ...] = ()

FRONTEND_RENDER_TARGETS: tuple[dict[str, str], ...] = (
    {
        "id": "unifiedInbox",
        "owner_script": "src/views/unified-inbox.js",
        "binding_script": "src/services/unified-inbox-workbench.js",
        "workspace": "now",
        "workspace_route": "true",
        "role": "exact item-local Work continuity and Needs Review drawer projection",
    },
    {
        "id": "assetOverview",
        "owner_script": "src/views/asset-overview.js",
        "binding_script": "src/services/asset-overview-workbench.js",
        "workspace": "library",
        "workspace_route": "true",
        "role": "asset overview projection",
    },
    {
        "id": "homeCommandCenter",
        "owner_script": "src/views/home-command-center.js",
        "binding_script": "src/plugins/research-portfolio.js",
        "workspace": "now",
        "workspace_route": "true",
        "role": "home command center projection",
    },
    {
        "id": "pluginUtilitySlots",
        "owner_script": "src/services/plugin-runtime.js",
        "binding_script": "src/plugins/system-stewardship.js",
        "workspace": "utility",
        "workspace_route": "false",
        "role": "declarative Utility plugin slot host",
    },
    {
        "id": "markdownPreview",
        "owner_script": "src/views/markdown-preview.js",
        "binding_script": "src/services/preview-workbench.js",
        "workspace": "preview",
        "workspace_route": "false",
        "role": "markdown preview projection",
    },
)


FRONTEND_PLUGIN_OWNER_SCRIPTS: dict[str, tuple[str, ...]] = {
    "system_stewardship": (
        "src/plugins/system-stewardship.js",
        "src/services/maintenance-workbench.js",
        "src/services/maintenance-client.js",
        "src/services/command-list-workbench.js",
        "src/views/maintenance.js",
        "src/views/external-evidence.js",
    ),
    "material_pipeline": (
        "src/plugins/material-pipeline.js",
        "src/services/material-intake-workbench.js",
        "src/services/onboarding-workbench.js",
        "src/views/material-intake.js",
        "src/views/onboarding.js",
    ),
    "research_assets": (
        "src/plugins/research-assets.js",
        "src/services/asset-overview-model.js",
        "src/services/asset-overview-workbench.js",
        "src/services/paper-field-rules.js",
        "src/services/card-group-seeds.js",
        "src/services/card-groups.js",
        "src/services/card-group-state.js",
        "src/views/asset-overview.js",
    ),
    "research_portfolio": (
        "src/plugins/research-portfolio-copy.js",
        "src/plugins/research-portfolio-model.js",
        "src/plugins/research-portfolio-view.js",
        "src/plugins/research-portfolio-workbench.js",
        "src/plugins/research-portfolio.js",
    ),
    "unified_research_desk": (
        "src/services/item-composition-model.js",
        "src/services/codex-thread-router.js",
        "src/services/handoff-composer.js",
        "src/plugins/unified-desk-calendar.js",
        "src/plugins/unified-desk-handoff.js",
        "src/plugins/unified-research-desk.js",
    ),
}

FRONTEND_CORE_OWNER_SCRIPTS: dict[str, tuple[str, ...]] = {
    "stable_kernel": (
        "src/core/contracts.js",
        "src/core/state.js",
        "src/core/storage-contract.js",
        "src/core/surface-contract.js",
        "src/core/view-state.js",
        "src/core/workspace-routing.js",
    ),
    "review_kernel": (
        "src/services/confirmation-state.js",
        "src/services/confirmation-client.js",
        "src/services/inbox.js",
        "src/services/action-inbox-state.js",
        "src/services/queue-sync.js",
        "src/services/doing-board-state.js",
        "src/services/unified-inbox-workbench.js",
        "src/views/unified-inbox.js",
    ),
    "work_session_kernel": (
        "src/services/runtime-profile-projection.js",
        "src/services/result-envelope.js",
        "src/services/codex-runner-client.js",
        "src/services/model-catalog.js",
        "src/services/codex-run-router.js",
        "src/services/task-intent.js",
        "src/services/handoff-receipt-projection.js",
        "src/services/handoff-admit-surface.js",
        "src/services/work-session-router.js",
        "src/services/work-session-client.js",
        "src/services/work-session-state.js",
        "src/services/context-pack-projection.js",
        "src/services/work-session-workbench.js",
        "src/services/agent-prompt.js",
        "src/views/handoff-receipt.js",
        "src/views/handoff-admit-surface.js",
        "src/views/work-session.js",
        "src/views/runtime-profile.js",
    ),
}

FRONTEND_PLUGIN_SLOTS = {
    "system_stewardship": "utility|review|workbench",
    "material_pipeline": "workbench|review",
    "research_assets": "library|review",
    "research_portfolio": "workbench",
    "unified_research_desk": "workbench|library|review",
}


def _logical_frontend_owner(script: str) -> dict[str, str]:
    for plugin_id, scripts in FRONTEND_PLUGIN_OWNER_SCRIPTS.items():
        if script in scripts:
            return {
                "logical_owner": plugin_id,
                "owner_kind": "plugin",
                "deployment_role": "capability_guest",
                "plugin_id": plugin_id,
                "payload_contract": f"researchos-{plugin_id.replace('_', '-')}-plugin-payload-v1",
                "render_target_or_slot": FRONTEND_PLUGIN_SLOTS[plugin_id],
                "public_mode": "shared_code_policy_gated",
                "behavior_test": "evals/test_frontend_contract.py",
                "migration_state": "native_plugin_adapter",
                "removal_phase": "not_applicable",
            }
    for owner_id, scripts in FRONTEND_CORE_OWNER_SCRIPTS.items():
        if script in scripts:
            return {
                "logical_owner": owner_id,
                "owner_kind": "core",
                "deployment_role": "headless_kernel_projection",
                "plugin_id": "",
                "payload_contract": f"researchos-{owner_id.replace('_', '-')}-v1",
                "render_target_or_slot": "workbench|library|review",
                "public_mode": "shared_contract",
                "behavior_test": "evals/test_frontend_contract.py",
                "migration_state": "current",
                "removal_phase": "not_applicable",
            }
    if script.startswith("src/components/") or script in {
        "src/services/clipboard-workbench.js",
        "src/services/app-copy-actions.js",
    }:
        owner_id = "ui_platform"
        slot = "shared_ui"
    elif "preview" in script or script.endswith("pdf-preview.js"):
        owner_id = "preview_platform"
        slot = "preview"
    elif script in {
        "src/services/request-auth.js",
        "src/services/action-gateway.js",
        "src/services/feedback-client.js",
        "src/services/dashboard-data-client.js",
        "src/services/work-session-client.js",
        "src/services/plugin-runtime.js",
    }:
        owner_id = "runtime_platform"
        slot = "shared_runtime"
    else:
        owner_id = "application_shell"
        slot = "workbench|library|processing|review|utility"
    return {
        "logical_owner": owner_id,
        "owner_kind": "platform",
        "deployment_role": "optional_application_shell" if owner_id == "application_shell" else "client_platform_adapter",
        "plugin_id": "",
        "payload_contract": "researchos-frontend-platform-v1",
        "render_target_or_slot": slot,
        "public_mode": "shared_contract",
        "behavior_test": "evals/test_frontend_contract.py",
        "migration_state": "current",
        "removal_phase": "not_applicable",
    }


def frontend_logical_ownership() -> tuple[dict[str, str], ...]:
    """Assign every active script to exactly one logical core/platform/plugin owner."""
    return tuple(
        {"owner_path": script, **_logical_frontend_owner(script)}
        for script in frontend_script_load_order()
    )


def frontend_client_shell_entry() -> dict[str, str]:
    """Describe the optional Dashboard entrypoint separately from loaded modules."""
    return {
        "owner_path": APP_SCRIPT,
        "logical_owner": "application_shell",
        "owner_kind": "platform",
        "deployment_role": "optional_application_shell",
        "payload_contract": "researchos-client-shell-v1",
        "render_target_or_slot": "start|library|next|preview|review|utility",
        "public_mode": "copy_only",
        "behavior_test": "evals/test_frontend_contract.py",
        "migration_state": "current",
        "removal_phase": "optional_client",
    }


def frontend_ownership_report() -> dict[str, Any]:
    """Return ownership change-radius and cross-owner load dependencies."""
    ownership = frontend_logical_ownership()
    owner_by_script = {entry["owner_path"]: entry["logical_owner"] for entry in ownership}
    owner_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    for entry in ownership:
        owner_counts[entry["logical_owner"]] = owner_counts.get(entry["logical_owner"], 0) + 1
        kind_counts[entry["owner_kind"]] = kind_counts.get(entry["owner_kind"], 0) + 1
    cross_owner_dependencies = [
        {
            "before": constraint["before"],
            "after": constraint["after"],
            "from_owner": owner_by_script[constraint["before"]],
            "to_owner": owner_by_script[constraint["after"]],
        }
        for constraint in FRONTEND_SCRIPT_ORDER_CONSTRAINTS
        if owner_by_script[constraint["before"]] != owner_by_script[constraint["after"]]
    ]
    return {
        "version": "researchos-frontend-logical-ownership-v1",
        "active_owner_count": len(ownership),
        "logical_owner_count": len(owner_counts),
        "owner_kind_counts": kind_counts,
        "change_radius_by_owner": dict(sorted(owner_counts.items())),
        "cross_owner_load_dependencies": cross_owner_dependencies,
    }


def frontend_script_load_order() -> tuple[str, ...]:
    """Return classic scripts that must load before app.js."""
    scripts: list[str] = []
    for group in FRONTEND_SCRIPT_GROUPS:
        scripts.extend(str(script) for script in group["scripts"])
    return tuple(scripts)


def frontend_surface_ids() -> tuple[str, ...]:
    """Return stable frontend surface scope ids."""
    return tuple(str(surface["id"]) for surface in FRONTEND_SURFACE_SCOPES)


def frontend_workspace_ids() -> tuple[str, ...]:
    """Return top-level workspace tab/panel ids."""
    return tuple(str(surface["id"]) for surface in FRONTEND_SURFACE_SCOPES if surface.get("kind") == "workspace")


def frontend_asset_detail_panel_ids() -> tuple[str, ...]:
    """Return asset-detail panel ids in view-state order."""
    return tuple(str(panel["id"]) for panel in FRONTEND_ASSET_DETAIL_PANELS)


def frontend_render_target_ids() -> tuple[str, ...]:
    """Return stable render-target ids."""
    return tuple(str(target["id"]) for target in FRONTEND_RENDER_TARGETS)


def frontend_workspace_route_map() -> dict[str, str]:
    """Return render targets that must be present in the workspace routing map."""
    return {
        str(target["id"]): str(target["workspace"])
        for target in FRONTEND_RENDER_TARGETS
        if target.get("workspace_route") == "true"
    }


def frontend_manifest_summary() -> dict[str, Any]:
    """Return a compact frontend script manifest summary for validators."""
    scripts = frontend_script_load_order()
    ownership_report = frontend_ownership_report()
    return {
        "version": "researchos-frontend-script-manifest-v1",
        "app_script": APP_SCRIPT,
        "client_profile_id": FRONTEND_CLIENT_PROFILE_ID,
        "script_count": len(scripts),
        "order_constraint_count": len(FRONTEND_SCRIPT_ORDER_CONSTRAINTS),
        "surface_scope_count": len(FRONTEND_SURFACE_SCOPES),
        "asset_detail_panel_count": len(FRONTEND_ASSET_DETAIL_PANELS),
        "render_target_count": len(FRONTEND_RENDER_TARGETS),
        "logical_ownership": ownership_report,
        "client_shell": frontend_client_shell_entry(),
        "groups": [
            {
                "id": group["id"],
                "owner": group["owner"],
                "script_count": len(group["scripts"]),
            }
            for group in FRONTEND_SCRIPT_GROUPS
        ],
    }
