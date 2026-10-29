/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 可复用 UI 组件「segmented control」；只生成通用结构，业务语义由调用方传入。
 * English: Reusable ResearchOS dashboard UI component for segmented control; renders generic structure while callers provide domain semantics.
 */

(function attachResearchOSSegmentedControlComponent(global) {
  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
    };
  }

  function safeDataAttributeName(value = "") {
    const normalized = String(value || "").trim();
    return /^data-[a-zA-Z0-9_-]+$/.test(normalized) ? normalized : "";
  }

  function safeTagName(value = "span") {
    const normalized = String(value || "span").toLowerCase();
    return ["b", "em", "small", "span", "strong"].includes(normalized) ? normalized : "span";
  }

  function renderSegmentButton(option = {}, deps = {}) {
    const { escapeHtml } = normalizeDeps(deps);
    const value = String(option.value ?? option.id ?? "");
    const selected = Boolean(option.selected);
    const label = String(option.label ?? value);
    const labelTag = option.labelTag ? safeTagName(option.labelTag) : "";
    const countTag = option.countTag ? safeTagName(option.countTag) : "";
    const dataAttr = safeDataAttributeName(option.dataAttr || "");
    const className = global.ResearchOSUiCore.safeClassList(`${option.className || ""} ${selected ? "selected" : ""}`);
    const dataAttrHtml = dataAttr ? ` ${dataAttr}="${escapeHtml(value)}"` : "";
    const classHtml = className ? ` class="${escapeHtml(className)}"` : "";
    const titleHtml = option.title ? ` title="${escapeHtml(option.title)}"` : "";
    const disabledHtml = option.disabled ? " disabled" : "";
    const ariaPressed = option.ariaPressed === false ? "" : ` aria-pressed="${selected ? "true" : "false"}"`;
    const labelHtml = labelTag ? `<${labelTag}>${escapeHtml(label)}</${labelTag}>` : escapeHtml(label);
    const countHtml = option.count === undefined || option.count === null || option.count === ""
      ? ""
      : `<${countTag || "span"}>${escapeHtml(String(option.count))}</${countTag || "span"}>`;
    return `<button type="button"${classHtml} data-action-kind="navigation"${dataAttrHtml}${ariaPressed}${titleHtml}${disabledHtml}>${labelHtml}${countHtml}</button>`;
  }

  function renderSegmentButtons(options = [], deps = {}) {
    return (options || []).map((option) => renderSegmentButton(option, deps)).join("");
  }

  global.ResearchOSSegmentedControlComponent = Object.freeze({
    renderSegmentButtons,
  });
  global.document?.documentElement?.setAttribute("data-researchos-segmented-control-component", "ready");
})(window);
