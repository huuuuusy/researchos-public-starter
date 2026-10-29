# ResearchOS maintenance header.
# 中文：ResearchOS 插件宿主合同；验证、规范化并汇总 manifest，同时把 task-extension v1 作为兼容输入。
# English: ResearchOS plugin-host contract; validates, normalizes, and summarizes manifests while adapting task-extension v1 inputs.

"""Fail-closed ResearchOS plugin manifest loader and compatibility registry."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from researchos_data.plugin_governance import EFFECTS, validate_governance
from researchos_data.plugin_docs import validate_documentation
from researchos_data.task_extensions import (
    LANGUAGES,
    PUBLIC_READ_SOURCE_SENSITIVITY,
    PUBLIC_SAFE_DEFAULTS,
    RUNTIME_SCOPES,
    SENSITIVITY_VALUES,
    _frontmatter_sensitivity,
    descriptor_paths as task_extension_paths,
    task_from_descriptor,
    validate_descriptor as validate_task_extension_descriptor,
)


SCHEMA_ID = "researchos-plugin-v1"
CORE_API_VERSION = "1"
EXECUTION_PROFILES = frozenset({"declarative", "trusted_local", "external_bridge"})
PRODUCT_TIER_VALUES = frozenset({"foundation_projection", "bundled_capability", "optional_extension"})
STATE_ACCESS_VALUES = frozenset({"none", "namespaced_local"})
CONTRIBUTION_TYPES = (
    "tasks",
    "actions",
    "candidate_types",
    "asset_types",
    "source_adapters",
    "previewers",
    "projections",
    "work_item_providers",
    "ui_slots",
)
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
DOMAIN_PATTERN = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
PROJECTION_SOURCE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
PROJECTION_FIELD_PATTERN = re.compile(r"^(?:\$|[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*)$")
PUBLIC_FORBIDDEN_VALIDATION_MARKERS = ("/Users/", "/home/", "~/", "../", "private")
ACTION_EXECUTION_VALUES = frozenset({"client", "platform_registered", "review"})
ACTION_CONFIRMATION_VALUES = frozenset({"inline", "review"})
ACTION_RISK_VALUES = frozenset({"low", "medium", "high"})
ACTION_WRITE_SCOPE_VALUES = frozenset({"none", "session_state", "attention_state", "lifecycle_state", "durable_content"})
INLINE_ACTION_WRITE_SCOPE_VALUES = frozenset({"session_state", "attention_state", "lifecycle_state"})
PUBLIC_BEHAVIOR_VALUES = frozenset({"enabled", "demo_only", "disabled"})
UI_SLOT_VALUES = frozenset({"utility", "review", "workbench", "library"})
CANONICAL_SURFACE_VALUES = frozenset({"start", "library", "overlay"})
PROJECTION_FRESHNESS_VALUES = frozenset({"snapshot", "live"})
LEGACY_SLOT_COORDINATES = {
    "workbench": ("start", "primary"),
    "library": ("library", "context"),
    "review": ("overlay", "governance"),
    "utility": ("overlay", "utility"),
}
EXECUTION_BOUNDARY_CONTRACTS = {
    "declarative": (),
    "trusted_local": (
        "platform_registered_action", "researchos-policy-decision-v1", "researchos-authorization-grant-v1",
    ),
    "external_bridge": (
        "platform_registered_action", "researchos-policy-decision-v1", "researchos-authorization-grant-v1",
    ),
}


class PluginManifestError(ValueError):
    """Raised when a plugin manifest violates the stable host contract."""


def _fail(source: Path, message: str) -> PluginManifestError:
    return PluginManifestError(f"{source}: {message}")


def _string(value: Any) -> str:
    return str(value or "").strip()


def _string_list(value: Any, source: Path, field: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise _fail(source, f"{field} must be a{' non-empty' if not allow_empty else ''} string list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise _fail(source, f"{field} must contain only non-empty strings")
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        raise _fail(source, f"{field} must not contain duplicate values")
    return normalized


def _safe_source_data(root: Path, source: Path) -> Any:
    try:
        resolved = source.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except FileNotFoundError:
        raise _fail(source, "manifest file does not exist")
    except (OSError, RuntimeError, ValueError):
        raise _fail(source, "manifest must stay inside the repository after resolving links")
    if not resolved.is_file():
        raise _fail(source, "manifest must be a file")
    return json.loads(resolved.read_text(encoding="utf-8"))


def _read_path(value: str, *, root: Path, source: Path, public_scope: bool) -> str:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise _fail(source, f"permissions.read_paths must stay inside the repository: {value}")
    try:
        resolved = (root / relative).resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except FileNotFoundError:
        raise _fail(source, f"permissions.read_paths target does not exist: {value}")
    except (OSError, RuntimeError, ValueError):
        raise _fail(source, f"permissions.read_paths must stay inside the repository after resolving links: {value}")
    if not resolved.is_file():
        raise _fail(source, f"permissions.read_paths must point to a file: {value}")
    if public_scope:
        sensitivity = _frontmatter_sensitivity(resolved)
        if sensitivity not in PUBLIC_READ_SOURCE_SENSITIVITY:
            found = sensitivity or "missing"
            raise _fail(
                source,
                f"public_starter read target must declare public/public_safe frontmatter sensitivity: {value} ({found})",
            )
    return relative.as_posix()


def plugin_manifest_paths(root: Path, *, include_examples: bool = False) -> list[Path]:
    """Return reviewed and ignored-local manifest paths in deterministic order."""
    paths: list[Path] = []
    for directory in (root / "config" / "plugins", root / "config" / "plugins.local"):
        if not directory.exists():
            continue
        for source in sorted(directory.glob("*.json")):
            if not include_examples and source.name.endswith(".example.json"):
                continue
            paths.append(source)
    return paths


def _authority(data: Any, source: Path) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise _fail(source, "authority must be an object")
    allowed_fields = {
        "source",
        "candidate",
        "confirmation",
        "save_target",
        "requires_human_confirmation",
        "writeback_route",
        "storage_owner",
        "locales",
    }
    unknown_fields = set(data) - allowed_fields
    if unknown_fields:
        raise _fail(source, f"authority contains unsupported fields: {sorted(unknown_fields)}")
    required_copy = ("source", "candidate", "confirmation", "save_target")
    normalized = {field: _string(data.get(field)) for field in required_copy}
    for field, value in normalized.items():
        if not value:
            raise _fail(source, f"authority.{field} is required")
    if _string(data.get("confirmation")).lower() in {"none", "false", "no"}:
        raise _fail(source, "authority.confirmation must preserve human review")
    if data.get("requires_human_confirmation") is not True:
        raise _fail(source, "authority.requires_human_confirmation must be true")
    if data.get("writeback_route") != "review":
        raise _fail(source, "authority.writeback_route must be review")
    if data.get("storage_owner") != "researchos_core":
        raise _fail(source, "authority.storage_owner must be researchos_core")
    locales = _localized_copy(
        data.get("locales"),
        source,
        "authority.locales",
        required_copy,
        allow_missing=True,
    )
    return {
        **normalized,
        **({"locales": locales} if locales else {}),
        "requires_human_confirmation": True,
        "writeback_route": "review",
        "storage_owner": "researchos_core",
    }


def _localized_copy(
    value: Any,
    source: Path,
    field: str,
    required_fields: tuple[str, ...],
    *,
    allow_missing: bool = False,
) -> dict[str, dict[str, str]]:
    if value is None and allow_missing:
        return {}
    if not isinstance(value, dict) or set(value) != set(LANGUAGES):
        raise _fail(source, f"{field} must define exactly en and zh-CN")
    normalized: dict[str, dict[str, str]] = {}
    for language in LANGUAGES:
        locale = value.get(language)
        if not isinstance(locale, dict) or set(locale) != set(required_fields):
            raise _fail(source, f"{field}.{language} must define exactly {list(required_fields)}")
        normalized[language] = {}
        for copy_field in required_fields:
            text = _string(locale.get(copy_field))
            if not text:
                raise _fail(source, f"{field}.{language}.{copy_field} is required")
            normalized[language][copy_field] = text
    return normalized


def _permissions(
    data: Any,
    *,
    root: Path,
    source: Path,
    public_scope: bool,
    execution_profile: str,
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise _fail(source, "permissions must be an object")
    allowed_fields = {"read_paths", "network_domains", "command_ids", "state_access", "canonical_write"}
    unknown_fields = set(data) - allowed_fields
    if unknown_fields:
        raise _fail(source, f"permissions contains unsupported fields: {sorted(unknown_fields)}")
    read_paths = [
        _read_path(value, root=root, source=source, public_scope=public_scope)
        for value in _string_list(data.get("read_paths"), source, "permissions.read_paths")
    ]
    network_domains = [value.lower() for value in _string_list(data.get("network_domains"), source, "permissions.network_domains")]
    invalid_domains = [value for value in network_domains if not DOMAIN_PATTERN.fullmatch(value)]
    if invalid_domains:
        raise _fail(source, f"permissions.network_domains contains invalid hostnames: {invalid_domains}")
    command_ids = _string_list(data.get("command_ids"), source, "permissions.command_ids")
    invalid_commands = [value for value in command_ids if not ID_PATTERN.fullmatch(value)]
    if invalid_commands:
        raise _fail(source, f"permissions.command_ids must use registered lower_snake_case ids: {invalid_commands}")
    state_access = _string(data.get("state_access"))
    if state_access not in STATE_ACCESS_VALUES:
        raise _fail(source, f"permissions.state_access must be one of {sorted(STATE_ACCESS_VALUES)}")
    if data.get("canonical_write") is not False:
        raise _fail(source, "permissions.canonical_write must be false; durable writes use Review")
    if execution_profile == "declarative" and (network_domains or command_ids):
        raise _fail(source, "declarative plugins cannot request network or command permissions")
    if execution_profile == "trusted_local" and (network_domains or not command_ids):
        raise _fail(source, "trusted_local plugins require command_ids and cannot request network domains")
    if execution_profile == "external_bridge" and (not network_domains or command_ids):
        raise _fail(source, "external_bridge plugins require network_domains and cannot request command ids")
    if public_scope and (network_domains or command_ids or execution_profile != "declarative"):
        raise _fail(source, "public_starter plugins must be declarative and cannot request network or command permissions")
    return {
        "read_paths": read_paths,
        "network_domains": network_domains,
        "command_ids": command_ids,
        "state_access": state_access,
        "canonical_write": False,
    }


def _contribution_items(value: Any, source: Path, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise _fail(source, f"contributions.{field} must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            raise _fail(source, f"contributions.{field} entries must be objects")
        contribution_id = _string(item.get("id"))
        if not ID_PATTERN.fullmatch(contribution_id):
            raise _fail(source, f"contributions.{field}.id must use lower_snake_case")
        if contribution_id in seen:
            raise _fail(source, f"contributions.{field} repeats id: {contribution_id}")
        seen.add(contribution_id)
        if field == "tasks":
            allowed = {"id", "task"}
            if set(item) - allowed:
                raise _fail(source, f"contributions.tasks contains unsupported fields: {sorted(set(item) - allowed)}")
            normalized.append({**item, "id": contribution_id})
            continue
        if field == "actions":
            allowed = {
                "id", "handler", "surface", "execution", "confirmation_mode", "risk",
                "write_scope", "reversible", "public_behavior", "effect",
            }
            unknown = set(item) - allowed
            if unknown:
                raise _fail(source, f"contributions.actions contains unsupported fields: {sorted(unknown)}")
            handler = _string(item.get("handler"))
            surface = _string(item.get("surface"))
            execution = _string(item.get("execution"))
            if not ID_PATTERN.fullmatch(handler):
                raise _fail(source, "contributions.actions.handler must use lower_snake_case")
            if surface in UI_SLOT_VALUES:
                surface = LEGACY_SLOT_COORDINATES[surface][0]
            if surface not in CANONICAL_SURFACE_VALUES:
                raise _fail(source, f"contributions.actions.surface must be one of {sorted(CANONICAL_SURFACE_VALUES | UI_SLOT_VALUES)}")
            if execution not in ACTION_EXECUTION_VALUES:
                raise _fail(source, f"contributions.actions.execution must be one of {sorted(ACTION_EXECUTION_VALUES)}")
            normalized_action = {"id": contribution_id, "handler": handler, "surface": surface, "execution": execution}
            if "effect" in item:
                effect = _string(item.get("effect"))
                if effect not in EFFECTS:
                    raise _fail(source, f"contributions.actions.effect must be one of {sorted(EFFECTS)}")
                normalized_action["effect"] = effect
            optional_contract = {
                "confirmation_mode": ACTION_CONFIRMATION_VALUES,
                "risk": ACTION_RISK_VALUES,
                "write_scope": ACTION_WRITE_SCOPE_VALUES,
                "public_behavior": PUBLIC_BEHAVIOR_VALUES,
            }
            for name, values in optional_contract.items():
                if name not in item:
                    continue
                normalized_value = _string(item.get(name))
                if normalized_value not in values:
                    raise _fail(source, f"contributions.actions.{name} must be one of {sorted(values)}")
                normalized_action[name] = normalized_value
            if "reversible" in item:
                if not isinstance(item.get("reversible"), bool):
                    raise _fail(source, "contributions.actions.reversible must be true or false")
                normalized_action["reversible"] = item["reversible"]
            contract_fields = {"confirmation_mode", "risk", "write_scope", "reversible", "public_behavior"}
            declared_contract = contract_fields.intersection(item)
            if declared_contract and declared_contract != contract_fields:
                missing = sorted(contract_fields - declared_contract)
                raise _fail(source, f"contributions.actions v1.2 contract is incomplete; missing {missing}")
            if normalized_action.get("confirmation_mode") == "inline":
                if execution != "platform_registered":
                    raise _fail(source, "inline write actions must use platform_registered execution")
                if normalized_action.get("write_scope") not in INLINE_ACTION_WRITE_SCOPE_VALUES:
                    raise _fail(
                        source,
                        "inline write actions must use a bounded state scope: "
                        f"{sorted(INLINE_ACTION_WRITE_SCOPE_VALUES)}",
                    )
                if normalized_action.get("reversible") is not True:
                    raise _fail(source, "inline write actions must be reversible")
                if normalized_action.get("public_behavior") == "enabled":
                    raise _fail(source, "inline write actions cannot be enabled in public runtime")
            normalized.append(normalized_action)
            continue
        if field == "projections":
            allowed = {"id", "source", "optional", "schema_id", "version", "sensitivity", "freshness", "export_fields"}
            unknown = set(item) - allowed
            if unknown:
                raise _fail(source, f"contributions.projections contains unsupported fields: {sorted(unknown)}")
            projection_source = _string(item.get("source"))
            if not PROJECTION_SOURCE_PATTERN.fullmatch(projection_source):
                raise _fail(source, "contributions.projections.source must be a safe dotted data path")
            optional = item.get("optional", False)
            if not isinstance(optional, bool):
                raise _fail(source, "contributions.projections.optional must be true or false")
            schema_id = _string(item.get("schema_id") or "researchos-projection-envelope-v1")
            version = _string(item.get("version") or "1")
            sensitivity = _string(item.get("sensitivity") or "local_only")
            freshness = _string(item.get("freshness") or "snapshot")
            export_fields = _string_list(item.get("export_fields", ["$"]), source, "contributions.projections.export_fields", allow_empty=False)
            if schema_id != "researchos-projection-envelope-v1" or version != "1":
                raise _fail(source, "contributions.projections must use researchos-projection-envelope-v1 version 1")
            if sensitivity not in SENSITIVITY_VALUES:
                raise _fail(source, f"contributions.projections.sensitivity must be one of {sorted(SENSITIVITY_VALUES)}")
            if freshness not in PROJECTION_FRESHNESS_VALUES:
                raise _fail(source, f"contributions.projections.freshness must be one of {sorted(PROJECTION_FRESHNESS_VALUES)}")
            if any(not PROJECTION_FIELD_PATTERN.fullmatch(value) for value in export_fields) or ("$" in export_fields and len(export_fields) != 1):
                raise _fail(source, "contributions.projections.export_fields must be safe dotted fields, or one exact '$' source export")
            normalized.append({
                "id": contribution_id,
                "source": projection_source,
                "optional": optional,
                "schema_id": schema_id,
                "version": version,
                "sensitivity": sensitivity,
                "freshness": freshness,
                "export_fields": export_fields,
            })
            continue
        if field == "work_item_providers":
            allowed = {"id", "projection_id", "adapter", "optional", "public_behavior"}
            unknown = set(item) - allowed
            if unknown:
                raise _fail(source, f"contributions.work_item_providers contains unsupported fields: {sorted(unknown)}")
            projection_id = _string(item.get("projection_id"))
            adapter = _string(item.get("adapter"))
            optional = item.get("optional")
            public_behavior = _string(item.get("public_behavior"))
            if not ID_PATTERN.fullmatch(projection_id) or not ID_PATTERN.fullmatch(adapter):
                raise _fail(source, "work_item provider projection_id and adapter must use lower_snake_case")
            if not isinstance(optional, bool):
                raise _fail(source, "work_item provider optional must be true or false")
            if public_behavior not in PUBLIC_BEHAVIOR_VALUES:
                raise _fail(source, f"work_item provider public_behavior must be one of {sorted(PUBLIC_BEHAVIOR_VALUES)}")
            normalized.append({
                "id": contribution_id,
                "projection_id": projection_id,
                "adapter": adapter,
                "optional": optional,
                "public_behavior": public_behavior,
            })
            continue
        if field == "ui_slots":
            allowed = {"id", "slot", "surface", "region", "adapter", "order", "projection_ids", "action_ids", "locales"}
            unknown = set(item) - allowed
            if unknown:
                raise _fail(source, f"contributions.ui_slots contains unsupported fields: {sorted(unknown)}")
            slot = _string(item.get("slot"))
            derived_surface, derived_region = LEGACY_SLOT_COORDINATES.get(slot, ("", ""))
            surface = _string(item.get("surface") or derived_surface)
            region = _string(item.get("region") or derived_region)
            adapter = _string(item.get("adapter"))
            order = item.get("order")
            if slot not in UI_SLOT_VALUES:
                raise _fail(source, f"contributions.ui_slots.slot must be one of {sorted(UI_SLOT_VALUES)}")
            if surface != derived_surface or region != derived_region:
                raise _fail(source, f"contributions.ui_slots {slot} must map to canonical coordinate {derived_surface}.{derived_region}")
            if not ID_PATTERN.fullmatch(adapter):
                raise _fail(source, "contributions.ui_slots.adapter must use lower_snake_case")
            if not isinstance(order, int) or isinstance(order, bool) or not 0 <= order <= 1000:
                raise _fail(source, "contributions.ui_slots.order must be an integer from 0 to 1000")
            projection_ids = _string_list(item.get("projection_ids"), source, "contributions.ui_slots.projection_ids")
            action_ids = _string_list(item.get("action_ids"), source, "contributions.ui_slots.action_ids")
            invalid_refs = [value for value in [*projection_ids, *action_ids] if not ID_PATTERN.fullmatch(value)]
            if invalid_refs:
                raise _fail(source, f"contributions.ui_slots references must use lower_snake_case: {invalid_refs}")
            locales = _localized_copy(item.get("locales"), source, "contributions.ui_slots.locales", ("title", "hint"))
            normalized.append({
                "id": contribution_id,
                "slot": slot,
                "surface": surface,
                "region": region,
                "adapter": adapter,
                "order": order,
                "projection_ids": projection_ids,
                "action_ids": action_ids,
                "locales": locales,
            })
            continue
        unknown = set(item) - {"id"}
        if unknown:
            raise _fail(source, f"contributions.{field} contains unsupported fields: {sorted(unknown)}")
        normalized.append({"id": contribution_id})
    return normalized


def validate_plugin_manifest(
    data: Any, *, root: Path, source: Path, require_documentation: bool = False
) -> dict[str, Any]:
    """Validate and normalize one native plugin manifest."""
    try:
        source.resolve(strict=True).relative_to(root.resolve(strict=True))
    except FileNotFoundError:
        raise _fail(source, "manifest file does not exist")
    except (OSError, RuntimeError, ValueError):
        raise _fail(source, "manifest must stay inside the repository after resolving links")
    if not isinstance(data, dict):
        raise _fail(source, "manifest root must be an object")
    allowed_fields = {
        "schema_id",
        "core_api_version",
        "id",
        "version",
        "enabled",
        "available_in",
        "execution_profile",
        "product_tier",
        "public_safe",
        "sensitivity_default",
        "documentation",
        "authority",
        "permissions",
        "contributions",
        "state_namespace",
        "lifecycle",
        "validation",
        "governance",
    }
    unknown_fields = set(data) - allowed_fields
    if unknown_fields:
        raise _fail(source, f"manifest contains unsupported fields: {sorted(unknown_fields)}")
    if data.get("schema_id") != SCHEMA_ID:
        raise _fail(source, f"schema_id must be {SCHEMA_ID}")
    if _string(data.get("core_api_version")) != CORE_API_VERSION:
        raise _fail(source, f"unknown core_api_version: {_string(data.get('core_api_version')) or 'missing'}")

    plugin_id = _string(data.get("id"))
    if not ID_PATTERN.fullmatch(plugin_id):
        raise _fail(source, "id must use lower_snake_case and start with a letter")
    version = _string(data.get("version"))
    if not VERSION_PATTERN.fullmatch(version):
        raise _fail(source, "version must use semantic x.y.z form")
    if not isinstance(data.get("enabled"), bool):
        raise _fail(source, "enabled must be true or false")
    available_in = _string_list(data.get("available_in"), source, "available_in", allow_empty=False)
    unknown_scopes = set(available_in) - RUNTIME_SCOPES
    if unknown_scopes:
        raise _fail(source, f"available_in contains unsupported scopes: {sorted(unknown_scopes)}")
    execution_profile = _string(data.get("execution_profile"))
    if execution_profile not in EXECUTION_PROFILES:
        raise _fail(source, f"execution_profile must be one of {sorted(EXECUTION_PROFILES)}")
    product_tier = _string(data.get("product_tier"))
    if product_tier not in PRODUCT_TIER_VALUES:
        raise _fail(source, f"product_tier must be one of {sorted(PRODUCT_TIER_VALUES)}")
    public_safe = data.get("public_safe")
    if not isinstance(public_safe, bool):
        raise _fail(source, "public_safe must be true or false")
    sensitivity = _string(data.get("sensitivity_default"))
    if sensitivity not in SENSITIVITY_VALUES:
        raise _fail(source, f"unsupported sensitivity_default: {sensitivity}")
    public_scope = "public_starter" in available_in
    if public_scope and (not public_safe or sensitivity not in PUBLIC_SAFE_DEFAULTS):
        raise _fail(source, "public_starter plugins must be public_safe with a public/public_safe/local_only default")

    documentation = (
        validate_documentation(
            data.get("documentation"), root=root, source=source, plugin_id=plugin_id, fail=_fail
        )
        if require_documentation or data.get("documentation") is not None
        else {}
    )

    authority = _authority(data.get("authority"), source)
    permissions = _permissions(
        data.get("permissions"),
        root=root,
        source=source,
        public_scope=public_scope,
        execution_profile=execution_profile,
    )
    state_namespace = _string(data.get("state_namespace"))
    if state_namespace != f"researchos.plugin.{plugin_id}":
        raise _fail(source, f"state_namespace must be researchos.plugin.{plugin_id}")

    contributions = data.get("contributions")
    if not isinstance(contributions, dict):
        raise _fail(source, "contributions must be an object")
    unknown_contributions = set(contributions) - set(CONTRIBUTION_TYPES)
    if unknown_contributions:
        raise _fail(source, f"contributions contains unsupported types: {sorted(unknown_contributions)}")
    normalized_contributions = {
        field: _contribution_items(contributions.get(field, []), source, field)
        for field in CONTRIBUTION_TYPES
    }
    if not any(normalized_contributions.values()):
        raise _fail(source, "contributions must declare at least one contribution")
    if execution_profile != "declarative" and any(
        action["execution"] != "platform_registered" for action in normalized_contributions["actions"]
    ):
        raise _fail(source, "executable plugin actions must use platform_registered execution")
    if product_tier == "foundation_projection" and normalized_contributions["tasks"]:
        raise _fail(source, "foundation_projection plugins may project the optional Dashboard but must not own conversation tasks")
    action_ids = {item["id"] for item in normalized_contributions["actions"]}
    projection_ids = {item["id"] for item in normalized_contributions["projections"]}
    for provider in normalized_contributions["work_item_providers"]:
        if provider["projection_id"] not in projection_ids:
            raise _fail(source, f"work_item provider references missing projection: {provider['projection_id']}")
    for slot in normalized_contributions["ui_slots"]:
        missing_actions = sorted(set(slot["action_ids"]) - action_ids)
        missing_projections = sorted(set(slot["projection_ids"]) - projection_ids)
        if missing_actions:
            raise _fail(source, f"ui slot {slot['id']} references unknown actions: {missing_actions}")
        if missing_projections:
            raise _fail(source, f"ui slot {slot['id']} references unknown projections: {missing_projections}")
        action_by_id = {item["id"]: item for item in normalized_contributions["actions"]}
        mismatched_actions = sorted(
            action_id for action_id in slot["action_ids"]
            if action_by_id[action_id]["surface"] != slot["surface"]
        )
        if mismatched_actions:
            raise _fail(source, f"ui slot {slot['id']} references actions from another surface: {mismatched_actions}")

    task_descriptors: list[dict[str, Any]] = []
    for contribution in normalized_contributions["tasks"]:
        task_data = contribution.get("task")
        descriptor = validate_task_extension_descriptor(
            {
                "schema_id": "researchos-task-extension-v1",
                "core_api_version": CORE_API_VERSION,
                "id": contribution["id"],
                "version": version,
                "enabled": True,
                "available_in": available_in,
                "public_safe": public_safe,
                "sensitivity_default": sensitivity,
                "authority": authority,
                "task": task_data,
            },
            root=root,
            source=source,
            require_documentation=False,
        )
        task_descriptors.append(descriptor)

    result_modes = {
        mode
        for descriptor in task_descriptors
        for mode in descriptor["task"]["result_modes"]
    }
    governance = validate_governance(
        data.get("governance"),
        root=root,
        source=source,
        plugin_id=plugin_id,
        product_tier=product_tier,
        enabled=data["enabled"],
        result_modes=result_modes,
        public_safe=public_safe,
        sensitivity_default=sensitivity,
    )
    allowed_effects = set(governance["effects"]["allowed_effects"])
    for action in normalized_contributions["actions"]:
        action_effect = action.get("effect")
        if action_effect is not None and action_effect not in allowed_effects:
            raise _fail(source, f"action {action['id']} effect is not allowed by governance.effects")
        if action.get("confirmation_mode") == "inline" and action_effect != "bounded_runtime_state":
            raise _fail(source, f"inline action {action['id']} must declare bounded_runtime_state effect")
        if action["execution"] == "review" and action_effect != "review_candidate":
            raise _fail(source, f"review action {action['id']} must declare review_candidate effect")
        if action_effect == "reversible_workspace_write":
            if action["execution"] != "platform_registered" or action.get("reversible") is not True:
                raise _fail(source, f"workspace-writing action {action['id']} must be platform_registered and reversible")

    lifecycle = data.get("lifecycle")
    if not isinstance(lifecycle, dict):
        raise _fail(source, "lifecycle must be an object")
    unknown_lifecycle = set(lifecycle) - {"install", "enable", "disable", "uninstall", "migrations"}
    if unknown_lifecycle:
        raise _fail(source, f"lifecycle contains unsupported fields: {sorted(unknown_lifecycle)}")
    lifecycle_by_deployment = {
        "embedded_foundation": {
            "install": "core_bundled",
            "enable": "runtime_scope",
            "disable": "runtime_scope",
            "uninstall": "core_release_change",
        },
        "bundled_default_on": {
            "install": "release_bundled",
            "enable": "manifest_flag",
            "disable": "manifest_flag",
            "uninstall": "release_change",
        },
        "local_installable": {
            "install": "manifest_present",
            "enable": "manifest_flag",
            "disable": "manifest_flag",
            "uninstall": "remove_manifest",
        },
    }
    expected_lifecycle = (
        lifecycle_by_deployment["local_installable"]
        if governance["compatibility_defaulted"]
        else lifecycle_by_deployment[governance["deployment_mode"]]
    )
    for field, expected in expected_lifecycle.items():
        if lifecycle.get(field) != expected:
            raise _fail(source, f"lifecycle.{field} must be {expected}")
    migrations = _string_list(lifecycle.get("migrations"), source, "lifecycle.migrations")
    invalid_migrations = [value for value in migrations if not ID_PATTERN.fullmatch(value)]
    if invalid_migrations:
        raise _fail(source, f"lifecycle.migrations must use lower_snake_case ids: {invalid_migrations}")

    validation = data.get("validation")
    if not isinstance(validation, dict):
        raise _fail(source, "validation must be an object")
    unknown_validation = set(validation) - {"commands", "behavior_tests"}
    if unknown_validation:
        raise _fail(source, f"validation contains unsupported fields: {sorted(unknown_validation)}")
    commands = _string_list(validation.get("commands"), source, "validation.commands", allow_empty=False)
    behavior_tests = _string_list(
        validation.get("behavior_tests"), source, "validation.behavior_tests", allow_empty=False
    )
    if public_scope:
        unsafe_metadata = [
            value
            for value in [*commands, *behavior_tests]
            if any(marker in value for marker in PUBLIC_FORBIDDEN_VALIDATION_MARKERS)
        ]
        if unsafe_metadata:
            raise _fail(source, "public_starter validation metadata must not reference private or escaping paths")

    return {
        **data,
        "id": plugin_id,
        "version": version,
        "available_in": available_in,
        "execution_profile": execution_profile,
        "product_tier": product_tier,
        "sensitivity_default": sensitivity,
        **({"documentation": documentation} if documentation else {}),
        "authority": authority,
        "permissions": permissions,
        "contributions": normalized_contributions,
        "state_namespace": state_namespace,
        "lifecycle": {**expected_lifecycle, "migrations": migrations},
        "validation": {"commands": commands, "behavior_tests": behavior_tests},
        "governance": governance,
        "_origin": "plugin_v1",
        "_source": source,
        "_task_descriptors": task_descriptors,
    }


def normalize_task_extension_plugin(
    descriptor: dict[str, Any], *, source: Path, root: Path
) -> dict[str, Any]:
    """Adapt one already-valid task-extension v1 descriptor into the plugin registry model."""
    validated = validate_task_extension_descriptor(descriptor, root=root, source=source)
    extension_id = validated["id"]
    return {
        "schema_id": SCHEMA_ID,
        "core_api_version": CORE_API_VERSION,
        "id": extension_id,
        "version": validated["version"],
        "enabled": validated["enabled"],
        "available_in": list(validated["available_in"]),
        "execution_profile": "declarative",
        "product_tier": "optional_extension",
        "public_safe": validated["public_safe"],
        "sensitivity_default": validated["sensitivity_default"],
        **({"documentation": dict(validated["documentation"])} if validated.get("documentation") else {}),
        "authority": dict(validated["authority"]),
        "permissions": {
            "read_paths": [],
            "network_domains": [],
            "command_ids": [],
            "state_access": "none",
            "canonical_write": False,
        },
        "contributions": {
            "tasks": [{"id": extension_id, "task": dict(validated["task"])}],
            **{field: [] for field in CONTRIBUTION_TYPES if field != "tasks"},
        },
        "state_namespace": f"researchos.plugin.{extension_id}",
        "lifecycle": {
            "install": "manifest_present",
            "enable": "manifest_flag",
            "disable": "manifest_flag",
            "uninstall": "remove_manifest",
            "migrations": [],
        },
        "validation": {
            "commands": ["python3 scripts/validate_task_extensions.py"],
            "behavior_tests": ["python3 -m unittest evals.test_task_extensions"],
        },
        "governance": dict(validated["governance"]),
        "_origin": "task_extension_v1",
        "_source": source,
        "_task_descriptors": [validated],
    }


def _manifest_identifiers(plugin: dict[str, Any]) -> set[str]:
    identifiers = {plugin["id"]}
    for descriptor in plugin.get("_task_descriptors", []):
        identifiers.add(descriptor["id"])
        identifiers.update(descriptor["task"].get("aliases", []))
    return identifiers


def _safe_registry_entry(plugin: dict[str, Any]) -> dict[str, Any]:
    contribution_counts = {
        field: len(plugin["contributions"].get(field, []))
        for field in CONTRIBUTION_TYPES
    }
    return {
        "id": plugin["id"],
        "version": plugin["version"],
        "origin": plugin["_origin"],
        "execution_profile": plugin["execution_profile"],
        "execution_boundary": {
            "state": "declarative_only" if plugin["execution_profile"] == "declarative" else "host_disabled",
            "host_execution_available": False,
            "required_contracts": list(EXECUTION_BOUNDARY_CONTRACTS[plugin["execution_profile"]]),
        },
        "product_tier": plugin["product_tier"],
        "deployment_mode": plugin["governance"]["deployment_mode"],
        "distribution": dict(plugin["governance"]["distribution"]),
        "effects": dict(plugin["governance"]["effects"]),
        "maturity": plugin["governance"]["admission"]["maturity"],
        "public_safe": plugin["public_safe"],
        "available_in": list(plugin["available_in"]),
        "sensitivity_default": plugin["sensitivity_default"],
        "state_namespace": plugin["state_namespace"],
        "contribution_counts": contribution_counts,
    }


def _runtime_contributions(plugin: dict[str, Any], language: str) -> dict[str, list[dict[str, Any]]]:
    """Project reviewed declarative contributions without paths, permissions, or frozen-language copy."""
    projected = {field: [] for field in CONTRIBUTION_TYPES if field != "tasks"}
    for field in projected:
        for contribution in plugin["contributions"].get(field, []):
            item = {
                **contribution,
                "contribution_key": f"{plugin['id']}:{contribution['id']}",
                "plugin_id": plugin["id"],
                "plugin_version": plugin["version"],
                "plugin_tier": plugin["product_tier"],
            }
            if field == "ui_slots":
                locale = contribution["locales"][language]
                item = {key: value for key, value in item.items() if key != "locales"}
                item.update(locale)
            projected[field].append(item)
    return projected


def validated_plugin_manifests(
    root: Path, *, base_task_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Read one validated inventory, including disabled entries, for host consumers."""
    plugins: list[dict[str, Any]] = []
    for source in plugin_manifest_paths(root):
        plugins.append(validate_plugin_manifest(_safe_source_data(root, source), root=root, source=source))
    for source in task_extension_paths(root):
        data = _safe_source_data(root, source)
        plugins.append(normalize_task_extension_plugin(data, source=source, root=root))

    used_identifiers = set(base_task_ids or set())
    identifier_owners = {identifier: "core" for identifier in used_identifiers}
    plugin_id_owners: dict[str, Path] = {}
    for plugin in plugins:
        if plugin["id"] in plugin_id_owners:
            raise _fail(plugin["_source"], f"plugin id {plugin['id']} already belongs to {plugin_id_owners[plugin['id']]}")
        plugin_id_owners[plugin["id"]] = plugin["_source"]
        for identifier in sorted(_manifest_identifiers(plugin)):
            owner = identifier_owners.get(identifier)
            if owner and owner != plugin["id"]:
                raise _fail(plugin["_source"], f"plugin/task/alias {identifier} already belongs to {owner}")
            identifier_owners[identifier] = plugin["id"]
            used_identifiers.add(identifier)

    return plugins


