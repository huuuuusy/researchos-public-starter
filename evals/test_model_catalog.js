const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const values = new Map();
const storage = {
  getItem: (key) => values.has(key) ? values.get(key) : null,
  setItem: (key, value) => values.set(key, String(value)),
};
const context = { window: { localStorage: storage } };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, "dashboard/src/services/model-catalog.js"), "utf8"), context);

const catalog = context.window.ResearchOSModelCatalog;
const runtime = {
  ok: true,
  recommended_model: "gpt-5.6-sol",
  configured_default_model: "gpt-5.5",
  models: [
    { id: "gpt-5.6-sol", label: "GPT-5.6-Sol", priority: 1, reasoning_efforts: ["low", "medium", "ultra"] },
    { id: "gpt-5.5", label: "GPT-5.5", priority: 2, reasoning_efforts: ["low", "medium", "high"] },
  ],
};

const automatic = catalog.selectionState("auto", runtime, []);
assert.equal(automatic.effectiveModel, "gpt-5.6-sol");
assert.equal(automatic.autoModel.label, "GPT-5.6-Sol");
const normalizedTwice = catalog.normalizeRuntimeCatalog(catalog.normalizeRuntimeCatalog(runtime));
assert.deepEqual(Array.from(normalizedTwice.models[0].reasoningEfforts), ["low", "medium", "ultra"]);
assert.equal(normalizedTwice.recommendedModel, "gpt-5.6-sol");

const added = catalog.addCustomModel([], "company/research-model");
assert.equal(added.ok, true);
assert.equal(added.model.custom, true);
const publicAutomatic = catalog.selectionState("auto", { ok: true, models: [] }, added.customModels);
assert.equal(publicAutomatic.autoModel, null, "Auto must not silently promote a user-defined model to provider default");
assert.equal(publicAutomatic.effectiveModel, "auto");
const written = catalog.writeSettings({ customModels: added.customModels, selectedModel: added.model.id, selectedReasoning: "high" }, storage, "private");
assert.equal(written.selectedModel, "company/research-model");
assert.equal(written.selectedReasoning, "high");
assert.equal(catalog.readSettings(storage, "private").customModels[0].id, "company/research-model");

const missing = catalog.selectionState("gpt-retired", runtime, []);
assert.equal(missing.unavailable, true);
assert.equal(missing.effectiveModel, "gpt-5.6-sol");
assert.deepEqual(
  Array.from(catalog.reasoningEffortsFor("auto", runtime, [])),
  ["low", "medium", "ultra"]
);

assert.equal(catalog.cleanModelId("bad model"), "");

async function testController() {
  let changes = 0;
  const statuses = [];
  const controllerValues = new Map();
  const controllerStorage = {
    getItem: (key) => controllerValues.has(key) ? controllerValues.get(key) : null,
    removeItem: (key) => controllerValues.delete(key),
    setItem: (key, value) => controllerValues.set(key, String(value)),
  };
  controllerValues.set("researchos-codex-runner-reasoning", "ultra");
  const controller = catalog.createController({
    client: { loadModelCatalog: async () => runtime },
    onChange: () => { changes += 1; },
    onStatus: (key) => statuses.push(key),
    publicStarter: () => false,
    storage: controllerStorage,
  });
  controller.initialize("private");
  assert.equal(controller.snapshot().selectedReasoning, "ultra", "legacy reasoning must migrate into the model preference owner");
  assert.equal(controllerValues.has("researchos-codex-runner-reasoning"), false);
  await controller.refresh({ rerender: false });
  assert.equal(controller.snapshot().selection.effectiveModel, "gpt-5.6-sol");
  assert.equal(controller.snapshot().selectedReasoning, "ultra", "a supported persisted effort must survive catalog refresh");
  controller.selectModel("gpt-5.5");
  assert.equal(controller.payloadModel(), "gpt-5.5");
  assert.equal(controller.snapshot().selectedReasoning, "auto", "unsupported reasoning effort must fall back safely");
  assert.equal(controller.add("company/next-model"), true);
  assert.equal(controller.payloadModel(), "company/next-model");
  controller.remove("company/next-model");
  assert.equal(controller.payloadModel(), "auto");
  assert.ok(changes >= 3);
  assert.ok(statuses.includes("workSessionModelSaved"));
}

testController()
  .then(() => console.log("model catalog tests passed"))
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
