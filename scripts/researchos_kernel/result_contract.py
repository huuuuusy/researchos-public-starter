# ResearchOS maintenance header.
# 中文：ResultEnvelope / ErrorEnvelope v1 的唯一内核 owner；结果形态、运行失败与 authority 保持正交。
# English: Sole kernel owner for ResultEnvelope / ErrorEnvelope v1; result shape, runtime failure, and authority stay orthogonal.

"""Public-safe result and error contracts for every ResearchOS execution client."""

from __future__ import annotations


from .ledger import digest as _digest


RESULT_ENVELOPE_SCHEMA_ID = "researchos-result-envelope-v1"
ERROR_ENVELOPE_SCHEMA_ID = "researchos-error-envelope-v1"
RESULT_MODES = frozenset({"answer", "artifact", "writeback"})
RUN_STATUSES = frozenset({"submitted", "queued", "running", "completed", "failed"})
RUNTIME_SCOPES = frozenset({"private", "public_starter", "personal_vault"})
ERROR_STAGES = frozenset({
    "intake", "normalization", "policy", "provider_preflight", "dispatch",
    "execution", "result_normalization", "projection", "client_transport", "unknown",
})
LAST_SAFE_POINTS = frozenset({
    "client_pre_submit", "request_delivery_unknown", "server_pre_dispatch", "server_queued",
    "provider_started", "provider_finished", "result_recorded", "effects_confirmed", "unknown",
})
RECOVERY_ACTIONS = frozenset({
    "correct_request", "choose_provider", "configure_provider", "copy_task", "inspect",
    "rebuild_projection", "request_authorization", "retry_same", "wait", "none",
})

