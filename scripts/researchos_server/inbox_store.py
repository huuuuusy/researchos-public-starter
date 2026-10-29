# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard server 中关于「inbox store」的辅助 owner；保持 serve_dashboard.py 只做 HTTP 编排。
# English: Helper owner for inbox store in the local ResearchOS dashboard server; keeps serve_dashboard.py HTTP-orchestration-only.

"""Inbox persistence helpers for the local ResearchOS dashboard server."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from researchos_kernel.atomic_files import append_text, atomic_write_text


@dataclass(frozen=True)
class InboxStore:
    root: Path
    cleanup_archive: Path

    def safe_md_path(self, value: object) -> str:
        path = str(value or "").strip()
        if not path:
            return ""
        if not path.endswith(".md") or path.startswith("/") or ".." in Path(path).parts:
            return ""
        root = self.root.resolve()
        target = (root / path).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            return ""
        return path

    @staticmethod
    def inbox_status_is_active(value: object) -> bool:
        status = str(value or "").strip().lower()
        if not status:
            return True
        if (
            status == "withdrawn"
            or status == "done"
            or status == "archived"
            or status.startswith("processed_")
            or status.startswith("done")
            or "skipped" in status
            or "superseded" in status
            or "merged" in status
        ):
            return False
        if "pending" in status or "in_progress" in status or "queued" in status:
            return True
        return True

    def archive_cleared_inbox_records(self, source: str, records: list[object]) -> None:
        if not records:
            return
        cleaned_at = datetime.now().isoformat(timespec="seconds")
        append_text(
            self.cleanup_archive,
            "".join(
                json.dumps({"cleaned_at": cleaned_at, "source": source, "record": record}, ensure_ascii=False) + "\n"
                for record in records
            ),
        )

    @staticmethod
    def read_json_object(path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def read_json_array(path: Path) -> list[object]:
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return data if isinstance(data, list) else []

    @staticmethod
    def write_json(path: Path, data: object) -> None:
        atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def write_empty_inbox_md(self, path: Path, title: str, summary: str, empty_line: str) -> None:
        today = datetime.now().date().isoformat()
        atomic_write_text(
            path,
            "\n".join(
                [
                    "---",
                    "type: active_context",
                    f'title: "{title}"',
                    "status: active",
                    f"created: {today}",
                    f"updated: {today}",
                    "tags:",
                    "  - dashboard",
                    "  - inbox",
                    "  - cleaned",
                    "sensitivity: internal",
                    "---",
                    "",
                    f"# {title}",
                    "",
                    "## Agent Summary",
                    "",
                    summary,
                    "",
                    "## Pending Items",
                    "",
                    empty_line,
                    "",
                    "## Cleanup Note",
                    "",
                    f"- cleaned_at: `{datetime.now().isoformat(timespec='seconds')}`",
                    "- cleared_scope: processed / withdrawn / skipped / merged records only",
                    f"- archive_file: `{self.cleanup_archive.resolve().relative_to(self.root.resolve())}`",
                    "",
                ]
            ),
        )
