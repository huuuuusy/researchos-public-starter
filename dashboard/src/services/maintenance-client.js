/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端客户端「maintenance」；集中管理 /auto-update 请求和失败结果归一化。
 * English: Frontend maintenance client for the ResearchOS dashboard; centralizes /auto-update requests and failure-result normalization.
 */

(function attachResearchOSMaintenanceClient(global) {
  const AUTO_UPDATE_ENDPOINT = "/auto-update";
  const MAINTENANCE_ACTION_ENDPOINT = "/maintenance-action";
  const EVOLUTION_DECISION_ENDPOINT = "/evolution-decision";
  const EVOLUTION_PLAN_ENDPOINT = "/evolution-plan";

  function autoUpdateErrorResult(error = "Auto-update request failed") {
    return {
      ok: false,
      seconds: "",
      steps: [
        {
          label: "auto-update",
          ok: false,
          optional: false,
          output: error?.message || String(error || "Auto-update request failed"),
        },
      ],
    };
  }

  async function parseAutoUpdateResponse(response) {
    const payload = await response.json();
    return response.ok ? payload : { ...payload, ok: false };
  }

  async function loadEvolutionPlan(deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") throw new Error("Evolution plan service unavailable");
    const response = await fetcher(EVOLUTION_PLAN_ENDPOINT, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload?.message || "Evolution plan request failed");
    return payload;
  }

  async function runAutoUpdate(planId = "", deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") return autoUpdateErrorResult("Auto-update service unavailable");
    if (!planId) return autoUpdateErrorResult("A current evolution plan must be reviewed before refresh.");
    try {
      const response = await fetcher(AUTO_UPDATE_ENDPOINT, {
        method: "POST",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId }),
      });
      return parseAutoUpdateResponse(response);
    } catch (error) {
      return autoUpdateErrorResult(error);
    }
  }

  async function runMaintenanceAction(actionId = "", deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") return autoUpdateErrorResult("Maintenance action service unavailable");
    if (!actionId) return autoUpdateErrorResult("A registered maintenance action is required.");
    try {
      const response = await fetcher(MAINTENANCE_ACTION_ENDPOINT, {
        method: "POST",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: actionId }),
      });
      return parseAutoUpdateResponse(response);
    } catch (error) {
      return autoUpdateErrorResult(error);
    }
  }

  async function decideEvolutionPlan(planId = "", decision = "", deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") return { ok: false, message: "Evolution decision service unavailable" };
    if (!planId || !["deferred", "rejected"].includes(decision)) return { ok: false, message: "A current manual plan and explicit decision are required." };
    try {
      const response = await fetcher(EVOLUTION_DECISION_ENDPOINT, {
        method: "POST",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId, decision }),
      });
      const payload = await response.json();
      return response.ok ? payload : { ...payload, ok: false };
    } catch (error) {
      return { ok: false, message: error?.message || String(error || "Evolution decision request failed") };
    }
  }

  function createEvolutionPlanState(deps = {}) {
    const available = typeof deps.available === "function" ? deps.available : () => true;
    const onChange = typeof deps.onChange === "function" ? deps.onChange : () => {};
    let state = { plan: null, loading: false, error: "" };
    const snapshot = () => ({ ...state });
    const publish = (patch = {}) => {
      state = { ...state, ...patch };
      onChange(snapshot());
      return snapshot();
    };
    const refresh = async () => {
      if (!available() || state.loading) return snapshot();
      publish({ loading: true, error: "" });
      try {
        publish({ plan: await loadEvolutionPlan(deps), error: "" });
      } catch (error) {
        publish({ error: error?.message || String(error || "Evolution plan request failed") });
      } finally {
        publish({ loading: false });
      }
      return snapshot();
    };
    return Object.freeze({
      accept: (plan) => publish({ plan: plan || state.plan }),
      clear: () => publish({ plan: null, error: "" }),
      refresh,
      snapshot,
    });
  }

  global.ResearchOSMaintenanceClient = Object.freeze({
    autoUpdateErrorResult,
    createEvolutionPlanState,
    decideEvolutionPlan,
    endpoint: AUTO_UPDATE_ENDPOINT,
    evolutionDecisionEndpoint: EVOLUTION_DECISION_ENDPOINT,
    evolutionPlanEndpoint: EVOLUTION_PLAN_ENDPOINT,
    maintenanceActionEndpoint: MAINTENANCE_ACTION_ENDPOINT,
    loadEvolutionPlan,
    runAutoUpdate,
    runMaintenanceAction,
  });
})(window);
