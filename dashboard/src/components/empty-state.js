/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 可复用 UI 组件「empty state」；只生成通用结构，业务语义由调用方传入。
 * English: Reusable ResearchOS dashboard UI component for empty state; renders generic structure while callers provide domain semantics.
 */

(function attachResearchOSEmptyStateComponent(global) {
  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
    };
  }

  function safeBlockTagName(value = "p") {
    const normalized = String(value || "p").toLowerCase();
    return ["article", "aside", "div", "p", "section"].includes(normalized) ? normalized : "p";
  }

  function safeTextTagName(value = "p") {
    const normalized = String(value || "p").toLowerCase();
    return ["em", "p", "small", "span", "strong"].includes(normalized) ? normalized : "p";
  }

  function renderEmptyState({ message = "", title = "", eyebrow = "", className = "empty-state", tag = "p", bodyTag = "p" } = {}, deps = {}) {
    const { escapeHtml } = normalizeDeps(deps);
    const safeTag = safeBlockTagName(tag);
    const safeBodyTag = safeTextTagName(bodyTag);
    const classes = global.ResearchOSUiCore.safeClassList(className);
    const classHtml = classes ? ` class="${escapeHtml(classes)}"` : "";
    if (!title && !eyebrow && safeTag === "p") {
      return `<p${classHtml}>${escapeHtml(message)}</p>`;
    }
    return `
      <${safeTag}${classHtml}>
        ${eyebrow ? `<span>${escapeHtml(eyebrow)}</span>` : ""}
        ${title ? `<strong>${escapeHtml(title)}</strong>` : ""}
        ${message ? `<${safeBodyTag}>${escapeHtml(message)}</${safeBodyTag}>` : ""}
      </${safeTag}>
    `;
  }

  function renderEmptyCard({ message = "", title = "", eyebrow = "", actionHtml = "", className = "empty-card", tag = "article" } = {}, deps = {}) {
    const { escapeHtml } = normalizeDeps(deps);
    const safeTag = safeBlockTagName(tag);
    const classes = global.ResearchOSUiCore.safeClassList(className);
    const classHtml = classes ? ` class="${escapeHtml(classes)}"` : "";
    return `
      <${safeTag}${classHtml}>
        <div>
          ${eyebrow ? `<span>${escapeHtml(eyebrow)}</span>` : ""}
          ${title ? `<strong>${escapeHtml(title)}</strong>` : ""}
          ${message ? `<p>${escapeHtml(message)}</p>` : ""}
        </div>
        ${actionHtml || ""}
      </${safeTag}>
    `;
  }

  function renderEmptyList(items = [], mapper = () => "", empty = {}, deps = {}) {
    const list = Array.isArray(items) ? items.filter(Boolean) : [];
    if (list.length) return list.map(mapper).join("");
    return renderEmptyState(typeof empty === "string" ? { message: empty } : empty, deps);
  }

  global.ResearchOSEmptyStateComponent = Object.freeze({
    renderEmptyCard,
    renderEmptyList,
    renderEmptyState,
  });
  global.document?.documentElement?.setAttribute("data-researchos-empty-state-component", "ready");
})(window);
