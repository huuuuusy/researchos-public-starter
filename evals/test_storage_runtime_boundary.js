/* ResearchOS maintenance header.
 * 中文：验证浏览器本地状态不会跨 private、personal-vault 与 public-starter 运行模式泄漏。
 * English: Verifies browser-local state cannot leak across private, personal-vault, and public-starter modes.
 */

"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function memoryStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    get length() { return values.size; },
    clear() { values.clear(); },
    getItem(key) { return values.has(String(key)) ? values.get(String(key)) : null; },
    key(index) { return Array.from(values.keys())[Number(index)] || null; },
    removeItem(key) { values.delete(String(key)); },
    setItem(key, value) { values.set(String(key), String(value)); },
  };
}

function loadContract(storage, search = "") {
  const window = {
    document: { documentElement: { setAttribute() {} } },
    localStorage: storage,
    location: { search },
  };
  const source = fs.readFileSync(path.join(__dirname, "..", "dashboard", "src", "core", "storage-contract.js"), "utf8");
  vm.runInNewContext(source, { Map, Set, URLSearchParams, window });
  return window.ResearchOSStorageContract;
}

function loadRuntimeProfile(window) {
  const source = fs.readFileSync(path.join(__dirname, "..", "dashboard", "src", "core", "edition-profile.js"), "utf8");
  vm.runInNewContext(source, { window });
  return window.ResearchOSEditionProfile;
}

function loadUiPreferences(storage, dataset = undefined) {
  const window = { localStorage: storage, document: dataset ? { documentElement: { dataset } } : undefined };
  loadRuntimeProfile(window);
  const source = fs.readFileSync(path.join(__dirname, "..", "dashboard", "src", "core", "ui-preferences.js"), "utf8");
  vm.runInNewContext(source, { window });
  return window.ResearchOSUiPreferences;
}

// index.html's root element carries the edition defaults; a missing or invalid attribute falls back to the public starter.
const bareProfile = loadRuntimeProfile({});
assert.equal(bareProfile.clientProfileId, "public_explanatory_v1");
assert.equal(bareProfile.defaultLanguage, "en");
assert.equal(bareProfile.serverUrl, "http://127.0.0.1:8880/");
const declaredProfile = loadRuntimeProfile({ document: { documentElement: { dataset: {
  clientProfile: "private_compact_v1", defaultLanguage: "zh-CN", serverUrl: "http://127.0.0.1:8878/",
} } } });
assert.equal(declaredProfile.clientProfileId, "private_compact_v1");
assert.equal(declaredProfile.defaultLanguage, "zh-CN");
assert.equal(declaredProfile.serverUrl, "http://127.0.0.1:8878/");
assert.equal(loadRuntimeProfile({ document: { documentElement: { dataset: { defaultLanguage: "fr", serverUrl: " " } } } }).defaultLanguage, "en");
assert.equal(loadRuntimeProfile({ document: { documentElement: { dataset: { serverUrl: " " } } } }).serverUrl, "http://127.0.0.1:8880/");
assert.equal(loadUiPreferences(memoryStorage({})).read().language, "en", "without a declared default the dashboard opens in English");
assert.equal(loadUiPreferences(memoryStorage({}), { defaultLanguage: "zh-CN" }).read().language, "zh-CN");

const privateStorage = memoryStorage({
  "researchos-unified-inbox-archive": "private-work",
  "researchos-dashboard-language": "zh-CN",
});
const privateContract = loadContract(privateStorage);
assert.equal(privateContract.ensureRuntimeStorageBoundary("private_vault"), false);
assert.equal(privateStorage.getItem("researchos-unified-inbox-archive"), "private-work");

const publicStorage = memoryStorage({
  "researchos-unified-inbox-archive": "private-work",
  "researchos-dashboard-language": "zh-CN",
});
const publicContract = loadContract(publicStorage);
assert.equal(publicContract.ensureRuntimeStorageBoundary("public_starter"), true);
assert.equal(publicStorage.getItem("researchos-unified-inbox-archive"), null);
assert.equal(publicStorage.getItem("researchos-dashboard-language"), "zh-CN");
assert.equal(publicContract.ensureRuntimeStorageBoundary("public_starter"), false);

publicStorage.setItem("researchos-material-intake-inbox", "public-work");
assert.equal(publicContract.ensureRuntimeStorageBoundary("personal_vault"), true);
assert.equal(publicStorage.getItem("researchos-material-intake-inbox"), null);

const cleanContract = loadContract(memoryStorage({ "researchos-unified-inbox-archive": "ignored" }), "?researchos_clean_state=1");
assert.ok(cleanContract.cleanStateStorage);
assert.equal(cleanContract.ensureRuntimeStorageBoundary("public_starter"), false);
assert.equal(cleanContract.cleanStateStorage.getItem(cleanContract.runtimeModeStorageKey), "public_starter");

const damagedPreferences = memoryStorage({
  "researchos-dashboard-language": "broken-language",
  "researchos-dashboard-theme": "broken-theme",
});
const preferences = loadUiPreferences(damagedPreferences);
const recovered = preferences.read();
assert.equal(recovered.language, preferences.defaults.dashboardLanguage);
assert.equal(recovered.theme, preferences.defaults.dashboardTheme);
assert.equal(preferences.writeLanguage("broken-language", damagedPreferences), preferences.defaults.dashboardLanguage);
assert.equal(preferences.writeTheme("broken-theme", damagedPreferences), preferences.defaults.dashboardTheme);

// A browser that blocks site data throws on any localStorage access; the contract swaps in memory storage
// before other scripts read it, so the dashboard still starts instead of stopping at the first read.
const blockedWindow = {
  document: { documentElement: { attributes: {}, setAttribute(name, value) { this.attributes[name] = value; } } },
  location: { search: "" },
};
Object.defineProperty(blockedWindow, "localStorage", {
  configurable: true,
  get() { throw new Error("SecurityError: site data blocked"); },
});
vm.runInNewContext(
  fs.readFileSync(path.join(__dirname, "..", "dashboard", "src", "core", "storage-contract.js"), "utf8"),
  { Map, Set, URLSearchParams, window: blockedWindow },
);
blockedWindow.localStorage.setItem("researchos-dashboard-language", "en");
assert.equal(blockedWindow.localStorage.getItem("researchos-dashboard-language"), "en");
assert.equal(blockedWindow.document.documentElement.attributes["data-researchos-clean-state"], "blocked-memory-storage");
assert.equal(blockedWindow.ResearchOSStorageContract.ensureRuntimeStorageBoundary("public_starter"), false);

console.log("Storage runtime boundary regression passed.");
