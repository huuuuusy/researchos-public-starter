/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「storage contract」；供 app、service、view 复用。
 * English: Browser-side core primitive for storage contract in the ResearchOS dashboard; shared by app, services, and views.
 */

(function attachResearchOSStorageContract(global) {
  function createMemoryStorage() {
    const values = new Map();
    return {
      get length() {
        return values.size;
      },
      clear() {
        values.clear();
      },
      getItem(key) {
        const normalizedKey = String(key || "");
        return values.has(normalizedKey) ? values.get(normalizedKey) : null;
      },
      key(index) {
        return Array.from(values.keys())[Number(index)] || null;
      },
      removeItem(key) {
        values.delete(String(key || ""));
      },
      setItem(key, value) {
        values.set(String(key || ""), String(value || ""));
      },
    };
  }

  function browserStorageBlocked() {
    // Reading `localStorage` throws when the browser blocks site data; every later read would then stop the app.
    try {
      global.localStorage.getItem("researchos-runtime-mode");
      return false;
    } catch {
      return true;
    }
  }

  function enableCleanStateStorageIfRequested() {
    const search = new URLSearchParams(global.location?.search || "");
    const requested = search.get("researchos_clean_state") === "1";
    if (!requested && !browserStorageBlocked()) return null;
    const memoryStorage = createMemoryStorage();
    try {
      Object.defineProperty(global, "localStorage", {
        configurable: true,
        value: memoryStorage,
      });
      global.document?.documentElement?.setAttribute("data-researchos-clean-state", requested ? "memory-storage" : "blocked-memory-storage");
    } catch {
      global.document?.documentElement?.setAttribute("data-researchos-clean-state", "unavailable");
      return null;
    }
    return memoryStorage;
  }

  // 中文：public release smoke 用内存 storage 验证冷启动，不清空用户真实浏览器状态。
  // English: Public-release smoke can verify cold boot with memory storage without clearing user browser state.
  const cleanStateStorage = enableCleanStateStorageIfRequested();

  const runtimeModeStorageKey = "researchos-runtime-mode";
  const portablePreferenceKeys = new Set([
    "researchos-dashboard-language",
    "researchos-dashboard-theme",
    "researchos-preview-panel-width",
    "researchos-public-demo-visible",
  ]);

  function ensureRuntimeStorageBoundary(runtimeMode = "", storage = global.localStorage) {
    const mode = String(runtimeMode || "").trim();
    if (!mode || !storage) return false;
    if (storage === cleanStateStorage) {
      storage.setItem(runtimeModeStorageKey, mode);
      return false;
    }
    const previousMode = String(storage.getItem(runtimeModeStorageKey) || "").trim();
    if (previousMode === mode) return false;

    // Preserve an existing private workspace on first upgrade; public/demo entry fails closed.
    if (!previousMode && mode !== "public_starter") {
      storage.setItem(runtimeModeStorageKey, mode);
      return false;
    }

    const keys = Array.from({ length: Number(storage.length || 0) }, (_, index) => storage.key(index)).filter(Boolean);
    keys.forEach((key) => {
      if (key.startsWith("researchos-") && key !== runtimeModeStorageKey && !portablePreferenceKeys.has(key)) {
        storage.removeItem(key);
      }
    });
    storage.setItem(runtimeModeStorageKey, mode);
    return true;
  }

  const storageKeys = Object.freeze({
    cardGroupDissolutions: "researchos-card-group-dissolutions",
    cardGroups: "researchos-card-groups",
    cardGroupsSelected: "researchos-card-groups-selected",
    confirmationCursor: "researchos-confirmation-cursor",
    confirmationDecisions: "researchos-confirmation-decisions",
    doingBoard: "researchos-doing-board",
    materialIntakeInbox: "researchos-material-intake-inbox",
    materialUpgradeInbox: "researchos-material-upgrade-inbox",
    previewFeedbackInbox: "researchos-preview-feedback-inbox",
    researchScoutInbox: "researchos-scout-inbox",
    workSessionPrivate: "researchos-private-work-session-v1",
    workSessionPublic: "researchos-public-work-session-v1",
    workSessionHistoryPrivate: "researchos-private-work-session-history-v1",
    workSessionHistoryPublic: "researchos-public-work-session-history-v1",
    unifiedInboxArchive: "researchos-unified-inbox-archive",
    unifiedInboxArchiveResolved: "researchos-unified-inbox-archive-resolved",
  });

  const activeContextPaths = Object.freeze({
    cardGroupDissolutions: "06_active_context/ui-card-group-dissolution-inbox.md",
    cardGroups: "06_active_context/ui-card-groups.md",
    confirmations: "06_active_context/ui-confirmation-decisions.md",
    feedback: "06_active_context/ui-feedback-inbox.md",
    materialIntake: "06_active_context/ui-material-intake-inbox.md",
    materialUpgrade: "06_active_context/ui-material-upgrade-inbox.md",
    researchScout: "06_active_context/ui-research-scout-inbox.md",
  });

  const standardPaths = Object.freeze({
    groupComposition: "05_workflows/research_management/group-composition-lifecycle-standard.md",
  });

  global.ResearchOSStorageContract = Object.freeze({
    activeContextPaths,
    cleanStateStorage,
    createMemoryStorage,
    ensureRuntimeStorageBoundary,
    runtimeModeStorageKey,
    standardPaths,
    storageKeys,
  });
})(window);
