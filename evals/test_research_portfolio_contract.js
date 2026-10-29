/* Research Portfolio contract: shared model plus each edition's view, workbench and plugin, driven by fictional fixtures.
 * The fixture evals/fixtures/dashboard/research-portfolio-demo.json is a copy of the public demo agenda, so this file is
 * byte-identical in both repositories and never reads a dashboard data file.
 */
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { element, frozenDate, loadModules, read, root } = require("./helpers/dashboard-vm.js");

const dashboardIndex = read("dashboard/index.html");
assert.ok(dashboardIndex.includes('<script src="src/components/preview-links.js"></script>'), "index.html must load the context-aware preview labels");
assert.ok(dashboardIndex.includes('<link rel="stylesheet" href="style.css" />') && !dashboardIndex.includes("?v="), "index.html loads the stylesheet without a ?v= cache query");
for (const script of [
  "src/plugins/research-portfolio-copy.js",
  "src/plugins/research-portfolio-model.js",
  "src/plugins/research-portfolio-view.js",
  "src/plugins/research-portfolio-workbench.js",
  "src/plugins/research-portfolio.js",
]) assert.ok(dashboardIndex.includes(`<script src="${script}"></script>`), `${script} must be registered in index.html`);
assert.ok(read("dashboard/style.css").includes("./styles/views/research-portfolio.css"), "the portfolio stylesheet must be imported");

const FrozenDate = frozenDate("2026-08-12T12:00:00Z");
const context = loadModules([
  "dashboard/src/core/interactions.js",
  "dashboard/src/core/surface-contract.js",
  "dashboard/src/services/result-envelope.js",
  "dashboard/src/services/work-session-state.js",
  "dashboard/src/core/ui.js",
  "dashboard/src/services/plugin-runtime.js",
  "dashboard/src/views/home-command-center.js",
  "dashboard/src/plugins/research-portfolio-model.js",
  "dashboard/src/plugins/research-portfolio-view.js",
  "dashboard/src/plugins/research-portfolio-workbench.js",
  "dashboard/src/plugins/research-portfolio.js",
], {
  crypto: { randomUUID: () => "portfolio-contract-session" },
  Date: FrozenDate,
  ResearchOSConfirmationState: {},
  ResearchOSDoingBoardState: {},
  ResearchOSUiCore: {},
});
// The copy catalog is loaded on its own so the plugin under test keeps returning raw keys.
const portfolioCopy = loadModules(["dashboard/src/plugins/research-portfolio-copy.js"]).ResearchOSResearchPortfolioCopy;
const demoPortfolio = () => JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures/dashboard/research-portfolio-demo.json"), "utf8"));

// Every class the rendered portfolio uses with a research- prefix must be styled somewhere under dashboard/styles.
function stylesheetClasses() {
  const names = new Set();
  const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).forEach((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.name.endsWith(".css")) {
      const css = fs.readFileSync(full, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
      for (const match of css.matchAll(/\.(-?[A-Za-z_][\w-]*)/g)) names.add(match[1]);
    }
  });
  walk(path.join(root, "dashboard/styles"));
  return names;
}
const renderedClasses = (html) => new Set([...String(html).matchAll(/class="([^"]*)"/g)].flatMap((match) => match[1].split(/\s+/)).filter(Boolean));

const demoModel = context.ResearchOSResearchPortfolioModel.build(
  demoPortfolio(),
  (key) => key,
);
const demoHorizons = context.ResearchOSResearchPortfolioView.startHorizonGroups(demoModel.items);
const demoHorizonIds = Object.values(demoHorizons).flat().map((item) => item.id);
assert.equal(new Set(demoHorizonIds).size, demoHorizonIds.length, "a demo project must not appear in more than one Start destination");
for (const item of demoModel.items.filter((candidate) => context.ResearchOSResearchPortfolioView.parkedCommitment(candidate))) {
  assert.ok(
    demoHorizons.frozen.some((candidate) => candidate.id === item.id),
    `the demo manually parked commitment ${item.id} must remain reachable under Parked`,
  );
}

const portfolioManifest = JSON.parse(read("config/plugins/research-portfolio.json"));
const manifestCandidate = portfolioManifest.authority?.candidate || "";
const librarySlot = portfolioManifest.contributions?.ui_slots?.find((slot) => slot.id === "research_portfolio_library") || {};
assert.equal(portfolioManifest.version, "2.0.0", "the shared portfolio contract version must change with the two-surface direct-interaction composition");
assert.equal(portfolioManifest.contributions.ui_slots.some((slot) => slot.surface === "next"), false, "Portfolio must not add a second task lifecycle to Next");
assert.equal(portfolioManifest.contributions.actions.some((action) => action.id === "copy_portfolio_task_packet"), false, "task-packet handoff must stay with the Work Session owner");
assert.equal(Object.keys(librarySlot).length, 0, "Library must not receive a duplicate project-status slot");
assert.ok(manifestCandidate.includes("Now projects every Today commitment, confirmed calendar date, active or waiting project"));
assert.ok(manifestCandidate.includes("Library never owns project state or scheduling"));
const overnightAttention = context.ResearchOSResearchPortfolioModel.liveAttention(
  "today",
  "2026-08-06",
  0,
  new FrozenDate("2026-08-09T12:00:00Z"),
);
assert.equal(overnightAttention.attentionState, "carryover", "an overnight projection must become an explicit carryover");
assert.equal(overnightAttention.carryoverDays, 3, "carryover age must be recomputed without requiring a rebuild");
const currentAttention = context.ResearchOSResearchPortfolioModel.liveAttention(
  "today",
  "2026-08-09",
  0,
  new FrozenDate("2026-08-09T12:00:00Z"),
);
assert.equal(currentAttention.attentionState, "today", "an item planned for the current day must remain today");
assert.equal(currentAttention.carryoverDays, 0);
const upcomingBecomesToday = context.ResearchOSResearchPortfolioModel.liveAttention(
  "upcoming",
  "2026-08-09",
  0,
  new FrozenDate("2026-08-09T12:00:00Z"),
);
assert.equal(upcomingBecomesToday.attentionState, "today", "an upcoming item must become Today after midnight without rebuilding dashboard data");
const staleUpcomingBecomesCarryover = context.ResearchOSResearchPortfolioModel.liveAttention(
  "upcoming",
  "2026-08-06",
  0,
  new FrozenDate("2026-08-09T12:00:00Z"),
);
assert.equal(staleUpcomingBecomesCarryover.attentionState, "carryover", "an overdue upcoming item must become carryover without rebuilding dashboard data");
assert.equal(staleUpcomingBecomesCarryover.carryoverDays, 3);
const futureAttention = context.ResearchOSResearchPortfolioModel.liveAttention(
  "today",
  "2026-08-10",
  0,
  new FrozenDate("2026-08-09T12:00:00Z"),
);
assert.equal(futureAttention.attentionState, "upcoming", "a rescheduled future item must not remain mislabeled as Today");

for (const [item, expectedBucket, expectedZone] of [
  [{ state: "mainline", lifecycleState: "open" }, "active", "active"],
  [{ state: "queued", lifecycleState: "open" }, "queued", "pending"],
  [{ state: "conditional", lifecycleState: "open" }, "project_candidate", "pending"],
  [{ state: "waiting", lifecycleState: "open" }, "waiting", "inactive"],
  [{ state: "mainline", lifecycleState: "waiting" }, "waiting", "inactive"],
  [{ state: "paused", lifecycleState: "paused" }, "paused", "inactive"],
  [{ state: "closed", lifecycleState: "open" }, "closed", "closed"],
]) {
  const bucket = context.ResearchOSResearchPortfolioModel.managementBucketForItem(item);
  assert.equal(bucket, expectedBucket, `${JSON.stringify(item)} must derive ${expectedBucket}`);
  assert.equal(context.ResearchOSResearchPortfolioModel.managementZoneForBucket(bucket), expectedZone);
}

const localizedPublicModel = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "public_demo",
  items: [{
    id: "localized-demo",
    title: "Evaluation Pilot Decision",
    next_step: "Inspect the pilot evidence",
    source_path: "08_exports/public_starter/demo-research-agenda.md",
    responsibility: "lead",
    state: "mainline",
    lifecycle_phase: "experiment_preparation",
    lifecycle_state: "open",
    attention_state: "today",
    localized: {
      "zh-CN": {
        title: "评估 Pilot 判断",
        next_step: "检查 pilot 证据",
        source_path: "08_exports/public_starter/demo-research-agenda.zh.md",
      },
    },
  }],
}, (key) => key, "zh-CN");
assert.equal(localizedPublicModel.items[0].title, "评估 Pilot 判断", "the public demo must follow the selected UI language");
assert.equal(localizedPublicModel.items[0].nextStep, "检查 pilot 证据");
assert.ok(localizedPublicModel.items[0].sourcePath.endsWith("demo-research-agenda.zh.md"));

