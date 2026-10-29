/* ResearchOS maintenance header.
 * 中文：验证前端统一动作语义、Agent Composer 私有直执行与公开交接降级。
 * English: Verifies unified action semantics, private direct execution, and public handoff fallback.
 */

"use strict";

const assert = require("node:assert/strict");
const vm = require("node:vm");

const { read } = require("./helpers/dashboard-vm.js");
const window = {};
const context = vm.createContext({ window });

for (const relativePath of [
  "dashboard/src/core/surface-contract.js",
  "dashboard/src/services/codex-run-router.js",
  "dashboard/src/components/buttons.js",
  "dashboard/src/components/preview-links.js",
  "dashboard/src/services/command-list-workbench.js",
  "dashboard/src/views/unified-inbox.js",
]) {
  vm.runInContext(read(relativePath), context);
}

const contract = window.ResearchOSActionContract;
const runtimeResult = (input) => ({ ...contract.runtimeCapabilities(input) });
const executionDisabled = { localExecution: false, registeredMaintenance: true, workspaceWrite: false };
const privateProvider = {
  executionAvailable: true,
  executionProbeRequired: true,
  executionScope: "workspace_write",
  providerMode: "local_codex",
  serverMode: true,
};
assert.equal(
  contract.resolveActionKind(contract.OPERATIONS.EXECUTE, { providerMode: "local_codex", serverMode: true }),
  contract.ACTION_KINDS.DIRECT,
  "private server mode must execute bounded actions directly",
);
assert.equal(
  contract.resolveActionKind(contract.OPERATIONS.EXECUTE, {
    executionScope: "read_only",
    providerMode: "local_codex",
    requiresWrite: true,
    serverMode: true,
  }),
  contract.ACTION_KINDS.HANDOFF,
  "a public read-only executor must not become a durable inbox writer",
);
assert.equal(
  contract.workspaceWriteAvailable({
    executionScope: "workspace_write",
    providerMode: "local_codex",
    serverMode: true,
  }),
  true,
  "private registered execution authority must remain available",
);
assert.equal(
  contract.resolveActionKind(contract.OPERATIONS.EXECUTE, { providerMode: "local_codex", serverMode: false }),
  contract.ACTION_KINDS.HANDOFF,
  "static private files must fall back to handoff",
);
assert.equal(
  contract.resolveActionKind(contract.OPERATIONS.EXECUTE, { providerMode: "demo_only", serverMode: true }),
  contract.ACTION_KINDS.HANDOFF,
  "demo-only mode must not imply local execution",
);
assert.equal(
  contract.resolveActionKind(contract.OPERATIONS.EXECUTE, { providerMode: "copy_only", serverMode: true }),
  contract.ACTION_KINDS.HANDOFF,
  "copy-only mode must fail closed even when a local server is present",
);
assert.equal(contract.resolveActionKind(contract.OPERATIONS.WRITEBACK), contract.ACTION_KINDS.PREVIEW_CONFIRM);
assert.equal(contract.resolveActionKind(contract.OPERATIONS.NAVIGATE), contract.ACTION_KINDS.NAVIGATION);
assert.deepEqual(
  { ...contract.runtimeCapabilities({
    executionAvailable: false,
    executionProbeRequired: false,
    executionScope: "none",
    providerMode: "copy_only",
    serverMode: true,
  }) },
  { localExecution: false, registeredMaintenance: true, workspaceWrite: false },
  "public copy-only mode must block model execution while registered maintenance remains available",
);
assert.equal(
  contract.runtimeCapabilities({
    executionAvailable: false,
    executionProbeRequired: true,
    providerMode: "local_codex",
    serverMode: true,
  }).localExecution,
  false,
  "a failed executor probe must close direct execution",
);
assert.deepEqual(
  runtimeResult(privateProvider),
  { localExecution: true, registeredMaintenance: true, workspaceWrite: true },
  "an explicit successful local Codex probe must restore private execution",
);
assert.deepEqual(
  runtimeResult({ ...privateProvider, executionScope: "read_only" }),
  { localExecution: true, registeredMaintenance: true, workspaceWrite: false },
  "read-only execution must not imply workspace write authority",
);
assert.deepEqual(
  { ...contract.executionRoute({ localExecution: true, publicStarter: false }) },
  {
    actionKind: "direct", effect: "execute_bounded", mode: "registered_runner",
    reason: "runner_available", resultLocation: "dashboard",
  },
  "a verified private runner must return its result to the Dashboard",
);
assert.deepEqual(
  { ...contract.executionRoute({ localExecution: false, publicStarter: false }) },
  {
    actionKind: "handoff", effect: "copy_task", mode: "copy_only",
    reason: "runner_unavailable", resultLocation: "external_client",
  },
  "a private runtime without a verified runner must fail closed to an explicit handoff",
);
assert.equal(
  contract.executionRoute({ localExecution: true, publicStarter: true }).reason,
  "public_policy",
  "public policy must remain copy-only even when stale capability input claims local execution",
);
for (const [label, input] of [
  ["missing provider declaration", { ...privateProvider, providerMode: undefined }],
  ["missing scope declaration", { ...privateProvider, executionScope: undefined }],
  ["missing probe policy", { ...privateProvider, executionProbeRequired: undefined }],
  ["probe not completed", { ...privateProvider, executionAvailable: undefined }],
  ["probe failed", { ...privateProvider, executionAvailable: false }],
  ["string probe result", { ...privateProvider, executionAvailable: "true" }],
  ["string probe policy", { ...privateProvider, executionProbeRequired: "true" }],
  ["unknown provider mode", { ...privateProvider, providerMode: "future_provider" }],
  ["legacy broad write scope", { ...privateProvider, executionScope: "full" }],
]) {
  assert.deepEqual(runtimeResult(input), executionDisabled, `${label} must fail closed`);
}
assert.deepEqual(
  runtimeResult({ ...privateProvider, serverMode: false }),
  { localExecution: false, registeredMaintenance: false, workspaceWrite: false },
  "static delivery must not inherit execution or registered maintenance",
);
assert.equal(contract.localExecutionAvailable(), false, "missing provider metadata must fail closed");
assert.equal(
  contract.workspaceWriteAvailable({ providerMode: "local_codex", serverMode: true }),
  false,
  "missing scope metadata must fail closed",
);
assert.equal(
  contract.durableMutationAvailable({ runtimeMode: "private", serverMode: true }),
  true,
  "durable project mutations require the private runtime and local server together",
);
assert.equal(
  contract.durableMutationAvailable({ runtimeMode: "personal_vault", serverMode: true }),
  false,
  "a personal-vault/public intake runtime must not inherit private durable project controls",
);
assert.equal(
  contract.durableMutationAvailable({ runtimeMode: "private", publicStarter: true, serverMode: true }),
  false,
  "the public starter identity must fail closed even if upstream runtime metadata drifts",
);

