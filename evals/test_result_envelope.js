const assert = require("node:assert/strict");
const vm = require("node:vm");

const { read } = require("./helpers/dashboard-vm.js");
const context = {
  URLSearchParams,
  console,
  crypto: { randomUUID: () => "12345678-1234-4234-8234-123456789abc" },
  ResearchOSRequestAuth: { resolveFetcher(candidate) { return candidate; } },
};
context.window = context;
vm.runInNewContext(read("dashboard/src/services/result-envelope.js"), context);
vm.runInNewContext(read("dashboard/src/services/codex-runner-client.js"), context);

const contract = context.ResearchOSResultEnvelope;
const client = context.ResearchOSCodexRunnerClient;

const unknown = contract.errorEnvelope("transport_delivery_unknown", {
  retryable: true, recovery_action: "retry_same", side_effects: "unknown",
});
assert.equal(unknown.retryable, false, "delivery unknown cannot be retried before B7 dedupe/reconcile");
assert.equal(unknown.recovery_action, "inspect");
assert.equal(unknown.run_id, "", "the browser must not manufacture a server run id");
const forgedUnknown = contract.normalizeError({
  ...unknown, side_effects: "none", recovery_action: "retry_same", retryable: true,
});
assert.equal(forgedUnknown.side_effects, "unknown", "serialized risk claims cannot downgrade policy");
assert.equal(forgedUnknown.recovery_action, "inspect");
assert.equal(forgedUnknown.retryable, false);

const completed = contract.normalizeResult({
  schema_id: "researchos-result-envelope-v1",
  client_request_id: "request-1", task_id: "task:one", run_id: "run-1", runtime_scope: "private",
  status: "completed", result_mode: "artifact",
  result: { kind: "artifact", text: "Done", reported_refs: [{ kind: "file", ref: "output.md", state: "verified" }] },
  provider_snapshot: { provider: "codex", model: "gpt", reasoning_effort: "medium", task_complexity: "standard" },
  timing: { created_at: "", started_at: "", finished_at: "", seconds: 1 }, usage: {}, warnings: [],
});
assert.equal(completed.result.reported_refs[0].state, "reported", "client data cannot upgrade reported refs to verified");
assert.equal(contract.normalizeResult({ ...completed, status: "failed" }), null, "failed runs are not ResultEnvelopes");
assert.equal(contract.normalizeResult({ ...completed, runtime_scope: "forged" }), null, "runtime scope cannot silently default to private");

