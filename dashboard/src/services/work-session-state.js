/* ResearchOS maintenance header.
 * 中文：任务状态优先 Work Session V1 的浏览器状态；保存当前任务和有界恢复摘要，不拥有长期记忆。
 * English: Browser state for task-state-first Work Session V1; owns the current task and bounded resume summaries, not durable memory.
 */

(function attachResearchOSWorkSessionState(global) {
  const VERSION = 10;
  const HISTORY_LIMIT = 10;
  const storageKeys = global.ResearchOSStorageContract?.storageKeys || {};
  const PRIVATE_KEY = storageKeys.workSessionPrivate || "researchos-private-work-session-v1";
  const PUBLIC_KEY = storageKeys.workSessionPublic || "researchos-public-work-session-v1";
  const PRIVATE_HISTORY_KEY = storageKeys.workSessionHistoryPrivate || "researchos-private-work-session-history-v1";
  const PUBLIC_HISTORY_KEY = storageKeys.workSessionHistoryPublic || "researchos-public-work-session-history-v1";

  function cleanText(value = "") {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function summaryMarkdown(value = "", limit = 1200) {
    const normalized = String(value || "")
      .replace(/\r\n?/g, "\n")
      .replace(/[ \t]+$/gm, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
    if (normalized.length <= limit) return normalized;
    const candidate = normalized.slice(0, Math.max(0, limit - 2));
    const lastLineBreak = candidate.lastIndexOf("\n");
    const lastSpace = candidate.lastIndexOf(" ");
    const boundary = Math.max(lastLineBreak, lastSpace);
    const clipped = candidate.slice(0, boundary >= Math.floor(limit * 0.65) ? boundary : candidate.length).trimEnd();
    return `${clipped}\n\n…`;
  }

  function plainRecord(value = null) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    try {
      return JSON.parse(JSON.stringify(value));
    } catch {
      return null;
    }
  }

  function runtimeStorageKey(runtimeMode = "") {
    return String(runtimeMode || "").trim() === "public_starter" ? PUBLIC_KEY : PRIVATE_KEY;
  }

  function runtimeHistoryStorageKey(runtimeMode = "") {
    return String(runtimeMode || "").trim() === "public_starter" ? PUBLIC_HISTORY_KEY : PRIVATE_HISTORY_KEY;
  }

  function isPublicDemoSession(session = {}) {
    const references = [
      session.portfolioBinding?.portfolioPath,
      session.portfolioBinding?.sourcePath,
      ...(Array.isArray(session.sourceHints) ? session.sourceHints : []),
      ...(Array.isArray(session.cards) ? session.cards.map((card) => card?.path) : []),
    ].map(cleanText).filter(Boolean);
    return references.some((value) => value.startsWith("08_exports/public_starter/"));
  }

  function portfolioBindingContextStatus(item = {}, binding = {}) {
    const itemId = cleanText(item.id || item.item_id);
    const boundItemId = cleanText(binding.itemId || binding.item_id);
    if (!itemId || !boundItemId || itemId !== boundItemId) return "unbound";
    const currentHash = cleanText(item.nextStepHash || item.next_step_hash);
    const boundHash = cleanText(binding.nextStepHash || binding.next_step_hash);
    if (currentHash && boundHash && currentHash !== boundHash) return "stale";
    const currentStep = cleanText(item.nextStepCanonical || item.next_step_canonical || item.nextStep || item.next_step);
    const boundStep = cleanText(binding.nextStepCanonical || binding.next_step_canonical || binding.nextStep || binding.next_step);
    if (currentStep && boundStep && currentStep !== boundStep) return "stale";
    const currentStage = cleanText(item.currentStageCanonical || item.current_stage_canonical || item.currentStage || item.current_stage);
    const boundStage = cleanText(binding.currentStageCanonical || binding.current_stage_canonical || binding.currentStage || binding.current_stage);
    if (currentStage && boundStage) return currentStage === boundStage ? "current" : "stale";
    return "unknown";
  }

  function sessionId() {
    if (global.crypto?.randomUUID) return `work-${global.crypto.randomUUID()}`;
    return `work-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function newClientRequestId() {
    if (global.crypto?.randomUUID) return `request-${global.crypto.randomUUID()}`;
    return `request-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function createLatestRequestGate() {
    let revision = 0;
    return Object.freeze({
      begin(identity = "") {
        revision += 1;
        return Object.freeze({ identity: cleanText(identity), revision });
      },
      invalidate() {
        revision += 1;
        return revision;
      },
      isCurrent(token = null, identity = "") {
        return Boolean(
          token
          && Number(token.revision) === revision
          && cleanText(token.identity) === cleanText(identity)
        );
      },
    });
  }

  function normalizeCard(card = {}) {
    const id = cleanText(card.id || card.path || card.title);
    const title = cleanText(card.title || card.path || id);
    if (!id || !title) return null;
    return {
      id,
      path: cleanText(card.path),
      preview: cleanText(card.preview || card.note),
      subtitle: cleanText(card.subtitle),
      title,
      type: cleanText(card.type || "asset"),
      typeLabel: cleanText(card.typeLabel || card.type_label || card.type || "asset"),
    };
  }

  function cardFromAssetElement(card = null, payload = null) {
    const dataset = card?.dataset || {};
    return normalizeCard({
      id: dataset.assetCardId || payload?.path || payload?.title,
      path: dataset.assetCardPath || payload?.path,
      preview: dataset.assetCardPreview || payload?.note,
      subtitle: dataset.assetCardSubtitle,
      title: dataset.assetCardTitle || payload?.title,
      type: dataset.assetCardType || payload?.type || "asset",
      typeLabel: dataset.assetCardTypeLabel,
    });
  }

  function sourceCardFromInput(input = {}, text = (key) => key) {
    const attachmentName = cleanText(input.attachmentName);
    const sourceHint = cleanText(input.sourceHint);
    const title = attachmentName || sourceHint;
    if (!title) return null;
    return normalizeCard({
      id: `source:${sourceHint || attachmentName}`,
      path: sourceHint,
      preview: sourceHint || cleanText(text("workSessionSourceCardHint")),
      title,
      type: "source",
      typeLabel: cleanText(text("workSessionInputSourceType")),
    });
  }

  function normalizePortfolioBinding(binding = {}) {
    if (!binding || typeof binding !== "object") return null;
    const itemId = cleanText(binding.itemId || binding.item_id);
    if (!itemId) return null;
    return {
      completeProjectActionId: cleanText(binding.completeProjectActionId || binding.complete_project_action_id),
      completeStepActionId: cleanText(binding.completeStepActionId || binding.complete_step_action_id),
      currentStage: cleanText(binding.currentStage || binding.current_stage),
      currentStageCanonical: cleanText(binding.currentStageCanonical || binding.current_stage_canonical),
      itemId,
      nextStep: cleanText(binding.nextStep || binding.next_step),
      nextStepCanonical: cleanText(binding.nextStepCanonical || binding.next_step_canonical),
      nextStepHash: cleanText(binding.nextStepHash || binding.next_step_hash),
      portfolioPath: cleanText(binding.portfolioPath || binding.portfolio_path),
      pluginId: cleanText(binding.pluginId || binding.plugin_id || binding.providerId || binding.provider_id),
      providerId: cleanText(binding.providerId || binding.provider_id),
      continuationSource: cleanText(binding.continuationSource || binding.continuation_source),
      sourcePath: cleanText(binding.sourcePath || binding.source_path),
      title: cleanText(binding.title),
    };
  }

  function normalizeTurn(turn = {}) {
    const status = cleanText(turn.status || "completed");
    if (status !== "completed") return null;
    const question = cleanText(turn.question);
    const answer = String(turn.answer || "").trim().slice(0, 24000);
    if (!question || !answer) return null;
    return {
      answer,
      artifacts: (Array.isArray(turn.artifacts) ? turn.artifacts : []).slice(0, 12),
      createdAt: cleanText(turn.createdAt) || new Date().toISOString(),
      includeInPrompt: turn.includeInPrompt !== false,
      taskComplexity: cleanText(turn.taskComplexity || turn.task_complexity || turn.modelTier || turn.model_tier),
      question,
      reasoningEffort: cleanText(turn.reasoningEffort || turn.reasoning_effort),
      responseMode: cleanText(turn.responseMode || turn.response_mode || "answer"),
      runId: cleanText(turn.runId || turn.id),
      status,
    };
  }

  function workItemBindingProjection(session = null, items = []) {
    const binding = normalizePortfolioBinding(session?.portfolioBinding);
    if (!binding) {
      return {
        bound: false,
        itemFound: false,
        projectOpen: false,
        stepCompleted: false,
        stepCurrent: false,
      };
    }
    const item = (Array.isArray(items) ? items : []).find((candidate) => (
      cleanText(candidate?.id || candidate?.item_id) === binding.itemId
      && cleanText(candidate?.provider_id || candidate?.providerId || "research_portfolio") === (binding.providerId || "research_portfolio")
    ));
    if (!item) {
      return {
        bound: true,
        itemFound: false,
        projectOpen: false,
        stepCompleted: false,
        stepCurrent: false,
      };
    }
    const currentHash = cleanText(item.next_step_hash || item.nextStepHash);
    const completedHash = cleanText(item.completed_step_hash || item.completedStepHash);
    const projectOpen = cleanText(item.state) !== "closed"
      && cleanText(item.lifecycle_state || item.lifecycleState) !== "completed";
    const stepCurrent = Boolean(binding.nextStepHash && currentHash === binding.nextStepHash);
    return {
      bound: true,
      itemFound: true,
      projectOpen,
      stepCompleted: projectOpen
        && stepCurrent
        && cleanText(item.attention_state || item.attentionState) === "needs_next_step"
        && completedHash === binding.nextStepHash,
      stepCurrent,
    };
  }

  function artifactPaths(items = []) {
    return [...new Set((Array.isArray(items) ? items : [])
      .map((item) => cleanText(typeof item === "string" ? item : item?.path))
      .filter(Boolean))]
      .slice(0, 12);
  }

  function normalizeHistoryEntry(entry = {}) {
    if (!entry || typeof entry !== "object") return null;
    const id = cleanText(entry.id || entry.historyId);
    const intent = cleanText(entry.intent || entry.title);
    if (!id || !intent) return null;
    const status = ["paused", "ready", "completed"].includes(entry.status) ? entry.status : "paused";
    const goal = cleanText(entry.goal || entry.title || intent);
    return {
      artifacts: artifactPaths(entry.artifacts).slice(0, 8),
      candidate: plainRecord(entry.candidate),
      cards: (Array.isArray(entry.cards) ? entry.cards : []).map(normalizeCard).filter(Boolean).slice(0, 8),
      createdAt: cleanText(entry.createdAt) || new Date().toISOString(),
      evidenceBoundary: cleanText(entry.evidenceBoundary),
      enhancement: plainRecord(entry.enhancement),
      goal,
      id,
      intent,
      portfolioBinding: normalizePortfolioBinding(entry.portfolioBinding),
      responseMode: ["auto", "answer", "artifact", "writeback"].includes(entry.responseMode) ? entry.responseMode : "auto",
      resultSummary: summaryMarkdown(entry.resultSummary),
      sensitivity: cleanText(entry.sensitivity || "internal"),
      sourceHints: (Array.isArray(entry.sourceHints) ? entry.sourceHints : []).map(cleanText).filter(Boolean).slice(0, 6),
      status,
      templateLanguage: cleanText(entry.templateLanguage),
      title: cleanText(entry.title) || intent,
      turnCount: Math.max(0, Math.min(99, Number(entry.turnCount) || 0)),
      updatedAt: cleanText(entry.updatedAt) || new Date().toISOString(),
    };
  }

  function taskIdentityProjection(entry = {}) {
    const binding = normalizePortfolioBinding(entry?.portfolioBinding);
    if (binding?.itemId) {
      const owner = cleanText(binding.providerId || binding.pluginId || "research_portfolio");
      const stepSignature = cleanText(binding.nextStepHash || binding.nextStep);
      if (stepSignature) return Object.freeze({
        identity_kind: "registered_item_step",
        item_id: binding.itemId,
        logical_task_id: `portfolio:${owner}:${binding.itemId}:${stepSignature}`,
        next_step_signature: stepSignature,
        provider_id: owner,
        session_id: cleanText(entry?.id),
      });
    }
    const historyId = cleanText(entry?.historyId || entry?.resumedFromId || entry?.id);
    return Object.freeze({
      identity_kind: historyId ? "unbound_session" : "none",
      item_id: "",
      logical_task_id: historyId ? `session:${historyId}` : "",
      next_step_signature: "",
      provider_id: "",
      session_id: cleanText(entry?.id || historyId),
    });
  }

  function historyTaskIdentity(entry = {}) {
    return taskIdentityProjection(entry).logical_task_id;
  }

  function sessionRegistryProjection(currentSession = null, historyEntries = [], runs = []) {
    const current = normalizeSession(currentSession);
    const seenSessionIds = new Set(current?.id ? [current.id] : []);
    const history = (Array.isArray(historyEntries) ? historyEntries : [])
      .map(normalizeHistoryEntry)
      .filter(Boolean)
      .filter((entry) => {
        if (seenSessionIds.has(entry.id)) return false;
        seenSessionIds.add(entry.id);
        return true;
      })
      .sort((left, right) => String(right.updatedAt).localeCompare(String(left.updatedAt)))
      .slice(0, HISTORY_LIMIT);
    const runList = Array.isArray(runs) ? runs.filter(Boolean) : [];
    const project = (entry, selected = false) => {
      const sessionId = cleanText(entry?.id);
      const run = runList.find((candidate) => cleanText(candidate?.work_session_id) === sessionId) || null;
      const lifecycle = selected
        ? lifecycleProjection(current, run)
        : null;
      const terminalRunNeedsReview = !selected && ["completed", "failed"].includes(cleanText(run?.status));
      const rawState = selected
        ? lifecycle?.state
        : terminalRunNeedsReview
          ? "late_result_ready"
          : cleanText(entry?.status || "paused");
      const workState = ["result_ready", "late_result_ready", "invalid"].includes(rawState)
        || (!selected && rawState === "ready")
        ? "needs_review"
        : ["running", "verify_delivery", "verify_run", "failed_retryable", "failed_needs_impact_check", "ended_with_run_tracking"].includes(rawState)
          ? "active"
          : ["ended", "completed"].includes(rawState)
            ? "done"
            : rawState === "paused"
              ? "waiting"
              : "ready";
      return Object.freeze({
        intent: cleanText(entry?.intent || entry?.title),
        item_id: taskIdentityProjection(entry).item_id,
        logical_task_id: taskIdentityProjection(entry).logical_task_id,
        next_step_signature: taskIdentityProjection(entry).next_step_signature,
        run_id: cleanText(run?.id || (selected ? current?.latestRunId : "")),
        selected,
        session_id: sessionId,
        work_state: workState,
      });
    };
    return Object.freeze([
      ...(current ? [project(current, true)] : []),
      ...history.map((entry) => project(entry, false)),
    ]);
  }

  function mergeHistoryCards(primary = [], secondary = []) {
    const seen = new Set();
    return [...primary, ...secondary]
      .map(normalizeCard)
      .filter(Boolean)
      .filter((card) => {
        const key = cleanText(card.id || card.path || card.title);
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .slice(0, 8);
  }

  function mergeHistoryEntries(primary = {}, secondary = {}) {
    const sameStoredRecord = cleanText(primary.id) === cleanText(secondary.id);
    const createdAt = [cleanText(primary.createdAt), cleanText(secondary.createdAt)]
      .filter(Boolean)
      .sort()[0];
    return normalizeHistoryEntry({
      ...secondary,
      ...primary,
      artifacts: artifactPaths([...(primary.artifacts || []), ...(secondary.artifacts || [])]).slice(0, 8),
      candidate: primary.candidate || secondary.candidate,
      cards: mergeHistoryCards(primary.cards, secondary.cards),
      createdAt,
      enhancement: primary.enhancement || secondary.enhancement,
      evidenceBoundary: primary.evidenceBoundary || secondary.evidenceBoundary,
      portfolioBinding: primary.portfolioBinding || secondary.portfolioBinding,
      resultSummary: primary.resultSummary || secondary.resultSummary,
      sourceHints: [...new Set([...(primary.sourceHints || []), ...(secondary.sourceHints || [])]
        .map(cleanText)
        .filter(Boolean))].slice(0, 6),
      turnCount: sameStoredRecord
        ? Math.max(primary.turnCount || 0, secondary.turnCount || 0)
        : Math.min(99, (primary.turnCount || 0) + (secondary.turnCount || 0)),
    });
  }

  function normalizeHistory(entries = []) {
    const normalized = (Array.isArray(entries) ? entries : [])
      .map(normalizeHistoryEntry)
      .filter(Boolean)
      .sort((left, right) => String(right.updatedAt).localeCompare(String(left.updatedAt)));
    const identityIndexes = new Map();
    const collapsed = [];
    normalized.forEach((entry) => {
      const identity = historyTaskIdentity(entry);
      if (!identityIndexes.has(identity)) {
        identityIndexes.set(identity, collapsed.length);
        collapsed.push(entry);
        return;
      }
      const index = identityIndexes.get(identity);
      collapsed[index] = mergeHistoryEntries(collapsed[index], entry);
    });
    return collapsed.slice(0, HISTORY_LIMIT);
  }

  function turnFromResult(question = "", result = {}) {
    if (cleanText(result?.status) !== "completed") return null;
    return normalizeTurn({
      answer: result?.answer,
      artifacts: result?.artifacts,
      createdAt: result?.completed_at || result?.updated_at || result?.created_at,
      includeInPrompt: result?.execution_status !== "copy_ready",
      task_complexity: result?.task_complexity || result?.model_tier,
      question,
      reasoning_effort: result?.reasoning_effort,
      response_mode: result?.response_mode,
      runId: result?.id,
      status: result?.status,
    });
  }

  function normalizeSession(session = {}) {
    if (!session || typeof session !== "object") return null;
    const intent = cleanText(session.intent);
    const id = cleanText(session.id);
    if (!id || !intent) return null;
    const storedTitle = cleanText(session.title);
    const title = intent.length > 72 && storedTitle === intent.slice(0, 72) ? intent : storedTitle || intent;
    const goal = cleanText(session.goal || title || intent);
    const cards = (Array.isArray(session.cards) ? session.cards : [])
      .map(normalizeCard)
      .filter(Boolean)
      .slice(0, 12);
    const sourceHints = (Array.isArray(session.sourceHints) ? session.sourceHints : [])
      .map(cleanText)
      .filter(Boolean)
      .slice(0, 8);
    const turns = (Array.isArray(session.turns) ? session.turns : [])
      .map(normalizeTurn)
      .filter(Boolean)
      .slice(-8);
    const draftStatus = cleanText(session.draftResult?.status || "completed");
    const draftError = draftStatus === "failed"
      ? global.ResearchOSResultEnvelope?.normalizeError?.({
          ...(session.draftResult?.error_envelope || {}),
          error_type: session.draftResult?.error_envelope?.error_type || session.draftResult?.error_type,
          run_id: session.draftResult?.error_envelope?.run_id || session.draftResult?.id,
        }, session.draftResult?.error_type)
      : null;
    const draftResult = session.draftResult && typeof session.draftResult === "object"
      ? {
          answer: draftError ? "" : String(session.draftResult.answer || "").slice(0, 24000),
          artifacts: draftError ? [] : (Array.isArray(session.draftResult.artifacts) ? session.draftResult.artifacts : []).slice(0, 12),
          client_request_id: cleanText(session.draftResult.client_request_id),
          error_envelope: draftError,
          error_type: draftError?.error_type || "",
          execution_status: cleanText(session.draftResult.execution_status),
          id: /^failed-/.test(cleanText(session.draftResult.id)) ? "" : cleanText(session.draftResult.id),
          lease_expired: session.draftResult.lease_expired === true,
          message: draftError?.message || "",
          model: cleanText(session.draftResult.model),
          result_envelope: global.ResearchOSResultEnvelope?.normalizeResult?.(session.draftResult.result_envelope),
          task_complexity: cleanText(session.draftResult.task_complexity || session.draftResult.model_tier),
          reasoning_effort: cleanText(session.draftResult.reasoning_effort),
          response_mode: cleanText(session.draftResult.response_mode),
          status: draftStatus,
          title: cleanText(session.draftResult.title),
          work_session_id: cleanText(session.draftResult.work_session_id || id),
        }
      : null;
    const storedStatus = ["draft", "active", "running", "ready", "completed"].includes(session.status) ? session.status : "active";
    const deliveryUnknownTypes = new Set(["transport_delivery_unknown", "invalid_server_response", "submit_rejected"]);
    const reconcileFailureTypes = new Set(["run_ledger_corrupt", "run_ledger_unavailable", "run_request_conflict", "run_reconcile_ambiguous"]);
    const errorType = cleanText(draftError?.error_type);
    const deliveryUnknown = deliveryUnknownTypes.has(errorType) || draftResult?.execution_status === "delivery_unknown";
    const sessionLifecycle = storedStatus === "completed" ? "ended" : "open";
    const explicitRunLifecycle = ["none", "submitted", "queued", "running", "completed", "failed"].includes(session.runLifecycle)
      ? session.runLifecycle : "none";
    const runLifecycle = deliveryUnknown
      ? "submitted"
      : reconcileFailureTypes.has(errorType)
        ? ["submitted", "queued", "running"].includes(explicitRunLifecycle)
          ? explicitRunLifecycle
          : cleanText(session.latestRunId) ? "running" : "none"
      : ["submitted", "queued", "running", "completed", "failed"].includes(draftResult?.status)
        ? draftResult.status
        : storedStatus === "running" && (cleanText(session.latestRunId) || cleanText(session.clientRequestId))
          ? "running"
          : storedStatus === "ready"
            ? "completed"
            : explicitRunLifecycle;
    const explicitObservation = ["none", "fresh", "delivery_unknown", "lease_expired", "reconcile_failed"].includes(session.runObservation)
      ? session.runObservation : "none";
    const runObservation = runLifecycle === "none"
      ? "none"
      : deliveryUnknown
        ? "delivery_unknown"
        : draftResult?.lease_expired === true
          ? "lease_expired"
          : reconcileFailureTypes.has(errorType) || (storedStatus === "running" && !draftResult
            && !(cleanText(session.latestRunId) && explicitObservation === "fresh"))
            ? "reconcile_failed"
            : draftResult || ["completed", "failed"].includes(runLifecycle)
              ? "fresh"
              : explicitObservation;
    const resultEnvelopeMode = cleanText(draftResult?.result_envelope?.result_mode);
    const legacyResultMode = ["answer", "artifact", "writeback"].includes(cleanText(draftResult?.response_mode))
      ? cleanText(draftResult.response_mode)
      : ["answer", "artifact", "writeback"].includes(cleanText(session.responseMode))
        ? cleanText(session.responseMode)
        : "answer";
    const invalidEnvelope = draftResult?.status === "completed"
      && Boolean(session.draftResult?.result_envelope)
      && !draftResult?.result_envelope;
    const explicitResultMode = ["none", "answer", "artifact", "writeback", "invalid"].includes(session.resultMode)
      ? session.resultMode : "none";
    const resultMode = runLifecycle === "completed"
      ? invalidEnvelope
        ? "invalid"
        : ["answer", "artifact", "writeback"].includes(resultEnvelopeMode)
          ? resultEnvelopeMode
          : legacyResultMode
      : explicitResultMode === "invalid" ? "invalid" : "none";
    const rawAdmission = session.admissionState && typeof session.admissionState === "object" ? session.admissionState : {};
    const hasCandidate = Boolean(session.candidate && typeof session.candidate === "object");
    const admissionState = {
      decision: ["none", "pending", "accepted", "revised", "rejected", "deferred"].includes(rawAdmission.decision)
        ? rawAdmission.decision : hasCandidate ? "pending" : "none",
      mutation: ["not_applied", "applied", "reverted"].includes(rawAdmission.mutation) ? rawAdmission.mutation : "not_applied",
      validation: ["not_run", "passed", "failed"].includes(rawAdmission.validation) ? rawAdmission.validation : "not_run",
      authority_role: ["none", "candidate", "admitted", "reverted"].includes(rawAdmission.authority_role)
        ? rawAdmission.authority_role : hasCandidate ? "candidate" : "none",
    };
    const status = sessionLifecycle === "ended"
      ? "completed"
      : ["answer", "artifact", "writeback"].includes(resultMode)
        ? "ready"
        : ["submitted", "queued", "running"].includes(runLifecycle) && runObservation === "fresh"
          ? "running"
          : storedStatus === "draft" && runLifecycle === "none"
            ? "draft"
            : "active";
    return {
      attachmentName: cleanText(session.attachmentName),
      admissionState,
      candidate: plainRecord(session.candidate),
      cards,
      clientRequestId: cleanText(session.clientRequestId),
      createdAt: cleanText(session.createdAt) || new Date().toISOString(),
      draftResult,
      evidenceBoundary: cleanText(session.evidenceBoundary),
      enhancement: plainRecord(session.enhancement),
      goal,
      handoffKey: cleanText(session.handoffKey),
      historyCreatedAt: cleanText(session.historyCreatedAt),
      historyId: cleanText(session.historyId),
      id,
      inputKind: cleanText(session.inputKind || "intent"),
      intent,
      latestRunId: cleanText(session.latestRunId),
      portfolioBinding: normalizePortfolioBinding(session.portfolioBinding),
      responseMode: ["auto", "answer", "artifact", "writeback"].includes(session.responseMode) ? session.responseMode : "auto",
      resultMode,
      resumeArtifacts: artifactPaths(session.resumeArtifacts).slice(0, 8),
      resumeSummary: summaryMarkdown(session.resumeSummary, 2400),
      resumeTurnCount: Math.max(0, Math.min(99, Number(session.resumeTurnCount) || 0)),
      resumedFromId: cleanText(session.resumedFromId),
      runLifecycle,
      runObservation,
      sensitivity: cleanText(session.sensitivity || "internal"),
      sessionLifecycle,
      sideEffects: ["none", "unknown", "confirmed"].includes(draftError?.side_effects)
        ? draftError.side_effects : ["none", "unknown", "confirmed"].includes(session.sideEffects) ? session.sideEffects : "none",
      sourceHints,
      status,
      templateLanguage: cleanText(session.templateLanguage),
      title,
      turns,
      updatedAt: cleanText(session.updatedAt) || new Date().toISOString(),
      version: VERSION,
    };
  }

  function createSession(input = {}) {
    const intent = cleanText(input.intent);
    if (!intent) return null;
    const now = new Date().toISOString();
    const sourceCard = sourceCardFromInput(input, input.text);
    const cards = Array.isArray(input.cards) && input.cards.length
      ? input.cards
      : sourceCard ? [sourceCard] : [];
    return normalizeSession({
      attachmentName: input.attachmentName,
      candidate: input.candidate,
      cards,
      createdAt: now,
      evidenceBoundary: input.evidenceBoundary,
      enhancement: input.enhancement,
      goal: input.goal || intent,
      id: sessionId(),
      inputKind: input.inputKind || (input.attachmentName ? "file" : input.sourceHint ? "link" : "intent"),
      intent,
      portfolioBinding: input.portfolioBinding,
      responseMode: input.responseMode || "auto",
      sensitivity: input.sensitivity,
      sourceHints: [input.sourceHint || input.attachmentName].filter(Boolean),
      status: "active",
      templateLanguage: input.templateLanguage,
      title: input.title || intent,
      turns: input.turns || [],
      updatedAt: now,
      version: VERSION,
    });
  }

  function lifecycleProjection(session = null, observedRun = null) {
    const current = normalizeSession(observedRun && typeof observedRun === "object"
      ? { ...(session || {}), draftResult: observedRun }
      : session);
    const interaction = global.ResearchOSInteractionContract;
    if (!interaction?.deriveTaskPresentation) {
      return Object.freeze({
        allowedActions: Object.freeze(["inspect_contract"]),
        errors: ["interaction_contract_unavailable"],
        primaryAction: "inspect_contract",
        retryAllowed: false,
        state: "invalid",
      });
    }
    if (!current) return interaction.deriveTaskPresentation({ session: "none" });
    return interaction.deriveTaskPresentation({
      admission: current.admissionState,
      observation: current.runObservation,
      result: current.resultMode,
      run: current.runLifecycle,
      session: current.sessionLifecycle,
      sideEffects: current.sideEffects,
    });
  }

  function updateSession(session, updates = {}) {
    const current = normalizeSession(session);
    if (!current) return null;
    const merged = {
      ...current,
      ...updates,
      updatedAt: new Date().toISOString(),
    };
    if (["active", "draft"].includes(updates.status) && !current.draftResult && !Object.hasOwn(updates, "draftResult")) {
      merged.runLifecycle = "none";
      merged.runObservation = "none";
      merged.resultMode = "none";
    }
    return normalizeSession(merged);
  }

  function sourceReferences(card = {}) {
    if (cleanText(card.type) !== "source") return [];
    return [...new Set([card.path, card.title].map(cleanText).filter(Boolean))];
  }

  function removeSourceReferences(sourceHints = [], removedCard = {}, remainingCards = []) {
    const removed = new Set(sourceReferences(removedCard));
    if (!removed.size) return sourceHints;
    const stillActive = new Set(remainingCards.flatMap(sourceReferences));
    return sourceHints.filter((hint) => {
      const normalized = cleanText(hint);
      return !removed.has(normalized) || stillActive.has(normalized);
    });
  }

  function addCard(session, card = {}) {
    const current = normalizeSession(session);
    const normalizedCard = normalizeCard(card);
    if (!current || !normalizedCard) return current;
    const cards = current.cards.filter((item) => item.id !== normalizedCard.id);
    cards.push(normalizedCard);
    let sourceHints = current.sourceHints;
    if (cards.length > 12) {
      const newestIndex = cards.length - 1;
      const removableIndex = cards.findIndex((item, index) => index !== newestIndex && item.type !== "source");
      const [removedCard] = cards.splice(removableIndex >= 0 ? removableIndex : 0, 1);
      sourceHints = removeSourceReferences(sourceHints, removedCard, cards);
    }
    return updateSession(current, { cards, sourceHints });
  }

  function addSource(session, input = {}, text = (key) => key) {
    const current = normalizeSession(session);
    if (!current) return null;
    const sourceCard = sourceCardFromInput(input, text);
    const sourceHints = [
      ...current.sourceHints,
      cleanText(input.sourceHint) || cleanText(input.attachmentName),
    ].filter(Boolean);
    const withHints = updateSession(current, {
      attachmentName: cleanText(input.attachmentName) || current.attachmentName,
      inputKind: input.attachmentName ? "file" : input.sourceHint ? "link" : current.inputKind,
      sourceHints: [...new Set(sourceHints)].slice(-8),
    });
    if (!sourceCard || withHints.cards.some((card) => card.id === sourceCard.id)) return withHints;
    return addCard(withHints, sourceCard);
  }

  function removeCard(session, cardId = "") {
    const current = normalizeSession(session);
    if (!current) return null;
    const targetId = cleanText(cardId);
    const removedCard = current.cards.find((item) => item.id === targetId);
    const cards = current.cards.filter((item) => item.id !== targetId);
    const sourceHints = removeSourceReferences(current.sourceHints, removedCard, cards);
    const removedReferences = new Set(sourceReferences(removedCard));
    return updateSession(current, {
      attachmentName: removedReferences.has(current.attachmentName) ? "" : current.attachmentName,
      cards,
      sourceHints,
    });
  }

  function appendTurn(session, turn = {}) {
    const current = normalizeSession(session);
    const normalizedTurn = normalizeTurn(turn);
    if (!current || !normalizedTurn) return current;
    const duplicate = current.turns.some((item) => (
      normalizedTurn.runId
        ? item.runId === normalizedTurn.runId
        : item.question === normalizedTurn.question && item.answer === normalizedTurn.answer
    ));
    return duplicate ? current : updateSession(current, { turns: [...current.turns, normalizedTurn] });
  }

  function reconcileRun(session, runs = [], options = {}) {
    const current = normalizeSession(session);
    if (!current) return null;
    const sessionEnded = current.sessionLifecycle === "ended" || current.status === "completed";
    const availableRuns = Array.isArray(runs) ? runs.filter(Boolean) : [];
    const latestRunId = cleanText(current.latestRunId);
    if (current.status !== "running" && !latestRunId && !current.clientRequestId) return null;
    const matchingRun = latestRunId
      ? availableRuns.find((run) => cleanText(run.id) === latestRunId)
      : current.clientRequestId
        ? availableRuns.find((run) => cleanText(
            run.client_request_id || run.result_envelope?.client_request_id || run.error_envelope?.client_request_id
          ) === current.clientRequestId)
        : null;
    if (matchingRun) {
      const runStatus = cleanText(matchingRun.status);
      const reconciledStatus = sessionEnded
        ? "completed"
        : ["submitted", "queued", "running"].includes(runStatus)
          ? "running"
          : runStatus === "completed"
            ? "ready"
            : "active";
      return updateSession(current, {
        draftResult: matchingRun,
        latestRunId: cleanText(matchingRun.id),
        status: reconciledStatus,
      });
    }
    const reconciliation = options.reconciliation && typeof options.reconciliation === "object" ? options.reconciliation : {};
    if (reconciliation.state === "not_found" && current.clientRequestId
      && cleanText(reconciliation.client_request_id) === current.clientRequestId) {
      const error = global.ResearchOSResultEnvelope?.errorEnvelope?.("run_reconcile_not_found", {
        client_request_id: current.clientRequestId, retryable: true, recovery_action: "retry_same",
      });
      return updateSession(current, {
        draftResult: {
          error_envelope: error, error_type: error?.error_type || "run_reconcile_not_found",
          execution_status: "failed", status: "failed", work_session_id: current.id,
        },
        latestRunId: "",
        status: sessionEnded ? "completed" : "active",
      });
    }
    const reconcileErrorTypes = {
      ambiguous: "run_reconcile_ambiguous",
      ledger_corrupt: "run_ledger_corrupt",
      ledger_unavailable: "run_ledger_unavailable",
      request_conflict: "run_request_conflict",
    };
    const reconcileErrorType = reconcileErrorTypes[cleanText(reconciliation.state)] || "";
    const reconciliationRequestId = cleanText(reconciliation.client_request_id);
    if (reconcileErrorType && (!reconciliationRequestId || reconciliationRequestId === current.clientRequestId)) {
      const error = global.ResearchOSResultEnvelope?.errorEnvelope?.(reconcileErrorType, {
        client_request_id: current.clientRequestId,
        run_id: current.latestRunId,
      });
      return updateSession(current, {
        draftResult: {
          error_envelope: error, error_type: error?.error_type || reconcileErrorType,
          execution_status: "failed", id: current.latestRunId, status: "failed", work_session_id: current.id,
        },
        latestRunId: current.latestRunId,
        status: sessionEnded ? "completed" : "active",
      });
    }
    return null;
  }

  function historyEntryFromSession(session, options = {}) {
    const current = normalizeSession(session);
    if (!current) return null;
    const result = options.result && typeof options.result === "object" ? options.result : current.draftResult || {};
    const resultAnswer = result.status === "completed" ? String(result.answer || "").trim() : "";
    const answer = String(
      result.execution_status === "copy_ready"
        ? current.intent
        : resultAnswer || current.resumeSummary || ""
    ).trim();
    const currentResultCount = resultAnswer ? 1 : (!current.resumeTurnCount && answer ? 1 : 0);
    const status = options.status
      || (current.status === "completed" ? "completed" : current.status === "ready" ? "ready" : "paused");
    return normalizeHistoryEntry({
      artifacts: [...artifactPaths(result.artifacts), ...current.resumeArtifacts],
      candidate: current.candidate,
      cards: current.cards,
      createdAt: current.historyCreatedAt || current.createdAt,
      evidenceBoundary: current.evidenceBoundary,
      enhancement: current.enhancement,
      goal: current.goal,
      id: current.historyId || current.id,
      intent: current.intent,
      portfolioBinding: current.portfolioBinding,
      responseMode: current.responseMode,
      resultSummary: answer,
      sensitivity: current.sensitivity,
      sourceHints: current.sourceHints,
      status,
      templateLanguage: current.templateLanguage,
      title: current.title,
      turnCount: current.resumeTurnCount + current.turns.length + currentResultCount,
      updatedAt: new Date().toISOString(),
    });
  }

  function upsertHistory(entries = [], session = null, options = {}) {
    const next = historyEntryFromSession(session, options);
    if (!next) return normalizeHistory(entries);
    return normalizeHistory([next, ...normalizeHistory(entries).filter((entry) => entry.id !== next.id)]);
  }

  function removeHistoryEntry(entries = [], id = "") {
    const target = cleanText(id);
    return normalizeHistory(entries).filter((entry) => entry.id !== target);
  }

  function sessionFromHistory(entry = {}) {
    const historyEntry = normalizeHistoryEntry(entry);
    if (!historyEntry) return null;
    const session = createSession({
      candidate: historyEntry.candidate,
      cards: historyEntry.cards,
      evidenceBoundary: historyEntry.evidenceBoundary,
      enhancement: historyEntry.enhancement,
      goal: historyEntry.goal,
      intent: historyEntry.intent,
      portfolioBinding: historyEntry.portfolioBinding,
      responseMode: historyEntry.responseMode,
      sensitivity: historyEntry.sensitivity,
      sourceHint: historyEntry.sourceHints[0] || "",
      templateLanguage: historyEntry.templateLanguage,
      title: historyEntry.title,
    });
    return updateSession(session, {
      cards: historyEntry.cards,
      historyCreatedAt: historyEntry.createdAt,
      historyId: historyEntry.id,
      resumeArtifacts: historyEntry.artifacts,
      resumeSummary: historyEntry.resultSummary,
      resumeTurnCount: historyEntry.turnCount,
      resumedFromId: historyEntry.id,
      sourceHints: historyEntry.sourceHints,
      status: "active",
    });
  }

  function handoffPayload(session = {}, text = (key) => key) {
    const current = normalizeSession(session);
    if (!current) return null;
    const cardLines = current.cards.map((card) => [card.typeLabel, card.title, card.path].filter(Boolean).join(": "));
    const resultForReview = String(current.draftResult?.answer || "").trim().slice(0, 6000);
    return {
      action: "work_session_handoff",
      id: `handoff:work-session:${current.id}`,
      admission_state: {
        schema_id: "researchos-admission-state-v1",
        decision_state: "proposed",
        mutation_state: "not_requested",
        validation_state: "unvalidated",
        authority_role: "none",
      },
      candidate: current.candidate,
      note: [
        `${text("workSessionGoal")}: ${current.goal}`,
        current.intent !== current.goal ? `${text("workSessionCurrentStep")}: ${current.intent}` : "",
        current.sourceHints.length ? `${text("workSessionSources")}: ${current.sourceHints.join(" | ")}` : "",
        cardLines.length ? `${text("workSessionDeck")}:\n${cardLines.join("\n")}` : "",
        resultForReview ? `${text("workSessionResultForReview")}:\n${resultForReview}` : "",
        current.evidenceBoundary ? `${text("workSessionBoundary")}: ${current.evidenceBoundary}` : "",
      ].filter(Boolean).join("\n"),
      path: current.cards.find((card) => card.path)?.path || current.sourceHints[0] || "",
      current_state: text("workSessionCurrentAuthorityState"),
      evidence_state: "candidate",
      impact_scope: text("workSessionImpactScope"),
      proposed_state: text("workSessionProposedAuthorityState"),
      sensitivity: current.sensitivity,
      source: "work-session",
      source_cards: current.cards.map((card) => ({
        id: card.id,
        path: card.path,
        title: card.title,
        type: card.type,
      })),
      title: current.title,
      type: "task",
      work_session_id: current.id,
    };
  }

  function syncHandoffStatus(session, type = "", id = "", status = "") {
    const current = normalizeSession(session);
    if (!current?.handoffKey || type !== "task" || id !== current.handoffKey) return null;
    const nextStatus = ["active", "ready", "completed"].includes(status) ? status : current.status;
    return updateSession(current, {
      handoffKey: nextStatus === "active" ? "" : current.handoffKey,
      status: nextStatus,
    });
  }

  function handoffMutationPlan(previousSession, nextSession, options = {}) {
    const previous = normalizeSession(previousSession);
    const next = normalizeSession(nextSession);
    if (!next) return { payload: null, removeKey: "", session: null };
    if (!options.handoffActive || !previous?.handoffKey) {
      return {
        payload: null,
        removeKey: "",
        session: updateSession(next, {
          handoffKey: "",
          status: previous?.status === "draft" ? "draft" : "active",
        }),
      };
    }
    const payload = handoffPayload(next, options.text);
    const nextKey = cleanText(options.itemKey?.(payload));
    if (!payload || !nextKey) {
      return {
        payload: null,
        removeKey: previous.handoffKey,
        session: updateSession(next, { handoffKey: "", status: "active" }),
      };
    }
    return {
      payload,
      removeKey: nextKey === previous.handoffKey ? "" : previous.handoffKey,
      session: updateSession(next, { handoffKey: nextKey, status: "ready" }),
    };
  }

  function read(options = {}) {
    const storage = options.storage || global.localStorage;
    if (!storage) return null;
    try {
      const key = runtimeStorageKey(options.runtimeMode);
      const raw = storage.getItem(key) || "null";
      const normalized = normalizeSession(JSON.parse(raw));
      if (normalized) {
        const migrated = JSON.stringify(normalized);
        if (migrated !== raw) storage.setItem(key, migrated);
      }
      return normalized;
    } catch {
      return null;
    }
  }

  function write(session, options = {}) {
    const storage = options.storage || global.localStorage;
    const normalized = normalizeSession(session);
    if (!storage) return normalized;
    const key = runtimeStorageKey(options.runtimeMode);
    if (!normalized) {
      try {
        storage.removeItem(key);
      } catch {
        // Clearing browser persistence must not break the in-memory task lifecycle.
      }
      return null;
    }
    try {
      storage.setItem(key, JSON.stringify(normalized));
    } catch {
      // Keep the in-memory task usable when browser persistence is unavailable.
    }
    return normalized;
  }

  function clear(options = {}) {
    const storage = options.storage || global.localStorage;
    try {
      storage?.removeItem?.(runtimeStorageKey(options.runtimeMode));
    } catch {
      // Clearing browser persistence must not break the in-memory task lifecycle.
    }
  }

  function readHistory(options = {}) {
    const storage = options.storage || global.localStorage;
    if (!storage) return [];
    try {
      const key = runtimeHistoryStorageKey(options.runtimeMode);
      const raw = storage.getItem(key) || "[]";
      const normalized = normalizeHistory(JSON.parse(raw));
      const migrated = JSON.stringify(normalized);
      if (migrated !== raw) storage.setItem(key, migrated);
      return normalized;
    } catch {
      return [];
    }
  }

  function writeHistory(entries = [], options = {}) {
    const storage = options.storage || global.localStorage;
    const normalized = normalizeHistory(entries);
    if (storage) {
      try {
        storage.setItem(runtimeHistoryStorageKey(options.runtimeMode), JSON.stringify(normalized));
      } catch {
        // Keep the in-memory history usable when browser persistence is unavailable.
      }
    }
    return normalized;
  }

  global.ResearchOSWorkSessionState = Object.freeze({
    PRIVATE_KEY,
    PRIVATE_HISTORY_KEY,
    PUBLIC_KEY,
    PUBLIC_HISTORY_KEY,
    HISTORY_LIMIT,
    VERSION,
    addCard,
    addSource,
    appendTurn,
    cardFromAssetElement,
    clear,
    createLatestRequestGate,
    createSession,
    handoffMutationPlan,
    handoffPayload,
    historyTaskIdentity,
    taskIdentityProjection,
    sessionRegistryProjection,
    isPublicDemoSession,
    lifecycleProjection,
    normalizeSession,
    newClientRequestId,
    normalizeHistory,
    portfolioBindingContextStatus,
    workItemBindingProjection,
    read,
    readHistory,
    reconcileRun,
    removeCard,
    removeHistoryEntry,
    runtimeStorageKey,
    sessionFromHistory,
    syncHandoffStatus,
    turnFromResult,
    updateSession,
    upsertHistory,
    write,
    writeHistory,
  });
})(window);
