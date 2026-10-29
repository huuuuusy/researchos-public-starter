/* ResearchOS maintenance header.
 * 中文：Research portfolio 插件视图；在 Now 投影短期注意力、日历、项目生命周期与事项级执行摘要。
 * English: Research-portfolio plugin view; projects attention, calendar, lifecycle, and item-local execution summaries onto Now.
 */

(function attachResearchOSResearchPortfolioView(global) {
  const projectMaturityLevels = Object.freeze([
    Object.freeze({ id: "I0", labelKey: "researchMaturityI0Label", criteriaKey: "researchMaturityI0Criteria" }),
    Object.freeze({ id: "I1", labelKey: "researchMaturityI1Label", criteriaKey: "researchMaturityI1Criteria" }),
    Object.freeze({ id: "I2", labelKey: "researchMaturityI2Label", criteriaKey: "researchMaturityI2Criteria" }),
    Object.freeze({ id: "I3", labelKey: "researchMaturityI3Label", criteriaKey: "researchMaturityI3Criteria" }),
  ]);

  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      calendarMoveEnabled: Boolean(deps.calendarMoveEnabled),
      mutationEnabled: Boolean(deps.mutationEnabled),
      previewButton: deps.previewButton || (() => ""),
      publicDemo: Boolean(deps.publicDemo),
      translate: deps.translate || ((key) => key),
      mutationReceipt: deps.mutationReceipt || null,
    };
  }

  function displayText(value = "") {
    return String(value ?? "").replace(/_/g, " ").trim();
  }

  function sessionPresentation(session = null) {
    return global.ResearchOSWorkSessionState?.lifecycleProjection?.(session) || {
      state: session?.status === "running" ? "running" : session?.status === "completed" ? "ended" : session ? "ready" : "no_task",
    };
  }

  function startActionPresentation(item = {}, session = null) {
    const state = sessionPresentation(session).state || "invalid";
    const boundItemId = String(session?.portfolioBinding?.itemId || session?.portfolioBinding?.item_id || "").trim();
    const itemId = String(item?.id || "").trim();
    if (!session || state === "ended") {
      return Object.freeze({
        hintKey: "researchAttentionPrepareStepHint",
        labelKey: "researchAttentionPrepareStep",
        state: "prepare_step",
      });
    }
    if (!boundItemId || boundItemId !== itemId) {
      return Object.freeze({
        hintKey: "researchAttentionSwitchResearchHint",
        labelKey: "researchAttentionSwitchResearch",
        state: "switch_research",
      });
    }
    if (["verify_delivery", "verify_run", "failed_needs_impact_check", "ended_with_run_tracking"].includes(state)) {
      return Object.freeze({
        hintKey: "researchAttentionVerifyRunHint",
        labelKey: "researchAttentionVerifyRun",
        state,
      });
    }
    if (state === "running") {
      return Object.freeze({ hintKey: "researchAttentionViewRunHint", labelKey: "researchAttentionViewRun", state });
    }
    if (state === "failed_retryable") {
      return Object.freeze({ hintKey: "researchAttentionReviewFailureHint", labelKey: "researchAttentionReviewFailure", state });
    }
    if (["result_ready", "late_result_ready"].includes(state)) {
      return Object.freeze({ hintKey: "researchAttentionReviewResultHint", labelKey: "researchAttentionReviewResult", state });
    }
    if (state === "ended") {
      return Object.freeze({ hintKey: "researchAttentionStartAgainHint", labelKey: "researchAttentionStartAgain", state });
    }
    if (state === "invalid") {
      return Object.freeze({ hintKey: "researchAttentionInspectTaskStateHint", labelKey: "researchAttentionInspectTaskState", state });
    }
    const hasContinuity = Array.isArray(session?.turns) && session.turns.length > 0;
    return Object.freeze({
      hintKey: hasContinuity ? "researchAttentionCurrentTaskHint" : "researchAttentionPrepareStepHint",
      labelKey: hasContinuity ? "researchAttentionCurrentTask" : "researchAttentionPrepareStep",
      state: hasContinuity ? "current_task" : "prepare_step",
    });
  }

  function itemDomToken(item = {}) {
    return String(item.id || item.title || "item").replace(/[^a-zA-Z0-9_-]+/g, "-").replace(/^-+|-+$/g, "") || "item";
  }

  function contextualActionLabel(label = "", item = {}) {
    return `${String(label || "").trim()}: ${displayText(item.title || item.id || "")}`;
  }

  function projectMaturityLevel(item = {}) {
    const level = String(item.cardMaturity?.level || "").trim().toUpperCase();
    return projectMaturityLevels.some((entry) => entry.id === level) ? level : "";
  }

  function renderProjectMaturityPicker(item = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (item.state === "closed") return "";
    const currentLevel = projectMaturityLevel(item);
    return `<details class="research-maturity-picker">
      <summary>${escapeHtml(translate("researchMaturityChoose"))}</summary>
      <div class="research-maturity-options" role="group" aria-label="${escapeHtml(contextualActionLabel(translate("researchMaturityChoose"), item))}">
        ${projectMaturityLevels.map((entry) => {
          const criteria = translate(entry.criteriaKey);
          return `<button type="button" data-action-kind="handoff" data-portfolio-maturity-target="${entry.id}" data-portfolio-maturity-item="${escapeHtml(item.id || "")}" title="${escapeHtml(criteria)}" aria-pressed="${currentLevel === entry.id ? "true" : "false"}"><strong>${escapeHtml(translate(entry.labelKey))}</strong><span>${escapeHtml(criteria)}</span></button>`;
        }).join("")}
      </div>
      <small>${escapeHtml(translate("researchMaturityChooseHint"))}</small>
    </details>`;
  }
  function priorityLabel(value = "") {
    const normalized = String(value || "").trim();
    return normalized.match(/^P[0-3]/i)?.[0]?.toUpperCase() || normalized || "P2";
  }

  function managementBucketForItem(item = {}) {
    if (item.managementBucket) return item.managementBucket;
    return global.ResearchOSResearchPortfolioModel?.managementBucketForItem?.(item) || "unclassified";
  }

  function managementZoneForItem(item = {}) {
    if (item.managementZone) return item.managementZone;
    return global.ResearchOSResearchPortfolioModel?.managementZoneForItem?.(item) || "pending";
  }

  function managementBucketLabel(bucket = "unclassified", translate = (key) => key) {
    return translate({
      active: "researchManagementBucketActive",
      queued: "researchManagementBucketQueued",
      project_candidate: "researchManagementBucketCandidate",
      waiting: "researchManagementBucketWaiting",
      paused: "researchManagementBucketPaused",
      closed: "researchManagementBucketClosed",
      unclassified: "researchManagementBucketUnclassified",
    }[String(bucket || "unclassified")] || "researchManagementBucketUnclassified");
  }
  function phaseLabel(phase = "", translate = (key) => key) {
    return translate({
      accepted: "researchLifecyclePhaseAccepted",
      completed: "researchLifecyclePhaseCompleted",
      decision: "researchLifecyclePhaseDecision",
      experiment_preparation: "researchLifecyclePhaseExperimentPreparation",
      gated_operation: "researchLifecyclePhaseGatedOperation",
      planned: "researchLifecyclePhasePlanned",
      paused: "researchLifecyclePhasePaused",
      production: "researchLifecyclePhaseProduction",
      published: "researchLifecyclePhasePublished",
      rebuttal: "researchLifecyclePhaseRebuttal",
      release_preparation: "researchLifecyclePhaseReleasePreparation",
      revision: "researchLifecyclePhaseRevision",
      scoping: "researchLifecyclePhaseScoping",
      submitted: "researchLifecyclePhaseSubmitted",
      under_review: "researchLifecyclePhaseUnderReview",
      writing: "researchLifecyclePhaseWriting",
    }[String(phase || "").trim()] || "researchLifecyclePhaseScoping");
  }

  function responsibilityLabel(item = {}, translate = (key) => key) {
    if (item.responsibility === "support" && item.engagement === "temporary") {
      return translate("researchPortfolioResponsibilityTemporary");
    }
    return translate({
      lead: "researchPortfolioResponsibilityLead",
      support: "researchPortfolioResponsibilitySupport",
      unclassified: "researchPortfolioResponsibilityUnclassified",
    }[item.responsibility] || "researchPortfolioResponsibilityUnclassified");
  }

  function attentionLabel(item = {}, translate = (key) => key) {
    if (item.attentionState === "carryover") {
      return String(translate("researchAttentionCarryoverDays")).replace("{count}", String(item.carryoverDays || 1));
    }
    return translate({
      today: "researchAttentionToday",
      upcoming: "researchAttentionUpcoming",
      unscheduled: "researchAttentionUnscheduled",
      waiting: "researchAttentionDeferred",
      paused: "researchAttentionDeferred",
      needs_next_step: "researchAttentionNeedsNextStep",
      review_due: "researchAttentionReviewDue",
      completed: "researchAttentionCompleted",
    }[item.attentionState] || "researchAttentionUnscheduled");
  }

  function humanCheckOnly(item = {}) {
    return Boolean(item.backgroundPhase)
      && !item.needsAttention
      && ["today", "carryover"].includes(item.attentionState);
  }

  function workEligibleToday(item = {}) {
    return managementBucketForItem(item) === "active"
      && item.lifecycleState === "open"
      && ["today", "carryover"].includes(item.attentionState)
      && !humanCheckOnly(item);
  }

  function parkedCommitment(item = {}) {
    return item.state === "mainline"
      && item.lifecycleState === "open"
      && ["waiting", "paused"].includes(item.attentionState)
      && item.attentionSource === "attention_schedule"
      && ["waiting", "paused"].includes(item.lastAttentionAction)
      && !["review_due", "needs_next_step"].includes(item.attentionState);
  }

  function backgroundWithoutEvent(item = {}) {
    const background = Boolean(item.backgroundPhase)
      || ["submitted", "under_review", "decision"].includes(String(item.lifecyclePhase || ""));
    return background && !item.eventTriggered;
  }

  function terminalProject(item = {}) {
    return item.state === "closed"
      || item.lifecycleState === "completed"
      || item.lifecyclePhase === "completed";
  }

  function visibleOnStart(item = {}) {
    if (terminalProject(item)) return false;
    if (parkedCommitment(item)) return true;
    const bucket = managementBucketForItem(item);
    if (bucket === "active") {
      return !backgroundWithoutEvent(item);
    }
    return item.attentionState === "review_due" || Boolean(item.eventTriggered);
  }
  function isoOffset(days = 0) {
    const current = new Date();
    current.setHours(12, 0, 0, 0);
    current.setDate(current.getDate() + Number(days || 0));
    const year = current.getFullYear();
    const month = String(current.getMonth() + 1).padStart(2, "0");
    const day = String(current.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function validIsoDate(value = "") {
    const normalized = String(value || "").trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(normalized)) return false;
    const year = Number(normalized.slice(0, 4));
    const month = Number(normalized.slice(5, 7));
    const day = Number(normalized.slice(8, 10));
    const parsed = new Date(year, month - 1, day, 12, 0, 0, 0);
    return parsed.getFullYear() === year
      && parsed.getMonth() === month - 1
      && parsed.getDate() === day;
  }

  function currentMonthKey() {
    return isoOffset(0).slice(0, 7);
  }

  function normalizeMonthKey(value = "") {
    const normalized = String(value || "").trim();
    if (!/^\d{4}-\d{2}$/.test(normalized)) return currentMonthKey();
    const month = Number(normalized.slice(5, 7));
    return month >= 1 && month <= 12 ? normalized : currentMonthKey();
  }

  function shiftMonthKey(value = "", offset = 0) {
    const normalized = normalizeMonthKey(value);
    const year = Number(normalized.slice(0, 4));
    const month = Number(normalized.slice(5, 7));
    const shifted = new Date(year, month - 1 + Number(offset || 0), 1, 12, 0, 0, 0);
    return `${shifted.getFullYear()}-${String(shifted.getMonth() + 1).padStart(2, "0")}`;
  }

  function projectDateEvents(item = {}) {
    if (terminalProject(item)) return [];
    const fieldTypes = [
      ["attentionDate", "attention"],
      ["reviewDate", "review"],
      ["deadline", "deadline"],
    ];
    const inactive = ["waiting", "paused"].includes(item?.lifecycleState)
      || ["waiting", "paused"].includes(item?.state)
      || ["waiting", "paused"].includes(item?.attentionState);
    return fieldTypes.flatMap(([field, type]) => {
      const date = String(item?.[field] || "").trim();
      if ((type === "attention" && (backgroundWithoutEvent(item) || inactive)) || !validIsoDate(date)) return [];
      return [{ date, item, type }];
    }).sort((left, right) => left.date.localeCompare(right.date)
      || ({ attention: 0, review: 1, deadline: 2 }[left.type] ?? 3)
        - ({ attention: 0, review: 1, deadline: 2 }[right.type] ?? 3));
  }

  function calendarEvents(items = []) {
    const seen = new Set();
    return items.flatMap((item) => projectDateEvents(item).flatMap((event) => {
      const key = `${item?.id || ""}:${event.type}:${event.date}`;
      if (seen.has(key)) return [];
      seen.add(key);
      return [event];
    })).sort((left, right) => left.date.localeCompare(right.date)
      || ({ attention: 0, review: 1, deadline: 2 }[left.type] ?? 3)
        - ({ attention: 0, review: 1, deadline: 2 }[right.type] ?? 3)
      || String(left.item.title || "").localeCompare(String(right.item.title || "")));
  }

  function calendarUndatedItems(items = []) {
    return items.filter((item) => !terminalProject(item) && !projectDateEvents(item).length);
  }

  function calendarOtherMonthEvents(items = [], monthKey = currentMonthKey()) {
    const normalized = normalizeMonthKey(monthKey);
    const events = calendarEvents(items);
    const currentMonthIds = new Set(events
      .filter((event) => event.date.startsWith(`${normalized}-`))
      .map((event) => String(event.item?.id || event.item?.title || "")));
    const selected = new Map();
    for (const event of events) {
      const itemId = String(event.item?.id || event.item?.title || "");
      if (event.date.startsWith(`${normalized}-`) || currentMonthIds.has(itemId) || selected.has(itemId)) continue;
      selected.set(itemId, event);
    }
    return [...selected.values()];
  }

  function monthCells(monthKey = currentMonthKey()) {
    const normalized = normalizeMonthKey(monthKey);
    const year = Number(normalized.slice(0, 4));
    const month = Number(normalized.slice(5, 7));
    const leading = (new Date(year, month - 1, 1, 12, 0, 0, 0).getDay() + 6) % 7;
    const days = new Date(year, month, 0, 12, 0, 0, 0).getDate();
    const cells = Array.from({ length: leading }, () => "");
    for (let day = 1; day <= days; day += 1) {
      cells.push(`${normalized}-${String(day).padStart(2, "0")}`);
    }
    while (cells.length % 7) cells.push("");
    return Array.from({ length: cells.length / 7 }, (_, index) => cells.slice(index * 7, index * 7 + 7));
  }

  function calendarEventLabel(type = "attention", translate = (key) => key) {
    return translate({
      attention: "researchCalendarEventAttention",
      deadline: "researchCalendarEventDeadline",
      review: "researchCalendarEventReview",
    }[type] || "researchCalendarEventAttention");
  }

  function renderCalendarEvent(event = {}, deps = {}) {
    const { calendarMoveEnabled, escapeHtml, translate } = normalizeDeps(deps);
    const item = event.item || {};
    const movable = calendarMoveEnabled && event.type === "attention" && validIsoDate(event.date);
    const dragAttributes = movable
      ? ` data-calendar-drag-item="${escapeHtml(item.id || "")}" data-calendar-event-date="${escapeHtml(event.date)}" aria-grabbed="false"`
      : "";
    const interactionHint = movable ? ` · ${translate("researchCalendarEventMoveHint")}` : "";
    return `<button type="button" class="research-calendar-event type-${escapeHtml(event.type || "attention")}" data-action-kind="navigation" data-calendar-open-card="${escapeHtml(item.id || "")}"${dragAttributes} title="${escapeHtml(`${calendarEventLabel(event.type, translate)} · ${displayText(item.title || "")}${interactionHint}`)}">
      <span>${escapeHtml(calendarEventLabel(event.type, translate))}</span>
      <strong>${escapeHtml(displayText(item.title || ""))}</strong>
    </button>`;
  }

  function renderCalendarAgenda(events = [], deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const dates = [...new Set(events.map((event) => event.date))];
    if (!dates.length) return `<p class="research-calendar-empty">${escapeHtml(translate("researchCalendarMonthEmpty"))}</p>`;
    return `<div class="research-calendar-agenda" data-calendar-agenda>${dates.map((date) => `
      <section>
        <time datetime="${escapeHtml(date)}">${escapeHtml(date)}</time>
        <div>${events.filter((event) => event.date === date).map((event) => renderCalendarEvent(event, deps)).join("")}</div>
      </section>`).join("")}</div>`;
  }

  function renderCalendarMonth(items = [], monthKey = currentMonthKey(), deps = {}) {
    const { calendarMoveEnabled, escapeHtml, mutationEnabled, publicDemo, translate } = normalizeDeps(deps);
    const normalized = normalizeMonthKey(monthKey);
    const allEvents = calendarEvents(items);
    const events = allEvents.filter((event) => event.date.startsWith(`${normalized}-`));
    const otherMonthEvents = calendarOtherMonthEvents(items, normalized);
    const undated = calendarUndatedItems(items);
    const today = isoOffset(0);
    const monthLabel = String(translate("researchCalendarMonthLabel"))
      .replace("{year}", normalized.slice(0, 4))
      .replace("{month}", String(Number(normalized.slice(5, 7))));
    const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const rows = monthCells(normalized);
    return `<section class="research-calendar" data-research-calendar data-calendar-month="${escapeHtml(normalized)}">
      <header class="research-calendar-header">
        <div>
          <span>${escapeHtml(translate("researchCalendarEyebrow"))}</span>
          <h4>${escapeHtml(monthLabel)}</h4>
          <p>${escapeHtml(translate("researchCalendarHint"))}</p>
        </div>
        <div class="research-calendar-navigation" aria-label="${escapeHtml(translate("researchCalendarNavigation"))}">
          <button type="button" data-action-kind="navigation" data-calendar-shift="-1" aria-label="${escapeHtml(translate("researchCalendarPrevious"))}">‹</button>
          <button type="button" data-action-kind="navigation" data-calendar-current>${escapeHtml(translate("researchCalendarCurrent"))}</button>
          <button type="button" data-action-kind="navigation" data-calendar-shift="1" aria-label="${escapeHtml(translate("researchCalendarNext"))}">›</button>
        </div>
      </header>
      <div class="research-calendar-legend" aria-label="${escapeHtml(translate("researchCalendarLegend"))}">
        ${["attention", "review", "deadline"].map((type) => `<span class="type-${type}">${escapeHtml(calendarEventLabel(type, translate))}</span>`).join("")}
      </div>
      <p class="research-calendar-interaction-hint">${escapeHtml(translate(mutationEnabled ? "researchCalendarInteractionPrivate" : (calendarMoveEnabled ? "researchCalendarInteractionPreview" : "researchCalendarInteractionReadOnly")))}</p>
      <div class="research-calendar-grid-wrap">
        <table class="research-calendar-grid" aria-label="${escapeHtml(monthLabel)}">
          <thead><tr>${weekdays.map((day) => `<th scope="col">${escapeHtml(translate(`researchCalendarWeekday${day}`))}</th>`).join("")}</tr></thead>
          <tbody>${rows.map((row) => `<tr>${row.map((date) => {
            if (!date) return `<td class="is-outside" aria-hidden="true"></td>`;
            const dayEvents = events.filter((event) => event.date === date);
            return `<td class="${date === today ? "is-today" : ""}" data-calendar-date="${escapeHtml(date)}">
              <time datetime="${escapeHtml(date)}">${escapeHtml(String(Number(date.slice(8, 10))))}</time>
              <div>${dayEvents.slice(0, 3).map((event) => renderCalendarEvent(event, deps)).join("")}</div>
              ${dayEvents.length > 3 ? `<details class="research-calendar-day-more">
                <summary role="button" aria-label="${escapeHtml(String(translate("researchCalendarMore")).replace("{count}", String(dayEvents.length - 3)))}">${escapeHtml(String(translate("researchCalendarMore")).replace("{count}", String(dayEvents.length - 3)))}</summary>
                <div>${dayEvents.slice(3).map((event) => renderCalendarEvent(event, deps)).join("")}</div>
              </details>` : ""}
            </td>`;
          }).join("")}</tr>`).join("")}</tbody>
        </table>
      </div>
      ${renderCalendarAgenda(events, deps)}
      ${otherMonthEvents.length ? `<details class="research-calendar-other-months">
        <summary><span>${escapeHtml(translate("researchCalendarOtherMonths"))}</span><strong>${escapeHtml(String(otherMonthEvents.length))}</strong></summary>
        <p>${escapeHtml(translate("researchCalendarOtherMonthsHint"))}</p>
        <div>${otherMonthEvents.map((event) => `<button type="button" data-action-kind="navigation" data-calendar-open-card="${escapeHtml(event.item?.id || "")}"><time datetime="${escapeHtml(event.date)}">${escapeHtml(event.date)}</time><span>${escapeHtml(calendarEventLabel(event.type, translate))}</span><strong>${escapeHtml(displayText(event.item?.title || ""))}</strong></button>`).join("")}</div>
      </details>` : ""}
      ${undated.length ? `<details class="research-calendar-undated">
        <summary><span>${escapeHtml(translate("researchCalendarUndated"))}</span><strong>${escapeHtml(String(undated.length))}</strong></summary>
        <p>${escapeHtml(translate("researchCalendarUndatedHint"))}</p>
        <div>${undated.map((item) => `<button type="button" data-action-kind="navigation" data-calendar-open-card="${escapeHtml(item.id || "")}"><span>${escapeHtml(phaseLabel(item.lifecyclePhase, translate))}</span><strong>${escapeHtml(displayText(item.title || ""))}</strong><small>${escapeHtml(displayText(item.activationTrigger || item.nextStep || ""))}</small></button>`).join("")}</div>
      </details>` : ""}
      <p class="research-calendar-boundary">${escapeHtml(translate(publicDemo ? "researchCalendarBoundaryPublic" : "researchCalendarBoundary"))}</p>
    </section>`;
  }

  function renderCalendarWeek(items = [], anchorDate = isoOffset(0), deps = {}) {
    const { calendarMoveEnabled, escapeHtml, mutationEnabled, publicDemo, translate } = normalizeDeps(deps);
    const normalizedAnchor = validIsoDate(anchorDate) ? anchorDate : isoOffset(0);
    const day = new Date(`${normalizedAnchor}T12:00:00`);
    const start = shiftIsoDate(normalizedAnchor, -((day.getDay() + 6) % 7));
    const dates = Array.from({ length: 7 }, (_, index) => shiftIsoDate(start, index));
    const events = calendarEvents(items).filter((event) => dates.includes(event.date));
    return `<section class="research-calendar research-calendar-week" data-research-calendar data-calendar-week="${escapeHtml(start)}"><header class="research-calendar-header"><div><span>${escapeHtml(translate("researchCalendarWeekView"))}</span><h4>${escapeHtml(`${dates[0]} — ${dates[6]}`)}</h4><p>${escapeHtml(translate("researchCalendarHint"))}</p></div></header><div class="research-calendar-week-grid">${dates.map((date) => `<section class="${date === isoOffset(0) ? "is-today" : ""}" data-calendar-date="${escapeHtml(date)}"><time datetime="${escapeHtml(date)}">${escapeHtml(date)}</time><div>${events.filter((event) => event.date === date).map((event) => renderCalendarEvent(event, { ...deps, calendarMoveEnabled })).join("")}</div></section>`).join("")}</div><p class="research-calendar-interaction-hint">${escapeHtml(translate(mutationEnabled ? "researchCalendarInteractionPrivate" : (publicDemo ? "researchCalendarInteractionPreview" : "researchCalendarInteractionReadOnly")))}</p></section>`;
  }

  function actionButton(item = {}, label = "", action = "", options = {}, deps = {}) {
    const { escapeHtml } = normalizeDeps(deps);
    const disabled = options.disabled ? "disabled" : "";
    const className = options.primary ? "primary" : "";
    const offset = options.offset == null ? "" : ` data-attention-offset="${escapeHtml(String(options.offset))}"`;
    const startPrimary = options.startPrimary ? " data-start-primary-action" : "";
    return `<button type="button" class="${className}" data-action-kind="direct" data-attention-action="${escapeHtml(action)}" data-attention-item="${escapeHtml(item.id || "")}"${offset}${startPrimary} aria-label="${escapeHtml(contextualActionLabel(label, item))}" ${disabled}>${escapeHtml(label)}</button>`;
  }

  function renderMutationReceipt(receipt = null, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (!receipt) return "";
    return `
      <section class="research-attention-receipt" data-attention-receipt aria-live="polite">
        <span>${escapeHtml(receipt.message || translate("researchAttentionActionSaved"))}</span>
        ${receipt.viewToday ? `<button type="button" data-action-kind="navigation" data-portfolio-receipt-today>${escapeHtml(translate("researchAttentionViewToday"))}</button>` : ""}
        ${receipt.undo?.token ? `<button type="button" data-action-kind="direct" data-portfolio-undo>${escapeHtml(translate("researchAttentionUndo"))}</button>` : ""}
      </section>
    `;
  }

  function renderCard(item = {}, options = {}, deps = {}) {
    const { escapeHtml, previewButton, translate } = normalizeDeps(deps);
    const compact = Boolean(options.compact);
    const publicDemo = Boolean(options.publicDemo);
    const disabled = !options.mutationEnabled;
    const showMutationControls = !publicDemo || !disabled;
    const isToday = ["today", "carryover"].includes(item.attentionState);
    const isOpen = item.lifecycleState === "open" && !terminalProject(item);
    const managementBucket = managementBucketForItem(item);
    const canSchedule = managementBucket === "active" && !terminalProject(item);
    const needsStatusDecision = managementBucket !== "active" && !terminalProject(item);
    const showStepComplete = isOpen
      && managementBucketForItem(item) === "active"
      && item.attentionState !== "needs_next_step";
    const checkOnly = humanCheckOnly(item);
    const statusLabel = attentionLabel(item, translate);
    const whyNow = [
      statusLabel,
      item.deadline ? `${translate("researchAttentionDeadline")} ${item.deadline}` : "",
    ].filter(Boolean).join(" · ");
    const suggestedDate = item.attentionDate || isoOffset(1);
    const suggestedReviewDate = item.reviewDate || isoOffset(7);
    const showAdvanced = showMutationControls && (showStepComplete || isOpen)
      || (item.sourcePath && item.sourceAvailable);
    const tomorrowControl = showMutationControls && canSchedule
      ? actionButton(item, translate(checkOnly ? "researchAttentionCheckTomorrow" : "researchAttentionTomorrow"), "schedule", { offset: 1, disabled }, deps)
      : "";
    const dateControl = showMutationControls && canSchedule ? `<details class="research-attention-quick-choice is-date">
      <summary>${escapeHtml(translate("researchAttentionChooseDateQuick"))}</summary>
      <label>
        <span>${escapeHtml(translate("researchAttentionChooseDate"))}</span>
        <input type="date" min="${escapeHtml(isoOffset(0))}" value="${escapeHtml(suggestedDate)}" data-attention-date-input="${escapeHtml(item.id || "")}" ${disabled ? "disabled" : ""}>
      </label>
      <button type="button" data-action-kind="direct" data-attention-custom="schedule" data-attention-item="${escapeHtml(item.id || "")}" ${disabled ? "disabled" : ""}>${escapeHtml(translate("researchAttentionSchedule"))}</button>
    </details>` : "";
    const notNowControl = showMutationControls && canSchedule ? `<details class="research-attention-quick-choice is-not-now">
      <summary>${escapeHtml(translate("researchAttentionNotNow"))}</summary>
      <p>${escapeHtml(translate("researchAttentionNotNowHint"))}</p>
      <label>
        <span>${escapeHtml(translate("researchAttentionReviewOn"))}</span>
        <input type="date" min="${escapeHtml(isoOffset(0))}" value="${escapeHtml(suggestedReviewDate)}" data-attention-review-input="${escapeHtml(item.id || "")}" ${disabled ? "disabled" : ""}>
      </label>
      <div>
        <button type="button" data-action-kind="direct" data-attention-custom="paused" data-attention-item="${escapeHtml(item.id || "")}" ${disabled ? "disabled" : ""}>${escapeHtml(translate("researchAttentionDeferStep"))}</button>
      </div>
    </details>` : "";
    const scheduleControls = compact && canSchedule && showMutationControls
      ? `<details class="research-attention-adjust">
          <summary>${escapeHtml(translate("researchAttentionAdjustSchedule"))}</summary>
          <div>${tomorrowControl}${dateControl}${notNowControl}</div>
        </details>`
      : `${tomorrowControl}${dateControl}${notNowControl}`;
    const nextValue = checkOnly
      ? displayText(item.activationTrigger || item.nextStep || "")
      : item.attentionState === "needs_next_step"
        ? translate("researchAttentionNeedsNextStepBody")
        : displayText(item.nextStep || "");
    const cardTitleId = `research-attention-title-${itemDomToken(item)}`;
    const startAction = startActionPresentation(item, options.currentWorkSession || null);
    const currentTaskTitle = displayText(options.currentWorkSession?.portfolioBinding?.title || options.currentWorkSession?.title || options.currentWorkSession?.goal || "");
    const switchConfirmation = startAction.state === "switch_research" ? `<section class="research-attention-switch-confirm" data-research-switch-confirm hidden role="group" aria-label="${escapeHtml(translate("researchAttentionSwitchTitle"))}">
      <strong>${escapeHtml(translate("researchAttentionSwitchTitle"))}</strong>
      <dl>
        <div><dt>${escapeHtml(translate("researchAttentionSwitchCurrent"))}</dt><dd>${escapeHtml(currentTaskTitle)}</dd></div>
        <div><dt>${escapeHtml(translate("researchAttentionSwitchNext"))}</dt><dd>${escapeHtml(displayText(item.title || ""))}</dd></div>
      </dl>
      <p>${escapeHtml(translate("researchAttentionSwitchConsequence"))}</p>
      <div><button type="button" data-action-kind="navigation" data-portfolio-switch-cancel="${escapeHtml(item.id || "")}">${escapeHtml(translate("researchAttentionKeepCurrent"))}</button><button type="button" class="primary" data-action-kind="direct" data-portfolio-switch-confirm="${escapeHtml(item.id || "")}">${escapeHtml(translate("researchAttentionSaveAndSwitch"))}</button></div>
    </section>` : "";
    const reorderControls = isToday && Number(options.todayCount || 0) > 1 ? `<div class="research-attention-order" role="group" aria-label="${escapeHtml(translate("researchAttentionOrderLabel"))}">
      <button type="button" data-action-kind="direct" data-attention-reorder="up" data-attention-item="${escapeHtml(item.id || "")}" aria-label="${escapeHtml(contextualActionLabel(translate("researchAttentionMoveUp"), item))}" ${Number(options.todayIndex || 0) <= 0 ? "disabled" : ""}>${escapeHtml(translate("researchAttentionMoveUp"))}</button>
      <button type="button" data-action-kind="direct" data-attention-reorder="down" data-attention-item="${escapeHtml(item.id || "")}" aria-label="${escapeHtml(contextualActionLabel(translate("researchAttentionMoveDown"), item))}" ${Number(options.todayIndex || 0) >= Number(options.todayCount || 0) - 1 ? "disabled" : ""}>${escapeHtml(translate("researchAttentionMoveDown"))}</button>
    </div>` : "";
    return `
      <article class="research-attention-card state-${escapeHtml(item.attentionState || "unscheduled")} ${compact ? "is-compact" : ""}" data-attention-card="${escapeHtml(item.id || "")}"${isToday ? ` draggable="true" data-attention-sort-item="${escapeHtml(item.id || "")}"` : ""}${options.primaryCommitment ? " data-start-primary-commitment" : ""} aria-labelledby="${escapeHtml(cardTitleId)}">
        <header>
          <div>
            <span>${escapeHtml(responsibilityLabel(item, translate))} · ${escapeHtml(phaseLabel(item.lifecyclePhase, translate))}</span>
            <strong id="${escapeHtml(cardTitleId)}">${escapeHtml(displayText(item.title || ""))}</strong>
          </div>
          ${compact && item.attentionState === "today" ? "" : `<em>${escapeHtml(statusLabel)}</em>`}
        </header>
        <section class="research-attention-why" data-start-why-now>
          <small>${escapeHtml(translate("researchAttentionWhyNow"))}</small>
          <p>${escapeHtml(whyNow)}</p>
        </section>
        <section class="research-attention-next">
          <small>${escapeHtml(translate(checkOnly ? "researchAttentionHumanCheck" : "researchAttentionNextSafeAction"))}</small>
          <p title="${escapeHtml(nextValue)}">${escapeHtml(nextValue)}</p>
        </section>
        ${compact && options.expandableSummary ? `<details class="research-attention-card-details" data-attention-card-details ${options.defaultExpanded ? "open" : ""}>
          <summary><strong>${escapeHtml(translate("researchAttentionExpandItem"))}</strong></summary>
          <div class="research-attention-card-detail-body">` : ""}
        <div class="research-attention-meta">
          ${item.attentionDate ? `<time datetime="${escapeHtml(item.attentionDate)}">${escapeHtml(item.attentionDate)}</time>` : ""}
          ${item.deadline ? `<span>${escapeHtml(translate("researchAttentionDeadline"))} ${escapeHtml(item.deadline)}</span>` : ""}
          ${item.reviewDate ? `<span>${escapeHtml(translate("researchAttentionReviewDate"))} ${escapeHtml(item.reviewDate)}</span>` : ""}
        </div>
        <div class="research-attention-primary-actions">
          ${needsStatusDecision ? `<button type="button" class="primary" data-action-kind="direct" data-portfolio-open-execution="${escapeHtml(item.id || "")}" data-execution-panel="review"${options.primaryCommitment ? " data-start-primary-action" : ""} aria-label="${escapeHtml(contextualActionLabel(translate("researchAttentionReviewProject"), item))}">${escapeHtml(translate("researchAttentionReviewProject"))}</button>` : ""}
          ${isToday && isOpen && !checkOnly ? `<div class="research-attention-open-task" data-start-action-state="${escapeHtml(startAction.state)}">
            <button type="button" class="primary" data-action-kind="${startAction.state === "switch_research" ? "navigation" : "direct"}" data-portfolio-open-today="${escapeHtml(item.id || "")}"${options.primaryCommitment ? " data-start-primary-action" : ""} aria-describedby="research-attention-action-hint-${escapeHtml(itemDomToken(item))}"${startAction.state === "switch_research" ? ' aria-expanded="false"' : ""} aria-label="${escapeHtml(contextualActionLabel(translate(startAction.labelKey), item))}">${escapeHtml(translate(startAction.labelKey))}</button>
            <small id="research-attention-action-hint-${escapeHtml(itemDomToken(item))}">${escapeHtml(translate(startAction.hintKey))}</small>
          </div>` : ""}
          ${showMutationControls && !isToday && canSchedule ? actionButton(item, translate("researchAttentionToday"), "schedule", { offset: 0, disabled, primary: true, startPrimary: options.primaryCommitment }, deps) : ""}
          ${scheduleControls}
          ${showMutationControls && needsStatusDecision ? `<details class="research-attention-quick-choice is-not-now is-review-only">
            <summary>${escapeHtml(translate("researchAttentionSetReview"))}</summary>
            <p>${escapeHtml(translate("researchAttentionSetReviewHint"))}</p>
            <label>
              <span>${escapeHtml(translate("researchAttentionReviewOn"))}</span>
              <input type="date" min="${escapeHtml(isoOffset(0))}" value="${escapeHtml(suggestedReviewDate)}" data-attention-review-input="${escapeHtml(item.id || "")}" ${disabled ? "disabled" : ""}>
            </label>
            <button type="button" data-action-kind="direct" data-attention-custom="${managementBucket === "paused" ? "paused" : "waiting"}" data-attention-item="${escapeHtml(item.id || "")}" ${disabled ? "disabled" : ""}>${escapeHtml(translate("researchAttentionSaveReview"))}</button>
          </details>` : ""}
        </div>
        ${reorderControls}
        ${switchConfirmation}
        ${showAdvanced ? `<details class="research-attention-more">
          <summary>${escapeHtml(translate(showMutationControls ? (compact ? "researchAttentionProjectActions" : "researchAttentionMoreActions") : "researchPortfolioOpenSource"))}</summary>
          ${showMutationControls && showStepComplete ? `<div class="research-attention-step-action">
            ${actionButton(item, translate("researchAttentionCompleteStep"), "complete_step", { disabled }, deps)}
          </div>` : ""}
          ${showMutationControls && isOpen ? `<details class="research-attention-complete-project">
            <summary>${escapeHtml(translate("researchAttentionCompleteProjectSummary"))}</summary>
            <p>${escapeHtml(translate("researchAttentionCompleteProjectBody"))}</p>
            <button type="button" data-action-kind="direct" data-portfolio-complete-project="${escapeHtml(item.id || "")}" aria-label="${escapeHtml(contextualActionLabel(translate("researchAttentionCompleteProjectConfirm"), item))}" ${disabled ? "disabled" : ""}>${escapeHtml(translate("researchAttentionCompleteProjectConfirm"))}</button>
          </details>` : ""}
          ${item.sourcePath && item.sourceAvailable ? `<footer>${previewButton(item.sourcePath, translate("researchPortfolioOpenSource"), { anchor: item.sourceAnchor || "", ariaLabel: contextualActionLabel(translate("researchPortfolioOpenSource"), item) })}</footer>` : ""}
        </details>` : ""}
        <footer class="research-attention-context-actions"><button type="button" data-action-kind="navigation" data-portfolio-open-library="${escapeHtml(item.id || "")}">${escapeHtml(translate("researchAttentionViewRelated"))}</button><button type="button" data-action-kind="direct" data-portfolio-open-execution="${escapeHtml(item.id || "")}" data-execution-panel="work">${escapeHtml(translate("researchAttentionViewExecution"))}</button></footer>
        ${disabled && !publicDemo ? `<small class="research-attention-demo-note">${escapeHtml(translate("researchAttentionReadOnly"))}</small>` : ""}
        ${compact && options.expandableSummary ? "</div></details>" : ""}
        <output data-portfolio-action-status aria-live="polite"></output>
      </article>
    `;
  }

  function renderSection(titleKey, hintKey, items = [], options = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (!items.length && options.hideWhenEmpty) return "";
    const visibleLimit = Math.max(0, Number(options.visibleLimit || items.length));
    const visibleItems = items.slice(0, visibleLimit);
    const remainingItems = items.slice(visibleLimit);
    const moreClass = options.moreClass || "research-attention-today-more";
    const moreKey = options.moreKey || "researchAttentionTodayMore";
    return `
      <section class="research-attention-section ${escapeHtml(options.className || "")}">
        <header><div><h4>${escapeHtml(translate(titleKey))}</h4><p>${escapeHtml(translate(hintKey))}</p></div><strong>${escapeHtml(String(items.length))}</strong></header>
        ${items.length
          ? `<div class="research-attention-grid">${visibleItems.map((item, index) => renderCard(item, { ...options, defaultExpanded: Boolean(options.defaultExpandFirst) && index === 0, primaryCommitment: Boolean(options.primaryCommitment) && index === 0, todayCount: items.length, todayIndex: index }, deps)).join("")}</div>
            ${remainingItems.length ? `<details class="${escapeHtml(moreClass)}">
              <summary>${escapeHtml(String(translate(moreKey)).replace("{count}", String(remainingItems.length)))}</summary>
              <div class="research-attention-grid">${remainingItems.map((item) => renderCard(item, { ...options, primaryCommitment: false }, deps)).join("")}</div>
            </details>` : ""}`
          : `<p class="research-attention-empty">${escapeHtml(translate("researchAttentionEmpty"))}</p>`}
      </section>
    `;
  }

  function renderDecisionSection(items = [], options = {}, deps = {}) {
    if (!items.length) return "";
    const { escapeHtml, translate } = normalizeDeps(deps);
    const [current, ...remaining] = items;
    return `
      <details class="research-attention-section is-decision" data-attention-decision-queue open>
        <summary><span>${escapeHtml(translate("researchAttentionDecisionTitle"))}</span><strong>${escapeHtml(String(items.length))}</strong></summary>
        <p class="research-attention-decision-hint">${escapeHtml(translate("researchAttentionDecisionHint"))}</p>
        ${current ? `<div class="research-attention-grid" data-attention-decision-current>${renderCard(current, options, deps)}</div>` : `<p class="research-attention-empty">${escapeHtml(translate("researchAttentionEmpty"))}</p>`}
        ${remaining.length ? `<details class="research-attention-decision-more">
          <summary>${escapeHtml(String(translate("researchAttentionDecisionMore")).replace("{count}", String(remaining.length)))}</summary>
          <div class="research-attention-grid">${remaining.map((item) => renderCard(item, options, deps)).join("")}</div>
        </details>` : ""}
      </details>
    `;
  }
  function groups(items = []) {
    const today = items.filter((item) => ["today", "carryover"].includes(item.attentionState) && item.lifecycleState === "open");
    const upcoming = items.filter((item) => item.attentionState === "upcoming" && item.lifecycleState === "open");
    const decision = items.filter((item) => (
      item.state === "mainline" && item.lifecycleState === "open" && ["unscheduled", "needs_next_step", "review_due"].includes(item.attentionState)
    ) || (["waiting", "paused"].includes(item.lifecycleState) && item.attentionState === "review_due"));
    return {
      today,
      decision,
      upcoming,
      waiting: items.filter((item) => item.lifecycleState === "waiting" && item.attentionState !== "review_due"),
      paused: items.filter((item) => item.lifecycleState === "paused" && item.attentionState !== "review_due"),
      later: items.filter((item) => ["queued", "conditional"].includes(item.state) && item.lifecycleState === "open"),
      completed: items.filter((item) => item.lifecycleState === "completed"),
    };
  }
  function managementZoneGroups(items = []) {
    return items.reduce((result, item) => {
      result[managementZoneForItem(item)].push(item);
      return result;
    }, { active: [], pending: [], inactive: [], closed: [] });
  }

  function relevantProjectDate(item = {}) {
    const bucket = managementBucketForItem(item);
    const allowedTypes = bucket === "active"
      ? new Set(["attention", "review", "deadline"])
      : ["queued", "project_candidate", "waiting", "paused", "unclassified"].includes(bucket)
        ? new Set(["review", "deadline"])
        : new Set();
    const event = projectDateEvents(item).find((candidate) => allowedTypes.has(candidate.type));
    return event ? [event.type, event.date] : ["", ""];
  }

  function earliestProjectDate(item = {}) {
    return projectDateEvents(item)[0]?.date || "";
  }

  function shiftIsoDate(value = isoOffset(0), offset = 0) {
    const normalized = validIsoDate(value) ? value : isoOffset(0);
    const date = new Date(
      Number(normalized.slice(0, 4)),
      Number(normalized.slice(5, 7)) - 1,
      Number(normalized.slice(8, 10)),
      12,
      0,
      0,
      0,
    );
    date.setDate(date.getDate() + Number(offset || 0));
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  }

  function horizonForItem(item = {}, today = isoOffset(0)) {
    if (item.lifecycleState === "completed" || item.lifecyclePhase === "completed" || item.state === "closed") return "frozen";
    if (parkedCommitment(item)) return "frozen";
    if (["review_due", "needs_next_step"].includes(item.attentionState) || item.eventTriggered) return "today";
    if (item.lifecycleState === "paused" || item.lifecyclePhase === "paused" || item.state === "paused") return "frozen";
    if (backgroundWithoutEvent(item)) return "frozen";
    if (["today", "carryover"].includes(item.attentionState)) return "today";
    if (item.actionable && item.attentionState === "unscheduled") return "today";
    const date = earliestProjectDate(item);
    if (date && date <= today) return "today";
    if (date === shiftIsoDate(today, 1)) return "tomorrow";
    if (date) return "future";
    if (item.lifecycleState === "waiting" || item.state === "waiting" || item.backgroundPhase) return "frozen";
    return "future";
  }

  function horizonGroups(items = []) {
    return items.reduce((result, item) => {
      result[horizonForItem(item)].push(item);
      return result;
    }, { today: [], tomorrow: [], future: [], frozen: [] });
  }

  function startHorizonGroups(items = []) {
    return horizonGroups(items.filter(visibleOnStart));
  }

  function horizonLabel(horizon = "today", translate = (key) => key) {
    return translate({
      today: "researchLifecycleHorizonToday",
      tomorrow: "researchLifecycleHorizonTomorrow",
      future: "researchLifecycleHorizonFuture",
      frozen: "researchLifecycleHorizonFrozen",
    }[horizon] || "researchLifecycleHorizonToday");
  }

  function renderHorizonPanel(items = [], horizon = "today", options = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const hint = translate({
      today: "researchLifecycleHorizonTodayHint",
      tomorrow: "researchLifecycleHorizonTomorrowHint",
      future: "researchLifecycleHorizonFutureHint",
      frozen: "researchLifecycleHorizonFrozenHint",
    }[horizon] || "researchLifecycleHorizonTodayHint");
    const archivedItems = horizon === "frozen" ? items.filter(terminalProject) : [];
    const currentItems = horizon === "frozen" ? items.filter((item) => !terminalProject(item)) : items;
    const visibleLimit = Math.max(0, Number(options.visibleLimit || 0));
    const visibleItems = visibleLimit ? currentItems.slice(0, visibleLimit) : currentItems;
    const foldedItems = visibleLimit ? currentItems.slice(visibleLimit) : [];
    return `<section class="research-lifecycle-horizon-panel" data-lifecycle-horizon-panel="${escapeHtml(horizon)}">
      <header><h4>${escapeHtml(horizonLabel(horizon, translate))}</h4><p>${escapeHtml(hint)}</p></header>
      ${currentItems.length
        ? `<div class="research-lifecycle-grid">${visibleItems.map((item) => renderLifecycleCard(item, options, deps)).join("")}</div>
          ${foldedItems.length ? `<details class="research-lifecycle-horizon-more">
            <summary>${escapeHtml(String(translate("researchLifecycleMore")).replace("{count}", String(foldedItems.length)))}</summary>
            <div class="research-lifecycle-grid">${foldedItems.map((item) => renderLifecycleCard(item, options, deps)).join("")}</div>
          </details>` : ""}`
        : archivedItems.length ? "" : `<p class="research-lifecycle-horizon-empty">${escapeHtml(translate("researchLifecycleHorizonEmpty"))}</p>`}
      ${archivedItems.length ? `<details class="research-lifecycle-horizon-more research-lifecycle-archive">
        <summary>${escapeHtml(String(translate("researchLifecycleArchiveMore")).replace("{count}", String(archivedItems.length)))}</summary>
        <div class="research-lifecycle-grid">${archivedItems.map((item) => renderLifecycleCard(item, options, deps)).join("")}</div>
      </details>` : ""}
    </section>`;
  }

  function renderLifecycleCard(item = {}, options = {}, deps = {}) {
    const { escapeHtml, previewButton, translate } = normalizeDeps(deps);
    const bucket = managementBucketForItem(item);
    const zone = managementZoneForItem(item);
    const inactive = zone === "inactive" && item.attentionState !== "review_due";
    const canMoveToday = parkedCommitment(item) || (
      bucket === "active"
      && !backgroundWithoutEvent(item)
      && !["today", "carryover"].includes(item.attentionState)
    );
    const showMutationControls = !options.publicDemo || options.mutationEnabled;
    const [relevantDateType, relevantDate] = relevantProjectDate(item);
    const status = relevantDate
      ? String(translate({
        attention: "researchLifecycleAttentionDate",
        deadline: "researchLifecycleDeadlineDate",
        review: "researchLifecycleReviewDate",
      }[relevantDateType] || "researchLifecycleScheduledFor")).replace("{date}", relevantDate)
      : item.activationTrigger
        ? translate("researchLifecycleWaitingForEvent")
        : bucket === "closed"
          ? translate("researchAttentionCompleted")
          : item.attentionState === "unscheduled"
          ? translate("researchLifecycleNotDated")
          : inactive
            ? translate("researchLifecycleNoAction")
            : attentionLabel(item, translate);
    const nextLabel = item.activationTrigger ? translate("researchLifecycleTrigger") : translate("researchPortfolioNextStep");
    const nextValue = item.activationTrigger || item.nextStep || "";
    const focused = options.focusItemId && options.focusItemId === item.id;
    const rawPriority = String(item.priority || "P2").trim();
    const showPriority = ["active", "queued"].includes(bucket);
    const levelText = `${responsibilityLabel(item, translate)}${showPriority ? ` · ${priorityLabel(rawPriority)}` : ""}`;
    const updatedDate = String(item.lastVerified || "").trim();
    const updatedLabel = updatedDate
      ? String(translate("researchLifecycleUpdated")).replace("{date}", updatedDate)
      : translate("researchLifecycleUpdatedUnknown");
    const maturity = item.cardMaturity || {};
    const maturityLevel = maturity.display_level || maturity.level || "I?";
    const maturityActionKey = ({
      enhance: "assetAdvancedUpgrade",
      reverify: "assetAdvancedReverify",
      use: "assetCardInspectUpgrade",
      verify: "assetAdvancedVerifyLevel",
    })[maturity.action || "verify"] || "assetAdvancedVerifyLevel";
    const maturityDisplay = maturity.confirmed
      ? maturityLevel
      : maturity.level
        ? `${maturityLevel} · ${translate("assetMaturityPendingShort")}`
        : translate("researchMaturityUnregisteredBadge");
    const maturityTitle = maturity.reason || (maturity.confirmed
      ? [maturityLevel, maturity.target_level ? `→ ${maturity.target_level}` : "", translate(maturityActionKey)].filter(Boolean).join(" · ")
      : translate("assetLineagePendingHint"));
    const relatedPeople = Array.isArray(item.relatedPeople) ? item.relatedPeople : [];
    const itemSessions = (Array.isArray(options.sessionRegistry) ? options.sessionRegistry : []).filter((entry) => String(entry?.item_id || "") === String(item.id || ""));
    const workCounts = itemSessions.reduce((counts, entry) => { const key = ["active", "needs_review", "waiting", "ready", "done"].includes(entry.work_state) ? entry.work_state : "ready"; counts[key] += 1; return counts; }, { active: 0, done: 0, needs_review: 0, ready: 0, waiting: 0 });
    const executionSummary = itemSessions.length ? `<div class="research-lifecycle-execution" aria-label="${escapeHtml(translate("researchExecutionSummaryLabel"))}"><small>${escapeHtml(translate("researchExecutionSummaryLabel"))}</small><span>${escapeHtml(String(translate("researchExecutionSummaryValue")).replace("{sessions}", String(itemSessions.length)).replace("{active}", String(workCounts.active)).replace("{review}", String(workCounts.needs_review)))}</span></div>` : `<div class="research-lifecycle-execution is-empty"><small>${escapeHtml(translate("researchExecutionSummaryLabel"))}</small><span>${escapeHtml(translate("researchExecutionSummaryEmpty"))}</span></div>`;
    const cardTitleId = `research-lifecycle-title-${itemDomToken(item)}`;
    return `
      <article class="research-lifecycle-card phase-${escapeHtml(item.lifecyclePhase || "scoping")} ${focused ? "is-calendar-focus" : ""}" data-lifecycle-card="${escapeHtml(item.id || "")}" tabindex="-1" aria-labelledby="${escapeHtml(cardTitleId)}">
        <header>
          <div>
            <span class="research-lifecycle-level" data-priority-code="${escapeHtml(rawPriority)}">${escapeHtml(levelText)}</span>
            <strong id="${escapeHtml(cardTitleId)}" title="${escapeHtml(displayText(item.title || ""))}">${escapeHtml(displayText(item.title || ""))}</strong>
          </div>
          ${!options.compact ? `<time class="research-lifecycle-updated" data-project-updated-date="${escapeHtml(updatedDate)}"${updatedDate ? ` datetime="${escapeHtml(updatedDate)}"` : ""}>${escapeHtml(updatedLabel)}</time>` : ""}
        </header>
        <div class="research-lifecycle-status-row" aria-label="${escapeHtml(translate("researchManagementStatusLabel"))}">
          <span>${escapeHtml(managementBucketLabel(bucket, translate))}</span>
          <em>${escapeHtml(phaseLabel(item.lifecyclePhase, translate))}</em>
          <b class="research-lifecycle-maturity ${maturity.confirmed ? "is-confirmed" : "is-pending"}" title="${escapeHtml(maturityTitle)}">${escapeHtml(maturityDisplay)}</b>
        </div>
        ${executionSummary}
        ${relatedPeople.length ? `<div class="research-lifecycle-people" title="${escapeHtml(relatedPeople.map((person) => person.name).join(" / "))}">
          <small>${escapeHtml(translate("assetLineagePeople"))}</small>
          <span>${escapeHtml(relatedPeople.slice(0, 2).map((person) => person.name).join(" / "))}${relatedPeople.length > 2 ? ` +${escapeHtml(String(relatedPeople.length - 2))}` : ""}</span>
        </div>` : ""}
        <section>
          <small>${escapeHtml(nextLabel)}</small>
          <p title="${escapeHtml(displayText(nextValue))}">${escapeHtml(displayText(nextValue))}</p>
        </section>
        ${item.currentStage ? `<details class="research-lifecycle-context">
          <summary>${escapeHtml(translate("researchLifecycleContext"))}</summary>
          <p>${escapeHtml(displayText(item.currentStage))}</p>
        </details>` : ""}
        <footer>
          <span class="research-lifecycle-attention ${inactive ? "is-background" : ""}">${escapeHtml(status)}</span>
          ${bucket !== "closed" ? renderProjectMaturityPicker(item, deps) : ""}
          ${item.sourcePath && item.sourceAvailable ? previewButton(item.sourcePath, translate("researchPortfolioOpenSource"), { anchor: item.sourceAnchor || "", ariaLabel: contextualActionLabel(translate("researchPortfolioOpenSource"), item) }) : ""}
          ${showMutationControls && canMoveToday ? `<button type="button" data-action-kind="direct" data-attention-action="schedule" data-attention-item="${escapeHtml(item.id || "")}" data-attention-offset="0" aria-label="${escapeHtml(contextualActionLabel(translate(item.backgroundPhase ? "researchLifecycleTriggerAction" : "researchLifecycleMoveToday"), item))}" ${options.mutationEnabled ? "" : "disabled"}>${escapeHtml(translate(item.backgroundPhase ? "researchLifecycleTriggerAction" : "researchLifecycleMoveToday"))}</button>` : ""}
          <button type="button" data-action-kind="navigation" data-portfolio-open-library="${escapeHtml(item.id || "")}">${escapeHtml(translate("researchAttentionViewRelated"))}</button>
          <button type="button" data-action-kind="direct" data-portfolio-open-execution="${escapeHtml(item.id || "")}" data-execution-panel="work">${escapeHtml(translate("researchAttentionViewExecution"))}</button>
        </footer>
        ${!options.mutationEnabled && !options.publicDemo ? `<small class="research-attention-demo-note">${escapeHtml(translate("researchAttentionReadOnly"))}</small>` : ""}
        <output data-portfolio-action-status aria-live="polite"></output>
      </article>
    `;
  }
  function render({ calendarMonth = "", calendarView = "month", horizon = "today", researchPortfolio = {}, mutationEnabled = false, mutationReceipt = null, currentWorkSession = null, sessionRegistry = [] } = {}, deps = {}) {
    const { escapeHtml, previewButton, translate } = normalizeDeps(deps);
    if (!researchPortfolio?.available || !Array.isArray(researchPortfolio.items)) return "";
    const focusFilteredItems = researchPortfolio.items;
    const horizons = startHorizonGroups(focusFilteredItems);
    const activeProjects = focusFilteredItems.filter((item) => !terminalProject(item));
    const recentlyClosedProjects = focusFilteredItems.filter(terminalProject);
    const visibleActiveProjects = activeProjects.slice(0, 6);
    const foldedActiveProjects = activeProjects.slice(6);
    const todayItems = horizons.today.filter(workEligibleToday);
    const todayIds = new Set(todayItems.map((item) => item.id));
    const decisionItems = horizons.today.filter((item) => !todayIds.has(item.id));
    const normalizedHorizon = ["today", "tomorrow", "future", "frozen"].includes(horizon) ? horizon : "today";
    const options = { compact: true, currentWorkSession, mutationEnabled: Boolean(mutationEnabled), publicDemo: Boolean(researchPortfolio.publicDemo), sessionRegistry };
    const scheduledCount = horizons.today.length + horizons.tomorrow.length + horizons.future.length + horizons.frozen.length;
    const scheduleSummary = String(translate("researchAttentionScheduleSummary"))
      .replace("{count}", String(scheduledCount));
    return `
      <section class="research-attention-board" data-research-portfolio aria-label="${escapeHtml(translate("researchAttentionTitle"))}">
        ${researchPortfolio.publicDemo ? `<p class="research-attention-demo-boundary">${escapeHtml(translate("researchAttentionDemoBoundary"))}</p>` : ""}
        ${renderMutationReceipt(mutationReceipt, deps)}
        ${normalizedHorizon === "today"
          ? horizons.today.length
            ? `${renderSection("researchAttentionTodayTitle", "researchAttentionTodayHint", todayItems, { ...options, className: "is-today", defaultExpandFirst: true, expandableSummary: true, visibleLimit: todayItems.length, hideWhenEmpty: true, primaryCommitment: false }, deps)}
              ${renderDecisionSection(decisionItems, options, deps)}`
            : `<p class="research-attention-empty">${escapeHtml(translate("researchAttentionNothingActionable"))}</p>`
          : ""}
        <details class="research-attention-schedule" ${normalizedHorizon === "today" ? "" : "open"}>
          <summary><span>${escapeHtml(translate("researchAttentionScheduleTitle"))}</span><small>${escapeHtml(scheduleSummary)}</small></summary>
          <div class="research-attention-schedule-body">
            <div class="research-lifecycle-horizon-switch research-attention-horizon-switch" role="group" aria-label="${escapeHtml(translate("researchLifecycleDestinationLabel"))}">
              ${["today", "tomorrow", "future", "frozen"].map((key) => `<button type="button" data-action-kind="navigation" data-portfolio-start-horizon="${key}" aria-pressed="${normalizedHorizon === key ? "true" : "false"}" class="${normalizedHorizon === key ? "selected" : ""}"><span>${escapeHtml(horizonLabel(key, translate))}</span><strong>${escapeHtml(String(key === "today" ? todayItems.length : horizons[key].length))}</strong></button>`).join("")}
            </div>
            ${normalizedHorizon === "today"
              ? ""
              : renderHorizonPanel(horizons[normalizedHorizon], normalizedHorizon, { ...options, visibleLimit: 3 }, deps)}
          </div>
        </details>
        <section class="research-now-calendar" data-now-calendar aria-label="${escapeHtml(translate("researchLifecycleViewCalendar"))}"><header><div><h4>${escapeHtml(translate("researchLifecycleViewCalendar"))}</h4><p>${escapeHtml(translate("researchCalendarHint"))}</p></div><div class="research-calendar-view-switch" role="group" aria-label="${escapeHtml(translate("researchCalendarViewLabel"))}"><button type="button" data-action-kind="navigation" data-calendar-view="week" aria-pressed="${calendarView === "week" ? "true" : "false"}" class="${calendarView === "week" ? "selected" : ""}">${escapeHtml(translate("researchCalendarWeekView"))}</button><button type="button" data-action-kind="navigation" data-calendar-view="month" aria-pressed="${calendarView !== "week" ? "true" : "false"}" class="${calendarView !== "week" ? "selected" : ""}">${escapeHtml(translate("researchCalendarMonthView"))}</button></div></header>${calendarView === "week" ? renderCalendarWeek(focusFilteredItems, isoOffset(0), { ...deps, calendarMoveEnabled: true, mutationEnabled, publicDemo: true }) : renderCalendarMonth(focusFilteredItems, calendarMonth || currentMonthKey(), { ...deps, calendarMoveEnabled: true, mutationEnabled, publicDemo: true })}</section>
        <section class="research-now-active-projects" data-now-active-projects><header><div><h4>${escapeHtml(translate("researchLifecycleTitle"))}</h4><p>${escapeHtml(translate("researchManagementBucketActiveHint"))}</p></div><strong>${escapeHtml(String(activeProjects.length))}</strong></header><div class="research-lifecycle-grid">${visibleActiveProjects.map((item) => renderLifecycleCard(item, { ...options, compact: false }, deps)).join("")}</div>${foldedActiveProjects.length ? `<details class="research-lifecycle-horizon-more" data-now-active-projects-more><summary>${escapeHtml(String(translate("researchLifecycleMore")).replace("{count}", String(foldedActiveProjects.length)))}</summary><div class="research-lifecycle-grid">${foldedActiveProjects.map((item) => renderLifecycleCard(item, { ...options, compact: false }, deps)).join("")}</div></details>` : ""}${recentlyClosedProjects.length ? `<details class="research-lifecycle-horizon-more research-lifecycle-archive"><summary>${escapeHtml(String(translate("researchLifecycleArchiveMore")).replace("{count}", String(recentlyClosedProjects.length)))}</summary><div class="research-lifecycle-grid">${recentlyClosedProjects.map((item) => renderLifecycleCard(item, { ...options, compact: false }, deps)).join("")}</div></details>` : ""}</section>
      </section>
    `;
  }

  function renderLibrary({ calendarMonth = "", focusItemId = "", zone = "active", mutationReceipt = null, researchPortfolio = {}, mutationEnabled = false, viewMode = "cards" } = {}, deps = {}) {
    return "";
  }

  global.ResearchOSResearchPortfolioView = Object.freeze({
    attentionLabel,
    calendarEvents,
    calendarOtherMonthEvents,
    calendarUndatedItems,
    projectDateEvents,
    currentMonthKey,
    displayText,
    groups,
    humanCheckOnly,
    terminalProject,
    horizonForItem,
    horizonGroups,
    startHorizonGroups,
    managementBucketForItem,
    managementZoneForItem,
    managementZoneGroups,
    parkedCommitment,
    phaseLabel,
    priorityLabel,
    isoOffset,
    monthCells,
    normalizeMonthKey,
    render,
    renderCard,
    renderCalendarMonth,
    renderCalendarWeek,
    renderLibrary,
    renderLifecycleCard,
    responsibilityLabel,
    shiftIsoDate,
    shiftMonthKey,
    startActionPresentation,
    validIsoDate,
  });
})(window);
