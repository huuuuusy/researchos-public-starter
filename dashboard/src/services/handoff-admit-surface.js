/* ResearchOS maintenance header.
 * 中文：第三屏 Handoff/Admit candidate 的唯一模式与投影 owner；默认关闭，不推断 authority 或执行能力。
 * English: Sole mode/projection owner for the third-surface Handoff/Admit candidate; default-off and non-authoritative.
 */

(function attachResearchOSHandoffAdmitSurface(global) {
  const LEGACY_MODE = "legacy_work_session";
  const CANDIDATE_MODE = "handoff_admit_candidate";

  function enabled(config) {
    return Boolean(config && typeof config === "object" && !Array.isArray(config)
      && config.handoff_admit_candidate === true);
  }

  function cleanText(value, maximum = 500) {
    if (typeof value !== "string" || value.includes("\0")) return "";
    return [...value.trim()].slice(0, maximum).join("");
  }

  function project(options = {}) {
    const session = options.session && typeof options.session === "object" ? options.session : null;
    const mode = enabled(options.config) ? CANDIDATE_MODE : LEGACY_MODE;
    if (mode === LEGACY_MODE || !session) return Object.freeze({ mode: LEGACY_MODE });
    const result = options.result && typeof options.result === "object" ? options.result : null;
    const resultStatus = ["submitted", "queued", "running", "completed", "failed"].includes(result?.status)
      ? result.status : "unknown";
    const resultMode = ["answer", "artifact", "writeback"].includes(result?.response_mode || result?.result_mode)
      ? (result.response_mode || result.result_mode) : "unknown";
    return Object.freeze({
      mode: CANDIDATE_MODE,
      goal: cleanText(session.portfolioBinding?.title || session.title || session.goal || session.intent, 1000),
      result: Object.freeze({ mode: resultMode, status: resultStatus }),
      routes: Object.freeze({
        manual: Object.freeze({ available: true, outcome: "no_system_action" }),
        codex: Object.freeze({ available: true, outcome: "copy_task_packet" }),
        background: Object.freeze({
          available: options.backgroundPreparationAvailable === true,
          outcome: options.backgroundPreparationAvailable === true ? "registered_task_only" : "not_registered",
        }),
        review: Object.freeze({
          available: true,
          outcome: options.handoffActive === true ? "open_existing_review" : "create_handoff_review_item",
        }),
      }),
      limitations: Object.freeze([
        "candidate_not_default", "dashboard_not_work_client", "review_not_admission", "no_authority_change",
      ]),
    });
  }

  global.ResearchOSHandoffAdmitSurface = Object.freeze({ CANDIDATE_MODE, LEGACY_MODE, enabled, project });
})(window);
