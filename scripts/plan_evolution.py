#!/usr/bin/env python3
"""Plan and explicitly confirm bounded ResearchOS maintenance updates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from researchos_server.auto_update_runner import AutoUpdateRunner
from researchos_adapters.command_runner import CommandRunner
from researchos_server.evolution_planner import EvolutionPlanner


ROOT = Path(__file__).resolve().parents[1]


def print_plan(plan: dict[str, object]) -> None:
    print(f"Evolution candidate: {plan['plan_id']}")
    print(f"- status: {plan['status']}")
    print(f"- changed paths: {plan['changed_path_count']}")
    print(f"- selected steps: {len(plan['selected_step_ids'])}")
    print(f"- safe/observe steps: {', '.join(plan['auto_eligible_step_ids']) or 'none'}")
    print(f"- manual steps: {', '.join(plan['manual_step_ids']) or 'none'}")
    print(f"- writes: {', '.join(plan['writes']) or 'none'}")
    if plan["selected_step_ids"]:
        print(f"Confirm safe subset with: python3 scripts/plan_evolution.py --apply-safe --confirm {plan['plan_id']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed", action="append", default=None, help="Explicit repository-relative changed path; repeat as needed.")
    parser.add_argument("--runtime-mode", choices=("public_starter", "personal_vault"), default="public_starter")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    parser.add_argument("--apply-safe", action="store_true", help="Run only observe/safe_refresh steps from the current plan.")
    parser.add_argument("--confirm", default="", help="Exact plan id printed by a prior planning pass.")
    args = parser.parse_args()

    planner = EvolutionPlanner(ROOT, runtime_mode=args.runtime_mode)
    plan = planner.plan(args.changed)
    if not args.apply_safe:
        if args.json:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print_plan(plan)
        return 0

    if not planner.confirmed(plan, args.confirm):
        print_plan(plan)
        print("Refused: --confirm must match the current plan id.", file=sys.stderr)
        return 2
    step_ids = list(plan.get("auto_eligible_step_ids", []))
    if not step_ids:
        print("No safe or observe maintenance steps are selected.")
        return 0
    result = AutoUpdateRunner(command_runner=CommandRunner(ROOT)).run(step_ids)
    checkpoint = None
    if result.get("ok"):
        checkpoint = planner.mark_applied(plan, result)
    payload = {
        "plan": plan,
        "result": result,
        "checkpoint": checkpoint,
        "pending_manual_step_ids": list(plan.get("manual_step_ids", [])),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Safe maintenance {'completed' if result.get('ok') else 'failed'}: {', '.join(result.get('executed_step_ids', []))}")
        if plan.get("manual_step_ids"):
            print(f"Safe subset checkpointed; manual candidate remains: {', '.join(plan['manual_step_ids'])}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
