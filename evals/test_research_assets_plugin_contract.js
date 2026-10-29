const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const assetsManifest = JSON.parse(read("config/plugins/research-assets.json"));
assert.equal(
  assetsManifest.contributions.ui_slots.find((slot) => slot.id === "research_assets_library")?.order,
  90,
  "Library must place Project Overview before the collapsed source browser when no task is active",
);
const groups = [{ id: "group-1", title: "Method family", group_level: "G1", items: [{ path: "paper.md" }] }];
let dissolutions = [{ id: "dissolve-1", title: "Old group", group_level: "G1", status: "pending_codex_migration_review" }];
let removedGroup = "";
let withdrawnDissolution = "";
const context = {
  console,
  localStorage: { getItem() { return null; }, setItem() {} },
  ResearchOSStorageContract: { storageKeys: {}, activeContextPaths: {} },
  ResearchOSCardGroupStateService: {
    ensureCardGroups: () => ({ groups, selectedId: "group-1" }),
    loadStoredCardGroups: () => groups,
    loadCardGroupDissolutions: () => dissolutions,
    loadCardGroups: () => groups,
    markCardGroupDissolutionWithdrawn: (id) => { withdrawnDissolution = id; return { id, status: "withdrawn" }; },
    removeStoredCardGroup: (id) => { removedGroup = id; return { id }; },
    saveCardGroupDissolutions: (items) => { dissolutions = items; return items; },
  },
  ResearchOSCardGroupService: {},
  ResearchOSDoingBoardState: { normalizeItem: (item) => item },
  ResearchOSInboxService: {
    inboxStatusIsActive: (status) => !["withdrawn", "processed", "done"].includes(status),
    resolveClearedInboxItems: ({ localItems }) => ({ items: localItems.filter((item) => item.status !== "processed"), shouldSave: true }),
    unifiedInboxStatusLabel: (status) => status,
  },
  ResearchOSQueueSyncService: {
    syncCardGroupDissolutions: async () => "local",
    syncGroups: async () => "local",
  },
  ResearchOSDashboardRenderPlan: {
    publicStarterGraphForDisplay: (graph) => graph,
    publicStarterOverviewForDisplay: (overview) => overview,
  },
  ResearchOSAssetOverviewModel: {
    buildAssetOverviewModel: ({ graph, groups: inputGroups, inboxTotal }) => ({
      cardBoxes: graph.papers || [],
      focusCard: null,
      groups: inputGroups,
      inboxTotal,
      summary: { paperCount: (graph.papers || []).length },
    }),
  },
  ResearchOSAssetOverviewView: {
    renderAssetOverviewHtml: ({ summary, publicDemoToggleHtml }) => `<section data-research-assets>${summary.paperCount}${publicDemoToggleHtml}</section>`,
    renderCommitmentLensProjection: ({ active, commitments }) => active
      ? `<section data-library-lens-projection>${commitments.flatMap((item) => [item.anchor, ...item.related]).filter(Boolean).map((item) => item.path).join("|")}</section>`
      : "",
    renderPublicDemoToggle: () => "<aside data-demo-toggle></aside>",
  },
  ResearchOSAssetOverviewWorkbenchService: { bindAssetOverviewEvents() {} },
};
context.window = context;
vm.runInNewContext(read("dashboard/src/core/ui.js"), context);
vm.runInNewContext(read("dashboard/src/services/plugin-runtime.js"), context);
vm.runInNewContext(read("dashboard/src/plugins/research-assets.js"), context);

function data(enabled = true) {
  return {
    generated_at: "2026-08-13T00:00:00Z",
    runtime_mode: "private",
    source_overview: { materials: {} },
    asset_graph: { papers: [{ id: "paper-1", path: "paper.md", title: "Related paper" }] },
    preview_documents: [{ path: "project.md", related_papers: ["paper.md"], title: "Project source", type: "project" }, { path: "paper.md", title: "Related paper", type: "paper" }],
    plugins: enabled ? {
      schema_id: "researchos-plugin-v1",
      core_api_version: "1",
      loaded: [{ id: "research_assets" }],
      contributions: {
        actions: [],
        candidate_types: ["group", "dissolution"].map((id) => ({ id, plugin_id: "research_assets" })),
        projections: [
          { id: "source_overview", source: "source_overview", plugin_id: "research_assets", schema_id: "researchos-projection-envelope-v1", version: "1", sensitivity: "local_only", freshness: "snapshot", export_fields: ["$"] },
          { id: "asset_graph", source: "asset_graph", plugin_id: "research_assets", schema_id: "researchos-projection-envelope-v1", version: "1", sensitivity: "local_only", freshness: "snapshot", export_fields: ["$"] },
          { id: "preview_documents", source: "preview_documents", plugin_id: "research_assets", schema_id: "researchos-projection-envelope-v1", version: "1", sensitivity: "local_only", freshness: "snapshot", export_fields: ["$"] },
        ],
        ui_slots: [{
          id: "research_assets_library",
          slot: "library",
          surface: "library",
          region: "context",
          adapter: "research_assets_library",
          projection_ids: ["source_overview", "asset_graph", "preview_documents"],
          action_ids: [],
          plugin_id: "research_assets",
        }],
      },
    } : {
      schema_id: "researchos-plugin-v1",
      core_api_version: "1",
      loaded: [],
      contributions: { actions: [], candidate_types: [], projections: [], ui_slots: [] },
    },
  };
}

