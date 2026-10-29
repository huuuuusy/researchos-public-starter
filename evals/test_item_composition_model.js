/* ResearchOS maintenance header.
 * 中文：验证产品—组件双向投影只使用 exact identity，并分离 confirmed、candidate 与本轮 Handoff 选择。
 * English: Verifies that the product-component dual lens uses exact identity and separates confirmed/candidate relations from Handoff selection.
 */

"use strict";

const assert = require("node:assert/strict");
const { loadModules } = require("./helpers/dashboard-vm.js");

// All people, paths and projects below are fictional; the module is byte-identical in both editions.
const CompositionModel = loadModules(["dashboard/src/services/item-composition-model.js"]).ResearchOSItemCompositionModel;

const fixture = CompositionModel.build({
  selfPersonAliases: ["Demo Researcher", "Demo", "示例研究者"],
  assetBoxes: [{
    label: "论文与阅读资产",
    cards: [{
      id: "paper:confirmed",
      path: "01_knowledge/papers/confirmed.md",
      relation_ids: [],
      state: "confirmed",
      title: "Confirmed Paper",
      type: "paper",
    }, {
      id: "project:exact-canonical",
      path: "01_knowledge/projects/family/exact.md",
      relation_ids: [],
      state: "confirmed",
      title: "Exact Project Card",
      type: "project",
    }, {
      id: "person:demo-collaborator",
      path: "04_people/collaborators/demo-collaborator.md",
      relation_ids: [],
      state: "confirmed",
      title: "示例合作者 / Demo Collaborator",
      type: "person",
    }],
  }],
  graph: {
    asset_relation_matrix: [],
    project_action_cards: [],
    projects: [{
      id: "graph:conflicting-project-id",
      path: "01_knowledge/projects/family/exact.md",
      related_people: [{ confidence: "high", name: "Exact Person", path: "04_people/exact-person.md" }],
      resolved_papers: [{ confidence: "high", source: "project_frontmatter", match: "source_file", path: "01_knowledge/papers/confirmed.md", title: "Confirmed Paper" }],
      candidate_papers: [{ confidence: "medium", match: "semantic_candidate", path: "01_knowledge/papers/candidate.md", title: "Candidate Paper" }],
      source_files: ["../../papers/support-note.md", "local-note.md"],
      title: "Exact Project",
    }],
  },
  portfolioItems: [
    { id: "exact-item", sourcePath: "01_knowledge/projects/family/exact.md", title: "Exact Product" },
    { id: "same-title-item", sourcePath: "06_active_context/unbound.md", title: "Exact Project" },
    {
      accountableOwner: "Demo Collaborator / manuscript team",
      id: "portfolio-linked-item",
      sourcePath: "06_active_context/research-portfolio.md",
      sourceRoot: "/fictional/external-project/docs/brief.md",
      title: "Portfolio Linked Product",
    },
    {
      accountableOwner: "Unknown Owner / manuscript team",
      id: "unresolved-owner-item",
      sourcePath: "06_active_context/research-portfolio.md",
      title: "Unresolved Owner Product",
    },
    {
      accountableOwner: "Demo",
      id: "self-owned-item",
      sourcePath: "06_active_context/research-portfolio.md",
      title: "Self-owned Product",
    },
  ],
});

const exact = fixture.compositionForItem("exact-item");
assert.equal(exact.identityState, "exact_project");
assert.equal(exact.rootComponentId, "project:exact-canonical", "exact path must dominate a conflicting source ID");
assert.ok(exact.confirmedComponents.some((entry) => entry.componentId === "paper:confirmed"));
assert.ok(exact.candidateComponents.some((entry) => entry.type === "person" && entry.title === "Exact Person"), "high confidence alone does not confirm the person's relation to this project");
assert.ok(exact.confirmedComponents.some((entry) => entry.path === "01_knowledge/papers/support-note.md"));
assert.ok(exact.confirmedComponents.some((entry) => entry.path === "01_knowledge/projects/family/local-note.md"), "bare source_files names must resolve beside their project owner");
assert.ok(exact.candidateComponents.some((entry) => entry.title === "Candidate Paper"));
assert.equal(fixture.components.filter((entry) => entry.path === "01_knowledge/projects/family/exact.md").length, 1, "one exact path must not produce duplicate component identities");

const unbound = fixture.compositionForItem("same-title-item");
assert.equal(unbound.identityState, "source_only");
assert.equal(unbound.confirmedComponents.length, 0, "same title must never create a confirmed relation");
assert.equal(unbound.candidateComponents.length, 0, "same title must never create a candidate relation implicitly");
assert.match(unbound.evidenceGaps.join(" "), /未按标题猜测关系/);

