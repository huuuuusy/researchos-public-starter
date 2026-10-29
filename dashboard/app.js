/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端编排层；只保留状态汇合、副作用和重渲染调度，模板/规则/事件绑定下放到 src 模块。
 * English: ResearchOS dashboard frontend orchestrator; keeps state aggregation, side effects, and rerender scheduling while templates, rules, and event binding live in src modules.
 */

const I18N = window.ResearchOSI18N || {};
const UiCopy = window.ResearchOSUICopy || {};
const I18nRuntime = window.ResearchOSI18NRuntime;
const ThemeRuntime = window.ResearchOSTheme;
const I18N_OVERRIDES = UiCopy.i18nOverrides || {};
const SIMPLE_UI_TEXT = UiCopy.simpleText || {};
const PreviewService = window.ResearchOSPreviewService;
const PreviewContentClient = window.ResearchOSPreviewContentClient;
const PreviewMarkdownService = window.ResearchOSPreviewMarkdownService;
const PreviewFeedbackService = window.ResearchOSPreviewFeedbackService;
const FeedbackClient = window.ResearchOSFeedbackClient;
const PreviewFeedbackWorkflow = window.ResearchOSPreviewFeedbackWorkflow;
const PreviewDocumentsService = window.ResearchOSPreviewDocuments;
const PreviewState = window.ResearchOSPreviewState;
const PreviewSessionState = window.ResearchOSPreviewSessionState;
const PreviewSurfaceWorkbenchService = window.ResearchOSPreviewSurfaceWorkbenchService;
const PreviewPdfWorkbenchService = window.ResearchOSPreviewPdfWorkbenchService;
const PreviewWorkbenchService = window.ResearchOSPreviewWorkbenchService;
const UiCore = window.ResearchOSUiCore;
const escapeHtml = UiCore.escapeHtml;
const ClipboardWorkbenchService = window.ResearchOSClipboardWorkbenchService;
const AppCopyActionsService = window.ResearchOSAppCopyActionsService;
const Interactions = window.ResearchOSInteractions;
const StatePolicy = window.ResearchOSStatePolicy;
const StorageContract = window.ResearchOSStorageContract || {};
const ServiceMode = window.ResearchOSServiceMode;
const ActionContract = window.ResearchOSActionContract;
const ActionGatewayService = window.ResearchOSActionGateway;
const SurfaceContract = window.ResearchOSSurfaceContract;
const ViewState = window.ResearchOSViewState;
const UiPreferences = window.ResearchOSUiPreferences;
const WorkspaceRouting = window.ResearchOSWorkspaceRouting;
const InboxService = window.ResearchOSInboxService;
const PluginRuntime = window.ResearchOSPluginRuntime;
const AgentPromptService = window.ResearchOSAgentPromptService;
const MarkdownPreviewWorkbenchService = window.ResearchOSMarkdownPreviewWorkbenchService;
const ConfirmationState = window.ResearchOSConfirmationState;
const ConfirmationClient = window.ResearchOSConfirmationClient;
const ResultEnvelopeContract = window.ResearchOSResultEnvelope;
const RuntimeProfileProjection = window.ResearchOSRuntimeProfileProjection;
const CodexRunnerClient = window.ResearchOSCodexRunnerClient;
const ModelCatalogService = window.ResearchOSModelCatalog;
const CodexRunRouter = window.ResearchOSCodexRunRouter;
const DoingBoardState = window.ResearchOSDoingBoardState;
const WorkSessionClient = window.ResearchOSWorkSessionClient;
const WorkSessionRouter = window.ResearchOSWorkSessionRouter;
const WorkSessionState = window.ResearchOSWorkSessionState;
const ContextPackProjection = window.ResearchOSContextPackProjection;
const WorkSessionWorkbenchService = window.ResearchOSWorkSessionWorkbenchService;
const HandoffReceiptProjection = window.ResearchOSHandoffReceiptProjection;
const HandoffAdmitSurface = window.ResearchOSHandoffAdmitSurface;
const PaperFieldRules = window.ResearchOSPaperFieldRules;
const WorkspaceShellWorkbenchService = window.ResearchOSWorkspaceShellWorkbenchService;
const DashboardRenderPlan = window.ResearchOSDashboardRenderPlan;
const DashboardLifecycleAdapter = window.ResearchOSDashboardLifecycleAdapter;
const DashboardDataClient = window.ResearchOSDashboardDataClient;
const DailyProfileRefreshClient = window.ResearchOSDailyProfileRefreshClient;
const PreviewLinksComponent = window.ResearchOSPreviewLinksComponent;
const ButtonsComponent = window.ResearchOSButtonsComponent;
const MarkdownPreviewView = window.ResearchOSMarkdownPreviewView;
const PdfPreviewView = window.ResearchOSPdfPreviewView;
const ErrorPageView = window.ResearchOSErrorPageView;
const WorkSessionView = window.ResearchOSWorkSessionView;
const HomeCommandCenterView = window.ResearchOSHomeCommandCenterView;
const UnifiedInboxWorkbenchService = window.ResearchOSUnifiedInboxWorkbenchService;
const initialViewState = ViewState.read();
let initialPreviewState = PreviewState.read({ previewService: PreviewService });
const initialUiPreferences = UiPreferences.read();
const PREVIEW_STORAGE_KEYS = PreviewState.storageKeys;
const STORAGE_KEYS = StorageContract.storageKeys || {};
const ACTIVE_CONTEXT_PATHS = StorageContract.activeContextPaths || {};
let lang = initialUiPreferences.language;
let theme = initialUiPreferences.theme;
let dashboardData = null;
let previewFeedbackWorkflow = null;
let previewWorkbench = null;
let selectedUnfinishedKey = initialUiPreferences.selectedUnfinishedKey;
// A fresh page load always restores the current research state first. The
// Durable Work Session state remains available, while surface filters are
// ephemeral projections and the shell opens on Now.
let selectedWorkspaceTab = "now";
const DOING_STORAGE_KEY = STORAGE_KEYS.doingBoard || "researchos-doing-board";
const CONFIRMATION_STORAGE_KEY = STORAGE_KEYS.confirmationDecisions || "researchos-confirmation-decisions";
const PREVIEW_HISTORY_KEY = PREVIEW_STORAGE_KEYS.history;
const PREVIEW_HISTORY_INDEX_KEY = PREVIEW_STORAGE_KEYS.historyIndex;
const PREVIEW_FEEDBACK_STORAGE_KEY = STORAGE_KEYS.previewFeedbackInbox || "researchos-preview-feedback-inbox";
const CONFIRMATION_INBOX_PATH = ACTIVE_CONTEXT_PATHS.confirmations || "06_active_context/ui-confirmation-decisions.md";
const FEEDBACK_INBOX_PATH = ACTIVE_CONTEXT_PATHS.feedback || "06_active_context/ui-feedback-inbox.md";
const UNIFIED_INBOX_ARCHIVE_STORAGE_KEY = STORAGE_KEYS.unifiedInboxArchive || "researchos-unified-inbox-archive";
const UNIFIED_INBOX_ARCHIVE_RESOLVED_STORAGE_KEY = STORAGE_KEYS.unifiedInboxArchiveResolved || "researchos-unified-inbox-archive-resolved";
const PUBLIC_DEMO_VISIBLE_STORAGE_KEY = "researchos-public-demo-visible";
let selectedUnifiedInboxView = initialViewState.unifiedInboxView;
let selectedWorkFilter = "active";
let selectedLibraryLensIds = [];
let selectedExecutionItemId = "";
let selectedExecutionPanel = "work";
let lastUnavailableExecutionItemId = "";
const itemExecutionRequestGate = WorkSessionState.createLatestRequestGate();
const runnerRefreshRequestGate = WorkSessionState.createLatestRequestGate();
let codexRunnerRuns = [];
let codexRunnerProviderStatus = null;
let codexRunnerPollTimer = null;
const ModelCatalogController = ModelCatalogService.createController({
  client: CodexRunnerClient,
  onChange: () => WorkSessionWorkbenchService.renderPreservingInteraction(
    dashboardTarget("todayWorkSession"),
    () => renderDashboard(dashboardData),
    { resolveRoot: () => dashboardTarget("todayWorkSession") },
  ),
  onStatus: (key) => {
    const status = dashboardTarget("todayWorkSession")?.querySelector("[data-work-session-status]");
    if (status) status.textContent = simpleText(key);
  },
  publicStarter: () => isPublicStarterRuntime(),
  storage: localStorage,
});
let doingItems = loadDoingItems();
saveDoingItems();
let workSession = null;
let workSessionHistory = [];
let publicDemoVisible = localStorage.getItem(PUBLIC_DEMO_VISIBLE_STORAGE_KEY) !== "false";
let lastMutationReceipt = null;
const DASHBOARD_UI_VERSION = "20260816-two-surface-direct-v6";
const DEFAULT_SERVER_URL = ServiceMode.DEFAULT_SERVER_URL;
if (UiPreferences.needsUiVersionReset(DASHBOARD_UI_VERSION)) {
  const resetPreviewState = PreviewState.reset();
  initialPreviewState = resetPreviewState;
  selectedWorkspaceTab = ViewState.writeWorkspaceTab("now");
  selectedUnfinishedKey = "";
  UiPreferences.removeUnfinishedCurrent();
  UiPreferences.removeSelectedTask();
  ViewState.writeWorkspaceTab(selectedWorkspaceTab);
  UiPreferences.writeUiVersion(DASHBOARD_UI_VERSION);
}

function t(key) {
  return I18N_OVERRIDES?.[lang]?.[key]
    || I18N_OVERRIDES?.en?.[key]
    || I18nRuntime.translate(I18N, lang, key);
}

const AppCopyActions = AppCopyActionsService.createAppCopyActions({
  buttonsComponent: ButtonsComponent,
  clipboardWorkbenchService: ClipboardWorkbenchService,
  translate: t,
  uiCore: UiCore,
});
const copyEncodedPayload = AppCopyActions.copyEncodedPayload;
const copyPlainText = AppCopyActions.copyPlainText;
const copyValueButton = AppCopyActions.copyValueButton;
function shortText(value, limit = 72) {
  const text = String(value || "").trim();
  if (text.length <= limit) return text;
  return `${text.slice(0, Math.max(0, limit - 1)).trim()}…`;
}

function activeTemplateLanguage(data = dashboardData) { return DashboardRenderPlan.activeTemplateLanguage(data); }

