const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const dashboardIndex = read("dashboard/index.html");
const dashboardStyles = read("dashboard/style.css");
const contextPackSchema = JSON.parse(read("09_templates/data_contracts/researchos-context-pack-projection-v1.schema.json"));
// index.html loads every asset without a ?v= cache query (serve_dashboard.py sends Cache-Control: no-store).
assert.ok(!dashboardIndex.includes("?v="), "index.html must not carry hand-maintained ?v= cache queries");
for (const asset of [
  "src/core/surface-contract.js",
  "src/core/ui-copy-work-session.js",
  "src/core/ui-copy.js",
  "src/plugins/research-assets.js",
  "src/plugins/research-portfolio-copy.js",
  "src/plugins/research-portfolio-view.js",
  "src/plugins/research-portfolio-workbench.js",
  "src/plugins/research-portfolio.js",
  "src/services/codex-runner-client.js",
  "src/services/context-pack-projection.js",
  "src/services/handoff-admit-surface.js",
  "src/services/handoff-receipt-projection.js",
  "src/services/plugin-runtime.js",
  "src/services/preview-markdown.js",
  "src/services/request-auth.js",
  "src/services/result-envelope.js",
  "src/services/runtime-profile-projection.js",
  "src/services/task-intent.js",
  "src/services/work-session-client.js",
  "src/services/work-session-router.js",
  "src/services/work-session-state.js",
  "src/services/work-session-workbench.js",
  "src/views/handoff-admit-surface.js",
  "src/views/handoff-receipt.js",
  "src/views/home-command-center.js",
  "src/views/runtime-profile.js",
  "src/views/unified-inbox.js",
  "src/views/work-session.js",
]) {
  assert.ok(dashboardIndex.includes(`<script src="${asset}"></script>`), `${asset} must be loaded by index.html`);
}
for (const asset of ["asset-overview.css", "preview/markdown.css", "research-portfolio.css", "today-review.css", "work-session.css"]) {
  assert.ok(dashboardStyles.includes(`${asset}")`), `${asset} must be imported by the dashboard stylesheet`);
}

const copyContext = { document: { documentElement: { setAttribute() {} } } };
copyContext.window = copyContext;
vm.runInNewContext(read("dashboard/src/core/ui-copy-work-session.js"), copyContext);
vm.runInNewContext(read("dashboard/src/core/ui-copy.js"), copyContext);
assert.equal(copyContext.ResearchOSUICopy.simpleText["zh-CN"].workSessionEndSession, "结束任务", "the primary answer closeout must use plain task language");
assert.equal(copyContext.ResearchOSUICopy.simpleText["zh-CN"].workSessionAddFollowup, "补充后继续", "the answer secondary action must reveal its extra-run consequence");
assert.equal(copyContext.ResearchOSUICopy.simpleText["zh-CN"].workSessionDeliveryUnknown, "未收到服务器确认，无法判断任务是否已经送达。请先刷新并核对运行状态；在确认前重试可能造成重复执行。");
assert.equal(copyContext.ResearchOSUICopy.simpleText.en.workSessionEndSession, "End task");

function memoryStorage() {
  const values = new Map();
  return {
    get length() { return values.size; },
    getItem(key) { return values.has(String(key)) ? values.get(String(key)) : null; },
    key(index) { return [...values.keys()][Number(index)] || null; },
    removeItem(key) { values.delete(String(key)); },
    setItem(key, value) { values.set(String(key), String(value)); },
  };
}

const storage = memoryStorage();
const context = {
  URLSearchParams,
  console,
  crypto: { randomUUID: () => "session-test" },
  document: { documentElement: { setAttribute() {} } },
  localStorage: storage,
  location: { search: "" },
};
context.window = context;
vm.runInNewContext(read("dashboard/src/core/ui.js"), context);
vm.runInNewContext(read("dashboard/src/core/storage-contract.js"), context);
vm.runInNewContext(read("dashboard/src/core/surface-contract.js"), context);
vm.runInNewContext(read("dashboard/src/services/result-envelope.js"), context);
vm.runInNewContext(read("dashboard/src/services/task-intent.js"), context);
vm.runInNewContext(read("dashboard/src/services/work-session-router.js"), context);
vm.runInNewContext(read("dashboard/src/services/work-session-state.js"), context);
vm.runInNewContext(read("dashboard/src/services/context-pack-projection.js"), context);
vm.runInNewContext(read("dashboard/src/services/doing-board-state.js"), context);
vm.runInNewContext(read("dashboard/src/services/work-session-workbench.js"), context);
vm.runInNewContext(read("dashboard/src/services/request-auth.js"), context);
vm.runInNewContext(read("dashboard/src/services/work-session-client.js"), context);
vm.runInNewContext(read("dashboard/src/services/preview.js"), context);
vm.runInNewContext(read("dashboard/src/services/preview-markdown.js"), context);
vm.runInNewContext(read("dashboard/src/services/preview-pdf-workbench.js"), context);
vm.runInNewContext(read("dashboard/src/services/dashboard-render-plan.js"), context);
vm.runInNewContext(read("dashboard/src/components/preview-links.js"), context);
vm.runInNewContext(read("dashboard/src/views/work-session.js"), context);

const state = context.ResearchOSWorkSessionState;
const requestGate = state.createLatestRequestGate();
const firstA = requestGate.begin("item-a");
const requestB = requestGate.begin("item-b");
const secondA = requestGate.begin("item-a");
assert.equal(requestGate.isCurrent(firstA, "item-a"), false, "A to B to A navigation must reject the first A response by revision, not only by item id");
assert.equal(requestGate.isCurrent(requestB, "item-b"), false, "a superseded B response must not update the selected item");
assert.equal(requestGate.isCurrent(secondA, "item-a"), true, "the latest exact item request remains applicable");
requestGate.invalidate();
assert.equal(requestGate.isCurrent(secondA, "item-a"), false, "closing or switching the surface must invalidate an outstanding response");
assert.equal(state.isPublicDemoSession({ portfolioBinding: { sourcePath: "08_exports/public_starter/demo.md" } }), true, "public-demo Work Sessions must be identifiable for display filtering");
assert.equal(state.isPublicDemoSession({ sourceHints: ["personal_vault/01_knowledge/paper.md"] }), false, "personal-vault Work Sessions must remain visible when fictional examples are hidden");
const sharedStepBinding = { itemId: "shared-step", nextStepHash: "sha256:shared", providerId: "research_portfolio" };
assert.equal(state.portfolioBindingContextStatus(
  {
    id: "shared-step",
    nextStepHash: "sha256:shared",
    nextStep: "Inspect the evidence",
    nextStepCanonical: "Inspect the evidence",
    currentStage: "Evidence ready",
    currentStageCanonical: "Evidence ready",
  },
  {
    ...sharedStepBinding,
    nextStep: "核对证据",
    nextStepCanonical: "Inspect the evidence",
    currentStage: "证据已就绪",
    currentStageCanonical: "Evidence ready",
  },
), "current", "localized display text must not make a newly bound Work Session stale when canonical context matches");
const multiSessionRegistry = state.sessionRegistryProjection(
  { id: "session-a", intent: "Inspect the same evidence", portfolioBinding: sharedStepBinding, status: "active" },
  [
    { id: "session-b", intent: "Inspect the same evidence", portfolioBinding: sharedStepBinding, status: "paused", updatedAt: "2026-08-14T12:00:00Z" },
    { id: "session-c", intent: "Inspect the same evidence", portfolioBinding: sharedStepBinding, status: "ready", updatedAt: "2026-08-13T12:00:00Z" },
  ],
  [{ id: "run-a", status: "running", work_session_id: "session-a" }],
);
assert.equal(multiSessionRegistry.length, 3);
assert.equal(new Set(multiSessionRegistry.map((entry) => entry.session_id)).size, 3, "session identity must not collapse by title or logical task");
assert.equal(new Set(multiSessionRegistry.map((entry) => entry.logical_task_id)).size, 1, "separate sessions may still point to one registered task step");
assert.equal(multiSessionRegistry[0].run_id, "run-a", "a Run must bind by exact Work Session identity");
assert.equal(multiSessionRegistry[0].work_state, "active");
assert.equal(multiSessionRegistry.find((entry) => entry.session_id === "session-b").work_state, "waiting");
assert.equal(multiSessionRegistry.find((entry) => entry.session_id === "session-c").work_state, "needs_review");
const view = context.ResearchOSWorkSessionView;
const preview = context.ResearchOSPreviewService;
const previewMarkdown = context.ResearchOSPreviewMarkdownService;
const previewLinks = context.ResearchOSPreviewLinksComponent;
const renderPlan = context.ResearchOSDashboardRenderPlan;

const publicGraphFixture = {
  papers: [
    { path: "08_exports/public_starter/demo.md" },
    { path: "01_knowledge/papers/real.md" },
  ],
  projects: [{ case_mode: "public starter demo" }, { id: "real-project" }],
};
const hiddenDemoGraph = renderPlan.publicStarterGraphForDisplay(publicGraphFixture, false);
assert.equal(hiddenDemoGraph.papers.length, 1, "render plan must hide public demo papers without mutating the source graph");
assert.equal(hiddenDemoGraph.projects.length, 1, "render plan must hide public demo projects consistently");
assert.equal(publicGraphFixture.papers.length, 2, "render plan projection must keep generated source data immutable");
const hiddenDemoOverview = renderPlan.publicStarterOverviewForDisplay({ research_map: { mainlines: [{ title: "Demo direction" }], mainline_count: 1 } }, hiddenDemoGraph, { publicStarter: true, publicDemoVisible: false });
assert.equal(hiddenDemoOverview.research_map.mainline_count, 0, "hiding the public demo must not leave a phantom direction in the Library count");
assert.equal(hiddenDemoOverview.research_map.mainlines.length, 0, "hiding the public demo must remove its direction labels from the Library projection");
assert.equal(renderPlan.isPublicStarterRuntime({ runtime_mode: "public_starter" }), true);
const pdfTitleWorkbench = context.ResearchOSPreviewPdfWorkbenchService.createPreviewPdfWorkbench({
  document: { querySelector() { return null; }, getElementById() { return null; } },
  isPdfPreviewPath: (value) => String(value).endsWith(".pdf"),
  normalizePreviewPath: String,
  pdfPreviewLabel: (value) => String(value).split("/").pop(),
  pdfPreviewView: { renderPdfPreviewFrame() { return ""; } },
  previewSurfaceWorkbench: { bindPdfPreviewFrameEvents() {} },
});
pdfTitleWorkbench.openPdfPreview("uploads/preview-test-hash.pdf", { title: "点击打开本地 PDF" });
assert.equal(pdfTitleWorkbench.state().title, "preview-test-hash.pdf", "generic local-PDF actions must fall back to the file label");
pdfTitleWorkbench.openPdfPreview("uploads/preview-test-hash.pdf", { title: "Appendix A" });
assert.equal(pdfTitleWorkbench.state().title, "Appendix A", "descriptive PDF titles must remain intact");

