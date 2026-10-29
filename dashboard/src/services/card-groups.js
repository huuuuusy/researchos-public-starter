/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「card groups」；承接可复用逻辑，避免 app.js 重新变成大杂烩。
 * English: Frontend service for card groups in the ResearchOS dashboard; keeps reusable logic out of app.js so it does not become a catch-all again.
 */

(function attachResearchOSCardGroupService(global) {
  const ITEM_TYPES = Object.freeze(["paper", "person", "project", "talk", "source"]);

  function defaultText(key) {
    return key;
  }

  function seedRules() {
    return global.ResearchOSCardGroupSeedRules || {};
  }

  function inferCardGroupItemType(path = "") {
    const value = String(path || "");
    if (value.includes("/papers/") || value.includes("01_knowledge/papers/")) return "paper";
    if (value.includes("04_people/")) return "person";
    if (value.includes("01_knowledge/projects/")) return "project";
    if (value.includes("01_knowledge/talks/")) return "talk";
    return "source";
  }

  function cardGroupItemKey(item = {}) {
    return `${item.type || "item"}:${item.path || item.title || ""}`;
  }

  function normalizeCardGroupItem(item = {}, options = {}) {
    const normalizeItem = options.normalizeItem || ((value) => value);
    const now = options.now || new Date().toISOString();
    const normalized = normalizeItem(item);
    if (!normalized) return null;
    if (!ITEM_TYPES.includes(normalized.type)) return null;
    return {
      type: normalized.type,
      title: normalized.title,
      path: normalized.path,
      note: normalized.note,
      source: normalized.source || "",
      addedAt: item.addedAt || normalized.addedAt || now,
    };
  }

  function createCardGroup(partial = {}, options = {}) {
    const text = options.text || defaultText;
    const now = options.now || new Date().toISOString();
    const idFactory = options.idFactory || (() => `group-${Date.now()}-${Math.random().toString(16).slice(2)}`);
    return {
      id: partial.id || idFactory(),
      title: partial.title || text("cardGroupTitle"),
      purpose: partial.purpose || "",
      items: Array.isArray(partial.items) ? partial.items.map((item) => normalizeCardGroupItem(item, { ...options, now })).filter(Boolean) : [],
      group_level: partial.group_level || "G1",
      group_kind: partial.group_kind || "",
      source_type: partial.source_type || "",
      source_path: partial.source_path || "",
      source_note: partial.source_note || "",
      createdAt: partial.createdAt || now,
      updatedAt: partial.updatedAt || now,
    };
  }

  function normalizeCardGroup(group = {}, index = 0, options = {}) {
    const text = options.text || defaultText;
    if (!group || typeof group !== "object") return null;
    const normalized = createCardGroup(
      {
        ...group,
        id: group.id || `group-${index + 1}`,
        title: group.title || `${text("cardGroupTitle")} ${index + 1}`,
      },
      options
    );
    const seen = new Set();
    normalized.items = normalized.items.filter((item) => {
      const key = cardGroupItemKey(item);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    return normalized;
  }

  function cardGroupSeedOptions(options = {}) {
    return {
      ...options,
      inferCardGroupItemType,
      normalizeCardGroup,
      normalizeCardGroupItem,
      shouldKeepSeedGroup,
    };
  }

  function seededCardGroups(documents = [], options = {}) {
    return seedRules().seededCardGroups?.(documents, cardGroupSeedOptions(options)) || [];
  }

  function mergeSeededCardGroups(stored = [], seedGroups = [], options = {}) {
    const merged = new Map();
    (Array.isArray(seedGroups) ? seedGroups : []).forEach((group, index) => {
      const normalized = normalizeCardGroup(group, index, options);
      if (normalized) merged.set(normalized.id, normalized);
    });
    (Array.isArray(stored) ? stored : []).forEach((group, index) => {
      const normalized = normalizeCardGroup(group, index, options);
      if (!normalized || !shouldKeepSeedGroup(normalized)) return;
      const seed = merged.get(normalized.id);
      if (!seed) {
        merged.set(normalized.id, normalized);
        return;
      }
      const seen = new Set();
      const items = [...(seed.items || []), ...(normalized.items || [])].filter((item) => {
        const key = cardGroupItemKey(item);
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      const mergedGroup = {
        ...seed,
        ...normalized,
        items,
        source_type: normalized.source_type || seed.source_type,
        source_path: normalized.source_path || seed.source_path,
        source_note: normalized.source_note || seed.source_note,
        group_level: normalized.group_level || seed.group_level,
        group_kind: normalized.group_kind || seed.group_kind,
      };
      if (shouldKeepSeedGroup(mergedGroup)) merged.set(normalized.id, mergedGroup);
    });
    return Array.from(merged.values()).filter((group) => !group.source_type || shouldKeepSeedGroup(group));
  }

  function cardGroupCounts(group = {}) {
    const items = Array.isArray(group.items) ? group.items : [];
    const counts = {
      paper: items.filter((item) => item.type === "paper").length,
      person: items.filter((item) => item.type === "person").length,
      project: items.filter((item) => item.type === "project").length,
      talk: items.filter((item) => item.type === "talk").length,
      source: items.filter((item) => item.type === "source").length,
    };
    counts.total = counts.paper + counts.person + counts.project + counts.talk + counts.source;
    return counts;
  }

  function shouldKeepSeedGroup(group = {}) {
    const counts = cardGroupCounts(group);
    if (group.group_level === "G1" && group.source_type && counts.total <= 1) return false;
    return true;
  }

  global.ResearchOSCardGroupService = Object.freeze({
    ITEM_TYPES,
    cardGroupCounts,
    cardGroupItemKey,
    createCardGroup,
    inferCardGroupItemType,
    mergeSeededCardGroups,
    normalizeCardGroup,
    normalizeCardGroupItem,
    seededCardGroups,
    shouldKeepSeedGroup,
  });
})(window);
