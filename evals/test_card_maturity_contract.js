const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const memory = new Map();
const context = {
  console,
  crypto: { randomUUID: () => "test-session" },
  Date,
  document: { documentElement: { setAttribute() {} } },
  localStorage: {
    getItem: (key) => memory.get(key) || null,
    removeItem: (key) => memory.delete(key),
    setItem: (key, value) => memory.set(key, String(value)),
  },
  ResearchOSInteractions: { bindAll() {} },
  ResearchOSStatePolicy: { readJsonArray: () => [], writeJson: (_key, value) => value },
};
context.window = context;

[
  "dashboard/src/core/contracts.js",
  "dashboard/src/services/asset-overview-model.js",
  "dashboard/src/services/asset-overview-workbench.js",
  "dashboard/src/services/work-session-state.js",
  "dashboard/src/services/task-intent.js",
  "dashboard/src/services/work-session-router.js",
  "dashboard/src/services/doing-board-state.js",
  "dashboard/src/services/inbox.js",
  "dashboard/src/plugins/research-portfolio-model.js",
].forEach((file) => vm.runInNewContext(read(file), context, { filename: file }));

const Contracts = context.ResearchOSContracts;
assert.match(read("dashboard/src/views/asset-overview.js"), /data-asset-card-maturity-reason="\$\{escapeHtml\(cardMaturity\.reason \|\| ""\)\}"/);
assert.match(read("dashboard/src/services/asset-overview-workbench.js"), /maturityAxis === "M"/);
assert.match(read("dashboard/src/services/asset-overview-workbench.js"), /verify: "assetAdvancedVerifyLevel"/);
assert.match(read("dashboard/src/services/asset-overview-workbench.js"), /reverify: "assetAdvancedReverify"/);
assert.match(read("dashboard/src/plugins/research-assets.js"), /verify: "assetAdvancedVerifyLevel"/);
assert.match(read("dashboard/src/plugins/research-assets.js"), /reverify: "assetAdvancedReverify"/);
assert.match(read("dashboard/src/plugins/research-assets.js"), /note\.startsWith\(`\$\{transition\} · `/);
assert.match(read("dashboard/src/plugins/research-portfolio-view.js"), /maturity\.confirmed[\s\S]*maturityActionKey/);
assert.match(read("dashboard/src/views/asset-overview.js"), /assetMaturityPendingShort/);
assert.equal(Contracts.cardMaturityProfile("paper", { analysis_state: "M2_refined_read" }).level, "M2");
assert.equal(Contracts.cardMaturityProfile("project", {}).display_level, "I?");
assert.equal(Contracts.cardMaturityProfile("project", {}).target_level, "I0");
assert.equal(Contracts.cardMaturityProfile("project", { maturity_reason_cn: "M2 material reason" }).reason, "");
assert.equal(Contracts.cardMaturityProfile("person", { person_maturity_level: "Person-M2" }).level, "", "Legacy familiarity is not relationship maturity");
assert.equal(Contracts.cardMaturityProfile("person", { person_maturity_level: "Person-M2" }).confirmed, false);
assert.equal(Contracts.cardMaturityProfile("group", { group_level: "G2_direction_abstraction" }).level, "G2");

const model = context.ResearchOSAssetOverviewModel.buildAssetOverviewModel({
  overview: { people: { registered_collaborators: 2 } },
  graph: {
    asset_intelligence: [{
      path: "01_knowledge/papers/paper.md",
      material_maturity: { level: "M2_refined_read", label_zh: "精读可用", short_label: "M2" },
    }],
    asset_relation_matrix: [{
      path: "01_knowledge/papers/paper.md",
      title: "Paper",
      score: 10,
      projects: [{ path: "01_knowledge/projects/project.md", title: "Project", confidence: "high", project_maturity: "I2_active_mount" }],
      people: [{ path: "04_people/collaborators/person.md", title: "Person", confidence: "high", person_maturity_level: "Person-M2", relationship_maturity: "R2_evidence_linked" }],
    }],
  },
  translate: (key) => key,
});
const boxes = Object.fromEntries(model.cardBoxes.map((box) => [box.type, box]));
assert.equal(boxes.paper.cards[0].card_maturity.level, "M2");
assert.equal(boxes.project.cards[0].card_maturity.level, "I2");
assert.equal(boxes.person.cards[0].card_maturity.level, "R2");
assert.equal(boxes.person.cards[0].card_maturity.confirmed, true);
assert.equal(model.summary.peopleCount, 1, "the Library hero must count the same visible person cards as the person box");
assert.equal(boxes.project.cards[0].related_people_preview[0].title, "Person");
assert.deepEqual(
  Array.from(boxes.project.maturity_filters),
  ["all", "I0", "I1", "I2", "I3", "M1", "M2", "M3"],
  "the project box may contain operational project cards and knowledge/composition source cards",
);

const card = {
  dataset: {
    assetCardId: "project:project",
    assetCardMaturityAction: "enhance",
    assetCardMaturityAxis: "I",
    assetCardMaturityConfirmed: "true",
    assetCardMaturityLevel: "I2",
    assetCardMaturityReason: "Evidence is registered but the independent boundary is not yet confirmed.",
    assetCardMaturitySource: "explicit",
    assetCardMaturityTarget: "I3",
    assetCardPath: "01_knowledge/projects/project.md",
    assetCardPreview: "Project preview",
    assetCardTitle: "Project",
    assetCardType: "project",
  },
};
const payload = context.ResearchOSAssetOverviewWorkbenchService.assetTaskPayloadFromCard(card);
assert.equal(payload.action, "enhance_card_maturity");
assert.equal(payload.candidate.candidate_type, "card_enhancement");
assert.equal(payload.candidate.proposed_writeback.current_state, "I2");
assert.equal(payload.candidate.proposed_writeback.proposed_state, "I3");

const State = context.ResearchOSWorkSessionState;
const session = State.createSession({
  candidate: payload.candidate,
  enhancement: payload.enhancement,
  intent: "Enhance project card",
  title: "Project",
});
assert.equal(session.candidate.candidate_type, "card_enhancement");
assert.equal(State.normalizeSession(session).enhancement.target_level, "I3");
assert.equal(State.handoffPayload(session, (key) => key).candidate.candidate_type, "card_enhancement");
assert.equal(context.ResearchOSWorkSessionRouter.runPayload(session, {}, {}).candidate.candidate_type, "card_enhancement");
const doingItem = context.ResearchOSDoingBoardState.normalizeItem(State.handoffPayload(session, (key) => key));
assert.equal(doingItem.candidate.candidate_type, "card_enhancement");
const review = context.ResearchOSInboxService.collectUnifiedInboxEntries({ doingItems: [doingItem] }, {
  doingKey: (item) => item.id,
  doingTypeLabel: (type) => type,
  text: (key) => key,
});
assert.equal(review.entries[0].candidate.candidate_type, "card_enhancement");
assert.equal(review.entries[0].candidate.proposed_writeback.proposed_state, "I3");

const portfolio = context.ResearchOSResearchPortfolioModel.build({
  available: true,
  presentation_mode: "personal_vault",
  items: [{
    id: "project",
    title: "Project",
    state: "mainline",
    responsibility: "lead",
    lifecycle_state: "open",
    project_maturity: "I1_sandbox",
    source_root: "/example-workspaces/project/brief.md",
    related_people: ["Person A", { name: "Person B", path: "04_people/person-b.md" }],
  }],
}, (key) => key, "en");
assert.equal(portfolio.items[0].cardMaturity.level, "I1");
assert.equal(portfolio.items[0].relatedPeople.length, 2);
assert.equal(portfolio.items[0].sourceRoot, "/example-workspaces/project/brief.md");

console.log("card maturity contract ok");

assert.equal(Contracts.cardMaturityProfile("person", {person_maturity_level:"Person-M2"}).action,"verify", "Compatibility evidence must be verified before promotion");
