const assert = require("node:assert/strict");
const vm = require("node:vm");

const { read } = require("./helpers/dashboard-vm.js");
const context = {};
context.window = context;
vm.runInNewContext(read("dashboard/src/services/handoff-receipt-projection.js"), context);
vm.runInNewContext(read("dashboard/src/views/handoff-receipt.js"), context);

const model = context.ResearchOSHandoffReceiptProjection;
const view = context.ResearchOSHandoffReceiptView;
const digest = "a".repeat(64);
const fixture = () => ({
  schema_id: "researchos-handoff-projection-v1",
  source_schema_id: "researchos-handoff-receipt-v1",
  handoff_id: `handoff:${digest}`,
  task_id: `task:${"b".repeat(64)}`,
  runtime_scope: "private",
  content_state: "included",
  source_revision: { state: "verified", source_id: `src:${"c".repeat(64)}`, value_digest: "d".repeat(64) },
  last_judgment: { state: "candidate", text: "Candidate <script>secret()</script>" },
  open_boundary: { state: "recorded", text: "External validity remains open." },
  next_safe_action: { state: "recommended", text: "Inspect the exact source revision." },
  forbidden_actions: { state: "recorded", items: ["Do not promote to canonical memory."] },
  target_client: { kind: "codex", surface: "conversation", binding_state: "requested" },
  limitations: ["projection_not_authority", "target_not_delivery", "no_transcript"],
});
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;",
}[char]));

const normalized = model.normalize(fixture());
assert.ok(normalized);
assert.equal(normalized.targetClient.binding_state, "requested");
assert.equal("delivery" in normalized.targetClient, false);
assert.equal("authority" in normalized.targetClient, false,
  "browser view must not add an authority or delivery projection");
assert.equal(Object.isFrozen(normalized), true);
const html = view.render(normalized, { escapeHtml, translate: (key) => key });
assert.match(html, /data-handoff-receipt-projection/);
assert.match(html, /Candidate &lt;script&gt;secret\(\)&lt;\/script&gt;/);
assert.doesNotMatch(html, /<script>secret/);
assert.doesNotMatch(html, /<button|<form|data-action-kind|evidence_ref|transcript|prompt|history/);
assert.match(html, /handoffReceiptTargetRequested/);
assert.match(html, /handoffReceiptLimitation/);

assert.equal(model.normalize(null), null);
assert.equal(view.render(null, { escapeHtml }), "", "missing receipt projection must add no UI noise");

const suppressed = fixture();
suppressed.content_state = "suppressed";
suppressed.last_judgment.text = "";
suppressed.open_boundary.text = "";
suppressed.next_safe_action.text = "";
suppressed.forbidden_actions.items = [];
const suppressedModel = model.normalize(suppressed);
assert.ok(suppressedModel);
const suppressedHtml = view.render(suppressedModel, { escapeHtml, translate: (key) => key });
assert.match(suppressedHtml, /handoffReceiptState_judgment_candidate/);
assert.doesNotMatch(suppressedHtml, /External validity|canonical memory/);

for (const [label, mutate] of Object.entries({
  extra_key: (value) => { value.transcript = "secret"; },
  bad_handoff_id: (value) => { value.handoff_id = "handoff:forged"; },
  unknown_with_content: (value) => { value.last_judgment = { state: "unknown", text: "forged" }; },
  target_claims_delivery: (value) => { value.target_client.binding_state = "delivered"; },
  limitation_removed: (value) => { value.limitations.pop(); },
  suppressed_content: (value) => { value.content_state = "suppressed"; },
})) {
  const attack = fixture();
  mutate(attack);
  assert.equal(model.normalize(attack), null, `${label} must fail closed`);
}

const appSource = read("dashboard/app.js");
const workSessionSource = read("dashboard/src/views/work-session.js");
assert.match(appSource, /HandoffReceiptProjection\.normalize\(dashboardData\?\.handoff_receipt_projection\)/);
assert.match(workSessionSource, /ResearchOSHandoffReceiptView\?\.render/);

console.log("OK: HandoffReceipt dashboard projection remains read-only, empty-safe, and fail-closed");
