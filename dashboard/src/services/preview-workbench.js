/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「preview workbench」；负责 DOM 事件绑定，把副作用回调交还 app。
 * English: Workbench interaction adapter for preview workbench in the ResearchOS dashboard; owns DOM event binding and returns side effects to app callbacks.
 */

(function attachResearchOSPreviewWorkbenchService(global) {
  const interactionPrimitives = global.ResearchOSInteractions || {};
  const focusElement = interactionPrimitives.focusElement || ((target) => {
    target?.focus?.();
    return Boolean(target);
  });
  const scrollIntoView = interactionPrimitives.scrollIntoView || ((target, options = {}) => {
    target?.scrollIntoView?.(options);
    return Boolean(target);
  });

  function createPreviewWorkbench(options = {}) {
    const {
      escapeHtml = global.ResearchOSUiCore?.escapeHtml,
      feedbackStorageKey = "",
      getDocuments = () => [],
      historyIndexKey = "",
      historyKey = "",
      initialState = {},
      onBindTooltips = () => {},
      onFeedbackSaved = () => {},
      paths = {},
      services = {},
      simpleText = (key) => key,
      translate = (key) => key,
    } = options;

    const previewService = services.preview || global.ResearchOSPreviewService;
    const previewContentClient = services.contentClient || global.ResearchOSPreviewContentClient;
    const previewMarkdownService = services.markdown || global.ResearchOSPreviewMarkdownService;
    const previewFeedbackService = services.feedback || global.ResearchOSPreviewFeedbackService;
    const feedbackClient = services.feedbackClient || global.ResearchOSFeedbackClient;
    const previewFeedbackWorkflowFactory = services.feedbackWorkflowService || global.ResearchOSPreviewFeedbackWorkflow;
    const previewDocumentsService = services.documents || global.ResearchOSPreviewDocuments;
    const previewState = services.state || global.ResearchOSPreviewState;
    const previewSessionStateService = services.sessionState || global.ResearchOSPreviewSessionState;
    const previewSurfaceWorkbench = services.surfaceWorkbench || global.ResearchOSPreviewSurfaceWorkbenchService;
    const previewPdfWorkbenchService = services.pdfWorkbench || global.ResearchOSPreviewPdfWorkbenchService;
    const markdownPreviewWorkbench = services.markdownWorkbench || global.ResearchOSMarkdownPreviewWorkbenchService;
    const markdownPreviewView = services.markdownView || global.ResearchOSMarkdownPreviewView;
    const pdfPreviewView = services.pdfView || global.ResearchOSPdfPreviewView;

    const previewSessionState = previewSessionStateService.createPreviewSessionState({
      historyIndexKey,
      historyKey,
      initialState,
      previewService,
      previewState,
    });
    const previewFeedbackWorkflow = services.feedbackWorkflow || previewFeedbackWorkflowFactory.createPreviewFeedbackWorkflow({
      feedbackStorageKey,
      services: {
        feedback: previewFeedbackService,
        feedbackClient,
      },
      simpleText,
    });
    let scheduledRestorePath = "";

    function previewDocuments() {
      const documents = getDocuments();
      return Array.isArray(documents) ? documents : [];
    }

    const { isPdfPreviewPath, normalizePreviewPath, resolveRelativeMdPath } = previewService;

    function pdfPreviewLabel(path) {
      return previewService.pdfPreviewLabel(path, translate("preview.pdfTitle"));
    }

    function getPreviewDoc(path) {
      return previewDocumentsService.resolvePreviewDoc(path, {
        documents: previewDocuments(),
        normalizePath: normalizePreviewPath,
        paths,
        text: simpleText,
      });
    }

    const previewPdfController = previewPdfWorkbenchService.createPreviewPdfWorkbench({
      document: global.document,
      escapeHtml,
      isPdfPreviewPath,
      normalizePreviewPath,
      pdfPreviewLabel,
      pdfPreviewView,
      previewSurfaceWorkbench,
      translate,
    });

    function markdownToHtml(markdown, basePath = "") {
      return previewMarkdownService.markdownToHtml(markdown, basePath, {
        escapeHtml,
        resolveDocument: getPreviewDoc,
      });
    }

    function previewShell() {
      return global.document.querySelector(".dashboard-shell");
    }

    function previewResizeHandle() {
      return global.document.getElementById("previewResizeHandle");
    }

    function clampPreviewPanelWidth(width) {
      const shell = previewShell();
      const shellWidth = shell?.getBoundingClientRect?.().width || global.innerWidth || 1280;
      const minWidth = Math.min(420, Math.max(340, shellWidth * 0.28));
      const maxWidth = Math.max(minWidth, Math.min(760, shellWidth - 520));
      const value = Number(width);
      if (!Number.isFinite(value) || value <= 0) return 0;
      return Math.round(Math.min(maxWidth, Math.max(minWidth, value)));
    }

    function applyPreviewPanelWidth(width, { persist = false } = {}) {
      const shell = previewShell();
      const handle = previewResizeHandle();
      if (!shell) return 0;
      const nextWidth = clampPreviewPanelWidth(width);
      if (!nextWidth) {
        shell.style.removeProperty("--preview-panel-width");
        handle?.removeAttribute("aria-valuenow");
        return 0;
      }
      shell.style.setProperty("--preview-panel-width", `${nextWidth}px`);
      handle?.setAttribute("aria-valuenow", String(nextWidth));
      if (persist) previewState.writePanelWidth?.(nextWidth);
      return nextWidth;
    }

    function restorePreviewPanelWidth() {
      const storedWidth = previewState.readPanelWidth?.() || 0;
      if (storedWidth) applyPreviewPanelWidth(storedWidth);
    }

    function bindPreviewResizeHandle() {
      const handle = previewResizeHandle();
      const shell = previewShell();
      if (!handle || !shell || handle.__researchosPreviewResizeBound) return;
      handle.__researchosPreviewResizeBound = true;
      handle.setAttribute("role", "separator");
      handle.setAttribute("aria-orientation", "vertical");
      handle.setAttribute("aria-valuemin", "340");
      handle.setAttribute("aria-valuemax", "760");
      handle.addEventListener("pointerdown", (event) => {
        if (global.matchMedia?.("(max-width: 1180px)")?.matches) return;
        event.preventDefault();
        handle.setPointerCapture?.(event.pointerId);
        shell.classList.add("preview-resizing");
        const resize = (moveEvent) => {
          const shellRect = shell.getBoundingClientRect();
          applyPreviewPanelWidth(shellRect.right - moveEvent.clientX);
        };
        const stop = (upEvent) => {
          resize(upEvent);
          previewState.writePanelWidth?.(clampPreviewPanelWidth(shell.getBoundingClientRect().right - upEvent.clientX));
          shell.classList.remove("preview-resizing");
          handle.releasePointerCapture?.(event.pointerId);
          global.document.removeEventListener("pointermove", resize);
          global.document.removeEventListener("pointerup", stop);
          global.document.removeEventListener("pointercancel", stop);
        };
        global.document.addEventListener("pointermove", resize);
        global.document.addEventListener("pointerup", stop);
        global.document.addEventListener("pointercancel", stop);
      });
      handle.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        const currentWidth = clampPreviewPanelWidth(
          previewState.readPanelWidth?.()
            || global.document.getElementById("markdownPreviewPanel")?.getBoundingClientRect?.().width
            || 0
        );
        if (event.key === "Home") {
          applyPreviewPanelWidth(340, { persist: true });
          return;
        }
        if (event.key === "End") {
          applyPreviewPanelWidth(760, { persist: true });
          return;
        }
        const delta = event.shiftKey ? 48 : 24;
        const direction = event.key === "ArrowLeft" ? 1 : -1;
        applyPreviewPanelWidth(currentWidth + (direction * delta), { persist: true });
      });
    }

    function navigatePreviewHistory(direction) {
      const navigation = previewSessionState.navigateHistory(direction);
      if (!navigation) return;
      openMarkdownPreview(navigation.entry.path, {
        anchor: navigation.entry.anchor || "",
        fromHistory: true,
      });
    }

    async function closePreviewTab(path = "", anchor = "") {
      const result = previewSessionState.closeHistoryEntry(path, anchor);
      if (result.closedCurrent && result.entry?.path) {
        await openMarkdownPreview(result.entry.path, {
          anchor: result.entry.anchor || "",
          focusPanel: false,
          fromHistory: true,
          scrollPanel: false,
        });
        restorePreviewFocus();
        return;
      }
      if (result.closedCurrent && !result.entry) {
        renderMarkdownPreview();
        restorePreviewFocus();
        return;
      }
      renderMarkdownPreview();
      restorePreviewFocus();
    }

    function restorePreviewFocus() {
      global.requestAnimationFrame?.(() => {
        const target = global.document.querySelector?.(".preview-history-tabs .preview-tab-card.selected > button:not(.preview-tab-close)")
          || global.document.querySelector?.(".preview-show-button")
          || global.document.getElementById?.("previewCollapse");
        focusElement(target, { preventScroll: true });
      });
    }

    function scrollPreviewToAnchor(anchor) {
      if (!anchor) return;
      const body = global.document.querySelector("#markdownPreview .markdown-body");
      if (!body) return;
      const slug = previewMarkdownService.slugifyMarkdownHeading(decodeURIComponent(anchor));
      const target =
        body.querySelector(`#${global.CSS.escape(slug)}`) ||
        body.querySelector(`#${global.CSS.escape(anchor)}`);
      if (!target) return;
      body.querySelectorAll(".md-preview-anchor-highlight").forEach((item) => {
        item.classList.remove("md-preview-anchor-highlight");
      });
      target.classList.add("md-preview-anchor-highlight");
      scrollIntoView(target, { block: "start", behavior: "smooth" });
    }

    function openPdfPreview(path, openOptions = {}) {
      previewSessionState.setOpen(true);
      previewPdfController.openPdfPreview(path, openOptions);
      renderMarkdownPreview();
      scrollIntoView(global.document.getElementById("markdownPreviewPanel"), { block: "nearest", behavior: "smooth" });
    }

    function renderPdfPreview() {
      return previewPdfController.renderPdfPreview(global.document.getElementById("markdownPreview"));
    }

    function isPublicStarterPreviewPath(path = "") {
      return normalizePreviewPath(path).startsWith("08_exports/public_starter/");
    }

    function previewHistoryTabs(previewSnapshot = {}) {
      const history = Array.isArray(previewSnapshot.history) ? previewSnapshot.history : [];
      const publicStarterMode = isPublicStarterPreviewPath(previewSnapshot.selectedPath);
      const seen = new Set();
      // 中文：public starter 预览只能显示 public starter 历史，避免 DOM 或 UI 泄露私人 vault 路径。
      // English: Public-starter preview shows public-starter history only, preventing private vault paths from leaking through UI or DOM state.
      return history
        .slice()
        .reverse()
        .map((entry) => {
          const path = normalizePreviewPath(entry?.path || "");
          if (!path || seen.has(path)) return null;
          if (publicStarterMode && !isPublicStarterPreviewPath(path)) return null;
          seen.add(path);
          const doc = getPreviewDoc(path);
          if (!doc) return null;
          return {
            anchor: entry.anchor || "",
            layer: doc.layer || "",
            path,
            title: doc.title || path,
          };
        })
        .filter(Boolean)
        .slice(0, 8)
        .reverse();
    }

    async function openMarkdownPreview(path, openOptions = {}) {
      const doc = getPreviewDoc(path);
      if (!doc) return;
      previewPdfController.showDocumentPreview();
      previewSessionState.startMarkdownOpen(path, { anchor: openOptions.anchor || "" });
      if (!openOptions.fromHistory) previewSessionState.pushHistory(path, openOptions.anchor || "");
      renderMarkdownPreview();
      try {
        previewSessionState.setContent(await previewContentClient.loadPreviewContent(path));
      } catch {
        previewSessionState.setError(translate("preview.error"));
      } finally {
        const currentState = previewSessionState.finishMarkdownLoad();
        renderMarkdownPreview();
        if (currentState.anchor) {
          global.requestAnimationFrame(() => scrollPreviewToAnchor(currentState.anchor));
        }
        if (openOptions.scrollPanel !== false) {
          scrollIntoView(global.document.getElementById("markdownPreviewPanel"), { block: "nearest", behavior: "smooth" });
        }
        if (openOptions.focusPanel) {
          focusElement(global.document.getElementById("previewCollapse"), { preventScroll: true });
        }
      }
    }

    function capturePreviewSelection(root = global.document) {
      const selection = global.getSelection?.();
      const text = previewFeedbackService.normalizePreviewSelectedText(selection?.toString?.() || "");
      if (!text) return;
      const anchor = selection.anchorNode?.nodeType === global.Node.ELEMENT_NODE
        ? selection.anchorNode
        : selection.anchorNode?.parentElement;
      if (!anchor?.closest?.("#markdownPreview .markdown-body")) return;
      previewSessionState.setSelectedText(text);
      renderMarkdownPreview();
      scrollIntoView(root.querySelector("[data-preview-feedback]"), { block: "nearest", behavior: "smooth" });
    }

    async function submitPreviewFeedback(selectedDoc, root = global.document) {
      const previewStateSnapshot = previewSessionState.snapshot();
      const box = root.querySelector("[data-preview-feedback-input]");
      const category = root.querySelector("[data-preview-feedback-category]")?.value;
      const status = root.querySelector("[data-preview-feedback-status]");
      const feedback = String(box?.value || "").trim();
      if (!selectedDoc?.path) return;
      if (!feedback) {
        if (status) status.textContent = simpleText("previewFeedbackEmpty");
        box?.focus();
        return;
      }
      const submission = await previewFeedbackWorkflow.submitPreviewFeedback({
        category,
        feedback,
        selectedDoc,
        selectedText: previewStateSnapshot.selectedText,
      });
      if (!submission.ok) return;
      previewSessionState.markFeedbackSaved(
        simpleText(submission.localOnly ? "previewFeedbackLocalSaved" : "previewFeedbackSaved")
      );
      renderMarkdownPreview();
      onFeedbackSaved();
    }

    function renderMarkdownPreview() {
      const panel = global.document.getElementById("markdownPreviewPanel");
      const root = global.document.getElementById("markdownPreview");
      const collapse = global.document.getElementById("previewCollapse");
      if (!panel || !root || !collapse) return;
      const previewSnapshot = previewSessionState.snapshot();
      panel.classList.toggle("collapsed", !previewSnapshot.open);
      const historyTabs = previewHistoryTabs(previewSnapshot);
      panel.classList.toggle("has-history", Boolean(historyTabs.length));
      restorePreviewPanelWidth();
      bindPreviewResizeHandle();
      root.dataset.previewHistoryIndex = String(previewSnapshot.historyIndex);
      root.dataset.previewHistorySize = String(previewSnapshot.history.length);
      root.dataset.previewHistoryPaths = historyTabs.map((entry) => entry.path).join("||");
      collapse.textContent = previewSnapshot.open ? translate("preview.hide") : translate("preview.show");
      collapse.setAttribute("aria-expanded", String(previewSnapshot.open));
      collapse.setAttribute("aria-label", collapse.textContent);
      collapse.title = collapse.textContent;
      const togglePreviewOpen = (open = !previewSessionState.snapshot().open) => {
        previewSessionState.setOpen(open);
        renderMarkdownPreview();
        if (open) ensureSelectedPreviewLoaded();
      };
      markdownPreviewWorkbench.bindMarkdownPreviewEvents({
        root,
        collapse,
        callbacks: {
          onTogglePreview: () => togglePreviewOpen(!previewSessionState.snapshot().open),
        },
      });
      if (!previewSnapshot.open) {
        root.innerHTML = markdownPreviewView.renderCollapsedPreview(
          {
            historyTabs,
            label: translate("preview.show"),
            selectedPreviewPath: previewSnapshot.selectedPath,
          },
          { escapeHtml, simpleText, translate }
        );
        markdownPreviewWorkbench.bindMarkdownPreviewEvents({
          root,
          collapse,
          callbacks: {
            onOpenPath: ({ path, anchor }) => openMarkdownPreview(path, { anchor }),
            onShowPreview: () => togglePreviewOpen(true),
            onClosePath: ({ path, anchor }) => closePreviewTab(path, anchor),
            onTogglePreview: () => togglePreviewOpen(!previewSessionState.snapshot().open),
          },
        });
        return;
      }

      const docs = previewDocuments();
      const selectedDoc = getPreviewDoc(previewSnapshot.selectedPath);
      const normalizedSearch = previewSnapshot.searchTerm.trim().toLowerCase();
      const filtered = docs.filter((doc) => {
        if (!normalizedSearch) return true;
        return `${doc.title} ${doc.path} ${doc.layer}`.toLowerCase().includes(normalizedSearch);
      });
      const matches = filtered.slice(0, 80);
      const tooMany = filtered.length > matches.length;
      const browserOpen = !selectedDoc || previewSnapshot.searchTerm ? "open" : "";
      const pdfPreviewState = previewPdfController.state();

      root.innerHTML = markdownPreviewView.renderMarkdownPreviewHtml(
        {
          browserOpen,
          canBack: previewSessionState.canBack(),
          canForward: previewSessionState.canForward(),
          matches,
          previewContent: previewSnapshot.content,
          previewError: previewSnapshot.error,
          previewFeedbackDraft: previewSnapshot.feedbackDraft,
          previewFeedbackStatusText: previewSnapshot.feedbackStatusText,
          previewHistoryTabs: historyTabs,
          previewLoadingPath: previewSnapshot.loadingPath,
          previewSearchTerm: previewSnapshot.searchTerm,
          previewSelectedText: previewSnapshot.selectedText,
          previewMode: pdfPreviewState.mode,
          pdfPreviewOpen: pdfPreviewState.open,
          pdfPreviewTitle: pdfPreviewState.title,
          selectedDoc,
          selectedPreviewPath: previewSnapshot.selectedPath,
          tooMany,
        },
        {
          escapeHtml,
          markdownToHtml,
          simpleText,
          translate,
        }
      );
      markdownPreviewWorkbench.bindMarkdownPreviewEvents({
        root,
        collapse,
        callbacks: {
          onBindPdfButtons: ({ root: previewRoot }) => bindPdfPreviewButtons(previewRoot),
          onBindTooltips: ({ root: previewRoot }) => onBindTooltips(previewRoot),
          onCaptureSelection: ({ root: previewRoot }) => {
            global.setTimeout(() => capturePreviewSelection(previewRoot), 0);
          },
          onFeedbackInput: ({ value }) => {
            previewSessionState.setFeedbackDraft(value);
          },
          onFeedbackSubmit: ({ root: previewRoot }) => {
            submitPreviewFeedback(selectedDoc, previewRoot);
          },
          onClosePath: ({ path, anchor }) => closePreviewTab(path, anchor),
          onHistory: ({ direction }) => navigatePreviewHistory(direction),
          onOpenPath: ({ path, anchor }) => openMarkdownPreview(path, { anchor }),
          onPreviewMode: ({ mode }) => {
            if (mode === "pdf") {
              previewPdfController.showPdfPreview();
            } else {
              previewPdfController.showDocumentPreview();
            }
            renderMarkdownPreview();
          },
          onSearchInput: ({ value }) => {
            previewSessionState.setSearchTerm(value);
            renderMarkdownPreview();
          },
          onTogglePreview: () => togglePreviewOpen(!previewSessionState.snapshot().open),
        },
      });
      root.querySelectorAll("[data-preview-close-path]").forEach((button) => {
        button.onclick = (event) => {
          event.preventDefault();
          event.stopPropagation();
          closePreviewTab(button.dataset.previewClosePath || "", button.dataset.previewCloseAnchor || "");
        };
      });
      scrollIntoView(root.querySelector(".preview-history-tabs .preview-tab-card.selected"), {
        block: "nearest",
        inline: "nearest",
      });
      renderPdfPreview();
    }

    function bindPreviewButtons(root = global.document) {
      previewSurfaceWorkbench.bindPreviewSurfaceEvents(root, {
        onOpenPath: ({ path, anchor }) => {
          openMarkdownPreview(path, { anchor, focusPanel: true });
        },
        onOpenPdf: ({ path, title }) => {
          openPdfPreview(path, { title });
        },
      });
    }

    function bindPdfPreviewButtons(root = global.document) {
      previewSurfaceWorkbench.bindPdfPreviewButtons(root, {
        onOpenPdf: ({ path, title }) => {
          openPdfPreview(path, { title });
        },
      });
    }

    function bindPreviewHistoryNavigation() {
      if (global.__researchosPreviewHistoryBound) return;
      global.__researchosPreviewHistoryBound = true;
      global.document.addEventListener(
        "click",
        (event) => {
          const target = event.target?.nodeType === global.Node.ELEMENT_NODE
            ? event.target
            : event.target?.parentElement;
          const button = target?.closest?.("[data-preview-history]");
          if (!button || !button.closest("#markdownPreview")) return;
          event.preventDefault();
          event.stopPropagation();
          navigatePreviewHistory(button.dataset.previewHistory === "back" ? -1 : 1);
        },
        true,
      );
    }

    function ensureSelectedPreviewLoaded() {
      const previewSnapshot = previewSessionState.snapshot();
      if (
        !previewSnapshot.selectedPath ||
        !previewSnapshot.open ||
        previewSnapshot.content ||
        previewSnapshot.loadingPath ||
        previewSnapshot.error
      ) return false;
      const selectedPath = normalizePreviewPath(previewSnapshot.selectedPath);
      if (!selectedPath || !getPreviewDoc(selectedPath) || scheduledRestorePath === selectedPath) return false;
      scheduledRestorePath = selectedPath;
      global.setTimeout(async () => {
        try {
          const currentState = previewSessionState.snapshot();
          if (
            normalizePreviewPath(currentState.selectedPath) !== selectedPath ||
            !currentState.open ||
            currentState.content ||
            currentState.loadingPath ||
            currentState.error
          ) return;
          await openMarkdownPreview(selectedPath, {
            fromHistory: true,
            scrollPanel: false,
          });
        } finally {
          if (scheduledRestorePath === selectedPath) scheduledRestorePath = "";
        }
      }, 0);
      return true;
    }

    function setPreviewOpen(open) {
      return previewSessionState.setOpen(open);
    }

    return Object.freeze({
      bindPreviewButtons,
      bindPreviewHistoryNavigation,
      ensureSelectedPreviewLoaded,
      getPreviewDoc,
      openMarkdownPreview,
      renderMarkdownPreview,
      resolveRelativeMdPath,
      setPreviewOpen,
    });
  }

  global.ResearchOSPreviewWorkbenchService = Object.freeze({
    createPreviewWorkbench,
  });
})(window);
