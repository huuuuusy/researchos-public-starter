/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「preview session state」；拥有 Markdown preview 的局部状态机和 history 持久化桥接。
 * English: Frontend session-state service for Markdown preview; owns local preview state transitions and history persistence bridging.
 */

(function attachResearchOSPreviewSessionState(global) {
  function normalizeInitialState(initialState = {}) {
    return {
      anchor: initialState.anchor || "",
      content: initialState.content || "",
      error: initialState.error || "",
      feedbackDraft: initialState.feedbackDraft || "",
      feedbackStatusText: initialState.feedbackStatusText || "",
      history: Array.isArray(initialState.history) ? initialState.history : [],
      historyIndex: Number.isFinite(Number(initialState.historyIndex))
        ? Math.trunc(Number(initialState.historyIndex))
        : -1,
      loadingPath: initialState.loadingPath || "",
      open: Boolean(initialState.open),
      searchTerm: initialState.searchTerm || "",
      selectedPath: initialState.selectedPath || "",
      selectedText: initialState.selectedText || "",
    };
  }

  function createPreviewSessionState(options = {}) {
    const {
      historyIndexKey = "",
      historyKey = "",
      initialState = {},
      previewService = global.ResearchOSPreviewService,
      previewState = global.ResearchOSPreviewState,
    } = options;
    const state = normalizeInitialState(initialState);

    function snapshot() {
      return {
        ...state,
        history: [...state.history],
      };
    }

    function saveHistory() {
      previewService.savePreviewHistory({
        history: state.history,
        index: state.historyIndex,
        historyKey,
        indexKey: historyIndexKey,
      });
    }

    function pushHistory(path, anchor = "") {
      const nextHistory = previewService.pushPreviewHistory({
        history: state.history,
        index: state.historyIndex,
        path,
        anchor,
      });
      state.history = nextHistory.history;
      state.historyIndex = nextHistory.index;
      saveHistory();
      return snapshot();
    }

    function canBack() {
      return previewService.canPreviewBack(state.history, state.historyIndex);
    }

    function canForward() {
      return previewService.canPreviewForward(state.history, state.historyIndex);
    }

    function navigateHistory(direction) {
      const navigation = previewService.navigatePreviewHistory(state.history, state.historyIndex, direction);
      if (!navigation) return null;
      state.history = navigation.history;
      state.historyIndex = navigation.index;
      saveHistory();
      return {
        ...navigation,
        state: snapshot(),
      };
    }

    function closeHistoryEntry(path = "", anchor = "") {
      const result = previewService.closePreviewHistoryEntry({
        anchor,
        history: state.history,
        index: state.historyIndex,
        path,
      });
      state.history = result.history;
      state.historyIndex = result.index;
      saveHistory();
      if (!result.entry && result.closedCurrent) {
        state.selectedPath = "";
        state.anchor = "";
        state.content = "";
        state.error = "";
        state.loadingPath = "";
        state.selectedText = "";
        previewState.writeSelectedPath("");
      }
      return {
        ...result,
        state: snapshot(),
      };
    }

    function startMarkdownOpen(path, openOptions = {}) {
      state.selectedPath = String(path || "");
      state.anchor = openOptions.anchor || "";
      state.open = previewState.writeOpen(true);
      state.loadingPath = state.selectedPath;
      state.content = "";
      state.error = "";
      state.selectedText = "";
      state.feedbackStatusText = "";
      previewState.writeSelectedPath(state.selectedPath);
      return snapshot();
    }

    function finishMarkdownLoad() {
      state.loadingPath = "";
      return snapshot();
    }

    function setContent(content = "") {
      state.content = String(content || "");
      return state.content;
    }

    function setError(error = "") {
      state.error = String(error || "");
      return state.error;
    }

    function setFeedbackDraft(value = "") {
      state.feedbackDraft = previewState.writeFeedbackDraft(value);
      state.feedbackStatusText = "";
      return state.feedbackDraft;
    }

    function markFeedbackSaved(statusText = "") {
      state.feedbackDraft = "";
      state.selectedText = "";
      state.feedbackStatusText = statusText;
      previewState.clearFeedbackDraft();
      return snapshot();
    }

    function setOpen(open) {
      state.open = previewState.writeOpen(Boolean(open));
      return state.open;
    }

    function setSearchTerm(value = "") {
      state.searchTerm = String(value || "");
      return state.searchTerm;
    }

    function setSelectedText(text = "") {
      state.selectedText = String(text || "");
      return state.selectedText;
    }

    return Object.freeze({
      canBack,
      canForward,
      closeHistoryEntry,
      finishMarkdownLoad,
      markFeedbackSaved,
      navigateHistory,
      pushHistory,
      setContent,
      setError,
      setFeedbackDraft,
      setOpen,
      setSearchTerm,
      setSelectedText,
      snapshot,
      startMarkdownOpen,
    });
  }

  global.ResearchOSPreviewSessionState = Object.freeze({
    createPreviewSessionState,
    normalizeInitialState,
  });
})(window);
