/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「state」；供 app、service、view 复用。
 * English: Browser-side core primitive for state in the ResearchOS dashboard; shared by app, services, and views.
 */

(function attachResearchOSStatePolicy(global) {
  const durableStateBoundary = global.ResearchOSContracts?.durableStateBoundary || Object.freeze({
    activeContext: Object.freeze([]),
    canonicalMarkdown: Object.freeze([]),
    localStorage: Object.freeze([]),
  });

  const storageNamespaces = Object.freeze({
    dashboard: "researchos-dashboard",
    assistant: "researchos-assistant",
    context: "researchos-context",
    inbox: "researchos-unified-inbox",
  });

  const localOnlyStateKinds = durableStateBoundary.localStorage;
  const activeContextStateKinds = durableStateBoundary.activeContext;
  const canonicalStateKinds = durableStateBoundary.canonicalMarkdown;

  function storageKey(namespace, name) {
    const prefix = storageNamespaces[namespace] || String(namespace || "researchos");
    return `${prefix}-${String(name || "state")}`;
  }

  function readJsonObject(key, fallback = {}, storage = global.localStorage) {
    try {
      const parsed = JSON.parse(storage.getItem(key) || "{}");
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : fallback;
    } catch {
      return fallback;
    }
  }

  function writeJsonObject(key, value = {}, storage = global.localStorage) {
    const safeValue = value && typeof value === "object" && !Array.isArray(value) ? value : {};
    storage.setItem(key, JSON.stringify(safeValue));
  }

  function readJsonArray(key, { objectOnly = true, storage = global.localStorage } = {}) {
    try {
      const parsed = JSON.parse(storage.getItem(key) || "[]");
      if (!Array.isArray(parsed)) return [];
      return objectOnly ? parsed.filter((item) => item && typeof item === "object") : parsed;
    } catch {
      return [];
    }
  }

  function writeJsonArray(key, items = [], { limit = 80, storage = global.localStorage } = {}) {
    const safeItems = Array.isArray(items) ? items : [];
    const boundedItems = Number.isFinite(limit) ? safeItems.slice(0, limit) : safeItems;
    storage.setItem(key, JSON.stringify(boundedItems));
  }

  global.ResearchOSStatePolicy = Object.freeze({
    durableStateBoundary,
    storageNamespaces,
    localOnlyStateKinds,
    activeContextStateKinds,
    canonicalStateKinds,
    storageKey,
    readJsonObject,
    writeJsonObject,
    readJsonArray,
    writeJsonArray,
  });
})(window);
