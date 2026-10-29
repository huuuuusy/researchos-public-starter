/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard app 层 copy/button 适配器；把 clipboard 与 button 组合逻辑从 app.js 拆出。
 * English: App-layer copy/button adapter for the ResearchOS dashboard; moves clipboard and button composition out of app.js.
 */

(function attachResearchOSAppCopyActionsService(global) {
  function normalizeDeps(deps = {}) {
    return {
      buttonsComponent: deps.buttonsComponent,
      clipboardWorkbenchService: deps.clipboardWorkbenchService,
      translate: deps.translate || ((key) => key),
      uiCore: deps.uiCore,
    };
  }

  function createAppCopyActions(deps = {}) {
    const { buttonsComponent, clipboardWorkbenchService, translate, uiCore } = normalizeDeps(deps);

    function copyValueButton(value, options = {}) {
      return buttonsComponent.copyValueButton(
        {
          value,
          label: options.label || translate("actions.copy"),
          title: options.title || "",
          className: options.className || "",
          actionAttribute: options.actionAttribute || "",
          actionKind: options.actionKind || "",
        },
        { escapeHtml: uiCore.escapeHtml },
      );
    }

    async function copyPlainText(value) {
      return clipboardWorkbenchService.copyPlainText(value, {
        writeClipboardText: uiCore.writeClipboardText,
      });
    }

    async function copyEncodedPayload(encodedPayload) {
      return clipboardWorkbenchService.copyEncodedPayload(encodedPayload, {
        decodeDataPayload: uiCore.decodeDataPayload,
        writeClipboardText: uiCore.writeClipboardText,
      });
    }

    return Object.freeze({
      copyEncodedPayload,
      copyPlainText,
      copyValueButton,
    });
  }

  global.ResearchOSAppCopyActionsService = Object.freeze({
    createAppCopyActions,
  });
  global.document?.documentElement?.setAttribute("data-researchos-app-copy-actions", "ready");
})(window);
