/* B17: personal-vault mode must not draw the fictional-demo asset-create panel or its open button, on Now or in Library;
 * the public demo still draws both. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const PANEL = "data-asset-create-panel";
const OPEN = "data-asset-open-intake";
const boxes = [{ id: "papers", type: "paper", label: "Papers", count: 1, cards: [{ id: "paper-1", path: "01_knowledge/papers/example.md", title: "Example paper", type: "paper" }] }];
const deps = { escapeHtml: (value) => String(value ?? ""), shortText: (value) => String(value ?? ""), translate: (key) => key };

function viewContext() {
  const context = { console };
  context.window = context;
  vm.createContext(context);
  vm.runInContext(read("dashboard/src/views/asset-overview.js"), context);
  return context;
}

// The view: one flag drops both the panel and the button; without it the public demo panel is drawn as before.
{
  const View = viewContext().ResearchOSAssetOverviewView;
  const demo = View.renderAssetCardBoxWorkbench({ boxes, publicMode: true }, deps);
  assert.ok(demo.includes(PANEL) && demo.includes(OPEN), "the public demo still draws the create panel and its button");
  assert.ok(demo.includes("researchPortfolioPublicDemoLabel") && demo.includes("onboardingPublicBody"));
  const vault = View.renderAssetCardBoxWorkbench({ boxes, publicMode: true, hideCreatePanel: true }, deps);
  assert.ok(!vault.includes(PANEL) && !vault.includes(OPEN) && !vault.includes("onboardingPublicBody"), "hideCreatePanel drops the panel and the button");
  assert.ok(vault.includes("Example paper"), "the cards themselves stay");
  const overview = View.renderAssetOverviewHtml({ cardBoxes: boxes, publicMode: true, hideCreatePanel: true, deps });
  assert.ok(!overview.includes(PANEL) && !overview.includes(OPEN), "renderAssetOverviewHtml forwards the flag");
  console.log("OK: asset-create panel flag in the view");
}

// Library: the research-assets plugin hides the panel only when the runtime is personal_vault.
{
  const context = viewContext();
  Object.assign(context, {
    localStorage: { getItem() { return null; }, setItem() {} },
    ResearchOSStorageContract: { storageKeys: {}, activeContextPaths: {} },
    ResearchOSCardGroupStateService: { ensureCardGroups: () => ({ groups: [], selectedId: "" }), loadCardGroupDissolutions: () => [], loadStoredCardGroups: () => [] },
    ResearchOSCardGroupService: {},
    ResearchOSDoingBoardState: { normalizeItem: (item) => item },
    ResearchOSInboxService: { inboxStatusIsActive: () => true, unifiedInboxStatusLabel: (status) => status },
    ResearchOSQueueSyncService: {},
    ResearchOSDashboardRenderPlan: { publicStarterGraphForDisplay: (graph) => graph, publicStarterOverviewForDisplay: (overview) => overview },
    ResearchOSAssetOverviewModel: { buildAssetOverviewModel: () => ({ cardBoxes: boxes, focusCard: null, summary: {} }) },
    ResearchOSAssetOverviewWorkbenchService: { bindAssetOverviewEvents() {} },
  });
  vm.runInContext(read("dashboard/src/core/ui.js"), context);
  vm.runInContext(read("dashboard/src/plugins/research-assets.js"), context);
  const model = { payloads: { asset_graph: {}, source_overview: {}, preview_documents: [] } };
  const libraryHtml = (runtimeMode) => context.ResearchOSResearchAssetsPlugin.renderLibrary(model, {
    escapeHtml: deps.escapeHtml,
    generatedAt: () => "2026-11-11",
    libraryLens: () => ({ items: [], selectedIds: [] }),
    publicDemoVisible: () => true,
    publicStarter: () => true, // a personal-vault projection also carries a public_starter block
    runtimeMode: () => runtimeMode,
    text: (key) => key,
    toNumber: Number,
  });
  const demo = libraryHtml("public_starter");
  assert.ok(demo.includes(PANEL) && demo.includes(OPEN), "Library in the public demo still draws the panel and its button");
  const vault = libraryHtml("personal_vault");
  assert.ok(!vault.includes(PANEL) && !vault.includes(OPEN), "Library in personal-vault mode draws neither");
  assert.ok(vault.includes("Example paper"));
  console.log("OK: Library hides the create panel only in personal-vault mode");
}

// Now: the Research desk resource library follows the loaded projection's runtime_mode.
(async () => {
  const nodes = new Map();
  class Node {
    constructor(tag = "div") { this.tag = tag; this.dataset = {}; this.children = []; this.listeners = {}; this.classList = { add() {}, remove() {}, toggle() {} }; this.innerHTML = ""; }
    append(...items) { this.children.push(...items); }
    replaceChildren(...items) { this.children = items; }
    setAttribute(key, value) { this[key] = value; }
    removeAttribute() {}
    toggleAttribute() {}
    addEventListener(key, callback) { this.listeners[key] = callback; }
    cloneNode() { return new Node(); }
    replaceWith() {}
    querySelectorAll() { return []; }
    querySelector() { return null; }
    focus() {}
    contains() { return false; }
  }
  const html = read("dashboard/index.html");
  for (const [, id] of html.matchAll(/\sid="([^"]+)"/g)) nodes.set(id, new Node());
  const deskRoot = new Node();
  deskRoot.dataset.runtimeScope = "public_starter"; // index.html ships this attribute in every mode
  const context = {
    console,
    Date: class FixedDate extends Date { constructor(value) { super(value === undefined ? "2026-11-11T12:00:00" : value); } },
    URLSearchParams,
    document: {
      readyState: "complete",
      documentElement: { lang: "en" },
      addEventListener() {},
      createElement: (tag) => new Node(tag),
      createDocumentFragment: () => new Node(),
      createTextNode: (value) => Object.assign(new Node(), { textContent: value }),
      getElementById: (id) => nodes.get(id) || null,
      querySelector: (selector) => selector === "[data-unified-desk]" ? deskRoot : null,
      querySelectorAll: () => [],
    },
    ResearchOSResearchPortfolioModel: { build: () => ({ items: [] }) },
    ResearchOSAssetOverviewModel: { buildAssetOverviewModel: () => ({ cardBoxes: boxes }) },
    ResearchOSItemCompositionModel: { build: () => ({ components: [], compositionForItem: () => null }) },
    ResearchOSUiCore: { escapeHtml: deps.escapeHtml },
    ResearchOSInteractions: { bindAll() {} },
  };
  context.window = context;
  vm.createContext(context);
  vm.runInContext(read("dashboard/src/core/contracts.js"), context);
  vm.runInContext(read("dashboard/src/views/asset-overview.js"), context);
  vm.runInContext(read("dashboard/src/plugins/research-portfolio-workbench.js"), context);
  context.ResearchOSResearchPortfolioWorkbench = { ...context.ResearchOSResearchPortfolioWorkbench, bind() {} };
  for (const file of ["research-portfolio-copy", "unified-desk-calendar", "unified-desk-handoff", "unified-research-desk"]) {
    vm.runInContext(read(`dashboard/src/plugins/${file}.js`), context);
  }
  const desk = context.ResearchOSUnifiedResearchDesk;
  const nowHtml = async (runtimeMode) => {
    await desk.init({ fetcher: async () => ({ ok: true, json: async () => ({ runtime_mode: runtimeMode, config: { content_language: "en" } }) }) });
    return nodes.get("resource-card-boxes").innerHTML;
  };
  const demo = await nowHtml("public_starter");
  assert.ok(demo.includes(PANEL) && demo.includes(OPEN), "Now in the public demo still draws the panel and its button");
  const vault = await nowHtml("personal_vault");
  assert.ok(!vault.includes(PANEL) && !vault.includes(OPEN), "Now in personal-vault mode draws neither");
  assert.ok(vault.includes("Example paper"));
  console.log("OK: Now hides the create panel only in personal-vault mode");
})().catch((error) => { console.error(error); process.exitCode = 1; });
