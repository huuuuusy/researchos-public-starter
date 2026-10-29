/* ResearchOS maintenance header.
 * 中文：RuntimeProfileProjection v1 的浏览器白名单 owner；只接受可显示状态，不读取配置、凭据或 endpoint。
 * English: Browser allowlist owner for RuntimeProfileProjection v1; accepts display state only, never config, credentials, or endpoints.
 */

(function attachResearchOSRuntimeProfileProjection(global) {
  const SCHEMA_ID = "researchos-runtime-profile-projection-v1";
  const KEYS = [
    "schema_id", "profile_id", "adapter_family", "provider", "enabled", "execution_scope",
    "model", "reasoning_effort", "result_modes", "cancel", "status", "verification_state",
    "selector_state", "error_type", "configuration_handoff",
  ];
  const FAMILIES = ["none", "local_codex", "local_claude_code"];
  const MODES = ["answer", "artifact", "writeback"];
  const STATUSES = ["configured", "disabled", "copy_only", "invalid"];
  const VERIFICATION = [
    "local_probe_required", "local_probe_passed", "local_probe_failed",
    "disabled", "copy_only", "configuration_invalid",
  ];
  const EXECUTION = ["none", "answer_only", "workspace_write"];

  function exactKeys(value, keys) {
    return value && typeof value === "object" && !Array.isArray(value)
      && Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key));
  }

  function text(value, maximum) {
    return typeof value === "string" && !value.includes("\0") && value.length <= maximum ? value : null;
  }

  function normalize(value) {
    if (!exactKeys(value, KEYS) || value.schema_id !== SCHEMA_ID || typeof value.enabled !== "boolean") return null;
    if (!FAMILIES.includes(value.adapter_family) || !EXECUTION.includes(value.execution_scope)
      || !STATUSES.includes(value.status) || !VERIFICATION.includes(value.verification_state)
      || value.cancel !== "unsupported" || value.selector_state !== "candidate_off") return null;
    const profileId = text(value.profile_id, 64); const provider = text(value.provider, 160);
    const model = text(value.model, 160); const reasoning = text(value.reasoning_effort, 160);
    const errorType = text(value.error_type, 160);
    if (!profileId || provider === null || model === null || reasoning === null || errorType === null) return null;
    if (!Array.isArray(value.result_modes) || value.result_modes.length > 3
      || new Set(value.result_modes).size !== value.result_modes.length
      || value.result_modes.some((mode) => !MODES.includes(mode))) return null;
    const handoff = value.configuration_handoff;
    if (!exactKeys(handoff, ["mode", "command", "config_target"]) || handoff.mode !== "copy_only"
      || handoff.config_target !== "config/researchos.runtime.local.json") return null;
    const command = text(handoff.command, 180);
    if (!command || !/^python3 scripts\/runtime_profile_cli\.py (?:validate|list --scope public_starter|show --profile [a-z][a-z0-9_-]{0,63})$/.test(command)) return null;
    if (["disabled", "copy_only", "invalid"].includes(value.status) && (value.enabled || value.execution_scope !== "none")) return null;
    if (["configured", "disabled"].includes(value.status)
      && (!/^[a-z][a-z0-9_-]{0,63}$/.test(profileId) || !provider || !model || !reasoning
        || command !== `python3 scripts/runtime_profile_cli.py show --profile ${profileId}`)) return null;
    if (value.status === "configured" && !value.enabled) return null;
    if (value.status === "disabled" && value.verification_state !== "disabled") return null;
    if (value.status === "copy_only" && (profileId !== "public-copy-only" || value.adapter_family !== "none"
      || value.verification_state !== "copy_only" || command !== "python3 scripts/runtime_profile_cli.py list --scope public_starter" || errorType)) return null;
    if (value.status === "invalid" && (profileId !== "unavailable" || value.adapter_family !== "none"
      || value.verification_state !== "configuration_invalid" || command !== "python3 scripts/runtime_profile_cli.py validate" || !errorType)) return null;
    if (value.adapter_family === "local_codex" && value.enabled
      && (value.execution_scope !== "workspace_write" || !["local_probe_required", "local_probe_passed", "local_probe_failed"].includes(value.verification_state))) return null;
    const configurationHandoff = Object.freeze({
      mode: "copy_only", command, config_target: handoff.config_target,
    });
    return Object.freeze({
      schema_id: SCHEMA_ID, profile_id: profileId, adapter_family: value.adapter_family,
      provider, enabled: value.enabled, execution_scope: value.execution_scope,
      model, reasoning_effort: reasoning, result_modes: Object.freeze([...value.result_modes]),
      cancel: "unsupported", status: value.status, verification_state: value.verification_state,
      selector_state: "candidate_off", error_type: errorType, configuration_handoff: configurationHandoff,
    });
  }

  global.ResearchOSRuntimeProfileProjection = Object.freeze({ SCHEMA_ID, normalize });
})(window);
