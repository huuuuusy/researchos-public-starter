# ResearchOS maintenance header.
# English: Owns responsibility-aware Research Agenda parsing and public/personal projection boundaries.

"""Project a responsibility-aware Research Agenda without crossing its material boundary."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path

VALID_STATES = ("mainline", "queued", "conditional", "waiting", "paused", "closed")
VALID_LIFECYCLE_PHASES = (
    "scoping", "planned", "experiment_preparation", "production", "gated_operation",
    "writing", "release_preparation", "submitted", "under_review", "rebuttal",
    "decision", "revision", "accepted", "published", "paused", "completed",
)
BACKGROUND_LIFECYCLE_PHASES = frozenset({"submitted", "under_review", "decision"})
VALID_SCHEDULE_BUCKETS = ("today", "this_week", "later")
VALID_ATTENTION_STATES = ("today", "carryover", "upcoming", "unscheduled", "needs_next_step", "review_due", "completed")
VALID_RESPONSIBILITIES = ("lead", "support", "unclassified")
REQUIRED_ACTION_FIELDS = ("accountable_owner", "role_summary", "lifecycle_phase", "next_step", "last_verified")
ITEM_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
LOCALIZED_ITEM_FIELDS = (
    "title", "schedule_label", "accountable_owner", "owner", "role_summary", "assistant",
    "activation_trigger", "current_stage", "progress_label", "next_step", "self_action",
    "ai_action", "success_gate", "source_path", "merge_rule", "action_prompt", "adjust_prompt",
)


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start == -1:
        return ""
    rest = text[start + len(marker) :]
    next_heading = re.search(r"^## ", rest, re.MULTILINE)
    return rest[: next_heading.start()] if next_heading else rest


def _fields(block: str) -> dict[str, str]:
    return {
        match.group(1).strip(): match.group(2).strip().strip('"')
        for match in re.finditer(r"^- ([a-z0-9_]+):[ \t]*(.*)$", block, re.MULTILINE)
    }


def _integer(value: str, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _date_value(value: str) -> date | None:
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _priority_rank(priority: str) -> int:
    match = re.match(r"^P([0-9]+)", str(priority).strip(), re.IGNORECASE)
    return int(match.group(1)) if match else 99


def _freshness(last_verified: str, stale_after_days: int, *, today: date) -> tuple[str, int | None]:
    verified = _date_value(last_verified)
    if not verified:
        return "unverified", None
    age_days = (today - verified).days
    if age_days < 0:
        return "unverified", age_days
    if age_days > max(0, stale_after_days):
        return "stale", age_days
    if age_days == max(0, stale_after_days):
        return "review_due", age_days
    return "current", age_days


def _split_values(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*;\s*", str(value or "")) if part.strip()]


def _source_exists(root: Path, value: str) -> bool:
    source = str(value or "").strip()
    if not source:
        return False
    path = Path(source)
    return path.exists() if path.is_absolute() else (root / path).exists()


def _coverage_receipt(root: Path, text: str, *, today: date) -> dict[str, object]:
    fields = _fields(_section(text, "Coverage Receipt"))
    sources = _split_values(fields.get("coverage_sources", ""))
    candidates = _split_values(fields.get("coverage_candidates", ""))
    exclusions = _split_values(fields.get("coverage_exclusions", ""))
    reviewed = fields.get("coverage_reviewed", "").strip()
    stale_after_days = max(1, _integer(fields.get("coverage_stale_after_days", "14"), 14))
    freshness, age_days = _freshness(reviewed, stale_after_days, today=today)
    status = fields.get("coverage_status", "unverified").strip().lower()
    missing_sources = [source for source in sources if not _source_exists(root, source)]
    issues: list[str] = []
    if not fields.get("coverage_scope", "").strip():
        issues.append("missing_coverage_scope")
    if status != "reviewed":
        issues.append("coverage_not_reviewed")
    if not reviewed:
        issues.append("missing_coverage_reviewed")
    elif _date_value(reviewed) is None:
        issues.append("invalid_coverage_reviewed")
    elif freshness == "unverified" and age_days is not None and age_days < 0:
        issues.append("future_coverage_reviewed")
    elif freshness in {"review_due", "stale"}:
        issues.append(f"coverage_{freshness}")
    if not sources:
        issues.append("missing_coverage_sources")
    if missing_sources:
        issues.append("coverage_source_unavailable")
    if candidates:
        issues.append("unresolved_coverage_candidates")
    complete = status == "reviewed" and freshness == "current" and bool(sources) and not missing_sources and not candidates
    return {
        "scope": fields.get("coverage_scope", ""),
        "status": status,
        "reviewed": reviewed,
        "stale_after_days": stale_after_days,
        "freshness": freshness,
        "age_days": age_days,
        "sources": sources,
        "missing_sources": missing_sources,
        "candidates": candidates,
        "exclusions": exclusions,
        "issues": issues,
        "complete": complete,
    }


def _quality_issues(
    root: Path,
    *,
    fields: dict[str, str],
    responsibility: str,
    freshness: str,
    age_days: int | None,
) -> list[str]:
    issues: list[str] = []
    raw_responsibility = fields.get("responsibility", "").strip().lower()
    if not raw_responsibility:
        issues.append("missing_responsibility")
    elif raw_responsibility not in {"lead", "support"}:
        issues.append("invalid_responsibility")
    if responsibility == "unclassified" and not any(
        issue in issues for issue in {"missing_responsibility", "invalid_responsibility"}
    ):
        issues.append("unclassified_responsibility")
    for field in REQUIRED_ACTION_FIELDS:
        if not fields.get(field, "").strip():
            issues.append(f"missing_{field}")
    lifecycle_phase = fields.get("lifecycle_phase", "").strip().lower()
    if lifecycle_phase and lifecycle_phase not in VALID_LIFECYCLE_PHASES:
        issues.append("invalid_lifecycle_phase")
    if lifecycle_phase in BACKGROUND_LIFECYCLE_PHASES and not fields.get("activation_trigger", "").strip():
        issues.append("missing_activation_trigger")
    source_path = fields.get("source_path", "").strip()
    source_root = fields.get("source_root", "").strip()
    if not source_path and not source_root:
        issues.append("missing_source")
    elif source_root and not _source_exists(root, source_root):
        issues.append("source_root_unavailable")
    elif source_path and not _source_exists(root, source_path):
        issues.append("source_path_unavailable")
    last_verified = fields.get("last_verified", "").strip()
    if last_verified and _date_value(last_verified) is None:
        issues.append("invalid_last_verified")
    elif freshness == "unverified" and age_days is not None and age_days < 0:
        issues.append("future_last_verified")
    return issues


def _item_id(fields: dict[str, str], index: int, seen_ids: set[str]) -> str:
    item_id = fields.get("id", "").strip() or f"portfolio-{index + 1}"
    if not ITEM_ID_PATTERN.fullmatch(item_id):
        raise ValueError(f"invalid Research Agenda item id: {item_id}")
    if item_id in seen_ids:
        raise ValueError(f"duplicate Research Agenda item id: {item_id}")
    seen_ids.add(item_id)
    return item_id


def _prompts(
    item: dict[str, object],
    language: str,
    authority_path: str,
    presentation_mode: str,
) -> tuple[str, str]:
    title = str(item.get("title", "")).strip()
    stage = str(item.get("current_stage", "")).strip()
    next_step = str(item.get("next_step", "")).strip()
    ai_action = str(item.get("ai_action", "")).strip()
    success_gate = str(item.get("success_gate", "")).strip()
    state = str(item.get("state", "conditional")).strip()
    responsibility = str(item.get("responsibility", "unclassified")).strip()
    schedule_bucket = str(item.get("schedule_bucket", "later")).strip()
    owner = str(item.get("accountable_owner", item.get("owner", "You"))).strip()
    role_summary = str(item.get("role_summary", "")).strip()
    assistant = str(item.get("assistant", "")).strip()
    progress_done = _integer(str(item.get("progress_done", "0")))
    progress_total = _integer(str(item.get("progress_total", "0")))
    progress_label = str(item.get("progress_label", "")).strip()
    self_action = str(item.get("self_action", "")).strip()
    target_date = str(item.get("target_date", "")).strip()
    last_verified = str(item.get("last_verified", "")).strip()
    lifecycle_phase = str(item.get("lifecycle_phase", "scoping")).strip()
    activation_trigger = str(item.get("activation_trigger", "")).strip()
    progress = f"{progress_done}/{progress_total}" if progress_total else (
        progress_label or ("持续型/未量化" if language == "zh-CN" else "continuous / not quantified")
    )
    public_demo = presentation_mode == "public_demo"
    if language == "zh-CN":
        scope = "虚构公开示例" if public_demo else "本地材料"
        if responsibility == "support":
            opening = f"在辅助角色边界内处理「{title}」"
        elif responsibility == "unclassified":
            opening = f"先核对「{title}」的责任归属，再决定是否推进"
        else:
            opening = f"继续推进「{title}」" if state == "mainline" else f"评估「{title}」的下一承诺"
        action = (
            f"{opening}。责任类型：{responsibility}；最终负责人：{owner}；生命周期：{lifecycle_phase}；当前阶段：{stage}；"
            f"唯一下一步：{next_step}；助手边界：{ai_action}；完成门：{success_gate}。"
            f"重新触发条件：{activation_trigger or '当前事项可直接安排'}。"
            f"先核对{scope}权威来源 {authority_path}，返回有证据边界的候选结果；"
            "不要把辅助事项改写成用户主责，不要声称已经执行或写回。"
        )
        if public_demo:
            action += " 不要调用私人材料。"
        adjust = (
            f"核对并更新研究议程事项「{title}」。状态：{state}；时间栏：{schedule_bucket}；"
            f"目标：{target_date or '未设定'}；生命周期：{lifecycle_phase}；阶段：{stage}；里程碑：{progress}；下一步：{next_step}；"
            f"重新触发条件：{activation_trigger or '无单独外部触发条件'}；"
            f"完成门：{success_gate}；责任类型：{responsibility}；最终负责人：{owner}；"
            f"用户角色：{role_summary or '未说明'}；最近核验：{last_verified or '未核验'}；"
            f"协助：{assistant or '未分配'}；研究者动作：{self_action}；助手边界：{ai_action}。"
            "先确认新增的可核对证据和已确认判断，再提出 responsibility、accountable_owner、role_summary、"
            "lifecycle_phase、activation_trigger、current_stage、progress、next_step、schedule、state、last_verified 或 success_gate 的最小候选修改；"
            f"明确不变字段和证据缺口，只提出 {authority_path} 的候选修改，不自动写回。"
        )
        if public_demo:
            adjust += " 不要调用私人材料。"
    else:
        scope = "fictional public example" if public_demo else "local"
        item_kind = "fictional Research Agenda item" if public_demo else "local Research Agenda item"
        if responsibility == "support":
            opening = f"Work on the {item_kind} '{title}' within the support-role boundary"
        elif responsibility == "unclassified":
            opening = f"Verify responsibility for the {item_kind} '{title}' before deciding whether to proceed"
        else:
            opening = (
                f"Continue the {item_kind} '{title}'"
                if state == "mainline"
                else f"Evaluate the next commitment for the {item_kind} '{title}'"
            )
        action = (
            f"{opening}. Responsibility: {responsibility}; accountable owner: {owner}; lifecycle: {lifecycle_phase}; current stage: {stage}; "
            f"single next step: {next_step}; assistant boundary: {ai_action}; success gate: {success_gate}. "
            f"Resurface when: {activation_trigger or 'the item is explicitly scheduled'}. "
            f"Check the {scope} authority source {authority_path} and return an evidence-bounded candidate result. "
            "Do not promote a support item into user-owned work, and do not claim execution or writeback."
        )
        if public_demo:
            action += " Do not use private material."
        adjust = (
            f"Verify and update the Research Agenda item '{title}'. State: {state}; time bucket: {schedule_bucket}; "
            f"target: {target_date or 'not set'}; lifecycle: {lifecycle_phase}; stage: {stage}; milestone: {progress}; next step: {next_step}; "
            f"resurface when: {activation_trigger or 'no separate external trigger'}; "
            f"success gate: {success_gate}; responsibility: {responsibility}; accountable owner: {owner}; "
            f"user role: {role_summary or 'not stated'}; last verified: {last_verified or 'unverified'}; "
            f"support: {assistant or 'unassigned'}; researcher action: {self_action}; assistant boundary: {ai_action}. "
            "Confirm new verifiable evidence and approved judgments, then propose the smallest candidate change to responsibility, "
            "accountable owner, role, lifecycle phase, activation trigger, stage, progress, next step, schedule, state, freshness, or success gate. "
            f"State unchanged fields and evidence gaps; propose only a candidate change to {authority_path}. Do not write it automatically."
        )
        if public_demo:
            adjust += " Do not use private material."
    return action, adjust


def research_agenda_from_markdown(
    root: Path,
    path: Path,
    *,
    language: str,
    presentation_mode: str,
    boundary: str,
    sensitivity: str,
    updated: str = "",
    today: date | None = None,
    source_base: Path | None = None,
) -> dict[str, object]:
    """Return one public-demo or local-private responsibility projection.

    ``source_base`` is the folder the portfolio's ``source_path`` and coverage sources are relative to
    (the vault in personal-vault mode, as ``ros --root`` reads them); it defaults to ``root``."""
    source_base = source_base or root
    authority_path = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    if not path.exists():
        return {
            "available": False,
            "counts": {state: 0 for state in VALID_STATES},
            "responsibility_counts": {responsibility: 0 for responsibility in VALID_RESPONSIBILITIES},
            "schedule_counts": {bucket: 0 for bucket in VALID_SCHEDULE_BUCKETS},
            "phase_counts": {phase: 0 for phase in VALID_LIFECYCLE_PHASES},
            "answer": {
                "lead_active": 0,
                "lead_open": 0,
                "support_active": 0,
                "support_open": 0,
                "unclassified": 0,
                "waiting": 0,
                "queued": 0,
                "paused": 0,
                "needs_review": 0,
                "needs_attention": 0,
                "registered_total": 0,
                "classified_total": 0,
                "coverage_verified": False,
                "coverage_candidates": 0,
                "top_priority_ids": [],
            },
            "coverage": {
                "status": "unverified",
                "complete": False,
                "issues": ["authority_file_unavailable"],
                "sources": [],
                "candidates": [],
            },
            "integrity": {
                "status": "needs_attention",
                "issue_count": 1,
                "issues": [{"scope": "authority", "codes": ["authority_file_unavailable"]}],
            },
            "items": [],
            "path": authority_path,
            "presentation_mode": presentation_mode,
            "sensitivity": sensitivity,
            "updated": updated,
        }

    text = path.read_text(encoding="utf-8")
    items_block = _section(text, "Responsibility Items") or _section(text, "Independent Items")
    matches = list(re.finditer(r"^### (.+)$", items_block, re.MULTILINE))
    items: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    current_date = today or date.today()
    coverage = _coverage_receipt(source_base, text, today=current_date)
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(items_block)
        fields = _fields(items_block[match.end() : end])
        state = fields.get("state", "conditional").strip().lower()
        if state not in VALID_STATES:
            state = "conditional"
        lifecycle_phase = fields.get("lifecycle_phase", "scoping").strip().lower()
        if lifecycle_phase not in VALID_LIFECYCLE_PHASES:
            lifecycle_phase = "scoping"
        schedule_bucket = fields.get("schedule_bucket", "later").strip().lower()
        if schedule_bucket not in VALID_SCHEDULE_BUCKETS:
            schedule_bucket = "later"
        raw_responsibility = fields.get("responsibility", "").strip().lower()
        responsibility = raw_responsibility if raw_responsibility in {"lead", "support"} else "unclassified"
        progress_total = max(0, _integer(fields.get("progress_total", "0")))
        progress_done = max(0, _integer(fields.get("progress_done", "0")))
        if progress_total:
            progress_done = min(progress_done, progress_total)
        else:
            progress_done = 0
        last_verified = fields.get("last_verified", "").strip()
        stale_after_days = max(1, _integer(fields.get("stale_after_days", "14"), 14))
        freshness, age_days = _freshness(
            last_verified,
            stale_after_days,
            today=current_date,
        )
        source_path = fields.get("source_path", authority_path).strip() or authority_path
        accountable_owner = fields.get("accountable_owner", fields.get("owner", "")).strip()
        quality_issues = _quality_issues(
            source_base,
            fields=fields,
            responsibility=responsibility,
            freshness=freshness,
            age_days=age_days,
        )
        item: dict[str, object] = {
            "id": _item_id(fields, index, seen_ids),
            "title": title,
            "state": state,
            "schedule_bucket": schedule_bucket,
            "schedule_label": fields.get("schedule_label", ""),
            "schedule_order": _integer(fields.get("schedule_order", str((index + 1) * 10)), (index + 1) * 10),
            "priority": fields.get("priority", "P2"),
            "priority_rank": _priority_rank(fields.get("priority", "P2")),
            "project_maturity": fields.get("project_maturity", fields.get("incubation_maturity", "")),
            "related_people": _split_values(fields.get("related_people", "")),
            "responsibility": responsibility,
            "accountable_owner": accountable_owner,
            "owner": accountable_owner,
            "role_summary": fields.get("role_summary", ""),
            "assistant": fields.get("assistant", "自选助手" if language == "zh-CN" else "Chosen assistant"),
            "lane": fields.get("lane", "research"),
            "output_type": fields.get("output_type", "research-output"),
            "lifecycle_phase": lifecycle_phase,
            "activation_trigger": fields.get("activation_trigger", ""),
            "current_stage": fields.get("current_stage", ""),
            "progress_done": progress_done,
            "progress_total": progress_total,
            "progress_percent": round(progress_done / progress_total * 100) if progress_total else 0,
            "has_numeric_progress": bool(progress_total),
            "progress_label": fields.get("progress_label", ""),
            "next_step": fields.get("next_step", ""),
            "self_action": fields.get("self_action", ""),
            "ai_action": fields.get("ai_action", ""),
            "success_gate": fields.get("success_gate", ""),
            "target_date": fields.get("target_date", ""),
            "last_verified": last_verified,
            "stale_after_days": stale_after_days,
            "freshness": freshness,
            "age_days": age_days,
            "source_path": source_path,
            "source_anchor": fields.get("source_anchor", ""),
            "source_root": fields.get("source_root", ""),
            "source_available": _source_exists(source_base, fields.get("source_root", "").strip() or source_path),
            "merge_rule": fields.get("merge_rule", ""),
            "quality_issues": quality_issues,
            "needs_attention": bool(quality_issues) or freshness in {"review_due", "stale", "unverified"},
        }
        lifecycle_state = "completed" if state == "closed" else state if state in {"waiting", "paused"} else "open"
        explicit_attention_state = fields.get("attention_state", "").strip().lower()
        attention_date = fields.get("attention_date", "").strip()
        review_date = fields.get("review_date", "").strip()
        deadline = fields.get("deadline", "").strip()
        attention_date = attention_date if _date_value(attention_date) else ""
        review_date = review_date if _date_value(review_date) else ""
        deadline = deadline if _date_value(deadline) else ""
        if lifecycle_state == "completed":
            attention_state = "completed"
        elif lifecycle_state in {"waiting", "paused"}:
            attention_state = "unscheduled"
        elif explicit_attention_state in VALID_ATTENTION_STATES:
            attention_state = explicit_attention_state
        elif schedule_bucket == "today":
            attention_state = "today"
        elif schedule_bucket == "this_week":
            attention_state = "upcoming"
        else:
            attention_state = "unscheduled"
        target_date = fields.get("target_date", "").strip()
        item.update({
            "provider_id": "research_portfolio",
            "lifecycle_state": lifecycle_state,
            "attention_state": attention_state,
            "attention_date": attention_date,
            "review_date": review_date,
            "deadline": deadline or (target_date if _date_value(target_date) else ""),
            "today_order": item["schedule_order"] if attention_state == "today" else 0,
            "carryover_days": 0,
            "attention_source": "public_demo_projection" if presentation_mode == "public_demo" else "agenda_projection",
        })
        item["action_prompt"], item["adjust_prompt"] = _prompts(
            item, language, authority_path, presentation_mode
        )
        items.append(item)

    items.sort(
        key=lambda item: (
            {"lead": 0, "support": 1, "unclassified": 2}.get(str(item.get("responsibility")), 2),
            0 if item.get("state") == "mainline" else 1,
            _integer(str(item.get("priority_rank", 99)), 99),
            _integer(str(item.get("schedule_order", 999)), 999),
            str(item.get("title", "")),
        )
    )
    counts = Counter(str(item.get("state", "conditional")) for item in items)
    phase_counts = Counter(str(item.get("lifecycle_phase", "scoping")) for item in items)
    schedule_counts = Counter(str(item.get("schedule_bucket", "later")) for item in items)
    responsibility_counts = Counter(str(item.get("responsibility", "unclassified")) for item in items)
    lead_active = [
        item for item in items
        if item.get("responsibility") == "lead" and item.get("state") == "mainline"
    ]
    support_active = [
        item for item in items
        if item.get("responsibility") == "support" and item.get("state") == "mainline"
    ]
    open_items = [item for item in items if item.get("state") != "closed"]
    needs_review = [
        item for item in open_items
        if item.get("needs_attention")
    ]
    integrity_issues = [
        {"scope": "item", "item_id": str(item.get("id", "")), "codes": list(item.get("quality_issues", []))}
        for item in items
        if item.get("quality_issues")
    ]
    if coverage.get("issues"):
        integrity_issues.insert(0, {"scope": "coverage", "codes": list(coverage.get("issues", []))})
    return {
        "available": bool(items),
        "boundary": boundary,
        "counts": {state: counts[state] for state in VALID_STATES},
        "phase_counts": {phase: phase_counts[phase] for phase in VALID_LIFECYCLE_PHASES},
        "responsibility_counts": {
            responsibility: responsibility_counts[responsibility]
            for responsibility in VALID_RESPONSIBILITIES
        },
        "schedule_counts": {bucket: schedule_counts[bucket] for bucket in VALID_SCHEDULE_BUCKETS},
        "answer": {
            "lead_active": len(lead_active),
            "lead_open": sum(1 for item in open_items if item.get("responsibility") == "lead"),
            "support_active": len(support_active),
            "support_open": sum(1 for item in open_items if item.get("responsibility") == "support"),
            "unclassified": responsibility_counts["unclassified"],
            "waiting": counts["waiting"],
            "queued": counts["queued"],
            "paused": counts["paused"],
            "needs_review": len(needs_review),
            "needs_attention": len(needs_review),
            "registered_total": len(items),
            "classified_total": len(items) - responsibility_counts["unclassified"],
            "coverage_verified": bool(coverage.get("complete")),
            "coverage_candidates": len(coverage.get("candidates", [])),
            "top_priority_ids": [str(item.get("id", "")) for item in lead_active[:3]],
        },
        "coverage": coverage,
        "integrity": {
            "status": "pass" if not integrity_issues and coverage.get("complete") else "needs_attention",
            "issue_count": sum(len(issue.get("codes", [])) for issue in integrity_issues),
            "issues": integrity_issues,
        },
        "items": items,
        "path": authority_path,
        "presentation_mode": presentation_mode,
        "sensitivity": sensitivity,
        "updated": updated,
    }


def public_research_agenda(root: Path, starter_dir: Path, public_data: dict[str, object]) -> dict[str, object]:
    language = str(public_data.get("case_materials", {}).get("content_language", "en"))
    path = starter_dir / ("demo-research-agenda.zh.md" if language == "zh-CN" else "demo-research-agenda.md")
    # The fictional agenda is set on its own date, so its schedule and freshness read the same on any day.
    reference = re.search(r"^reference_date:\s*(\d{4}-\d{2}-\d{2})\s*$", path.read_text(encoding="utf-8") if path.exists() else "", re.MULTILINE)
    projection_date = _date_value(reference.group(1) if reference else str(public_data.get("generated_at", "")))
    if not bool(public_data.get("case_materials", {}).get("enabled", True)):
        return research_agenda_from_markdown(
            root,
            root / "__disabled_research_agenda__.md",
            language=language,
            presentation_mode="public_demo",
            boundary="fictional_public_demo_only",
            sensitivity="public",
            updated=str(public_data.get("generated_at", "")),
            today=projection_date,
        ) | {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path)}
    agenda = research_agenda_from_markdown(
        root,
        path,
        language=language,
        presentation_mode="public_demo",
        boundary="fictional_public_demo_only",
        sensitivity="public",
        updated=str(public_data.get("generated_at", "")),
            today=projection_date,
    )
    localized_by_language: dict[str, dict[str, dict[str, object]]] = {}
    for localized_language, filename in (("zh-CN", "demo-research-agenda.zh.md"), ("en", "demo-research-agenda.md")):
        localized_agenda = research_agenda_from_markdown(
            root,
            starter_dir / filename,
            language=localized_language,
            presentation_mode="public_demo",
            boundary="fictional_public_demo_only",
            sensitivity="public",
            updated=str(public_data.get("generated_at", "")),
            today=projection_date,
        )
        localized_by_language[localized_language] = {
            str(item.get("id", "")): {field: item.get(field, "") for field in LOCALIZED_ITEM_FIELDS}
            for item in localized_agenda.get("items", [])
        }
    for item in agenda.get("items", []):
        item_id = str(item.get("id", ""))
        item["localized"] = {
            localized_language: by_id[item_id]
            for localized_language, by_id in localized_by_language.items()
            if item_id in by_id
        }
    if reference:
        agenda["reference_date"] = reference.group(1)
    return agenda


def personal_research_agenda(
    root: Path,
    personal_data: dict[str, object],
    language: str,
    vault_root: Path | None = None,
) -> dict[str, object]:
    return research_agenda_from_markdown(
        root,
        (vault_root or root) / "06_active_context" / "research-portfolio.md",
        language=language,
        presentation_mode="personal_vault",
        boundary="local_private_material",
        sensitivity="private",
        updated=str(personal_data.get("generated_at", "")),
        source_base=vault_root or root,
    )