async function main() {
const resultDeps = {
  escapeHtml: String,
  markdownToHtml: String,
  previewButton: () => "",
  translate: (key) => key,
};
const boundedPreviewButton = (path, label) => previewLinks.resolvedPreviewButton(path, label, {
    escapeHtml: String,
    resolveDocument: (candidate) => candidate === "docs/system-reference.en.md" ? { path: candidate } : null,
    resolvePreviewLink: preview.resolvePreviewLink,
    simpleText: (key) => key,
  });
const completedAnswer = { answer: "Visible answer", response_mode: "answer", status: "completed" };
const launcherHtml = view.renderLauncher({}, resultDeps);
assert.ok(!launcherHtml.includes("work-session-value-frame"), "the optional launcher must not repeat a three-step product explanation before the user can state a task");
assert.ok(launcherHtml.includes("work-session-surface-boundary"), "the launcher must state the bounded Dashboard and Codex-client responsibilities");
assert.ok(!launcherHtml.includes("workSessionRoleChatGPT"), "the core UI must not introduce a third discussion surface");
assert.ok(launcherHtml.includes("work-session-source-options"), "source controls must remain available behind progressive disclosure");
assert.ok(launcherHtml.includes("data-work-session-source-summary"), "the collapsed material control must have a visible selected-source receipt");
assert.ok(launcherHtml.includes("<summary aria-label=\"workSessionAddSource\""), "the icon-only mobile material control must keep an accessible name");
assert.ok(launcherHtml.includes("data-work-session-popover-close"), "mobile progressive-disclosure panels must provide an explicit close action");
assert.ok(launcherHtml.includes("work-session-examples"), "starter examples must remain available without occupying the primary composer");
assert.ok(launcherHtml.indexOf("work-session-primary-input") < launcherHtml.indexOf("work-session-source-options"), "language input must precede optional controls");
assert.ok(launcherHtml.indexOf("work-session-form") < launcherHtml.indexOf("work-session-surface-boundary"), "surface explanations must not block the primary task input");
assert.ok(!launcherHtml.includes("work-session-model-options"), "model and reasoning selection belong to the Codex client, not the default Dashboard composer");
assert.ok(!launcherHtml.includes("work-session-output-options"), "the Dashboard must infer the bounded result mode instead of asking new users to choose an internal execution type");
const collapsedWorkSessionHtml = view.renderWorkSessionHtml({}, resultDeps);
assert.ok(collapsedWorkSessionHtml.startsWith('<details class="work-session-launcher-shell">'), "an idle Work Session must not occupy the Progress page before the user asks for it");
assert.ok(collapsedWorkSessionHtml.includes("workSessionLauncherSummary"), "the optional dialogue entry must remain discoverable by purpose");
assert.ok(!collapsedWorkSessionHtml.startsWith('<details class="work-session-launcher-shell" open'), "the optional dialogue entry must be collapsed by default");
const onboardingWorkSessionHtml = view.renderWorkSessionHtml({ onboardingRequired: true }, resultDeps);
assert.ok(onboardingWorkSessionHtml.includes("work-session-onboarding-gate"), "an empty personal vault must explain why Work has no grounded task yet");
assert.ok(onboardingWorkSessionHtml.includes('aria-labelledby="workSessionOnboardingTitle"'), "the onboarding gate must expose a stable accessible name without a repeated live announcement");
assert.ok(onboardingWorkSessionHtml.includes('data-open-workspace="now"'), "the empty personal-vault state must return to first-run setup on Now");
assert.ok(onboardingWorkSessionHtml.includes("work-session-launcher-shell"), "advanced users may still register a bounded temporary task");
const activeWorkSessionHtml = view.renderWorkSessionHtml({
  session: { id: "active-1", title: "Review the paper", goal: "Long bounded task goal", intent: "Long internal execution instruction", status: "draft", cards: [], turns: [] },
}, resultDeps);
assert.ok(activeWorkSessionHtml.includes('data-work-session-active'), "an existing task must remain immediately visible");
assert.ok(!activeWorkSessionHtml.includes('class="work-session-launcher-shell"'), "an active task must not be hidden behind the idle launcher disclosure");
assert.ok(activeWorkSessionHtml.includes("Review the paper"), "the active task must lead with its short user-facing goal");
assert.ok(activeWorkSessionHtml.includes('class="work-session-task-brief"'), "a distinct internal instruction may remain available behind disclosure");
assert.ok(activeWorkSessionHtml.includes("data-work-session-run-draft"), "a draft created from the Card Library must expose an immediate start action");
const contextPack = context.ResearchOSContextPackProjection.project({
  cards: [{ id: "paper-1", path: "paper.md", title: "Selected paper", type: "paper", typeLabel: "Paper" }],
  evidenceBoundary: "Candidate evidence only", goal: "Inspect selected paper", id: "library-task",
  portfolioBinding: { itemId: "revision-closeout", nextStep: "Check the reviewer response", title: "Revision Claim Closeout" },
  sessionLifecycle: "open", sourceHints: ["paper.md", "appendix.pdf"], status: "draft",
  title: "Work on registered item: Revision Claim Closeout",
}, {
  previewDocuments: [
    { path: "paper.md", title: "Selected paper" },
    { path: "appendix.pdf", title: "Appendix" },
  ],
  runtimeMode: "private",
});
assert.equal(contextPack.included.length, 2);
assert.equal(contextPack.task.session_id, "library-task", "the Context Pack must expose the bounded Work Session instance separately");
assert.equal(contextPack.task.identity_kind, "registered_item_step");
assert.equal(contextPack.task.id, contextPack.task.logical_task_id, "the compatibility task id must mean logical task identity, never session identity");
assert.notEqual(contextPack.task.logical_task_id, contextPack.task.session_id, "registered task identity and Work Session identity must not collapse");
assert.equal(contextPack.task.logical_task_id, state.taskIdentityProjection({
  id: "another-session",
  portfolioBinding: { itemId: "revision-closeout", nextStep: "Check the reviewer response", title: "Revision Claim Closeout" },
}).logical_task_id, "two sessions for the same registered next step must project one logical task identity");
assert.ok(contextPackSchema.properties.task.required.includes("logical_task_id"));
assert.ok(contextPackSchema.properties.task.required.includes("session_id"));
assert.ok(contextPackSchema.properties.included.items.required.includes("preview_state"), "the schema must cover source-resolution fields emitted by the projection");
assert.equal(contextPack.task.goal, "Check the reviewer response", "a bound Context Pack must show the concise registered next step instead of the execution prompt");
assert.equal(contextPack.excluded[0].reason, "explicit_selection_required");
assert.equal(contextPack.egress.state, "not_granted_by_library");
const libraryContextHtml = view.renderLibraryContextPack({ projection: contextPack }, resultDeps);
assert.ok(libraryContextHtml.includes("data-current-context-pack"));
assert.ok(libraryContextHtml.includes("Revision Claim Closeout"));
assert.ok(!libraryContextHtml.includes("Work on registered item:"));
assert.ok(libraryContextHtml.includes("work-session-context-summary") && libraryContextHtml.includes("work-session-context-details"));
assert.ok(!libraryContextHtml.includes("Inspect selected paper"));
assert.equal((libraryContextHtml.match(/>appendix\.pdf</g) || []).length, 1, "a path-only source must not render the same path twice visibly");
assert.ok(libraryContextHtml.includes("data-context-included") && libraryContextHtml.includes("data-context-excluded") && libraryContextHtml.includes("data-context-egress"));
assert.ok(libraryContextHtml.includes('data-open-item-panel="work"'), "the prepared Context Pack must return to the exact item's Work panel without navigating to a global screen");
assert.ok(libraryContextHtml.includes('data-preview-path="paper.md"') && libraryContextHtml.includes("workSessionContextPreviewSource"), "an included source must open in the existing right-side preview workbench");
const relocatedContextPack = context.ResearchOSContextPackProjection.project({
  id: "relocated-source",
  sourceHints: ["06_active_context/example-source.md"],
  status: "draft",
}, {
  previewDocuments: [{ path: "07_archive/project_plans/example-source.md", title: "Example source" }],
  runtimeMode: "private",
});
assert.equal(relocatedContextPack.included[0].preview_state, "needs_confirmation", "a same-name source is only a candidate until identity is verified");
assert.equal(relocatedContextPack.included[0].requested_path, "06_active_context/example-source.md", "the original task reference must remain visible in the projection contract");
assert.equal(relocatedContextPack.included[0].candidate_preview_path, "07_archive/project_plans/example-source.md", "keep the archive candidate without silently rebinding the source");
const relocatedContextHtml = view.renderLibraryContextPack({ projection: relocatedContextPack }, resultDeps);
assert.ok(!relocatedContextHtml.includes('data-preview-path="07_archive/project_plans/example-source.md"'), "an unverified same-name candidate must not become the source preview");
assert.ok(relocatedContextHtml.includes("07_archive/project_plans/example-source.md"), "archive candidate remains visible for investigation");
const ambiguousContextPack = context.ResearchOSContextPackProjection.project({ id: "ambiguous-source", sourceHints: ["old/shared.md"], status: "draft" }, {
  previewDocuments: [{ path: "a/shared.md" }, { path: "b/shared.md" }],
  runtimeMode: "private",
});
assert.equal(ambiguousContextPack.included[0].preview_state, "ambiguous", "duplicate basenames must fail closed instead of guessing a source");
const ambiguousContextHtml = view.renderLibraryContextPack({ projection: ambiguousContextPack }, resultDeps);
assert.ok(!ambiguousContextHtml.includes('data-preview-path="old/shared.md"'), "an ambiguous source must not render a broken or guessed preview action");
assert.ok(ambiguousContextHtml.includes("workSessionContextSourceUnavailable"), "an unresolved source must explain the recovery action");
const publicContextPack = context.ResearchOSContextPackProjection.project({ id: "public-task", intent: "Check demo", status: "draft" }, { runtimeMode: "public_starter" });
assert.equal(publicContextPack.task.identity_kind, "unbound_session");
assert.equal(publicContextPack.task.logical_task_id, "session:public-task");
assert.equal(publicContextPack.task.session_id, "public-task");
assert.equal(publicContextPack.egress.state, "copy_only_user_controlled");
assert.equal(view.renderLibraryContextPack({ projection: context.ResearchOSContextPackProjection.project({ id: "finished", intent: "Done", sessionLifecycle: "ended", status: "completed" }) }, resultDeps), "");
const boundRecentHtml = view.renderRecentTasks([{
  id: "history-bound",
  intent: "Check the registered item",
  title: "Work on registered item: Revision Claim Closeout",
  portfolioBinding: { itemId: "revision-closeout", title: "Revision Claim Closeout" },
  status: "paused",
  updatedAt: "2026-08-10T00:00:00Z",
}], resultDeps);
assert.ok(boundRecentHtml.includes("Revision Claim Closeout"), "recent registered tasks must use the stable project title after a language switch");
assert.ok(!boundRecentHtml.includes("Work on registered item:"), "recent tasks must not preserve a stale language-specific launcher prefix");
assert.equal(view.renderModelSettings, undefined, "model and reasoning selection belong to the Codex client, not the Dashboard task flow");
const publicLauncherHtml = view.renderLauncher({ publicMode: true }, resultDeps);
assert.ok(publicLauncherHtml.includes("workSessionQuestionHintPublic"), "public launch copy must explain that the page prepares a task packet");
assert.ok(publicLauncherHtml.includes("workSessionPreparePacket"), "public launch action must not imply that a model runs in the page");
assert.ok(!publicLauncherHtml.includes("work-session-model-options"), "public Dashboard must not expose provider or model configuration in the task flow");
assert.ok(!publicLauncherHtml.includes("work-session-output-options"), "public Dashboard must not ask users to classify internal response modes");
assert.ok(!publicLauncherHtml.includes('accept=".'), "the source picker must not hide an artificial file-type allowlist in the native picker");
const executablePublicLauncherHtml = view.renderLauncher({ publicMode: true, executionAvailable: true }, resultDeps);
assert.ok(executablePublicLauncherHtml.includes("workSessionPreparePacket"), "public mode must stay copy-only even if upstream capability metadata incorrectly reports an executor");
assert.ok(executablePublicLauncherHtml.includes('data-action-kind="handoff"'), "public mode must fail closed to a handoff action");
assert.ok(!executablePublicLauncherHtml.includes("workSessionGetResult"), "public mode must not imply that it can run a model locally");
const unavailablePrivateLauncherHtml = view.renderLauncher({ executionAvailable: false, publicMode: false }, resultDeps);
assert.ok(unavailablePrivateLauncherHtml.includes("workSessionPreparePacket"), "a private page without a verified runner must offer an explicit task-packet handoff");
assert.ok(unavailablePrivateLauncherHtml.includes('data-action-kind="handoff"'), "an unavailable private runner must not retain a direct execution action");
assert.ok(!unavailablePrivateLauncherHtml.includes("workSessionGetResult"), "private deployment identity alone must not promise a model result");
const executablePrivateLauncherHtml = view.renderLauncher({ executionAvailable: true, publicMode: false }, resultDeps);
assert.ok(executablePrivateLauncherHtml.includes("workSessionGetResult"), "only a verified private runner may expose direct execution");
assert.ok(executablePrivateLauncherHtml.includes('data-action-kind="direct"'));
const recentLauncherHtml = view.renderLauncher({
  recentSessions: [{ id: "history-1", intent: "Continue paper review", resultSummary: "## Evidence\n\n| Boundary | State |\n|---|---|\n| IRB | **checked** |", status: "paused", title: "Paper review", turnCount: 2, updatedAt: "2026-07-15T12:00:00Z" }],
}, resultDeps);
assert.ok(recentLauncherHtml.includes("work-session-recent-tasks"), "bounded browser-local task summaries must be visible without becoming a chat sidebar");
assert.ok(recentLauncherHtml.includes("<details class=\"work-session-recent-tasks"), "recent task summaries must stay collapsed until the user chooses to resume one");
assert.ok(recentLauncherHtml.includes('data-work-session-history-resume="history-1"'), "recent tasks must provide an explicit resume action");
assert.ok(recentLauncherHtml.includes('data-work-session-history-delete="history-1"'), "recent task summaries must remain user-deletable");
assert.ok(recentLauncherHtml.includes("Evidence Boundary State IRB checked"), "recent-task cards must derive a compact readable excerpt instead of exposing raw Markdown delimiters");
assert.ok(!recentLauncherHtml.includes("|---|"), "recent-task cards must not display raw Markdown table syntax");
const publicResultHtml = view.renderResult(completedAnswer, { publicMode: true }, resultDeps);
const workSessionCss = read("dashboard/styles/views/work-session.css");
assert.match(workSessionCss, /\.work-session-result-body pre\s*\{[^}]*white-space:\s*pre-wrap;/s, "task packet code blocks must wrap on mobile instead of hiding result text behind horizontal scroll");
assert.match(workSessionCss, /\.work-session-resume-markdown\s*\{[^}]*height:\s*auto;[^}]*border:\s*0;[^}]*background:\s*transparent;/s, "restored Markdown summaries must fit the bounded resume card without a nested preview frame");
assert.ok(publicResultHtml.includes("data-work-session-copy-result"), "public results must remain directly copyable");
assert.ok(publicResultHtml.includes("workSessionPacketReady"), "public completion must be labeled as a ready task packet");
assert.ok(publicResultHtml.includes("workSessionCopyPacket"), "public copy action must name the task packet truthfully");
assert.ok(publicResultHtml.includes("data-work-session-writeback"), "public results must allow a browser-local writeback proposal");
assert.ok(!publicResultHtml.includes("data-work-session-save-result"), "public results must not offer private artifact creation");
const privateResultHtml = view.renderResult(completedAnswer, { publicMode: false }, resultDeps);
assert.ok(privateResultHtml.includes("data-work-session-save-result"), "private answer results must offer explicit artifact creation");
const deliveryUnknownHtml = view.renderResult({ execution_status: "delivery_unknown", status: "failed" }, {}, {
  ...resultDeps,
  translate: (key) => key === "workSessionDeliveryUnknown" ? "Delivery unknown; retry may duplicate execution." : key,
});
assert.ok(deliveryUnknownHtml.includes("Delivery unknown; retry may duplicate execution."), "delivery-unknown failures must explain the duplicate-execution risk without persisting it as model output");
const readOnlyExecutedResultHtml = view.renderResult(completedAnswer, {
  artifactCreationAvailable: false,
  publicMode: false,
}, resultDeps);
assert.ok(!readOnlyExecutedResultHtml.includes("data-work-session-save-result"), "a direct read-only result must not offer fake Markdown creation just because execution was available");
assert.ok(privateResultHtml.includes("data-work-session-writeback"), "private answer results must allow a writeback proposal");
const refreshFailureHtml = view.renderResult({
  ...completedAnswer,
  post_run_refresh: { attempted: true, ok: false, error_type: "post_run_refresh_failed" },
}, { publicMode: false }, resultDeps);
assert.ok(refreshFailureHtml.includes("work-session-refresh-warning"), "a successful write with a failed projection refresh must remain visibly incomplete");
assert.ok(refreshFailureHtml.includes('role="alert"'), "a projection refresh failure must be announced when it appears");
assert.ok(!refreshFailureHtml.includes("post_run_refresh_failed"), "internal refresh error types must not leak into the user-facing result");
const privateArtifactHtml = view.renderResult({ ...completedAnswer, artifacts: [{ path: "06_active_context/work_state/outputs/result.md" }], response_mode: "artifact" }, { publicMode: false }, resultDeps);
assert.ok(!privateArtifactHtml.includes("data-work-session-save-result"), "artifact results must not offer duplicate artifact creation");
assert.ok(privateArtifactHtml.includes("data-work-session-writeback"), "artifact results must still allow a writeback proposal");
assert.match(privateArtifactHtml, /class="primary"[^>]*data-result-primary-action="open_artifact"/, "an artifact result must make opening the artifact its primary action");
const writebackResultHtml = view.renderResult({ ...completedAnswer, response_mode: "writeback" }, { publicMode: false }, resultDeps);
assert.match(writebackResultHtml, /class="primary"[^>]*data-result-primary-action="open_review"/, "a writeback result must make Review its primary action");
assert.equal((writebackResultHtml.match(/data-work-session-writeback/g) || []).length, 1, "a writeback result must not offer a second proposal action");
const linkedReferenceResultHtml = view.renderResult({
  answer: "See [Start Here](START_HERE.md)",
  artifacts: [],
  response_mode: "answer",
  status: "completed",
}, { publicMode: false }, resultDeps);
assert.ok(!linkedReferenceResultHtml.includes("work-session-artifacts"), "an existing file linked in an answer must not be mislabeled as a newly generated artifact");
const explicitArtifactResultHtml = view.renderResult({
  answer: "Created the requested report.",
  artifacts: [{ path: "06_active_context/work_state/outputs/report.md" }],
  response_mode: "artifact",
  status: "completed",
}, { publicMode: false }, resultDeps);
assert.ok(explicitArtifactResultHtml.includes("work-session-artifacts"), "files explicitly reported as changed artifacts must remain visible as generated outputs");
const absoluteMarkdownPath = "/opt/researchos/06_active_context/README.md";
const absolutePdfPath = "/opt/researchos/corpus/papers/example.pdf";
assert.equal(preview.repositoryRelativePath(absoluteMarkdownPath), "06_active_context/README.md");
assert.equal(preview.repositoryRelativePath(absolutePdfPath), "", "public starter must not resolve private corpus paths");
assert.equal(preview.repositoryRelativePath("/opt/researchos/08_exports/reports/result.md"), "08_exports/reports/result.md");
const resolvedAbsoluteMarkdown = preview.resolvePreviewLink("", absoluteMarkdownPath, {
  resolveDocument: (path) => path === "06_active_context/README.md" ? { path } : null,
});
assert.equal(resolvedAbsoluteMarkdown.path, "06_active_context/README.md", "absolute ResearchOS Markdown paths must map to clickable repository-relative previews");
assert.equal(resolvedAbsoluteMarkdown.anchor, "");
const resolvedAbsolutePdf = preview.resolvePreviewLink("", absolutePdfPath);
assert.equal(resolvedAbsolutePdf, null, "public starter must reject private corpus PDF paths");
assert.equal(preview.isPdfPreviewPath("corpus/papers/APPENDIX.PDF"), true, "PDF preview detection must accept case-insensitive file extensions");
assert.equal(preview.resolvePreviewLink("", "corpus/papers/APPENDIX.PDF"), null, "public starter must reject relative corpus PDF paths");
assert.equal(preview.isPdfPreviewPath("/opt/private.pdf"), false, "absolute local paths must be resolved to an approved repository path before PDF preview");
assert.equal(preview.isPdfPreviewPath("https://example.com/paper.pdf"), false, "remote PDF URLs must not be sent to the local preview endpoint");
const componentPdfButton = previewLinks.previewButton("corpus/papers/example.pdf", "View PDF", {
  escapeHtml: String,
  previewExists: () => true,
  simpleText: (key) => key,
});
assert.ok(componentPdfButton.includes('data-pdf-preview-path="corpus/papers/example.pdf"'), "shared preview buttons must route PDF files through the PDF surface");
assert.ok(componentPdfButton.includes('data-pdf-preview-title="example.pdf"'), "PDF preview tabs must use the file name instead of a generic action label");
assert.ok(!componentPdfButton.includes('data-preview-path='), "PDF buttons must not be mislabeled as Markdown-document previews");
const spacedMarkdownPath = "/opt/researchos/06_active_context/My Notes (draft).md";
const spacedPdfPath = "/opt/researchos/corpus/papers/My Paper (draft).pdf";
const linkedSpacedMarkdown = previewMarkdown.markdownToHtml(
  `[notes](<${spacedMarkdownPath}>)`,
  "",
  {
    escapeHtml: String,
    resolveDocument: (target) => target === "06_active_context/My Notes (draft).md" ? { path: target } : null,
  }
);
assert.ok(linkedSpacedMarkdown.includes('data-preview-path="06_active_context/My Notes (draft).md"'), "angle-bracket Markdown links must preserve local paths with spaces and parentheses");
const linkedSpacedPdf = previewMarkdown.markdownToHtml(`[paper](<${spacedPdfPath}>)`, "", { escapeHtml: String });
assert.ok(!linkedSpacedPdf.includes("data-pdf-preview-path"), "public starter must not expose absolute corpus PDF links");
const linkedUppercasePdf = previewMarkdown.markdownToHtml("[appendix](corpus/papers/APPENDIX.PDF)", "", { escapeHtml: String });
assert.ok(!linkedUppercasePdf.includes("data-pdf-preview-path"), "public starter must not expose relative corpus PDF links");
const linkedFileUrl = previewMarkdown.markdownToHtml(
  "[notes](file:///opt/researchos/06_active_context/My%20Notes%20(draft).md)",
  "",
  {
    escapeHtml: String,
    resolveDocument: (target) => target === "06_active_context/My Notes (draft).md" ? { path: target } : null,
  }
);
assert.ok(linkedFileUrl.includes('data-preview-path="06_active_context/My Notes (draft).md"'), "file URLs must map to bounded repository previews");
const linkedLocalFile = previewMarkdown.markdownToHtml(
  `[README.md](${absoluteMarkdownPath})`,
  "",
  {
    escapeHtml: String,
    resolveDocument: (path) => path === "06_active_context/README.md" ? { path } : null,
  }
);
assert.ok(linkedLocalFile.includes('data-preview-path="06_active_context/README.md"'), "answer Markdown must render a clickable local-file preview link");
const labeledLocalFile = previewMarkdown.markdownToHtml(
  "[来源：START_HERE.md](START_HERE.md)",
  "",
  {
    escapeHtml: String,
    resolveDocument: (target) => target === "START_HERE.md" ? { path: target } : null,
  }
);
assert.equal((labeledLocalFile.match(/data-preview-path=/g) || []).length, 1, "a filename inside a Markdown link label must not create a nested duplicate link");
assert.ok(labeledLocalFile.includes("来源：START_HERE.md"));
assert.equal(state.createSession({ intent: "   " }), null, "blank goals must not create a Work Session");
assert.equal(state.runtimeStorageKey(""), state.PRIVATE_KEY, "missing runtime mode must default to private storage");
assert.equal(state.runtimeStorageKey("public_starter"), state.PUBLIC_KEY, "public runtime must use isolated public storage");
const session = state.createSession({
  evidenceBoundary: "Source and derived claims remain candidates",
  intent: "Understand this PDF and connect it to the current project",
  sensitivity: "internal",
  sourceHint: "/tmp/paper.pdf",
  templateLanguage: "en",
  text: (key) => ({
    workSessionInputSourceType: "Input source",
    workSessionSourceCardHint: "Source supplied for this task",
  })[key] || key,
});
assert.equal(session.id, "work-session-test");
assert.equal(session.status, "active");
assert.equal(session.version, 10, "new and migrated sessions must persist the v10 lifecycle schema");
assert.equal(session.sessionLifecycle, "open");
assert.equal(session.runLifecycle, "none");
assert.equal(session.runObservation, "none");
assert.equal(session.resultMode, "none");
assert.deepEqual(JSON.parse(JSON.stringify(session.admissionState)), {
  decision: "none",
  mutation: "not_applied",
  validation: "not_run",
  authority_role: "none",
});
const migratedLegacyRunning = state.normalizeSession({
  ...session,
  clientRequestId: "request-legacy-running",
  draftResult: { id: "run-legacy-running", status: "running" },
  latestRunId: "run-legacy-running",
  status: "running",
  version: 9,
});
assert.equal(migratedLegacyRunning.version, 10);
assert.equal(migratedLegacyRunning.sessionLifecycle, "open");
assert.equal(migratedLegacyRunning.runLifecycle, "running");
assert.equal(migratedLegacyRunning.runObservation, "fresh");
assert.equal(migratedLegacyRunning.status, "running");
const migratedDeliveryUnknown = state.normalizeSession({
  ...session,
  clientRequestId: "request-delivery-unknown",
  draftResult: {
    error_envelope: { error_type: "transport_delivery_unknown" },
    error_type: "transport_delivery_unknown",
    status: "failed",
  },
  status: "active",
  version: 9,
});
assert.equal(migratedDeliveryUnknown.runLifecycle, "submitted");
assert.equal(migratedDeliveryUnknown.runObservation, "delivery_unknown");
assert.equal(migratedDeliveryUnknown.status, "active", "delivery unknown must not reuse the running compatibility label");
assert.equal(state.lifecycleProjection(migratedDeliveryUnknown).state, "verify_delivery");
const migratedLeaseExpired = state.normalizeSession({
  ...session,
  draftResult: { id: "run-expired", lease_expired: true, status: "running" },
  latestRunId: "run-expired",
  status: "running",
  version: 9,
});
assert.equal(migratedLeaseExpired.runLifecycle, "running");
assert.equal(migratedLeaseExpired.runObservation, "lease_expired");
assert.equal(migratedLeaseExpired.status, "active", "an expired observation must not keep an infinite running spinner");
assert.equal(state.lifecycleProjection(migratedLeaseExpired).state, "verify_run");
const endedWithTrackedRun = state.normalizeSession({
  ...session,
  draftResult: { id: "run-after-end", status: "running" },
  latestRunId: "run-after-end",
  status: "completed",
  version: 9,
});
assert.equal(endedWithTrackedRun.sessionLifecycle, "ended");
assert.equal(endedWithTrackedRun.runLifecycle, "running");
assert.equal(endedWithTrackedRun.runObservation, "fresh");
assert.equal(endedWithTrackedRun.status, "completed", "ending a session must preserve but not masquerade as its bound run");
assert.equal(state.lifecycleProjection(endedWithTrackedRun).state, "ended_with_run_tracking");
const leaseExpiredHtml = view.renderActiveSession({
  executionAvailable: true,
  result: migratedLeaseExpired.draftResult,
  session: migratedLeaseExpired,
}, resultDeps);
assert.ok(leaseExpiredHtml.includes("workSessionLifecycle_verify_run"));
assert.ok(leaseExpiredHtml.includes("data-work-session-reconcile"), "an expired observation must expose status verification, not another submission form");
assert.ok(leaseExpiredHtml.includes("workSessionLastSafePoint"));
assert.ok(leaseExpiredHtml.includes("workSessionSafePointObserved"), "recovery must expose the last confirmed observation, not only an error label");
assert.ok(!leaseExpiredHtml.includes("data-work-session-run-form"), "an unverified run must not accept a follow-up that could duplicate execution");
assert.ok(!leaseExpiredHtml.includes('aria-busy="true"'), "lease expiry must stop the infinite busy indicator");
const endedTrackingHtml = view.renderActiveSession({
  executionAvailable: true,
  result: endedWithTrackedRun.draftResult,
  session: endedWithTrackedRun,
}, resultDeps);
assert.ok(endedTrackingHtml.includes("data-work-session-reconcile"), "ending a session must retain an explicit run-receipt check when execution is unresolved");
assert.ok(!endedTrackingHtml.includes("data-work-session-run-form"), "an ended session with run tracking must never reopen a submission form");