const WorkSessionLifecycle = WorkSessionWorkbenchService.createWorkSessionLifecycle({
  addDoingItem,
  allowSessionAction: (session, action) => workSessionActionAllowed(session, action),
  archiveHandoff: archiveUnifiedInboxEntryFromUi,
  completeWorkItemProject: (session) => dispatchBoundWorkItemAction(session, "completeProjectActionId"),
  completeWorkItemStep: (session) => dispatchBoundWorkItemAction(session, "completeStepActionId", { confirmed: true }),
  confirmDeleteHistory: () => window.confirm(simpleText("workSessionConfirmDeleteHistory")),
  confirmNew: () => window.confirm(simpleText("workSessionConfirmNew")),
  confirmSwitchHistory: () => window.confirm(simpleText("workSessionConfirmSwitchHistory")),
  decodePayload: UiCore.decodeDataPayload,
  getDoingItems: () => doingItems,
  getHistory: () => workSessionHistory,
  getResult: () => WorkSessionRouter.resultForSession(codexRunnerRuns, workSession || {}),
  getSession: () => workSession,
  openWorkspace: (surface, options = {}) => {
    const route = SurfaceContract.surfaceRoute?.(surface) || {};
    if (route.panel) return openItemExecutionDrawer(selectedExecutionItemId, route.panel, { focus: Boolean(options.scroll) });
    return setWorkspaceTab(surface, options);
  },
  openItemPanel: (panel = "work") => openItemExecutionDrawer(selectedExecutionItemId, panel, { focus: true }),
  executionAvailable: () => localExecutionAvailable(),
  openLocalFile: (path) => ServiceMode.isServerMode(location)
    ? WorkSessionClient.openLocalFile(path)
    : Promise.resolve({ ok: false, message: "local service unavailable" }),
  publicMode: () => isPublicStarterRuntime(),
  refreshSurfaces: refreshWorkSessionSurfaces,
  removeDoingItem,
  renderHome: () => renderHomeCommandCenter(dashboardData?.home_command_center || {}),
  reconcileSession: (session) => reconcileWorkSessionRun(session),
  saveSession: (session) => {
    workSession = WorkSessionState.write(session, { runtimeMode: dashboardData?.runtime_mode || "private" });
    return workSession;
  },
  saveHistory: (history) => {
    workSessionHistory = WorkSessionState.writeHistory(history, { runtimeMode: dashboardData?.runtime_mode || "private" });
    return workSessionHistory;
  },
  copyResult: (result) => WorkSessionClient.copyResult(result, {
    statusTarget: dashboardTarget("todayWorkSession")?.querySelector("[data-work-session-status]"),
    successMessage: simpleText(workSessionExecutionRoute().mode === "copy_only" ? "workSessionPacketCopied" : "workSessionResultCopied"),
  }),
  copyTask: (session) => copyWorkSessionTaskPacket(session),
  scheduleInboxStatus: UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus,
  showStatus: (message) => {
    const status = dashboardTarget("todayWorkSession")?.querySelector("[data-work-session-status]");
    if (status) status.textContent = message;
  },
  submitSession: (session, options) => submitWorkSessionRun(session, options),
  templateLanguage: () => lang || activeTemplateLanguage(),
  uploadFile: (file) => WorkSessionClient.uploadSourceFile(file),
}, {
  inboxStatusIsActive: InboxService.inboxStatusIsActive,
  itemKey: DoingBoardState.itemKey,
  router: WorkSessionRouter,
  state: WorkSessionState,
  translate: simpleText,
});

const pluginHost = window.ResearchOSPluginHost.createPluginHost(() => ({
  codexRunnerRuns,
  data: dashboardData,
  lang,
  lastMutationReceipt,
  publicDemoVisible,
  selectedLibraryLensIds,
  selectedWorkspaceTab,
  workSessionHistory,
  setLibraryLensIds: (ids) => { selectedLibraryLensIds = ids; },
  setPublicDemoVisible: (visible) => {
    publicDemoVisible = Boolean(visible);
    localStorage.setItem(PUBLIC_DEMO_VISIBLE_STORAGE_KEY, publicDemoVisible ? "true" : "false");
  },
  setWorkFilter: (filter) => { selectedWorkFilter = ViewState.normalizeWorkFilter(filter); },
  undoLastMutation: async () => {
    if (!lastMutationReceipt?.undo) return { ok: false, message: "undo unavailable" };
    const result = await WorkSessionClient.undoMutation(lastMutationReceipt.undo);
    if (result?.ok) {
      lastMutationReceipt = null;
      dashboardData = await loadDashboard();
      renderDashboard(dashboardData);
    }
    return result;
  },
  addDoingItem,
  bindPreviewButtons,
  collectUnifiedInboxEntries,
  copyPlainText,
  currentContextPackProjection,
  dashboardTarget,
  dispatchPluginAction,
  durableWorkItemMutationAvailable,
  escapeHtml,
  focusDashboardSection,
  getPreviewDoc,
  isPublicStarterRuntime,
  loadDashboard,
  localExecutionAvailable,
  openItemExecutionDrawer,
  openMarkdownPreview,
  openWorkspaceOrItemPanel,
  previewDocuments,
  previewWorkbenchController,
  registeredMaintenanceAvailable,
  renderDashboard,
  renderServiceModeBanner,
  setWorkspaceTab,
  simpleText,
  t,
  workSessionForDisplay,
  workSessionLifecycle: WorkSessionLifecycle,
}));

function refreshWorkSessionSurfaces() {
  renderHomeCommandCenter(dashboardData?.home_command_center || {});
  renderUnifiedInbox();
  renderPluginLibrarySlots(dashboardData);
  syncVisibleHandoffCounts();
}

async function loadDashboard() {
  return DashboardDataClient.loadDashboardData();
}

function renderServiceModeBanner() {
  ServiceMode.updateServiceModeBanner({
    banner: WorkspaceShellWorkbenchService.dashboardChromeNodes(document).serviceModeBanner,
    config: dashboardData?.config || {},
    defaultServerUrl: DEFAULT_SERVER_URL,
    documentElement: document.documentElement,
    locationLike: location,
  });
}

function applyTranslations() {
  I18nRuntime.applyTranslations({
    language: lang,
    translateText: t,
    onAfterApply: renderServiceModeBanner,
  });
}

function applyTheme() {
  theme = ThemeRuntime.applyTheme(theme);
}

function setupThemePicker() {
  ThemeRuntime.setupThemePicker({
    root: WorkspaceShellWorkbenchService.dashboardChromeNodes(document).themePicker,
    selectedTheme: theme,
    translate: t,
    onSelect: (themeId) => {
      theme = themeId;
      UiPreferences.writeTheme(theme);
      applyTheme();
      setupThemePicker();
    },
  });
}

function setupLanguageSelect(data) {
  const select = WorkspaceShellWorkbenchService.dashboardChromeNodes(document).languageSelect;
  const languages = data.config?.available_languages || ["zh-CN", "en"];
  I18nRuntime.setupLanguageSelect({
    select,
    languages,
    selectedLanguage: lang,
    onChange: (language) => {
      const workSessionRoot = dashboardTarget("todayWorkSession");
      if (WorkSessionWorkbenchService.captureInteraction(workSessionRoot)?.hasSelectedFile) {
        select.value = lang;
        const status = workSessionRoot?.querySelector("[data-work-session-status]");
        if (status) status.textContent = simpleText("workSessionLanguageBlockedByFile");
        return;
      }
      lang = language;
      UiPreferences.writeLanguage(lang);
      WorkSessionWorkbenchService.renderPreservingInteraction(
        workSessionRoot,
        () => renderDashboard(dashboardData),
        { resolveRoot: () => dashboardTarget("todayWorkSession") },
      );
    },
  });
}

function previewDocuments() {
  return dashboardData?.preview_documents || [];
}

function isPublicStarterRuntime(data = dashboardData) {
  return DashboardRenderPlan.isPublicStarterRuntime(data);
}

function durableWorkItemMutationAvailable(data = dashboardData) {
  return ActionContract.durableMutationAvailable({
    publicStarter: isPublicStarterRuntime(data),
    runtimeMode: data?.runtime_mode,
    serverMode: ServiceMode.isServerMode(location),
  });
}

function workSessionForDisplay(session = workSession) {
  const demoHidden = isPublicStarterRuntime() && !publicDemoVisible;
  return demoHidden && WorkSessionState.isPublicDemoSession?.(session) ? null : session;
}

function currentContextPackProjection() {
  return ContextPackProjection.project(workSessionForDisplay(), {
    previewDocuments: previewDocuments(),
    publicStarter: isPublicStarterRuntime(),
    runtimeMode: dashboardData?.runtime_mode || "private",
  });
}

function workSessionHistoryForDisplay() {
  if (!isPublicStarterRuntime() || publicDemoVisible) return workSessionHistory;
  return workSessionHistory.filter((session) => !WorkSessionState.isPublicDemoSession?.(session));
}

function workSessionHistoryForFilter(filter = selectedWorkFilter) {
  const history = workSessionHistoryForDisplay().filter((entry) => (
    !selectedExecutionItemId || String(entry?.portfolioBinding?.itemId || "") === selectedExecutionItemId
  ));
  const normalizedFilter = ViewState.normalizeWorkFilter(filter);
  if (normalizedFilter === "all") return history;
  const stateBySessionId = new Map(WorkSessionState.sessionRegistryProjection(
    workSessionForDisplay(),
    history,
    codexRunnerRuns,
  ).map((entry) => [entry.session_id, entry.work_state]));
  return history.filter((entry) => stateBySessionId.get(String(entry?.id || "")) === normalizedFilter);
}

function executionRuntime(data = dashboardData) {
  const profile = RuntimeProfileProjection.normalize(codexRunnerProviderStatus?.runtime_profile);
  const localProfile = profile?.status === "configured"
    && profile.enabled === true
    && profile.adapter_family === "local_codex"
    && profile.verification_state === "local_probe_passed";
  return ActionContract.runtimeCapabilities({
    executionAvailable: localProfile && codexRunnerProviderStatus?.execution_available === true,
    executionProbeRequired: true,
    executionScope: localProfile ? profile.execution_scope : "none",
    providerMode: localProfile ? "local_codex" : "disabled",
    serverMode: ServiceMode.isServerMode(location),
  });
}
const localExecutionAvailable = (data) => executionRuntime(data).localExecution;
const workspaceWriteAvailable = (data) => executionRuntime(data).workspaceWrite;
const registeredMaintenanceAvailable = (data) => executionRuntime(data).registeredMaintenance;
const workSessionExecutionRoute = (data) => ActionContract.executionRoute({
  localExecution: localExecutionAvailable(data),
  publicStarter: isPublicStarterRuntime(data),
});

