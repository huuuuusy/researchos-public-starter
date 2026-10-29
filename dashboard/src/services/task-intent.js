/* ResearchOS maintenance header.
 * 中文：TaskIntent v1 的唯一浏览器 owner；只表达不可信任务请求，不授予权限、运行范围或长期 authority。
 * English: Sole browser owner for TaskIntent v1; represents untrusted task requests without granting permission, runtime scope, or durable authority.
 */

(function attachResearchOSTaskIntent(global) {
  const SCHEMA_ID = "researchos-task-intent-v1";
  const RESULT_MODES = Object.freeze(["answer", "artifact", "writeback"]);
  const REASONING_EFFORTS = Object.freeze(["auto", "low", "medium", "high", "xhigh", "max", "ultra"]);
  const TASK_COMPLEXITIES = Object.freeze(["auto", "economy", "standard", "deep"]);
  const SOURCE_KINDS = Object.freeze(["artifact", "card", "object", "session_source", "url"]);
  const MAX_SOURCE_REFS = 20;
  const MAX_INSTRUCTION_LENGTH = 65536;

  function contractError(code, field) {
    const error = new Error(code);
    error.code = code;
    error.field = field;
    return error;
  }

  function boundedText(value, maxLength, field, options = {}) {
    const fallback = options.fallback;
    if (value === undefined || value === null) return fallback ?? "";
    let normalized = String(value);
    if (normalized.includes("\u0000")) throw contractError("task_intent_invalid_character", field);
    if (options.normalizeNewlines) normalized = normalized.replace(/\r\n?/g, "\n");
    if ([...normalized].length > maxLength) throw contractError("task_intent_input_too_large", field);
    if (options.nonempty && normalized.trim().length === 0) throw contractError("task_intent_invalid_value", field);
    return normalized;
  }

  function requestedValue(value, fallback, field, maxLength = 240) {
    return boundedText(value, maxLength, field, { fallback, nonempty: true });
  }

  function sourceRef(value = {}, index = 0) {
    const record = typeof value === "string" ? { ref: value } : value && typeof value === "object" ? value : {};
    const refValue = record.ref ?? record.path ?? record.url ?? record.id;
    const ref = boundedText(refValue, 2048, `source_refs[${index}].ref`, { nonempty: true });
    const inferredKind = /^https?:\/\//i.test(ref) ? "url" : "session_source";
    return {
      kind: requestedValue(record.kind ?? record.type, inferredKind, `source_refs[${index}].kind`, 80),
      ref,
      label: boundedText(record.label ?? record.title, 240, `source_refs[${index}].label`, { fallback: "" }),
    };
  }

  function normalizeSourceRefs(values = []) {
    if (!Array.isArray(values)) throw contractError("task_intent_invalid_value", "source_refs");
    const refs = [];
    const seen = new Set();
    values.forEach((value, index) => {
      const normalized = sourceRef(value, index);
      const key = `${normalized.kind}\u0000${normalized.ref}\u0000${normalized.label}`;
      if (seen.has(key)) return;
      seen.add(key);
      refs.push(normalized);
    });
    if (refs.length > MAX_SOURCE_REFS) throw contractError("task_intent_input_too_large", "source_refs");
    return refs;
  }

  function normalize(input = {}) {
    const record = input && typeof input === "object" ? input : {};
    const client = record.client && typeof record.client === "object" ? record.client : {};
    const result = record.requested_result && typeof record.requested_result === "object" ? record.requested_result : {};
    const profile = record.requested_profile && typeof record.requested_profile === "object" ? record.requested_profile : {};
    const hints = record.client_hints && typeof record.client_hints === "object" ? record.client_hints : {};
    return {
      schema_id: SCHEMA_ID,
      input_trust: "untrusted",
      goal: boundedText(record.goal, 4000, "goal", { fallback: "", normalizeNewlines: true }),
      instruction: boundedText(record.instruction, MAX_INSTRUCTION_LENGTH, "instruction", { fallback: "", normalizeNewlines: true }),
      client_request_id: boundedText(record.client_request_id, 160, "client_request_id", { fallback: "" }),
      client: {
        kind: requestedValue(client.kind, "unknown", "client.kind", 120),
        surface: requestedValue(client.surface, "unknown", "client.surface", 120),
        task_ref: boundedText(client.task_ref, 240, "client.task_ref", { fallback: "" }),
      },
      requested_result: {
        mode: requestedValue(result.mode, "answer", "requested_result.mode", 80),
      },
      requested_profile: {
        provider: requestedValue(profile.provider, "auto", "requested_profile.provider", 120),
        model: requestedValue(profile.model, "auto", "requested_profile.model", 240),
        reasoning_effort: requestedValue(profile.reasoning_effort, "auto", "requested_profile.reasoning_effort", 80),
        task_complexity: requestedValue(profile.task_complexity, "auto", "requested_profile.task_complexity", 80),
      },
      client_hints: {
        recommended_reasoning_effort: requestedValue(hints.recommended_reasoning_effort, "auto", "client_hints.recommended_reasoning_effort", 80),
        recommended_task_complexity: requestedValue(hints.recommended_task_complexity, "standard", "client_hints.recommended_task_complexity", 80),
      },
      source_refs: normalizeSourceRefs(record.source_refs),
    };
  }

  function sessionSourceRefs(session = {}) {
    const candidateRefs = Array.isArray(session.candidate?.source_refs) ? session.candidate.source_refs : [];
    const sourceHints = (Array.isArray(session.sourceHints) ? session.sourceHints : []).map((ref) => ({
      kind: "session_source",
      ref,
    }));
    const cards = (Array.isArray(session.cards) ? session.cards : []).map((card) => ({
      kind: "card",
      ref: card?.path || card?.id || card?.title,
      label: card?.title || card?.typeLabel || card?.type,
    }));
    return [...candidateRefs, ...sourceHints, ...cards];
  }

  function fromWorkSession(session = {}, options = {}) {
    return normalize({
      goal: session.goal || session.title || session.intent,
      instruction: session.intent,
      client_request_id: options.clientRequestId,
      client: { kind: "dashboard", surface: "work_session", task_ref: session.id },
      requested_result: { mode: options.responseMode },
      requested_profile: {
        provider: options.provider,
        model: options.model,
        reasoning_effort: options.reasoningEffort,
        task_complexity: options.taskComplexity,
      },
      client_hints: {
        recommended_reasoning_effort: options.recommendedReasoningEffort,
        recommended_task_complexity: options.recommendedTaskComplexity,
      },
      source_refs: sessionSourceRefs(session),
    });
  }

  global.ResearchOSTaskIntent = Object.freeze({
    MAX_INSTRUCTION_LENGTH,
    MAX_SOURCE_REFS,
    REASONING_EFFORTS,
    RESULT_MODES,
    SCHEMA_ID,
    SOURCE_KINDS,
    TASK_COMPLEXITIES,
    fromWorkSession,
    normalize,
  });
})(window);
