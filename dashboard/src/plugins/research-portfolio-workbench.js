/* ResearchOS maintenance header.
 * 中文：Research portfolio 插件交互层；独占筛选、选择及 Work Session 路由。
 * English: Research-portfolio plugin interaction layer; owns filtering, selection, and Work Session routing.
 */

(function attachResearchOSResearchPortfolioWorkbench(global) {
  const { bindAll } = global.ResearchOSInteractions;
  let activeFilter = "lead_active";
  let selectedItemId = "";

  function selectItem(root, itemId = "") {
    if (!root) return "";
    const rows = Array.from(root.querySelectorAll("[data-portfolio-select]"));
    const visibleRows = rows.filter((row) => !row.hidden);
    const nextId = rows.some((row) => row.dataset.portfolioSelect === itemId && !row.hidden)
      ? itemId
      : (visibleRows[0]?.dataset?.portfolioSelect || "");
    if (!nextId) return "";
    selectedItemId = nextId;
    rows.forEach((row) => {
      const selected = row.dataset.portfolioSelect === nextId;
      row.classList.toggle("selected", selected);
      row.setAttribute("aria-pressed", selected ? "true" : "false");
    });
    Array.from(root.querySelectorAll("[data-portfolio-detail]")).forEach((detail) => {
      detail.hidden = detail.dataset.portfolioDetail !== nextId;
    });
    return nextId;
  }

  function applyFilter(root, filter = "lead_active") {
    if (!root) return 0;
    const requestedFilter = String(filter || "lead_active").trim() || "lead_active";
    const nextFilter = { lead_mainline: "lead_active", support: "support_all" }[requestedFilter] || requestedFilter;
    activeFilter = nextFilter;
    const cards = Array.from(root.querySelectorAll("[data-portfolio-card]"));
    let visibleCount = 0;
    cards.forEach((card) => {
      const responsibility = card.dataset.portfolioResponsibility || "unclassified";
      const state = card.dataset.portfolioState || "conditional";
      const freshness = card.dataset.portfolioFreshness || "unverified";
      const visible = {
        lead_active: responsibility === "lead" && state === "mainline",
        lead_all: responsibility === "lead" && state !== "closed",
        support_active: responsibility === "support" && state === "mainline",
        support_all: responsibility === "support" && state !== "closed",
        waiting: state === "waiting",
        queued: state === "queued",
        conditional: state === "conditional",
        paused: state === "paused",
        unclassified: responsibility === "unclassified",
        review: ["review_due", "stale", "unverified"].includes(freshness) && state !== "closed",
        all: true,
      }[nextFilter] ?? card.dataset.portfolioSchedule === nextFilter;
      card.hidden = !visible;
      if (visible) visibleCount += 1;
    });
    Array.from(root.querySelectorAll("[data-portfolio-filter]")).forEach((button) => {
      const selected = button.dataset.portfolioFilter === nextFilter;
      button.classList.toggle("selected", selected);
      button.setAttribute("aria-pressed", selected ? "true" : "false");
    });
    const status = root.querySelector("[data-portfolio-filter-status]");
    if (status) status.textContent = `${visibleCount}/${cards.length}`;
    selectItem(root, selectedItemId);
    return visibleCount;
  }

  function createActions({
    defaultSourceHint = "",
    draftWorkSession = () => ({ ok: false }),
    text = (key) => key,
    titleSeparator = ": ",
  } = {}) {
    const optionValue = (value, fallback = "") => {
      const resolved = typeof value === "function" ? value() : value;
      return resolved == null || resolved === "" ? fallback : resolved;
    };
    return {
      preparePrompt: (request, item = {}, mode = "start", options = {}) => {
        const portfolioPath = optionValue(defaultSourceHint);
        const maturity = item.cardMaturity || null;
        const selectedTarget = ["I0", "I1", "I2", "I3"].includes(String(item.selectedMaturityTarget || "").toUpperCase())
          ? String(item.selectedMaturityTarget).toUpperCase()
          : "";
        const enhancement = mode === "adjust" && maturity ? {
          action: maturity.action || "verify",
          axis: maturity.axis || "I",
          confirmed: Boolean(maturity.confirmed),
          current_level: maturity.level || "I?",
          source: maturity.source || "missing",
          target_level: selectedTarget || maturity.target_level || "I0",
        } : null;
        const candidate = enhancement ? {
          candidate_id: `candidate:card-enhancement:${item.id || item.sourcePath || item.title || "project"}`,
          plugin_id: "research_portfolio",
          candidate_type: "card_enhancement",
          source_refs: item.sourcePath ? [{ kind: "object", path: item.sourcePath }] : [],
          summary: `${item.title || "project"} · ${enhancement.current_level} -> ${enhancement.target_level}`,
          proposed_action: { id: "enhance_card_maturity", target_agent: "project_steward" },
          proposed_writeback: {
            save_target: item.publicDemo ? "" : (item.sourcePath || portfolioPath),
            object_type: "project",
            object_id: item.id || item.title || "project",
            object_path: item.sourcePath || "",
            current_state: enhancement.current_level,
            proposed_state: item.publicDemo ? "copy_only_review" : enhancement.target_level,
            decision_rationale: maturity.reason || "",
            impact_scope: item.sourcePath || portfolioPath,
            rollback_ref: "",
            validation_state: "not_run",
          },
          sensitivity: item.publicDemo ? "public_safe" : "internal",
          required_confirmation: item.publicDemo ? "handoff_only" : "candidate_diff",
          validation: { workflow_status: "active", evidence_state: "candidate", authority_state: "proposed", state: "not_run" },
        } : null;
        return draftWorkSession({
          cards: Array.isArray(item.workSessionCards) ? item.workSessionCards : [],
          candidate,
          enhancement,
          intent: request,
          portfolioBinding: mode === "create" || !item.id ? null : {
            completeProjectActionId: "complete_portfolio_project",
            completeStepActionId: "complete_portfolio_step",
            currentStage: item.currentStage || "",
            currentStageCanonical: item.currentStageCanonical || item.currentStage || "",
            itemId: item.id,
            nextStep: item.nextStep || "",
            nextStepCanonical: item.nextStepCanonical || item.nextStep || "",
            nextStepHash: item.nextStepHash || "",
            portfolioPath,
            pluginId: "research_portfolio",
            providerId: item.providerId || "research_portfolio",
            sourcePath: item.sourcePath || "",
            title: item.title || "",
          },
          responseMode: "answer",
          replaceConfirmed: options.replaceConfirmed === true,
          sourceHint: item.sourcePath || portfolioPath,
          title: mode === "create"
            ? text("researchPortfolioCreateTaskTitle")
            : `${text(mode === "adjust" ? "researchPortfolioAdjustTaskTitle" : "researchPortfolioStartTaskTitle")}${optionValue(titleSeparator, ": ")}${item.title || ""}`,
        });
      },
    };
  }

  function bind(root, callbacks = {}) {
    if (!root) return;
    const {
      onAdjust = () => {},
      onAttentionAction = () => {},
      onAttentionCustom = () => {},
      onCompleteProject = () => {},
      onCalendarCurrent = () => {},
      onCalendarView = () => {},
      onCalendarMove = () => {},
      onCalendarOpenCard = () => {},
      onCalendarShift = () => {},
      onCreate = () => {},
      onLibraryZone = () => {},
      onLibraryMode = () => {},
      onMaturitySelect = () => {},
      onOpenLibrary = () => {},
      onOpenToday = () => {},
      onReceiptToday = () => {},
      onReorderToday = () => {},
      onStartHorizon = () => {},
      onSwitchCancel = () => {},
      onSwitchConfirm = () => {},
      onUndo = () => {},
      onSelect = ({ itemId }) => selectItem(root, itemId),
    } = callbacks;
    let calendarPointer = null;
    let suppressCalendarOpenUntil = 0;
    const clearCalendarDrag = () => {
      if (calendarPointer?.button) calendarPointer.button.setAttribute("aria-grabbed", "false");
      calendarPointer = null;
      Array.from(root.querySelectorAll("[data-calendar-drag-item].is-dragging, [data-calendar-date].is-drop-target"))
        .forEach((node) => node.classList.remove("is-dragging", "is-drop-target"));
    };
    const calendarCellAt = (event) => global.document?.elementFromPoint?.(event.clientX, event.clientY)?.closest?.("[data-calendar-date]") || null;
    bindAll(root, "[data-portfolio-filter]", "click", (event, button) => {
      event.preventDefault();
      applyFilter(root, button.dataset.portfolioFilter || "lead_active");
    });
    bindAll(root, "[data-portfolio-select]", "click", (event, button) => {
      onSelect({ event, button, itemId: button.dataset.portfolioSelect || "" });
    });
    bindAll(root, "[data-portfolio-open-today]", "click", (event, button) => {
      onOpenToday({ event, button, itemId: button.dataset.portfolioOpenToday || "" });
    });
    bindAll(root, "[data-portfolio-switch-cancel]", "click", (event, button) => {
      event.preventDefault();
      onSwitchCancel({ event, button, itemId: button.dataset.portfolioSwitchCancel || "" });
    });
    bindAll(root, "[data-portfolio-switch-confirm]", "click", (event, button) => {
      event.preventDefault();
      onSwitchConfirm({ event, button, itemId: button.dataset.portfolioSwitchConfirm || "" });
    });
    bindAll(root, "[data-portfolio-adjust]", "click", (event, button) => {
      onAdjust({ event, button, itemId: button.dataset.portfolioAdjust || "" });
    });
    bindAll(root, "[data-portfolio-maturity-target]", "click", (event, button) => {
      event.preventDefault();
      onMaturitySelect({
        event,
        button,
        itemId: button.dataset.portfolioMaturityItem || "",
        targetLevel: button.dataset.portfolioMaturityTarget || "",
      });
    });
    bindAll(root, "[data-portfolio-create]", "click", (event, button) => onCreate({ event, button }));
    bindAll(root, "[data-portfolio-open-library]", "click", (event, button) => {
      event.preventDefault();
      onOpenLibrary({ event, button, itemId: button.dataset.portfolioOpenLibrary || "" });
    });
    bindAll(root, "[data-portfolio-open-execution]", "click", (event, button) => {
      event.preventDefault();
      callbacks.onOpenExecution?.({ button, event, itemId: button.dataset.portfolioOpenExecution || "", panel: button.dataset.executionPanel || "work" });
    });
    bindAll(root, "[data-portfolio-library-mode]", "click", (event, button) => {
      event.preventDefault();
      onLibraryMode({ event, button, mode: button.dataset.portfolioLibraryMode || "cards" });
    });
    bindAll(root, "[data-portfolio-zone]", "click", (event, button) => {
      event.preventDefault();
      onLibraryZone({ event, button, zone: button.dataset.portfolioZone || "active" });
    });
    bindAll(root, "[data-portfolio-start-horizon]", "click", (event, button) => {
      event.preventDefault();
      onStartHorizon({ event, button, horizon: button.dataset.portfolioStartHorizon || "today" });
    });
    bindAll(root, "[data-calendar-shift]", "click", (event, button) => {
      event.preventDefault();
      onCalendarShift({ event, button, offset: Number(button.dataset.calendarShift || 0) });
    });
    bindAll(root, "[data-calendar-current]", "click", (event, button) => {
      event.preventDefault();
      onCalendarCurrent({ event, button });
    });
    bindAll(root, "[data-calendar-view]", "click", (event, button) => {
      event.preventDefault();
      onCalendarView({ event, button, view: button.dataset.calendarView || "month" });
    });
    bindAll(root, "[data-calendar-drag-item]", "pointerdown", (event, button) => {
      if (event.button !== 0) return;
      const itemId = button.dataset.calendarDragItem || "";
      if (!itemId) return;
      calendarPointer = {
        active: false,
        button,
        itemId,
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
      };
    });
    bindAll(root, "[data-research-calendar]", "pointermove", (event) => {
      if (!calendarPointer || calendarPointer.pointerId !== event.pointerId) return;
      const distance = Math.hypot(event.clientX - calendarPointer.startX, event.clientY - calendarPointer.startY);
      if (!calendarPointer.active && distance < 6) return;
      if (!calendarPointer.active) {
        calendarPointer.active = true;
        calendarPointer.button.classList.add("is-dragging");
        calendarPointer.button.setAttribute("aria-grabbed", "true");
        calendarPointer.button.setPointerCapture?.(event.pointerId);
      }
      event.preventDefault();
      const cell = calendarCellAt(event);
      Array.from(root.querySelectorAll("[data-calendar-date].is-drop-target"))
        .forEach((node) => node.classList.toggle("is-drop-target", node === cell));
      cell?.classList.add("is-drop-target");
    });
    bindAll(root, "[data-research-calendar]", "pointerup", (event) => {
      if (!calendarPointer || calendarPointer.pointerId !== event.pointerId) return;
      const pointer = calendarPointer;
      const cell = pointer.active ? calendarCellAt(event) : null;
      const targetDate = cell?.dataset?.calendarDate || "";
      if (pointer.active) {
        event.preventDefault();
        suppressCalendarOpenUntil = Date.now() + 350;
      }
      clearCalendarDrag();
      if (targetDate) onCalendarMove({ event, button: cell, itemId: pointer.itemId, targetDate });
    });
    bindAll(root, "[data-research-calendar]", "pointercancel", clearCalendarDrag);
    bindAll(root, "[data-calendar-drag-item]", "keydown", (event, button) => {
      if (!event.altKey) return;
      const offset = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[event.key];
      if (!offset) return;
      const currentDate = button.dataset.calendarEventDate || "";
      const targetDate = global.ResearchOSResearchPortfolioView?.shiftIsoDate?.(currentDate, offset) || "";
      if (!targetDate) return;
      event.preventDefault();
      onCalendarMove({ event, button, itemId: button.dataset.calendarDragItem || "", targetDate });
    });
    bindAll(root, "[data-calendar-open-card]", "click", (event, button) => {
      event.preventDefault();
      if (Date.now() < suppressCalendarOpenUntil) return;
      onCalendarOpenCard({ event, button, itemId: button.dataset.calendarOpenCard || "" });
    });
    bindAll(root, "[data-attention-action]", "click", (event, button) => {
      onAttentionAction({
        action: button.dataset.attentionAction || "",
        button,
        event,
        itemId: button.dataset.attentionItem || "",
        offset: Number(button.dataset.attentionOffset || 0),
      });
    });
    bindAll(root, "[data-attention-reorder]", "click", (event, button) => { event.preventDefault(); onReorderToday({ direction: button.dataset.attentionReorder || "", event, itemId: button.dataset.attentionItem || "" }); });
    let draggedTodayItemId = "";
    bindAll(root, "[data-attention-sort-item]", "dragstart", (event, card) => { draggedTodayItemId = card.dataset.attentionSortItem || ""; card.classList.add("is-dragging"); event.dataTransfer?.setData?.("text/plain", draggedTodayItemId); });
    bindAll(root, "[data-attention-sort-item]", "dragover", (event, card) => { if (!draggedTodayItemId || draggedTodayItemId === card.dataset.attentionSortItem) return; event.preventDefault(); card.classList.add("is-drop-target"); });
    bindAll(root, "[data-attention-sort-item]", "dragleave", (_event, card) => card.classList.remove("is-drop-target"));
    bindAll(root, "[data-attention-sort-item]", "drop", (event, card) => { event.preventDefault(); const targetItemId = card.dataset.attentionSortItem || ""; card.classList.remove("is-drop-target"); if (draggedTodayItemId && targetItemId && draggedTodayItemId !== targetItemId) onReorderToday({ event, itemId: draggedTodayItemId, targetItemId }); });
    bindAll(root, "[data-attention-sort-item]", "dragend", (_event, card) => { card.classList.remove("is-dragging"); Array.from(root.querySelectorAll("[data-attention-sort-item].is-drop-target")).forEach((node) => node.classList.remove("is-drop-target")); draggedTodayItemId = ""; });
    bindAll(root, "[data-portfolio-receipt-today]", "click", (event, button) => {
      event.preventDefault();
      onReceiptToday({ event, button });
    });
    bindAll(root, "[data-attention-custom]", "click", (event, button) => {
      const itemId = button.dataset.attentionItem || "";
      const action = button.dataset.attentionCustom || "";
      const inputSelector = action === "schedule" ? "attention-date-input" : "attention-review-input";
      const input = root.querySelector(`[data-${inputSelector}="${itemId}"]`);
      onAttentionCustom({
        action,
        button,
        date: String(input?.value || ""),
        event,
        itemId,
      });
    });
    bindAll(root, "[data-portfolio-complete-project]", "click", (event, button) => {
      onCompleteProject({ event, button, itemId: button.dataset.portfolioCompleteProject || "" });
    });
    bindAll(root, "[data-portfolio-undo]", "click", (event, button) => onUndo({ event, button }));
    if (root.querySelector?.("[data-portfolio-filter]")) applyFilter(root, activeFilter);
  }

  function renderLifecycle(item, root, context) {
    const {state, copy, element, clean, selectedTask, status, refreshLifecycleProjection, invalidateHandoff, renderDesk, renderItemLens} = context;
    const labels = {mainline: ["进行中", "Active"], queued: ["排队", "Queued"], conditional: ["条件触发", "Conditional"], waiting: ["等待", "Waiting"], paused: ["暂停", "Paused"], closed: ["已结束", "Ended"]};
    const box = element("section", "research-provenance");
    box.append(element("h3", "", copy("事项生命周期", "Item lifecycle")));
    const label = element("label", "", copy("登记状态", "Recorded state"));
    const select = element("select");
    select.dataset.lifecycleState = "";
    Object.entries(labels).forEach(([value, names]) => {
      const option = element("option", "", copy(...names));
      option.value = value;
      select.append(option);
    });
    select.value = item.state;
    select.disabled = !state.effectsEnabled || state.mutationPending;
    label.append(select);
    const reopenFields = element("div", "lifecycle-reopen");
    const reopenInputs = {};
    if (item.state === "closed") {
      for (const [field, names] of Object.entries({next_step:["重开后的下一步", "New next step"], success_gate:["重开后的完成标准", "New acceptance criteria"], priority:["重开后的优先级", "New priority"]})) {
        const fieldLabel = element("label", "", copy(...names));
        const input = element(field === "priority" ? "select" : "input");
        if (field === "priority") {
          for (const value of ["", "P0", "P1", "P2", "P3"]) {
            const option = element("option", "", value || copy("请选择", "Choose"));
            option.value = value;
            input.append(option);
          }
        } else { input.type = "text"; input.maxLength = 500; }
        input.disabled = select.disabled;
        input.dataset.reopenField = field;
        fieldLabel.append(input);
        reopenFields.append(fieldLabel);
        reopenInputs[field] = input;
      }
      reopenFields.append(element("p", "drawer-note", copy("重开将用这些信息替换本事项的旧计划、责任动作与完成态优先级；来源文件不改。", "Reopening replaces this item's old plan, responsibility actions and completion priority with these values; the source file is unchanged.")));
    }
    const confirm = element("input");
    confirm.type = "checkbox";
    confirm.disabled = select.disabled;
    const confirmation = element("label", "effect-confirm");
    confirmation.append(confirm, global.document.createTextNode(copy("确认登记本事项生命周期及明确填写的重开计划；不代表申请获批或成功条件达成。", "Confirm this responsibility's lifecycle and any explicitly entered reopening plan; this does not assert approval or achievement.")));
    select.addEventListener("change", () => { confirm.checked = false; });
    Object.values(reopenInputs).forEach(input => input.addEventListener("input", () => { confirm.checked = false; }));
    const save = element("button", "", copy("保存状态", "Save state"));
    save.type = "button";
    save.disabled = select.disabled;
    save.addEventListener("click", async () => {
      if (!state.effectsEnabled || state.mutationPending || selectedTask()?.id !== item.id) return;
      if (!confirm.checked) return status(copy("请先确认状态变更。", "Confirm the state change first."));
      if (select.value === item.state) return status(copy("状态未改变，无需保存。", "The state is unchanged."));
      const reopening = item.state === "closed";
      const reopen = Object.fromEntries(Object.entries(reopenInputs).map(([key, input]) => [key, clean(input.value)]));
      if (reopening && (!reopen.next_step || !reopen.success_gate || !reopen.priority)) return status(copy("重开前请填写新的下一步、完成标准和优先级。", "Enter a new next step, acceptance criteria and priority before reopening."));
      state.mutationPending = true;
      save.disabled = true;
      const previous = {...item};
      try {
        const result = await global.ResearchOSWorkSessionClient.setPortfolioState(item, select.value, {reopen});
        if (!result?.ok) throw new Error(result?.message || copy("保存被拒绝，请刷新核对", "Save rejected; refresh to verify"));
        item.state = result.result.state;
        item.lifecycleState = item.state === "closed" ? "completed" : ["waiting", "paused"].includes(item.state) ? item.state : "open";
        item.primaryRegion = {closed: "Archive", waiting: "Waiting", paused: "Paused", mainline: "Review", queued: "Review", conditional: "Review"}[item.state];
        item.lifecycleNote = result.result.fields?.lifecycle_note || item.lifecycleNote;
        if (reopening) Object.assign(item, {nextStep:reopen.next_step, nextStepCanonical:reopen.next_step, successGate:reopen.success_gate, priority:reopen.priority, currentStage:result.result.fields?.current_stage || ""});
        state.lastUndo = result.undo ? {...result.undo, itemId: item.id, previous} : null;
        if (result.rebuilt) await refreshLifecycleProjection();
        invalidateHandoff();
        renderDesk();
        status(result.rebuilt ? copy("生命周期已登记；仅重开时替换明确确认的新计划，来源文件未改变。", "Lifecycle recorded; only reopening replaces the explicitly confirmed plan. Source files are unchanged.") : copy("状态已保存，但视图重建失败；请保留此页的撤销入口并检查服务。", "State saved, but view rebuild failed. Keep this page for undo and check the service."));
      } catch (error) { status(error.message); }
      finally {
        state.mutationPending = false;
        if (selectedTask()?.id === item.id && state.drawerLens === "item") renderItemLens();
      }
    });
    // A read-only preview shows the recorded state only; a confirm box and Save button that can never act just confuse.
    box.append(label, ...(state.effectsEnabled ? [reopenFields, confirmation, save] : []), element("p", "drawer-note", state.effectsEnabled
      ? copy("选择不自动保存。结束仅关闭这项责任；在归档或全部中可找到并重开。保存后 120 秒内可用下方“撤销上次写入”；刷新页面后不保留撤销入口。", "Selection does not save. Ending closes only this responsibility; find it in Archive or All to reopen. Undo last write is available below for 120 seconds and is not retained after a page refresh.")
      : copy("当前为只读预览，不能保存生命周期。", "This preview is read-only; lifecycle changes cannot be saved.")));
    root.append(box);
  }

  function renderItemSource(item, what, {data, copy, element}) {
    if (item.sourcePath) {
      const source = element("details", "research-provenance");
      source.append(element("summary", "", copy("打开来源 Markdown", "Open source Markdown")));
      const content = element("div", "markdown-body card-content-body");
      source.append(content);
      let loaded = false;
      source.addEventListener("toggle", async () => {
        if (!source.open || loaded) return;
        loaded = true;
        if (!(Array.isArray(data?.preview_documents) ? data.preview_documents : []).some((doc) => doc.path === item.sourcePath)) {
          content.textContent = copy("来源已登记，但不在当前文本预览清单中；没有读取全文。", "The source is registered but not allowed by this preview manifest; its text was not read.");
          return;
        }
        content.textContent = copy("正在读取…", "Loading…");
        try {
          const markdown = await global.ResearchOSPreviewContentClient.loadPreviewContent(item.sourcePath);
          content.innerHTML = global.ResearchOSPreviewMarkdownService.markdownToHtml(markdown, item.sourcePath);
        } catch {
          loaded = false;
          content.textContent = copy("读取失败；请检查本地服务，收起后可再次展开重试。", "Could not load the source. Check the local service, then collapse and reopen to retry.");
        }
      });
      what.append(source);
    }
  }
  async function refreshLifecycleProjection(dataPath, state, projectionPayload) {
    if (typeof global.fetch !== "function") return false;
    try {
      const response = await global.fetch(dataPath, {cache: "no-store"});
      if (!response.ok) return false;
      const data = await response.json();
      Object.assign(state, projectionPayload(data), {data});
      return true;
    } catch { return false; }
  }

  function cardLevelName(level = "", copy) {
    const labels = {M1:["已登记","Registered"],M2:["精读可用","Close-read usable"],M3:["跨项目深化","Cross-project deepening"],I0:["待判断","Assessment"],I1:["项目沙盒","Sandbox"],I2:["正在孵化","Incubating"],I3:["独立项目","Independent project"],R0:["待核对","Candidate"],R1:["已登记","Registered"],R2:["协作资料可用","Working context"],R3:["跨项目上下文","Cross-project context"],G0:["单卡","Single card"],G1:["基础组合","Basic group"],G2:["方向组合","Research direction"],R_research_mainline:["研究主线","Research mainline"]};
    const label = labels[level];
    return label ? `${level === "R_research_mainline" ? "" : level + " · "}${copy(...label)}` : copy("尚未评定等级", "Level not assessed");
  }

  global.ResearchOSResearchPortfolioWorkbench = Object.freeze({
    cardLevelName,
    refreshLifecycleProjection,
    renderLifecycle,
    renderItemSource,
    applyFilter,
    bind,
    createActions,
    selectItem,
  });
})(window);