(async () => {
  const runtimeContext = {
    collectInbox: () => ({ total: 2 }),
    generatedAt: () => "2026-08-05T00:00:00Z",
    previewDocuments: () => [],
    text: (key) => key,
    toNumber: Number,
  };
  assert.equal(context.ResearchOSPluginRuntime.collectCandidateEntries({ data: data(false), context: runtimeContext }).entries.length, 0);
  const candidates = context.ResearchOSPluginRuntime.collectCandidateEntries({ data: data(true), context: runtimeContext });
  assert.deepEqual(Array.from(candidates.entries, (entry) => entry.type).sort(), ["dissolution", "group"]);
  assert.ok(candidates.entries.every((entry) => entry.candidate.plugin_id === "research_assets"));
  assert.ok(candidates.entries.every((entry) => entry.candidate.required_confirmation === "confirm"));

  const host = { hidden: true, innerHTML: "", querySelector() { return null; } };
  const receipt = context.ResearchOSPluginRuntime.renderSlots({ data: data(true), host, slot: "library", context: runtimeContext });
  assert.deepEqual(Array.from(receipt.rendered), ["research_assets_library"]);
  assert.ok(host.innerHTML.includes("data-research-assets"));
  context.ResearchOSPluginRuntime.renderSlots({ data: data(false), host, slot: "library", context: runtimeContext });
  assert.equal(host.innerHTML, "");
  assert.equal(host.hidden, true, "disabled research-assets plugin must remove its Library contribution cleanly");

  const libraryModel = { payloads: data(true) };
  const libraryContext = {
    collectInbox: () => ({ total: 0 }),
    escapeHtml: (value) => String(value),
    generatedAt: () => "2026-08-12",
    getPreviewDocument: (path) => data(true).preview_documents.find((document) => document.path === path) || null,
    libraryLens: () => ({ items: [{ id: "commitment-1", sourcePath: "project.md", title: "Current commitment" }], selectedIds: ["commitment-1"] }),
    previewButton: (path, label) => `<button data-preview-path="${path}">${label}</button>`,
    previewDocuments: () => data(true).preview_documents,
    publicDemoVisible: () => true,
    publicStarter: () => true,
    runtimeMode: () => "public_starter",
    resolveRelativePath: (_base, target) => target,
    text: (key) => key,
    toNumber: Number,
  };
  assert.ok(context.ResearchOSResearchAssetsPlugin.renderLibrary(libraryModel, libraryContext).includes("data-demo-toggle"));
  const selectedLibraryHtml = context.ResearchOSResearchAssetsPlugin.renderLibrary(libraryModel, libraryContext);
  assert.ok(selectedLibraryHtml.includes("data-library-lens-projection"), "a selected Commitment must create a visible material projection, not only a selected button");
  assert.ok(read("dashboard/src/views/asset-overview.js").includes("data-library-open-execution"), "a selected Library Commitment must expose its item-local Work/Review entry without returning to Now");
  assert.ok(selectedLibraryHtml.includes("project.md|paper.md"), "the lens projection must contain the exact source anchor and its explicit relation");
  assert.ok(!context.ResearchOSResearchAssetsPlugin.renderLibrary(libraryModel, {
    ...libraryContext,
    libraryLens: () => ({ items: [{ id: "commitment-1", sourcePath: "project.md" }], selectedIds: [] }),
  }).includes("data-library-lens-projection"), "clearing the lens must remove the commitment-specific material projection");
  const namedRelationProjection = context.ResearchOSResearchAssetsPlugin.buildCommitmentLensProjection({
    graph: {},
    lens: { items: [{ id: "named", sourcePath: "named.md", title: "Named relations" }], selectedIds: ["named"] },
    previewDocuments: [{ path: "named.md", related_people: ["Fictional Research Partner"], source_files: ["https://example.test/source"] }],
    viewModel: { cardBoxes: [] },
  }, { resolveRelativePath: (_base, target) => `resolved/${target}` });
  assert.deepEqual(Array.from(namedRelationProjection.commitments[0].related, (item) => item.path), ["", ""], "named and external references must not be forged into local paths");
  assert.deepEqual(Array.from(namedRelationProjection.commitments[0].related, (item) => item.title), ["Fictional Research Partner", "https://example.test/source"]);
  assert.ok(context.ResearchOSResearchAssetsPlugin.renderLibrary(libraryModel, libraryContext).includes("data-library-source-browser"), "without an active task the global source wall must stay behind an on-demand browser");
  assert.ok(!context.ResearchOSResearchAssetsPlugin.renderLibrary(libraryModel, libraryContext).includes("data-current-context-pack"), "the Assets plugin must not duplicate the Shell-owned Context Pack");
  assert.ok(!context.ResearchOSResearchAssetsPlugin.renderLibrary(libraryModel, {
    ...libraryContext,
    runtimeMode: () => "personal_vault",
  }).includes("data-demo-toggle"), "a personal vault must not offer a demo toggle when no demo projection is mounted");

  await context.ResearchOSPluginRuntime.runCandidateAction({
    action: "withdraw", candidateType: "group", data: data(true), context: runtimeContext, id: "group-1",
  });
  await context.ResearchOSPluginRuntime.runCandidateAction({
    action: "withdraw", candidateType: "dissolution", data: data(true), context: runtimeContext, id: "dissolve-1",
  });
  assert.equal(removedGroup, "group-1");
  assert.equal(withdrawnDissolution, "dissolve-1");

  const selectedCard = { id: "paper-1", path: "paper.md", title: "Selected paper" };
  let draftedInput = null;
  let addedCard = null;
  context.ResearchOSResearchAssetsPlugin.handleAssetTask({
    card: {},
    payload: { path: "paper.md", source: "asset-overview-card", title: "Selected paper" },
  }, {
    addWorkSessionCard: (card) => { addedCard = card; return { ok: true }; },
    cardFromElement: () => selectedCard,
    currentWorkSession: () => null,
    draftWorkSession: (input) => { draftedInput = input; return { ok: true, session: { status: "draft" } }; },
    text: (key) => key,
  });
  assert.equal(draftedInput.cards[0], selectedCard, "a card selected without a current task must create a draft task containing that card");
  assert.equal(draftedInput.responseMode, "auto", "card-created drafts must keep result-mode inference in the Work Session owner");
  assert.equal(addedCard, null, "a newly drafted task must not add the same card twice");

  draftedInput = null;
  context.ResearchOSResearchAssetsPlugin.handleAssetTask({
    card: {},
    payload: { path: "paper.md", source: "asset-overview-card", title: "Selected paper" },
  }, {
    addWorkSessionCard: (card) => { addedCard = card; return { ok: true }; },
    cardFromElement: () => selectedCard,
    currentWorkSession: () => ({ id: "active-task", status: "active" }),
    draftWorkSession: (input) => { draftedInput = input; return { ok: true }; },
    text: (key) => key,
  });
  assert.equal(addedCard, selectedCard, "a card selected during an existing task must extend that task's working deck");
  assert.equal(draftedInput, null, "an existing unfinished task must not be replaced by an implicit draft");

  let openedWorkspace = "";
  context.ResearchOSResearchAssetsPlugin.handleAssetTask({
    payload: {
      note: "Compare these sources",
      source: "asset-card-basket",
      source_cards: [{ id: "paper-1", path: "paper.md", title: "Selected paper" }],
      title: "Bounded comparison",
    },
  }, {
    draftWorkSession: () => ({ ok: true }),
    openWorkspace: (workspace) => { openedWorkspace = workspace; },
  });
  assert.equal(openedWorkspace, "", "Library context selection must update in place instead of navigating to a global Work screen");

  const relationshipContext = {
    previewDocuments: () => [{
      path: "04_people/network/pattern.md",
      related_people: ["../person.md"],
      source_files: [],
      title: "Existing relation",
      type: "relationship_pattern",
      updated: "2026-08-05",
    }],
    resolveRelativePath: () => "04_people/person.md",
  };
  const reviewDeps = context.ResearchOSPluginRuntime.resolveSurfaceDependencies({
    data: data(true), surface: "work", context: relationshipContext,
  });
  assert.equal(reviewDeps.relatedCompositionCards([{ path: "04_people/person.md" }])[0].title, "Existing relation");
  assert.deepEqual(
    Object.keys(context.ResearchOSPluginRuntime.resolveSurfaceDependencies({ data: data(false), surface: "work", context: relationshipContext })),
    [],
    "disabled research-assets plugin must not decorate Work/Needs Review",
  );

  const inboxSource = read("dashboard/src/services/inbox.js");
  const appSource = read("dashboard/app.js");
  const deskSource = read("dashboard/src/plugins/unified-research-desk.js");
  for (const retiredPath of ["sources.cardGroups", "sources.dissolutionItems", "paths.cardGroups", "paths.cardGroupDissolution"]) {
    assert.ok(!inboxSource.includes(retiredPath), `Review core must not retain ${retiredPath}`);
  }
  assert.ok(!appSource.includes("function renderAssetOverview"));
  const pluginHostSource = read("dashboard/src/services/plugin-host.js");
  assert.ok(pluginHostSource.includes("global.ResearchOSAssetOverviewView.renderCommitmentLens"), "the plugin host must render the Commitment lens through the existing Library view owner");
  assert.ok(pluginHostSource.includes("libraryLens: () => ({"), "the plugin host must pass ephemeral Commitment selection into the existing Library projection owner");
  assert.ok(pluginHostSource.includes("app.selectedLibraryLensIds.filter((itemId) => commitmentIds.has(String(itemId)))"), "stale Commitment IDs must fail closed before the Library lens is rendered");
  assert.ok(!read("dashboard/src/views/asset-overview.js").includes('data-open-workspace="review"'));
  assert.ok(!read("dashboard/src/views/asset-overview.js").includes('data-open-workspace="work"'), "Library output must not emit global Work or Review navigation");
  assert.ok(!appSource.includes("ResearchOSCardGroupStateService"));
  assert.ok(!appSource.includes("relatedCompositionCardsForBasket"));

  vm.runInNewContext(read("dashboard/src/views/asset-overview.js"), context);
  const relationHtml = context.ResearchOSAssetOverviewView.renderCommitmentLensProjection({
    active: true,
    commitments: [{
      anchor: { path: "project.md", previewable: true, relationKind: "canonical_anchor", title: "Project source" },
      id: "commitment-1",
      related: [{ path: "paper.md", previewable: true, relationKind: "canonical_relation", title: "Related paper" }],
      title: "Current commitment",
    }],
  }, {
    escapeHtml: (value) => String(value),
    previewButton: (path, label) => `<button data-preview-path="${path}">${label}</button>`,
    translate: (key) => key,
  });
  assert.ok(relationHtml.includes('data-library-relation-kind="canonical_anchor"'));
  assert.ok(relationHtml.includes('data-library-relation-kind="canonical_relation"'));
  assert.ok(relationHtml.includes('data-preview-path="paper.md"'));
  const overflowSelectorHtml = context.ResearchOSAssetOverviewView.renderCommitmentLens({
    items: Array.from({ length: 13 }, (_, index) => ({ id: `commitment-${index + 1}`, title: `Commitment ${index + 1}` })),
    selectedIds: ["commitment-13"],
  }, { escapeHtml: (value) => String(value), translate: (key) => key });
  assert.ok(overflowSelectorHtml.includes('data-library-lens-item="commitment-13"'), "a selected Commitment beyond the default display cap must remain visible and removable");
  assert.equal((overflowSelectorHtml.match(/data-library-lens-item=/g) || []).length, 13, "all Commitments must remain reachable inside region groups");
  assert.ok(overflowSelectorHtml.includes("library-commitment-region-more"), "items outside the soft default budget must be folded rather than dropped");
  const mandatoryOverflowHtml = context.ResearchOSAssetOverviewView.renderCommitmentLens({
    items: Array.from({ length: 15 }, (_, index) => ({
      id: `required-${index + 1}`,
      title: `Required ${index + 1}`,
      mandatory_visibility: true,
    })),
    selectedIds: [],
  }, { escapeHtml: (value) => String(value), translate: (key) => key });
  assert.equal((mandatoryOverflowHtml.match(/data-library-lens-item=/g) || []).length, 15, "mandatory Commitments must overflow the soft budget instead of being truncated");
  assert.equal((mandatoryOverflowHtml.match(/data-library-lens-mandatory="true"/g) || []).length, 15, "mandatory visibility must remain explicit in the rendered contract");
  assert.ok(deskSource.includes("card_view_consolidation?.placement?.commitments"), "the Library lens must consume the shared single-region projection");
  console.log("Research assets plugin contract passed.");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
