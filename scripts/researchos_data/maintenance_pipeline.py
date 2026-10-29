# ResearchOS maintenance header.
# 中文：ResearchOS 维护刷新 pipeline manifest；集中声明生成、审计和校验步骤的顺序与边界。
# English: ResearchOS maintenance refresh pipeline manifest; centralizes generation, audit, and validation step order and boundaries.

"""Machine-readable maintenance pipeline manifest for ResearchOS."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from typing import Any


PYTHON_EXECUTABLE_PLACEHOLDER = "{python}"
MAX_CHANGED_PATHS = 200
MAX_VISIBLE_PATHS = 40
FULL_REVIEW_MARKDOWN_RATIO = 0.25
FULL_REVIEW_PATTERNS = (
    "09_templates/data_contracts/*",
    "scripts/researchos_data/maintenance_pipeline.py",
    "scripts/researchos_server/evolution_planner.py",
)
RISK_TIER_ORDER = {"E0": 0, "E1": 1, "E2": 2, "E3": 3, "E4": 4}
PROJECTION_TRIGGERS = ("AGENTS.md", "README*", "docs/*", "01_knowledge/*", "04_people/*", "05_workflows/*", "06_active_context/*", "08_exports/public_starter/*", "09_templates/*", "config/extensions/*", "config/researchos.runtime*", "scripts/build_public_starter_data.py")


def maintenance_step(
    *,
    id: str,
    label: str,
    command: tuple[str, ...],
    timeout: int,
    phase: str,
    triggers: tuple[str, ...],
    writes: tuple[str, ...] = (),
    validates: tuple[str, ...] = (),
    depends_on: tuple[str, ...] = (),
    execution_policy: str = "observe",
    cost: str = "small",
    optional: bool = False,
    runtime_modes: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build one public fixed step with controlled-evolution metadata."""
    return {
        "id": id,
        "label": label,
        "command": command,
        "timeout": timeout,
        "optional": optional,
        "phase": phase,
        "triggers": triggers,
        "depends_on": depends_on,
        "writes": writes,
        "validates": validates,
        "execution_policy": execution_policy,
        "cost": cost,
        "runtime_modes": runtime_modes,
    }

RESEARCHOS_MAINTENANCE_STEPS: tuple[dict[str, Any], ...] = (
    maintenance_step(
        id="build_public_starter_data",
        label="Build public starter data",
        command=(PYTHON_EXECUTABLE_PLACEHOLDER, "scripts/build_public_starter_data.py", "--write"),
        timeout=90,
        phase="projection",
        triggers=PROJECTION_TRIGGERS,
        writes=(
            "08_exports/public_starter/generated-public-starter-data.json",
            "dashboard/data/researchos-dashboard.json",
        ),
        validates=("public demo records", "dashboard projection"),
        execution_policy="safe_refresh",
        cost="medium",
        runtime_modes=("public_starter",),
    ),
    maintenance_step(
        id="build_personal_vault_data",
        label="Build personal vault data",
        command=(PYTHON_EXECUTABLE_PLACEHOLDER, "scripts/build_public_starter_data.py", "--personal-vault", "--write"),
        timeout=90,
        phase="projection",
        triggers=PROJECTION_TRIGGERS,
        writes=("dashboard/data/researchos-local.json",),
        validates=("local personal-vault projection",),
        execution_policy="safe_refresh",
        cost="medium",
        runtime_modes=("personal_vault",),
    ),
    maintenance_step(id="validate_runtime_config", label="Validate runtime config", command=(PYTHON_EXECUTABLE_PLACEHOLDER, "scripts/validate_runtime_config.py"), timeout=45, phase="validation", triggers=("config/*", "scripts/researchos_adapters/*", "scripts/start_researchos.py"), validates=("public copy-only runtime config", "private execution boundary", "case switch", "language routing", "provider schema", "public starter no-executor boundary")),
    maintenance_step(id="validate_task_extensions", label="Validate task extensions", command=(PYTHON_EXECUTABLE_PLACEHOLDER, "scripts/validate_task_extensions.py"), timeout=30, phase="validation", triggers=("config/extensions/*", "docs/plugins/*", "scripts/plan_context.py", "scripts/researchos_data/task_extensions.py", "scripts/researchos_data/plugin_docs.py"), validates=("declarative task extensions", "core API compatibility", "plugin README contract", "public safety declarations")),
    maintenance_step(id="validate_plugins", label="Validate plugin host", command=(PYTHON_EXECUTABLE_PLACEHOLDER, "scripts/validate_plugins.py"), timeout=45, phase="validation", triggers=("config/plugins/*", "config/extensions/*", "docs/plugins/*", "scripts/plan_context.py", "scripts/researchos_data/plugins.py", "scripts/researchos_data/plugin_docs.py"), validates=("native plugin manifests", "runtime contributions", "ownership overlays", "task-extension compatibility", "plugin README contract")),
    maintenance_step(id="validate_agent_architecture", label="Validate Agent architecture", command=(PYTHON_EXECUTABLE_PLACEHOLDER, "scripts/validate_agent_architecture.py"), timeout=90, phase="validation", triggers=("dashboard/*", "scripts/*", "config/*", "docs/system-reference*"), validates=("Agent code routes", "runtime reachability", "frontend registration", "owner budgets"), cost="medium"),
    maintenance_step(id="validate_evolution_control", label="Validate evolution control", command=(PYTHON_EXECUTABLE_PLACEHOLDER, "scripts/validate_evolution_control.py"), timeout=45, phase="validation", triggers=("docs/self-evolution-control-plane*", "09_templates/data_contracts/researchos-evolution-control-v1.json", "config/plugins/system-stewardship.json", "scripts/researchos_data/maintenance_pipeline.py", "scripts/researchos_server/auto_update_runner.py", "scripts/researchos_server/evolution_planner.py", "scripts/plan_evolution.py"), validates=("evolution contract", "fixed-step planning", "confirmation and public boundary")),
    maintenance_step(id="validate_public_safety", label="Validate public safety", command=(PYTHON_EXECUTABLE_PLACEHOLDER, "scripts/validate_public_safety.py"), timeout=120, phase="validation", triggers=("*",), validates=("private semantic residue", "secrets", "local paths", "raw corpus boundary"), cost="medium"),
    maintenance_step(id="check_all_links", label="Check Markdown links", command=(PYTHON_EXECUTABLE_PLACEHOLDER, "scripts/check_all_links.py"), timeout=120, phase="validation", triggers=("*.md",), validates=("Markdown links",), cost="medium"),
)

