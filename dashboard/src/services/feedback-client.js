/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端客户端「feedback」；集中管理 /feedback 写入和异步提交 fallback 规则。
 * English: Frontend feedback client for the ResearchOS dashboard; centralizes /feedback writes and async-submit fallback rules.
 */

(function attachResearchOSFeedbackClient(global) {
  const FEEDBACK_ENDPOINT = "/feedback";

  function canSubmitFeedbackAsync(deps = {}) {
    return typeof global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher) === "function";
  }

  function feedbackErrorResult(error = "Feedback request failed") {
    return {
      ok: false,
      localOnly: true,
      message: error?.message || String(error || "Feedback request failed"),
    };
  }

  async function submitFeedbackPayload(payload = {}, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") return feedbackErrorResult("Feedback service unavailable");
    try {
      const response = await fetcher(FEEDBACK_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload || {}),
      });
      if (response?.ok) return { ok: true, localOnly: false, message: "" };
      const detail = await response.text().catch(() => "");
      return feedbackErrorResult(`HTTP ${response?.status || "unknown"}${detail ? `: ${detail}` : ""}`);
    } catch (error) {
      return feedbackErrorResult(error);
    }
  }

  global.ResearchOSFeedbackClient = Object.freeze({
    canSubmitFeedbackAsync,
    endpoint: FEEDBACK_ENDPOINT,
    feedbackErrorResult,
    submitFeedbackPayload,
  });
})(window);
