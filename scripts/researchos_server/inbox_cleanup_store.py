# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard server 中关于「inbox cleanup store」的辅助 owner；保持 serve_dashboard.py 只做 HTTP 编排。
# English: Helper owner for inbox cleanup store in the local ResearchOS dashboard server; keeps serve_dashboard.py HTTP-orchestration-only.

"""Processed-inbox cleanup helpers for the local ResearchOS dashboard server."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from researchos_server.inbox_store import InboxStore
from researchos_kernel.atomic_files import atomic_write_text, runtime_state_transaction


@dataclass(frozen=True)
class InboxArraySpec:
    key: str
    json_path: Path
    md_path: Path
    title: str
    summary: str
    empty_line: str


@dataclass(frozen=True)
class InboxCleanupStore:
    store: InboxStore
    confirmation_json: Path
    confirmation_md: Path
    feedback_jsonl: Path
    feedback_md: Path
    array_specs: tuple[InboxArraySpec, ...]

    def clear_processed(self) -> dict[str, object]:
        with runtime_state_transaction(lock_path=self.confirmation_json.with_name(f'.{self.confirmation_json.name}.lock')):
            return self._clear_processed_locked()

    def _clear_processed_locked(self) -> dict[str, object]:
        cleared: dict[str, int] = {}
        remaining: dict[str, int] = {}
        state: dict[str, object] = {"confirmations": {}, "feedback": []}
        state.update({spec.key: [] for spec in self.array_specs})
        self.clear_confirmations(cleared, remaining, state)
        self.clear_feedback(cleared, remaining, state)
        self.clear_array_inboxes(cleared, remaining, state)
        return {"cleared": cleared, "remaining": remaining, "state": state}

    def clear_confirmations(self, cleared: dict[str, int], remaining: dict[str, int], state: dict[str, object]) -> None:
        records = self.store.read_json_object(self.confirmation_json)
        next_records: dict[str, object] = {}
        removed_records: list[object] = []
        for key, record in records.items():
            if isinstance(record, dict) and self.store.inbox_status_is_active(record.get("status", "")):
                next_records[key] = record
            else:
                removed_records.append({"id": key, **(record if isinstance(record, dict) else {"value": record})})
        if records or removed_records:
            self.store.write_json(self.confirmation_json, next_records)
            self.store.archive_cleared_inbox_records("confirmation", removed_records)
            cleared["confirmation"] = len(removed_records)
            remaining["confirmation"] = len(next_records)
            state["confirmations"] = next_records
            if not next_records:
                self.store.write_empty_inbox_md(
                    self.confirmation_md,
                    "UI Confirmation Decisions",
                    "本文件记录 dashboard 确认按钮生成的候选判断。已处理记录已清理到 cleanup archive；当前只保留仍需 Codex 处理的确认。",
                    "暂无 pending confirmation。",
                )

    def clear_feedback(self, cleared: dict[str, int], remaining: dict[str, int], state: dict[str, object]) -> None:
        next_records: list[dict[str, object]] = []
        removed_records: list[object] = []
        if self.feedback_jsonl.exists():
            for line in self.feedback_jsonl.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict) and self.store.inbox_status_is_active(record.get("status", "")):
                    next_records.append(record)
                else:
                    removed_records.append(record)
            atomic_write_text(
                self.feedback_jsonl,
                "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in next_records),
            )
            self.store.archive_cleared_inbox_records("feedback", removed_records)
            cleared["feedback"] = len(removed_records)
            remaining["feedback"] = len(next_records)
            state["feedback"] = next_records
            if not next_records:
                self.store.write_empty_inbox_md(
                    self.feedback_md,
                    "UI Feedback Inbox",
                    "本文件暂存 dashboard 反馈。已处理记录已清理到 cleanup archive；当前只保留仍需 Codex 审阅的反馈。",
                    "暂无 pending feedback。",
                )
        state["feedback"] = next_records

    def clear_array_inboxes(self, cleared: dict[str, int], remaining: dict[str, int], state: dict[str, object]) -> None:
        for spec in self.array_specs:
            records = self.store.read_json_array(spec.json_path)
            if not records:
                cleared[spec.key] = 0
                remaining[spec.key] = 0
                state[spec.key] = []
                continue
            active_records = [
                item for item in records if isinstance(item, dict) and self.store.inbox_status_is_active(item.get("status", ""))
            ]
            removed_records = [
                item for item in records if not (isinstance(item, dict) and self.store.inbox_status_is_active(item.get("status", "")))
            ]
            self.store.write_json(spec.json_path, active_records)
            self.store.archive_cleared_inbox_records(spec.key, removed_records)
            cleared[spec.key] = len(removed_records)
            remaining[spec.key] = len(active_records)
            state[spec.key] = active_records
            if not active_records:
                self.store.write_empty_inbox_md(spec.md_path, spec.title, spec.summary, spec.empty_line)
