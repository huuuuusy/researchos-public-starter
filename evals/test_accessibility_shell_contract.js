const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const profileWindow = {};
vm.runInContext(read("dashboard/src/core/surface-contract.js"), vm.createContext({ window: profileWindow }));
const surfaceContract = profileWindow.ResearchOSSurfaceContract;
const workspaceIds = Array.from(surfaceContract.canonicalSurfaceIds);

function classList() {
  const values = new Set();
  return {
    add(value) { values.add(value); },
    remove(value) { values.delete(value); },
    toggle(value, enabled) { enabled ? values.add(value) : values.delete(value); },
    contains(value) { return values.has(value); },
  };
}

function node({ id = "", panel = "", tab = "" } = {}) {
  const attributes = new Map();
  const value = {
    attributes,
    classList: classList(),
    dataset: {},
    hidden: false,
    id,
    innerHTML: "",
    tagName: "SECTION",
    focusOptions: null,
    scrollOptions: null,
    closest() { return this.panelOwner || null; },
    focus(options) { this.focusOptions = options || {}; },
    hasAttribute(name) { return attributes.has(name); },
    removeAttribute(name) { attributes.delete(name); },
    scrollIntoView(options) { this.scrollOptions = options; },
    setAttribute(name, entry) { attributes.set(name, String(entry)); },
  };
  if (panel) value.dataset.workspacePanel = panel;
  if (tab) value.dataset.workspaceTab = tab;
  return value;
}

let reducedMotion = false;
const scheduled = [];
const tabs = workspaceIds.map((tab) => node({ tab }));
tabs.forEach((tab) => { tab.tagName = "BUTTON"; });
const panels = workspaceIds.map((panel) => node({ panel }));
const switcher = node({ id: "switcher" });
const launcher = node({ id: "launcher" });
launcher.dataset.openWorkspace = surfaceContract.canonicalSurface("review") || "review";
const document = {
  documentElement: { dataset: {} },
  getElementById(id) { return this.byId?.[id] || null; },
  querySelector(selector) { return selector === ".workspace-switcher" ? switcher : null; },
  querySelectorAll(selector) {
    if (selector === "button[data-workspace-tab]") return tabs;
    if (selector === "[data-workspace-panel]") return panels;
    if (selector === "[data-open-workspace]") return [launcher];
    return [];
  },
};
const context = {
  console,
  document,
  matchMedia: () => ({ matches: reducedMotion }),
  scrollTo() {},
  setTimeout(callback) { scheduled.push(callback); return scheduled.length; },
};
context.window = context;
vm.runInNewContext(read("dashboard/src/core/interactions.js"), context);
vm.runInNewContext(read("dashboard/src/core/ui.js"), context);
vm.runInNewContext(read("dashboard/src/services/workspace-shell-workbench.js"), context);

const interactions = context.ResearchOSInteractions;
const shell = context.ResearchOSWorkspaceShellWorkbenchService;
const scrollTarget = node();
interactions.scrollIntoView(scrollTarget, { behavior: "smooth", block: "start" });
assert.equal(scrollTarget.scrollOptions.behavior, "smooth");
reducedMotion = true;
interactions.scrollIntoView(scrollTarget, { behavior: "smooth", block: "start" });
assert.equal(scrollTarget.scrollOptions.behavior, "auto", "reduced motion must override imperative smooth scrolling");

shell.syncWorkspaceShell(document, {
  focusMode: "panel",
  hintFor: (value) => `${value} hint`,
  labelFor: (value) => value,
  scroll: true,
  selectedWorkspace: "library",
});
assert.equal(tabs[1].attributes.get("aria-selected"), "true");
assert.equal(tabs[1].attributes.get("tabindex"), "0");
assert.equal(tabs[0].attributes.get("tabindex"), "-1");
assert.equal(panels[0].hidden, true);
assert.equal(panels[1].hidden, false);
scheduled.shift()();
assert.equal(panels[1].focusOptions?.preventScroll, true, "cross-screen actions must focus the destination panel");

const activations = [];
shell.bindWorkspaceTabs(document, {
  onWorkspaceTab(payload) { activations.push(payload); },
});
let prevented = false;
tabs[1].onkeydown({ key: "ArrowRight", preventDefault() { prevented = true; } });
assert.equal(prevented, true);
assert.equal(activations.at(-1).tabId, workspaceIds[(1 + 1) % workspaceIds.length]);
assert.equal(activations.at(-1).focusMode, "tab");
tabs[0].onkeydown({ key: "ArrowLeft", preventDefault() {} });
assert.equal(activations.at(-1).tabId, workspaceIds.at(-1), "arrow navigation must wrap across the active profile workspaces");

const launches = [];
shell.bindWorkspaceLaunchers(document, { onWorkspace(payload) { launches.push(payload); } });
launcher.onclick({ type: "click" });
assert.equal(launches.at(-1).workspace, launcher.dataset.openWorkspace);
assert.equal(launches.at(-1).focusMode, "panel", "content launchers must move focus into the destination panel");
assert.equal(launches.at(-1).scroll, true);

const panel = node();
const target = node({ id: "target" });
target.panelOwner = panel;
document.byId = { target };
shell.focusDashboardTarget(document, "target");
assert.equal(target.attributes.get("tabindex"), "-1");
assert.equal(target.focusOptions?.preventScroll, true);
assert.equal(panel.scrollOptions.behavior, "auto", "section focus must also honor reduced motion");

const index = read("dashboard/index.html");
assert.match(index, /class="workspace-switcher"[\s\S]*?role="tablist"/);
for (const surface of workspaceIds) {
  assert.ok(index.includes(`id="workspace-tab-${surface}" role="tab" aria-controls="workspace-panel-${surface}"`));
  assert.match(index, new RegExp(`id="workspace-panel-${surface}" role="tabpanel" aria-labelledby="workspace-tab-${surface}"`));
}
assert.ok(read("dashboard/styles/base.css").includes("prefers-reduced-motion: reduce"));
assert.ok(read("dashboard/styles/shell/workspace.css").includes(".workspace-panel:focus-visible"));
const uiCopy = read("dashboard/src/core/ui-copy.js");
assert.equal(uiCopy.includes("staged in Work"), false, "live task feedback must not restore retired Work-screen vocabulary");
assert.equal(/scrollIntoView\??\.\(\{[^\n]*behavior:\s*"smooth"/.test(
  fs.readdirSync(path.join(root, "dashboard/src/services"))
    .filter((name) => name.endsWith(".js"))
    .map((name) => read(`dashboard/src/services/${name}`))
    .join("\n"),
), false, "services must route imperative smooth scrolling through the reduced-motion primitive");

console.log("Accessibility shell behavior contract checks passed.");
