/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 临时 UI 状态「card group state」；只管理浏览器侧草稿/队列，不作为长期记忆。
 * English: Temporary UI-state owner for card group state in the ResearchOS dashboard; manages browser-side drafts/queues, not long-term memory.
 */

(function attachResearchOSCardGroupStateService(global) {
  function normalizeDeps(deps = {}) {
    return {
      cardGroupService: deps.cardGroupService || global.ResearchOSCardGroupService,
      localStorage: deps.localStorage || global.localStorage,
      now: deps.now || (() => new Date().toISOString()),
      statePolicy: deps.statePolicy || global.ResearchOSStatePolicy,
    };
  }

  function normalizeOptions(options = {}) {
    return {
      cardGroupDeps: options.cardGroupDeps || {},
      defaultTitle: options.defaultTitle || "Research Group",
      dissolutionStorageKey: options.dissolutionStorageKey || "",
      documents: Array.isArray(options.documents) ? options.documents : [],
      limit: options.limit || 80,
      selectedId: options.selectedId || "",
      selectedStorageKey: options.selectedStorageKey || "",
      storageKey: options.storageKey || "",
    };
  }

  function seedGroups(options = {}, deps = {}) {
    const { cardGroupService } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    return cardGroupService.seededCardGroups(safeOptions.documents, safeOptions.cardGroupDeps);
  }

  function loadCardGroups(options = {}, deps = {}) {
    const { cardGroupService, statePolicy } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    const stored = statePolicy.readJsonArray(safeOptions.storageKey, { objectOnly: false });
    return cardGroupService.mergeSeededCardGroups(
      stored,
      seedGroups(safeOptions, deps),
      safeOptions.cardGroupDeps
    );
  }

  function loadStoredCardGroups(options = {}, deps = {}) {
    const { cardGroupService, statePolicy } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    return statePolicy.readJsonArray(safeOptions.storageKey, { objectOnly: false })
      .map((group, index) => cardGroupService.normalizeCardGroup(group, index, safeOptions.cardGroupDeps))
      .filter(Boolean);
  }

  function saveCardGroups(groups = [], options = {}, deps = {}) {
    const { cardGroupService, statePolicy } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    const safeGroups = (Array.isArray(groups) ? groups : [])
      .map((group, index) => cardGroupService.normalizeCardGroup(group, index, safeOptions.cardGroupDeps))
      .filter((group) => group && (!group.source_type || cardGroupService.shouldKeepSeedGroup(group)));
    statePolicy.writeJsonArray(safeOptions.storageKey, safeGroups, { limit: safeOptions.limit });
    return safeGroups;
  }

  function readSelectedId(options = {}, deps = {}) {
    const { localStorage } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    return safeOptions.selectedStorageKey ? localStorage.getItem(safeOptions.selectedStorageKey) || "" : "";
  }

  function writeSelectedId(selectedId = "", options = {}, deps = {}) {
    const { localStorage } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    if (safeOptions.selectedStorageKey) {
      localStorage.setItem(safeOptions.selectedStorageKey, selectedId || "");
    }
    return selectedId;
  }

  function ensureCardGroups(options = {}, deps = {}) {
    const { cardGroupService } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    let groups = loadCardGroups(safeOptions, deps);
    if (!groups.length) {
      groups = [cardGroupService.createCardGroup({ title: "Research Group 1" }, safeOptions.cardGroupDeps)];
      saveCardGroups(groups, safeOptions, deps);
    }
    const preferredGroup = groups.find((group) => group.source_type === "relationship_pattern") || groups.find((group) => group.group_level === "G1") || groups[0];
    const selectedGroup = groups.find((group) => group.id === safeOptions.selectedId);
    const selectedCounts = cardGroupService.cardGroupCounts(selectedGroup || {});
    const selectedLooksEmptyCustom = Boolean(
      selectedGroup &&
      !selectedGroup.source_type &&
      !selectedCounts.total &&
      !String(selectedGroup.purpose || "").trim()
    );
    const nextSelectedId = (!selectedGroup || selectedLooksEmptyCustom) ? preferredGroup.id : safeOptions.selectedId;
    if (nextSelectedId !== safeOptions.selectedId) {
      writeSelectedId(nextSelectedId, safeOptions, deps);
    }
    return {
      groups,
      selectedId: nextSelectedId,
      selectionChanged: nextSelectedId !== safeOptions.selectedId,
    };
  }

  function removeStoredCardGroup(groupId = "", options = {}, deps = {}) {
    const groups = loadStoredCardGroups(options, deps).filter((group) => group && group.id !== groupId);
    saveCardGroups(groups, options, deps);
    return groups;
  }

  function loadCardGroupDissolutions(options = {}, deps = {}) {
    const { statePolicy } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    return statePolicy.readJsonArray(safeOptions.dissolutionStorageKey);
  }

  function saveCardGroupDissolutions(items = [], options = {}, deps = {}) {
    const { statePolicy } = normalizeDeps(deps);
    const safeOptions = normalizeOptions(options);
    const safeItems = (items || []).filter((item) => item && typeof item === "object");
    statePolicy.writeJsonArray(safeOptions.dissolutionStorageKey, safeItems, { limit: safeOptions.limit });
    return safeItems;
  }

  function markCardGroupDissolutionWithdrawn(id = "", options = {}, deps = {}) {
    const { now } = normalizeDeps(deps);
    const timestamp = now();
    const items = loadCardGroupDissolutions(options, deps).map((item) => (
      item.id === id ? { ...item, status: "withdrawn", updatedAt: timestamp } : item
    ));
    return saveCardGroupDissolutions(items, options, deps);
  }

  global.ResearchOSCardGroupStateService = Object.freeze({
    ensureCardGroups,
    loadCardGroupDissolutions,
    loadCardGroups,
    loadStoredCardGroups,
    markCardGroupDissolutionWithdrawn,
    removeStoredCardGroup,
    readSelectedId,
    saveCardGroupDissolutions,
    saveCardGroups,
    seedGroups,
    writeSelectedId,
  });
})(window);
