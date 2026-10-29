const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

function memoryStorage(initial = {}) {
  const values = new Map(Object.entries(initial).map(([key, value]) => [String(key), String(value)]));
  return {
    getItem(key) { return values.has(String(key)) ? values.get(String(key)) : null; },
    removeItem(key) { values.delete(String(key)); },
    setItem(key, value) { values.set(String(key), String(value)); },
  };
}

function domNode() {
  return {
    __researchosPreviewResizeBound: false,
    classList: { add() {}, remove() {}, toggle() {} },
    dataset: {},
    innerHTML: "",
    querySelector() { return null; },
    querySelectorAll() { return []; },
    removeAttribute() {},
    scrollIntoView() {},
    setAttribute() {},
    style: { removeProperty() {}, setProperty() {} },
  };
}

async function main() {
  const scheduled = [];
  const panel = domNode();
  const previewRoot = domNode();
  const collapse = domNode();
  let focusRestores = 0;
  const previewFocusFallback = domNode();
  previewFocusFallback.focus = () => { focusRestores += 1; };
  const document = {
    addEventListener() {},
    getElementById(id) {
      if (id === "markdownPreviewPanel") return panel;
      if (id === "markdownPreview") return previewRoot;
      if (id === "previewCollapse") return collapse;
      return null;
    },
    querySelector(selector) {
      return selector === ".preview-history-tabs .preview-tab-card.selected > button:not(.preview-tab-close)"
        ? previewFocusFallback
        : null;
    },
    removeEventListener() {},
  };
  const storage = memoryStorage({
    "researchos-preview-history": JSON.stringify([{ path: "docs/restored.md", anchor: "" }]),
    "researchos-preview-history-index": "0",
    "researchos-preview-open": "true",
    "researchos-preview-path": "docs/restored.md",
  });
  const context = {
    CSS: { escape: String },
    Node: { ELEMENT_NODE: 1 },
    console,
    document,
    innerWidth: 1280,
    localStorage: storage,
    matchMedia: () => ({ matches: false }),
    requestAnimationFrame: (callback) => callback(),
    setTimeout: (callback) => { scheduled.push(callback); return scheduled.length; },
  };
  context.window = context;
  vm.runInNewContext(read("dashboard/src/core/preview-state.js"), context);
  vm.runInNewContext(read("dashboard/src/services/preview-session-state.js"), context);
  vm.runInNewContext(read("dashboard/src/services/preview-workbench.js"), context);

  const restoredState = context.ResearchOSPreviewState.read({
    previewService: {
      loadPreviewHistory: ({ storage: source, storageKey }) => JSON.parse(source.getItem(storageKey) || "[]"),
    },
    storage,
  });
  assert.equal(restoredState.open, true, "a preview left open must reopen after refresh");
  assert.equal(restoredState.selectedPath, "docs/restored.md");

  const documents = [{ layer: "docs", path: "docs/restored.md", title: "Restored document" }];
  const loadedPaths = [];
  const renderedStates = [];
  const eventBindings = [];
  let historyPushes = 0;
  const previewService = {
    canPreviewBack: () => false,
    canPreviewForward: () => false,
    closePreviewHistoryEntry: ({ history, index }) => ({ closedCurrent: false, entry: null, history, index }),
    isPdfPreviewPath: () => false,
    navigatePreviewHistory: () => null,
    normalizePreviewPath: (value) => String(value || "").replace(/^\.\//, ""),
    pdfPreviewLabel: String,
    pushPreviewHistory: ({ history, index }) => {
      historyPushes += 1;
      return { history, index };
    },
    resolvePreviewLink: () => null,
    resolveRelativeMdPath: () => "",
    savePreviewHistory() {},
  };
  const sharedServices = {
    contentClient: {
      async loadPreviewContent(value) {
        loadedPaths.push(value);
        return "# Restored body";
      },
    },
    documents: {
      resolvePreviewDoc(value, options) {
        return options.documents.find((doc) => doc.path === value) || null;
      },
    },
    feedback: { normalizePreviewSelectedText: String },
    feedbackClient: {},
    feedbackWorkflow: { async submitPreviewFeedback() { return { localOnly: true }; } },
    markdown: {
      inlineMarkdownToHtml: String,
      markdownToHtml: String,
      slugifyMarkdownHeading: String,
    },
    markdownView: {
      renderCollapsedPreview: () => "<button class=\"preview-show-button\"></button>",
      renderMarkdownPreviewHtml: (state) => {
        renderedStates.push(state);
        return "<div class=\"markdown-body\"></div>";
      },
    },
    markdownWorkbench: {
      bindMarkdownPreviewEvents({ callbacks }) { eventBindings.push(callbacks); },
    },
    pdfView: {},
    pdfWorkbench: {
      createPreviewPdfWorkbench: () => ({
        closePdfPreview() {},
        openPdfPreview() {},
        renderPdfPreview() {},
        showDocumentPreview() {},
        showPdfPreview() {},
        state: () => ({ mode: "document", open: false, title: "" }),
      }),
    },
    preview: previewService,
    sessionState: context.ResearchOSPreviewSessionState,
    state: context.ResearchOSPreviewState,
    surfaceWorkbench: {
      bindPdfPreviewButtons() {},
      bindPreviewSurfaceEvents() {},
    },
  };
  const createWorkbench = (initialState) => context.ResearchOSPreviewWorkbenchService.createPreviewWorkbench({
    getDocuments: () => documents,
    initialState,
    services: sharedServices,
  });

  const restoredWorkbench = createWorkbench(restoredState);
  assert.equal(restoredWorkbench.ensureSelectedPreviewLoaded(), true);
  assert.equal(restoredWorkbench.ensureSelectedPreviewLoaded(), false, "repeated renders must not schedule duplicate restores");
  assert.equal(scheduled.length, 1);
  await scheduled.shift()();
  assert.deepEqual(loadedPaths, ["docs/restored.md"]);
  assert.equal(historyPushes, 0, "restoring the current tab must not append it to preview history again");
  assert.equal(renderedStates.at(-1).previewContent, "# Restored body");

  const deniedWorkbench = createWorkbench({
    ...restoredState,
    selectedPath: "private/denied.md",
  });
  assert.equal(deniedWorkbench.ensureSelectedPreviewLoaded(), false);
  assert.equal(scheduled.length, 0, "a path absent from the bounded preview projection must never be fetched");
  assert.deepEqual(loadedPaths, ["docs/restored.md"]);

  eventBindings.length = 0;
  const collapsedWorkbench = createWorkbench({
    ...restoredState,
    content: "",
    loadingPath: "",
    open: false,
  });
  collapsedWorkbench.renderMarkdownPreview();
  const collapsedBinding = eventBindings.at(-1);
  assert.equal(typeof collapsedBinding.onShowPreview, "function");
  collapsedBinding.onShowPreview();
  assert.equal(scheduled.length, 1, "expanding a restored tab must start its body load without another tab click");
  await scheduled.shift()();
  assert.equal(loadedPaths.at(-1), "docs/restored.md");
  assert.equal(historyPushes, 0);

  await collapsedBinding.onClosePath({ anchor: "", path: "docs/restored.md" });
  assert.equal(focusRestores, 1, "closing a preview tab must restore focus after the removed close button disappears");

  assert.ok(
    read("dashboard/index.html").includes('<script src="src/core/preview-state.js"></script>'),
    "index.html must load the preview state owner",
  );
  assert.ok(
    read("dashboard/index.html").includes('<script src="src/services/preview-workbench.js"></script>'),
    "index.html must load the preview workbench",
  );
  console.log("Preview restore behavior contract checks passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