const crossMidnightModel = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "private_authority",
  items: [{
    id: "cross-midnight-task",
    title: "Cross-midnight task",
    responsibility: "lead",
    state: "mainline",
    lifecycle_phase: "writing",
    lifecycle_state: "open",
    attention_state: "upcoming",
    attention_date: "2026-08-12",
    next_step: "Run the scheduled task",
    last_verified: "2026-08-12",
  }],
}, (key) => key);
assert.equal(crossMidnightModel.items[0].attentionState, "today");
const crossMidnightStartHtml = context.ResearchOSResearchPortfolioView.render(
  { researchPortfolio: crossMidnightModel },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(crossMidnightStartHtml.includes('data-attention-card="cross-midnight-task"'), "the Today body must render a task whose saved upcoming date became today");
assert.ok(!crossMidnightStartHtml.includes("researchAttentionNothingActionable"), "a non-empty Today count must never render the empty-Today message");
assert.equal(portfolioManifest.contributions.ui_slots.filter((slot) => slot.surface === "next").length, 0, "Start must bind a Today commitment into Work Session instead of rendering it again on Next");
assert.equal(context.ResearchOSResearchPortfolioView.currentMonthKey(), "2026-08");
assert.equal(context.ResearchOSResearchPortfolioView.shiftMonthKey("2026-08", 1), "2026-09");
assert.equal(context.ResearchOSResearchPortfolioView.shiftMonthKey("2026-01", -1), "2025-12");
assert.equal(context.ResearchOSResearchPortfolioView.shiftIsoDate("2026-08-31", 1), "2026-09-01");
assert.equal(context.ResearchOSResearchPortfolioView.shiftIsoDate("2026-08-08", -7), "2026-08-01");
assert.equal(context.ResearchOSResearchPortfolioView.validIsoDate("2026-02-31"), false, "calendar projection must reject impossible dates");
assert.equal(context.ResearchOSResearchPortfolioView.monthCells("2026-08").flat().filter(Boolean).length, 31);

const calendarFixture = [
  {
    id: "dated-project",
    title: "Dated project",
    lifecycleState: "open",
    lifecyclePhase: "writing",
    attentionDate: "2026-08-08",
    reviewDate: "2026-08-15",
    deadline: "2026-09-01",
  },
  {
    id: "event-project",
    title: "Event-driven project",
    lifecycleState: "waiting",
    lifecyclePhase: "under_review",
    activationTrigger: "Reviews arrive",
  },
  {
    id: "future-only-project",
    title: "Scheduled next month",
    lifecycleState: "open",
    lifecyclePhase: "writing",
    deadline: "2026-09-15",
  },
  {
    id: "inactive-review",
    title: "Inactive review",
    lifecycleState: "open",
    lifecyclePhase: "under_review",
    backgroundPhase: true,
    eventTriggered: false,
    attentionState: "carryover",
    attentionDate: "2026-08-07",
  },
  {
    id: "completed-project",
    title: "Completed project",
    lifecycleState: "completed",
    lifecyclePhase: "completed",
    attentionDate: "2026-08-09",
  },
  {
    id: "paused-review",
    title: "Paused until review",
    state: "mainline",
    lifecycleState: "paused",
    lifecyclePhase: "writing",
    attentionDate: "2026-08-07",
    reviewDate: "2026-08-20",
  },
  {
    id: "paused-undated",
    title: "Paused without review",
    state: "mainline",
    lifecycleState: "paused",
    lifecyclePhase: "writing",
  },
];
assert.deepEqual(
  Array.from(context.ResearchOSResearchPortfolioView.calendarEvents(calendarFixture), (event) => [event.date, event.type]),
  [["2026-08-08", "attention"], ["2026-08-15", "review"], ["2026-08-20", "review"], ["2026-09-01", "deadline"], ["2026-09-15", "deadline"]],
  "calendar projection must preserve explicit schedule, review, and deadline dates, including the resurface date of paused work",
);
assert.deepEqual(
  Array.from(context.ResearchOSResearchPortfolioView.calendarOtherMonthEvents(calendarFixture, "2026-08"), (event) => [event.item.id, event.date, event.type]),
  [["future-only-project", "2026-09-15", "deadline"]],
  "the selected month must explain projects scheduled elsewhere without duplicating projects already represented this month",
);
assert.deepEqual(
  Array.from(context.ResearchOSResearchPortfolioView.calendarUndatedItems(calendarFixture), (item) => item.id),
  ["event-project", "inactive-review", "paused-undated"],
  "every open project without a visible date must remain in the undated lane, including paused work",
);
assert.ok(
  !context.ResearchOSResearchPortfolioView.calendarEvents(calendarFixture).some((event) => event.item.id === "paused-review" && event.type === "attention"),
  "a stale attention date must not masquerade as planned work after the project is paused",
);
assert.equal(context.ResearchOSResearchPortfolioView.horizonForItem(calendarFixture.find((item) => item.id === "dated-project"), "2026-08-09"), "today");
assert.equal(context.ResearchOSResearchPortfolioView.horizonForItem(calendarFixture.find((item) => item.id === "event-project"), "2026-08-09"), "frozen");
assert.equal(context.ResearchOSResearchPortfolioView.horizonForItem(calendarFixture.find((item) => item.id === "inactive-review"), "2026-08-09"), "frozen");
assert.equal(context.ResearchOSResearchPortfolioView.horizonForItem({
  lifecycleState: "paused",
  lifecyclePhase: "writing",
  attentionState: "review_due",
  reviewDate: "2026-08-09",
}, "2026-08-09"), "today", "a paused project must resurface on Today when its explicit review becomes due");
assert.equal(context.ResearchOSResearchPortfolioView.horizonForItem({
  lifecycleState: "waiting",
  lifecyclePhase: "under_review",
  attentionState: "unscheduled",
  eventTriggered: true,
}, "2026-08-09"), "today", "a waiting project must resurface on Today when its external event arrives");
assert.equal(context.ResearchOSResearchPortfolioView.horizonForItem({
  lifecycleState: "open",
  attentionDate: "2026-08-10",
}, "2026-08-09"), "tomorrow");
const calendarFixtureHtml = context.ResearchOSResearchPortfolioView.renderCalendarMonth(calendarFixture, "2026-08", {
  escapeHtml: String,
  translate: (key) => key,
});
assert.ok(calendarFixtureHtml.includes('data-calendar-date="2026-08-08"'));
assert.ok(calendarFixtureHtml.includes('data-calendar-open-card="dated-project"'));
assert.ok(calendarFixtureHtml.includes('data-calendar-open-card="event-project"'));
assert.ok(calendarFixtureHtml.includes('data-calendar-open-card="future-only-project"'));
assert.ok(calendarFixtureHtml.includes("researchCalendarOtherMonthsHint"));
assert.ok(calendarFixtureHtml.includes("researchCalendarUndatedHint"));
assert.ok(!calendarFixtureHtml.includes("data-calendar-drag-item"), "a read-only calendar projection must not pretend that drag changes can be saved");
const overflowFixture = Array.from({ length: 4 }, (_, index) => ({
  id: `plan-${index + 1}`,
  title: `Plan ${index + 1}`,
  lifecycleState: "open",
  lifecyclePhase: "writing",
  attentionDate: "2026-08-08",
}));
overflowFixture.push({
  id: "fixed-review",
  title: "Fixed review",
  lifecycleState: "open",
  lifecyclePhase: "under_review",
  reviewDate: "2026-08-08",
});
const movableCalendarHtml = context.ResearchOSResearchPortfolioView.renderCalendarMonth(overflowFixture, "2026-08", {
  escapeHtml: String,
  calendarMoveEnabled: true,
  mutationEnabled: true,
  translate: (key) => key === "researchCalendarMore" ? "+{count}" : key,
});
assert.equal((movableCalendarHtml.match(/data-calendar-drag-item=/g) || []).length, 8, "each movable attention event must be draggable in both desktop and mobile calendar projections");
assert.ok(movableCalendarHtml.includes('data-calendar-drag-item="plan-1"'));
assert.ok(!movableCalendarHtml.includes('data-calendar-drag-item="fixed-review"'), "review and deadline facts must remain fixed markers");
assert.ok(movableCalendarHtml.includes('class="research-calendar-day-more"'), "calendar overflow must use an expandable disclosure");
assert.ok(movableCalendarHtml.includes('<summary role="button"'), "calendar overflow must expose a clear button affordance to assistive technology");
assert.ok(movableCalendarHtml.includes("+2"), "the overflow disclosure must state how many hidden events can be expanded");
const publicPreviewCalendarHtml = context.ResearchOSResearchPortfolioView.renderCalendarWeek(
  overflowFixture,
  "2026-08-08",
  {
    calendarMoveEnabled: true,
    escapeHtml: String,
    mutationEnabled: false,
    publicDemo: true,
    translate: (key) => key,
  },
);
assert.ok(publicPreviewCalendarHtml.includes('data-calendar-drag-item="plan-1"'), "the public starter must expose the same drag gesture as an explicitly transient preview");
for (const language of ["en", "zh-CN"]) assert.ok(portfolioCopy.text(language, "researchCalendarInteractionPreview"), `the transient calendar preview must be explained in ${language}`);

const rawPortfolio = demoPortfolio();
const model = context.ResearchOSResearchPortfolioModel.build(rawPortfolio, (key) => key);
const privateAuthority = model.presentationMode === "private_authority";

assert.equal(model.available, true, "the runtime authority board must project onto the home page");
assert.ok(["private_authority", "public_demo"].includes(model.presentationMode));
assert.equal(model.publicDemo, !privateAuthority);
assert.equal(model.items.length, rawPortfolio.answer.registered_total, "the model must preserve every registered ledger item");
assert.equal(model.answer.leadActive, rawPortfolio.answer.lead_active, "the default answer must preserve accountable lead mainlines");
assert.equal(model.answer.supportActive, rawPortfolio.answer.support_active);
assert.equal(model.answer.waiting, rawPortfolio.answer.waiting);
assert.equal(model.answer.paused, rawPortfolio.answer.paused);
assert.equal(
  model.answer.needsReview,
  model.items.filter((item) => item.needsAttention && item.state !== "closed").length,
  "needs-review count must follow the current freshness projection instead of a date-frozen fixture value",
);
assert.equal(model.answer.unclassified, 0);
assert.equal(model.answer.registeredTotal, model.items.length);
assert.equal(model.answer.classifiedTotal, model.items.length);
assert.equal(model.answer.coverageVerified, model.coverage.complete,
  "coverage verification must preserve the fail-closed model result");
if (!rawPortfolio.coverage.complete) {
  assert.equal(model.coverage.complete, false,
    "a regenerated incomplete coverage receipt must not become verified");
}
for (const [reviewed, complete, expected] of [
  ["2026-08-11", true, true],
  ["2026-07-01", true, false],
  ["2026-08-11", false, false],
]) {
  const coverageModel = context.ResearchOSResearchPortfolioModel.build({
    ...rawPortfolio,
    coverage: { ...rawPortfolio.coverage, reviewed, complete,
      stale_after_days: 30, candidates: [], missing_sources: [] },
  }, (key) => key);
  assert.equal(coverageModel.answer.coverageVerified, expected);
  assert.equal(coverageModel.coverage.complete, expected);
}
assert.ok(model.items.every((item) => item.lifecyclePhase), "every project must expose an explicit lifecycle phase");
assert.ok(model.items.every((item) => item.managementBucket), "every project must expose one derived management bucket");
assert.ok(model.items.every((item) => item.managementZone), "every project must expose one derived management area");
assert.equal(
  Object.values(model.managementZoneCounts).reduce((sum, count) => sum + count, 0),
  model.items.length,
  "the four management areas must preserve every registered project",
);
assert.equal(
  Object.values(model.managementCounts).reduce((sum, count) => sum + count, 0),
  model.items.length,
  "derived management buckets, including fail-closed unclassified items, must preserve every project",
);
assert.ok(
  model.items.filter((item) => item.backgroundPhase).every((item) => item.activationTrigger),
  "background review stages must state which event resurfaces them",
);
assert.ok(
  model.actionItems.every((item) => item.actionable),
  "the first-screen projection must contain only actionable attention",
);
assert.equal(model.defaultFilter, "lead_active");
assert.deepEqual(
  model.items.slice(0, model.answer.leadActive).map((item) => [item.responsibility, item.state]),
  Array.from({ length: model.answer.leadActive }, () => ["lead", "mainline"]),
  "accountable lead mainlines must be the first-class default"
);
if (privateAuthority) {
  assert.ok(
    model.items.some((item) => item.responsibility === "support" && item.engagement === "temporary"),
    "the authority ledger must distinguish temporary involvement from ongoing collaboration",
  );
}

const html = context.ResearchOSResearchPortfolioView.render(
  { researchPortfolio: model },
  {
    encodeDataPayload: (value) => `encoded:${value}`,
    escapeHtml: (value) => String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll('"', "&quot;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;"),
    previewButton: (sourcePath, label) => `<button data-preview-path="${sourcePath}">${label}</button>`,
    translate: (key) => key,
  }
);
assert.ok(html.includes("data-research-portfolio"));
assert.ok(html.includes('class="research-attention-board"'), "registered work must render through the fixed attention surface");
const startTodayItems = context.ResearchOSResearchPortfolioView.startHorizonGroups(model.items).today;
const executableStartToday = startTodayItems.filter((item) => (
  item.managementBucket === "active"
  && item.lifecycleState === "open"
  && ["today", "carryover"].includes(item.attentionState)
  && !context.ResearchOSResearchPortfolioView.humanCheckOnly(item)
));
assert.match(
  html,
  new RegExp(`data-portfolio-start-horizon="today"[^>]*>[\\s\\S]*?<strong>${executableStartToday.length}<\\/strong><\\/button>`),
  "the real Start Today badge must count the same executable commitments projected into Work",
);
if (executableStartToday.length) {
  assert.ok(html.includes("researchAttentionTodayTitle"), "the first project group must answer what moves today");
} else if (startTodayItems.length) {
  assert.ok(html.includes("researchAttentionDecisionTitle"), "triage-only attention must be explained without an empty Today section");
} else {
  assert.ok(html.includes("researchAttentionNothingActionable"), "an empty Today destination must use one calm explanation instead of an empty section");
}
assert.ok(!html.includes("researchAttentionWaitingTitle"), "normal review-stage waiting must not appear on the first screen");
assert.ok(!html.includes("researchAttentionLaterTitle"), "queued and candidate projects belong to the lifecycle library");
assert.ok(html.includes("data-portfolio-open-library"), "the first screen must expose an owned navigation action to the lifecycle board");
assert.equal((html.match(/data-portfolio-start-horizon=/g) || []).length, 4, "the first screen must expose Today, Tomorrow, Future, and Parked as direct destinations");
if (executableStartToday.length > 1) {
  const visibleTodayCards = (html.match(/class="research-attention-card state-/g) || []).length;
  assert.ok(visibleTodayCards >= Math.min(3, executableStartToday.length), "Now must expose several Commitment cards without inventing one global focus");
}
const editableStartHtml = context.ResearchOSResearchPortfolioView.render(
  {
    mutationEnabled: true,
    researchPortfolio: {
      available: true,
      publicDemo: false,
      items: [{
        id: "compact-today",
        title: "Readable compact card",
        responsibility: "lead",
        state: "mainline",
        lifecycleState: "open",
        lifecyclePhase: "writing",
        attentionState: "today",
        attentionDate: "2026-08-07",
        managementBucket: "active",
        nextStep: "Keep this next step readable across the full card width.",
      }],
    },
  },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(editableStartHtml.includes('class="research-attention-adjust"'), "compact Start cards must fold secondary scheduling choices behind one plain-language control");
assert.ok(editableStartHtml.includes("researchAttentionAdjustSchedule"), "the compact scheduling disclosure must explain that it adjusts timing");
assert.equal((editableStartHtml.match(/data-start-primary-commitment/g) || []).length, 0, "Now must not invent a page-level primary Commitment");
assert.equal((editableStartHtml.match(/data-portfolio-open-today/g) || []).length, 1, "each visible Commitment must expose one bounded next action");
assert.ok(editableStartHtml.includes('data-start-action-state="prepare_step"'), "an unbound commitment must prepare its exact bounded step");
assert.ok(editableStartHtml.includes("researchAttentionPrepareStep"), "the default Now action must name the bounded preparation consequence");
assert.ok(editableStartHtml.includes("researchAttentionPrepareStepHint"), "the primary action must disclose that it does not execute immediately");
assert.ok(editableStartHtml.includes('aria-describedby="research-attention-action-hint-compact-today"'), "the primary action must expose its effect hint to assistive technology");
assert.equal((editableStartHtml.match(/data-start-why-now/g) || []).length, 1, "the primary commitment must explain why it needs attention now");
assert.ok(editableStartHtml.includes("researchAttentionWhyNow"), "the reason must use an explicit human-facing label");
assert.ok(editableStartHtml.includes("researchAttentionNextSafeAction"), "the commitment must distinguish its next safe action from its reason");
assert.equal((editableStartHtml.match(/data-attention-card-details/g) || []).length, 1, "each Today item must keep its summary visible while owning an independent details disclosure");
assert.match(editableStartHtml, /data-attention-card-details open/, "the first Today item must be expanded by default");
const boundSession = context.ResearchOSWorkSessionState.createSession({
  intent: "Handle the compact task",
  portfolioBinding: { itemId: "compact-today" },
});
const activeTaskPortfolioHtml = context.ResearchOSResearchPortfolioView.render({
  currentWorkSession: boundSession,
  mutationEnabled: true,
  researchPortfolio: {
    available: true,
    publicDemo: false,
    items: [{
      id: "other-today",
      title: "A second possible task",
      responsibility: "lead",
      state: "mainline",
      lifecycleState: "open",
      lifecyclePhase: "writing",
      attentionState: "today",
      managementBucket: "active",
      nextStep: "Prepare another task",
    }],
  },
}, { escapeHtml: String, previewButton: () => "", translate: (key) => key });
assert.equal((activeTaskPortfolioHtml.match(/data-start-primary-action/g) || []).length, 0, "an active Work Session must own Now's sole page-level primary action even in a worst-case competing-project fixture");
assert.ok(activeTaskPortfolioHtml.includes("research-attention-schedule"), "competing projects must remain recoverable behind secondary scheduling disclosure");
assert.ok(activeTaskPortfolioHtml.includes('data-start-action-state="switch_research"'), "a competing commitment must not silently replace the active Work Session");
assert.ok(activeTaskPortfolioHtml.includes('data-portfolio-switch-confirm="other-today"'), "switching research must expose an explicit consequence confirmation");
assert.equal(context.ResearchOSResearchPortfolioView.startActionPresentation({ id: "compact-today" }, boundSession).labelKey, "researchAttentionPrepareStep");
const continuedSession = context.ResearchOSWorkSessionState.appendTurn(boundSession, {
  answer: "Prior bounded result",
  question: "Initial pass",
});
assert.equal(context.ResearchOSResearchPortfolioView.startActionPresentation({ id: "compact-today" }, continuedSession).labelKey, "researchAttentionCurrentTask");
const runningSession = context.ResearchOSWorkSessionState.updateSession(boundSession, {
  clientRequestId: "request-running",
  latestRunId: "run-running",
  runLifecycle: "running",
  runObservation: "fresh",
  status: "running",
});
assert.equal(context.ResearchOSResearchPortfolioView.startActionPresentation({ id: "compact-today" }, runningSession).labelKey, "researchAttentionViewRun");
const uncertainSession = context.ResearchOSWorkSessionState.updateSession(runningSession, { runObservation: "lease_expired" });
assert.equal(context.ResearchOSResearchPortfolioView.startActionPresentation({ id: "compact-today" }, uncertainSession).labelKey, "researchAttentionVerifyRun");
const resultSession = context.ResearchOSWorkSessionState.updateSession(boundSession, {
  draftResult: { answer: "Done", response_mode: "answer", status: "completed" },
  status: "ready",
});
assert.equal(context.ResearchOSResearchPortfolioView.startActionPresentation({ id: "compact-today" }, resultSession).labelKey, "researchAttentionReviewResult");
const endedSession = context.ResearchOSWorkSessionState.updateSession(boundSession, { status: "completed" });
assert.equal(context.ResearchOSResearchPortfolioView.startActionPresentation({ id: "compact-today" }, endedSession).labelKey, "researchAttentionPrepareStep");
assert.ok(!html.includes("<em>researchAttentionToday</em>"), "Today cards must not repeat a redundant Today chip inside every card");
assert.ok(
  !html.includes("researchAttentionUpcomingTitle"),
  "future work must appear only after its explicit first-screen destination is selected",
);
const futureStartHtml = context.ResearchOSResearchPortfolioView.render(
  { horizon: "future", researchPortfolio: model },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(futureStartHtml.includes('data-lifecycle-horizon-panel="future"'), "Future must switch in place on the first screen");
if (context.ResearchOSResearchPortfolioView.startHorizonGroups(model.items).future.length > 2) {
  assert.ok(futureStartHtml.includes('class="research-lifecycle-horizon-more"'), "long first-screen destinations must fold after two projects");
}
assert.ok(!futureStartHtml.includes("P0-closeout ·"), "technical priority suffixes must not increase first-screen cognitive load");
const priorityCardHtml = context.ResearchOSResearchPortfolioView.renderLifecycleCard(
  { ...model.items[0], priority: "P0-closeout" },
  {},
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(priorityCardHtml.includes("· P0<"), "an active Library card must retain its decision level without exposing implementation suffixes");
assert.ok(priorityCardHtml.includes('data-priority-code="P0-closeout"'), "the complete priority code must remain machine-readable without becoming UI jargon");
assert.ok(priorityCardHtml.includes('aria-labelledby="research-lifecycle-title-'), "Library cards must expose their project title as the accessible card name");
assert.ok(!priorityCardHtml.includes('title="P0-closeout"'), "technical priority suffixes must stay out of assistive and hover labels");
if (model.items[0].currentStage) {
  assert.ok(priorityCardHtml.includes('class="research-lifecycle-context"'), "long project context must stay behind progressive disclosure");
  assert.ok(priorityCardHtml.includes("researchLifecycleContext"), "the context disclosure must state what it reveals");
}
assert.ok([
  "researchLifecycleWaitingForEvent",
  "researchLifecycleNotDated",
  "researchLifecycleAttentionDate",
  "researchLifecycleReviewDate",
  "researchLifecycleDeadlineDate",
  "researchAttentionCompleted",
].some((key) => priorityCardHtml.includes(key)), "lifecycle cards must distinguish schedules, review dates, deadlines, event triggers, undated work, and completion");
const hasDecision = context.ResearchOSResearchPortfolioView.startHorizonGroups(model.items).today.some((item) => !(
  item.managementBucket === "active"
  && item.lifecycleState === "open"
  && ["today", "carryover"].includes(item.attentionState)
  && !context.ResearchOSResearchPortfolioView.humanCheckOnly(item)
));
assert.equal(html.includes("researchAttentionDecisionTitle"), hasDecision, "the Decision section must appear only when a judgment is actually pending");
if (hasDecision) {
  assert.ok(html.includes('class="research-attention-section is-decision" data-attention-decision-queue open'), "the pending-decision queue must be reachable without a preliminary disclosure click");
}
const syntheticDecisionHtml = context.ResearchOSResearchPortfolioView.render(
  {
    researchPortfolio: {
      ...model,
      items: model.items.slice(0, 3).map((item, index) => ({
        ...item,
        id: `decision-${index}`,
        state: "mainline",
        lifecycleState: "open",
        attentionState: "unscheduled",
        actionable: true,
      })),
    },
  },
  {
    encodeDataPayload: (value) => `encoded:${value}`,
    escapeHtml: String,
    previewButton: () => "",
    translate: (key) => key,
  },
);
assert.ok(syntheticDecisionHtml.includes('class="research-attention-decision-more"'), "only the first pending judgment should remain open by default");
assert.ok(syntheticDecisionHtml.includes("data-attention-decision-current"), "the queue must expose one current judgment while retaining the remaining queue");
const mixedTriageItems = [
  ...Array.from({ length: 3 }, (_, index) => ({
    ...model.items[0], id: `rapid-today-${index}`, title: `Rapid Today ${index}`, state: "mainline", lifecycleState: "open", lifecyclePhase: "writing", attentionState: "today", managementBucket: "active", actionable: true,
  })),
  ...Array.from({ length: 5 }, (_, index) => ({
    ...model.items[0], id: `rapid-decision-${index}`, title: `Rapid Decision ${index}`, state: "mainline", lifecycleState: "open", lifecyclePhase: "writing", attentionState: "unscheduled", managementBucket: "active", actionable: true,
  })),
  { ...model.items[0], id: "rapid-later", title: "Rapid Later", state: "mainline", lifecycleState: "open", lifecyclePhase: "writing", attentionState: "upcoming", attentionDate: "2026-09-01", managementBucket: "active", actionable: true },
  { ...model.items[0], id: "rapid-waiting", title: "Rapid Waiting", state: "waiting", lifecycleState: "waiting", lifecyclePhase: "under_review", attentionState: "review_due", reviewDate: "2026-08-12", managementBucket: "waiting", managementZone: "inactive", actionable: false },
  { ...model.items[0], id: "rapid-paused", title: "Rapid Paused", state: "paused", lifecycleState: "paused", lifecyclePhase: "paused", attentionState: "review_due", reviewDate: "2026-08-12", managementBucket: "paused", managementZone: "inactive", actionable: false },
  { ...model.items[0], id: "rapid-done", title: "Rapid Done", state: "closed", lifecycleState: "completed", lifecyclePhase: "completed", attentionState: "completed", managementBucket: "closed", managementZone: "closed", actionable: false },
];
const mixedTriageModel = { available: true, items: mixedTriageItems };
const mixedTriageNowHtml = context.ResearchOSResearchPortfolioView.render(
  { researchPortfolio: mixedTriageModel, mutationEnabled: true },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.equal((mixedTriageNowHtml.match(/data-start-primary-action/g) || []).length, 0, "rapid triage must not manufacture one system-wide primary commitment");
assert.equal((mixedTriageNowHtml.match(/data-attention-card-details/g) || []).length, 3, "all Today summaries must remain directly visible");
assert.equal((mixedTriageNowHtml.match(/data-attention-card-details open/g) || []).length, 1, "Today must emphasize exactly one item by default without preventing independent expansion of the others");
assert.ok(mixedTriageNowHtml.includes('class="research-attention-order" role="group"'), "Today ordering controls must expose group semantics");
assert.match(mixedTriageNowHtml, /data-attention-reorder="up"[^>]*aria-label="[^"]*Rapid Today 0/, "Today ordering controls must name the affected item");
for (const id of ["rapid-today-0", "rapid-today-1", "rapid-today-2", "rapid-decision-0", "rapid-decision-1", "rapid-decision-2", "rapid-decision-3", "rapid-decision-4", "rapid-waiting", "rapid-paused"]) {
  assert.ok(mixedTriageNowHtml.includes(`data-attention-card="${id}"`), `${id} must remain reachable in the open Today or pending-decision surface`);
}
assert.equal((mixedTriageNowHtml.match(/data-attention-decision-current/g) || []).length, 1, "rapid triage must expose exactly one current pending judgment");
assert.ok(mixedTriageNowHtml.includes('class="research-attention-decision-more"'), "remaining pending judgments must stay continuously reachable in one queue");
for (const actionMarker of ['data-attention-action="schedule"', 'data-attention-offset="1"', "data-attention-date-input", 'data-attention-custom="paused"', "data-portfolio-complete-project"]) {
  assert.ok(mixedTriageNowHtml.includes(actionMarker), `rapid triage must retain the existing reversible or owner-routed disposition: ${actionMarker}`);
}
const mixedLaterHtml = context.ResearchOSResearchPortfolioView.render(
  { horizon: "future", researchPortfolio: mixedTriageModel, mutationEnabled: true },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(mixedLaterHtml.includes('data-lifecycle-card="rapid-later"'), "a Later disposition must remain reachable from the existing Future horizon");
const mixedDoneHtml = context.ResearchOSResearchPortfolioView.renderLibrary(
  { zone: "closed", researchPortfolio: mixedTriageModel, mutationEnabled: true },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.equal(mixedDoneHtml, "", "Library must not recreate the retired Closed project-management surface");
assert.ok(mixedTriageModel.items.some((item) => item.id === "rapid-done" && item.state === "closed"), "terminal project truth must remain in the model even when it is not a Library status card");
assert.ok(!mixedDoneHtml.includes('data-attention-action='), "terminal dispositions must not regain attention-scheduling controls");
const alignedTodayCountHtml = context.ResearchOSResearchPortfolioView.render(
  {
    researchPortfolio: {
      available: true,
      items: [
        {
          id: "scheduled-today",
          title: "Scheduled today",
          state: "mainline",
          lifecycleState: "open",
          lifecyclePhase: "writing",
          attentionState: "today",
          managementBucket: "active",
          actionable: true,
        },
        {
          id: "needs-triage",
          title: "Needs triage",
          state: "mainline",
          lifecycleState: "open",
          lifecyclePhase: "writing",
          attentionState: "unscheduled",
          managementBucket: "active",
          actionable: true,
        },
      ],
    },
  },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.match(
  alignedTodayCountHtml,
  /data-portfolio-start-horizon="today"[^>]*>[\s\S]*?<strong>1<\/strong><\/button>/,
  "the Start Today badge must count only commitments that also appear in Work; unscheduled triage has its own folded count",
);
assert.ok(alignedTodayCountHtml.includes("researchAttentionDecisionTitle"), "unscheduled active work must remain visible as scheduling or review, not disappear");
const triageOnlyHtml = context.ResearchOSResearchPortfolioView.render(
  {
    researchPortfolio: {
      available: true,
      items: [{
        id: "triage-only",
        title: "Triage only",
        state: "mainline",
        lifecycleState: "open",
        lifecyclePhase: "writing",
        attentionState: "unscheduled",
        managementBucket: "active",
        actionable: true,
      }],
    },
  },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(!triageOnlyHtml.includes('class="research-attention-section is-today"'), "a zero-count Today destination must not render a second empty section above triage");
assert.ok(triageOnlyHtml.includes("researchAttentionDecisionTitle"), "a triage-only Start state must still explain what needs scheduling or review");
const quickActionCardHtml = context.ResearchOSResearchPortfolioView.renderCard(
  {
    ...model.items[0],
    attentionState: "upcoming",
    attentionDate: "2026-08-12",
    lifecycleState: "open",
    managementBucket: "active",
    managementZone: "active",
  },
  { mutationEnabled: true },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(quickActionCardHtml.includes("researchAttentionToday"));
assert.ok(quickActionCardHtml.includes("researchAttentionTomorrow"));
assert.ok(quickActionCardHtml.includes('aria-labelledby="research-attention-title-'), "Start cards must expose their project title as the accessible card name");
assert.ok(quickActionCardHtml.includes('class="research-attention-quick-choice is-date"'));
assert.ok(quickActionCardHtml.includes('class="research-attention-quick-choice is-not-now"'));
assert.ok(!quickActionCardHtml.includes("researchAttentionThreeDays"), "the quick row must not grow into a preset wall");
assert.ok(!quickActionCardHtml.includes("researchAttentionWeek"), "the quick row must keep one custom-date path instead of competing presets");
const reviewDecisionCardHtml = context.ResearchOSResearchPortfolioView.renderCard(
  {
    ...model.items[0],
    id: "waiting-review-decision",
    state: "waiting",
    lifecycleState: "waiting",
    managementBucket: "waiting",
    managementZone: "inactive",
    attentionState: "review_due",
    reviewDate: "2026-08-11",
  },
  { mutationEnabled: true },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(reviewDecisionCardHtml.includes('data-portfolio-open-library="waiting-review-decision"'), "a due inactive project may explicitly open related materials without moving status judgment out of Now");
assert.ok(reviewDecisionCardHtml.includes("researchAttentionSetReview"), "a due inactive project may set one next review date");
assert.ok(!reviewDecisionCardHtml.includes('data-attention-action="schedule"'), "a waiting or frozen project must not clear its review trigger through active scheduling");
assert.ok(!reviewDecisionCardHtml.includes("researchAttentionChooseDateQuick"), "a non-active project must not expose the active scheduling grammar");
const syntheticCompletedHtml = context.ResearchOSResearchPortfolioView.render(
  {
    researchPortfolio: {
      ...model,
      items: [{ ...model.items[0], id: "completed-demo", state: "closed", lifecycleState: "completed", attentionState: "completed" }],
      actionItems: [],
    },
  },
  {
    encodeDataPayload: (value) => `encoded:${value}`,
    escapeHtml: String,
    previewButton: () => "",
    translate: (key) => key,
  },
);
assert.ok(!syntheticCompletedHtml.includes('data-portfolio-start="completed-demo"'), "completed work must not offer a misleading start action");
assert.ok(!syntheticCompletedHtml.includes('data-attention-action='), "completed work must not offer scheduling actions");
const inconsistentClosedItem = {
  ...model.items[0],
  id: "closed-state-only",
  state: "closed",
  lifecycleState: "open",
  lifecyclePhase: "under_review",
  attentionState: "unscheduled",
  managementBucket: "closed",
  managementZone: "closed",
};
const inconsistentClosedLibraryHtml = context.ResearchOSResearchPortfolioView.renderLibrary(
  { zone: "closed", researchPortfolio: { ...model, items: [inconsistentClosedItem] }, viewMode: "cards" },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.equal(inconsistentClosedLibraryHtml, "", "Library must not expose the retired Closed management area");
assert.equal(inconsistentClosedItem.state, "closed", "the canonical closed state remains available outside the Library projection");
assert.ok(!inconsistentClosedLibraryHtml.includes('data-attention-action='), "closed state must never expose a Move to Today action");
if (privateAuthority) {
  const completedItems = model.items.filter((item) => item.lifecycleState === "completed");
  assert.ok(completedItems.length > 0, "the private portfolio has completed work to check");
  for (const item of completedItems) assert.equal(item.state, "closed", `${item.id} is completed but not closed`);
}
const firstScreenGroups = context.ResearchOSResearchPortfolioView.startHorizonGroups(model.items);
assert.equal(
  (html.match(/data-attention-card=/g) || []).length,
  firstScreenGroups.today.length,
  "the first screen must render only work needing action or judgment now",
);
const backgroundMainline = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "private_authority",
  items: [{
    id: "background-mainline",
    title: "Submitted Lead Paper",
    responsibility: "lead",
    state: "mainline",
    lifecycle_phase: "under_review",
    lifecycle_state: "open",
    attention_state: "today",
    attention_date: "2099-01-01",
    last_verified: "2026-08-07",
  }],
}, (key) => key);
assert.equal(backgroundMainline.actionItems.length, 0, "an untriggered background review is not actionable merely because an old attention date remains");
assert.equal(
  context.ResearchOSResearchPortfolioView.startHorizonGroups(backgroundMainline.items).frozen.length,
  0,
  "an untriggered background review must stay off Start even when an old attention date still says Today",
);
assert.equal(
  context.ResearchOSResearchPortfolioView.horizonGroups(backgroundMainline.items).frozen.length,
  1,
  "an untriggered background review must stay outside Start until an external event arrives",
);
const quietCandidate = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "private_authority",
  items: [{
    id: "quiet-candidate",
    title: "Idea that has not passed the gate",
    responsibility: "lead",
    state: "conditional",
    lifecycle_phase: "scoping",
    lifecycle_state: "open",
    attention_state: "upcoming",
    attention_date: "2099-01-01",
    last_verified: "2026-08-07",
  }],
}, (key) => key);
assert.equal(
  context.ResearchOSResearchPortfolioView.startHorizonGroups(quietCandidate.items).future.length,
  0,
  "a candidate must stay in Library until a review is due instead of occupying Start merely because it has a future date",
);
const dueCandidate = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "private_authority",
  items: [{
    id: "due-candidate",
    title: "Candidate due for a decision",
    responsibility: "lead",
    state: "conditional",
    lifecycle_phase: "scoping",
    lifecycle_state: "open",
    attention_state: "review_due",
    review_date: "2026-08-11",
    last_verified: "2026-08-07",
  }],
}, (key) => key);
assert.equal(
  context.ResearchOSResearchPortfolioView.startHorizonGroups(dueCandidate.items).today.length,
  1,
  "a candidate may resurface on Start only when its explicit review is due",
);
const triggeredReview = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "private_authority",
  items: [{
    id: "triggered-review",
    title: "Reviews Arrived",
    responsibility: "lead",
    state: "mainline",
    lifecycle_phase: "under_review",
    lifecycle_state: "open",
    attention_state: "needs_next_step",
  }],
}, (key) => key);
assert.equal(triggeredReview.actionItems.length, 1, "an explicit review event must resurface the project on Start");
const dueBackgroundReview = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "private_authority",
  items: [{
    id: "due-background-review",
    title: "Scheduled review check is due",
    responsibility: "lead",
    state: "mainline",
    lifecycle_phase: "under_review",
    lifecycle_state: "open",
    attention_state: "review_due",
    review_date: "2026-08-11",
  }],
}, (key) => key);
assert.equal(dueBackgroundReview.items[0].eventTriggered, true, "a due review date must become an explicit resurfacing trigger");
assert.equal(
  context.ResearchOSResearchPortfolioView.startHorizonGroups(dueBackgroundReview.items).today.length,
  1,
  "a background review whose review date is due must return to Start as a judgment item",
);
const manuallyParked = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "private_authority",
  items: [{
    id: "manually-parked",
    title: "Manually parked active commitment",
    responsibility: "lead",
    state: "mainline",
    lifecycle_phase: "production",
    lifecycle_state: "open",
    attention_state: "paused",
    attention_source: "attention_schedule",
    last_attention_action: "paused",
  }],
}, (key) => key);
assert.equal(context.ResearchOSResearchPortfolioView.parkedCommitment(manuallyParked.items[0]), true);
assert.equal(
  context.ResearchOSResearchPortfolioView.startHorizonGroups(manuallyParked.items).frozen.length,
  1,
  "an active commitment explicitly parked by the user must remain reachable under Parked",
);
const staleButParked = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "private_authority",
  items: [{
    id: "stale-but-parked",
    title: "Stale but deliberately parked",
    responsibility: "lead",
    state: "mainline",
    lifecycle_phase: "production",
    lifecycle_state: "open",
    attention_state: "paused",
    attention_source: "attention_schedule",
    last_attention_action: "paused",
    needs_attention: true,
    last_verified: "2026-01-01",
  }],
}, (key) => key);
assert.equal(staleButParked.items[0].eventTriggered, false, "generic stale metadata must not pretend that a real resurfacing event arrived");
assert.equal(
  context.ResearchOSResearchPortfolioView.startHorizonGroups(staleButParked.items).frozen.length,
  1,
  "a deliberate Parked choice must outrank generic stale metadata",
);
const parkedReviewDue = {
  ...manuallyParked.items[0],
  attentionState: "review_due",
  eventTriggered: true,
};
assert.equal(context.ResearchOSResearchPortfolioView.parkedCommitment(parkedReviewDue), false);
assert.equal(
  context.ResearchOSResearchPortfolioView.horizonForItem(parkedReviewDue, "2026-08-11"),
  "today",
  "an explicitly due review must resurface even when the previous action was Parked",
);
assert.match(
  context.ResearchOSResearchPortfolioView.renderLifecycleCard(
    manuallyParked.items[0],
    { mutationEnabled: true },
    { escapeHtml: String, previewButton: () => "", translate: (key) => key },
  ),
  /data-attention-action="schedule"/,
  "a manually parked commitment must offer a route back to Today",
);
const schedulableCardHtml = context.ResearchOSResearchPortfolioView.renderCard(
  {
    ...manuallyParked.items[0],
    attentionState: "upcoming",
    attentionDate: "2026-08-20",
    lastAttentionAction: "schedule",
  },
  { compact: true, mutationEnabled: true },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(schedulableCardHtml.includes("researchAttentionDeferStep"));
assert.ok(!schedulableCardHtml.includes('data-attention-custom="waiting"'), "Start must park only the current step instead of pretending to change project lifecycle");
assert.equal(
  context.ResearchOSResearchPortfolioModel.managementBucketForItem(manuallyParked.items[0]),
  "active",
  "parking a next step must not move an active project into the inactive lifecycle zone",
);
const lifecycleHtml = context.ResearchOSResearchPortfolioView.render(
  { calendarMonth: context.ResearchOSResearchPortfolioView.currentMonthKey(), researchPortfolio: model },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(lifecycleHtml.includes("data-research-portfolio"));
assert.ok(lifecycleHtml.includes("data-now-active-projects"), "Now must own the full active-project projection");
assert.equal((lifecycleHtml.match(/data-lifecycle-card=/g) || []).length, model.items.length, "Now must keep every registered project discoverable, including the folded closed archive");
const largeActiveHtml = context.ResearchOSResearchPortfolioView.render({
  mutationEnabled: true,
  researchPortfolio: { ...model, items: Array.from({ length: 8 }, (_, index) => ({ ...model.items[0], id: `active-${index}`, title: `Active ${index}` })) },
}, { escapeHtml: String, previewButton: () => "", translate: (key) => key });
assert.ok(largeActiveHtml.includes("data-now-active-projects-more"), "the full active-project inventory must use progressive disclosure instead of pushing the exact-item drawer far below the fold");
assert.equal((largeActiveHtml.match(/data-lifecycle-card=/g) || []).length, 8, "folding the long active-project inventory must preserve every project in the DOM");
for (const level of ["I0", "I1", "I2", "I3"]) {
  assert.ok(lifecycleHtml.includes(`data-portfolio-maturity-target="${level}"`), `each project card must offer ${level} as an explicit candidate choice`);
}
assert.ok(lifecycleHtml.includes("researchMaturityI3Criteria"), "maturity choices must expose their classification criteria for hover and keyboard focus");
assert.ok(lifecycleHtml.includes("researchMaturityChooseHint"), "the selector must explain that a choice remains candidate-only before confirmation");
assert.ok(lifecycleHtml.includes("researchMaturityUnregisteredBadge"), "a missing project maturity must use a plain-language label instead of exposing the internal I? placeholder");
const updateCopy = (key) => ({
  researchLifecycleUpdated: "更新 {date}",
  researchLifecycleUpdatedUnknown: "更新日期未知",
}[key] || key);
const datedLifecycleCardHtml = context.ResearchOSResearchPortfolioView.renderLifecycleCard(
  model.items[0],
  {},
  { escapeHtml: String, previewButton: () => "", translate: updateCopy },
);
assert.ok(datedLifecycleCardHtml.includes(`data-project-updated-date="${model.items[0].lastVerified}"`), "every Library project card must expose its authoritative per-item update date");
assert.ok(datedLifecycleCardHtml.includes(`更新 ${model.items[0].lastVerified}`), "the update date must be readable without opening card details");
const compactLifecycleCardHtml = context.ResearchOSResearchPortfolioView.renderLifecycleCard(
  model.items[0],
  { compact: true },
  { escapeHtml: String, previewButton: () => "", translate: updateCopy },
);
assert.ok(!compactLifecycleCardHtml.includes("data-project-updated-date"), "the first-screen compact projection must not duplicate Library freshness metadata");
const unknownUpdateCardHtml = context.ResearchOSResearchPortfolioView.renderLifecycleCard(
  { ...model.items[0], lastVerified: "" },
  {},
  { escapeHtml: String, previewButton: () => "", translate: updateCopy },
);
assert.ok(unknownUpdateCardHtml.includes("更新日期未知"), "a missing update date must stay explicit instead of being guessed");
const horizons = context.ResearchOSResearchPortfolioView.horizonGroups(model.items);
assert.equal(Object.values(horizons).flat().length, model.items.length, "the four destinations must partition every registered project exactly once");
const managementZones = context.ResearchOSResearchPortfolioView.managementZoneGroups(model.items);
assert.equal(Object.values(managementZones).flat().length, model.items.length, "the four management areas must partition every registered project exactly once");
const datedCalendarProjectIds = new Set(context.ResearchOSResearchPortfolioView.calendarEvents(model.items).map((event) => event.item.id));
const undatedCalendarProjectIds = new Set(context.ResearchOSResearchPortfolioView.calendarUndatedItems(model.items).map((item) => item.id));
const openProjectIds = new Set(model.items.filter((item) => !context.ResearchOSResearchPortfolioView.terminalProject(item)).map((item) => item.id));
assert.deepEqual(
  [...datedCalendarProjectIds].filter((id) => undatedCalendarProjectIds.has(id)),
  [],
  "a project cannot be both dated and undated in Calendar",
);
assert.deepEqual(
  [...new Set([...datedCalendarProjectIds, ...undatedCalendarProjectIds])].sort(),
  [...openProjectIds].sort(),
  "dated events plus the undated lane must preserve every open project from Project Overview",
);
const selectedCalendarMonth = context.ResearchOSResearchPortfolioView.currentMonthKey();
const selectedMonthProjectIds = new Set(context.ResearchOSResearchPortfolioView.calendarEvents(model.items)
  .filter((event) => event.date.startsWith(`${selectedCalendarMonth}-`))
  .map((event) => event.item.id));
const otherMonthProjectIds = new Set(context.ResearchOSResearchPortfolioView.calendarOtherMonthEvents(model.items, selectedCalendarMonth)
  .map((event) => event.item.id));
assert.deepEqual(
  [...selectedMonthProjectIds].filter((id) => otherMonthProjectIds.has(id) || undatedCalendarProjectIds.has(id)),
  [],
  "the selected-month, other-month, and undated Calendar lanes cannot overlap",
);
assert.deepEqual(
  [...otherMonthProjectIds].filter((id) => undatedCalendarProjectIds.has(id)),
  [],
  "a project scheduled in another month cannot also be labeled undated",
);
assert.deepEqual(
  [...new Set([...selectedMonthProjectIds, ...otherMonthProjectIds, ...undatedCalendarProjectIds])].sort(),
  [...openProjectIds].sort(),
  "the current Calendar month must account for every open Project Overview item",
);
for (const item of model.items.filter((candidate) => candidate.reviewDate && ["waiting", "paused"].includes(candidate.lifecycleState))) {
  assert.ok(
    context.ResearchOSResearchPortfolioView.calendarEvents([item]).some((event) => event.type === "review" && event.date === item.reviewDate),
    `${item.id} must keep its explicit review date visible while inactive`,
  );
}
assert.ok(lifecycleHtml.includes('data-calendar-view="month" aria-pressed="true"'), "Now must default to the month schedule while preserving the week switch");
assert.ok(lifecycleHtml.includes('data-now-active-projects'), "Now must expose active and waiting project context directly");
if (model.publicDemo) {
  assert.ok(lifecycleHtml.includes("researchAttentionDemoBoundary"), "the public Now projection must explain its in-memory attention boundary");
}
const alreadyTodayActive = model.items.find((item) => item.managementBucket === "active" && ["today", "carryover"].includes(item.attentionState));
if (alreadyTodayActive) {
  const alreadyTodayCardHtml = context.ResearchOSResearchPortfolioView.renderLifecycleCard(
    alreadyTodayActive,
    {},
    { escapeHtml: String, previewButton: () => "", translate: (key) => key },
  );
  assert.ok(!alreadyTodayCardHtml.includes("researchLifecycleMoveToday"), "a project already in Today must not offer a redundant Move to today action");
}
assert.ok(lifecycleHtml.includes('data-calendar-view="week"'), "Now must keep week and month as explicit schedule views");
const populatedZone = ["active", "pending", "inactive", "closed"].find((zone) => managementZones[zone].length) || "active";
const populatedLibraryHtml = context.ResearchOSResearchPortfolioView.render(
  { researchPortfolio: model },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(populatedLibraryHtml.includes("research-lifecycle-level"), "project responsibility and decision-relevant priority must remain visible without replacing lifecycle phase");
assert.ok(populatedLibraryHtml.includes("data-now-active-projects"));
assert.ok(!populatedLibraryHtml.includes("data-portfolio-zone="), "Now must show lifecycle context without reviving Library management zones");
const inactiveLibraryHtml = context.ResearchOSResearchPortfolioView.render(
  { researchPortfolio: { ...model, items: managementZones.inactive } },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.equal((inactiveLibraryHtml.match(/data-lifecycle-card=/g) || []).length, managementZones.inactive.length, "Not advancing must collect waiting and frozen projects without erasing lifecycle truth");
if (managementZones.inactive.some((item) => item.backgroundPhase)) {
  assert.ok(inactiveLibraryHtml.includes("researchLifecycleWaitingForEvent"), "background review cards must state that they are waiting for an external event");
}
for (const item of managementZones.inactive.filter((candidate) => !context.ResearchOSResearchPortfolioView.parkedCommitment(candidate))) {
  const inactiveCardHtml = context.ResearchOSResearchPortfolioView.renderLifecycleCard(
    item,
    { mutationEnabled: true },
    { escapeHtml: String, previewButton: () => "", translate: (key) => key },
  );
  assert.ok(!inactiveCardHtml.includes('data-attention-action="schedule"'), "ordinary waiting and paused projects must not masquerade as active work through Move to Today");
}
const closedLibraryHtml = context.ResearchOSResearchPortfolioView.render(
  { researchPortfolio: { ...model, items: managementZones.closed } },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.equal((closedLibraryHtml.match(/data-lifecycle-card=/g) || []).length, managementZones.closed.length, "closed projects must remain recoverable in Now's folded archive");
const publicReadOnlyHtml = context.ResearchOSResearchPortfolioView.render(
  { researchPortfolio: { ...model, publicDemo: true } },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(publicReadOnlyHtml.includes("researchAttentionDemoBoundary"), "the public example needs one board-level read-only explanation");
assert.ok(!publicReadOnlyHtml.includes('disabled>researchAttentionTomorrow'), "the public example must hide dead scheduling controls");
const calendarLibraryHtml = context.ResearchOSResearchPortfolioView.render(
  { calendarMonth: "2026-08", mutationReceipt: { message: "moved", viewToday: true, undo: { token: "undo" } }, researchPortfolio: model, calendarView: "month" },
  { escapeHtml: String, previewButton: () => "", translate: (key) => key },
);
assert.ok(calendarLibraryHtml.includes('data-calendar-view="month" aria-pressed="true"'));
assert.ok(calendarLibraryHtml.includes("data-now-calendar"), "Now must render the owned monthly schedule projection");
assert.ok(calendarLibraryHtml.includes("data-portfolio-undo"), "calendar moves must expose the existing reversible mutation receipt");
assert.ok(calendarLibraryHtml.includes("data-portfolio-receipt-today"), "a moved item must offer a direct route to the Today destination");
assert.equal((calendarLibraryHtml.match(/data-lifecycle-card=/g) || []).length, model.items.length, "the calendar must coexist with the complete project context on Now");
// Layout is checked by screenshots; here every structural class the views render must at least be styled.
const styledClasses = stylesheetClasses();
const renderedPortfolioClasses = new Set([
  html, lifecycleHtml, largeActiveHtml, calendarLibraryHtml, calendarFixtureHtml, movableCalendarHtml, publicPreviewCalendarHtml,
  editableStartHtml, publicReadOnlyHtml, compactLifecycleCardHtml,
].flatMap((fragment) => [...renderedClasses(fragment)]));
for (const name of [
  "research-attention-board",
  "research-attention-grid",
  "research-attention-card",
  "research-attention-next",
  "research-attention-adjust",
  "research-lifecycle-card",
  "research-lifecycle-status-row",
  "research-maturity-options",
  "research-calendar-grid-wrap",
  "research-calendar-agenda",
  "research-calendar-week-grid",
  "research-calendar-day-more",
]) {
  assert.ok(renderedPortfolioClasses.has(name), `the portfolio views must render ${name}`);
  assert.ok(styledClasses.has(name), `${name} must have at least one rule under dashboard/styles`);
}
assert.ok(!html.includes('data-portfolio-start="'), "the Judgment surface must classify work without starting execution");
if (firstScreenGroups.today.length && !model.publicDemo) {
  assert.ok(html.includes("data-attention-action"), "date and step actions must be direct attention-kernel actions");
  assert.ok(html.includes("data-portfolio-complete-project"), "project completion must remain visually distinct from step completion");
} else if (!firstScreenGroups.today.length) {
  assert.ok(html.includes("researchAttentionNothingActionable"), "an empty Start screen must explain that background projects remain in Library");
}
assert.ok(!html.includes("data-unfinished-prompt"), "portfolio actions must not auto-run a Work Session");

const nowHtml = context.ResearchOSHomeCommandCenterView.renderNowHtml(
  { workSessionHtml: '<section data-work-session>session</section>' },
  {
    escapeHtml: (value) => String(value ?? ""),
    sectionTranslate: (key) => key,
    translate: (key) => key,
  }
);
assert.ok(nowHtml.includes('data-plugin-slot-host="workbench"'));
assert.ok(!nowHtml.includes("data-work-session"), "Now must not absorb the Work Session lifecycle surface");
assert.ok(!nowHtml.includes('data-plugin-slot-host="processing"'), "Now must not host a competing Portfolio processing projection");
assert.ok(!nowHtml.includes("data-research-portfolio"), "Now core must not render portfolio fields directly");
assert.ok(!nowHtml.includes('data-open-workspace="work"'), "Now must not navigate to a third Work screen");

const humanCheckToday = model.items.find((item) => context.ResearchOSResearchPortfolioView.humanCheckOnly(item));
if (humanCheckToday) {
  assert.ok(!html.includes(`data-attention-card="${humanCheckToday.id}"`), "a routine review-stage check must stay off Start until a real external event arrives");
}

assert.equal(
  context.ResearchOSResearchPortfolioView.render({ researchPortfolio: { ...model, available: false } }),
  "",
  "public or unavailable data must not render the private portfolio"
);

const pluginData = {
  generated_at: "2026-08-13T00:00:00Z",
  home_command_center: { research_portfolio: rawPortfolio },
  runtime_mode: "private",
  plugins: {
    schema_id: "researchos-plugin-v1",
    core_api_version: "1",
    loaded: [{ id: "research_portfolio" }],
    contributions: {
      actions: [],
      candidate_types: [],
      projections: [{
        id: "research_portfolio",
        source: "home_command_center.research_portfolio",
        contribution_key: "research_portfolio:research_portfolio",
        plugin_id: "research_portfolio",
        schema_id: "researchos-projection-envelope-v1",
        version: "1",
        sensitivity: "local_only",
        freshness: "snapshot",
        export_fields: ["$"],
      }],
      ui_slots: [
        {
          id: "research_portfolio_workbench",
          contribution_key: "research_portfolio:research_portfolio_workbench",
          plugin_id: "research_portfolio",
          slot: "workbench",
          surface: "start",
          region: "primary",
          adapter: "research_portfolio_workbench",
          projection_ids: ["research_portfolio"],
          action_ids: [],
        },
        {
          id: "research_portfolio_library",
          contribution_key: "research_portfolio:research_portfolio_library",
          plugin_id: "research_portfolio",
          slot: "library",
          surface: "library",
          region: "context",
          adapter: "research_portfolio_library",
          projection_ids: ["research_portfolio"],
          action_ids: [],
        },
      ],
    },
  },
};
const pluginHost = {
  hidden: true,
  innerHTML: "",
  querySelector() { return null; },
};
const pluginReceipt = context.ResearchOSPluginRuntime.renderSlots({
  data: pluginData,
  host: pluginHost,
  slot: "workbench",
  context: {
    escapeHtml: (value) => String(value ?? ""),
    previewButton: () => "",
    text: (key) => key,
  },
});
assert.deepEqual(Array.from(pluginReceipt.rendered), ["research_portfolio_workbench"]);
assert.ok(pluginHost.innerHTML.includes("data-research-portfolio"), "enabled portfolio plugin must restore the authority drawer");
const libraryHost = { ...pluginHost, hidden: true, innerHTML: "" };
const libraryReceipt = context.ResearchOSPluginRuntime.renderSlots({
  data: pluginData,
  host: libraryHost,
  slot: "library",
  context: {
    escapeHtml: String,
    previewButton: () => "",
    text: (key) => key,
  },
});
assert.deepEqual(Array.from(libraryReceipt.rendered), []);
assert.equal(libraryHost.innerHTML, "", "portfolio lifecycle and calendar must not contribute to the Library slot");
context.ResearchOSPluginRuntime.renderSlots({ data: {}, host: pluginHost, slot: "workbench" });
assert.equal(pluginHost.innerHTML, "", "disabled portfolio plugin must leave no orphan Today content");
const processingHost = { ...pluginHost, hidden: true, innerHTML: "" };
const processingReceipt = context.ResearchOSPluginRuntime.renderSlots({
  data: pluginData,
  host: processingHost,
  slot: "processing",
  context: {
    currentWorkSession: null,
    escapeHtml: String,
    previewButton: () => "",
    text: (key) => key,
  },
});
assert.deepEqual(Array.from(processingReceipt.rendered), [], "Portfolio must contribute no processing slot after Next adopts one lifecycle owner");
assert.equal(processingHost.innerHTML, "", "an unowned legacy processing host must remain empty");

const publicDemoSlot = {
  payloads: {
    research_portfolio: {
      available: true,
      presentation_mode: "public_demo",
      items: [{ id: "demo-item", title: "Demo item", responsibility: "lead", state: "mainline", attention_state: "today" }],
    },
  },
};
const hiddenPublicDemoContext = { publicDemoVisible: () => false };
assert.equal(context.ResearchOSResearchPortfolioPlugin.renderWorkbench(publicDemoSlot, hiddenPublicDemoContext), "", "hiding the public demo must remove its Start projection");
assert.equal(typeof context.ResearchOSResearchPortfolioPlugin.renderLibrary, "undefined", "portfolio must not expose a Library project/calendar renderer");
assert.equal(typeof context.ResearchOSResearchPortfolioPlugin.renderProcessing, "undefined", "Portfolio must expose no second Next lifecycle renderer");
const publicOnboardingHtml = context.ResearchOSResearchPortfolioPlugin.renderWorkbench(publicDemoSlot, {
  escapeHtml: String,
  previewButton: () => "",
  publicDemoVisible: () => true,
  text: (key) => key,
});
assert.ok(publicOnboardingHtml.includes('class="research-portfolio-onboarding"'), "the public starter must provide one optional worked-example path");
assert.equal((publicOnboardingHtml.match(/researchPortfolioOnboardingStep/g) || []).length, 6, "the worked example must explain three steps without adding a second workflow");
assert.ok(publicOnboardingHtml.includes("researchPortfolioPublicExampleHint"), "the worked example must explain that it continues the first-library onboarding path");
const activeTaskLibraryHost = { ...pluginHost, hidden: true, innerHTML: "" };
const activeTaskLibraryReceipt = context.ResearchOSPluginRuntime.renderSlots({
  data: pluginData,
  host: activeTaskLibraryHost,
  slot: "library",
  context: {
    currentContextPack: () => ({ active: true }),
    escapeHtml: String,
    previewButton: () => "",
    publicDemoVisible: () => true,
    text: (key) => key,
  },
});
assert.deepEqual(Array.from(activeTaskLibraryReceipt.rendered), [], "an active Context Pack must not gain a portfolio-owned Library projection");
assert.equal(activeTaskLibraryHost.innerHTML, "");
const inactiveLibraryHost = { ...pluginHost, hidden: true, innerHTML: "" };
const inactiveLibraryReceipt = context.ResearchOSPluginRuntime.renderSlots({
  data: pluginData,
  host: inactiveLibraryHost,
  slot: "library",
  context: {
    currentContextPack: () => ({ active: false }),
    escapeHtml: String,
    previewButton: () => "",
    publicDemoVisible: () => true,
    text: (key) => key,
  },
});
assert.deepEqual(Array.from(inactiveLibraryReceipt.rendered), [], "Library remains source-and-relation focused when no Context Pack is active");
assert.equal(inactiveLibraryHost.innerHTML, "");

function classList() {
  const values = new Set();
  return {
    contains(value) { return values.has(value); },
    toggle(value, enabled) { enabled ? values.add(value) : values.delete(value); },
  };
}

const cardSpecs = [
  ["today", "lead", "mainline", "current"],
  ["today", "lead", "mainline", "current"],
  ["this_week", "support", "mainline", "current"],
  ["later", "support", "waiting", "stale"],
];
const cards = cardSpecs.map(([schedule, responsibility, state, freshness], index) => ({
  classList: classList(),
  dataset: {
    portfolioSchedule: schedule,
    portfolioResponsibility: responsibility,
    portfolioState: state,
    portfolioFreshness: freshness,
    portfolioSelect: `item-${index}`,
  },
  hidden: !(responsibility === "lead" && state === "mainline"),
  setAttribute(name, value) { this[name] = value; },
}));
const details = cards.map((card) => ({ dataset: { portfolioDetail: card.dataset.portfolioSelect }, hidden: true }));
const buttons = ["lead_active", "lead_all", "support_active", "support_all", "waiting", "queued", "conditional", "paused", "review", "unclassified", "all"].map((filter) => ({
  classList: classList(),
  dataset: { portfolioFilter: filter },
  setAttribute(name, value) { this[name] = value; },
}));
const status = { textContent: "2/4" };
const fakeRoot = {
  querySelector(selector) { return selector === "[data-portfolio-filter-status]" ? status : null; },
  querySelectorAll(selector) {
    if (selector === "[data-portfolio-card]") return cards;
    if (selector === "[data-portfolio-select]") return cards;
    if (selector === "[data-portfolio-detail]") return details;
    if (selector === "[data-portfolio-filter]") return buttons;
    return [];
  },
};
const visibleSupport = context.ResearchOSResearchPortfolioWorkbench.applyFilter(fakeRoot, "support_all");
assert.equal(visibleSupport, 2);
assert.deepEqual(cards.map((card) => card.hidden), [true, true, false, false]);
assert.equal(buttons[3]["aria-pressed"], "true");
assert.equal(status.textContent, "2/4");
assert.equal(details[2].hidden, false, "responsibility filter changes must reveal the corresponding action panel");

const failClosedModel = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "private_authority",
  sensitivity: "private",
  coverage: { complete: false, candidates: ["unknown"], reviewed: "2026-07-26", stale_after_days: 14 },
  items: [{
    id: "bad-role",
    title: "Bad role",
    responsibility: "reviewer",
    state: "mainline",
    last_verified: "2099-01-01",
    stale_after_days: 14,
    quality_issues: ["invalid_responsibility"],
  }],
}, (key) => key);
assert.equal(failClosedModel.answer.leadActive, 0, "invalid responsibility must never fall through to lead");
assert.equal(failClosedModel.answer.unclassified, 1);
assert.equal(failClosedModel.items[0].freshness, "unverified", "future verification dates must fail closed");
assert.equal(failClosedModel.answer.needsAttention, 1);
assert.equal(failClosedModel.answer.coverageVerified, false);

const thresholdModel = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "private_authority",
  sensitivity: "private",
  coverage: { complete: true, reviewed: "2026-07-26", stale_after_days: 14 },
  items: [{
    id: "threshold-date",
    title: "Threshold date",
    responsibility: "lead",
    state: "mainline",
    last_verified: "2026-08-09",
    stale_after_days: 3,
  }],
}, (key) => key);
assert.equal(thresholdModel.items[0].freshness, "review_due", "an item must enter review_due on the threshold day");
assert.equal(thresholdModel.answer.needsAttention, 1);

let publicRuntime = false;
const draftedSessions = [];
const runtimeActions = context.ResearchOSResearchPortfolioWorkbench.createActions({
  defaultSourceHint: () => publicRuntime
    ? "public-demo-ledger.md"
    : "private-ledger.md",
  draftWorkSession: (session) => {
    draftedSessions.push(session);
    return { ok: true, session };
  },
  text: (key) => key,
  titleSeparator: () => publicRuntime ? ": " : "：",
});
runtimeActions.preparePrompt("Private request", { title: "Private item" });
publicRuntime = true;
runtimeActions.preparePrompt("Public request", { title: "Public item" });
assert.deepEqual(
  draftedSessions.map((session) => [session.sourceHint, session.title, session.portfolioBinding?.itemId || ""]),
  [
    ["private-ledger.md", "researchPortfolioStartTaskTitle：Private item", ""],
    ["public-demo-ledger.md", "researchPortfolioStartTaskTitle: Public item", ""],
  ],
  "one shared drafting entrypoint must resolve the correct private or public agenda source without executing the task"
);

runtimeActions.preparePrompt("Bound request", {
  currentStage: "Evidence ready for review",
  id: "registered-item",
  nextStep: "Run the registered check",
  nextStepHash: "registered-step-signature",
  providerId: "research_portfolio",
  sourcePath: "registered-item.md",
  title: "Registered item",
});
assert.deepEqual(
  JSON.parse(JSON.stringify(draftedSessions.at(-1).portfolioBinding)),
  {
    completeProjectActionId: "complete_portfolio_project",
    completeStepActionId: "complete_portfolio_step",
    currentStage: "Evidence ready for review",
    currentStageCanonical: "Evidence ready for review",
    itemId: "registered-item",
    nextStep: "Run the registered check",
    nextStepCanonical: "Run the registered check",
    nextStepHash: "registered-step-signature",
    portfolioPath: "public-demo-ledger.md",
    pluginId: "research_portfolio",
    providerId: "research_portfolio",
    sourcePath: "registered-item.md",
    title: "Registered item",
  },
  "a Work Session created from an agenda item must retain stable identity, authority paths, provider, and the original next-step signature"
);
runtimeActions.preparePrompt("Switch request", { id: "switch-item", title: "Switch item" }, "now", { replaceConfirmed: true });
assert.equal(draftedSessions.at(-1).replaceConfirmed, true, "an explicit switch confirmation must be the only route that replaces an unfinished session without a second ambiguous prompt");
runtimeActions.preparePrompt("Background-shaped request", { id: "background-item", title: "Background item" }, "background");
assert.equal(draftedSessions.at(-1).portfolioBinding.itemId, "background-item", "Portfolio must draft rather than execute even if a legacy caller supplies the background mode");
runtimeActions.preparePrompt("Check selected maturity", {
  id: "maturity-item",
  title: "Maturity item",
  selectedMaturityTarget: "I3",
  cardMaturity: { action: "verify", axis: "I", confirmed: false, level: "", source: "missing", target_level: "I0" },
}, "adjust");
assert.equal(draftedSessions.at(-1).enhancement.target_level, "I3", "the user-selected maturity must replace the missing-record I0 fallback in the candidate");
assert.equal(draftedSessions.at(-1).candidate.proposed_writeback.proposed_state, "I3", "the selected maturity must remain a proposed writeback, not an applied state");
assert.equal(draftedSessions.at(-1).candidate.validation.authority_state, "proposed", "choosing a maturity must not bypass human confirmation");


// A private-authority fixture (fictional) exercises source routes, coverage evidence and fail-closed classification.
const privateEdition = /data-client-profile="private_compact_v1"/.test(dashboardIndex);
const authorityPayload = {
  available: true,
  presentation_mode: "private_authority",
  sensitivity: "private",
  coverage: {
    candidates: ["Demo student manuscript"],
    candidate_evidence_packets: [{
      affected_objects: ["source.md", "person.md"],
      automatic_writeback_allowed: false,
      candidate_id: "Demo student manuscript",
      conflict_signals: ["student_relationship_contradiction"],
      direct_statement_count: 2,
      evidence_boundary: "local_private_evidence_only",
      human_only_fields: ["authorship_or_formal_authority"],
      projectable_fields: [{ field: "responsibility", value: "support", source_paths: ["person.md"] }],
      recursive_propagation_allowed: false,
      source_refs: [
        { path: "source.md", kind: "coverage_source", excerpts: ["The demo student leads the manuscript."] },
        { path: "person.md", kind: "linked_source", excerpts: ["The researcher follows the submission."] },
      ],
      stale_signals: ["explicit_stale_or_error_marker"],
      status: "evidence_found_needs_human_disposition",
    }],
    complete: false,
    evidence_ready_count: 1,
    reviewed: "2026-08-12",
    source_unresolved_count: 0,
    sources: ["source.md"],
    status: "reviewed",
  },
  items: [
    {
      id: "today-a", title: "Today A", provider_id: "research_portfolio", responsibility: "lead", state: "mainline",
      lifecycle_state: "open", lifecycle_phase: "writing", attention_state: "today", attention_date: "2026-08-12", today_order: 1,
      next_step: "Write the result", source_available: true,
      source_path: "06_active_context/example-portfolio.md", source_path_available: true,
      source_root: "/workspace/demo", source_root_available: true, continuation_source: "/workspace/demo",
      last_verified: "2026-08-12",
    },
    {
      id: "today-b", title: "Today B", provider_id: "research_portfolio", responsibility: "support", state: "mainline",
      engagement: "ongoing", lifecycle_state: "open", lifecycle_phase: "production", attention_state: "today", attention_date: "2026-08-12", today_order: 2,
      next_step: "Check evidence", last_verified: "2026-08-12",
    },
    {
      id: "waiting-c", title: "Waiting C", provider_id: "research_portfolio", responsibility: "lead", state: "waiting",
      lifecycle_state: "waiting", lifecycle_phase: "under_review", attention_state: "waiting", review_date: "2026-08-20",
      activation_trigger: "Reviewer response", next_step: "Wait", last_verified: "2026-08-12",
    },
    {
      id: "closed-invalid", title: "Closed Invalid", provider_id: "research_portfolio", responsibility: "lead", state: "closed",
      lifecycle_phase: "made_up_phase", attention_state: "unscheduled", next_step: "Clarify closure", last_verified: "2026-08-12",
    },
    {
      id: "unclear-f", title: "Unclear F", provider_id: "research_portfolio", responsibility: "support", state: "mainline",
      engagement: "ad-hoc", lifecycle_state: "open", lifecycle_phase: "made_up_phase", attention_state: "today",
      attention_date: "2026-08-12", next_step: "Clarify status", last_verified: "2026-08-12",
      quality_issues: ["invalid_engagement", "invalid_lifecycle_phase"],
    },
  ],
};
const authorityCopy = (key) => portfolioCopy.text("en", key);
const authorityModel = context.ResearchOSResearchPortfolioModel.build(authorityPayload, authorityCopy, "en");
assert.equal(authorityModel.items[0].sourcePathAvailable, true);
assert.equal(authorityModel.items[0].sourceRootAvailable, true);
assert.equal(authorityModel.items[0].continuationSource, "/workspace/demo");
assert.equal(authorityModel.coverage.candidateEvidencePackets.length, 1);
assert.equal(authorityModel.coverage.candidateEvidencePackets[0].sourceRefs[1].path, "person.md");
assert.equal(authorityModel.coverage.candidateEvidencePackets[0].automaticWritebackAllowed, false);
const unclearAuthorityItem = authorityModel.items.find((item) => item.id === "unclear-f");
assert.equal(unclearAuthorityItem.engagement, "unclassified", "invalid support engagement must not become ongoing");
assert.equal(unclearAuthorityItem.lifecyclePhase, "unclassified", "invalid lifecycle must not become scoping");
assert.equal(unclearAuthorityItem.managementBucket, "unclassified");
assert.equal(unclearAuthorityItem.actionable, false, "unclassified status must not enter the actionable queue");
const closedInvalidItem = authorityModel.items.find((item) => item.id === "closed-invalid");
assert.equal(closedInvalidItem.lifecyclePhase, "unclassified", "closed action state must not infer professional completion");
assert.equal(closedInvalidItem.lifecycleState, "open", "missing lifecycle state must remain independent from closed action state");
assert.equal(closedInvalidItem.managementBucket, "unclassified");
assert.equal(closedInvalidItem.actionable, false);
assert.equal(context.ResearchOSResearchPortfolioModel.build({
  ...authorityPayload,
  items: [{ ...authorityPayload.items[0], id: "talk-g", lifecycle_phase: "presentation_preparation" }],
}, authorityCopy, "en").items[0].lifecyclePhase, "presentation_preparation", "registered talk preparation must remain a real lifecycle phase");

const authorityHtml = context.ResearchOSResearchPortfolioView.render({
  calendarMonth: "2026-08",
  calendarView: "month",
  mutationEnabled: true,
  researchPortfolio: authorityModel,
  sessionRegistry: [
    { item_id: "today-a", session_id: "session-a", run_id: "run-a", work_state: "active" },
    { item_id: "today-a", session_id: "session-b", run_id: "run-b", work_state: "needs_review" },
  ],
}, { escapeHtml: (value) => String(value ?? ""), previewButton: () => "", translate: authorityCopy });
assert.equal((authorityHtml.match(/data-attention-card-details/g) || []).length, 2, "every Today summary must keep its own details disclosure");
assert.equal((authorityHtml.match(/data-attention-card-details open/g) || []).length, 1, "Now must emphasize exactly one Today item by default");
assert.ok(authorityHtml.includes('class="research-attention-order" role="group"'), "Today ordering controls must expose group semantics");
assert.match(authorityHtml, /data-attention-reorder="up"[^>]*aria-label="[^"]*Today A/, "Today ordering controls must name the affected item");
assert.ok(authorityHtml.includes("2 sessions · 1 active · 1 needs review"), "an exact item must show its execution summary");
if (privateEdition) {
  // Only the private compact view links canonical sources and lists coverage evidence before a decision.
  const sourceActions = context.ResearchOSResearchPortfolioView.renderSourceActions(authorityModel.items[0], {
    previewButton: (sourcePath, label) => `[${label}:${sourcePath}]`,
    translate: (key) => key,
  });
  assert.match(sourceActions, /researchPortfolioOpenSource:06_active_context\/example-portfolio\.md/, "canonical authority must remain directly inspectable");
  assert.match(sourceActions, /researchPortfolioOpenWorkspace:\/workspace\/demo/, "an available project workspace must be exposed as the execution entry");
  const boundedSourceActions = context.ResearchOSResearchPortfolioView.renderSourceActions(authorityModel.items[0], {
    escapeHtml: (value) => String(value),
    previewButton: (sourcePath, label) => sourcePath.startsWith("/") ? "" : `[${label}:${sourcePath}]`,
    translate: (key) => key,
  });
  assert.match(boundedSourceActions, /research-workspace-route/, "an external workspace must remain visible when the repository preview boundary rejects it");
  assert.match(boundedSourceActions, /\/workspace\/demo/, "the non-previewable workspace route must preserve its exact registered path");
  assert.ok(authorityHtml.includes("data-coverage-evidence"), "unresolved coverage candidates must expose an evidence packet before asking for a decision");
  assert.ok(authorityHtml.includes('data-coverage-candidate="Demo student manuscript"'));
  assert.ok(authorityHtml.includes("student_relationship_contradiction"));
  assert.ok(authorityHtml.includes("The demo student leads the manuscript."));
}
const authoritySession = context.ResearchOSWorkSessionState.createSession({
  intent: "Handle Today A",
  portfolioBinding: { itemId: "today-a", title: "Today A" },
});
const authoritySwitchHtml = context.ResearchOSResearchPortfolioView.render({
  currentWorkSession: authoritySession,
  mutationEnabled: true,
  researchPortfolio: authorityModel,
}, { escapeHtml: (value) => String(value ?? ""), previewButton: () => "", translate: authorityCopy });
assert.ok(authoritySwitchHtml.includes('data-start-action-state="switch_research"'), "a competing Today commitment must not silently replace the active Work Session");
assert.ok(authoritySwitchHtml.includes('data-portfolio-switch-confirm="today-b"'), "switching research must expose an explicit consequence confirmation");

// Plugin bindings, driven through the DOM shim: an exact item opens its own drawer, public reordering stays in memory
// until undone, and feedback lands on the card whose button was pressed.
async function checkPluginBindings() {
  const orderItem = (id, order) => ({
    id, title: `Order ${id}`, provider_id: "research_portfolio", responsibility: "lead", state: "mainline",
    lifecycle_state: "open", lifecycle_phase: "writing", attention_state: "today", attention_date: "2026-08-12",
    today_order: order, next_step: `Step ${id}`, last_verified: "2026-08-12",
  });
  const slot = { payloads: { research_portfolio: {
    available: true, presentation_mode: "public_demo", sensitivity: "public", items: [orderItem("a", 1), orderItem("b", 2)],
  } } };
  const calls = { dispatched: 0, drawers: [], rerendered: 0 };
  const bindingContext = {
    dispatchPluginAction: async () => { calls.dispatched += 1; return { ok: true }; },
    draftWorkSession: () => ({ cancelled: true }),
    escapeHtml: String,
    openItemExecutionDrawer: (...args) => calls.drawers.push(args),
    previewButton: () => "",
    publicDemoVisible: () => true,
    rerenderDashboard: () => { calls.rerendered += 1; },
    text: (key) => key,
  };
  const order = (fragment) => [...fragment.matchAll(/data-attention-card="([^"]+)"/g)].map((match) => match[1]);
  assert.deepEqual(order(context.ResearchOSResearchPortfolioPlugin.renderWorkbench(slot, bindingContext)), ["a", "b"]);

  const statusA = element("p", { dataset: { portfolioActionStatus: "" } });
  const statusB = element("p", { dataset: { portfolioActionStatus: "" } });
  const maturityB = element("button", { dataset: { portfolioMaturityItem: "b", portfolioMaturityTarget: "I2" } });
  const reorderA = element("button", { dataset: { attentionItem: "a", attentionReorder: "down" } });
  const openExecution = element("button", { dataset: { executionPanel: "review", portfolioOpenExecution: "b" } });
  const undo = element("button", { dataset: { portfolioUndo: "" } });
  const bindingRoot = element("section", { dataset: { researchPortfolio: "" }, children: [
    element("article", { dataset: { lifecycleCard: "a" }, children: [statusA] }),
    element("article", { dataset: { lifecycleCard: "b" }, children: [maturityB, statusB] }),
    reorderA, openExecution, undo,
  ] });
  context.ResearchOSResearchPortfolioPlugin.bindWorkbench({ context: bindingContext, model: slot, root: bindingRoot });

  openExecution.click();
  assert.deepEqual(JSON.parse(JSON.stringify(calls.drawers)), [["b", "review", { focus: true }]], "execution must open on the exact item's drawer and requested panel");

  reorderA.click();
  assert.equal(calls.dispatched, 0, "public reordering must not dispatch a persistent attention mutation");
  assert.ok(calls.rerendered > 0, "public reordering must rerender the Now projection");
  assert.deepEqual(order(context.ResearchOSResearchPortfolioPlugin.renderWorkbench(slot, bindingContext)), ["b", "a"], "public reordering must be visible in memory");
  undo.click();
  assert.deepEqual(order(context.ResearchOSResearchPortfolioPlugin.renderWorkbench(slot, bindingContext)), ["a", "b"], "undo must clear the in-memory public order");

  maturityB.click();
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(statusB.textContent, "researchPortfolioActionCancelled", "action feedback must resolve against the clicked card");
  assert.equal(statusA.textContent, "", "feedback must not land on another card");

  const client = loadModules(["dashboard/src/services/request-auth.js", "dashboard/src/services/work-session-client.js"]).ResearchOSWorkSessionClient;
  let attentionBody = null;
  await client.applyAttentionAction({ id: "a", providerId: "research_portfolio" }, { action: "schedule", attentionDate: "2026-08-12", todayOrder: 2 }, {
    fetcher: async (url, init) => { attentionBody = { url, ...JSON.parse(init.body) }; return { ok: true, status: 200, json: async () => ({ ok: true }) }; },
  });
  assert.equal(attentionBody.url, "/attention-action");
  assert.equal(attentionBody.today_order, 2, "same-day order must travel through the existing reversible attention owner");
}

checkPluginBindings().then(() => console.log("Research portfolio contract passed."), (error) => { console.error(error); process.exitCode = 1; });