const portfolioLinked = fixture.compositionForItem("portfolio-linked-item");
assert.equal(portfolioLinked.identityState, "portfolio_relations");
assert.ok(portfolioLinked.confirmedComponents.some((entry) => entry.componentId === "person:demo-collaborator"), "a uniquely matched accountable owner must reuse the existing person card");
assert.ok(portfolioLinked.confirmedComponents.some((entry) => entry.path === "/fictional/external-project/docs/brief.md"), "an explicit external source_root must remain absolute and become a confirmed material card");
assert.equal(portfolioLinked.candidateComponents.length, 0);

const unresolvedOwner = fixture.compositionForItem("unresolved-owner-item");
assert.ok(unresolvedOwner.candidateComponents.some((entry) => entry.type === "person" && entry.title.includes("Unknown Owner")), "an unmatched accountable owner must remain a visible candidate");
assert.match(unresolvedOwner.evidenceGaps.join(" "), /尚未匹配到人物卡/);

const selfOwned = fixture.compositionForItem("self-owned-item");
assert.equal(selfOwned.candidateComponents.length, 0, "the self owner belongs in WHO and must not be repeated as a resource candidate on every task");

const reverse = fixture.reverseForComponent("paper:confirmed");
assert.deepEqual(Array.from(reverse.confirmedItems, (item) => item.id), ["exact-item"]);
assert.equal(reverse.candidateItems.length, 0);
assert.equal(Object.hasOwn(exact, "handoffSelection"), false, "composition projection must not own bounded Handoff selection");

// Fictional projection exercises the integration shape without reading a dashboard file.
const dashboard = {
  asset_graph: {
    projects: [
      { id: "demo-review", path: "01_knowledge/projects/demo-review.md", source_files: ["demo-evidence.md"] },
      { id: "demo-study", path: "01_knowledge/projects/demo-study.md", project_status_summary: "Paper and people evidence remains unresolved" },
    ],
  },
  home_command_center: { research_portfolio: { items: [
    { id: "demo-review", sourcePath: "01_knowledge/projects/demo-review.md" },
    { id: "demo-study", sourcePath: "01_knowledge/projects/demo-study.md", sourceRoot: "/fictional/study-source", accountableOwner: "Demo" },
    { id: "demo-brief", sourcePath: "06_active_context/example-portfolio.md", sourceRoot: "/fictional/collaboration/brief.md" },
  ] } },
};
const projected = CompositionModel.build({
  assetBoxes: [], graph: dashboard.asset_graph,
  portfolioItems: dashboard.home_command_center.research_portfolio.items,
  selfPersonAliases: ["Demo Researcher", "Demo", "示例研究者"],
});
const review = projected.compositionForItem("demo-review");
const study = projected.compositionForItem("demo-study");
const brief = projected.compositionForItem("demo-brief");
assert.equal(review.identityState, "exact_project");
assert.ok(review.confirmedComponents.length > 0, "the fictional review exercises non-zero confirmed composition");
assert.equal(study.identityState, "exact_project");
assert.ok(study.confirmedComponents.some((entry) => entry.path === "/fictional/study-source"), "explicit source_root remains a confirmed stable source");
assert.equal(study.candidateComponents.length, 0, "the self owner stays in WHO");
assert.ok(study.evidenceGaps.length > 0, "stable sources must not hide unresolved evidence");
assert.ok(brief.confirmedComponents.some((entry) => entry.path === "/fictional/collaboration/brief.md"));

console.log("OK: Product-component dual lens is exact, bidirectional, provenance-aware, and Handoff-independent");


// Relation evidence decides confirmation: confidence alone stays a candidate, rejected evidence removes the relation.
function compositionWithEvidence(state, confidence = "high") {
  return CompositionModel.build({
    assetBoxes: [],
    portfolioItems: [{ id: "task-a", sourcePath: "01_knowledge/projects/example.md", title: "Project" }],
    graph: {
      projects: [{
        id: "project-a",
        path: "01_knowledge/projects/example.md",
        related_people: [{ path: "04_people/example.md", name: "Example Person", confidence }],
        resolved_papers: [],
      }],
      asset_relation_evidence: state ? [{
        source_path: "01_knowledge/projects/example.md",
        target_path: "04_people/example.md",
        edge_type: "collaborator_role",
        evidence_state: state,
        needs_confirmation: state === "candidate",
      }] : [],
    },
  }).compositionForItem("task-a");
}
assert.equal(compositionWithEvidence().confirmedComponents.length, 0);
assert.equal(compositionWithEvidence().candidateComponents.length, 1);
assert.equal(compositionWithEvidence("confirmed").confirmedComponents.length, 1);
assert.equal(compositionWithEvidence("rejected").candidateComponents.length, 0);
assert.equal(compositionWithEvidence("rejected").confirmedComponents.length, 0);
assert.equal(compositionWithEvidence("candidate").confirmedComponents.length, 0);
console.log("OK: confidence, confirmed evidence and rejected relations remain distinct");
