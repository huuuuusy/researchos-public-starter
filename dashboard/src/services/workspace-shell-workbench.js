/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「workspace shell workbench」；负责 DOM 事件绑定，把副作用回调交还 app。
 * English: Workbench interaction adapter for workspace shell workbench in the ResearchOS dashboard; owns DOM event binding and returns side effects to app callbacks.
 */

(function attachResearchOSWorkspaceShellWorkbenchService(global) {
  const interactionPrimitives = global.ResearchOSInteractions || {};
  const focusElement = interactionPrimitives.focusElement || ((target) => {
    target?.focus?.();
    return Boolean(target);
  });
  const scrollIntoView = interactionPrimitives.scrollIntoView || ((target, options = {}) => {
    target?.scrollIntoView?.(options);
    return Boolean(target);
  });

  function workspaceShellNodes(root = global.document) {
    return {
      panels: Array.from(root.querySelectorAll("[data-workspace-panel]")),
      switcher: root.querySelector(".workspace-switcher"),
      tabs: Array.from(root.querySelectorAll("button[data-workspace-tab]")),
    };
  }

  function dashboardChromeNodes(root = global.document) {
    return {
      generatedAt: root.getElementById("generatedAt"),
      languageSelect: root.getElementById("languageSelect"),
      serviceModeBanner: root.getElementById("serviceModeBanner"),
      subtitle: root.getElementById("subtitle"),
      themePicker: root.getElementById("themePicker"),
    };
  }

  function setText(node, value = "") {
    if (node) node.textContent = value;
  }

  function showStartupError(root = global.document, html = "") {
    if (!root?.body) return false;
    root.body.innerHTML = html;
    const errorSurface = root.querySelector?.("[data-startup-error], #mainContent") || null;
    focusElement(errorSurface);
    return Boolean(errorSurface);
  }

  function applyDashboardHeader(root = global.document, header = {}) {
    const nodes = dashboardChromeNodes(root);
    setText(nodes.subtitle, header.subtitle || "");
    setText(nodes.generatedAt, header.generatedAt || "");
  }

  function syncWorkspaceShell(root = global.document, options = {}) {
    const {
      hintFor = (tab) => tab,
      labelFor = (tab) => tab,
      focusMode = "none",
      scroll = false,
      selectedWorkspace = "now",
    } = options;
    if (root.documentElement) {
      root.documentElement.dataset.currentWorkspace = selectedWorkspace;
    }
    const nodes = workspaceShellNodes(root);
    nodes.tabs.forEach((button) => {
      const tab = button.dataset.workspaceTab || "";
      const active = tab === selectedWorkspace;
      const label = labelFor(tab);
      const escapeHtml = global.ResearchOSUiCore?.escapeHtml;
      button.innerHTML = `<strong>${escapeHtml(label)}</strong><span>${escapeHtml(hintFor(tab))}</span>`;
      button.setAttribute("aria-label", label);
      button.title = hintFor(tab);
      button.classList.toggle("selected", active);
      button.setAttribute("aria-selected", String(active));
      button.setAttribute("tabindex", active ? "0" : "-1");
    });
    let activePanel = null;
    nodes.panels.forEach((panel) => {
      const active = panel.dataset.workspacePanel === selectedWorkspace;
      panel.classList.toggle("workspace-active", active);
      panel.hidden = !active;
      panel.setAttribute("aria-hidden", String(!active));
      if (active) activePanel = panel;
    });
    if (scroll || focusMode !== "none") {
      global.setTimeout(() => {
        const activeTab = nodes.tabs.find((button) => button.dataset.workspaceTab === selectedWorkspace);
        if (focusMode === "tab") {
          focusElement(activeTab, { preventScroll: true });
        } else if (focusMode === "panel") {
          focusElement(activePanel, { ensureTabIndex: true, preventScroll: true });
        }
        if (!scroll) return;
        if (typeof global.scrollTo === "function") {
          global.scrollTo({ top: 0, left: 0, behavior: "auto" });
        } else {
          scrollIntoView(activePanel || nodes.switcher, { block: "start", behavior: "auto" });
        }
      }, 0);
    }
  }

  function bindWorkspaceTabs(root = global.document, callbacks = {}) {
    const { onWorkspaceTab = () => {} } = callbacks;
    workspaceShellNodes(root).tabs.forEach((button) => {
      button.onclick = () => onWorkspaceTab({ button, focusMode: "tab", scroll: true, tabId: button.dataset.workspaceTab || "now" });
      button.onkeydown = (event) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        const tabs = workspaceShellNodes(root).tabs;
        const currentIndex = Math.max(0, tabs.indexOf(button));
        const nextIndex = event.key === "Home"
          ? 0
          : event.key === "End"
            ? tabs.length - 1
            : (currentIndex + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
        const next = tabs[nextIndex];
        onWorkspaceTab({ button: next, focusMode: "tab", scroll: false, tabId: next?.dataset.workspaceTab || "now" });
      };
    });
  }

  function bindWorkspaceLaunchers(root = global.document, callbacks = {}) {
    const { onWorkspace = () => {} } = callbacks;
    root?.querySelectorAll?.("[data-open-workspace]").forEach((button) => {
      button.onclick = (event) => onWorkspace({
        button,
        event,
        focusMode: "panel",
        scroll: true,
        workspace: button.dataset.openWorkspace || "now",
      });
    });
  }

  function bindAssetDetailLauncher(root = global.document, callbacks = {}) {
    const { onAssetDetail = () => {} } = callbacks;
    root.querySelectorAll(".asset-detail-launcher [data-asset-detail]").forEach((button) => {
      button.onclick = (event) => onAssetDetail({
        button,
        event,
        detail: button.dataset.assetDetail || "",
      });
    });
  }

  function bindProductFlowEvents(root, callbacks = {}) {
    if (!root) return;
    const { onProductWorkspace = () => {} } = callbacks;
    root.querySelectorAll("[data-product-workspace]").forEach((button) => {
      button.addEventListener("click", (event) => {
        onProductWorkspace({
          button,
          event,
          targetId: button.dataset.scrollTarget || "",
          workspace: button.dataset.productWorkspace || "now",
        });
      });
    });
  }

  function scrollToDashboardTarget(targetId = "") {
    if (!targetId) return;
    global.setTimeout(() => {
      scrollIntoView(dashboardTarget(global.document, targetId), { block: "start", behavior: "smooth" });
    }, 0);
  }

  function dashboardTarget(root = global.document, targetId = "") {
    if (!root || !targetId) return null;
    return root.getElementById(targetId);
  }

  function isAssetDetailPanel(panelIds = [], targetId = "") {
    return Array.isArray(panelIds) && panelIds.includes(targetId);
  }

  function syncAssetDetailPanels(root = global.document, options = {}) {
    const {
      fallbackPanel = "materialRadar",
      onSelectedPanel = (panelId) => panelId,
      panelIds = [],
      selectedPanel = "",
    } = options;
    const panels = Array.from(root.querySelectorAll("[data-asset-detail-panel]"));
    if (!panels.length) return selectedPanel;
    const drawer = root.querySelector(".asset-detail-drawer");
    let activePanel = selectedPanel;
    if (drawer && !drawer.open && activePanel) {
      activePanel = onSelectedPanel("") || "";
    }
    if (!isAssetDetailPanel(panelIds, activePanel)) {
      activePanel = onSelectedPanel(fallbackPanel) || fallbackPanel;
    }
    const sourceGrid = root.querySelector(".asset-detail-drawer > .source-map-grid");
    if (sourceGrid) {
      sourceGrid.hidden = !activePanel || activePanel === "cardGroupWorkbench";
    }
    root.querySelectorAll(".asset-detail-launcher [data-asset-detail]").forEach((button) => {
      const active = button.dataset.assetDetail === activePanel;
      button.classList.toggle("selected", active);
      button.setAttribute("aria-pressed", String(active));
    });
    panels.forEach((panel) => {
      const active = panel.dataset.assetDetailPanel === activePanel;
      panel.hidden = !active;
      panel.classList.toggle("asset-detail-active", active);
    });
    return activePanel;
  }

  function openAssetDetailPanel(root = global.document, options = {}) {
    const {
      fallbackPanel = "materialRadar",
      panelIds = [],
      selectedPanel = "",
      targetId = "",
      writePanel = (panelId) => panelId,
    } = options;
    if (!isAssetDetailPanel(panelIds, targetId)) return selectedPanel;
    const activePanel = writePanel(targetId) || targetId;
    root.querySelector(".asset-detail-drawer")?.setAttribute("open", "");
    return syncAssetDetailPanels(root, {
      fallbackPanel,
      onSelectedPanel: writePanel,
      panelIds,
      selectedPanel: activePanel,
    });
  }

  function focusDashboardTarget(root = global.document, targetId = "", options = {}) {
    if (!targetId) return;
    const {
      focusClass = "section-focus",
      focusTimeout = 1400,
    } = options;
    const target = dashboardTarget(root, targetId);
    if (!target) return;
    if (target.tagName === "DETAILS") {
      target.open = true;
    }
    const collapsedParent = target.closest("details:not([open])");
    if (collapsedParent) {
      collapsedParent.open = true;
    }
    const panel = target.closest(".panel") || target;
    focusElement(target, { ensureTabIndex: true, preventScroll: true });
    scrollIntoView(panel, { block: "start", behavior: "smooth" });
    panel.classList.add(focusClass);
    global.setTimeout(() => panel.classList.remove(focusClass), focusTimeout);
  }

  global.ResearchOSWorkspaceShellWorkbenchService = Object.freeze({
    applyDashboardHeader,
    bindAssetDetailLauncher,
    bindProductFlowEvents,
    bindWorkspaceLaunchers,
    bindWorkspaceTabs,
    dashboardChromeNodes,
    dashboardTarget,
    focusDashboardTarget,
    isAssetDetailPanel,
    openAssetDetailPanel,
    scrollToDashboardTarget,
    showStartupError,
    syncAssetDetailPanels,
    syncWorkspaceShell,
    workspaceShellNodes,
  });
})(window);
