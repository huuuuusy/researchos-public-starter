/* ResearchOS maintenance header.
 * 中文：Dashboard HandoffReceipt projection 的唯一前端模型 owner；只校验服务端 allowlist，不重算证据、身份或 authority。
 * English: Sole browser model owner for HandoffReceipt projections; validates the server allowlist without re-deriving evidence, identity, or authority.
 */

(function attachResearchOSHandoffReceiptProjection(global) {
  const TOP_KEYS = [
    "schema_id", "source_schema_id", "handoff_id", "task_id", "runtime_scope", "content_state",
    "source_revision", "last_judgment", "open_boundary", "next_safe_action", "forbidden_actions",
    "target_client", "limitations",
  ];
  const STATES = Object.freeze({
    source_revision: ["unknown", "verified"],
    last_judgment: ["unknown", "candidate", "human_recorded"],
    open_boundary: ["unknown", "recorded"],
    next_safe_action: ["unknown", "recommended"],
    forbidden_actions: ["unknown", "recorded"],
  });
  const LIMITATIONS = ["projection_not_authority", "target_not_delivery", "no_transcript"];
  const SCOPES = ["private", "public_starter", "personal_vault"];

  function exactKeys(value, keys) {
    return Boolean(value && typeof value === "object" && !Array.isArray(value)
      && Object.keys(value).sort().join("|") === [...keys].sort().join("|"));
  }

  function boundedText(value, maximum, nonempty = false) {
    if (typeof value !== "string" || value.includes("\0") || [...value].length > maximum) return null;
    if (nonempty && !value.trim()) return null;
    return value;
  }

  function statement(value, name, contentState) {
    if (!exactKeys(value, ["state", "text"])) return null;
    const state = boundedText(value.state, 40, true);
    const text = boundedText(value.text, 2000);
    if (!state || text === null || !STATES[name].includes(state)) return null;
    if ((state === "unknown" || contentState === "suppressed") && text) return null;
    if (state !== "unknown" && contentState === "included" && !text.trim()) return null;
    return Object.freeze({ state, text });
  }

  function normalize(value) {
    if (!exactKeys(value, TOP_KEYS)) return null;
    if (value.schema_id !== "researchos-handoff-projection-v1"
      || value.source_schema_id !== "researchos-handoff-receipt-v1"
      || !/^handoff:[0-9a-f]{64}$/.test(value.handoff_id)
      || !/^task:[0-9a-f]{64}$/.test(value.task_id)
      || !SCOPES.includes(value.runtime_scope)
      || !["included", "suppressed"].includes(value.content_state)) return null;
    const source = value.source_revision;
    if (!exactKeys(source, ["state", "source_id", "value_digest"])
      || !STATES.source_revision.includes(source.state)) return null;
    if (source.state === "unknown" && (source.source_id || source.value_digest)) return null;
    if (source.state === "verified"
      && (!/^src:[0-9a-f]{64}$/.test(source.source_id) || !/^[0-9a-f]{64}$/.test(source.value_digest))) return null;
    const lastJudgment = statement(value.last_judgment, "last_judgment", value.content_state);
    const openBoundary = statement(value.open_boundary, "open_boundary", value.content_state);
    const nextSafeAction = statement(value.next_safe_action, "next_safe_action", value.content_state);
    const forbidden = value.forbidden_actions;
    if (!lastJudgment || !openBoundary || !nextSafeAction
      || !exactKeys(forbidden, ["state", "items"])
      || !STATES.forbidden_actions.includes(forbidden.state)
      || !Array.isArray(forbidden.items) || forbidden.items.length > 8
      || forbidden.items.some((item) => boundedText(item, 500, true) === null)
      || (forbidden.state === "unknown" || value.content_state === "suppressed") && forbidden.items.length) return null;
    const target = value.target_client;
    if (!exactKeys(target, ["kind", "surface", "binding_state"])
      || boundedText(target.kind, 120, true) === null
      || boundedText(target.surface, 120, true) === null
      || target.binding_state !== "requested") return null;
    if (!Array.isArray(value.limitations)
      || value.limitations.join("|") !== LIMITATIONS.join("|")) return null;
    return Object.freeze({
      schemaId: value.schema_id, sourceSchemaId: value.source_schema_id,
      handoffId: value.handoff_id, taskId: value.task_id, runtimeScope: value.runtime_scope,
      contentState: value.content_state, sourceRevision: Object.freeze({ ...source }),
      lastJudgment, openBoundary, nextSafeAction,
      forbiddenActions: Object.freeze({ state: forbidden.state, items: Object.freeze([...forbidden.items]) }),
      targetClient: Object.freeze({ ...target }), limitations: Object.freeze([...value.limitations]),
    });
  }

  global.ResearchOSHandoffReceiptProjection = Object.freeze({ normalize });
})(window);
