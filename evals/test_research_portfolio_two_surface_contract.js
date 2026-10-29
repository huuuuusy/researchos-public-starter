/* Two-surface contract: Now owns every Today commitment, the calendar and project lifecycle; Library owns none of it.
 * Runs the real portfolio copy, model, view and workbench on a fictional public-demo payload in both editions.
 */
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { frozenDate, loadModules, read, root } = require("./helpers/dashboard-vm.js");

const context = loadModules([
  "dashboard/src/core/surface-contract.js",
  "dashboard/src/services/result-envelope.js",
  "dashboard/src/services/work-session-state.js",
  "dashboard/src/services/plugin-runtime.js",
  "dashboard/src/plugins/research-portfolio-copy.js",
  "dashboard/src/plugins/research-portfolio-model.js",
  "dashboard/src/plugins/research-portfolio-view.js",
  "dashboard/src/plugins/research-portfolio-workbench.js",
  "dashboard/src/views/home-command-center.js",
], {
  crypto: { randomUUID: () => "portfolio-contract-session" },
  Date: frozenDate("2026-08-16T12:00:00+08:00"),
  ResearchOSConfirmationState: {},
  ResearchOSDoingBoardState: {},
  ResearchOSInteractions: { bindAll() {} },
  ResearchOSUiCore: { escapeHtml: (value) => String(value ?? "") },
});
const View = context.ResearchOSResearchPortfolioView;

const manifest = JSON.parse(read("config/plugins/research-portfolio.json"));
assert.equal(manifest.version, "2.0.0");
assert.deepEqual([...new Set(manifest.contributions.actions.map((entry) => entry.surface))], ["start"], "plugin schema keeps start as the internal Now-slot id");
assert.deepEqual(manifest.contributions.ui_slots.map((entry) => entry.surface), ["start"]);
assert.ok(manifest.authority.candidate.includes("Library never owns project state or scheduling"));

const payload = {
  available: true,
  presentation_mode: "public_demo",
  sensitivity: "public",
  items: [
    { id: "today-a", title: "Today A", provider_id: "research_portfolio", responsibility: "lead", state: "mainline", lifecycle_state: "open", lifecycle_phase: "writing", attention_state: "today", attention_date: "2026-08-16", today_order: 1, next_step: "Write the result", source_available: true, source_path: "examples/demo-research-agenda.md", last_verified: "2026-08-16" },
    { id: "today-b", title: "Today B", provider_id: "research_portfolio", responsibility: "support", state: "mainline", lifecycle_state: "open", lifecycle_phase: "production", attention_state: "today", attention_date: "2026-08-16", today_order: 2, next_step: "Check evidence", last_verified: "2026-08-16" },
    { id: "today-c", title: "Today C", provider_id: "research_portfolio", responsibility: "lead", state: "mainline", lifecycle_state: "open", lifecycle_phase: "writing", attention_state: "today", attention_date: "2026-08-16", today_order: 3, next_step: "Draft the figure", last_verified: "2026-08-16" },
    { id: "today-d", title: "Today D", provider_id: "research_portfolio", responsibility: "lead", state: "mainline", lifecycle_state: "open", lifecycle_phase: "writing", attention_state: "today", attention_date: "2026-08-16", today_order: 4, next_step: "Read the reviews", last_verified: "2026-08-16" },
    { id: "waiting-c", title: "Waiting C", provider_id: "research_portfolio", responsibility: "lead", state: "waiting", lifecycle_state: "waiting", lifecycle_phase: "under_review", attention_state: "waiting", review_date: "2026-08-20", activation_trigger: "Reviewer response", next_step: "Wait", last_verified: "2026-08-16" },
    { id: "future-d", title: "Future D", provider_id: "research_portfolio", responsibility: "lead", state: "queued", lifecycle_state: "open", lifecycle_phase: "planned", attention_state: "upcoming", attention_date: "2026-09-03", next_step: "Start later", last_verified: "2026-08-16" },
    { id: "closed-e", title: "Closed E", provider_id: "research_portfolio", responsibility: "lead", state: "closed", lifecycle_state: "completed", lifecycle_phase: "completed", attention_state: "completed", next_step: "Done", last_verified: "2026-08-16" },
  ],
};
const todayIds = ["today-a", "today-b", "today-c", "today-d"];
const copy = (key) => context.ResearchOSResearchPortfolioCopy.text("en", key);
const model = context.ResearchOSResearchPortfolioModel.build(payload, copy, "en");
assert.equal(model.items.length, 7);
assert.deepEqual(Array.from(View.startHorizonGroups(model.items).today, (item) => item.id).sort(), todayIds, "every Today commitment belongs to the Today horizon");

