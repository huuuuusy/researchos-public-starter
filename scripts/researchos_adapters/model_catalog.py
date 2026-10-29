# ResearchOS maintenance header.
# 中文：运行时模型目录 owner；发现当前 provider 可用模型，并解析 Auto/固定/自定义选择。
# English: Runtime model-catalog owner; discovers provider models and resolves auto, pinned, or custom selections.

"""Runtime model discovery and selection for ResearchOS."""

from __future__ import annotations

import json
import re
import shutil
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    try:
        import tomli as tomllib
    except ModuleNotFoundError:  # pragma: no cover - dependency-free Python 3.9 fallback
        tomllib = None

from researchos_adapters.command_runner import CommandRunner, codex_cli_env


CODEX_APP_CLI = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
CODEX_APP_CLI_CANDIDATES = (
    CODEX_APP_CLI,
    Path("/Applications/Codex.app/Contents/Resources/codex"),
)
MODEL_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
REASONING_EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}
TASK_COMPLEXITY_REASONING = {"economy": "low", "standard": "medium", "deep": "high"}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def clean_model_id(value: object) -> str:
    model_id = str(value or "").strip()
    return model_id if MODEL_ID_PATTERN.fullmatch(model_id) else ""


def task_complexity_fields(value: object) -> dict[str, str]:
    record = value if isinstance(value, dict) else {}
    return {
        "task_complexity": str(record.get("task_complexity", record.get("model_tier", ""))).strip()[:80],
        "task_complexity_mode": str(
            record.get("task_complexity_mode", record.get("model_tier_mode", ""))
        ).strip()[:80],
        "recommended_task_complexity": str(
            record.get("recommended_task_complexity", record.get("recommended_model_tier", ""))
        ).strip()[:80],
    }


def resolve_codex_executable(preferred_path: Path | None = None) -> Path | None:
    candidates = [preferred_path, *CODEX_APP_CLI_CANDIDATES]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    resolved = shutil.which("codex")
    return Path(resolved) if resolved else None


def configured_codex_model(config_path: Path | None = None) -> str:
    path = config_path or (Path.home() / ".codex" / "config.toml")
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    if tomllib:
        try:
            data = tomllib.loads(text)
        except (TypeError, ValueError):
            return ""
        return clean_model_id(data.get("model", "")) if isinstance(data, dict) else ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            break
        match = re.fullmatch(r'model\s*=\s*(["\'])([^"\']+)\1\s*(?:#.*)?', stripped)
        if match:
            return clean_model_id(match.group(2))
    return ""


def extract_json_object(output: object) -> dict[str, Any]:
    text = str(output or "")
    start = text.find("{")
    if start < 0:
        return {}
    try:
        value = json.loads(text[start:])
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def normalize_reasoning_levels(model: dict[str, Any]) -> list[str]:
    values = []
    for item in model.get("supported_reasoning_levels", []):
        effort = str(item.get("effort", "")).strip() if isinstance(item, dict) else ""
        if effort in REASONING_EFFORTS and effort not in values:
            values.append(effort)
    default = str(model.get("default_reasoning_level", "")).strip()
    if default in REASONING_EFFORTS and default not in values:
        values.insert(0, default)
    return values


def normalize_catalog_model(model: object) -> dict[str, object] | None:
    if not isinstance(model, dict):
        return None
    model_id = clean_model_id(model.get("slug", ""))
    if not model_id or str(model.get("visibility", "list")) == "hide":
        return None
    priority = model.get("priority")
    return {
        "id": model_id,
        "label": str(model.get("display_name") or model_id).strip()[:160],
        "description": str(model.get("description", "")).strip()[:600],
        "default_reasoning_effort": str(model.get("default_reasoning_level", "")).strip(),
        "reasoning_efforts": normalize_reasoning_levels(model),
        "priority": int(priority) if isinstance(priority, int) else 9999,
        "source": "runtime",
        "available": True,
        "supported_in_api": bool(model.get("supported_in_api")),
    }


def resolve_model_config(
    requested_model: object,
    requested_reasoning: object,
    recommended_complexity: object,
    catalog: dict[str, object],
) -> dict[str, str]:
    selected = clean_model_id(requested_model)
    if selected == "auto":
        selected = ""
    auto_model = clean_model_id(catalog.get("recommended_model", "")) or clean_model_id(catalog.get("configured_default_model", ""))
    model = selected or auto_model or "auto"
    task_complexity = str(recommended_complexity or "standard").strip()
    if task_complexity not in TASK_COMPLEXITY_REASONING:
        task_complexity = "standard"
    reasoning = str(requested_reasoning or "auto").strip()
    if reasoning not in REASONING_EFFORTS:
        reasoning = TASK_COMPLEXITY_REASONING[task_complexity]
    return {
        "task_complexity": task_complexity,
        "model": model,
        "model_mode": "manual_override" if selected else "auto_catalog",
        "reasoning_effort": reasoning,
    }


@dataclass
class ModelCatalog:
    root: Path
    command_runner: CommandRunner
    codex_path: Path = CODEX_APP_CLI
    cache_seconds: int = 300
    _cached: dict[str, object] | None = field(default=None, init=False, repr=False)
    _cached_at: float = field(default=0.0, init=False, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    def codex_executable(self) -> Path | None:
        return resolve_codex_executable(self.codex_path)

    def public_status(self) -> dict[str, object]:
        return {
            "ok": False,
            "provider": "codex",
            "discovery": "public_copy_only",
            "recommended_model": "",
            "configured_default_model": "",
            "models": [],
            "refreshed_at": now_iso(),
            "runtime_scope": "public_copy_only",
        }

    def status(self, *, public_starter: bool = False, refresh: bool = False) -> dict[str, object]:
        if public_starter:
            return self.public_status()
        with self._lock:
            fresh = self._cached and (time.monotonic() - self._cached_at) < self.cache_seconds
            if fresh and not refresh:
                return dict(self._cached or {})
            payload = self._discover_codex()
            self._cached = payload
            self._cached_at = time.monotonic()
            return dict(payload)

    def _discover_codex(self, *, allow_user_config: bool = True) -> dict[str, object]:
        executable = self.codex_executable()
        configured = configured_codex_model() if allow_user_config else ""
        if not executable:
            return {
                "ok": False,
                "provider": "codex",
                "discovery": "codex_cli_missing",
                "recommended_model": configured or "auto",
                "configured_default_model": configured,
                "models": [],
                "refreshed_at": now_iso(),
            }
        result = self.command_runner.run(
            [str(executable), "debug", "models"],
            timeout=30,
            input_text=None,
            env=codex_cli_env(),
        )
        raw = extract_json_object(result.get("stdout", ""))
        models = [normalize_catalog_model(item) for item in raw.get("models", [])]
        models = sorted((item for item in models if item), key=lambda item: (int(item["priority"]), str(item["label"])))
        recommended = str(models[0]["id"]) if models else configured or "auto"
        return {
            "ok": bool(result.get("ok") and models),
            "provider": "codex",
            "discovery": "codex_debug_models" if models else "codex_catalog_unavailable",
            "recommended_model": recommended,
            "configured_default_model": configured,
            "models": models,
            "refreshed_at": now_iso(),
        }
