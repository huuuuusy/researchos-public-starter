/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「Codex runner client」；只负责本地 runner HTTP 调用，不持久化长期状态。
 * English: Frontend service for the Codex runner client in the ResearchOS dashboard; owns local runner HTTP calls without durable memory writes.
 */

(function attachResearchOSCodexRunnerClient(global) {
  const resultContract = global.ResearchOSResultEnvelope;

  function clientFailure(errorType, options = {}) {
    const error = resultContract.errorEnvelope(errorType, options);
    return { ok: false, status: Number(options.status) || 0, error_type: error.error_type, error_envelope: error, retryable: error.retryable };
  }

  function requestCorrelation(payload = {}) {
    return String(payload?.task_intent?.client_request_id || "").trim().slice(0, 160);
  }

  async function responseBody(response) {
    try {
      const body = await response.json();
      return { body: body && typeof body === "object" && !Array.isArray(body) ? body : {}, parsed: true };
    } catch {
      return { body: {}, parsed: false };
    }
  }

  async function submitCodexRun(payload = {}, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") {
      return clientFailure("client_transport_unavailable");
    }
    let body;
    try {
      body = JSON.stringify(payload || {});
    } catch {
      return clientFailure("client_request_invalid");
    }
    try {
      // 中文：Codex runner 是执行交接面；真正写回必须由本地流程产生 diff 并通过验证。
      // English: The Codex runner is an execution handoff surface; durable writeback must come through local diffs and validation.
      const response = await fetcher("/codex-runner", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        cache: "no-store",
      });
      const parsed = await responseBody(response);
      if (!parsed.parsed) return clientFailure("invalid_server_response", {
        client_request_id: requestCorrelation(payload), status: response.status,
      });
      return resultContract.normalizeSubmitResponse(parsed.body, { httpOk: response.ok, httpStatus: response.status });
    } catch {
      return clientFailure("transport_delivery_unknown", { client_request_id: requestCorrelation(payload) });
    }
  }

  async function loadCodexRuns({ limit = 12, clientRequestId = "", idempotencyKey = "" } = {}, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") {
      return { ...clientFailure("client_transport_unavailable"), runs: [] };
    }
    try {
      // 中文：runner 历史是运行态观察面，不能被 public starter 或 confirmed memory 复用。
      // English: Runner history is runtime observability state, not reusable public-starter or confirmed-memory content.
      const safeLimit = Math.max(1, Math.min(Number(limit) || 12, 80));
      const query = new URLSearchParams({ limit: String(safeLimit) });
      if (clientRequestId) query.set("client_request_id", String(clientRequestId).slice(0, 160));
      if (idempotencyKey) query.set("idempotency_key", String(idempotencyKey).slice(0, 80));
      const response = await fetcher(`/codex-runner?${query.toString()}`, {
        cache: "no-store",
      });
      const parsed = await responseBody(response);
      if (parsed.parsed && response.ok && parsed.body.ok === false && parsed.body.error_envelope) {
        const error = resultContract.normalizeError(parsed.body.error_envelope, parsed.body.error_type);
        return { ok: false, status: response.status, error_type: error.error_type, error_envelope: error, retryable: false, runs: [] };
      }
      if (!parsed.parsed || !response.ok || parsed.body.ok !== true || !Array.isArray(parsed.body.runs)) {
        const failure = clientFailure("invalid_server_response", {
          last_safe_point: "client_pre_submit", recovery_action: "inspect", side_effects: "none", status: response.status,
        });
        return { ...failure, runs: [] };
      }
      const rawReconciliation = parsed.body.reconciliation && typeof parsed.body.reconciliation === "object"
        ? parsed.body.reconciliation : {};
      return {
        ok: true, status: response.status,
        runs: parsed.body.runs.map(resultContract.normalizeRun).filter(Boolean),
        count: Math.max(0, Number(parsed.body.count) || 0),
        provider_status: resultContract.providerStatus(parsed.body.provider_status),
        reconciliation: {
          state: ["matched", "not_found"].includes(rawReconciliation.state) ? rawReconciliation.state : "",
          client_request_id: String(rawReconciliation.client_request_id || "").slice(0, 160),
          idempotency_key: String(rawReconciliation.idempotency_key || "").slice(0, 80),
          run_id: String(rawReconciliation.run_id || "").slice(0, 160),
        },
      };
    } catch {
      return { ...clientFailure("client_transport_unavailable"), runs: [] };
    }
  }

  async function loadModelCatalog({ publicStarter = false, refresh = false } = {}, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") {
      return { ...clientFailure("client_transport_unavailable"), models: [] };
    }
    try {
      const query = new URLSearchParams({
        public_starter: publicStarter ? "true" : "false",
        refresh: refresh ? "true" : "false",
      });
      const response = await fetcher(`/model-catalog?${query.toString()}`, { cache: "no-store" });
      const parsed = await responseBody(response);
      if (!parsed.parsed || !response.ok || parsed.body.ok !== true || !Array.isArray(parsed.body.models)) {
        return { ...clientFailure("invalid_server_response", {
          last_safe_point: "client_pre_submit", recovery_action: "inspect", side_effects: "none", status: response.status,
        }), models: [] };
      }
      const allowed = ["configured_default_model", "discovery", "provider", "recommended_model", "refreshed_at"];
      return {
        ...Object.fromEntries(allowed.filter((key) => typeof parsed.body[key] === "string").map((key) => [key, parsed.body[key]])),
        ok: true, status: response.status,
        models: parsed.body.models.filter((model) => model && typeof model === "object").map((model) => ({
          available: model.available !== false,
          default_reasoning_effort: String(model.default_reasoning_effort || "").slice(0, 80),
          description: String(model.description || "").slice(0, 500),
          id: String(model.id || "").slice(0, 240),
          label: String(model.label || model.id || "").slice(0, 240),
          priority: Number(model.priority) || 0,
          reasoning_efforts: (Array.isArray(model.reasoning_efforts) ? model.reasoning_efforts : []).map(String).slice(0, 12),
        })).filter((model) => model.id),
      };
    } catch {
      return { ...clientFailure("client_transport_unavailable"), models: [] };
    }
  }

  global.ResearchOSCodexRunnerClient = Object.freeze({
    loadCodexRuns,
    loadModelCatalog,
    submitCodexRun,
  });
})(window);
