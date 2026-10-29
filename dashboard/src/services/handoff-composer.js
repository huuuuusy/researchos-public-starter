/* ResearchOS maintenance header.
 * 中文：Projection-first UI 的纯 Codex handoff 编译器；组合既有 TaskIntent、ContextPack、HandoffReceipt 与 Work Session prompt，不授予 authority 或执行 transport。
 * English: Pure Codex handoff compiler for the projection-first UI; composes existing TaskIntent, ContextPack, HandoffReceipt, and Work Session prompt owners without granting authority or dispatching transport.
 */

(function attachResearchOSHandoffComposer(global) {
  "use strict";

  const SCHEMA_ID = "researchos-ui-handoff-envelope-v1";
  const MAX_RELATED_PROJECTS = 8;
  const MAX_DEFINITION_ITEMS = 12;

  function contractError(code, field = "") {
    const error = new Error(code);
    error.code = code;
    error.field = field;
    return error;
  }

  function clean(value = "") {
    return String(value ?? "").trim();
  }

  function bounded(value = "", maximum = 4000, field = "") {
    const text = clean(value).replace(/\r\n?/g, "\n");
    if (text.includes("\u0000")) throw contractError("handoff_invalid_character", field);
    if ([...text].length > maximum) throw contractError("handoff_input_too_large", field);
    return text;
  }

  function safeArray(value = []) {
    return Array.isArray(value) ? value : [];
  }

  function deepFreeze(value) {
    if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
    Object.values(value).forEach(deepFreeze);
    return Object.freeze(value);
  }

  function canonicalValue(value) {
    if (Array.isArray(value)) return value.map(canonicalValue);
    if (!value || typeof value !== "object") return value;
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalValue(value[key])]).filter(([, item]) => item !== undefined));
  }

  function canonicalJson(value) {
    return JSON.stringify(canonicalValue(value));
  }

  async function sha256(value = "", deps = {}) {
    if (typeof deps.digest === "function") return clean(await deps.digest(value));
    const subtle = deps.crypto?.subtle || global.crypto?.subtle;
    const Encoder = deps.TextEncoder || global.TextEncoder;
    if (!subtle || typeof Encoder !== "function") throw contractError("handoff_digest_unavailable", "digest");
    const bytes = await subtle.digest("SHA-256", new Encoder().encode(value));
    return [...new Uint8Array(bytes)].map((item) => item.toString(16).padStart(2, "0")).join("");
  }

  function project(value = {}, fallback = {}) {
    const record = value && typeof value === "object" ? value : {};
    const sourcePath = bounded(record.path || record.sourcePath || fallback.path || fallback.sourcePath, 2048, "project.path");
    const id = clean(record.id || fallback.id);
    // Full path identities are lossless and bounded by the already-validated path.
    // Arbitrary explicit IDs retain the original limit.
    const pathIdentity = `reference:project:${encodeURIComponent(sourcePath)}`;
    const result = {
      id: bounded(id, sourcePath && id === pathIdentity ? pathIdentity.length : 240, "project.id"),
      path: sourcePath,
      reason: bounded(record.reason || fallback.reason, 1000, "project.reason"),
      title: bounded(record.title || fallback.title || record.id || fallback.id, 500, "project.title"),
    };
    return result.id || result.title || result.path ? result : null;
  }

  function relatedProjects(values = []) {
    if (!Array.isArray(values)) throw contractError("handoff_invalid_value", "relatedProjects");
    const deduped = new Map();
    values.forEach((value) => {
      const item = project(value);
      const identity = clean(item?.id || item?.path || item?.title);
      if (identity && !deduped.has(identity)) deduped.set(identity, item);
    });
    if (deduped.size > MAX_RELATED_PROJECTS) throw contractError("handoff_input_too_large", "relatedProjects");
    return [...deduped.values()];
  }

  function exclusion(value = {}) {
    const record = value && typeof value === "object" ? value : { scope: value };
    return {
      reason: bounded(record.reason || "explicit_selection_required", 500, "excluded.reason"),
      scope: bounded(record.scope || record.path || record.id, 2048, "excluded.scope"),
    };
  }

  function uniqueExclusions(values = []) {
    const items = [];
    const seen = new Set();
    safeArray(values).forEach((value) => {
      const item = exclusion(value);
      const identity = `${item.scope}\u0000${item.reason}`;
      if (!item.scope || seen.has(identity)) return;
      seen.add(identity);
      items.push(item);
    });
    return items;
  }

  function receiptSummary(receipt = null) {
    const present = receipt && typeof receipt === "object";
    const statement = (name) => ({
      state: clean(receipt?.[name]?.state || "unknown"),
      text: bounded(receipt?.[name]?.text, 2000, `handoffReceipt.${name}.text`),
    });
    return {
      content_state: clean(receipt?.contentState || "unknown"),
      forbidden_actions: {
        items: safeArray(receipt?.forbiddenActions?.items).map((item) => bounded(item, 500, "forbidden_action")).filter(Boolean).slice(0, 8),
        state: clean(receipt?.forbiddenActions?.state || "unknown"),
      },
      handoff_id: clean(receipt?.handoffId),
      last_judgment: statement("lastJudgment"),
      limitations: safeArray(receipt?.limitations).map(clean).filter(Boolean),
      next_safe_action: statement("nextSafeAction"),
      open_boundary: statement("openBoundary"),
      projection_state: present ? "provided" : "unavailable",
      runtime_scope: clean(receipt?.runtimeScope || "unknown"),
      source_revision: receipt?.sourceRevision && typeof receipt.sourceRevision === "object" ? { ...receipt.sourceRevision } : { state: "unknown", source_id: "", value_digest: "" },
      target_client: receipt?.targetClient && typeof receipt.targetClient === "object" ? { ...receipt.targetClient } : { kind: "codex", surface: "desktop", binding_state: "requested" },
      task_id: clean(receipt?.taskId),
    };
  }

  function routeSummary(route = {}) {
    return {
      fallback_route: clean(route.fallback_route || "copy_only"),
      intended_route: clean(route.intended_route || "copy_only"),
      reason_codes: [...new Set(safeArray(route.reason_codes).map(clean).filter(Boolean))],
      recommended_route: clean(route.recommended_route || "copy_only"),
      thread_id: clean(route.thread_id),
      transport_state: clean(route.transport_state || "unavailable"),
    };
  }

  function list(values = [], fallback = "- （无）") {
    const lines = safeArray(values).filter(Boolean).map((value) => `- ${value}`);
    return lines.length ? lines.join("\n") : fallback;
  }

  function projectLine(item = {}) {
    return [item.title || item.id, item.id ? `ID: ${item.id}` : "", item.path, item.reason].filter(Boolean).join(" · ");
  }

  function sourceLine(item = {}, language = "zh-CN") {
    return [item.title || item.id || item.path, item.type_label || item.type, item.path, global.ResearchOSContextPackProjection.sourceBoundary(item, language)].filter(Boolean).join(" · ");
  }

  function renderMarkdown(envelope = {}, digest = "", language = "zh-CN") {
    const copy = (chinese, english) => language === "en" ? english : chinese;
    const listing = (values) => list(values, copy("- （无）", "- None"));
    const unbound = copy("（未绑定）", "(unbound)");
    const unknown = copy("（未知）", "(unknown)");
    const receipt = envelope.handoff_receipt;
    const route = envelope.route;
    const task = envelope.context_pack.task;
    return [
      copy("## Agent 交接包", "## Agent handoff"),
      "",
      `- Packet digest: \`${digest}\``,
      `- ${copy("生成时间", "Generated at")}: ${envelope.generated_at}`,
      `- ${copy("推荐动作", "Recommended action")}: \`${route.recommended_route}\``,
      `- ${copy("语义目标", "Intended action")}: \`${route.intended_route}\``,
      `- Exact thread: ${route.thread_id || unbound}`,
      `- ${copy("路由理由", "Route reasons")}: ${route.reason_codes.join(", ") || "copy_only_fallback"}`,
      `- Transport: ${route.transport_state}; ${copy("失败回退", "fallback")} \`${route.fallback_route}\``,
      "",
      copy("### 目标与当前要求", "### Goal and current instruction"),
      "",
      envelope.prompt,
      "",
      copy("### 项目与任务身份", "### Project and task identity"),
      "",
      `- Primary project: ${envelope.primary_project ? projectLine(envelope.primary_project) : unbound}`,
      `- Commitment/item: ${task.item_id || unbound}`,
      `- Logical task: ${task.logical_task_id || task.id || unbound}`,
      `- Work Session: ${task.session_id || unbound}`,
      "- Related projects:",
      listing(envelope.related_projects.map(projectLine)),
      "",
      copy("### 纳入的文件与资产", "### Included files and assets"),
      "",
      listing(envelope.context_pack.included.map((item) => sourceLine(item, language))),
      "",
      copy("### 明确排除", "### Explicit exclusions"),
      "",
      listing(envelope.context_pack.excluded.map((item) => `${item.scope} · ${item.reason}`)),
      "",
      copy("### 已确认判断、开放边界与下一安全动作", "### Confirmed judgment, open boundary and next safe action"),
      "",
      `- ${copy("已确认判断", "Confirmed judgment")} [${receipt.last_judgment.state}]: ${receipt.last_judgment.text || unknown}`,
      `- ${copy("开放边界", "Open boundary")} [${receipt.open_boundary.state}]: ${receipt.open_boundary.text || unknown}`,
      `- ${copy("下一安全动作", "Next safe action")} [${receipt.next_safe_action.state}]: ${receipt.next_safe_action.text || unknown}`,
      copy("- 禁止动作:", "- Forbidden actions:"),
      listing(receipt.forbidden_actions.items),
      "",
      copy("### 产出与验收", "### Output and acceptance"),
      "",
      `- Result mode: ${envelope.requested_result.mode}`,
      `- Save target: ${envelope.requested_result.save_target || copy("（当前会话回答）", "(answer in the current conversation)")}`,
      "- Definition of Done:",
      listing(envelope.requested_result.definition_of_done),
      "",
      copy("### Authority 与外发边界", "### Authority and egress boundary"),
      "",
      `- Authority owner: ${envelope.authority_owner || copy("（未声明）", "(not declared)")}`,
      `- Authority state: ${envelope.authority_state}`,
      `- Sensitivity: ${envelope.sensitivity}`,
      `- Egress: ${envelope.context_pack.egress.state}`,
      copy("- 本交接只准备上下文，不证明 Agent 任务已创建、已续接、已提交或已交付。", "- This handoff prepares context only. It does not prove that a client task was created, resumed, committed or delivered."),
    ].join("\n");
  }

  async function compose(input = {}, options = {}, deps = {}) {
    const session = input.session && typeof input.session === "object" ? input.session : {};
    const selection = input.selection && typeof input.selection === "object" ? input.selection : {};
    const taskIntentOwner = global.ResearchOSTaskIntent;
    const contextPackOwner = global.ResearchOSContextPackProjection;
    const promptOwner = global.ResearchOSWorkSessionRouter;
    if (!taskIntentOwner?.fromWorkSession) throw contractError("task_intent_contract_unavailable");
    if (!contextPackOwner?.project) throw contractError("context_pack_contract_unavailable");
    if (!promptOwner?.buildPrompt || !promptOwner?.inferResponseMode) throw contractError("work_session_prompt_contract_unavailable");

    const responseMode = promptOwner.inferResponseMode(session.intent, options.responseMode || session.responseMode);
    const taskIntent = taskIntentOwner.fromWorkSession(session, {
      clientRequestId: options.clientRequestId || session.clientRequestId,
      model: options.model || "auto",
      provider: options.provider || "auto",
      reasoningEffort: options.reasoning || "auto",
      recommendedReasoningEffort: options.recommendedReasoning || promptOwner.recommendReasoningEffort(session, responseMode),
      recommendedTaskComplexity: options.recommendedComplexity || promptOwner.recommendTaskComplexity(session, responseMode),
      responseMode,
      taskComplexity: options.taskComplexity || "auto",
    });
    const contextPack = contextPackOwner.project(session, {
      previewDocuments: options.previewDocuments,
      publicStarter: options.publicStarter,
      runtimeMode: options.runtimeMode || "unknown",
    });
    if (!contextPack.active) throw contractError("handoff_session_inactive", "session");
    const exclusions = uniqueExclusions([...safeArray(contextPack.excluded), ...safeArray(selection.excluded)]);
    const includedIds = new Set(contextPack.included.flatMap((item) => [item.id, item.path, item.requested_path].map(clean).filter(Boolean)));
    const conflict = exclusions.find((item) => includedIds.has(item.scope));
    if (conflict) throw contractError("handoff_source_conflict", "excluded");
    const definitionOfDone = safeArray(selection.definitionOfDone)
      .map((item) => bounded(item, 1000, "definitionOfDone"))
      .filter(Boolean);
    if (definitionOfDone.length > MAX_DEFINITION_ITEMS) throw contractError("handoff_input_too_large", "definitionOfDone");
    const primaryProject = project(selection.primaryProject, session.portfolioBinding || {});
    const generatedAt = bounded(options.generatedAt || session.updatedAt || "unknown", 120, "generatedAt");
    const envelopeWithoutDigest = {
      authority_owner: bounded(selection.authority || "", 1000, "authority"),
      authority_state: "projection_not_authority",
      context_pack: {
        ...contextPack,
        excluded: exclusions,
      },
      generated_at: generatedAt,
      handoff_receipt: receiptSummary(input.handoffReceipt),
      primary_project: primaryProject,
      prompt: promptOwner.buildPrompt({ ...session, cards: contextPack.included }, { language: options.language || session.templateLanguage || "zh-CN", responseMode }),
      related_projects: relatedProjects(selection.relatedProjects),
      requested_result: {
        definition_of_done: definitionOfDone,
        mode: taskIntent.requested_result.mode,
        save_target: bounded(selection.saveTarget || "", 2048, "saveTarget"),
      },
      route: routeSummary(input.route),
      schema_id: SCHEMA_ID,
      sensitivity: bounded(session.sensitivity || selection.sensitivity || "internal", 80, "sensitivity"),
      task_intent: taskIntent,
      version: "1",
    };
    const digest = await sha256(canonicalJson(envelopeWithoutDigest), deps);
    if (!/^[0-9a-f]{64}$/.test(digest)) throw contractError("handoff_digest_invalid", "digest");
    const envelope = deepFreeze({ ...envelopeWithoutDigest, packet_digest: digest });
    return deepFreeze({ digest, envelope, markdown: renderMarkdown(envelope, digest, options.displayLanguage || options.language || session.templateLanguage || "zh-CN") });
  }

  global.ResearchOSHandoffComposer = Object.freeze({
    SCHEMA_ID,
    canonicalJson,
    compose,
    renderMarkdown,
  });
})(window);
