# ResearchOS maintenance header.
# 中文：短期注意力台账的数据契约与投影；只拥有何时再看和本步完成回执，不拥有项目事实。条目怎样随动作变化、写成什么样也在这里定，写入只由 attention_schedule_store 做。
# English: Data contract and projection for the short-term attention ledger; owns when-to-resurface and step receipts, not project facts. It also defines how an entry changes with an action and how it is rendered; only attention_schedule_store writes it.

"""Read the local Markdown attention schedule without treating it as stable memory."""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from pathlib import Path


ATTENTION_PATH = Path("06_active_context/work_state/attention-schedule.md")
VALID_STATUSES = frozenset({"scheduled", "waiting", "paused", "needs_next_step", "unscheduled"})
ALLOWED_ACTIONS = frozenset({"schedule", "waiting", "paused", "complete_step", "clear"})
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
SECTION_PATTERN = re.compile(r"(?ms)^### (?P<key>[^\n]+)\n(?P<body>.*?)(?=^### |\Z)")


class AttentionScheduleError(ValueError):
    """Raised when an attention mutation is unsafe or invalid."""


def date_value(value: object) -> date | None:
    try:
        return datetime.strptime(str(value or "").strip(), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def step_signature(next_step: object) -> str:
    normalized = " ".join(str(next_step or "").split()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16] if normalized else ""


def _fields(block: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2).strip().strip('"')
        for match in re.finditer(r"(?m)^- ([a-z0-9_]+):[ \t]*(.*)$", block)
    }


def item_key(provider_id: object, item_id: object) -> str:
    provider = str(provider_id or "").strip()
    item = str(item_id or "").strip()
    return f"{provider}:{item}" if provider and item else ""


def read_attention_schedule(root: Path, path: Path | None = None) -> dict[str, object]:
    schedule_path = path or (root / ATTENTION_PATH)
    if not schedule_path.exists():
        return {
            "available": False,
            "items": [],
            "items_by_key": {},
            "path": ATTENTION_PATH.as_posix(),
            "schema_id": "researchos-attention-schedule-v1",
        }
    text = schedule_path.read_text(encoding="utf-8")
    items: list[dict[str, object]] = []
    seen: set[str] = set()
    for match in SECTION_PATTERN.finditer(text):
        fields = _fields(match.group("body"))
        provider_id = fields.get("provider_id", "").strip()
        source_item_id = fields.get("item_id", "").strip()
        key = item_key(provider_id, source_item_id)
        if (
            not key
            or key in seen
            or not ID_PATTERN.fullmatch(provider_id)
            or not ID_PATTERN.fullmatch(source_item_id)
            or match.group("key").strip() != key
        ):
            continue
        seen.add(key)
        status = fields.get("status", "unscheduled").strip().lower()
        if status not in VALID_STATUSES:
            status = "unscheduled"
        attention_date = fields.get("attention_date", "").strip()
        review_date = fields.get("review_date", "").strip()
        try:
            today_order = max(0, int(fields.get("today_order", "0") or 0))
        except ValueError:
            today_order = 0
        items.append({
            "key": key,
            "provider_id": provider_id,
            "item_id": source_item_id,
            "attention_date": attention_date if date_value(attention_date) else "",
            "review_date": review_date if date_value(review_date) else "",
            "today_order": today_order,
            "status": status,
            "completed_step_hash": fields.get("completed_step_hash", "").strip(),
            "updated_at": fields.get("updated_at", "").strip(),
            "last_action": fields.get("last_action", "").strip(),
        })
    items.sort(key=lambda item: (int(item.get("today_order", 0) or 0), str(item.get("key", ""))))
    return {
        "available": True,
        "items": items,
        "items_by_key": {str(item["key"]): item for item in items},
        "path": schedule_path.relative_to(root).as_posix() if schedule_path.is_relative_to(root) else str(schedule_path),
        "schema_id": "researchos-attention-schedule-v1",
    }


