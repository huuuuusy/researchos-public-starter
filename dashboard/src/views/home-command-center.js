/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 视图「home command center」的纯 HTML 渲染层；不保存持久状态、不直接执行写入副作用。
 * English: Pure HTML rendering layer for the home command center dashboard view; stores no durable state and performs no write side effects.
 */

(function attachResearchOSHomeCommandCenterView(global) {
  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      sectionTranslate: deps.sectionTranslate || deps.translate || ((key) => key),
      translate: deps.translate || ((key) => key),
    };
  }

  function renderNowHtml(_model = {}, deps = {}) {
    const { escapeHtml, sectionTranslate, translate } = normalizeDeps(deps);
    return `
      <section class="now-surface" data-now-surface aria-label="${escapeHtml(sectionTranslate("sections.commandCenter"))}">
        <section class="now-research-choices" aria-label="${escapeHtml(translate("nowResearchChoicesLabel"))}">
          <div data-plugin-slot-host="workbench" hidden></div>
        </section>
      </section>
    `;
  }

  global.ResearchOSHomeCommandCenterView = Object.freeze({
    renderNowHtml,
  });
})(window);
