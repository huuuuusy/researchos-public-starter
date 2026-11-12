#!/usr/bin/env python3
"""Answer responsibility-aware Research Agenda questions from Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_agenda_projection import research_agenda_from_markdown


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        default="",
        help="Agenda Markdown path relative to the repository root. Default: personal_vault/06_active_context/"
             "research-portfolio.md when it exists, otherwise the fictional demo agenda.",
    )
    parser.add_argument("--language", choices=("en", "zh-CN"), default="",
                        help="Default: the language of the personal vault (its config/ros.json), otherwise en.")
    parser.add_argument(
        "--view",
        choices=(
            "summary",
            "lead-active",
            "lead-all",
            "support-active",
            "support-all",
            "waiting",
            "queued",
            "conditional",
            "paused",
            "review",
            "unclassified",
            "all",
            "lead",
            "support",
        ),
        default="summary",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _selected(items: list[dict[str, object]], view: str) -> list[dict[str, object]]:
    if view in {"summary", "lead-active", "lead"}:
        return [item for item in items if item["responsibility"] == "lead" and item["state"] == "mainline"]
    if view == "lead-all":
        return [item for item in items if item["responsibility"] == "lead"]
    if view in {"support-active", "support"}:
        return [item for item in items if item["responsibility"] == "support" and item["state"] == "mainline"]
    if view == "support-all":
        return [item for item in items if item["responsibility"] == "support"]
    if view in {"waiting", "queued", "conditional", "paused"}:
        return [item for item in items if item["state"] == view]
    if view == "review":
        return [item for item in items if item.get("needs_attention")]
    if view == "unclassified":
        return [item for item in items if item["responsibility"] == "unclassified"]
    return items


def main() -> int:
    args = _args()
    root = Path(__file__).resolve().parents[1]
    vault_agenda = root / "personal_vault" / "06_active_context" / "research-portfolio.md"
    if not args.language:
        try:
            config = json.loads((root / "personal_vault" / "config" / "ros.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            config = {}
        args.language = "zh-CN" if config.get("language") == "zh-CN" else "en"
    if not args.path:
        demo = "08_exports/public_starter/demo-research-agenda" + (".zh.md" if args.language == "zh-CN" else ".md")
        args.path = str(vault_agenda) if vault_agenda.is_file() else demo
    path = Path(args.path)
    if not path.is_absolute():
        path = root / path
    agenda = research_agenda_from_markdown(
        root,
        path,
        language=args.language,
        presentation_mode="public_demo" if "public_starter" in path.parts else "personal_vault",
        boundary="fictional_public_demo_only" if "public_starter" in path.parts else "local_private_material",
        sensitivity="public" if "public_starter" in path.parts else "private",
    )
    selected = _selected(agenda["items"], args.view)
    if args.json:
        print(json.dumps({
            "answer": agenda["answer"],
            "coverage": agenda["coverage"],
            "integrity": agenda["integrity"],
            "items": selected,
        }, ensure_ascii=False, indent=2))
        return 0
    answer = agenda["answer"]
    if args.language == "zh-CN":
        print(
            f"已登记且核验的主责推进中 {answer['lead_active']} 项 | 协作推进中 {answer['support_active']} 项 | "
            f"等待 {answer['waiting']} 项 | 排队 {answer['queued']} 项 | 暂停 {answer['paused']} 项 | "
            f"需关注 {answer['needs_review']} 项"
        )
        print(
            f"覆盖：{'已核验' if answer['coverage_verified'] else '未闭合，以上是已登记数量'} | "
            f"已登记 {answer['registered_total']} 项 | 已分类 {answer['classified_total']} 项 | "
            f"覆盖候选 {answer['coverage_candidates']} 个"
        )
        for item in selected:
            print(f"- [{item['priority']}] {item['title']} —— {item['next_step']}")
        return 0
    print(
        f"Registered and verified lead active: {answer['lead_active']} | Support active: {answer['support_active']} | "
        f"Waiting: {answer['waiting']} | Queued: {answer['queued']} | "
        f"Paused: {answer['paused']} | Needs review: {answer['needs_review']}"
    )
    print(
        f"Coverage: {'verified' if answer['coverage_verified'] else 'provisional'} | "
        f"Registered: {answer['registered_total']} | Classified: {answer['classified_total']} | "
        f"Candidates: {answer['coverage_candidates']}"
    )
    for item in selected:
        print(f"- [{item['priority']}] {item['title']} — {item['next_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
