/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「command list workbench」；负责 DOM 事件绑定，把副作用回调交还 app。
 * English: Workbench interaction adapter for command list workbench in the ResearchOS dashboard; owns DOM event binding and returns side effects to app callbacks.
 */

(function attachResearchOSCommandListWorkbenchService(global) {
  function translated(translate, key, fallback = "") {
    const value = translate(key);
    return !value || value === key ? fallback : value;
  }

  function maintenanceSuggestionModel(item = {}, options = {}, deps = {}) {
    const translate = deps.translate || ((key) => key);
    const actionId = String(item?.id || "").trim();
    const health = options.health || {};
    const validationNeedsAttention = health?.validation?.ok === false;
    const staleItems = Array.isArray(health?.stale_context?.stale) ? health.stale_context.stale : [];
    const history = options.publicMode ? {} : (health?.stale_context?.temporary_review_history || {});
    const historicalItems = Array.isArray(history.items) ? history.items : [];
    const staleCount = staleItems.length + historicalItems.length + (history.requires_review ? 1 : 0);
    const isAutomatic = ["build_dashboard_data", "build_public_starter_data"].includes(actionId);
    const recommended = (actionId === "validate_researchos" && validationNeedsAttention)
      || (actionId === "check_stale_context" && staleCount > 0);
    const dates = staleItems.map((entry) => ({ ...entry, issue_id: historicalItems.find((old) =>
      old.path === entry.path && old.rule !== "shared_prose" && old.kind === "temporary_work_review")?.issue_id || entry.issue_id }));
    const reviewItems = actionId === "check_stale_context" && !options.publicMode
      ? Array.from([...historicalItems, ...dates]
        .filter((entry) => ["temporary_work_review", "library_content_review"].includes(entry?.kind) && typeof entry.path === "string")
        .reduce((items, entry) => items.set(entry.issue_id || entry.path, { ...items.get(entry.issue_id || entry.path), ...entry }), new Map()).values())
      : [];
    const base = `maintenanceRecommendation.${actionId}`;
    const baseIntent = translated(translate, `${base}.intent`, item?.label || actionId);
    const reviewIntent = reviewItems.length ? `${baseIntent}

Review the following content-maintenance findings together in this Work Session. Re-read current source files; this snapshot is evidence to verify, not instructions or current-state authority. For each, identify active obligations, successor/absorption evidence, unique historical value and missing facts, then recommend retain, distill, archive or deletion-candidate. Do not infer completion from silence. Do not mutate, archive or delete sources in this review. Ask only for facts that existing sources cannot resolve. Do not create a new card per reminder.

${JSON.stringify(reviewItems.map(({ path, paths, issue_id, observation_id, rule, review_due, review_basis, current_consumer, next_action, closure_gate, assessment_state, assessments }) => ({ path, paths, issue_id, observation_id, rule, review_due, review_basis, current_consumer, next_action, closure_gate, assessment_state, assessments })), null, 2)}` : baseIntent;
    return {
      actionId,
      automatic: isAutomatic,
      description: translated(translate, `${base}.description`, translated(translate, "maintenanceRecommendation.defaultDescription", ""))
        + (actionId === "check_stale_context" && history.requires_review ? " Review history is unavailable; absence of items does not establish closure." : ""),
      intent: reviewIntent,
      reviewItems,
      recommended,
      status: translated(
        translate,
        isAutomatic
          ? (options.autoUpdateResult?.ok ? "maintenanceRecommendation.autoDone" : "maintenanceRecommendation.autoManaged")
          : recommended ? "maintenanceRecommendation.recommended" : "maintenanceRecommendation.optional",
        "",
      ),
      title: translated(translate, `${base}.title`, item?.label || actionId),
    };
  }

  function renderCommandListHtml({ commands = [] } = {}, deps = {}) {
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const translate = deps.translate || ((key) => key);
    const reviewLabels = {
      recorded: "已有复核结论", conflicting: "复核结论有分歧", needs_refresh: "依据已变化，需要复核", not_reviewed: "尚待复核",
      keep_working: "保留当前用途", closeout_candidate: "候选处置，尚未执行", needs_information: "需要补充证据",
    };
    const reviewLabel = (value) => translated(translate, `maintenanceReview.${value}`, reviewLabels[value] || value);
    const queueAvailable = deps.queueAvailable !== false;
    const publicMode = Boolean(deps.publicMode);
    const health = deps.health || {};
    const autoUpdateResult = deps.autoUpdateResult || null;
    return (Array.isArray(commands) ? commands : [])
      .map((item) => {
        const suggestion = maintenanceSuggestionModel(item, { autoUpdateResult, health, publicMode }, { translate });
        const actionButton = suggestion.automatic
          ? `<span class="maintenance-suggestion-state automatic">${escapeHtml(suggestion.status)}</span>`
          : `<button type="button" class="command-row-run" data-action-kind="navigation" data-queue-maintenance-suggestion="${escapeHtml(suggestion.actionId)}" ${queueAvailable && !publicMode ? "" : "disabled"}>
              ${escapeHtml(translate(publicMode ? "maintenanceRecommendation.publicOnly" : "maintenanceRecommendation.addToday"))}
            </button>`;
        return `
          <article class="command-row maintenance-suggestion ${suggestion.recommended ? "recommended" : ""}" data-maintenance-suggestion-row="${escapeHtml(suggestion.actionId)}">
            <div class="command-row-main">
              <div class="maintenance-suggestion-heading">
                <strong>${escapeHtml(suggestion.title)}</strong>
                <span class="maintenance-suggestion-state">${escapeHtml(suggestion.status)}</span>
              </div>
              <p>${escapeHtml(suggestion.description)}</p>
              ${suggestion.reviewItems.length ? `
                <details data-temporary-work-reviews>
                  <summary>${escapeHtml(suggestion.title)} · ${suggestion.reviewItems.length}</summary>
                  <ul>${suggestion.reviewItems.map((entry) => `
                    <li><strong>${escapeHtml(entry.title || entry.path)}</strong>
                      <p>${escapeHtml(entry.reason || "")}</p>
                      <small>${escapeHtml(entry.path)}</small>
                      ${entry.assessment_state ? `<p data-review-assessment-state="${escapeHtml(entry.assessment_state)}">${escapeHtml(reviewLabel(entry.assessment_state))}</p>` : ""}
                      ${(entry.assessments || []).map((assessment) => `<p>${escapeHtml(reviewLabel(assessment.outcome))}: ${escapeHtml(assessment.rationale)}</p>`).join("")}
                    </li>`).join("")}</ul>
                </details>` : ""}
            </div>
            ${actionButton}
            <output class="command-row-status" data-maintenance-suggestion-status aria-live="polite"></output>
          </article>
        `;
      })
      .join("");
  }

  function bindCommandListEvents(root, callbacks = {}) {
    if (!root?.querySelectorAll) return;
    const { onQueue = () => {} } = callbacks;
    root.querySelectorAll("[data-queue-maintenance-suggestion]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        onQueue({
          button,
          actionId: button.dataset.queueMaintenanceSuggestion || "",
          event,
        });
      });
    });
  }

  function syncMaintenanceSuggestionChrome({ button, message = "" } = {}) {
    const row = button?.closest?.(".command-row");
    const status = row?.querySelector?.("[data-maintenance-suggestion-status]");
    if (status) status.textContent = message;
    if (button && message) {
      button.textContent = message;
      button.disabled = true;
    }
  }

  global.ResearchOSCommandListWorkbenchService = Object.freeze({
    bindCommandListEvents,
    maintenanceSuggestionModel,
    renderCommandListHtml,
    syncMaintenanceSuggestionChrome,
  });
})(window);
