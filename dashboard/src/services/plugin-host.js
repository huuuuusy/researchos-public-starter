/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 插件托管；把应用壳的状态与回调组装成插件运行时上下文，并渲染 utility、library 与 workbench 插件槽。
 * English: Plugin hosting for the ResearchOS dashboard; assembles the plugin runtime context from the shell's state and callbacks and renders the utility, library and workbench plugin slots.
 */

(function attachResearchOSPluginHost(global) {
  "use strict";

  /**
   * getState() is called whenever the host needs the shell. It returns the shell's current values
   * (data, lang, codexRunnerRuns, lastMutationReceipt, publicDemoVisible, selectedLibraryLensIds,
   * selectedWorkspaceTab, workSessionHistory), its setters (setLibraryLensIds, setPublicDemoVisible,
   * setWorkFilter) and the shell callbacks the plugin context exposes. Closures handed to plugins
   * call getState() again, so a plugin that keeps its context always sees current values.
   */
  function createPluginHost(getState) {
    const runtime = () => global.ResearchOSPluginRuntime;

    function previewButtonFor(app) {
      return (path, label = app.simpleText("openPreview"), options = {}) =>
        global.ResearchOSPreviewLinksComponent.previewButton(path, label, {
          ...options,
          escapeHtml: app.escapeHtml,
          previewExists: (candidatePath) => Boolean(app.getPreviewDoc(candidatePath)),
          simpleText: app.simpleText,
        });
    }

    function runtimeContext(extra = {}) {
      const app = getState();
      const lifecycle = app.workSessionLifecycle;
      return {
        addTransientTask: app.addDoingItem,
        addWorkSessionCard: lifecycle.addCard,
        attentionMutationAvailable: app.durableWorkItemMutationAvailable,
        bindPreviewButtons: app.bindPreviewButtons,
        cardFromElement: global.ResearchOSWorkSessionState.cardFromAssetElement,
        collectInbox: () => app.collectUnifiedInboxEntries(),
        copyPlainText: app.copyPlainText,
        dispatchPluginAction: app.dispatchPluginAction,
        currentWorkSession: () => app.workSessionForDisplay(),
        currentContextPack: app.currentContextPackProjection,
        executionAvailable: app.localExecutionAvailable,
        draftWorkSession: lifecycle.draft,
        startWorkSession: lifecycle.start,
        ensureWorkSession: lifecycle.ensure,
        escapeHtml: app.escapeHtml,
        focusSection: app.focusDashboardSection,
        generatedAt: () => getState().data?.generated_at || "",
        language: app.lang,
        getPreviewDocument: app.getPreviewDoc,
        openPreview: app.openMarkdownPreview,
        openItemExecutionDrawer: app.openItemExecutionDrawer,
        openWorkspace: app.openWorkspaceOrItemPanel,
        pluginData: () => getState().data,
        previewButton: previewButtonFor(app),
        previewDocuments: app.previewDocuments,
        publicDemoVisible: () => getState().publicDemoVisible,
        publicStarter: app.isPublicStarterRuntime,
        runtimeMode: () => getState().data?.runtime_mode || "private",
        serviceMode: () => global.ResearchOSServiceMode.isServerMode(global.location),
        uploadSourceFile: (file) => global.ResearchOSWorkSessionClient.uploadSourceFile(file),
        lastMutationReceipt: (workspace = getState().selectedWorkspaceTab) => {
          const receipt = getState().lastMutationReceipt;
          return !receipt?.workspace || receipt.workspace === workspace ? receipt : null;
        },
        recentRuns: () => getState().codexRunnerRuns,
        sessionRegistry: () => {
          const current = getState();
          return global.ResearchOSWorkSessionState.sessionRegistryProjection(
            current.workSessionForDisplay(),
            current.workSessionHistory,
            current.codexRunnerRuns,
          );
        },
        runCurrentWorkSession: lifecycle.callbacks.onRunDraft,
        rerender: () => renderLibrarySlots(getState().data),
        rerenderDashboard: () => getState().renderDashboard(getState().data),
        selectLibraryLens: (itemId = "") => {
          const normalized = String(itemId || "").trim();
          getState().setLibraryLensIds(normalized ? [normalized] : []);
          renderLibrarySlots(getState().data);
        },
        resolveRelativePath: (basePath = "", targetPath = "") =>
          app.previewWorkbenchController().resolveRelativeMdPath(basePath, targetPath),
        setPublicDemoVisible: (visible) => getState().setPublicDemoVisible(visible),
        undoLastMutation: () => getState().undoLastMutation(),
        text: app.simpleText,
        toNumber: global.ResearchOSMetricPrimitivesComponent.simpleNumber,
        translate: app.simpleText,
        ...extra,
      };
    }

    function renderUtilitySlots(data) {
      const app = getState();
      const host = app.dashboardTarget("pluginUtilitySlots");
      if (!host || !runtime()) return;
      runtime().renderSlots({
        data,
        host,
        slot: "utility",
        context: {
          bindPreviewButtons: app.bindPreviewButtons,
          copyPlainText: app.copyPlainText,
          document: global.document,
          escapeHtml: app.escapeHtml,
          language: app.lang,
          draftWorkSession: app.workSessionLifecycle.draft,
          focusSection: app.focusDashboardSection,
          openWorkspace: app.setWorkspaceTab,
          taskById: (taskId) => (Array.isArray(data?.tasks) ? data.tasks : []).find((task) => task?.id === taskId) || null,
          previewButton: (path, label = app.t("preview.open")) =>
            global.ResearchOSPreviewLinksComponent.previewButton(path, label, {
              escapeHtml: app.escapeHtml,
              previewExists: (candidatePath) => Boolean(app.getPreviewDoc(candidatePath)),
              simpleText: app.simpleText,
            }),
          registeredMaintenanceAvailable: () => getState().registeredMaintenanceAvailable(),
          publicStarter: app.isPublicStarterRuntime,
          reloadDashboard: async () => {
            const nextData = await getState().loadDashboard();
            getState().renderDashboard(nextData);
            return nextData;
          },
          serverMode: () => global.ResearchOSServiceMode.isServerMode(global.location),
          showServiceModeBanner: () => {
            getState().renderServiceModeBanner();
            global.ResearchOSServiceMode.scrollServiceModeBanner(global.document);
          },
          translate: app.t,
        },
      });
    }

    // Library commitments carry their placement projection; without one an item is optional and sits under Review.
    function libraryCommitments(data) {
      const commitmentItems = runtime().workItemProviderModels(data)
        .flatMap((provider) => Array.isArray(provider?.projection?.items) ? provider.projection.items : []);
      const consolidation = data?.asset_graph?.card_view_consolidation || {};
      const mandatoryCommitmentIds = new Set((consolidation.mandatory_visibility?.mandatory_commitment_ids || []).map(String));
      const commitmentPlacements = new Map((consolidation.placement?.commitments || []).map((item = {}) => [String(item.id || ""), item]));
      const visibleCommitmentItems = commitmentItems.map((item = {}) => ({
        ...item,
        mandatory_visibility: mandatoryCommitmentIds.has(String(item.id || "")),
        placement: commitmentPlacements.get(String(item.id || "")) || null,
        primary_region: commitmentPlacements.get(String(item.id || ""))?.primary_region || "Review",
      }));
      return { commitmentItems, visibleCommitmentItems };
    }

    function renderLibrarySlots(data) {
      const app = getState();
      const host = app.dashboardTarget("assetOverview");
      if (!host || !runtime()) return;
      const WorkSessionView = global.ResearchOSWorkSessionView;
      const { commitmentItems, visibleCommitmentItems } = libraryCommitments(data);
      const commitmentIds = new Set(commitmentItems.map((item = {}) => String(item.id || "")).filter(Boolean));
      const selectedLibraryLensIds = app.selectedLibraryLensIds.filter((itemId) => commitmentIds.has(String(itemId)));
      app.setLibraryLensIds(selectedLibraryLensIds);
      const libraryContext = runtimeContext({
        libraryLens: () => ({
          items: visibleCommitmentItems,
          selectedIds: [...getState().selectedLibraryLensIds],
        }),
      });
      const result = runtime().renderSlots({
        data,
        host,
        slot: "library",
        context: libraryContext,
      });
      const contextProjection = app.currentContextPackProjection();
      const selectedCommitments = commitmentItems.filter((item = {}) => selectedLibraryLensIds.includes(String(item.id || "")));
      const contextLensMismatch = Boolean(
        contextProjection.active
        && selectedLibraryLensIds.length
        && (!contextProjection.task?.item_id || !selectedLibraryLensIds.includes(String(contextProjection.task.item_id))),
      );
      const contextPackHtml = contextLensMismatch
        ? WorkSessionView.renderLibraryContextMismatch({
            currentTask: contextProjection.task,
            selectedItems: selectedCommitments,
          }, { escapeHtml: app.escapeHtml, translate: app.simpleText })
        : WorkSessionView.renderLibraryContextPack(
            { projection: contextProjection },
            {
              escapeHtml: app.escapeHtml,
              previewButton: (path, label, options = {}) => global.ResearchOSPreviewLinksComponent.resolvedPreviewButton(path, label, {
                ...options,
                escapeHtml: app.escapeHtml,
                resolveDocument: app.getPreviewDoc,
                resolvePreviewLink: global.ResearchOSPreviewService.resolvePreviewLink,
                simpleText: app.simpleText,
              }),
              translate: app.simpleText,
            },
          );
      const commitmentLensHtml = global.ResearchOSAssetOverviewView.renderCommitmentLens({
        items: visibleCommitmentItems,
        selectedIds: selectedLibraryLensIds,
      }, { escapeHtml: app.escapeHtml, translate: app.simpleText });
      if (contextPackHtml) host.insertAdjacentHTML("afterbegin", contextPackHtml);
      if (commitmentLensHtml) host.insertAdjacentHTML("afterbegin", commitmentLensHtml);
      if (!result.rendered.length && !contextPackHtml && !commitmentLensHtml) {
        host.innerHTML = global.ResearchOSEmptyStateComponent.renderEmptyCard({
          message: app.simpleText("unifiedInboxEmpty"),
          title: app.t("sections.assetOverview"),
        }, { escapeHtml: app.escapeHtml });
        host.hidden = false;
      } else if (contextPackHtml || commitmentLensHtml) host.hidden = false;
      host.querySelectorAll?.("[data-library-lens-item]").forEach((button) => {
        button.onclick = () => {
          const itemId = String(button.dataset.libraryLensItem || "");
          if (!itemId) return;
          const current = getState().selectedLibraryLensIds;
          getState().setLibraryLensIds(current.includes(itemId)
            ? current.filter((id) => id !== itemId)
            : [...current, itemId].slice(-3));
          renderLibrarySlots(data);
        };
      });
      host.querySelectorAll?.("[data-library-open-execution]").forEach((button) => {
        button.onclick = () => getState().openItemExecutionDrawer(String(button.dataset.libraryOpenExecution || ""), "work", { focus: true });
      });
      app.bindPreviewButtons(host);
      global.ResearchOSWorkspaceShellWorkbenchService.bindWorkspaceLaunchers(host, {
        onWorkspace: ({ button, focusMode, scroll, workspace }) => {
          if (button?.dataset?.workFilterValue) getState().setWorkFilter(button.dataset.workFilterValue);
          getState().openWorkspaceOrItemPanel(workspace || "now", {
            focusMode: focusMode || "panel",
            scroll: Boolean(scroll),
          });
        },
      });
    }

    function renderWorkbenchSlots(root) {
      const host = root?.querySelector?.('[data-plugin-slot-host="workbench"]');
      if (!host || !runtime()) return;
      runtime().renderSlots({
        data: getState().data,
        host,
        slot: "workbench",
        context: runtimeContext(),
      });
    }

    return Object.freeze({ renderLibrarySlots, renderUtilitySlots, renderWorkbenchSlots, runtimeContext });
  }

  global.ResearchOSPluginHost = Object.freeze({ createPluginHost });
})(window);
