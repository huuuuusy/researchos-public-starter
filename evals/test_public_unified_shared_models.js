/* Public-safe contract test for the shared Unified Desk models. */
"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const modelContext = { console };
modelContext.window = modelContext;
vm.createContext(modelContext);
vm.runInContext(read("dashboard/src/services/item-composition-model.js"), modelContext);
const composition = modelContext.ResearchOSItemCompositionModel.build({
  assetBoxes: [{ label: "Demo assets", cards: [
    { id: "paper:demo", path: "demo/paper.md", state: "confirmed", title: "Demo Paper", type: "paper" },
    { id: "project:demo", path: "demo/project.md", state: "confirmed", title: "Demo Project", type: "project" },
  ] }],
  graph: { asset_relation_matrix: [], project_action_cards: [], projects: [{
    id: "project:demo",
    path: "demo/project.md",
    related_people: [],
    resolved_papers: [{ evidence_state: "confirmed", confidence: "high", match: "source_file", path: "paper.md", title: "Demo Paper" }],
    candidate_papers: [],
    source_files: [],
    title: "Demo Project",
  }] },
  portfolioItems: [{ id: "item:demo", sourcePath: "demo/project.md", title: "Demo Item" }],
});
assert.equal(composition.compositionForItem("item:demo").identityState, "exact_project");
const confirmedPaper = composition.compositionForItem("item:demo").confirmedComponents.find((entry) => entry.path === "demo/paper.md");
assert.ok(confirmedPaper, "the exact project relation must retain its confirmed paper component");
assert.equal(
  composition.reverseForComponent(confirmedPaper.componentId).confirmedItems.map((item) => item.id).join(","),
  "item:demo",
);

const routerContext = { console };
routerContext.window = routerContext;
vm.createContext(routerContext);
vm.runInContext(read("dashboard/src/services/codex-thread-router.js"), routerContext);
const publicRoute = routerContext.ResearchOSCodexThreadRouter.decide({
  publicStarter: true,
  routeReceipt: { status: "ready", identity: { continued_from_prior: true, drift_reasons: [], episode_id: "demo", thread_id: "thread:demo" } },
  runtime: { create_available: true, exact_thread_id: "thread:demo", thread_state: "resumable", transport_available: true },
});
assert.equal(publicRoute.recommended_route, "copy_only");
assert.equal(publicRoute.transport_state, "public_policy_blocked");

const composerContext = { console, crypto: crypto.webcrypto, TextEncoder };
composerContext.window = composerContext;
composerContext.ResearchOSWorkSessionState = {
  taskIdentityProjection: (session = {}) => Object.freeze({
    identity_kind: "portfolio_item",
    item_id: session.portfolioBinding?.itemId || "",
    logical_task_id: "task:demo",
    next_step_signature: "step:demo",
    provider_id: "research_portfolio",
    session_id: session.id || "",
  }),
};
vm.createContext(composerContext);
[
  "dashboard/src/services/task-intent.js",
  "dashboard/src/services/context-pack-projection.js",
  "dashboard/src/services/work-session-router.js",
  "dashboard/src/services/handoff-composer.js",
].forEach((file) => vm.runInContext(read(file), composerContext, { filename: file }));

async function main() {
  const input = {
    session: {
      cards: [{ id: "paper:demo", path: "demo/paper.md", title: "Demo Paper", type: "paper" }],
      evidenceBoundary: "Public demo sources only.",
      goal: "Prepare a public-safe handoff preview.",
      id: "work:demo",
      intent: "Review the demo item.",
      portfolioBinding: { itemId: "item:demo", nextStep: "Review", nextStepHash: "step:demo", providerId: "research_portfolio", sourcePath: "demo/project.md", title: "Demo Item" },
      responseMode: "answer",
      sensitivity: "public",
      templateLanguage: "en",
    },
    selection: {
      authority: "User confirmation + public-safe local Markdown owners",
      definitionOfDone: ["Preview generated"],
      excluded: [{ reason: "public_policy", scope: "provider execution and canonical writeback" }],
      primaryProject: { id: "item:demo", path: "demo/project.md", reason: "Selected item", title: "Demo Item" },
      relatedProjects: [],
      saveTarget: "",
    },
    handoffReceipt: {
      contentState: "included",
      forbiddenActions: { state: "recorded", items: ["No provider execution", "No canonical writeback"] },
      handoffId: `handoff:${"a".repeat(64)}`,
      lastJudgment: { state: "human_recorded", text: "Preview first." },
      limitations: ["projection_not_authority"],
      nextSafeAction: { state: "recommended", text: "Copy the reviewed text." },
      openBoundary: { state: "recorded", text: "External delivery is not proven." },
      runtimeScope: "public_starter",
      sourceRevision: { state: "verified", source_id: `src:${"b".repeat(64)}`, value_digest: "c".repeat(64) },
      targetClient: { kind: "codex", surface: "desktop", binding_state: "requested" },
      taskId: `task:${"d".repeat(64)}`,
    },
    route: publicRoute,
  };
  const result = await composerContext.ResearchOSHandoffComposer.compose(input, { language: "en", displayLanguage: "en" });
  const translated = await composerContext.ResearchOSHandoffComposer.compose(input, { language: "en", displayLanguage: "zh-CN" });
  assert.match(result.markdown, /## Agent handoff/);
  assert.match(translated.markdown, /## Agent 交接包/);
  assert.match(translated.envelope.prompt, /Response language: en/);
  assert.equal(result.digest, translated.digest, "display language must not change the bound handoff envelope");
  assert.equal(result.envelope.authority_state, "projection_not_authority");
  assert.equal(result.envelope.route.recommended_route, "copy_only");
  assert.match(result.markdown, /Demo Item/);
  assert.match(result.markdown, /provider execution and canonical writeback/);
  console.log("OK: Public Unified Desk shared models are exact, anonymous, and copy-only");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
