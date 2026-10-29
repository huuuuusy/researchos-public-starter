const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const context = { window: {} };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, "dashboard/src/services/task-intent.js"), "utf8"), context);

const TaskIntent = context.window.ResearchOSTaskIntent;
const schema = JSON.parse(fs.readFileSync(path.join(root, "09_templates/data_contracts/researchos-task-intent-v1.schema.json"), "utf8"));

function assertExactKeys(record, keys, label) {
  assert.deepEqual(Object.keys(record).sort(), [...keys].sort(), `${label} keys must match the canonical schema`);
}

function assertMatchesSchema(intent) {
  assertExactKeys(intent, schema.required, "TaskIntent");
  assert.equal(intent.schema_id, schema.properties.schema_id.const);
  assert.equal(intent.input_trust, schema.properties.input_trust.const);
  for (const field of ["goal", "instruction", "client_request_id"]) {
    assert.equal(typeof intent[field], "string");
    assert.ok(intent[field].length <= schema.properties[field].maxLength, `${field} must respect maxLength`);
  }
  assertExactKeys(intent.client, schema.properties.client.required, "client");
  assert.ok(intent.client.kind.length >= 1 && intent.client.kind.length <= 120);
  assert.ok(intent.client.surface.length >= 1 && intent.client.surface.length <= 120);
  assert.ok(intent.client.task_ref.length <= 240);
  assertExactKeys(intent.requested_result, schema.properties.requested_result.required, "requested_result");
  assert.ok(intent.requested_result.mode.length >= 1 && intent.requested_result.mode.length <= 80);
  assertExactKeys(intent.requested_profile, schema.properties.requested_profile.required, "requested_profile");
  assert.ok(intent.requested_profile.provider.length >= 1 && intent.requested_profile.provider.length <= 120);
  assert.ok(intent.requested_profile.model.length >= 1 && intent.requested_profile.model.length <= 240);
  assert.ok(intent.requested_profile.reasoning_effort.length >= 1 && intent.requested_profile.reasoning_effort.length <= 80);
  assert.ok(intent.requested_profile.task_complexity.length >= 1 && intent.requested_profile.task_complexity.length <= 80);
  assertExactKeys(intent.client_hints, schema.properties.client_hints.required, "client_hints");
  assert.ok(intent.client_hints.recommended_reasoning_effort.length >= 1 && intent.client_hints.recommended_reasoning_effort.length <= 80);
  assert.ok(intent.client_hints.recommended_task_complexity.length >= 1 && intent.client_hints.recommended_task_complexity.length <= 80);
  assert.ok(intent.source_refs.length <= schema.properties.source_refs.maxItems);
  intent.source_refs.forEach((ref) => {
    const itemSchema = schema.properties.source_refs.items;
    assertExactKeys(ref, itemSchema.required, "source_ref");
    assert.ok(ref.kind.length >= 1 && ref.kind.length <= 80);
    assert.ok(ref.ref.length >= 1 && ref.ref.length <= itemSchema.properties.ref.maxLength);
    assert.ok(ref.label.length <= itemSchema.properties.label.maxLength);
  });
}

const crafted = {
  authority: { approved: true },
  client: { kind: "trusted_host", surface: "admin", task_ref: "task-1" },
  client_hints: { recommended_reasoning_effort: "high", recommended_task_complexity: "deep" },
  client_request_id: "request-1",
  goal: "  Long-term   goal  ",
  idempotency_key: "attacker-key",
  input_trust: "trusted",
  instruction: "Inspect the evidence",
  requested_profile: { provider: "claude", model: "claude-test", reasoning_effort: "ultra", task_complexity: "deep" },
  requested_result: { mode: "writeback", canonical_write: true },
  runtime_scope: "workspace_write",
  source_refs: [
    { kind: "card", ref: "paper-1", label: "Paper" },
    { kind: "card", ref: "paper-1", label: "Duplicate" },
    { kind: "invalid", path: "/tmp/input.pdf" },
  ],
};
const normalized = TaskIntent.normalize(crafted);
assert.deepEqual(JSON.parse(JSON.stringify(normalized)), JSON.parse(JSON.stringify(TaskIntent.normalize(crafted))), "normalization must be deterministic");
assert.equal(normalized.schema_id, "researchos-task-intent-v1");
assert.equal(normalized.input_trust, "untrusted");
assert.deepEqual(JSON.parse(JSON.stringify(normalized.client)), { kind: "trusted_host", surface: "admin", task_ref: "task-1" });
assert.equal(normalized.goal, "  Long-term   goal  ");
assert.equal(normalized.client_request_id, "request-1");
assert.equal(normalized.requested_result.mode, "writeback");
assert.equal(normalized.requested_profile.provider, "claude");
assert.equal(normalized.requested_profile.reasoning_effort, "ultra");
assert.equal(normalized.source_refs.length, 3, "only exact duplicate source refs may be deduplicated");
assertMatchesSchema(normalized);
for (const forbidden of ["authority", "idempotency_key", "runtime_scope", "canonical_write"]) {
  assert.equal(JSON.stringify(normalized).includes(forbidden), false, `${forbidden} must not survive TaskIntent normalization`);
}

