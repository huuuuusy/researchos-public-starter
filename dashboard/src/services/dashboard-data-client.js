/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端客户端「dashboard data」；集中管理 generated dashboard JSON 加载规则。
 * English: Frontend dashboard-data client for ResearchOS; centralizes generated dashboard JSON loading rules.
 */

(function attachResearchOSDashboardDataClient(global) {
  const DASHBOARD_DATA_ENDPOINT = "data/researchos-dashboard.json";
  const DASHBOARD_DATA_MISSING_MESSAGE = "Dashboard data not found. Start ResearchOS with scripts/start_researchos.py, which builds the missing projection.";

  async function loadDashboardData(deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") throw new Error(DASHBOARD_DATA_MISSING_MESSAGE);
    const response = await fetcher(DASHBOARD_DATA_ENDPOINT, { cache: "no-store" });
    if (!response?.ok) throw new Error(DASHBOARD_DATA_MISSING_MESSAGE);
    return response.json();
  }

  global.ResearchOSDashboardDataClient = Object.freeze({
    endpoint: DASHBOARD_DATA_ENDPOINT,
    loadDashboardData,
    missingMessage: DASHBOARD_DATA_MISSING_MESSAGE,
  });
})(window);
