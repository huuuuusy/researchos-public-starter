/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 视图「maintenance」的纯 HTML 渲染层；不保存持久状态、不直接执行写入副作用。
 * English: Pure HTML rendering layer for the maintenance dashboard view; stores no durable state and performs no write side effects.
 */

(function attachResearchOSMaintenanceView(global) {
  function translatedTemplate(translate, key, values = {}) {
    return Object.entries(values).reduce(
      (text, [name, value]) => String(text).replaceAll(`{${name}}`, String(value)),
      translate(key),
    );
  }

  function firstFailedStep(result = {}) {
    return (Array.isArray(result.steps) ? result.steps : []).find((step) => !step.ok) || null;
  }

  function autoUpdateSummary(result, translate) {
    if (!result) return translate("autoUpdate.ready");
    if (result.ok && result.external_partial) return translate("autoUpdate.partial");
    if (result.ok) return translate("autoUpdate.success");
    return translate("autoUpdate.failed");
  }

  function autoUpdateStatus(plan, result, translate) {
    if (!plan) return result ? autoUpdateSummary(result, translate) : translate("autoUpdate.checking");
    if (plan?.execution_allowed === false) return translate("evolutionPlan.readOnlyStatus");
    if (plan?.manual_step_ids?.length && !plan?.auto_eligible_step_ids?.length) return translate("evolutionPlan.manualStatus");
    return autoUpdateSummary(result, translate);
  }

  function renderAutoUpdateResultHtml({ error = "", loading = false, result, plan, running = false } = {}, deps = {}) {
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const translate = deps.translate || ((key) => key);
    const autoStepIds = Array.isArray(plan?.auto_eligible_step_ids) ? plan.auto_eligible_step_ids : [];
    const manualStepIds = Array.isArray(plan?.manual_step_ids) ? plan.manual_step_ids : [];
    const pendingManualStepIds = Array.isArray(result?.pending_manual_step_ids) ? result.pending_manual_step_ids : [];
    const safeCount = autoStepIds.length;
    const manualCount = Math.max(manualStepIds.length, pendingManualStepIds.length);
    const changedPathCount = Number(plan?.changed_path_count || 0);
    const readOnly = plan?.execution_allowed === false;
    const canRun = !readOnly && safeCount > 0;
    if (loading || (!plan && !result && !error)) {
      return `<section class="maintenance-result-card is-checking" role="status" aria-live="polite">
        <span class="maintenance-result-eyebrow">${escapeHtml(translate("autoUpdate.checkingLabel"))}</span>
        <strong>${escapeHtml(translate("autoUpdate.checkingTitle"))}</strong>
        <p>${escapeHtml(translate("autoUpdate.checkingBody"))}</p>
        <span class="maintenance-running-indicator" aria-hidden="true"></span>
      </section>`;
    }
    if (error) {
      return `<section class="maintenance-result-card is-failed" role="alert">
        <span class="maintenance-result-eyebrow">${escapeHtml(translate("autoUpdate.statusUnavailableLabel"))}</span>
        <strong>${escapeHtml(translate("autoUpdate.statusUnavailableTitle"))}</strong>
        <p>${escapeHtml(translate("autoUpdate.statusUnavailableBody"))}</p>
      </section>`;
    }
    if (running) {
      return `<section class="maintenance-result-card is-running" role="status" aria-live="polite" aria-busy="true">
        <span class="maintenance-result-eyebrow">${escapeHtml(translate("autoUpdate.runningLabel"))}</span>
        <strong>${escapeHtml(translate("autoUpdate.runningTitle"))}</strong>
        <p>${escapeHtml(translatedTemplate(translate, "autoUpdate.runningBody", { count: safeCount }))}</p>
        <span class="maintenance-running-indicator" aria-hidden="true"></span>
      </section>
      <p class="maintenance-boundary-note">${escapeHtml(translate("autoUpdate.runningBoundary"))}</p>`;
    }
    if (!result) {
      const titleKey = readOnly ? "autoUpdate.publicTitle" : canRun ? "autoUpdate.readyTitle" : "autoUpdate.idleTitle";
      const body = readOnly
        ? translate("autoUpdate.publicBody")
        : canRun
          ? translatedTemplate(translate, "autoUpdate.readyBody", { paths: changedPathCount })
          : translate(manualCount ? "autoUpdate.manualOnlyBody" : "autoUpdate.idleBody");
      return `
        <section class="maintenance-result-card ${readOnly ? "is-read-only" : canRun ? "is-ready" : "is-idle"}">
          <span class="maintenance-result-eyebrow">${escapeHtml(translate(readOnly ? "autoUpdate.readOnlyLabel" : canRun ? "autoUpdate.problemLabel" : "autoUpdate.healthyLabel"))}</span>
          <strong>${escapeHtml(translate(titleKey))}</strong>
          <p>${escapeHtml(body)}</p>
          ${canRun ? `<div class="maintenance-update-impact">
            <div><strong>${escapeHtml(String(safeCount))}</strong><span>${escapeHtml(translate("autoUpdate.safePlan"))}</span></div>
            ${manualCount ? `<div><strong>${escapeHtml(String(manualCount))}</strong><span>${escapeHtml(translate("autoUpdate.manualPlan"))}</span></div>` : ""}
          </div>
          <p class="maintenance-action-explanation">${escapeHtml(translate("autoUpdate.clickExplanation"))}</p>
          <button type="button" class="primary auto-update-button" data-action-kind="direct" data-run-auto-update>${escapeHtml(translate("autoUpdate.button"))}</button>` : manualCount ? `<p class="maintenance-manual-note">${escapeHtml(translatedTemplate(translate, "autoUpdate.manualRemaining", { count: manualCount }))}</p>` : ""}
        </section>
        <p class="maintenance-boundary-note">${escapeHtml(translate(readOnly ? "autoUpdate.publicBoundary" : "autoUpdate.localHint"))}</p>
      `;
    }
    const steps = Array.isArray(result.steps) ? result.steps : [];
    const failedStep = firstFailedStep(result);
    const rollback = result.rollback && typeof result.rollback === "object" ? result.rollback : null;
    const restoredCount = Array.isArray(rollback?.restored) ? rollback.restored.length : 0;
    const rollbackTargetText = String(translate("autoUpdate.rollbackTargets")).replace("{count}", String(restoredCount));
    const successfulCount = steps.filter((step) => step.ok).length;
    const resultTitleKey = result.ok
      ? "autoUpdate.successTitle"
      : rollback?.attempted && rollback?.ok
        ? "autoUpdate.restoredTitle"
        : "autoUpdate.failedTitle";
    const resultBodyKey = result.ok
      ? "autoUpdate.successBody"
      : rollback?.attempted && rollback?.ok
        ? "autoUpdate.restoredBody"
        : "autoUpdate.failedBody";
    return `
      <section class="maintenance-result-card ${result.ok ? "is-success" : rollback?.ok ? "is-restored" : "is-failed"}">
        <span class="maintenance-result-eyebrow">${escapeHtml(translate(result.ok ? "autoUpdate.completedLabel" : "autoUpdate.attentionLabel"))}</span>
        <strong>${escapeHtml(translate(resultTitleKey))}</strong>
        <p>${escapeHtml(translate(resultBodyKey))}</p>
        <small>${escapeHtml(translatedTemplate(translate, "autoUpdate.resultMeta", { passed: successfulCount, seconds: result.seconds || "0" }))}</small>
        ${manualCount ? `<p class="maintenance-manual-note">${escapeHtml(translatedTemplate(translate, "autoUpdate.manualRemaining", { count: manualCount }))}</p>` : ""}
      </section>
      ${failedStep ? `
        <section class="maintenance-primary-issue">
          <span>${escapeHtml(translate("autoUpdate.primaryIssue"))}</span>
          <strong>${escapeHtml(failedStep.label || translate("autoUpdate.unknownStep"))}</strong>
          <p>${escapeHtml(translate("autoUpdate.primaryIssueHint"))}</p>
        </section>` : ""}
      ${rollback?.attempted ? `<p class="maintenance-boundary-note ${rollback.ok ? "is-safe" : "is-risk"}">${escapeHtml(translate(rollback.ok ? "autoUpdate.rollbackComplete" : "autoUpdate.rollbackFailed"))} · ${escapeHtml(rollbackTargetText)}</p>` : ""}
      ${steps.length ? `
        <details class="maintenance-log-drawer">
          <summary>${escapeHtml(translatedTemplate(translate, "autoUpdate.technicalLogs", { count: steps.length }))}</summary>
          <div class="auto-update-steps">
            ${steps
              .map(
                (step) => `
                  <details class="auto-update-step ${step.ok ? "ok" : step.optional ? "warn" : "risk"}">
                    <summary>
                      <span>${escapeHtml(step.label || "")}${step.optional ? ` · ${escapeHtml(translate("autoUpdate.optional"))}` : ""}</span>
                      <strong>${escapeHtml(step.ok ? translate("autoUpdate.stepOk") : translate("autoUpdate.stepFail"))}</strong>
                    </summary>
                    <pre>${escapeHtml(step.output || "")}</pre>
                  </details>
                `
              )
              .join("")}
          </div>
        </details>` : ""}
      ${canRun ? `<button type="button" data-action-kind="direct" data-run-auto-update>${escapeHtml(translate("autoUpdate.rerun"))}</button>` : ""}
    `;
  }

  function renderEvolutionPlanHtml({ plan, loading = false, error = "", decisionMessage = "", decisionRunning = false } = {}, deps = {}) {
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const translate = deps.translate || ((key) => key);
    if (loading) {
      return `<section class="maintenance-evolution-plan pending"><strong>${escapeHtml(translate("evolutionPlan.loading"))}</strong></section>`;
    }
    if (error) {
      return `<section class="maintenance-evolution-plan risk"><strong>${escapeHtml(translate("evolutionPlan.failed"))}</strong><span>${escapeHtml(error)}</span></section>`;
    }
    if (!plan) return "";
    const selected = Array.isArray(plan.selected_step_ids) ? plan.selected_step_ids : [];
    const manual = Array.isArray(plan.manual_step_ids) ? plan.manual_step_ids : [];
    const writes = Array.isArray(plan.writes) ? plan.writes : [];
    const autoWrites = Array.isArray(plan.auto_writes) ? plan.auto_writes : [];
    const manualWrites = Array.isArray(plan.manual_writes) ? plan.manual_writes : [];
    const paths = Array.isArray(plan.changed_paths) ? plan.changed_paths : [];
    const autoStepIds = Array.isArray(plan.auto_eligible_step_ids) ? plan.auto_eligible_step_ids : [];
    const carriedManual = Array.isArray(plan.carried_manual_step_ids) ? plan.carried_manual_step_ids : [];
    const upToDate = plan.status === "up_to_date" || !selected.length;
    const deferred = plan.status === "deferred";
    const readOnly = plan.execution_allowed === false;
    const manualOnly = manual.length && !autoStepIds.length;
    const tone = upToDate ? "ok" : deferred ? "pending" : manual.length ? "warn" : writes.length ? "pending" : "ok";
    const decisionAllowed = !readOnly && manualOnly && !deferred;
    const carriedText = String(translate("evolutionPlan.carried")).replace("{count}", String(carriedManual.length));
    const titleKey = readOnly
      ? "evolutionPlan.publicTitle"
      : upToDate
        ? "evolutionPlan.upToDate"
        : deferred
          ? "evolutionPlan.deferred"
          : manualOnly
            ? "evolutionPlan.manualTitle"
            : "evolutionPlan.candidate";
    const hintKey = readOnly
      ? "evolutionPlan.demoReadOnlyHint"
      : upToDate
        ? "evolutionPlan.upToDateHint"
        : deferred
          ? "evolutionPlan.deferredHint"
          : manualOnly
            ? "evolutionPlan.manualHint"
            : "evolutionPlan.candidateHint";
    return `
      <section class="maintenance-evolution-plan ${escapeHtml(tone)}" data-evolution-plan-id="${escapeHtml(plan.plan_id || "")}">
        <header>
          <div>
            <span>${escapeHtml(translate("evolutionPlan.eyebrow"))}</span>
            <strong>${escapeHtml(translate(titleKey))}</strong>
          </div>
          <small class="maintenance-plan-badge">${escapeHtml(translate(readOnly ? "evolutionPlan.readOnlyStatus" : upToDate ? "evolutionPlan.okStatus" : manualOnly ? "evolutionPlan.manualBadge" : "evolutionPlan.actionBadge"))}</small>
        </header>
        <p>${escapeHtml(translate(hintKey))}</p>
        ${selected.length ? `<p class="maintenance-plan-summary">${escapeHtml(translatedTemplate(translate, "evolutionPlan.plainSummary", { safe: autoStepIds.length, manual: manual.length }))}</p>` : ""}
        ${carriedManual.length ? `<p>${escapeHtml(carriedText)}</p>` : ""}
        ${
          selected.length
            ? `<details class="maintenance-plan-technical"><summary>${escapeHtml(translate("evolutionPlan.details"))}</summary>
                <dl>
                  <div><dt>${escapeHtml(translate("evolutionPlan.risk"))}</dt><dd>${escapeHtml(plan.risk_tier || "E0")}</dd></div>
                  <div><dt>${escapeHtml(translate("evolutionPlan.planId"))}</dt><dd>${escapeHtml(plan.plan_id || translate("evolutionPlan.none"))}</dd></div>
                  <div><dt>${escapeHtml(translate("evolutionPlan.scope"))}</dt><dd>${escapeHtml(String(plan.changed_path_count || 0))} ${escapeHtml(translate("evolutionPlan.paths"))} · ${escapeHtml(String(selected.length))} ${escapeHtml(translate("evolutionPlan.steps"))}</dd></div>
                  <div><dt>${escapeHtml(translate("evolutionPlan.safe"))}</dt><dd>${escapeHtml((plan.auto_eligible_step_ids || []).join(" · ") || translate("evolutionPlan.none"))}</dd></div>
                  <div><dt>${escapeHtml(translate("evolutionPlan.manual"))}</dt><dd>${escapeHtml(manual.join(" · ") || translate("evolutionPlan.none"))}</dd></div>
                  <div><dt>${escapeHtml(translate("evolutionPlan.writes"))}</dt><dd>${escapeHtml(autoWrites.join(" · ") || translate("evolutionPlan.none"))}</dd></div>
                  <div><dt>${escapeHtml(translate("evolutionPlan.manualWrites"))}</dt><dd>${escapeHtml(manualWrites.join(" · ") || translate("evolutionPlan.none"))}</dd></div>
                  <div><dt>${escapeHtml(translate("evolutionPlan.changed"))}</dt><dd>${escapeHtml(paths.join(" · ") || translate("evolutionPlan.none"))}${plan.changed_paths_truncated ? ` · ${escapeHtml(translate("evolutionPlan.truncated"))}` : ""}</dd></div>
                </dl>
                <p class="maintenance-boundary-note">${escapeHtml(translate("evolutionPlan.authority"))}</p>
              </details>`
            : ""
        }
        ${decisionAllowed ? `<footer><span>${escapeHtml(translate("evolutionPlan.manualActionHint"))}</span><div class="maintenance-evolution-actions"><button type="button" data-action-kind="preview-confirm" data-evolution-decision="deferred" ${decisionRunning ? "disabled" : ""}>${escapeHtml(translate("evolutionPlan.defer"))}</button><button type="button" data-action-kind="preview-confirm" data-evolution-decision="rejected" ${decisionRunning ? "disabled" : ""}>${escapeHtml(translate("evolutionPlan.reject"))}</button></div></footer>` : ""}
        ${decisionMessage ? `<p role="status">${escapeHtml(decisionMessage)}</p>` : ""}
      </section>
    `;
  }

  function systemCheckItems(health = {}, translate = (key) => key) {
    const validation = health.validation || {};
    const stale = health.stale_context || {};
    const missingFrontmatter = Array.isArray(validation.missing_frontmatter) ? validation.missing_frontmatter : [];
    const missingAgentSummary = Array.isArray(validation.missing_agent_summary) ? validation.missing_agent_summary : [];
    const brokenLinks = Array.isArray(validation.broken_links) ? validation.broken_links : [];
    const staleItems = Array.isArray(stale.stale) ? stale.stale : [];
    return [
      { label: translate("checks.checked"), tone: "ok", value: validation.checked_markdown || 0 },
      { label: translate("checks.frontmatter"), tone: missingFrontmatter.length ? "risk" : "ok", value: missingFrontmatter.length },
      { label: translate("checks.agentSummary"), tone: missingAgentSummary.length ? "risk" : "ok", value: missingAgentSummary.length },
      { label: translate("checks.links"), tone: brokenLinks.length ? "risk" : "ok", value: brokenLinks.length },
      { label: translate("checks.stale"), tone: staleItems.length ? "warn" : "ok", value: staleItems.length },
    ];
  }

  function graphToneForCheck(item = {}) {
    if (item.tone === "risk") return "risk";
    if (item.tone === "warn") return "warn";
    return "ok";
  }

  function graphDepthForTone(tone = "ok") {
    if (tone === "risk") return 1;
    if (tone === "warn") return 2;
    return 3;
  }

  function maintenanceGraphModel({ assetGraph = {}, health = {}, overview = {}, safeExports = [] } = {}, deps = {}) {
    const translate = deps.translate || ((key) => key);
    const checks = systemCheckItems(health, translate);
    const validation = health?.validation || {};
    const stale = health?.stale_context || {};
    const metrics = assetGraph?.dynamic_graph?.metrics || {};
    const layers = Array.isArray(overview.layers) ? overview.layers : [];
    const activeLayer = layers.find((layer) => layer.layer === "06_active_context") || {};
    const checkTone = checks.some((item) => item.tone === "risk") ? "risk" : checks.some((item) => item.tone === "warn") ? "warn" : "ok";
    const dashboardTone = validation.ok === false ? "risk" : "ok";
    const staleTone = Array.isArray(stale.stale) && stale.stale.length ? "warn" : "ok";
    const nodes = [
      {
        id: "sources",
        type: "source",
        level: 3,
        title: translate("maintenanceGraph.sources"),
        meta: `${layers.length || 10} layers`,
        x: 9,
        y: 50,
      },
      {
        id: "indices",
        type: "index",
        level: 3,
        title: translate("maintenanceGraph.indices"),
        meta: translate("maintenanceGraph.indicesMeta"),
        x: 25,
        y: 20,
      },
      {
        id: "dashboard",
        type: "view",
        level: graphDepthForTone(dashboardTone),
        title: translate("maintenanceGraph.dashboard"),
        meta: `${metrics.node_count || 0} nodes · ${metrics.typed_edge_count || 0} edges`,
        tone: dashboardTone,
        x: 49,
        y: 37,
      },
      {
        id: "today",
        type: "view",
        level: 3,
        title: translate("workspace.agent"),
        meta: translate("workspace.agentHint"),
        x: 69,
        y: 17,
      },
      {
        id: "assets",
        type: "view",
        level: 3,
        title: translate("workspace.assets"),
        meta: translate("workspace.assetsHint"),
        x: 73,
        y: 48,
      },
      {
        id: "review",
        type: "action",
        level: 3,
        title: translate("sections.unifiedInbox"),
        meta: translate("sections.unifiedInboxHint"),
        x: 67,
        y: 78,
      },
      {
        id: "validation",
        type: "check",
        level: graphDepthForTone(checkTone),
        title: translate("sections.systemChecks"),
        meta: `${validation.checked_markdown || 0} md`,
        tone: checkTone,
        x: 38,
        y: 74,
      },
      {
        id: "links",
        type: "check",
        level: graphDepthForTone(graphToneForCheck(checks.find((item) => item.label === translate("checks.links")) || {})),
        title: translate("checks.links"),
        meta: String((checks.find((item) => item.label === translate("checks.links")) || {}).value ?? 0),
        x: 19,
        y: 78,
      },
      {
        id: "active",
        type: "state",
        level: graphDepthForTone(staleTone),
        title: translate("maintenanceGraph.active"),
        meta: `${activeLayer.markdown || 0} md`,
        tone: staleTone,
        x: 18,
        y: 42,
      },
      {
        id: "export",
        type: "export",
        level: 2,
        title: translate("maintenanceGraph.export"),
        meta: Array.isArray(safeExports) && safeExports.length
          ? `${safeExports.length} · ${translate("maintenanceGraph.exportMeta")}`
          : translate("maintenanceGraph.exportMeta"),
        x: 48,
        y: 12,
      },
      {
        id: "external",
        type: "external",
        level: 2,
        title: translate("sections.externalEvidence"),
        meta: translate("sections.externalEvidenceHint"),
        x: 88,
        y: 34,
      },
      {
        id: "commands",
        type: "action",
        level: 1,
        title: translate("sections.commands"),
        meta: translate("sections.commandsHint"),
        x: 88,
        y: 68,
      },
    ];
    const edges = [
      ["sources", "indices"],
      ["sources", "active"],
      ["indices", "dashboard"],
      ["dashboard", "today"],
      ["dashboard", "assets"],
      ["dashboard", "inbox"],
      ["active", "validation"],
      ["validation", "links"],
      ["validation", "dashboard"],
      ["dashboard", "export"],
      ["external", "dashboard"],
      ["commands", "validation"],
      ["commands", "indices"],
    ].map(([from, to]) => ({ from, to }));
    return { edges, nodes };
  }

  function renderMaintenanceRuntimeSummary(model = {}, deps = {}) {
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const translate = deps.translate || ((key) => key);
    const nodeById = Object.fromEntries((model.nodes || []).map((node) => [node.id, node]));
    const stepIds = ["sources", "indices", "dashboard", "validation", "active", "inbox"];
    return `
      <section class="maintenance-runtime-summary" aria-label="${escapeHtml(translate("maintenanceGraph.summaryTitle"))}">
        <header>
          <strong>${escapeHtml(translate("maintenanceGraph.summaryTitle"))}</strong>
          <span>${escapeHtml(translate("maintenanceGraph.summaryHint"))}</span>
        </header>
        <div class="maintenance-runtime-steps">
          ${stepIds
            .map((id, index) => {
              const node = nodeById[id] || {};
              return `
                <article class="maintenance-runtime-step type-${escapeHtml(node.type || "state")} depth-${escapeHtml(String(node.level || 1))} ${node.tone ? `tone-${escapeHtml(node.tone)}` : ""}">
                  <span>${escapeHtml(String(index + 1).padStart(2, "0"))} · ${escapeHtml(node.type || "")}</span>
                  <strong>${escapeHtml(node.title || id)}</strong>
                  <small>${escapeHtml(node.meta || "")}</small>
                </article>
              `;
            })
            .join("")}
        </div>
      </section>
    `;
  }

  function renderNetworkDiagnosticsHtml(dynamicGraph = {}, deps = {}) {
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const translate = deps.translate || ((key) => key);
    const network = dynamicGraph?.network_diagnostics || {};
    const diagnostics = (Array.isArray(network.diagnostics) ? network.diagnostics : [])
      .filter((item) => Number(item?.count || 0) > 0);
    const summary = network.summary || {};
    const state = network.state || "unavailable";
    const inputStatus = network.input_status || network?.coverage?.status || "unavailable";
    const stateLabel = translate(`maintenanceGraph.networkState.${state}`);
    const coverageLabel = translate(`maintenanceGraph.networkCoverage.${inputStatus}`);
    const modeLabel = (mode) => translate(`maintenanceGraph.networkMode.${mode}`);
    return `
      <section class="maintenance-runtime-summary network-diagnostics-summary" data-network-diagnostics-state="${escapeHtml(state)}" data-network-input-status="${escapeHtml(inputStatus)}">
        <header>
          <strong>${escapeHtml(translate("maintenanceGraph.networkTitle"))}</strong>
          <span>${escapeHtml(stateLabel)}${inputStatus === state ? "" : ` · ${escapeHtml(coverageLabel)}`}</span>
        </header>
        <div class="maintenance-runtime-steps">
          ${diagnostics.map((item) => `
            <article class="maintenance-runtime-step type-${item.adjustment_class === "automatic_derived_refresh" ? "state" : "check"}" data-network-diagnostic-kind="${escapeHtml(item.kind || "")}" data-network-adjustment-class="${escapeHtml(item.adjustment_class || "")}">
              <span>${escapeHtml(modeLabel(item.status === "refresh_required" ? "refresh_required" : item.adjustment_class || "observe_only"))}</span>
              <strong>${escapeHtml(translate(`maintenanceGraph.networkDiagnostic.${item.kind}`))}</strong>
              <small>${escapeHtml(String(item.count || 0))} · ${escapeHtml((item.affected_paths || []).slice(0, 2).join(" · "))}</small>
            </article>
          `).join("")}
        </div>
        <p class="maintenance-boundary-note">${escapeHtml(translate("maintenanceGraph.networkBoundary"))}</p>
        <small>${escapeHtml(translate("maintenanceGraph.networkStatus"))}: ${escapeHtml(String(summary.automatic_refresh_required_class_count || 0))} / ${escapeHtml(String(summary.verified_adjusted_class_count || 0))} / ${escapeHtml(String(summary.candidate_only_class_count || 0))} / ${escapeHtml(String(summary.human_review_class_count || 0))}</small>
      </section>
    `;
  }

  function renderSystemGraphHtml({ assetGraph = {}, health = {}, overview = {}, safeExports = [], evolutionPlan = null, evolutionPlanLoading = false, evolutionPlanError = "", decisionMessage = "", decisionRunning = false } = {}, deps = {}) {
    const model = maintenanceGraphModel({ assetGraph, health, overview, safeExports }, deps);
    return `
      <details class="maintenance-technical-drawer">
        <summary>${(deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml)((deps.translate || ((key) => key))("maintenanceGraph.technicalSummary"))}</summary>
        ${renderEvolutionPlanHtml({ plan: evolutionPlan, loading: evolutionPlanLoading, error: evolutionPlanError, decisionMessage, decisionRunning }, deps)}
        ${renderNetworkDiagnosticsHtml(assetGraph?.dynamic_graph || {}, deps)}
        ${renderMaintenanceRuntimeSummary(model, deps)}
      </details>
    `;
  }

  global.ResearchOSMaintenanceView = Object.freeze({
    autoUpdateSummary,
    autoUpdateStatus,
    firstFailedStep,
    maintenanceGraphModel,
    renderAutoUpdateResultHtml,
    renderEvolutionPlanHtml,
    renderNetworkDiagnosticsHtml,
    renderSystemGraphHtml,
    systemCheckItems,
  });
})(window);
