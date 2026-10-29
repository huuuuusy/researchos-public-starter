/* Black-box fixture: real browser client -> authenticated loopback HTTP. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..", "..");
const base = String(process.env.RESEARCHOS_TEST_BASE || "").replace(/\/$/, "");
const header = String(process.env.RESEARCHOS_TEST_HEADER || "");
const token = String(process.env.RESEARCHOS_TEST_TOKEN || "");
const expected = String(process.env.RESEARCHOS_TEST_EXPECT || "completed");
assert.ok(base && header && token, "loopback server configuration is required");

const context = {
  URLSearchParams,
  console,
  crypto: { randomUUID: () => "b9000000-0000-4000-8000-000000000001" },
  ResearchOSRequestAuth: { resolveFetcher(candidate) { return candidate; } },
};
context.window = context;
for (const relative of ["dashboard/src/services/result-envelope.js", "dashboard/src/services/codex-runner-client.js"]) {
  vm.runInNewContext(fs.readFileSync(path.join(root, relative), "utf8"), context);
}

let postCount = 0;
const fetcher = async (url, options = {}) => {
  const headers = new Headers(options.headers || {});
  headers.set("Origin", base);
  headers.set(header, token);
  if (String(options.method || "GET").toUpperCase() === "POST") postCount += 1;
  return fetch(`${base}${url}`, { ...options, headers });
};

const clientRequestId = "b9-transport-request";
const payload = {
  source: "dashboard-work-session",
  task_mode: "read_only_analysis",
  response_mode: "answer",
  work_session_id: "b9-transport-session",
  model: "auto",
  reasoning_effort: "low",
  recommended_reasoning_effort: "low",
  recommended_task_complexity: "standard",
  prompt: "Return the local B9 fixture result.",
  task_intent: {
    schema_id: "researchos-task-intent-v1",
    input_trust: "untrusted",
    goal: "B9 transport proof",
    instruction: "Return the local B9 fixture result.",
    client_request_id: clientRequestId,
    client: { kind: "dashboard", surface: "work_session", task_ref: "b9-transport-session" },
    requested_result: { mode: "answer" },
    requested_profile: {
      provider: "auto", model: "auto", reasoning_effort: "low", task_complexity: "standard",
    },
    client_hints: { recommended_reasoning_effort: "low", recommended_task_complexity: "standard" },
    source_refs: [],
  },
};

async function main() {
  const client = context.ResearchOSCodexRunnerClient;
  const submitted = await client.submitCodexRun(payload, { fetcher });
  if (expected === "copy_only") {
    assert.equal(submitted.ok, false);
    assert.equal(submitted.error_type, "public_starter_copy_only");
    assert.equal(postCount, 1);
    console.log(JSON.stringify({ ok: true, mode: expected, post_count: postCount }));
    return;
  }
  assert.equal(submitted.ok, true);
  assert.equal(submitted.run.client_request_id, clientRequestId);
  let observed = null;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    observed = await client.loadCodexRuns({ clientRequestId, limit: 2 }, { fetcher });
    if (observed.ok && observed.runs[0]?.status === "completed") break;
    await new Promise((resolve) => setTimeout(resolve, 25));
  }
  assert.equal(observed?.ok, true);
  assert.equal(observed.reconciliation.state, "matched");
  assert.equal(observed.reconciliation.client_request_id, clientRequestId);
  assert.equal(observed.runs.length, 1);
  assert.equal(observed.runs[0].id, submitted.run.id);
  assert.equal(observed.runs[0].result_envelope.run_id, submitted.run.id);
  assert.equal(observed.runs[0].result_envelope.task_id, observed.runs[0].task_envelope_ref.task_id);
  assert.equal(observed.runs[0].answer, "B9 fake provider result");
  const repeated = await client.loadCodexRuns({ clientRequestId, limit: 2 }, { fetcher });
  assert.equal(repeated.runs[0].id, submitted.run.id);
  assert.equal(postCount, 1, "poll/reconcile must not issue a second POST");
  console.log(JSON.stringify({
    ok: true, mode: expected, post_count: postCount,
    run_id: submitted.run.id, task_id: observed.runs[0].task_envelope_ref.task_id,
  }));
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exitCode = 1;
});
