const assert = require("node:assert/strict");
const vm = require("node:vm");

const { read } = require("./helpers/dashboard-vm.js");
const context = {};
context.window = context;
vm.runInNewContext(read("dashboard/src/services/runtime-profile-projection.js"), context);
vm.runInNewContext(read("dashboard/src/services/result-envelope.js"), context);
vm.runInNewContext(read("dashboard/src/views/runtime-profile.js"), context);
vm.runInNewContext(read("dashboard/src/views/unified-inbox.js"), context);

const model = context.ResearchOSRuntimeProfileProjection;
const resultContract = context.ResearchOSResultEnvelope;
const view = context.ResearchOSRuntimeProfileView;
const inboxView = context.ResearchOSUnifiedInboxView;
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;",
}[char]));
const translate = (key) => key;
const fixture = () => ({
  schema_id: "researchos-runtime-profile-projection-v1",
  profile_id: "codex_local",
  adapter_family: "local_codex",
  provider: "codex",
  enabled: true,
  execution_scope: "workspace_write",
  model: "gpt-5.6-sol",
  reasoning_effort: "high",
  result_modes: ["answer", "artifact", "writeback"],
  cancel: "unsupported",
  status: "configured",
  verification_state: "local_probe_passed",
  selector_state: "candidate_off",
  error_type: "",
  configuration_handoff: {
    mode: "copy_only",
    command: "python3 scripts/runtime_profile_cli.py show --profile codex_local",
    config_target: "config/researchos.runtime.local.json",
  },
});

const normalized = model.normalize(fixture());
assert.ok(normalized);
assert.equal(Object.isFrozen(normalized), true);
assert.equal(normalized.selector_state, "candidate_off");
const safeProvider = resultContract.providerStatus({
  ok: true,
  provider: "codex",
  runtime_profile: fixture(),
  api_key_env: "SHOULD_NOT_REACH_BROWSER",
  endpoint_ref: "https://secret.invalid",
  fix_en: "Set PRIVATE_SECRET",
});
assert.ok(safeProvider.runtime_profile);
assert.equal("api_key_env" in safeProvider, false);
assert.equal("endpoint_ref" in safeProvider, false);
assert.equal("fix_en" in safeProvider, false);

const html = view.render(normalized, { escapeHtml, translate });
assert.match(html, /data-runtime-profile-projection/);
assert.match(html, /codex_local/);
assert.match(html, /local_probe_passed/);
assert.match(html, /runtime_profile_cli\.py show --profile codex_local/);
assert.doesNotMatch(html, /<button|<form|data-action-kind|endpoint_ref|credential_ref|api_key|budget_ref|source_ref/i);

const emptyHtml = inboxView.renderUnifiedInboxHtml({
  inbox: {
    total: 0, visibleTotal: 0, archivedTotal: 0, allTotal: 0,
    codexRuns: [], codexRunnerProviderStatus: safeProvider, workFilter: "needs_review",
  },
  deps: {
    emptyState: ({ message }) => `<div>${escapeHtml(message)}</div>`, escapeHtml, translate,
  },
});
assert.match(emptyHtml, /data-runtime-profile-projection/,
  "runtime profile remains visible without queue items or a chat surface");
assert.match(emptyHtml, /data-review-current-result data-result-present="false"/,
  "Review must keep a distinct empty result boundary even when no candidate exists");

const resultHtml = inboxView.renderUnifiedInboxHtml({
  inbox: {
    total: 0, visibleTotal: 0, archivedTotal: 0, allTotal: 0,
    codexRuns: [], currentSession: { goal: "Check <claim>" }, workFilter: "needs_review",
    currentResult: { status: "completed", answer: "Bounded <result>", artifacts: ["draft.md"] },
  },
  deps: {
    emptyState: ({ message }) => `<div>${escapeHtml(message)}</div>`, escapeHtml, translate,
  },
});
assert.match(resultHtml, /data-review-current-result data-result-present="true"/);
assert.match(resultHtml, /Bounded &lt;result&gt;/);
assert.match(resultHtml, /<code>draft\.md<\/code>/);
assert.doesNotMatch(resultHtml, /Bounded <result>/);

const publicCopy = fixture();
Object.assign(publicCopy, {
  profile_id: "public-copy-only", adapter_family: "none", provider: "none", enabled: false,
  execution_scope: "none", model: "none", reasoning_effort: "none", result_modes: [],
  status: "copy_only", verification_state: "copy_only",
  configuration_handoff: {
    mode: "copy_only",
    command: "python3 scripts/runtime_profile_cli.py list --scope public_starter",
    config_target: "config/researchos.runtime.local.json",
  },
});
assert.ok(model.normalize(publicCopy));
assert.doesNotMatch(view.render(publicCopy, { escapeHtml, translate }), /<button|data-action-kind/);

for (const [label, mutate] of Object.entries({
  credential: (value) => { value.credential_ref = { name: "SECRET" }; },
  endpoint: (value) => { value.endpoint_ref = "https://secret.invalid"; },
  selector_enabled: (value) => { value.selector_state = "enabled"; },
  forged_remote_live: (value) => {
    value.adapter_family = "openai_compatible"; value.provider = "deepseek";
    value.execution_scope = "answer_only"; value.result_modes = ["answer"];
  },
  executable_handoff: (value) => { value.configuration_handoff.command = "curl https://secret.invalid"; },
  mismatched_profile: (value) => { value.profile_id = "other"; },
  configured_but_disabled: (value) => { value.enabled = false; value.execution_scope = "none"; },
})) {
  const attack = fixture(); mutate(attack);
  assert.equal(model.normalize(attack), null, `${label} must fail closed`);
  assert.equal(resultContract.providerStatus({ runtime_profile: attack }).runtime_profile, undefined);
}

assert.equal(view.render(null, { escapeHtml, translate }), "");
console.log("OK: RuntimeProfile projection is read-only, secret-free, public-safe, and selector-off");
