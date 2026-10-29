# ResearchOS maintenance header.
# 中文：声明式任务扩展加载器；让普通 DIY 通过配置接入现有任务/结果/确认链，而不修改 dashboard 编排内核。
# English: Declarative task-extension loader; connects DIY routes to the existing task/result/confirmation chain without dashboard-core edits.

"""Load and validate versioned ResearchOS task extension descriptors."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from researchos_data.conversation_contract import authority_contract, with_conversation_contract
from researchos_data.plugin_docs import validate_documentation
from researchos_data.plugin_governance import validate_governance


SCHEMA_ID = "researchos-task-extension-v1"
CORE_API_VERSION = "1"
RUNTIME_SCOPES = frozenset({"private", "public_starter", "personal_vault"})
WORKSPACES = frozenset({"agent", "assets", "inbox"})
RESULT_MODES = frozenset({"answer", "artifact", "writeback"})
SENSITIVITY_VALUES = frozenset({"public", "public_safe", "internal", "private", "local_only", "not_exportable"})
PUBLIC_SAFE_DEFAULTS = frozenset({"public", "public_safe", "local_only"})
PUBLIC_READ_SOURCE_SENSITIVITY = frozenset({"public", "public_safe"})
LANGUAGES = ("en", "zh-CN")
TIER_LIMITS = {"quick": 1, "standard": 5, "evidence": 8}
TOKEN_CEILINGS = {"quick": 10_000, "standard": 35_000, "evidence": 60_000}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


class TaskExtensionError(ValueError):
    """Raised when an extension descriptor violates the stable core contract."""


def _fail(source: Path, message: str) -> TaskExtensionError:
    return TaskExtensionError(f"{source}: {message}")


def _string(value: Any) -> str:
    return str(value or "").strip()


def _string_list(value: Any, source: Path, field: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise _fail(source, f"{field} must be a non-empty string list")
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        raise _fail(source, f"{field} must not contain duplicate values")
    return normalized


def _relative_read_path(value: str, root: Path, source: Path, field: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise _fail(source, f"{field} must stay inside the repository: {value}")
    candidate = root / path
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except FileNotFoundError:
        raise _fail(source, f"{field} does not exist: {value}")
    except (OSError, RuntimeError, ValueError):
        raise _fail(source, f"{field} must stay inside the repository after resolving links: {value}")
    if not resolved.is_file():
        raise _fail(source, f"{field} must point to a file: {value}")
    return path.as_posix()


def _frontmatter_sensitivity(path: Path) -> str:
    if path.suffix.lower() != ".md":
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        return ""
    block = text.split("\n---\n", 1)[0].removeprefix("---\n")
    match = re.search(r'^sensitivity:\s*["\']?([^\n"\']+)', block, flags=re.MULTILINE)
    return _string(match.group(1)).lower() if match else ""


def _normalize_read_tiers(read: Any, *, root: Path, source: Path, field: str) -> dict[str, list[str]]:
    if not isinstance(read, dict):
        raise _fail(source, f"{field} must define quick, standard, and evidence tiers")
    normalized_read: dict[str, list[str]] = {}
    previous: list[str] = []
    for tier, limit in TIER_LIMITS.items():
        tier_field = f"{field}.{tier}"
        tier_paths = _string_list(read.get(tier), source, tier_field)
        if len(tier_paths) > limit:
            raise _fail(source, f"{tier_field} exceeds the {limit}-file core limit")
        normalized = [_relative_read_path(value, root, source, tier_field) for value in tier_paths]
        if previous and not set(previous).issubset(normalized):
            raise _fail(source, f"{tier_field} must retain the preceding tier")
        normalized_read[tier] = normalized
        previous = normalized
    return normalized_read


def descriptor_paths(root: Path, *, include_examples: bool = False) -> list[Path]:
    paths: list[Path] = []
    for directory in (root / "config" / "extensions", root / "config" / "extensions.local"):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json")):
            if not include_examples and path.name.endswith(".example.json"):
                continue
            paths.append(path)
    return paths


def _descriptor_data(root: Path, source: Path) -> Any:
    try:
        resolved = source.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except FileNotFoundError:
        raise _fail(source, "descriptor file does not exist")
    except (OSError, RuntimeError, ValueError):
        raise _fail(source, "descriptor must stay inside the repository after resolving links")
    if not resolved.is_file():
        raise _fail(source, "descriptor must be a file")
    return json.loads(resolved.read_text(encoding="utf-8"))


def validate_descriptor(
    data: Any, *, root: Path, source: Path, require_documentation: bool = False
) -> dict[str, Any]:
    try:
        source.resolve(strict=True).relative_to(root.resolve(strict=True))
    except FileNotFoundError:
        raise _fail(source, "descriptor file does not exist")
    except (OSError, RuntimeError, ValueError):
        raise _fail(source, "descriptor must stay inside the repository after resolving links")
    if not isinstance(data, dict):
        raise _fail(source, "descriptor root must be an object")
    allowed_fields = {
        "schema_id", "core_api_version", "id", "version", "enabled", "available_in",
        "public_safe", "sensitivity_default", "documentation", "authority", "task", "governance",
    }
    unknown_fields = set(data) - allowed_fields
    if unknown_fields:
        raise _fail(source, f"descriptor contains unsupported fields: {sorted(unknown_fields)}")
    if data.get("schema_id") != SCHEMA_ID:
        raise _fail(source, f"schema_id must be {SCHEMA_ID}")
    if _string(data.get("core_api_version")) != CORE_API_VERSION:
        raise _fail(source, f"core_api_version must be {CORE_API_VERSION}")

    extension_id = _string(data.get("id"))
    if not ID_PATTERN.fullmatch(extension_id):
        raise _fail(source, "id must use lower_snake_case and start with a letter")
    if not VERSION_PATTERN.fullmatch(_string(data.get("version"))):
        raise _fail(source, "version must use semantic x.y.z form")
    if not isinstance(data.get("enabled"), bool):
        raise _fail(source, "enabled must be true or false")

    available_in = _string_list(data.get("available_in"), source, "available_in")
    unknown_scopes = set(available_in) - RUNTIME_SCOPES
    if unknown_scopes:
        raise _fail(source, f"available_in contains unsupported scopes: {sorted(unknown_scopes)}")

    sensitivity = _string(data.get("sensitivity_default"))
    if sensitivity not in SENSITIVITY_VALUES:
        raise _fail(source, f"unsupported sensitivity_default: {sensitivity}")
    public_safe = data.get("public_safe")
    if not isinstance(public_safe, bool):
        raise _fail(source, "public_safe must be true or false")
    if "public_starter" in available_in and (not public_safe or sensitivity not in PUBLIC_SAFE_DEFAULTS):
        raise _fail(source, "public_starter extensions must be public_safe with a public/public_safe/local_only default")

    documentation = (
        validate_documentation(
            data.get("documentation"), root=root, source=source, plugin_id=extension_id, fail=_fail
        )
        if require_documentation or data.get("documentation") is not None
        else {}
    )

    authority = data.get("authority")
    if not isinstance(authority, dict):
        raise _fail(source, "authority must be an object")
    for field in ("source", "candidate", "confirmation", "save_target"):
        if not _string(authority.get(field)):
            raise _fail(source, f"authority.{field} is required")
    if _string(authority.get("confirmation")).lower() in {"none", "false", "no"}:
        raise _fail(source, "authority.confirmation must preserve human review before durable writeback")
    if authority.get("requires_human_confirmation") is not True:
        raise _fail(source, "authority.requires_human_confirmation must be true")
    if authority.get("writeback_route") != "review":
        raise _fail(source, "authority.writeback_route must be review")
    if authority.get("storage_owner") != "researchos_core":
        raise _fail(source, "authority.storage_owner must be researchos_core")

    task = data.get("task")
    if not isinstance(task, dict):
        raise _fail(source, "task must be an object")
    workspace = _string(task.get("workspace"))
    if workspace not in WORKSPACES:
        raise _fail(source, f"task.workspace must be one of {sorted(WORKSPACES)}")
    result_modes = _string_list(task.get("result_modes"), source, "task.result_modes")
    if set(result_modes) - RESULT_MODES:
        raise _fail(source, f"task.result_modes contains unsupported modes: {sorted(set(result_modes) - RESULT_MODES)}")
    default_result_mode = _string(task.get("default_result_mode"))
    if default_result_mode not in result_modes:
        raise _fail(source, "task.default_result_mode must be listed in task.result_modes")
    if not _string(task.get("budget")):
        raise _fail(source, "task.budget is required")

    aliases = task.get("aliases", [])
    if aliases:
        aliases = _string_list(aliases, source, "task.aliases")
        if extension_id in aliases:
            raise _fail(source, "task.aliases must not repeat the extension id")

    normalized_read = _normalize_read_tiers(task.get("read"), root=root, source=source, field="task.read")
    normalized_read_locales: dict[str, dict[str, list[str]]] = {}
    read_locales = task.get("read_locales")
    if read_locales is not None:
        if not isinstance(read_locales, dict):
            raise _fail(source, "task.read_locales must contain en and zh-CN read tiers")
        for language in LANGUAGES:
            normalized_read_locales[language] = _normalize_read_tiers(
                read_locales.get(language), root=root, source=source, field=f"task.read_locales.{language}"
            )

    if "public_starter" in available_in:
        target_paths = {
            path
            for tiers in [normalized_read, *normalized_read_locales.values()]
            for paths in tiers.values()
            for path in paths
        }
        for target in sorted(target_paths):
            target_sensitivity = _frontmatter_sensitivity(root / target)
            if target_sensitivity not in PUBLIC_READ_SOURCE_SENSITIVITY:
                found = target_sensitivity or "missing"
                raise _fail(
                    source,
                    f"public_starter read target must declare public/public_safe frontmatter sensitivity: "
                    f"{target} ({found})",
                )

    locales = task.get("locales")
    if not isinstance(locales, dict):
        raise _fail(source, "task.locales must contain en and zh-CN")
    normalized_locales: dict[str, dict[str, Any]] = {}
    for language in LANGUAGES:
        locale = locales.get(language)
        if not isinstance(locale, dict):
            raise _fail(source, f"task.locales.{language} is required")
        normalized_locale: dict[str, Any] = {}
        for field in ("name", "goal", "user_input_hint", "output"):
            value = _string(locale.get(field))
            if not value:
                raise _fail(source, f"task.locales.{language}.{field} is required")
            normalized_locale[field] = value
        normalized_locale["next_steps"] = _string_list(
            locale.get("next_steps"), source, f"task.locales.{language}.next_steps"
        )
        normalized_locales[language] = normalized_locale

    normalized = dict(data)
    normalized["id"] = extension_id
    normalized["available_in"] = available_in
    normalized["sensitivity_default"] = sensitivity
    if documentation:
        normalized["documentation"] = documentation
    normalized_authority = {
        **{field: _string(authority[field]) for field in ("source", "candidate", "confirmation", "save_target")},
        "requires_human_confirmation": True,
        "writeback_route": "review",
        "storage_owner": "researchos_core",
    }
    authority_locales = authority.get("locales")
    if authority_locales is not None:
        if not isinstance(authority_locales, dict):
            raise _fail(source, "authority.locales must contain en and zh-CN")
        normalized_authority["locales"] = {}
        for language in LANGUAGES:
            locale = authority_locales.get(language)
            if not isinstance(locale, dict):
                raise _fail(source, f"authority.locales.{language} is required")
            normalized_authority["locales"][language] = {}
            for field in ("source", "candidate", "confirmation", "save_target"):
                value = _string(locale.get(field))
                if not value:
                    raise _fail(source, f"authority.locales.{language}.{field} is required")
                normalized_authority["locales"][language][field] = value
    normalized["authority"] = normalized_authority
    normalized["task"] = {
        **task,
        "aliases": aliases,
        "workspace": workspace,
        "result_modes": result_modes,
        "default_result_mode": default_result_mode,
        "read": normalized_read,
        "read_locales": normalized_read_locales,
        "locales": normalized_locales,
    }
    normalized["governance"] = validate_governance(
        data.get("governance"),
        root=root,
        source=source,
        plugin_id=extension_id,
        product_tier="optional_extension",
        enabled=data["enabled"],
        result_modes=set(result_modes),
        public_safe=public_safe,
        sensitivity_default=sensitivity,
    )
    return normalized


def _tier_labels(language: str) -> dict[str, tuple[str, str]]:
    if language == "zh-CN":
        return {
            "quick": ("最小读取", "只读一个主文件；有精确目标时直接读目标。"),
            "standard": ("平衡读取", "只在出现明确缺口后加入 workflow 或模板。"),
            "evidence": ("证据核验", "只为明确核验问题加入定向证据。"),
        }
    return {
        "quick": ("Minimal read", "Read one primary file; use an exact target directly when supplied."),
        "standard": ("Balanced read", "Add workflows or templates only after naming a gap."),
        "evidence": ("Evidence check", "Add targeted evidence only for a named verification question."),
    }


def task_from_descriptor(descriptor: dict[str, Any], language: str) -> dict[str, Any]:
    task = descriptor["task"]
    locale = task["locales"][language]
    selected_read = task.get("read_locales", {}).get(language) or task["read"]
    selected_authority = descriptor["authority"].get("locales", {}).get(language) or descriptor["authority"]
    labels = _tier_labels(language)
    read_tiers = [
        {
            "id": tier,
            "label": labels[tier][0],
            "description": labels[tier][1],
            "read": list(selected_read[tier]),
            "file_limit": TIER_LIMITS[tier],
            "token_ceiling": TOKEN_CEILINGS[tier],
            "requires_gap_reason": tier != "quick",
        }
        for tier in TIER_LIMITS
    ]
    confirmation = selected_authority["confirmation"]
    if language == "zh-CN":
        prompt = (
            f"任务：{locale['name']} ({descriptor['id']})\n"
            f"目标：{locale['goal']}\n"
            f"先读：{selected_read['quick'][0]}\n"
            f"用户需补充：{locale['user_input_hint']}\n"
            f"确认边界：{confirmation}\n"
            "先返回判断和候选结果；涉及长期记忆或公开内容时，必须进入既有 Review/确认链。"
        )
    else:
        prompt = (
            f"Task: {locale['name']} ({descriptor['id']})\n"
            f"Goal: {locale['goal']}\n"
            f"Read first: {selected_read['quick'][0]}\n"
            f"User should provide: {locale['user_input_hint']}\n"
            f"Confirmation boundary: {confirmation}\n"
            "Return judgment and candidate output first. Durable memory or public content must use the existing Review/confirmation flow."
        )
    contract = authority_contract(language)
    contract.update(
        {
            "source_owner": selected_authority["source"],
            "candidate_owner": selected_authority["candidate"],
            "durable_owner": selected_authority["save_target"],
            "summary": confirmation,
        }
    )
    return with_conversation_contract({
        "id": descriptor["id"],
        "name": locale["name"],
        "budget": _string(task["budget"]),
        "goal": locale["goal"],
        "user_input_hint": locale["user_input_hint"],
        "output": locale["output"],
        "next_steps": list(locale["next_steps"]),
        "read_first": list(selected_read["quick"]),
        "read_tiers": read_tiers,
        "agent_prompt": prompt,
        "command": f"python3 scripts/plan_context.py {descriptor['id']} --lang {language}",
        "aliases": list(task.get("aliases", [])),
        "workspace": task["workspace"],
        "result_modes": list(task["result_modes"]),
        "default_result_mode": task["default_result_mode"],
        "sensitivity_default": descriptor["sensitivity_default"],
        "authority": contract,
        "extension_id": descriptor["id"],
        "extension_version": descriptor["version"],
    }, language)


def load_task_extensions(
    root: Path,
    *,
    runtime_scope: str,
    language: str,
    base_task_ids: set[str] | None = None,
) -> dict[str, Any]:
    if runtime_scope not in RUNTIME_SCOPES:
        raise TaskExtensionError(f"unsupported runtime scope: {runtime_scope}")
    if language not in LANGUAGES:
        raise TaskExtensionError(f"unsupported extension language: {language}")
    used_ids = set(base_task_ids or set())
    tasks: list[dict[str, Any]] = []
    loaded: list[dict[str, Any]] = []
    for source in descriptor_paths(root):
        descriptor = validate_descriptor(_descriptor_data(root, source), root=root, source=source)
        if not descriptor["enabled"] or runtime_scope not in descriptor["available_in"]:
            continue
        extension_id = descriptor["id"]
        aliases = set(descriptor["task"].get("aliases", []))
        conflicts = ({extension_id} | aliases) & used_ids
        if conflicts:
            raise _fail(source, f"task id or alias conflicts with an existing route: {sorted(conflicts)}")
        used_ids.update({extension_id, *aliases})
        tasks.append(task_from_descriptor(descriptor, language))
        loaded.append(
            {
                "id": extension_id,
                "version": descriptor["version"],
                "workspace": descriptor["task"]["workspace"],
                "result_modes": list(descriptor["task"]["result_modes"]),
                "sensitivity_default": descriptor["sensitivity_default"],
                "writeback_route": descriptor["authority"]["writeback_route"],
                "storage_owner": descriptor["authority"]["storage_owner"],
                "source": source.relative_to(root).as_posix(),
            }
        )
    return {
        "api_version": CORE_API_VERSION,
        "schema_id": SCHEMA_ID,
        "runtime_scope": runtime_scope,
        "active_language": language,
        "loaded": loaded,
        "tasks": tasks,
    }


def validate_extension_files(root: Path) -> list[str]:
    failures: list[str] = []
    seen_routes: dict[str, Path] = {}
    for source in descriptor_paths(root, include_examples=True):
        try:
            descriptor = validate_descriptor(_descriptor_data(root, source), root=root, source=source)
            if not source.name.endswith(".example.json"):
                for route_id in [descriptor["id"], *descriptor["task"].get("aliases", [])]:
                    if route_id in seen_routes:
                        failures.append(f"{source}: route {route_id} already belongs to {seen_routes[route_id]}")
                    else:
                        seen_routes[route_id] = source
        except (json.JSONDecodeError, OSError, TaskExtensionError) as error:
            failures.append(str(error))
    return failures
