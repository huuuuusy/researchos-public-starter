const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

global.window = global;
global.localStorage = { getItem() { return null; }, setItem() {} };
global.ResearchOSInteractions = {
  bindAll(root, selector, eventName, handler) {
    (root.nodes?.[selector] || []).forEach((node) => node.addEventListener(eventName, (event) => handler(event, node)));
  },
  bindOne(root, selector, eventName, handler) {
    const node = (root.nodes?.[selector] || [])[0];
    if (node) node.addEventListener(eventName, (event) => handler(event, node));
  },
};
global.ResearchOSSegmentedControlComponent = {
  renderSegmentButtons(options) { return options.map((option) => `<button>${option.label}</button>`).join(""); },
};
global.ResearchOSEmptyStateComponent = { renderEmptyState(options) { return options.message || ""; } };
global.ResearchOSPreviewLinksComponent = { previewButton() { return ""; } };

for (const relativePath of [
  "dashboard/src/services/inbox.js",
  "dashboard/src/services/unified-inbox-workbench.js",
  "dashboard/src/views/unified-inbox.js",
]) {
  vm.runInThisContext(fs.readFileSync(path.join(__dirname, "..", relativePath), "utf8"), { filename: relativePath });
}

const text = (key) => ({
  unifiedInboxTask: "Task",
  unifiedInboxJudgmentDraftTitle: "First make the judgment explicit",
  unifiedInboxJudgmentDraftBody: "Record what you accept, revise, reject, or defer.",
  unifiedInboxJudgmentDraft: "Prepare Judgment Receipt",
  unifiedInboxJudgmentDraftHint: "Creates a draft and does not run",
  unifiedInboxJudgmentDraftAria: "Prepare a Judgment Receipt draft for “{title}”",
})[key] || key;

const inbox = ResearchOSInboxService.collectUnifiedInboxEntries({
  doingItems: [{
    id: "route-choice-1",
    type: "task",
    title: "Choose the submission route",
    current_state: "Two plausible routes",
    proposed_state: "Commit to one bounded route",
    impact_scope: "One submission cycle",
    status: "local",
  }],
}, { text, doingKey: (item) => item.id, doingTypeLabel: () => "Research route" });
const entry = inbox.entries[0];
assert.equal(entry.judgmentReceiptEligible, true, "a consequential proposed transition should offer a Judgment Receipt");

const draft = ResearchOSInboxService.judgmentReceiptDraftForEntry(entry, { includeContractCard: true, language: "en", text });
assert.equal(draft.responseMode, "writeback");
assert.equal(draft.candidate.candidate_type, "judgment_receipt");
assert.equal(draft.candidate.required_confirmation, "confirm");
assert.equal(draft.candidate.admission_state.decision_state, "proposed");
assert.equal(draft.candidate.proposed_writeback.save_target, "", "drafting a receipt must not acquire a durable target");
assert.match(draft.intent, /Do not decide for me/);
assert.match(draft.intent, /do not execute the original task/i);
assert.match(draft.intent, /instead of guessing or fabricating a schema-valid receipt/);
assert.equal(draft.cards[0].path, "09_templates/data_contracts/researchos-judgment-receipt-v1.schema.json");

const reversibleReview = ResearchOSInboxService.collectUnifiedInboxEntries({
  doingItems: [{ id: "read-1", type: "task", title: "Read a note", status: "local" }],
}, { text, doingKey: (item) => item.id, doingTypeLabel: () => "Read" });
assert.equal(reversibleReview.entries.length, 0, "ordinary reversible work must not become a Review item");
assert.equal(ResearchOSInboxService.reviewSourceItemIsEligible({ id: "read-1", type: "task", title: "Read a note" }), false);

const epistemicReview = ResearchOSInboxService.collectUnifiedInboxEntries({
  doingItems: [
    { id: "notification-1", type: "notification", title: "Build finished", status: "local" },
    { id: "browse-1", type: "material_browser", title: "Opened a source", status: "local" },
    { id: "log-1", type: "run_log", title: "Runner heartbeat", status: "local" },
    { id: "provider-1", type: "provider_status", title: "Provider available", status: "local" },
    { id: "result-1", type: "task", source: "work-session", work_session_id: "session-result-1", title: "Bound result", status: "local" },
    { id: "candidate-1", type: "task", title: "Candidate change", status: "local", candidate: { candidate_id: "candidate-1" } },
    { id: "validation-1", type: "task", title: "Validation failure", status: "local", validation_state: "failed" },
  ],
}, { text, doingKey: (item) => item.id, doingTypeLabel: (type) => type });
assert.equal(epistemicReview.entries.length, 3, "Needs Review must exclude notification, browsing, log, and provider-state noise");
assert.equal(epistemicReview.needsReviewTotal, 3, "the Work filter count must name the same epistemically eligible set rendered by Needs Review");
assert.deepEqual(epistemicReview.entries.map((item) => item.actionId).sort(), ["candidate-1", "result-1", "validation-1"]);

const deps = {
  escapeHtml(value) { return String(value ?? "").replaceAll('"', "&quot;"); },
  shortText(value) { return String(value || ""); },
  translate: text,
};
const privateHtml = ResearchOSUnifiedInboxView.renderEntryCards({
  entries: [entry], judgmentCalibrationAvailable: true, codexRuns: [], codexRunnerEnabled: true,
}, deps);
assert.match(privateHtml, /data-unified-inbox-judgment="task:route-choice-1"/);
assert.match(privateHtml, /Creates a draft and does not run/);
const publicHtml = ResearchOSUnifiedInboxView.renderEntryCards({
  entries: [entry], judgmentCalibrationAvailable: false, codexRuns: [], codexRunnerEnabled: false, publicMode: true,
}, deps);
assert.doesNotMatch(publicHtml, /data-unified-inbox-judgment/);
assert.match(publicHtml, /data-canonical-write="false"/);
assert.match(publicHtml, /data-mutation-state="not_requested"/);
assert.match(publicHtml, /data-action-non-effect="durable_state_unchanged"/);

