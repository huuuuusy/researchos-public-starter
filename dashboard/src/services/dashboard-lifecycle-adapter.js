/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard lifecycle adapter；集中声明 app 回调源的命名与 header 更新包装。
 * English: Dashboard lifecycle adapter for ResearchOS; centralizes app callback source names and header update wrapping.
 */

(function attachResearchOSDashboardLifecycleAdapter(global) {
  const DASHBOARD_LIFECYCLE_CALLBACK_SOURCE_NAMES = Object.freeze({
    applyTheme: "applyTheme",
    applyTranslations: "applyTranslations",
    bindDashboardButtonTooltips: "bindDashboardButtonTooltips",
    bindDashboardInteractiveSurfaces: "bindDashboardInteractiveSurfaces",
    bindWorkspaceTabs: "bindWorkspaceTabs",
    ensureSelectedPreviewLoaded: "ensureSelectedPreviewLoaded",
    renderPluginLibrarySlots: "renderPluginLibrarySlots",
    renderHomeCommandCenter: "renderHomeCommandCenter",
    renderMarkdownPreview: "renderMarkdownPreview",
    renderPluginSlots: "renderPluginSlots",
    renderUnifiedInbox: "renderUnifiedInbox",
    setupThemePicker: "setupThemePicker",
  });

  function callbackFromSource(source = {}, sourceName = "") {
    const callback = source?.[sourceName];
    return typeof callback === "function" ? callback : undefined;
  }

  function applyDashboardHeader(renderState = {}, options = {}) {
    const source = options.source || global;
    const applyHeader = options.applyDashboardHeader || callbackFromSource(source, "applyDashboardHeader");
    if (typeof applyHeader === "function") {
      applyHeader(renderState.header || {});
    }
  }

  function lifecycleSource(renderState = {}, options = {}) {
    const source = options.source || global;
    return Object.freeze({
      ...Object.fromEntries(
        Object.entries(DASHBOARD_LIFECYCLE_CALLBACK_SOURCE_NAMES)
          .map(([callbackName, sourceName]) => [callbackName, callbackFromSource(source, sourceName)])
          .filter(([, callback]) => typeof callback === "function")
      ),
      updateHeader: () => applyDashboardHeader(renderState, options),
    });
  }

  global.ResearchOSDashboardLifecycleAdapter = Object.freeze({
    applyDashboardHeader,
    callbackFromSource,
    callbackSourceNames: DASHBOARD_LIFECYCLE_CALLBACK_SOURCE_NAMES,
    lifecycleSource,
  });
})(window);
