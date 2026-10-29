/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「preview documents」；承接可复用逻辑，避免 app.js 重新变成大杂烩。
 * English: Frontend service for preview documents in the ResearchOS dashboard; keeps reusable logic out of app.js so it does not become a catch-all again.
 */

(function () {
  function previewFallbackDocuments(paths = {}, text = (key) => key) {
    return [
      {
        path: paths.confirmation,
        title: text("codexInboxFile"),
        layer: "06_active_context",
        sensitivity: "internal",
        updated: "",
        priority: 0,
      },
      {
        path: paths.feedback,
        title: text("codexFeedbackInboxFile"),
        layer: "06_active_context",
        sensitivity: "sensitive",
        updated: "",
        priority: 1,
      },
      ...(Array.isArray(paths.candidates) ? paths.candidates : []).map((source) => ({
        path: source.path,
        title: source.label || source.key || text("unifiedInboxSource"),
        layer: "06_active_context",
        sensitivity: "internal",
        updated: "",
        priority: 1,
      })),
      {
        path: paths.cardGroups,
        title: text("cardGroupInboxOpen"),
        layer: "06_active_context",
        sensitivity: "internal",
        updated: "",
        priority: 1,
      },
      {
        path: paths.cardGroupDissolution,
        title: text("cardGroupDissolveInboxOpen"),
        layer: "06_active_context",
        sensitivity: "internal",
        updated: "",
        priority: 1,
      },
    ].filter((item) => item.path);
  }

  function resolvePreviewDoc(path, {
    documents = [],
    normalizePath = (value) => String(value || ""),
    paths = {},
    text = (key) => key,
  } = {}) {
    const normalizedPath = normalizePath(path);
    const found = (Array.isArray(documents) ? documents : []).find((item) => item?.path === normalizedPath);
    if (found) return found;
    return previewFallbackDocuments(paths, text).find((item) => item.path === normalizedPath) || null;
  }

  window.ResearchOSPreviewDocuments = {
    previewFallbackDocuments,
    resolvePreviewDoc,
  };
})();