function previewFeedbackWorkflowController() {
  if (previewFeedbackWorkflow) return previewFeedbackWorkflow;
  previewFeedbackWorkflow = PreviewFeedbackWorkflow.createPreviewFeedbackWorkflow({
    feedbackStorageKey: PREVIEW_FEEDBACK_STORAGE_KEY,
    services: {
      feedback: PreviewFeedbackService,
      feedbackClient: FeedbackClient,
    },
    simpleText,
  });
  return previewFeedbackWorkflow;
}

function previewWorkbenchController() {
  if (previewWorkbench) return previewWorkbench;
  previewWorkbench = PreviewWorkbenchService.createPreviewWorkbench({
    escapeHtml,
    getDocuments: previewDocuments,
    historyIndexKey: PREVIEW_HISTORY_INDEX_KEY,
    historyKey: PREVIEW_HISTORY_KEY,
    initialState: initialPreviewState,
    onBindTooltips: bindButtonTooltips,
    onFeedbackSaved: () => {
      renderUnifiedInbox();
    },
    paths: {
      confirmation: CONFIRMATION_INBOX_PATH,
      feedback: FEEDBACK_INBOX_PATH,
      candidates: pluginCandidateSources(),
    },
    services: {
      contentClient: PreviewContentClient,
      documents: PreviewDocumentsService,
      feedback: PreviewFeedbackService,
      feedbackWorkflow: previewFeedbackWorkflowController(),
      markdown: PreviewMarkdownService,
      markdownView: MarkdownPreviewView,
      markdownWorkbench: MarkdownPreviewWorkbenchService,
      pdfWorkbench: PreviewPdfWorkbenchService,
      pdfView: PdfPreviewView,
      preview: PreviewService,
      sessionState: PreviewSessionState,
      state: PreviewState,
      surfaceWorkbench: PreviewSurfaceWorkbenchService,
    },
    simpleText,
    translate: t,
  });
  return previewWorkbench;
}

function getPreviewDoc(path) {
  return previewWorkbenchController().getPreviewDoc(path);
}

async function openMarkdownPreview(path, options = {}) {
  return previewWorkbenchController().openMarkdownPreview(path, options);
}

async function openMarkdownPreviewCards(paths = []) {
  const previewablePaths = [...new Set((Array.isArray(paths) ? paths : [])
    .map((path) => String(path || "").trim())
    .filter((path) => path && getPreviewDoc(path)))];
  for (let index = 0; index < previewablePaths.length; index += 1) {
    await openMarkdownPreview(previewablePaths[index], { scrollPanel: index === previewablePaths.length - 1 });
  }
  return previewablePaths;
}

function renderMarkdownPreview() {
  return previewWorkbenchController().renderMarkdownPreview();
}

function bindPreviewButtons(root = document) {
  return previewWorkbenchController().bindPreviewButtons(root);
}

function bindPreviewHistoryNavigation() {
  return previewWorkbenchController().bindPreviewHistoryNavigation();
}

function ensureSelectedPreviewLoaded() {
  return previewWorkbenchController().ensureSelectedPreviewLoaded();
}

function focusDashboardSection(targetId) {
  if (!targetId) return;
  const workspace = WorkspaceRouting.workspaceForTarget(targetId);
  if (workspace) {
    setWorkspaceTab(targetId === "unifiedInbox" ? "review" : workspace);
  }
  WorkspaceShellWorkbenchService.focusDashboardTarget(document, targetId, {
    focusClass: "section-focus",
    focusTimeout: 1400,
  });
}

function bindSectionJumpButtons(root = document) {
  Interactions.applySectionJumpButtons(root, focusDashboardSection);
}
function bindButtonTooltips(root = document) {
  Interactions.applyButtonTooltips(root, simpleText);
}
function bindInteractiveSurfaces(root = document) {
  Interactions.applyInteractiveSurfaces(root, { translate: simpleText, escapeHtml });
}
function bindDashboardButtonTooltips() {
  bindButtonTooltips(document);
}
function bindDashboardInteractiveSurfaces() {
  bindInteractiveSurfaces(document);
}
function applyDashboardHeader(header = {}) {
  WorkspaceShellWorkbenchService.applyDashboardHeader(document, header);
}
function setWorkspaceTab(tabId, options = {}) {
  const route = SurfaceContract.surfaceRoute?.(tabId) || { filter: "", surface: SurfaceContract.canonicalSurface(tabId) };
  selectedWorkspaceTab = ViewState.writeWorkspaceTab(route.surface || "now");
  if (route.filter) selectedWorkFilter = ViewState.normalizeWorkFilter(route.filter);
  syncVisibleHandoffCounts();
  if (selectedWorkspaceTab === "library" && previewWorkbench) {
    previewWorkbench.setPreviewOpen(false);
    previewWorkbench.renderMarkdownPreview();
  }
  WorkspaceShellWorkbenchService.syncWorkspaceShell(document, {
    focusMode: options.focusMode || (options.scroll ? "panel" : "none"),
    hintFor: (tab) => t(`${SurfaceContract.workspaceI18nKey(tab)}Hint`),
    labelFor: (tab) => t(SurfaceContract.workspaceI18nKey(tab)),
    scroll: Boolean(options.scroll),
    selectedWorkspace: selectedWorkspaceTab,
  });
  if (route.panel) openItemExecutionDrawer(route.item || "", route.panel, { focus: Boolean(options.scroll) });
}
function syncVisibleHandoffCounts() {
  if (!dashboardData) return;
  const total = collectUnifiedInboxEntries().total;
  document.querySelectorAll("[data-unified-handoff-count]").forEach((node) => {
    node.textContent = String(total);
  });
}
function dashboardTarget(targetId) {
  return WorkspaceShellWorkbenchService.dashboardTarget(document, targetId);
}

function executionWorkItems() {
  return PluginRuntime.workItemProviderModels(dashboardData)
    .flatMap((provider) => Array.isArray(provider?.projection?.items) ? provider.projection.items : []);
}

function executionItem(itemId = selectedExecutionItemId) {
  const normalized = String(itemId || "").trim();
  return normalized ? executionWorkItems().find((item) => String(item?.id || "") === normalized) || null : null;
}

function workSessionContextStatus(session = executionSessionForDisplay(), item = null) {
  const binding = session?.portfolioBinding || {};
  if (!binding.itemId) return "unbound";
  const currentItem = item || executionItem(binding.itemId);
  if (!currentItem || String(currentItem.id || "") !== String(binding.itemId || "")) return "missing";
  return WorkSessionState.portfolioBindingContextStatus?.(currentItem, binding) || "unknown";
}

function workSessionActionAllowed(session = {}, action = "") {
  const binding = session?.portfolioBinding || {};
  if (!binding.itemId) return true;
  if (["copy_result", "end_session", "new_session", "open_file", "view"].includes(String(action || ""))) return true;
  return workSessionContextStatus(session) === "current";
}

function executionSessionForDisplay() {
  const current = workSessionForDisplay();
  return selectedExecutionItemId && String(current?.portfolioBinding?.itemId || "") === selectedExecutionItemId ? current : null;
}

async function draftExecutionItemSession(itemId = selectedExecutionItemId) {
  const item = executionItem(itemId);
  if (!item || !ResearchPortfolioWorkbench?.createActions) return { ok: false, reason: "item_unavailable" };
  const requestToken = itemExecutionRequestGate.begin(item.id);
  const preparePrompt = ResearchPortfolioWorkbench.createActions({
    defaultSourceHint: item.sourcePath || "08_exports/public_starter/demo-research-agenda.md",
    draftWorkSession: WorkSessionLifecycle.draft,
    text: simpleText,
    titleSeparator: isPublicStarterRuntime() ? ": " : "：",
  }).preparePrompt;
  const request = item.actionPrompt || item.nextStep || item.next_step || "";
  if (!request) return { ok: false, reason: "next_step_unavailable" };
  const result = await Promise.resolve(preparePrompt(request, item, "now"));
  if (result?.ok && itemExecutionRequestGate.isCurrent(requestToken, selectedExecutionItemId)) {
    renderWorkSessionSurface(dashboardData?.home_command_center || {});
    renderUnifiedInbox();
    syncItemExecutionDrawer();
  }
  return result || { ok: false };
}

function syncItemExecutionDrawer() {
  const drawer = document.querySelector("[data-item-execution-drawer]");
  if (!drawer) return;
  const item = executionItem();
  const summary = drawer.querySelector("[data-execution-item-summary]");
  const identity = drawer.querySelector("[data-execution-item-identity]");
  const panelLabel = drawer.querySelector("[data-execution-panel-label]");
  const tabs = drawer.querySelector("[data-execution-tabs]");
  const workPanel = dashboardTarget("workSessionSurface");
  const reviewPanel = dashboardTarget("unifiedInbox");
  drawer.dataset.executionPanel = selectedExecutionPanel;
  drawer.dataset.executionItemId = selectedExecutionItemId;
  if (panelLabel) panelLabel.textContent = simpleText(selectedExecutionPanel === "review" ? "itemExecutionReviewTab" : "itemExecutionWorkTab");
  if (tabs) {
    tabs.hidden = !item;
    tabs.setAttribute("aria-label", simpleText("itemExecutionTabsLabel"));
    tabs.querySelectorAll("[data-execution-tab]").forEach((tab) => {
      const panel = tab.dataset.executionTab === "review" ? "review" : "work";
      const selected = item && panel === selectedExecutionPanel;
      tab.textContent = simpleText(panel === "review" ? "itemExecutionReviewTab" : "itemExecutionWorkTab");
      tab.setAttribute("aria-selected", selected ? "true" : "false");
      tab.tabIndex = selected ? 0 : -1;
    });
    if (!tabs.dataset.bound) {
      tabs.dataset.bound = "true";
      tabs.addEventListener("click", (event) => {
        const tab = event.target?.closest?.("[data-execution-tab]");
        if (!tab || !selectedExecutionItemId) return;
        openItemExecutionDrawer(selectedExecutionItemId, tab.dataset.executionTab, { focus: true });
      });
      tabs.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
        const ordered = [...tabs.querySelectorAll("[data-execution-tab]")];
        const currentIndex = Math.max(0, ordered.indexOf(event.target));
        event.preventDefault();
        ordered[(currentIndex + (event.key === "ArrowRight" ? 1 : -1) + ordered.length) % ordered.length]?.click();
      });
    }
  }
  if (workPanel) workPanel.hidden = !item || selectedExecutionPanel !== "work";
  if (reviewPanel) reviewPanel.hidden = !item || selectedExecutionPanel !== "review";
  if (!item) {
    if (summary) summary.textContent = lastUnavailableExecutionItemId
      ? (lang === "zh-CN"
        ? `未找到事项“${lastUnavailableExecutionItemId}”；已清除失效链接，请从 Now 或 Library 重新选择。`
        : `Item “${lastUnavailableExecutionItemId}” was not found. The stale link was cleared; select it again from Now or Library.`)
      : (lang === "zh-CN"
        ? "请选择一个明确事项；系统不会猜测当前项目，公开版也不会启用长期写入。"
        : "Select an exact item. The system will not guess a current project, and Public never enables durable mutation.");
    if (identity) {
      identity.hidden = true;
      identity.textContent = "";
    }
    return;
  }
  const binding = executionSessionForDisplay();
  const contextStatus = binding ? workSessionContextStatus(binding, item) : "unbound";
  drawer.dataset.executionContextStatus = contextStatus;
  const staleWarning = contextStatus === "stale"
    ? (lang === "zh-CN"
      ? "该 Work Session 使用旧的事项上下文，现已只读；请从当前事项新建任务后再执行。"
      : "This Work Session uses an older item context and is now read only. Start a new task from the current item before taking action.")
    : contextStatus === "unknown" && binding
      ? (lang === "zh-CN"
        ? "该 Work Session 建立于上下文版本跟踪之前，现按只读处理；请从当前事项新建任务。"
        : "This Work Session predates context revision tracking and is treated as read only. Start a new task from the current item.")
      : "";
  if (summary) summary.textContent = [item.title || item.id, item.next_step || item.nextStep || "", staleWarning].filter(Boolean).join(" · ");
  if (identity) {
    identity.hidden = false;
    identity.textContent = [
      `item: ${item.id}`,
      binding?.id ? `session: ${binding.id}` : "No Work Session yet",
      binding?.latestRunId ? `run: ${binding.latestRunId}` : "",
      contextStatus === "stale" ? (lang === "zh-CN" ? "context: 已过期" : "context: stale") : "",
      contextStatus === "unknown" && binding ? (lang === "zh-CN" ? "context: 未核验" : "context: unverified") : "",
      "Public: copy-only / in-memory",
    ].filter(Boolean).join(" · ");
  }
}

