/* Calm handoff contract: two stable workspaces (Now, Library), execution and Review only inside the exact item's drawer.
 * The real Review view, Now view, portfolio plugin chain, work-session lifecycle and asset plugin run on fictional data;
 * source assertions remain only for index.html registration/ids and for retired APIs.
 */
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { element, frozenDate, loadModules, read, root: repositoryRoot } = require("./helpers/dashboard-vm.js");

const index = read("dashboard/index.html");
const privateEdition = /data-client-profile="private_compact_v1"/.test(index);
const escapeHtml = (value) => String(value ?? "").replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
const text = (key) => key;
let css = "";
const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).forEach((entry) => {
  const full = path.join(dir, entry.name);
  if (entry.isDirectory()) walk(full);
  else if (entry.name.endsWith(".css")) css += fs.readFileSync(full, "utf8");
});
walk(path.join(repositoryRoot, "dashboard/styles"));
const styled = (name) => new RegExp(`\\.${name}(?![\\w-])`).test(css);

// --- index.html: exactly two workspaces and one item-local drawer -------------------------------------------------
assert.deepEqual([...index.matchAll(/id="(workspace-(?:tab|panel)-[a-z]+)"/g)].map((match) => match[1]).sort(),
  ["workspace-panel-library", "workspace-panel-now", "workspace-tab-library", "workspace-tab-now"], "Now and Library are the only stable workspaces");
for (const retired of ["workspace-tab-start", "workspace-tab-next", "workspace-tab-work", "workspace-panel-start", "workspace-panel-next", "workspace-panel-work"]) {
  assert.ok(!index.includes(retired), `retired workspace id ${retired} must not return`);
}
for (const id of ["workSessionSurface", "unifiedInbox"]) assert.equal((index.match(new RegExp(`id="${id}"`, "g")) || []).length, 1, `${id} must exist exactly once`);
assert.equal((index.match(/data-item-execution-drawer/g) || []).length, 1, "one item-local drawer composes continuity and Review");
assert.ok(index.indexOf("data-item-execution-drawer") < index.indexOf('id="workSessionSurface"') && index.indexOf('id="workSessionSurface"') < index.indexOf('id="unifiedInbox"'), "the drawer holds the Work Session surface and Review");
assert.equal((index.match(/<script src="src\/services\/app-copy-actions\.js"><\/script>/g) || []).length, 1, "shared services load exactly once");

// --- Retired APIs stay retired -------------------------------------------------------------------------------------
const app = read("dashboard/app.js");
assert.ok(!app.includes("renderPluginProcessingSlots"), "the Portfolio processing slot is retired");
assert.ok(!app.includes("HomeCommandCenterController"), "retired first-screen execution sequencing must not remain active");
assert.ok(!read("dashboard/src/core/i18n.js").includes('"workspace.review":'), "Review is not a workspace");

const context = loadModules([
  "dashboard/src/core/interactions.js",
  "dashboard/src/core/surface-contract.js",
  "dashboard/src/services/result-envelope.js",
  "dashboard/src/services/work-session-state.js",
  "dashboard/src/core/ui.js",
  "dashboard/src/services/plugin-runtime.js",
  "dashboard/src/services/inbox.js",
  "dashboard/src/components/segmented-control.js",
  "dashboard/src/views/unified-inbox.js",
  "dashboard/src/views/home-command-center.js",
  "dashboard/src/plugins/research-portfolio-model.js",
  "dashboard/src/plugins/research-portfolio-view.js",
  "dashboard/src/plugins/research-portfolio-workbench.js",
  "dashboard/src/plugins/research-portfolio.js",
  "dashboard/src/services/work-session-workbench.js",
], {
  crypto: { randomUUID: () => "calm-handoff-session" },
  Date: frozenDate("2026-08-12T12:00:00Z"),
  ResearchOSConfirmationState: {},
  ResearchOSDoingBoardState: { itemKey: (item) => item?.id || "" },
});

