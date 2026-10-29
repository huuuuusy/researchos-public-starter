/* ResearchOS maintenance header.
 * 中文：system_stewardship 的已审查 first-party adapter；拥有 Utility slot 的局部状态、渲染和受控维护动作，不拥有 canonical 或浏览器持久状态。
 * English: Reviewed first-party system_stewardship adapter; owns Utility-slot local state, rendering, and governed maintenance actions, but no canonical or durable browser state.
 */

(function registerResearchOSSystemStewardshipPlugin(global) {
  const PluginRuntime = global.ResearchOSPluginRuntime;
  if (!PluginRuntime) return;

  let activeContext = null;
  let activeModel = null;
  let activeRoot = null;
  let autoUpdateRunning = false;
  let autoUpdateResult = null;
  let drawerOpen = false;
  let evolutionDecisionMessage = "";
  let evolutionDecisionRunning = false;

  function dependencies() {
    return {
      commandWorkbench: global.ResearchOSCommandListWorkbenchService,
      externalView: global.ResearchOSExternalEvidenceView,
      maintenanceClient: global.ResearchOSMaintenanceClient,
      maintenanceView: global.ResearchOSMaintenanceView,
      maintenanceWorkbench: global.ResearchOSMaintenanceWorkbenchService,
      serviceMode: global.ResearchOSServiceMode,
    };
  }

  function documentRoot() {
    return activeContext?.document || global.document;
  }

  function translate(key) {
    return activeContext?.translate?.(key) || key;
  }

  function escapeHtml(value) {
    return (activeContext?.escapeHtml || global.ResearchOSUiCore?.escapeHtml)(value);
  }

  function hasAction(actionId) {
    return Boolean(activeModel?.actions?.[actionId]);
  }

  function hasProjection(projectionId) {
    return Object.prototype.hasOwnProperty.call(activeModel?.payloads || {}, projectionId);
  }

  function commandsForLanguage(value, language = "en") {
    if (Array.isArray(value)) return value;
    return value?.[language] || value?.en || [];
  }

  function render(model = {}, context = {}) {
    const systemHealth = Object.prototype.hasOwnProperty.call(model.payloads || {}, "system_health");
    const externalEvidence = Object.prototype.hasOwnProperty.call(model.payloads || {}, "external_evidence");
    const maintenanceCommands = Object.prototype.hasOwnProperty.call(model.payloads || {}, "maintenance_commands");
    const autoUpdate = Boolean(model.actions?.run_auto_update);
    const secondary = externalEvidence || maintenanceCommands;
    const open = drawerOpen ? "open" : "";
    const escape = context.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    return `
      <details class="expand-section supporting-section utility-drawer asset-health-drawer" id="utilityDrawer" ${open}>
        <summary>
          <span>${escape(context.translate?.("maintenanceGraph.title") || model.title || "")}</span>
          <small>${escape(context.translate?.("maintenanceGraph.hint") || model.hint || "")}</small>
        </summary>
        ${systemHealth || autoUpdate ? `
          <section class="maintenance-graph-shell">
            ${autoUpdate ? `
              <article class="panel auto-update-panel">
                <div class="panel-head">
                  <h2>${escape(context.translate?.("maintenanceGraph.primaryTitle") || "maintenanceGraph.primaryTitle")}</h2>
                  <span>${escape(context.translate?.("maintenanceGraph.primaryHint") || "maintenanceGraph.primaryHint")}</span>
                </div>
                <div class="auto-update-inline-actions">
                  <output class="auto-update-status" id="autoUpdateStatus" aria-live="polite"></output>
                </div>
                <div id="autoUpdateResult" class="auto-update-result"></div>
              </article>` : ""}
            ${systemHealth ? `
              <details class="maintenance-diagnostics-drawer">
                <summary><span>${escape(context.translate?.("maintenanceGraph.diagnosticsTitle") || "maintenanceGraph.diagnosticsTitle")}</span><small>${escape(context.translate?.("maintenanceGraph.diagnosticsHint") || "maintenanceGraph.diagnosticsHint")}</small></summary>
                <article class="panel maintenance-graph-panel">
                  <div id="systemChecks" class="maintenance-graph-view"></div>
                </article>
              </details>` : ""}
          </section>` : ""}
        ${secondary ? `
          <details class="simple-detail-drawer maintenance-detail-drawer">
            <summary>
              <span>${escape(context.translate?.("maintenanceGraph.details") || "maintenanceGraph.details")}</span>
              <small>${escape(context.translate?.("maintenanceGraph.detailsHint") || "maintenanceGraph.detailsHint")}</small>
            </summary>
            <section class="utility-grid maintenance-secondary-grid">
              ${externalEvidence ? `
                <article class="panel external-evidence-panel">
                  <div class="panel-head">
                    <h2>${escape(context.translate?.("sections.externalEvidence") || "sections.externalEvidence")}</h2>
                    <span>${escape(context.translate?.("sections.externalEvidenceHint") || "sections.externalEvidenceHint")}</span>
                  </div>
                  <div id="externalEvidence" class="external-evidence-view"></div>
                </article>` : ""}
              ${maintenanceCommands ? `
                <article class="panel">
                  <div class="panel-head">
                    <h2>${escape(context.translate?.("sections.commands") || "sections.commands")}</h2>
                    <span>${escape(context.translate?.("sections.commandsHint") || "sections.commandsHint")}</span>
                  </div>
                  <div id="commands" class="command-list"></div>
                </article>` : ""}
            </section>
          </details>` : ""}
      </details>
    `;
  }

  const evolutionPlanState = dependencies().maintenanceClient.createEvolutionPlanState({
    available: () => Boolean(activeContext?.serverMode?.()),
    onChange: () => {
      renderSystemGraph();
      renderAutoUpdateResult();
    },
  });

  function drawerIsOpen() {
    return Boolean(documentRoot()?.getElementById?.("utilityDrawer")?.open);
  }

  function renderExternalEvidence() {
    if (!activeRoot || !hasProjection("external_evidence") || !drawerIsOpen()) return;
    const root = activeRoot.querySelector("#externalEvidence");
    if (!root) return;
    const external = activeModel.payloads.external_evidence || {};
    const sources = Array.isArray(external.sources) ? external.sources : [];
    root.innerHTML = dependencies().externalView.renderExternalEvidenceHtml(
      { external, sources },
      {
        escapeHtml,
        previewButton: (path, label = translate("preview.open")) => activeContext?.previewButton?.(path, label) || "",
        translate,
      },
    );
    activeContext?.bindPreviewButtons?.(root);
  }

  function renderCommands() {
    if (!activeRoot || !hasProjection("maintenance_commands") || !drawerIsOpen()) return;
    const root = activeRoot.querySelector("#commands");
    if (!root) return;
    const { commandWorkbench } = dependencies();
    const commands = commandsForLanguage(activeModel.payloads.maintenance_commands, activeContext?.language || "en");
    root.innerHTML = commandWorkbench.renderCommandListHtml(
      { commands },
      {
        autoUpdateResult,
        escapeHtml,
        health: activeModel.payloads.system_health || {},
        publicMode: Boolean(activeContext?.publicStarter?.()),
        queueAvailable: typeof activeContext?.draftWorkSession === "function",
        translate,
      },
    );
    commandWorkbench.bindCommandListEvents(root, {
      onQueue: ({ button, actionId }) => {
        const command = commands.find((item) => item?.id === actionId);
        if (!command || activeContext?.publicStarter?.() || typeof activeContext?.draftWorkSession !== "function") return;
        const suggestion = commandWorkbench.maintenanceSuggestionModel(
          command,
          { autoUpdateResult, health: activeModel.payloads.system_health || {} },
          { translate },
        );
        const result = activeContext.draftWorkSession({
          intent: suggestion.intent,
          responseMode: "answer",
          title: suggestion.title,
        });
        if (result?.cancelled || result?.ok === false) return;
        commandWorkbench.syncMaintenanceSuggestionChrome({ button, message: translate("maintenanceRecommendation.added") });
        activeContext?.openWorkspace?.("next", { scroll: true });
        activeContext?.focusSection?.("todayWorkSession");
      },
    });
  }

  function renderAutoUpdateResult() {
    if (!activeRoot || !hasAction("run_auto_update")) return;
    const { maintenanceView, maintenanceWorkbench } = dependencies();
    const evolution = evolutionPlanState.snapshot();
    const root = activeRoot.querySelector("#autoUpdateResult");
    if (!root) return;
    root.innerHTML = maintenanceView.renderAutoUpdateResultHtml(
      {
        error: evolution.error,
        loading: evolution.loading,
        plan: evolution.plan,
        result: autoUpdateResult,
        running: autoUpdateRunning,
      },
      { escapeHtml, summary: (result) => maintenanceView.autoUpdateSummary(result, translate), translate },
    );
    maintenanceWorkbench.bindAutoUpdateResultEvents(root, { onRun: () => runAutoUpdate() });
    maintenanceWorkbench.syncAutoUpdateChrome({
      root: documentRoot(),
      running: autoUpdateRunning,
      disabled: evolution.plan?.execution_allowed === false || !evolution.plan?.auto_eligible_step_ids?.length,
      labels: {
        button: translate("autoUpdate.button"),
        running: translate("autoUpdate.running"),
        summary: evolution.error
          ? translate("autoUpdate.statusUnavailableLabel")
          : maintenanceView.autoUpdateStatus(evolution.plan, autoUpdateResult, translate),
        tone: autoUpdateResult?.ok ? "ok" : autoUpdateResult ? "risk" : "",
      },
    });
  }

  function renderSystemGraph() {
    if (!activeRoot || !hasProjection("system_health") || !drawerIsOpen()) return;
    const root = activeRoot.querySelector("#systemChecks");
    if (!root) return;
    const { maintenanceClient, maintenanceView, maintenanceWorkbench } = dependencies();
    const evolution = evolutionPlanState.snapshot();
    root.innerHTML = maintenanceView.renderSystemGraphHtml({
      assetGraph: activeModel.payloads.asset_graph || {},
      health: activeModel.payloads.system_health || {},
      overview: activeModel.payloads.source_overview || {},
      safeExports: activeModel.payloads.safe_export || [],
      evolutionPlan: evolution.plan,
      evolutionPlanLoading: evolution.loading,
      evolutionPlanError: evolution.error,
      decisionMessage: evolutionDecisionMessage,
      decisionRunning: evolutionDecisionRunning,
    }, { escapeHtml, translate });
    if (!hasAction("review_evolution_plan")) return;
    maintenanceWorkbench.bindEvolutionDecisionEvents(root, {
      onDecision: async ({ button, decision }) => {
        const plan = evolutionPlanState.snapshot().plan;
        if (!plan?.plan_id || plan.execution_allowed === false || evolutionDecisionRunning) return;
        button.disabled = true;
        evolutionDecisionRunning = true;
        evolutionDecisionMessage = translate("evolutionPlan.decisionRunning");
        renderSystemGraph();
        let result = null;
        try {
          result = await maintenanceClient.decideEvolutionPlan(plan.plan_id, decision);
        } finally {
          evolutionDecisionRunning = false;
        }
        if (result?.plan) evolutionPlanState.accept(result.plan);
        evolutionDecisionMessage = translate(
          result?.ok
            ? decision === "deferred" ? "evolutionPlan.decisionDeferred" : "evolutionPlan.decisionRejected"
            : "evolutionPlan.decisionFailed",
        );
        renderSystemGraph();
      },
    });
  }

  function renderLazySections() {
    if (!drawerIsOpen()) return;
    renderExternalEvidence();
    renderCommands();
    renderSystemGraph();
    renderAutoUpdateResult();
    if (!evolutionPlanState.snapshot().plan && !evolutionPlanState.snapshot().loading) void evolutionPlanState.refresh();
  }

  async function runAutoUpdate() {
    if (!hasAction("run_auto_update") || autoUpdateRunning) return;
    const { maintenanceClient, maintenanceWorkbench, serviceMode } = dependencies();
    if (!activeContext?.serverMode?.()) {
      autoUpdateResult = serviceMode.blockedResult({ label: "auto-update", message: translate("serviceMode.actionBlocked") });
      renderAutoUpdateResult();
      activeContext?.showServiceModeBanner?.();
      return;
    }
    let evolution = evolutionPlanState.snapshot();
    if (!evolution.plan?.plan_id) evolution = await evolutionPlanState.refresh();
    if (evolution.plan?.execution_allowed === false || !evolution.plan?.auto_eligible_step_ids?.length) {
      renderAutoUpdateResult();
      return;
    }
    autoUpdateRunning = true;
    renderAutoUpdateResult();
    try {
      autoUpdateResult = await maintenanceClient.runAutoUpdate(evolution.plan.plan_id);
      if (autoUpdateResult?.plan) evolutionPlanState.accept(autoUpdateResult.plan);
      if (autoUpdateResult.ok) {
        evolutionPlanState.clear();
        await activeContext?.reloadDashboard?.();
        await evolutionPlanState.refresh();
      }
    } catch (error) {
      autoUpdateResult = maintenanceClient.autoUpdateErrorResult(error);
    } finally {
      autoUpdateRunning = false;
      renderAutoUpdateResult();
      maintenanceWorkbench.focusAutoUpdateResult(documentRoot());
    }
  }

  function bind({ context = {}, model = {}, root = null } = {}) {
    activeContext = context;
    activeModel = model;
    activeRoot = root;
    const drawer = activeRoot?.querySelector?.("#utilityDrawer");
    if (!drawer) return;
    drawerOpen = Boolean(drawer.open);
    drawer.addEventListener("toggle", () => {
      drawerOpen = Boolean(drawer.open);
      if (drawerOpen) renderLazySections();
    });
    if (hasAction("run_auto_update")) {
      dependencies().maintenanceWorkbench.bindAutoUpdateButton(documentRoot(), { onRun: () => runAutoUpdate() });
      renderAutoUpdateResult();
    }
    if (drawerOpen) renderLazySections();
  }

  PluginRuntime.registerOwnedAdapter("system_stewardship", "system_stewardship", Object.freeze({ bind, render }));
})(window);