assert.equal(session.responseMode, "auto", "new sessions must infer result mode unless the user overrides it");
assert.equal(session.templateLanguage, "en", "template language must be frozen on the Work Session");
assert.equal(session.cards.length, 1, "a supplied PDF or link must enter the working deck automatically");
assert.equal(session.cards[0].type, "source");
assert.equal(session.cards[0].path, "/tmp/paper.pdf");
assert.equal(session.evidenceBoundary, "Source and derived claims remain candidates");
assert.equal(session.sensitivity, "internal");
assert.equal(session.goal, "Understand this PDF and connect it to the current project", "the original task objective must be stored separately from later instructions");
const sessionWithNewInstruction = state.updateSession(session, { intent: "Compare its weakest evidence with the current project" });
assert.equal(sessionWithNewInstruction.goal, session.goal, "follow-up instructions must not replace the original task objective");
const continuedPrompt = context.ResearchOSWorkSessionRouter.buildPrompt(sessionWithNewInstruction);
assert.ok(continuedPrompt.includes(`Task objective: ${session.goal}`));
assert.ok(continuedPrompt.includes("Current instruction: Compare its weakest evidence with the current project"));
const archivedTurn = state.turnFromResult(session.intent, {
  answer: "First grounded answer",
  id: "run-first",
  response_mode: "answer",
  status: "completed",
});
const sessionWithTurn = state.appendTurn(session, archivedTurn);
assert.equal(sessionWithTurn.turns.length, 1, "a completed answer must become bounded conversation context before follow-up");
assert.equal(state.appendTurn(sessionWithTurn, archivedTurn).turns.length, 1, "conversation history must deduplicate run ids");
const publicPacketTurn = state.turnFromResult("Refine this public task", {
  answer: "## Copy-ready task packet\nNested prompt body",
  execution_status: "copy_ready",
  id: "public-packet-1",
  status: "completed",
});
assert.equal(publicPacketTurn.includeInPrompt, false, "public copy-ready packets must not recursively feed later prompts");
const boundedTurns = state.normalizeSession({
  ...session,
  turns: Array.from({ length: 12 }, (_, index) => ({ answer: `Answer ${index}`, question: `Question ${index}`, runId: `run-${index}` })),
});
assert.equal(boundedTurns.turns.length, 8, "browser conversation history must stay bounded");
const history = state.upsertHistory([], state.updateSession(sessionWithTurn, {
  draftResult: { answer: "Latest result summary with a bounded conclusion", artifacts: ["06_active_context/work_state/outputs/result.md"], status: "completed" },
}), { status: "paused" });
assert.equal(history.length, 1, "starting another task must create one bounded recent-task summary");
assert.equal(history[0].resultSummary, "Latest result summary with a bounded conclusion");
assert.deepEqual(Array.from(history[0].artifacts), ["06_active_context/work_state/outputs/result.md"]);
assert.equal(Object.hasOwn(history[0], "turns"), false, "recent task storage must not retain full conversation turns");
const resumedFromHistory = state.sessionFromHistory(history[0]);
assert.equal(resumedFromHistory.historyId, history[0].id, "resumed tasks must update the same recent-task record instead of duplicating it");
assert.equal(resumedFromHistory.resumeSummary, history[0].resultSummary, "resume must carry only the latest task summary");
assert.equal(resumedFromHistory.goal, session.goal, "resuming a task must preserve its original objective");
assert.equal(resumedFromHistory.resumeTurnCount, history[0].turnCount, "resuming a task must preserve its cumulative step count");
assert.equal(resumedFromHistory.turns.length, 0, "resume must not reconstruct a full chat transcript");
assert.ok(context.ResearchOSWorkSessionRouter.buildPrompt(resumedFromHistory).includes("not a full chat transcript"), "the execution prompt must label restored context as a task summary");
const rearchivedWithoutNewResult = state.upsertHistory(history, resumedFromHistory, { status: "paused" });
assert.equal(rearchivedWithoutNewResult[0].turnCount, history[0].turnCount, "opening and re-archiving a task must not reduce or inflate its cumulative step count");
const resumedWithNewResult = state.updateSession(resumedFromHistory, {
  draftResult: { answer: "A new bounded result", id: "run-after-resume", status: "completed" },
});
const rearchivedWithNewResult = state.upsertHistory(history, resumedWithNewResult, { status: "paused" });
assert.equal(rearchivedWithNewResult[0].turnCount, history[0].turnCount + 1, "a completed result after resume must increment the cumulative step count once");
const publicSummaryHistory = state.upsertHistory([], state.updateSession(session, {
  draftResult: {
    answer: "## Task packet ready\nPublic packet boilerplate",
    execution_status: "copy_ready",
    id: "public-summary",
    status: "completed",
  },
}));
assert.equal(publicSummaryHistory[0].resultSummary, session.intent, "recent public tasks must summarize the user's instruction rather than raw packet boilerplate");
const linkedSummaryHistory = state.upsertHistory([], state.updateSession(session, {
  draftResult: {
    answer: "**结论**：[来源：START_HERE.md](START_HERE.md)",
    id: "linked-summary",
    status: "completed",
  },
}));
assert.equal(linkedSummaryHistory[0].resultSummary, "**结论**：[来源：START_HERE.md](START_HERE.md)", "recent task storage must preserve bounded Markdown instead of destructively flattening it");
const structuredSummary = [
  "## 核心判断",
  "",
  "| 字段 | 当前值 |",
  "|---|---|",
  "| 阶段 | **等待审批** |",
  "| 下一步 | `核对 approval` |",
  "",
  "<script>unsafe()</script>",
].join("\n");
const structuredHistory = state.upsertHistory([], state.updateSession(session, {
  draftResult: { answer: structuredSummary, id: "structured-summary", status: "completed" },
}));
assert.equal(structuredHistory[0].resultSummary, structuredSummary, "history normalization must preserve Markdown line breaks, tables, emphasis, and inline code");
const structuredResumedSession = state.sessionFromHistory(structuredHistory[0]);
assert.equal(structuredResumedSession.resumeSummary, structuredSummary, "resuming a task must not flatten the stored Markdown summary");
const structuredResumeHtml = view.renderActiveSession({
  executionAvailable: true,
  session: structuredResumedSession,
}, {
  ...resultDeps,
  markdownToHtml: (content) => previewMarkdown.markdownToHtml(content),
});
assert.ok(structuredResumeHtml.includes('class="markdown-body work-session-resume-markdown"'), "the restored task summary must use the shared safe Markdown renderer");
assert.ok(structuredResumeHtml.includes("<h2"), "restored Markdown headings must render structurally");
assert.ok(structuredResumeHtml.includes("<table>"), "restored Markdown tables must render structurally");
assert.ok(structuredResumeHtml.includes('<th scope="col">字段</th>'), "restored Markdown tables must preserve semantic column headers");
assert.ok(structuredResumeHtml.includes("<strong>等待审批</strong>"), "restored Markdown emphasis must render structurally");
assert.ok(structuredResumeHtml.includes("<code>核对 approval</code>"), "restored inline code must render structurally");
assert.ok(!structuredResumeHtml.includes("<script>unsafe()"), "restored summaries must not execute embedded HTML");
assert.ok(structuredResumeHtml.includes("&lt;script&gt;unsafe()&lt;/script&gt;"), "unsafe embedded HTML must remain visible as escaped text");
const presentationalHtml = previewMarkdown.markdownToHtml('<p align="right">\n<strong>English</strong> | <a href="README.zh.md">中文</a>\n</p>\n\n<script>unsafe()</script>');
assert.ok(presentationalHtml.includes("<p>English | 中文</p>"), "a purely presentational HTML line shows its text, not raw tags");
assert.ok(!presentationalHtml.includes("&lt;strong&gt;") && !presentationalHtml.includes("&lt;p align"), "presentational tags are not shown as escaped text");
assert.ok(presentationalHtml.includes("&lt;script&gt;unsafe()&lt;/script&gt;"), "a script line still stays visible as escaped text");
const semanticMarkdownHtml = previewMarkdown.markdownToHtml([
  "## 任务摘要",
  "",
  "- 核对来源",
  "+ 保留边界",
  "",
  "1. 查看结果",
  "2) 决定是否结束",
  "",
  "[安全链接](https://example.com/evidence)",
  "[危险链接](javascript:alert(1))",
].join("\n"), "", {
  resolvePreviewLink: (_basePath, href) => href.startsWith("https://") ? { external: true, href } : null,
});
assert.ok(semanticMarkdownHtml.includes("<ul>"), "task summaries must preserve unordered list structure");
assert.ok(semanticMarkdownHtml.includes("<ol>"), "task summaries must preserve ordered list structure");
assert.ok(semanticMarkdownHtml.includes('href="https://example.com/evidence"'), "explicitly resolved safe links must remain usable");
assert.ok(!semanticMarkdownHtml.includes('href="javascript:'), "dangerous link protocols must fail closed");
assert.ok(semanticMarkdownHtml.includes('<span class="md-unresolved-link">危险链接</span>'), "rejected links must keep a readable label");
assert.match(workSessionCss, /\.work-session-result-body\s*\{[^}]*height:\s*auto;[^}]*overflow:\s*visible;/s, "embedded result Markdown must not create a nested scrolling surface");
const legacyFlattenedSummary = "核心判断：先核对最新结果。 | 字段 | 当前值 | 候选值 | |---|---|---| | current_stage | waiting | approved | | progress_label | 等待审批 | 已收到 |";
const legacyResumeHtml = view.renderActiveSession({
  executionAvailable: true,
  session: { ...structuredResumedSession, resumeSummary: legacyFlattenedSummary },
}, {
  ...resultDeps,
  markdownToHtml: (content) => previewMarkdown.markdownToHtml(content),
});
assert.ok(legacyResumeHtml.includes("<table>"), "one-line summaries flattened by the legacy state version must reconstruct a table when the separator row still proves the column count");
assert.ok(legacyResumeHtml.includes("<td>current_stage</td>"), "legacy table reconstruction must preserve the first field row");
assert.ok(legacyResumeHtml.includes("<td>progress_label</td>"), "legacy table reconstruction must preserve later field rows");
const boundedHistory = state.normalizeHistory(Array.from({ length: 15 }, (_, index) => ({
  id: `history-${index}`,
  intent: `Task ${index}`,
  updatedAt: `2026-07-${String(index + 1).padStart(2, "0")}T00:00:00Z`,
})));
assert.equal(boundedHistory.length, state.HISTORY_LIMIT, "recent task summaries must stay within their explicit retention bound");
const sessionWithFollowupSource = state.addSource(sessionWithTurn, {
  attachmentName: "appendix.pdf",
  sourceHint: "/tmp/appendix.pdf",
}, (key) => key);
assert.ok(sessionWithFollowupSource.sourceHints.includes("/tmp/appendix.pdf"), "a follow-up must be able to add another bounded source");
assert.ok(!sessionWithFollowupSource.sourceHints.includes("appendix.pdf"), "a file name must not duplicate its stored path in source hints");
assert.equal(sessionWithFollowupSource.cards.filter((card) => card.path === "/tmp/appendix.pdf").length, 1, "a follow-up source must become one context card");
assert.equal(state.addSource(sessionWithFollowupSource, { sourceHint: "/tmp/appendix.pdf" }, (key) => key).sourceHints.length, sessionWithFollowupSource.sourceHints.length, "follow-up sources must deduplicate");
const followupSourceLines = context.ResearchOSWorkSessionRouter.sourceLines(sessionWithFollowupSource)
  .filter((line) => line.includes("appendix.pdf"));
