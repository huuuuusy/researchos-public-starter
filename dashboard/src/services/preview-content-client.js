/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端客户端「preview content」；集中管理 Markdown preview 内容加载规则。
 * English: Frontend preview-content client for ResearchOS; centralizes Markdown preview content loading rules.
 */

(function attachResearchOSPreviewContentClient(global) {
  const PREVIEW_CONTENT_ENDPOINT = "/preview";

  function previewContentUrl(path = "") {
    return `${PREVIEW_CONTENT_ENDPOINT}?path=${encodeURIComponent(path)}`;
  }

  async function loadPreviewContent(path = "", deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") throw new Error("Preview content service unavailable");
    const response = await fetcher(previewContentUrl(path), { cache: "no-store" });
    if (!response?.ok) throw new Error(`HTTP ${response?.status || "unknown"}`);
    return response.text();
  }

  global.ResearchOSPreviewContentClient = Object.freeze({
    endpoint: PREVIEW_CONTENT_ENDPOINT,
    loadPreviewContent,
    previewContentUrl,
  });
})(window);
