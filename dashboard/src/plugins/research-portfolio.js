/* ResearchOS maintenance header.
 * 中文：Research portfolio 第一方插件适配器；独占责任台账投影、lead/support/waiting 计算和 Today 领域事件，核心只保留任务生命周期。
 * English: First-party research-portfolio plugin adapter; exclusively owns responsibility projection, lead/support/waiting calculation, and Today domain events while core retains task lifecycle.
 */

(function attachResearchOSResearchPortfolioPlugin(global) {
  const scrollIntoView = global.ResearchOSInteractions?.scrollIntoView || ((target, options = {}) => target?.scrollIntoView?.(options));
  const PluginRuntime = global.ResearchOSPluginRuntime;
  const PortfolioModel = global.ResearchOSResearchPortfolioModel;
  const PortfolioView = global.ResearchOSResearchPortfolioView;
  const pluginId = "research_portfolio";
  const PortfolioWorkbench = global.ResearchOSResearchPortfolioWorkbench;
  const PortfolioCopy = global.ResearchOSResearchPortfolioCopy;
  const WorkSessionClient = global.ResearchOSWorkSessionClient;
  let startHorizon = "today";
  let nowCalendarMonth = PortfolioView?.currentMonthKey?.() || "";
  let nowCalendarView = "month";
  const publicCalendarPreviewDates = Object.create(null);
  const publicTodayPreviewOrders = Object.create(null);
  let publicPreviewReceipt = null;

  function rerenderStart(context = {}, reopenPublicExample = false) {
    context.rerenderDashboard?.();
    if (!reopenPublicExample) return;
    global.setTimeout?.(() => {
      const example = global.document?.querySelector?.("details.research-portfolio-public-example");
      if (example) example.open = true;
    }, 0);
  }

  function textFrom(context = {}, key = "") {
    return PortfolioCopy?.text(context.language || "en", key)
      || context.translate?.(key)
      || context.text?.(key)
      || key;
  }

  function modelFrom(slotModel = {}, context = {}) {
    return PortfolioModel.build(
      slotModel.payloads?.research_portfolio || {},
      (key) => textFrom(context, key),
      context.language || "en"
    );
  }

  function publicDemoHidden(model = {}, context = {}) {
    return Boolean(model.publicDemo) && context.publicDemoVisible?.() === false;
  }

  function modelWithCalendarPreview(model = {}) {
    if (!model.publicDemo || (!Object.keys(publicCalendarPreviewDates).length && !Object.keys(publicTodayPreviewOrders).length)) return model;
    return {
      ...model,
      items: model.items.map((item) => ({ ...item, ...(publicCalendarPreviewDates[item.id] ? { attentionDate: publicCalendarPreviewDates[item.id] } : {}), ...(publicTodayPreviewOrders[item.id] ? { todayOrder: publicTodayPreviewOrders[item.id] } : {}) })).sort((left, right) => left.todayOrder - right.todayOrder || left.title.localeCompare(right.title)),
    };
  }

  function renderWorkbench(slotModel = {}, context = {}) {
    if (!PortfolioModel || !PortfolioView) return "";
    const model = modelWithCalendarPreview(modelFrom(slotModel, context));
    if (publicDemoHidden(model, context)) return "";
    const html = PortfolioView.render(
      {
        calendarMonth: nowCalendarMonth,
        calendarView: nowCalendarView,
        currentWorkSession: context.currentWorkSession?.() || null,
        horizon: startHorizon,
        mutationEnabled: Boolean(context.attentionMutationAvailable?.()),
        researchPortfolio: model,
        sessionRegistry: context.sessionRegistry?.() || [],
        mutationReceipt: publicPreviewReceipt || context.lastMutationReceipt?.("now") || null,
      },
      {
        escapeHtml: context.escapeHtml,
        previewButton: context.previewButton,
        translate: (key) => textFrom(context, key),
      }
    );
    if (!model.publicDemo || !html) return html;
    const escapeHtml = context.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    return `<details class="research-portfolio-public-example">
      <summary><strong>${escapeHtml(textFrom(context, "researchPortfolioPublicExampleTitle"))}</strong><span>${escapeHtml(textFrom(context, "researchPortfolioPublicExampleHint"))}</span></summary>
      <section class="research-portfolio-onboarding" aria-label="${escapeHtml(textFrom(context, "researchPortfolioOnboardingTitle"))}">
        <header><strong>${escapeHtml(textFrom(context, "researchPortfolioOnboardingTitle"))}</strong><span>${escapeHtml(textFrom(context, "researchPortfolioOnboardingHint"))}</span></header>
        <ol>
          <li><span>1</span><div><strong>${escapeHtml(textFrom(context, "researchPortfolioOnboardingStepOne"))}</strong><small>${escapeHtml(textFrom(context, "researchPortfolioOnboardingStepOneHint"))}</small></div></li>
          <li><span>2</span><div><strong>${escapeHtml(textFrom(context, "researchPortfolioOnboardingStepTwo"))}</strong><small>${escapeHtml(textFrom(context, "researchPortfolioOnboardingStepTwoHint"))}</small></div></li>
          <li><span>3</span><div><strong>${escapeHtml(textFrom(context, "researchPortfolioOnboardingStepThree"))}</strong><small>${escapeHtml(textFrom(context, "researchPortfolioOnboardingStepThreeHint"))}</small></div></li>
        </ol>
      </section>
      ${html}
    </details>`;
  }

  function bindWorkbench({ context = {}, model: slotModel = {}, root = null } = {}) {
    if (!root || !PortfolioWorkbench) return;
    const model = modelWithCalendarPreview(modelFrom(slotModel, context));
    const preparePortfolioPrompt = PortfolioWorkbench.createActions({
      defaultSourceHint: () => model.path || (context.publicStarter?.()
        ? "08_exports/public_starter/demo-research-agenda.md"
        : "06_active_context/research-portfolio.md"),
      draftWorkSession: context.draftWorkSession || (() => ({ ok: false })),
      text: (key) => textFrom(context, key),
      titleSeparator: () => context.publicStarter?.() ? ": " : "：",
    }).preparePrompt;
    const itemById = (itemId = "") => model.items.find((item) => item.id === itemId) || null;
    const status = (message = "", button = null) => {
      const node = button?.closest?.("[data-attention-card], [data-lifecycle-card], [data-portfolio-detail]")?.querySelector?.("[data-portfolio-action-status]")
        || root.querySelector?.("[data-portfolio-detail]:not([hidden]) [data-portfolio-action-status]")
        || root.querySelector?.("[data-portfolio-action-status]");
      if (node) node.textContent = message;
    };
    const prepare = async (item = {}, mode = "background", button = null, targetLevel = "", prepareOptions = {}) => {
      const normalizedTarget = ["I0", "I1", "I2", "I3"].includes(String(targetLevel || "").toUpperCase())
        ? String(targetLevel).toUpperCase()
        : "";
      const baseRequest = mode === "create"
        ? textFrom(context, "researchPortfolioCreatePrompt")
        : mode === "adjust" ? item.adjustPrompt : item.actionPrompt;
      const targetPrompt = normalizedTarget
        ? String(textFrom(context, "researchMaturityCandidatePrompt")).replace("{level}", normalizedTarget)
        : "";
      const request = [baseRequest, targetPrompt].filter(Boolean).join("\n\n");
      if (!request) return;
      const currentSession = context.currentWorkSession?.() || null;
      const carryCards = currentSession?.status === "draft" && !currentSession?.portfolioBinding?.itemId
        ? currentSession.cards || []
        : [];
      const result = await Promise.resolve(preparePortfolioPrompt(request, { ...item, selectedMaturityTarget: normalizedTarget, workSessionCards: carryCards }, mode, prepareOptions));
      if (result?.cancelled) status(textFrom(context, "researchPortfolioActionCancelled"), button);
      else if (result?.busy) status(textFrom(context, "workSessionWaitForResult"), button);
      return result;
    };
    const mutateAttention = async (item = {}, action = {}) => {
      if (!item.id || typeof context.dispatchPluginAction !== "function") return { ok: false };
      const actionId = action.action === "complete_step" ? "complete_portfolio_step" : "update_portfolio_attention";
      const result = await context.dispatchPluginAction({
        actionId,
        confirmed: true,
        input: { action, item },
        pluginId,
      });
      if (!result?.ok) status(textFrom(context, context.publicStarter?.() ? "researchAttentionDemoOnly" : "researchAttentionActionFailed"));
      return result;
    };
    PortfolioWorkbench.bind(root, {
      onAdjust: ({ itemId }) => prepare(itemById(itemId) || {}, "adjust"),
      onMaturitySelect: ({ itemId, targetLevel, button }) => prepare(itemById(itemId) || {}, "adjust", button, targetLevel),
      onAttentionAction: ({ action, button, itemId, offset }) => {
        const item = itemById(itemId);
        if (!item) return;
        if (action === "schedule") {
          const attentionDate = PortfolioView.isoOffset(offset);
          const inLibrary = Boolean(button?.closest?.("[data-research-portfolio-library]"));
          const inStart = Boolean(button?.closest?.("[data-research-portfolio]"));
          const messageKey = offset === 0 ? "researchAttentionMovedToday" : "researchAttentionScheduledDate";
          const receiptMessage = String(textFrom(context, messageKey))
            .replace("{title}", item.title || "")
            .replace("{date}", attentionDate);
          mutateAttention(item, { action, attentionDate, receiptMessage, viewToday: offset === 0 && (inLibrary || (inStart && startHorizon !== "today")) });
        } else {
          mutateAttention(item, { action });
        }
      },
      onAttentionCustom: ({ action, date, itemId }) => {
        const item = itemById(itemId);
        if (!item || !date) return;
        mutateAttention(item, action === "schedule"
          ? { action, attentionDate: date }
          : { action, reviewDate: date });
      },
      onCompleteProject: async ({ itemId }) => {
        const item = itemById(itemId);
        if (!item || typeof context.dispatchPluginAction !== "function") return;
        const result = await context.dispatchPluginAction({
          actionId: "complete_portfolio_project",
          input: {
            confirmationMessage: textFrom(context, "researchAttentionCompleteProjectBody"),
            item,
          },
          pluginId,
        });
        if (!result?.ok) status(textFrom(context, context.publicStarter?.() ? "researchAttentionDemoOnly" : "researchAttentionActionFailed"));
      },
      onCalendarCurrent: () => {
        nowCalendarMonth = PortfolioView.currentMonthKey();
        rerenderStart(context, true);
      },
      onCalendarView: ({ view }) => {
        nowCalendarView = view === "week" ? "week" : "month";
        rerenderStart(context, true);
      },
      onCalendarMove: ({ itemId, targetDate }) => {
        const item = itemById(itemId);
        if (!item || !PortfolioView.validIsoDate(targetDate) || item.attentionDate === targetDate) return;
        nowCalendarMonth = targetDate.slice(0, 7);
        if (model.publicDemo) {
          publicCalendarPreviewDates[itemId] = targetDate;
          publicPreviewReceipt = {
            itemId,
            message: String(textFrom(context, "researchCalendarPreviewMoved")).replace("{date}", targetDate),
            undo: { token: "calendar-preview" },
          };
          rerenderStart(context, true);
          return;
        }
        mutateAttention(item, {
          action: "schedule",
          attentionDate: targetDate,
          receiptMessage: String(textFrom(context, "researchCalendarMoveSaved")).replace("{date}", targetDate),
        });
      },
      onCalendarOpenCard: ({ itemId }) => {
        rerenderStart(context, true);
        global.setTimeout?.(() => { const target = Array.from(global.document?.querySelectorAll?.("[data-now-active-projects] [data-lifecycle-card]") || []).find((node) => node.dataset.lifecycleCard === itemId); target?.focus?.({ preventScroll: true }); scrollIntoView(target, { behavior: "smooth", block: "center" }); }, 48);
      },
      onCalendarShift: ({ offset }) => {
        nowCalendarMonth = PortfolioView.shiftMonthKey(nowCalendarMonth, offset);
        rerenderStart(context, true);
      },
      onCreate: () => prepare({ sourcePath: model.path || "" }, "create"),
      onOpenLibrary: ({ itemId = "" } = {}) => {
        if (itemId) {
          context.selectLibraryLens?.(itemId);
          context.openWorkspace?.("library", { scroll: true });
          return;
        }
        context.openWorkspace?.("library", { scroll: true });
      },
      onOpenExecution: ({ itemId = "", panel = "work" } = {}) => context.openItemExecutionDrawer?.(itemId, panel, { focus: true }),
      onOpenToday: async ({ button, itemId } = {}) => {
        const item = itemById(itemId);
        if (!item) return;
        const actionState = button?.closest?.("[data-start-action-state]")?.dataset?.startActionState || "";
        if (actionState === "switch_research") {
          const panel = button?.closest?.(".research-attention-card")?.querySelector?.("[data-research-switch-confirm]");
          if (panel) {
            panel.hidden = false;
            button.setAttribute("aria-expanded", "true");
            panel.querySelector?.("[data-portfolio-switch-confirm]")?.focus?.({ preventScroll: true });
          }
          return;
        }
        const current = context.currentWorkSession?.() || null;
        const currentState = global.ResearchOSWorkSessionState?.lifecycleProjection?.(current)?.state || "no_task";
        if (current?.portfolioBinding?.itemId !== item.id || currentState === "ended") {
          const result = await prepare(item, "now");
          if (!result?.ok) return;
        }
        context.openItemExecutionDrawer?.(item.id, "work", { focus: true });
      },
      onReorderToday: async ({ direction = "", itemId = "", targetItemId = "" } = {}) => {
        const todayItems = PortfolioView.startHorizonGroups(model.items).today.filter((item) => ["today", "carryover"].includes(item.attentionState));
        const fromIndex = todayItems.findIndex((item) => item.id === itemId);
        if (fromIndex < 0) return;
        const toIndex = targetItemId ? todayItems.findIndex((item) => item.id === targetItemId) : fromIndex + (direction === "up" ? -1 : 1);
        if (toIndex < 0 || toIndex >= todayItems.length || toIndex === fromIndex) return;
        const reordered = [...todayItems]; const [moved] = reordered.splice(fromIndex, 1); reordered.splice(toIndex, 0, moved);
        reordered.forEach((item, index) => { publicTodayPreviewOrders[item.id] = index + 1; });
        publicPreviewReceipt = { itemId: moved.id, message: textFrom(context, "researchAttentionOrderPreview"), undo: { token: "today-order-preview" } };
        rerenderStart(context, true);
      },
      onSwitchCancel: ({ button } = {}) => {
        const card = button?.closest?.(".research-attention-card");
        const panel = card?.querySelector?.("[data-research-switch-confirm]");
        if (panel) panel.hidden = true;
        const trigger = card?.querySelector?.("[data-portfolio-open-today]");
        trigger?.setAttribute?.("aria-expanded", "false");
        trigger?.focus?.({ preventScroll: true });
      },
      onSwitchConfirm: async ({ button, itemId } = {}) => {
        const item = itemById(itemId);
        if (!item) return;
        const result = await prepare(item, "now", button, "", { replaceConfirmed: true });
        if (!result?.ok) return;
        context.openItemExecutionDrawer?.(item.id, "work", { focus: true });
      },
      onReceiptToday: ({ button } = {}) => {
        if (button?.closest?.("[data-research-portfolio]")) {
          startHorizon = "today";
          rerenderStart(context, Boolean(model.publicDemo));
          return;
        }
        startHorizon = "today";
        context.openWorkspace?.("now", { scroll: true });
        rerenderStart(context, Boolean(model.publicDemo));
      },
      onStartHorizon: ({ button, horizon }) => {
        startHorizon = ["today", "tomorrow", "future", "frozen"].includes(horizon) ? horizon : "today";
        rerenderStart(context, Boolean(button?.closest?.("details.research-portfolio-public-example")));
      },
      onSelect: ({ itemId }) => PortfolioWorkbench.selectItem(root, itemId),
      onUndo: async () => {
        if (model.publicDemo && publicPreviewReceipt) {
          delete publicCalendarPreviewDates[publicPreviewReceipt.itemId];
          Object.keys(publicTodayPreviewOrders).forEach((key) => delete publicTodayPreviewOrders[key]);
          publicPreviewReceipt = null;
          rerenderStart(context, true);
          return;
        }
        if (typeof context.undoLastMutation !== "function") return;
        const result = await context.undoLastMutation();
        if (!result?.ok) status(textFrom(context, "researchAttentionUndoFailed"));
      },
    });
    context.bindPreviewButtons?.(root);
  }

  if (PluginRuntime) {
    PluginRuntime.registerWorkItemAdapter(pluginId, "research_portfolio_work_items", {
      actions: {
        completeProjectActionId: "complete_portfolio_project",
        completeStepActionId: "complete_portfolio_step",
      },
      project: ({ payload }) => ({
        items: (Array.isArray(payload?.items) ? payload.items : []).map((item) => ({
          ...item,
          plugin_id: pluginId,
          provider_id: String(item?.provider_id || item?.providerId || pluginId),
        })),
        schema_id: "researchos-work-item-projection-v1",
        version: "1",
      }),
    });
    const attentionHandler = (actionId) => ({
      execute: async ({ context, input }) => {
        const binding = input?.binding || {};
        const item = input?.item || {
          id: binding.itemId,
          nextStep: binding.nextStep,
          nextStepHash: binding.nextStepHash,
          providerId: binding.providerId,
        };
        const action = input?.action || { action: actionId === "complete_portfolio_step" ? "complete_step" : "" };
        const result = await WorkSessionClient?.applyAttentionAction?.(item, action);
        if (!result?.ok) return result || { ok: false, message: "attention_action_failed" };
        return {
          ...result,
          projection_refresh_required: true,
          presentation_receipt: {
            itemId: item.id || "",
            message: action.receiptMessage || PortfolioCopy?.text(context?.language, action.action === "complete_step" ? "researchAttentionNeedsNextStepBody" : "researchAttentionActionSaved") || "",
            viewToday: Boolean(action.viewToday),
          },
        };
      },
      handlerId: "attention_action",
      spec: {
        actor: "human",
        confirmation: "inline",
        effect: "mutate_attention",
        fallback: "show_attention_action_failure",
        id: `${pluginId}.${actionId}`,
        location: "current_surface",
        reversible: true,
        risk: "low",
        target: "portfolio_attention_state",
        verb: actionId === "complete_portfolio_step" ? "complete_step" : "update_attention",
      },
    });
    PluginRuntime.registerActionHandler(pluginId, "update_portfolio_attention", attentionHandler("update_portfolio_attention"));
    PluginRuntime.registerActionHandler(pluginId, "complete_portfolio_step", attentionHandler("complete_portfolio_step"));
    PluginRuntime.registerActionHandler(pluginId, "complete_portfolio_project", {
      execute: async ({ context, input }) => {
        const binding = input?.binding || {};
        const itemId = String(input?.item?.id || binding.itemId || "");
        const result = await WorkSessionClient?.completePortfolioItem?.(
          { itemId },
          { completionNote: PortfolioCopy?.text(context?.language, "researchAttentionCompleteProjectReceipt") || "" },
        );
        if (!result?.ok) return result || { ok: false, message: "project_completion_failed" };
        return {
          ...result,
          projection_refresh_required: true,
          presentation_receipt: {
            itemId,
            message: PortfolioCopy?.text(context?.language, "researchAttentionProjectCompleted") || "",
            workspace: "now",
          },
        };
      },
      handlerId: "complete_portfolio_project",
      spec: {
        actor: "human",
        confirmation: "preview_confirm",
        effect: "mutate_canonical",
        fallback: "keep_project_open_and_show_failure",
        id: `${pluginId}.complete_portfolio_project`,
        location: "current_surface",
        reversible: true,
        risk: "high",
        target: "portfolio_project_lifecycle",
        verb: "complete_project",
      },
    });
    PluginRuntime.registerOwnedAdapter(pluginId, "research_portfolio_workbench", {
      bind: bindWorkbench,
      render: renderWorkbench,
    });
  }

  global.ResearchOSResearchPortfolioPlugin = Object.freeze({
    bindWorkbench,
    modelFrom,
    publicDemoHidden,
    renderWorkbench,
  });
})(window);