const unsupported = TaskIntent.normalize({
  requested_profile: { reasoning_effort: "root", task_complexity: "unbounded" },
  requested_result: { mode: "delete" },
});
assert.equal(unsupported.requested_result.mode, "delete");
assert.equal(unsupported.requested_profile.reasoning_effort, "root");
assert.equal(unsupported.requested_profile.task_complexity, "unbounded");
assertMatchesSchema(unsupported);
assert.throws(
  () => TaskIntent.normalize({ source_refs: Array.from({ length: 24 }, (_, index) => ({ kind: "object", ref: `object-${index}` })) }),
  (error) => error.code === "task_intent_input_too_large" && error.field === "source_refs",
);
assert.throws(
  () => TaskIntent.normalize({ instruction: "x".repeat(TaskIntent.MAX_INSTRUCTION_LENGTH + 1) }),
  (error) => error.code === "task_intent_input_too_large" && error.field === "instruction",
);

const cliIntent = TaskIntent.normalize({ client: { kind: "cli", surface: "terminal", task_ref: "cli-task" } });
const codexIntent = TaskIntent.normalize({ client: { kind: "codex", surface: "desktop", task_ref: "codex-task" } });
const editorIntent = TaskIntent.normalize({ client: { kind: "zotero", surface: "extension", task_ref: "zotero-task" } });
assert.deepEqual(JSON.parse(JSON.stringify(cliIntent.client)), { kind: "cli", surface: "terminal", task_ref: "cli-task" });
assert.deepEqual(JSON.parse(JSON.stringify(codexIntent.client)), { kind: "codex", surface: "desktop", task_ref: "codex-task" });
assert.equal(cliIntent.input_trust, "untrusted", "a CLI producer does not become trusted by naming itself");
assert.equal(codexIntent.input_trust, "untrusted", "a Codex producer does not become trusted by naming itself");
assert.deepEqual(JSON.parse(JSON.stringify(editorIntent.client)), { kind: "zotero", surface: "extension", task_ref: "zotero-task" });
assertMatchesSchema(cliIntent);
assertMatchesSchema(codexIntent);
assertMatchesSchema(editorIntent);

const semanticContent = TaskIntent.normalize({
  goal: "Heading\r\n\r\n  indented goal",
  instruction: "Use this code:\r\n\r\n    value = 1\r\n    return value",
  source_refs: [{ kind: "session_source", ref: "papers/with  two spaces.md" }],
});
assert.equal(semanticContent.goal, "Heading\n\n  indented goal");
assert.equal(semanticContent.instruction, "Use this code:\n\n    value = 1\n    return value");
assert.equal(semanticContent.source_refs[0].ref, "papers/with  two spaces.md");
assertMatchesSchema(semanticContent);

const fromSession = TaskIntent.fromWorkSession({
  cards: [{ id: "card-1", path: "01_knowledge/card.md", title: "Card one" }],
  goal: "Original goal", id: "work-1", intent: "Current instruction", sourceHints: ["input.pdf", "input.pdf"],
}, {
  clientRequestId: "correlation-only", model: "gpt-5.6-sol", provider: "auto", reasoningEffort: "high",
  recommendedReasoningEffort: "medium", recommendedTaskComplexity: "standard", responseMode: "artifact", taskComplexity: "auto",
});
assert.equal(fromSession.goal, "Original goal");
assert.equal(fromSession.instruction, "Current instruction");
assert.equal(fromSession.client.task_ref, "work-1");
assert.equal(fromSession.client_request_id, "correlation-only");
assert.equal(fromSession.requested_result.mode, "artifact");
assert.equal(fromSession.source_refs.length, 2);
assertMatchesSchema(fromSession);

assert.equal(schema.properties.input_trust.const, "untrusted");
assert.equal(schema.properties.client_request_id.description.includes("must not treat it as an authorization"), true);
assert.equal(schema.properties.client.properties.kind.description.includes("must never select policy"), true);
assert.deepEqual(schema.properties.requested_result.properties.mode["x-supported-values"], [...TaskIntent.RESULT_MODES]);
assert.deepEqual(schema.properties.requested_profile.properties.reasoning_effort["x-supported-values"], [...TaskIntent.REASONING_EFFORTS]);
assert.deepEqual(schema.properties.requested_profile.properties.task_complexity["x-supported-values"], [...TaskIntent.TASK_COMPLEXITIES]);
assert.deepEqual(schema.properties.source_refs.items.properties.kind["x-supported-values"], [...TaskIntent.SOURCE_KINDS]);
assert.equal(schema.properties.instruction.maxLength, TaskIntent.MAX_INSTRUCTION_LENGTH);
assert.equal(schema.properties.source_refs.maxItems, TaskIntent.MAX_SOURCE_REFS);
assert.equal(TaskIntent.normalize({ instruction: "😀".repeat(40000) }).instruction.length, 80000, "JS must count Unicode code points like JSON Schema and Python");
assert.equal(schema.additionalProperties, false);

console.log("TaskIntent v1 regression passed.");
