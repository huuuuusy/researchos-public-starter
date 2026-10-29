# ResearchOS maintenance header.
# 中文：RuntimeProfile v1 的唯一规范化与安全投影 owner；profile 只描述执行配置，不授予 authority 或 egress。
# English: Sole normalizer and safe-projection owner for RuntimeProfile v1; profiles describe execution configuration without granting authority or egress.

"""Runtime profiles derived from the providers block of the runtime configuration."""

from __future__ import annotations

import re
from typing import Mapping

from researchos_adapters.model_catalog import MODEL_ID_PATTERN, REASONING_EFFORTS
from researchos_adapters.provider_registry import PROVIDERS, get_provider_spec
from researchos_kernel.task_envelope import RUNTIME_SCOPES


RUNTIME_PROFILE_SCHEMA_ID = "researchos-runtime-profile-v1"
ADAPTER_FAMILIES = tuple(spec.type for spec in PROVIDERS.values())
PROFILE_SCOPES = ("private", "personal_vault")
RESULT_MODES = ("answer", "artifact", "writeback")
REASONING_VALUES = ("auto", *sorted(REASONING_EFFORTS))
PROFILE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
PROFILE_KEYS = {
    "schema_id", "profile_id", "adapter_family", "provider", "enabled", "allowed_scopes",
    "model", "allowed_models", "reasoning_effort", "allowed_reasoning_efforts", "endpoint_ref",
    "credential_ref", "capabilities", "timeout_seconds", "cost_policy", "fallback_policy",
}
PROJECTION_SCHEMA_ID = "researchos-runtime-profile-projection-v1"
PROJECTION_KEYS = {
    "schema_id", "profile_id", "adapter_family", "provider", "enabled", "execution_scope",
    "model", "reasoning_effort", "result_modes", "cancel", "status", "verification_state",
    "selector_state", "error_type", "configuration_handoff",
}


