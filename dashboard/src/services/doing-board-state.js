/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 临时 UI 状态「doing board state」；只管理浏览器侧草稿/队列，不作为长期记忆。
 * English: Temporary UI-state owner for doing board state in the ResearchOS dashboard; manages browser-side drafts/queues, not long-term memory.
 */

(function () {
  const defaultStorageKey = window.ResearchOSStorageContract?.storageKeys?.doingBoard || "researchos-doing-board";
  const defaultLimit = 24;
  const retiredActionIds = new Set(["research_portfolio_self_action"]);
  let localIdentitySequence = 0;

  function legacyItemKey(item = {}) {
    return `${item.type || "item"}:${item.path || item.title || item.id || ""}`;
  }

  function lineageIdentity(item = {}) {
    const explicitId = String(item.id || "").trim();
    if (explicitId) return { id: explicitId, kind: "explicit" };
    const workSessionId = String(item.work_session_id || "").trim();
    if (workSessionId) return { id: `handoff:work-session:${workSessionId}`, kind: "work_session" };
    const candidateId = String(item.candidate?.candidate_id || item.candidate_id || "").trim();
    if (candidateId) return { id: `handoff:candidate:${candidateId}`, kind: "candidate" };
    const type = String(item.type || "item").trim() || "item";
    const path = String(item.path || "").trim();
    if (type !== "task" && path) return { id: `source:${type}:${path}`, kind: "source" };
    return { id: "", kind: "unbound" };
  }

  function newLocalIdentity() {
    localIdentitySequence += 1;
    const uuid = globalThis.crypto?.randomUUID?.();
    return uuid ? `local:${uuid}` : `local:${Date.now()}:${localIdentitySequence}`;
  }

  function itemKey(item = {}) {
    return lineageIdentity(item).id || legacyItemKey(item);
  }

  function normalizeItem(item = {}, options = {}) {
    if (!item || typeof item !== "object") return null;
    const type = item.type || "item";
    const title = String(item.title || item.name || "").trim();
    const path = String(item.path || "").trim();
    if (!title && !path) return null;
    const note = String(item.note || item.summary || item.next_step || item.ask || item.why || "").trim();
    const source = String(item.source || "").trim();
    const workSessionGoal = source === "work-session"
      ? String(note.split("\n", 1)[0] || "").replace(/^[^:：]+[:：]\s*/, "").trim()
      : "";
    const displayTitle = workSessionGoal.length > 72 && title === workSessionGoal.slice(0, 72) ? workSessionGoal : title;
    const fieldUpdates = item.field_updates && typeof item.field_updates === "object" && !Array.isArray(item.field_updates)
      ? Object.fromEntries(
          Object.entries(item.field_updates)
            .map(([key, value]) => [String(key), String(value ?? "").trim()])
            .filter(([, value]) => value)
        )
      : {};
    const sourceCards = Array.isArray(item.source_cards)
      ? item.source_cards.slice(0, 24).map((card = {}) => ({
          id: String(card.id || "").trim(),
          path: String(card.path || "").trim(),
          preview: String(card.preview || "").trim(),
          subtitle: String(card.subtitle || "").trim(),
          title: String(card.title || "").trim(),
          type: String(card.type || "asset").trim(),
          type_label: String(card.type_label || "").trim(),
        })).filter((card) => card.id || card.path || card.title)
      : [];
    const writebackModes = Array.isArray(item.writeback_modes)
      ? item.writeback_modes.map((mode) => String(mode || "").trim()).filter(Boolean)
      : [];
    const targetExistingPaths = Array.isArray(item.target_existing_paths)
      ? item.target_existing_paths.map((pathValue) => String(pathValue || "").trim()).filter(Boolean).slice(0, 24)
      : [];
    const lineage = lineageIdentity({ ...item, type, title, path });
    const id = lineage.id || (options.createIdentity ? newLocalIdentity() : legacyItemKey({ ...item, type, title, path }));
    return {
      id,
      identity_kind: lineage.id ? lineage.kind : (options.createIdentity ? "local" : "legacy"),
      lineage_id: lineage.id || "",
      type,
      title: displayTitle || path,
      path,
      note,
      status: !item.status || item.status === "today" ? "local" : item.status,
      source,
      action: String(item.action || item.intent || "").trim(),
      admission_state: item.admission_state && typeof item.admission_state === "object" && !Array.isArray(item.admission_state)
        ? item.admission_state : null,
      candidate: item.candidate && typeof item.candidate === "object" && !Array.isArray(item.candidate) ? item.candidate : null,
      current_state: String(item.current_state || "").trim(),
      decision_rationale: String(item.decision_rationale || item.rationale || "").trim(),
      evidence_state: String(item.evidence_state || "").trim(),
      impact_scope: String(item.impact_scope || "").trim(),
      proposed_state: String(item.proposed_state || "").trim(),
      rollback_ref: String(item.rollback_ref || "").trim(),
      save_target: String(item.save_target || "").trim(),
      sensitivity: String(item.sensitivity || "").trim(),
      target_state: String(item.target_state || "").trim(),
      work_session_id: String(item.work_session_id || "").trim(),
      field_updates: fieldUpdates,
      selected_text: String(item.selected_text || "").trim(),
      create_composition_card: item.create_composition_card === true,
      source_cards: sourceCards,
      supplement_existing_cards: item.supplement_existing_cards === true,
      target_existing_paths: targetExistingPaths,
      writeback_modes: writebackModes,
      addedAt: item.addedAt || new Date().toISOString(),
    };
  }

  function readItems({
    statePolicy = window.ResearchOSStatePolicy,
    storageKey = defaultStorageKey,
  } = {}) {
    return statePolicy.readJsonArray(storageKey, { objectOnly: false })
      .map(normalizeItem)
      .filter((item) => item && !retiredActionIds.has(item.action));
  }

  function writeItems(items = [], {
    limit = defaultLimit,
    statePolicy = window.ResearchOSStatePolicy,
    storageKey = defaultStorageKey,
  } = {}) {
    statePolicy.writeJsonArray(storageKey, (Array.isArray(items) ? items : []).map(normalizeItem).filter(Boolean), { limit });
  }

  function encodePayload(item = {}) {
    return encodeURIComponent(JSON.stringify(normalizeItem(item) || {}));
  }

  function decodePayload(value = "") {
    try {
      return normalizeItem(JSON.parse(decodeURIComponent(value || "")));
    } catch {
      return null;
    }
  }

  function typeLabel(type = "", text = (key) => key) {
    const labels = {
      mount: "itemMount",
      paper: "itemPaper",
      paper_field_update: "itemPaperFieldUpdate",
      person: "itemPerson",
      project: "itemProject",
      source: "itemSource",
      talk: "itemTalk",
    };
    const labelKey = labels[type];
    return labelKey ? text(labelKey) : type || "item";
  }

  function upsertItem(items = [], item = {}, status = "local") {
    const normalized = normalizeItem({ ...item, status }, { createIdentity: true });
    const currentItems = Array.isArray(items) ? items : [];
    if (!normalized) return { item: null, items: currentItems };
    const key = itemKey(normalized);
    const existingIndex = currentItems.findIndex((entry) => itemKey(entry) === key);
    if (existingIndex >= 0) {
      const nextItems = currentItems.slice();
      nextItems[existingIndex] = { ...nextItems[existingIndex], ...normalized, status: normalized.status || status };
      return { item: nextItems[existingIndex], items: nextItems };
    }
    return { item: normalized, items: [normalized, ...currentItems] };
  }

  function removeItem(items = [], key = "") {
    return (Array.isArray(items) ? items : []).filter((item) => itemKey(item) !== key);
  }

  window.ResearchOSDoingBoardState = {
    decodePayload,
    defaultLimit,
    defaultStorageKey,
    encodePayload,
    itemKey,
    legacyItemKey,
    lineageIdentity,
    normalizeItem,
    readItems,
    removeItem,
    typeLabel,
    upsertItem,
    writeItems,
  };
})();
