/* Item-local Review contract: Review entries fail closed to the exact item and session, the local ledger offers the four
 * decisions privately and only a copy-only disclosure in public, and the drawer's copy and markup stay owned in one place.
 */
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { loadModules, read, root } = require("./helpers/dashboard-vm.js");

const context = loadModules([
  "dashboard/src/services/inbox.js",
  "dashboard/src/components/segmented-control.js",
  "dashboard/src/views/unified-inbox.js",
  "dashboard/src/views/asset-overview.js",
  "dashboard/src/core/ui-copy-work-session.js",
]);
const service = context.ResearchOSInboxService;
const view = context.ResearchOSUnifiedInboxView;
const text = (key) => key;
const collected = service.collectUnifiedInboxEntries({
  doingItems: [
    {
      id: "handoff:work-session:S1",
      type: "task",
      title: "Exact item candidate",
      source: "work-session",
      status: "local",
      work_session_id: "S1",
      candidate: {
        candidate_id: "candidate:S1",
        candidate_type: "writeback",
        required_confirmation: "confirm",
        proposed_writeback: { object_id: "item-a", current_state: "draft", proposed_state: "reviewed" },
        admission_state: {
          schema_id: "researchos-admission-state-v1",
          decision_state: "proposed",
          mutation_state: "not_requested",
          validation_state: "unvalidated",
          authority_role: "none",
        },
      },
    },
    {
      id: "handoff:work-session:S2",
      type: "task",
      title: "Other item candidate",
      source: "work-session",
      status: "local",
      work_session_id: "S2",
      candidate: { candidate_id: "candidate:S2", proposed_writeback: { object_id: "item-b" } },
    },
  ],
}, { doingKey: (item) => item.id, doingTypeLabel: () => "Task", text });

const exact = service.entriesForItem(collected.entries, { itemId: "item-a", sessionIds: ["S1"] });
assert.equal(exact.length, 1, "item-local Review must fail closed to the exact item/session identity");
assert.equal(exact[0].raw.work_session_id, "S1");
assert.equal(service.entriesForItem(collected.entries, { itemId: "", sessionIds: ["S1"] }).length, 0);
assert.equal(service.entriesForItem(collected.entries, { itemId: "item-a", sessionIds: [] }).length, 0);

const deps = {
  emptyState: ({ message = "" } = {}) => `<p>${message}</p>`,
  encodeDataPayload: encodeURIComponent,
  escapeHtml: (value) => String(value ?? "").replaceAll('"', "&quot;").replaceAll("<", "&lt;"),
  previewButton: () => "",
  relatedCompositionCards: () => [],
  shortText: (value) => String(value || ""),
  translate: text,
};
const baseInbox = {
  allTotal: 1,
  archivedTotal: 0,
  codexRunnerEnabled: true,
  codexRuns: [],
  entries: exact,
  itemLocal: true,
  sessionRegistry: [{ intent: "Exact item session", item_id: "item-a", session_id: "S1", work_state: "needs_review" }],
  total: 1,
  visibleTotal: 1,
  workFilter: "needs_review",
};
const privateHtml = view.renderUnifiedInboxHtml({ inbox: baseInbox, deps });
for (const decision of ["accepted", "revised", "rejected", "deferred"]) {
  assert.ok(privateHtml.includes(`data-item-review-decision="${decision}"`));
}
assert.ok(privateHtml.includes("data-item-local-review-ledger"));
assert.ok(privateHtml.includes("data-item-local-session-registry") && privateHtml.includes("Exact item session"), "the drawer lists the item's own sessions");
assert.ok(privateHtml.includes("data-review-current-result"), "the drawer shows the current result next to its candidates");
assert.ok(!privateHtml.includes("Other item candidate"));
assert.ok(!privateHtml.includes("data-unified-inbox-generate"), "item-local Review must not recreate a global Inbox action");
assert.ok(!privateHtml.includes("data-work-filter"), "the item drawer has no global Work filter");

const publicHtml = view.renderUnifiedInboxHtml({ inbox: { ...baseInbox, publicMode: true }, deps });
assert.ok(publicHtml.includes('data-canonical-write="false"'));
assert.ok(!publicHtml.includes("data-item-review-decision="));

const emptyHtml = view.renderUnifiedInboxHtml({ inbox: { ...baseInbox, entries: [], sessionRegistry: [], total: 0, visibleTotal: 0, allTotal: 0 }, deps });
assert.ok(emptyHtml.includes("<p>itemReviewCandidatesEmpty</p>") && !emptyHtml.includes("data-item-review-decision="), "an item without candidates shows one empty line and no decisions");

