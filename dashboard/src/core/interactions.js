/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「interactions」；供 app、service、view 复用。
 * English: Browser-side core primitive for interactions in the ResearchOS dashboard; shared by app, services, and views.
 */

(function attachResearchOSInteractions(global) {
  const BUTTON_TOOLTIP_RULES = Object.freeze([
    ["[data-preview-path]", "openPreviewHint"],
    ["[data-unified-inbox-generate]", "unifiedInboxGenerateHint"],
    ["[data-unified-inbox-copy]", "unifiedInboxCopyHint"],
    ["[data-unified-inbox-clear]", "unifiedInboxClearHint"],
    ["[data-unified-inbox-withdraw]", "unifiedInboxWithdrawHint"],
    ["[data-unified-inbox-archive]", "unifiedInboxArchiveHint"],
    ["[data-unified-inbox-restore]", "unifiedInboxRestoreHint"],
    ["[data-codex-inbox-task]", "unifiedInboxGenerateHint"],
    ["[data-secretary-inbox]", "unifiedInboxGenerateHint"],
    ["[data-secretary-run]", "secretaryHint"],
    ["[data-add-upgrade-task]", "handoffTaskHint"],
    ["[data-send-scout-prompt]", "handoffTaskHint"],
    ["[data-card-group-start]", "unifiedInboxGenerateHint"],
  ]);

  function bindAll(root, selector, eventName, handler) {
    const scope = root || global.document;
    if (!scope?.querySelectorAll) return;
    scope.querySelectorAll(selector).forEach((node) => {
      node.addEventListener(eventName, (event) => handler(event, node));
    });
  }

  function bindOne(root, selector, eventName, handler) {
    const scope = root || global.document;
    if (!scope?.querySelector) return;
    const node = scope.querySelector(selector);
    if (node) node.addEventListener(eventName, (event) => handler(event, node));
  }

  function applyButtonTooltips(root = global.document, translate = (key) => key) {
    BUTTON_TOOLTIP_RULES.forEach(([selector, key]) => {
      root.querySelectorAll(selector).forEach((node) => {
        if (!node.getAttribute("title")) node.setAttribute("title", translate(key));
      });
    });
  }

  function applySectionJumpButtons(root = global.document, focusTarget = () => {}) {
    root.querySelectorAll("[data-scroll-target]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        focusTarget(button.dataset.scrollTarget || "");
      });
      if (!["BUTTON", "A"].includes(button.tagName)) {
        button.addEventListener("keydown", (event) => {
          if (event.key !== "Enter" && event.key !== " ") return;
          event.preventDefault();
          event.stopPropagation();
          focusTarget(button.dataset.scrollTarget || "");
        });
      }
    });
  }

  function prefersReducedMotion(matchMedia = global.matchMedia) {
    try {
      return Boolean(matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
    } catch {
      return false;
    }
  }

  function motionBehavior(preferred = "smooth", matchMedia = global.matchMedia) {
    return prefersReducedMotion(matchMedia) ? "auto" : preferred;
  }

  function scrollIntoView(target, options = {}) {
    if (!target?.scrollIntoView) return false;
    target.scrollIntoView({
      ...options,
      behavior: motionBehavior(options.behavior || "smooth"),
    });
    return true;
  }

  function scrollTo(target, options = {}) {
    if (!target?.scrollTo) return false;
    target.scrollTo({
      ...options,
      behavior: motionBehavior(options.behavior || "smooth"),
    });
    return true;
  }

  function focusElement(target, options = {}) {
    if (!target?.focus) return false;
    const { ensureTabIndex = false, preventScroll = true } = options;
    if (ensureTabIndex && !target.hasAttribute?.("tabindex")) {
      target.setAttribute?.("tabindex", "-1");
      target.dataset.researchosProgrammaticFocus = "true";
    }
    try {
      target.focus({ preventScroll });
    } catch {
      target.focus();
    }
    return true;
  }

  function surfaceTextLabel(surface) {
    if (!surface) return "";
    const preferred = surface.querySelector("h2, h3, strong, summary strong, header strong, [data-i18n]");
    const text = (preferred?.textContent || surface.getAttribute("aria-label") || surface.id || "").trim();
    return text.replace(/\s+/g, " ").slice(0, 80);
  }

  let interactionFeedbackTimer = null;

  function showInteractionFeedback({
    title = "",
    translate = (key) => key,
    escapeHtml = global.ResearchOSUiCore?.escapeHtml,
  } = {}) {
    let toast = global.document.getElementById("interactionFeedback");
    if (!toast) {
      toast = global.document.createElement("div");
      toast.id = "interactionFeedback";
      toast.className = "interaction-feedback";
      toast.setAttribute("aria-live", "polite");
      global.document.body.appendChild(toast);
    }
    toast.innerHTML = `
      <strong>${escapeHtml(translate("surfaceSelected"))}${title ? ` · ${escapeHtml(title)}` : ""}</strong>
      <span>${escapeHtml(translate("surfaceSelectedHint"))}</span>
    `;
    toast.hidden = false;
    toast.classList.add("visible");
    global.clearTimeout(interactionFeedbackTimer);
    interactionFeedbackTimer = global.setTimeout(() => {
      toast.classList.remove("visible");
    }, 1800);
  }

  function applyInteractiveSurfaces(root = global.document, options = {}) {
    const selector = [
      ".unified-inbox-item",
      ".unified-inbox-source",
      ".simple-paper-card",
      ".simple-project-card",
      ".project-intake-card",
      ".simple-person-card",
      ".simple-route-card",
      ".paper-upgrade-card",
      ".analysis-state-card",
      ".card-group-item",
      ".card-group-source-banner",
      ".scout-inbox-item",
      ".upgrade-candidate-card",
      ".upgrade-inbox-item",
    ].join(",");
    const selectSurface = (surface) => {
      global.document.querySelectorAll(".surface-selected").forEach((item) => item.classList.remove("surface-selected"));
      surface.classList.add("surface-selected");
      showInteractionFeedback({ ...options, title: surfaceTextLabel(surface) });
    };
    root.querySelectorAll(selector).forEach((surface) => {
      if (surface.dataset.surfaceBound === "true") return;
      surface.dataset.surfaceBound = "true";
      surface.classList.add("interactive-surface");
      if (!surface.hasAttribute("tabindex")) surface.setAttribute("tabindex", "0");
      surface.addEventListener("click", (event) => {
        if (event.target?.closest?.("button, a, input, select, textarea, label, summary")) return;
        selectSurface(surface);
      });
      surface.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        if (event.target !== surface) return;
        event.preventDefault();
        selectSurface(surface);
      });
    });
  }

  window.ResearchOSInteractions = Object.freeze({
    BUTTON_TOOLTIP_RULES,
    bindAll,
    bindOne,
    focusElement,
    scrollIntoView,
    scrollTo,
    applyButtonTooltips,
    applySectionJumpButtons,
    applyInteractiveSurfaces,
    surfaceTextLabel,
    showInteractionFeedback,
  });
})(window);
