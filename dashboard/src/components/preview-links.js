/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 可复用 UI 组件「preview links」；只生成通用结构，业务语义由调用方传入。
 * English: Reusable ResearchOS dashboard UI component for preview links; renders generic structure while callers provide domain semantics.
 */

(function attachResearchOSPreviewLinksComponent(global) {
  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      previewExists: deps.previewExists || (() => false),
      simpleText: deps.simpleText || ((key) => key),
    };
  }

  function previewButton(path = "", label = "", deps = {}) {
    const { escapeHtml, previewExists, simpleText } = normalizeDeps(deps);
    if (!previewExists(path)) return "";
    const fallbackLabel = simpleText("assetCardViewEvidence") || simpleText("openPreview") || "Preview";
    const visibleLabel = String(label || fallbackLabel);
    const accessibleLabel = String(deps.ariaLabel || visibleLabel);
    const pdf = /\.pdf(?:[?#].*)?$/i.test(String(path || "").trim());
    if (pdf) {
      const pdfTitle = String(path || "").split(/[\\/]/).pop() || visibleLabel;
      return `<button type="button" class="inline-preview-button pdf-inline-preview" data-action-kind="navigation" data-pdf-preview-path="${escapeHtml(path)}" data-pdf-preview-title="${escapeHtml(pdfTitle)}" title="${escapeHtml(simpleText("openPreviewHint"))}" aria-label="${escapeHtml(accessibleLabel)}">${escapeHtml(visibleLabel)}</button>`;
    }
    const anchor = deps.anchor ? ` data-preview-anchor="${escapeHtml(deps.anchor)}"` : "";
    return `<button type="button" class="inline-preview-button" data-action-kind="navigation" data-preview-path="${escapeHtml(path)}"${anchor} title="${escapeHtml(simpleText("openPreviewHint"))}" aria-label="${escapeHtml(accessibleLabel)}">${escapeHtml(visibleLabel)}</button>`;
  }

  function resolvedPreviewButton(path = "", label = "", deps = {}) {
    const resolvePreviewLink = typeof deps.resolvePreviewLink === "function" ? deps.resolvePreviewLink : () => null;
    const resolveDocument = typeof deps.resolveDocument === "function" ? deps.resolveDocument : () => null;
    const resolved = resolvePreviewLink("", path, { resolveDocument });
    if (!resolved?.path) return "";
    return previewButton(resolved.path, label, {
      ...deps,
      anchor: resolved.anchor || "",
      previewExists: () => true,
    });
  }

  global.ResearchOSPreviewLinksComponent = Object.freeze({
    previewButton,
    resolvedPreviewButton,
  });
  global.document?.documentElement?.setAttribute("data-researchos-preview-links-component", "ready");
})(window);