assert.equal(followupSourceLines.length, 1, "a task prompt must list one source card instead of repeating its path and filename");
const sessionWithoutFollowupSource = state.removeCard(
  sessionWithFollowupSource,
  sessionWithFollowupSource.cards.find((card) => card.path === "/tmp/appendix.pdf").id,
);
assert.ok(!sessionWithoutFollowupSource.sourceHints.includes("/tmp/appendix.pdf"), "removing a source card must also remove its hidden prompt hint");
assert.ok(!context.ResearchOSWorkSessionRouter.buildPrompt(sessionWithoutFollowupSource).includes("/tmp/appendix.pdf"), "a visibly removed source must not remain in the execution prompt");
assert.equal(sessionWithoutFollowupSource.attachmentName, "", "removing the latest attached source must clear its stale attachment label");
const conversationHtml = view.renderConversation({
  result: completedAnswer,
  session: { ...sessionWithTurn, intent: "Follow-up question" },
}, resultDeps);
assert.ok(conversationHtml.includes("First grounded answer"), "archived turns must remain visible in the conversation");
assert.ok(conversationHtml.includes("Follow-up question"), "the current question must render after archived turns");
assert.ok(conversationHtml.includes("work-session-archived-result"), "completed prior results must collapse behind progressive disclosure");
assert.ok(conversationHtml.includes("work-session-task-progress"), "the active surface must present task progress instead of a chat transcript");
assert.ok(conversationHtml.includes("work-session-process-log"), "older processing steps must live in one collapsed process log");
assert.ok(!conversationHtml.includes("work-session-turn is-user"), "the task surface must not render the current instruction as a chat bubble");
const publicConversationHtml = view.renderConversation({
  publicMode: true,
  result: completedAnswer,
  session: { ...session, turns: [publicPacketTurn] },
}, resultDeps);
assert.ok(publicConversationHtml.includes("workSessionPreviousPacket"), "archived public packets must be labeled as task-packet history");
const activeSessionHtml = view.renderActiveSession({ executionAvailable: true, result: completedAnswer, session }, resultDeps);
assert.ok(activeSessionHtml.includes("work-session-source-options"), "the follow-up composer must allow adding material without leaving the task");
assert.ok(activeSessionHtml.includes("work-session-continue"), "task continuation must stay behind progressive disclosure rather than a persistent chat composer");
assert.match(activeSessionHtml, /class="primary"[^>]*data-result-primary-action="finish_session"[^>]*data-work-session-complete/, "an answer result must make ending the task the primary action");
assert.ok(activeSessionHtml.includes("data-work-session-add-followup"), "an answer result must offer an explicit secondary route to add context before another run");
assert.ok(activeSessionHtml.indexOf('data-result-primary-action="finish_session"') < activeSessionHtml.indexOf("data-work-session-add-followup"), "ending the task must precede the optional follow-up route");
assert.ok(!activeSessionHtml.includes("data-work-session-continue-recommended"), "model advice must not silently become the default next run");
const continuationHandlers = {};
const continuationLauncher = {
  addEventListener(type, handler) { continuationHandlers[`launcher:${type}`] = handler; },
};
const continuationDetails = { open: false };
let followupFocused = 0;
const continuationRoot = {
  querySelector(selector) {
    if (selector === "[data-work-session-add-followup]") return continuationLauncher;
    if (selector === ".work-session-continue") return continuationDetails;
    if (selector === "[data-work-session-intent-edit]") return { focus() { followupFocused += 1; } };
    return null;
  },
  querySelectorAll() { return []; },
};
context.ResearchOSWorkSessionWorkbenchService.bindWorkSessionEvents(continuationRoot, {}, resultDeps);
continuationHandlers["launcher:click"]();
assert.equal(continuationDetails.open, true, "the secondary follow-up action must reveal the existing bounded composer");
assert.equal(followupFocused, 1, "the secondary follow-up action must move focus to the instruction field without starting a run");
assert.equal((activeSessionHtml.match(/data-work-session-status/g) || []).length, 1, "an active session must expose one live status region");
assert.ok(activeSessionHtml.includes('aria-busy="false"'), "the result region must expose its loading state to assistive technology");
assert.ok(!/data-work-session-result[^>]*aria-live/.test(activeSessionHtml), "a long result body must not become one giant live region");
assert.match(activeSessionHtml, /<strong role="status" aria-live="polite" aria-atomic="true">workSessionResultReady<\/strong>/, "only the concise atomic result status should announce completion");
const boundPortfolioSession = state.updateSession(session, {
  portfolioBinding: {
    itemId: "pilot-approval",
    nextStep: "Confirm the ethics approval",
    nextStepHash: "step-fixture",
    portfolioPath: "06_active_context/research-portfolio.md",
    providerId: "research_portfolio",
    sourcePath: "01_knowledge/projects/pilot-approval.md",
    title: "Pilot Study Approval",
  },
});
const boundPortfolioHtml = view.renderActiveSession({ contextStatus: "current", executionAvailable: true, workItemMutationAvailable: true, publicMode: false, result: completedAnswer, session: boundPortfolioSession }, resultDeps);
assert.ok(boundPortfolioHtml.includes("data-work-session-complete-step"), "a private bound Work Session must expose scoped Commitment completion");
assert.ok(boundPortfolioHtml.includes("data-work-session-complete"), "a private bound Work Session must retain an independent session archive action");
assert.ok(boundPortfolioHtml.includes("data-work-session-complete-project"), "a private bound Work Session must place durable project closeout behind a distinct inline confirmation");
const unavailableBoundPortfolioHtml = view.renderActiveSession({ contextStatus: "current", executionAvailable: true, workItemMutationAvailable: false, publicMode: false, result: completedAnswer, session: boundPortfolioSession }, resultDeps);
assert.ok(unavailableBoundPortfolioHtml.includes('aria-describedby="workSessionCompleteStepReason"'), "a disabled step action must point to a visible reason");
assert.ok(unavailableBoundPortfolioHtml.includes('id="workSessionCompleteStepReason"'), "the disabled step reason must remain available outside hover-only title text");
assert.ok(unavailableBoundPortfolioHtml.includes('aria-describedby="workSessionCompleteProjectReason"'), "a disabled project action must point to a visible reason");
const publicBoundPortfolioHtml = view.renderActiveSession({ contextStatus: "current", publicMode: true, result: completedAnswer, session: boundPortfolioSession }, resultDeps);
assert.ok(publicBoundPortfolioHtml.includes("data-work-session-complete"), "public demo sessions must keep session completion browser-local");
assert.ok(!publicBoundPortfolioHtml.includes("data-work-session-complete-step"), "public demo sessions must not imply a private attention write");
assert.ok(!publicBoundPortfolioHtml.includes("data-work-session-complete-project"), "public demo sessions must not imply private Markdown writeback");
const currentBindingProjection = state.workItemBindingProjection(boundPortfolioSession, [{
  attention_state: "today",
  completed_step_hash: "",
  id: "pilot-approval",
  lifecycle_state: "open",
  next_step_hash: "step-fixture",
  provider_id: "research_portfolio",
  state: "mainline",
}]);
assert.deepEqual(JSON.parse(JSON.stringify(currentBindingProjection)), {
  bound: true,
  itemFound: true,
  projectOpen: true,
  stepCompleted: false,
  stepCurrent: true,
}, "the view projection must match a Work Session only to its exact canonical item and frozen step");
const completedBindingProjection = state.workItemBindingProjection(boundPortfolioSession, [{
  attention_state: "needs_next_step",
  completed_step_hash: "step-fixture",
  id: "pilot-approval",
  lifecycle_state: "open",
  next_step_hash: "step-fixture",
  provider_id: "research_portfolio",
  state: "mainline",
}]);
const completedStepHtml = view.renderActiveSession({
  contextStatus: "current",
  executionAvailable: true,
  workItemBindingState: completedBindingProjection,
  workItemMutationAvailable: true,
  publicMode: false,
  result: completedAnswer,
  session: boundPortfolioSession,
}, resultDeps);
assert.match(completedStepHtml, /data-work-session-complete-step disabled[^>]*workSessionStepAlreadyCompletedHint|workSessionStepAlreadyCompletedHint[^>]*data-work-session-complete-step disabled/, "an already completed bound step must not be submitted twice");
assert.ok(completedStepHtml.includes("workSessionStepAlreadyCompleted"));
const staleBindingProjection = state.workItemBindingProjection(boundPortfolioSession, [{
  attention_state: "today",
  completed_step_hash: "",
  id: "pilot-approval",
  lifecycle_state: "open",
  next_step_hash: "new-step-signature",
  provider_id: "research_portfolio",
  state: "mainline",
}]);
assert.equal(staleBindingProjection.stepCurrent, false);
const staleStepHtml = view.renderActiveSession({
  contextStatus: "stale",
  executionAvailable: true,
  workItemBindingState: staleBindingProjection,
  workItemMutationAvailable: true,
  publicMode: false,
  result: completedAnswer,
  session: boundPortfolioSession,
}, resultDeps);
assert.ok(staleStepHtml.includes("data-work-session-context-read-only"), "a stale Work Session must be visibly read only");
assert.ok(!staleStepHtml.includes("data-work-session-run-draft"), "a stale Work Session must not expose a new run");
assert.ok(!staleStepHtml.includes("data-work-session-run-form"), "a stale Work Session must not expose follow-up execution");
assert.ok(!staleStepHtml.includes("data-work-session-complete-step"), "a stale Work Session must not expose step completion");
assert.ok(!staleStepHtml.includes("data-work-session-complete-project"), "a stale Work Session must not expose project closeout");
assert.ok(!staleStepHtml.includes("data-work-session-writeback"), "a stale Work Session must not expose writeback");
assert.ok(staleStepHtml.includes("data-work-session-new"), "a stale Work Session must offer a fresh task route");
assert.ok(staleStepHtml.includes("data-work-session-complete"), "a stale Work Session must remain independently endable");
const closedBindingProjection = state.workItemBindingProjection(boundPortfolioSession, [{
  attention_state: "completed",
  completed_step_hash: "step-fixture",
  id: "pilot-approval",
  lifecycle_state: "completed",
  next_step_hash: "step-fixture",
  provider_id: "research_portfolio",
  state: "closed",
}]);
const closedProjectSessionHtml = view.renderActiveSession({
  contextStatus: "current",
  executionAvailable: true,
  workItemBindingState: closedBindingProjection,
  workItemMutationAvailable: true,
  publicMode: false,
  result: completedAnswer,
  session: boundPortfolioSession,
}, resultDeps);
assert.ok(closedProjectSessionHtml.includes("data-work-session-complete"), "a session bound to a closed project must still be independently endable");
assert.ok(!closedProjectSessionHtml.includes("data-work-session-complete-step"), "a closed project must expose no further step action");
assert.ok(!closedProjectSessionHtml.includes("data-work-session-complete-project"), "a closed project must expose no duplicate project closeout");
const legacyBoundPortfolioHtml = view.renderActiveSession({
  contextStatus: "unknown",
  executionAvailable: true,
  publicMode: false,
  workItemMutationAvailable: true,
  result: completedAnswer,
  session: state.updateSession(session, { portfolioBinding: { itemId: "legacy-item", title: "Legacy item" } }),
}, resultDeps);
assert.ok(legacyBoundPortfolioHtml.includes("data-work-session-context-read-only"), "legacy sessions without a bound next-step signature must fail closed as read only");
assert.ok(!legacyBoundPortfolioHtml.includes("data-work-session-complete-step"), "legacy sessions must not expose an unverifiable step mutation");
const disconnectedBoundPortfolioHtml = view.renderActiveSession({
  contextStatus: "current",
  executionAvailable: true,
  workItemMutationAvailable: false,
  publicMode: false,
  result: completedAnswer,
  session: boundPortfolioSession,
}, resultDeps);
assert.match(disconnectedBoundPortfolioHtml, /data-work-session-complete-step disabled[^>]*workSessionPortfolioMutationUnavailableHint|workSessionPortfolioMutationUnavailableHint[^>]*data-work-session-complete-step disabled/, "a disconnected private page must not expose a fake step write");
assert.match(disconnectedBoundPortfolioHtml, /data-work-session-complete-project disabled/, "a disconnected private page must disable durable project closeout");
const boundHistory = state.upsertHistory([], boundPortfolioSession, { status: "paused" });
assert.equal(boundHistory[0].portfolioBinding.itemId, "pilot-approval", "recent task summaries must preserve the registered-item binding");
assert.equal(state.sessionFromHistory(boundHistory[0]).portfolioBinding.itemId, "pilot-approval", "resuming a registered task must preserve its completion target");
assert.equal(state.sessionFromHistory(boundHistory[0]).portfolioBinding.nextStepHash, "step-fixture", "resuming a registered task must preserve its original next-step signature");
const duplicateLogicalTaskRecords = [
  {
    ...boundHistory[0],
    artifacts: ["outputs/older.md"],
    id: "bound-history-older",
    resultSummary: "Older bounded result",
    sourceHints: ["sources/older.md"],
    turnCount: 1,
    updatedAt: "2026-08-13T08:00:00Z",
  },
  {
    ...boundHistory[0],
    artifacts: ["outputs/newer.md"],
    id: "bound-history-newer",
    resultSummary: "Newest bounded result",
    sourceHints: ["sources/newer.md"],
    turnCount: 2,
    updatedAt: "2026-08-13T09:00:00Z",
  },
];
const collapsedLogicalTaskHistory = state.normalizeHistory(duplicateLogicalTaskRecords);
assert.equal(collapsedLogicalTaskHistory.length, 1, "two sessions for the same registered item and next-step signature must become one recent task");
assert.equal(collapsedLogicalTaskHistory[0].id, "bound-history-newer", "the newest session must own the resumable recent-task identity");
assert.equal(collapsedLogicalTaskHistory[0].resultSummary, "Newest bounded result", "logical-task migration must retain the newest bounded result");
assert.deepEqual(Array.from(collapsedLogicalTaskHistory[0].artifacts), ["outputs/newer.md", "outputs/older.md"], "logical-task migration must retain artifacts from both sessions");
assert.deepEqual(Array.from(collapsedLogicalTaskHistory[0].sourceHints), ["sources/newer.md", "sources/older.md"], "logical-task migration must retain bounded sources from both sessions");
assert.equal(collapsedLogicalTaskHistory[0].turnCount, 3, "logical-task migration must preserve the cumulative recorded-step count");
assert.equal(state.historyTaskIdentity(duplicateLogicalTaskRecords[0]), state.historyTaskIdentity(duplicateLogicalTaskRecords[1]), "task identity must come from the registered item and step signature rather than a random session id");
assert.equal(state.normalizeHistory([
  { id: "unbound-same-title-a", intent: "Same visible title", title: "Same visible title", updatedAt: "2026-08-13T08:00:00Z" },
  { id: "unbound-same-title-b", intent: "Same visible title", title: "Same visible title", updatedAt: "2026-08-13T09:00:00Z" },
]).length, 2, "title equality alone must never erase two unbound user tasks");
const nextStepHistory = state.normalizeHistory([
  duplicateLogicalTaskRecords[1],
  {
    ...duplicateLogicalTaskRecords[0],
    id: "bound-history-followup-step",
    portfolioBinding: {
      ...duplicateLogicalTaskRecords[0].portfolioBinding,
      nextStep: "Prepare the camera-ready experiment table",
      nextStepHash: "step-followup",
    },
    updatedAt: "2026-08-14T09:00:00Z",
  },
]);
assert.equal(nextStepHistory.length, 2, "different next-step signatures for one project must remain separately recoverable");
const nextStepHistoryHtml = view.renderRecentTasks(nextStepHistory, resultDeps);
assert.ok(nextStepHistoryHtml.includes("Confirm the ethics approval"), "a recent task must reveal the bound next step that distinguishes it");
assert.ok(nextStepHistoryHtml.includes("Prepare the camera-ready experiment table"), "a later task for the same project must reveal its different next step");
const duplicateHistoryMigrationStorage = memoryStorage();
duplicateHistoryMigrationStorage.setItem(state.PRIVATE_HISTORY_KEY, JSON.stringify(duplicateLogicalTaskRecords));
assert.equal(state.readHistory({ runtimeMode: "private", storage: duplicateHistoryMigrationStorage }).length, 1, "reading stored history must collapse existing logical-task duplicates");
assert.equal(JSON.parse(duplicateHistoryMigrationStorage.getItem(state.PRIVATE_HISTORY_KEY)).length, 1, "read-time history migration must persist the collapsed record once");
const sameLogicalTaskActiveHtml = view.renderActiveSession({
  executionAvailable: true,
  recentSessions: duplicateLogicalTaskRecords,
  session: boundPortfolioSession,
}, resultDeps);
assert.ok(!sameLogicalTaskActiveHtml.includes('data-work-session-history-resume="bound-history-newer"'), "the current logical task must not also appear in its own recent-task switcher");
const stagedSession = state.updateSession(session, { status: "draft" });
const stagedSessionHtml = view.renderActiveSession({ executionAvailable: true, publicMode: false, session: stagedSession }, resultDeps);
assert.ok(stagedSessionHtml.includes("workSessionLifecycle_ready"), "a staged agenda task must use the shared ready projection rather than an in-progress label");
assert.ok(stagedSessionHtml.includes("data-work-session-run-draft"), "a staged agenda task must expose one explicit confirmation action");
assert.ok(stagedSessionHtml.includes("workSessionRunDraft"), "the private draft action must clearly promise a result");
for (const key of ["workSessionPredictionPrivateRoute", "workSessionPredictionPrivateEffect", "workSessionPredictionPrivateBoundary", "workSessionPredictionPrivateFallback"]) {
  assert.ok(stagedSessionHtml.includes(key), `private execution prediction must expose ${key}`);
}
const publicStagedSessionHtml = view.renderActiveSession({ publicMode: true, session: stagedSession }, resultDeps);
assert.ok(publicStagedSessionHtml.includes("workSessionRunDraftPublic"), "the public draft action must prepare a packet rather than imply model execution");
for (const key of ["workSessionPredictionPublicRoute", "workSessionPredictionPublicEffect", "workSessionPredictionPublicBoundary", "workSessionPredictionPublicFallback"]) {
  assert.ok(publicStagedSessionHtml.includes(key), `public handoff prediction must expose ${key}`);
}
const executablePublicStagedSessionHtml = view.renderActiveSession({ executionAvailable: true, publicMode: true, session: stagedSession }, resultDeps);
assert.ok(executablePublicStagedSessionHtml.includes("workSessionRunDraftPublic"), "public mode must still prepare a packet when stale metadata claims execution is available");
assert.ok(executablePublicStagedSessionHtml.includes('data-action-kind="handoff"'));
const unavailablePrivateStagedSessionHtml = view.renderActiveSession({ executionAvailable: false, publicMode: false, session: stagedSession }, resultDeps);
assert.ok(unavailablePrivateStagedSessionHtml.includes("workSessionRunDraftPublic"), "a private draft without a verified runner must be labeled as a task-packet handoff");
assert.ok(unavailablePrivateStagedSessionHtml.includes('data-action-kind="handoff"'));
const executablePublicReadySessionHtml = view.renderActiveSession({
  executionAvailable: true,
  publicMode: true,
  result: completedAnswer,
  session,
  workspaceWriteAvailable: false,
}, resultDeps);
assert.ok(!executablePublicReadySessionHtml.includes("data-work-session-save-result"), "public copy-only mode must never expose an artifact action");
const publicPacketReadyHtml = view.renderActiveSession({
  publicMode: true,
  result: { status: "completed", execution_status: "copy_ready" },
  session: state.updateSession(session, {
    status: "ready",
    draftResult: { status: "completed", execution_status: "copy_ready" },
  }),
}, resultDeps);
assert.ok(publicPacketReadyHtml.includes("workSessionStatus_copy_ready"), "a prepared public packet must not be mislabeled as an ended research session");
assert.ok(!publicPacketReadyHtml.includes("data-work-session-continue-recommended"), "packet fallback must not imply that it can directly continue with Codex");
assert.ok(publicPacketReadyHtml.includes('class="work-session-continue"'), "packet fallback must keep the next-step composer available");
const publicPacketFooter = publicPacketReadyHtml.match(/<footer class="work-session-result-footer"[^>]*>[\s\S]*?<\/footer>/)?.[0] || "";
assert.equal((publicPacketFooter.match(/class="primary"/g) || []).length, 1, "packet fallback must keep one primary action instead of competing continuation and copy CTAs");
assert.match(publicPacketFooter, /class="primary"[^>]*data-work-session-copy-result/, "copying the execution brief must remain the primary packet-fallback action");
const completedPortfolioHtml = view.renderActiveSession({
  executionAvailable: true,
  publicMode: false,
  result: { ...completedAnswer, model: "gpt-5.6-sol", reasoning_effort: "medium", task_complexity: "standard" },
  session: state.updateSession({
    ...boundPortfolioSession,
    title: "处理已登记事项: Example Review Closeout",
    portfolioBinding: { ...boundPortfolioSession.portfolioBinding, title: "Example Review Closeout" },
  }, { status: "completed" }),
  workspaceWriteAvailable: true,
}, resultDeps);
assert.ok(completedPortfolioHtml.includes("workSessionCompletedPurposeTitle"), "an ended task must explain that the lower panel is a saved Codex result");
assert.ok(completedPortfolioHtml.includes('aria-label="workSessionCompletedResultRegion"'), "assistive technology must hear an ended result region instead of a current task");
assert.ok(completedPortfolioHtml.includes('class="work-session-completed-result"'), "an ended result must use a collapsed archive disclosure");
assert.ok(!completedPortfolioHtml.includes('<details class="work-session-completed-result" open'), "long ended results must stay collapsed by default");
assert.ok(completedPortfolioHtml.includes("Example Review Closeout"), "a bound task must show the project title");
assert.ok(!completedPortfolioHtml.includes("处理已登记事项: Example Review Closeout"), "an ended task must not expose an internal launcher prefix as its title");
assert.ok(!completedPortfolioHtml.includes('class="work-session-current-step"'), "an ended bound task must not repeat its goal below the title");
assert.ok(!completedPortfolioHtml.includes('class="work-session-continue"'), "an ended task must not offer a contradictory current-task composer");
assert.ok(!completedPortfolioHtml.includes("data-work-session-continue-recommended"), "an ended task must not offer a continuation action that cannot run");
assert.ok(!completedPortfolioHtml.includes("data-work-session-save-result"), "an ended task must not silently restart execution through Create Markdown");
assert.ok(!completedPortfolioHtml.includes("gpt-5.6-sol"), "an ended result archive must hide technical runtime details from the default view");
const stagedMutationPlan = state.handoffMutationPlan(
  stagedSession,
  state.addCard(stagedSession, { id: "draft-context", title: "Draft context" }),
  { handoffActive: false },
);
assert.equal(stagedMutationPlan.session.status, "draft", "editing a staged task must preserve its explicit confirmation gate");
const activeWithHistoryHtml = view.renderActiveSession({
  executionAvailable: true,
  recentSessions: [{ ...history[0], id: "other-history" }],
  result: completedAnswer,
  session,
}, resultDeps);
assert.ok(activeWithHistoryHtml.includes("work-session-recent-panel"), "recent tasks must remain reachable without leaving the active task");
assert.match(activeWithHistoryHtml, /aria-label="workSessionRecentContinue: [^"]+"/, "repeated recent-task actions must name the task they affect");
const busySessionHtml = view.renderActiveSession({
  executionAvailable: true,
  result: { status: "queued" },
  session,
}, resultDeps);
assert.match(busySessionHtml, /data-work-session-new[^>]*disabled/, "running tasks must disable task replacement");
assert.match(busySessionHtml, /data-work-session-complete[^>]*disabled/, "running tasks must disable premature completion");
assert.match(busySessionHtml, /data-work-session-remove-card[^>]*disabled/, "running tasks must keep their submitted context stable");
assert.match(busySessionHtml, /name="source_file"[^>]*disabled/, "running tasks must not accept a file selection that polling cannot safely restore");
const pdfDeckHtml = view.renderDeck([{ id: "pdf-source", path: "08_exports/public_starter/example.pdf", title: "Example PDF" }], {
  ...resultDeps,
  previewButton: boundedPreviewButton,
});
assert.ok(pdfDeckHtml.includes('data-pdf-preview-path="08_exports/public_starter/example.pdf"'), "public-safe PDF context cards must open the PDF preview instead of the Markdown preview");
const corpusDeckHtml = view.renderDeck([{ id: "corpus-source", path: "corpus/papers/example.pdf", title: "Private corpus PDF" }], {
  ...resultDeps,
  previewButton: boundedPreviewButton,
});
assert.ok(!corpusDeckHtml.includes("data-pdf-preview-path"), "public starter context cards must not expose the private corpus preview surface");
const unpreviewableDeckHtml = view.renderDeck([{ id: "private-source", path: "/opt/private/SECRET.PDF", title: "Private reference" }], resultDeps);
assert.ok(!unpreviewableDeckHtml.includes("data-pdf-preview-path"), "unresolved absolute paths must remain references instead of showing a broken preview action");
assert.ok(!unpreviewableDeckHtml.includes("data-preview-path"), "unresolved absolute paths must not bypass the bounded preview resolver");
const externalDeckHtml = view.renderDeck([{ id: "external-source", path: "https://example.com/paper.pdf", title: "External paper" }], resultDeps);
assert.ok(externalDeckHtml.includes('href="https://example.com/paper.pdf"'), "external source cards must use a normal safe link instead of the local PDF endpoint");

