/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 可复用 UI 组件「metric primitives」；只生成通用结构，业务语义由调用方传入。
 * English: Reusable ResearchOS dashboard UI component for metric primitives; renders generic structure while callers provide domain semantics.
 */

(function attachResearchOSMetricPrimitivesComponent(global) {
  function simpleNumber(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : 0;
  }

  global.ResearchOSMetricPrimitivesComponent = Object.freeze({
    simpleNumber,
  });
  global.document?.documentElement?.setAttribute("data-researchos-metric-primitives-component", "ready");
})(window);
