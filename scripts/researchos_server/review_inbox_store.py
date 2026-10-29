# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard server 中关于「review inbox store」的辅助 owner；保持 serve_dashboard.py 只做 HTTP 编排。
# English: Helper owner for review inbox store in the local ResearchOS dashboard server; keeps serve_dashboard.py HTTP-orchestration-only.

"""Review inbox persistence helpers for the local ResearchOS dashboard server."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from researchos_kernel.atomic_files import append_text, atomic_write_text, runtime_state_transaction


class ReviewInboxValidationError(ValueError):
    """Raised when dashboard review input should be rejected with HTTP 400."""


@dataclass(frozen=True)
class ReviewInboxStore:
    root: Path
    feedback_jsonl: Path
    feedback_md: Path
    confirmation_json: Path
    confirmation_md: Path

    def save_feedback(self, payload: dict[str, object]) -> dict[str, object]:
        target_path = self.existing_md_path(payload.get("target_path", ""), required=True)
        feedback = str(payload.get("feedback", "")).strip()
        if not feedback:
            raise ReviewInboxValidationError("Feedback is empty")
        record = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "target_path": target_path,
            "person_name": str(payload.get("person_name", "")).strip(),
            "category": str(payload.get("category", "补充/纠错")).strip(),
            "feedback": feedback,
            "source": "dashboard",
            "status": "pending_codex_review",
        }
        with runtime_state_transaction(lock_path=self.feedback_jsonl.with_name(f'.{self.feedback_jsonl.name}.lock')):
            append_text(self.feedback_jsonl, json.dumps(record, ensure_ascii=False) + "\n")
            self.ensure_feedback_markdown()
            append_text(self.feedback_md, self.render_feedback_entry(record))
        return record

    def withdraw_confirmation(self, payload: dict[str, object]) -> dict[str, object]:
        decision_id = str(payload.get("decision_id", "")).strip()
        if not decision_id or len(decision_id) > 240:
            raise ReviewInboxValidationError("Invalid decision id")
        with runtime_state_transaction(lock_path=self.feedback_jsonl.with_name(f'.{self.feedback_jsonl.name}.lock')):
            records = self.read_confirmation_records()
            removed = records.pop(decision_id, None)
            atomic_write_text(self.confirmation_json, json.dumps(records, ensure_ascii=False, indent=2) + "\n")
            atomic_write_text(self.confirmation_md, self.render_confirmation_markdown(records))
        return {
            "decision_id": decision_id,
            "withdrawn": isinstance(removed, dict),
            "remaining": len(records),
        }

    def existing_md_path(self, value: object, required: bool) -> str:
        path = str(value or "").strip()
        if not path:
            if required:
                raise ReviewInboxValidationError("Invalid target path")
            return ""
        if not path.endswith(".md") or path.startswith("/") or ".." in Path(path).parts:
            raise ReviewInboxValidationError("Invalid target path")
        root = self.root.resolve()
        target = (root / path).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ReviewInboxValidationError("Invalid target path") from exc
        if not target.exists():
            raise ReviewInboxValidationError("Target file not found")
        return path

    def read_confirmation_records(self) -> dict[str, object]:
        if not self.confirmation_json.exists():
            return {}
        try:
            records = json.loads(self.confirmation_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return records if isinstance(records, dict) else {}

    def ensure_feedback_markdown(self) -> None:
        if self.feedback_md.exists():
            return
        atomic_write_text(
            self.feedback_md,
            "---\n"
            "type: active_context\n"
            'title: "UI Feedback Inbox"\n'
            "status: active\n"
            "created: 2026-06-16\n"
            "updated: 2026-06-16\n"
            "tags:\n"
            "  - dashboard\n"
            "  - feedback\n"
            "  - pending-review\n"
            "sensitivity: sensitive\n"
            "---\n\n"
            "# UI Feedback Inbox\n\n"
            "## Agent Summary\n\n"
            "本文件是 dashboard 反馈收件箱，用于暂存用户在本地 UI 中提交的人物档案补充、纠错、主页链接、论文角色和关系边界说明。它不是稳定长期记忆；所有条目都需要 Codex 按证据等级和 sensitive/local-only 边界审阅后，才可写入目标 md。\n\n"
            "本文件由本地 dashboard 的补充说明框追加生成。这里不是稳定长期记忆；所有条目都需要 Codex 按证据边界审阅后，才可写入目标 md。\n",
        )

    @staticmethod
    def render_feedback_entry(record: dict[str, object]) -> str:
        return (
            "\n## Pending Feedback\n\n"
            f"- created_at: `{record['created_at']}`\n"
            f"- target_path: `{record['target_path']}`\n"
            f"- person_name: {record['person_name'] or '未指定'}\n"
            f"- category: {record['category']}\n"
            "- status: pending_codex_review\n\n"
            f"{record['feedback']}\n"
        )

    @staticmethod
    def render_confirmation_markdown(records: dict[str, object]) -> str:
        lines = [
            "---",
            "type: active_context",
            'title: "UI Confirmation Decisions"',
            "status: active",
            "created: 2026-06-17",
            "updated: 2026-06-17",
            "tags:",
            "  - dashboard",
            "  - confirmation",
            "  - pending-review",
            "sensitivity: internal",
            "---",
            "",
            "# UI Confirmation Decisions",
            "",
            "## Agent Summary",
            "",
            "本文件由本地 dashboard 的直接确认按钮生成，记录用户对候选判断的最新选择。它不是稳定长期记忆；所有条目都需要 Codex 审阅后，才可写入 decision log、stable memory 或 public-facing context。",
            "",
        ]
        sorted_records = sorted(
            (item for item in records.values() if isinstance(item, dict)),
            key=lambda row: str(row.get("updated_at", "")),
            reverse=True,
        )
        pending_records = [
            item
            for item in sorted_records
            if not str(item.get("status", "pending_codex_review")).strip().startswith("processed")
        ]
        processed_count = len(sorted_records) - len(pending_records)
        lines.extend(
            [
                "## Queue Summary",
                "",
                f"- pending_or_current: {len(pending_records)}",
                f"- processed_entries_in_active_json: {processed_count}",
                "- processed_archive: `06_active_context/work_state/confirmation-archives/`",
                "",
            ]
        )
        for item in pending_records:
            item_status = str(item.get("status", "pending_codex_review")).strip() or "pending_codex_review"
            lines.extend(
                [
                    "## Pending Confirmation",
                    "",
                    f"- updated_at: `{item.get('updated_at', '')}`",
                    f"- decision_id: `{item.get('decision_id', '')}`",
                    f"- choice: {item.get('choice_label') or item.get('choice', '')}",
                    f"- target_path: `{item.get('target_path', '')}`" if item.get("target_path") else "- target_path: 未指定",
                    f"- status: {item_status}",
                    f"- processed_at: `{item.get('processed_at', '')}`" if item.get("processed_at") else "- processed_at: 未处理",
                    "",
                    f"对象：{item.get('title', '') or '未指定'}",
                    "",
                    f"问题：{item.get('question', '') or '未指定'}",
                    "",
                    f"修改建议：{item.get('suggestion', '') or '无'}",
                    "",
                    f"Codex 处理结果：{item.get('codex_result', '') or '待处理'}",
                    "",
                ]
            )
        return "\n".join(lines)
