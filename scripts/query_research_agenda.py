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
        default="08_exports/public_starter/demo-research-agenda.md",
        help="Agenda Markdown path relative to the repository root.",
    )
    parser.add_argument("--language", choices=("en", "zh-CN"), default="en")
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