function writeItemExecutionRoute(itemId = "", panel = "work", options = {}) {
  if (!globalThis.history || !globalThis.location?.href || options.syncRoute === false) return;
  const routeUrl = new URL(globalThis.location.href);
  if (itemId) {
    routeUrl.searchParams.set("item", itemId);
    routeUrl.searchParams.set("panel", panel === "review" ? "review" : "work");
  } else {
    routeUrl.searchParams.delete("item");
    routeUrl.searchParams.delete("panel");
  }
  const nextRoute = `${routeUrl.pathname}${routeUrl.search}${routeUrl.hash}`;
  const currentRoute = `${globalThis.location.pathname}${globalThis.location.search}${globalThis.location.hash}`;
  if (nextRoute === currentRoute) return;
  const method = options.replaceRoute ? "replaceState" : "pushState";
  globalThis.history[method]?.(globalThis.history.state, "", nextRoute);
}

function openItemExecutionDrawer(itemId = "", panel = "work", options = {}) {
  itemExecutionRequestGate.invalidate();
  const requestedItem = executionItem(itemId);
  lastUnavailableExecutionItemId = requestedItem ? "" : String(itemId || "").trim();
  selectedExecutionItemId = requestedItem ? String(requestedItem.id) : "";
  selectedExecutionPanel = panel === "review" ? "review" : "work";
  selectedWorkFilter = selectedExecutionPanel === "review" ? "needs_review" : "active";
  writeItemExecutionRoute(selectedExecutionItemId, selectedExecutionPanel, options);
  renderWorkSessionSurface(dashboardData?.home_command_center || {});
  renderUnifiedInbox();
  syncItemExecutionDrawer();
  const drawer = document.querySelector("[data-item-execution-drawer]");
  if (!drawer) return false;
  if (!drawer.dataset.routeBound) {
    drawer.dataset.routeBound = "true";
    drawer.addEventListener("toggle", () => {
      if (drawer.open || !selectedExecutionItemId) return;
      selectedExecutionItemId = "";
      selectedExecutionPanel = "work";
      selectedWorkFilter = "active";
      writeItemExecutionRoute("", "work");
      renderWorkSessionSurface(dashboardData?.home_command_center || {});
      renderUnifiedInbox();
      syncItemExecutionDrawer();
    });
  }
  drawer.open = true;
  if (options.focus) {
    globalThis.setTimeout?.(() => {
      const target = requestedItem
        ? dashboardTarget(selectedExecutionPanel === "review" ? "unifiedInbox" : "workSessionSurface")
        : drawer.querySelector("summary");
      target?.setAttribute?.("tabindex", "-1");
      target?.focus?.({ preventScroll: true });
      Interactions.scrollIntoView?.(target || drawer, { behavior: "smooth", block: "start" });
    }, 0);
  }
  return Boolean(requestedItem);
}

function openWorkspaceOrItemPanel(surface = "now", options = {}) {
  const route = SurfaceContract.surfaceRoute?.(surface) || {};
  if (!route.panel) return setWorkspaceTab(surface, options);
  const lensItemId = selectedLibraryLensIds.length === 1 ? selectedLibraryLensIds[0] : "";
  return openItemExecutionDrawer(route.item || selectedExecutionItemId || lensItemId, route.panel, { focus: Boolean(options.scroll) });
}

function applyInitialSurfaceRequest(options = {}) {
  const params = new URLSearchParams(globalThis.location?.search || "");
  const requestedSurface = params.get("surface") || params.get("workspace") || params.get("view") || "";
  const requestedPanel = params.get("panel") || "";
  const requestedItem = params.get("item") || "";
  if (!requestedSurface && !requestedPanel && !requestedItem) {
    if (options.historyNavigation) {
      selectedExecutionItemId = "";
      selectedExecutionPanel = "work";
      selectedWorkFilter = "active";
      lastUnavailableExecutionItemId = "";
      setWorkspaceTab("now", { scroll: false });
      renderWorkSessionSurface(dashboardData?.home_command_center || {});
      renderUnifiedInbox();
      const drawer = document.querySelector("[data-item-execution-drawer]");
      if (drawer) drawer.open = false;
      syncItemExecutionDrawer();
    }
    return;
  }
  const route = SurfaceContract.surfaceRoute?.(requestedSurface || "now") || {};
  const panel = ["work", "review"].includes(requestedPanel) ? requestedPanel : route.panel || "";
  if (panel) {
    setWorkspaceTab("now", { scroll: false });
    openItemExecutionDrawer(requestedItem || route.item || "", panel, { focus: true, replaceRoute: true });
    return;
  }
  setWorkspaceTab(route.surface || requestedSurface || "now", { scroll: false });
}

globalThis.addEventListener?.("popstate", () => applyInitialSurfaceRequest({ historyNavigation: true }));

const PluginActionGateway = ActionGatewayService?.create({
  authorize: ({ spec }) => {
    if (["mutate_attention", "mutate_canonical"].includes(spec?.effect)) {
      return durableWorkItemMutationAvailable()
        ? { allowed: true }
        : { allowed: false, reason: "durable_mutation_unavailable" };
    }
    return ["execute_bounded", "propose_writeback"].includes(spec?.effect)
      ? { allowed: false, reason: "privileged_action_migration_required" }
      : { allowed: true };
  },
  confirm: ({ input }) => window.confirm(String(input?.confirmationMessage || simpleText("workSessionCompleteProjectBody"))),
  interactionContract: window.ResearchOSInteractionContract,
});
if (PluginActionGateway) PluginRuntime?.configureActionGateway?.(PluginActionGateway);

async function dispatchPluginAction(request = {}) {
  const receipt = await (PluginRuntime?.dispatchAction?.({
    ...request,
    context: Object.freeze({ copyPlainText, language: lang }),
    data: dashboardData,
  }) || Promise.resolve({ ok: false, reason: "action_gateway_unavailable", status: "rejected" }));
  if (receipt?.ok && receipt?.outcome?.projection_refresh_required) {
    const presentation = receipt.outcome.presentation_receipt || {};
    lastMutationReceipt = {
      itemId: String(presentation.itemId || ""),
      message: String(presentation.message || ""),
      viewToday: Boolean(presentation.viewToday),
      workspace: SurfaceContract.canonicalSurface(presentation.workspace || selectedWorkspaceTab) || "now",
      undo: receipt.outcome.undo || presentation.undo || null,
    };
    dashboardData = await loadDashboard();
    renderDashboard(dashboardData);
  }
  return receipt;
}

function dispatchBoundWorkItemAction(session = {}, actionField = "", options = {}) {
  const binding = session?.portfolioBinding || {};
  const pluginId = String(binding.pluginId || binding.providerId || "").trim();
  const actionId = String(binding[actionField] || PluginRuntime?.workItemActionId?.(pluginId, actionField) || "").trim();
  if (!pluginId || !actionId || !binding.itemId) return Promise.resolve({ ok: false, reason: "work_item_action_unavailable" });
  if (!workSessionActionAllowed(session, actionField)) return Promise.resolve({ ok: false, reason: "stale_context" });
  return dispatchPluginAction({
    actionId,
    confirmed: options.confirmed === true,
    input: { binding, confirmationMessage: simpleText("workSessionCompleteProjectBody") },
    pluginId,
  });
}

// The lifecycle adapter resolves these two render callbacks by name on window; dashboardData is their default.
function renderPluginSlots(data = dashboardData) {
  pluginHost.renderUtilitySlots(data);
}

function renderPluginLibrarySlots(data = dashboardData) {
  pluginHost.renderLibrarySlots(data);
}

function bindWorkspaceTabs() {
  WorkspaceShellWorkbenchService.bindWorkspaceTabs(document, {
    onWorkspaceTab: ({ focusMode, scroll, tabId }) => setWorkspaceTab(tabId || "now", {
      focusMode: focusMode || "tab",
      scroll: Boolean(scroll),
    }),
  });
  WorkspaceShellWorkbenchService.bindAssetDetailLauncher(document, {
    onAssetDetail: ({ detail }) => focusDashboardSection(detail || "assetOverview"),
  });
  setWorkspaceTab(selectedWorkspaceTab);
}

window.setResearchOSWorkspaceTab = setWorkspaceTab;

function simpleText(key) { return simpleTextForLanguage(key, lang); }
function simpleTextForLanguage(key, language = lang) {
  return (SIMPLE_UI_TEXT[language] || SIMPLE_UI_TEXT.en)[key] || SIMPLE_UI_TEXT.en[key] || key;
}

