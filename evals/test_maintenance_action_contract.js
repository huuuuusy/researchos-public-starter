/* ResearchOS maintenance header.
 * 中文：验证维护建议先进入今日处理；底层执行客户端仍只发送已登记 ID，不接受任意命令。
 * English: Verifies maintenance suggestions enter Today Work first while the low-level client still sends registered IDs only.
 */

"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const window = {
  ResearchOSRequestAuth: { resolveFetcher: (fetcher) => fetcher },
};
const context = vm.createContext({ window });
for (const relative of [
  "dashboard/src/services/command-list-workbench.js",
  "dashboard/src/services/maintenance-client.js",
]) {
  vm.runInContext(fs.readFileSync(path.join(root, relative), "utf8"), context);
}
const stewardshipSource = fs.readFileSync(path.join(root, "dashboard/src/plugins/system-stewardship.js"), "utf8");
assert.doesNotMatch(stewardshipSource, /runAutomaticUpdateIfNeeded/, "opening or binding maintenance must never start a refresh");
assert.match(stewardshipSource, /bindAutoUpdateResultEvents\(root, \{ onRun: \(\) => runAutoUpdate\(\) \}\)/);
assert.doesNotMatch(stewardshipSource, /data-run-maintenance-action|syncMaintenanceActionChrome/);
assert.doesNotMatch(stewardshipSource, /setInterval|setTimeout/, "the browser adapter must not become a scheduler");

let registeredStewardship = null;
let maintenanceRunCalls = 0;
let explicitRun = null;
const currentPlanState = {
  plan: { plan_id: "high-risk-plan", execution_allowed: true, requires_confirmation: true, auto_eligible_step_ids: ["safe-refresh"] },
};
const evolutionState = {
  accept(plan) { currentPlanState.plan = plan; },
  clear() {},
  async refresh() { return { loading: false, plan: currentPlanState.plan }; },
  snapshot() { return { loading: false, plan: currentPlanState.plan }; },
};
const maintenanceDocument = { getElementById: () => ({ open: false }) };
const autoUpdateResultRoot = { innerHTML: "" };
const maintenanceRoot = {
  querySelector(selector) {
    if (selector === "#utilityDrawer") return { open: false, addEventListener() {} };
    if (selector === "#autoUpdateResult") return autoUpdateResultRoot;
    return null;
  },
};
const stewardshipWindow = {
  ResearchOSCommandListWorkbenchService: {},
  ResearchOSExternalEvidenceView: {},
  ResearchOSMaintenanceClient: {
    createEvolutionPlanState: () => evolutionState,
    async runAutoUpdate() {
      maintenanceRunCalls += 1;
      return { ok: true, plan: currentPlanState.plan };
    },
  },
  ResearchOSMaintenanceView: {
    autoUpdateStatus: () => "",
    renderAutoUpdateResultHtml: () => "",
  },
  ResearchOSMaintenanceWorkbenchService: {
    bindAutoUpdateButton() {},
    bindAutoUpdateResultEvents(_root, { onRun }) { explicitRun = onRun; },
    focusAutoUpdateResult() {},
    syncAutoUpdateChrome() {},
  },
  ResearchOSPluginRuntime: {
    registerOwnedAdapter(_pluginId, _id, adapter) { registeredStewardship = adapter; },
  },
  ResearchOSServiceMode: {},
  document: maintenanceDocument,
};
vm.runInContext(stewardshipSource, vm.createContext({ window: stewardshipWindow }));
registeredStewardship.bind({
  context: {
    document: maintenanceDocument,
    publicStarter: () => false,
    reloadDashboard: async () => {},
    serverMode: () => true,
    translate: (key) => key,
  },
  model: { actions: { run_auto_update: {} }, payloads: {} },
  root: maintenanceRoot,
});

const html = window.ResearchOSCommandListWorkbenchService.renderCommandListHtml(
  { commands: [{ id: "check_stale_context", label: "检查时效", command: "python3 scripts/check_stale_context.py" }] },
  { escapeHtml: String, queueAvailable: true, publicMode: false, translate: (key) => key }
);
assert.match(html, /data-action-kind="navigation" data-queue-maintenance-suggestion="check_stale_context"/);
assert.match(html, /data-maintenance-suggestion-status/);
assert.doesNotMatch(html, /python3|data-run-maintenance-action|data-copy-maintenance-command/);
const publicHtml = window.ResearchOSCommandListWorkbenchService.renderCommandListHtml(
  { commands: [{ id: "check_stale_context", label: "检查时效", command: "python3 scripts/check_stale_context.py" }] },
  { escapeHtml: String, queueAvailable: false, publicMode: true, translate: (key) => key }
);
assert.match(publicHtml, /data-queue-maintenance-suggestion="check_stale_context" disabled/);
assert.doesNotMatch(publicHtml, /python3|data-run-maintenance-action|data-copy-maintenance-command/);

let clickHandler = null;
const button = {
  dataset: { queueMaintenanceSuggestion: "check_stale_context" },
  addEventListener: (_name, handler) => { clickHandler = handler; },
};
let selectedAction = "";
window.ResearchOSCommandListWorkbenchService.bindCommandListEvents(
  { querySelectorAll: (selector) => selector === "[data-queue-maintenance-suggestion]" ? [button] : [] },
  { onQueue: ({ actionId }) => { selectedAction = actionId; } }
);
clickHandler({ preventDefault() {} });
assert.equal(selectedAction, "check_stale_context");

const suggestion = window.ResearchOSCommandListWorkbenchService.maintenanceSuggestionModel(
  { id: "check_stale_context", label: "检查时效", command: "python3 scripts/check_stale_context.py" },
  { health: { stale_context: { stale: ["old.md"] } } },
  { translate: (key) => key },
);
assert.equal(suggestion.actionId, "check_stale_context");
assert.equal(suggestion.recommended, true);

(async () => {
  const calls = [];
  const result = await window.ResearchOSMaintenanceClient.runMaintenanceAction("check_stale_context", {
    fetcher: async (url, init) => {
      calls.push({ url, init });
      return { ok: true, async json() { return { ok: true, steps: [] }; } };
    },
  });
  assert.equal(result.ok, true);
  assert.equal(calls[0].url, "/maintenance-action");
  assert.deepEqual(JSON.parse(calls[0].init.body), { action_id: "check_stale_context" });
  assert.equal(Object.hasOwn(JSON.parse(calls[0].init.body), "command"), false);
  await Promise.resolve();
  await Promise.resolve();
  assert.equal(maintenanceRunCalls, 0, "binding the dashboard must never auto-run maintenance");
  assert.equal(typeof explicitRun, "function", "the rendered maintenance button must bind an explicit run action");
  currentPlanState.plan = { ...currentPlanState.plan, plan_id: "safe-plan", requires_confirmation: false };
  await explicitRun();
  assert.equal(maintenanceRunCalls, 1, "maintenance should run once after the user activates the explicit control");

  console.log("Maintenance action contract passed.");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
