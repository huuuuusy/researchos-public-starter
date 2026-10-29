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
            "长期记忆或公开内容写回前必须进入 Review；对话先形成回答、成果或写回候选，公开 Dashboard/导出只是投影，不是 authority。"
            if zh
            else "Use Review before durable writeback. Conversation produces an answer, artifact, or writeback candidate first; the public Dashboard/export is a projection, never authority, and durable writeback enters the user's vault only after confirmation."
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
