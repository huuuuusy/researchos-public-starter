/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「view state」；供 app、service、view 复用。
 * English: Browser-side core primitive for view state in the ResearchOS dashboard; shared by app, services, and views.
 */

(function attachResearchOSViewState(global) {
  const SurfaceContract = global.ResearchOSSurfaceContract || {};
  const workspaceTabs = SurfaceContract.workspaceTabs || Object.freeze([]);
  const unifiedInboxViews = Object.freeze(["active", "archived", "all"]);
  const workFilters = Object.freeze(["ready", "active", "waiting", "needs_review", "done", "all"]);

  const storageKeys = Object.freeze({
    workspaceTab: "researchos-workspace-tab",
    unifiedInboxView: "researchos-unified-inbox-view",
  });

  const defaults = Object.freeze({
    workspaceTab: "now",
    unifiedInboxView: "active",
    workFilter: "active",
  });

  function normalizeChoice(value, choices, fallback) {
    const text = String(value || "").trim();
    return choices.includes(text) ? text : fallback;
  }

  function normalizeWorkspaceTab(value) {
    const canonical = SurfaceContract.canonicalSurface?.(value) || "";
    return normalizeChoice(canonical, workspaceTabs, defaults.workspaceTab);
  }

  function normalizeUnifiedInboxView(value) {
    return normalizeChoice(value, unifiedInboxViews, defaults.unifiedInboxView);
  }

  function normalizeWorkFilter(value) {
    return normalizeChoice(value, workFilters, defaults.workFilter);
  }

  function read(storage = global.localStorage) {
    return {
      workspaceTab: normalizeWorkspaceTab(storage.getItem(storageKeys.workspaceTab)),
      unifiedInboxView: normalizeUnifiedInboxView(storage.getItem(storageKeys.unifiedInboxView)),
    };
  }

  function writeStateValue(name, value, normalizer = (item) => String(item || "").trim(), storage = global.localStorage) {
    const next = normalizer(value);
    storage.setItem(storageKeys[name], next);
    return next;
  }

  function writeWorkspaceTab(value, storage = global.localStorage) {
    return writeStateValue("workspaceTab", value, normalizeWorkspaceTab, storage);
  }

  function writeUnifiedInboxView(value, storage = global.localStorage) {
    return writeStateValue("unifiedInboxView", value, normalizeUnifiedInboxView, storage);
  }

  global.ResearchOSViewState = Object.freeze({
    storageKeys,
    defaults,
    workspaceTabs,
    unifiedInboxViews,
    workFilters,
    read,
    normalizeWorkspaceTab,
    normalizeUnifiedInboxView,
    normalizeWorkFilter,
    writeWorkspaceTab,
    writeUnifiedInboxView,
  });
})(window);
