/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 视图「error page」的纯 HTML 渲染层；不保存持久状态、不直接执行写入副作用。
 * English: Pure HTML rendering layer for the dashboard error page; stores no durable state and performs no write side effects.
 */

(function attachResearchOSErrorPageView(global) {
  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      translate: deps.translate || ((key) => key),
    };
  }

  function renderErrorPageHtml({ message = "", serviceHint = "" } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const technicalDetails = message
      ? `<details><summary>${escapeHtml(translate("error.details"))}</summary><code>${escapeHtml(message)}</code></details>`
      : "";
    return `${serviceHint}<main id="mainContent" class="error-page panel" data-startup-error tabindex="-1" aria-labelledby="startupErrorTitle" aria-live="assertive">
      <h1 id="startupErrorTitle">${escapeHtml(translate("error.title"))}</h1>
      <p>${escapeHtml(translate("error.body"))}</p>
      <button type="button" class="primary-button" data-action-kind="direct" data-dashboard-retry>${escapeHtml(translate("error.retry"))}</button>
      ${technicalDetails}
    </main>`;
  }

  global.ResearchOSErrorPageView = Object.freeze({
    renderErrorPageHtml,
  });
})(window);
