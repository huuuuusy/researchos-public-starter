/* ResearchOS maintenance header.
 * 中文：Library / Prepare 的任务上下文投影 owner；只从当前 Work Session 派生纳入项、默认排除规则和外发边界。
 * English: Task-context projection owner for Library / Prepare; derives included items, default exclusions, and egress boundary only from the current Work Session.
 */

(function attachResearchOSContextPackProjection(global) {
  const SCHEMA_ID = "researchos-context-pack-projection-v1";

  function clean(value = "") {
    return String(value ?? "").trim();
  }

  function displayText(value = "", maximum = 180) {
    const text = clean(value).replace(/\s+/g, " ");
    const characters = [...text];
    return characters.length > maximum ? `${characters.slice(0, maximum - 1).join("")}…` : text;
  }

  function activeSession(session = null) {
    if (!session || typeof session !== "object") return false;
    return session.sessionLifecycle !== "ended" && session.status !== "completed";
  }

  function sourceBasename(path = "") {
    return clean(path).split(/[\\/]/).filter(Boolean).pop() || "";
  }

  function previewResolution(path = "", documents = [], sourceId = "") {
    const requestedPath = clean(path);
    if (!requestedPath) return Object.freeze({ document: null, preview_path: "", state: "unavailable" });
    const available = (Array.isArray(documents) ? documents : [])
      .filter((document) => document && clean(document.path));
    const exact = available.find((document) => clean(document.path) === requestedPath);
    if (exact) return Object.freeze({ document: exact, preview_path: requestedPath, state: "exact" });
    // A registered exact identity can establish relocation; a filename cannot.
    const identified = clean(sourceId)
      ? available.filter((document) => clean(document.id) === clean(sourceId)) : [];
    if (identified.length === 1) {
      return Object.freeze({ document: identified[0], preview_path: clean(identified[0].path), state: "relocated" });
    }
    const basename = sourceBasename(requestedPath);
    const matches = basename
      ? available.filter((document) => sourceBasename(document.path) === basename)
      : [];
    if (matches.length === 1) {
      return Object.freeze({ document: null, preview_path: "", candidate_preview_path: clean(matches[0].path), state: "needs_confirmation" });
    }
    return Object.freeze({
      document: null,
      preview_path: "",
      state: matches.length > 1 ? "ambiguous" : "unavailable",
    });
  }

  function includedSources(session = {}, options = {}) {
    const sources = [];
    const seen = new Set();
    const add = (candidate = {}) => {
      const requestedPath = clean(candidate.path);
      const resolution = previewResolution(requestedPath, options.previewDocuments, candidate.id);
      const path = requestedPath;
      const candidateTitle = clean(candidate.title);
      const title = clean(
        (!candidateTitle || candidateTitle === requestedPath) && resolution.document?.title
          ? resolution.document.title
          : candidateTitle || path || candidate.id,
      );
      const identity = requestedPath || clean(candidate.id) || title;
      if (!identity || !title || seen.has(identity)) return;
      seen.add(identity);
      sources.push(Object.freeze({
        id: clean(candidate.id || identity),
        path,
        preview_path: resolution.preview_path,
        preview_state: resolution.state,
        candidate_preview_path: resolution.candidate_preview_path || "",
        identity_state: clean(candidate.identity_state),
        identity_scope: clean(candidate.identity_scope),
        requested_path: requestedPath,
        title,
        type: clean(candidate.type || "source"),
        type_label: clean(candidate.typeLabel || candidate.type_label || candidate.type || "source"),
      }));
    };
    (Array.isArray(session.cards) ? session.cards : []).forEach(add);
    (Array.isArray(session.sourceHints) ? session.sourceHints : []).forEach((path) => add({ path, title: path, type: "source" }));
    return Object.freeze(sources.slice(0, 8));
  }

  function sourceBoundary(source = {}, language = "zh-CN") {
    const zh = language !== "en";
    const notes = [];
    if (source.identity_state === "unresolved_reference") {
      notes.push(zh ? "身份待核对：仅为局部引用，不代表已确认的全局对象" : "Identity unresolved: a local reference, not a confirmed global object");
      if (source.identity_scope) notes.push(`${zh ? "引用范围" : "Reference scope"}: ${source.identity_scope}`);
    }
    if (source.preview_state === "needs_confirmation") {
      notes.push(`${zh ? "同名候选，尚未证明是原来源" : "Same-name candidate; not verified as the original source"}: ${source.candidate_preview_path}`);
    } else if (source.preview_state === "relocated") {
      notes.push(`${zh ? "登记 ID 一致的预览位置；原请求路径保留" : "Preview location with matching registered ID; requested path retained"}: ${source.preview_path}`);
    } else if (source.preview_state === "ambiguous") {
      notes.push(zh ? "来源位置有歧义，未选择替代文件" : "Source location ambiguous; no replacement selected");
    } else if (source.preview_state === "unavailable") {
      notes.push(zh ? "未定位可预览来源" : "Preview source unavailable");
    }
    return notes.join(" · ");
  }

  function currentStep(session = {}) {
    return displayText(
      session.portfolioBinding?.nextStep
        || session.title
        || session.goal
        || session.intent,
    );
  }

  function project(session = null, options = {}) {
    const active = activeSession(session);
    const identity = active && global.ResearchOSWorkSessionState?.taskIdentityProjection
      ? global.ResearchOSWorkSessionState.taskIdentityProjection(session)
      : Object.freeze({
          identity_kind: "none", item_id: "", logical_task_id: "", next_step_signature: "",
          provider_id: "", session_id: active ? clean(session?.id) : "",
        });
    const runtimeMode = clean(options.runtimeMode || "private");
    const publicStarter = options.publicStarter === true || runtimeMode === "public_starter";
    return Object.freeze({
      active,
      boundary: active ? clean(session.evidenceBoundary) : "",
      egress: Object.freeze({
        state: publicStarter ? "copy_only_user_controlled" : "not_granted_by_library",
      }),
      excluded: Object.freeze(active ? [Object.freeze({
        reason: "explicit_selection_required",
        scope: "unselected_library_items",
      })] : []),
      included: active ? includedSources(session, options) : Object.freeze([]),
      schema_id: SCHEMA_ID,
      status: active ? "ready" : "empty",
      task: Object.freeze({
        goal: active ? currentStep(session) : "",
        id: identity.logical_task_id,
        identity_kind: identity.identity_kind,
        item_id: identity.item_id,
        logical_task_id: identity.logical_task_id,
        next_step_signature: identity.next_step_signature,
        provider_id: identity.provider_id,
        session_id: identity.session_id,
        title: active ? displayText(session.portfolioBinding?.title || session.title || session.goal || session.intent, 120) : "",
      }),
      version: "1",
    });
  }

  global.ResearchOSContextPackProjection = Object.freeze({
    SCHEMA_ID,
    currentStep,
    includedSources,
    previewResolution,
    sourceBoundary,
    project,
  });
})(window);
