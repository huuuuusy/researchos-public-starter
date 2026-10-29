/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「unified inbox workbench」；负责 DOM 事件绑定，把副作用回调交还 app。
 * English: Workbench interaction adapter for unified inbox workbench in the ResearchOS dashboard; owns DOM event binding and returns side effects to app callbacks.
 */

(function attachResearchOSUnifiedInboxWorkbenchService(global) {
  const UNIFIED_INBOX_STATUS_SELECTOR = "[data-unified-inbox-status]";
  const { bindAll, bindOne } = global.ResearchOSInteractions;

  function splitInboxActionPayload(value = "") {
    const raw = String(value || "");
    const splitIndex = raw.indexOf(":");
    return {
      type: splitIndex >= 0 ? raw.slice(0, splitIndex) : "",
      id: splitIndex >= 0 ? raw.slice(splitIndex + 1) : "",
    };
  }

  function setUnifiedInboxStatus(message = "", root = global.document) {
    const status = root?.querySelector?.(UNIFIED_INBOX_STATUS_SELECTOR);
    if (!status) return false;
    status.textContent = String(message ?? "");
    return true;
  }

  function scheduleUnifiedInboxStatus(message = "", options = {}) {
    const delay = Number.isFinite(options.delay) ? options.delay : 0;
    const root = options.root || global.document;
    const applyStatus = () => setUnifiedInboxStatus(message, root);
    if (typeof global.setTimeout === "function") {
      global.setTimeout(applyStatus, delay);
      return true;
    }
    return applyStatus();
  }

  function decodeInboxJsonPayload(value = "", fallback = null) {
    try {
      const decoded = global.ResearchOSUiCore?.decodeDataPayload
        ? global.ResearchOSUiCore.decodeDataPayload(value || "")
        : decodeURIComponent(value || "");
      return JSON.parse(decoded);
    } catch {
      return fallback;
    }
  }

  function bindUnifiedInboxEvents(root, callbacks = {}) {
    if (!root) return;
    const {
      onArchive = () => {},
      onClear = () => {},
      onClearLocal = () => {},
      onCopy = () => {},
      onGenerate = () => {},
      onHandoff = () => {},
      onItemReviewDecision = () => {},
      onJudgment = () => {},
      onPreviewCards = () => {},
      onResolveArchived = () => {},
      onRunnerRefresh = () => {},
      onRestore = () => {},
      onRestoreAllArchived = () => {},
      onViewChange = () => {},
      onWorkFilter = () => {},
      onWithdraw = () => {},
    } = callbacks;

    bindAll(root, "[data-unified-inbox-view]", "click", (event, button) => {
      onViewChange(button.dataset.unifiedInboxView || "active");
    });
    bindAll(root, "[data-work-filter-value]", "click", (event, button) => {
      onWorkFilter(button.dataset.workFilterValue || "active");
    });
    bindOne(root, "[data-unified-inbox-generate]", "click", (event, button) => {
      onGenerate({ event, button });
    });
    bindAll(root, "[data-unified-inbox-handoff]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onHandoff({
        ...splitInboxActionPayload(button.dataset.unifiedInboxHandoff || ""),
        event,
        button,
      });
    });
    bindAll(root, "[data-unified-inbox-judgment]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onJudgment({
        ...splitInboxActionPayload(button.dataset.unifiedInboxJudgment || ""),
        event,
        button,
      });
    });
    bindAll(root, "[data-item-review-decision]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onItemReviewDecision({
        ...splitInboxActionPayload(button.dataset.itemReviewEntry || ""),
        button,
        decision: button.dataset.itemReviewDecision || "",
        event,
      });
    });
    bindOne(root, "[data-unified-inbox-copy]", "click", (event, button) => {
      onCopy({
        event,
        button,
        encodedPrompt: button.dataset.unifiedInboxCopy || "",
      });
    });
    bindOne(root, "[data-unified-inbox-clear]", "click", (event, button) => {
      onClear({ event, button });
    });
    bindOne(root, "[data-unified-inbox-clear-local]", "click", (event, button) => {
      onClearLocal({ event, button });
    });
    bindOne(root, "[data-unified-inbox-restore-all-archived]", "click", (event, button) => {
      onRestoreAllArchived({ event, button });
    });
    bindOne(root, "[data-unified-inbox-resolve-archived]", "click", (event, button) => {
      onResolveArchived({ event, button });
    });
    bindOne(root, "[data-unified-inbox-runner-refresh]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onRunnerRefresh({ event, button });
    });
    bindAll(root, "[data-unified-inbox-preview-cards]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      const paths = decodeInboxJsonPayload(button.dataset.unifiedInboxPreviewCards || "", []);
      onPreviewCards({
        button,
        event,
        paths: Array.isArray(paths) ? paths.map((path) => String(path || "").trim()).filter(Boolean) : [],
      });
    });
    bindAll(root, "[data-unified-inbox-archive]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onArchive({
        ...splitInboxActionPayload(button.dataset.unifiedInboxArchive || ""),
        event,
        button,
      });
    });
    bindAll(root, "[data-unified-inbox-restore]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onRestore({
        ...splitInboxActionPayload(button.dataset.unifiedInboxRestore || ""),
        event,
        button,
      });
    });
    bindAll(root, "[data-unified-inbox-withdraw]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onWithdraw({
        ...splitInboxActionPayload(button.dataset.unifiedInboxWithdraw || ""),
        event,
        button,
      });
    });
  }

  // Item-local Review: projects the selected item's inbox entries, runs and current result into the
  // review view, then binds its actions to the shell callbacks in app (see app.js renderUnifiedInbox).
  function renderItemReview(root, app) {
    const inbox = app.collectUnifiedInboxEntries();
    inbox.codexRuns = app.codexRunnerRuns;
    inbox.codexRunnerProviderStatus = app.codexRunnerProviderStatus;
    inbox.codexRunnerEnabled = app.workspaceWriteAvailable();
    inbox.currentSession = app.executionSessionForDisplay();
    inbox.currentResultProjection = global.ResearchOSWorkSessionRouter.resultProjectionForSession(app.codexRunnerRuns, inbox.currentSession || {});
    inbox.currentResult = inbox.currentResultProjection.result;
    inbox.publicMode = app.isPublicStarterRuntime();
    inbox.judgmentCalibrationAvailable = app.dashboardData?.runtime_mode === "private";
    inbox.primaryActionKind = inbox.codexRunnerEnabled ? global.ResearchOSActionContract.ACTION_KINDS.DIRECT : global.ResearchOSActionContract.ACTION_KINDS.HANDOFF;
    inbox.workFilter = app.selectedWorkFilter;
    inbox.sessionRegistry = app.itemLocalSessionRegistry();
    inbox.entries = global.ResearchOSInboxService.entriesForItem(inbox.entries, {
      itemId: app.selectedExecutionItemId,
      sessionIds: inbox.sessionRegistry.map((entry) => entry.session_id),
    });
    inbox.total = inbox.entries.filter((entry) => !entry.archived).length;
    inbox.visibleTotal = inbox.entries.length;
    inbox.archivedTotal = inbox.entries.filter((entry) => entry.archived).length;
    inbox.allTotal = inbox.entries.length;
    inbox.itemLocal = true;
    inbox.itemId = app.selectedExecutionItemId;
    inbox.workStateCounts = inbox.sessionRegistry.reduce((counts, item) => ({
      ...counts,
      [item.work_state]: Number(counts[item.work_state] || 0) + 1,
    }), { needs_review: 0 });
    const prompt = app.codexInboxTaskPrompt();
    const pluginDependencies = global.ResearchOSPluginRuntime.resolveSurfaceDependencies({
      context: app.pluginContext(),
      data: app.dashboardData,
      surface: "work",
    });
    root.innerHTML = global.ResearchOSUnifiedInboxView.renderUnifiedInboxHtml({
      inbox,
      prompt,
      deps: {
        ...pluginDependencies,
        escapeHtml: app.escapeHtml,
        encodeDataPayload: global.ResearchOSUiCore.encodeDataPayload,
        previewButton: (path, label = app.simpleText("openPreview"), options = {}) =>
          global.ResearchOSPreviewLinksComponent.previewButton(path, label, {
            ...options,
            escapeHtml: app.escapeHtml,
            previewExists: (candidatePath) => Boolean(app.getPreviewDoc(candidatePath)),
            simpleText: app.simpleText,
          }),
        translate: app.simpleText,
      },
    });
    app.bindPreviewButtons(root);
    app.bindSectionJumpButtons(root);
    bindUnifiedInboxEvents(root, {
      onArchive: ({ type, id }) => app.archiveUnifiedInboxEntryFromUi(type, id),
      onClear: async () => {
        await app.clearUnifiedInboxProcessedItems();
      },
      onClearLocal: () => {
        app.clearLocalUnifiedInboxItems();
      },
      onResolveArchived: () => {
        app.resolveArchivedUnifiedInboxEntriesFromUi();
      },
      onRestoreAllArchived: () => {
        app.restoreAllArchivedUnifiedInboxEntriesFromUi();
      },
      onCopy: async ({ button, encodedPrompt }) => {
        const { copied } = await app.copyEncodedPayload(encodedPrompt || "");
        global.ResearchOSClipboardWorkbenchService.applyCopyButtonFeedback({
          button,
          copied,
          copiedLabel: app.simpleText("unifiedInboxCopied"),
          fallbackLabel: app.simpleText("unifiedInboxCopyUnavailable"),
          resetMs: 1400,
          resetOnFallback: true,
        });
        setUnifiedInboxStatus(
          app.simpleText(copied ? "unifiedInboxCopied" : "unifiedInboxCopyUnavailableHint"),
          root
        );
      },
      onGenerate: async () => {
        if (!inbox.total) {
          setUnifiedInboxStatus(app.simpleText("unifiedInboxNoPendingAction"), root);
          return;
        }
        await app.submitCodexRunnerTask({
          entries: inbox.entries || [],
          prompt,
          root,
          title: app.simpleText("unifiedInboxTitle"),
        });
      },
      onHandoff: async ({ type, id }) => {
        const entry = app.findSingleInboxEntry(type, id);
        if (!entry) {
          setUnifiedInboxStatus(app.simpleText("unifiedInboxSingleMissing"), root);
          return;
        }
        const singlePrompt = global.ResearchOSAgentPromptService.buildCodexInboxTaskPrompt({
          entries: [entry],
          paths: app.codexInboxPaths(),
          language: app.activeTemplateLanguage(),
        });
        if (!app.workspaceWriteAvailable()) {
          const { copied } = await app.copyPlainText(singlePrompt);
          setUnifiedInboxStatus(
            app.simpleText(copied ? "unifiedInboxCopied" : "unifiedInboxCopyUnavailableHint"),
            root
          );
          return;
        }
        await app.submitCodexRunnerTask({
          entries: [entry],
          prompt: singlePrompt,
          root,
          title: entry.displayTitle || entry.title || app.simpleText("unifiedInboxTitle"),
        });
      },
      onJudgment: ({ type, id }) => {
        if (app.dashboardData?.runtime_mode !== "private") {
          setUnifiedInboxStatus(app.simpleText("unifiedInboxJudgmentPrivateOnly"), root);
          return;
        }
        const entry = app.findSingleInboxEntry(type, id);
        const draft = entry ? global.ResearchOSInboxService.judgmentReceiptDraftForEntry(entry, {
          includeContractCard: true,
          language: app.activeTemplateLanguage(),
          text: app.simpleText,
        }) : null;
        if (!draft) {
          setUnifiedInboxStatus(app.simpleText("unifiedInboxJudgmentNotApplicable"), root);
          return;
        }
        const result = app.draftWorkSession(draft);
        if (!result?.ok) return;
        app.openItemExecutionDrawer(app.selectedExecutionItemId, "work", { focus: true });
        global.requestAnimationFrame?.(() => {
          app.focusDashboardSection("todayWorkSession");
          global.document.querySelector("#todayWorkSession [data-work-session-intent-edit]")?.focus?.({ preventScroll: true });
        });
      },
      onItemReviewDecision: ({ type, id, decision }) => {
        app.recordItemReviewDecision(type, id, decision);
      },
      onPreviewCards: async ({ paths }) => {
        const opened = await app.openMarkdownPreviewCards(paths);
        setUnifiedInboxStatus(
          opened.length
            ? String(app.simpleText("unifiedInboxBasketCardCount")).replace("{count}", String(opened.length))
            : app.simpleText("previewEmptyState"),
          root
        );
      },
      onRunnerRefresh: async () => {
        await app.refreshCodexRunnerRuns({ root, rerender: true, updateStatus: true });
        if (app.hasActiveCodexRunnerRun()) {
          app.scheduleCodexRunnerStatusRefresh(app.dashboardTarget("unifiedInbox") || root || global.document);
        }
      },
      onRestore: ({ type, id }) => app.restoreUnifiedInboxEntryFromUi(type, id),
      onViewChange: (view) => {
        app.setUnifiedInboxView(view || "active");
        app.rerender();
      },
      onWorkFilter: (filter) => {
        app.setWorkFilter(filter || "active");
        app.rerender();
      },
      onWithdraw: async ({ type, id }) => {
        await app.withdrawUnifiedInboxEntry(type, id);
      },
    });
    app.bindButtonTooltips(root);
    app.renderWorkSessionSurface(app.dashboardData?.home_command_center || {});
  }

  global.ResearchOSUnifiedInboxWorkbenchService = Object.freeze({
    bindUnifiedInboxEvents,
    renderItemReview,
    scheduleUnifiedInboxStatus,
    setUnifiedInboxStatus,
    splitInboxActionPayload,
  });
})(window);