class RuntimeProfileError(ValueError):
    """Stable fail-closed error at the profile boundary."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _exact_mapping(value: object, keys: set[str], code: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise RuntimeProfileError(code)
    return value


def _bounded(value: object, *, maximum: int, code: str) -> str:
    text = str(value or "").strip()
    if not text or "\x00" in text or len(text) > maximum:
        raise RuntimeProfileError(code)
    return text


def _unique_strings(value: object, *, maximum: int, code: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or len(value) > maximum:
        raise RuntimeProfileError(code)
    result: list[str] = []
    for item in value:
        text = _bounded(item, maximum=160, code=code)
        if text in result:
            raise RuntimeProfileError(code)
        result.append(text)
    return tuple(result)


def normalize_runtime_profile(value: object) -> dict[str, object]:
    """Normalize a strict profile without resolving credentials, endpoints, policy, or network access."""
    raw = _exact_mapping(value, PROFILE_KEYS, "runtime_profile_shape_invalid")
    if raw["schema_id"] != RUNTIME_PROFILE_SCHEMA_ID:
        raise RuntimeProfileError("runtime_profile_schema_invalid")
    profile_id = _bounded(raw["profile_id"], maximum=64, code="runtime_profile_id_invalid")
    if not PROFILE_ID_PATTERN.fullmatch(profile_id):
        raise RuntimeProfileError("runtime_profile_id_invalid")
    family = _bounded(raw["adapter_family"], maximum=40, code="runtime_profile_adapter_invalid")
    provider = _bounded(raw["provider"], maximum=64, code="runtime_profile_provider_invalid")
    if family not in ADAPTER_FAMILIES:
        raise RuntimeProfileError("runtime_profile_adapter_invalid")
    try:
        provider_spec = get_provider_spec(provider)
    except KeyError as exc:
        raise RuntimeProfileError("runtime_profile_provider_invalid") from exc
    if provider_spec.type != family:
        raise RuntimeProfileError("runtime_profile_provider_mismatch")
    if not isinstance(raw["enabled"], bool):
        raise RuntimeProfileError("runtime_profile_enabled_invalid")

    scopes = _unique_strings(raw["allowed_scopes"], maximum=2, code="runtime_profile_scope_invalid")
    if any(scope not in PROFILE_SCOPES for scope in scopes):
        raise RuntimeProfileError("runtime_profile_scope_invalid")
    models = _unique_strings(raw["allowed_models"], maximum=32, code="runtime_profile_model_invalid")
    if any(model != "auto" and not MODEL_ID_PATTERN.fullmatch(model) for model in models):
        raise RuntimeProfileError("runtime_profile_model_invalid")
    model = _bounded(raw["model"], maximum=160, code="runtime_profile_model_invalid")
    if model not in models:
        raise RuntimeProfileError("runtime_profile_model_not_allowed")
    reasoning_values = _unique_strings(
        raw["allowed_reasoning_efforts"], maximum=len(REASONING_VALUES),
        code="runtime_profile_reasoning_invalid",
    )
    if any(value not in REASONING_VALUES for value in reasoning_values):
        raise RuntimeProfileError("runtime_profile_reasoning_invalid")
    reasoning = _bounded(raw["reasoning_effort"], maximum=16, code="runtime_profile_reasoning_invalid")
    if reasoning not in reasoning_values:
        raise RuntimeProfileError("runtime_profile_reasoning_not_allowed")

    endpoint_ref = _bounded(raw["endpoint_ref"], maximum=120, code="runtime_profile_endpoint_ref_invalid")
    credential = _exact_mapping(
        raw["credential_ref"], {"kind", "name"}, "runtime_profile_credential_ref_invalid"
    )
    credential_kind = str(credential["kind"])
    credential_name = str(credential["name"])
    if endpoint_ref != provider_spec.endpoint_ref or credential_kind != "none" or credential_name:
        raise RuntimeProfileError("runtime_profile_local_binding_invalid")

    capabilities = _exact_mapping(
        raw["capabilities"], {"result_modes", "streaming", "cancel", "tool_calling", "agent_loop"},
        "runtime_profile_capabilities_invalid",
    )
    result_modes = _unique_strings(
        capabilities["result_modes"], maximum=3, code="runtime_profile_capabilities_invalid"
    )
    if any(mode not in RESULT_MODES for mode in result_modes):
        raise RuntimeProfileError("runtime_profile_capabilities_invalid")
    booleans = (capabilities["streaming"], capabilities["tool_calling"], capabilities["agent_loop"])
    cancel = str(capabilities["cancel"])
    if any(not isinstance(flag, bool) for flag in booleans) or cancel not in {"unsupported", "best_effort", "supported"}:
        raise RuntimeProfileError("runtime_profile_capabilities_invalid")
    if any(booleans) or cancel != "unsupported":
        raise RuntimeProfileError("runtime_profile_capability_not_enabled")
    if family != "local_codex" and result_modes != ("answer",):
        raise RuntimeProfileError("runtime_profile_capability_not_enabled")  # Claude Code answers only; it never writes

    timeout = raw["timeout_seconds"]
    if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 3600:
        raise RuntimeProfileError("runtime_profile_timeout_invalid")
    cost = _exact_mapping(raw["cost_policy"], {"mode", "budget_ref"}, "runtime_profile_cost_policy_invalid")
    cost_mode, budget_ref = str(cost["mode"]), str(cost["budget_ref"])
    if cost_mode != "local_unmetered" or budget_ref:
        raise RuntimeProfileError("runtime_profile_cost_policy_invalid")
    fallback = _exact_mapping(raw["fallback_policy"], {"mode"}, "runtime_profile_fallback_policy_invalid")
    if fallback["mode"] != "none":
        raise RuntimeProfileError("runtime_profile_fallback_policy_invalid")

    return {
        "schema_id": RUNTIME_PROFILE_SCHEMA_ID,
        "profile_id": profile_id,
        "adapter_family": family,
        "provider": provider,
        "enabled": raw["enabled"],
        "allowed_scopes": list(scopes),
        "model": model,
        "allowed_models": list(models),
        "reasoning_effort": reasoning,
        "allowed_reasoning_efforts": list(reasoning_values),
        "endpoint_ref": endpoint_ref,
        "credential_ref": {"kind": credential_kind, "name": credential_name},
        "capabilities": {
            "result_modes": list(result_modes), "streaming": capabilities["streaming"],
            "cancel": cancel, "tool_calling": capabilities["tool_calling"],
            "agent_loop": capabilities["agent_loop"],
        },
        "timeout_seconds": timeout,
        "cost_policy": {"mode": cost_mode, "budget_ref": budget_ref},
        "fallback_policy": {"mode": "none"},
    }


def _provider_profile(provider: str, value: object) -> dict[str, object]:
    config = value if isinstance(value, Mapping) else {}
    try:
        spec = get_provider_spec(provider)
    except KeyError as exc:
        raise RuntimeProfileError("runtime_profile_provider_invalid") from exc
    family = str(config.get("type") or spec.type)
    model = str(config.get("default_model") or spec.default_model)
    enabled = config.get("enabled", False)
    if not isinstance(enabled, bool):
        raise RuntimeProfileError("runtime_profile_enabled_invalid")
    return normalize_runtime_profile({
        "schema_id": RUNTIME_PROFILE_SCHEMA_ID,
        "profile_id": provider,
        "adapter_family": family,
        "provider": provider,
        "enabled": enabled,
        "allowed_scopes": ["private", "personal_vault"],
        "model": model,
        "allowed_models": [model],
        "reasoning_effort": "auto",
        "allowed_reasoning_efforts": ["auto"],
        "endpoint_ref": spec.endpoint_ref,
        "credential_ref": {"kind": "none", "name": ""},
        "capabilities": {
            "result_modes": ["answer", "artifact", "writeback"] if family == "local_codex" else ["answer"],
            "streaming": False, "cancel": "unsupported", "tool_calling": False, "agent_loop": False,
        },
        "timeout_seconds": 900,
        "cost_policy": {"mode": "local_unmetered", "budget_ref": ""},
        "fallback_policy": {"mode": "none"},
    })


def runtime_profiles_from_config(config: object) -> dict[str, dict[str, object]]:
    """One profile per entry of the providers block, built without mutating the configuration."""
    if not isinstance(config, Mapping) or config.get("schema_id") != "researchos-runtime-config-v1":
        raise RuntimeProfileError("runtime_config_invalid")
    if "runtime_profiles" in config:  # the retired dual-read key: refuse it rather than ignore it silently
        raise RuntimeProfileError("runtime_profiles_invalid")
    providers = config.get("providers")
    if not isinstance(providers, Mapping) or not providers:
        raise RuntimeProfileError("runtime_profiles_invalid")
    return {str(name): _provider_profile(str(name), value) for name, value in providers.items()}


def select_runtime_profile(
    config: object, *, profile_id: str | None = None, runtime_scope: str
) -> dict[str, object]:
    if runtime_scope not in RUNTIME_SCOPES:
        raise RuntimeProfileError("runtime_profile_scope_invalid")
    if runtime_scope == "public_starter":
        raise RuntimeProfileError("public_starter_copy_only")
    profiles = runtime_profiles_from_config(config)
    selected = str(profile_id or (config.get("default_runtime_profile") if isinstance(config, Mapping) else "") or (
        config.get("default_provider") if isinstance(config, Mapping) else ""
    ))
    if selected not in profiles:
        raise RuntimeProfileError("runtime_profile_unknown")
    profile = profiles[selected]
    if not profile["enabled"]:
        raise RuntimeProfileError("runtime_profile_disabled")
    if runtime_scope not in profile["allowed_scopes"]:
        raise RuntimeProfileError("runtime_profile_scope_forbidden")
    return profile


def resolve_runtime_profile_route(
    config: object, payload: object, *, runtime_scope: str
) -> tuple[str, str]:
    """Resolve a trusted profile route; a request that names only a provider keeps that provider."""
    if not isinstance(payload, Mapping):
        raise RuntimeProfileError("runtime_profile_request_invalid")
    explicit_profile = str(payload.get("runtime_profile_id") or "").strip()
    if explicit_profile or "provider" not in payload:
        profile = select_runtime_profile(config, profile_id=explicit_profile or None, runtime_scope=runtime_scope)
        return str(profile["profile_id"]), str(profile["provider"])
    provider = str(payload.get("provider") or "codex").strip() or "codex"
    return provider, provider


def _configuration_handoff(profile_id: str, *, public_starter: bool = False, invalid: bool = False) -> dict[str, str]:
    if invalid:
        command = "python3 scripts/runtime_profile_cli.py validate"
    elif public_starter:
        command = "python3 scripts/runtime_profile_cli.py list --scope public_starter"
    else:
        command = f"python3 scripts/runtime_profile_cli.py show --profile {profile_id}"
    return {
        "mode": "copy_only", "command": command,
        "config_target": "config/researchos.runtime.local.json",
    }


def normalize_runtime_profile_projection(value: object) -> dict[str, object]:
    """Validate the exact browser-safe projection; unknown or extra fields fail closed."""
    raw = _exact_mapping(value, PROJECTION_KEYS, "runtime_profile_projection_shape_invalid")
    if raw["schema_id"] != PROJECTION_SCHEMA_ID:
        raise RuntimeProfileError("runtime_profile_projection_schema_invalid")
    profile_id = _bounded(raw["profile_id"], maximum=64, code="runtime_profile_projection_invalid")
    family = str(raw["adapter_family"]); provider = str(raw["provider"])
    model = str(raw["model"]); reasoning = str(raw["reasoning_effort"])
    status = str(raw["status"]); verification = str(raw["verification_state"])
    execution_scope = str(raw["execution_scope"]); error_type = str(raw["error_type"])
    if family not in (*ADAPTER_FAMILIES, "none") or not all(len(item) <= 160 for item in (provider, model, reasoning, error_type)):
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    if not isinstance(raw["enabled"], bool) or raw["selector_state"] != "candidate_off":
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    modes = _unique_strings(raw["result_modes"], maximum=3, code="runtime_profile_projection_invalid") if raw["result_modes"] else ()
    if any(mode not in RESULT_MODES for mode in modes) or raw["cancel"] != "unsupported":
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    handoff = _exact_mapping(
        raw["configuration_handoff"], {"mode", "command", "config_target"},
        "runtime_profile_projection_invalid",
    )
    command = str(handoff["command"]); target = str(handoff["config_target"])
    if handoff["mode"] != "copy_only" or target != "config/researchos.runtime.local.json" or len(command) > 180:
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    command_pattern = r"^python3 scripts/runtime_profile_cli\.py (?:validate|list --scope public_starter|show --profile [a-z][a-z0-9_-]{0,63})$"
    if not re.fullmatch(command_pattern, command):
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    allowed_status = {"configured", "disabled", "copy_only", "invalid"}
    allowed_verification = {"local_probe_required", "local_probe_passed", "local_probe_failed", "disabled", "copy_only", "configuration_invalid"}
    if status not in allowed_status or verification not in allowed_verification or execution_scope not in {"none", "answer_only", "workspace_write"}:
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    if status in {"configured", "disabled"} and (
        not PROFILE_ID_PATTERN.fullmatch(profile_id) or not provider or not model or not reasoning
        or command != f"python3 scripts/runtime_profile_cli.py show --profile {profile_id}"
    ):
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    if status == "configured" and not raw["enabled"]:
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    if status in {"disabled", "copy_only", "invalid"} and (raw["enabled"] or execution_scope != "none"):
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    if status == "disabled" and verification != "disabled":
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    if status == "copy_only" and (
        profile_id != "public-copy-only" or family != "none" or verification != "copy_only"
        or command != "python3 scripts/runtime_profile_cli.py list --scope public_starter" or error_type
    ):
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    if status == "invalid" and (
        profile_id != "unavailable" or family != "none" or verification != "configuration_invalid"
        or command != "python3 scripts/runtime_profile_cli.py validate" or not error_type
    ):
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    if family == "local_codex" and raw["enabled"] and (execution_scope != "workspace_write" or verification not in {"local_probe_required", "local_probe_passed", "local_probe_failed"}):
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    if family not in ("local_codex", "none") and raw["enabled"] and (execution_scope != "answer_only" or verification not in {"local_probe_required", "local_probe_passed", "local_probe_failed"} or modes != ("answer",)):
        raise RuntimeProfileError("runtime_profile_projection_invalid")
    return {
        "schema_id": PROJECTION_SCHEMA_ID, "profile_id": profile_id, "adapter_family": family,
        "provider": provider, "enabled": raw["enabled"], "execution_scope": execution_scope,
        "model": model, "reasoning_effort": reasoning, "result_modes": list(modes),
        "cancel": "unsupported", "status": status, "verification_state": verification,
        "selector_state": "candidate_off", "error_type": error_type,
        "configuration_handoff": {"mode": "copy_only", "command": command, "config_target": target},
    }


def project_runtime_profile(
    value: object, *, runtime_scope: str, execution_available: bool | None = None
) -> dict[str, object]:
    """Return a client-safe capability projection with no endpoint or credential reference."""
    if runtime_scope not in RUNTIME_SCOPES:
        raise RuntimeProfileError("runtime_profile_scope_invalid")
    if runtime_scope == "public_starter":
        return normalize_runtime_profile_projection({
            "schema_id": PROJECTION_SCHEMA_ID, "profile_id": "public-copy-only",
            "adapter_family": "none", "provider": "none", "enabled": False, "execution_scope": "none",
            "model": "none", "reasoning_effort": "none", "result_modes": [], "cancel": "unsupported",
            "status": "copy_only", "verification_state": "copy_only", "selector_state": "candidate_off",
            "error_type": "", "configuration_handoff": _configuration_handoff("", public_starter=True),
        })
    profile = normalize_runtime_profile(value)
    enabled = bool(profile["enabled"])
    family = str(profile["adapter_family"])
    verification = "disabled"
    if enabled:
        verification = "local_probe_required" if execution_available is None else (
            "local_probe_passed" if execution_available else "local_probe_failed"
        )
    return normalize_runtime_profile_projection({
        "schema_id": PROJECTION_SCHEMA_ID,
        "profile_id": profile["profile_id"], "adapter_family": profile["adapter_family"],
        "provider": profile["provider"], "enabled": enabled,
        "execution_scope": ("workspace_write" if family == "local_codex" else "answer_only") if enabled else "none",
        "model": profile["model"],
        "reasoning_effort": profile["reasoning_effort"],
        "result_modes": list(profile["capabilities"]["result_modes"]),
        "cancel": profile["capabilities"]["cancel"], "status": "configured" if enabled else "disabled",
        "verification_state": verification, "selector_state": "candidate_off", "error_type": "",
        "configuration_handoff": _configuration_handoff(str(profile["profile_id"])),
    })


def project_selected_runtime_profile(
    config: object, *, runtime_scope: str, execution_available: bool | None = None
) -> dict[str, object]:
    """Project the configured selection without resolving an endpoint, credential, budget, or source."""
    if runtime_scope == "public_starter":
        return project_runtime_profile({}, runtime_scope=runtime_scope)
    try:
        profiles = runtime_profiles_from_config(config)
        selected = str((config.get("default_runtime_profile") if isinstance(config, Mapping) else "") or (
            config.get("default_provider") if isinstance(config, Mapping) else ""
        ))
        if selected not in profiles:
            raise RuntimeProfileError("runtime_profile_unknown")
        return project_runtime_profile(
            profiles[selected], runtime_scope=runtime_scope, execution_available=execution_available,
        )
    except RuntimeProfileError as exc:
        return normalize_runtime_profile_projection({
            "schema_id": PROJECTION_SCHEMA_ID, "profile_id": "unavailable", "adapter_family": "none",
            "provider": "none", "enabled": False, "execution_scope": "none", "model": "none",
            "reasoning_effort": "none", "result_modes": [], "cancel": "unsupported", "status": "invalid",
            "verification_state": "configuration_invalid", "selector_state": "candidate_off",
            "error_type": exc.code, "configuration_handoff": _configuration_handoff("", invalid=True),
        })
