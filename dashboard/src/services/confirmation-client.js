/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端客户端「confirmation」；集中管理 /confirmation-withdraw 撤回和本地 fallback 规则。
 *   旧的 /confirmation 提交路径已退役，前端不再提交确认。
 * English: Frontend confirmation client for the ResearchOS dashboard; centralizes /confirmation-withdraw withdrawals and local fallback rules.
 *   The old /confirmation submit path is retired; the frontend no longer submits confirmations.
 */

(function attachResearchOSConfirmationClient(global) {
  const CONFIRMATION_WITHDRAW_ENDPOINT = "/confirmation-withdraw";

  function confirmationSyncResult(ok = false) {
    return { ok: Boolean(ok), localOnly: !ok, syncStatus: ok ? "synced" : "local" };
  }

  async function withdrawConfirmationPayload(decisionId = "", deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") return confirmationSyncResult(false);
    try {
      // 中文：撤回只改变候选队列状态，不删除 canonical Markdown 证据。
      // English: Withdrawal changes candidate-queue state only; it does not delete canonical Markdown evidence.
      const response = await fetcher(CONFIRMATION_WITHDRAW_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision_id: decisionId || "" }),
      });
      return confirmationSyncResult(Boolean(response?.ok));
    } catch {
      return confirmationSyncResult(false);
    }
  }

  global.ResearchOSConfirmationClient = Object.freeze({
    confirmationSyncResult,
    withdrawConfirmationPayload,
    withdrawEndpoint: CONFIRMATION_WITHDRAW_ENDPOINT,
  });
})(window);
