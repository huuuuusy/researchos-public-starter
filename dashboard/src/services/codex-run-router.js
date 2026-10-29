/* ResearchOS maintenance header.
 * 中文：Codex 执行路由纯规则；负责交接队列的任务复杂度建议和运行载荷，不拥有网络或界面状态。
 * English: Pure Codex run routing rules for Handoff task-complexity recommendations and payloads; owns no network or UI state.
 */

(function attachResearchOSCodexRunRouter(global) {
  function reasoningForComplexity(complexity = "economy") {
    if (complexity === "deep") return "high";
    if (complexity === "standard") return "medium";
    return "low";
  }

  function complexityForEntry(entry = {}) {
    const candidate = entry.candidate || {};
    const action = candidate.proposed_action || {};
    const writeback = candidate.proposed_writeback || {};
    const validation = candidate.validation || {};
    const text = [
      entry.type,
      entry.typeLabel,
      entry.displayTitle,
      entry.title,
      entry.displayBody,
      entry.body,
      entry.actionId,
      entry.status,
      action.target_agent,
      candidate.required_confirmation,
      validation.evidence_state,
      candidate.summary,
      writeback.save_target,
      writeback.object_type,
      writeback.object_id,
      writeback.object_path,
    ].filter(Boolean).join(" ").toLowerCase();

    if ([
      "mrm4", "m4", "technical report", "技术报告", "主体文档", "主线强化", "深度综合", "全面重构",
    ].some((token) => text.includes(token))) return "deep";

    if ([
      "mrm3", "m3", "material-upgrade", "upgrade", "升级", "深读", "补证据", "needs_evidence",
      "evidence", "asset_cartographer", "research_scout", "project_steward", "writing_agent", "synthesis", "综合",
    ].some((token) => text.includes(token))) return "standard";

    if ([
      "archive", "归档", "status", "stage", "public", "confirm", "reject", "是与否", "分类",
    ].some((token) => text.includes(token))) return "economy";

    return "standard";
  }

  function complexityForBudget(budgetChoice = {}) {
    const value = [budgetChoice.id, budgetChoice.mode, budgetChoice.depth, budgetChoice.label]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    if (/(evidence|deep|full|全面|证据|深度)/.test(value)) return "deep";
    if (/(quick|economy|节省|快速)/.test(value)) return "economy";
    return "standard";
  }

  function payloadForAgentPrompt({ budgetChoice = {}, model = "auto", prompt = "", reasoning = "auto", task = {} } = {}) {
    const taskId = String(task?.id || "custom").trim() || "custom";
    const title = String(task?.name || task?.goal || taskId).trim();
    const complexity = complexityForBudget(budgetChoice);
    return {
      source: "dashboard-agent-composer",
      task_mode: "read_only_analysis",
      response_mode: "answer",
      task_complexity: "auto",
      recommended_task_complexity: complexity,
      model: String(model || "auto"),
      reasoning_effort: String(reasoning || "auto"),
      recommended_reasoning_effort: reasoningForComplexity(complexity),
      title,
      prompt: String(prompt || "").trim(),
      candidate: {
        candidate_id: `candidate:agent-composer:${taskId}`,
        plugin_id: "researchos_core",
        candidate_type: "task",
        source_refs: [],
        summary: title,
        proposed_action: { id: "run_task", target_agent: "research_assistant" },
        proposed_writeback: { save_target: "", object_type: "task", object_id: taskId, object_path: "" },
        sensitivity: "internal",
        required_confirmation: "handoff_only",
        validation: {
          workflow_status: "active",
          evidence_state: "candidate",
          authority_state: "proposed",
          state: "not_run",
        },
      },
    };
  }

  function payloadForEntries(entries = [], prompt = "", title = "", options = {}) {
    const safeEntries = Array.isArray(entries) ? entries : [];
    const selectedReasoning = options.selectedReasoning || "auto";
    const selectedModel = options.selectedModel || "auto";
    return {
      source: "dashboard-unified-inbox",
      task_mode: "direct_execution",
      task_complexity: "auto",
      model: selectedModel,
      reasoning_effort: selectedReasoning,
      title: title || options.fallbackTitle || "",
      prompt,
      entries: safeEntries.map((entry) => {
        const recommendedComplexity = complexityForEntry(entry);
        const recommendedReasoning = reasoningForComplexity(recommendedComplexity);
        return {
          type: entry.type,
          typeLabel: entry.typeLabel,
          title: entry.displayTitle || entry.title || "",
          body: entry.displayBody || entry.body || "",
          path: entry.path || "",
          sourcePath: entry.sourcePath || "",
          status: entry.status || "",
          actionId: entry.actionId || "",
          candidate: entry.candidate || {},
          recommended_task_complexity: recommendedComplexity,
          recommended_reasoning_effort: recommendedReasoning,
          task_complexity: recommendedComplexity,
          reasoning_effort: selectedReasoning === "auto" ? recommendedReasoning : selectedReasoning,
          task_complexity_mode: "auto_recommended",
          reasoning_effort_mode: selectedReasoning === "auto" ? "auto_recommended" : "manual_override",
        };
      }),
      candidate: safeEntries.length === 1
        ? safeEntries[0].candidate || {}
        : options.candidateEnvelopeForBatch?.(safeEntries) || {},
    };
  }

  global.ResearchOSCodexRunRouter = Object.freeze({
    payloadForAgentPrompt,
    payloadForEntries,
  });
})(window);
