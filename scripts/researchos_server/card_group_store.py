# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard server 中关于「card group store」的辅助 owner；保持 serve_dashboard.py 只做 HTTP 编排。
# English: Helper owner for card group store in the local ResearchOS dashboard server; keeps serve_dashboard.py HTTP-orchestration-only.

"""Card group persistence helpers for the local ResearchOS dashboard server."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from researchos_kernel.atomic_files import atomic_write_json, atomic_write_text, lock_path_for, runtime_state_transaction


SafePath = Callable[[object], str]


@dataclass(frozen=True)
class CardGroupStore:
    root: Path
    card_groups_json: Path
    card_groups_md: Path
    group_dissolution_json: Path
    group_dissolution_md: Path
    safe_md_path: SafePath

    allowed_item_types = {"paper", "person", "project", "talk", "source"}
    allowed_group_levels = {"G1", "G2"}
    allowed_dissolution_statuses = {
        "pending_codex_migration_review",
        "migration_review_ready_pending_researcher_confirmation",
        "in_progress",
        "migrated_pending_delete_confirmation",
        "done",
        "withdrawn",
    }

    def save_groups(self, groups: object) -> dict[str, object]:
        if not isinstance(groups, list):
            raise ValueError("Invalid groups")
        safe_groups = [group for group in (self.normalize_group(item) for item in groups[:80]) if group]
        with runtime_state_transaction(lock_path=lock_path_for(self.card_groups_json)):
            atomic_write_json(self.card_groups_json, safe_groups)
            atomic_write_text(self.card_groups_md, self.render_groups_markdown(safe_groups))
        return {"ok": True, "count": len(safe_groups), "path": str(self.card_groups_md.relative_to(self.root))}

    def save_dissolutions(self, items: object) -> dict[str, object]:
        if not isinstance(items, list):
            raise ValueError("Invalid dissolution items")
        safe_records = [record for record in (self.normalize_dissolution(item) for item in items[:80]) if record]
        with runtime_state_transaction(lock_path=lock_path_for(self.card_groups_json)):
            atomic_write_json(self.group_dissolution_json, safe_records)
            atomic_write_text(self.group_dissolution_md, self.render_dissolutions_markdown(safe_records))
        return {"ok": True, "count": len(safe_records), "path": str(self.group_dissolution_md.relative_to(self.root))}

    def normalize_group(self, group: object) -> dict[str, object] | None:
        if not isinstance(group, dict):
            return None
        raw_items = group.get("items", [])
        if not isinstance(raw_items, list):
            raw_items = []
        safe_items = self.normalize_cards(raw_items, limit=80)
        group_level = str(group.get("group_level", "G1")).strip()
        return {
            "id": str(group.get("id", "")).strip()[:160],
            "title": str(group.get("title", "")).strip()[:300] or "Card Group",
            "purpose": str(group.get("purpose", "")).strip()[:3000],
            "items": safe_items,
            "group_level": group_level if group_level in self.allowed_group_levels else "G1",
            "group_kind": str(group.get("group_kind", "")).strip()[:80],
            "source_type": str(group.get("source_type", "")).strip()[:80],
            "source_path": self.safe_md_path(group.get("source_path", "")),
            "source_note": str(group.get("source_note", "")).strip()[:300],
            "createdAt": str(group.get("createdAt", "")).strip()[:80],
            "updatedAt": str(group.get("updatedAt", "")).strip()[:80],
            "source": "dashboard",
        }

    def normalize_dissolution(self, item: object) -> dict[str, object] | None:
        if not isinstance(item, dict):
            return None
        source_path = self.safe_md_path(item.get("source_path", ""))
        if not source_path:
            return None
        raw_cards = item.get("items", [])
        if not isinstance(raw_cards, list):
            raw_cards = []
        group_level = str(item.get("group_level", "G1")).strip()
        status = str(item.get("status", "pending_codex_migration_review")).strip()
        return {
            "id": str(item.get("id", "")).strip().replace("\n", " ")[:180] or f"dissolve:{source_path}",
            "status": status if status in self.allowed_dissolution_statuses else "pending_codex_migration_review",
            "title": str(item.get("title", "")).strip().replace("\n", " ")[:300] or source_path,
            "group_id": str(item.get("group_id", "")).strip().replace("\n", " ")[:180],
            "group_level": group_level if group_level in self.allowed_group_levels else "G1",
            "group_kind": str(item.get("group_kind", "")).strip().replace("\n", " ")[:80],
            "source_type": str(item.get("source_type", "")).strip().replace("\n", " ")[:80],
            "source_path": source_path,
            "source_note": str(item.get("source_note", "")).strip().replace("\n", " ")[:300],
            "purpose": str(item.get("purpose", "")).strip()[:3000],
            "items": self.normalize_cards(raw_cards, limit=120),
            "user_intent": "dissolve_after_migration_review",
            "safety_rule": "No deletion is performed by the dashboard server. Codex must read the group source and all card files, migrate reusable experience back to related cards, then ask the user before deleting the source md.",
            "createdAt": str(item.get("createdAt", "")).strip()[:80],
            "updatedAt": str(item.get("updatedAt", "")).strip()[:80],
            "processed_at": str(item.get("processed_at", "")).strip()[:80],
            "review_file": self.safe_md_path(item.get("review_file", "")),
            "deletion_status": str(item.get("deletion_status", "")).strip()[:160],
            "next_action": str(item.get("next_action", "")).strip()[:500],
            "source": "dashboard",
        }

    def normalize_cards(self, cards: list[object], limit: int) -> list[dict[str, object]]:
        safe_cards: list[dict[str, object]] = []
        seen_cards: set[str] = set()
        for card in cards[:limit]:
            if not isinstance(card, dict):
                continue
            card_type = str(card.get("type", "")).strip()[:40]
            if card_type not in self.allowed_item_types:
                continue
            card_path = self.safe_md_path(card.get("path", ""))
            title = str(card.get("title", "")).strip().replace("\n", " ")[:300]
            if not title and not card_path:
                continue
            card_key = f"{card_type}:{card_path or title}"
            if card_key in seen_cards:
                continue
            seen_cards.add(card_key)
            safe_cards.append(
                {
                    "type": card_type,
                    "title": title or card_path,
                    "path": card_path,
                    "note": str(card.get("note", "")).strip()[:1200],
                    "source": str(card.get("source", "")).strip()[:80],
                    "addedAt": str(card.get("addedAt", "")).strip()[:80],
                }
            )
        return safe_cards

    @staticmethod
    def render_groups_markdown(groups: list[dict[str, object]]) -> str:
        lines = [
            "---",
            "type: active_context",
            'title: "UI Card Groups"',
            "status: active",
            "created: 2026-06-18",
            "updated: 2026-06-18",
            "tags:",
            "  - dashboard",
            "  - card-group",
            "  - recombination",
            "  - pending-review",
            "sensitivity: internal",
            "---",
            "",
            "# UI Card Groups",
            "",
            "## Agent Summary",
            "",
            "本文件由本地 dashboard 的卡片组合工作台生成，用于暂存用户主动重组的论文卡、人物卡和组合目的。它不是稳定长期记忆；Codex 处理时应把 group 视为 user-defined task space：卡片是组件，purpose 是查询条件，输出应揭示可解释的能力边界、合作路线或项目动作。",
            "",
        ]
        if not groups:
            lines.extend(["## Card Groups", "", "暂无 card group。", ""])
        for group in groups:
            items = group.get("items", [])
            if not isinstance(items, list):
                items = []
            paper_count = sum(1 for item in items if isinstance(item, dict) and item.get("type") == "paper")
            person_count = sum(1 for item in items if isinstance(item, dict) and item.get("type") == "person")
            lines.extend(
                [
                    "## Card Group",
                    "",
                    f"- id: `{group.get('id', '')}`",
                    f"- title: {group.get('title', '')}",
                    f"- group_level: {group.get('group_level', 'G1')}",
                    f"- group_kind: {group.get('group_kind', '') or 'custom'}",
                    f"- source_type: {group.get('source_type', '') or 'dashboard'}",
                    f"- source_path: `{group.get('source_path', '')}`" if group.get("source_path") else "- source_path: 未指定",
                    f"- source_note: {group.get('source_note', '') or '无'}",
                    f"- updatedAt: `{group.get('updatedAt', '')}`",
                    f"- paper_cards: {paper_count}",
                    f"- person_cards: {person_count}",
                    "",
                    "### Purpose",
                    "",
                    str(group.get("purpose", "")) or "未填写。",
                    "",
                    "### Cards",
                    "",
                ]
            )
            CardGroupStore.append_card_lines(lines, items, empty_line="暂无卡片。")
            lines.extend(
                [
                    "",
                    "### Codex Handling Note",
                    "",
                    "处理时不要把本组当作收藏夹；请说明每张卡在组合中的功能：证据、对照、桥接、合作者、待确认或行动入口，并给出缺失卡片建议。",
                    "",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def render_dissolutions_markdown(records: list[dict[str, object]]) -> str:
        today = datetime.now().date().isoformat()
        lines = [
            "---",
            "type: active_context",
            'title: "UI Card Group Dissolution Inbox"',
            "status: active",
            "created: 2026-06-18",
            f"updated: {today}",
            "tags:",
            "  - dashboard",
            "  - card-group",
            "  - dissolution",
            "  - migration-review",
            "  - pending-review",
            "sensitivity: internal",
            "---",
            "",
            "# UI Card Group Dissolution Inbox",
            "",
            "## Agent Summary",
            "",
            "本文件由 dashboard 的 group 解散按钮生成。解散不是直接删除：Codex 必须先读取 group 来源 MD 和所有相关卡片，把 group 里已经沉淀的经验、关系判断、项目逻辑、证据边界和可复用表达写回到单独相关卡片或下层 group。只有迁移建议完成并经用户明确确认后，才可以删除来源 MD。",
            "",
            "## Handling Protocol",
            "",
            "1. 先读每个任务的 `source_path`，再读 `Cards To Reconcile` 中列出的所有卡片。",
            "2. 提取可复用内容：经验、关系判断、项目机制、证据边界、行动路线、待确认问题。",
            "3. 提出写回目标和 diff 摘要；不确定内容保留为待确认。",
            "4. 不要自动删除来源 MD；只能列出 deletion candidate、风险和确认清单。",
            "5. 获得用户明确确认后，才可删除候选 MD，并随后重建 dashboard data、运行 validation 和 link check。",
            "",
            "## Pending Dissolutions",
            "",
        ]
        if not records:
            lines.extend(["暂无待处理 group 解散任务。", ""])
        for record in records:
            lines.extend(
                [
                    "### Dissolution Task",
                    "",
                    f"- id: `{record.get('id', '')}`",
                    f"- status: `{record.get('status', '')}`",
                    f"- title: {record.get('title', '')}",
                    f"- group_level: {record.get('group_level', '')}",
                    f"- group_kind: {record.get('group_kind', '') or 'unknown'}",
                    f"- source_type: {record.get('source_type', '') or 'unknown'}",
                    f"- source_path: `{record.get('source_path', '')}`",
                    f"- source_note: {record.get('source_note', '') or '无'}",
                    f"- updatedAt: `{record.get('updatedAt', '')}`",
                    "",
                    "#### User Intent",
                    "",
                    "解散该 group，但必须先把可保留经验迁移回相关卡片；本任务不授权直接删除来源 MD。",
                    "",
                    "#### Purpose",
                    "",
                    str(record.get("purpose", "")) or "未填写。",
                    "",
                    "#### Cards To Reconcile",
                    "",
                ]
            )
            items = record.get("items", [])
            CardGroupStore.append_card_lines(lines, items if isinstance(items, list) else [], empty_line="暂无卡片；先读取 source_path 判断应补哪些卡片。")
            lines.extend(
                [
                    "",
                    "#### Required Output Before Any Deletion",
                    "",
                    "- 已读取文件清单",
                    "- 可迁移经验 -> 写回目标卡片",
                    "- 建议写回 diff 摘要",
                    "- deletion candidate 与风险",
                    "- 需要用户确认的问题",
                    "",
                ]
            )
            if record.get("review_file") or record.get("processed_at") or record.get("next_action"):
                lines.extend(
                    [
                        "#### Codex Migration Review",
                        "",
                        f"- processed_at: `{record.get('processed_at', '') or '未处理'}`",
                        f"- review_file: `{record.get('review_file', '')}`" if record.get("review_file") else "- review_file: 未生成",
                        f"- deletion_status: {record.get('deletion_status', '') or '未确认'}",
                        f"- next_action: {record.get('next_action', '') or '未填写'}",
                        "",
                    ]
                )
        return "\n".join(lines)

    @staticmethod
    def append_card_lines(lines: list[str], cards: list[object], empty_line: str) -> None:
        if not cards:
            lines.extend([empty_line, ""])
            return
        for card in cards:
            if not isinstance(card, dict):
                continue
            path = card.get("path", "")
            title = card.get("title", "")
            line = f"- [{card.get('type', '')}] {title}"
            if path:
                line += f" (`{path}`)"
            if card.get("note"):
                line += f" — {card.get('note')}"
            lines.append(line)
