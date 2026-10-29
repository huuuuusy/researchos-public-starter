/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 可复用 UI 组件「buttons」；只生成通用结构，业务语义由调用方传入。
 * English: Reusable ResearchOS dashboard UI component for buttons; renders generic structure while callers provide domain semantics.
 */

(function attachResearchOSButtonsComponent(global) {
  function copyValueButton(
    {
      value = "",
      label = "Copy",
      title = "",
      className = "",
      actionAttribute = "",
      actionKind = "handoff",
    } = {},
    deps = {},
  ) {
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const safeActionAttribute = /^data-[a-z0-9-]+$/.test(actionAttribute) ? actionAttribute : "";
    const safeActionKind = ["direct", "preview-confirm", "handoff", "navigation"].includes(actionKind)
      ? actionKind
      : "";
    const classAttr = className ? ` class="${escapeHtml(className)}"` : "";
    const titleAttr = title ? ` title="${escapeHtml(title)}"` : "";
    const actionAttr = safeActionAttribute ? ` ${safeActionAttribute}` : "";
    const actionKindAttr = safeActionKind ? ` data-action-kind="${escapeHtml(safeActionKind)}"` : "";
    return `<button type="button"${classAttr}${actionAttr}${actionKindAttr} data-copy-value="${escapeHtml(value)}"${titleAttr}>${escapeHtml(label)}</button>`;
  }

  global.ResearchOSButtonsComponent = Object.freeze({
    copyValueButton,
  });
  global.document?.documentElement?.setAttribute("data-researchos-buttons-component", "ready");
})(window);
