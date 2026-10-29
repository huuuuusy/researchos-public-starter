/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 临时 UI 状态「confirmation state」；只管理浏览器侧草稿/队列，不作为长期记忆。
 * English: Temporary UI-state owner for confirmation state in the ResearchOS dashboard; manages browser-side drafts/queues, not long-term memory.
 */

(function attachResearchOSConfirmationState(global) {
  function loadConfirmationDecisions({ statePolicy, storageKey } = {}) {
    return statePolicy?.readJsonObject(storageKey) || {};
  }

  function mergeConfirmationDecisions(...sources) {
    return Object.assign(
      {},
      ...sources.map((source) => (
        source && typeof source === "object" && !Array.isArray(source) ? source : {}
      ))
    );
  }

  function saveConfirmationDecisions(decisions = {}, { statePolicy, storageKey } = {}) {
    if (!statePolicy || !storageKey) return {};
    const safeDecisions = Object.fromEntries(
      Object.entries(decisions || {}).filter(
        ([id, record]) => id && record && typeof record === "object" && !Array.isArray(record)
      )
    );
    statePolicy.writeJsonObject(storageKey, safeDecisions);
    return safeDecisions;
  }

  function deleteConfirmationDecision(decisionId, { statePolicy, storageKey } = {}) {
    if (!decisionId || !statePolicy || !storageKey) return;
    const current = loadConfirmationDecisions({ statePolicy, storageKey });
    delete current[decisionId];
    return saveConfirmationDecisions(current, { statePolicy, storageKey });
  }

  function filterActiveConfirmationDecisions(decisions = {}, { statusIsActive = () => true } = {}) {
    return Object.fromEntries(
      Object.entries(decisions || {}).filter(
        ([, record]) => record && typeof record === "object" && statusIsActive(record.status || record.syncStatus, true)
      )
    );
  }

  function normalizeConfirmationChoice(choice = "") {
    const value = String(choice || "");
    if (value === "reject" || value === "evidence") return "uncertain";
    return value;
  }

  function confirmationChoiceLabel(choice = "", text = (key) => key) {
    const value = normalizeConfirmationChoice(choice);
    if (value === "accept") return text("confirmAccept");
    if (value === "revise") return text("confirmRevise");
    if (value === "uncertain") return text("confirmUnable");
    return text("confirmPendingStatus");
  }

  global.ResearchOSConfirmationState = Object.freeze({
    confirmationChoiceLabel,
    deleteConfirmationDecision,
    filterActiveConfirmationDecisions,
    loadConfirmationDecisions,
    mergeConfirmationDecisions,
    normalizeConfirmationChoice,
    saveConfirmationDecisions,
  });
})(window);
