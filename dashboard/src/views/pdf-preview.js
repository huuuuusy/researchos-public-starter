/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 视图「PDF preview」的纯 HTML 渲染层；不保存持久状态、不直接执行写入副作用。
 * English: Pure HTML rendering layer for the PDF preview dashboard view; stores no durable state and performs no write side effects.
 */

(function attachResearchOSPdfPreviewView(global) {
  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
    };
  }

  function pdfPreviewSrc(path = "") {
    return `/pdf?path=${encodeURIComponent(path)}`;
  }

  function renderPdfPreviewFrame({
    closeLabel = "",
    fallbackTitle = "",
    hint = "",
    openTabLabel = "",
    path = "",
    technicalLabel = "",
    title = "",
  } = {}, deps = {}) {
    const { escapeHtml } = normalizeDeps(deps);
    const displayTitle = title || fallbackTitle;
    const src = pdfPreviewSrc(path);
    return `
      <header class="pdf-preview-toolbar">
        <div class="pdf-preview-title-block">
          <span class="pdf-preview-kicker">${escapeHtml(hint)}</span>
          <strong title="${escapeHtml(displayTitle)}">${escapeHtml(displayTitle)}</strong>
        </div>
        <div class="pdf-preview-actions">
          <a href="${escapeHtml(src)}" target="_blank" rel="noreferrer" data-action-kind="navigation">${escapeHtml(openTabLabel)}</a>
          <button type="button" data-action-kind="navigation" data-pdf-close>${escapeHtml(closeLabel)}</button>
        </div>
      </header>
      <details class="pdf-preview-technical">
        <summary>${escapeHtml(technicalLabel || fallbackTitle)}</summary>
        <code>${escapeHtml(path)}</code>
      </details>
      <iframe class="pdf-preview-frame" title="${escapeHtml(displayTitle || fallbackTitle)}" src="${escapeHtml(src)}"></iframe>
    `;
  }

  global.ResearchOSPdfPreviewView = Object.freeze({
    pdfPreviewSrc,
    renderPdfPreviewFrame,
  });
  global.document?.documentElement?.setAttribute("data-researchos-pdf-preview-view", "ready");
})(window);
