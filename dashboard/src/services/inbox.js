/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「inbox」；承接可复用逻辑，避免 app.js 重新变成大杂烩。
 * English: Frontend service for inbox in the ResearchOS dashboard; owns reusable logic so app.js stays from becoming a catch-all again.
 */

(function attachResearchOSInboxService(global) {
  const ACTIVE_VIEWS = new Set(["active", "archived", "all"]);
  const INACTIVE_EXACT_STATUSES = new Set(["withdrawn", "done", "archived"]);
  const INACTIVE_STATUS_PARTS = ["skipped", "superseded", "merged"];
  const ACTIVE_STATUS_PARTS = ["pending", "in_progress", "queued"];
  const ADMISSION_STATE_SCHEMA_ID = "researchos-admission-state-v1";
  const ADMISSION_VOCABULARIES = Object.freeze({
    decision_state: new Set(["unproposed", "proposed", "accepted", "revised", "rejected", "deferred"]),
    mutation_state: new Set(["not_requested", "staged", "applied", "rolled_back"]),
    validation_state: new Set(["unvalidated", "pending", "passed", "failed"]),
    authority_role: new Set(["none", "informative", "interpretive", "normative"]),
  });

  function defaultText(key) {
    return key;
  }

  function inboxStatusIsActive(status = "", fallbackActive = true) {
    const value = String(status || "").trim().toLowerCase();
    if (!value) return fallbackActive;
    if (
      INACTIVE_EXACT_STATUSES.has(value) ||
      value.startsWith("processed_") ||
      value.startsWith("done") ||
      INACTIVE_STATUS_PARTS.some((part) => value.includes(part))
    ) {
      return false;
    }
    if (ACTIVE_STATUS_PARTS.some((part) => value.includes(part))) return true;
    return fallbackActive;
  }

  function filterActiveInboxItems(items = [], fallbackActive = true) {
    return (Array.isArray(items) ? items : []).filter(
      (item) => item && typeof item === "object" && inboxStatusIsActive(item.status, fallbackActive)
    );
  }

  function unifiedInboxStatusLabel(status = "", text = defaultText) {
    const value = String(status || "").trim().toLowerCase();
    if (!value) return "";
    if (value === "today" || value === "local") return text("unifiedInboxStatusLocal");
    if (value === "synced") return text("unifiedInboxStatusSynced");
    if (value === "source_file") return text("unifiedInboxStatusSource");
    if (value === "pending_codex_review") return text("unifiedInboxStatusCodexReview");
    if (value === "pending_codex_migration_review") return text("unifiedInboxStatusMigrationReview");
    if (value === "queued") return text("unifiedInboxStatusQueued");
    if (value === "in_progress") return text("unifiedInboxStatusInProgress");
    if (value === "needs_edit") return text("unifiedInboxStatusNeedsEdit");
    if (value === "needs_evidence") return text("unifiedInboxStatusNeedsEvidence");
    if (value === "processed") return text("unifiedInboxStatusProcessed");
    if (value === "done" || value.startsWith("done") || value.startsWith("processed_")) return text("unifiedInboxStatusDone");
    if (value === "withdrawn") return text("unifiedInboxStatusWithdrawn");
    if (value === "archived") return text("unifiedInboxArchivedStatus");
    return status;
  }

  function compactInboxText(value = "", limit = 140) {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    if (!text) return "";
    return text.length > limit ? `${text.slice(0, Math.max(0, limit - 1)).trim()}…` : text;
  }

  function inboxLooksLikeInternalId(value = "") {
    const text = String(value || "").trim();
    if (!text) return true;
    return (
      /^(status|public|stage|project-evidence|paper|asset|task|confirmation):/i.test(text) ||
      /^[a-z0-9_-]+:[a-z0-9_./-]+$/i.test(text) ||
      /^[a-z0-9_./-]{18,}$/i.test(text)
    );
  }

  function inboxBasename(path = "") {
    const value = String(path || "").trim();
    if (!value) return "";
    const filename = value.split("/").filter(Boolean).pop() || value;
    return filename.replace(/\.(md|json|jsonl|txt)$/i, "").replaceAll("_", " ").replaceAll("-", " ").trim();
  }

  function inboxTitleFromDecisionId(decisionId = "") {
    const value = String(decisionId || "").trim();
    const [, slug = ""] = value.match(/^[^:]+:([^:]+)(?::[^:]+)?$/) || [];
    return slug.replaceAll("-", " ").replaceAll("_", " ").trim();
  }

  function firstReadableInboxText(candidates = []) {
    return candidates
      .map((value) => String(value ?? "").trim())
      .find((value) => value && !inboxLooksLikeInternalId(value)) || "";
  }

  function confirmationTypeLabel(decisionId = "", text = defaultText) {
    const value = String(decisionId || "").trim().toLowerCase();
    if (value.startsWith("status:")) return text("confirmTypeStatusBoundary");
    if (value.startsWith("stage:")) return text("unifiedInboxDecisionStage");
    if (value.startsWith("public:")) return text("confirmTypePublicBoundary");
    if (value.startsWith("project-evidence:")) return text("confirmTypeProjectEvidence");
    return text("confirmTypeGeneral");
  }

  function unifiedInboxActionLabel(action = "", text = defaultText) {
    const value = String(action || "").trim();
    const labels = {
      check_evidence_boundary: text("unifiedInboxActionCheckEvidence"),
      inspect_selected_asset: text("unifiedInboxActionInspectAsset"),
      interpret_or_correct_material: text("unifiedInboxActionInterpretMaterial"),
      record_edit_or_reuse_note: text("unifiedInboxActionRecordReuse"),
      upgrade_to_M2_close_read: text("unifiedInboxActionUpgradeM2"),
      upgrade_to_M3_cross_project_deepening: text("unifiedInboxActionUpgradeM3"),
    };
    return labels[value] || text("unifiedInboxActionReview");
  }

  function inboxEntryDisplayTitle(entry = {}, text = defaultText) {
    const raw = entry.raw || {};
    const entryTitle = String(entry.title || "").trim();
    const genericTitle = entryTitle === String(entry.typeLabel || "").trim() || entryTitle === text("unifiedInboxConfirmation");
    const readable = firstReadableInboxText([
      genericTitle ? "" : entry.title,
      raw.object_title,
      genericTitle ? "" : raw.title,
      raw.target_title,
      raw.paper_title,
      raw.source_title,
      raw.type_label,
      raw.topic,
      raw.target_path ? inboxBasename(raw.target_path) : "",
      raw.path ? inboxBasename(raw.path) : "",
      entry.path ? inboxBasename(entry.path) : "",
      raw.decision_id ? inboxTitleFromDecisionId(raw.decision_id) : "",
    ]);
    if (readable) return compactInboxText(readable, raw.source === "work-session" ? 240 : 92);
    return entry.typeLabel || text("unifiedInboxUntitledTask");
  }

  function inboxEntryDisplayBody(entry = {}, text = defaultText) {
    const raw = entry.raw || {};
    if (entry.type === "task") {
      const actionLabel = unifiedInboxActionLabel(raw.action || "", text);
      return compactInboxText([actionLabel, raw.note].filter(Boolean).join(" · "), 150);
    }
    if (entry.type === "confirmation") {
      return compactInboxText([
        text("unifiedInboxUserDecision"),
        raw.choiceLabel || entry.body,
        raw.question,
        raw.suggestion,
      ].filter(Boolean).join(" · "), 150);
    }
    return compactInboxText(entry.body || raw.note || "", 150);
  }

  function inboxEntryDisplayMeta(entry = {}, text = defaultText) {
    const raw = entry.raw || {};
    const parts = [
      entry.type === "confirmation" ? confirmationTypeLabel(raw.decision_id || entry.actionId, text) : "",
      raw.material_type || raw.type || "",
      raw.current_state && raw.target_state ? `${raw.current_state} -> ${raw.target_state}` : "",
      raw.target_hint || raw.intent || "",
    ].filter(Boolean);
    if (!parts.length && (entry.path || entry.sourcePath)) {
      parts.push(text("unifiedInboxTechnicalAvailable"));
    }
    return compactInboxText(parts.join(" · "), 120);
  }

  function normalizeClearedInboxServerState(serverState = null) {
    return serverState && typeof serverState === "object" ? serverState : null;
  }

  function resolveClearedInboxItems({
    fallbackActive = true,
    localItems = [],
    serverKey = "",
    serverState = null,
  } = {}) {
    const safeState = normalizeClearedInboxServerState(serverState);
    if (safeState) {
      if (Array.isArray(safeState[serverKey])) {
        return { items: safeState[serverKey], shouldSave: true, source: "server" };
      }
      return { items: [], shouldSave: false, source: "server_missing" };
    }
    return { items: filterActiveInboxItems(localItems, fallbackActive), shouldSave: true, source: "local_active" };
  }

  function resolveClearedInboxObject({
    fallbackRecords = {},
    serverKey = "",
    serverState = null,
  } = {}) {
    const safeState = normalizeClearedInboxServerState(serverState);
    const serverRecords = safeState?.[serverKey];
    if (serverRecords && typeof serverRecords === "object" && !Array.isArray(serverRecords)) {
      return { records: serverRecords, shouldSave: true, source: "server" };
    }
    return { records: fallbackRecords, shouldSave: true, source: safeState ? "server_missing" : "local_active" };
  }

  async function clearProcessedInbox({ scope = "processed" } = {}, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (typeof fetcher !== "function") {
      return { ok: false, serverState: null };
    }
    try {
      const response = await fetcher("/clear-inbox", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scope }),
        cache: "no-store",
      });
      if (!response?.ok) return { ok: false, serverState: null };
      const payload = await response.json();
      return {
        ok: true,
        serverState: normalizeClearedInboxServerState(payload?.state),
      };
    } catch {
      return { ok: false, serverState: null };
    }
  }

  function normalizeUnifiedInboxView(view = "") {
    const value = String(view || "").trim();
    return ACTIVE_VIEWS.has(value) ? value : "active";
  }

  function unifiedInboxEntryArchiveKey(type = "", id = "") {
    const safeType = String(type || "").trim();
    const safeId = String(id || "").trim();
    return safeType && safeId ? `${safeType}:${safeId}` : "";
  }

  function loadUnifiedInboxArchive(storageKey = "researchos-unified-inbox-archive", storage = global.localStorage) {
    try {
      const parsed = JSON.parse(storage.getItem(storageKey) || "{}");
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
    } catch {
      return {};
    }
  }

  function saveUnifiedInboxArchive(records = {}, storageKey = "researchos-unified-inbox-archive", storage = global.localStorage) {
    const safeRecords = Object.fromEntries(
      Object.entries(records || {})
        .filter(([key, record]) => key && record && typeof record === "object")
        .slice(-240)
    );
    storage.setItem(storageKey, JSON.stringify(safeRecords));
  }

  function archiveUnifiedInboxEntry({ storageKey = "researchos-unified-inbox-archive", type = "", id = "", entry = {} } = {}) {
    const key = unifiedInboxEntryArchiveKey(type, id);
    if (!key) return false;
    const archive = loadUnifiedInboxArchive(storageKey);
    archive[key] = {
      ...(archive[key] || {}),
      key,
      type,
      id,
      title: entry.title || archive[key]?.title || "",
      body: entry.body || archive[key]?.body || "",
      status_before_archive: entry.status || archive[key]?.status_before_archive || "",
      source_path: entry.sourcePath || archive[key]?.source_path || "",
      archivedAt: new Date().toISOString(),
    };
    saveUnifiedInboxArchive(archive, storageKey);
    return true;
  }

  function restoreUnifiedInboxEntry({ storageKey = "researchos-unified-inbox-archive", type = "", id = "" } = {}) {
    const key = unifiedInboxEntryArchiveKey(type, id);
    if (!key) return false;
    const archive = loadUnifiedInboxArchive(storageKey);
    delete archive[key];
    saveUnifiedInboxArchive(archive, storageKey);
    return true;
  }

  function findUnifiedInboxEntry(entries = [], type = "", id = "") {
    return (Array.isArray(entries) ? entries : []).find(
      (entry) => entry && entry.type === type && entry.actionId === id
    ) || null;
  }

  function completedRunCanArchiveEntry(run = {}, entry = {}, timeValue = (value) => Date.parse(value || "") || 0) {
    const completedAt = timeValue(run.finished_at || run.updated_at || run.created_at || "");
    const entryAddedAt = timeValue(entry.updatedAt || entry.raw?.addedAt || "");
    if (!completedAt || !entryAddedAt) return true;
    return entryAddedAt <= completedAt;
  }

  function archiveUnifiedInboxEntryFromInbox({
    inbox = {},
    storageKey = "researchos-unified-inbox-archive",
    type = "",
    id = "",
  } = {}) {
    return archiveUnifiedInboxEntry({
      entry: findUnifiedInboxEntry(inbox.entries || [], type, id) || {},
      id,
      storageKey,
      type,
    });
  }

  async function withdrawUnifiedInboxEntry({ type = "", id = "", restore = () => false, handlers = {} } = {}) {
    if (!type || !id) return { handled: false, restored: false, type, id };
    const restored = restore(type, id);
    const handler = handlers[type];
    if (typeof handler !== "function") return { handled: false, restored, type, id };
    const result = await handler(id);
    return { handled: true, restored, result, type, id };
  }

  function sourceAgentForInboxEntry(entry = {}) {
    const raw = entry.raw || {};
    const rawSource = String(raw.source || raw.source_agent || "").trim();
    if (rawSource === "asset-overview-card") return "asset_cartographer";
    if (entry.type === "confirmation" || entry.type === "preview_feedback") return "evidence_auditor";
    if (entry.type === "paper_field_update") return "evidence_auditor";
    if (raw.action === "generate_daily_research_recommendation") return "project_steward";
    if (rawSource === "user" || rawSource === "manual") return "user";
    return "orchestrator";
  }

  function targetAgentForInboxEntry(entry = {}) {
    const raw = entry.raw || {};
    const action = String(raw.action || "").trim();
    if (entry.type === "confirmation" || action === "check_evidence_boundary") return "evidence_auditor";
    if (action === "inspect_selected_asset") return "asset_cartographer";
    if (entry.type === "paper_field_update" || entry.type === "preview_feedback") return "writing_agent";
    return "inbox_secretary";
  }

  function objectTypeForInboxEntry(entry = {}) {
    const raw = entry.raw || {};
    const rawType = String(raw.material_type || raw.type || "").trim();
    if (rawType && rawType !== "task") return rawType;
    if (entry.type === "paper_field_update") return "paper";
    if (entry.type === "confirmation") return "boundary";
    if (entry.type === "preview_feedback") return "source";
    if (entry.type === "task") return raw.path ? "source" : "action";
    return entry.type || "action";
  }

  function evidenceStateForInboxEntry(entry = {}) {
    const raw = entry.raw || {};
    const status = String(entry.status || "").trim().toLowerCase();
    const choice = String(raw.choice || "").trim().toLowerCase();
    const action = String(raw.action || "").trim();
    const explicit = String(raw.evidence_state || "").trim().toLowerCase();
    const allowed = new Set(["candidate", "needs_evidence", "supported", "contradicted", "bounded", "blocked"]);
    if (allowed.has(explicit)) return explicit;
    if (explicit === "confirmed") return "supported";
    if (explicit === "local_only") return "candidate";
    if (entry.archived) return "candidate";
    if (choice === "uncertain" || action === "check_evidence_boundary") return "needs_evidence";
    return "candidate";
  }

  function admissionCombinationIsValid(value = {}) {
    const decision = value.decision_state;
    const mutation = value.mutation_state;
    const validation = value.validation_state;
    if (!["accepted", "revised"].includes(decision) && mutation !== "not_requested") return false;
    if (mutation === "not_requested" && validation !== "unvalidated") return false;
    if (mutation === "staged" && !["unvalidated", "pending"].includes(validation)) return false;
    if (mutation === "applied" && !["pending", "passed", "failed"].includes(validation)) return false;
    return mutation !== "rolled_back" || ["unvalidated", "pending", "passed", "failed"].includes(validation);
  }

  function normalizeAdmissionState(value = {}, fallbackDecision = "proposed") {
    const normalized = {
      schema_id: String(value?.schema_id || ADMISSION_STATE_SCHEMA_ID).trim(),
      decision_state: String(value?.decision_state || fallbackDecision).trim().toLowerCase(),
      mutation_state: String(value?.mutation_state || "not_requested").trim().toLowerCase(),
      validation_state: String(value?.validation_state || "unvalidated").trim().toLowerCase(),
      authority_role: String(value?.authority_role || "none").trim().toLowerCase(),
    };
    const valid = normalized.schema_id === ADMISSION_STATE_SCHEMA_ID
      && Object.entries(ADMISSION_VOCABULARIES).every(([axis, values]) => values.has(normalized[axis]))
      && admissionCombinationIsValid(normalized);
    return Object.freeze(valid ? normalized : {
      schema_id: ADMISSION_STATE_SCHEMA_ID,
      decision_state: fallbackDecision,
      mutation_state: "not_requested",
      validation_state: "unvalidated",
      authority_role: "none",
    });
  }

  function admissionStateForInboxEntry(entry = {}, candidate = {}) {
    const raw = entry.raw || {};
    const canonical = candidate.admission_state && typeof candidate.admission_state === "object"
      ? candidate.admission_state
      : raw.admission_state && typeof raw.admission_state === "object" ? raw.admission_state : null;
    if (canonical) return normalizeAdmissionState({ ...canonical, authority_role: "none" });
    const validation = candidate.validation && typeof candidate.validation === "object" ? candidate.validation : {};
    const writeback = candidate.proposed_writeback && typeof candidate.proposed_writeback === "object"
      ? candidate.proposed_writeback
      : {};
    const legacyAuthority = String(
      validation.authority_state || candidate.authority_state || raw.authority_state || "",
    ).trim().toLowerCase();
    const choice = String(raw.choice || "").trim().toLowerCase();
    const mapped = {
      schema_id: ADMISSION_STATE_SCHEMA_ID,
      decision_state: choice === "accept" ? "accepted"
        : choice === "revise" ? "revised"
          : choice === "reject" ? "rejected"
            : choice === "uncertain" ? "deferred" : "proposed",
      mutation_state: "not_requested",
      validation_state: "unvalidated",
      authority_role: "none",
    };
    if (legacyAuthority === "approved") mapped.decision_state = "accepted";
    if (legacyAuthority === "written_back") {
      mapped.decision_state = "accepted";
      mapped.mutation_state = "applied";
      mapped.validation_state = "pending";
    }
    if (legacyAuthority === "validated") {
      mapped.decision_state = "accepted";
      mapped.mutation_state = "applied";
      mapped.validation_state = "passed";
    }
    if (legacyAuthority === "reverted") {
      mapped.decision_state = "accepted";
      mapped.mutation_state = "rolled_back";
    }
    const legacyValidation = String(
      writeback.validation_state || validation.state || raw.validation_state || raw.last_run_status || "",
    ).trim().toLowerCase();
    if (["pending", "passed", "failed"].includes(legacyValidation) && ["applied", "rolled_back"].includes(mapped.mutation_state)) {
      mapped.validation_state = legacyValidation;
    }
    return normalizeAdmissionState(mapped);
  }

  function transitionForInboxEntry(entry = {}) {
    const raw = entry.raw || {};
    return {
      current_state: String(raw.current_state || "").trim(),
      proposed_state: String(raw.proposed_state || raw.target_state || "").trim(),
      decision_rationale: String(raw.decision_rationale || raw.rationale || "").trim(),
      impact_scope: String(raw.impact_scope || "").trim(),
      rollback_ref: String(raw.rollback_ref || "").trim(),
      validation_state: String(raw.validation_state || raw.last_run_status || "unvalidated").trim(),
    };
  }

  function explicitSensitivityValue(value = "") {
    const text = String(value || "").trim().toLowerCase();
    if (!text) return "";
    if (/private_cloud_ok|private cloud/.test(text)) return "internal";
    if (/local[-_ ]?only|private|sensitive|internal[-_ ]?only|no public|do not export/.test(text)) return "private";
    if (/public[_-]?safe|public-facing|可公开|公开使用|稳定公开|public/.test(text)) return "public_safe";
    if (/internal|内部|本地/.test(text)) return "internal";
    return "";
  }

  function sensitivityFromPath(path = "") {
    const value = String(path || "").trim();
    if (!value) return "";
    if (/^(06_active_context|04_people|07_archive|corpus)\//.test(value)) return "private";
    if (/^(00_identity|03_cognition|05_workflows)\//.test(value)) return "internal";
    if (/^(01_knowledge\/papers\/own_papers|01_knowledge\/talks)\//.test(value)) return "internal";
    return "";
  }

  function sensitivityForInboxEntry(entry = {}) {
    const raw = entry.raw || {};
    const explicit = explicitSensitivityValue([
      raw.sensitivity,
      raw.sensitivity_hint,
      raw.public_boundary,
      raw.boundary,
      raw.sensitivity_note,
      raw.evidence_state,
    ].filter(Boolean).join(" "));
    if (explicit) return explicit;
    if (raw.local_only === true || raw.local_only === "true") return "private";
    if (entry.status === "local") return "private";
    const pathSensitivity = sensitivityFromPath(raw.target_path || raw.path || entry.path || entry.sourcePath || "");
    if (pathSensitivity) return pathSensitivity;
    if (entry.type === "confirmation" || entry.type === "preview_feedback" || entry.type === "task") return "internal";
    return "internal";
  }

  function requiredConfirmationForInboxEntry(entry = {}) {
    const raw = entry.raw || {};
    if (entry.archived) return "archive";
    if (entry.type === "confirmation") {
      if (raw.choice === "revise") return "revise";
      if (raw.choice === "uncertain") return "confirm";
      return "handoff_only";
    }
    if (entry.type === "preview_feedback" || entry.type === "paper_field_update") return "revise";
    if (entry.type === "dissolution") return "confirm";
    return "handoff_only";
  }

  function candidateStatusForInboxEntry(entry = {}) {
    if (entry.archived) return "archived";
    const status = String(entry.status || "").trim().toLowerCase();
    if (status === "withdrawn") return "withdrawn";
    if (!inboxStatusIsActive(status, true)) return "processed";
    return "active";
  }

  function normalizeCandidateEnvelope(candidate = {}, entry = {}) {
    const raw = entry.raw || {};
    const candidateType = String(candidate.candidate_type || entry.type || "item").trim() || "item";
    const actionId = String(entry.actionId || raw.id || raw.decision_id || entry.path || entry.title || "").trim();
    const legacyObjectRef = candidate.object_ref && typeof candidate.object_ref === "object" ? candidate.object_ref : {};
    const legacyTransition = candidate.transition && typeof candidate.transition === "object" ? candidate.transition : {};
    const proposedAction = candidate.proposed_action && typeof candidate.proposed_action === "object"
      ? candidate.proposed_action
      : {};
    const proposedWriteback = candidate.proposed_writeback && typeof candidate.proposed_writeback === "object"
      ? candidate.proposed_writeback
      : {};
    const validation = candidate.validation && typeof candidate.validation === "object" ? candidate.validation : {};
    const sourceRefs = Array.isArray(candidate.source_refs)
      ? candidate.source_refs.filter((item) => item && typeof item === "object")
      : [
          entry.path ? { kind: "object", path: entry.path } : null,
          entry.sourcePath ? { kind: "inbox", path: entry.sourcePath } : null,
        ].filter(Boolean);
    const workflowStatus = String(validation.workflow_status || candidate.workflow_status || candidate.status || candidateStatusForInboxEntry(entry)).trim();
    const evidenceState = String(validation.evidence_state || candidate.evidence_state || evidenceStateForInboxEntry(entry)).trim();
    const admissionState = admissionStateForInboxEntry(entry, candidate);
    const saveTarget = String(proposedWriteback.save_target || candidate.save_target || "").trim();
    const summary = compactInboxText(candidate.summary || candidate.claim_or_task || [entry.displayTitle || entry.title, entry.displayBody || entry.body].filter(Boolean).join(" · "), 220);
    const candidateId = String(candidate.candidate_id || candidate.id || `candidate:${candidateType}:${actionId || compactInboxText(summary || "untitled", 80)}`).trim();
    const targetAgent = String(proposedAction.target_agent || candidate.target_agent || "inbox_secretary").trim();
    const objectRef = {
      type: String(proposedWriteback.object_type || legacyObjectRef.type || objectTypeForInboxEntry(entry)).trim(),
      id: String(proposedWriteback.object_id || legacyObjectRef.id || actionId || summary).trim(),
      path: String(proposedWriteback.object_path || legacyObjectRef.path || entry.path || "").trim(),
    };
    const transition = {
      current_state: String(proposedWriteback.current_state || legacyTransition.current_state || "").trim(),
      proposed_state: String(proposedWriteback.proposed_state || legacyTransition.proposed_state || "").trim(),
      decision_rationale: String(proposedWriteback.decision_rationale || legacyTransition.decision_rationale || "").trim(),
      impact_scope: String(proposedWriteback.impact_scope || legacyTransition.impact_scope || "").trim(),
      rollback_ref: String(proposedWriteback.rollback_ref || legacyTransition.rollback_ref || "").trim(),
      validation_state: admissionState.validation_state,
    };
    return {
      ...candidate,
      candidate_id: candidateId,
      plugin_id: String(candidate.plugin_id || "researchos_core").trim(),
      candidate_type: candidateType,
      source_refs: sourceRefs,
      summary,
      proposed_action: {
        id: String(proposedAction.id || "review_candidate").trim(),
        target_agent: targetAgent,
      },
      proposed_writeback: {
        save_target: saveTarget,
        object_type: objectRef.type,
        object_id: objectRef.id,
        object_path: objectRef.path,
        ...transition,
      },
      sensitivity: String(candidate.sensitivity || sensitivityForInboxEntry(entry)).trim(),
      required_confirmation: String(candidate.required_confirmation || requiredConfirmationForInboxEntry(entry)).trim(),
      validation: {
        workflow_status: workflowStatus,
        evidence_state: evidenceState,
      },
      admission_state: admissionState,
      // Compatibility aliases preserve historical runner records while consumers migrate to the v1 envelope.
      id: candidateId,
      target_agent: targetAgent,
      object_ref: objectRef,
      claim_or_task: summary,
      evidence_state: evidenceState,
      save_target: saveTarget,
      workflow_status: workflowStatus,
      status: workflowStatus,
      transition,
    };
  }

  function candidateEnvelopeForEntry(entry = {}) {
    const raw = entry.raw || {};
    const actionId = String(entry.actionId || raw.id || raw.decision_id || raw.path || entry.path || entry.title || "").trim();
    const objectPath = String(entry.path || raw.target_path || raw.path || raw.source_path || "").trim();
    const inferredSaveTarget = entry.type === "task" || raw.source === "work-session"
      ? ""
      : entry.path || entry.sourcePath || "";
    return normalizeCandidateEnvelope({
      candidate_id: `candidate:${entry.type || "item"}:${actionId || compactInboxText(entry.displayTitle || entry.title || "untitled", 80)}`,
      plugin_id: "researchos_core",
      candidate_type: entry.type || "item",
      source_refs: [
        objectPath ? { kind: "object", path: objectPath } : null,
        entry.sourcePath ? { kind: "inbox", path: entry.sourcePath } : null,
      ].filter(Boolean),
      summary: compactInboxText([entry.displayTitle || entry.title, entry.displayBody || entry.body].filter(Boolean).join(" · "), 220),
      proposed_action: {
        id: "review_candidate",
        target_agent: targetAgentForInboxEntry(entry),
      },
      proposed_writeback: {
        save_target: String(raw.save_target || raw.target_path || inferredSaveTarget).trim(),
        object_type: objectTypeForInboxEntry(entry),
        object_id: actionId || objectPath || String(entry.displayTitle || entry.title || "").trim(),
        object_path: objectPath,
        ...transitionForInboxEntry(entry),
      },
      sensitivity: sensitivityForInboxEntry(entry),
      required_confirmation: requiredConfirmationForInboxEntry(entry),
      validation: {
        workflow_status: candidateStatusForInboxEntry(entry),
        evidence_state: evidenceStateForInboxEntry(entry),
      },
      source_agent: sourceAgentForInboxEntry(entry),
      created_at: raw.createdAt || raw.created_at || "",
      updated_at: entry.updatedAt || raw.updatedAt || raw.updated_at || "",
    }, entry);
  }

  function candidateEnvelopeForBatch(entries = [], text = defaultText) {
    const count = Array.isArray(entries) ? entries.length : 0;
    return normalizeCandidateEnvelope({
      candidate_id: `candidate:unified-inbox:${Date.now()}`,
      plugin_id: "researchos_core",
      candidate_type: "inbox_batch",
      source_refs: [{ kind: "active_context", path: "06_active_context" }],
      summary: `${count} ${text("unifiedInboxPending")}`,
      proposed_action: { id: "review_candidate_batch", target_agent: "inbox_secretary" },
      proposed_writeback: {
        save_target: "06_active_context",
        object_type: "inbox_batch",
        object_id: "active-unified-inbox",
        object_path: "06_active_context",
        current_state: text("unifiedInboxAuthorityNoChange"),
        proposed_state: text("unifiedInboxAuthorityCandidateOnly"),
        decision_rationale: "",
        impact_scope: String(text("unifiedInboxBatchImpactScope")).replace("{count}", String(count)),
        rollback_ref: "",
        validation_state: "unvalidated",
      },
      sensitivity: "internal",
      required_confirmation: "handoff_only",
      validation: {
        workflow_status: "active",
        evidence_state: "candidate",
      },
      admission_state: normalizeAdmissionState({ decision_state: "proposed" }),
      source_agent: "orchestrator",
    }, { type: "inbox_batch" });
  }

  function candidateRequiresJudgmentReceipt(entry = {}) {
    const candidate = entry.candidate || {};
    const admission = candidate.admission_state || {};
    const transition = candidate.proposed_writeback || {};
    if (!candidate.candidate_id || entry.archived || entry.sourceOnly) return false;
    if (["accepted", "revised", "rejected", "deferred"].includes(String(admission.decision_state || ""))) return false;
    return entry.type === "confirmation"
      || entry.type === "dissolution"
      || String(candidate.required_confirmation || "handoff_only") !== "handoff_only"
      || [transition.current_state, transition.proposed_state, transition.decision_rationale, transition.impact_scope]
        .some((value) => Boolean(String(value || "").trim()));
  }

  function reviewSourceItemIsEligible(item = {}) {
    if (!item || typeof item !== "object") return false;
    if (item.type === "paper_field_update" || item.source === "work-session" || item.work_session_id) return true;
    if (item.candidate && typeof item.candidate === "object") return true;
    if (item.admission_state && typeof item.admission_state === "object") return true;
    if (item.proposed_writeback && typeof item.proposed_writeback === "object") return true;
    if (item.transition && typeof item.transition === "object") return true;
    return [
      item.current_state,
      item.proposed_state,
      item.target_state,
      item.decision_rationale,
      item.impact_scope,
      item.rollback_ref,
      item.validation_state,
      item.mutation_state,
    ].some((value) => Boolean(String(value || "").trim()));
  }

  function entriesForItem(entries = [], options = {}) {
    const itemId = String(options.itemId || "").trim();
    const sessionIds = new Set((Array.isArray(options.sessionIds) ? options.sessionIds : [])
      .map((value) => String(value || "").trim()).filter(Boolean));
    if (!itemId || !sessionIds.size) return [];
    return (Array.isArray(entries) ? entries : []).filter((entry = {}) => {
      const raw = entry.raw && typeof entry.raw === "object" ? entry.raw : {};
      const candidate = entry.candidate && typeof entry.candidate === "object" ? entry.candidate : {};
      const writeback = candidate.proposed_writeback && typeof candidate.proposed_writeback === "object"
        ? candidate.proposed_writeback : {};
      const explicitItemIds = [
        raw.item_id,
        raw.itemId,
        raw.portfolio_binding?.item_id,
        raw.portfolioBinding?.itemId,
        writeback.object_id,
      ].map((value) => String(value || "").trim()).filter(Boolean);
      const workSessionId = String(raw.work_session_id || raw.workSessionId || "").trim();
      return sessionIds.has(workSessionId) || explicitItemIds.includes(itemId);
    });
  }

  function judgmentReceiptDraftForEntry(entry = {}, options = {}) {
    if (!candidateRequiresJudgmentReceipt(entry)) return null;
    const text = options.text || defaultText;
    const language = String(options.language || "zh-CN").toLowerCase();
    const isZh = language.startsWith("zh");
    const source = entry.candidate || candidateEnvelopeForEntry(entry);
    const title = inboxEntryDisplayTitle(entry, text);
    const objectRef = source.proposed_writeback || {};
    const sourceRefs = (Array.isArray(source.source_refs) ? source.source_refs : [])
      .map((item) => String(item?.path || item?.id || item || "").trim())
      .filter(Boolean)
      .slice(0, 12);
    const intent = isZh
      ? [
          `为“${title}”准备一份可编辑的判断回执候选。`,
          "先把候选内容拆成可以逐项判断的主张；不要替我决定，而是把每条主张保留为待我明确采纳、修订、拒绝或暂缓的选项。",
          "同时列出支持证据、最强反证、未知项、当前信心、实际投入或风险、责任人、什么证据会让我改判，以及何时复核。",
          "结果尚未出现，因此不要生成经验教训、反思结论或声称判断已被校准。只返回可审阅候选；不自动执行原任务，不直接写入长期记忆、稳定规则或公开内容。",
          "按 researchos-judgment-receipt-v1 合同组织结果。若我尚未对每条主张给出明确处置，先返回待确认表格与最少问题，不要猜测处置，也不要伪造一份通过校验的回执。",
        ].join("\n\n")
      : [
          `Prepare an editable Judgment Receipt candidate for “${title}”.`,
          "Split the candidate into individually decidable claims. Do not decide for me; leave every claim for my explicit accept, revise, reject, or defer decision.",
          "Include supporting evidence, the strongest counterevidence, unknowns, current confidence, real stake, responsible actor, change trigger, and review trigger.",
          "The outcome is not known yet, so do not create lessons learned, a reflection conclusion, or claim that the judgment is calibrated. Return a reviewable candidate only; do not execute the original task or directly write durable memory, stable rules, or public content.",
          "Use the researchos-judgment-receipt-v1 contract. If I have not explicitly disposed every claim, return a pending-decision table and the minimum questions instead of guessing or fabricating a schema-valid receipt.",
        ].join("\n\n");
    return {
      candidate: normalizeCandidateEnvelope({
        ...source,
        candidate_id: `candidate:judgment_receipt:${source.candidate_id}`,
        candidate_type: "judgment_receipt",
        source_candidate_id: source.candidate_id,
        source_refs: Array.isArray(source.source_refs) ? source.source_refs : [],
        summary: isZh ? `判断回执候选：${title}` : `Judgment Receipt candidate: ${title}`,
        proposed_action: { id: "prepare_judgment_receipt", target_agent: "inbox_secretary" },
        proposed_writeback: {
          save_target: "",
          object_type: String(objectRef.object_type || entry.type || "candidate"),
          object_id: String(objectRef.object_id || entry.actionId || source.candidate_id || ""),
          object_path: String(objectRef.object_path || entry.path || ""),
          current_state: String(objectRef.current_state || "candidate awaiting judgment"),
          proposed_state: "judgment receipt candidate awaiting human disposition",
          decision_rationale: "",
          impact_scope: String(objectRef.impact_scope || ""),
          rollback_ref: "",
          validation_state: "unvalidated",
        },
        required_confirmation: "confirm",
        validation: { workflow_status: "active", evidence_state: "candidate" },
        admission_state: normalizeAdmissionState({ decision_state: "proposed" }),
      }, entry),
      cards: options.includeContractCard === true ? [{
        id: "contract:researchos-judgment-receipt-v1",
        path: "09_templates/data_contracts/researchos-judgment-receipt-v1.schema.json",
        title: "ResearchOS Judgment Receipt v1",
        type: "contract",
        typeLabel: isZh ? "判断回执合同" : "Judgment Receipt contract",
      }] : [],
      evidenceBoundary: isZh
        ? "原候选与已登记来源是证据；模型整理只形成候选。人的逐项处置、责任承诺和任何长期写回必须在 Review 中明确确认。"
        : "The original candidate and registered sources are evidence; model synthesis remains a candidate. Human disposition, responsibility, and any durable writeback require explicit Review confirmation.",
      goal: isZh ? `冻结结果未知时对“${title}”的判断边界` : `Freeze the pre-outcome judgment boundary for “${title}”`,
      intent,
      responseMode: "writeback",
      sensitivity: source.sensitivity || "internal",
      sourceHint: sourceRefs[0] || entry.path || entry.sourcePath || "",
      templateLanguage: options.language || "zh-CN",
      title: isZh ? `判断回执：${title}` : `Judgment Receipt: ${title}`,
    };
  }

  function collectUnifiedInboxEntries(sources = {}, deps = {}) {
    const text = deps.text || defaultText;
    const view = normalizeUnifiedInboxView(sources.view || "active");
    const archive = sources.archive && typeof sources.archive === "object" ? sources.archive : {};
    const resolvedArchive = sources.resolvedArchive && typeof sources.resolvedArchive === "object" ? sources.resolvedArchive : {};
    const paths = deps.paths || {};
    const activeDoingItems = filterActiveInboxItems(sources.doingItems || [], true)
      .filter(reviewSourceItemIsEligible);
    const doingKey = deps.doingKey || ((item = {}) => item.key || item.id || "");
    const doingTypeLabel = deps.doingTypeLabel || ((type = "") => type);
    const paperFieldSummary = deps.paperFieldSummary || (() => "");
    const confirmationChoiceLabel = deps.confirmationChoiceLabel || ((choice = "") => choice);

    const paperFieldRecords = activeDoingItems
      .filter((item) => item.type === "paper_field_update")
      .map((item) => ({
        type: "paper_field_update",
        typeLabel: text("unifiedInboxPaperField"),
        title: item.title || item.path || "",
        body: paperFieldSummary(item.field_updates || {}),
        path: item.path || "",
        status: item.status || "local",
        statusLabel: unifiedInboxStatusLabel(item.status || "local", text),
        sourcePath: "",
        updatedAt: item.addedAt || "",
        actionId: doingKey(item),
        candidate: item.candidate || null,
        raw: item,
      }));
    const taskRecords = activeDoingItems
      .filter((item) => item.type !== "paper_field_update")
      .map((item) => ({
        type: "task",
        typeLabel: text("unifiedInboxTask"),
        title: item.title || item.path || "",
        body: `${doingTypeLabel(item.type)}${item.action ? ` · ${item.action}` : ""}${item.target_state ? ` · ${item.target_state}` : ""}${item.note ? ` · ${item.note}` : ""}`,
        path: item.path || "",
        status: item.status || "local",
        statusLabel: unifiedInboxStatusLabel(item.status || "local", text),
        sourcePath: "",
        updatedAt: item.addedAt || "",
        actionId: doingKey(item),
        candidate: item.candidate || null,
        raw: item,
      }));
    const confirmationRecords = Object.entries(sources.confirmationDecisions || {})
      .filter(([, record]) => record && typeof record === "object" && record.choice && inboxStatusIsActive(record.status || record.syncStatus, true))
      .map(([id, record]) => ({
        type: "confirmation",
        typeLabel: text("unifiedInboxConfirmation"),
        title: record.title || id,
        body: `${record.choiceLabel || confirmationChoiceLabel(record.choice)}${record.suggestion ? ` · ${record.suggestion}` : ""}`,
        path: record.target_path || "",
        status: record.status || record.syncStatus || "local",
        statusLabel: unifiedInboxStatusLabel(record.status || record.syncStatus || "local", text),
        sourcePath: paths.confirmation || "",
        updatedAt: record.updatedAt || "",
        actionId: id,
        raw: { decision_id: id, ...record },
      }));
    const previewFeedbackRecords = (Array.isArray(sources.previewFeedbackItems) ? sources.previewFeedbackItems : [])
      .filter((item) => inboxStatusIsActive(item.status, true))
      .map((item) => ({
        type: "preview_feedback",
        typeLabel: text("unifiedInboxPreviewFeedback"),
        title: item.title || item.target_path || "",
        body: `${item.category || text("previewFeedbackCategoryDefault")} · ${item.feedback || ""}`,
        path: item.target_path || "",
        status: item.status || "pending_codex_review",
        statusLabel: unifiedInboxStatusLabel(item.status || "pending_codex_review", text),
        sourcePath: paths.feedback || "",
        updatedAt: item.updatedAt || item.createdAt || "",
        actionId: item.id || "",
        raw: item,
      }));
    const pluginCandidateRecords = (Array.isArray(sources.candidateEntries) ? sources.candidateEntries : [])
      .filter((entry) => entry && typeof entry === "object" && inboxStatusIsActive(entry.status, true));
    const feedbackSource = {
      type: "feedback",
      typeLabel: text("unifiedInboxFeedback"),
      title: text("codexFeedbackInboxFile"),
      body: text("feedbackHint"),
      path: paths.feedback || "",
      status: "source_file",
      statusLabel: unifiedInboxStatusLabel("source_file", text),
      sourcePath: paths.feedback || "",
      updatedAt: "",
      raw: { note: "Feedback items are written directly to the markdown/jsonl inbox by the server." },
      sourceOnly: true,
    };
    const decorateEntry = (entry = {}) => {
      const archiveKey = unifiedInboxEntryArchiveKey(entry.type, entry.actionId);
      const archiveRecord = archiveKey ? archive[archiveKey] : null;
      const decorated = {
        ...entry,
        archiveKey,
        archived: Boolean(archiveRecord),
        archivedAt: archiveRecord?.archivedAt || "",
        archiveRecord: archiveRecord || null,
        displayBody: entry.displayBody || inboxEntryDisplayBody(entry, text),
        displayMeta: entry.displayMeta || inboxEntryDisplayMeta(entry, text),
        displayTitle: entry.displayTitle || inboxEntryDisplayTitle(entry, text),
      };
      const candidate = normalizeCandidateEnvelope(entry.candidate || candidateEnvelopeForEntry(decorated), decorated);
      const governed = { ...decorated, candidate };
      return {
        ...governed,
        judgmentReceiptEligible: candidateRequiresJudgmentReceipt(governed),
      };
    };
    const allEntries = [
      ...paperFieldRecords,
      ...taskRecords,
      ...confirmationRecords,
      ...previewFeedbackRecords,
      ...pluginCandidateRecords,
    ]
      .map(decorateEntry)
      .filter((entry) => !entry.archiveKey || !resolvedArchive[entry.archiveKey]);
    const activeEntries = allEntries.filter((entry) => !entry.archived);
    const archivedEntries = allEntries.filter((entry) => entry.archived);
    const entries = view === "archived" ? archivedEntries : view === "all" ? allEntries : activeEntries;
    const localActiveTotal = activeEntries.filter((entry) => entry.type === "task" || entry.type === "paper_field_update").length;
    const visibleCount = (type) => entries.filter((entry) => entry.type === type).length;
    const sourceEntries = [
      { key: "paper_field_update", label: text("unifiedInboxPaperField"), path: "", count: visibleCount("paper_field_update") },
      { key: "task", label: text("unifiedInboxTask"), path: "", count: visibleCount("task") },
      { key: "confirmation", label: text("unifiedInboxConfirmation"), path: paths.confirmation || "", count: visibleCount("confirmation") },
      { key: "feedback", label: text("unifiedInboxFeedback"), path: paths.feedback || "", count: visibleCount("preview_feedback") },
      ...(Array.isArray(sources.candidateSourceEntries) ? sources.candidateSourceEntries : []).map((source) => ({
        ...source,
        count: visibleCount(source.key),
      })),
    ];
    return {
      entries,
      sourceEntries,
      sourceOnly: feedbackSource,
      needsReviewTotal: activeEntries.length,
      total: activeEntries.length,
      visibleTotal: entries.length,
      archivedTotal: archivedEntries.length,
      allTotal: allEntries.length,
      localActiveTotal,
      view,
    };
  }

  global.ResearchOSInboxService = Object.freeze({
    inboxStatusIsActive,
    unifiedInboxStatusLabel,
    filterActiveInboxItems,
    normalizeClearedInboxServerState,
    resolveClearedInboxItems,
    resolveClearedInboxObject,
    normalizeUnifiedInboxView,
    unifiedInboxEntryArchiveKey,
    archiveUnifiedInboxEntryFromInbox,
    findUnifiedInboxEntry,
    loadUnifiedInboxArchive,
    normalizeCandidateEnvelope,
    saveUnifiedInboxArchive,
    archiveUnifiedInboxEntry,
    clearProcessedInbox,
    collectUnifiedInboxEntries,
    completedRunCanArchiveEntry,
    candidateEnvelopeForEntry,
    candidateEnvelopeForBatch,
    entriesForItem,
    reviewSourceItemIsEligible,
    judgmentReceiptDraftForEntry,
    admissionStateForInboxEntry,
    normalizeAdmissionState,
    candidateStatusForInboxEntry,
    evidenceStateForInboxEntry,
    transitionForInboxEntry,
    restoreUnifiedInboxEntry,
    requiredConfirmationForInboxEntry,
    sensitivityForInboxEntry,
    sourceAgentForInboxEntry,
    targetAgentForInboxEntry,
    withdrawUnifiedInboxEntry,
  });
})(window);