// --- Review (item-local) ------------------------------------------------------------------------------------------
const Inbox = context.ResearchOSUnifiedInboxView;
const inboxDeps = {
  emptyState: ({ className = "", message = "" } = {}) => `<section class="${className}"><p>${message}</p></section>`,
  encodeDataPayload: encodeURIComponent,
  escapeHtml,
  previewButton: () => "",
  relatedCompositionCards: () => [],
  shortText: (value) => String(value || ""),
  translate: text,
};
const candidateItem = (id) => ({
  id: `handoff:work-session:${id}`, type: "task", title: `Candidate ${id}`, source: "work-session", status: "local", work_session_id: id,
  candidate: { candidate_id: `candidate:${id}`, proposed_writeback: { object_id: "item-a" } },
});
const collect = (count) => context.ResearchOSInboxService.collectUnifiedInboxEntries({
  doingItems: Array.from({ length: count }, (_, position) => candidateItem(`S${position + 1}`)),
}, { doingKey: (item) => item.id, doingTypeLabel: () => "Task", text }).entries;
const reviewInbox = (entries, extra = {}) => ({
  allTotal: entries.length, archivedTotal: 0, codexRunnerEnabled: true, codexRuns: [], entries,
  total: entries.length, visibleTotal: entries.length, view: "active", workFilter: "needs_review", ...extra,
});

const oneReady = Inbox.renderUnifiedInboxHtml({ inbox: reviewInbox(collect(1)), deps: inboxDeps });
assert.ok(oneReady.includes(">unifiedInboxReadyCountOne<"), "one ready item uses the singular label");
const twoReady = Inbox.renderUnifiedInboxHtml({ inbox: reviewInbox(collect(2)), deps: inboxDeps });
assert.ok(twoReady.includes(">unifiedInboxReadyCount<") && !twoReady.includes("unifiedInboxReadyCountOne"));
assert.ok(oneReady.includes("data-work-filter") && oneReady.includes('data-work-filter-value="needs_review" aria-pressed="true"'), "Needs Review stays a local Work filter");

const emptyReview = Inbox.renderUnifiedInboxHtml({ inbox: reviewInbox([]), deps: inboxDeps });
assert.ok(emptyReview.includes('class="unified-inbox-empty-state"'), "an empty Review collapses to one explanatory state");
for (const control of ["data-unified-inbox-generate", "data-unified-inbox-copy", "data-unified-inbox-clear", "unified-inbox-ledger"]) {
  assert.ok(!emptyReview.includes(control), `an empty Review must not expose ${control}`);
}
assert.ok(emptyReview.includes('data-review-current-result data-result-present="false"'), "the current result area stays visible even without candidates");

const resultInbox = reviewInbox([], {
  currentResult: { answer: "Fictional summary of the finished step", artifacts: ["notes/result.md"] },
  currentSession: { goal: "Check the fictional evidence" },
});
const withResult = Inbox.renderUnifiedInboxHtml({ inbox: resultInbox, deps: inboxDeps });
assert.ok(withResult.includes('data-result-present="true"') && withResult.includes("Fictional summary of the finished step") && withResult.includes("<code>notes/result.md</code>"), "Review shows the current result independently from durable-change candidates");
const withheld = Inbox.renderUnifiedInboxHtml({
  inbox: { ...resultInbox, currentResultProjection: { state: "withheld", reason: "identity_mismatch", provenance: { work_session_id: "S1", observed_work_session_id: "S2" } } },
  deps: inboxDeps,
});
assert.ok(withheld.includes('data-result-identity="withheld"') && !withheld.includes("Fictional summary of the finished step"), "a result whose identity does not match the item is withheld");

const runningEntries = collect(1);
const runs = [{ id: "run-1", status: "running", task_mode: "direct_execution", action_key: `${runningEntries[0].type}:${runningEntries[0].actionId}`, updated_at: "2026-08-12T11:59:00Z" }];
const runningReview = Inbox.renderUnifiedInboxHtml({ inbox: reviewInbox(runningEntries, { codexRuns: runs }), deps: inboxDeps });
assert.ok(runningReview.includes('class="unified-inbox-item-run-status running"'), "live progress is shown inline on the candidate card");
assert.ok(runningReview.includes('class="unified-inbox-runner-overview"'), "queue progress has an always-visible overview while a run is active");
for (const name of ["unified-inbox-item-run-status", "unified-inbox-runner-overview", "unified-inbox-empty-state"]) assert.ok(styled(name), `${name} must be styled`);

const privateAction = Inbox.renderUnifiedInboxHtml({ inbox: reviewInbox(collect(1)), deps: inboxDeps });
const publicAction = Inbox.renderUnifiedInboxHtml({ inbox: reviewInbox(collect(1), { publicMode: true }), deps: inboxDeps });
assert.ok(privateAction.includes('data-canonical-write="candidate_only"'), "a private Review action only creates a candidate");
assert.ok(publicAction.includes('data-canonical-write="false"') && !publicAction.includes('data-canonical-write="candidate_only"'), "each public Review action discloses that canonical write is unavailable");

