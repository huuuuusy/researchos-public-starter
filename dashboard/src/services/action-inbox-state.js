/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 临时 UI 状态「action inbox state」；只管理浏览器侧草稿/队列，不作为长期记忆。
 * English: Temporary UI-state owner for action inbox state in the ResearchOS dashboard; manages browser-side drafts/queues, not long-term memory.
 */

(function attachResearchOSActionInboxState(global) {
  function normalizeDeps(deps = {}) {
    return {
      now: deps.now || (() => new Date().toISOString()),
      statePolicy: deps.statePolicy || global.ResearchOSStatePolicy,
    };
  }

  function normalizeOptions(options = {}) {
    return {
      limit: options.limit || 80,
      storageKey: options.storageKey || "",
    };
  }

  function loadItems(options = {}, deps = {}) {
    const { statePolicy } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    return statePolicy.readJsonArray(safeOptions.storageKey);
  }

  function saveItems(items = [], options = {}, deps = {}) {
    const { statePolicy } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    const safeItems = (items || []).filter((item) => item && typeof item === "object");
    statePolicy.writeJsonArray(safeOptions.storageKey, safeItems, { limit: safeOptions.limit });
    return safeItems;
  }

  function removeItem(id = "", options = {}, deps = {}) {
    if (!id) return { item: null, items: loadItems(options, deps) };
    const items = loadItems(options, deps);
    const item = items.find((entry) => entry.id === id) || null;
    const nextItems = items.filter((entry) => entry.id !== id);
    saveItems(nextItems, options, deps);
    return { item, items: nextItems };
  }

  function markItemWithdrawn(id = "", options = {}, deps = {}) {
    const { now } = normalizeDeps(deps);
    const timestamp = now();
    const items = loadItems(options, deps).map((item) => (
      item.id === id ? { ...item, status: "withdrawn", updatedAt: timestamp } : item
    ));
    const item = items.find((entry) => entry.id === id) || null;
    saveItems(items, options, deps);
    return { item, items };
  }

  function updateItem(id = "", patch = {}, options = {}, deps = {}) {
    if (!id) return { next: null, previous: null, items: loadItems(options, deps) };
    const { now } = normalizeDeps(deps);
    const items = loadItems(options, deps);
    const previous = items.find((item) => item.id === id) || null;
    const timestamp = now();
    const nextItems = items.map((item) => (
      item.id === id ? { ...item, ...patch, updatedAt: timestamp } : item
    ));
    saveItems(nextItems, options, deps);
    return {
      items: nextItems,
      next: nextItems.find((item) => item.id === id) || null,
      previous,
    };
  }

  global.ResearchOSActionInboxState = Object.freeze({
    loadItems,
    markItemWithdrawn,
    removeItem,
    saveItems,
    updateItem,
  });
})(window);