function loadConfirmationDecisions() {
  return ConfirmationState.loadConfirmationDecisions({ statePolicy: StatePolicy, storageKey: CONFIRMATION_STORAGE_KEY });
}

function mergedConfirmationDecisions(graph = dashboardData?.asset_graph || {}) {
  return ConfirmationState.mergeConfirmationDecisions(
    graph?.submitted_confirmation_decisions || {},
    loadConfirmationDecisions()
  );
}

function saveConfirmationDecisions(decisions = {}) {
  return ConfirmationState.saveConfirmationDecisions(decisions, { statePolicy: StatePolicy, storageKey: CONFIRMATION_STORAGE_KEY });
}
function deleteConfirmationDecision(decisionId) {
  return ConfirmationState.deleteConfirmationDecision(decisionId, { statePolicy: StatePolicy, storageKey: CONFIRMATION_STORAGE_KEY });
}

async function withdrawConfirmationDecision(decisionId) {
  deleteConfirmationDecision(decisionId);
  return ConfirmationClient.withdrawConfirmationPayload(decisionId);
}
function saveResolvedClearedInboxItems(serverState, serverKey = "", localItems = [], saveItems = () => {}) {
  const resolution = InboxService.resolveClearedInboxItems({
    localItems,
    serverKey,
    serverState,
  });
  if (resolution.shouldSave) saveItems(resolution.items);
  return resolution;
}

function loadUnifiedInboxArchive() {
  return InboxService.loadUnifiedInboxArchive(UNIFIED_INBOX_ARCHIVE_STORAGE_KEY);
}

function saveUnifiedInboxArchive(records = {}) {
  InboxService.saveUnifiedInboxArchive(records, UNIFIED_INBOX_ARCHIVE_STORAGE_KEY);
}

function loadUnifiedInboxResolvedArchive() {
  return InboxService.loadUnifiedInboxArchive(UNIFIED_INBOX_ARCHIVE_RESOLVED_STORAGE_KEY);
}

function saveUnifiedInboxResolvedArchive(records = {}) {
  InboxService.saveUnifiedInboxArchive(records, UNIFIED_INBOX_ARCHIVE_RESOLVED_STORAGE_KEY);
}

function restoreUnifiedInboxEntry(type = "", id = "") {
  return InboxService.restoreUnifiedInboxEntry({
    storageKey: UNIFIED_INBOX_ARCHIVE_STORAGE_KEY,
    type,
    id,
  });
}

function collectUnifiedInboxEntries(options = {}) {
  const pluginCandidates = PluginRuntime.collectCandidateEntries({
    data: dashboardData,
    context: pluginHost.runtimeContext(),
  });
  return InboxService.collectUnifiedInboxEntries(
    {
      archive: loadUnifiedInboxArchive(),
      candidateEntries: pluginCandidates.entries,
      candidateSourceEntries: pluginCandidates.sourceEntries,
      confirmationDecisions: mergedConfirmationDecisions(dashboardData?.asset_graph || {}),
      doingItems,
      previewFeedbackItems: previewFeedbackWorkflowController().loadPreviewFeedbackItems(),
      resolvedArchive: loadUnifiedInboxResolvedArchive(),
      view: options?.view || selectedUnifiedInboxView,
    },
    {
      confirmationChoiceLabel: (choice = "") => ConfirmationState.confirmationChoiceLabel(choice, simpleText),
      doingKey: DoingBoardState.itemKey,
      doingTypeLabel: (type = "") => DoingBoardState.typeLabel(type, simpleText),
      paperFieldSummary: (fields = {}) => PaperFieldRules.paperFieldSummary(fields, simpleText),
      paths: {
        confirmation: CONFIRMATION_INBOX_PATH,
        feedback: FEEDBACK_INBOX_PATH,
      },
      text: simpleText,
    }
  );
}

function pluginCandidateSources() {
  return PluginRuntime.collectCandidateEntries({
    data: dashboardData,
    context: pluginHost.runtimeContext(),
  }).sourceEntries;
}

async function withdrawUnifiedInboxEntry(type = "", id = "") {
  const restored = restoreUnifiedInboxEntry(type, id);
  const pluginResult = await PluginRuntime.runCandidateAction({
    action: "withdraw",
    candidateType: type,
    context: pluginHost.runtimeContext(),
    data: dashboardData,
    id,
  });
  const result = pluginResult.handled ? pluginResult : await InboxService.withdrawUnifiedInboxEntry({
    handlers: {
      confirmation: (entryId) => withdrawConfirmationDecision(entryId),
      paper_field_update: (entryId) => removeDoingItem(entryId),
      preview_feedback: (entryId) => previewFeedbackWorkflowController().removePreviewFeedbackItem(entryId),
      task: (entryId) => removeDoingItem(entryId),
    },
    id,
    restore: () => restored,
    type,
  });
  if (!result.handled) return;
  WorkSessionLifecycle.syncHandoffStatus(type, id, "active");
  renderDashboard(dashboardData);
  UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus(simpleText("unifiedInboxWithdrawn"));
}

function archiveUnifiedInboxEntryFromUi(type = "", id = "") {
  if (!InboxService.archiveUnifiedInboxEntryFromInbox({
    inbox: collectUnifiedInboxEntries({ view: "all" }),
    id,
    storageKey: UNIFIED_INBOX_ARCHIVE_STORAGE_KEY,
    type,
  })) return;
  renderDashboard(dashboardData);
  UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus(simpleText("unifiedInboxArchived"));
}

function restoreUnifiedInboxEntryFromUi(type = "", id = "") {
  if (!restoreUnifiedInboxEntry(type, id)) return;
  selectedUnifiedInboxView = ViewState.writeUnifiedInboxView("active");
  renderDashboard(dashboardData);
  UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus(simpleText("unifiedInboxRestored"));
}

function restoreAllArchivedUnifiedInboxEntriesFromUi() {
  const inbox = collectUnifiedInboxEntries({ view: "archived" });
  const entries = (inbox.entries || []).filter((entry) => entry.archiveKey);
  if (!entries.length) {
    UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus(simpleText("unifiedInboxArchiveBulkEmpty"));
    return;
  }
  const archive = loadUnifiedInboxArchive();
  entries.forEach((entry) => {
    delete archive[entry.archiveKey];
  });
  saveUnifiedInboxArchive(archive);
  selectedUnifiedInboxView = ViewState.writeUnifiedInboxView("active");
  renderDashboard(dashboardData);
  UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus(
    String(simpleText("unifiedInboxArchiveRestoreAllDone")).replace("{count}", String(entries.length))
  );
}

function resolveArchivedUnifiedInboxEntriesFromUi() {
  const inbox = collectUnifiedInboxEntries({ view: "archived" });
  const entries = (inbox.entries || []).filter((entry) => entry.archiveKey);
  if (!entries.length) {
    UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus(simpleText("unifiedInboxArchiveBulkEmpty"));
    return;
  }
  const archive = loadUnifiedInboxArchive();
  const resolvedArchive = loadUnifiedInboxResolvedArchive();
  const resolvedAt = new Date().toISOString();
  entries.forEach((entry) => {
    resolvedArchive[entry.archiveKey] = {
      ...(entry.archiveRecord || {}),
      key: entry.archiveKey,
      type: entry.type,
      id: entry.actionId,
      title: entry.displayTitle || entry.title || entry.typeLabel || "",
      body: entry.displayBody || entry.body || "",
      source_path: entry.sourcePath || entry.path || "",
      archivedAt: entry.archivedAt || entry.archiveRecord?.archivedAt || "",
      resolvedAt,
      resolution: "no_longer_processing",
    };
    delete archive[entry.archiveKey];
  });
  saveUnifiedInboxArchive(archive);
  saveUnifiedInboxResolvedArchive(resolvedArchive);
  renderDashboard(dashboardData);
  UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus(
    String(simpleText("unifiedInboxArchiveResolveDone")).replace("{count}", String(entries.length))
  );
}

function codexInboxTaskPrompt() {
  const inbox = collectUnifiedInboxEntries({ view: "active" });
  return AgentPromptService.buildCodexInboxTaskPrompt({
    entries: inbox.entries,
    paths: codexInboxPaths(),
    language: activeTemplateLanguage(),
  });
}

function codexInboxPaths() {
  return {
    confirmation: CONFIRMATION_INBOX_PATH,
    feedback: FEEDBACK_INBOX_PATH,
    candidates: pluginCandidateSources(),
  };
}

function findSingleInboxEntry(type = "", id = "") {
  const inbox = collectUnifiedInboxEntries({ view: "all" });
  return InboxService.findUnifiedInboxEntry(inbox.entries || [], type, id);
}

function codexRunnerPayloadForEntries(entries = [], prompt = "", title = "") {
  const modelSettings = ModelCatalogController.snapshot();
  return CodexRunRouter.payloadForEntries(entries, prompt, title, {
    candidateEnvelopeForBatch: (items) => InboxService.candidateEnvelopeForBatch(items, simpleText),
    fallbackTitle: simpleText("unifiedInboxTitle"),
    selectedModel: ModelCatalogController.payloadModel(),
    selectedReasoning: modelSettings.selectedReasoning,
  });
}

