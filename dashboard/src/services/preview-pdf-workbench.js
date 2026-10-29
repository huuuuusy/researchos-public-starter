/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「preview PDF workbench」；负责 PDF 浮层状态和 DOM 生命周期，把 HTML 与事件规则委托给专门模块。
 * English: Workbench interaction adapter for the preview PDF surface; owns PDF floating-frame state and DOM lifecycle while delegating HTML and event rules.
 */

(function attachResearchOSPreviewPdfWorkbenchService(global) {
  function createPreviewPdfWorkbench(options = {}) {
    const {
      document = global.document,
      escapeHtml = global.ResearchOSUiCore?.escapeHtml,
      isPdfPreviewPath = () => false,
      normalizePreviewPath = (path) => String(path ?? ""),
      pdfPreviewLabel = (path) => String(path ?? ""),
      pdfPreviewView = global.ResearchOSPdfPreviewView,
      previewSurfaceWorkbench = global.ResearchOSPreviewSurfaceWorkbenchService,
      translate = (key) => key,
    } = options;

    const PDF_PREVIEW_ROOT_ID = "pdfPreviewFloat";
    const PDF_PREVIEW_ROOT_CLASS = "pdf-preview-float";
    const GENERIC_PDF_LABELS = new Set([
      "", "pdf", "pdf preview", "preview", "预览",
      "view pdf", "open pdf", "open local pdf", "click to open local pdf",
      "查看 pdf", "打开 pdf", "打开本地 pdf", "点击打开本地 pdf",
    ]);
    let pdfPreviewOpen = false;
    let pdfPreviewPath = "";
    let pdfPreviewTitle = "";
    let pdfPreviewMode = "document";

    function pdfPreviewRoot(root = document) {
      return root?.querySelector?.("[data-preview-pdf-pane]")
        || document?.getElementById?.(PDF_PREVIEW_ROOT_ID)
        || null;
    }

    function clearPdfPreviewRoot(root = document) {
      const previewRoot = pdfPreviewRoot(root);
      if (previewRoot) previewRoot.innerHTML = "";
    }

    function displayPdfTitle(path, rawTitle = "") {
      const candidateTitle = String(rawTitle || "").trim();
      const normalizedTitle = candidateTitle.toLowerCase().replace(/\s+/g, " ");
      const genericLocalLabel = /^local\s+source$/i.test(candidateTitle) || candidateTitle === "\u672c\u5730\u6765\u6e90";
      if (candidateTitle && !GENERIC_PDF_LABELS.has(normalizedTitle) && !genericLocalLabel) return candidateTitle;
      return pdfPreviewLabel(path);
    }

    function resetPdfPaneScroll(root = document) {
      const previewRoot = pdfPreviewRoot(root);
      const paneStack = previewRoot?.closest?.(".preview-pane-stack");
      if (paneStack) paneStack.scrollTop = 0;
      if (previewRoot) previewRoot.scrollTop = 0;
    }

    function alignPdfPanelWithTopbar(root = document) {
      const previewRoot = pdfPreviewRoot(root);
      const panel = previewRoot?.closest?.(".markdown-preview-panel");
      if (!panel || typeof global.scrollTo !== "function") return;
      const topbarHeight = Number.parseFloat(
        global.getComputedStyle?.(document?.documentElement)?.getPropertyValue("--topbar-height") || "",
      ) || 0;
      const targetTop = topbarHeight + 12;
      const panelTop = panel.getBoundingClientRect().top;
      if (panelTop >= targetTop) return;
      const currentScroll = global.scrollY || document?.documentElement?.scrollTop || 0;
      global.scrollTo(global.scrollX || 0, Math.max(0, currentScroll + panelTop - targetTop));
    }

    function openPdfPreview(path, openOptions = {}) {
      const normalizedPath = normalizePreviewPath(path);
      if (!isPdfPreviewPath(normalizedPath)) return;
      pdfPreviewPath = normalizedPath;
      pdfPreviewTitle = displayPdfTitle(normalizedPath, openOptions.title);
      pdfPreviewOpen = true;
      pdfPreviewMode = "pdf";
      renderPdfPreview();
    }

    function closePdfPreview() {
      pdfPreviewOpen = false;
      pdfPreviewMode = "document";
      renderPdfPreview();
    }

    function showDocumentPreview() {
      pdfPreviewMode = "document";
      renderPdfPreview();
    }

    function showPdfPreview() {
      if (!pdfPreviewOpen || !pdfPreviewPath) return;
      pdfPreviewMode = "pdf";
      renderPdfPreview();
    }

    function renderPdfPreview(rootContext = document) {
      const root = pdfPreviewRoot(rootContext);
      if (!pdfPreviewOpen || !pdfPreviewPath) {
        clearPdfPreviewRoot(rootContext);
        return;
      }
      if (!root) return;
      root.id = PDF_PREVIEW_ROOT_ID;
      root.classList.add(PDF_PREVIEW_ROOT_CLASS);
      root.hidden = pdfPreviewMode !== "pdf";
      root.setAttribute("aria-label", translate("preview.pdfTitle"));
      root.innerHTML = pdfPreviewView.renderPdfPreviewFrame(
        {
          closeLabel: translate("preview.pdfClose"),
          fallbackTitle: translate("preview.pdfTitle"),
          hint: translate("preview.pdfHint"),
          openTabLabel: translate("preview.pdfOpenTab"),
          path: pdfPreviewPath,
          technicalLabel: translate("preview.pdfPath"),
          title: pdfPreviewTitle || pdfPreviewLabel(pdfPreviewPath),
        },
        { escapeHtml },
      );
      previewSurfaceWorkbench.bindPdfPreviewFrameEvents(root, {
        onClose: () => closePdfPreview(),
      });
      if (pdfPreviewMode === "pdf") {
        resetPdfPaneScroll(rootContext);
        alignPdfPanelWithTopbar(rootContext);
      }
    }

    function state() {
      return {
        mode: pdfPreviewMode,
        open: pdfPreviewOpen,
        path: pdfPreviewPath,
        title: pdfPreviewTitle,
      };
    }

    return Object.freeze({
      closePdfPreview,
      isOpen: () => pdfPreviewOpen,
      openPdfPreview,
      renderPdfPreview,
      showDocumentPreview,
      showPdfPreview,
      state,
    });
  }

  global.ResearchOSPreviewPdfWorkbenchService = Object.freeze({
    createPreviewPdfWorkbench,
  });
})(window);
