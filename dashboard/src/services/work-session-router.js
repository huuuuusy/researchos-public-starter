/* ResearchOS maintenance header.
 * 中文：工作会话意图、风险与任务复杂度建议的纯路由 owner；不绑定 DOM，不执行写入。
 * English: Pure routing owner for work-session intent, risk, and task-complexity recommendations; no DOM or write side effects.
 */

(function attachResearchOSWorkSessionRouter(global) {
  const RESPONSE_MODES = Object.freeze(["answer", "artifact", "writeback"]);
  const DEEP_INTENT_MARKERS = Object.freeze([
    "全面审计", "全面重构", "架构重构", "技术报告", "系统综述", "深度综合", "多文件综合",
    "full audit", "architecture refactor", "technical report", "systematic review", "deep synthesis",
  ]);
  const STANDARD_INTENT_MARKERS = Object.freeze([
    "分析", "判断", "比较", "阅读", "论文", "pdf", "证据", "综合", "review", "analyze",
    "compare", "paper", "evidence", "synthesis",
  ]);
  const CURRENT_STATE_MARKERS = Object.freeze([
    "今天", "当前", "现在", "下一步", "优先", "进度", "状态", "待办",
    "today", "current", "right now", "next", "priority", "progress", "status", "todo",
  ]);

  function cleanText(value = "") {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function includesAny(text = "", markers = []) {
    const normalized = cleanText(text).toLowerCase();
    return markers.some((marker) => normalized.includes(String(marker).toLowerCase()));
  }

  function isChineseLanguage(language = "zh-CN") {
    return cleanText(language).toLowerCase().startsWith("zh");
  }

  function normalizeResponseMode(mode = "auto") {
    const value = cleanText(mode).toLowerCase();
    return RESPONSE_MODES.includes(value) ? value : "auto";
  }

  function inferResponseMode(intent = "", requestedMode = "auto") {
    const explicit = normalizeResponseMode(requestedMode);
    if (explicit !== "auto") return explicit;
    if (includesAny(intent, [
      "写回", "沉淀", "长期记忆", "更新 researchos", "更新 research os", "加入记忆",
      "write back", "durable memory", "confirmed memory", "update researchos",
    ])) return "writeback";
    if (includesAny(intent, [
      "生成文件", "生成文档", "生成 markdown", "整理成", "写成报告", "保存为", "导出",
      "create a file", "generate a document", "save as", "export", "write a report",
    ])) return "artifact";
    return "answer";
  }

  function sourceCount(session = {}) {
    const sources = Array.isArray(session.sourceHints) ? session.sourceHints.filter(Boolean) : [];
    const cards = Array.isArray(session.cards) ? session.cards.filter(Boolean) : [];
    return new Set([
      ...sources.map(cleanText),
      ...cards.map((card) => cleanText(card.path || card.id || card.title)),
    ].filter(Boolean)).size;
  }

  function recommendTaskComplexity(session = {}, requestedMode = "auto") {
    const mode = inferResponseMode(session.intent, requestedMode || session.responseMode);
    const intent = cleanText(session.intent);
    const sources = sourceCount(session);
    if (includesAny(intent, DEEP_INTENT_MARKERS) || sources >= 5) return "deep";
    if (mode === "artifact" || mode === "writeback" || sources > 0 || includesAny(intent, STANDARD_INTENT_MARKERS)) return "standard";
    if (includesAny(intent, [
      "分类", "归档", "改状态", "列出文件", "查找路径", "classify", "archive", "status", "locate",
    ])) return "economy";
    return "standard";
  }

  function recommendReasoningEffort(session = {}, requestedMode = "auto") {
    const mode = inferResponseMode(session.intent, requestedMode || session.responseMode);
    const complexity = recommendTaskComplexity(session, mode);
    if (complexity === "deep") return "high";
    if (complexity === "economy") return "low";
    if (mode === "artifact" || mode === "writeback" || sourceCount(session) > 0) return "medium";
    return includesAny(session.intent, STANDARD_INTENT_MARKERS) ? "medium" : "low";
  }

  function contextRoute(session = {}) {
    const intent = cleanText(session.intent);
    if (includesAny(intent, DEEP_INTENT_MARKERS) || sourceCount(session) >= 5) return "deep_audit";
    if (sourceCount(session) > 0) return "session_sources";
    if (includesAny(intent, CURRENT_STATE_MARKERS)) return "current_state";
    return "quick";
  }

  function contextInstruction(session = {}, language = "zh-CN", options = {}) {
    const route = contextRoute(session);
    const isZh = isChineseLanguage(language);
    if (route === "deep_audit") {
      return isZh
        ? "上下文路由：deep_audit。把审计拆成问题明确的小批次；首批最多读取 5 个直接相关的来源、入口或 canonical 文件。先说明仍缺的事实或验证问题，再扩到下一批；不得以全面审计为由无差别扫描整库。"
        : "Context route: deep_audit. Split the audit into question-specific batches. Read at most five directly relevant sources, entry files, or canonical files in the first batch. Name the missing fact or verification question before expanding; do not scan the repository indiscriminately.";
    }
    if (route === "session_sources") {
      return isZh
        ? "上下文路由：session_sources。先只读取本轮明确提供的来源；首批最多 3 个，来源更多时分批处理。只有在这些来源不足以回答时，才说明缺口并读取 1 个直接相关入口；不得顺手扫描整库或历史审计。"
        : "Context route: session_sources. Start with only the sources explicitly provided for this session, at most three in the first batch. If they are insufficient, name the gap before reading one directly relevant entry file; do not scan the repository or historical audits by default.";
    }
    if (route === "current_state") {
      if (options.publicStarter === true) {
        return isZh
          ? "上下文路由：current_state。公开 starter 不拥有你的私人当前状态，也不会从 demo 数据推断今天的优先级。先只使用本轮目标与来源；若在你自己的 personal vault 中执行，请让所选助手读取该 vault 的最短 current-task/current-project 入口。没有这些材料时明确说明缺口，不读取示例状态或带日期的旧审计来补全。"
          : "Context route: current_state. The public starter does not own your private current state and must not infer today's priorities from demo data. Start with only this session's goal and sources. When running inside your personal vault, ask the chosen assistant for that vault's shortest current-task/current-project entry. If it is unavailable, state the gap instead of filling it from examples or dated audits.";
      }
      return isZh
        ? "上下文路由：current_state。首轮只读取 `06_active_context/research-portfolio.md` 中直接相关的责任项；需要项目边界时再追加 `current-projects.md`，询问人物时改读 `current-people.md`。信息足够就停止，不读取带日期的旧看板、计划或审计；只有当前权威明确指向且仍缺关键事实时，才追加 1 个精确来源。"
        : "Context route: current_state. First read only the directly relevant responsibility item in `06_active_context/research-portfolio.md`; add `current-projects.md` only for a project boundary, or use `current-people.md` for a people question. Stop when sufficient. Do not read dated boards, plans, or audits unless the current authority points to one and a specific fact is still missing.";
    }
    if (options.publicStarter === true) {
      return isZh
        ? "上下文路由：quick。优先只根据用户目标回答；确需 ResearchOS 背景时，先读 `docs/user-manual.zh.md` 第 2 节，再最多读取 2 个由它直接路由的 canonical 文件。信息足够就停止，不做整库扫描，也不默认读取运行日志、历史审计、raw corpus 或 people-sensitive 材料。"
        : "Context route: quick. Answer from the user goal first. If ResearchOS context is required, read Section 2 of `docs/user-manual.en.md` and at most two canonical files directly routed from it. Stop when sufficient; do not scan the repository or read runtime logs, historical audits, raw corpus, or people-sensitive material by default.";
    }
    return isZh
      ? "上下文路由：quick。优先只根据用户目标回答；确需 ResearchOS 背景时，先读 `START_HERE.md`，再最多读取 2 个由它直接路由的 canonical 文件。信息足够就停止，不做整库扫描，也不默认读取运行日志、历史审计、raw corpus 或 people-sensitive 材料。"
      : "Context route: quick. Answer from the user goal first. If ResearchOS context is required, read `START_HERE.md` and at most two canonical files directly routed from it. Stop when sufficient; do not scan the repository or read runtime logs, historical audits, raw corpus, or people-sensitive material by default.";
  }

  function taskModeForResponseMode(mode = "answer") {
    if (mode === "artifact") return "direct_execution";
    if (mode === "writeback") return "candidate_patch_plan";
    return "read_only_analysis";
  }

  function sourceLines(session = {}) {
    const lines = [];
    const cards = (session.cards || []).filter(Boolean);
    const cardRefs = new Set(cards.flatMap((card) => [card.id, card.path, card.title].map(cleanText).filter(Boolean)));
    (session.sourceHints || []).filter(Boolean).forEach((source) => {
      const normalized = cleanText(source);
      if (!cardRefs.has(normalized)) lines.push(`- ${normalized}`);
    });
    cards.forEach((card) => {
      const label = [...new Set([card.typeLabel || card.type, card.title, card.path].map(cleanText).filter(Boolean))].join(": ");
      const boundary = global.ResearchOSContextPackProjection?.sourceBoundary(card, session.templateLanguage || "zh-CN") || "";
      if (label) lines.push(`- ${cleanText(label)}${boundary ? ` · ${boundary}` : ""}`);
    });
    return [...new Set(lines)];
  }

  function conversationLines(session = {}, language = "zh-CN") {
    const isZh = isChineseLanguage(language);
    const separator = isZh ? "：" : ": ";
    const turns = (Array.isArray(session.turns) ? session.turns : []).slice(-6);
    let remaining = 12000;
    const lines = [];
    turns.forEach((turn) => {
      if (remaining <= 0) return;
      const question = cleanText(turn.question).slice(0, 1200);
      const answer = turn.includeInPrompt === false
        ? ""
        : String(turn.answer || "").trim().slice(0, Math.min(3200, remaining));
      if (!question) return;
      const block = answer
        ? `${isZh ? "用户" : "User"}${separator}${question}\nResearchOS${separator}${answer}`
        : `${isZh ? "先前处理要求" : "Prior instruction"}${separator}${question}`;
      lines.push(block);
      remaining -= block.length;
    });
    return lines;
  }

  function buildPrompt(session = {}, options = {}) {
    const mode = inferResponseMode(session.intent, options.responseMode || session.responseMode);
    const language = cleanText(options.language || session.templateLanguage || "zh-CN");
    const isZh = isChineseLanguage(language);
    const separator = isZh ? "：" : ": ";
    const objective = cleanText(session.goal || session.title || session.intent);
    const currentInstruction = cleanText(session.intent);
    const sources = sourceLines(session);
    const conversation = conversationLines(session, language);
    const resumeSummary = cleanText(session.resumeSummary).slice(0, 2400);
    const resumeArtifacts = (Array.isArray(session.resumeArtifacts) ? session.resumeArtifacts : [])
      .map((artifact) => cleanText(typeof artifact === "string" ? artifact : artifact?.path))
      .filter(Boolean)
      .slice(0, 8);
    const modeInstruction = mode === "artifact"
      ? isZh
        ? "用户明确要求生成成果文件。只创建完成本任务所需的文件，并在回答中说明产物路径与内容要点。"
        : "The user explicitly requested an artifact. Create only the files required for this task, then report their paths and key contents."
      : mode === "writeback"
        ? isZh
          ? "先给出可审阅的候选修改与证据边界，不要直接改写长期记忆、稳定认知或公开内容。"
          : "Return a reviewable candidate change and its evidence boundary first. Do not directly rewrite durable memory, stable cognition, or public content."
        : isZh
        ? "直接回答用户的问题。不要创建或修改文件；把完整、可读的结果返回当前助手会话。"
        : "Answer the user's question directly. Do not create or modify files; return the complete readable result in the current assistant conversation.";
    const responseShapeInstruction = includesAny(session.intent, ["一句话", "单句", "one sentence"])
      ? isZh
        ? "用户明确要求单句回答：只返回一句完整的话，不追加标题、依据、不确定性或下一步。"
        : "The user explicitly requested one sentence. Return exactly one complete sentence with no heading, evidence section, uncertainty section, or next step."
      : includesAny(session.intent, ["简短", "简洁", "briefly", "concise", "short answer"])
        ? isZh
          ? "用户明确要求简短回答：直接给结论，只保留理解该结论不可缺少的信息。"
          : "The user explicitly requested a concise answer. Give the conclusion directly and retain only information essential to understand it."
        : isZh
          ? "用户没有指定特殊格式时，先给核心判断，再给必要依据、不确定性和可选下一步。"
          : "When the user has not specified a format, give the core judgment first, followed by only the necessary evidence, uncertainty, and optional next step.";
    return [
      objective && objective !== currentInstruction
        ? `${isZh ? "任务目标" : "Task objective"}${separator}${objective}\n${isZh ? "当前处理要求" : "Current instruction"}${separator}${currentInstruction}`
        : `${isZh ? "用户目标" : "User goal"}${separator}${currentInstruction}`,
      resumeSummary && resumeSummary !== currentInstruction ? `${isZh ? "上次任务摘要（不是完整聊天记录）" : "Previous task summary (not a full chat transcript)"}${separator.trim()}\n${resumeSummary}${resumeArtifacts.length ? `\n${isZh ? "已有成果" : "Existing artifacts"}${separator.trim()}\n${resumeArtifacts.map((path) => `- ${path}`).join("\n")}` : ""}` : "",
      conversation.length ? `${isZh ? "本任务先前步骤（由旧到新）" : "Prior task steps (oldest to newest)"}${separator.trim()}\n\n${conversation.join("\n\n")}` : "",
      sources.length ? `${isZh ? "本轮来源" : "Session sources"}${separator.trim()}\n${sources.join("\n")}` : "",
      contextInstruction(session, language, options),
      session.evidenceBoundary ? `${isZh ? "证据与权限边界" : "Evidence and permission boundary"}${separator}${cleanText(session.evidenceBoundary)}` : "",
      `${isZh ? "回答语言" : "Response language"}${separator}${language}`,
      modeInstruction,
      responseShapeInstruction,
      isZh
        ? "严格遵循用户明确指定的篇幅、结构、语气和输出格式。不要把内部运行日志当作用户结果。"
        : "Follow any user-specified length, structure, tone, and output format exactly. Do not present internal runtime logs as the user result.",
    ].filter(Boolean).join("\n\n");
  }

  function previousAnswer(runs = [], session = {}) {
    const latestArchivedAnswer = String(session.turns?.[session.turns.length - 1]?.answer || "").trim();
    return String(resultForSession(runs, session)?.answer || latestArchivedAnswer).trim();
  }

  function runPayload(session = {}, options = {}, deps = {}) {
    const responseMode = inferResponseMode(session.intent, options.responseMode || session.responseMode || "auto");
    const recommendedComplexity = recommendTaskComplexity(session, responseMode);
    const recommendedReasoning = recommendReasoningEffort(session, responseMode);
    const language = cleanText(deps.language || session.templateLanguage || "zh-CN");
    const selectedModel = cleanText(deps.selectedModel || "auto") || "auto";
    const selectedReasoning = cleanText(deps.selectedReasoning || "auto") || "auto";
    const text = deps.text || ((key) => key);
    const taskIntentOwner = global.ResearchOSTaskIntent;
    if (!taskIntentOwner?.fromWorkSession) throw new Error("task_intent_contract_unavailable");
    const priorAnswer = previousAnswer(deps.runs || [], session);
    const prompt = options.artifactFromResult && priorAnswer
      ? [
          options.promptSuffix,
          `${text("workSessionPreviousResult")}\n\n${priorAnswer}`,
          `${isChineseLanguage(language) ? "回答语言：" : "Response language: "}${language}`,
        ].filter(Boolean).join("\n\n")
      : [
          buildPrompt(session, { language, responseMode }),
          options.promptSuffix || "",
          options.promptSuffix && priorAnswer
            ? `${text("workSessionPreviousResult")}\n\n${priorAnswer}`
            : "",
        ].filter(Boolean).join("\n\n");
    const suppliedCandidate = session.candidate && typeof session.candidate === "object" ? session.candidate : {};
    const suppliedWriteback = suppliedCandidate.proposed_writeback && typeof suppliedCandidate.proposed_writeback === "object"
      ? suppliedCandidate.proposed_writeback
      : {};
    const sourcePath = session.sourceHints?.[0] || session.cards?.find((card) => card.path)?.path || "";
    const artifactCandidate = {
      candidate_id: suppliedCandidate.candidate_id || suppliedCandidate.id || `candidate:work-session:${session.id || Date.now()}`,
      plugin_id: "researchos_core",
      candidate_type: "work_session",
      source_refs: Array.isArray(suppliedCandidate.source_refs)
        ? suppliedCandidate.source_refs
        : sourcePath ? [{ kind: "session_source", path: sourcePath }] : [],
      summary: options.artifactFromResult ? options.promptSuffix || "" : session.intent || "",
      proposed_action: { id: "work_session_artifact", target_agent: "research_assistant" },
      proposed_writeback: {
        ...suppliedWriteback,
        save_target: "",
        object_type: "work_session_artifact",
        object_id: session.id || "",
        object_path: "",
      },
      sensitivity: suppliedCandidate.sensitivity || session.sensitivity || "internal",
      required_confirmation: "none",
      validation: suppliedCandidate.validation || {
        workflow_status: "active",
        evidence_state: "working",
        authority_state: "proposed",
        state: "not_run",
      },
      source_agent: "researchos_workbench",
      status: suppliedCandidate.validation?.workflow_status || suppliedCandidate.status || "active",
    };
    return {
      source: "dashboard-work-session",
      task_mode: taskModeForResponseMode(responseMode),
      response_mode: responseMode,
      work_session_id: session.id || "",
      task_complexity: "auto",
      model: selectedModel,
      recommended_task_complexity: recommendedComplexity,
      reasoning_effort: selectedReasoning,
      recommended_reasoning_effort: recommendedReasoning,
      title: session.title || session.intent || text("workSessionCurrent"),
      prompt,
      task_intent: taskIntentOwner.fromWorkSession(session, {
        clientRequestId: deps.clientRequestId || session.clientRequestId,
        model: selectedModel,
        provider: deps.selectedProvider || "auto",
        reasoningEffort: selectedReasoning,
        recommendedReasoningEffort: recommendedReasoning,
        recommendedTaskComplexity: recommendedComplexity,
        responseMode,
        taskComplexity: "auto",
      }),
      candidate: responseMode === "artifact" ? artifactCandidate : session.candidate && typeof session.candidate === "object" ? {
        ...session.candidate,
        source_agent: "researchos_workbench",
        status: session.candidate.validation?.workflow_status || session.candidate.status || "active",
      } : {
        id: `candidate:work-session:${session.id || Date.now()}`,
        source_agent: "researchos_workbench",
        target_agent: responseMode === "writeback" ? "inbox_secretary" : "research_assistant",
        object_ref: {
          type: "work_session",
          id: session.id || "",
          path: session.sourceHints?.[0] || session.cards?.find((card) => card.path)?.path || "",
        },
        claim_or_task: options.artifactFromResult ? options.promptSuffix || "" : session.intent || "",
        evidence_state: responseMode === "writeback" ? "candidate" : "working",
        sensitivity: session.sensitivity || "internal",
        required_confirmation: responseMode === "writeback" ? "candidate_diff" : "none",
        status: "active",
      },
    };
  }

  function resultIdentityProjection(result = null, session = {}) {
    if (!result || typeof result !== "object") {
      return Object.freeze({ state: "none", reason: "no_result", result: null });
    }
    const sessionId = cleanText(session.id);
    const expectedRunId = cleanText(session.latestRunId);
    const expectedRequestId = cleanText(session.clientRequestId || session.client_request_id);
    const observedSessionId = cleanText(result.work_session_id || result.result_envelope?.work_session_id || result.error_envelope?.work_session_id);
    const observedRunId = cleanText(result.id || result.run_id || result.result_envelope?.run_id || result.error_envelope?.run_id);
    const observedRequestId = cleanText(result.client_request_id || result.result_envelope?.client_request_id || result.error_envelope?.client_request_id);
    const provenance = Object.freeze({
      expected_client_request_id: expectedRequestId,
      expected_run_id: expectedRunId,
      observed_client_request_id: observedRequestId,
      observed_run_id: observedRunId,
      observed_work_session_id: observedSessionId,
      work_session_id: sessionId,
    });
    let reason = "";
    if (!sessionId) reason = "missing_current_work_session_id";
    else if (!observedSessionId) reason = "missing_result_work_session_id";
    else if (observedSessionId !== sessionId) reason = "work_session_id_mismatch";
    else if (expectedRunId && !observedRunId) reason = "missing_result_run_id";
    else if (expectedRunId && observedRunId !== expectedRunId) reason = "run_id_mismatch";
    else if (expectedRequestId && !observedRequestId) reason = "missing_result_client_request_id";
    else if (expectedRequestId && observedRequestId !== expectedRequestId) reason = "client_request_id_mismatch";
    if (reason) return Object.freeze({ state: "withheld", reason, provenance, result: null });
    return Object.freeze({ state: "matched", reason: "identity_matched", provenance, result });
  }

  function resultProjectionForSession(runs = [], session = {}) {
    const latestRunId = cleanText(session.latestRunId);
    const sessionId = cleanText(session.id);
    const availableRuns = Array.isArray(runs) ? runs : [];
    let candidate = null;
    if (session.status === "running" && session.draftResult?.status === "running") {
      candidate = session.draftResult;
    } else if (latestRunId) {
      const exactRun = availableRuns.find((run) => cleanText(run.id) === latestRunId);
      candidate = exactRun || session.draftResult || null;
    } else if (session.draftResult?.status === "failed") {
      candidate = session.draftResult;
    } else {
      candidate = session.draftResult || availableRuns.find((run) => sessionId && cleanText(run.work_session_id) === sessionId) || null;
    }
    return resultIdentityProjection(candidate, session);
  }

  function resultForSession(runs = [], session = {}) {
    return resultProjectionForSession(runs, session).result;
  }

  function publicTaskPacket(session = {}, options = {}) {
    const mode = inferResponseMode(session.intent, options.responseMode || session.responseMode);
    const prompt = buildPrompt(session, { ...options, publicStarter: true, responseMode: mode });
    const isZh = isChineseLanguage(options.language || session.templateLanguage || "zh-CN");
    const recommendedComplexity = recommendTaskComplexity(session, mode);
    const recommendedReasoning = recommendReasoningEffort(session, mode);
    const requestedModel = cleanText(options.model || "auto") || "auto";
    const requestedReasoning = cleanText(options.reasoning || "auto") || "auto";
    const localizedComplexity = isZh
      ? ({ economy: "轻量（economy）", standard: "标准（standard）", deep: "深入（deep）" }[recommendedComplexity] || recommendedComplexity)
      : recommendedComplexity;
    const localizedReasoning = isZh
      ? ({ low: "低（low）", medium: "中等（medium）", high: "高（high）" }[recommendedReasoning] || recommendedReasoning)
      : recommendedReasoning;
    const modelPreference = requestedModel === "auto"
      ? (isZh ? "Auto（接收任务包的助手默认）" : "Auto (receiving assistant default)")
      : requestedModel;
    const reasoningPreference = requestedReasoning === "auto"
      ? (isZh ? `Auto（本任务建议 ${localizedReasoning}）` : `Auto (${recommendedReasoning} recommended for this task)`)
      : isZh
        ? ({ low: "低（low）", medium: "中等（medium）", high: "高（high）" }[requestedReasoning] || requestedReasoning)
        : requestedReasoning;
    const executionPreference = isZh
      ? `执行偏好（本页未执行）：\n- 模型：${modelPreference}\n- 推理：${reasoningPreference}\n- 任务复杂度建议：${localizedComplexity}`
      : `Execution preference (not run on this page):\n- Model: ${modelPreference}\n- Reasoning: ${reasoningPreference}\n- Task complexity recommendation: ${recommendedComplexity}`;
    return {
      answer: [
        options.heading || (isZh ? "## 任务包已准备好" : "## Task packet ready"),
        "",
        options.body || (isZh
          ? "公开版不会把你的材料发送给模型。请把下面的任务包复制到能访问你私人工作副本的助手中；如果助手不能读取本地路径，请在那里另行附加文件。"
          : "The public starter does not send your material to a model. Copy the task packet below into an assistant that can access your private working copy. If it cannot read local paths, attach the file there separately."),
        "",
        "```text",
        executionPreference,
        "",
        prompt,
        "```",
      ].join("\n"),
      execution_status: "copy_ready",
      id: `public-result-${Date.now()}`,
      task_complexity: recommendedComplexity,
      model: requestedModel,
      reasoning_effort: requestedReasoning === "auto" ? recommendedReasoning : requestedReasoning,
      response_mode: mode,
      status: "completed",
      title: cleanText(session.title || session.intent),
      work_session_id: cleanText(session.id),
    };
  }

  global.ResearchOSWorkSessionRouter = Object.freeze({
    RESPONSE_MODES,
    buildPrompt,
    contextRoute,
    conversationLines,
    inferResponseMode,
    publicTaskPacket,
    recommendTaskComplexity,
    recommendReasoningEffort,
    resultIdentityProjection,
    resultForSession,
    resultProjectionForSession,
    runPayload,
    sourceCount,
    sourceLines,
    taskModeForResponseMode,
  });
})(window);