function workSessionRunPayload(session = {}, options = {}) {
  const modelSettings = ModelCatalogController.snapshot();
  return WorkSessionRouter.runPayload(session, options, {
    language: session.templateLanguage || lang || activeTemplateLanguage(),
    clientRequestId: session.clientRequestId,
    runs: codexRunnerRuns,
    selectedModel: ModelCatalogController.payloadModel(),
    selectedReasoning: modelSettings.selectedReasoning,
    text: simpleText,
  });
}
async function copyWorkSessionTaskPacket(session = {}) {
  if (!session?.id) return { ok: false };
  const modelSettings = ModelCatalogController.snapshot();
  const sessionLanguage = session.templateLanguage || lang || activeTemplateLanguage();
  const packet = WorkSessionRouter.publicTaskPacket(session, {
    body: simpleTextForLanguage("handoffAdmitTaskPacketBody", sessionLanguage),
    heading: simpleTextForLanguage("handoffAdmitTaskPacketHeading", sessionLanguage),
    language: sessionLanguage,
    model: modelSettings.selection.effectiveModel,
    reasoning: modelSettings.selectedReasoning,
    responseMode: session.responseMode || "auto",
  });
  const result = await copyPlainText(packet.answer || "");
  const status = dashboardTarget("todayWorkSession")?.querySelector("[data-work-session-status]");
  if (status) status.textContent = simpleText(result.copied ? "handoffAdmitTaskCopied" : "handoffAdmitTaskCopyFailed");
  return { ok: Boolean(result.copied), outcome: result.copied ? "copied" : "copy_failed" };
}
async function submitWorkSessionRun(session = {}, options = {}) {
  if (!workSessionActionAllowed(session, "run")) return { ok: false, reason: "stale_context" };
  const responseMode = WorkSessionRouter.inferResponseMode(
    session.intent,
    options.responseMode || session.responseMode || "auto"
  );
  const executionRoute = workSessionExecutionRoute();
  if (executionRoute.mode !== "registered_runner") {
    const modelSettings = ModelCatalogController.snapshot();
    const sessionLanguage = session.templateLanguage || lang || activeTemplateLanguage();
    const run = WorkSessionRouter.publicTaskPacket(session, {
      body: simpleTextForLanguage(
        executionRoute.reason === "public_policy" ? "workSessionPacketBody" : "handoffAdmitTaskPacketBody",
        sessionLanguage,
      ),
      heading: simpleTextForLanguage("workSessionPacketHeading", sessionLanguage),
      language: sessionLanguage,
      model: modelSettings.selection.effectiveModel,
      reasoning: modelSettings.selectedReasoning,
      responseMode,
    });
    return { ok: true, persistResult: true, run };
  }
  if (!CodexRunnerClient?.submitCodexRun) {
    return ResultEnvelopeContract.failureResult("client_transport_unavailable", {
      client_request_id: session.clientRequestId, response_mode: responseMode, work_session_id: session.id,
    });
  }
  let payload;
  try {
    payload = workSessionRunPayload(session, options);
  } catch {
    return ResultEnvelopeContract.failureResult("client_request_invalid", {
      client_request_id: session.clientRequestId, response_mode: responseMode, work_session_id: session.id,
    });
  }
  const result = await CodexRunnerClient.submitCodexRun(payload);
  if (!result.ok) {
    return ResultEnvelopeContract.failureResult(result.error_envelope || result.error_type, {
      client_request_id: session.clientRequestId, response_mode: responseMode, work_session_id: session.id,
    });
  }
  codexRunnerRuns = [
    result.run,
    ...codexRunnerRuns.filter((run) => run.id !== result.run?.id),
  ].filter(Boolean).slice(0, 40);
  renderHomeCommandCenter(dashboardData?.home_command_center || {});
  startCodexRunnerPolling(dashboardTarget("todayWorkSession") || document);
  return result;
}

async function reconcileWorkSessionRun(session = {}) {
  const clientRequestId = String(session.clientRequestId || "").trim();
  if (!clientRequestId || !CodexRunnerClient?.loadCodexRuns) {
    return ResultEnvelopeContract.failureResult("client_request_invalid", {
      client_request_id: clientRequestId, response_mode: session.responseMode, work_session_id: session.id,
    });
  }
  const result = await CodexRunnerClient.loadCodexRuns({ clientRequestId, limit: 2 });
  if (!result.ok) {
    const failure = ResultEnvelopeContract.failureResult(result.error_envelope || result.error_type, {
      client_request_id: clientRequestId, response_mode: session.responseMode, work_session_id: session.id,
    });
    workSession = WorkSessionState.write(WorkSessionState.updateSession(session, {
      draftResult: failure.run,
      latestRunId: session.latestRunId || "",
      status: session.sessionLifecycle === "ended" || session.status === "completed" ? "completed" : "active",
    }), { runtimeMode: dashboardData?.runtime_mode || "private" });
    refreshWorkSessionSurfaces();
    return failure;
  }
  codexRunnerRuns = [...result.runs, ...codexRunnerRuns.filter(
    (run) => !result.runs.some((candidate) => candidate.id === run.id)
  )].slice(0, 40);
  const reconciled = WorkSessionState.reconcileRun(session, result.runs, {
    reconciliation: result.reconciliation,
  });
  if (reconciled) {
    workSession = WorkSessionState.write(reconciled, { runtimeMode: dashboardData?.runtime_mode || "private" });
    refreshWorkSessionSurfaces();
  }
  return {
    ok: Boolean(reconciled && ["running", "ready"].includes(reconciled.status)),
    reconciled: true,
    reconciliation: result.reconciliation,
    run: result.runs[0] || reconciled?.draftResult || null,
  };
}

async function submitCodexRunnerTask({ entries = [], prompt = "", root = null, title = "" } = {}) {
  if (!entries.length) {
    UnifiedInboxWorkbenchService.setUnifiedInboxStatus(simpleText("unifiedInboxNoPendingAction"), root || document);
    return { ok: false };
  }
  if (!workspaceWriteAvailable()) {
    UnifiedInboxWorkbenchService.setUnifiedInboxStatus(simpleText("unifiedInboxRunnerDemoDisabled"), root || document);
    return { ok: false, error_type: "public_starter_writeback_blocked" };
  }
  if (!CodexRunnerClient?.submitCodexRun) {
    UnifiedInboxWorkbenchService.setUnifiedInboxStatus(simpleText("unifiedInboxRunnerUnavailable"), root || document);
    return { ok: false };
  }
  const confirmation = String(simpleText("unifiedInboxRunnerConfirm")).replace("{count}", String(entries.length));
  if (!window.confirm(confirmation)) {
    UnifiedInboxWorkbenchService.setUnifiedInboxStatus(simpleText("unifiedInboxRunnerCancelled"), root || document);
    return { ok: false, cancelled: true };
  }
  UnifiedInboxWorkbenchService.setUnifiedInboxStatus(simpleText("unifiedInboxRunnerStarting"), root || document);
  const result = await CodexRunnerClient.submitCodexRun(codexRunnerPayloadForEntries(entries, prompt, title));
  if (!result.ok) {
    UnifiedInboxWorkbenchService.setUnifiedInboxStatus(simpleText("unifiedInboxRunnerFailed"), root || document);
    return result;
  }
  UnifiedInboxWorkbenchService.setUnifiedInboxStatus(
    `${simpleText("unifiedInboxRunnerQueued")}：${result.run?.id || ""}`,
    root || document
  );
  codexRunnerRuns = [
    ...(result.runs || []),
    result.run,
    ...codexRunnerRuns.filter((run) => run.id !== result.run?.id),
  ].filter(Boolean).slice(0, 40);
  renderUnifiedInbox();
  startCodexRunnerPolling(root || document);
  return result;
}

function codexRunnerTimeValue(value = "") {
  const time = new Date(value || "").getTime();
  return isNaN(time) ? 0 : time;
}

function hasActiveCodexRunnerRun(runs = codexRunnerRuns) {
  const safeRuns = runs || [];
  if (safeRuns.some((run) => run.status === "submitted" || run.status === "running")) return true;
  const directChildren = safeRuns.filter((run) => run.task_mode === "direct_execution" && run.action_key);
  const queuedChildren = directChildren.filter((run) => run.status === "queued");
  if (!queuedChildren.length) return safeRuns.some((run) => run.status === "queued" && run.task_mode !== "direct_execution");
  const completedOrFailed = directChildren.some((run) => run.status === "completed" || run.status === "failed");
  const lastActivity = Math.max(
    ...directChildren.map((run) => codexRunnerTimeValue(run.updated_at || run.started_at || run.created_at)),
    ...safeRuns
      .filter((run) => run.task_mode === "direct_execution" && !run.action_key)
      .map((run) => codexRunnerTimeValue(run.updated_at || run.created_at))
  );
  return !(completedOrFailed && Date.now() - lastActivity > 60000);
}

function fillCodexRunnerCopy(template = "", values = {}) {
  return Object.entries(values).reduce(
    (text, [key, value]) => String(text).replaceAll(`{${key}}`, String(value ?? "")),
    String(template || "")
  );
}

function latestCodexRunnerQueueSummary(runs = codexRunnerRuns) {
  const safeRuns = runs || [];
  const directRuns = safeRuns.filter((run) => run.task_mode === "direct_execution");
  const parents = directRuns
    .filter((run) => !run.parent_id && !run.action_key)
    .sort((left, right) => codexRunnerTimeValue(right.created_at || right.updated_at) - codexRunnerTimeValue(left.created_at || left.updated_at));
  const activeParent = parents.find((run) => run.status === "running" || run.status === "queued");
  const parent = activeParent || parents[0] || null;
  const children = parent
    ? directRuns.filter((run) => run.parent_id === parent.id)
    : directRuns.filter((run) => run.action_key);
  const orderedChildren = [...children].sort((left, right) => {
    const leftIndex = Number(left.queue_index || 9999);
    const rightIndex = Number(right.queue_index || 9999);
    if (leftIndex !== rightIndex) return leftIndex - rightIndex;
    return codexRunnerTimeValue(left.created_at || left.updated_at) - codexRunnerTimeValue(right.created_at || right.updated_at);
  });
  const runningRun = orderedChildren.find((run) => run.status === "running") || null;
  const nextQueuedRun = orderedChildren.find((run) => run.status === "queued") || null;
  const latestChild = [...orderedChildren].sort((left, right) => codexRunnerTimeValue(right.updated_at) - codexRunnerTimeValue(left.updated_at))[0] || null;
  const completed = orderedChildren.filter((run) => run.status === "completed").length;
  const failed = orderedChildren.filter((run) => run.status === "failed").length;
  const queued = orderedChildren.filter((run) => run.status === "queued").length;
  const running = orderedChildren.filter((run) => run.status === "running").length;
  const total = Number(parent?.queue_total || orderedChildren[0]?.queue_total || orderedChildren.length || 0);
  const lastActivity = Math.max(
    codexRunnerTimeValue(parent?.updated_at || ""),
    ...orderedChildren.map((run) => codexRunnerTimeValue(run.updated_at || run.started_at || run.created_at))
  );
  const stale = Boolean(queued && !running && (completed || failed) && Date.now() - lastActivity > 60000);
  return { parent, children: orderedChildren, runningRun, nextQueuedRun, latestChild, completed, failed, queued, running, total, stale };
}

function archiveCompletedCodexRunnerItems(runs = []) {
  let archived = 0;
  const existingArchive = InboxService.loadUnifiedInboxArchive(UNIFIED_INBOX_ARCHIVE_STORAGE_KEY);
  (runs || []).forEach((run) => {
    if (run?.task_mode !== "direct_execution" || run?.status !== "completed" || !run?.action_key) return;
    const [type = "", ...idParts] = String(run.action_key || "").split(":");
    const id = idParts.join(":");
    if (!type || !id) return;
    if (existingArchive[run.action_key]) return;
    const inbox = collectUnifiedInboxEntries({ view: "all" });
    const entry = InboxService.findUnifiedInboxEntry(inbox.entries || [], type, id);
    if (!entry || !InboxService.completedRunCanArchiveEntry(run, entry, codexRunnerTimeValue)) return;
    if (InboxService.archiveUnifiedInboxEntryFromInbox({
      inbox,
      id,
      storageKey: UNIFIED_INBOX_ARCHIVE_STORAGE_KEY,
      type,
    })) {
      WorkSessionLifecycle.syncHandoffStatus(type, id, "completed");
      archived += 1;
    }
  });
  return archived;
}