_ERROR_POLICIES: dict[str, tuple[str, str, str, str, str, str]] = {
    "public_starter_copy_only": ("policy", "terminal", "none", "server_pre_dispatch", "copy_task", "Execution is disabled in this runtime."),
    "task_intent_invalid_shape": ("normalization", "terminal", "none", "server_pre_dispatch", "correct_request", "The task request did not match the supported contract."),
    "task_intent_schema_mismatch": ("normalization", "terminal", "none", "server_pre_dispatch", "correct_request", "The task request used an unsupported contract version."),
    "task_intent_invalid_trust": ("normalization", "terminal", "none", "server_pre_dispatch", "correct_request", "The task request contained an invalid trust declaration."),
    "task_intent_invalid_character": ("normalization", "terminal", "none", "server_pre_dispatch", "correct_request", "The task request contained an unsupported character."),
    "task_intent_input_too_large": ("normalization", "terminal", "none", "server_pre_dispatch", "correct_request", "The task request exceeded the supported size."),
    "task_intent_invalid_value": ("normalization", "terminal", "none", "server_pre_dispatch", "correct_request", "The task request contained an unsupported value."),
    "unsupported_result_mode": ("normalization", "terminal", "none", "server_pre_dispatch", "correct_request", "The requested result mode is unsupported."),
    "unsupported_reasoning_effort": ("normalization", "terminal", "none", "server_pre_dispatch", "correct_request", "The requested reasoning effort is unsupported."),
    "unsupported_task_complexity": ("normalization", "terminal", "none", "server_pre_dispatch", "correct_request", "The requested task complexity is unsupported."),
    "runtime_profile_unknown": ("provider_preflight", "terminal", "none", "server_pre_dispatch", "choose_provider", "The requested runtime profile is unknown."),
    "runtime_profile_disabled": ("provider_preflight", "terminal", "none", "server_pre_dispatch", "choose_provider", "The requested runtime profile is disabled."),
    "runtime_profile_scope_forbidden": ("policy", "terminal", "none", "server_pre_dispatch", "choose_provider", "The requested runtime profile is unavailable in this runtime scope."),
    "runtime_profile_model_not_allowed": ("provider_preflight", "terminal", "none", "server_pre_dispatch", "choose_provider", "The requested model is not allowed by the selected runtime profile."),
    "runtime_profile_reasoning_not_allowed": ("provider_preflight", "terminal", "none", "server_pre_dispatch", "choose_provider", "The requested reasoning effort is not allowed by the selected runtime profile."),
    "unknown_provider": ("provider_preflight", "terminal", "none", "server_pre_dispatch", "choose_provider", "The requested provider is unknown."),
    "provider_not_configured": ("provider_preflight", "terminal", "none", "server_pre_dispatch", "configure_provider", "The requested provider is not configured."),
    "provider_call_not_implemented": ("provider_preflight", "terminal", "none", "server_pre_dispatch", "choose_provider", "The requested provider adapter is not implemented."),
    "provider_dispatch_invalid": ("dispatch", "terminal", "none", "server_pre_dispatch", "inspect", "The provider dispatch request did not satisfy the execution contract."),
    "provider_cancel_unsupported": ("provider_preflight", "terminal", "none", "server_pre_dispatch", "inspect", "This provider adapter does not support cancellation."),
    "codex_cli_missing": ("provider_preflight", "terminal", "none", "server_pre_dispatch", "configure_provider", "The local Codex runtime is unavailable."),
    "claude_code_cli_missing": ("provider_preflight", "terminal", "none", "server_pre_dispatch", "configure_provider", "The local Claude Code runtime is unavailable."),
    "unregistered_direct_execution_action": ("policy", "terminal", "none", "server_pre_dispatch", "request_authorization", "The requested action is not registered for execution."),
    "authorization_grant_invalid": ("policy", "terminal", "none", "server_pre_dispatch", "request_authorization", "Execution authorization could not be verified."),
    "authorization_grant_expired": ("policy", "terminal", "none", "server_pre_dispatch", "request_authorization", "Execution authorization expired before dispatch."),
    "runner_permission_boundary_failed": ("policy", "terminal", "none", "server_pre_dispatch", "inspect", "Execution stopped because its permission boundary was unsafe."),
    "runner_boundary_unavailable": ("policy", "terminal", "none", "server_pre_dispatch", "inspect", "The launch boundary could not be built, so nothing was started."),
    "filesystem_staging_invalid": ("policy", "terminal", "none", "server_pre_dispatch", "inspect", "Artifact staging could not prove a safe filesystem boundary."),
    "filesystem_staging_limit_exceeded": ("policy", "terminal", "none", "server_pre_dispatch", "inspect", "The artifact exceeded the bounded staging limits."),
    "filesystem_staging_conflict": ("execution", "terminal", "confirmed", "provider_finished", "inspect", "Artifact promotion stopped because the target changed after preparation."),
    "filesystem_promotion_failed": ("execution", "terminal", "unknown", "provider_finished", "inspect", "Artifact promotion failed; inspect its filesystem receipt before continuing."),
    "filesystem_compensation_failed": ("execution", "terminal", "unknown", "provider_finished", "inspect", "Artifact compensation could not be verified; inspect the filesystem before continuing."),
    "filesystem_rollback_invalid": ("execution", "terminal", "none", "result_recorded", "inspect", "The artifact rollback receipt could not be verified."),
    "filesystem_rollback_conflict": ("execution", "terminal", "confirmed", "result_recorded", "inspect", "Rollback stopped because the artifact changed after its receipt was recorded."),
    "runner_execution_failed": ("execution", "terminal", "unknown", "provider_started", "inspect", "Execution failed after dispatch; inspect the run before trying again."),
    "queue_execution_failed": ("execution", "terminal", "unknown", "provider_started", "inspect", "The execution queue stopped; inspect item status before trying again."),
    "runner_stale": ("execution", "terminal", "unknown", "unknown", "inspect", "The run stopped reporting status; inspect it before trying again."),
    "post_run_refresh_failed": ("projection", "warning", "confirmed", "result_recorded", "rebuild_projection", "Execution completed, but the derived projection did not refresh."),
    "result_normalization_failed": ("result_normalization", "terminal", "unknown", "provider_finished", "inspect", "Execution returned without a valid result contract."),
    "client_request_invalid": ("intake", "terminal", "none", "client_pre_submit", "correct_request", "The client could not prepare a valid task request."),
    "client_transport_unavailable": ("client_transport", "terminal", "none", "client_pre_submit", "inspect", "The local transport is unavailable."),
    "transport_delivery_unknown": ("client_transport", "terminal", "unknown", "request_delivery_unknown", "inspect", "No server acknowledgement was received; inspect run status before trying again."),
    "invalid_server_response": ("client_transport", "terminal", "unknown", "request_delivery_unknown", "inspect", "The server response could not be verified; inspect run status before trying again."),
    "submit_rejected": ("client_transport", "terminal", "unknown", "request_delivery_unknown", "inspect", "No server acknowledgement was received; inspect run status before trying again."),
    "runtime_failure": ("unknown", "terminal", "unknown", "unknown", "inspect", "The task failed at an unknown point; inspect the run before trying again."),
    "run_ledger_corrupt": ("normalization", "terminal", "unknown", "unknown", "inspect", "The run ledger could not be verified."),
    "run_ledger_unavailable": ("normalization", "terminal", "unknown", "unknown", "inspect", "The run ledger is unavailable."),
    "run_request_conflict": ("normalization", "terminal", "unknown", "unknown", "inspect", "The request correlation conflicts with an existing run."),
    "run_reconcile_ambiguous": ("normalization", "terminal", "unknown", "unknown", "inspect", "The request matched more than one run; inspect the ledger."),
    "run_reservation_invalid": ("normalization", "terminal", "none", "server_pre_dispatch", "correct_request", "The run could not be reserved safely."),
    "run_reservation_missing": ("normalization", "terminal", "none", "server_pre_dispatch", "inspect", "The run reservation is missing."),
    "run_state_transition_invalid": ("normalization", "terminal", "unknown", "unknown", "inspect", "The run state transition was rejected."),
}
# Errors raised before anything is dispatched: nothing was sent, so no side effect can have happened.
PRE_DISPATCH_ERRORS = frozenset(code for code, policy in _ERROR_POLICIES.items() if policy[3] == "server_pre_dispatch")