const execution = window.ResearchOSCodexRunRouter;
const payload = execution.payloadForAgentPrompt({
  budgetChoice: { id: "evidence", depth: "deep" },
  model: "auto",
  prompt: "Audit the current boundary.",
  reasoning: "high",
  task: { id: "audit", name: "Boundary audit" },
});
assert.equal(payload.source, "dashboard-agent-composer");
assert.equal(payload.task_mode, "read_only_analysis", "composer execution must not bypass candidate-before-confirmation");
assert.equal(payload.response_mode, "answer");
assert.equal(payload.recommended_task_complexity, "deep");
assert.equal(payload.candidate.required_confirmation, "handoff_only");
assert.equal(payload.candidate.sensitivity, "internal");

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll('"', "&quot;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;");
const translate = (key) => key;
const copyValueButton = (value, options = {}) => {
  const className = options.className ? ` class="${escapeHtml(options.className)}"` : "";
  const actionKind = options.actionKind ? ` data-action-kind="${escapeHtml(options.actionKind)}"` : "";
  return `<button type="button"${className} ${options.actionAttribute || ""}${actionKind} data-copy-value="${escapeHtml(value)}">${escapeHtml(options.label || "Copy")}</button>`;
};
const inboxDeps = {
  emptyState: () => "",
  encodeDataPayload: encodeURIComponent,
  escapeHtml,
  previewButton: () => "",
  relatedCompositionCards: () => [],
  segmentedButtons: () => "",
  shortText: String,
  translate,
};
const inboxBase = {
  allTotal: 1,
  archivedTotal: 0,
  codexRunnerEnabled: true,
  entries: [],
  localActiveTotal: 0,
  runs: [],
  sources: [],
  total: 1,
  view: "active",
  visibleTotal: 0,
  workFilter: "needs_review",
};
const privateInbox = window.ResearchOSUnifiedInboxView.renderUnifiedInboxHtml({
  inbox: { ...inboxBase, primaryActionKind: "direct" },
  prompt: "Run inbox",
  deps: inboxDeps,
});
assert.match(privateInbox, /data-action-kind="direct" data-unified-inbox-generate/);
assert.match(privateInbox, /data-action-kind="handoff" data-unified-inbox-copy/);

