#!/usr/bin/env python3
"""Print the smallest public ResearchOS context route for a core or extension task."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from researchos_data.plugins import load_plugin_registry
from researchos_data.public_conversation_catalog import public_tasks_for_language
from researchos_data.conversation_contract import with_conversation_contract
from researchos_data.task_router import route_task_intent


ROOT = Path(__file__).resolve().parents[1]
ALIASES = {
    "start": "first_run_onboarding",
    "onboarding": "first_run_onboarding",
    "material": "material_intake",
    "intake": "material_intake",
    "upgrade": "card_upgrade",
    "handoff": "codex_handoff",
    "relationship": "relationship_opportunity",
    "maintenance": "maintenance_check",
    "relationship_network": "relationship_opportunity",
    "self_evolution": "system_evolution_review",
    "system_maintenance": "maintenance_check",
    "memory_update": "card_upgrade",
    "codex_thread_handoff": "codex_handoff",
}


def task_routes(language: str) -> list[dict[str, object]]:
    base_tasks = public_tasks_for_language(language)
    plugins = load_plugin_registry(
        ROOT,
        runtime_scope="public_starter",
        language=language,
        base_task_ids={str(task.get("id", "")) for task in base_tasks} | set(ALIASES),
    )
    tasks = [*base_tasks, *plugins["tasks"]]
    return [with_conversation_contract(task, language) for task in tasks]


def route_for(task_id: str, language: str) -> dict[str, object] | None:
    route_id = ALIASES.get(task_id, task_id)
    return next(
        (
            task
            for task in task_routes(language)
            if task.get("id") == route_id or route_id in task.get("aliases", [])
        ),
        None,
    )


def selected_tier(task: dict[str, object], mode: str) -> dict[str, object]:
    tiers = task.get("read_tiers", [])
    return next((tier for tier in tiers if tier.get("id") == mode), tiers[0])


def route_payload(
    task: dict[str, object],
    language: str,
    mode: str,
    *,
    include_legacy_client_fields: bool = True,
) -> dict[str, object]:
    tier = selected_tier(task, mode)
    payload = {
        "task_id": task["id"],
        "name": task["name"],
        "mode": tier["id"],
        "active_language": language,
        "template_policy": "active_language_only",
        "inactive_language_behavior": "reference_only_do_not_read_by_agent",
        "file_limit": tier["file_limit"],
        "token_ceiling": tier["token_ceiling"],
        "read_now": tier["read"],
        "expected_output": task["output"],
        "workspace": task.get("workspace", "agent"),
        "result_modes": task.get("result_modes", ["answer", "artifact", "writeback"]),
        "default_result_mode": task.get("default_result_mode", "answer"),
        "sensitivity_default": task.get("sensitivity_default", "local_only"),
        "authority": task["authority"],
        "confirmation_boundary": task["authority"]["summary"],
    }
    if task.get("extension_id"):
        payload["extension"] = {
            "id": task["extension_id"],
            "version": task["extension_version"],
            "resume_command": (
                f"python3 scripts/plan_context.py {task['id']} --lang {language} "
                f"--mode {tier['id']} --headless-json "
                f"--expected-extension-version {task['extension_version']}"
            ),
        }
    if include_legacy_client_fields:
        payload.update({
            "primary_surface": task["primary_surface"],
            "dashboard_role": task["dashboard_role"],
        })
    return payload


def plan_task_intent(
    intent: dict[str, object],
    language: str,
    mode: str | None = None,
    prior_receipt: dict[str, object] | None = None,
) -> dict[str, object]:
    """Attach the public context budget to a typed, non-effectful receipt."""
    receipt = route_task_intent(intent, prior_receipt=prior_receipt)
    context = receipt["context"]
    task_id = context.get("context_route_id")
    fallback_id = context.get("fallback_context_route_id")
    task = route_for(str(task_id), language) if task_id else None
    resolution = "primary"
    if task is None and fallback_id:
        task = route_for(str(fallback_id), language)
        resolution = "fallback"
    if task is None:
        context["context_route_resolution"] = "unavailable"
        return receipt

    tier = selected_tier(task, mode or str(context.get("tier", "quick")))
    exact_targets = [str(item) for item in intent.get("exact_targets", []) if str(item).strip()]
    prior_context = (prior_receipt or {}).get("context", {})
    prior_intent = (prior_receipt or {}).get("intent", {})
    prior_route = (prior_receipt or {}).get("route", {})
    prior_read_now = prior_context.get("read_now", []) if isinstance(prior_context, dict) else []
    reuse = bool(
        not exact_targets
        and prior_receipt
        and receipt["identity"].get("commitment_id")
        and receipt["identity"].get("commitment_id") == (prior_receipt or {}).get("identity", {}).get("commitment_id")
        and receipt["route"].get("primary_family") == prior_route.get("primary_family")
        and receipt["intent"].get("sensitivity") == prior_intent.get("sensitivity")
        and receipt["intent"].get("destination") != "external"
        and isinstance(prior_read_now, list)
        and all(isinstance(item, str) for item in prior_read_now)
        and prior_read_now
    )
    context.update({
        "tier": tier["id"],
        "context_route_id": task["id"],
        "context_route_resolution": resolution,
        "file_limit": tier["file_limit"],
        "token_ceiling": tier["token_ceiling"],
        "read_now": exact_targets or (list(prior_read_now) if reuse else list(tier["read"])),
        "exact_target_shortcut_used": bool(exact_targets),
        "prior_context_reused": reuse,
        "prior_context_reuse_boundary": (
            "same_commitment_family_sensitivity_and_non_external" if reuse else "not_reused"
        ),
        "expected_output": task["output"],
        "authority_summary": task["authority"]["summary"],
    })
    return receipt


def _load_json_argument(value: str) -> dict[str, object]:
    payload = json.load(sys.stdin) if value == "-" else json.loads(Path(value).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected a JSON object in {value}")
    return payload


def as_text(payload: dict[str, object], language: str) -> str:
    zh = language == "zh-CN"
    labels = {
        "task": "任务" if zh else "Task",
        "language": "当前模板语言" if zh else "Active template language",
        "template_policy": "非当前语言模板" if zh else "Inactive-language templates",
        "mode": "读取档位" if zh else "Read tier",
        "read": "本轮只读" if zh else "Read now only",
        "output": "输出" if zh else "Output",
        "workspace": "工作区" if zh else "Workspace",
        "result": "结果协议" if zh else "Result protocol",
        "sensitivity": "默认敏感度" if zh else "Sensitivity default",
        "boundary": "确认边界" if zh else "Confirmation boundary",
    }
    lines = [
        f"{labels['task']}: {payload['name']} ({payload['task_id']})",
        f"{labels['language']}: {payload['active_language']}",
        f"{labels['template_policy']}: {payload['inactive_language_behavior']}",
        f"{labels['mode']}: {payload['mode']} / {payload['file_limit']} files / {payload['token_ceiling']} tokens",
        "",
        f"{labels['read']}:",
        *(f"- {path}" for path in payload["read_now"]),
        "",
        f"{labels['output']}: {payload['expected_output']}",
        f"{labels['workspace']}: {payload['workspace']}",
        f"{labels['result']}: {', '.join(payload['result_modes'])}; default={payload['default_result_mode']}",
        f"{labels['sensitivity']}: {payload['sensitivity_default']}",
        f"{labels['boundary']}: {payload['confirmation_boundary']}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Print a bounded context route for a registered ResearchOS task ID. "
            "This command does not interpret natural-language research requests."
        ),
        epilog=(
            "Run with --list to see valid IDs. For a natural-language task, work "
            "directly with a file-aware agent or use the optional dashboard."
        ),
    )
    parser.add_argument(
        "task",
        nargs="?",
        metavar="TASK_ID",
        help="Registered task ID, alias, or enabled extension ID.",
    )
    parser.add_argument("--lang", choices=("en", "zh-CN"), default="en")
    parser.add_argument("--mode", choices=("quick", "standard", "evidence"), default="quick")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--headless-json", action="store_true")
    parser.add_argument("--intent-json", help="Route a typed TaskIntent JSON file, or read it from stdin with '-'.")
    parser.add_argument("--prior-receipt-json", help="Reuse a prior route receipt only within its bounded identity.")
    parser.add_argument("--expected-extension-version", help="Fail closed when resuming a missing or changed task extension.")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--reroute-intent", action="store_true", help="Explicitly reclassify an intent in this runtime; discard prior profile classification and identity, never grant effects.")
    args = parser.parse_args()
    if args.reroute_intent and (not args.intent_json or args.prior_receipt_json):
        parser.error("--reroute-intent requires --intent-json and cannot reuse a prior receipt")
    if args.expected_extension_version and (args.list or args.intent_json or not args.task):
        parser.error("--expected-extension-version requires an explicit task id")
    if args.list:
        for task in task_routes(args.lang):
            print(f"{task['id']}: {task['name']}")
        return 0
    if args.intent_json:
        intent = _load_json_argument(args.intent_json)
        if args.reroute_intent:
            for key in ("primary_family_candidate", "secondary_family_candidates", "authority_owner", "current_commitment_id", "thread_id"):
                intent.pop(key, None)
        prior = _load_json_argument(args.prior_receipt_json) if args.prior_receipt_json else None
        print(json.dumps(plan_task_intent(intent, args.lang, args.mode, prior), ensure_ascii=False, indent=2))
        return 0
    if not args.task:
        parser.error("task is required unless --list is used")
    task = route_for(args.task, args.lang)
    if task is None:
        known = ", ".join(str(item["id"]) for item in task_routes(args.lang))
        raise SystemExit(
            f"Unknown task ID: {args.task}. The extension may be disabled or removed; previous results remain valid records, but this route cannot resume. Known task IDs: {known}. "
            "Run `python3 scripts/plan_context.py --list` to inspect valid IDs. "
            "Natural-language research requests belong in a file-aware agent or the optional dashboard."
        )
    if args.expected_extension_version and (not task.get("extension_id") or task.get("extension_version") != args.expected_extension_version):
        raise SystemExit("Task extension version changed; preserve the previous result and review the current plan before starting a new task.")
    payload = route_payload(
        task,
        args.lang,
        args.mode,
        include_legacy_client_fields=not args.headless_json,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json or args.headless_json else as_text(payload, args.lang))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