function interactionSurface(controls, details) {
  return {
    querySelector(selector) {
      return selector === "[data-work-session-selected-file='true']" ? this.pendingDrop || null : null;
    },
    querySelectorAll(selector) {
      if (selector === "input, textarea, select") return controls;
      if (selector === "details") return details;
      return [];
    },
  };
}
const oldIntent = { checked: false, files: [], selectionEnd: 18, selectionStart: 4, type: "textarea", value: "Unsubmitted follow-up" };
const oldMode = { checked: false, files: [], type: "select-one", value: "artifact" };
let currentInteractionSurface = interactionSurface([oldIntent, oldMode], [
  { className: "work-session-continue", open: true },
  { className: "work-session-context", open: false },
]);
const interactionRoot = {
  matches: () => false,
  querySelector: () => currentInteractionSurface,
};
context.document.activeElement = oldIntent;
const interactionSnapshot = context.ResearchOSWorkSessionWorkbenchService.captureInteraction(interactionRoot);
const restoredIntent = {
  checked: false,
  files: [],
  focus() { this.focused = true; },
  setSelectionRange(start, end) { this.restoredSelection = [start, end]; },
  type: "textarea",
  value: "",
};
const restoredMode = { checked: false, files: [], type: "select-one", value: "auto" };
const restoredDetails = [
  { className: "work-session-result-actions", open: false },
  { className: "work-session-continue", open: false },
  { className: "work-session-context", open: true },
];
currentInteractionSurface = interactionSurface([restoredIntent, restoredMode], restoredDetails);
assert.equal(context.ResearchOSWorkSessionWorkbenchService.restoreInteraction(interactionRoot, interactionSnapshot), true);
assert.equal(restoredIntent.value, "Unsubmitted follow-up", "background rendering must restore an unfocused draft");
assert.equal(restoredMode.value, "artifact", "background rendering must restore the selected response mode");
assert.deepEqual(restoredIntent.restoredSelection, [4, 18], "background rendering must restore the caret selection");
assert.equal(restoredDetails[0].open, false, "newly inserted panels must keep their own default disclosure state");
assert.equal(restoredDetails[1].open, true, "background rendering must restore the matching progressive-disclosure panel by identity");
assert.equal(restoredDetails[2].open, false, "background rendering must not transfer disclosure state to a neighboring panel");
assert.equal(restoredIntent.focused, true, "background rendering must return focus to the active composer control");
const detachedIntent = { checked: false, files: [], selectionEnd: 14, selectionStart: 0, type: "textarea", value: "Draft before full render" };
currentInteractionSurface = interactionSurface([detachedIntent], [{ className: "work-session-continue", open: true }]);
context.document.activeElement = detachedIntent;
const replacementIntent = { checked: false, files: [], focus() { this.focused = true; }, type: "textarea", value: "" };
const replacementDetails = [{ className: "work-session-continue", open: false }];
const replacementSurface = interactionSurface([replacementIntent], replacementDetails);
const replacementRoot = { matches: () => false, querySelector: () => replacementSurface };
assert.equal(context.ResearchOSWorkSessionWorkbenchService.renderPreservingInteraction(
  interactionRoot,
  () => {},
  { resolveRoot: () => replacementRoot },
), true, "full dashboard rendering must support restoring into the replacement Work Session root");
assert.equal(replacementIntent.value, "Draft before full render", "a replacement Work Session root must receive the unsubmitted draft");
assert.equal(replacementDetails[0].open, true, "a replacement Work Session root must keep the continuation composer expanded");
assert.equal(replacementIntent.focused, true, "a replacement Work Session root must recover composer focus");
const oldModelControl = { checked: false, closest: () => ({}), files: [], type: "select-one", value: "gpt-5.5" };
currentInteractionSurface = interactionSurface([oldModelControl], [{ className: "work-session-model-options", open: true }]);
const modelSnapshot = context.ResearchOSWorkSessionWorkbenchService.captureInteraction(interactionRoot);
const newModelControl = { checked: false, closest: () => ({}), files: [], type: "select-one", value: "company/research-model" };
const modelDetails = [{ className: "work-session-model-options", open: false }];
currentInteractionSurface = interactionSurface([newModelControl], modelDetails);
context.ResearchOSWorkSessionWorkbenchService.restoreInteraction(
  interactionRoot,
  modelSnapshot,
  { skipControlsWithin: ".work-session-model-options" },
);
assert.equal(newModelControl.value, "company/research-model", "model controls must reflect the newly persisted selection");
assert.equal(modelDetails[0].open, true, "model updates must still preserve the panel disclosure state");
const selectedFile = { checked: false, files: [{ name: "paper.pdf" }], type: "file", value: "paper.pdf" };
currentInteractionSurface = interactionSurface([selectedFile], []);
let renderedOverFile = false;
assert.equal(context.ResearchOSWorkSessionWorkbenchService.renderPreservingInteraction(
  interactionRoot,
  () => { renderedOverFile = true; }
), false, "background rendering must pause while a non-restorable file selection exists");
assert.equal(renderedOverFile, false, "a selected file must never be erased by polling");
currentInteractionSurface = interactionSurface([], []);
currentInteractionSurface.pendingDrop = {};
renderedOverFile = false;
assert.equal(context.ResearchOSWorkSessionWorkbenchService.renderPreservingInteraction(
  interactionRoot,
  () => { renderedOverFile = true; }
), false, "background rendering must also preserve a drag-and-drop file held by the event owner");
assert.equal(renderedOverFile, false, "a dropped file must never be erased by polling before submit");
const longIntent = "Understand this paper, compare it with the current project, and preserve every decision boundary in the handoff";
assert.equal(state.createSession({ intent: longIntent }).title, longIntent, "Work Session titles must not silently truncate the user's goal");
assert.equal(state.normalizeSession({ id: "legacy", intent: longIntent, title: longIntent.slice(0, 72) }).title, longIntent, "legacy truncated Work Session titles must migrate on read");
assert.equal(
  state.normalizeSession({ id: "legacy-tier", intent: "Resume old result", draftResult: { model_tier: "deep" } }).draftResult.task_complexity,
  "deep",
  "legacy model-tier results must migrate to task-complexity semantics on read",
);
assert.equal(
  state.normalizeSession({
    id: "legacy-public-packet",
    intent: "Reuse a ready packet",
    status: "active",
    draftResult: { execution_status: "copy_ready", status: "completed" },
  }).status,
  "ready",
  "persisted copy-ready packets must migrate to an adjustable ready state",
);
const migrationStorage = memoryStorage();
migrationStorage.setItem(state.PUBLIC_KEY, JSON.stringify({
  id: "stored-public-packet",
  intent: "Reuse a stored packet",
  status: "active",
  draftResult: { execution_status: "copy_ready", status: "completed" },
}));
assert.equal(state.read({ runtimeMode: "public_starter", storage: migrationStorage }).status, "ready");
assert.equal(JSON.parse(migrationStorage.getItem(state.PUBLIC_KEY)).status, "ready", "read-time schema migration must persist the adjustable packet status once");
const completedAnswerMigrationStorage = memoryStorage();
completedAnswerMigrationStorage.setItem(state.PRIVATE_KEY, JSON.stringify({
  id: "legacy-completed-answer",
  intent: "Review completed answer",
  status: "active",
  draftResult: { answer: "Completed result", status: "completed" },
}));
assert.equal(state.read({ runtimeMode: "private", storage: completedAnswerMigrationStorage }).status, "ready", "any persisted completed result must recover as ready for review, not remain in progress");
const legacyHandoff = state.handoffPayload(state.createSession({ intent: longIntent }), (key) => key);
legacyHandoff.title = longIntent.slice(0, 72);
assert.equal(context.ResearchOSDoingBoardState.normalizeItem(legacyHandoff).title, longIntent, "legacy prepared Handoff titles must migrate from their full goal note");

const withCard = state.addCard(session, {
  id: "paper:1",
  path: "01_knowledge/papers/paper-1.md",
  title: "Paper One",
  type: "paper",
});
assert.equal(withCard.cards.length, 2);
assert.equal(state.addCard(withCard, withCard.cards[1]).cards.length, 2, "working deck must deduplicate cards");
const replacedCard = state.addCard(withCard, { ...withCard.cards[1], title: "Updated Paper One" });
assert.equal(replacedCard.cards.find((card) => card.id === "paper:1").title, "Updated Paper One", "re-adding a card must refresh its metadata");

const boundedSession = state.normalizeSession({
  ...session,
  cards: Array.from({ length: 20 }, (_, index) => ({ id: `paper:${index}`, title: `Paper ${index}` })),
  sourceHints: Array.from({ length: 12 }, (_, index) => `source-${index}`),
  status: "unknown",
});
assert.equal(boundedSession.cards.length, 12, "working decks must stay within their 12-card context bound");
assert.equal(boundedSession.sourceHints.length, 8, "source hints must stay within their context bound");
assert.equal(boundedSession.status, "active", "unknown status values must fail closed to active");
const healedTerminalSession = state.normalizeSession({
  id: "terminal-session-stored-running",
  intent: "Inspect the prior dispatch",
  status: "running",
  draftResult: { execution_status: "delivery_unknown", status: "failed" },
});
assert.equal(healedTerminalSession.status, "active", "a terminal result must heal a stale persisted running lock on read");
const sessionWithNewestCard = state.addCard(boundedSession, { id: "paper:new", title: "Newest Paper" });
assert.equal(sessionWithNewestCard.cards.length, 12, "adding a card at capacity must preserve the working-deck bound");
assert.ok(sessionWithNewestCard.cards.some((card) => card.id === "paper:new"), "adding a card at capacity must retain the new user selection");
assert.ok(!sessionWithNewestCard.cards.some((card) => card.id === "paper:0"), "adding a card at capacity must evict the oldest replaceable card instead of silently dropping the new one");