async function attacks() {
  const maliciousResponse = {
    ok: false,
    status: 503,
    async json() { return { ok: true, status: 200, runs: "evil", models: "evil", message: "sensitive-diagnostic::token" }; },
  };
  const submit = await client.submitCodexRun({ prompt: "bounded" }, { fetcher: async () => maliciousResponse });
  assert.equal(submit.ok, false);
  assert.equal(submit.status, 503, "body status cannot override HTTP truth");
  assert.equal(submit.error_type, "invalid_server_response");
  assert.equal(JSON.stringify(submit).includes("sensitive-diagnostic::token"), false);

  const forgedHttpFailure = await client.submitCodexRun({}, { fetcher: async () => ({
    ok: false, status: 503, async json() {
      return {
        ok: false,
        error_envelope: contract.errorEnvelope("client_request_invalid", {
          retryable: true, recovery_action: "retry_same", side_effects: "none",
        }),
      };
    },
  }) });
  assert.equal(forgedHttpFailure.error_type, "invalid_server_response", "a non-2xx POST cannot self-declare a safe retry");
  assert.equal(forgedHttpFailure.retryable, false);

  const malformedSuccess = await client.submitCodexRun({}, { fetcher: async () => ({
    ok: true, status: 200, async json() { return { ok: true, run: {} }; },
  }) });
  assert.equal(malformedSuccess.error_type, "invalid_server_response", "a success response requires a real server run reference");

  const forgedAck = await client.submitCodexRun({}, { fetcher: async () => ({
    ok: true, status: 200, async json() {
      return { ok: false, error_envelope: {
        ...unknown, side_effects: "none", recovery_action: "retry_same", retryable: true,
      } };
    },
  }) });
  assert.equal(forgedAck.error_type, "transport_delivery_unknown");
  assert.equal(forgedAck.error_envelope.side_effects, "unknown");
  assert.equal(forgedAck.retryable, false, "an acknowledged body cannot forge safe retry semantics");

  const status = await client.loadCodexRuns({}, { fetcher: async () => maliciousResponse });
  assert.equal(status.ok, false);
  assert.equal(status.status, 503);
  assert.equal(status.runs.length, 0);

  const catalog = await client.loadModelCatalog({}, { fetcher: async () => maliciousResponse });
  assert.equal(catalog.ok, false);
  assert.equal(catalog.status, 503);
  assert.equal(catalog.models.length, 0);

  const secretFailure = await client.submitCodexRun({}, {
    fetcher: async () => { throw new Error("network sensitive-diagnostic::private-token"); },
  });
  assert.equal(secretFailure.error_type, "transport_delivery_unknown");
  assert.equal(secretFailure.retryable, false);
  assert.equal(JSON.stringify(secretFailure).includes("private-token"), false);

  const invalidJson = await client.submitCodexRun({}, {
    fetcher: async () => ({ ok: true, status: 200, async json() { throw new Error("secret parse"); } }),
  });
  assert.equal(invalidJson.error_type, "invalid_server_response");
  assert.equal(invalidJson.error_envelope.side_effects, "unknown");

  const failedRun = contract.normalizeRun({
    id: "run-failed", status: "failed", answer: "secret answer", output: "secret output", message: "secret message",
    candidate: { summary: "secret candidate" }, post_run_refresh: { output: "secret refresh" },
    error_envelope: contract.errorEnvelope("runner_execution_failed", { run_id: "run-failed" }),
  });
  assert.equal(failedRun.answer, "");
  assert.equal(failedRun.output, "");
  assert.equal(failedRun.execution_status, "failed", "a server-observed runner failure must not be mislabeled as unknown request delivery");
  assert.equal(JSON.stringify(failedRun).includes("secret"), false);
  assert.equal(contract.failureResult("transport_delivery_unknown").run.execution_status, "delivery_unknown");
  assert.equal(contract.failureResult("runner_execution_failed").run.execution_status, "failed");

  for (const [label, run] of Object.entries({
    queued_with_result: { id: "outer", status: "queued", response_mode: "artifact", result_envelope: completed },
    mismatched_run: { id: "outer", status: "completed", response_mode: "artifact", result_envelope: completed },
    mismatched_mode: { id: "run-1", status: "completed", response_mode: "answer", result_envelope: completed },
    mismatched_error: {
      id: "outer", status: "failed",
      error_envelope: contract.errorEnvelope("runner_execution_failed", { run_id: "different" }),
    },
  })) {
    assert.equal(contract.normalizeRun(run), null, `${label} must fail closed instead of mixing outer and nested state`);
  }

  const list = await client.loadCodexRuns({}, { fetcher: async () => ({
    ok: true, status: 200, async json() { return { ok: true, runs: [{}, { id: "run-ok", status: "completed" }] }; },
  }) });
  assert.equal(list.runs.length, 1, "invalid history records must not become synthetic failed runs");
  assert.equal(list.runs[0].id, "run-ok");

  let exactStatusUrl = "";
  const exactStatus = await client.loadCodexRuns({ clientRequestId: "request exact", limit: 2 }, {
    fetcher: async (url) => {
      exactStatusUrl = url;
      return { ok: true, status: 200, async json() {
        return { ok: true, runs: [], count: 0, reconciliation: {
          state: "not_found", client_request_id: "request exact", idempotency_key: "",
        } };
      } };
    },
  });
  assert.equal(exactStatusUrl, "/codex-runner?limit=2&client_request_id=request+exact");
  assert.equal(exactStatus.reconciliation.state, "not_found");
  assert.equal(exactStatus.reconciliation.client_request_id, "request exact");

  const ambiguous = await client.loadCodexRuns({ clientRequestId: "ambiguous" }, {
    fetcher: async () => ({ ok: true, status: 200, async json() { return {
      ok: false,
      error_type: "run_reconcile_ambiguous",
      error_envelope: contract.errorEnvelope("run_reconcile_ambiguous"),
    }; } }),
  });
  assert.equal(ambiguous.error_type, "run_reconcile_ambiguous");
  assert.equal(ambiguous.error_envelope.side_effects, "unknown");
  assert.equal(ambiguous.retryable, false);
}

attacks().then(() => console.log("OK: ResultEnvelope/ErrorEnvelope browser contract validated"));
