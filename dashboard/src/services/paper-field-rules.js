/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端业务规则「paper field rules」；保持语义判断独立于 app 编排和 view 模板。
 * English: Frontend rule owner for paper field rules in the ResearchOS dashboard; keeps semantic decisions separate from app orchestration and view templates.
 */

(function attachResearchOSPaperFieldRules(global) {
  function paperFieldOptions(kind = "", text = (key) => key) {
    if (kind === "stage") {
      return [
        ["accepted_or_published", text("paperStageAccepted")],
        ["preprint", text("paperStagePreprint")],
        ["submitted_version", text("paperStageSubmitted")],
        ["in_progress", text("paperStageProgress")],
        ["idea_seed", text("paperStageIdea")],
        ["thesis", text("paperStageThesis")],
        ["unknown", text("paperStageUnknown")],
      ];
    }
    if (kind === "public_boundary") {
      return [
        ["stable_public", text("paperBoundaryStable")],
        ["public_candidate", text("paperBoundaryCandidate")],
        ["internal", text("paperBoundaryInternal")],
        ["local_only", text("paperBoundaryLocal")],
        ["needs_confirmation", text("paperBoundaryConfirm")],
      ];
    }
    if (kind === "ccf_rank") {
      return [
        ["A", text("paperCcfA")],
        ["B", text("paperCcfB")],
        ["C", text("paperCcfC")],
        ["not_applicable", text("paperCcfNA")],
        ["unknown", text("paperCcfUnknown")],
      ];
    }
    return [
      ["M1_registered", text("paperDepthM1")],
      ["M2_refined_read", text("paperDepthM2")],
      ["M3_cross_project_deepening", text("paperDepthM3")],
    ];
  }

  function paperFieldLabel(kind = "", value = "", text = (key) => key) {
    const option = paperFieldOptions(kind, text).find(([candidate]) => candidate === value);
    return option ? option[1] : value;
  }

  function paperFieldSummary(fields = {}, text = (key) => key) {
    const parts = [];
    if (fields.stage) parts.push(`${text("paperFieldStage")}=${paperFieldLabel("stage", fields.stage, text)}`);
    if (fields.public_boundary) {
      parts.push(`${text("paperFieldBoundary")}=${paperFieldLabel("public_boundary", fields.public_boundary, text)}`);
    }
    if (fields.ccf_rank) parts.push(`${text("paperFieldCcf")}=${paperFieldLabel("ccf_rank", fields.ccf_rank, text)}`);
    if (fields.analysis_state) {
      parts.push(`${text("paperFieldDepth")}=${paperFieldLabel("analysis_state", fields.analysis_state, text)}`);
    }
    return parts.join(" · ");
  }

  global.ResearchOSPaperFieldRules = Object.freeze({
    paperFieldLabel,
    paperFieldOptions,
    paperFieldSummary,
  });
})(window);
