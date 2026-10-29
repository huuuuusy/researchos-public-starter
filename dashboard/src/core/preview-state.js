/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「preview state」；供 app、service、view 复用。
 * English: Browser-side core primitive for preview state in the ResearchOS dashboard; shared by app, services, and views.
 */

(function () {
  const storageKeys = Object.freeze({
    path: "researchos-preview-path",
    open: "researchos-preview-open",
    panelWidth: "researchos-preview-panel-width",
    history: "researchos-preview-history",
    historyIndex: "researchos-preview-history-index",
    feedbackDraft: "researchos-preview-feedback-draft",
  });

  const emptyState = Object.freeze({
    selectedPath: "",
    open: false,
    searchTerm: "",
    loadingPath: "",
    content: "",
    error: "",
    anchor: "",
    selectedText: "",
    feedbackDraft: "",
    feedbackStatusText: "",
    history: Object.freeze([]),
    historyIndex: -1,
  });

  function historyIndex(value) {
    const number = Number(value);
    return Number.isFinite(number) ? Math.trunc(number) : -1;
  }

  // The preview service (a services-layer owner) is passed in by the shell; core does not resolve it.
  function read({ storage = window.localStorage, previewService = null } = {}) {
    const loadHistory = previewService?.loadPreviewHistory;
    const history = typeof loadHistory === "function"
      ? loadHistory({ storageKey: storageKeys.history, storage })
      : [];
    return {
      ...emptyState,
      selectedPath: storage.getItem(storageKeys.path) || "",
      open: storage.getItem(storageKeys.open) === "true",
      feedbackDraft: storage.getItem(storageKeys.feedbackDraft) || "",
      history,
      historyIndex: historyIndex(storage.getItem(storageKeys.historyIndex)),
    };
  }

  function reset({ storage = window.localStorage } = {}) {
    storage.setItem(storageKeys.open, "false");
    storage.removeItem(storageKeys.path);
    storage.removeItem(storageKeys.history);
    storage.removeItem(storageKeys.historyIndex);
    return {
      ...emptyState,
      history: [],
    };
  }

  function writeOpen(open, storage = window.localStorage) {
    const nextOpen = Boolean(open);
    storage.setItem(storageKeys.open, String(nextOpen));
    return nextOpen;
  }

  function writeSelectedPath(path, storage = window.localStorage) {
    const nextPath = String(path || "");
    if (nextPath) storage.setItem(storageKeys.path, nextPath);
    else storage.removeItem(storageKeys.path);
    return nextPath;
  }

  function clearFeedbackDraft(storage = window.localStorage) {
    storage.removeItem(storageKeys.feedbackDraft);
  }

  function writeFeedbackDraft(value, storage = window.localStorage) {
    const draft = String(value || "");
    storage.setItem(storageKeys.feedbackDraft, draft);
    return draft;
  }

  function readPanelWidth(storage = window.localStorage) {
    const value = Number(storage.getItem(storageKeys.panelWidth));
    return Number.isFinite(value) ? Math.trunc(value) : 0;
  }

  function writePanelWidth(width, storage = window.localStorage) {
    const value = Number(width);
    if (!Number.isFinite(value) || value <= 0) {
      storage.removeItem(storageKeys.panelWidth);
      return 0;
    }
    const nextWidth = Math.trunc(value);
    storage.setItem(storageKeys.panelWidth, String(nextWidth));
    return nextWidth;
  }

  window.ResearchOSPreviewState = {
    storageKeys,
    emptyState,
    historyIndex,
    read,
    readPanelWidth,
    reset,
    writeOpen,
    writeSelectedPath,
    clearFeedbackDraft,
    writeFeedbackDraft,
    writePanelWidth,
  };
})();
