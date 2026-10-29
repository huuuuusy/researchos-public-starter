/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「preview feedback workflow」；负责预览反馈的本地入队、远端同步和 fallback 状态规则。
 * English: Frontend service for the preview feedback workflow in the ResearchOS dashboard; owns local enqueue, remote sync, and fallback status rules.
 */

(function attachResearchOSPreviewFeedbackWorkflow(global) {
  function createPreviewFeedbackWorkflow(options = {}) {
    const {
      feedbackStorageKey = "",
      services = {},
      simpleText = (key) => key,
    } = options;

    const previewFeedbackService = services.feedback || global.ResearchOSPreviewFeedbackService;
    const feedbackClient = services.feedbackClient || global.ResearchOSFeedbackClient;

    function stateOptions() {
      return {
        limit: 80,
        storageKey: feedbackStorageKey,
      };
    }

    function loadPreviewFeedbackItems() {
      return previewFeedbackService.loadPreviewFeedbackItems(stateOptions());
    }

    function savePreviewFeedbackItems(items = []) {
      return previewFeedbackService.savePreviewFeedbackItems(items, stateOptions());
    }

    function removePreviewFeedbackItem(id = "") {
      return previewFeedbackService.removePreviewFeedbackItem(id, stateOptions());
    }

    async function submitPreviewFeedback({
      category = "",
      feedback = "",
      idSuffix = Date.now(),
      now = new Date().toISOString(),
      selectedDoc = null,
      selectedText = "",
    } = {}) {
      const safeFeedback = String(feedback || "").trim();
      if (!selectedDoc?.path) return { ok: false, reason: "missing_doc" };
      if (!safeFeedback) return { ok: false, reason: "empty_feedback" };

      const record = previewFeedbackService.buildPreviewFeedbackRecord({
        category,
        feedback: safeFeedback,
        idSuffix,
        now,
        selectedDoc,
        selectedText,
        text: simpleText,
      });
      previewFeedbackService.prependPreviewFeedbackItem(record, stateOptions());

      try {
        const syncResult = await feedbackClient.submitFeedbackPayload(
          previewFeedbackService.buildPreviewFeedbackPayload({
            category,
            feedback: safeFeedback,
            selectedDoc,
            selectedText,
            text: simpleText,
          })
        );
        if (!syncResult.ok) throw new Error(syncResult.message || "Feedback request failed");
        return { localOnly: false, ok: true, record, syncResult };
      } catch {
        const localRecord = { ...record, status: "browser_local" };
        previewFeedbackService.replacePreviewFeedbackItem(localRecord, stateOptions());
        return { localOnly: true, ok: true, record: localRecord };
      }
    }

    return Object.freeze({
      loadPreviewFeedbackItems,
      removePreviewFeedbackItem,
      savePreviewFeedbackItems,
      stateOptions,
      submitPreviewFeedback,
    });
  }

  global.ResearchOSPreviewFeedbackWorkflow = Object.freeze({
    createPreviewFeedbackWorkflow,
  });
})(typeof window !== "undefined" ? window : globalThis);