def load_plugin_registry(
    root: Path,
    *,
    runtime_scope: str,
    language: str,
    base_task_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Load native manifests and compatible task extensions into one safe registry."""
    if runtime_scope not in RUNTIME_SCOPES:
        raise PluginManifestError(f"unsupported runtime scope: {runtime_scope}")
    if language not in LANGUAGES:
        raise PluginManifestError(f"unsupported plugin language: {language}")

    plugins = validated_plugin_manifests(root, base_task_ids=base_task_ids)

    tasks: list[dict[str, Any]] = []
    loaded: list[dict[str, Any]] = []
    runtime_contributions = {field: [] for field in CONTRIBUTION_TYPES if field != "tasks"}
    disabled_count = 0
    unavailable_count = 0
    for plugin in plugins:
        if not plugin["enabled"]:
            disabled_count += 1
            continue
        if runtime_scope not in plugin["available_in"]:
            unavailable_count += 1
            continue
        if runtime_scope == "public_starter" and not plugin["public_safe"]:
            raise _fail(plugin["_source"], "public_starter attempted to load a non-public-safe plugin")
        executable_profile = plugin["execution_profile"] != "declarative"
        for descriptor in plugin.get("_task_descriptors", []):
            if executable_profile:
                continue
            task = task_from_descriptor(descriptor, language)
            task.update(
                {
                    "plugin_id": plugin["id"],
                    "plugin_version": plugin["version"],
                    "plugin_origin": plugin["_origin"],
                    "plugin_tier": plugin["product_tier"],
                }
            )
            tasks.append(task)
        projected = _runtime_contributions(plugin, language)
        if not executable_profile:
            for field, items in projected.items():
                runtime_contributions[field].extend(items)
        loaded.append(_safe_registry_entry(plugin))

    return {
        "schema_id": SCHEMA_ID,
        "core_api_version": CORE_API_VERSION,
        "runtime_scope": runtime_scope,
        "active_language": language,
        "loaded": loaded,
        "loaded_count": len(loaded),
        "disabled_count": disabled_count,
        "unavailable_count": unavailable_count,
        "compatibility_task_extension_count": sum(
            1 for plugin in plugins if plugin["_origin"] == "task_extension_v1" and plugin["enabled"]
        ),
        "product_tier_counts": {
            tier: sum(1 for plugin in plugins if plugin["enabled"] and runtime_scope in plugin["available_in"] and plugin["product_tier"] == tier)
            for tier in sorted(PRODUCT_TIER_VALUES)
        },
        "tasks": tasks,
        "contributions": runtime_contributions,
    }


def validate_plugin_files(root: Path) -> list[str]:
    """Validate every native manifest, including disabled examples."""
    failures: list[str] = []
    seen_ids: dict[str, Path] = {}
    for source in plugin_manifest_paths(root, include_examples=True):
        try:
            manifest = validate_plugin_manifest(_safe_source_data(root, source), root=root, source=source)
            if source.name.endswith(".example.json"):
                continue
            plugin_id = manifest["id"]
            if plugin_id in seen_ids:
                failures.append(f"{source}: plugin id {plugin_id} already belongs to {seen_ids[plugin_id]}")
            else:
                seen_ids[plugin_id] = source
        except (json.JSONDecodeError, OSError, PluginManifestError, ValueError) as error:
            failures.append(str(error))
    return failures


def _overlay_failures(
    *,
    root: Path,
    label: str,
    ownership: tuple[dict[str, str], ...],
    active_paths: set[str],
) -> list[str]:
    failures: list[str] = []
    required_fields = {
        "owner_path",
        "logical_owner",
        "owner_kind",
        "plugin_id",
        "payload_contract",
        "render_target_or_slot",
        "public_mode",
        "behavior_test",
        "migration_state",
        "removal_phase",
    }
    owner_paths = [entry.get("owner_path", "") for entry in ownership]
    duplicates = sorted({path for path in owner_paths if owner_paths.count(path) > 1})
    if duplicates:
        failures.append(f"{label} ownership repeats active owners: {duplicates}")
    missing = sorted(active_paths - set(owner_paths))
    extra = sorted(set(owner_paths) - active_paths)
    if missing:
        failures.append(f"{label} ownership is missing active owners: {missing}")
    if extra:
        failures.append(f"{label} ownership references inactive owners: {extra}")
    for entry in ownership:
        absent = sorted(field for field in required_fields if field not in entry)
        if absent:
            failures.append(f"{label} owner {entry.get('owner_path', 'unknown')} is missing fields: {absent}")
            continue
        owner_kind = entry["owner_kind"]
        if owner_kind not in {"core", "platform", "plugin"}:
            failures.append(f"{label} owner {entry['owner_path']} has invalid owner_kind: {owner_kind}")
        if owner_kind == "plugin":
            if not ID_PATTERN.fullmatch(entry["plugin_id"]):
                failures.append(f"{label} plugin owner {entry['owner_path']} has invalid plugin_id")
            if entry["migration_state"] != "native_plugin_adapter":
                failures.append(f"{label} plugin owner {entry['owner_path']} must be a native plugin adapter")
            if entry["removal_phase"] != "not_applicable":
                failures.append(f"{label} native plugin owner {entry['owner_path']} must close its removal milestone")
        elif entry["plugin_id"]:
            failures.append(f"{label} non-plugin owner {entry['owner_path']} must not declare plugin_id")
        for field in ("logical_owner", "payload_contract", "render_target_or_slot", "public_mode", "behavior_test"):
            if not _string(entry[field]):
                failures.append(f"{label} owner {entry['owner_path']} has empty {field}")
        behavior_test = root / entry["behavior_test"]
        if not behavior_test.is_file():
            failures.append(f"{label} owner {entry['owner_path']} behavior test does not exist: {entry['behavior_test']}")
    return failures


def ownership_overlay_failures(root: Path) -> list[str]:
    """Validate one logical owner per active frontend, style, and data source owner."""
    from researchos_data.frontend_manifest import (
        FRONTEND_CORE_OWNER_SCRIPTS,
        FRONTEND_PLUGIN_OWNER_SCRIPTS,
        frontend_logical_ownership,
        frontend_script_load_order,
    )
    from researchos_data.plugin_ownership import (
        DATA_CORE_OWNER_MODULES,
        DATA_PLUGIN_OWNER_MODULES,
        data_logical_ownership,
    )
    from researchos_data.style_manifest import (
        STYLE_CORE_OWNER_IDS,
        STYLE_LAYER_IMPORTS,
        STYLE_PLUGIN_OWNER_IDS,
        style_logical_ownership,
    )

    failures: list[str] = []

    def duplicate_declarations(groups: dict[str, tuple[str, ...]], label: str) -> None:
        paths = [path for members in groups.values() for path in members]
        duplicates = sorted({path for path in paths if paths.count(path) > 1})
        if duplicates:
            failures.append(f"{label} logical-owner declarations overlap: {duplicates}")

    duplicate_declarations(
        {**FRONTEND_CORE_OWNER_SCRIPTS, **FRONTEND_PLUGIN_OWNER_SCRIPTS}, "frontend"
    )
    duplicate_declarations({**STYLE_CORE_OWNER_IDS, **STYLE_PLUGIN_OWNER_IDS}, "style")
    duplicate_declarations({**DATA_CORE_OWNER_MODULES, **DATA_PLUGIN_OWNER_MODULES}, "data")

    failures.extend(
        _overlay_failures(
            root=root,
            label="frontend",
            ownership=frontend_logical_ownership(),
            active_paths=set(frontend_script_load_order()),
        )
    )
    failures.extend(
        _overlay_failures(
            root=root,
            label="style",
            ownership=style_logical_ownership(),
            active_paths={entry["path"] for entry in STYLE_LAYER_IMPORTS},
        )
    )
    data_ownership = data_logical_ownership(root)
    failures.extend(
        _overlay_failures(
            root=root,
            label="data",
            ownership=data_ownership,
            active_paths={
                path.relative_to(root).as_posix()
                for path in sorted((root / "scripts" / "researchos_data").glob("*.py"))
            },
        )
    )
    return failures


def ownership_registry_summary(root: Path) -> dict[str, Any]:
    """Return compact ownership and change-radius reports for all three active owner planes."""
    from researchos_data.frontend_manifest import frontend_ownership_report
    from researchos_data.plugin_ownership import data_ownership_report
    from researchos_data.style_manifest import style_ownership_report

    return {
        "schema_id": "researchos-plugin-ownership-overlay-v1",
        "frontend": frontend_ownership_report(),
        "style": style_ownership_report(),
        "data": data_ownership_report(root),
    }
