/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 视图「markdown preview」的纯 HTML 渲染层；不保存持久状态、不直接执行写入副作用。
 * English: Pure HTML rendering layer for the markdown preview dashboard view; stores no durable state and performs no write side effects.
 */

(function attachResearchOSMarkdownPreviewView(global) {
  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      markdownToHtml: deps.markdownToHtml || ((content) => global.ResearchOSUiCore?.escapeHtml(content)),
      simpleText: deps.simpleText || ((key) => key),
      translate: deps.translate || ((key) => key),
    };
  }

  function renderCollapsedPreview({
    label = "",
  } = {}, deps = {}) {
    const { escapeHtml } = normalizeDeps(deps);
    return `<button type="button" class="preview-show-button" data-action-kind="navigation">${escapeHtml(label)}</button>`;
  }

  function renderPreviewMeta({ selectedDoc = null } = {}, deps = {}) {
    if (!selectedDoc) return "";
    const { escapeHtml, translate } = normalizeDeps(deps);
    const layerLabels = {
      "00_identity": translate("preview.layer.identity"),
      "01_knowledge": translate("preview.layer.knowledge"),
      "03_cognition": translate("preview.layer.cognition"),
      "04_people": translate("preview.layer.people"),
      "05_workflows": translate("preview.layer.workflows"),
      "06_active_context": translate("preview.layer.active"),
    };
    const sensitivityLabels = {
      internal: translate("preview.sensitivity.internal"),
      sensitive: translate("preview.sensitivity.sensitive"),
      private: translate("preview.sensitivity.private"),
      public: translate("preview.sensitivity.public"),
    };
    const metaItems = [
      layerLabels[selectedDoc.layer],
      sensitivityLabels[selectedDoc.sensitivity],
      selectedDoc.updated ? `${translate("preview.updated")}: ${selectedDoc.updated}` : "",
    ].filter(Boolean);
    if (!metaItems.length) return "";
    return `
      <div class="preview-meta">
        ${metaItems.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
      </div>
    `;
  }

  function renderCurrentDoc({ selectedDoc = null } = {}, deps = {}) {
    if (!selectedDoc) return "";
    const { escapeHtml, translate } = normalizeDeps(deps);
    return `
      <div class="preview-current">
        <div class="preview-current-main">
          <strong>${escapeHtml(selectedDoc.title)}</strong>
          <code title="${escapeHtml(selectedDoc.path)}">${escapeHtml(selectedDoc.path)}</code>
        </div>
        ${renderPreviewMeta({ selectedDoc }, deps)}
      </div>
    `;
  }

  function renderPreviewContent({
    previewContent = "",
    previewError = "",
    previewLoadingPath = "",
    selectedDoc = null,
  } = {}, deps = {}) {
    const { escapeHtml, markdownToHtml, translate } = normalizeDeps(deps);
    if (!selectedDoc) return `<div class="preview-empty">${escapeHtml(translate("preview.empty"))}</div>`;
    if (previewLoadingPath === selectedDoc.path) {
      return `<div class="preview-empty">${escapeHtml(translate("preview.loading"))}</div>`;
    }
    if (previewError) return `<div class="preview-empty">${escapeHtml(previewError)}</div>`;
    return `<section class="preview-evidence-content" aria-label="${escapeHtml(translate("preview.content"))}"><article class="markdown-body">${markdownToHtml(previewContent, selectedDoc.path)}</article></section>`;
  }

  function renderPreviewModeTabs({
    activeMode = "document",
    pdfPreviewOpen = false,
    pdfPreviewTitle = "",
  } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const pdfDisabled = pdfPreviewOpen ? "" : "disabled";
    return `
      <div class="preview-mode-tabs" role="group" aria-label="${escapeHtml(translate("preview.modeTabs"))}">
        <button type="button" data-action-kind="navigation" data-preview-mode="document" aria-pressed="${activeMode !== "pdf"}">
          ${escapeHtml(translate("preview.modeDocument"))}
        </button>
        <button type="button" data-action-kind="navigation" data-preview-mode="pdf" aria-pressed="${activeMode === "pdf"}" ${pdfDisabled}>
          ${escapeHtml(pdfPreviewOpen ? (pdfPreviewTitle || translate("preview.modePdf")) : translate("preview.modePdf"))}
        </button>
      </div>
    `;
  }

  function renderFeedbackPanel({
    previewFeedbackDraft = "",
    previewFeedbackStatusText = "",
    previewSelectedText = "",
    selectedDoc = null,
  } = {}, deps = {}) {
    if (!selectedDoc) return "";
    const { escapeHtml, simpleText } = normalizeDeps(deps);
    const categories = [
      simpleText("previewFeedbackCategoryDefault"),
      simpleText("previewFeedbackCategoryEvidence"),
      simpleText("previewFeedbackCategoryInterpret"),
      simpleText("previewFeedbackCategoryFix"),
      simpleText("previewFeedbackCategoryStructure"),
    ];
    const open = previewSelectedText || previewFeedbackDraft || previewFeedbackStatusText ? "open" : "";
    return `
      <details class="preview-feedback-panel" data-preview-feedback ${open}>
        <summary>
          <div>
            <strong>${escapeHtml(simpleText("previewFeedbackTitle"))}</strong>
            <span>${escapeHtml(simpleText("previewFeedbackHint"))}</span>
          </div>
        </summary>
        <div class="preview-feedback-selection">
          <span>${escapeHtml(previewSelectedText ? simpleText("previewFeedbackSelected") : simpleText("previewFeedbackNoSelection"))}</span>
          <p>${escapeHtml(previewSelectedText || simpleText("previewFeedbackSelectHint"))}</p>
        </div>
        <div class="preview-feedback-form">
          <label>
            <span>${escapeHtml(simpleText("feedbackCategory"))}</span>
            <select data-preview-feedback-category aria-label="${escapeHtml(simpleText("feedbackCategory"))}">
              ${categories.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("")}
            </select>
          </label>
          <label>
            <span>${escapeHtml(simpleText("confirmSuggestion"))}</span>
            <textarea data-preview-feedback-input aria-label="${escapeHtml(simpleText("confirmSuggestion"))}" placeholder="${escapeHtml(simpleText("previewFeedbackPlaceholder"))}">${escapeHtml(previewFeedbackDraft)}</textarea>
          </label>
        </div>
        <footer>
          <button type="button" data-action-kind="preview-confirm" data-preview-feedback-submit title="${escapeHtml(simpleText("previewFeedbackHint"))}">${escapeHtml(simpleText("previewFeedbackAdd"))}</button>
          <output data-preview-feedback-status>${escapeHtml(previewFeedbackStatusText || simpleText("previewFeedbackLocalOnly"))}</output>
        </footer>
      </details>
    `;
  }

  function renderHistoryControls({ canBack = false, canForward = false, selectedDoc = null } = {}, deps = {}) {
    if (!selectedDoc) return "";
    const { escapeHtml, translate } = normalizeDeps(deps);
    return `
      <div class="preview-nav" aria-label="${escapeHtml(translate("preview.title"))}">
        <button type="button" data-action-kind="navigation" data-preview-history="back" ${canBack ? "" : "disabled"}>${escapeHtml(translate("preview.back"))}</button>
        <button type="button" data-action-kind="navigation" data-preview-history="forward" ${canForward ? "" : "disabled"}>${escapeHtml(translate("preview.forward"))}</button>
      </div>
    `;
  }

  function renderPreviewToolbar({
    activeMode = "document",
    canBack = false,
    canForward = false,
    pdfPreviewOpen = false,
    pdfPreviewTitle = "",
    selectedDoc = null,
  } = {}, deps = {}) {
    return `
      <div class="preview-toolbar">
        ${renderPreviewModeTabs({ activeMode, pdfPreviewOpen, pdfPreviewTitle }, deps)}
        ${renderHistoryControls({ canBack, canForward, selectedDoc }, deps)}
      </div>
    `;
  }

  function renderHistoryTabs({
    historyTabs = [],
    selectedPreviewPath = "",
  } = {}, deps = {}) {
    const { escapeHtml, simpleText } = normalizeDeps(deps);
    if (!Array.isArray(historyTabs) || !historyTabs.length) return "";
    return `
      <div class="preview-history-tabs" role="list" aria-label="${escapeHtml(simpleText("preview.recentTabs"))}">
        ${historyTabs.map((tab) => `
          <span class="preview-tab-card ${tab.path === selectedPreviewPath ? "selected" : ""}" role="listitem">
            <button
              type="button"
              data-action-kind="navigation"
              data-preview-path="${escapeHtml(tab.path)}"
              data-preview-anchor="${escapeHtml(tab.anchor || "")}"
              ${tab.path === selectedPreviewPath ? 'aria-current="page"' : ""}
              title="${escapeHtml(tab.path)}"
            >
              <span>${escapeHtml(tab.title || tab.path)}</span>
              ${tab.layer ? `<small>${escapeHtml(tab.layer)}</small>` : ""}
            </button>
            <button
              type="button"
              class="preview-tab-close"
              data-action-kind="navigation"
              data-preview-close-path="${escapeHtml(tab.path)}"
              data-preview-close-anchor="${escapeHtml(tab.anchor || "")}"
              aria-label="${escapeHtml(simpleText("preview.closeTab"))}: ${escapeHtml(tab.title || tab.path)}"
              title="${escapeHtml(simpleText("preview.closeTab"))}"
            >×</button>
          </span>
        `).join("")}
      </div>
    `;
  }

  function renderBrowser({
    browserOpen = false,
    matches = [],
    previewSearchTerm = "",
    selectedPreviewPath = "",
    tooMany = false,
  } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    return `
      <details class="preview-browser" ${browserOpen ? "open" : ""}>
        <summary>${escapeHtml(translate("preview.sources"))}</summary>
        <label class="preview-search">
          <span>${escapeHtml(translate("preview.search"))}</span>
          <input type="search" value="${escapeHtml(previewSearchTerm)}" placeholder="${escapeHtml(translate("preview.searchPlaceholder"))}">
        </label>
        <div class="preview-doc-list">
          ${(matches || [])
            .map((doc) => `
              <button type="button" class="${doc.path === selectedPreviewPath ? "selected" : ""}" data-action-kind="navigation" data-preview-path="${escapeHtml(doc.path)}">
                <strong>${escapeHtml(doc.title)}</strong>
                <span>${escapeHtml([doc.sensitivity, doc.updated].filter(Boolean).join(" · ") || translate("preview.openHint"))}</span>
              </button>
            `)
            .join("")}
        </div>
        ${tooMany ? `<p class="preview-note">${escapeHtml(translate("preview.tooMany"))}</p>` : ""}
      </details>
    `;
  }

  function renderMarkdownPreviewHtml({
    browserOpen = false,
    canBack = false,
    canForward = false,
    matches = [],
    previewContent = "",
    previewError = "",
    previewFeedbackDraft = "",
    previewFeedbackStatusText = "",
    previewHistoryTabs = [],
    previewLoadingPath = "",
    previewSearchTerm = "",
    previewSelectedText = "",
    previewMode = "document",
    pdfPreviewOpen = false,
    pdfPreviewTitle = "",
    selectedDoc = null,
    selectedPreviewPath = "",
    tooMany = false,
  } = {}, deps = {}) {
    const activeMode = pdfPreviewOpen && previewMode === "pdf" ? "pdf" : "document";
    const documentHidden = activeMode === "pdf" ? "hidden" : "";
    const pdfHidden = activeMode === "pdf" ? "" : "hidden";
    return `
      ${renderPreviewToolbar({ activeMode, canBack, canForward, pdfPreviewOpen, pdfPreviewTitle, selectedDoc }, deps)}
      <div class="preview-pane-stack">
        <section class="preview-document-pane" data-preview-pane="document" ${documentHidden}>
          ${renderHistoryTabs({ historyTabs: previewHistoryTabs, selectedPreviewPath }, deps)}
          ${renderCurrentDoc({ selectedDoc }, deps)}
          ${renderPreviewContent({ previewContent, previewError, previewLoadingPath, selectedDoc }, deps)}
          ${renderFeedbackPanel({ previewFeedbackDraft, previewFeedbackStatusText, previewSelectedText, selectedDoc }, deps)}
          ${renderBrowser({ browserOpen, matches, previewSearchTerm, selectedPreviewPath, tooMany }, deps)}
        </section>
        <section id="pdfPreviewFloat" class="pdf-preview-float preview-pdf-pane" data-preview-pane="pdf" data-preview-pdf-pane ${pdfHidden}></section>
      </div>
    `;
  }

  global.ResearchOSMarkdownPreviewView = Object.freeze({
    renderBrowser,
    renderCollapsedPreview,
    renderCurrentDoc,
    renderFeedbackPanel,
    renderHistoryControls,
    renderHistoryTabs,
    renderMarkdownPreviewHtml,
    renderPreviewContent,
    renderPreviewModeTabs,
    renderPreviewMeta,
    renderPreviewToolbar,
  });
})(window);
