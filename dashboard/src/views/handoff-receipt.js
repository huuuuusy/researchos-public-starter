/* ResearchOS maintenance header.
 * 中文：HandoffReceipt 的窄只读视图；只呈现已归一化 projection，不生成判断或交互动作。
 * English: Narrow read-only HandoffReceipt view; renders normalized projection without generating judgments or actions.
 */

(function attachResearchOSHandoffReceiptView(global) {
  function row(label, value, deps) {
    if (!value) return "";
    return `<div class="work-session-handoff-row"><span>${deps.escapeHtml(label)}</span><p>${deps.escapeHtml(value)}</p></div>`;
  }

  function render(projection, deps = {}) {
    if (!projection) return "";
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const translate = deps.translate || ((key) => key);
    const stateLabel = (name, state) => translate(`handoffReceiptState_${name}_${state}`);
    const source = projection.sourceRevision;
    const forbidden = projection.forbiddenActions;
    const target = projection.targetClient;
    const content = projection.contentState === "included";
    return `<aside class="work-session-completed-purpose work-session-handoff-receipt" data-handoff-receipt-projection data-handoff-id="${escapeHtml(projection.handoffId)}">
      <header><div><span>${escapeHtml(translate("handoffReceiptEyebrow"))}</span><strong>${escapeHtml(translate("handoffReceiptTitle"))}</strong></div><small>${escapeHtml(translate("handoffReceiptReadOnly"))}</small></header>
      ${row(translate("handoffReceiptSourceRevision"), stateLabel("source", source.state), { escapeHtml })}
      ${row(translate("handoffReceiptLastJudgment"), content ? projection.lastJudgment.text : stateLabel("judgment", projection.lastJudgment.state), { escapeHtml })}
      ${row(translate("handoffReceiptOpenBoundary"), content ? projection.openBoundary.text : stateLabel("boundary", projection.openBoundary.state), { escapeHtml })}
      ${row(translate("handoffReceiptNextSafeAction"), content ? projection.nextSafeAction.text : stateLabel("action", projection.nextSafeAction.state), { escapeHtml })}
      ${forbidden.items.length ? `<div class="work-session-handoff-row"><span>${escapeHtml(translate("handoffReceiptForbidden"))}</span><ul>${forbidden.items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>` : row(translate("handoffReceiptForbidden"), stateLabel("forbidden", forbidden.state), { escapeHtml })}
      ${row(translate("handoffReceiptTarget"), `${target.kind} · ${target.surface} · ${translate("handoffReceiptTargetRequested")}`, { escapeHtml })}
      <p class="work-session-handoff-limitation">${escapeHtml(translate("handoffReceiptLimitation"))}</p>
    </aside>`;
  }

  global.ResearchOSHandoffReceiptView = Object.freeze({ render });
})(window);
