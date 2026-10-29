const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const source = fs.readFileSync(path.join(root, "dashboard/src/services/plugin-runtime.js"), "utf8");
const warnings = [];
const context = { console: { ...console, warn: (...args) => warnings.push(args) } };
context.window = context;
vm.runInNewContext(source, context);

const runtime = context.ResearchOSPluginRuntime;
assert.equal(runtime.registerWorkItemAdapter("fixture", "fixture_items", {
  project: ({ payload }) => ({ schema_id: "researchos-work-item-projection-v1", version: "1", items: [{ id: "fixture-item", payload }] }),
}), true);
assert.equal(runtime.registerWorkItemAdapter("fixture", "fixture_items", { project: () => ({}) }), false, "a plugin cannot replace its registered WorkItem adapter");
const disabledData = {
  plugins: {
    schema_id: "researchos-plugin-v1",
    core_api_version: "1",
    loaded: [],
    contributions: { actions: [], projections: [], work_item_providers: [], ui_slots: [] },
  },
};
assert.deepEqual(Array.from(runtime.slotModels(disabledData, "utility")), [], "disabled plugins must produce no Utility slot models");
assert.deepEqual(Array.from(runtime.slotModels({ plugins: { ...disabledData.plugins, core_api_version: "1.1" } }, "utility")), [], "the browser must reject undeclared core API versions exactly like the builder");

const enabledData = {
  generated_at: "2026-08-13T00:00:00Z",
  health: { validation: { ok: true } },
  runtime_mode: "private",
  plugins: {
    schema_id: "researchos-plugin-v1",
    core_api_version: "1",
    loaded: [{ id: "fixture", version: "1.0.0" }],
    contributions: {
      actions: [{ id: "run_check", handler: "registered_check", surface: "overlay", plugin_id: "fixture", plugin_version: "1.0.0" }],
      projections: [{ id: "health", source: "health", plugin_id: "fixture", plugin_version: "1.0.0", schema_id: "researchos-projection-envelope-v1", version: "1", sensitivity: "local_only", freshness: "snapshot", export_fields: ["$"] }],
      work_item_providers: [{
        id: "fixture_items",
        projection_id: "health",
        adapter: "fixture_items",
        optional: false,
        plugin_id: "fixture",
        plugin_version: "1.1.0",
      }],
      ui_slots: [{
        id: "fixture_utility",
        slot: "utility",
        surface: "overlay",
        region: "utility",
        adapter: "fixture",
        order: 10,
        projection_ids: ["health"],
        action_ids: ["run_check"],
        title: "Fixture",
        hint: "Fixture hint",
        plugin_id: "fixture",
        plugin_version: "1.0.0",
      }],
    },
  },
};

const models = runtime.slotModels(enabledData, "utility");
assert.equal(models.length, 1);
assert.equal(models[0].payloads.health.validation.ok, true, "projection paths must resolve from the dashboard payload");
assert.equal(models[0].projections.health.schema_id, "researchos-projection-envelope-v1");
assert.equal(models[0].projections.health.freshness.state, "known");
assert.equal(models[0].actions.run_check.handler, "registered_check", "slots must receive only their declared actions");
assert.equal(runtime.workItemProviderModels(enabledData)[0].projection.items[0].payload.validation.ok, true, "work-item providers must execute their declared adapter over only the owned projection");
assert.equal(runtime.workItemProviderModels(enabledData)[0].projection.schema_id, "researchos-work-item-projection-v1");
assert.equal(runtime.valueAtPath(enabledData, "../private"), undefined, "unsafe projection paths must fail closed");
const fieldProjection = {
  ...enabledData.plugins.contributions.projections[0],
  export_fields: ["validation.ok"],
};
const fieldEnvelope = runtime.projectionEnvelope({ ...enabledData, health: { validation: { ok: true, secret: "hidden" }, sibling: "hidden" } }, fieldProjection);
assert.deepEqual(JSON.parse(JSON.stringify(fieldEnvelope.payload)), { validation: { ok: true } }, "field export maps must omit undeclared sibling data");
assert.equal(runtime.projectionEnvelope(enabledData, { ...fieldProjection, version: "2" }).error, "unsupported_projection_contract");
assert.equal(runtime.projectionEnvelope({ ...enabledData, generated_at: "" }, fieldProjection).error, "freshness_unknown");
assert.equal(runtime.projectionEnvelope({ ...enabledData, runtime_mode: "public_starter" }, { ...fieldProjection, sensitivity: "private" }).error, "sensitivity_denied");
const crossSurfaceData = structuredClone(enabledData);
crossSurfaceData.plugins.contributions.actions[0].surface = "start";
assert.deepEqual(Object.keys(runtime.slotModels(crossSurfaceData, "utility")[0].actions), [], "an action declared on another canonical surface must fail closed at the slot host");

