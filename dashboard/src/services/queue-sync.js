/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 临时队列同步服务；集中管理本地 UI 队列到本地 HTTP 服务的 POST/fallback 规则。
 * English: Temporary queue sync service for the ResearchOS dashboard; centralizes POST/fallback rules from local UI queues to the local HTTP service.
 */

(function attachResearchOSQueueSyncService(global) {
  const QUEUE_SYNC_ENDPOINTS = Object.freeze({
    cardGroupDissolutions: "/group-dissolutions",
    cardGroups: "/card-groups",
  });

  async function postJson(endpoint = "", payload = {}, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (!endpoint || typeof fetcher !== "function") return "local";
    try {
      const response = await fetcher(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload || {}),
      });
      return response?.ok ? "synced" : "local";
    } catch {
      return "local";
    }
  }

  function syncItems(endpoint = "", items = [], deps = {}) {
    return postJson(endpoint, { items: Array.isArray(items) ? items : [] }, deps);
  }

  function syncGroups(groups = [], deps = {}) {
    return postJson(QUEUE_SYNC_ENDPOINTS.cardGroups, { groups: Array.isArray(groups) ? groups : [] }, deps);
  }

  function syncCardGroupDissolutions(items = [], deps = {}) {
    return syncItems(QUEUE_SYNC_ENDPOINTS.cardGroupDissolutions, items, deps);
  }

  global.ResearchOSQueueSyncService = Object.freeze({
    endpoints: QUEUE_SYNC_ENDPOINTS,
    postJson,
    syncCardGroupDissolutions,
    syncGroups,
    syncItems,
  });
})(window);
