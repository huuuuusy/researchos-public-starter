/* ResearchOS maintenance header.
 * 中文：ResultEnvelope / ErrorEnvelope v1 的唯一浏览器 owner；只接收公开安全的结果和恢复语义。
 * English: Sole browser owner for ResultEnvelope / ErrorEnvelope v1; accepts only public-safe results and recovery semantics.
 */

(function attachResearchOSResultEnvelope(global) {
  const runtimeProfileContract = global.ResearchOSRuntimeProfileProjection;
  const RESULT_SCHEMA_ID = "researchos-result-envelope-v1";
  const ERROR_SCHEMA_ID = "researchos-error-envelope-v1";
  const RESULT_MODES = Object.freeze(["answer", "artifact", "writeback"]);
  const RUN_STATUSES = Object.freeze(["submitted", "queued", "running", "completed", "failed"]);
  const STAGES = Object.freeze([
    "intake", "normalization", "policy", "provider_preflight", "dispatch", "execution",
    "result_normalization", "projection", "client_transport", "unknown",
  ]);
  const LAST_SAFE_POINTS = Object.freeze([
    "client_pre_submit", "request_delivery_unknown", "server_pre_dispatch", "server_queued",
    "provider_started", "provider_finished", "result_recorded", "effects_confirmed", "unknown",
  ]);
  const DELIVERY_UNKNOWN_ERRORS = new Set(["transport_delivery_unknown", "invalid_server_response", "submit_rejected"]);
  const RECOVERY_ACTIONS = Object.freeze([
    "correct_request", "choose_provider", "configure_provider", "copy_task", "inspect",
    "rebuild_projection", "request_authorization", "retry_same", "wait", "none",
  ]);
  const ERROR_POLICIES = Object.freeze({
    public_starter_copy_only: ["policy", "none", "server_pre_dispatch", "copy_task", "Execution is disabled in this runtime."],
    task_intent_invalid_shape: ["normalization", "none", "server_pre_dispatch", "correct_request", "The task request did not match the supported contract."],
    task_intent_schema_mismatch: ["normalization", "none", "server_pre_dispatch", "correct_request", "The task request used an unsupported contract version."],
    task_intent_invalid_trust: ["normalization", "none", "server_pre_dispatch", "correct_request", "The task request contained an invalid trust declaration."],
    task_intent_invalid_character: ["normalization", "none", "server_pre_dispatch", "correct_request", "The task request contained an unsupported character."],
    task_intent_input_too_large: ["normalization", "none", "server_pre_dispatch", "correct_request", "The task request exceeded the supported size."],
    task_intent_invalid_value: ["normalization", "none", "server_pre_dispatch", "correct_request", "The task request contained an unsupported value."],
    unsupported_result_mode: ["normalization", "none", "server_pre_dispatch", "correct_request", "The requested result mode is unsupported."],
    unsupported_reasoning_effort: ["normalization", "none", "server_pre_dispatch", "correct_request", "The requested reasoning effort is unsupported."],
    unsupported_task_complexity: ["normalization", "none", "server_pre_dispatch", "correct_request", "The requested task complexity is unsupported."],
    unknown_provider: ["provider_preflight", "none", "server_pre_dispatch", "choose_provider", "The requested provider is unknown."],
    provider_not_configured: ["provider_preflight", "none", "server_pre_dispatch", "configure_provider", "The requested provider is not configured."],
    provider_call_not_implemented: ["provider_preflight", "none", "server_pre_dispatch", "choose_provider", "The requested provider adapter is not implemented."],
    provider_dispatch_invalid: ["dispatch", "none", "server_pre_dispatch", "inspect", "The provider dispatch request did not satisfy the execution contract."],
    codex_cli_missing: ["provider_preflight", "none", "server_pre_dispatch", "configure_provider", "The local Codex runtime is unavailable."],
    claude_code_cli_missing: ["provider_preflight", "none", "server_pre_dispatch", "configure_provider", "The local Claude Code runtime is unavailable."],
    unregistered_direct_execution_action: ["policy", "none", "server_pre_dispatch", "request_authorization", "The requested action is not registered for execution."],
    authorization_grant_invalid: ["policy", "none", "server_pre_dispatch", "request_authorization", "Execution authorization could not be verified."],
    authorization_grant_expired: ["policy", "none", "server_pre_dispatch", "request_authorization", "Execution authorization expired before dispatch."],
    runner_permission_boundary_failed: ["policy", "none", "server_pre_dispatch", "inspect", "Execution stopped because its permission boundary was unsafe."],
    filesystem_staging_invalid: ["policy", "none", "server_pre_dispatch", "inspect", "Artifact staging could not prove a safe filesystem boundary."],
    filesystem_staging_limit_exceeded: ["policy", "none", "server_pre_dispatch", "inspect", "The artifact exceeded the bounded staging limits."],
    filesystem_staging_conflict: ["execution", "confirmed", "provider_finished", "inspect", "Artifact promotion stopped because the target changed after preparation."],
    filesystem_promotion_failed: ["execution", "unknown", "provider_finished", "inspect", "Artifact promotion failed; inspect its filesystem receipt before continuing."],
    filesystem_compensation_failed: ["execution", "unknown", "provider_finished", "inspect", "Artifact compensation could not be verified; inspect the filesystem before continuing."],
    filesystem_rollback_invalid: ["execution", "none", "result_recorded", "inspect", "The artifact rollback receipt could not be verified."],
    filesystem_rollback_conflict: ["execution", "confirmed", "result_recorded", "inspect", "Rollback stopped because the artifact changed after its receipt was recorded."],
    runner_execution_failed: ["execution", "unknown", "provider_started", "inspect", "Execution failed after dispatch; inspect the run before trying again."],
    queue_execution_failed: ["execution", "unknown", "provider_started", "inspect", "The execution queue stopped; inspect item status before trying again."],
    runner_stale: ["execution", "unknown", "unknown", "inspect", "The run stopped reporting status; inspect it before trying again."],
    post_run_refresh_failed: ["projection", "confirmed", "result_recorded", "rebuild_projection", "Execution completed, but the derived projection did not refresh."],
    client_request_invalid: ["intake", "none", "client_pre_submit", "correct_request", "The client could not prepare a valid task request."],
    client_transport_unavailable: ["client_transport", "none", "client_pre_submit", "inspect", "The local transport is unavailable."],
    transport_delivery_unknown: ["client_transport", "unknown", "request_delivery_unknown", "inspect", "No server acknowledgement was received; inspect run status before trying again."],
    invalid_server_response: ["client_transport", "unknown", "request_delivery_unknown", "inspect", "The server response could not be verified; inspect run status before trying again."],
    submit_rejected: ["client_transport", "unknown", "request_delivery_unknown", "inspect", "No server acknowledgement was received; inspect run status before trying again."],
    runtime_failure: ["unknown", "unknown", "unknown", "inspect", "The task failed at an unknown point; inspect the run before trying again."],
    run_ledger_corrupt: ["normalization", "unknown", "unknown", "inspect", "The run ledger could not be verified."],
    run_ledger_unavailable: ["normalization", "unknown", "unknown", "inspect", "The run ledger is unavailable."],
    run_request_conflict: ["normalization", "unknown", "unknown", "inspect", "The request correlation conflicts with an existing run."],
    run_reconcile_ambiguous: ["normalization", "unknown", "unknown", "inspect", "The request matched more than one run; inspect the ledger."],
    run_reservation_invalid: ["normalization", "none", "server_pre_dispatch", "correct_request", "The run could not be reserved safely."],
    run_reservation_missing: ["normalization", "none", "server_pre_dispatch", "inspect", "The run reservation is missing."],
    run_state_transition_invalid: ["normalization", "unknown", "unknown", "inspect", "The run state transition was rejected."],
    run_reconcile_not_found: ["normalization", "none", "server_pre_dispatch", "retry_same", "No matching server run exists; the same request may be submitted again safely."],
  });

  const executionStatusForError = (error = {}) => DELIVERY_UNKNOWN_ERRORS.has(error.error_type)
    ? "delivery_unknown"
    : "failed";

  function text(value, maximum = 240) {
    return String(value || "").trim().slice(0, maximum);
  }

  function clientErrorId() {
    const fallback = `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`;
    const raw = String(global.crypto?.randomUUID?.() || fallback).replace(/[^0-9a-f]/gi, "").toLowerCase();
    return `error:client:${(raw + "0".repeat(32)).slice(0, 32)}`;
  }

  function errorEnvelope(errorType = "runtime_failure", options = {}) {
    const safeType = Object.hasOwn(ERROR_POLICIES, errorType) ? errorType : "runtime_failure";
    const policy = ERROR_POLICIES[safeType];
    const stage = STAGES.includes(options.stage) ? options.stage : policy[0];
    const sideEffects = policy[1] === "none" && ["unknown", "confirmed"].includes(options.side_effects)
      ? options.side_effects : policy[1];
    const lastSafePoint = LAST_SAFE_POINTS.includes(options.last_safe_point) ? options.last_safe_point : policy[2];
    let recoveryAction = RECOVERY_ACTIONS.includes(options.recovery_action) ? options.recovery_action : policy[3];
    if (recoveryAction === "retry_same" && (sideEffects !== "none" || policy[1] !== "none")) recoveryAction = policy[3];
    const retryable = (options.retryable === true || policy[3] === "retry_same")
      && sideEffects === "none" && recoveryAction === "retry_same";
    const errorId = /^error:server:[0-9a-f]{64}$|^error:client:[0-9a-f]{32}$/.test(String(options.error_id || ""))
      ? String(options.error_id)
      : clientErrorId();
    return {
      schema_id: ERROR_SCHEMA_ID,
      error_id: errorId,
      client_request_id: text(options.client_request_id, 160),
      task_id: text(options.task_id, 80),
      run_id: text(options.run_id, 160),
      error_type: safeType,
      stage,
      impact: options.impact === "warning" ? "warning" : "terminal",
      retryable,
      last_safe_point: lastSafePoint,
      side_effects: sideEffects,
      recovery_action: recoveryAction,
      message: policy[4],
    };
  }

  function normalizeError(value = {}, fallbackType = "runtime_failure") {
    const record = value && typeof value === "object" && !Array.isArray(value) ? value : {};
    return errorEnvelope(text(record.error_type, 120) || fallbackType, {
      client_request_id: record.client_request_id, error_id: record.error_id,
      run_id: record.run_id, task_id: record.task_id,
    });
  }

  function normalizeRefs(values = [], { candidate = false } = {}) {
    const seen = new Set();
    return (Array.isArray(values) ? values : []).map((value) => {
      const record = value && typeof value === "object" ? value : { ref: value };
      const ref = text(record.ref || record.path, candidate ? 240 : 2048);
      const kind = candidate ? "" : text(record.kind || "file", 40);
      const key = `${kind}\u0000${ref}`;
      if (!ref || seen.has(key)) return null;
      seen.add(key);
      return candidate ? { ref, state: "reported" } : { kind, ref, state: "reported" };
    }).filter(Boolean).slice(0, 40);
  }

  function normalizeResult(value = {}) {
    if (!value || typeof value !== "object" || value.schema_id !== RESULT_SCHEMA_ID || value.status !== "completed") return null;
    if (!text(value.run_id, 160) || !["private", "public_starter", "personal_vault"].includes(value.runtime_scope)) return null;
    const mode = RESULT_MODES.includes(value.result_mode) ? value.result_mode : "";
    const content = value.result && typeof value.result === "object" ? value.result : {};
    if (!mode || content.kind !== mode) return null;
    const result = mode === "answer"
      ? { kind: mode, text: String(content.text || "").slice(0, 24000) }
      : mode === "artifact"
        ? { kind: mode, text: String(content.text || "").slice(0, 24000), reported_refs: normalizeRefs(content.reported_refs) }
        : { kind: mode, text: String(content.text || "").slice(0, 24000), candidate_refs: normalizeRefs(content.candidate_refs, { candidate: true }) };
    const provider = value.provider_snapshot && typeof value.provider_snapshot === "object" ? value.provider_snapshot : {};
    const timing = value.timing && typeof value.timing === "object" ? value.timing : {};
    const usage = value.usage && typeof value.usage === "object" ? value.usage : {};
    const warnings = (Array.isArray(value.warnings) ? value.warnings : []).map((item) => normalizeError(item)).filter((item) => item.impact === "warning").slice(0, 8);
    return {
      schema_id: RESULT_SCHEMA_ID,
      client_request_id: text(value.client_request_id, 160), task_id: text(value.task_id, 80), run_id: text(value.run_id, 160),
      runtime_scope: value.runtime_scope,
      status: "completed", result_mode: mode, result,
      provider_snapshot: {
        provider: text(provider.provider || "codex", 120), model: text(provider.model, 240),
        reasoning_effort: text(provider.reasoning_effort, 80), task_complexity: text(provider.task_complexity, 80),
      },
      timing: {
        created_at: text(timing.created_at, 80), started_at: text(timing.started_at, 80), finished_at: text(timing.finished_at, 80),
        seconds: Math.max(0, Number(timing.seconds) || 0),
      },
      usage: {
        input_tokens: Math.max(0, Number(usage.input_tokens) || 0), cached_input_tokens: Math.max(0, Number(usage.cached_input_tokens) || 0),
        output_tokens: Math.max(0, Number(usage.output_tokens) || 0), reasoning_output_tokens: Math.max(0, Number(usage.reasoning_output_tokens) || 0),
      },
      error_ref: warnings[0]?.error_id || null, warnings,
    };
  }

  function plainRecord(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    try { return JSON.parse(JSON.stringify(value)); } catch { return {}; }
  }

  function providerStatus(value = {}) {
    const record = value && typeof value === "object" ? value : {};
    const allowed = [
      "ok", "provider", "selected_adapter", "type", "model", "runtime_mode", "public_starter_api",
      "execution_available", "execution_scope", "error_type", "message_zh", "message_en", "key_status",
    ];
    const safe = Object.fromEntries(allowed.filter((key) => ["boolean", "number", "string"].includes(typeof record[key])).map((key) => [key, record[key]]));
    const runtimeProfile = runtimeProfileContract?.normalize(record.runtime_profile);
    if (runtimeProfile) safe.runtime_profile = runtimeProfile;
    return safe;
  }

  function normalizeRun(value = {}) {
    const run = value && typeof value === "object" && !Array.isArray(value) ? value : {};
    const id = text(run.id, 160);
    const status = RUN_STATUSES.includes(run.status) ? run.status : "";
    if (!id || !status) return null;
    const hasResultEnvelope = Object.hasOwn(run, "result_envelope");
    const resultEnvelope = hasResultEnvelope ? normalizeResult(run.result_envelope) : null;
    if (hasResultEnvelope && (!resultEnvelope || status !== "completed"
      || resultEnvelope.run_id !== id || text(run.response_mode, 80) !== resultEnvelope.result_mode)) return null;
    const hasErrorEnvelope = Object.hasOwn(run, "error_envelope");
    if (hasErrorEnvelope && status !== "failed") return null;
    const error = status === "failed"
      ? normalizeError(hasErrorEnvelope ? run.error_envelope : { error_type: run.error_type, run_id: id }, text(run.error_type, 120) || "runner_execution_failed")
      : null;
    if (hasErrorEnvelope && (!error.run_id || error.run_id !== id)) return null;
    const rawRef = run.task_envelope_ref && typeof run.task_envelope_ref === "object" ? run.task_envelope_ref : {};
    if (text(rawRef.run_id, 160) && text(rawRef.run_id, 160) !== id) return null;
    if (resultEnvelope && text(rawRef.task_id, 80) && resultEnvelope.task_id !== text(rawRef.task_id, 80)) return null;
    const fields = [
      "id", "task_mode", "response_mode", "work_session_id", "title", "created_at", "updated_at", "started_at", "finished_at",
      "returncode", "seconds", "task_complexity", "task_complexity_mode", "recommended_task_complexity", "model", "model_mode",
      "provider", "reasoning_effort", "reasoning_effort_mode", "recommended_reasoning_effort", "parent_id", "entry_type", "entry_id",
      "action_key", "queue_index", "queue_total", "queue_completed", "queue_failed", "current_item_id", "current_action_key", "current_queue_index",
    ];
    const safe = Object.fromEntries(fields.filter((key) => ["boolean", "number", "string"].includes(typeof run[key])).map((key) => [key, run[key]]));
    safe.status = status;
    safe.client_request_id = text(
      resultEnvelope?.client_request_id || error?.client_request_id || run.client_request_id || rawRef.client_request_id, 160);
    safe.lease_expired = run.lease_expired === true;
    safe.provider_status = providerStatus(run.provider_status);
    const usage = run.usage && typeof run.usage === "object" ? run.usage : {};
    safe.usage = Object.fromEntries(["input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"]
      .map((key) => [key, Math.max(0, Number(usage[key]) || 0)]));
    const refresh = run.post_run_refresh && typeof run.post_run_refresh === "object" ? run.post_run_refresh : {};
    safe.post_run_refresh = {
      attempted: refresh.attempted === true, ok: refresh.ok === true,
      error_type: text(refresh.error_type, 120),
    };
    safe.candidate = plainRecord(run.candidate);
    const envelopeRef = rawRef;
    safe.task_envelope_ref = Object.fromEntries(["client_request_id", "task_id", "run_id", "idempotency_key", "envelope_digest"]
      .map((key) => [key, text(envelopeRef[key], 160)]).filter(([, value]) => value));
    if (resultEnvelope) {
      safe.result_envelope = resultEnvelope;
      safe.answer = resultEnvelope.result.text;
      safe.artifacts = resultEnvelope.result.kind === "artifact"
        ? resultEnvelope.result.reported_refs.map(({ kind, ref }) => ({ kind, path: ref }))
        : [];
      safe.output = "";
    } else if (status === "completed") {
      safe.answer = String(run.answer || "").slice(0, 24000);
      safe.artifacts = (Array.isArray(run.artifacts) ? run.artifacts : []).slice(0, 40);
      safe.output = String(run.output || "").slice(-24000);
    }
    if (error) {
      safe.candidate = {};
      safe.error_envelope = error;
      safe.error_type = error.error_type;
      safe.message = error.message;
      safe.execution_status = executionStatusForError(error);
      safe.answer = ""; safe.artifacts = []; safe.output = "";
    } else {
      safe.execution_status = text(run.execution_status, 80);
    }
    return safe;
  }

  function normalizeSubmitResponse(body = {}, { httpOk = false, httpStatus = 0 } = {}) {
    const record = body && typeof body === "object" && !Array.isArray(body) ? body : {};
    if (!httpOk) {
      const error = errorEnvelope("invalid_server_response");
      return { ok: false, status: Number(httpStatus) || 0, error_type: error.error_type, error_envelope: error, provider_status: {}, retryable: false };
    }
    if (httpOk && record.ok === true && record.run && typeof record.run === "object") {
      const run = normalizeRun(record.run);
      if (!run || !["submitted", "queued", "running", "completed"].includes(run.status)) {
        const error = errorEnvelope("invalid_server_response");
        return { ok: false, status: Number(httpStatus) || 0, error_type: error.error_type, error_envelope: error, provider_status: {}, retryable: false };
      }
      return {
        ok: true, status: Number(httpStatus) || 200, run,
        runs: (Array.isArray(record.runs) ? record.runs : []).map(normalizeRun).filter(Boolean),
      };
    }
    const error = normalizeError(record.error_envelope, text(record.error_type, 120) || "invalid_server_response");
    return { ok: false, status: Number(httpStatus) || 0, error_type: error.error_type, error_envelope: error, provider_status: providerStatus(record.provider_status), retryable: error.retryable };
  }

  function failureResult(errorOrType = "runtime_failure", options = {}) {
    const error = typeof errorOrType === "string" ? errorEnvelope(errorOrType, options) : normalizeError(errorOrType);
    return {
      ok: false, persistResult: true, error_type: error.error_type, error_envelope: error, retryable: error.retryable,
      run: {
        error_envelope: error,
        execution_status: executionStatusForError(error),
        ...(error.run_id ? { id: error.run_id } : {}),
        response_mode: RESULT_MODES.includes(options.response_mode) ? options.response_mode : "answer",
        status: "failed",
        work_session_id: text(options.work_session_id, 240),
      },
    };
  }

  global.ResearchOSResultEnvelope = Object.freeze({
    ERROR_SCHEMA_ID, RESULT_MODES, RESULT_SCHEMA_ID, errorEnvelope, failureResult, normalizeError,
    normalizeResult, normalizeRun, normalizeSubmitResponse, providerStatus,
  });
})(window);