const collisionData = structuredClone(enabledData);
collisionData.asset_payload = { owner: "asset" };
collisionData.system_payload = { owner: "system" };
collisionData.plugins.loaded.push({ id: "system", version: "1.0.0" });
collisionData.plugins.contributions.projections = [
  { ...enabledData.plugins.contributions.projections[0], contribution_key: "fixture:health", source: "asset_payload" },
  { ...enabledData.plugins.contributions.projections[0], contribution_key: "system:health", source: "system_payload", plugin_id: "system" },
];
collisionData.plugins.contributions.ui_slots = [
  { ...enabledData.plugins.contributions.ui_slots[0], projection_ids: ["health"] },
  { id: "system_utility", slot: "utility", surface: "overlay", region: "utility", adapter: "system", order: 11, projection_ids: ["health"], action_ids: [], plugin_id: "system" },
];
const collisionModels = runtime.slotModels(collisionData, "utility");
assert.equal(collisionModels[0].payloads.health.owner, "asset", "bare projection ids must resolve inside the slot's plugin namespace");
assert.equal(collisionModels[1].payloads.health.owner, "system", "a sibling plugin must receive its own same-named projection");
assert.notEqual(runtime.contributionKey(collisionData.plugins.contributions.projections[0]), runtime.contributionKey(collisionData.plugins.contributions.projections[1]));
collisionData.plugins.contributions.work_item_providers = [
  { id: "fixture_items", projection_id: "health", adapter: "fixture_items", optional: false, plugin_id: "fixture" },
  { id: "system_items", projection_id: "health", adapter: "system_items", optional: false, plugin_id: "system" },
];
assert.equal(runtime.registerWorkItemAdapter("system", "system_items", {
  project: ({ payload }) => ({ schema_id: "researchos-work-item-projection-v1", version: "1", items: [{ id: "system-item", payload }] }),
}), true);
const collisionProviders = runtime.workItemProviderModels(collisionData);
assert.equal(collisionProviders[0].projection.items[0].payload.owner, "asset", "work items must not attach a sibling plugin's same-named projection");
assert.equal(collisionProviders[1].projection.items[0].payload.owner, "system");
assert.equal(runtime.unregisterWorkItemAdapter("system", "system_items", "fixture"), false, "a sibling owner cannot remove a WorkItem adapter");
assert.equal(runtime.unregisterWorkItemAdapter("system", "system_items", "system"), true);
const missingAdapterData = structuredClone(enabledData);
missingAdapterData.plugins.contributions.work_item_providers[0].adapter = "missing_adapter";
assert.equal(runtime.workItemProviderModels(missingAdapterData)[0].projection.error, "adapter_unavailable");
assert.equal(runtime.workItemProviderModels(missingAdapterData)[0].projection.items.length, 0, "a missing adapter must fail closed instead of exposing raw payload items");
assert.equal(runtime.registerWorkItemAdapter("fixture", "broken_items", { project: () => { throw new Error("broken work item fixture"); } }), true);
const brokenProviderData = structuredClone(enabledData);
brokenProviderData.plugins.contributions.work_item_providers[0].adapter = "broken_items";
assert.equal(runtime.workItemProviderModels(brokenProviderData)[0].projection.error, "adapter_failed");
warnings.length = 0;
collisionData.plugins.contributions.candidate_types = [
  { id: "shared_candidate", plugin_id: "fixture" },
  { id: "shared_candidate", plugin_id: "system" },
];
assert.equal(runtime.candidateContribution(collisionData, "shared_candidate"), null, "ambiguous global candidate dispatch ids must fail closed");

