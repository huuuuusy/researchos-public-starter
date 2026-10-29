#!/usr/bin/env python3
"""Validate the public controlled-evolution contract and privacy boundary."""

from __future__ import annotations

import json
from pathlib import Path

from researchos_data.maintenance_pipeline import (
    FULL_REVIEW_MARKDOWN_RATIO,
    MAX_CHANGED_PATHS,
    MAX_VISIBLE_PATHS,
    RESEARCHOS_MAINTENANCE_STEPS,
    maintenance_plan,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "09_templates/data_contracts/researchos-evolution-control-v1.json"
DOC_EN = ROOT / "docs/self-evolution-control-plane.en.md"
DOC_ZH = ROOT / "docs/self-evolution-control-plane.zh.md"
PLANNER_PATH = ROOT / "scripts/researchos_server/evolution_planner.py"
RUNNER_PATH = ROOT / "scripts/researchos_server/auto_update_runner.py"
CLI_PATH = ROOT / "scripts/plan_evolution.py"
PLUGIN_MANIFEST_PATH = ROOT / "config/plugins/system-stewardship.json"
SERVER_PATH = ROOT / "scripts/serve_dashboard.py"
MAINTENANCE_CLIENT_PATH = ROOT / "dashboard/src/services/maintenance-client.js"
MAINTENANCE_WORKBENCH_PATH = ROOT / "dashboard/src/services/maintenance-workbench.js"
MAINTENANCE_VIEW_PATH = ROOT / "dashboard/src/views/maintenance.js"
MAINTENANCE_FACADE_PATH = ROOT / "scripts/researchos_server/maintenance_facade.py"
INDEX_PATH = ROOT / "dashboard/index.html"
STYLE_PATH = ROOT / "dashboard/style.css"
APP_PATH = ROOT / "dashboard/app.js"
SYSTEM_PLUGIN_PATH = ROOT / "dashboard/src/plugins/system-stewardship.js"
EXECUTION_POLICIES = {"observe", "safe_refresh", "manual_heavy", "network_manual"}
COSTS = {"small", "medium", "large"}


def relative_write_allowed(path: str, allowed_prefixes: tuple[str, ...]) -> bool:
    normalized = str(path or "").replace("\\", "/")
    return bool(normalized) and not normalized.startswith("/") and ".." not in Path(normalized).parts and normalized.startswith(allowed_prefixes)


def failures() -> list[str]:
    issues: list[str] = []
    required_paths = (CONTRACT_PATH, DOC_EN, DOC_ZH, PLANNER_PATH, RUNNER_PATH, CLI_PATH, PLUGIN_MANIFEST_PATH, SERVER_PATH, MAINTENANCE_FACADE_PATH, MAINTENANCE_CLIENT_PATH, MAINTENANCE_WORKBENCH_PATH, MAINTENANCE_VIEW_PATH, INDEX_PATH, STYLE_PATH, APP_PATH, SYSTEM_PLUGIN_PATH)
    for path in required_paths:
        if not path.exists():
            issues.append(f"missing public evolution control file: {path.relative_to(ROOT)}")
    if issues:
        return issues
    try:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"invalid evolution contract JSON: {error}"]
    if contract.get("schema_id") != "researchos-evolution-control-v1":
        issues.append("evolution contract schema id drifted")
    if contract.get("version") != "1.1.0":
        issues.append("public evolution contract version must include derived-write rollback")
    if not any("retains snapshots for reconciliation" in item for item in contract.get("invariants", [])):
        issues.append("public evolution contract must preserve changed targets and recovery evidence without write attribution")
    if not any("unresolved manual candidate remains visible" in item and "defer retains" in item for item in contract.get("invariants", [])):
        issues.append("public evolution contract must preserve deferred manual candidates until exact rejection")
    if not any("declares its actual repository relative write owners" in item for item in contract.get("invariants", [])):
        issues.append("public evolution contract must require truthful declared write owners")
    limits = contract.get("limits", {})
    if limits.get("max_changed_paths") != MAX_CHANGED_PATHS or limits.get("max_visible_paths") != MAX_VISIBLE_PATHS:
        issues.append("evolution contract path limits drifted")
    if limits.get("full_review_tracked_markdown_ratio") != FULL_REVIEW_MARKDOWN_RATIO:
        issues.append("evolution contract Markdown ratio drifted")
    required_fields = set(contract.get("step_required_fields", []))
    ids = [str(step.get("id", "")) for step in RESEARCHOS_MAINTENANCE_STEPS]
    if len(ids) != len(set(ids)) or any(not step_id for step_id in ids):
        issues.append("public maintenance step ids must be unique and non-empty")
    safe_prefixes = tuple(contract.get("derived_prefixes", [])) + tuple(contract.get("runtime_prefixes", []))
    seen: set[str] = set()
    for step in RESEARCHOS_MAINTENANCE_STEPS:
        step_id = str(step.get("id", "unknown"))
        missing = sorted(required_fields - set(step))
        if missing:
            issues.append(f"public maintenance step {step_id} missing fields: {', '.join(missing)}")
        if step.get("execution_policy") not in EXECUTION_POLICIES or step.get("cost") not in COSTS:
            issues.append(f"public maintenance step {step_id} has invalid policy or cost")
        if not step.get("triggers"):
            issues.append(f"public maintenance step {step_id} must declare triggers")
        for dependency in step.get("depends_on", ()):
            if dependency not in seen:
                issues.append(f"public maintenance step {step_id} dependency must exist earlier: {dependency}")
        if step.get("execution_policy") == "observe" and step.get("writes"):
            issues.append(f"observe step {step_id} must not write files")
        if step.get("execution_policy") == "safe_refresh":
            for write in step.get("writes", ()):
                if not relative_write_allowed(str(write), safe_prefixes):
                    issues.append(f"safe public refresh {step_id} writes outside derived/runtime owners: {write}")
        seen.add(step_id)
    no_change = maintenance_plan([], runtime_mode="public_starter")
    if no_change.get("status") != "up_to_date" or no_change.get("selected_step_ids"):
        issues.append("empty public change set must produce no work")
    public_plan = maintenance_plan(["docs/self-evolution-control-plane.en.md"], runtime_mode="public_starter")
    personal_plan = maintenance_plan(["docs/self-evolution-control-plane.en.md"], runtime_mode="personal_vault")
    if "build_public_starter_data" not in public_plan.get("selected_step_ids", []) or "build_personal_vault_data" in public_plan.get("selected_step_ids", []):
        issues.append("public-starter plan must select only the public projection owner")
    if public_plan.get("risk_tier") != "E1":
        issues.append("public generated projection refresh must remain E1")
    if "build_personal_vault_data" not in personal_plan.get("selected_step_ids", []) or "build_public_starter_data" in personal_plan.get("selected_step_ids", []):
        issues.append("personal-vault plan must select only the local projection owner")
    code_plan = maintenance_plan(["dashboard/app.js"], runtime_mode="public_starter")
    if "validate_agent_architecture" not in code_plan.get("selected_step_ids", []):
        issues.append("public dashboard changes must select Agent architecture validation")
    if code_plan.get("risk_tier") != "E0":
        issues.append("read-only validation of public code changes must remain E0")
    traversal_plan = maintenance_plan(["../outside.md", "/absolute/path.md"], runtime_mode="public_starter")
    if traversal_plan.get("changed_path_count"):
        issues.append("public evolution planning must reject absolute and traversal paths")
    plugin = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))
    authority = plugin.get("authority", {})
    if plugin.get("public_safe") is not True or "public_starter" not in plugin.get("available_in", []):
        issues.append("public system stewardship plugin must be explicitly public-safe")
    if authority.get("requires_human_confirmation") is not True or authority.get("writeback_route") != "review":
        issues.append("public system stewardship plugin must remain candidate-before-confirmation")
    task_ids = [item.get("id") for item in plugin.get("contributions", {}).get("tasks", [])]
    if task_ids != ["system_evolution_review"]:
        issues.append("public system evolution task must have one native system_stewardship manifest owner")
    if "06_active_context/work_state/evolution/" not in (ROOT / ".gitignore").read_text(encoding="utf-8"):
        issues.append("public evolution checkpoint must remain Git-ignored")
    server_source = SERVER_PATH.read_text(encoding="utf-8")
    for token in (
        '"/evolution-plan": ResearchOSDashboardHandler.evolution_plan',
        '"/evolution-decision": (ResearchOSDashboardHandler.evolution_decision',
        "EVOLUTION_PLANNER.confirmed(plan, plan_id)",
        "EVOLUTION_PLANNER.decide_manual",
        "AUTO_UPDATE_RUNNER.run(step_ids)",
    ):
        if token not in server_source:
            issues.append(f"public dashboard evolution integration missing: {token}")
    if '"execution_allowed": not demo_read_only' not in MAINTENANCE_FACADE_PATH.read_text(encoding="utf-8"):
        issues.append("public evolution facade must keep demo projection read-only")
    client_source = MAINTENANCE_CLIENT_PATH.read_text(encoding="utf-8")
    workbench_source = MAINTENANCE_WORKBENCH_PATH.read_text(encoding="utf-8")
    view_source = MAINTENANCE_VIEW_PATH.read_text(encoding="utf-8")
    runner_source = RUNNER_PATH.read_text(encoding="utf-8")
    if "loadEvolutionPlan" not in client_source or "JSON.stringify({ plan_id: planId })" not in client_source:
        issues.append("public maintenance client must confirm an exact current plan")
    if "decideEvolutionPlan" not in client_source or "JSON.stringify({ plan_id: planId, decision })" not in client_source:
        issues.append("public maintenance client must send an exact manual-candidate decision")
    if "bindEvolutionDecisionEvents" not in workbench_source or 'querySelectorAll("[data-evolution-decision]")' not in workbench_source:
        issues.append("public maintenance workbench must bind explicit manual-candidate decisions")
    app_source = APP_PATH.read_text(encoding="utf-8")
    plugin_source = SYSTEM_PLUGIN_PATH.read_text(encoding="utf-8")
    if "evolutionDecisionRunning" not in plugin_source or "evolutionDecisionRunning = false" not in plugin_source:
        issues.append("public system stewardship adapter must keep an in-flight decision lock across UI re-renders")
    if "evolutionDecisionRunning" in app_source or "renderSystemChecks" in app_source:
        issues.append("public application shell must not retain system stewardship decision or rendering branches")
    if "renderEvolutionPlanHtml" not in view_source or "evolutionPlan.demoReadOnlyHint" not in view_source:
        issues.append("public maintenance view must expose candidate and demo read-only boundaries")
    if 'data-evolution-decision="deferred"' not in view_source or 'data-evolution-decision="rejected"' not in view_source:
        issues.append("public maintenance view must expose defer and reject candidate decisions")
    if "WriteSnapshot.capture" not in runner_source or '"rollback": rollback' not in runner_source:
        issues.append("public maintenance runner must capture declared writes and report recovery after failed safe refresh")
    if "autoUpdate.rollbackComplete" not in view_source:
        issues.append("public maintenance view must expose rollback completion")
    # Evolution-specific UI assets must stay loaded. index.html and style.css carry no ?v= cache
    # query: serve_dashboard.py sends Cache-Control: no-store.
    evolution_assets = (
        "src/core/contracts.js",
        "src/services/action-gateway.js",
        "src/core/service-mode.js",
        "src/core/interactions.js",
        "src/core/surface-contract.js",
        "src/services/inbox.js",
        "src/services/doing-board-state.js",
        "src/services/command-list-workbench.js",
        "src/services/preview-pdf-workbench.js",
        "src/services/maintenance-workbench.js",
        "src/services/maintenance-client.js",
        "src/services/daily-profile-refresh-client.js",
        "src/services/plugin-runtime.js",
        "src/services/request-auth.js",
        "src/services/preview-markdown.js",
        "src/services/preview-workbench.js",
        "src/core/ui-copy.js",
        "src/core/ui-copy-work-session.js",
        "src/services/onboarding-workbench.js",
        "src/plugins/material-pipeline.js",
        "src/views/onboarding.js",
        "src/services/handoff-receipt-projection.js",
        "src/services/handoff-admit-surface.js",
        "src/views/handoff-receipt.js",
        "src/views/handoff-admit-surface.js",
        "src/views/work-session.js",
        "src/views/unified-inbox.js",
        "src/services/result-envelope.js",
        "src/services/runtime-profile-projection.js",
        "src/views/runtime-profile.js",
        "src/services/codex-runner-client.js",
        "src/services/work-session-state.js",
        "src/services/context-pack-projection.js",
        "src/services/task-intent.js",
        "src/services/work-session-router.js",
        "src/services/work-session-client.js",
        "src/services/work-session-workbench.js",
        "src/services/asset-overview-workbench.js",
        "src/services/item-composition-model.js",
        "src/services/codex-thread-router.js",
        "src/services/handoff-composer.js",
        "src/services/workspace-shell-workbench.js",
        "src/views/asset-overview.js",
        "src/plugins/research-assets.js",
        "src/views/home-command-center.js",
        "src/plugins/research-portfolio-copy.js",
        "src/plugins/research-portfolio-model.js",
        "src/plugins/research-portfolio-view.js",
        "src/plugins/research-portfolio-workbench.js",
        "src/plugins/research-portfolio.js",
        "src/plugins/unified-research-desk.js",
        "src/views/maintenance.js",
        "src/plugins/system-stewardship.js",
    )
    index_source = INDEX_PATH.read_text(encoding="utf-8")
    style_source = STYLE_PATH.read_text(encoding="utf-8")
    if any(f'<script src="{asset}"></script>' not in index_source for asset in evolution_assets):
        issues.append("public evolution-specific UI assets must stay loaded by index.html")
    if "?v=" in index_source + style_source:
        issues.append("public dashboard assets must not carry hand-maintained ?v= cache queries")
    planner_source = PLANNER_PATH.read_text(encoding="utf-8")
    if "merge_pending_manual" not in planner_source or "ctime_ns" not in planner_source:
        issues.append("public evolution planner must preserve pending candidates and fingerprint metadata changes")
    allowed = server_source.split("PUBLIC_DEMO_ALLOWED_POST_PATHS = frozenset(", 1)[-1].split(")", 1)[0]
    if "PUBLIC_DEMO_ALLOWED_POST_PATHS = frozenset(" not in server_source or '"/evolution-decision"' in allowed:
        issues.append("public demo must block manual-candidate decision writes")
    cli_source = CLI_PATH.read_text(encoding="utf-8")
    if 'choices=("public_starter", "personal_vault")' not in cli_source or 'default="public_starter"' not in cli_source:
        issues.append("public evolution CLI must not expose private runtime mode")
    return issues


def main() -> int:
    issues = failures()
    if issues:
        print("Public evolution control validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(f"OK: public controlled evolution validated ({len(RESEARCHOS_MAINTENANCE_STEPS)} fixed maintenance steps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
