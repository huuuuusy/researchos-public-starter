/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「agent prompt」；只组装统一收件箱的 Agent 交接 prompt。
 * English: Frontend service for agent prompts in the ResearchOS dashboard; builds the unified-inbox handoff prompt only.
 *   Prompt lines that differ between the private and public editions come from ui-copy-profile.js (agentPrompt).
 */

(function attachResearchOSAgentPromptService(global) {
  function isChineseUi(language = "zh-CN") {
    return String(language || "").toLowerCase().startsWith("zh");
  }

  // Edition-specific prompt lines for one language; a missing entry yields no line.
  function promptProfile(language = "zh-CN") {
    return global.ResearchOSUICopyProfile?.agentPrompt?.[isChineseUi(language) ? "zh-CN" : "en"] || {};
  }

  function buildCodexInboxTaskPrompt({ entries = [], paths = {}, language = "zh-CN" } = {}) {
    const candidatePaths = (Array.isArray(paths.candidates) ? paths.candidates : [])
      .map((source) => String(source?.path || "").trim())
      .filter(Boolean)
      .map((path) => `- ${path}`);
    const copy = promptProfile(language);
    if (!isChineseUi(language)) {
      return [
        copy.inboxTitle || "",
        "",
        ...(copy.inboxPreamble || []),
        "Read only the relevant inbox file(s) first:",
        `- ${paths.confirmation || ""}`,
        `- ${paths.feedback || ""}`,
        ...candidatePaths,
        `- ${paths.cardGroups || ""}`,
        `- ${paths.cardGroupDissolution || ""}`,
        "",
        "Current UI snapshot:",
        JSON.stringify(entries, null, 2),
        "",
        ...(copy.inboxRules || []),
        "",
        copy.inboxReturn || "",
      ].join("\n");
    }
    return [
      copy.inboxTitle || "",
      "",
      ...(copy.inboxPreamble || []),
      "只先读取相关收件箱文件：",
      `- ${paths.confirmation || ""}`,
      `- ${paths.feedback || ""}`,
      ...candidatePaths,
      `- ${paths.cardGroups || ""}`,
      `- ${paths.cardGroupDissolution || ""}`,
      "",
      "当前 UI 汇总快照：",
      JSON.stringify(entries, null, 2),
      "",
      ...(copy.inboxRules || []),
      "",
      copy.inboxReturn || "",
    ].join("\n");
  }

  global.ResearchOSAgentPromptService = Object.freeze({
    buildCodexInboxTaskPrompt,
  });
})(window);
