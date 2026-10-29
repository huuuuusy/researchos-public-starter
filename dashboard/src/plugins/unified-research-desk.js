/* ResearchOS maintenance header.
 * 中文：Unified Desk v2.5 双运行时投影；共享产品组成与交接语义，同时由 runtime scope 冻结 effect 与公开边界。
 * English: Unified Desk v2.5 dual-runtime projection sharing composition and handoff semantics while runtime scope freezes effects and public boundaries.
 */

(function attachResearchOSUnifiedResearchDesk(global) {
  "use strict";

  const DATA_PATH = "data/researchos-dashboard.json";
  const UI_COPY = Object.freeze({
    assetsBoxGroup: "关系组合",
    assetsBoxPaper: "论文与阅读资产",
    assetsBoxPeople: "人物资产",
    assetsBoxProject: "项目资产",
    assetsBoxTalk: "报告与表达资产",
  });
  function runtimeProfile() {
    const root = global.document?.querySelector("[data-unified-desk]");
    const runtimeScope = String(root?.dataset.runtimeScope || "public_starter").trim();
    const publicStarter = runtimeScope === "public_starter";
    return Object.freeze({
      authority: String(root?.dataset.authorityOwner || (publicStarter
        ? "User confirmation + public-safe local Markdown owners"
        : "Human confirmation + canonical Markdown/Git owners")).trim(),
      get language() { return global.document?.documentElement?.lang === "en" ? "en" : "zh-CN"; },
      publicStarter,
      runtimeScope,
      selfPersonAliases: String(root?.dataset.selfPersonAliases || "").split("|").map((value) => value.trim()).filter(Boolean),
    });
  }
  const profile = runtimeProfile();
  // The Research Portfolio workbench takes copy(chinese, english); the desk's own wording lives in research-portfolio-copy.js.
  function copy(chinese, english, language = profile.language) {
    return language === "en" ? english : chinese;
  }
  function deskText(key, params = {}, language = profile.language) {
    return global.ResearchOSResearchPortfolioCopy.format(language, key, params);
  }

  function contentLanguage(data = state.data) {
    const config = data?.config || {};
    const language = config.content_language || config.language_freeze?.active_language
      || data?.language_freeze?.active_language || config.language;
    return ["en", "zh-CN"].includes(language) ? language : (profile.publicStarter ? "en" : "zh-CN");
  }

  const state = {
    anchorDate: "",
    assetCards: [],
    assetModel: null,
    calendarView: "week",
    compositionModel: null,
    data: null,
    drawerLens: "item",
    effectsEnabled: !profile.publicStarter && new URLSearchParams(global.location?.search || "").get("effects") !== "readonly",
    expandedCompositionItems: new Set(),
    focusedAssetId: "",
    handoffAssetsByTask: Object.create(null),
    lastHandoff: null,
    lastUndo: null,
    mandatoryCommitmentIds: new Set(),
    mutationPending: false,
    handoffRevision: 0,
    portfolioModel: null,
    previewAttentionDates: Object.create(null),
    proposedAssetsByTask: Object.create(null),
    selectedTaskId: "",
    placementFilter: "Current",
    taskFilter: "all",
    taskQuery: "",
    resourceFilter: "all",
    resourceQuery: "",
    explorationIntent: "",
    explorationAssets: new Set(),
    previewRevision: 0,
    today: "",
  };

  const byId = (id) => global.document?.getElementById(id);
  const clean = (value = "") => String(value ?? "").trim();
  const safeArray = (value) => Array.isArray(value) ? value : [];
  const text = (node, value = "") => { if (node) node.textContent = String(value ?? ""); return node; };

  function uiText(key = "") {
    return global.ResearchOSResearchPortfolioCopy?.text?.(profile.language, key)
      || global.ResearchOSUICopy?.simpleText?.[profile.language]?.[key]
      || global.ResearchOSUICopy?.simpleText?.["zh-CN"]?.[key]
      || UI_COPY[key]
      || key;
  }

  function shortText(value = "", maximum = 80) {
    const content = clean(value);
    return content.length > maximum ? `${content.slice(0, Math.max(1, maximum - 1))}…` : content;
  }

  function element(tag, className = "", content = "") {
    const node = global.document.createElement(tag);
    if (className) node.className = className;
    if (content) node.textContent = content;
    return node;
  }

  function invalidateHandoff() {
    state.previewRevision += 1;
    state.handoffRevision += 1;
    state.lastHandoff = null;
    byId("handoff-dialog")?.close?.();
  }

  function status(message = "", mode = "event") {
    state.statusMode = mode;
    text(byId("prototype-status"), message);
  }

  const calendar = global.ResearchOSUnifiedDeskCalendar;
  const { isoDate, parseIso } = calendar;
  const visibleDates = () => calendar.visibleDates(state.calendarView, state.anchorDate);
  const periodLabel = (dates = visibleDates()) => calendar.periodLabel(state.calendarView, state.anchorDate, dates,
    (year, month) => deskText("deskCalendarMonthLabel", { year, month: profile.language === "en" ? month : Number(month) }));

  function selectedTask() {
    return state.portfolioModel?.items?.find((item) => item.id === state.selectedTaskId) || null;
  }

  function taskScopedSet(store = {}, taskId = state.selectedTaskId) {
    if (!taskId) return new Set();
    if (!(store[taskId] instanceof Set)) store[taskId] = new Set();
    return store[taskId];
  }

  function handoffAssetIds(taskId = state.selectedTaskId) {
    return taskId ? taskScopedSet(state.handoffAssetsByTask, taskId) : state.explorationAssets;
  }

  function proposedAssetIds(taskId = state.selectedTaskId) {
    return taskScopedSet(state.proposedAssetsByTask, taskId);
  }

  function selectedAssets() {
    const ids = handoffAssetIds();
    return [...ids].map((id) => state.compositionModel?.componentForId(id)).filter(Boolean);
  }

  function selectedComposition() {
    return state.compositionModel?.compositionForItem(state.selectedTaskId) || null;
  }

  function projectionPayload(data = {}) {
    const portfolio = data?.home_command_center?.research_portfolio || {};
    const basePortfolioModel = global.ResearchOSResearchPortfolioModel.build(portfolio, (key) => key, contentLanguage(data));
    const placements = new Map(safeArray(data?.asset_graph?.card_view_consolidation?.placement?.commitments)
      .map((entry) => [String(entry?.id || ""), entry]));
    const portfolioModel = {
      ...basePortfolioModel,
      items: basePortfolioModel.items.map((item) => {
        const placement = placements.get(String(item.id || ""));
        return placement ? {
          ...item,
          mandatoryVisibility: placement.mandatory_visibility === true,
          placementBasis: safeArray(placement.placement_basis),
          primaryRegion: placement.primary_region || "Review",
        } : item;
      }),
    };
    const assetModel = global.ResearchOSAssetOverviewModel.buildAssetOverviewModel({
      currentDate: clean(data.generated_at).slice(0, 10),
      graph: data.asset_graph || {},
      groups: [],
      inboxTotal: 0,
      overview: data.source_overview || {},
      previewDocuments: data.preview_documents || [],
      recentRuns: [],
      translate: uiText,
    });
    const assetCards = safeArray(assetModel.cardBoxes).flatMap((box) => safeArray(box.cards).map((card) => ({ ...card, boxLabel: box.label })));
    const compositionModel = global.ResearchOSItemCompositionModel.build({
      assetBoxes: assetModel.cardBoxes,
      graph: data.asset_graph || {},
      portfolioItems: portfolioModel.items,
      selfPersonAliases: profile.selfPersonAliases,
    });
    return { assetCards, assetModel, compositionModel, portfolioModel };
  }

  function activeItems() {
    return safeArray(state.portfolioModel?.items).filter((item) => item.lifecycleState !== "completed" && item.state !== "closed");
  }

  const placementRegionOrder = Object.freeze(["Current", "Review", "Waiting", "Incubating", "Paused", "Archive"]);

  function allPortfolioItems() {
    return safeArray(state.portfolioModel?.items);
  }

  function hasPlacementProjection() {
    return safeArray(state.data?.asset_graph?.card_view_consolidation?.placement?.commitments).length > 0;
  }

  function placementRegion(item = {}) {
    if (placementRegionOrder.includes(item.primaryRegion)) return item.primaryRegion;
    return item.lifecycleState === "completed" || item.state === "closed" ? "Archive" : "Review";
  }

  function placementLabel(region = "Current") {
    return uiText({
      Current: "researchPlacementCurrent",
      Review: "researchPlacementReview",
      Waiting: "researchPlacementWaiting",
      Incubating: "researchPlacementIncubating",
      Paused: "researchPlacementPaused",
      Archive: "researchPlacementArchive",
    }[region] || "researchPlacementCurrent");
  }

  function placementItems() {
    // Older or deliberately reduced public projections do not carry the
    // single-region placement contract.  In that case there is no meaningful
    // Current/Review split to apply, so fail open for visibility rather than
    // hiding every item behind the default Current filter.
    if (!hasPlacementProjection()) return allPortfolioItems();
    return state.placementFilter === "all"
      ? allPortfolioItems()
      : allPortfolioItems().filter((item) => placementRegion(item) === state.placementFilter);
  }

  function renderPlacementControls() {
    const root = byId("desk-placement-controls");
    if (!root) return;
    const counts = Object.fromEntries(placementRegionOrder.map((region) => [region, 0]));
    allPortfolioItems().forEach((item) => { counts[placementRegion(item)] += 1; });
    const heading = element("header");
    heading.append(element("strong", "", uiText("researchPlacementTitle")), element("small", "", deskText("deskOneRegionPerItem")));
    const controls = element("div", "desk-segment");
    controls.setAttribute("role", "group");
    controls.setAttribute("aria-label", uiText("researchPlacementTitle"));
    placementRegionOrder.forEach((region) => {
      if (!counts[region]) return;
      const button = element("button", "");
      button.type = "button";
      button.dataset.placementFilter = region;
      button.dataset.actionKind = "direct";
      button.setAttribute("aria-pressed", String(state.placementFilter === region));
      button.append(element("span", "", placementLabel(region)), element("b", "", counts[region]));
      controls.append(button);
    });
    const boundary = element("p", "", uiText("researchPlacementBoundary"));
    root.replaceChildren(heading, controls, boundary);
  }

  function effectiveDate(item = {}) {
    return clean(state.previewAttentionDates[item.id] ?? item.attentionDate);
  }

  function exceptionFor(item = {}) {
    const date = effectiveDate(item);
    return item.needsAttention || item.attentionState === "carryover" || (item.deadline && item.deadline < state.today) || (date && date < state.today);
  }

  function titleCard(item = {}, date = "") {
    const button = element("button", "desk-title-card");
    button.type = "button";
    button.setAttribute("draggable", "true");
    button.dataset.calendarDragItem = item.id;
    button.dataset.calendarOpenCard = item.id;
    if (date) button.dataset.calendarEventDate = date;
    button.setAttribute("aria-label", deskText("deskOpenItem", { title: item.title || item.id }));
    button.setAttribute("aria-grabbed", "false");
    button.setAttribute("aria-pressed", String(item.id === state.selectedTaskId));
    button.append(element("strong", "", item.title || item.id));
    if (hasPlacementProjection()) {
      const region = placementRegion(item);
      const regionBadge = element("small", `placement-region-badge region-${region.toLowerCase()}`, placementLabel(region));
      regionBadge.title = safeArray(item.placementBasis).join(" · ");
      button.append(regionBadge);
    }
    if (state.mandatoryCommitmentIds.has(String(item.id || ""))) {
      button.dataset.mandatoryVisibility = "true";
      button.append(element("em", "mandatory-visibility-badge", deskText("deskRequired")));
    }
    if (exceptionFor(item)) button.append(element("span", "exception-dot", ""));
    return button;
  }

  function renderCardViewContract() {
    const root = byId("resource-contract-summary");
    if (!root) return;
    const summary = state.assetModel?.summary || {};
    const countLine = deskText("deskResearchObjectsCommitments", { objects: summary.semanticObjectCount || 0, commitments: summary.commitmentCount || 0, previews: summary.previewDocumentCount || 0, archived: summary.archivedDocumentCount || 0 });
    const mandatoryCount = Number(summary.mandatoryCommitmentCount || state.mandatoryCommitmentIds.size || 0);
    const overflow = Number(summary.mandatoryOverflow || Math.max(0, mandatoryCount - 12));
    const guarantee = summary.viewSafe
      ? deskText("deskViewGuaranteesPassIdentities")
      : deskText("deskViewGuaranteesNeedReview");
    root.replaceChildren(
      element("strong", "resource-contract-count", countLine),
      element("span", `resource-contract-guarantee ${summary.viewSafe ? "is-safe" : "needs-review"}`, guarantee),
      element("span", "resource-contract-mandatory", deskText("deskRequiredSoftBudgetOverflow", { mandatoryCount, overflow })),
    );
  }

  function renderDesk() {
    const dates = visibleDates();
    const dateSet = new Set(dates);
    const tray = byId("desk-tray");
    const oldCalendar = byId("desk-calendar");
    if (!tray || !oldCalendar) return;
    const calendar = oldCalendar.cloneNode(false);
    calendar.className = `calendar-${state.calendarView}-grid`;
    oldCalendar.replaceWith(calendar);
    tray.replaceChildren();

    const byDate = Object.fromEntries(dates.map((date) => [date, []]));
    const unscheduled = [];
    activeItems().forEach((item) => {
      const date = effectiveDate(item);
      if (dateSet.has(date)) byDate[date].push(item);
      else unscheduled.push(item);
    });
    const placed = placementItems();
    const placedIds = new Set(placed.map((item) => item.id));
    const candidates = state.taskFilter === "all" ? placed
      : state.taskFilter === "attention" ? placed.filter((item) => activeItems().includes(item) && exceptionFor(item))
        : unscheduled.filter((item) => placedIds.has(item.id));
    const listed = candidates.filter((item) => !state.taskQuery || clean(`${item.title} ${item.nextStep || ""}`).toLowerCase().includes(state.taskQuery));
    listed.forEach((item) => tray.append(titleCard(item, effectiveDate(item))));
    if (!listed.length) tray.append(element("p", "empty-state", deskText("deskNoMatchingItemsChoose")));

    const weekday = new Intl.DateTimeFormat(profile.language, { weekday: "short" });
    dates.forEach((date) => {
      const cell = element("section", "calendar-day");
      cell.dataset.calendarDate = date;
      if (date === state.today) cell.classList.add("is-today");
      if (state.calendarView === "month" && date.slice(0, 7) !== state.anchorDate.slice(0, 7)) cell.classList.add("is-outside-month");
      const heading = element("header");
      heading.append(element("span", "", weekday.format(parseIso(date))), element("strong", "", date.slice(5)));
      const stack = element("div", "calendar-day-cards");
      byDate[date].forEach((item) => stack.append(titleCard(item, date)));
      cell.append(heading, stack);
      calendar.append(cell);
    });
    text(byId("tray-count"), `${listed.length} / ${placed.length}`);
    text(byId("tray-heading"), deskText("deskResearchItemsLabel"));
    text(byId("calendar-heading"), { day: deskText("deskDayCalendar"), week: deskText("deskWeekCalendar"), month: deskText("deskMonthCalendar") }[state.calendarView]);
    text(byId("calendar-range"), periodLabel(dates) + (!dates.some((date) => byDate[date].length) && unscheduled.length ? ` · ${deskText("deskNothingScheduledInThis", { count: unscheduled.length })}` : ""));
    global.document.querySelectorAll("[data-calendar-view]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.calendarView === state.calendarView));
    });
    global.document.querySelectorAll("[data-task-filter]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.taskFilter === state.taskFilter)));
    renderPlacementControls();
    bindDeskInteractions();
  }

  function bindDeskInteractions() {
    global.ResearchOSResearchPortfolioWorkbench.bind(global.document.querySelector("[data-unified-desk]"), {
      onCalendarMove: ({ itemId, targetDate }) => previewAttention(itemId, targetDate),
      onCalendarOpenCard: ({ itemId }) => openDrawer(itemId),
    });
  }

  function paragraphs(values = []) {
    const fragment = global.document.createDocumentFragment();
    safeArray(values).filter(Boolean).forEach((value) => fragment.append(element("p", "", value)));
    return fragment;
  }

  function showDrawerLens(lens = "item") {
    state.drawerLens = lens;
    global.document.querySelectorAll("[data-lens-section]").forEach((section) => {
      section.hidden = section.dataset.lensSection !== lens;
    });
    byId("back-to-item").hidden = lens !== "component" || !selectedTask();
    byId("prepare-handoff").hidden = lens !== "item";
    if (byId("open-item-review")) byId("open-item-review").hidden = lens !== "item";
    text(byId("drawer-lens-label"), lens === "item" ? deskText("deskContinueThisResearch") : deskText("deskCardPreview"));
  }

  const REASON_COPY = Object.freeze({
    "Portfolio source_root 的明确文件入口": "Explicit file entry in Portfolio source_root",
    "Project Hub source_files 的稳定引用": "Stable reference in Project Hub source_files",
    "Portfolio related_people 的明确关系": "Explicit relationship in Portfolio related_people",
    "Portfolio accountable_owner 与人物卡唯一匹配": "Portfolio accountable_owner uniquely matches a person card",
    "accountable_owner 匹配到多个人物卡，需人工消歧": "accountable_owner matches several people; human disambiguation is required",
    "accountable_owner 尚未匹配到人物卡": "accountable_owner has not been matched to a person card",
    "可复用经验链接；仍需在当前事项下确认": "Reusable experience link; confirm its relevance to the current item",
    "当前 source_path 尚未连接到 Project Hub 或 Asset Graph；未按标题猜测关系。": "The source_path is not connected to Project Hub or Asset Graph; no relationship was inferred from its title.",
    "当前事项缺少可用于关系投影的 exact source identity。": "The item lacks an exact source identity for relationship projection."
});
  function reasonText(value = "") {
    return profile.language === "en" ? (REASON_COPY[value] || value) : value;
  }

  function componentTypeLabel(type = "asset") {
    return ({ paper: deskText("deskPaper"), project: deskText("deskProject"), person: deskText("deskPerson"), talk: deskText("deskTalk"), group: deskText("deskRelationshipGroup"), material: deskText("deskMaterial") })[type] || deskText("deskComponent");
  }

  function relationButton(relation = {}, stateLabel = "") {
    const button = element("button", "component-relation-card");
    button.type = "button";
    button.dataset.componentId = relation.componentId;
    button.append(element("strong", "", relation.title || relation.path || relation.componentId));
    const meta = [relation.identityState === "unresolved_reference" ? deskText("deskRecordedReferenceIdentityUnverified") : stateLabel, componentTypeLabel(relation.type), reasonText(safeArray(relation.reasons)[0])].filter(Boolean).join(" · ");
    if (meta) button.append(element("span", "", meta));
    if (relation.type === "material" && relation.path) button.append(element("span", "component-relation-path", shortText(relation.path, 96)));
    button.addEventListener("click", () => openComponentLens(relation.componentId));
    return button;
  }

  function proposedRelations(composition = selectedComposition()) {
    const confirmedIds = new Set(safeArray(composition?.confirmedComponents).map((entry) => entry.componentId));
    const existingIds = new Set(safeArray(composition?.candidateComponents).map((entry) => entry.componentId));
    return [...proposedAssetIds()].filter((id) => !confirmedIds.has(id) && !existingIds.has(id)).map((id) => {
      const component = state.compositionModel?.componentForId(id);
      return component ? {
        componentId: component.id,
        libraryAvailable: component.libraryAvailable,
        path: component.path,
        reasons: [deskText("deskRelationshipProposedOnThis")],
        relationTypes: ["browser_proposal"],
        sources: ["browser_disposable_state"],
        state: "candidate",
        title: component.title,
        type: component.type,
      } : null;
    }).filter(Boolean);
  }

  function renderComposition() {
    const composition = selectedComposition();
    if (!composition) return;
    const confirmed = safeArray(composition.confirmedComponents);
    const candidates = [...safeArray(composition.candidateComponents), ...proposedRelations(composition)];
    const handoff = selectedAssets();
    const summary = byId("drawer-composition-summary");
    const identityCopy = ({ exact_project: deskText("deskConnectedToProjectHub"), exact_asset_matrix: deskText("deskConnectedToThePaper"), exact_asset_card: deskText("deskConnectedToAnAsset"), portfolio_relations: deskText("deskComponentsLinkedThroughExplicit"), source_only: deskText("deskExactSourceFoundRelationships"), unbound: deskText("deskExactSourceIdentityIs") })[composition.identityState] || composition.identityState;
    summary.replaceChildren(paragraphs([
      identityCopy,
      confirmed.length ? deskText("deskRegisteredComponentsTheFull", { count: confirmed.length }) : deskText("deskRegisteredComponents0Similar"),
    ]));
    safeArray(composition.evidenceGaps).forEach((gap) => summary.append(element("p", "evidence-gap", deskText("deskEvidenceGap", { gap: reasonText(gap) }))));

    const confirmedRoot = byId("drawer-confirmed-components");
    confirmedRoot.replaceChildren();
    const confirmedVisible = state.expandedCompositionItems.has(composition.itemId) ? confirmed : confirmed.slice(0, 5);
    confirmedVisible.forEach((relation) => confirmedRoot.append(relationButton(relation, deskText("deskLinked"))));
    if (confirmed.length > 5) {
      const expanded = state.expandedCompositionItems.has(composition.itemId);
      const expand = element("button", "component-expand-button", expanded ? deskText("deskShowFirst5") : deskText("deskShowAll", { count: confirmed.length }));
      expand.type = "button";
      expand.dataset.expandComposition = "";
      expand.setAttribute("aria-expanded", String(expanded));
      expand.addEventListener("click", () => {
        if (expanded) state.expandedCompositionItems.delete(composition.itemId);
        else state.expandedCompositionItems.add(composition.itemId);
        renderComposition();
        byId("drawer-confirmed-components")?.querySelector("[data-expand-composition]")?.focus();
      });
      confirmedRoot.append(expand);
    }
    if (!confirmed.length) confirmedRoot.append(element("p", "drawer-note", deskText("deskNoRegisteredComponentsBrowse")));

    const candidateRoot = byId("drawer-candidate-components");
    candidateRoot.replaceChildren();
    candidates.forEach((relation) => candidateRoot.append(relationButton(relation, relation.sources?.includes("browser_disposable_state") ? deskText("deskPageCandidate") : deskText("deskRelationshipCandidate"))));
    if (!candidates.length) candidateRoot.append(element("p", "drawer-note", deskText("deskNoRegisteredCandidatesBrowse")));

    const handoffRoot = byId("drawer-handoff-components");
    handoffRoot.replaceChildren();
    handoff.forEach((component) => handoffRoot.append(relationButton({
      componentId: component.id,
      reasons: [deskText("deskIncludedOnlyInThis")],
      title: component.title,
      type: component.type,
    }, deskText("deskThisHandoff"))));
    if (!handoff.length) handoffRoot.append(element("p", "drawer-note", deskText("deskNothingSelectedUpTo")));
    text(byId("confirmed-component-count"), confirmed.length);
    text(byId("candidate-component-count"), candidates.length);
    text(byId("handoff-component-count"), handoff.length);
    renderResourceContextStatus();
  }

  function renderItemLens() {
    const item = selectedTask();
    const drawer = byId("item-drawer");
    if (!item || !drawer) return;
    showDrawerLens("item");
    drawer.dataset.exactItemId = item.id;
    text(byId("drawer-title"), item.title || item.id);

    const what = byId("drawer-what");
    what.replaceChildren(paragraphs([
      item.state === "closed" ? deskText("deskThisResponsibilityHasEnded") : "",
      item.lifecycleNote || "",
      item.currentStage || deskText("deskNoProgressSummaryIs"),
    ]));
    const provenance = element("details", "research-provenance");
    provenance.append(element("summary", "", deskText("deskJudgmentsBoundariesSource")));
    provenance.append(paragraphs([
      deskText("deskThisItemSummaryDoes"),
      item.sourcePath ? deskText("deskCanonicalSource", { sourcePath: item.sourcePath, sourcePathAvailable: item.sourcePathAvailable ? "" : deskText("deskCurrentlyUnavailable") }) : deskText("deskNoCanonicalSourceIs"),
      item.sourceRoot ? deskText("deskProjectWorkspaceEntry", { sourceRoot: item.sourceRoot, sourceRootAvailable: item.sourceRootAvailable ? "" : deskText("deskCurrentlyUnavailableContinuationFalls") }) : deskText("deskNoProjectWorkspace"),
      item.lastVerified ? deskText("deskRecordLastChecked", { lastVerified: item.lastVerified }) : "",
      ...safeArray(item.qualityIssues),
    ]));
    what.append(provenance);
    global.ResearchOSResearchPortfolioWorkbench.renderItemSource(item, what, {data: state.data, copy, element});
    renderLifecycle(item, what);
    renderComposition();

    const when = byId("drawer-when");
    when.replaceChildren();
    const dateLabel = element("label", "", deskText("deskAttentionDate"));
    const dateInput = element("input");
    dateInput.type = "date";
    dateInput.value = effectiveDate(item);
    dateInput.dataset.drawerAttentionDate = "";
    dateLabel.append(dateInput);
    const fixedFacts = element("p", "drawer-note", deskText("deskDeadlineReview", { deadline: item.deadline || deskText("deskNotRecorded"), reviewDate: item.reviewDate || deskText("deskNotRecorded") }));
    if (item.historicalTargetDate) {
      fixedFacts.append(element("span", "historical-date", deskText("deskPreviousTargetHistorical", { historicalTargetDate: item.historicalTargetDate })));
      if (item.targetDateBasis) fixedFacts.append(element("span", "date-basis", ` — ${item.targetDateBasis}`));
    }
    const confirmLabel = element("label", "effect-confirm");
    const confirmInput = element("input");
    confirmInput.type = "checkbox";
    confirmInput.dataset.attentionConfirm = "";
    confirmLabel.append(confirmInput, global.document.createTextNode(state.effectsEnabled
      ? deskText("deskConfirmChangingOnlyAttention")
      : deskText("deskPreviewDatesWithoutSaving")));
    if (!state.effectsEnabled) confirmInput.disabled = true;
    const actionRow = element("div", "button-row");
    const schedule = element("button", "", state.effectsEnabled ? deskText("deskSaveAttention") : deskText("deskPreviewSchedule"));
    schedule.type = "button";
    schedule.disabled = state.mutationPending;
    schedule.addEventListener("click", () => saveAttention(item.id, clean(dateInput.value)));
    const undo = element("button", "", deskText("deskUndoLastWrite"));
    undo.type = "button";
    undo.disabled = !state.effectsEnabled || state.mutationPending || state.lastUndo?.itemId !== item.id;
    undo.addEventListener("click", undoAttention);
    const reset = element("button", "", deskText("deskCancelDatePreview"));
    reset.type = "button";
    reset.disabled = !Object.prototype.hasOwnProperty.call(state.previewAttentionDates, item.id);
    reset.addEventListener("click", () => {
      delete state.previewAttentionDates[item.id];
      renderDesk();
      renderItemLens();
      byId("item-drawer")?.querySelector("[data-drawer-attention-date]")?.focus();
      status(deskText("deskRecordedDateRestoredOther"));
    });
    actionRow.append(schedule, reset);
    if (state.effectsEnabled) actionRow.append(undo);
    const note = element("p", "mutation-note", state.effectsEnabled
      ? deskText("deskSavingChangesThisItem")
      : deskText("deskDraggingAndDateSelection"));
    note.dataset.attentionStatus = "";
    note.setAttribute("aria-live", "polite");
    when.append(dateLabel, fixedFacts);
    if (state.effectsEnabled) when.append(confirmLabel);
    when.append(actionRow, note);

    const who = byId("drawer-who");
    const people = safeArray(item.relatedPeople).map((person) => person.name).filter(Boolean).join(deskText("deskListSeparator"));
    // English shows the recorded responsibility id; Chinese translates the two known ids.
    const responsibilityLabel = profile.language === "en"
      ? (item.responsibility || deskText("deskResponsibilityUnregistered"))
      : ({lead: deskText("deskLead"), support: deskText("deskSupport")}[item.responsibility] || deskText("deskResponsibilityUnregistered"));
    who.replaceChildren(paragraphs([
      deskText("deskResponsibility", { responsibilityLabel }),
      deskText("deskOwner", { accountableOwner: item.accountableOwner || item.owner || deskText("deskNotRecorded") }),
      people ? deskText("deskRelatedPeople", { people }) : "",
    ]));

    const how = byId("drawer-how");
    how.replaceChildren(paragraphs([
      item.state === "closed" ? deskText("deskHistoricalNextStep", { nextStep: item.nextStep || deskText("deskNotRecorded") }) : deskText("deskNextStep", { nextStep: item.nextStep || deskText("deskNotRecorded") }),
      item.state === "closed" ? deskText("deskPriorAcceptanceCriteriaNot", { successGate: item.successGate || deskText("deskNotRecorded") }) : deskText("deskAcceptance", { successGate: item.successGate || deskText("deskReturnAReviewableResult") }),
    ]));
    renderResourceCardBoxes();
  }

  function currentRelationState(componentId = "") {
    const composition = selectedComposition();
    if (!composition) return "unbound";
    if (safeArray(composition.confirmedComponents).some((entry) => entry.componentId === componentId)) return "confirmed";
    if (safeArray(composition.candidateComponents).some((entry) => entry.componentId === componentId) || proposedAssetIds().has(componentId)) return "candidate";
    return "unlinked";
  }

  function itemRelationButton(item = {}, label = "") {
    const button = element("button", "component-relation-card");
    button.type = "button";
    button.append(element("strong", "", item.title || item.id));
    if (label || safeArray(item.reasons)[0]) button.append(element("span", "", [label, reasonText(safeArray(item.reasons)[0])].filter(Boolean).join(" · ")));
    button.addEventListener("click", () => openDrawer(item.id));
    return button;
  }

  function renderComponentLens(componentId = state.focusedAssetId) {
    const component = state.compositionModel?.componentForId(componentId);
    const drawer = byId("item-drawer");
    if (!component || !drawer) return status(deskText("deskCannotIdentifyTheExact"));
    state.focusedAssetId = component.id;
    showDrawerLens("component");
    text(byId("drawer-title"), component.title || component.id);
    const identity = byId("component-identity");
    identity.replaceChildren(paragraphs([
      deskText("deskType", { componentTypeLabel: componentTypeLabel(component.type) }),
      component.path ? deskText("deskSource", { path: component.path }) : deskText("deskSourcePathNotRecorded"),
      component.type === "project" && global.ResearchOSAssetOverviewView?.projectOperationalStatusLabel
        ? global.ResearchOSAssetOverviewView.projectOperationalStatusLabel(component, uiText)
        : "",
      component.identity_state === "unresolved_reference"
        ? deskText("deskThisIsAnUnresolved")
        : component.libraryAvailable ? deskText("deskAvailableInTheCard") : deskText("deskThisObjectHasAn"),
      safeArray(component.relation_reasons)[0] ? deskText("deskRelationshipEvidence", { reason: reasonText(safeArray(component.relation_reasons)[0]) }) : "",
    ]));

    renderCardContent(component);
    renderCardMaturity(component);

    const reverse = state.compositionModel.reverseForComponent(component.id);
    const confirmedRoot = byId("component-confirmed-items");
    confirmedRoot.replaceChildren();
    safeArray(reverse.rootItems).forEach((item) => confirmedRoot.append(itemRelationButton(item, deskText("deskPrimaryItem"))));
    safeArray(reverse.confirmedItems).forEach((item) => confirmedRoot.append(itemRelationButton(item, deskText("deskLinked"))));
    if (!reverse.rootItems.length && !reverse.confirmedItems.length) confirmedRoot.append(element("p", "drawer-note", deskText("deskNoLinkedItemsAre")));

    const candidateRoot = byId("component-candidate-items");
    candidateRoot.replaceChildren();
    safeArray(reverse.candidateItems).forEach((item) => candidateRoot.append(itemRelationButton(item, deskText("deskRelationshipCandidate"))));
    if (!reverse.candidateItems.length) candidateRoot.append(element("p", "drawer-note", deskText("deskNoGraphCandidatesAre")));

    const task = selectedTask();
    const relationState = currentRelationState(component.id);
    const relationCopy = ({ confirmed: deskText("deskLinkedToTheCurrent"), candidate: deskText("deskCandidateRelationshipToThe"), unlinked: deskText("deskNoRegisteredRelationshipTo"), unbound: deskText("deskNoCurrentItemSelected") })[relationState];
    text(byId("component-current-relation"), relationCopy);
    const actions = byId("component-actions");
    actions.replaceChildren();
    {
      const handoff = handoffAssetIds();
      const handoffButton = element("button", "", handoff.has(component.id) ? deskText("deskRemoveFromHandoff") : (task ? deskText("deskAddToHandoff") : deskText("deskSelectForExploration")));
      handoffButton.type = "button";
      handoffButton.dataset.componentAction = "handoff";
      handoffButton.disabled = !handoff.has(component.id) && handoff.size >= 3;
      handoffButton.addEventListener("click", () => toggleHandoffComponent(component.id));
      actions.append(handoffButton);
      const proposed = proposedAssetIds();
      if (task && (relationState === "unlinked" || proposed.has(component.id))) {
        const candidateButton = element("button", "", proposed.has(component.id) ? deskText("deskCancelPageCandidate") : deskText("deskProposeRelationship"));
        candidateButton.type = "button";
        candidateButton.dataset.componentAction = "candidate";
        candidateButton.addEventListener("click", () => toggleProposedComponent(component.id));
        actions.append(candidateButton);
      }
      if (relationState === "candidate" && !proposed.has(component.id)) {
        actions.append(element("p", "drawer-note", deskText("deskTheGraphMarksThis")));
      }
      actions.append(element("p", "drawer-note", deskText("deskSelectionIsForThis")));
    }
    renderResourceContextStatus();
    syncResourceCardBoxSelection();
    const library = byId("resource-card-boxes");
    if (library) applyResourceCardBoxSearch(library, state.resourceQuery);
  }

  function renderLifecycle(item, root) {
    global.ResearchOSResearchPortfolioWorkbench.renderLifecycle(item, root, {
      state, copy, element, clean, selectedTask, status,
      refreshLifecycleProjection: () => global.ResearchOSResearchPortfolioWorkbench.refreshLifecycleProjection(DATA_PATH, state, projectionPayload),
      invalidateHandoff, renderDesk, renderItemLens,
    });
  }

  const cardLevelName = (level = "") => global.ResearchOSResearchPortfolioWorkbench.cardLevelName(level, copy);

  async function renderCardContent(component) {
    const root = byId("component-content");
    if (!root) return;
    const revision = ++state.previewRevision;
    root.replaceChildren(element("p", "drawer-note", component.preview || deskText("deskLoadingCardContent")));
    const previewDocuments = safeArray(state.data?.preview_documents);
    const admitted = (path = "") => previewDocuments.some((doc) => doc.path === path);
    if (component.identity_state === "unresolved_reference") {
      const composition = selectedComposition();
      const belongsToCurrentItem = [...safeArray(composition?.confirmedComponents), ...safeArray(composition?.candidateComponents)]
        .some((relation) => relation.componentId === component.id);
      const source = belongsToCurrentItem
        ? state.compositionModel?.componentForId(composition?.rootComponentId) : null;
      const content = paragraphs([
        component.preview,
        deskText("deskThisIsARelationship"),
        source?.path ? deskText("deskReferenceRecordedInItem", { path: source.path }) : deskText("deskThisReferenceHasNo"),
      ]);
      if (source?.path && admitted(source.path) && /\.(md|ya?ml)$/i.test(source.path)) {
        const button = element("button", "", deskText("deskViewItemSourceMarkdown"));
        button.type = "button";
        button.addEventListener("click", () => openComponentLens(source.id));
        content.append(button);
      } else if (source?.path) {
        content.append(element("p", "drawer-note", deskText("deskTheItemSourceIs")));
      }
      root.replaceChildren(content);
      return;
    }
    if (!component.path) {
      root.replaceChildren(paragraphs([component.preview, deskText("deskThisObjectHasNo")]));
      return;
    }
    if (!/\.(md|ya?ml)$/i.test(component.path)) {
      root.replaceChildren(paragraphs([component.preview, deskText("deskThisSourceIsNot")]));
      return;
    }
    if (!admitted(component.path)) {
      root.replaceChildren(paragraphs([component.preview, deskText("deskTheSourcePathIs")]));
      return;
    }
    try {
      const content = await global.ResearchOSPreviewContentClient.loadPreviewContent(component.path);
      if (revision !== state.previewRevision || state.focusedAssetId !== component.id || byId("item-drawer")?.hidden) return;
      const body = element("div", "markdown-body card-content-body");
      // Preserve source text, but move a source-page language switch out of the reading lead.
      const navigation = content.match(/^(?:---\r?\n[\s\S]*?\r?\n---\s*)?(<p align="right">[\s\S]*?<\/p>)/i);
      const navigationLabel = navigation?.[1].replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim();
      const sourceText = ["English | 中文", "中文 | English"].includes(navigationLabel) ? content.replace(navigation[1], "") : content;
      body.innerHTML = global.ResearchOSPreviewMarkdownService.markdownToHtml(sourceText, component.path);
      if (sourceText !== content) {
        const metadata = element("details", "card-source-format");
        metadata.append(element("summary", "", deskText("deskLanguageNavigationInSource")), element("pre", "", navigation[1]));
        body.append(metadata);
      }
      root.replaceChildren(body);
    } catch {
      if (revision !== state.previewRevision || state.focusedAssetId !== component.id) return;
      root.replaceChildren(paragraphs([component.preview, deskText("deskFullContentCouldNot")]));
    }
  }

  function renderCardMaturity(component) {
    const root = byId("component-maturity");
    if (!root) return;
    const maturity = component.card_maturity || global.ResearchOSContracts.cardMaturityProfile(component.type, component);
    const axisNames = {M:deskText("deskMaterialMaturity"),I:deskText("deskProjectMaturity"),R:deskText("deskRelationshipContextMaturity"),G:deskText("deskCompositionLevel")};
    root.replaceChildren(element("h3", "", `${axisNames[maturity.axis] || ""} · ${cardLevelName(maturity.level)}`));
    const sequence = element("ol", "card-level-sequence");
    safeArray(global.ResearchOSContracts.cardMaturitySequences[maturity.axis]).forEach((level) => {
      const entry = element("li", "", cardLevelName(level));
      if (level === maturity.level) entry.setAttribute("aria-current", "step");
      sequence.append(entry);
    });
    root.append(sequence, paragraphs([
      maturity.confirmed ? deskText("deskRecordedLevelNotScientific") : deskText("deskTheCurrentLevelNeeds"),
      maturity.reason || deskText("deskTheProjectionSuppliesNo"),
      maturity.axis === "R" ? deskText("deskThisDescribesTheRelationship") : deskText("deskMaturityIsDistinctFrom"),
    ]));
    const targetCriteria = {
      M1:["补齐身份、来源、边界与下一步。","Identify the source, boundary and next step."],
      M2:["核对论证结构、关键证据、版本与可复用条件。","Check the argument, evidence, version and reuse conditions."],
      M3:["建立跨项目联系，说明可迁移判断及适用条件。","Explain cross-project connections, transferable judgments and their conditions."],
      I1:["明确值得试验的问题与沙盒范围。","Define a testable question and sandbox scope."],
      I2:["明确责任人、目标与下一步。","Establish ownership, a goal and the next step."],
      I3:["明确独立贡献、研究路线与协作安排。","Establish an independent contribution, research route and collaboration."],
      R1:["核对关系来源与登记边界。","Verify relationship sources and registration boundaries."],
      R2:["补齐有依据的具体协作上下文。","Supply sourced context for concrete collaboration."],
      R3:["核对跨项目协作上下文及使用边界。","Verify cross-project collaboration context and its use boundaries."],
      G1:["说明组合目的与组成关系。","Explain the grouping purpose and component relations."],
      G2:["从组合中提炼有依据的研究方向。","Derive a justified research direction from the group."],
      R_research_mainline:["核对方向之间的联系及主线判断。","Verify relations among directions and the mainline judgment."],
    };
    if (maturity.confirmed && maturity.action === "enhance" && targetCriteria[maturity.target_level]) {
      root.append(element("p", "drawer-note", `${deskText("deskProposedTarget")}: ${cardLevelName(maturity.target_level)} — ${copy(...targetCriteria[maturity.target_level])}`));
    }
    const action = !maturity.confirmed ? "verify" : maturity.action;
    const actionNames = {enhance:deskText("deskPreviewEnhancement"),verify:deskText("deskPreviewLevelVerification"),reverify:deskText("deskPreviewReverification"),use:deskText("deskUseInThisHandoff")};
    const button = element("button", "primary", component.path ? actionNames[action] : deskText("deskSourceRequired"));
    button.type = "button";
    button.disabled = !component.path;
    button.dataset.cardEnhancement = component.id;
    button.addEventListener("click", () => {
      if (action === "use") return toggleHandoffComponent(component.id);
      prepareCardEnhancement(component, maturity, action).catch((error) => status(deskText("deskEnhancementPreviewFailed", { message: error.message })));
    });
    root.append(button, element("p", "drawer-note", deskText("deskTheSystemRecomputesLevels")));
  }

  async function prepareCardEnhancement(component, maturity, action) {
    const card = [...global.document.querySelectorAll("[data-asset-box-card]")].find((node) => node.dataset.assetCardId === component.id);
    if (!card || !component.path) return;
    const payload = global.ResearchOSAssetOverviewWorkbenchService.assetTaskPayloadFromCard(card);
    const target = action === "enhance" ? maturity.target_level : maturity.level;
    payload.enhancement = {...payload.enhancement, action, target_level: target || ""};
    payload.candidate.proposed_writeback.proposed_state = target || "unverified";
    if (profile.publicStarter) {
      payload.candidate.proposed_writeback.save_target = "";
      payload.candidate.proposed_writeback.proposed_state = "copy_only_review";
      payload.candidate.sensitivity = "public_safe";
      payload.candidate.required_confirmation = "handoff_only";
    }
    const intent = deskText("deskReviewTheAxisOf", { title: component.title, axis: maturity.axis, maturity: maturity.level || deskText("deskUnverifiedLevel", {}, contentLanguage()), action: action === "enhance" ? deskText("deskProposedTargetLevel", { target }, contentLanguage()) : deskText("deskVerifyTheCurrentLevel", {}, contentLanguage()) }, contentLanguage());
    const session = {id:`unified-desk:enhance:${component.id}`,title:component.title,goal:intent,intent,cards:[component],sourceHints:[component.path],portfolioBinding:null,responseMode:"answer",templateLanguage:contentLanguage(),sensitivity:profile.publicStarter?"public":"private",evidenceBoundary:intent,enhancement:payload.enhancement,candidate:payload.candidate};
    const selection = {authority:profile.authority,primaryProject:null,relatedProjects:[],saveTarget:"",definitionOfDone:[intent],excluded:[{reason:"candidate_only",scope:"canonical writes, automatic level changes and unrelated material"}]};
    // Capture the current item only as a UI cancellation guard, never as enhancement task ownership.
    return presentHandoff(session, selection, null, selectedTask()?.id || "");
  }

  let drawerReturnTarget = null;

  function enterDrawer() {
    const active = global.document.activeElement;
    if (active && !byId("item-drawer")?.contains(active)) {
      drawerReturnTarget = {
        node: active,
        itemId: active.dataset?.calendarOpenCard,
        assetId: active.dataset?.assetCardId,
      };
    }
  }

  function focusDrawer() {
    const heading = byId("drawer-title");
    heading?.setAttribute("tabindex", "-1");
    heading?.focus();
  }

  function closeDrawer() {
    invalidateHandoff();
    byId("item-drawer").hidden = true;
    state.drawerLens = "item";
    state.focusedAssetId = "";
    state.selectedTaskId = "";
    if (state.resourceFilter === "related") state.resourceFilter = "all";
    renderDesk();
    renderResourceCardBoxes();
    const target = drawerReturnTarget;
    const replacement = [...global.document.querySelectorAll("[data-calendar-open-card], [data-asset-card-id]")]
      .find((node) => (target?.itemId && node.dataset.calendarOpenCard === target.itemId)
        || (target?.assetId && node.dataset.assetCardId === target.assetId));
    (replacement || (target?.node?.isConnected ? target.node : byId("current-period")))?.focus();
    drawerReturnTarget = null;
  }

  function openDrawer(itemId = "") {
    const item = state.portfolioModel?.items?.find((candidate) => candidate.id === itemId);
    if (!item) return status(deskText("deskCannotIdentifyTheExactItem"));
    enterDrawer();
    invalidateHandoff();
    state.selectedTaskId = item.id;
    state.focusedAssetId = "";
    const drawer = byId("item-drawer");
    drawer.hidden = false;
    renderDesk();
    renderItemLens();
    focusDrawer();
    if (global.matchMedia?.("(max-width: 720px)")?.matches) drawer.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function openComponentLens(componentId = "") {
    const component = state.compositionModel?.componentForId(componentId);
    if (!component) return status(deskText("deskCannotIdentifyTheExact"));
    const drawer = byId("item-drawer");
    enterDrawer();
    invalidateHandoff();
    drawer.hidden = false;
    renderComponentLens(component.id);
    focusDrawer();
    if (global.matchMedia?.("(max-width: 720px)")?.matches) drawer.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function toggleHandoffComponent(componentId = "") {
    if (!state.compositionModel?.componentForId(componentId)) return;
    const ids = handoffAssetIds();
    if (ids.has(componentId)) ids.delete(componentId);
    else if (ids.size >= 3) return status(deskText("deskAHandoffCanInclude"));
    else ids.add(componentId);
    invalidateHandoff();
    renderComponentLens(componentId);
    byId("component-actions")?.querySelector('[data-component-action="handoff"]')?.focus();
    status(deskText("deskSelectionUpdatedNoDurable"));
  }

  function toggleProposedComponent(componentId = "") {
    if (!selectedTask()) return status(deskText("deskSelectAnItemBefore"));
    if (currentRelationState(componentId) === "confirmed") return status(deskText("deskThisComponentAlreadyHas"));
    const ids = proposedAssetIds();
    if (ids.has(componentId)) ids.delete(componentId);
    else ids.add(componentId);
    invalidateHandoff();
    renderComponentLens(componentId);
    byId("component-actions")?.querySelector('[data-component-action="candidate"]')?.focus();
    status(deskText("deskPageCandidateUpdatedCanonical"));
  }

  function previewAttention(itemId = "", targetDate = "") {
    const item = state.portfolioModel?.items?.find((candidate) => candidate.id === itemId);
    if (!item || !parseIso(targetDate)) return status(deskText("deskInvalidAttentionDateNo"));
    state.previewAttentionDates[item.id] = targetDate;
    state.selectedTaskId = item.id;
    const drawer = byId("item-drawer");
    if (drawer) drawer.hidden = false;
    renderDesk();
    renderItemLens();
    byId("item-drawer")?.querySelector("[data-drawer-attention-date]")?.focus();
    const message = state.effectsEnabled
      ? deskText("deskPreviewedForConfirm", { title: item.title, targetDate })
      : deskText("deskPreviewedForDeadline", { title: item.title, targetDate });
    text(global.document.querySelector("[data-attention-status]"), message);
    return status(message);
  }

  // 保存和撤销都保持 deadline / lifecycle 未改变。
  async function saveAttention(itemId = "", targetDate = "") {
    const item = state.portfolioModel?.items?.find((candidate) => candidate.id === itemId);
    if (!item || !parseIso(targetDate)) return status(deskText("deskInvalidAttentionDateNo"));
    if (!state.effectsEnabled) return previewAttention(itemId, targetDate);
    const drawer = byId("item-drawer");
    const confirmed = selectedTask()?.id === item.id && state.drawerLens === "item"
      && drawer && !drawer.hidden && drawer.dataset.exactItemId === item.id
      && drawer.querySelector("[data-attention-confirm]")?.checked;
    if (!confirmed) {
      openDrawer(item.id);
      return text(global.document.querySelector("[data-attention-status]"), deskText("deskConfirmBeforeSavingPreview"));
    }
    if (state.mutationPending) return status(deskText("deskWaitForTheCurrent"));
    state.mutationPending = true;
    const previous = { attentionDate: item.attentionDate, attentionState: item.attentionState };
    try {
      const result = await global.ResearchOSWorkSessionClient.applyAttentionAction(item, {
        action: "schedule",
        attentionDate: targetDate,
      });
      if (!result?.ok) throw new Error(result?.message || result?.status || "unknown");
      state.lastUndo = result.undo ? { ...result.undo, itemId: item.id, previous } : null;
      item.attentionDate = targetDate;
      item.attentionState = targetDate === state.today ? "today" : "upcoming";
      delete state.previewAttentionDates[item.id];
      invalidateHandoff();
      renderDesk();
      status(deskText("deskSavedTheAttentionDate", { title: item.title || item.id }));
    } catch (error) {
      status(deskText("deskCouldNotSave", { title: item.title || item.id, message: error.message }));
    } finally {
      state.mutationPending = false;
      if (selectedTask()?.id === item.id && !byId("item-drawer")?.hidden && state.drawerLens === "item") {
        renderItemLens();
        byId("item-drawer")?.querySelector("[data-drawer-attention-date]")?.focus();
      }
    }
  }

  async function undoAttention() {
    if (!state.effectsEnabled || state.mutationPending) return;
    const receipt = state.lastUndo;
    const item = selectedTask();
    if (!receipt || receipt.itemId !== item?.id) return status(deskText("deskReturnToTheOriginal"));
    state.mutationPending = true;
    try {
      const result = await global.ResearchOSWorkSessionClient.undoMutation(receipt);
      if (!result?.ok) throw new Error(result?.message || result?.status || "unknown");
      Object.assign(item, receipt.previous);
      if (receipt.kind === "portfolio_state" && result.rebuilt) await global.ResearchOSResearchPortfolioWorkbench.refreshLifecycleProjection(DATA_PATH, state, projectionPayload);
      delete state.previewAttentionDates[item.id];
      state.lastUndo = null;
      invalidateHandoff();
      renderDesk();
      status(result.rebuilt === false
        ? deskText("deskTheStateWriteWas")
        : deskText("deskUndidTheLastWrite", { title: item.title || item.id }));
    } catch (error) {
      status(deskText("deskCouldNotUndo", { title: item.title || item.id, message: error.message }));
    } finally {
      state.mutationPending = false;
      if (selectedTask()?.id === item.id && !byId("item-drawer")?.hidden && state.drawerLens === "item") {
        renderItemLens();
        byId("item-drawer")?.querySelector("[data-drawer-attention-date]")?.focus();
      }
    }
  }

  function syncResourceCardBoxSelection(root = byId("resource-card-boxes")) {
    if (!root) return;
    const composition = selectedComposition();
    const confirmedIds = new Set(safeArray(composition?.confirmedComponents).map((entry) => entry.componentId));
    const candidateIds = new Set([
      ...safeArray(composition?.candidateComponents).map((entry) => entry.componentId),
      ...proposedAssetIds(),
    ]);
    const handoffIds = handoffAssetIds();
    root.querySelectorAll("[data-asset-box-card]").forEach((button) => {
      const id = button.dataset.assetCardId || "";
      const confirmed = confirmedIds.has(id);
      const candidate = candidateIds.has(id) && !confirmed;
      const selected = handoffIds.has(id);
      button.classList.toggle("is-linked-component", confirmed);
      button.classList.toggle("is-candidate-component", candidate);
      button.classList.toggle("is-handoff-selected", selected);
      const viewing = state.focusedAssetId === id && state.drawerLens === "component";
      button.classList.toggle("is-viewing", viewing);
      button.setAttribute("aria-expanded", String(viewing));
      button.dataset.relationState = confirmed ? "confirmed" : candidate ? "candidate" : "unlinked";
      button.setAttribute("aria-pressed", String(selected));
      button.draggable = false;
      const chip = button.querySelector(".asset-card-maturity-chip");
      if (chip) chip.textContent = cardLevelName(button.dataset.assetCardMaturityLevel) + (!button.dataset.assetCardMaturityLevel || button.dataset.assetCardMaturityConfirmed === "true" ? "" : deskText("deskUnverified"));
    });
  }

  function renderResourceContextStatus() {
    const composition = selectedComposition();
    const confirmed = safeArray(composition?.confirmedComponents);
    const candidates = [...safeArray(composition?.candidateComponents), ...proposedRelations(composition)];
    text(byId("resource-linked-count"), confirmed.length);
    text(byId("resource-candidate-count"), candidates.length);
    text(byId("resource-count"), handoffAssetIds().size);
    global.document.querySelectorAll("[data-resource-filter]").forEach((button) => {
      button.disabled = button.dataset.resourceFilter === "related" && !selectedTask();
      button.setAttribute("aria-pressed", String(button.dataset.resourceFilter === state.resourceFilter));
    });
    const exploration = byId("exploration-bar");
    if (exploration) exploration.hidden = Boolean(selectedTask()) || handoffAssetIds().size === 0;
    text(byId("exploration-count"), handoffAssetIds().size);
    text(byId("exploration-selection"), selectedAssets().map((asset) => asset.title || asset.id).join(deskText("deskListSeparator")));
    const prepare = byId("prepare-exploration");
    if (prepare) prepare.disabled = !clean(state.explorationIntent) || !handoffAssetIds().size;
    text(byId("resource-context-note"), selectedTask()
      ? deskText("deskRelatedToA", { title: selectedTask().title })
      : deskText("deskYouCanStartWith"));
  }

  function applyResourceCardBoxSearch(root, value = "") {
    state.resourceQuery = value;
    const query = clean(value).toLowerCase();
    let matches = 0;
    root.querySelectorAll("[data-asset-card-box]").forEach((box) => {
      let boxMatches = 0;
      box.querySelectorAll("[data-asset-box-card]").forEach((card) => {
        const match = !query || clean(card.dataset.assetCardSearchText).toLowerCase().includes(query);
        const id = card.dataset.assetCardId;
        const relation = currentRelationState(id);
        const inScope = state.resourceFilter === "all" || (state.resourceFilter === "selected" ? handoffAssetIds().has(id) : ["confirmed", "candidate"].includes(relation));
        const eligible = match && inScope;
        const visible = eligible;
        card.hidden = !visible;
        if (visible) boxMatches += 1;
      });
      box.hidden = boxMatches === 0;
      if (query && boxMatches) box.open = true;
      matches += boxMatches;
    });
    const empty = byId("resource-empty");
    if (empty) empty.hidden = matches > 0;
    const searchStatus = root.querySelector("[data-asset-card-global-search-status]");
    if (searchStatus) searchStatus.textContent = query ? deskText("deskMatchingCards", { matches }) : deskText("deskSearchByTitleType");
    const clear = root.querySelector("[data-asset-card-global-search-clear]");
    if (clear) {
      clear.hidden = !query;
      clear.disabled = !query;
    }
  }

  function bindResourceCardBoxes(root) {
    if (!root) return;
    root.querySelectorAll("[data-asset-box-card]").forEach((button) => button.addEventListener("click", (event) => {
      event.preventDefault();
      const cardId = button.dataset.assetCardId || "";
      openComponentLens(cardId);
    }));
    const search = root.querySelector("[data-asset-card-global-search]");
    search?.addEventListener("input", () => applyResourceCardBoxSearch(root, search.value));
    root.querySelector("[data-asset-card-global-search-clear]")?.addEventListener("click", () => {
      if (search) search.value = "";
      applyResourceCardBoxSearch(root, "");
    });
    root.querySelectorAll("[data-asset-card-expand-box]").forEach((button) => button.addEventListener("click", (event) => {
      event.preventDefault();
      const box = button.closest("[data-asset-card-box]");
      if (!box) return;
      box.classList.toggle("user-expanded");
      button.setAttribute("aria-expanded", String(box.classList.contains("user-expanded")));
      applyResourceCardBoxSearch(root, search?.value || "");
    }));
  }

  function renderResourceCardBoxes() {
    const root = byId("resource-card-boxes");
    if (!root) return;
    const renderer = global.ResearchOSAssetOverviewView.renderAssetCardBoxWorkbench;
    if (typeof renderer !== "function") return text(root, deskText("deskTheCardLibraryView"));
    root.innerHTML = renderer({ boxes: safeArray(state.assetModel?.cardBoxes), publicMode: profile.publicStarter }, {
      escapeHtml: global.ResearchOSUiCore.escapeHtml,
      shortText,
      translate: uiText,
    });
    bindResourceCardBoxes(root);
    syncResourceCardBoxSelection(root);
    const search = root.querySelector("[data-asset-card-global-search]");
    if (search) search.value = state.resourceQuery;
    applyResourceCardBoxSearch(root, state.resourceQuery);
    renderResourceContextStatus();
    renderCardViewContract();
  }

  const handoff = global.ResearchOSUnifiedDeskHandoff.create({
    state, profile, selectedTask, selectedAssets, contentLanguage, deskText, status, text, byId, element,
  });
  const { buildSession, copyHandoff, prepareHandoff, presentHandoff, routeDecision, selectionFor } = handoff;

  function shiftPeriod(direction = 1) {
    state.anchorDate = calendar.shiftAnchor(state.calendarView, state.anchorDate, direction);
    renderDesk();
  }

  const STATIC_COPY = Object.freeze({
    reviewResults: {"zh-CN":"结果与审阅","en":"Results & review"},
    componentIdentity: {"zh-CN":"来源与关系","en":"Source & relationships"},
    prepareContext: {"zh-CN":"准备研究上下文","en":"Prepare research context"},
    completePacket: {"zh-CN":"查看完整交接文本与技术信息","en":"Full handoff text & technical details"},
    cardContent: {"zh-CN":"卡片内容","en":"Card content"},
    cardLevel: {"zh-CN":"等级与增强","en":"Maturity & enhancement"},
    workspaceLabel: {"zh-CN": "安排 · 探索 · 接续", "en": "Plan · Explore · Continue"},
    materialsLabel: {"zh-CN": "从已有积累出发", "en": "Build on what you know"},
    taskScope: {"zh-CN": "事项筛选", "en": "Item filter"},
    resourceScope: {"zh-CN": "资源范围", "en": "Resource scope"},
    taskSearch: {"zh-CN": "搜索研究事项", "en": "Find a research item"},
    outside: {"zh-CN": "本期之外", "en": "Outside period"},
    all: {"zh-CN": "全部", "en": "All"},
    attention: {"zh-CN": "需关注", "en": "Needs attention"},
    related: {"zh-CN": "相关", "en": "Related"},
    selected: {"zh-CN": "本轮选取", "en": "Selected"},
    emptyResources: {"zh-CN": "没有匹配的资源。切换全部或清空搜索继续浏览。", "en": "No matching resources. Choose All or clear the search to keep exploring."},
    exploration: {"zh-CN": "本轮探索", "en": "This exploration"},
    explorationIntent: {"zh-CN": "这次想了解什么？", "en": "What would you like to explore?"},
    explorationHint: {"zh-CN": "尚未绑定事项 · 仅在本页保留选取与草稿", "en": "No item bound · Selection and draft stay on this page"},
    clearSelection: {"zh-CN": "清空选取", "en": "Clear selection"},
    previewExploration: {"zh-CN": "预览探索交接", "en": "Preview exploration handoff"},
    currentState: {"zh-CN": "进展记录", "en": "Progress record"},
    nextAction: {"zh-CN": "下一步与完成标准", "en": "Next step & acceptance"},
    researchContext: {"zh-CN": "关联资源", "en": "Related resources"},
    attentionPlan: {"zh-CN": "安排关注时间", "en": "Plan attention"},
    responsibility: {"zh-CN": "责任与协作", "en": "Responsibility & people"},

    "deskTitle": {"zh-CN": "研究工作台", "en": "Research desk"},
    "calendarView": {"zh-CN": "日历视图", "en": "Calendar view"},
    "day": {"zh-CN": "日", "en": "Day"},
    "week": {"zh-CN": "周", "en": "Week"},
    "month": {"zh-CN": "月", "en": "Month"},
    "previous": {"zh-CN": "上一个时间段", "en": "Previous period"},
    "today": {"zh-CN": "今天", "en": "Today"},
    "next": {"zh-CN": "下一个时间段", "en": "Next period"},
    "trayHint": {"zh-CN": "先选一项，查看当前状态与下一步；需要时再安排日期。", "en": "Choose an item to recover its state and next step. Schedule attention when needed."},
    "calendarBoundary": {"zh-CN": "拖动只预览关注日期，不改变截止日期或研究进展。", "en": "Dragging previews attention dates; it does not change deadlines or project state."},
    "libraryTitle": {"zh-CN": "资源库", "en": "Resource library"},
    "libraryHint": {"zh-CN": "浏览、连接、再组合。选中资源先查看，不会自动关联或执行。", "en": "Browse, connect, then compose. Opening a resource does not link it or run anything."},
    "linked": {"zh-CN": "已关联", "en": "Linked"},
    "candidate": {"zh-CN": "候选", "en": "Candidate"},
    "handoff": {"zh-CN": "本轮交接", "en": "This handoff"},
    "itemDetails": {"zh-CN": "事项详情", "en": "Item details"},
    "back": {"zh-CN": "返回事项", "en": "Back to item"},
    "closeDetails": {"zh-CN": "关闭详情", "en": "Close details"},
    "close": {"zh-CN": "关闭", "en": "Close"},
    "linkedComponents": {"zh-CN": "已关联组件", "en": "Linked components"},
    "candidateComponents": {"zh-CN": "可增加组件", "en": "Candidate components"},
    "toCodex": {"zh-CN": "本轮交给 Agent", "en": "For this agent handoff"},
    "browse": {"zh-CN": "浏览下方全部组件", "en": "Browse all components below"},
    "supported": {"zh-CN": "已关联的事项", "en": "Linked items"},
    "possible": {"zh-CN": "待核对的关联", "en": "Relationships to check"},
    "prepare": {"zh-CN": "预览 Agent 交接包", "en": "Preview agent handoff"},
    "handoffTitle": {"zh-CN": "Agent 交接预览", "en": "Agent handoff preview"},
    "copy": {"zh-CN": "复制交接文本", "en": "Copy handoff text"}
  });
  function translateStaticCopy() {
    global.document.querySelectorAll("[data-desk-copy]").forEach((node) => {
      const value = STATIC_COPY[node.dataset.deskCopy]?.[profile.language];
      if (value) node.textContent = value;
    });
    global.document.querySelectorAll("[data-desk-copy-aria]").forEach((node) => {
      const value = STATIC_COPY[node.dataset.deskCopyAria]?.[profile.language];
      if (value) node.setAttribute("aria-label", value);
    });
  }

  function renderReadyStatus() {
    const mode = state.effectsEnabled ? deskText("deskLocalWorkspaceConfirm") : deskText("deskReadOnlyPreviewCopy");
    const referenceDate = state.portfolioModel?.referenceDate;
    status(deskText("deskReadyStatus", { count: activeItems().length, mode: referenceDate ? `${mode} · ${deskText("deskFictionalDate", { date: referenceDate })}` : mode }), "ready");
  }

  function refreshLanguage() {
    translateStaticCopy();
    if (!state.data) return;
    if (state.statusMode === "ready") renderReadyStatus();
    state.assetModel = projectionPayload(state.data).assetModel;
    renderDesk();
    if (state.selectedTaskId && !byId("item-drawer")?.hidden) {
      if (state.drawerLens === "component") renderComponentLens();
      else renderItemLens();
    } else {
      renderResourceCardBoxes();
      if (state.drawerLens === "component" && !byId("item-drawer")?.hidden) renderComponentLens();
    }
  }

  function bind() {
    if (global.MutationObserver) {
      new global.MutationObserver(refreshLanguage).observe(global.document.documentElement, { attributes: true, attributeFilter: ["lang"] });
    }
    translateStaticCopy();
    global.document.querySelectorAll("[data-calendar-view]").forEach((button) => button.addEventListener("click", () => {
      state.calendarView = button.dataset.calendarView;
      renderDesk();
    }));
    global.document.querySelectorAll("[data-task-filter]").forEach((button) => button.addEventListener("click", () => {
      state.taskFilter = button.dataset.taskFilter;
      renderDesk();
    }));
    byId("desk-placement-controls")?.addEventListener("click", (event) => {
      const button = event.target?.closest?.("[data-placement-filter]");
      if (!button) return;
      state.placementFilter = button.dataset.placementFilter;
      renderDesk();
    });
    byId("desk-task-search")?.addEventListener("input", (event) => { state.taskQuery = clean(event.target.value).toLowerCase(); renderDesk(); });
    global.document.querySelectorAll("[data-resource-filter]").forEach((button) => button.addEventListener("click", () => {
      state.resourceFilter = button.dataset.resourceFilter;
      const root = byId("resource-card-boxes");
      if (root) applyResourceCardBoxSearch(root, state.resourceQuery);
      renderResourceContextStatus();
    }));
    byId("exploration-intent")?.addEventListener("input", (event) => {
      state.explorationIntent = event.target.value;
      invalidateHandoff();
      renderResourceContextStatus();
    });
    byId("prepare-exploration")?.addEventListener("click", () => prepareHandoff().catch((error) => status(deskText("deskHandoffPreparationFailed", { code: error.code || error.message }))));
    byId("clear-exploration")?.addEventListener("click", () => {
      handoffAssetIds("").clear();
      invalidateHandoff();
      renderResourceCardBoxes();
      if (state.drawerLens === "component" && !byId("item-drawer")?.hidden) renderComponentLens();
      global.document.querySelector('[data-resource-filter="all"]')?.focus();
    });
    byId("previous-period")?.addEventListener("click", () => shiftPeriod(-1));
    byId("current-period")?.addEventListener("click", () => { state.anchorDate = state.today; renderDesk(); });
    byId("next-period")?.addEventListener("click", () => shiftPeriod(1));
    byId("back-to-item")?.addEventListener("click", () => { renderItemLens(); focusDrawer(); });
    byId("close-drawer")?.addEventListener("click", closeDrawer);
    byId("open-item-review")?.addEventListener("click", () => {
      const item = selectedTask();
      if (!item || typeof global.openItemExecutionDrawer !== "function") return status(deskText("deskReviewIsUnavailableHere"));
      if (global.openItemExecutionDrawer(item.id, "review", { focus: true })) closeDrawer();
    });
    byId("item-drawer")?.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !byId("handoff-dialog")?.open) {
        event.preventDefault();
        closeDrawer();
      }
    });
    byId("prepare-handoff")?.addEventListener("click", () => prepareHandoff().catch((error) => status(deskText("deskHandoffPreparationFailed", { code: error.code || error.message }))));
    byId("copy-handoff")?.addEventListener("click", copyHandoff);
    byId("close-handoff")?.addEventListener("click", () => byId("handoff-dialog")?.close());
  }

  async function init(options = {}) {
    bind();
    const fetcher = options.fetcher || global.fetch?.bind(global);
    if (typeof fetcher !== "function") return status(deskText("deskCannotReadTheLocal"));
    try {
      const response = await fetcher(options.dataPath || DATA_PATH, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      state.data = await response.json();
      const projected = projectionPayload(state.data);
      state.portfolioModel = projected.portfolioModel;
      state.assetModel = projected.assetModel;
      state.compositionModel = projected.compositionModel;
      state.assetCards = projected.compositionModel.components;
      state.mandatoryCommitmentIds = new Set(
        safeArray(state.data?.asset_graph?.card_view_consolidation?.mandatory_visibility?.mandatory_commitment_ids).map(String),
      );
      state.today = state.portfolioModel.referenceDate || isoDate();
      state.anchorDate = state.today;
      translateStaticCopy();
      renderDesk();
      renderResourceCardBoxes();
      renderReadyStatus();
    } catch (error) {
      status(deskText("deskLocalProjectionCouldNot", { message: error.message }));
    }
  }

  // The desk's operations are exported so behaviour tests can drive them directly.
  global.ResearchOSUnifiedResearchDesk = Object.freeze({
    applyResourceCardBoxSearch,
    buildSession,
    closeDrawer,
    handoffAssetIds,
    init,
    placementItems,
    prepareCardEnhancement,
    prepareHandoff,
    projectionPayload,
    renderCardContent,
    renderDesk,
    renderItemLens,
    renderLifecycle,
    routeDecision,
    saveAttention,
    selectionFor,
    state,
    titleCard,
    toggleHandoffComponent,
    undoAttention,
  });

  if (global.document?.readyState === "loading") global.document.addEventListener("DOMContentLoaded", () => init());
  else init();
})(window);
