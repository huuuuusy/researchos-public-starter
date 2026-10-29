/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「markdown preview workbench」；负责 DOM 事件绑定，把副作用回调交还 app。
 * English: Workbench interaction adapter for markdown preview workbench in the ResearchOS dashboard; owns DOM event binding and returns side effects to app callbacks.
 */

(function attachResearchOSMarkdownPreviewWorkbenchService(global) {
  const { bindAll, bindOne } = global.ResearchOSInteractions;

  function bindMarkdownPreviewEvents({ root, collapse, callbacks = {} } = {}) {
    if (!root) return;
    const {
      onBindPdfButtons = () => {},
      onBindTooltips = () => {},
      onCaptureSelection = () => {},
      onFeedbackInput = () => {},
      onFeedbackSubmit = () => {},
      onClosePath = () => {},
      onHistory = () => {},
      onOpenPath = () => {},
      onPreviewMode = () => {},
      onSearchInput = () => {},
      onShowPreview = () => {},
      onTogglePreview = () => {},
    } = callbacks;

    if (collapse) {
      collapse.onclick = (event) => {
        onTogglePreview({ event, button: collapse });
      };
    }
    root.__researchosPreviewClosePath = onClosePath;
    if (root.dataset.previewCloseDelegated !== "true") {
      root.dataset.previewCloseDelegated = "true";
      root.addEventListener("click", (event) => {
        const target = event.target?.nodeType === global.Node.ELEMENT_NODE
          ? event.target
          : event.target?.parentElement;
        const closeButton = target?.closest?.("[data-preview-close-path]");
        if (!closeButton || !root.contains(closeButton)) return;
        event.preventDefault();
        event.stopPropagation();
        root.__researchosPreviewClosePath?.({
          anchor: closeButton.dataset.previewCloseAnchor || "",
          event,
          button: closeButton,
          path: closeButton.dataset.previewClosePath || "",
        });
      }, true);
    }
    bindOne(root, ".preview-show-button", "click", (event, button) => {
      onShowPreview({ event, button });
    });
    bindOne(root, ".preview-search input", "input", (event, input) => {
      onSearchInput({ event, input, value: input.value });
    });
    bindAll(root, "[data-preview-history]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onHistory({
        direction: button.dataset.previewHistory === "back" ? -1 : 1,
        event,
        button,
      });
    });
    bindAll(root, "[data-preview-mode]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onPreviewMode({
        event,
        button,
        mode: button.dataset.previewMode || "document",
      });
    });
    bindAll(root, "[data-preview-close-path]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      root.__researchosPreviewClosePath?.({
        anchor: button.dataset.previewCloseAnchor || "",
        event,
        button,
        path: button.dataset.previewClosePath || "",
      });
    });
    bindAll(root, "[data-preview-path]", "click", (event, button) => {
      event.preventDefault();
      event.stopPropagation();
      onOpenPath({
        anchor: button.dataset.previewAnchor || "",
        event,
        button,
        path: button.dataset.previewPath || "",
      });
    });
    bindOne(root, ".markdown-body", "mouseup", (event, body) => {
      onCaptureSelection({ event, body, root });
    });
    bindOne(root, ".markdown-body", "keyup", (event, body) => {
      onCaptureSelection({ event, body, root });
    });
    bindOne(root, "[data-preview-feedback-input]", "input", (event, input) => {
      onFeedbackInput({ event, input, value: input.value });
    });
    bindOne(root, "[data-preview-feedback-submit]", "click", (event, button) => {
      onFeedbackSubmit({ event, button, root });
    });
    onBindPdfButtons({ root });
    onBindTooltips({ root });
  }

  global.ResearchOSMarkdownPreviewWorkbenchService = Object.freeze({
    bindMarkdownPreviewEvents,
  });
})(window);