function codexRunnerStatusMessage(run = null) {
  const queue = latestCodexRunnerQueueSummary();
  if (queue.parent || queue.children.length) {
    const focusRun = queue.runningRun || queue.nextQueuedRun || queue.latestChild || queue.parent || run || {};
    const index = focusRun.queue_index || queue.parent?.current_queue_index || "";
    const total = queue.total || focusRun.queue_total || "";
    if (queue.runningRun) {
      return fillCodexRunnerCopy(simpleText("unifiedInboxRunnerProgressRunning"), { index, total });
    }
    if (queue.queued && queue.stale) {
      return fillCodexRunnerCopy(simpleText("unifiedInboxRunnerProgressPaused"), { index: queue.nextQueuedRun?.queue_index || index, total });
    }
    if (queue.queued) {
      return fillCodexRunnerCopy(simpleText("unifiedInboxRunnerProgressNext"), { index: queue.nextQueuedRun?.queue_index || index, total });
    }
    if (queue.failed) return simpleText("unifiedInboxRunnerProgressDoneWithFailure");
    if (queue.completed) return simpleText("unifiedInboxRunnerProgressDone");
  }
  const fallbackRun = run || codexRunnerRuns[0] || null;
  if (!fallbackRun) return simpleText("unifiedInboxRunnerEmpty");
  if (fallbackRun.status === "failed") {
    const output = String(fallbackRun.error_envelope?.message || "").replace(/\s+/g, " ").trim();
    return `${simpleText("unifiedInboxRunnerRunFailed")}：${shortText(output, 180)}`;
  }
  if (fallbackRun.status === "completed") return `${simpleText("unifiedInboxRunnerCompleted")}：${fallbackRun.id}`;
  if (fallbackRun.status === "submitted" || fallbackRun.status === "queued") return `${simpleText("unifiedInboxRunnerQueued")}：${fallbackRun.id}`;
  if (fallbackRun.status === "running") return `${simpleText("unifiedInboxRunnerRunning")}：${fallbackRun.id}`;
  return `${simpleText("unifiedInboxRunnerStatusUnknown")}：${fallbackRun.id || ""}`;
}

async function refreshCodexRunnerRuns({ root = document, rerender = true, updateStatus = true } = {}) {
  if (!CodexRunnerClient?.loadCodexRuns) {
    if (updateStatus) UnifiedInboxWorkbenchService.setUnifiedInboxStatus(simpleText("unifiedInboxRunnerUnavailable"), root);
    return { ok: false, runs: [] };
  }
  const requestToken = runnerRefreshRequestGate.begin("codex-runs");
  const hadActiveRun = hasActiveCodexRunnerRun(codexRunnerRuns);
  const result = await CodexRunnerClient.loadCodexRuns({ limit: 40 });
  if (!runnerRefreshRequestGate.isCurrent(requestToken, "codex-runs")) {
    return { ok: false, ignored: true, reason: "stale_response", runs: [] };
  }
  if (!result.ok) {
    if (updateStatus) UnifiedInboxWorkbenchService.setUnifiedInboxStatus(simpleText("unifiedInboxRunnerStatusLoadFailed"), root);
    return result;
  }
  codexRunnerRuns = result.runs || [];
  if (hadActiveRun && !hasActiveCodexRunnerRun(codexRunnerRuns) && dashboardData?.runtime_mode === "personal_vault") {
    try {
      dashboardData = await loadDashboard();
    } catch {
      // The completed run remains visible even if the derived projection needs a manual retry.
    }
  }
  const reconciledSession = WorkSessionState.reconcileRun?.(workSession, codexRunnerRuns);
  if (reconciledSession) {
    workSession = WorkSessionState.write(reconciledSession, { runtimeMode: dashboardData?.runtime_mode || "private" });
  }
  codexRunnerProviderStatus = result.provider_status || codexRunnerProviderStatus || null;
  const archivedCompleted = archiveCompletedCodexRunnerItems(codexRunnerRuns);
  if (rerender) {
    renderUnifiedInbox();
    renderPluginLibrarySlots(dashboardData);
    WorkSessionWorkbenchService.renderPreservingInteraction(
      dashboardTarget("todayWorkSession"),
      () => renderHomeCommandCenter(dashboardData?.home_command_center || {})
    );
  }
  if (updateStatus) {
    const targetRoot = dashboardTarget("unifiedInbox") || root || document;
    const message = archivedCompleted
      ? `${codexRunnerStatusMessage(codexRunnerRuns[0])} · ${String(simpleText("unifiedInboxRunnerArchivedDone")).replace("{count}", String(archivedCompleted))}`
      : codexRunnerStatusMessage(codexRunnerRuns[0]);
    UnifiedInboxWorkbenchService.setUnifiedInboxStatus(message, targetRoot);
  }
  return result;
}

function scheduleCodexRunnerStatusRefresh(root = document) {
  if (codexRunnerPollTimer) window.clearTimeout(codexRunnerPollTimer);
  codexRunnerPollTimer = window.setTimeout(async () => {
    const result = await refreshCodexRunnerRuns({ root, rerender: true, updateStatus: true });
    if (result.ok && hasActiveCodexRunnerRun(result.runs || [])) {
      scheduleCodexRunnerStatusRefresh(dashboardTarget("unifiedInbox") || root || document);
    } else {
      codexRunnerPollTimer = null;
    }
  }, 3800);
}

function startCodexRunnerPolling(root = document) {
  if (codexRunnerPollTimer) window.clearTimeout(codexRunnerPollTimer);
  refreshCodexRunnerRuns({ root, rerender: true, updateStatus: true }).then((result) => {
    if (result.ok && hasActiveCodexRunnerRun(result.runs || [])) {
      scheduleCodexRunnerStatusRefresh(dashboardTarget("unifiedInbox") || root || document);
    }
  });
}

async function clearUnifiedInboxProcessedItems() {
  UnifiedInboxWorkbenchService.setUnifiedInboxStatus(simpleText("unifiedInboxClearing"));

  doingItems = InboxService.resolveClearedInboxItems({ localItems: doingItems }).items;
  saveDoingItems();
  saveResolvedClearedInboxItems(
    null,
    "preview_feedback",
    previewFeedbackWorkflowController().loadPreviewFeedbackItems(),
    (items) => previewFeedbackWorkflowController().savePreviewFeedbackItems(items),
  );

  const clearResult = await InboxService.clearProcessedInbox({ scope: "processed" });
  const cleanupServerState = InboxService.normalizeClearedInboxServerState(clearResult.serverState);
  const clientCleanupState = null;
  const clearedConfirmations = InboxService.resolveClearedInboxObject({
    fallbackRecords: ConfirmationState.filterActiveConfirmationDecisions(loadConfirmationDecisions(), {
      statusIsActive: InboxService.inboxStatusIsActive,
    }),
    serverKey: "confirmations",
    serverState: clientCleanupState,
  });
  saveConfirmationDecisions(clearedConfirmations.records);
  await Promise.allSettled([
    PluginRuntime.runCandidateActions({
      action: "clear_processed",
      context: pluginHost.runtimeContext(),
      data: dashboardData,
    }),
  ]);
  renderDashboard(dashboardData);
  UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus(
    cleanupServerState ? simpleText("unifiedInboxCleared") : simpleText("unifiedInboxClearFailed")
  );
}

function itemLocalSessionRegistry(itemId = selectedExecutionItemId) {
  return WorkSessionState.sessionRegistryProjection(
    executionSessionForDisplay(),
    workSessionHistoryForDisplay(),
    codexRunnerRuns,
  ).filter((entry) => entry.item_id === itemId);
}

function recordItemReviewDecision(type = "", id = "", decision = "") {
  const allowed = new Set(["accepted", "revised", "rejected", "deferred"]);
  const normalizedDecision = String(decision || "").trim();
  if (isPublicStarterRuntime() || !selectedExecutionItemId || !allowed.has(normalizedDecision)) return false;
  const registry = itemLocalSessionRegistry();
  const sessionIds = registry.map((entry) => entry.session_id).filter(Boolean);
  const inbox = collectUnifiedInboxEntries({ view: "all" });
  const exactEntries = InboxService.entriesForItem(inbox.entries, {
    itemId: selectedExecutionItemId,
    sessionIds,
  });
  const entry = InboxService.findUnifiedInboxEntry(exactEntries, type, id);
  if (!entry) return false;
  const index = doingItems.findIndex((item) => (
    DoingBoardState.itemKey(item) === id
    && sessionIds.includes(String(item.work_session_id || "").trim())
  ));
  if (index < 0) return false;
  const label = simpleText(`itemReviewDecision_${normalizedDecision}`);
  const confirmation = String(simpleText("itemReviewDecisionConfirm")).replace("{decision}", label);
  if (!window.confirm(confirmation)) return false;
  const current = doingItems[index];
  const admissionState = InboxService.normalizeAdmissionState({
    ...(current.candidate?.admission_state || current.admission_state || {}),
    decision_state: normalizedDecision,
    mutation_state: "not_requested",
    validation_state: "unvalidated",
    authority_role: "none",
  });
  doingItems = doingItems.map((item, itemIndex) => itemIndex === index ? {
    ...item,
    admission_state: admissionState,
    candidate: { ...(item.candidate || {}), admission_state: admissionState },
  } : item);
  saveDoingItems();
  renderUnifiedInbox();
  UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus(
    String(simpleText("itemReviewDecisionRecorded")).replace("{decision}", label),
    dashboardTarget("unifiedInbox") || document,
  );
  return true;
}

