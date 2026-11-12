"""Conversation-first task and writeback contract shared by public surfaces."""

from __future__ import annotations

from typing import Any


RESULT_MODES = ("answer", "artifact", "writeback")


def authority_contract(language: str) -> dict[str, Any]:
    zh = language == "zh-CN"
    return {
        "source_owner": "public_safe_markdown_or_explicit_user_source",
        "candidate_owner": "agent_working_result",
        "projection_owner": "generated_dashboard_or_export",
        "durable_owner": "user_confirmed_personal_vault",
        "requires_human_confirmation": True,
        "writeback_route": "review",
        "summary": (
            "写进长期记忆或公开之前，要你先看过并确认；对话先给出回答、成果或写回候选，Dashboard 和导出只是展示，不算定论。"
            if zh
            else "Nothing becomes durable memory or public until you have reviewed and confirmed it. A conversation first gives an answer, an artifact or a writeback candidate; the Dashboard and exports only display, they never decide."
        ),
    }


def with_conversation_contract(task: dict[str, Any], language: str) -> dict[str, Any]:
    normalized = dict(task)
    normalized.setdefault("workspace", "agent")
    normalized.setdefault("result_modes", list(RESULT_MODES))
    normalized.setdefault("default_result_mode", "answer")
    normalized.setdefault("sensitivity_default", "local_only")
    normalized.setdefault("authority", authority_contract(language))
    normalized["primary_surface"] = "conversation"
    normalized["dashboard_role"] = "projection_and_handoff"
    return normalized
