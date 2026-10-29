/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「preview feedback」；承接可复用逻辑，避免 app.js 重新变成大杂烩。
 * English: Frontend service for preview feedback in the ResearchOS dashboard; keeps reusable logic out of app.js so it does not become a catch-all again.
 */

(function attachResearchOSPreviewFeedbackService(global) {
  function normalizePreviewSelectedText(value = "", limit = 1200) {
    const text = String(value || "").trim().replace(/\s+/g, " ");
    if (!text) return "";
    return text.slice(0, Math.max(0, Number(limit) || 1200));
  }

  function previewFeedbackCategory(category = "", text = (key) => key) {
    const value = String(category || "").trim();
    return value || text("previewFeedbackCategoryDefault");
  }

  function previewFeedbackId(path = "", idSuffix = "") {
    return `preview-feedback:${String(path || "")}:${String(idSuffix || Date.now())}`;
  }

  function previewFeedbackNeedsEvidence(category = "", feedback = "") {
    const text = `${category || ""} ${feedback || ""}`.toLowerCase();
    return /证据不足|补证据|证据边界|先读源|needs? evidence|evidence boundary|source review/.test(text);
  }

  function buildPreviewFeedbackRecord({
    category = "",
    feedback = "",
    idSuffix = "",
    now = new Date().toISOString(),
    selectedDoc = null,
    selectedText = "",
    text = (key) => key,
  } = {}) {
    const path = selectedDoc?.path || "";
    const needsEvidence = previewFeedbackNeedsEvidence(category, feedback);
    return {
      id: previewFeedbackId(path, idSuffix),
      title: selectedDoc?.title || path,
      target_path: path,
      category: previewFeedbackCategory(category, text),
      selected_text: normalizePreviewSelectedText(selectedText),
      feedback: String(feedback || "").trim(),
      action: needsEvidence ? "check_evidence_boundary" : "revise_evidence_note",
      status: "pending_codex_review",
      createdAt: now,
      updatedAt: now,
    };
  }

  function buildPreviewFeedbackBody({
    feedback = "",
    selectedDoc = null,
    selectedText = "",
  } = {}) {
    const path = selectedDoc?.path || "";
    const title = selectedDoc?.title || "";
    const normalizedSelection = normalizePreviewSelectedText(selectedText);
    return [
      title ? `文件：${title}` : "",
      `路径：${path}`,
      normalizedSelection ? `选中文本：${normalizedSelection}` : "选中文本：未选择，属于文件级反馈",
      `修改意见：${String(feedback || "").trim()}`,
    ].filter(Boolean).join("\n");
  }

  function buildPreviewFeedbackPayload({
    category = "",
    feedback = "",
    selectedDoc = null,
    selectedText = "",
    text = (key) => key,
  } = {}) {
    return {
      target_path: selectedDoc?.path || "",
      person_name: "",
      category: previewFeedbackCategory(category, text),
      feedback: buildPreviewFeedbackBody({ feedback, selectedDoc, selectedText }),
    };
  }

  function normalizeStateOptions(options = {}) {
    return {
      limit: options.limit || 80,
      storageKey: options.storageKey || "",
    };
  }

  function normalizeStateDeps(deps = {}) {
    return {
      statePolicy: deps.statePolicy || global.ResearchOSStatePolicy,
    };
  }

  function loadPreviewFeedbackItems(options = {}, deps = {}) {
    const { statePolicy } = normalizeStateDeps(deps);
    const safeOptions = normalizeStateOptions(options);
    return statePolicy.readJsonArray(safeOptions.storageKey);
  }

  function savePreviewFeedbackItems(items = [], options = {}, deps = {}) {
    const { statePolicy } = normalizeStateDeps(deps);
    const safeOptions = normalizeStateOptions(options);
    const safeItems = (items || []).filter((item) => item && typeof item === "object");
    statePolicy.writeJsonArray(safeOptions.storageKey, safeItems, { limit: safeOptions.limit });
    return safeItems;
  }

  function prependPreviewFeedbackItem(record = {}, options = {}, deps = {}) {
    if (!record || typeof record !== "object") {
      return loadPreviewFeedbackItems(options, deps);
    }
    return savePreviewFeedbackItems([record, ...loadPreviewFeedbackItems(options, deps)], options, deps);
  }

  function replacePreviewFeedbackItem(record = {}, options = {}, deps = {}) {
    if (!record?.id) return prependPreviewFeedbackItem(record, options, deps);
    const items = loadPreviewFeedbackItems(options, deps).filter((item) => item.id !== record.id);
    return savePreviewFeedbackItems([record, ...items], options, deps);
  }

  function removePreviewFeedbackItem(id = "", options = {}, deps = {}) {
    if (!id) return loadPreviewFeedbackItems(options, deps);
    return savePreviewFeedbackItems(
      loadPreviewFeedbackItems(options, deps).filter((item) => item.id !== id),
      options,
      deps
    );
  }

  global.ResearchOSPreviewFeedbackService = Object.freeze({
    buildPreviewFeedbackBody,
    buildPreviewFeedbackPayload,
    buildPreviewFeedbackRecord,
    loadPreviewFeedbackItems,
    normalizePreviewSelectedText,
    prependPreviewFeedbackItem,
    previewFeedbackCategory,
    previewFeedbackId,
    previewFeedbackNeedsEvidence,
    removePreviewFeedbackItem,
    replacePreviewFeedbackItem,
    savePreviewFeedbackItems,
  });
})(typeof window !== "undefined" ? window : globalThis);