DIRECT_MAINTENANCE_ACTIONS: dict[str, tuple[str, ...]] = {
    "build_public_starter_data": ("build_public_starter_data",),
    "build_personal_vault_data": ("build_personal_vault_data",),
    "validate_runtime_config": ("validate_runtime_config",),
    "validate_agent_architecture": ("validate_agent_architecture",),
    "validate_public_safety": ("validate_public_safety",),
    "check_all_links": ("check_all_links",),
}


def direct_maintenance_step_ids(action_id: str) -> tuple[str, ...] | None:
    """Resolve one fixed maintenance action without accepting shell input."""
    step_ids = DIRECT_MAINTENANCE_ACTIONS.get(str(action_id or "").strip())
    if step_ids is None:
        return None
    known_ids = set(maintenance_step_ids())
    if any(step_id not in known_ids for step_id in step_ids):
        raise ValueError(f"direct maintenance action references an unknown step: {action_id}")
    return tuple(step_ids)


def maintenance_step_ids() -> tuple[str, ...]:
    """Return canonical maintenance step ids in execution order."""
    return tuple(str(step["id"]) for step in RESEARCHOS_MAINTENANCE_STEPS)


def maintenance_command(step: dict[str, Any], python_executable: str = "python3") -> tuple[str, ...]:
    """Return a concrete command tuple for a manifest step."""
    command = tuple(str(part) for part in step.get("command", ()))
    return tuple(python_executable if part == PYTHON_EXECUTABLE_PLACEHOLDER else part for part in command)


def maintenance_command_lines(python_executable: str = "python3") -> tuple[str, ...]:
    """Return shell-readable maintenance commands in canonical order."""
    return tuple(" ".join(maintenance_command(step, python_executable)) for step in RESEARCHOS_MAINTENANCE_STEPS)