def _text(value: object, maximum: int) -> str:
    return str(value or "").strip()[:maximum]


def _correlation(run: object) -> dict[str, str]:
    record = run if isinstance(run, dict) else {}
    envelope = record.get("task_envelope") if isinstance(record.get("task_envelope"), dict) else {}
    reference = record.get("task_envelope_ref") if isinstance(record.get("task_envelope_ref"), dict) else {}
    client = envelope.get("client") if isinstance(envelope.get("client"), dict) else {}
    return {
        "client_request_id": _text(client.get("request_id") or reference.get("client_request_id"), 160),
        "task_id": _text(envelope.get("task_id") or reference.get("task_id"), 80),
        "run_id": _text(record.get("id") or envelope.get("run_id") or reference.get("run_id"), 160),
    }


def build_error_envelope(
    error_type: object,
    *,
    run: object = None,
    stage: str | None = None,
    impact: str | None = None,
    side_effects: str | None = None,
    last_safe_point: str | None = None,
    recovery_action: str | None = None,
    retryable: bool | None = None,
) -> dict[str, object]:
    """Build a bounded failure receipt without copying raw exception text."""
    requested = _text(error_type, 120)
    safe_type = requested if requested in _ERROR_POLICIES else "runtime_failure"
    policy = _ERROR_POLICIES[safe_type]
    safe_stage = stage if stage in ERROR_STAGES else policy[0]
    safe_impact = impact if impact in {"terminal", "warning"} else policy[1]
    safe_effects = side_effects if policy[2] == "none" and side_effects in {"unknown", "confirmed"} else policy[2]
    safe_point = last_safe_point if last_safe_point in LAST_SAFE_POINTS else policy[3]
    provider_locked = safe_type == "provider_cancel_unsupported"
    safe_recovery = policy[4] if provider_locked else (
        recovery_action if recovery_action in RECOVERY_ACTIONS else policy[4]
    )
    if safe_recovery == "retry_same" and (safe_effects != "none" or policy[2] != "none"):
        safe_recovery = policy[4]
    safe_retryable = bool(retryable) and not provider_locked
    if safe_effects != "none" or safe_recovery != "retry_same":
        safe_retryable = False
    correlation = _correlation(run)
    identity = {"correlation": correlation, "error_type": safe_type, "stage": safe_stage, "last_safe_point": safe_point}
    return {
        "schema_id": ERROR_ENVELOPE_SCHEMA_ID,
        "error_id": f"error:server:{_digest(identity)}",
        **correlation,
        "error_type": safe_type,
        "stage": safe_stage,
        "impact": safe_impact,
        "retryable": safe_retryable,
        "last_safe_point": safe_point,
        "side_effects": safe_effects,
        "recovery_action": safe_recovery,
        "message": policy[5],
    }


def normalize_error_envelope(value: object) -> dict[str, object] | None:
    """Rebuild an envelope through the invariant owner; never trust serialized claims."""
    if not isinstance(value, dict) or value.get("schema_id") != ERROR_ENVELOPE_SCHEMA_ID:
        return None
    run = {
        "id": value.get("run_id", ""),
        "task_envelope_ref": {"task_id": value.get("task_id", "")},
        "task_envelope": {"client": {"request_id": value.get("client_request_id", "")}},
    }
    return build_error_envelope(value.get("error_type"), run=run)


def failure_response(source: object, *, run: object = None) -> dict[str, object]:
    """Adapt a legacy early failure to the additive ErrorEnvelope v1 response."""
    record = source if isinstance(source, dict) else {}
    envelope = normalize_error_envelope(record.get("error_envelope")) or build_error_envelope(
        record.get("error_type") or "runtime_failure", run=run
    )
    response: dict[str, object] = {
        "ok": False,
        "error_type": envelope["error_type"],
        "error_envelope": envelope,
    }
    if isinstance(record.get("provider_status"), dict):
        response["provider_status"] = record["provider_status"]
    for key in ("contract", "field"):
        if isinstance(record.get(key), str):
            response[key] = _text(record[key], 240)
    return response