// Library opens execution through its own copy key, which the Work Session catalog owns in both languages.
const lensHtml = context.ResearchOSAssetOverviewView.renderCommitmentLensProjection({
  active: true,
  commitments: [{ id: "item-a", title: "Item A", anchor: { path: "01_knowledge/projects/item-a.md", relationKind: "canonical_anchor", title: "Item A card" } }],
}, { escapeHtml: deps.escapeHtml, translate: text });
assert.ok(lensHtml.includes('data-library-open-execution="item-a"') && lensHtml.includes(">libraryLensOpenExecution<"), "Library execution actions use the Library-owned translation key");
assert.ok(!lensHtml.includes("researchAttentionViewExecution"), "Library must not depend on Research Portfolio plugin copy");
const workSessionCopy = context.ResearchOSUICopyWorkSession.simpleText;
for (const language of ["en", "zh-CN"]) {
  for (const key of ["libraryLensOpenExecution", "itemExecutionWorkTab", "itemExecutionReviewTab"]) {
    assert.ok(String(workSessionCopy[language]?.[key] || "").trim(), `${key} must have ${language} copy in the Work Session catalog`);
  }
}
assert.ok(!read("dashboard/src/core/i18n.js").includes('"libraryLensOpenExecution"'), "the Library execution label has one copy owner");

// index.html registers the owners and exposes the drawer as an accessible Work/Review tab pair.
const dashboardIndex = read("dashboard/index.html");
for (const asset of ["src/core/i18n.js", "src/core/ui-copy-work-session.js", "src/views/asset-overview.js", "src/views/unified-inbox.js", "src/services/inbox.js", "app.js"]) {
  assert.ok(dashboardIndex.includes(`<script src="${asset}"></script>`), `${asset} must be loaded by index.html`);
}
const drawerStart = dashboardIndex.indexOf("data-item-execution-drawer");
const drawer = dashboardIndex.slice(drawerStart, dashboardIndex.indexOf("</section>", dashboardIndex.indexOf('id="unifiedInbox"')));
assert.ok(drawerStart >= 0 && drawer.includes('role="tablist"') && (drawer.match(/role="tabpanel"/g) || []).length >= 2, "the exact-item drawer exposes an accessible Work/Review tab relationship");
assert.ok(drawer.indexOf('id="workSessionSurface"') >= 0 && drawer.indexOf('id="unifiedInbox"') >= 0, "the drawer holds both the Work Session surface and Review");

// Layout is checked by screenshots; the drawer and ledger classes must at least be styled.
let css = "";
const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).forEach((entry) => {
  const full = path.join(dir, entry.name);
  if (entry.isDirectory()) walk(full);
  else if (entry.name.endsWith(".css")) css += fs.readFileSync(full, "utf8");
});
walk(path.join(root, "dashboard/styles"));
for (const name of ["item-execution-drawer", "item-execution-tabs", "item-local-review-ledger"]) {
  assert.ok(new RegExp(`\\.${name}(?![\\w-])`).test(css), `${name} must have at least one rule under dashboard/styles`);
}

// Safety contracts in the app shell that a vm fixture cannot reach without booting the whole page:
// the exact-item deep link, stale-context disclosure and the request gates that drop late responses.
const appShell = fs.readFileSync(path.join(root, "dashboard/app.js"), "utf8");
for (const [token, reason] of [
  ['mutation_state: "not_requested"', "an item review decision records intent without requesting mutation"],
  ['validation_state: "unvalidated"', "an item review decision is not a validation"],
  ['authority_role: "none"', "an item review decision carries no authority"],
  ['routeUrl.searchParams.set("item", itemId)', "switching an item-local drawer keeps the deep-link item identity in sync"],
  ['routeUrl.searchParams.set("panel", panel === "review" ? "review" : "work")', "switching Work/Review keeps the deep-link panel identity in sync"],
  ['options.replaceRoute ? "replaceState" : "pushState"', "user navigation creates history while route repair stays replace-only"],
  ['addEventListener?.("popstate"', "browser Back/Forward restores the exact item-local route"],
  ['portfolioBindingContextStatus', "the drawer compares its frozen Work Session context with the current item"],
  ['contextStatus === "stale"', "a stale exact-item Work Session is disclosed instead of appearing current"],
  ['allowSessionAction', "stale-context safety is enforced below the view layer"],
  ["itemExecutionRequestGate.invalidate()", "every drawer navigation invalidates earlier same-item async responses"],
  ["itemExecutionRequestGate.isCurrent(requestToken, selectedExecutionItemId)", "an A to B to A response must match the latest revision and exact item"],
  ['runnerRefreshRequestGate.isCurrent(requestToken, "codex-runs")', "an older run-list response must not overwrite a newer refresh"],
]) assert.ok(appShell.includes(token), reason);

console.log("item-local Review contract ok");
