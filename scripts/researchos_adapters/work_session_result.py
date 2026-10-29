# ResearchOS maintenance header.
# 中文：工作会话 Codex JSONL 输出解析 owner；把执行日志压缩成前端可见答案和文件锚点。
# English: Work-session Codex JSONL result parser; reduces execution logs into visible answers and file anchors.

"""Parse Codex JSONL into a small Work Session result contract."""

from __future__ import annotations

import json


MARKERS = {"CHANGED_FILES", "PREVIEW_ANCHORS", "CHANGE_SUMMARY", "EXECUTION_STATUS"}


def marker_lines(text: str, marker: str) -> list[str]:
    lines = str(text or "").splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == f"{marker}:"), -1)
    if start < 0:
        return []
    values: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.endswith(":") and stripped[:-1] in MARKERS:
            break
        if stripped.startswith("EXECUTION_STATUS:"):
            break
        value = stripped.lstrip("-* ").strip().strip("`")
        if marker in {"CHANGED_FILES", "PREVIEW_ANCHORS"} and value.lower().rstrip("。.") in {
            "none", "n/a", "无", "无改动", "未修改文件",
        }:
            continue
        if value:
            values.append(value)
    return values


def result_from_output(output: str) -> dict[str, object]:
    messages: list[str] = []
    for line in str(output or "").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        item = event.get("item", {}) if isinstance(event.get("item"), dict) else {}
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            text = str(item.get("text", "")).strip()
        elif event.get("type") == "agent_message":
            text = str(event.get("text", "")).strip()
        else:
            text = ""
        if text:
            messages.append(text)

    answer = messages[-1] if messages else ""
    changed_files = marker_lines(answer, "CHANGED_FILES")
    preview_anchors = marker_lines(answer, "PREVIEW_ANCHORS")
    change_summary = marker_lines(answer, "CHANGE_SUMMARY")
    execution_status = next((
        line.split(":", 1)[1].strip().lower()
        for line in answer.splitlines()
        if line.strip().startswith("EXECUTION_STATUS:")
    ), "")
    marker_positions = []
    for marker in MARKERS:
        position = answer.find(f"{marker}:")
        if position == 0 or (position > 0 and answer[position - 1] == "\n"):
            marker_positions.append(position)
    visible_answer = answer[: min(marker_positions)].strip() if marker_positions else answer
    if not visible_answer and change_summary:
        visible_answer = "\n".join(f"- {item}" for item in change_summary)
    return {
        "answer": visible_answer,
        "artifacts": [{"path": path, "kind": "file"} for path in changed_files],
        "changed_files": changed_files,
        "preview_anchors": preview_anchors,
        "change_summary": change_summary,
        "execution_status": execution_status,
    }
