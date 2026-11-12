/* The onboarding worker writes cards with the First Run sensitivity defaults: internal for paper, project and
 * summary (capsule) cards, sensitive for person and meeting cards. `ros context` never packs private cards, so a
 * private default would leave every card the worker writes out of reach of the assistant. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

global.window = global;
global.addEventListener = () => {};
global.document = { querySelectorAll: () => [] };
const values = new Map();
global.localStorage = {
  getItem(key) { return values.has(key) ? values.get(key) : null; },
  setItem(key, value) { values.set(key, String(value)); },
  removeItem(key) { values.delete(key); },
};
global.fetch = async () => ({ ok: true, json: async () => ({ ok: true }) });
global.ResearchOSRequestAuth = { resolveFetcher: (fetcher) => fetcher || global.fetch };
global.ResearchOSStatePolicy = { readJsonArray: () => [], writeJsonArray: () => {} };
global.ResearchOSStorageContract = { storageKeys: {}, activeContextPaths: {} };

for (const relative of [
  "dashboard/src/services/action-inbox-state.js",
  "dashboard/src/services/queue-sync.js",
  "dashboard/src/services/inbox.js",
  "dashboard/src/services/plugin-runtime.js",
  "dashboard/src/services/onboarding-workbench.js",
  "dashboard/src/views/onboarding.js",
  "dashboard/src/plugins/material-pipeline.js",
]) {
  vm.runInThisContext(fs.readFileSync(path.join(__dirname, "..", relative), "utf8"), { filename: relative });
}

const Plugin = global.ResearchOSMaterialPipelinePlugin;
assert.ok(Plugin, "the material-pipeline plugin registers");

for (const language of ["en", "zh-CN"]) {
  const prompt = Plugin.onboardingPrompt("06_active_context/work_state/uploads/intake.json", language);
  assert.match(prompt, /paper, project, and summary \(capsule\) cards get sensitivity: internal/,
    "paper, project and summary cards default to internal");
  assert.match(prompt, /person cards \([^)]*\) and meeting cards get sensitivity: sensitive/,
    "person and meeting cards default to sensitive");
  const privateMentions = prompt.match(/sensitivity: private[^.]*/g) || [];
  for (const mention of privateMentions) {
    assert.match(mention, /^sensitivity: private only for a card the user says should never be handed to an assistant/,
      `private is only the user's explicit exception, never a default: "${mention}"`);
  }
  assert.ok(!/Keep real filled cards sensitivity: private/.test(prompt), "the old private default is gone");
}
console.log("OK: material-pipeline onboarding prompt uses the First Run sensitivity defaults");