def project_attention(
    item: dict[str, object],
    record: dict[str, object] | None,
    *,
    today: date,
) -> dict[str, object]:
    """Combine a project projection with its independent attention record."""
    record = record or {}
    lifecycle_state = {
        "closed": "completed",
        "waiting": "waiting",
        "paused": "paused",
    }.get(str(item.get("state", "")).strip(), "open")
    signature = step_signature(item.get("next_step", ""))
    completed_signature = str(record.get("completed_step_hash", "")).strip()
    record_status = str(record.get("status", "unscheduled")).strip()
    attention = date_value(record.get("attention_date"))
    review = date_value(record.get("review_date"))
    if lifecycle_state == "completed":
        attention_state = "completed"
    elif record_status == "needs_next_step" and completed_signature and completed_signature == signature:
        attention_state = "needs_next_step"
    elif review and review <= today and record_status in {"waiting", "paused"}:
        attention_state = "review_due"
    elif record_status in {"waiting", "paused"}:
        attention_state = record_status
    elif attention:
        attention_state = "carryover" if attention < today else "today" if attention == today else "upcoming"
    else:
        attention_state = "unscheduled"
    deadline = str(item.get("target_date", "")).strip()
    deadline = deadline if date_value(deadline) else ""
    return {
        "provider_id": "research_portfolio",
        "item_id": str(item.get("id", "")),
        "lifecycle_state": lifecycle_state,
        "attention_state": attention_state,
        "attention_date": str(record.get("attention_date", "")),
        "review_date": str(record.get("review_date", "")),
        "deadline": deadline,
        "today_order": int(record.get("today_order", 0) or 0),
        "carryover_days": (today - attention).days if attention and attention < today else 0,
        "next_step_hash": signature,
        "completed_step_hash": completed_signature,
        "last_attention_action": str(record.get("last_action", "")),
        "attention_updated_at": str(record.get("updated_at", "")),
        "attention_source": "attention_schedule" if record else "unassigned",
    }


def project_items(root: Path, provider_id: str, items: dict[str, dict[str, object]], *, today: date) -> dict[str, dict[str, object]]:
    """Read-only: each item's attention projection from the local schedule."""
    records = read_attention_schedule(root).get("items_by_key", {})
    return {item_id: project_attention({**fields, "id": item_id}, records.get(item_key(provider_id, item_id)), today=today)
            for item_id, fields in items.items()}


def _order(value: object) -> int:
    try:
        return max(0, min(9999, int(value or 0)))
    except (TypeError, ValueError):
        return 0


def next_record(
    previous: dict[str, object] | None,
    *,
    provider_id: object,
    item_id: object,
    action: object,
    now: datetime,
    attention_date: object = "",
    review_date: object = "",
    today_order: object = 0,
    next_step: object = "",
) -> tuple[str, dict[str, object] | None]:
    """(item key, the entry after one attention action); None when the action clears the entry.

    The store writes this record; the public starter prints it for the researcher to paste."""
    provider = str(provider_id or "").strip()
    source_item = str(item_id or "").strip()
    normalized_action = str(action or "").strip().lower()
    if not ID_PATTERN.fullmatch(provider) or not ID_PATTERN.fullmatch(source_item):
        raise AttentionScheduleError("Invalid attention item identity")
    if normalized_action not in ALLOWED_ACTIONS:
        raise AttentionScheduleError("Unsupported attention action")
    key = item_key(provider, source_item)
    if normalized_action == "clear":
        return key, None
    record = dict(previous or {})
    record.update({
        "key": key,
        "provider_id": provider,
        "item_id": source_item,
        "updated_at": now.isoformat(timespec="seconds"),
        "last_action": normalized_action,
    })
    if normalized_action == "schedule":
        normalized_date = str(attention_date or "").strip()
        if date_value(normalized_date) is None:
            raise AttentionScheduleError("Scheduling requires a YYYY-MM-DD attention_date")
        record.update({
            "attention_date": normalized_date,
            "review_date": "",
            "status": "scheduled",
            "completed_step_hash": "",
            "today_order": _order(today_order),
        })
    elif normalized_action in {"waiting", "paused"}:
        normalized_review = str(review_date or "").strip()
        if normalized_review and date_value(normalized_review) is None:
            raise AttentionScheduleError("review_date must use YYYY-MM-DD")
        record.update({
            "attention_date": "",
            "review_date": normalized_review,
            "status": normalized_action,
            "completed_step_hash": "",
            "today_order": 0,
        })
    elif normalized_action == "complete_step":
        signature = step_signature(next_step)
        if not signature:
            raise AttentionScheduleError("complete_step requires the bound next step")
        record.update({
            "attention_date": "",
            "review_date": "",
            "status": "needs_next_step",
            "completed_step_hash": signature,
            "today_order": 0,
        })
    if str(record.get("status", "")) not in VALID_STATUSES:
        raise AttentionScheduleError("Invalid attention status")
    return key, record


def entry_lines(key: str, record: dict[str, object]) -> list[str]:
    """One entry of the schedule file, as the store writes it (a blank line ends it)."""
    return [
        f"### {key}",
        "",
        f"- provider_id: {record.get('provider_id', '')}",
        f"- item_id: {record.get('item_id', '')}",
        f"- attention_date: {record.get('attention_date', '')}",
        f"- review_date: {record.get('review_date', '')}",
        f"- today_order: {int(record.get('today_order', 0) or 0)}",
        f"- status: {record.get('status', 'unscheduled')}",
        f"- completed_step_hash: {record.get('completed_step_hash', '')}",
        f"- updated_at: {record.get('updated_at', '')}",
        f"- last_action: {record.get('last_action', '')}",
        "",
    ]