const interruptedSession = state.normalizeSession({
  ...session,
  clientRequestId: "request-reload",
  draftResult: { status: "running", work_session_id: session.id },
  status: "running",
  updatedAt: "2026-07-15T10:00:00.000Z",
});
const completedAfterReload = {
  answer: "Recovered result after reload",
  created_at: "2026-07-15T10:00:01.000Z",
  id: "run-after-reload",
  client_request_id: "request-reload",
  status: "completed",
  work_session_id: session.id,
};
const reconciledAfterReload = state.reconcileRun(interruptedSession, [completedAfterReload]);
assert.equal(reconciledAfterReload.status, "ready", "a completed server run must recover as ready for review after a page reload");
assert.equal(reconciledAfterReload.latestRunId, "run-after-reload", "reload reconciliation must bind the recovered server run to the task");
assert.equal(reconciledAfterReload.draftResult.answer, "Recovered result after reload", "reload reconciliation must preserve the completed result for rendering");
const activeSessionWithExactRun = state.normalizeSession({
  ...session,
  latestRunId: "run-after-reload",
  status: "active",
});
assert.equal(state.reconcileRun(activeSessionWithExactRun, [completedAfterReload]).status, "ready", "an exact persisted run binding must reconcile even if an older client left the session active");
assert.equal(
  context.ResearchOSWorkSessionRouter.resultProjectionForSession([completedAfterReload], activeSessionWithExactRun).state,
  "matched",
  "Review may show a result only when Work Session, run, and request identities match",
);
const crossSessionProjection = context.ResearchOSWorkSessionRouter.resultProjectionForSession([completedAfterReload], {
  ...activeSessionWithExactRun,
  id: "session-2",
});
assert.equal(crossSessionProjection.state, "withheld", "an S1 result reused as S2's latest run must fail closed");
assert.equal(crossSessionProjection.reason, "work_session_id_mismatch");
assert.equal(crossSessionProjection.result, null, "a mismatched result must not reach result or mutation renderers");
const missingIdentityProjection = context.ResearchOSWorkSessionRouter.resultProjectionForSession([{ ...completedAfterReload, work_session_id: "" }], activeSessionWithExactRun);
assert.equal(missingIdentityProjection.state, "withheld", "a result missing its Work Session identity must fail closed");
assert.equal(missingIdentityProjection.reason, "missing_result_work_session_id");
const activeSessionWithoutRunBinding = state.normalizeSession({ ...session, clientRequestId: "", latestRunId: "", status: "active" });
assert.equal(state.reconcileRun(activeSessionWithoutRunBinding, [completedAfterReload]), null, "an active session without an exact run binding must not attach an old result by title or session id");
const unrelatedOldRun = { ...completedAfterReload, client_request_id: "request-old", created_at: "2026-07-15T09:00:00.000Z", id: "old-run" };
assert.equal(state.reconcileRun(interruptedSession, [unrelatedOldRun], {
  now: Date.parse("2026-07-15T10:01:00.000Z"),
}), null, "reload reconciliation must not attach an older run from the same task");
const recoveredStaleSession = state.reconcileRun(interruptedSession, [], {
  reconciliation: { state: "not_found", client_request_id: "request-reload" },
});
assert.equal(recoveredStaleSession.status, "active", "an exact durable not-found receipt may release the task for an explicit same-request retry");
assert.equal(recoveredStaleSession.draftResult.status, "failed", "not-found recovery must preserve a visible receipt");
assert.equal(recoveredStaleSession.draftResult.error_envelope.side_effects, "none", "only the exact server ledger may prove that no run exists");
assert.equal(recoveredStaleSession.draftResult.error_envelope.retryable, true);
const retryableFailureHtml = view.renderActiveSession({
  executionAvailable: true,
  result: recoveredStaleSession.draftResult,
  session: recoveredStaleSession,
}, resultDeps);
assert.ok(retryableFailureHtml.includes("data-work-session-retry"), "a failed run with proven side_effects=none must expose exact same-request retry");
assert.ok(retryableFailureHtml.includes("workSessionEndKeepReceipt"), "safe retry must remain optional; ending the task preserves the failure receipt");
assert.ok(retryableFailureHtml.includes("workSessionSafePointRetry"), "safe retry must name the server-proven no-effects point");
assert.ok(!retryableFailureHtml.includes("data-work-session-run-form"), "safe retry must not be confused with an edited follow-up submission");
const leaseExpiredAfterReload = state.reconcileRun(interruptedSession, [{
  id: "run-expired-after-reload",
  client_request_id: "request-reload",
  lease_expired: true,
  status: "running",
  work_session_id: session.id,
}]);
assert.equal(leaseExpiredAfterReload.status, "active", "an expired server lease must release the running compatibility lock");
assert.equal(leaseExpiredAfterReload.runLifecycle, "running", "lease expiry is an observation failure, not a fabricated terminal run");
assert.equal(leaseExpiredAfterReload.runObservation, "lease_expired");
const ambiguousAfterReload = state.reconcileRun(state.normalizeSession({
  ...interruptedSession,
  latestRunId: "run-ambiguous",
}), [], {
  reconciliation: { state: "ambiguous", client_request_id: "request-reload" },
});
assert.equal(ambiguousAfterReload.status, "active");
assert.equal(ambiguousAfterReload.runLifecycle, "running", "ambiguous reconciliation must preserve the bound run lifecycle");
assert.equal(ambiguousAfterReload.runObservation, "reconcile_failed");
assert.equal(ambiguousAfterReload.draftResult.error_envelope.error_type, "run_reconcile_ambiguous");
assert.equal(ambiguousAfterReload.draftResult.error_envelope.retryable, false, "ambiguous reconciliation must never authorize a second POST");
const impactFailure = context.ResearchOSResultEnvelope.failureResult("runner_execution_failed", {
  client_request_id: "request-impact-unknown",
  run_id: "run-impact-unknown",
  work_session_id: session.id,
}).run;
const impactFailureSession = state.updateSession(session, {
  clientRequestId: "request-impact-unknown",
  draftResult: impactFailure,
  latestRunId: "run-impact-unknown",
  status: "active",
});
const impactFailureHtml = view.renderActiveSession({ executionAvailable: true, result: impactFailure, session: impactFailureSession }, resultDeps);
assert.ok(impactFailureHtml.includes("workSessionImpactNeedsVerification"), "unknown side effects must be described as an impact check, not generic processing");
assert.ok(impactFailureHtml.includes("data-work-session-reconcile"), "unknown side effects must route to receipt inspection");
assert.ok(impactFailureHtml.includes("workSessionSafePointImpact"), "impact-unknown recovery must name what is and is not confirmed");
assert.ok(!impactFailureHtml.includes("data-work-session-retry"), "unknown side effects must never expose retry");
assert.ok(!impactFailureHtml.includes("data-work-session-run-form"), "unknown side effects must block edited resubmission");
const invalidWritebackSession = state.updateSession(session, {
  draftResult: { response_mode: "writeback", result_envelope: { schema_id: "broken" }, status: "completed" },
  status: "ready",
});
assert.equal(invalidWritebackSession.resultMode, "invalid");
const invalidWritebackHtml = view.renderActiveSession({ executionAvailable: true, result: invalidWritebackSession.draftResult, session: invalidWritebackSession }, resultDeps);
assert.ok(!invalidWritebackHtml.includes('data-result-primary-action="open_review"'), "an invalid writeback envelope must not expose Review as if a candidate existed");
assert.ok(!invalidWritebackHtml.includes("data-work-session-writeback"), "an invalid result must expose inspection, not a writeback proposal");
assert.equal(state.reconcileRun(interruptedSession, [], {
  reconciliation: { state: "ambiguous", client_request_id: "request-other" },
}), null, "a reconciliation receipt for another request must not mutate this task");
const endedAwaitingLateResult = state.normalizeSession({
  ...session,
  clientRequestId: "request-late-result",
  draftResult: { id: "run-late-result", status: "running" },
  latestRunId: "run-late-result",
  status: "completed",
});
const attachedLateResult = state.reconcileRun(endedAwaitingLateResult, [{
  answer: "Late result retained as a receipt",
  client_request_id: "request-late-result",
  id: "run-late-result",
  response_mode: "answer",
  status: "completed",
  work_session_id: session.id,
}]);
assert.equal(attachedLateResult.status, "completed", "a late terminal result must not reopen an ended Work Session");
assert.equal(attachedLateResult.sessionLifecycle, "ended");
assert.equal(attachedLateResult.runLifecycle, "completed");
assert.equal(attachedLateResult.resultMode, "answer");
assert.equal(attachedLateResult.draftResult.answer, "Late result retained as a receipt", "the ended session must keep the late result recoverable");
assert.equal(state.lifecycleProjection(attachedLateResult).state, "late_result_ready");

const sameTitleSessions = ["a", "b", "c"].map((suffix) => state.normalizeSession({
  ...session,
  id: `same-title-session-${suffix}`,
  title: "Same visible title",
  intent: "Same visible title",
  clientRequestId: `same-title-request-${suffix}`,
  latestRunId: `same-title-run-${suffix}`,
  portfolioBinding: { itemId: suffix === "c" ? "commitment-b" : "commitment-a", nextStepHash: `step-${suffix}`, providerId: "research_portfolio" },
  candidate: suffix === "a" ? { candidate_id: "candidate-late-a", object_ref: { type: "work_session", id: "same-title-session-a" } } : null,
  status: suffix === "a" ? "completed" : suffix === "b" ? "active" : "paused",
}));
const sameTitleRuns = [
  { answer: "Late A", client_request_id: "same-title-request-a", id: "same-title-run-a", response_mode: "writeback", status: "completed", work_session_id: "same-title-session-a" },
  { answer: "Current B", client_request_id: "same-title-request-b", id: "same-title-run-b", response_mode: "answer", status: "completed", work_session_id: "same-title-session-b" },
];
const sameTitleRegistry = state.sessionRegistryProjection(
  sameTitleSessions[1],
  [sameTitleSessions[0], sameTitleSessions[2]],
  sameTitleRuns,
);
assert.equal(sameTitleRegistry.length, 3, "three same-title sessions across two Commitments must survive the Work registry");
assert.equal(new Set(sameTitleRegistry.map((item) => item.session_id)).size, 3, "Work filters must bind by session identity rather than visible title");
assert.equal(new Set(sameTitleRegistry.map((item) => item.logical_task_id)).size, 3, "distinct Commitment/step bindings must not collapse into one logical task");
assert.equal(sameTitleRegistry.find((item) => item.session_id === "same-title-session-a").work_state, "needs_review", "an ended session with a late result remains recoverable as Needs Review");
assert.equal(sameTitleRegistry.find((item) => item.session_id === "same-title-session-b").work_state, "needs_review", "the selected session moves from Active to Needs Review only for its exact completed result");
assert.equal(sameTitleRegistry.find((item) => item.session_id === "same-title-session-c").work_state, "waiting", "the second Commitment remains independently waiting");
assert.equal(
  context.ResearchOSWorkSessionRouter.resultProjectionForSession(sameTitleRuns, sameTitleSessions[1]).result.answer,
  "Current B",
  "the current same-title session must bind only its exact result",
);
const lateResultCrossBind = context.ResearchOSWorkSessionRouter.resultIdentityProjection(sameTitleRuns[0], sameTitleSessions[1]);
assert.equal(lateResultCrossBind.state, "withheld", "a late result from a same-title sibling must fail closed");
assert.equal(lateResultCrossBind.reason, "work_session_id_mismatch");
const sameTitleCandidate = state.handoffPayload(sameTitleSessions[0], (key) => key);
assert.equal(sameTitleCandidate.work_session_id, "same-title-session-a", "a candidate handoff must preserve its exact late-result Work Session identity");
assert.equal(sameTitleCandidate.candidate.object_ref.id, "same-title-session-a", "candidate identity must not be rewritten from the shared visible title");


state.write(withCard, { runtimeMode: "private", storage });
assert.equal(state.read({ runtimeMode: "private", storage }).cards[1].id, "paper:1");
assert.equal(state.read({ runtimeMode: "public_starter", storage }), null, "public/private sessions must remain isolated");
storage.setItem(state.PUBLIC_KEY, "{broken-json");
assert.equal(state.read({ runtimeMode: "public_starter", storage }), null, "corrupt browser state must fail closed without breaking startup");
state.writeHistory(history, { runtimeMode: "private", storage });
assert.equal(state.readHistory({ runtimeMode: "private", storage })[0].id, history[0].id);
assert.equal(state.readHistory({ runtimeMode: "public_starter", storage }).length, 0, "public/private recent-task summaries must remain isolated");
const throwingStorage = {
  getItem: () => null,
  removeItem: () => { throw new Error("blocked"); },
  setItem: () => { throw new Error("quota"); },
};
assert.equal(state.write(withCard, { runtimeMode: "private", storage: throwingStorage }).id, withCard.id, "a blocked browser storage write must not crash the in-memory task");
assert.equal(state.write(null, { runtimeMode: "private", storage: throwingStorage }), null, "a blocked browser storage clear must fail safely");
assert.equal(state.writeHistory(history, { runtimeMode: "private", storage: throwingStorage })[0].id, history[0].id, "a blocked history write must keep the normalized in-memory summaries usable");

const payload = state.handoffPayload(withCard, (key) => key);
assert.equal(payload.action, "work_session_handoff");
assert.equal(payload.work_session_id, withCard.id);
assert.equal(payload.source_cards.length, 2);
assert.equal(payload.path, "/tmp/paper.pdf", "Handoff should retain the task's primary source path");
assert.equal(payload.evidence_state, "candidate");
assert.equal(payload.id, `handoff:work-session:${withCard.id}`);
assert.equal(payload.admission_state.decision_state, "proposed");
assert.equal(payload.admission_state.mutation_state, "not_requested");
assert.equal(payload.current_state, "workSessionCurrentAuthorityState");
assert.equal(payload.proposed_state, "workSessionProposedAuthorityState");
assert.equal(payload.impact_scope, "workSessionImpactScope");
assert.equal(payload.sensitivity, "internal");
assert.equal(payload.admission_state.validation_state, "unvalidated");
assert.equal(Object.hasOwn(payload, "result"), false, "a handoff-only Review item must not fabricate a machine result");
assert.ok(payload.note.includes("Source and derived claims remain candidates"));
const sourceOnlyPayload = state.handoffPayload(session, (key) => key);
assert.equal(sourceOnlyPayload.path, "/tmp/paper.pdf", "Handoff must retain a PDF/link source when no cards are selected");
const resultPayload = state.handoffPayload(state.updateSession(session, {
  draftResult: { answer: "Candidate result that the user has already reviewed", status: "completed" },
}), (key) => key);
assert.ok(resultPayload.note.includes("workSessionResultForReview:\nCandidate result"), "writeback review must carry the visible page result into Handoff");

const readySession = state.updateSession(withCard, { handoffKey: "task:paper", status: "ready" });
const completedSession = state.syncHandoffStatus(readySession, "task", "task:paper", "completed");
assert.equal(completedSession.status, "completed", "archiving the linked handoff must complete the Work Session");
const restoredSession = state.syncHandoffStatus(completedSession, "task", "task:paper", "ready");
assert.equal(restoredSession.status, "ready", "restoring the linked handoff must reactivate the Work Session");
const withdrawnSession = state.syncHandoffStatus(restoredSession, "task", "task:paper", "active");
assert.equal(withdrawnSession.status, "active", "withdrawing the linked handoff must return the Work Session to active");
assert.equal(withdrawnSession.handoffKey, "", "an active Work Session must be allowed to prepare a new handoff");
assert.equal(state.syncHandoffStatus(readySession, "task", "task:other", "completed"), null, "unrelated Handoff items must not mutate the Work Session");

const changedReadySession = state.updateSession(readySession, { intent: "Revised goal", title: "Revised goal" });
const liveSyncPlan = state.handoffMutationPlan(readySession, changedReadySession, {
  handoffActive: true,
  itemKey: () => "task:paper",
  text: (key) => key,
});
assert.equal(liveSyncPlan.session.status, "ready", "editing a prepared Work Session must keep its Handoff ready");
assert.equal(liveSyncPlan.session.intent, "Revised goal", "the synchronized Handoff must use the revised goal");
assert.equal(liveSyncPlan.payload.title, "Revised goal", "the Handoff payload must update with the Work Session");
assert.equal(liveSyncPlan.removeKey, "", "a stable Handoff key should update in place");

const reopenedPlan = state.handoffMutationPlan(completedSession, state.addCard(completedSession, {
  id: "paper:2",
  title: "Paper Two",
  type: "paper",
}), {
  handoffActive: false,
  itemKey: () => "task:paper-two",
  text: (key) => key,
});
assert.equal(reopenedPlan.session.status, "active", "editing a completed session must reopen it as active");
assert.equal(reopenedPlan.session.handoffKey, "", "reopened sessions must not remain bound to archived Handoff items");
assert.equal(reopenedPlan.payload, null, "reopening an archived session must require a fresh explicit handoff");

let lifecycleSession = null;
let lifecycleDoingItems = [];
let lifecycleRefreshes = 0;
let lifecycleWorkspace = "";
let lifecycleItemPanel = "";
let lifecycleInboxStatus = "";
let lifecycleStatus = "";
let lifecycleHistory = [];
let archivedHandoff = null;
let lifecycleNewConfirmations = 0;
const lifecycleItemKey = (item = {}) => item.work_session_id ? `task:${item.work_session_id}` : String(item.key || "");
const lifecycleText = (key) => ({
  workSessionDefaultBoundaryPrivate: "Private candidate boundary",
  workSessionDefaultBoundaryPublic: "Public candidate boundary",
  workSessionInputSourceType: "Input source",
  workSessionSourceCardHint: "Source supplied for this task",
})[key] || key;
const lifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  addDoingItem(item, status) {
    const next = { ...item, status };
    const key = lifecycleItemKey(next);
    lifecycleDoingItems = [...lifecycleDoingItems.filter((candidate) => lifecycleItemKey(candidate) !== key), next];
  },
  archiveHandoff: (type, id) => { archivedHandoff = { id, type }; },
  confirmNew: () => { lifecycleNewConfirmations += 1; return true; },
  decodePayload: (encoded) => JSON.parse(encoded),
  getDoingItems: () => lifecycleDoingItems,
  getHistory: () => lifecycleHistory,
  getSession: () => lifecycleSession,
  openWorkspace: (workspace) => { lifecycleWorkspace = workspace; },
  openItemPanel: (panel) => { lifecycleItemPanel = panel; },
  publicMode: () => true,
  refreshSurfaces: () => { lifecycleRefreshes += 1; },
  removeDoingItem: (key) => { lifecycleDoingItems = lifecycleDoingItems.filter((item) => lifecycleItemKey(item) !== key); },
  renderHome: () => { lifecycleRefreshes += 1; },
  saveSession: (next) => { lifecycleSession = next; return lifecycleSession; },
  saveHistory: (next) => { lifecycleHistory = next; return lifecycleHistory; },
  scheduleInboxStatus: (message) => { lifecycleInboxStatus = message; },
  showStatus: (message) => { lifecycleStatus = message; },
  submitSession: async (next) => ({ ok: true, run: { id: "run-lifecycle", status: "queued", work_session_id: next.id } }),
  templateLanguage: () => "en",
}, {
  inboxStatusIsActive: (status) => status === "local",
  itemKey: lifecycleItemKey,
  router: context.ResearchOSWorkSessionRouter,
  state,
  translate: lifecycleText,
});

let stagedLifecycleSession = null;
let stagedLifecycleStatus = "";
const stagedLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  getSession: () => stagedLifecycleSession,
  publicMode: () => true,
  refreshSurfaces: () => {},
  saveSession: (next) => { stagedLifecycleSession = next; return next; },
  showStatus: (message) => { stagedLifecycleStatus = message; },
  submitSession: async (next) => ({ ok: true, run: { id: "run-staged", status: "completed", work_session_id: next.id } }),
}, {
  router: context.ResearchOSWorkSessionRouter,
  state,
  translate: lifecycleText,
});
const stagedDraft = stagedLifecycle.draft({
  evidenceBoundary: "Explicit candidate-only judgment boundary",
  intent: "Prepare the registered agenda task",
  responseMode: "answer",
  sensitivity: "private",
});
assert.equal(stagedDraft.ok, true);
assert.equal(stagedLifecycleSession.status, "draft", "agenda preparation must remain a draft until the user confirms execution");
assert.equal(stagedLifecycleSession.evidenceBoundary, "Explicit candidate-only judgment boundary", "an owner-supplied receipt boundary must not be replaced by a generic default");
assert.equal(stagedLifecycleSession.sensitivity, "private", "an explicit stricter sensitivity must survive draft creation");
assert.equal(stagedLifecycleStatus, "workSessionDrafted");
const stagedRun = stagedLifecycle.callbacks.onRunDraft();
assert.equal(stagedLifecycleSession.status, "running", "the explicit draft action must be the point where execution begins");
await stagedRun;
assert.equal(stagedLifecycleSession.status, "ready", "a completed model run must stay visibly ready for user review");

