#!/usr/bin/env python3
"""Print the smallest public ResearchOS context route for a core or extension task."""

from __future__ import annotations

import argparse
import json
import re
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


LEVELS = ("quick", "standard", "evidence")


def write_chat_pack(payload: dict[str, object], vault: Path, out: Path, language: str) -> str:
    """One paste-ready file of the vault cards this level reads, for a chat in the browser.

    Only cards `ros context` would hand over without a terminal confirmation (public, internal) go in,
    with the task's workflow; sensitive, private and unlabeled cards are named as left out. The file
    goes outside the repository or under the git-ignored vault, never into tracked files."""
    from researchos_adapters.context_pack import DELIVERABLE
    zh = language == "zh-CN"
    target = out.resolve()
    if target.is_relative_to(ROOT) and not target.is_relative_to((ROOT / "personal_vault").resolve()):
        raise SystemExit("--pack 只能写到本仓库之外，或写在 personal_vault/ 下（Git 忽略）" if zh else
                         "--pack must write outside this repository or under personal_vault/ (git-ignored)")
    entry = payload["vault_entry"]
    cards = [path for path in [*payload["read_now"], *entry.get("named_cards", [])]
             if Path(path).resolve().is_relative_to(vault.resolve()) and Path(path).is_file()]
    workflows = [path for path in payload["read_now"] if str(path).startswith("05_workflows/") and (ROOT / path).is_file()]
    labels = {"sensitive": "敏感", "private": "私密", "unlabeled": "没有标签"} if zh else {}
    kept, left_out = [], []
    for card in dict.fromkeys(cards):
        text = Path(card).read_text(encoding="utf-8")
        label = next((line.split(":", 1)[1].strip().lower() for line in text.split("\n---\n", 1)[0].splitlines()
                      if line.startswith("sensitivity:")), "") or "unlabeled"
        body = text.split("\n---\n", 1)[1] if text.startswith("---\n") and "\n---\n" in text else text
        (kept if label in DELIVERABLE else left_out).append((card, labels.get(label, label), body.strip()))
    relative = lambda card: Path(card).resolve().relative_to(vault.resolve()).as_posix()
    head = (f"# 我的研究卡片：{payload['name']}\n\n"
            "下面是我自己写的几张研究卡片，请先读一遍，之后回答我时以它们为准。"
            "卡片里提到的文件路径在我的电脑上，你看不到；需要哪一份，请直接问我，我再上传或粘贴。"
            "卡片分成事实、我的看法和待核几部分，请不要把我的看法或待核的内容当成已确认的事实。\n" if zh else
            f"# My research cards: {payload['name']}\n\n"
            "Below are research cards I wrote myself. Please read them first and rely on them when you answer me. "
            "File paths in the cards are on my computer and you cannot see them; if you need one, ask me and I will "
            "upload or paste it. The cards keep facts, my view and things to verify apart; do not treat my view or "
            "the things to verify as confirmed facts.\n")
    if workflows:
        head += ("\n最后附上这类任务的做法说明，请照它的步骤来。\n" if zh else
                 "\nAt the end is how I want this kind of task done; please follow its steps.\n")
    body = "".join(f"\n---\n\n{text}\n" for _, _, text in kept)
    switch = re.compile(r"<p align=\"right\">.*?</p>\s*", re.S)  # the repository's language links mean nothing in a chat
    body += "".join(f"\n---\n\n{switch.sub('', (ROOT / path).read_text(encoding='utf-8').split(chr(10) + '---' + chr(10), 1)[-1]).strip()}\n"
                    for path in workflows)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head + body, encoding="utf-8")
    note = "".join(f"\n- {(vault / relative(card)).resolve()} ({label})" for card, label, _ in left_out)
    return ((f"已写入 {out}：{len(kept)} 张卡" + (f"、{len(workflows)} 份做法说明" if workflows else "") +
             (f"。这些卡没有放进来（要用就自己挑出需要的几句粘贴）：{note}" if left_out else "。")) if zh else
            (f"Wrote {out}: {len(kept)} card(s)" + (f" and {len(workflows)} workflow(s)" if workflows else "") +
             (f". Left out (paste only the lines you choose from them yourself):{note}" if left_out else ".")))


