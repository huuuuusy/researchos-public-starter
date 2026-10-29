/* ResearchOS maintenance header.
 * 中文：ResearchOS 浏览器端插件贡献装配器；只消费 builder 发出的安全 registry，不加载任意脚本或持久化插件状态。
 * English: Browser-side ResearchOS plugin contribution assembler; consumes only the builder's safe registry and never loads arbitrary scripts or owns durable plugin state.
 */

(function attachResearchOSPluginRuntime(global) {
  const adapters = new Map();
  const ownedAdapters = new Map();
  const actionHandlers = new Map();
  const candidateAdapters = new Map();
  const mountedSlots = new WeakMap();
  const surfaceDependencies = new Map();
  const workItemAdapters = new Map();
  let actionGateway = null;

  function pluginEnvelope(data = {}) {
    const plugins = data?.plugins;
    if (!plugins || plugins.schema_id !== "researchos-plugin-v1" || String(plugins.core_api_version || "") !== "1") {
      return { contributions: {}, loaded: [] };
    }
    return plugins;
  }

  function contributionList(data = {}, type = "") {
    const items = pluginEnvelope(data)?.contributions?.[type];
    return Array.isArray(items) ? items : [];
  }

  function contributionKey(item = {}) {
    const pluginId = String(item?.plugin_id || "").trim();
    const id = String(item?.id || "").trim();
    const projected = String(item?.contribution_key || "").trim();
    if (!/^[a-z][a-z0-9_]*$/.test(pluginId) || !/^[a-z][a-z0-9_]*$/.test(id)) return "";
    return projected === `${pluginId}:${id}` ? projected : `${pluginId}:${id}`;
  }

  function ownedContribution(data = {}, type = "", id = "", pluginId = "") {
    const key = `${String(pluginId || "").trim()}:${String(id || "").trim()}`;
    return contributionList(data, type).find((item) => contributionKey(item) === key) || null;
  }

  function candidateContribution(data = {}, candidateType = "") {
    const normalized = String(candidateType || "").trim();
    if (!normalized) return null;
    const matches = contributionList(data, "candidate_types").filter((item) => item.id === normalized);
    return matches.length === 1 ? matches[0] : null;
  }

  function candidateTypeEnabled(data = {}, candidateType = "") {
    return Boolean(candidateContribution(data, candidateType));
  }

  function valueAtPath(data = {}, source = "") {
    const parts = String(source || "").split(".").filter(Boolean);
    if (!parts.length || parts.some((part) => !/^[a-z][a-z0-9_]*$/.test(part))) return undefined;
    let value = data;
    for (const part of parts) {
      if (!value || typeof value !== "object" || !(part in value)) return undefined;
      value = value[part];
    }
    return value;
  }

  function projectionEnvelope(data = {}, contribution = {}) {
    const base = {
      error: "",
      freshness: Object.freeze({
        mode: String(contribution.freshness || ""),
        observed_at: String(data.generated_at || ""),
        state: data.generated_at ? "known" : "unknown",
      }),
      payload: null,
      plugin_id: String(contribution.plugin_id || ""),
      projection_id: String(contribution.id || ""),
      schema_id: "researchos-projection-envelope-v1",
      sensitivity: String(contribution.sensitivity || ""),
      source: String(contribution.source || ""),
      status: "error",
      version: "1",
    };
    const fail = (error, status = "error") => Object.freeze({ ...base, error, status });
    if (contribution.schema_id !== base.schema_id || String(contribution.version || "") !== "1") return fail("unsupported_projection_contract");
    if (!["snapshot", "live"].includes(base.freshness.mode) || !base.freshness.observed_at) return fail("freshness_unknown");
    if (!["public", "public_safe", "internal", "private", "local_only", "not_exportable"].includes(base.sensitivity)) return fail("invalid_sensitivity");
    if (["public_starter", "personal_vault"].includes(String(data.runtime_mode || "")) && ["internal", "private", "not_exportable"].includes(base.sensitivity)) {
      return fail("sensitivity_denied");
    }
    const fields = Array.isArray(contribution.export_fields) ? contribution.export_fields : [];
    if (!fields.length || (fields.includes("$") && fields.length !== 1)) return fail("invalid_export_map");
    const sourceValue = valueAtPath(data, contribution.source);
    if (sourceValue === undefined) return fail(contribution.optional ? "" : "source_unavailable", contribution.optional ? "empty" : "error");
    if (fields[0] === "$") return Object.freeze({ ...base, payload: sourceValue, status: "ready" });
    if (!sourceValue || typeof sourceValue !== "object" || Array.isArray(sourceValue)) return fail("field_export_requires_object");
    const payload = {};
    for (const field of fields) {
      const parts = String(field || "").split(".").filter(Boolean);
      if (!parts.length || parts.some((part) => !/^[a-z][a-z0-9_]*$/.test(part))) return fail("invalid_export_field");
      const value = valueAtPath(sourceValue, field);
      if (value === undefined) return fail("export_field_unavailable");
      let cursor = payload;
      parts.forEach((part, index) => {
        if (index === parts.length - 1) cursor[part] = value;
        else cursor = cursor[part] ||= {};
      });
    }
    return Object.freeze({ ...base, payload: Object.freeze(payload), status: "ready" });
  }

  function slotModels(data = {}, slotName = "") {
    return contributionList(data, "ui_slots")
      .filter((slot) => !slotName || slot.slot === slotName)
      .sort((left, right) => Number(left.order || 0) - Number(right.order || 0) || String(left.id).localeCompare(String(right.id)))
      .map((slot) => {
        const projections = Object.fromEntries((slot.projection_ids || [])
          .map((id) => [id, ownedContribution(data, "projections", id, slot.plugin_id)])
          .filter(([, item]) => item)
          .map(([id, item]) => [id, projectionEnvelope(data, item)]));
        return {
          ...slot,
          actions: Object.fromEntries((slot.action_ids || [])
            .map((id) => [id, ownedContribution(data, "actions", id, slot.plugin_id)])
            .filter(([, item]) => item && item.surface === slot.surface)),
          payloads: Object.fromEntries(Object.entries(projections)
            .filter(([, envelope]) => envelope.status === "ready")
            .map(([id, envelope]) => [id, envelope.payload])),
          projections,
        };
      });
  }

  function workItemError(provider = {}, error = "invalid_projection") {
    return Object.freeze({
      error,
      items: Object.freeze([]),
      plugin_id: String(provider.plugin_id || ""),
      provider_id: String(provider.id || ""),
      schema_id: "researchos-work-item-projection-v1",
      status: "error",
      version: "1",
    });
  }

  function normalizeWorkItemProjection(candidate = {}, provider = {}) {
    if (
      !candidate || candidate.schema_id !== "researchos-work-item-projection-v1"
      || String(candidate.version || "") !== "1" || !Array.isArray(candidate.items)
    ) return workItemError(provider, "invalid_projection");
    const items = candidate.items.filter((item) => item && typeof item === "object" && String(item.id || item.item_id || "").trim());
    if (items.length !== candidate.items.length) return workItemError(provider, "invalid_work_item");
    return Object.freeze({
      error: "",
      items: Object.freeze(items.map((item) => Object.freeze({ ...item }))),
      plugin_id: String(provider.plugin_id || ""),
      provider_id: String(provider.id || ""),
      schema_id: "researchos-work-item-projection-v1",
      status: "ready",
      version: "1",
    });
  }

  function registerWorkItemAdapter(pluginId = "", adapterId = "", adapter = {}) {
    const key = `${String(pluginId || "").trim()}:${String(adapterId || "").trim()}`;
    if (!/^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$/.test(key) || workItemAdapters.has(key) || typeof adapter.project !== "function") return false;
    workItemAdapters.set(key, Object.freeze({ ...adapter, owner: String(adapter.owner || pluginId) }));
    return true;
  }

  function unregisterWorkItemAdapter(pluginId = "", adapterId = "", owner = "") {
    const key = `${String(pluginId || "").trim()}:${String(adapterId || "").trim()}`;
    const adapter = workItemAdapters.get(key);
    if (!adapter || !owner || adapter.owner !== owner) return false;
    return workItemAdapters.delete(key);
  }

  function workItemActionId(pluginId = "", role = "") {
    const plugin = String(pluginId || "").trim();
    const actionRole = String(role || "").trim();
    if (!/^[a-z][a-z0-9_]*$/.test(plugin) || !/^[a-z][A-Za-z0-9]*$/.test(actionRole)) return "";
    const matches = new Set();
    for (const [key, adapter] of workItemAdapters.entries()) {
      if (!key.startsWith(`${plugin}:`)) continue;
      const actionId = String(adapter?.actions?.[actionRole] || "").trim();
      if (/^[a-z][a-z0-9_]*$/.test(actionId)) matches.add(actionId);
    }
    return matches.size === 1 ? [...matches][0] : "";
  }

  function workItemProviderModels(data = {}, context = {}) {
    return contributionList(data, "work_item_providers").map((provider) => {
      const projection = ownedContribution(data, "projections", provider.projection_id, provider.plugin_id);
      const envelope = projection ? projectionEnvelope(data, projection) : null;
      const payload = envelope?.status === "ready" ? envelope.payload : undefined;
      const adapter = workItemAdapters.get(`${provider.plugin_id}:${provider.adapter}`);
      let normalized;
      if (payload === undefined && provider.optional) normalized = Object.freeze({ ...workItemError(provider, ""), status: "empty" });
      else if (!adapter) normalized = workItemError(provider, "adapter_unavailable");
      else {
        try {
          normalized = normalizeWorkItemProjection(adapter.project({ context, payload, provider }), provider);
        } catch (error) {
          normalized = workItemError(provider, "adapter_failed");
          global.console?.warn?.(`ResearchOS work-item adapter failed: ${provider.plugin_id}:${provider.adapter}`, error);
        }
      }
      return {
        ...provider,
        source_projection: envelope,
        projection: normalized,
      };
    });
  }

  function registerActionHandler(pluginId = "", actionId = "", registration = {}) {
    const key = `${String(pluginId || "").trim()}:${String(actionId || "").trim()}`;
    if (!/^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$/.test(key) || actionHandlers.has(key)) return false;
    if (!registration?.spec || typeof registration.execute !== "function" || !String(registration.handlerId || "").trim()) return false;
    const owned = Object.freeze({ ...registration, owner: String(registration.owner || pluginId) });
    actionHandlers.set(key, owned);
    if (actionGateway && !actionGateway.register(pluginId, actionId, owned)) {
      actionHandlers.delete(key);
      return false;
    }
    return true;
  }

  function unregisterActionHandler(pluginId = "", actionId = "", owner = "") {
    const key = `${String(pluginId || "").trim()}:${String(actionId || "").trim()}`;
    const registration = actionHandlers.get(key);
    if (!registration || !owner || registration.owner !== owner) return false;
    if (actionGateway && !actionGateway.unregister(pluginId, actionId, owner)) return false;
    return actionHandlers.delete(key);
  }

  function configureActionGateway(gateway = null) {
    if (!gateway?.register || actionGateway) return false;
    for (const [key, registration] of actionHandlers.entries()) {
      const [pluginId, actionId] = key.split(":");
      if (!gateway.register(pluginId, actionId, registration)) return false;
    }
    actionGateway = gateway;
    return true;
  }

  async function dispatchAction({ actionId = "", confirmed = false, context = {}, data = {}, input = null, pluginId = "", requestId = "" } = {}) {
    const contribution = ownedContribution(data, "actions", actionId, pluginId);
    const registration = actionHandlers.get(`${pluginId}:${actionId}`);
    if (!actionGateway) return Object.freeze({ ok: false, reason: "action_gateway_unavailable", status: "rejected" });
    if (!contribution) return actionGateway.reject({ actionId, pluginId, requestId }, "action_contribution_unavailable");
    if (!registration || String(contribution.handler || "") !== registration.handlerId) {
      return actionGateway.reject({ actionId, pluginId, requestId }, "action_handler_mismatch");
    }
    return actionGateway.dispatch({ actionId, confirmed, context, input, pluginId, requestId });
  }

  function registerAdapter(adapterId = "", adapter = {}) {
    const normalized = String(adapterId || "").trim();
    if (!/^[a-z][a-z0-9_]*$/.test(normalized) || typeof adapter.render !== "function") return false;
    if (adapters.has(normalized)) return false;
    adapters.set(normalized, Object.freeze({ ...adapter }));
    return true;
  }

  function registerOwnedAdapter(pluginId = "", adapterId = "", adapter = {}) {
    const key = `${String(pluginId || "").trim()}:${String(adapterId || "").trim()}`;
    if (!/^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$/.test(key) || ownedAdapters.has(key) || typeof adapter.render !== "function") return false;
    ownedAdapters.set(key, Object.freeze({ ...adapter, owner: String(adapter.owner || pluginId) }));
    return true;
  }

  function unregisterOwnedAdapter(pluginId = "", adapterId = "", owner = "") {
    const key = `${String(pluginId || "").trim()}:${String(adapterId || "").trim()}`;
    const adapter = ownedAdapters.get(key);
    if (!adapter || !owner || adapter.owner !== owner) return false;
    return ownedAdapters.delete(key);
  }

  function adapterFor(model = {}) {
    return ownedAdapters.get(`${String(model.plugin_id || "")}:${String(model.adapter || "")}`)
      || adapters.get(String(model.adapter || ""))
      || null;
  }

  function registerCandidateAdapter(candidateType = "", adapter = {}) {
    const normalized = String(candidateType || "").trim();
    if (!/^[a-z][a-z0-9_]*$/.test(normalized) || typeof adapter.collect !== "function") return false;
    if (candidateAdapters.has(normalized)) return false;
    candidateAdapters.set(normalized, Object.freeze({ ...adapter }));
    return true;
  }

  function registerSurfaceDependency(surface = "", dependencyId = "", provider = {}) {
    const normalizedSurface = String(surface || "").trim();
    const normalizedId = String(dependencyId || "").trim();
    const pluginId = String(provider.pluginId || "").trim();
    if (
      !/^[a-z][a-z0-9_]*$/.test(normalizedSurface) ||
      !/^[a-z][A-Za-z0-9]*$/.test(normalizedId) ||
      !/^[a-z][a-z0-9_]*$/.test(pluginId) ||
      typeof provider.provide !== "function"
    ) return false;
    const key = `${normalizedSurface}:${normalizedId}`;
    if (surfaceDependencies.has(key)) return false;
    surfaceDependencies.set(key, Object.freeze({ ...provider, pluginId }));
    return true;
  }

  function resolveSurfaceDependencies({ data = {}, surface = "", context = {} } = {}) {
    const normalizedSurface = String(surface || "").trim();
    const loaded = new Set(pluginEnvelope(data).loaded.map((plugin) => String(plugin?.id || "").trim()));
    const resolved = {};
    [...surfaceDependencies.entries()]
      .filter(([key, provider]) => key.startsWith(`${normalizedSurface}:`) && loaded.has(provider.pluginId))
      .sort(([left], [right]) => left.localeCompare(right))
      .forEach(([key, provider]) => {
        const dependencyId = key.slice(normalizedSurface.length + 1);
        try {
          const value = provider.provide({ context, data });
          if (value !== undefined) resolved[dependencyId] = value;
        } catch (error) {
          global.console?.warn?.(`ResearchOS plugin dependency failed: ${dependencyId}`, error);
        }
      });
    return resolved;
  }

  function collectCandidateEntries({ data = {}, context = {} } = {}) {
    const entries = [];
    const sourceEntries = [];
    const missing = [];
    const errors = [];
    contributionList(data, "candidate_types").forEach((contribution) => {
      const adapter = candidateAdapters.get(contribution.id);
      if (!adapter) {
        missing.push(contribution.id);
        return;
      }
      try {
        const result = adapter.collect({ context, contribution, data }) || {};
        (Array.isArray(result.entries) ? result.entries : []).forEach((entry) => {
          if (entry && typeof entry === "object") entries.push(entry);
        });
        if (result.sourceEntry && typeof result.sourceEntry === "object") sourceEntries.push(result.sourceEntry);
      } catch (error) {
        errors.push(contribution.id);
        global.console?.warn?.(`ResearchOS candidate adapter failed: ${contribution.id}`, error);
      }
    });
    return { entries, errors, missing, sourceEntries };
  }

  async function runCandidateAction({ action = "", candidateType = "", context = {}, data = {}, id = "", payload = {} } = {}) {
    const contribution = candidateContribution(data, candidateType);
    const adapter = contribution ? candidateAdapters.get(candidateType) : null;
    const handler = adapter?.actions?.[action];
    if (typeof handler !== "function") {
      return { handled: false, action, candidateType, id };
    }
    try {
      const result = await handler({ context, contribution, data, id, payload });
      return { handled: true, action, candidateType, id, result };
    } catch (error) {
      global.console?.warn?.(`ResearchOS candidate action failed: ${candidateType}:${action}`, error);
      return { handled: true, ok: false, action, candidateType, id, error: "adapter_failed" };
    }
  }

  async function runCandidateActions({ action = "", context = {}, data = {}, payload = {} } = {}) {
    const results = [];
    for (const contribution of contributionList(data, "candidate_types")) {
      results.push(await runCandidateAction({
        action,
        candidateType: contribution.id,
        context,
        data,
        payload,
      }));
    }
    return results;
  }

  function disposeSlots(host = null) {
    if (!host) return { errors: [], disposed: [] };
    const instances = mountedSlots.get(host) || [];
    const disposed = [];
    const errors = [];
    instances.forEach((instance) => {
      try {
        instance.controller.dispose();
        disposed.push(instance.model.id);
      } catch (error) {
        errors.push(instance.model.id);
        global.console?.warn?.(`ResearchOS plugin dispose failed: ${instance.model.id}`, error);
      }
    });
    mountedSlots.delete(host);
    return { disposed, errors };
  }

  function updateMountedSlots(host, resolved, context) {
    const instances = mountedSlots.get(host) || [];
    if (
      !instances.length || instances.length !== resolved.length
      || instances.some((instance, index) => (
        instance.model.id !== resolved[index].model.id
        || instance.adapter !== resolved[index].adapter
        || typeof instance.controller.update !== "function"
      ))
    ) return { handled: false, errors: [] };
    const errors = [];
    for (let index = 0; index < instances.length; index += 1) {
      const instance = instances[index];
      const { model } = resolved[index];
      try {
        instance.controller.update({ context, model, root: instance.root });
        instance.model = model;
      } catch (error) {
        errors.push(model.id);
        global.console?.warn?.(`ResearchOS plugin update failed: ${model.id}`, error);
        return { handled: false, errors };
      }
    }
    return { handled: true, errors };
  }

  function renderSlots({ data = {}, host = null, slot = "", context = {} } = {}) {
    if (!host) return { errors: [], missing: [], rendered: [], updated: false };
    const models = slotModels(data, slot);
    const missing = [];
    const errors = [];
    const resolved = [];
    models.forEach((model) => {
      const adapter = adapterFor(model);
      if (!adapter) missing.push(model.id);
      else resolved.push({ adapter, model });
    });
    const updated = updateMountedSlots(host, resolved, context);
    errors.push(...updated.errors);
    if (updated.handled) {
      host.hidden = resolved.length === 0;
      return { errors: [...new Set(errors)], missing, rendered: resolved.map(({ model }) => model.id), updated: true };
    }
    errors.push(...disposeSlots(host).errors);
    const rendered = [];
    const fragments = [];
    resolved.forEach(({ adapter, model }) => {
      try {
        const html = adapter.render(model, context);
        if (!String(html || "").trim()) return;
        rendered.push(model.id);
        fragments.push(`<div class="plugin-slot-instance" data-plugin-slot-instance="${global.ResearchOSUiCore?.escapeHtml(model.id)}">${html}</div>`);
      } catch (error) {
        errors.push(model.id);
        global.console?.warn?.(`ResearchOS plugin render failed: ${model.id}`, error);
      }
    });
    const mounted = [];
    host.innerHTML = fragments.join("");
    rendered.forEach((slotId) => {
      const model = models.find((item) => item.id === slotId);
      const root = host.querySelector?.(`[data-plugin-slot-instance="${slotId}"]`);
      const adapter = model ? adapterFor(model) : null;
      if (root && typeof adapter?.mount === "function") {
        try {
          const controller = adapter.mount({ context, model, root });
          if (!controller || typeof controller.update !== "function" || typeof controller.dispose !== "function") {
            throw new Error("mount must return update and dispose");
          }
          mounted.push({ adapter, controller, model, root });
        } catch (error) {
          errors.push(slotId);
          global.console?.warn?.(`ResearchOS plugin mount failed: ${slotId}`, error);
        }
      } else if (root && typeof adapter?.bind === "function") {
        try {
          adapter.bind({ context, model, root });
        } catch (error) {
          errors.push(slotId);
          global.console?.warn?.(`ResearchOS plugin bind failed: ${slotId}`, error);
        }
      }
    });
    if (mounted.length) mountedSlots.set(host, mounted);
    host.hidden = rendered.length === 0;
    return { errors: [...new Set(errors)], missing, rendered, updated: false };
  }

  global.ResearchOSPluginRuntime = Object.freeze({
    candidateContribution,
    candidateTypeEnabled,
    collectCandidateEntries,
    configureActionGateway,
    contributionList,
    contributionKey,
    pluginEnvelope,
    projectionEnvelope,
    dispatchAction,
    registerActionHandler,
    registerCandidateAdapter,
    registerAdapter,
    registerOwnedAdapter,
    registerSurfaceDependency,
    registerWorkItemAdapter,
    renderSlots,
    resolveSurfaceDependencies,
    runCandidateAction,
    runCandidateActions,
    slotModels,
    unregisterActionHandler,
    unregisterOwnedAdapter,
    unregisterWorkItemAdapter,
    workItemActionId,
    valueAtPath,
    workItemProviderModels,
  });
})(window);