// --- Now --------------------------------------------------------------------------------------------------------
const Home = context.ResearchOSHomeCommandCenterView;
const nowHtml = Home.renderNowHtml({ workSessionHtml: '<section id="todayWorkSession" class="now-current-task">session</section>' }, { escapeHtml, sectionTranslate: text, translate: text });
assert.ok(nowHtml.includes('data-plugin-slot-host="workbench"') && nowHtml.includes("data-now-surface"), "Now hosts the portfolio workbench slot");
assert.ok(!nowHtml.includes('id="todayWorkSession"') && !nowHtml.includes("now-current-task"), "Now stays an attention portfolio; the Work Session belongs to the item drawer");
assert.ok(!nowHtml.includes('data-open-workspace="work"'), "Now must not navigate to a third Work screen");
assert.equal(Home.renderNextHtml, undefined, "the retired third workspace has no renderer");

const portfolioItem = (id, extra = {}) => ({
  id, title: `Item ${id}`, provider_id: "research_portfolio", responsibility: "lead", state: "mainline", lifecycle_state: "open",
  lifecycle_phase: "writing", attention_state: "today", attention_date: "2026-08-12", next_step: `Next step for ${id}`,
  action_prompt: `Continue ${id}`, last_verified: "2026-08-12", ...extra,
});
const portfolioPayload = (mode) => ({
  available: true,
  presentation_mode: mode,
  sensitivity: mode === "public_demo" ? "public" : "private",
  items: [
    ...["a", "b", "c", "d", "e"].map((id, position) => portfolioItem(id, { today_order: position + 1 })),
    portfolioItem("waiting", { state: "waiting", lifecycle_state: "waiting", lifecycle_phase: "under_review", attention_state: "waiting", attention_date: "", activation_trigger: "Reviewer response" }),
  ],
});
const Portfolio = context.ResearchOSResearchPortfolioView;
const Model = context.ResearchOSResearchPortfolioModel;
const privateModel = Model.build(portfolioPayload("private_authority"), text);
const firstScreen = Portfolio.render({ calendarMonth: "2026-08", calendarView: "month", mutationEnabled: true, researchPortfolio: privateModel }, { escapeHtml, previewButton: () => "", translate: text });
assert.equal((firstScreen.match(/data-attention-card="/g) || []).length, 5, "Now renders every Today commitment even when other horizons stay folded");
assert.ok(!firstScreen.includes('data-portfolio-start="'), "first-screen classification must not execute work");
assert.ok(firstScreen.includes("data-portfolio-start-horizon"), "the time destinations are exposed without executing work");
assert.ok(firstScreen.includes('data-portfolio-open-execution="a"'), "an exact item opens its own execution drawer");
assert.ok(firstScreen.includes("data-research-calendar") && firstScreen.includes("research-calendar-agenda"), "Now provides the calendar and its compact agenda");
assert.ok(firstScreen.includes('class="research-calendar-day-more"'), "calendar overflow is an expandable disclosure");
assert.ok(firstScreen.includes('data-calendar-drag-item="a"'), "editable attention dates expose a drag affordance");
assert.ok(firstScreen.includes('data-calendar-open-card="waiting"'), "undated event-driven work stays visible without an inferred date");
assert.deepEqual(Array.from(Portfolio.calendarUndatedItems(privateModel.items), (item) => item.id), ["waiting"]);
for (const retired of ["data-research-portfolio-library", "data-portfolio-zone=", "data-portfolio-library-mode", "research-management-zone-controls", "data-unfinished-prompt"]) {
  assert.ok(!firstScreen.includes(retired), `Now must not render the retired ${retired}`);
}
assert.equal(Portfolio.renderLibrary({ researchPortfolio: privateModel }, { translate: text }), "", "Library owns no project lifecycle surface");
for (const name of ["research-attention-board", "research-calendar-agenda", "research-calendar-day-more"]) assert.ok(styled(name), `${name} must be styled`);

const Plugin = context.ResearchOSResearchPortfolioPlugin;
assert.equal(Plugin.renderProcessing, undefined, "Portfolio renders no second task lifecycle");
const publicSlot = { payloads: { research_portfolio: portfolioPayload("public_demo") } };
assert.ok(Plugin.renderWorkbench(publicSlot, { escapeHtml, previewButton: () => "", publicDemoVisible: () => true, text }).includes('<details class="research-portfolio-public-example">'), "the public fictional agenda stays folded behind onboarding");

// Opening a Today item binds its research step to a Work Session and opens that item's own drawer.
function bindPortfolio(slot, overrides = {}) {
  const calls = { dispatched: [], drafted: [], drawers: [] };
  const button = (dataset) => element("button", { dataset });
  const cells = ["2026-08-12", "2026-08-13"].map((date) => element("div", { dataset: { calendarDate: date } }));
  const drag = button({ calendarDragItem: "a", calendarEventDate: "2026-08-12" });
  drag.setPointerCapture = (pointerId) => { calls.captured = pointerId; };
  drag.cloneNode = () => element("div");
  const calendar = element("section", { dataset: { researchCalendar: "" }, children: [...cells, drag] });
  const openToday = button({ portfolioOpenToday: "b" });
  const root = element("section", { dataset: { researchPortfolio: "" }, children: [calendar, openToday] });
  Plugin.bindWorkbench({
    context: {
      attentionMutationAvailable: () => true,
      dispatchPluginAction: async (request) => { calls.dispatched.push(request); return { ok: true }; },
      draftWorkSession: (session) => { calls.drafted.push(session); return { ok: true, session }; },
      escapeHtml,
      openItemExecutionDrawer: (...args) => calls.drawers.push(args),
      previewButton: () => "",
      rerenderDashboard: () => { calls.rerendered = (calls.rerendered || 0) + 1; },
      text,
      ...overrides,
    },
    model: slot,
    root,
  });
  // Bubbling stand-in: listeners on the calendar fire first, then any handler the root owns.
  const bubble = (type, event) => {
    const value = { type, target: calendar, preventDefault() {}, ...event };
    calendar.dispatchEvent(value);
    root[`on${type}`]?.(value);
  };
  return { bubble, calendar, calls, cells, drag, openToday };
}
const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

(async () => {
  const privateSlot = { payloads: { research_portfolio: portfolioPayload("private_authority") } };
  const opened = bindPortfolio(privateSlot);
  opened.openToday.click();
  await flush();
  assert.equal(opened.calls.drafted.length, 1, "opening a Today item drafts its bound Work Session");
  assert.equal(opened.calls.drafted[0].portfolioBinding.itemId, "b");
  assert.deepEqual(JSON.parse(JSON.stringify(opened.calls.drawers)), [["b", "work", { focus: true }]], "execution continuity opens on the exact item, not a global Work screen");

  // A calendar move by keyboard reuses the reversible attention-schedule owner.
  opened.drag.dispatchEvent({ type: "keydown", altKey: true, key: "ArrowRight" });
  await flush();
  assert.equal(opened.calls.dispatched.length, 1);
  assert.equal(opened.calls.dispatched[0].actionId, "update_portfolio_attention");
  assert.equal(opened.calls.dispatched[0].input.action.action, "schedule");
  assert.equal(opened.calls.dispatched[0].input.action.attentionDate, "2026-08-13", "Alt+ArrowRight moves the item one day later");
  assert.ok(opened.calls.dispatched[0].input.action.receiptMessage, "a calendar move carries an undo receipt message");

  // A pointer drag captures the pointer, marks the drop target while moving and schedules on release.
  const dragged = bindPortfolio(privateSlot);
  context.document.elementFromPoint = () => dragged.cells[1];
  dragged.drag.dispatchEvent({ type: "pointerdown", button: 0, pointerId: 7, clientX: 0, clientY: 0 });
  dragged.bubble("pointermove", { pointerId: 7, clientX: 40, clientY: 0 });
  assert.equal(dragged.calls.captured, 7, "a started drag holds the pointer so it can leave the card");
  assert.equal(dragged.drag.getAttribute("aria-grabbed"), "true");
  assert.ok(dragged.cells[1].classList.contains("is-drop-target"), "the cell under the pointer shows the drop target");
  dragged.bubble("pointerup", { pointerId: 7, clientX: 40, clientY: 0 });
  await flush();
  assert.equal(dragged.calls.dispatched.at(-1)?.input.action.attentionDate, "2026-08-13", "releasing over a day schedules the item there");
  assert.equal(dragged.drag.getAttribute("aria-grabbed"), "false");
  delete context.document.elementFromPoint;

  if (privateEdition) {
    // The private desk also accepts native drag and drop onto a day.
    const native = bindPortfolio(privateSlot);
    native.drag.dispatchEvent({ type: "dragstart", dataTransfer: { setData() {} } });
    native.cells[1].dispatchEvent({ type: "dragover" });
    assert.ok(native.cells[1].classList.contains("is-drop-target"));
    native.cells[1].dispatchEvent({ type: "drop", dataTransfer: { getData: () => "" } });
    await flush();
    assert.equal(native.calls.dispatched.at(-1)?.input.action.attentionDate, "2026-08-13");
  }

  // In the public demo the same gesture is an in-memory preview and never dispatches.
  const preview = bindPortfolio(publicSlot);
  preview.drag.dispatchEvent({ type: "keydown", altKey: true, key: "ArrowRight" });
  await flush();
  assert.equal(preview.calls.dispatched.length, 0, "the public demo never persists a calendar move");
  assert.ok(preview.calls.rerendered > 0, "the public preview rerenders Now");

  // --- Work Session lifecycle: explicit handoff reveals Review inside the exact item's drawer ------------------------
  let session = context.ResearchOSWorkSessionState.createSession({ intent: "Check the fictional evidence", portfolioBinding: { itemId: "b", title: "Item b" } });
  const doingItems = [];
  const panels = [];
  const lifecycle = context.ResearchOSWorkSessionWorkbenchService.createWorkSessionLifecycle({
    addDoingItem: (item) => doingItems.push({ ...item, status: "local" }),
    getDoingItems: () => doingItems,
    getSession: () => session,
    openItemPanel: (panel) => panels.push(panel),
    saveSession: (next) => { session = next; return next; },
  }, { inboxStatusIsActive: () => true, itemKey: (item) => item.id });
  lifecycle.prepareHandoff();
  assert.equal(doingItems.length, 1, "the first handoff creates one Review entry");
  lifecycle.prepareHandoff();
  assert.equal(doingItems.length, 1, "a repeated handoff does not duplicate the Review entry");
  assert.deepEqual(panels, ["review", "review"], "both handoff paths reveal Review inside the item's drawer");

  // --- Library: adding from Assets enters Review through the kernel without navigating ------------------------------
  const assets = loadModules(["dashboard/src/core/ui.js", "dashboard/src/services/plugin-runtime.js", "dashboard/src/plugins/research-assets.js"], {
    localStorage: { getItem() { return null; }, setItem() {} },
  }).ResearchOSResearchAssetsPlugin;
  const added = [];
  const navigation = [];
  const status = element("output");
  assets.handleAssetTask({ payload: { id: "asset-task", title: "Fictional asset task" }, status }, {
    addTransientTask: (payload, origin) => added.push([payload.id, origin]),
    openWorkspace: (...args) => navigation.push(args),
    setWorkspaceTab: (...args) => navigation.push(args),
    text,
  });
  assert.deepEqual(added, [["asset-task", "local"]], "asset actions enter Review through the kernel API");
  assert.deepEqual(navigation, [], "adding from Assets must not navigate automatically");

  // --- Switching workspaces starts the new page at the top -----------------------------------------------------------
  const shell = loadModules(["dashboard/src/core/ui.js", "dashboard/src/core/interactions.js", "dashboard/src/services/workspace-shell-workbench.js"]);
  const scrolls = [];
  shell.scrollTo = (options) => scrolls.push({ ...options });
  const tabs = ["now", "library"].map((tab) => element("button", { dataset: { workspaceTab: tab } }));
  const workspacePanels = ["now", "library"].map((tab) => element("section", { dataset: { workspacePanel: tab } }));
  shell.ResearchOSWorkspaceShellWorkbenchService.syncWorkspaceShell(element("main", { children: [...tabs, ...workspacePanels] }), { scroll: true, selectedWorkspace: "library" });
  await flush();
  assert.deepEqual(workspacePanels.map((panel) => panel.hidden), [true, false], "only the selected workspace panel is shown");
  assert.equal(tabs[1].getAttribute("aria-selected"), "true");
  assert.deepEqual(scrolls, [{ top: 0, left: 0, behavior: "auto" }], "switching a workspace starts the new page at the top");

  console.log("Calm handoff contract regression passed.");
})().catch((error) => { console.error(error); process.exitCode = 1; });
