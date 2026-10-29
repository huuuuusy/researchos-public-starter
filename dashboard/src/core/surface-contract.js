/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端 surface 与动作合约；集中声明工作区、target 路由和权限化动作语义。
 * English: Browser-side surface and action contract for the ResearchOS dashboard; centralizes workspaces, target routes, and permissioned action semantics.
 */

(function attachResearchOSSurfaceContract(global) {
  const semanticVersion = "researchos-interaction-semantics-v1";
  const clientProfileId = global.ResearchOSEditionProfile?.clientProfileId;
  const canonicalSurfaceIds = Object.freeze(["now", "library"]);
  const surfaceAliasMap = Object.freeze({ start: "now", today: "now", next: "now?panel=work", work: "now?panel=work", agent: "now", assets: "library", review: "now?panel=review", inbox: "now?panel=review" });
  const surfaceAliasFilterMap = Object.freeze({ review: "needs_review", inbox: "needs_review" });
  const surfaceScopes = Object.freeze([
    Object.freeze({
      id: "now",
      kind: "workspace",
      rootId: "",
      parentSurface: "",
      primaryQuestion: "which_commitments_need_attention_and_how_should_each_be_disposed",
      tabI18n: "workspace.now",
      role: "project a multi-commitment attention portfolio with one disposition and next step per item",
    }),
    Object.freeze({
      id: "library",
      kind: "workspace",
      rootId: "",
      parentSurface: "",
      primaryQuestion: "what_context_is_included_excluded_and_allowed_to_leave",
      tabI18n: "workspace.assets",
      role: "use one or a few commitments as a lens over relevant research objects and context",
    }),
    Object.freeze({
      id: "utility",
      kind: "slot_host",
      rootId: "pluginUtilitySlots",
      parentSurface: "library",
      primaryQuestion: "",
      tabI18n: "",
      role: "declarative Utility plugin slot host",
    }),
    Object.freeze({
      id: "preview",
      kind: "aside",
      rootId: "markdownPreviewPanel",
      parentSurface: "any",
      primaryQuestion: "",
      tabI18n: "",
      role: "markdown preview surface",
    }),
  ]);

  const assetDetailPanels = Object.freeze([]);

  const workspaceTabs = Object.freeze(surfaceScopes.filter((surface) => surface.kind === "workspace").map((surface) => surface.id));
  const assetDetailPanelIds = Object.freeze(assetDetailPanels.map((panel) => panel.id));
  const defaultAssetDetailPanel = assetDetailPanels.find((panel) => panel.default)?.id || "";

  const taskSurfaceMap = Object.freeze({
    material_understanding: "library",
    research_self_model: "now",
    relationship_network: "library",
    external_demand_response: "now",
    self_evolution: "now",
    new_project_intake: "library",
  });

  const targetSurfaceMap = Object.freeze({
    homeCommandCenter: "now",
    todayWorkSession: "now",
    unifiedInbox: "now",
    assetOverview: "library",
    newProjectIntake: "library",
  });

  const taskWorkspaceMap = taskSurfaceMap;
  const targetWorkspaceMap = targetSurfaceMap;

  const stateAxes = Object.freeze({
    session: Object.freeze(["none", "open", "ended"]),
    run: Object.freeze(["none", "submitted", "queued", "running", "completed", "failed"]),
    observation: Object.freeze(["none", "fresh", "delivery_unknown", "lease_expired", "reconcile_failed"]),
    result: Object.freeze(["none", "answer", "artifact", "writeback", "invalid"]),
    admission: Object.freeze({
      decision_state: Object.freeze(["unproposed", "proposed", "accepted", "revised", "rejected", "deferred"]),
      mutation_state: Object.freeze(["not_requested", "staged", "applied", "rolled_back"]),
      validation_state: Object.freeze(["unvalidated", "pending", "passed", "failed"]),
      authority_role: Object.freeze(["none", "informative", "interpretive", "normative"]),
    }),
  });
  const activeRunStates = Object.freeze(["submitted", "queued", "running"]);
  const derivedTaskStates = Object.freeze([
    "no_task", "ready", "running", "verify_delivery", "verify_run",
    "failed_retryable", "failed_needs_impact_check", "result_ready",
    "late_result_ready", "ended", "ended_with_run_tracking", "invalid",
  ]);
  const actionSpec = Object.freeze({
    required: Object.freeze(["id", "verb", "target", "actor", "location", "effect", "confirmation", "risk", "reversible", "fallback"]),
    actor: Object.freeze(["human", "codex", "runner", "system"]),
    location: Object.freeze(["current_surface", "codex", "cli", "work", "review", "utility"]),
    effect: Object.freeze(["navigate", "select_context", "mutate_attention", "handoff", "execute_bounded", "propose_writeback", "mutate_canonical", "recover"]),
    confirmation: Object.freeze(["none", "inline", "preview_confirm"]),
    risk: Object.freeze(["low", "medium", "high"]),
  });
  const predictionContract = Object.freeze({
    requiredVisibleQuestions: Object.freeze(["actor", "location", "effect", "non_effect", "fallback"]),
    beforeAction: "answer_without_opening_logs_or_recalling_hidden_policy",
    afterFailure: "show_last_confirmed_safe_point_and_only_legal_recovery",
  });

  const canonicalSurface = (value = "") => {
    const normalized = String(value || "").trim().toLowerCase();
    const alias = surfaceAliasMap[normalized] || "";
    return canonicalSurfaceIds.includes(normalized) ? normalized : String(alias).split("?", 1)[0];
  };

  const surfaceRoute = (value = "") => {
    const normalized = String(value || "").trim().toLowerCase();
    const alias = surfaceAliasMap[normalized] || "";
    const query = String(alias).split("?", 2)[1] || "";
    const params = query.split("&").map((part) => part.split("=", 2));
    const filter = params.find(([key]) => key === "filter")?.[1] || "";
    const panel = params.find(([key]) => key === "panel")?.[1] || "";
    const item = params.find(([key]) => key === "item")?.[1] || "";
    return Object.freeze({
      filter: decodeURIComponent(filter) || surfaceAliasFilterMap[normalized] || "",
      item: decodeURIComponent(item),
      panel: decodeURIComponent(panel) || (["review", "inbox"].includes(normalized) ? "review" : (["work", "next"].includes(normalized) ? "work" : "")),
      surface: canonicalSurface(normalized),
    });
  };

  const runtimeWorkspace = (value = "") => canonicalSurface(value);
  const workspaceI18nKey = (value = "") => surfaceScopes.find((surface) => surface.id === canonicalSurface(value))?.tabI18n || "";

  const defaultAdmission = () => ({
    decision_state: "unproposed",
    mutation_state: "not_requested",
    validation_state: "unvalidated",
    authority_role: "none",
  });

  function validateLifecycleSnapshot(snapshot = {}) {
    const errors = [];
    const session = String(snapshot.session || "none");
    const run = String(snapshot.run || "none");
    const observation = String(snapshot.observation || "none");
    const result = String(snapshot.result || "none");
    const admission = { ...defaultAdmission(), ...(snapshot.admission || {}) };
    for (const [axis, value] of [["session", session], ["run", run], ["observation", observation], ["result", result]]) {
      if (!stateAxes[axis].includes(value)) errors.push(`unknown_${axis}:${value}`);
    }
    for (const [dimension, allowed] of Object.entries(stateAxes.admission)) {
      if (!allowed.includes(admission[dimension])) errors.push(`unknown_admission_${dimension}:${admission[dimension]}`);
    }
    if (session === "none" && (run !== "none" || observation !== "none" || result !== "none")) errors.push("run_requires_session");
    if (run === "none" && (observation !== "none" || result !== "none")) errors.push("observation_or_result_requires_run");
    if (activeRunStates.includes(run) && !["fresh", "delivery_unknown", "lease_expired", "reconcile_failed"].includes(observation)) errors.push("active_run_requires_observation");
    if (activeRunStates.includes(run) && result !== "none") errors.push("active_run_cannot_have_result");
    if (["completed", "failed"].includes(run) && ["delivery_unknown", "lease_expired", "reconcile_failed"].includes(observation)) errors.push("terminal_run_cannot_have_uncertain_observation");
    if (!["none", "invalid"].includes(result) && run !== "completed") errors.push("result_requires_completed_run");
    if (run === "completed" && result === "none") errors.push("completed_run_requires_result");
    if (run === "failed" && !["none", "invalid"].includes(result)) errors.push("failed_run_cannot_have_valid_result");
    if (result === "writeback" && admission.decision_state === "unproposed") errors.push("writeback_requires_proposed_admission");
    if (["answer", "artifact"].includes(result) && admission.decision_state !== "unproposed") errors.push("non_writeback_result_cannot_claim_admission");
    if (!["accepted", "revised"].includes(admission.decision_state) && admission.mutation_state !== "not_requested") errors.push("mutation_requires_accept_or_revise");
    if (admission.mutation_state === "not_requested" && admission.validation_state !== "unvalidated") errors.push("validation_requires_mutation");
    if (admission.mutation_state === "staged" && !["unvalidated", "pending"].includes(admission.validation_state)) errors.push("staged_validation_invalid");
    if (admission.mutation_state === "applied" && !["pending", "passed", "failed"].includes(admission.validation_state)) errors.push("applied_validation_invalid");
    return Object.freeze(errors);
  }

  function deriveTaskPresentation(snapshot = {}) {
    const errors = validateLifecycleSnapshot(snapshot);
    const present = (state, primaryAction, allowedActions = [primaryAction], retryAllowed = false) => Object.freeze({
      allowedActions: Object.freeze([...new Set(allowedActions.filter(Boolean))]),
      errors,
      primaryAction,
      retryAllowed,
      state,
    });
    if (errors.length) return present("invalid", "inspect_contract");
    const session = String(snapshot.session || "none");
    const run = String(snapshot.run || "none");
    const observation = String(snapshot.observation || "none");
    const result = String(snapshot.result || "none");
    if (session === "none") return present("no_task", "create_or_bind_task");
    if (session === "ended" && (activeRunStates.includes(run) || ["delivery_unknown", "lease_expired", "reconcile_failed"].includes(observation))) {
      return present("ended_with_run_tracking", "check_run_receipt");
    }
    if (result === "invalid") return present("failed_needs_impact_check", "inspect_result_contract", ["inspect_result_contract", "finish_session_keep_receipt"]);
    if (session === "ended" && result !== "none") {
      const latePrimary = result === "artifact" ? "open_artifact" : result === "writeback" ? "open_review" : "view_late_result_receipt";
      return present("late_result_ready", latePrimary, [latePrimary, "view_late_result_receipt", "copy_result"]);
    }
    if (result !== "none") {
      const resultActions = {
        answer: ["finish_session", "add_followup", "copy_result", "propose_artifact", "propose_writeback"],
        artifact: ["open_artifact", "finish_session", "copy_result", "propose_writeback"],
        writeback: ["open_review", "finish_session", "copy_result"],
      };
      return present("result_ready", resultActions[result][0], resultActions[result]);
    }
    if (session === "ended") return present("ended", "view_receipt");
    if (observation === "delivery_unknown") return present("verify_delivery", "reconcile_by_client_request_id", ["reconcile_by_client_request_id", "finish_session_keep_tracking"]);
    if (["lease_expired", "reconcile_failed"].includes(observation)) return present("verify_run", "check_run_status", ["check_run_status", "finish_session_keep_tracking"]);
    if (activeRunStates.includes(run)) return present("running", "view_progress");
    if (run === "failed") {
      const retryAllowed = snapshot.sideEffects === "none";
      return retryAllowed
        ? present("failed_retryable", "retry_same_request", ["retry_same_request", "finish_session_keep_receipt"], true)
        : present("failed_needs_impact_check", "check_effects", ["check_effects", "finish_session_keep_receipt"]);
    }
    return present("ready", "choose_execution_location", ["choose_execution_location", "finish_session"]);
  }

  function validateActionSpec(candidate = {}) {
    const errors = [];
    if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) return Object.freeze(["action_spec_must_be_object"]);
    actionSpec.required.forEach((field) => {
      if (field === "reversible") {
        if (typeof candidate[field] !== "boolean") errors.push(`missing_or_invalid:${field}`);
      } else if (!String(candidate[field] || "").trim()) errors.push(`missing_or_invalid:${field}`);
    });
    for (const field of ["actor", "location", "effect", "confirmation", "risk"]) {
      if (candidate[field] && !actionSpec[field].includes(candidate[field])) errors.push(`unknown_${field}:${candidate[field]}`);
    }
    if (["mutate_attention", "mutate_canonical"].includes(candidate.effect) && candidate.confirmation === "none") errors.push("mutation_requires_confirmation");
    if (candidate.effect === "mutate_canonical" && (candidate.confirmation !== "preview_confirm" || candidate.risk !== "high")) errors.push("canonical_mutation_requires_high_risk_preview");
    return Object.freeze(errors);
  }

  const actionKinds = Object.freeze({
    DIRECT: "direct",
    PREVIEW_CONFIRM: "preview-confirm",
    HANDOFF: "handoff",
    NAVIGATION: "navigation",
  });

  const operations = Object.freeze({
    EXECUTE: "execute",
    WRITEBACK: "writeback",
    HANDOFF: "handoff",
    NAVIGATE: "navigate",
  });

  const executionScopes = Object.freeze({
    NONE: "none",
    READ_ONLY: "read_only",
    WORKSPACE_WRITE: "workspace_write",
  });

  const executionRouteModes = Object.freeze({
    COPY_ONLY: "copy_only",
    REGISTERED_RUNNER: "registered_runner",
  });

  function executionRoute({ localExecution = false, publicStarter = false } = {}) {
    if (publicStarter === true) return Object.freeze({
      actionKind: actionKinds.HANDOFF,
      effect: "copy_task",
      mode: executionRouteModes.COPY_ONLY,
      reason: "public_policy",
      resultLocation: "external_client",
    });
    if (localExecution === true) return Object.freeze({
      actionKind: actionKinds.DIRECT,
      effect: "execute_bounded",
      mode: executionRouteModes.REGISTERED_RUNNER,
      reason: "runner_available",
      resultLocation: "dashboard",
    });
    return Object.freeze({
      actionKind: actionKinds.HANDOFF,
      effect: "copy_task",
      mode: executionRouteModes.COPY_ONLY,
      reason: "runner_unavailable",
      resultLocation: "external_client",
    });
  }

  function localExecutionAvailable({ providerMode = "disabled", serverMode = false } = {}) {
    const mode = String(providerMode || "").trim().toLowerCase();
    return Boolean(serverMode) && mode === "local_codex";
  }

  function workspaceWriteAvailable(context = {}) {
    if (!localExecutionAvailable(context)) return false;
    const scope = String(context.executionScope || executionScopes.NONE).trim().toLowerCase();
    return scope === executionScopes.WORKSPACE_WRITE;
  }

  function durableMutationAvailable({ runtimeMode = "", publicStarter = false, serverMode = false } = {}) {
    return String(runtimeMode || "").trim().toLowerCase() === "private"
      && !publicStarter
      && Boolean(serverMode);
  }

  function runtimeCapabilities({
    executionAvailable = false,
    executionProbeRequired = false,
    executionScope = executionScopes.NONE,
    providerMode = "disabled",
    serverMode = false,
  } = {}) {
    const normalizedScope = typeof executionScope === "string"
      ? executionScope.trim().toLowerCase()
      : executionScopes.NONE;
    const normalizedProviderMode = typeof providerMode === "string"
      ? providerMode.trim().toLowerCase()
      : "disabled";
    const executionDeclared = executionProbeRequired === true
      && executionAvailable === true
      && normalizedProviderMode === "local_codex"
      && [executionScopes.READ_ONLY, executionScopes.WORKSPACE_WRITE].includes(normalizedScope);
    const runtime = {
      executionScope: executionDeclared ? normalizedScope : executionScopes.NONE,
      providerMode: executionDeclared ? normalizedProviderMode : "disabled",
      serverMode,
    };
    return Object.freeze({
      localExecution: localExecutionAvailable(runtime),
      registeredMaintenance: Boolean(serverMode),
      workspaceWrite: workspaceWriteAvailable(runtime),
    });
  }

  function resolveActionKind(operation = operations.HANDOFF, context = {}) {
    if (operation === operations.NAVIGATE) return actionKinds.NAVIGATION;
    if (operation === operations.WRITEBACK) return actionKinds.PREVIEW_CONFIRM;
    if (operation === operations.EXECUTE) {
      const available = context.requiresWrite
        ? workspaceWriteAvailable(context)
        : localExecutionAvailable(context);
      return available ? actionKinds.DIRECT : actionKinds.HANDOFF;
    }
    return actionKinds.HANDOFF;
  }

  const actionContract = Object.freeze({
    ACTION_KINDS: actionKinds,
    EXECUTION_ROUTE_MODES: executionRouteModes,
    EXECUTION_SCOPES: executionScopes,
    OPERATIONS: operations,
    durableMutationAvailable,
    executionRoute,
    isDirect: (kind = "") => kind === actionKinds.DIRECT,
    localExecutionAvailable,
    resolveActionKind,
    runtimeCapabilities,
    workspaceWriteAvailable,
  });

  global.ResearchOSSurfaceContract = Object.freeze({
    assetDetailPanelIds,
    assetDetailPanels,
    defaultAssetDetailPanel,
    canonicalSurface,
    canonicalSurfaceIds,
    clientProfileId,
    runtimeWorkspace,
    workspaceI18nKey,
    surfaceAliasMap,
    surfaceAliasFilterMap,
    surfaceRoute,
    surfaceScopes,
    targetSurfaceMap,
    targetWorkspaceMap,
    taskSurfaceMap,
    taskWorkspaceMap,
    workspaceTabs,
  });
  global.ResearchOSInteractionContract = Object.freeze({
    ACTION_SPEC: actionSpec,
    DERIVED_TASK_STATES: derivedTaskStates,
    PREDICTION_CONTRACT: predictionContract,
    STATE_AXES: stateAxes,
    VERSION: semanticVersion,
    deriveTaskPresentation,
    validateActionSpec,
    validateLifecycleSnapshot,
  });
  global.ResearchOSActionContract = actionContract;
})(window);