const withheldHtml = ResearchOSUnifiedInboxView.renderCurrentResultSummary({
  currentResult: null,
  currentResultProjection: {
    state: "withheld",
    reason: "work_session_id_mismatch",
    provenance: { work_session_id: "S2", observed_work_session_id: "S1", expected_run_id: "R1", observed_run_id: "R1" },
  },
  currentSession: { id: "S2", title: "Current task" },
}, deps);
assert.match(withheldHtml, /data-result-identity="withheld"/);
assert.match(withheldHtml, /S2/);
assert.match(withheldHtml, /S1/);
assert.doesNotMatch(withheldHtml, /Recovered result|Earlier completed result/);

const button = {
  dataset: { unifiedInboxJudgment: "task:route-choice-1" },
  addEventListener(_name, handler) { this.handler = handler; },
};
const calls = [];
ResearchOSUnifiedInboxWorkbenchService.bindUnifiedInboxEvents(
  { nodes: { "[data-unified-inbox-judgment]": [button] } },
  { onJudgment: (payload) => calls.push([payload.type, payload.id]) },
);
button.handler({ preventDefault() {}, stopPropagation() {} });
assert.deepEqual(calls, [["task", "route-choice-1"]], "the click must dispatch the exact reviewed entry identity");

// Item-local Review assembly: the judgment action drafts a receipt on the exact item and opens its Work panel.
function reviewFixture(runtimeMode) {
  const judgmentButton = {
    dataset: { unifiedInboxJudgment: "task:route-choice-1" },
    addEventListener(_name, handler) { this.handler = handler; },
  };
  const calls = { drafts: [], drawers: [], entriesForItem: [], rendered: null };
  const root = {
    innerHTML: "",
    nodes: { "[data-unified-inbox-judgment]": [judgmentButton] },
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
  const entry = inbox.entries.find((candidate) => candidate.id === "route-choice-1") || inbox.entries[0];
  global.ResearchOSPluginRuntime = { resolveSurfaceDependencies: () => ({}) };
  global.ResearchOSWorkSessionRouter = { resultProjectionForSession: () => ({ result: null }) };
  global.ResearchOSActionContract = { ACTION_KINDS: { DIRECT: "direct", HANDOFF: "handoff" } };
  global.ResearchOSUiCore = { encodeDataPayload: (value) => value };
  // The service and view are frozen; swap the globals the workbench resolves at call time.
  const inboxService = global.ResearchOSInboxService;
  const inboxView = global.ResearchOSUnifiedInboxView;
  global.ResearchOSInboxService = { ...inboxService, entriesForItem: (entries, scope) => { calls.entriesForItem.push(scope); return inboxService.entriesForItem(entries, scope); } };
  global.ResearchOSUnifiedInboxView = { ...inboxView, renderUnifiedInboxHtml: (input) => { calls.rendered = input.inbox; return ""; } };
  ResearchOSUnifiedInboxWorkbenchService.renderItemReview(root, {
    activeTemplateLanguage: () => "en",
    bindButtonTooltips() {}, bindPreviewButtons() {}, bindSectionJumpButtons() {},
    codexInboxTaskPrompt: () => "prompt",
    codexRunnerProviderStatus: null,
    codexRunnerRuns: [],
    collectUnifiedInboxEntries: () => ({ ...inbox, entries: [...inbox.entries] }),
    dashboardData: { runtime_mode: runtimeMode },
    draftWorkSession: (draft) => { calls.drafts.push(draft); return { ok: true }; },
    escapeHtml: (value) => String(value ?? ""),
    executionSessionForDisplay: () => null,
    findSingleInboxEntry: () => entry,
    focusDashboardSection() {},
    getPreviewDoc: () => null,
    isPublicStarterRuntime: () => runtimeMode !== "private",
    itemLocalSessionRegistry: () => [{ session_id: "S1", work_state: "needs_review" }],
    openItemExecutionDrawer: (...args) => calls.drawers.push(args),
    pluginContext: () => ({}),
    renderWorkSessionSurface() {},
    selectedExecutionItemId: "item-1",
    selectedWorkFilter: "active",
    simpleText: text,
    workspaceWriteAvailable: () => false,
  });
  judgmentButton.handler({ preventDefault() {}, stopPropagation() {} });
  global.ResearchOSInboxService = inboxService;
  global.ResearchOSUnifiedInboxView = inboxView;
  return calls;
}
const privateReview = reviewFixture("private");
assert.deepEqual(privateReview.entriesForItem, [{ itemId: "item-1", sessionIds: ["S1"] }], "review entries and counts must fail closed to the selected item identity");
assert.deepEqual(privateReview.rendered.sessionRegistry.map((entry) => entry.session_id), ["S1"]);
assert.equal(privateReview.rendered.workStateCounts.needs_review, 1);
assert.equal(privateReview.drafts.length, 1, "the judgment action must draft one receipt");
assert.deepEqual(privateReview.drawers, [["item-1", "work", { focus: true }]], "a judgment draft must remain bound to the exact item instead of navigating to a global Work screen");
const publicReview = reviewFixture("public_starter");
assert.equal(publicReview.drafts.length, 0, "judgment receipts are private-only");
assert.equal(publicReview.drawers.length, 0);

console.log("Judgment calibration frontend contract regression passed.");
