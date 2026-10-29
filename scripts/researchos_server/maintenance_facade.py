# ResearchOS maintenance header.
# 中文：Dashboard 维护动作的本地能力门面；HTTP 入口只负责请求与响应。
# English: Local capability facade for Dashboard maintenance actions; keeps HTTP entrypoints request/response-only.

"""Bounded public/personal-vault maintenance orchestration helpers."""

from __future__ import annotations

import sys
from typing import Any

from researchos_data.maintenance_pipeline import (
    RESEARCHOS_MAINTENANCE_STEPS,
    direct_maintenance_step_ids,
    maintenance_step_enabled,
)


def active_build_command(personal_vault: bool) -> list[str]:
    args = [sys.executable, "scripts/build_public_starter_data.py"]
    if personal_vault:
        args.append("--personal-vault")
    args.append("--write")
    return args


def evolution_plan_view(planner: Any, demo_read_only: bool) -> dict[str, object]:
    plan = planner.plan()
    return {
        **plan,
        "execution_allowed": not demo_read_only,
        "execution_reason": "public_demo_read_only" if demo_read_only else "personal_vault_plan_confirmation",
    }


def maintenance_action_response(
    request: dict[str, object],
    runner: Any,
    *,
    runtime_mode: str,
) -> tuple[dict[str, object], int]:
    action_id = str(request.get("action_id") or "").strip()
    step_ids = direct_maintenance_step_ids(action_id)
    if step_ids is None:
        return {"ok": False, "action_id": action_id, "message": "Unknown maintenance action", "steps": []}, 400
    steps_by_id = {str(step.get("id") or ""): step for step in RESEARCHOS_MAINTENANCE_STEPS}
    if any(not maintenance_step_enabled(steps_by_id[step_id], runtime_mode) for step_id in step_ids):
        return {
            "ok": False,
            "action_id": action_id,
            "error_type": "maintenance_action_runtime_blocked",
            "message": "Maintenance action is unavailable in the active runtime",
            "steps": [],
        }, 403
    payload = dict(runner.run(step_ids))
    payload["action_id"] = action_id
    return payload, 200