let bound = false;
assert.equal(runtime.registerAdapter("fixture", {
  render: (model) => `<section>${model.title}</section>`,
  bind: ({ model }) => { bound = model.id === "fixture_utility"; },
}), true);
assert.equal(runtime.registerAdapter("fixture", { render: () => "duplicate" }), false, "adapter ids cannot be overwritten");

const host = {
  hidden: true,
  innerHTML: "stale",
  querySelector(selector) {
    return selector.includes("fixture_utility") ? { dataset: { pluginSlotInstance: "fixture_utility" } } : null;
  },
};
const receipt = runtime.renderSlots({ data: enabledData, host, slot: "utility" });
assert.deepEqual(Array.from(receipt.rendered), ["fixture_utility"]);
assert.ok(host.innerHTML.includes("Fixture"));
assert.equal(host.hidden, false);
assert.equal(bound, true);

let lifecycleMounts = 0;
let lifecycleUpdates = 0;
let lifecycleDisposals = 0;
assert.equal(runtime.registerOwnedAdapter("fixture", "lifecycle", {
  render: (model) => `<section>${model.title}</section>`,
  mount: () => {
    lifecycleMounts += 1;
    return {
      update: () => { lifecycleUpdates += 1; },
      dispose: () => { lifecycleDisposals += 1; },
    };
  },
}), true);
assert.equal(runtime.registerOwnedAdapter("fixture", "lifecycle", { render: () => "duplicate" }), false, "a plugin cannot replace its owned adapter");
const lifecycleData = structuredClone(enabledData);
lifecycleData.plugins.contributions.ui_slots[0].adapter = "lifecycle";
let lifecycleHtml = "";
let lifecycleWrites = 0;
const lifecycleRoot = { dataset: { pluginSlotInstance: "fixture_utility" } };
const lifecycleHost = {
  hidden: true,
  get innerHTML() { return lifecycleHtml; },
  set innerHTML(value) { lifecycleWrites += 1; lifecycleHtml = value; },
  querySelector: () => lifecycleRoot,
};
const mountedReceipt = runtime.renderSlots({ data: lifecycleData, host: lifecycleHost, slot: "utility", context: { generation: 1 } });
assert.equal(mountedReceipt.updated, false);
assert.equal(lifecycleMounts, 1);
const updatedReceipt = runtime.renderSlots({ data: lifecycleData, host: lifecycleHost, slot: "utility", context: { generation: 2 } });
assert.equal(updatedReceipt.updated, true, "an unchanged owned slot must update its mounted controller without replacing the DOM");
assert.equal(lifecycleUpdates, 1);
assert.equal(lifecycleWrites, 1);
runtime.renderSlots({ data: disabledData, host: lifecycleHost, slot: "utility" });
assert.equal(lifecycleDisposals, 1, "disabling a plugin must dispose its mounted controller");
assert.equal(lifecycleWrites, 2);
assert.equal(runtime.unregisterOwnedAdapter("fixture", "lifecycle", "sibling"), false, "a sibling owner cannot unregister another plugin's adapter");
assert.equal(runtime.unregisterOwnedAdapter("fixture", "lifecycle", "fixture"), true);