def normalize_changed_paths(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Normalize repository-relative change signals and fail closed on traversal."""
    normalized: list[str] = []
    for raw in paths:
        path = str(raw or "").strip().replace("\\", "/")
        if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
            continue
        while path.startswith("./"):
            path = path[2:]
        parts = tuple(part for part in path.split("/") if part not in {"", "."})
        if not parts or ".." in parts or parts[0] == ".git":
            continue
        clean = "/".join(parts)
        if clean not in normalized:
            normalized.append(clean)
    return tuple(normalized)


def maintenance_step_matches(step: dict[str, Any], changed_paths: tuple[str, ...]) -> bool:
    patterns = tuple(str(pattern) for pattern in step.get("triggers", ()))
    return any(fnmatch.fnmatch(path, pattern) for path in changed_paths for pattern in patterns)


def maintenance_step_enabled(step: dict[str, Any], runtime_mode: str) -> bool:
    runtime_modes = tuple(str(mode) for mode in step.get("runtime_modes", ()))
    return not runtime_modes or runtime_mode in runtime_modes


def maintenance_risk_tier(steps: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> str:
    """Return the highest authority boundary touched by the planned operations."""
    policies = {str(step.get("execution_policy") or "observe") for step in steps}
    if "network_manual" in policies:
        return "E4"
    if "manual_heavy" in policies:
        return "E2"
    if any(step.get("writes") for step in steps):
        return "E1"
    return "E0"


def max_risk_tier(*tiers: object) -> str:
    normalized = [str(tier) for tier in tiers if str(tier) in RISK_TIER_ORDER]
    return max(normalized, key=RISK_TIER_ORDER.get) if normalized else "E0"


def maintenance_plan(
    changed_paths: list[str] | tuple[str, ...],
    runtime_mode: str = "private",
    *,
    force_full_review: bool = False,
    full_review_reason: str = "",
) -> dict[str, Any]:
    """Return a deterministic candidate plan without reading source-file bodies."""
    paths = normalize_changed_paths(changed_paths)
    over_path_budget = len(paths) > MAX_CHANGED_PATHS
    control_contract_changed = any(fnmatch.fnmatch(path, pattern) for path in paths for pattern in FULL_REVIEW_PATTERNS)
    full_review = force_full_review or over_path_budget or control_contract_changed
    if not full_review_reason:
        if force_full_review:
            full_review_reason = "caller_forced"
        elif over_path_budget:
            full_review_reason = "changed_path_budget"
        elif control_contract_changed:
            full_review_reason = "control_contract_changed"
    steps_by_id = {str(step["id"]): step for step in RESEARCHOS_MAINTENANCE_STEPS}
    selected = {
        str(step["id"])
        for step in RESEARCHOS_MAINTENANCE_STEPS
        if paths and maintenance_step_enabled(step, runtime_mode) and (full_review or maintenance_step_matches(step, paths))
    }
    pending = list(selected)
    while pending:
        step_id = pending.pop()
        for dependency in steps_by_id[step_id].get("depends_on", ()):
            dependency_id = str(dependency)
            if dependency_id not in selected:
                selected.add(dependency_id)
                pending.append(dependency_id)
    ordered_steps = [step for step in RESEARCHOS_MAINTENANCE_STEPS if str(step["id"]) in selected]
    selected_ids = [str(step["id"]) for step in ordered_steps]
    auto_eligible_ids = [
        str(step["id"])
        for step in ordered_steps
        if step.get("execution_policy") in {"observe", "safe_refresh"}
    ]
    manual_ids = [str(step["id"]) for step in ordered_steps if str(step["id"]) not in auto_eligible_ids]
    writes = sorted({str(path) for step in ordered_steps for path in step.get("writes", ())})
    auto_writes = sorted({str(path) for step in ordered_steps if str(step["id"]) in auto_eligible_ids for path in step.get("writes", ())})
    manual_writes = sorted({str(path) for step in ordered_steps if str(step["id"]) in manual_ids for path in step.get("writes", ())})
    validates = sorted({str(item) for step in ordered_steps for item in step.get("validates", ())})
    plan_seed = json.dumps(
        {"paths": paths, "runtime_mode": runtime_mode, "steps": selected_ids},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    plan_id = f"evo-{hashlib.sha256(plan_seed.encode('utf-8')).hexdigest()[:16]}"
    return {
        "schema_id": "researchos-evolution-plan-v1",
        "plan_id": plan_id,
        "status": "candidate" if paths else "up_to_date",
        "runtime_mode": runtime_mode,
        "changed_path_count": len(paths),
        "changed_paths": list(paths[:MAX_VISIBLE_PATHS]),
        "changed_paths_truncated": len(paths) > MAX_VISIBLE_PATHS,
        "full_review": full_review,
        "full_review_reason": full_review_reason if full_review else "",
        "risk_tier": maintenance_risk_tier(ordered_steps),
        "requires_confirmation": bool(writes or manual_ids),
        "selected_step_ids": selected_ids,
        "auto_eligible_step_ids": auto_eligible_ids,
        "manual_step_ids": manual_ids,
        "writes": writes,
        "auto_writes": auto_writes,
        "manual_writes": manual_writes,
        "validates": validates,
        "steps": [
            {
                "id": step["id"],
                "label": step["label"],
                "phase": step["phase"],
                "execution_policy": step["execution_policy"],
                "cost": step["cost"],
                "writes": list(step.get("writes", ())),
                "validates": list(step.get("validates", ())),
            }
            for step in ordered_steps
        ],
    }



def maintenance_pipeline_summary() -> dict[str, Any]:
    """Return a compact summary suitable for validators and docs."""
    required_steps = [step["id"] for step in RESEARCHOS_MAINTENANCE_STEPS if not step.get("optional")]
    optional_steps = [step["id"] for step in RESEARCHOS_MAINTENANCE_STEPS if step.get("optional")]
    return {
        "version": "researchos-maintenance-pipeline-v1",
        "step_count": len(RESEARCHOS_MAINTENANCE_STEPS),
        "step_ids": list(maintenance_step_ids()),
        "required_steps": list(required_steps),
        "optional_steps": list(optional_steps),
        "commands": list(maintenance_command_lines()),
        "steps": [
            {
                "id": step["id"],
                "label": step["label"],
                "phase": step["phase"],
                "optional": bool(step["optional"]),
                "triggers": list(step.get("triggers", ())),
                "depends_on": list(step.get("depends_on", ())),
                "execution_policy": step.get("execution_policy"),
                "cost": step.get("cost"),
                "runtime_modes": list(step.get("runtime_modes", ())),
                "writes": list(step.get("writes", ())),
                "validates": list(step.get("validates", ())),
            }
            for step in RESEARCHOS_MAINTENANCE_STEPS
        ],
    }