def _usage(value: object) -> dict[str, int]:
    record = value if isinstance(value, dict) else {}
    keys = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
    return {key: max(0, int(record.get(key, 0) or 0)) for key in keys}


def _reported_refs(run: dict[str, object]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    values = run.get("artifacts") if isinstance(run.get("artifacts"), list) else run.get("changed_files", [])
    for item in values if isinstance(values, list) else []:
        kind = _text(item.get("kind"), 40) if isinstance(item, dict) else "file"
        ref = _text(item.get("path"), 2048) if isinstance(item, dict) else _text(item, 2048)
        identity = (kind or "file", ref)
        if ref and identity not in seen:
            seen.add(identity)
            refs.append({"kind": kind or "file", "ref": ref, "state": "reported"})
    return refs[:40]


def _candidate_refs(run: dict[str, object]) -> list[dict[str, str]]:
    candidate = run.get("candidate") if isinstance(run.get("candidate"), dict) else {}
    value = _text(candidate.get("candidate_id") or candidate.get("id"), 240)
    return [{"ref": value, "state": "reported"}] if value else []


def build_result_envelope(
    run: object,
    *,
    runtime_scope: str,
    stale: bool = False,
) -> dict[str, object] | None:
    """Project one completed server run without owning the B7 run-state machine."""
    if runtime_scope not in RUNTIME_SCOPES:
        raise ValueError("Invalid result runtime scope")
    record = run if isinstance(run, dict) else {}
    raw_status = "failed" if stale else _text(record.get("status") or "queued", 40)
    status = raw_status if raw_status in RUN_STATUSES else "failed"
    raw_mode = _text(record.get("response_mode") or "answer", 40)
    if raw_mode == "copy_ready":
        raise ValueError("copy_ready is a handoff state, not a machine result")
    result_mode = raw_mode if raw_mode in RESULT_MODES else "answer"
    correlation = _correlation(record)
    if status != "completed":
        return None
    result: dict[str, object]
    warnings: list[dict[str, object]] = []
    answer = str(record.get("answer") or "")[:24000]
    if result_mode == "answer":
        result = {"kind": "answer", "text": answer}
    elif result_mode == "artifact":
        result = {"kind": "artifact", "text": answer, "reported_refs": _reported_refs(record)}
    else:
        result = {"kind": "writeback", "text": answer, "candidate_refs": _candidate_refs(record)}
    refresh = record.get("post_run_refresh") if isinstance(record.get("post_run_refresh"), dict) else {}
    if refresh and refresh.get("ok") is False:
        warnings.append(build_error_envelope("post_run_refresh_failed", run=record))
    return {
        "schema_id": RESULT_ENVELOPE_SCHEMA_ID,
        **correlation,
        "runtime_scope": runtime_scope,
        "status": status,
        "result_mode": result_mode,
        "result": result,
        "provider_snapshot": {
            "provider": _text(record.get("provider") or "codex", 120),
            "model": _text(record.get("model"), 240),
            "reasoning_effort": _text(record.get("reasoning_effort"), 80),
            "task_complexity": _text(record.get("task_complexity"), 80),
        },
        "timing": {
            "created_at": _text(record.get("created_at"), 80),
            "started_at": _text(record.get("started_at"), 80),
            "finished_at": _text(record.get("finished_at"), 80),
            "seconds": max(0.0, float(record.get("seconds", 0) or 0)),
        },
        "usage": _usage(record.get("usage")),
        "error_ref": warnings[0]["error_id"] if warnings else None,
        "warnings": warnings,
    }


def result_projection(run: object, *, runtime_scope: str, stale: bool = False) -> dict[str, object]:
    """Add v1 envelopes while retaining the legacy flat projection during migration."""
    record = dict(run) if isinstance(run, dict) else {}
    envelope = build_result_envelope(record, runtime_scope=runtime_scope, stale=stale)
    if envelope:
        record["result_envelope"] = envelope
    elif str(record.get("status")) == "failed" or stale:
        error = normalize_error_envelope(record.get("error_envelope")) or build_error_envelope(
            "runner_stale" if stale else record.get("error_type") or "runner_execution_failed", run=record
        )
        record.update({
            "answer": "", "artifacts": [], "changed_files": [], "change_summary": [],
            "error_envelope": error, "error_type": error["error_type"], "message": error["message"], "output": "",
        })
    return record
