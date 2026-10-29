/* ResearchOS maintenance header.
 * 中文：Projection-first UI 的 Codex task 路由视图；只解释后端 continuity receipt 与 exact thread runtime，不执行 transport。
 * English: Codex task route view for the projection-first UI; interprets backend continuity receipts and exact-thread runtime state without dispatching transport.
 */

(function attachResearchOSCodexThreadRouter(global) {
  "use strict";

  const ROUTES = Object.freeze(["continue_exact_thread", "create_new_task", "copy_only"]);
  const THREAD_STATES = Object.freeze(["resumable", "closed", "stale", "ambiguous", "missing", "unknown"]);

  function routeError(code) {
    const error = new Error(code);
    error.code = code;
    return error;
  }

  function clean(value = "") {
    return String(value ?? "").trim();
  }

  function safeArray(value = []) {
    return Array.isArray(value) ? value : [];
  }

  function dedupe(values = []) {
    return [...new Set(safeArray(values).map(clean).filter(Boolean))];
  }

  function deepFreeze(value) {
    if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
    Object.values(value).forEach(deepFreeze);
    return Object.freeze(value);
  }

  function copyDecision(reasonCodes = [], transportState = "identity_unverified", threadId = "") {
    return {
      fallback_route: "copy_only",
      intended_route: "copy_only",
      reason_codes: dedupe(reasonCodes),
      recommended_route: "copy_only",
      requires_confirmation: false,
      thread_id: clean(threadId),
      transport_state: transportState,
    };
  }

  function decide({ publicStarter = false, routeReceipt = null, runtime = {} } = {}) {
    const identity = routeReceipt?.identity && typeof routeReceipt.identity === "object"
      ? routeReceipt.identity
      : null;
    const receiptThreadId = clean(identity?.thread_id);
    if (publicStarter === true) {
      return deepFreeze(copyDecision(["public_policy", "copy_only_user_controlled"], "public_policy_blocked", receiptThreadId));
    }
    if (!routeReceipt || clean(routeReceipt.status) !== "ready" || !identity) {
      return deepFreeze(copyDecision(["route_receipt_not_ready"], "identity_unverified", receiptThreadId));
    }
    if (identity.thread_title_used_for_identity !== false) {
      return deepFreeze(copyDecision(["thread_identity_contract_invalid"], "identity_unverified", receiptThreadId));
    }

    const threadState = THREAD_STATES.includes(clean(runtime.thread_state))
      ? clean(runtime.thread_state)
      : "unknown";
    const runtimeThreadId = clean(runtime.exact_thread_id);
    const continued = identity.continued_from_prior === true;
    const driftReasons = dedupe(identity.drift_reasons);
    let intendedRoute = "create_new_task";
    let reasonCodes = [];

    if (continued) {
      if (driftReasons.length) {
        intendedRoute = "copy_only";
        reasonCodes = ["continuity_receipt_conflict", ...driftReasons];
      } else if (!receiptThreadId || ["ambiguous", "missing", "unknown"].includes(threadState)) {
        intendedRoute = "copy_only";
        reasonCodes = [threadState === "ambiguous" ? "thread_identity_ambiguous" : "exact_thread_unverifiable"];
      } else if (!runtimeThreadId || runtimeThreadId !== receiptThreadId) {
        intendedRoute = "copy_only";
        reasonCodes = ["exact_thread_id_mismatch"];
      } else if (["closed", "stale"].includes(threadState)) {
        intendedRoute = "create_new_task";
        reasonCodes = [threadState === "closed" ? "prior_thread_closed" : "prior_thread_stale"];
      } else if (threadState === "resumable") {
        intendedRoute = "continue_exact_thread";
        reasonCodes = ["same_bounded_episode", "exact_thread_resumable"];
      }
    } else {
      intendedRoute = "create_new_task";
      reasonCodes = driftReasons.length ? driftReasons : ["new_bounded_episode"];
    }

    if (intendedRoute === "copy_only") {
      return deepFreeze(copyDecision(reasonCodes, "identity_unverified", receiptThreadId));
    }

    const transportAvailable = runtime.transport_available === true;
    const routeAvailable = intendedRoute === "continue_exact_thread"
      ? runtime.continue_available !== false
      : runtime.create_available === true;
    const recommendedRoute = transportAvailable && routeAvailable ? intendedRoute : "copy_only";
    const transportState = recommendedRoute === intendedRoute ? "available" : "unavailable";
    if (recommendedRoute === "copy_only") reasonCodes.push(transportAvailable ? "route_transport_unavailable" : "transport_unavailable");
    return deepFreeze({
      fallback_route: "copy_only",
      intended_route: intendedRoute,
      reason_codes: dedupe(reasonCodes),
      recommended_route: recommendedRoute,
      requires_confirmation: recommendedRoute !== "copy_only",
      thread_id: receiptThreadId,
      transport_state: transportState,
    });
  }

  function applyOverride(decision = {}, requestedRoute = "copy_only", reason = "") {
    const route = clean(requestedRoute);
    const overrideReason = clean(reason);
    if (!ROUTES.includes(route)) throw routeError("invalid_thread_route_override");
    if (!overrideReason) throw routeError("thread_route_override_reason_required");
    if (route !== "copy_only" && route !== decision.intended_route) throw routeError("unsafe_thread_route_override");
    if (route !== "copy_only" && decision.transport_state !== "available") throw routeError("unsafe_thread_route_override");
    return deepFreeze({
      ...decision,
      recommended_route: route,
      requires_confirmation: route !== "copy_only",
      override: {
        original_route: clean(decision.recommended_route),
        reason: overrideReason,
        route,
      },
    });
  }

  global.ResearchOSCodexThreadRouter = Object.freeze({
    ROUTES,
    THREAD_STATES,
    applyOverride,
    decide,
  });
})(window);
