/* ResearchOS maintenance header.
 * 中文：默认关闭的 Handoff/Admit 第三屏候选视图；只组合既有路线、receipt 与 Review，不执行判断。
 * English: Default-off Handoff/Admit third-surface candidate; composes existing routes, receipt, and Review without deciding.
 */

(function attachResearchOSHandoffAdmitSurfaceView(global) {
  function render(model, options = {}, deps = {}) {
    if (!model || model.mode !== "handoff_admit_candidate") return "";
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const translate = deps.translate || ((key) => key);
    const receiptHtml = global.ResearchOSHandoffReceiptView?.render(
      options.handoffReceiptProjection || null, { escapeHtml, translate },
    ) || "";
    const background = model.routes.background;
    const review = model.routes.review;
    return `<section class="work-session-handoff-admit-candidate" data-handoff-admit-candidate>
      <header>
        <div><span>${escapeHtml(translate("handoffAdmitEyebrow"))}</span><h3>${escapeHtml(model.goal)}</h3></div>
        <small>${escapeHtml(translate("handoffAdmitCandidateBadge"))}</small>
      </header>
      <p class="work-session-handoff-limitation">${escapeHtml(translate("handoffAdmitCandidateBoundary"))}</p>
      <section class="work-session-handoff-routes" aria-label="${escapeHtml(translate("handoffAdmitRouteTitle"))}">
        <article><strong>${escapeHtml(translate("handoffAdmitManualTitle"))}</strong><p>${escapeHtml(translate("handoffAdmitManualBody"))}</p><small>${escapeHtml(translate("handoffAdmitManualOutcome"))}</small></article>
        <article><strong>${escapeHtml(translate("handoffAdmitCodexTitle"))}</strong><p>${escapeHtml(translate("handoffAdmitCodexBody"))}</p><button type="button" class="primary" data-action-kind="handoff" data-work-session-copy-task>${escapeHtml(translate("handoffAdmitCodexCopy"))}</button><small>${escapeHtml(translate("handoffAdmitCodexOutcome"))}</small></article>
        <article><strong>${escapeHtml(translate("handoffAdmitBackgroundTitle"))}</strong><p>${escapeHtml(translate(background.available ? "handoffAdmitBackgroundBody" : "handoffAdmitBackgroundUnavailable"))}</p><small>${escapeHtml(translate(background.available ? "handoffAdmitBackgroundRegistered" : "handoffAdmitBackgroundNoAction"))}</small></article>
      </section>
      <aside class="work-session-completed-purpose"><strong>${escapeHtml(translate("handoffAdmitResultTitle"))}</strong><p>${escapeHtml(`${translate(`handoffAdmitResultStatus_${model.result.status}`)} · ${translate(`handoffAdmitResultMode_${model.result.mode}`)}`)}</p></aside>
      ${receiptHtml}
      <section class="work-session-handoff-review">
        <strong>${escapeHtml(translate("handoffAdmitReviewTitle"))}</strong>
        <p>${escapeHtml(translate("handoffAdmitReviewBody"))}</p>
        <button type="button" data-action-kind="handoff" data-work-session-prepare>${escapeHtml(translate(review.outcome === "open_existing_review" ? "handoffAdmitReviewOpen" : "handoffAdmitReviewPrepare"))}</button>
        <small>${escapeHtml(translate("handoffAdmitReviewOutcome"))}</small>
      </section>
      <footer><small>${escapeHtml(translate("handoffAdmitCandidateFooter"))}</small></footer>
    </section>`;
  }

  global.ResearchOSHandoffAdmitSurfaceView = Object.freeze({ render });
})(window);