let rejectedLifecycleSession = null;
let rejectedLifecycleSubmissions = 0;
const rejectedLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  executionAvailable: () => true,
  getSession: () => rejectedLifecycleSession,
  publicMode: () => false,
  refreshSurfaces: () => {},
  saveSession: (next) => { rejectedLifecycleSession = next; return next; },
  submitSession: async (next) => {
    rejectedLifecycleSubmissions += 1;
    if (rejectedLifecycleSubmissions === 1) throw new Error("network unavailable secret");
    return { ok: true, run: { id: "run-after-rejection", status: "queued", work_session_id: next.id } };
  },
}, {
  router: context.ResearchOSWorkSessionRouter,
  state,
  translate: lifecycleText,
});
rejectedLifecycle.draft({ intent: "Recover after transport rejection", responseMode: "answer" });
const rejectedLifecycleResult = await rejectedLifecycle.callbacks.onRunDraft();
assert.equal(rejectedLifecycleResult.ok, false, "a rejected submit must resolve to a contained failure result");
assert.equal(rejectedLifecycleResult.error_type, "submit_rejected");
assert.equal(rejectedLifecycleResult.retryable, false, "delivery unknown cannot be retried before B7 reconcile/dedupe");
assert.equal(rejectedLifecycleSession.status, "active", "a rejected submit must release the running state");
assert.equal(rejectedLifecycleSession.draftResult.status, "failed", "the contained failure receipt must remain visible");
assert.equal(rejectedLifecycleSession.draftResult.execution_status, "delivery_unknown", "client rejection cannot prove whether delivery occurred");
assert.equal(rejectedLifecycleSession.latestRunId, "", "a client-side rejection must not create a fake server run binding");
assert.ok(rejectedLifecycleSession.clientRequestId.startsWith("request-"), "the client request id must be persisted before dispatch");
const priorCompletedRun = {
  answer: "Earlier completed result",
  id: "run-before-rejection",
  status: "completed",
  work_session_id: rejectedLifecycleSession.id,
};
assert.equal(
  context.ResearchOSWorkSessionRouter.resultForSession([priorCompletedRun], rejectedLifecycleSession).execution_status,
  "delivery_unknown",
  "a current local failure receipt must not be hidden by an older server result from the same session",
);
assert.equal(
  JSON.stringify({ result: rejectedLifecycleResult, session: rejectedLifecycleSession }).includes("network unavailable secret"),
  false,
  "the containment receipt must not leak the raw transport exception",
);
assert.equal(
  state.turnFromResult("Failed question", { status: "failed", message: "network sensitive-diagnostic::private-token" }),
  null,
  "failed diagnostics must never become prompt-bearing conversation turns",
);
state.write(rejectedLifecycleSession, { runtimeMode: "private", storage });
assert.equal(storage.getItem(state.PRIVATE_KEY).includes("network unavailable secret"), false, "raw transport diagnostics must not enter browser storage");
const rejectedLifecycleRetry = await rejectedLifecycle.callbacks.onRun();
assert.equal(rejectedLifecycleRetry.ok, false);
assert.equal(rejectedLifecycleRetry.retryable, false);
assert.equal(rejectedLifecycleSubmissions, 1, "delivery unknown must not start a second submission before inspection");
assert.equal(rejectedLifecycleSession.status, "active");
assert.equal(rejectedLifecycleSession.latestRunId, "");

const safeRetryFailure = context.ResearchOSResultEnvelope.failureResult("run_reconcile_not_found", {
  client_request_id: "request-safe-retry",
  response_mode: "answer",
  work_session_id: session.id,
}).run;
let safeRetryLifecycleSession = state.updateSession(state.createSession({
  intent: "Retry only after exact not-found",
  responseMode: "answer",
}), {
  clientRequestId: "request-safe-retry",
  draftResult: safeRetryFailure,
  status: "active",
});
let safeRetrySubmission = null;
const safeRetryLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  executionAvailable: () => true,
  getResult: () => safeRetryLifecycleSession.draftResult,
  getSession: () => safeRetryLifecycleSession,
  publicMode: () => false,
  refreshSurfaces: () => {},
  saveSession: (next) => { safeRetryLifecycleSession = next; return next; },
  submitSession: async (next, options) => {
    safeRetrySubmission = { next, options };
    return { ok: true, run: { id: "run-safe-retry", status: "queued", work_session_id: next.id } };
  },
}, { router: context.ResearchOSWorkSessionRouter, state, translate: lifecycleText });
await safeRetryLifecycle.callbacks.onRetry();
assert.ok(safeRetrySubmission, "a private failed run with side_effects=none must expose one exact same-request retry");
assert.equal(safeRetrySubmission.next.clientRequestId, "request-safe-retry", "safe retry must preserve the original idempotency identity");
assert.equal(safeRetrySubmission.options.responseMode, "answer", "safe retry must preserve the bounded response mode");
let publicRetrySubmitted = false;
const publicRetryLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  executionAvailable: () => true,
  getResult: () => safeRetryFailure,
  getSession: () => state.updateSession(safeRetryLifecycleSession, { draftResult: safeRetryFailure, status: "active" }),
  publicMode: () => true,
  submitSession: async () => { publicRetrySubmitted = true; return { ok: true }; },
}, { router: context.ResearchOSWorkSessionRouter, state, translate: lifecycleText });
assert.deepEqual(
  { ...await publicRetryLifecycle.callbacks.onRetry() },
  { ok: false },
  "public copy-only mode must reject crafted machine retry even when stale metadata reports execution",
);
assert.equal(publicRetrySubmitted, false);

let guardedStartSession = state.createSession({ intent: "Keep current task" });
let guardedStartSubmitted = false;
const guardedStartLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  confirmNew: () => false,
  getSession: () => guardedStartSession,
  saveSession: (next) => { guardedStartSession = next; return next; },
  submitSession: async () => { guardedStartSubmitted = true; return { ok: true }; },
}, { router: context.ResearchOSWorkSessionRouter, state, translate: lifecycleText });
const guardedStartResult = await guardedStartLifecycle.start({ intent: "Replace from background route" });
assert.equal(guardedStartResult.cancelled, true, "starting a background task must honor the same replacement confirmation as drafting one");
assert.equal(guardedStartSession.intent, "Keep current task", "a cancelled background start must preserve the active Work Session");
assert.equal(guardedStartSubmitted, false, "a cancelled replacement must not submit a hidden runner task");

let packetLifecycleSession = null;
const packetLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  getSession: () => packetLifecycleSession,
  publicMode: () => true,
  refreshSurfaces: () => {},
  saveSession: (next) => { packetLifecycleSession = next; return next; },
  submitSession: async (next) => ({
    ok: true,
    persistResult: true,
    run: {
      execution_status: "copy_ready",
      id: "packet-ready",
      status: "completed",
      work_session_id: next.id,
    },
  }),
}, {
  router: context.ResearchOSWorkSessionRouter,
  state,
  translate: lifecycleText,
});
packetLifecycle.draft({ intent: "Prepare a public task packet", responseMode: "answer" });
await packetLifecycle.callbacks.onRunDraft();
assert.equal(packetLifecycleSession.status, "ready", "a copy-ready public packet must remain adjustable after generation");
packetLifecycle.callbacks.onComplete();
assert.equal(packetLifecycleSession.status, "completed", "a public packet task must end only after the user explicitly completes it");

let boundLifecycleSession = null;
let completedPortfolioProject = "";
let completedPortfolioStep = "";
let boundLifecycleStatus = "";
const boundLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  completeWorkItemProject: async (current) => {
    completedPortfolioProject = current.portfolioBinding?.itemId || "";
    return { ok: true };
  },
  completeWorkItemStep: async (current) => {
    completedPortfolioStep = current.portfolioBinding?.nextStep || "";
    return { ok: true };
  },
  getHistory: () => [],
  getSession: () => boundLifecycleSession,
  publicMode: () => false,
  renderHome: () => {},
  saveHistory: (next) => next,
  saveSession: (next) => { boundLifecycleSession = next; return next; },
  showStatus: (message) => { boundLifecycleStatus = message; },
}, { state, translate: lifecycleText });
boundLifecycle.draft({
  intent: "Confirm the registered approval task",
  portfolioBinding: {
    itemId: "pilot-approval",
    nextStep: "Confirm the ethics approval",
    nextStepHash: "step-fixture",
    providerId: "research_portfolio",
    title: "Pilot Study Approval",
  },
});
const boundStepResult = await boundLifecycle.callbacks.onCompleteWorkItemStep();
assert.equal(boundStepResult.ok, true);
assert.equal(completedPortfolioStep, "Confirm the ethics approval", "step completion must use the exact next step frozen into the Work Session binding");
assert.equal(boundLifecycleSession.status, "draft", "completing a Commitment must not substitute for ending its Work Session");
assert.equal(boundLifecycleStatus, "workSessionStepCompleted");
const boundProjectResult = await boundLifecycle.callbacks.onCompleteWorkItemProject();
assert.equal(boundProjectResult.ok, true);
assert.equal(completedPortfolioProject, "pilot-approval", "project completion must close only the explicitly bound registered item");
assert.equal(boundLifecycleSession.status, "draft", "closing a durable project must not silently archive the Work Session");
assert.equal(boundLifecycleStatus, "workSessionProjectCompleted");
boundLifecycle.callbacks.onComplete();
assert.equal(boundLifecycleSession.status, "completed", "only End Work Session may archive the local session");
assert.equal(boundLifecycle.callbacks.onSaveResult().ok, false, "an archived Work Session must not restart through a hidden artifact callback");

let staleGuardSession = null;
let staleGuardMutationCalls = 0;
let staleGuardRunCalls = 0;
const staleGuardLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  allowSessionAction: (_session, action) => ["end_session", "new_session", "copy_result", "view"].includes(action),
  completeWorkItemStep: async () => { staleGuardMutationCalls += 1; return { ok: true }; },
  getSession: () => staleGuardSession,
  publicMode: () => false,
  saveSession: (next) => { staleGuardSession = next; return next; },
  showStatus: (message) => { boundLifecycleStatus = message; },
  submitSession: async () => { staleGuardRunCalls += 1; return { ok: true }; },
}, { state, translate: lifecycleText });
staleGuardLifecycle.draft({
  intent: "Old bound task",
  portfolioBinding: { itemId: "stale-item", nextStep: "Old step", nextStepHash: "old-step", providerId: "research_portfolio" },
});
assert.equal((await staleGuardLifecycle.callbacks.onRunDraft()).reason, "stale_context", "the central lifecycle must reject a stale bound run even if called without the view");
assert.equal((await staleGuardLifecycle.callbacks.onCompleteWorkItemStep()).reason, "stale_context", "the central lifecycle must reject a stale bound mutation even if called without the view");
assert.equal(staleGuardRunCalls, 0, "a rejected stale run must not reach the executor");
assert.equal(staleGuardMutationCalls, 0, "a rejected stale mutation must not reach the durable action");
assert.equal(boundLifecycleStatus, "workSessionContextReadOnlyStatus", "a rejected stale action must explain the read-only boundary");
staleGuardLifecycle.callbacks.onComplete();
assert.equal(staleGuardSession.status, "completed", "ending a stale session must remain available");

let failedBoundSession = null;
const failedBoundLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  completeWorkItemStep: async () => ({ ok: false }),
  getSession: () => failedBoundSession,
  publicMode: () => false,
  saveSession: (next) => { failedBoundSession = next; return next; },
}, { state, translate: lifecycleText });
failedBoundLifecycle.draft({
  intent: "Failed closeout",
  portfolioBinding: { itemId: "still-open", nextStep: "Run check", nextStepHash: "run-check-signature", providerId: "research_portfolio" },
});
const failedBoundResult = await failedBoundLifecycle.callbacks.onCompleteWorkItemStep();
assert.equal(failedBoundResult.ok, false);
assert.equal(failedBoundSession.status, "draft", "a failed step mutation must leave the registered task and Work Session open");

let releaseLockedMutation = null;
let lockedMutationSession = null;
let lockedProjectCalls = 0;
const lockedMutationLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  completeWorkItemProject: async () => { lockedProjectCalls += 1; return { ok: true }; },
  completeWorkItemStep: () => new Promise((resolve) => { releaseLockedMutation = resolve; }),
  getSession: () => lockedMutationSession,
  publicMode: () => false,
  saveSession: (next) => { lockedMutationSession = next; return next; },
}, { state, translate: lifecycleText });
lockedMutationLifecycle.draft({
  intent: "Lock one completion mutation",
  portfolioBinding: { itemId: "locked-item", nextStep: "Run check", nextStepHash: "locked-step", providerId: "research_portfolio" },
});
const pendingStepMutation = lockedMutationLifecycle.callbacks.onCompleteWorkItemStep();
const overlappingProjectMutation = await lockedMutationLifecycle.callbacks.onCompleteWorkItemProject();
assert.equal(overlappingProjectMutation.busy, true, "step and project completion must share one in-flight mutation lock");
assert.equal(lockedProjectCalls, 0, "an overlapping project closeout must not reach the durable writer");
releaseLockedMutation({ ok: false });
await pendingStepMutation;

assert.deepEqual(
  JSON.parse(JSON.stringify(lifecycle.creationDefaults())),
  {
    evidenceBoundary: "Public candidate boundary",
    sensitivity: "internal",
    templateLanguage: "en",
  },
  "lifecycle defaults must keep public inputs internal candidates until review"
);
const lifecycleCreate = lifecycle.callbacks.onCreate({ intent: "Read this paper", sourceHint: "/tmp/lifecycle.pdf" });
assert.equal(lifecycleSession.status, "running", "creating a Work Session must start its default result immediately");
assert.equal(lifecycleStatus, "workSessionPreparingPacket");
await lifecycleCreate;
assert.equal(lifecycleSession.status, "running", "an accepted queued Work Session must remain visibly running until polling returns a terminal result");
lifecycleSession = state.reconcileRun(lifecycleSession, [{
  id: "run-lifecycle",
  status: "completed",
  work_session_id: lifecycleSession.id,
}]);
assert.equal(lifecycleSession.status, "ready", "polling must move the completed queued task into review instead of back to active");
assert.equal(lifecycleSession.sensitivity, "internal");
assert.equal(lifecycleSession.evidenceBoundary, "Public candidate boundary");
assert.equal(lifecycleStatus, "workSessionQueued");
lifecycle.callbacks.onPrepare();
assert.equal(lifecycleSession.status, "ready", "prepare must bind the session to one ready Handoff");
assert.equal(lifecycleDoingItems.length, 1);
assert.equal(lifecycleWorkspace, "", "a prepared handoff must not navigate to a global Review workspace");
assert.equal(lifecycleItemPanel, "review", "a prepared handoff candidate must reveal Review inside the exact item's drawer");
assert.equal(lifecycleInboxStatus, "workSessionHandoffReady");
lifecycle.callbacks.onUpdateIntent({ intent: "Read and compare this paper" });
assert.equal(lifecycleSession.intent, "Read and compare this paper");
assert.equal(lifecycleDoingItems.length, 1, "editing a ready session must update the existing Handoff in place");
const refreshesBeforeReopen = lifecycleRefreshes;
lifecycle.callbacks.onPrepare();
assert.equal(lifecycleDoingItems.length, 1, "preparing an already ready session must not duplicate Handoff");
assert.equal(lifecycleInboxStatus, "workSessionReviewHandoffReady");
assert.equal(lifecycleRefreshes, refreshesBeforeReopen, "reopening Handoff must not rebuild unrelated surfaces");
lifecycle.callbacks.onComplete();
assert.deepEqual(archivedHandoff, { id: lifecycleSession.handoffKey, type: "task" });
const lifecycleRun = lifecycle.callbacks.onRun({ intent: "Now compare the paper with a second method" });
assert.equal(lifecycleSession.status, "running", "continuing a reviewed task must reopen it as a running session");
assert.equal(lifecycleSession.handoffKey, "", "a new run must release the stale Review relationship");
assert.equal(lifecycleDoingItems.length, 0, "a new run must withdraw the now-stale Review candidate");
await lifecycleRun;
lifecycleSession = state.updateSession(lifecycleSession, { status: "completed" });
lifecycle.callbacks.onNew();
assert.equal(lifecycleSession, null, "starting over must clear the browser-local Work Session");
assert.equal(lifecycleHistory.length, 1, "starting over must archive a bounded recent-task summary before clearing the active session");
assert.equal(Object.hasOwn(lifecycleHistory[0], "turns"), false, "lifecycle history must not retain raw conversation turns");
assert.equal(lifecycleNewConfirmations, 0, "a completed Work Session must start the next task without a redundant confirmation");
lifecycle.callbacks.onResumeHistory({ historyId: lifecycleHistory[0].id });
assert.equal(lifecycleSession.resumeSummary, lifecycleHistory[0].resultSummary);
assert.equal(lifecycleStatus, "workSessionHistoryResumed");
lifecycle.callbacks.onNew();
lifecycle.callbacks.onResume({ encodedPacket: JSON.stringify({ path: "resume.md", taskRunId: "run-1", title: "Resume task" }) });
assert.equal(lifecycleSession.title, "Resume task");
assert.equal(lifecycleSession.sourceHints[0], "resume.md");
assert.equal(lifecycleStatus, "workSessionResumeCreated");

let busySession = state.updateSession(session, {
  draftResult: { status: "queued" },
  status: "running",
});
let busyHistory = [{ ...history[0], id: "busy-other-history" }];
let busyStatus = "";
const busyLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  getHistory: () => busyHistory,
  getResult: () => ({ status: "queued" }),
  getSession: () => busySession,
  saveHistory: (next) => { busyHistory = next; return next; },
  saveSession: (next) => { busySession = next; return next; },
  showStatus: (message) => { busyStatus = message; },
}, { state, translate: lifecycleText });
const busyCardCount = busySession.cards.length;
assert.equal(busyLifecycle.callbacks.onNew().busy, true);
assert.equal(busyLifecycle.callbacks.onComplete().busy, true);
assert.equal(busyLifecycle.callbacks.onResumeHistory({ historyId: "busy-other-history" }).busy, true);
assert.equal(busyLifecycle.callbacks.onPrepare().busy, true);
assert.equal(busyLifecycle.addCard({ id: "late-card", title: "Late card" }).busy, true);
assert.equal(busyLifecycle.callbacks.onRemoveCard({ cardId: busySession.cards[0]?.id }).busy, true);
assert.equal(busySession.cards.length, busyCardCount, "running tasks must reject context mutations that would no longer match the submitted prompt");
assert.equal(busyStatus, "workSessionWaitForResult");

