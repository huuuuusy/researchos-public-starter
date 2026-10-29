/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「maintenance workbench」；负责 DOM 事件绑定，把副作用回调交还 app。
 * English: Workbench interaction adapter for maintenance workbench in the ResearchOS dashboard; owns DOM event binding and returns side effects to app callbacks.
 */

(function attachResearchOSMaintenanceWorkbenchService(global) {
  const scrollIntoView = global.ResearchOSInteractions?.scrollIntoView || ((target, options = {}) => target?.scrollIntoView?.(options));
  function autoUpdateChromeNodes(root = global.document) {
    return {
      button: root.getElementById("autoUpdateButton") || root.querySelector?.("[data-run-auto-update]") || null,
      result: root.getElementById("autoUpdateResult"),
      status: root.getElementById("autoUpdateStatus"),
      utilityDrawer: root.getElementById("utilityDrawer"),
    };
  }

  function autoUpdateButtonFrom(target = global.document) {
    if (target?.getElementById) return autoUpdateChromeNodes(target).button;
    return target;
  }

  function bindAutoUpdateButton(target = global.document, callbacks = {}) {
    const button = autoUpdateButtonFrom(target);
    if (!button) return;
    const { onRun = () => {} } = callbacks;
    button.onclick = (event) => {
      event.preventDefault();
      onRun({ button, event });
    };
  }

  function bindAutoUpdateResultEvents(root, callbacks = {}) {
    if (!root?.querySelectorAll) return;
    const { onRun = () => {} } = callbacks;
    root.querySelectorAll("[data-run-auto-update]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        onRun({ button, event });
      });
    });
  }

  function bindEvolutionDecisionEvents(root, callbacks = {}) {
    if (!root?.querySelectorAll) return;
    const { onDecision = () => {} } = callbacks;
    root.querySelectorAll("[data-evolution-decision]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        onDecision({ button, decision: button.dataset.evolutionDecision || "", event });
      });
    });
  }

  function syncAutoUpdateChrome({ button, root = global.document, running = false, disabled = false, status, labels = {} } = {}) {
    const nodes = autoUpdateChromeNodes(root);
    const targetButton = button || nodes.button;
    const targetStatus = status || nodes.status;
    if (targetButton) {
      targetButton.disabled = Boolean(running || disabled);
      targetButton.textContent = running ? labels.running || "" : labels.button || "";
    }
    if (targetStatus) {
      targetStatus.textContent = running ? labels.running || "" : labels.summary || "";
      targetStatus.className = `auto-update-status ${labels.tone || ""}`.trim();
    }
  }

  function focusAutoUpdateResult(root = global.document) {
    const nodes = autoUpdateChromeNodes(root);
    nodes.utilityDrawer?.setAttribute("open", "");
    scrollIntoView(nodes.result, { block: "nearest", behavior: "smooth" });
  }

  global.ResearchOSMaintenanceWorkbenchService = Object.freeze({
    bindAutoUpdateButton,
    bindAutoUpdateResultEvents,
    bindEvolutionDecisionEvents,
    focusAutoUpdateResult,
    syncAutoUpdateChrome,
  });
})(window);
