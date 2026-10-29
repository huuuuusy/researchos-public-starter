const assert = require("node:assert/strict");
const vm = require("node:vm");

const { read } = require("./helpers/dashboard-vm.js");
const values = new Map();
let uuidCounter = 0;
const storage = {
  getItem: (key) => values.get(String(key)) || null,
  removeItem: (key) => values.delete(String(key)),
  setItem: (key, value) => values.set(String(key), String(value)),
};
const context = {
  URLSearchParams,
  console,
  crypto: { randomUUID: () => `00000000-0000-4000-8000-${String(++uuidCounter).padStart(12, "0")}` },
  localStorage: storage,
  location: { search: "" },
};
context.window = context;
vm.runInNewContext(read("dashboard/src/core/storage-contract.js"), context);
vm.runInNewContext(read("dashboard/src/core/surface-contract.js"), context);
vm.runInNewContext(read("dashboard/src/services/result-envelope.js"), context);
vm.runInNewContext(read("dashboard/src/services/work-session-state.js"), context);
vm.runInNewContext(read("dashboard/src/services/work-session-workbench.js"), context);

const state = context.ResearchOSWorkSessionState;
const contract = context.ResearchOSResultEnvelope;
let session = null;
let submissions = 0;
let reconciliations = 0;
const submittedRequestIds = [];
const lifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  executionAvailable: () => true,
  getSession: () => session,
  publicMode: () => false,
  refreshSurfaces: () => {},
  saveSession: (next) => {
    session = state.write(next, { runtimeMode: "private", storage });
    return session;
  },
  submitSession: async (next) => {
    submissions += 1;
    submittedRequestIds.push(next.clientRequestId);
    if (submissions === 1) {
      return contract.failureResult("transport_delivery_unknown", {
        client_request_id: next.clientRequestId,
        response_mode: "answer",
        work_session_id: next.id,
      });
    }
    return {
      ok: true,
      run: {
        client_request_id: next.clientRequestId,
        id: "run-recovered",
        response_mode: "answer",
        status: "queued",
        work_session_id: next.id,
      },
    };
  },
  reconcileSession: async (current) => {
    reconciliations += 1;
    const reconciled = state.reconcileRun(current, [], {
      reconciliation: { state: "not_found", client_request_id: current.clientRequestId },
    });
    session = state.write(reconciled, { runtimeMode: "private", storage });
    return { ok: false, reconciled: true, reconciliation: { state: "not_found" } };
  },
  showStatus: () => {},
}, {
  router: { inferResponseMode: () => "answer" },
  state,
  translate: (key) => key,
});

async function main() {
  lifecycle.draft({ intent: "Recover one exact request", responseMode: "answer" });
  const first = await lifecycle.callbacks.onRunDraft();
  assert.equal(first.error_type, "transport_delivery_unknown");
  assert.equal(submissions, 1);
  const requestId = session.clientRequestId;
  assert.ok(requestId.startsWith("request-"));
  assert.equal(state.read({ runtimeMode: "private", storage }).clientRequestId, requestId,
    "correlation must be durable before acknowledgement");

  const inspected = await lifecycle.callbacks.onRun();
  assert.equal(inspected.reconciled, true);
  assert.equal(reconciliations, 1);
  assert.equal(submissions, 1, "delivery unknown must perform GET reconciliation, never a second POST");
  assert.equal(session.draftResult.error_envelope.side_effects, "none");
  assert.equal(session.draftResult.error_envelope.retryable, true);

  const retried = await lifecycle.callbacks.onRun();
  assert.equal(retried.ok, true);
  assert.equal(submissions, 2, "only a later explicit action may retry after durable not-found proof");
  assert.deepEqual(submittedRequestIds, [requestId, requestId], "safe retry must reuse the exact request id");
  assert.equal(session.latestRunId, "run-recovered");
  assert.equal(session.status, "running");
  console.log("OK: exact run reconciliation and same-request retry validated");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
