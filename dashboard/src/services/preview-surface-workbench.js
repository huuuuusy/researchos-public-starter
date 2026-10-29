/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「preview surface workbench」；负责 DOM 事件绑定，把副作用回调交还 app。
 * English: Workbench interaction adapter for preview surface workbench in the ResearchOS dashboard; owns DOM event binding and returns side effects to app callbacks.
 */

(function attachResearchOSPreviewSurfaceWorkbenchService(global) {
  const { bindAll, bindOne } = global.ResearchOSInteractions;

  function bindMarkdownPreviewButtons(root = global.document, callbacks = {}) {
    const { onOpenPath = () => {} } = callbacks;
    bindAll(root, "[data-preview-path]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onOpenPath({
        anchor: button.dataset.previewAnchor || "",
        button,
        event,
        path: button.dataset.previewPath || "",
      });
    });
  }

  function bindPdfPreviewButtons(root = global.document, callbacks = {}) {
    const { onOpenPdf = () => {} } = callbacks;
    bindAll(root, "[data-pdf-preview-path]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onOpenPdf({
        button,
        event,
        path: button.dataset.pdfPreviewPath || "",
        title: button.dataset.pdfPreviewTitle || button.textContent?.trim?.() || "",
      });
    });
  }

  function bindPdfPreviewFrameEvents(root = global.document, callbacks = {}) {
    const { onClose = () => {} } = callbacks;
    bindOne(root, "[data-pdf-close]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onClose({ button, event });
    });
  }

  function bindPreviewSurfaceEvents(root = global.document, callbacks = {}) {
    bindMarkdownPreviewButtons(root, callbacks);
    bindPdfPreviewButtons(root, callbacks);
  }

  global.ResearchOSPreviewSurfaceWorkbenchService = Object.freeze({
    bindMarkdownPreviewButtons,
    bindPdfPreviewButtons,
    bindPdfPreviewFrameEvents,
    bindPreviewSurfaceEvents,
  });
})(window);