const html = View.render({
  calendarMonth: "2026-08",
  calendarView: "month",
  mutationEnabled: false,
  researchPortfolio: model,
  sessionRegistry: [
    { item_id: "today-a", session_id: "session-a", run_id: "run-a", work_state: "active" },
    { item_id: "today-a", session_id: "session-b", run_id: "run-b", work_state: "needs_review" },
  ],
}, { escapeHtml: (value) => String(value ?? ""), previewButton: () => "", translate: copy });

// Four Today items guard against the retired three-item cap on Now.
assert.equal((html.match(/class="research-attention-card state-/g) || []).length, todayIds.length, "Now must show every Today commitment directly");
for (const id of todayIds) assert.ok(html.includes(`data-attention-card="${id}"`), `Today commitment ${id} must be directly discoverable`);
assert.ok(html.includes('data-attention-sort-item="today-a"'), "Today cards must be reorderable");
assert.ok(html.includes('data-attention-reorder="up"'), "button ordering must be available without drag");
assert.ok(html.includes('data-calendar-view="week"') && html.includes('data-calendar-view="month"'), "Now must expose week/month calendar modes");
assert.ok(html.includes("data-now-active-projects"), "Now must own project lifecycle context");
for (const id of ["today-a", "today-b", "waiting-c", "future-d"]) assert.ok(html.includes(`data-lifecycle-card="${id}"`), `active project ${id} must remain visible on Now`);
assert.ok(html.includes("2 sessions · 1 active · 1 needs review"), "an exact item must show its execution summary");
assert.ok(html.includes('data-portfolio-open-library="today-a"'), "only an explicit View related action may navigate to Library");
assert.ok(html.includes('data-portfolio-open-execution="today-a"'), "execution must open from an exact item");
assert.ok(html.includes("research-attention-demo-boundary"), "the public demo must state its copy-only boundary on Now");
assert.equal(View.renderLibrary({ researchPortfolio: model }, { translate: copy }), "", "Library must not duplicate project status or calendar");

const weekHtml = View.renderCalendarWeek(model.items, "2026-08-16", {
  calendarMoveEnabled: true,
  escapeHtml: (value) => String(value ?? ""),
  mutationEnabled: false,
  publicDemo: true,
  translate: copy,
});
assert.equal((weekHtml.match(/data-calendar-date=/g) || []).length, 7);
assert.ok(weekHtml.includes('data-calendar-drag-item="today-a"'));
assert.ok(!weekHtml.includes('data-calendar-drag-item="waiting-c"'), "review markers must remain fixed");

const nowHtml = context.ResearchOSHomeCommandCenterView.renderNowHtml({}, {
  escapeHtml: (value) => String(value ?? ""),
  sectionTranslate: (key) => key,
  translate: (key) => key,
});
assert.ok(nowHtml.includes('data-plugin-slot-host="workbench"'), "Now hosts the portfolio through its workbench slot");
assert.ok(!nowHtml.includes('data-open-workspace="work"'), "Now auxiliary actions must not navigate to a third Work surface");

// Retired navigation: portfolio actions open item-local drawers, never a third Work or Review screen.
const pluginSource = read("dashboard/src/plugins/research-portfolio.js");
assert.ok(!pluginSource.includes('openWorkspace?.("work"'), "portfolio actions must not navigate to a third Work surface");
assert.ok(!pluginSource.includes('openWorkspace?.("review"'), "portfolio actions must not navigate to a Review surface");

// Layout is checked by screenshots; the calendar and drop-target classes the views use must at least be styled.
const styled = new Set();
const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).forEach((entry) => {
  const full = path.join(dir, entry.name);
  if (entry.isDirectory()) walk(full);
  else if (entry.name.endsWith(".css")) for (const match of fs.readFileSync(full, "utf8").matchAll(/\.(-?[A-Za-z_][\w-]*)/g)) styled.add(match[1]);
});
walk(path.join(root, "dashboard/styles"));
assert.ok(weekHtml.includes("research-calendar-week-grid") && styled.has("research-calendar-week-grid"), "the week grid must be rendered and styled");
assert.ok(styled.has("is-drop-target"), "drag targets must have a visible drop state");

console.log("research portfolio two-surface contract ok");