let deleteAllowed = false;
let deleteHistory = [{ ...history[0], id: "delete-history" }];
const deleteLifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
  confirmDeleteHistory: () => deleteAllowed,
  getHistory: () => deleteHistory,
  getSession: () => null,
  saveHistory: (next) => { deleteHistory = next; return next; },
}, { state, translate: lifecycleText });
assert.equal(deleteLifecycle.callbacks.onDeleteHistory({ historyId: "delete-history" }), false, "deleting a recent task must require confirmation");
assert.equal(deleteHistory.length, 1);
deleteAllowed = true;
deleteLifecycle.callbacks.onDeleteHistory({ historyId: "delete-history" });
assert.equal(deleteHistory.length, 0);

const app = read("dashboard/app.js");
assert.match(app, /completeWorkItemStep:\s*\(session\)\s*=>\s*dispatchBoundWorkItemAction\(session,\s*"completeStepActionId"/, "the Work Session step action must route through the bound plugin action");
assert.match(app, /completeWorkItemProject:\s*\(session\)\s*=>\s*dispatchBoundWorkItemAction\(session,\s*"completeProjectActionId"/, "the explicit project action must route through the bound plugin action");
assert.ok(!app.includes("WorkSessionClient.completePortfolioItem"), "the application shell must not own Portfolio completion");
assert.ok(!app.includes("WorkSessionClient.applyAttentionAction"), "the application shell must not own Portfolio attention mutation");
assert.ok(!app.includes("ResearchPortfolioCopy"), "the application shell must not import Portfolio copy");
const researchPortfolioPlugin = read("dashboard/src/plugins/research-portfolio.js");
assert.ok(researchPortfolioPlugin.includes('registerActionHandler(pluginId, "complete_portfolio_project"'), "the Portfolio plugin must own project completion dispatch");
assert.ok(researchPortfolioPlugin.includes("WorkSessionClient?.completePortfolioItem"), "the Portfolio plugin must call its narrow completion client");
assert.match(app, /function durableWorkItemMutationAvailable[\s\S]*?ActionContract\.durableMutationAvailable/, "durable Work Item controls must use the shared fail-closed runtime capability");
assert.match(app, /workItemMutationAvailable:\s*durableWorkItemMutationAvailable\(\)/, "the Work Session view must receive the fail-closed durable mutation capability");
const researchAssetsPlugin = read("dashboard/src/plugins/research-assets.js");
const homeView = read("dashboard/src/views/home-command-center.js");
const portfolioView = read("dashboard/src/plugins/research-portfolio-view.js");
const assetView = read("dashboard/src/views/asset-overview.js");
const assetWorkbench = read("dashboard/src/services/asset-overview-workbench.js");
const inboxView = read("dashboard/src/views/unified-inbox.js");
const inboxService = read("dashboard/src/services/inbox.js");
const uiCopy = read("dashboard/src/core/ui-copy.js");
const workSessionView = read("dashboard/src/views/work-session.js");
const workSessionWorkbench = read("dashboard/src/services/work-session-workbench.js");
const workSessionStyles = read("dashboard/styles/views/work-session.css");
const markdownPreviewView = read("dashboard/src/views/markdown-preview.js");
const workSessionClient = context.ResearchOSWorkSessionClient;
assert.ok(app.includes("createWorkSessionLifecycle"), "app must compose the Work Session lifecycle owner once");
assert.ok(app.includes("WorkSessionLifecycle.callbacks"), "app must delegate Work Session actions to lifecycle callbacks");
assert.ok(!app.includes("function workSessionCreationDefaults"), "creation rules must not drift back into app orchestration");
assert.ok(!app.includes("WorkSessionState.handoffPayload"), "Handoff preparation rules must stay in the Work Session owner");
assert.ok(researchAssetsPlugin.includes('payload.source === "asset-overview-card"'), "ordinary asset cards must enter the working deck through the asset plugin");
assert.ok(researchAssetsPlugin.includes("context.addWorkSessionCard"), "the asset plugin must use the stable Work Session port");
assert.ok(!app.includes('payload.source === "asset-overview-card"'), "app shell must not interpret asset-domain payloads");
assert.ok(app.includes("workSessionLifecycle: WorkSessionLifecycle") && read("dashboard/src/services/plugin-host.js").includes("addWorkSessionCard: lifecycle.addCard"), "card additions must route through the lifecycle owner");
assert.ok(app.includes("WorkSessionLifecycle.syncHandoffStatus"), "Handoff state changes must route through the lifecycle owner");
assert.ok(app.includes("WorkSessionState.readHistory"), "app orchestration must load bounded recent-task summaries through the state owner");
assert.ok(app.includes("workSessionForDisplay()") && app.includes("workSessionHistoryForDisplay()"), "public-demo visibility must filter current and recent Work Sessions without deleting browser state");
assert.ok(app.includes("WorkSessionWorkbenchService.renderPreservingInteraction"), "background runner polling must delegate draft preservation to the Work Session owner");
assert.match(app, /onChange:\s*\(language\)[\s\S]*?WorkSessionWorkbenchService\.renderPreservingInteraction\([\s\S]*?renderDashboard\(dashboardData\)[\s\S]*?resolveRoot/, "language changes must preserve an expanded continuation composer and its unsubmitted draft across a full dashboard render");
assert.match(app, /onChange:\s*\(language\)[\s\S]*?captureInteraction\(workSessionRoot\)\?\.hasSelectedFile[\s\S]*?select\.value = lang[\s\S]*?workSessionLanguageBlockedByFile/, "language switching must fail closed before mutating global language when a browser-only file selection cannot be restored");
assert.match(uiCopy, /simpleText:\s*{\s*"zh-CN":\s*{\s*\.\.\.\(workSession\.simpleText\?\.\["zh-CN"\]/, "Chinese Work Session copy must merge into the simple-text dictionary used by live result rendering");
assert.ok(!app.includes("markHomeActionHandled"), "retired first-screen suggestion state must not survive the Judgment split");
assert.ok(app.includes("language: session.templateLanguage || lang || activeTemplateLanguage()"), "runner submission must preserve the language frozen when the Work Session was created");
assert.ok(app.includes('simpleTextForLanguage("workSessionPacketHeading", sessionLanguage)'), "public task-packet framing must use the frozen Work Session language");
assert.ok(homeView.includes("function renderNowHtml"), "Now must own the attention-portfolio renderer");
const nowRenderChunk = homeView.slice(homeView.indexOf("function renderNowHtml"), homeView.indexOf("global.ResearchOSHomeCommandCenterView"));
assert.ok(nowRenderChunk.includes('translate("nowResearchChoicesLabel")') && !nowRenderChunk.includes('translate("researchAttentionTitle")'), "Now's research-item region must use copy available to its own translator instead of exposing a plugin key as its accessible name");
assert.ok(!nowRenderChunk.includes('id="todayWorkSession"'), "Now must not own the Work Session mount");
assert.ok(app.includes('id="todayWorkSession"') && app.includes('dashboardTarget("workSessionSurface")'), "Work must compose the selected Work Session through its own mount");
assert.ok(!homeView.includes('data-plugin-slot-host="processing"'), "Portfolio must not duplicate Work Session state on Now");
assert.ok(nowRenderChunk.includes('data-plugin-slot-host="workbench"'), "Now must keep the attention-portfolio plugin slot");
assert.ok(portfolioView.includes('class="research-attention-board"'), "the portfolio plugin must own the attention control surface");
assert.ok(portfolioView.includes("data-attention-action"), "the attention control surface must expose button-first scheduling actions");
assert.ok(!homeView.includes("data-portfolio"), "Today core view must stay independent of portfolio domain markup");
assert.ok(markdownPreviewView.includes('class="preview-mode-tabs" role="group"'), "preview mode toggles must use button-group semantics");
assert.ok(markdownPreviewView.includes('class="preview-history-tabs" role="list"'), "recent evidence must use list semantics");
assert.ok(markdownPreviewView.includes('aria-current="page"'), "the selected evidence button must expose the current item");
assert.ok(!markdownPreviewView.includes('role="tablist"') && !markdownPreviewView.includes('role="tab"'), "preview must not claim an incomplete ARIA tabs pattern");
assert.ok(app.includes("publicMode: isPublicStarterRuntime()"), "the app must pass the runtime boundary into the home information architecture");
assert.ok(workSessionView.includes("workSessionReviewHandoff"), "a prepared Work Session must provide a direct route back to Handoff");
assert.ok(workSessionView.includes("work-session-public-outcome"), "the public result must explain what ResearchOS organized before exposing raw instructions");
assert.ok(workSessionView.includes("work-session-packet-details"), "the full public execution brief must use progressive disclosure");
assert.ok(workSessionView.includes('count === 1 ? "workSessionDeckCountOne"'), "card counts must use a singular label for one card");
assert.ok(uiCopy.includes('workSessionDeckCountOne: "1 card"'), "English UI copy must define the singular card label");
assert.ok(workSessionWorkbench.includes("createWorkSessionLifecycle"), "Work Session workbench must own lifecycle orchestration");
assert.ok(assetView.includes("workSessionTrayHtml"), "Card Library must expose the current task tray");
assert.ok(assetView.includes("data-asset-card-global-search"), "Card Library must provide one global search entrypoint");
assert.ok(assetWorkbench.includes("syncGlobalAssetCardSearch"), "Card Library workbench must own global search behavior");
assert.ok(inboxView.includes('entry.raw?.source === "work-session"'), "Handoff must identify Work Session action cards explicitly");
assert.ok(inboxView.includes('workSessionCards.length === 1 ? "workSessionDeckCountOne"'), "Handoff must preserve singular card counts");
assert.ok(inboxView.includes('translate("unifiedInboxAuthorityImpact")'), "Handoff must render the impact scope of a proposed authority change");
assert.ok(inboxView.includes('"unifiedInboxSaveTargetMissingPublic"'), "public Review must not imply that local Codex will choose the write-back target");
assert.ok(inboxService.includes('raw.source === "work-session" ? 240 : 92'), "Review must preserve enough of a Work Session goal for exact inspection");
assert.ok(workSessionWorkbench.includes('root.querySelector("[data-work-session-run-form]")'), "follow-up requests must stay in the Work Session result loop");
assert.ok(workSessionWorkbench.includes('root.querySelector("[data-work-session-add-followup]")'), "the optional follow-up action must only reveal the bounded composer through the Work Session owner");
assert.ok(workSessionWorkbench.includes('root.querySelector("[data-work-session-retry]")'), "safe same-request retry must bind through the lifecycle owner");
assert.ok(!workSessionWorkbench.includes("onContinueRecommended"), "model recommendations must not remain a hidden auto-continuation path");
assert.match(workSessionCss, /@media \(max-width: 640px\)[\s\S]*?\.work-session-result-actions\s*\{[^}]*flex-basis:\s*100%;[\s\S]*?\.work-session-result-actions > div\s*\{[^}]*right:\s*0;[^}]*left:\s*auto;[^}]*max-width:\s*calc\(100vw - 32px\);/, "the mobile More menu must open inside the viewport on its own row");
assert.ok(workSessionWorkbench.includes("callbacks.onRun"), "follow-up submission must route through the lifecycle owner");
assert.ok(workSessionWorkbench.includes("selectedRunFile"), "follow-up material must share the source-picker path instead of a separate workflow");
assert.ok(workSessionWorkbench.includes("workSessionSubmitting"), "slow uploads must lock each form before the first await to prevent duplicate material copies");
assert.ok(workSessionWorkbench.includes("workSessionSourceSelected"), "selecting a file or path must update the collapsed material summary");
assert.ok(workSessionWorkbench.includes("sourceSummaryControl?.setAttribute(\"aria-label\", accessibleLabel)"), "the material control accessible name must track the selected source");
assert.ok(workSessionWorkbench.includes("archiveCurrentSession"), "the lifecycle owner must archive a bounded summary before replacing the current task");
assert.ok(workSessionWorkbench.includes("selectedFile && sourceDetails"), "a selected file must close the mobile material panel automatically");
assert.ok(workSessionWorkbench.includes("upload?.storage?.notice_code"), "storage advisories must remain non-blocking Work Session copy");
assert.ok(uiCopy.includes("nothing is auto-deleted"), "the English storage advisory must state the non-deletion boundary");
assert.ok(!workSessionWorkbench.includes("work-session-output-options"), "response-mode selection belongs to Codex and must not reappear in the Dashboard workbench");
assert.ok(workSessionWorkbench.includes("function captureInteraction"), "the Work Session owner must capture drafts before background rendering");
assert.ok(workSessionWorkbench.includes("function restoreInteraction"), "the Work Session owner must restore drafts after background rendering");
assert.equal(Object.hasOwn(workSessionClient, "ALLOWED_SUFFIXES"), false, "the browser client must not reject user-selected research materials by file type");
const largeFile = { name: "large-paper.pdf", size: 2 * 1024 * 1024 * 1024 };
let uploadRequest = null;
const uploadResult = await workSessionClient.uploadSourceFile(largeFile, {
  fetcher: async (url, options) => {
    uploadRequest = { options, url };
    return { json: async () => ({ ok: true, path: "uploads/large-paper.pdf" }), ok: true, status: 200 };
  },
});
assert.equal(uploadResult.ok, true, "the browser client must not impose an arbitrary attachment-size quota");
assert.equal(uploadRequest.options.body, largeFile, "the browser client must stream the File body instead of base64-encoding it");
assert.equal(uploadRequest.options.headers["Content-Type"], "application/octet-stream");
assert.equal(uploadRequest.options.headers["X-ResearchOS-Filename"], "large-paper.pdf");
const notebookUpload = await workSessionClient.uploadSourceFile({ name: "实验分析.ipynb", size: 128 }, {
  fetcher: async () => ({ json: async () => ({ ok: true, path: "uploads/notebook.ipynb" }), ok: true, status: 200 }),
});
assert.equal(notebookUpload.ok, true, "non-English and non-document research files must reach the local intake boundary");
let completionRequest = null;
const completionClientResult = await workSessionClient.completePortfolioItem({ itemId: "pilot-approval" }, {
  completionNote: "Ethics approval received",
}, {
  fetcher: async (url, options) => {
    completionRequest = { options, url };
    return { json: async () => ({ ok: true, rebuilt: true }), ok: true, status: 200 };
  },
});
assert.equal(completionClientResult.ok, true);
assert.equal(completionRequest.url, "/portfolio-complete");
assert.deepEqual(JSON.parse(completionRequest.options.body), {
  completion_note: "Ethics approval received",
  item_id: "pilot-approval",
});
let attentionRequest = null;
const attentionClientResult = await workSessionClient.applyAttentionAction({
  providerId: "research_portfolio",
  id: "pilot-approval",
  nextStep: "Confirm approval",
}, {
  action: "schedule",
  attentionDate: "2026-08-07",
}, {
  fetcher: async (url, options) => {
    attentionRequest = { options, url };
    return { json: async () => ({ ok: true, undo: { kind: "attention", token: "receipt" } }), ok: true, status: 200 };
  },
});
assert.equal(attentionClientResult.ok, true);
assert.equal(attentionRequest.url, "/attention-action");
assert.deepEqual(JSON.parse(attentionRequest.options.body), {
  action: "schedule",
  attention_date: "2026-08-07",
  item_id: "pilot-approval",
  next_step: "Confirm approval",
  provider_id: "research_portfolio",
  review_date: "",
  today_order: 0,
});
let completeStepRequest = null;
const completeStepClientResult = await workSessionClient.applyAttentionAction({
  providerId: "research_portfolio",
  id: "pilot-approval",
  nextStep: "Confirm approval",
  nextStepHash: "frozen-step-signature",
}, {
  action: "complete_step",
}, {
  fetcher: async (url, options) => {
    completeStepRequest = { options, url };
    return { json: async () => ({ ok: true }), ok: true, status: 200 };
  },
});
assert.equal(completeStepClientResult.ok, true);
assert.equal(completeStepRequest.url, "/attention-action");
assert.equal(JSON.parse(completeStepRequest.options.body).next_step_hash, "frozen-step-signature", "step completion must send the signature frozen when the Work Session was bound");
let undoRequest = null;
const undoResult = await workSessionClient.undoMutation({ kind: "attention", token: "receipt" }, {
  fetcher: async (url, options) => {
    undoRequest = { options, url };
    return { json: async () => ({ ok: true }), ok: true, status: 200 };
  },
});
assert.equal(undoResult.ok, true);
assert.equal(undoRequest.url, "/mutation-undo");
assert.deepEqual(JSON.parse(undoRequest.options.body), { kind: "attention", token: "receipt" });
assert.equal(typeof workSessionClient.openLocalFile, "function", "explicit artifact clicks must use the bounded local-file bridge client");
assert.equal(workSessionClient.fileSuffix("PAPER.PDF"), ".pdf", "client suffix validation must be case-insensitive");
assert.ok(workSessionWorkbench.includes("artifactFromResult: true"), "creating Markdown from a page result must not inherit conflicting source instructions");
assert.ok(workSessionView.includes("data-work-session-result"), "the full Work Session result must render in the Workbench");
assert.ok(workSessionView.includes("work-session-task-progress"), "the Workbench must be task-state-first after submission");
assert.ok(uiCopy.includes('workSessionProcessTitle: "Process log"'), "English UI copy must distinguish a process log from chat history");
const mobileWorkSessionStyles = workSessionStyles.slice(workSessionStyles.indexOf("@media (max-width: 640px)"));
assert.match(mobileWorkSessionStyles, /\.work-session-run-form\s*\{[^}]*position:\s*static;[^}]*bottom:\s*auto;/s, "mobile follow-up must stay in document flow instead of covering the result");

console.log("Work session contract regression passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