function renderUnifiedInbox() {
  const root = dashboardTarget("unifiedInbox");
  if (!root) return;
  if (!selectedExecutionItemId) {
    root.innerHTML = `<p class="empty-state">${escapeHtml(lang === "zh-CN" ? "未选择事项。这里不是全局 Inbox；请从 Now 或 Library 的明确事项打开 Work/Review。" : "No item selected. This is not a global Inbox; open Work/Review from an exact item in Now or Library.")}</p>`;
    return;
  }
  UnifiedInboxWorkbenchService.renderItemReview(root, {
    activeTemplateLanguage,
    archiveUnifiedInboxEntryFromUi,
    bindButtonTooltips,
    bindPreviewButtons,
    bindSectionJumpButtons,
    clearLocalUnifiedInboxItems,
    clearUnifiedInboxProcessedItems,
    codexInboxPaths,
    codexInboxTaskPrompt,
    get codexRunnerProviderStatus() { return codexRunnerProviderStatus; },
    get codexRunnerRuns() { return codexRunnerRuns; },
    collectUnifiedInboxEntries,
    copyEncodedPayload,
    copyPlainText,
    get dashboardData() { return dashboardData; },
    dashboardTarget,
    draftWorkSession: WorkSessionLifecycle.draft,
    escapeHtml,
    executionSessionForDisplay,
    findSingleInboxEntry,
    focusDashboardSection,
    getPreviewDoc,
    hasActiveCodexRunnerRun,
    isPublicStarterRuntime,
    itemLocalSessionRegistry,
    openItemExecutionDrawer,
    openMarkdownPreviewCards,
    pluginContext: () => pluginHost.runtimeContext(),
    recordItemReviewDecision,
    refreshCodexRunnerRuns,
    renderWorkSessionSurface,
    rerender: renderUnifiedInbox,
    resolveArchivedUnifiedInboxEntriesFromUi,
    restoreAllArchivedUnifiedInboxEntriesFromUi,
    restoreUnifiedInboxEntryFromUi,
    scheduleCodexRunnerStatusRefresh,
    get selectedExecutionItemId() { return selectedExecutionItemId; },
    get selectedWorkFilter() { return selectedWorkFilter; },
    setUnifiedInboxView: (view) => { selectedUnifiedInboxView = ViewState.writeUnifiedInboxView(view); },
    setWorkFilter: (filter) => { selectedWorkFilter = ViewState.normalizeWorkFilter(filter); },
    simpleText,
    submitCodexRunnerTask,
    withdrawUnifiedInboxEntry,
    workspaceWriteAvailable,
  });
}
function loadDoingItems() {
  return DoingBoardState.readItems({ statePolicy: StatePolicy, storageKey: DOING_STORAGE_KEY });
}

function saveDoingItems() {
  DoingBoardState.writeItems(doingItems, { statePolicy: StatePolicy, storageKey: DOING_STORAGE_KEY });
}

function addDoingItem(item, status = "local") {
  const result = DoingBoardState.upsertItem(doingItems, item, status);
  if (!result.item) return null;
  doingItems = result.items;
  const inboxType = result.item.type === "paper_field_update" ? "paper_field_update" : "task";
  const inboxId = DoingBoardState.itemKey(result.item);
  InboxService.restoreUnifiedInboxEntry({
    storageKey: UNIFIED_INBOX_ARCHIVE_STORAGE_KEY,
    type: inboxType,
    id: inboxId,
  });
  InboxService.restoreUnifiedInboxEntry({
    storageKey: UNIFIED_INBOX_ARCHIVE_RESOLVED_STORAGE_KEY,
    type: inboxType,
    id: inboxId,
  });
  saveDoingItems();
  renderUnifiedInbox();
  syncVisibleHandoffCounts();
  return result.item;
}

function removeDoingItem(key) {
  doingItems = DoingBoardState.removeItem(doingItems, key);
  saveDoingItems();
}

function clearLocalUnifiedInboxItems() {
  doingItems = doingItems.filter((item) => !InboxService.inboxStatusIsActive(item.status, true));
  saveDoingItems();
  renderDashboard(dashboardData);
  UnifiedInboxWorkbenchService.scheduleUnifiedInboxStatus(simpleText("unifiedInboxLocalCleared"));
}

function renderHomeCommandCenter(center = {}) {
  const root = dashboardTarget("homeCommandCenter");
  if (!root) return;
  root.innerHTML = HomeCommandCenterView.renderNowHtml(
    {},
    { escapeHtml, sectionTranslate: t, translate: simpleText }
  );
  pluginHost.renderWorkbenchSlots(root);
  bindSectionJumpButtons(root);
  bindPreviewButtons(root);
}

function renderWorkSessionSurface(center = {}) {
  const root = dashboardTarget("workSessionSurface");
  if (!root) return;
  const displaySession = executionSessionForDisplay();
  const currentResult = WorkSessionRouter.resultForSession(codexRunnerRuns, displaySession || {});
  const handoffActive = WorkSessionLifecycle.handoffActive();
  const workItems = PluginRuntime.workItemProviderModels(dashboardData)
    .flatMap((provider) => Array.isArray(provider?.projection?.items) ? provider.projection.items : []);
  const workItemBindingState = WorkSessionState.workItemBindingProjection(displaySession, workItems);
  const selectedItem = executionItem();
  const contextStatus = displaySession ? workSessionContextStatus(displaySession, selectedItem) : "unbound";
  const workSessionHtml = displaySession ? WorkSessionView.renderWorkSessionHtml({
      contextStatus,
      executionAvailable: localExecutionAvailable(),
      executionRoute: workSessionExecutionRoute(),
      handoffActive,
      handoffAdmitSurface: HandoffAdmitSurface.project({
        backgroundPreparationAvailable: false,
        config: dashboardData?.config?.surface_candidates,
        handoffActive,
        result: currentResult,
        session: displaySession,
      }),
      handoffReceiptProjection: HandoffReceiptProjection.normalize(dashboardData?.handoff_receipt_projection),
      onboardingRequired: dashboardData?.runtime_mode === "personal_vault"
        && Number(dashboardData?.personal_vault?.record_count || 0) === 0,
      publicMode: isPublicStarterRuntime(),
      workItemMutationAvailable: durableWorkItemMutationAvailable(),
      workItemBindingState,
      recentSessions: workSessionHistoryForFilter(),
      result: currentResult,
      resumePackets: Array.isArray(center?.resume_packets) ? center.resume_packets : [],
      session: displaySession,
      workspaceWriteAvailable: workspaceWriteAvailable(),
    }, {
      encodeDataPayload: UiCore.encodeDataPayload,
      escapeHtml,
      markdownToHtml: (content) => PreviewMarkdownService.markdownToHtml(content, "", { escapeHtml, resolveDocument: getPreviewDoc }),
      normalizeArtifactPath: (path) => PreviewService.repositoryRelativePath?.(path) || String(path || ""),
      previewButton: (path, label) => PreviewLinksComponent.resolvedPreviewButton(path, label, { escapeHtml,
        resolveDocument: getPreviewDoc, resolvePreviewLink: PreviewService.resolvePreviewLink, simpleText }),
      translate: simpleText,
    }) : selectedItem ? WorkSessionView.renderItemLauncher({ item: selectedItem }, {
      escapeHtml,
      translate: simpleText,
    }) : "";
  root.innerHTML = `<section class="work-session-continuity" id="todayWorkSession" data-work-session-continuity>${workSessionHtml}</section>`;
  bindSectionJumpButtons(root);
  bindPreviewButtons(root);
  WorkSessionWorkbenchService.bindWorkSessionEvents(root, {
    ...WorkSessionLifecycle.callbacks,
  }, {
    translate: simpleText,
  });
  root.querySelector?.("[data-start-item-work-session]")?.addEventListener("click", (event) => {
    event.preventDefault();
    draftExecutionItemSession(String(event.currentTarget?.dataset?.startItemWorkSession || ""));
  });
}

function renderDashboard(data) {
  if (!data) return;
  dashboardData = data;
  const renderState = DashboardRenderPlan.prepareRenderState(data, {
    currentLang: lang,
    resolveLanguage: (defaultLanguage) => I18nRuntime.resolveLanguage(I18N, lang, defaultLanguage),
    translateFor: (key, nextLang) => I18nRuntime.translate(I18N, nextLang, key),
  });
  lang = renderState.lang;
  const lifecycleSource = DashboardLifecycleAdapter.lifecycleSource(renderState, {
    applyDashboardHeader,
    source: window,
  });
  DashboardRenderPlan.runBeforeRenderPlan({
    callbacks: DashboardRenderPlan.beforeRenderCallbacks(lifecycleSource),
  });
  DashboardRenderPlan.runRenderPlan(data, {
    lang,
    renderers: DashboardRenderPlan.rendererCallbacks(lifecycleSource),
  });
  DashboardRenderPlan.runAfterRenderPlan({
    callbacks: DashboardRenderPlan.afterRenderCallbacks(lifecycleSource),
  });
}

bindPreviewHistoryNavigation();

loadDashboard()
  .then(async (data) => {
    dashboardData = data;
    if (StorageContract.ensureRuntimeStorageBoundary?.(data.runtime_mode)) {
      window.location.reload();
      return;
    }
    ModelCatalogController.initialize(data.runtime_mode);
    workSession = WorkSessionState.read({ runtimeMode: data.runtime_mode });
    workSessionHistory = WorkSessionState.readHistory({ runtimeMode: data.runtime_mode });
    if (!UiPreferences.hasLanguagePreference()) {
      lang = data.config?.language || "en";
    }
    lang = I18nRuntime.resolveLanguage(I18N, lang, data.config?.language || "en");
    UiPreferences.writeLanguage(lang);
    applyTheme();
    UiPreferences.writeTheme(theme);
    setupLanguageSelect(data);
    setupThemePicker();
    const refreshResult = await DailyProfileRefreshClient?.refreshIfDue({ runtimeMode: data.runtime_mode });
    if (refreshResult?.dashboard_rebuilt) {
      data = await loadDashboard();
      dashboardData = data;
    }
    renderDashboard(data);
    applyInitialSurfaceRequest();
    ModelCatalogController.refresh({ force: false, rerender: true });
    refreshCodexRunnerRuns({ root: dashboardTarget("unifiedInbox") || document, rerender: true, updateStatus: false }).then((result) => {
      if (result.ok && hasActiveCodexRunnerRun(result.runs || [])) {
        scheduleCodexRunnerStatusRefresh(dashboardTarget("unifiedInbox") || document);
      }
    });
  })
  .catch((error) => {
    const serviceHint = !ServiceMode.isServerMode(location)
      ? ServiceMode.blockedHintHtml({
          title: t("serviceMode.fileTitle"),
          body: t("serviceMode.fileBody"),
          linkLabel: t("serviceMode.openServer"),
          defaultServerUrl: DEFAULT_SERVER_URL,
          escapeHtml,
        })
      : "";
    WorkspaceShellWorkbenchService.showStartupError(
      document,
      ErrorPageView.renderErrorPageHtml(
        { message: error.message, serviceHint },
        { escapeHtml, translate: t },
      ),
    );
    document.querySelector("[data-dashboard-retry]")?.addEventListener("click", () => window.location.reload());
  });
