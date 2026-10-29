/* ResearchOS maintenance header.
 * 中文：浏览器动作的通用门禁；集中验证 ActionSpec、策略、确认、owner 调度与即时反馈，不拥有领域状态或持久回执。
 * English: Generic browser action gateway for ActionSpec validation, policy, confirmation, owner dispatch, and immediate feedback without domain ownership or durable receipts.
 */

(function attachResearchOSActionGateway(global) {
  const identifier = /^[a-z][a-z0-9_]*$/;
  const privilegedEffects = new Set(["mutate_attention", "execute_bounded", "propose_writeback", "mutate_canonical"]);

  function actionKey(pluginId = "", actionId = "") {
    const plugin = String(pluginId || "").trim();
    const action = String(actionId || "").trim();
    return identifier.test(plugin) && identifier.test(action) ? `${plugin}:${action}` : "";
  }

  function create(options = {}) {
    const interaction = options.interactionContract || global.ResearchOSInteractionContract;
    const registry = new Map();
    const clock = typeof options.now === "function" ? options.now : () => new Date().toISOString();
    const gatewayInstanceId = String(
      options.gatewayId || global.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    ).replace(/[^a-zA-Z0-9._-]/g, "-").slice(0, 96) || "anonymous";
    let feedbackSequence = 0;

    function feedback({ actionId = "", effect = "", ok = false, outcome = null, pluginId = "", reason = "", requestId = "", reversible = false, status = "rejected" } = {}) {
      feedbackSequence += 1;
      return Object.freeze({
        action: Object.freeze({ action_id: String(actionId || ""), plugin_id: String(pluginId || "") }),
        durability: "ephemeral_ui_feedback",
        effect: String(effect || ""),
        feedback_id: `action-feedback:${gatewayInstanceId}:${feedbackSequence}`,
        gateway_instance_id: gatewayInstanceId,
        limitations: Object.freeze(["not_durable_receipt", "not_authority", "not_recovery_coordinate"]),
        ok: ok === true,
        outcome,
        reason: String(reason || ""),
        request_id: String(requestId || `action-request:${gatewayInstanceId}:${feedbackSequence}`),
        reversible: reversible === true,
        schema_id: "researchos-action-feedback-v1",
        sequence: feedbackSequence,
        status: String(status || "rejected"),
        timestamp: String(clock()),
      });
    }

    function reject(request = {}, reason = "action_rejected") {
      return feedback({
        actionId: request.actionId,
        pluginId: request.pluginId,
        reason,
        requestId: request.requestId,
        status: "rejected",
      });
    }

    function register(pluginId = "", actionId = "", registration = {}) {
      const key = actionKey(pluginId, actionId);
      const spec = registration?.spec;
      if (!key || registry.has(key) || typeof registration.execute !== "function") return false;
      if (typeof interaction?.validateActionSpec !== "function" || interaction.validateActionSpec(spec).length) return false;
      if (String(spec?.id || "") !== `${pluginId}.${actionId}`) return false;
      registry.set(key, Object.freeze({
        authorize: typeof registration.authorize === "function" ? registration.authorize : null,
        execute: registration.execute,
        owner: String(registration.owner || pluginId),
        spec: Object.freeze({ ...spec }),
      }));
      return true;
    }

    function unregister(pluginId = "", actionId = "", owner = "") {
      const key = actionKey(pluginId, actionId);
      const entry = registry.get(key);
      if (!entry || !owner || entry.owner !== owner) return false;
      return registry.delete(key);
    }

    async function authorized(entry, request) {
      const checks = [options.authorize, entry.authorize].filter((candidate) => typeof candidate === "function");
      if (privilegedEffects.has(entry.spec.effect) && checks.length === 0) return { allowed: false, reason: "policy_owner_missing" };
      for (const check of checks) {
        const decision = await check({ context: request.context || {}, input: request.input, spec: entry.spec });
        if (decision === false) return { allowed: false, reason: "policy_denied" };
        if (decision && typeof decision === "object" && decision.allowed !== true) {
          return { allowed: false, reason: String(decision.reason || "policy_denied") };
        }
      }
      return { allowed: true, reason: "" };
    }

    async function dispatch(request = {}) {
      const pluginId = String(request.pluginId || "").trim();
      const actionId = String(request.actionId || "").trim();
      const entry = registry.get(actionKey(pluginId, actionId));
      if (!entry) return reject({ actionId, pluginId, requestId: request.requestId }, "unregistered_action");
      const policy = await authorized(entry, request);
      if (!policy.allowed) return feedback({ actionId, effect: entry.spec.effect, pluginId, reason: policy.reason, requestId: request.requestId, reversible: entry.spec.reversible, status: "rejected" });
      if (entry.spec.confirmation === "inline" && request.confirmed !== true) {
        return feedback({ actionId, effect: entry.spec.effect, pluginId, reason: "confirmation_required", requestId: request.requestId, reversible: entry.spec.reversible, status: "rejected" });
      }
      if (entry.spec.confirmation === "preview_confirm") {
        const confirmed = typeof options.confirm === "function"
          ? await options.confirm({ context: request.context || {}, input: request.input, spec: entry.spec })
          : false;
        if (confirmed !== true) return feedback({ actionId, effect: entry.spec.effect, pluginId, reason: "confirmation_cancelled", requestId: request.requestId, reversible: entry.spec.reversible, status: "cancelled" });
      }
      try {
        const outcome = await entry.execute({ context: request.context || {}, input: request.input, spec: entry.spec });
        if (!outcome || outcome.ok !== true) {
          return feedback({ actionId, effect: entry.spec.effect, outcome: outcome || null, pluginId, reason: String(outcome?.message || "owner_failed"), requestId: request.requestId, reversible: entry.spec.reversible, status: "failed" });
        }
        return feedback({ actionId, effect: entry.spec.effect, ok: true, outcome, pluginId, requestId: request.requestId, reversible: entry.spec.reversible, status: "completed" });
      } catch {
        return feedback({ actionId, effect: entry.spec.effect, pluginId, reason: "owner_exception", requestId: request.requestId, reversible: entry.spec.reversible, status: "failed" });
      }
    }

    return Object.freeze({ actionKey, dispatch, list: () => Object.freeze([...registry.keys()].sort()), register, reject, unregister });
  }

  global.ResearchOSActionGateway = Object.freeze({ actionKey, create });
})(window);