const runningInbox = window.ResearchOSUnifiedInboxView.renderUnifiedInboxHtml({
  inbox: {
    ...inboxBase,
    codexRuns: [
      { id: "queue-1", task_mode: "direct_execution", status: "running", queue_total: 1, created_at: "2026-08-10T19:30:00Z" },
      { id: "run-1", parent_id: "queue-1", action_key: "task:task-1", task_mode: "direct_execution", status: "running", queue_index: 1, queue_total: 1, title: "Prepare evidence summary", updated_at: "2026-08-10T19:31:00Z" },
    ],
    entries: [{ actionId: "task-1", archived: false, displayTitle: "Prepare evidence summary", type: "task", typeLabel: "Task" }],
    primaryActionKind: "direct",
    visibleTotal: 1,
  },
  prompt: "Run inbox",
  deps: inboxDeps,
});
assert.ok(runningInbox.includes('data-entry-run-status="running"'), "the candidate card must own its live execution status");
assert.match(runningInbox, /class="unified-inbox-handoff primary"[^>]*data-action-kind="direct"[^>]*disabled>unifiedInboxRunnerStatusRunning/, "a running candidate must not offer a duplicate execution action");
assert.ok(!runningInbox.includes("data-unified-inbox-archive=\"task:task-1\""), "archive must not masquerade as a running-task control");
assert.ok(!runningInbox.includes("data-unified-inbox-withdraw=\"task:task-1\""), "withdraw must not imply that it cancels an active runner job");
assert.ok(runningInbox.includes('class="unified-inbox-runner-overview"'), "queue progress must remain visible without opening technical details");
assert.ok(runningInbox.indexOf("unified-inbox-runner-surface") < runningInbox.indexOf("unified-inbox-ledger"), "execution progress must precede the candidate ledger instead of living below it");
assert.ok(!runningInbox.includes('<details class="unified-inbox-runner-log" open'), "healthy running details must stay collapsed by default");
assert.ok(!runningInbox.includes('class="unified-inbox-runner-queue"'), "the current run must not be repeated as a one-item queue inside technical details");

const publicInbox = window.ResearchOSUnifiedInboxView.renderUnifiedInboxHtml({
  inbox: { ...inboxBase, codexRunnerEnabled: false, primaryActionKind: "handoff" },
  prompt: "Copy inbox",
  deps: inboxDeps,
});
assert.doesNotMatch(publicInbox, /data-unified-inbox-generate/);
assert.match(publicInbox, /class="focus-action-button primary" data-action-kind="handoff" data-unified-inbox-copy/);

const frontendSources = [
  read("dashboard/app.js"),
  read("dashboard/src/core/interactions.js"),
  read("dashboard/src/core/ui-copy.js"),
  read("dashboard/src/services/asset-overview-workbench.js"),
].join("\n");
for (const deadRule of [
  "data-copy-graph-prompt-encoded",
  "data-copy-deep-read",
  "data-run-scout-prompt",
  "onCopyGraphPrompt",
  "graphCopyPrompt",
  "graphPromptCopied",
  "copyDeepReadHint",
]) {
  assert.equal(frontendSources.includes(deadRule), false, `dead copy-only rule must stay removed: ${deadRule}`);
}

const workSessionView = read("dashboard/src/views/work-session.js");
assert.match(workSessionView, /data-action-kind="\$\{packetMode \? "handoff" : "direct"\}"/);
assert.match(workSessionView, /data-action-kind="preview-confirm" data-work-session-writeback/);
assert.match(workSessionView, /data-action-kind="preview-confirm" data-work-session-complete/);
assert.match(workSessionView, /data-action-kind="handoff" data-work-session-copy-result/);

const commandQueued = window.ResearchOSCommandListWorkbenchService.renderCommandListHtml(
  { commands: [{ id: "validate", label: "Validate", command: "python3 scripts/validate.py" }] },
  { escapeHtml, queueAvailable: true, translate },
);
assert.match(commandQueued, /data-action-kind="navigation" data-queue-maintenance-suggestion="validate"/);
assert.doesNotMatch(commandQueued, /data-run-maintenance-action/);
const commandUnavailable = window.ResearchOSCommandListWorkbenchService.renderCommandListHtml(
  { commands: [{ id: "validate", label: "Validate", command: "python3 scripts\/validate.py" }] },
  { escapeHtml, queueAvailable: false, translate },
);
assert.match(commandUnavailable, /data-queue-maintenance-suggestion="validate" disabled/);

const previewHtml = window.ResearchOSPreviewLinksComponent.previewButton("paper.pdf", "Open", {
  escapeHtml,
  previewExists: () => true,
  simpleText: translate,
});
assert.match(previewHtml, /data-action-kind="navigation"/);
console.log("Frontend action contract passed.");
