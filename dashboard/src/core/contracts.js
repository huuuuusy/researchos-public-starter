/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「contracts」；供 app、service、view 复用。
 * English: Browser-side core primitive for contracts in the ResearchOS dashboard; shared by app, services, and views.
 */

(function attachResearchOSContracts(global) {
  const primitiveTypes = Object.freeze(["atom", "edge", "state", "action", "view", "rule"]);

  const stateAxes = Object.freeze({
    L: Object.freeze(["L0_route", "L1_capsule", "L2_canonical", "L3_evidence"]),
    M: Object.freeze(["M1_registered", "M2_refined_read", "M3_cross_project_deepening"]),
    G: Object.freeze(["G0_atom", "G1_basic_group", "G2_direction_abstraction", "R_research_mainline"]),
    I: Object.freeze([
      "I0_assessment",
      "I1_sandbox",
      "I2_active_mount",
      "I3_independent_project",
      "I_hold",
      "I_archive",
    ]),
    Priority: Object.freeze(["P0", "P1", "P2", "P3"]),
    Workflow: Object.freeze(["active", "processed", "archived", "withdrawn"]),
    EvidenceState: Object.freeze(["candidate", "needs_evidence", "supported", "contradicted", "bounded", "blocked"]),
    AdmissionDecision: Object.freeze(["unproposed", "proposed", "accepted", "revised", "rejected", "deferred"]),
    AdmissionMutation: Object.freeze(["not_requested", "staged", "applied", "rolled_back"]),
    AdmissionValidation: Object.freeze(["unvalidated", "pending", "passed", "failed"]),
    AuthorityRole: Object.freeze(["none", "informative", "interpretive", "normative"]),
    Sensitivity: Object.freeze(["public_safe", "internal", "private", "local_only"]),
    EvidenceKind: Object.freeze(["fact", "judgment", "inference", "preference", "agent_guess"]),
  });

  const durableStateBoundary = Object.freeze({
    localStorage: Object.freeze([
      "language",
      "theme",
      "selected-tab",
      "draft-text",
      "temporary-view-filter",
      "model-selection",
      "reasoning-preference",
      "custom-model-list",
    ]),
    activeContext: Object.freeze(["inbox-action", "archive-record", "withdrawn-item", "confirmation-decision"]),
    canonicalMarkdown: Object.freeze(["confirmed-relationship", "confirmed-material-judgment", "stable-memory"]),
  });

  const viewContracts = Object.freeze({
    assets: Object.freeze(["Atom", "Edge", "State"]),
    inbox: Object.freeze(["Action", "State"]),
    preview: Object.freeze(["Atom", "Evidence"]),
    radar: Object.freeze(["Edge", "Rule", "Action"]),
    today: Object.freeze(["Action", "Atom", "Evidence"]),
  });

  const cardMaturityAxes = Object.freeze({
    group: "G",
    paper: "M",
    person: "R",
    project: "I",
    source: "M",
    talk: "M",
  });

  const cardMaturitySequences = Object.freeze({
    G: Object.freeze(["G0", "G1", "G2", "R_research_mainline"]),
    I: Object.freeze(["I0", "I1", "I2", "I3"]),
    M: Object.freeze(["M1", "M2", "M3"]),
    R: Object.freeze(["R0", "R1", "R2", "R3"]),
  });

  function cleanCardMaturityValue(value = "") {
    return String(value || "").trim();
  }

  function normalizedCardMaturityLevel(axis = "M", value = "") {
    const raw = cleanCardMaturityValue(value);
    if (!raw) return "";
    if (axis === "M") {
      const match = raw.match(/^M([1-3])(?:_|\b)/i);
      return match ? `M${match[1]}` : "";
    }
    if (axis === "I") {
      const match = raw.match(/^I([0-3])(?:_|\b)/i);
      return match ? `I${match[1]}` : "";
    }
    if (axis === "R") {
      const match = raw.match(/^R([0-3])(?:_|\b)/i);
      return match ? `R${match[1]}` : "";
    }
    if (/^R_research_mainline$/i.test(raw)) return "R_research_mainline";
    const match = raw.match(/^G([0-2])(?:_|\b)/i);
    return match ? `G${match[1]}` : "";
  }

  function cardMaturityProfile(type = "asset", item = {}) {
    const normalizedType = cleanCardMaturityValue(type || item.type || "asset").toLowerCase();
    const primary = item.primary_maturity && typeof item.primary_maturity === "object"
      ? item.primary_maturity : {};
    const primaryAxis = cleanCardMaturityValue(primary.axis).toUpperCase();
    const axis = ["M", "I", "R", "G"].includes(primaryAxis)
      ? primaryAxis : (cardMaturityAxes[normalizedType] || "M");
    const explicitValues = {
      G: [primary.level, item.card_maturity_level, item.group_level],
      I: [primary.level, item.card_maturity_level, item.project_maturity, item.project_maturity_level, item.incubation_maturity],
      M: [primary.level, item.card_maturity_level, item.material_maturity?.level, item.analysis_state, item.maturity_level],
      R: [primary.level, item.card_maturity_level, item.relationship_maturity, item.relationship_maturity_level],
    }[axis] || [];
    const explicitRaw = explicitValues.map(cleanCardMaturityValue).find(Boolean) || "";
    const legacyRaw = axis === "R"
      ? cleanCardMaturityValue(item.person_maturity_level || item.person_maturity?.level)
      : "";
    const raw = explicitRaw || legacyRaw;
    const level = normalizedCardMaturityLevel(axis, raw);
    const sequence = cardMaturitySequences[axis] || [];
    const index = sequence.indexOf(level);
    const primaryState = cleanCardMaturityValue(primary.state);
    const source = primary.level
      ? cleanCardMaturityValue(primary.source) || "card_state_projection"
      : explicitRaw
      ? (axis === "M" && !item.card_maturity_level ? "material_projection" : "explicit")
      : legacyRaw ? "legacy_person_maturity" : "missing";
    const needsConfirmation = Boolean(item.needs_confirmation)
      || source === "legacy_person_maturity"
      || ["candidate", "candidate_legacy_heuristic", "uncovered"].includes(primaryState)
      || !level;
    const reviewNeeded = needsConfirmation || ["stale", "review_due", "unverified"].includes(String(item.freshness || ""));
    const targetLevel = !level ? (sequence[0] || "") : index >= 0 && index < sequence.length - 1 ? sequence[index + 1] : "";
    const action = needsConfirmation
      ? "verify"
      : targetLevel
        ? "enhance"
        : reviewNeeded ? "reverify" : "use";
    const axisReason = {
      G: item.group_maturity_reason,
      I: item.project_maturity_reason || item.incubation_maturity_reason,
      M: item.maturity_reason_cn || item.material_maturity?.reason_cn,
      R: item.person_maturity?.reason_cn || item.person_maturity_reason,
    }[axis];
    const reason = cleanCardMaturityValue(primary.reason || item.card_maturity_reason || axisReason);
    return Object.freeze({
      action,
      axis,
      confirmed: Boolean(level) && !needsConfirmation,
      display_level: level === "R_research_mainline" ? "R" : (level || `${axis}?`),
      level,
      reason,
      review_needed: reviewNeeded,
      source,
      target_level: targetLevel,
    });
  }

  global.ResearchOSContracts = Object.freeze({
    cardMaturityAxes,
    cardMaturityProfile,
    cardMaturitySequences,
    durableStateBoundary,
    primitiveTypes,
    stateAxes,
    viewContracts,
  });
})(window);
