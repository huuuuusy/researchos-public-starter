/* ResearchOS maintenance header.
 * 中文：前端模型目录与默认选择 owner；合并运行时发现和浏览器本地自定义模型，不拥有 provider 凭证。
 * English: Frontend model catalog and default-selection owner; merges runtime discovery with browser-local custom models without owning provider credentials.
 */

(function attachResearchOSModelCatalog(global) {
  const MODEL_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$/;
  const REASONING_EFFORTS = Object.freeze(["low", "medium", "high", "xhigh", "max", "ultra"]);
  const LEGACY_REASONING_KEY = "researchos-codex-runner-reasoning";
  const LEGACY_TIER_KEY = "researchos-codex-runner-tier";

  function cleanModelId(value = "") {
    const modelId = String(value || "").trim();
    return MODEL_ID_PATTERN.test(modelId) ? modelId : "";
  }

  function storageKey(kind = "selection", runtimeMode = "private") {
    const scope = String(runtimeMode || "").trim() === "public_starter" ? "public" : "private";
    return `researchos-model-${kind}:${scope}:v1`;
  }

  function normalizeRuntimeCatalog(value = {}) {
    const models = (Array.isArray(value.models) ? value.models : []).map((model) => {
      const id = cleanModelId(model?.id);
      if (!id) return null;
      const defaultReasoningEffort = model.defaultReasoningEffort || model.default_reasoning_effort;
      const rawReasoningEfforts = model.reasoningEfforts || model.reasoning_efforts;
      return {
        available: model.available !== false,
        custom: false,
        defaultReasoningEffort: REASONING_EFFORTS.includes(defaultReasoningEffort) ? defaultReasoningEffort : "",
        description: String(model.description || "").trim(),
        id,
        label: String(model.label || id).trim(),
        priority: Number.isFinite(Number(model.priority)) ? Number(model.priority) : 9999,
        reasoningEfforts: (Array.isArray(rawReasoningEfforts) ? rawReasoningEfforts : []).filter((effort) => REASONING_EFFORTS.includes(effort)),
        source: "runtime",
      };
    }).filter(Boolean);
    return {
      configuredDefaultModel: cleanModelId(value.configuredDefaultModel || value.configured_default_model),
      discovery: String(value.discovery || "not_loaded"),
      models,
      ok: Boolean(value.ok),
      provider: String(value.provider || "codex"),
      recommendedModel: cleanModelId(value.recommendedModel || value.recommended_model) || "auto",
      refreshedAt: String(value.refreshedAt || value.refreshed_at || ""),
    };
  }

  function normalizeCustomModels(value = []) {
    const seen = new Set();
    return (Array.isArray(value) ? value : []).map((model) => {
      const id = cleanModelId(typeof model === "string" ? model : model?.id);
      if (!id || id === "auto" || seen.has(id)) return null;
      seen.add(id);
      return {
        available: null,
        custom: true,
        defaultReasoningEffort: "",
        description: "",
        id,
        label: String(model?.label || id).trim().slice(0, 160),
        priority: 9999,
        reasoningEfforts: [...REASONING_EFFORTS],
        source: "user",
      };
    }).filter(Boolean).slice(0, 40);
  }

  function readSettings(storage = global.localStorage, runtimeMode = "private") {
    let customModels = [];
    try {
      customModels = normalizeCustomModels(JSON.parse(storage?.getItem(storageKey("custom", runtimeMode)) || "[]"));
    } catch {
      customModels = [];
    }
    const storedReasoning = storage?.getItem(storageKey("reasoning", runtimeMode))
      || (runtimeMode === "public_starter" ? "" : storage?.getItem(LEGACY_REASONING_KEY));
    return {
      customModels,
      selectedModel: cleanModelId(storage?.getItem(storageKey("selection", runtimeMode)) || "auto") || "auto",
      selectedReasoning: ["auto", ...REASONING_EFFORTS].includes(storedReasoning)
        ? storedReasoning
        : "auto",
    };
  }

  function writeSettings(settings = {}, storage = global.localStorage, runtimeMode = "private") {
    const selectedModel = cleanModelId(settings.selectedModel || "auto") || "auto";
    const selectedReasoning = ["auto", ...REASONING_EFFORTS].includes(settings.selectedReasoning)
      ? settings.selectedReasoning
      : "auto";
    const customModels = normalizeCustomModels(settings.customModels);
    storage?.setItem(storageKey("selection", runtimeMode), selectedModel);
    storage?.setItem(storageKey("reasoning", runtimeMode), selectedReasoning);
    storage?.setItem(storageKey("custom", runtimeMode), JSON.stringify(customModels.map(({ id, label }) => ({ id, label }))));
    return { customModels, selectedModel, selectedReasoning };
  }

  function mergedModels(catalog = {}, customModels = []) {
    const runtime = normalizeRuntimeCatalog(catalog);
    const byId = new Map(runtime.models.map((model) => [model.id, model]));
    normalizeCustomModels(customModels).forEach((model) => {
      if (!byId.has(model.id)) byId.set(model.id, model);
    });
    return [...byId.values()].sort((left, right) => left.priority - right.priority || left.label.localeCompare(right.label));
  }

  function selectionState(selectedModel = "auto", catalog = {}, customModels = []) {
    const runtime = normalizeRuntimeCatalog(catalog);
    const requested = cleanModelId(selectedModel) || "auto";
    const models = mergedModels(catalog, customModels);
    const selected = models.find((model) => model.id === requested) || null;
    const autoModel = runtime.models.find((model) => model.id === runtime.recommendedModel)
      || runtime.models.find((model) => model.id === runtime.configuredDefaultModel)
      || runtime.models[0]
      || null;
    const unavailable = requested !== "auto" && !selected;
    return {
      autoModel,
      effectiveModel: requested === "auto" || unavailable ? autoModel?.id || "auto" : requested,
      models,
      requestedModel: requested,
      selected,
      unavailable,
    };
  }

  function addCustomModel(customModels = [], modelId = "", label = "") {
    const id = cleanModelId(modelId);
    if (!id || id === "auto") return { customModels: normalizeCustomModels(customModels), ok: false };
    const next = normalizeCustomModels([...customModels, { id, label: String(label || id).trim() }]);
    return { customModels: next, model: next.find((model) => model.id === id) || null, ok: true };
  }

  function removeCustomModel(customModels = [], modelId = "") {
    const id = cleanModelId(modelId);
    return normalizeCustomModels(customModels).filter((model) => model.id !== id);
  }

  function reasoningEffortsFor(selectedModel = "auto", catalog = {}, customModels = []) {
    const state = selectionState(selectedModel, catalog, customModels);
    const model = state.selected || state.autoModel;
    return model?.reasoningEfforts?.length ? model.reasoningEfforts : ["low", "medium", "high", "xhigh"];
  }

  function createController(options = {}) {
    let runtimeMode = "private";
    let runtimeCatalog = normalizeRuntimeCatalog({});
    let settings = { customModels: [], selectedModel: "auto", selectedReasoning: "auto" };
    const storage = options.storage || global.localStorage;
    const notify = () => options.onChange?.();
    const showStatus = (key) => options.onStatus?.(key);

    function selection() {
      return selectionState(settings.selectedModel, runtimeCatalog, settings.customModels);
    }

    function effectiveReasoning() {
      const selected = settings.selectedReasoning;
      if (selected === "auto") return "auto";
      if (!runtimeCatalog.ok && runtimeCatalog.models.length === 0) return selected;
      return reasoningEffortsFor(settings.selectedModel, runtimeCatalog, settings.customModels).includes(selected)
        ? selected
        : "auto";
    }

    function ensureCompatibleReasoning() {
      const compatible = effectiveReasoning();
      if (compatible !== settings.selectedReasoning) persist({ selectedReasoning: compatible });
      return compatible;
    }

    function persist(next = {}) {
      settings = writeSettings({ ...settings, ...next }, storage, runtimeMode);
      return settings;
    }

    function initialize(mode = "private") {
      runtimeMode = String(mode || "private");
      settings = writeSettings(readSettings(storage, runtimeMode), storage, runtimeMode);
      if (runtimeMode !== "public_starter") {
        storage?.removeItem(LEGACY_REASONING_KEY);
        storage?.removeItem(LEGACY_TIER_KEY);
        storage?.removeItem(`${LEGACY_TIER_KEY}:default-version`);
      }
      return snapshot();
    }

    function snapshot() {
      return {
        customModels: settings.customModels,
        modelCatalog: runtimeCatalog,
        selectedModel: settings.selectedModel,
        selectedReasoning: effectiveReasoning(),
        selection: selection(),
      };
    }

    async function refresh({ force = false, rerender = true } = {}) {
      const result = await options.client?.loadModelCatalog?.({
        publicStarter: Boolean(options.publicStarter?.()),
        refresh: force,
      }) || { ok: false, models: [] };
      runtimeCatalog = normalizeRuntimeCatalog(result);
      ensureCompatibleReasoning();
      if (rerender) notify();
      return result;
    }

    function selectModel(value = "auto") {
      persist({ selectedModel: cleanModelId(value) || "auto" });
      ensureCompatibleReasoning();
      notify();
      showStatus("workSessionModelSaved");
    }

    function selectReasoning(value = "auto") {
      const selected = ["auto", ...REASONING_EFFORTS].includes(value) ? value : "auto";
      persist({ selectedReasoning: selected });
      ensureCompatibleReasoning();
      notify();
      showStatus("workSessionReasoningSaved");
    }

    function add(value = "") {
      const added = addCustomModel(settings.customModels, value);
      if (!added.ok || !added.model) {
        showStatus("workSessionCustomModelInvalid");
        return false;
      }
      persist({ customModels: added.customModels, selectedModel: added.model.id });
      notify();
      showStatus("workSessionCustomModelAdded");
      return true;
    }

    function remove(value = "") {
      const customModels = removeCustomModel(settings.customModels, value);
      persist({ customModels, selectedModel: settings.selectedModel === value ? "auto" : settings.selectedModel });
      ensureCompatibleReasoning();
      notify();
      showStatus("workSessionCustomModelRemoved");
    }

    function payloadModel() {
      const state = selection();
      return state.unavailable ? "auto" : state.requestedModel;
    }

    return Object.freeze({ add, initialize, payloadModel, refresh, remove, selectModel, selectReasoning, snapshot });
  }

  global.ResearchOSModelCatalog = Object.freeze({
    REASONING_EFFORTS,
    addCustomModel,
    cleanModelId,
    createController,
    normalizeRuntimeCatalog,
    readSettings,
    reasoningEffortsFor,
    selectionState,
    storageKey,
    writeSettings,
  });
})(window);