def vault_reads(task: dict[str, object], vault: Path, mode: str, generic: list[str], file_limit: int,
                language: str) -> dict[str, object]:
    """Resolve a route's reading levels against the user's own vault (the user's cards come first).

    quick reads the route's first card (the boundary card before outward tasks, else the working-style
    card for this kind of task, else the research identity page); standard adds the identity page, the
    task's workflow, one direction summary and the vault files the route names; evidence adds the
    route's index cards and opens only originals named in the evidence boundaries of these cards."""
    slots = task.get("vault_reads") or {}
    suffix = ".zh.md" if language == "zh-CN" else ".md"
    identity = vault / "00_identity" / "research-identity.md"
    style = vault / "03_cognition" / "style" / f"{slots['style']}.md" if slots.get("style") else None
    capsules = sorted((vault / "01_knowledge" / "capsules").glob("*.md"))
    upto = LEVELS[: LEVELS.index(mode) + 1]
    wanted = {level: [vault / relative for relative in slots.get(level, [])] for level in upto}
    missing: list[dict[str, str]] = []
    expected = [(identity, "research-identity"), *([(style, "style")] if style is not None else []),
                *((path, path.stem) for level in upto for path in wanted[level] if not path.name.endswith("/") and path.suffix)]
    for path, skeleton in expected:
        if not path.is_file():
            missing.append({"path": path.as_posix(), "template": f"09_templates/basic/{skeleton}{suffix}"})
    if not capsules:
        missing.append({"path": (vault / "01_knowledge" / "capsules" / "<project>.md").as_posix(),
                        "template": f"09_templates/basic/capsule{suffix}"})
    first = [path.as_posix() for path in (*wanted["quick"], style, identity) if path is not None and path.is_file()][:1]
    if mode == "quick":
        return {"read_now": first or generic[:1], "direction_summaries": [], "named_cards": [], "missing": missing}
    named: list[str] = []
    for level in upto[1:]:
        for relative in slots.get(level, []):
            target = vault / relative
            named.extend(path.as_posix() for path in (sorted(target.glob("*.md")) if relative.endswith("/") else [target])
                         if path.is_file())
    own = list(dict.fromkeys([*first, *(path.as_posix() for path in (identity, style) if path is not None and path.is_file()),
                              *named]))
    # One direction summary is read; when there are several, the task picks one, and that choice takes one place.
    summary_places = 1 if capsules else 0
    room = max(file_limit - summary_places, 0)
    read_now = list(dict.fromkeys([*own, *generic]))[:room]
    named_cards: list[str] = []
    if len(capsules) == 1:
        read_now.insert(min(len(own), len(read_now)), capsules[0].as_posix())
        sources = parse_list_field(capsules[0], "source_files")
        named_cards = [card.as_posix() for card in (vault / item for item in sources)
                       if card.is_file() and card.as_posix() not in read_now]
    return {"read_now": read_now, "direction_summaries": [path.as_posix() for path in capsules] if len(capsules) > 1 else [],
            "named_cards": named_cards, "missing": missing}


def parse_list_field(card: Path, key: str) -> list[str]:
    """One YAML list field of a card's frontmatter: `key: [a, b]`, or `key:` followed by `- item` lines."""
    lines = card.read_text(encoding="utf-8").split("\n---\n", 1)[0].splitlines()
    items: list[str] = []
    inside = False
    for line in lines:
        if line.startswith(f"{key}:"):
            inline = line.split(":", 1)[1].strip()
            if inline.startswith("[") and inline.endswith("]"):
                return [item.strip().strip("'\"") for item in inline[1:-1].split(",") if item.strip()]
            inside = True
        elif inside and line.strip().startswith("- "):
            items.append(line.strip()[2:].strip())
        elif inside:
            break
    return items


DO_NOT_READ = {
    "en": [
        "files in the other language",
        "dashboard/data/ and 08_exports/public_starter/generated-public-starter-data.json",
        "the ros run records under the vault's work_state folder",
    ],
    "zh-CN": [
        "另一种语言的文件",
        "dashboard/data/ 与 08_exports/public_starter/generated-public-starter-data.json",
        "库里 work_state 文件夹下 ros 的运行记录",
    ],
}
ESCALATE = {"quick": "standard", "standard": "evidence", "evidence": "none"}


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
        "do_not_read": [*DO_NOT_READ[language if language in DO_NOT_READ else "en"],
                        *([] if tier["id"] == "evidence" else [
                            "原件：卡片「证据边界」里写明的原文、笔记和记录" if language == "zh-CN"
                            else "originals named in a card's Evidence boundary"])],
        "escalate_to": ESCALATE[str(tier["id"])],
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
        "boundary": "确认边界" if zh else "Confirmation boundary",
        "skip": "默认不要读" if zh else "Do not read by default",
        "escalate": "出现明确缺口后才升级" if zh else "Escalate only after a named gap",
    }
    sensitivity = (
        "敏感性: 新卡按类型标注（论文、项目、摘要 internal，人物、会议 sensitive）；标签只决定 ros context 打包什么，"
        "助手读到的和你说的都会发给服务商"
        if zh else
        "Sensitivity: new cards are labelled by type (paper, project, summary internal; person, meeting sensitive); "
        "the label decides only what ros context packs, and what the assistant reads or you say goes to the provider"
    )
    lines = [
        f"{labels['task']}: {payload['name']} ({payload['task_id']})",
        f"{labels['language']}: {payload['active_language']}",
        f"{labels['template_policy']}: {payload['inactive_language_behavior']}",
        f"{labels['mode']}: {payload['mode']} / {payload['file_limit']} files / {payload['token_ceiling']} tokens",
        "",
        f"{labels['read']}:",
        *(f"- {path}" for path in payload["read_now"]),
        "",
        *vault_lines(payload, zh),
        f"{labels['skip']}:",
        *(f"- {item}" for item in payload["do_not_read"]),
        "",
        f"{labels['escalate']}: {payload['escalate_to']}",
        f"{labels['output']}: {payload['expected_output']}",
        f"{labels['workspace']}: {payload['workspace']}",
        f"{labels['result']}: {', '.join(payload['result_modes'])}; default={payload['default_result_mode']}",
        sensitivity,
        f"{labels['boundary']}: {payload['confirmation_boundary']}",
    ]
    return "\n".join(lines)