assert.equal(runtime.registerOwnedAdapter("fixture", "shared", { render: () => "<p>Fixture owned</p>" }), true);
assert.equal(runtime.registerOwnedAdapter("system", "shared", { render: () => "<p>System owned</p>" }), true);
const ownedCollisionData = structuredClone(collisionData);
ownedCollisionData.plugins.contributions.ui_slots = [
  { id: "fixture_owned", slot: "utility", surface: "overlay", region: "utility", adapter: "shared", order: 1, projection_ids: [], action_ids: [], plugin_id: "fixture" },
  { id: "system_owned", slot: "utility", surface: "overlay", region: "utility", adapter: "shared", order: 2, projection_ids: [], action_ids: [], plugin_id: "system" },
];
const ownedCollisionHost = {
  hidden: true,
  innerHTML: "",
  querySelector: () => null,
};
runtime.renderSlots({ data: ownedCollisionData, host: ownedCollisionHost, slot: "utility" });
assert.ok(ownedCollisionHost.innerHTML.includes("Fixture owned"));
assert.ok(ownedCollisionHost.innerHTML.includes("System owned"), "same adapter ids must remain isolated by plugin namespace");

assert.equal(runtime.registerOwnedAdapter("fixture", "invalid_mount", {
  render: () => "<p>Invalid controller</p>",
  mount: () => ({ dispose() {} }),
}), true);
const invalidMountData = structuredClone(enabledData);
invalidMountData.plugins.contributions.ui_slots[0].adapter = "invalid_mount";
warnings.length = 0;
const invalidMountReceipt = runtime.renderSlots({ data: invalidMountData, host, slot: "utility" });
assert.deepEqual(Array.from(invalidMountReceipt.errors), ["fixture_utility"], "mount controllers without update and dispose must fail closed with one bounded error");
assert.equal(warnings.length, 1);

assert.equal(runtime.registerAdapter("broken", {
  render: () => { throw new Error("fixture render failure"); },
}), true);
assert.equal(runtime.registerAdapter("healthy", {
  render: () => "<section>Healthy</section>",
}), true);
warnings.length = 0;
const isolationData = structuredClone(enabledData);
isolationData.plugins.contributions.ui_slots = [
  { id: "broken_slot", slot: "utility", surface: "overlay", region: "utility", adapter: "broken", order: 1, projection_ids: [], action_ids: [] },
  { id: "healthy_slot", slot: "utility", surface: "overlay", region: "utility", adapter: "healthy", order: 2, projection_ids: [], action_ids: [] },
];
const isolationHost = {
  hidden: true,
  innerHTML: "",
  querySelector(selector) {
    const match = selector.match(/data-plugin-slot-instance="([^"]+)"/);
    return match ? { dataset: { pluginSlotInstance: match[1] } } : null;
  },
};
const isolationReceipt = runtime.renderSlots({ data: isolationData, host: isolationHost, slot: "utility" });
assert.deepEqual(Array.from(isolationReceipt.errors), ["broken_slot"], "plugin failures must be reported without stopping sibling slots");
assert.deepEqual(Array.from(isolationReceipt.rendered), ["healthy_slot"], "healthy sibling plugins must still render");
assert.ok(isolationHost.innerHTML.includes("Healthy"));
assert.equal(warnings.length, 1, "isolated plugin failures must produce one bounded diagnostic");

runtime.renderSlots({ data: disabledData, host, slot: "utility" });
assert.equal(host.innerHTML, "", "disabling a plugin must remove its rendered Utility content");
assert.equal(host.hidden, true, "disabling every Utility plugin must hide the host without an empty entry");

assert.equal(runtime.registerSurfaceDependency("work", "fixtureDependency", {
  pluginId: "fixture",
  provide: ({ context }) => context.value,
}), true);
assert.equal(runtime.registerSurfaceDependency("work", "fixtureDependency", {
  pluginId: "fixture",
  provide: () => "duplicate",
}), false, "surface dependency ids cannot be overwritten");
assert.equal(runtime.resolveSurfaceDependencies({ data: disabledData, surface: "work", context: { value: 7 } }).fixtureDependency, undefined);
assert.equal(runtime.resolveSurfaceDependencies({ data: enabledData, surface: "work", context: { value: 7 } }).fixtureDependency, 7);

console.log("OK: plugin runtime assembles reviewed slots and removes disabled contributions without orphan UI");
