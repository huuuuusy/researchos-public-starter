# ResearchOS maintenance header.
# English: Loads runtime provider configuration and keeps public execution local, read-only, and credential-free.
"""Runtime configuration loader for ResearchOS provider adapters."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from .provider_registry import get_provider_spec
from .runtime_profile import (
    RuntimeProfileError, normalize_runtime_profile_projection, project_selected_runtime_profile,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_CONFIG = REPO_ROOT / "config" / "researchos.runtime.example.json"
LOCAL_CONFIG = REPO_ROOT / "config" / "researchos.runtime.local.json"


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_runtime_config(include_local: bool = True) -> Dict[str, Any]:
    config = _read_json(EXAMPLE_CONFIG)
    if include_local and LOCAL_CONFIG.exists():
        config = _deep_merge(config, _read_json(LOCAL_CONFIG))
    return config


def provider_status(provider_name: str | None = None, public_starter: bool = False) -> Dict[str, Any]:
    config = load_runtime_config(include_local=not public_starter)
    selected = provider_name or config.get("default_provider", "codex")
    if public_starter:
        return {
            "ok": False,
            "error_type": "public_starter_copy_only",
            "provider": selected,
            "message_zh": "公开演示版只生成可复制任务包，不启动本机 Codex，也不调用远程 API。",
            "message_en": "The public starter produces copyable task packets only; it does not launch local Codex or remote APIs.",
            "public_starter_api": "copy_only",
            "execution_scope": "none",
        }

    try:
        spec = get_provider_spec(selected)
    except KeyError:
        return {
            "ok": False,
            "error_type": "unknown_provider",
            "provider": selected,
            "message_zh": f"provider `{selected}` 未在 ResearchOS registry 中登记。",
            "message_en": f"Provider `{selected}` is not registered in ResearchOS.",
            "public_starter_api": "disabled",
            "execution_available": False,
            "execution_scope": "none",
        }
    provider_config = config.get("providers", {}).get(selected, {})
    return {
        "ok": True,
        "provider": selected,
        "type": provider_config.get("type") or spec.type,
        "model": provider_config.get("default_model") or spec.default_model,
        "key_status": "not_required",  # no provider takes an API key; the frozen Dashboard panel still shows this field
        "runtime_mode": "private vault",
        "public_starter_api": "disabled",
        "execution_scope": "workspace_write",
    }


def provider_execution_status(
    provider_name: str = "codex", *, public_starter: bool = False, executable_available: bool = False,
    runtime_scope: str | None = None,
) -> Dict[str, Any]:
    """Combine provider permission with the local CLI availability probe of a registered provider."""
    status = provider_status(provider_name, public_starter=public_starter)
    if not status.get("ok"):
        result = {**status, "execution_available": False}
    elif not executable_available:
        spec = get_provider_spec(status["provider"])
        result = {
            **status,
            "ok": False,
            "execution_available": False,
            "error_type": spec.cli_missing_error,
            "message_en": f"The local {spec.label} CLI is unavailable; copy the task instead.",
            "message_zh": f"本机 {spec.label} CLI 不可用；请改用复制交接。",
        }
    else:
        result = {**status, "execution_available": True}
    selected_scope = runtime_scope or ("public_starter" if public_starter else "private")
    result["runtime_profile"] = project_selected_runtime_profile(
        load_runtime_config(include_local=selected_scope != "public_starter"), runtime_scope=selected_scope,
        execution_available=bool(result["execution_available"]) if provider_name == "codex" else None,
    )
    return result


def enforce_runtime_submission_boundary(
    payload: Dict[str, Any], *, public_starter: bool = False
) -> tuple[Dict[str, Any], Dict[str, Any] | None]:
    """Reject every public execution request; the public UI exports task packets only."""
    if not public_starter:
        return payload, None
    return payload, {
        "ok": False,
        "error_type": "public_starter_copy_only",
        "message_en": "The public starter does not execute tasks. Copy the generated task packet into a private agent task (Claude Code, Codex or another file-aware client).",
        "message_zh": "公开版不执行任务；请把生成的任务包复制到你自己的 Agent 客户端（Claude Code、Codex 等）任务中。",
    }


def public_provider_status(status: object, *, public_starter: bool = True) -> Dict[str, Any]:
    """Expose provider/runtime capability without leaking local configuration details."""
    if not isinstance(status, dict):
        return {}
    allowed = {
        "ok", "provider", "selected_adapter", "adapter_family", "type", "model", "runtime_mode", "cancel",
        "public_starter_api", "execution_available", "execution_scope", "error_type",
        "message_zh", "message_en",
    }
    if not public_starter:
        allowed.add("key_status")
    projection = {key: value for key, value in status.items() if key in allowed}
    try:
        projection["runtime_profile"] = normalize_runtime_profile_projection(status.get("runtime_profile"))
    except RuntimeProfileError:
        pass
    return projection


def sanitize_public_runtime_output(output: object, root: Path) -> str:
    """Remove workstation-specific path prefixes from public results and logs."""
    text = str(output or "")
    root_prefix = str(root.resolve())
    if root_prefix:
        text = text.replace(root_prefix, ".")
    home_prefix = str(Path.home())
    if home_prefix:
        text = text.replace(home_prefix, "~")
    text = re.sub(r"(?<![\w:])/(?:Users|home)/[^\s<>\"'`]+", "~", text)
    text = re.sub(r"(?<![\w:])/(?:private/var|var/folders|tmp)/[^\s<>\"'`]+", "[local path]", text)
    text = re.sub(r"(?<![A-Za-z0-9])[A-Za-z]:\\\\[^\s<>\"'`]+", "[local path]", text)
    return text


def sanitize_public_runtime_value(value: object, root: Path) -> object:
    """Apply the same workstation-path scrubber to every public text value."""
    if isinstance(value, str):
        return sanitize_public_runtime_output(value, root)
    if isinstance(value, list):
        return [sanitize_public_runtime_value(item, root) for item in value]
    if isinstance(value, tuple):
        return [sanitize_public_runtime_value(item, root) for item in value]
    if isinstance(value, dict):
        return {str(key): sanitize_public_runtime_value(item, root) for key, item in value.items()}
    return value


PUBLIC_RUN_KEYS = {
    "id", "status", "task_mode", "response_mode", "work_session_id", "title",
    "created_at", "updated_at", "started_at", "finished_at", "returncode", "seconds",
    "message", "usage", "task_complexity", "task_complexity_mode", "recommended_task_complexity",
    "model", "model_mode", "provider", "provider_status", "reasoning_effort",
    "reasoning_effort_mode", "recommended_reasoning_effort", "answer", "execution_status",
    "post_run_refresh",
}


def project_public_runtime_run(projection: Dict[str, Any], root: Path) -> Dict[str, Any]:
    """Return the public runner allowlist with every visible text value scrubbed."""
    return sanitize_public_runtime_value(
        {key: value for key, value in projection.items() if key in PUBLIC_RUN_KEYS}, root
    )