def vault_lines(payload: dict[str, object], zh: bool) -> list[str]:
    entry = payload.get("vault_entry")
    if not entry:
        return []
    lines = []
    if entry["direction_summaries"]:
        lines.append("方向摘要（按任务选其中一份，占一个名额；再按它的表用 ros context 取卡）：" if zh else
                     "Direction summaries (pick the one this task needs, it takes one place; then fetch its cards with ros context):")
        lines.extend(f"- {path}" for path in entry["direction_summaries"])
    if entry.get("named_cards") and payload["mode"] != "quick":
        lines.append("方向摘要点名的卡（任务需要哪张，就用 ros context 取哪张）：" if zh else
                     "Cards the direction summary names (fetch the ones the task needs with ros context):")
        lines.extend(f"- {path}" for path in entry["named_cards"])
    if payload["mode"] == "evidence":
        lines.append("原件：只打开这些卡「证据边界」里写明的原件，而且要有一个说得出的核对问题。" if zh else
                     "Originals: open only those named in the Evidence boundary of these cards, and only for a stated check.")
    if entry["missing"]:
        lines.append("你的库里还没有（本次跳过；想写时从模板开始）：" if zh else
                     "Not in your vault yet (skipped this time; start from the template when you want it):")
        lines.extend(f"- {item['path']} ← {item['template']}" for item in entry["missing"])
    return [*lines, ""] if lines else []


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
    parser.add_argument("--lang", choices=("en", "zh-CN"), default=None,
                        help="Default: the language of the --vault folder (its config/ros.json), otherwise en.")
    parser.add_argument("--mode", choices=("quick", "standard", "evidence"), default="quick")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--headless-json", action="store_true")
    parser.add_argument("--intent-json", help="Route a typed TaskIntent JSON file, or read it from stdin with '-'.")
    parser.add_argument("--prior-receipt-json", help="Reuse a prior route receipt only within its bounded identity.")
    parser.add_argument("--expected-extension-version", help="Fail closed when resuming a missing or changed task extension.")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--vault", metavar="FOLDER", help="Read the user's own cards in this vault first: the working-style card or research identity page at quick, plus the direction summary and named cards at standard.")
    parser.add_argument("--pack", metavar="FILE", help="With --vault: write the vault cards this level reads (public and internal only) into one paste-ready file for a browser chat.")
    parser.add_argument("--reroute-intent", action="store_true", help="Explicitly reclassify an intent in this runtime; discard prior profile classification and identity, never grant effects.")
    args = parser.parse_args()
    if args.lang is None:
        config = Path(args.vault or "") / "config" / "ros.json"
        language = json.loads(config.read_text(encoding="utf-8")).get("language") if args.vault and config.is_file() else ""
        args.lang = "zh-CN" if language == "zh-CN" else "en"
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
    if args.vault:
        vault = Path(args.vault)
        if not vault.is_dir():
            raise SystemExit(f"No vault folder at {args.vault}")
        entry = vault_reads(task, vault, str(payload["mode"]), list(payload["read_now"]), int(payload["file_limit"]), args.lang)
        payload["read_now"] = entry.pop("read_now")
        payload["vault_entry"] = entry
    if args.pack:
        if not args.vault:
            parser.error("--pack needs --vault")
        print(write_chat_pack(payload, Path(args.vault), Path(args.pack), args.lang))
        return 0
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json or args.headless_json else as_text(payload, args.lang))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
