/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 视图「unified inbox」的纯 HTML 渲染层；不保存持久状态、不直接执行写入副作用。
 * English: Pure HTML rendering layer for the unified inbox dashboard view; stores no durable state and performs no write side effects.
 */

(function attachResearchOSUnifiedInboxView(global) {
  function fallbackEncodeDataPayload(value) {
    return encodeURIComponent(String(value ?? ""));
  }

  function fallbackEmptyState(options = {}, deps = {}) {
    const emptyState = global.ResearchOSEmptyStateComponent?.renderEmptyState;
    if (emptyState) return emptyState(options, deps);
    const escape = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    return escape(options.message || "");
  }

  function fallbackPreviewButton(path = "", label = "", deps = {}) {
    const previewButton = global.ResearchOSPreviewLinksComponent?.previewButton;
    return previewButton ? previewButton(path, label, deps) : "";
  }

  function fallbackSegmentedButtons(options = [], deps = {}) {
    const renderSegmentButtons = global.ResearchOSSegmentedControlComponent?.renderSegmentButtons;
    if (!renderSegmentButtons) {
      throw new Error("ResearchOSSegmentedControlComponent.renderSegmentButtons must load before unified-inbox view rendering");
    }
    return renderSegmentButtons(options, deps);
  }

  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      emptyState: deps.emptyState || global.ResearchOSEmptyStateComponent?.renderEmptyState || fallbackEmptyState,
      encodeDataPayload: deps.encodeDataPayload || fallbackEncodeDataPayload,
      previewButton: deps.previewButton || ((path = "", label = "", options = {}) => fallbackPreviewButton(path, label, { ...deps, ...options })),
      relatedCompositionCards: deps.relatedCompositionCards || (() => []),
      segmentedButtons: deps.segmentedButtons || fallbackSegmentedButtons,
      shortText: deps.shortText || ((value, limit = 180) => {
        const text = String(value ?? "").trim();
        return text.length > limit ? `${text.slice(0, Math.max(0, limit - 1)).trim()}…` : text;
      }),
      translate: deps.translate || ((key) => key),
    };
  }

  function renderCurrentResultSummary(inbox = {}, deps = {}) {
    const { escapeHtml, shortText, translate } = normalizeDeps(deps);
    const result = inbox.currentResult && typeof inbox.currentResult === "object" ? inbox.currentResult : null;
    const identity = inbox.currentResultProjection && typeof inbox.currentResultProjection === "object"
      ? inbox.currentResultProjection
      : { state: result ? "matched" : "none", provenance: {} };
    const session = inbox.currentSession && typeof inbox.currentSession === "object" ? inbox.currentSession : null;
    const task = String(session?.goal || session?.intent || session?.title || "").trim();
    if (identity.state === "withheld") {
      const provenance = identity.provenance || {};
      const sourceIds = [
        provenance.work_session_id ? `${translate("reviewResultCurrentSessionId")}: ${provenance.work_session_id}` : "",
        provenance.observed_work_session_id ? `${translate("reviewResultObservedSessionId")}: ${provenance.observed_work_session_id}` : "",
        provenance.expected_run_id ? `${translate("reviewResultExpectedRunId")}: ${provenance.expected_run_id}` : "",
        provenance.observed_run_id ? `${translate("reviewResultObservedRunId")}: ${provenance.observed_run_id}` : "",
      ].filter(Boolean);
      return `<section class="unified-inbox-hero review-current-result is-withheld" data-review-current-result data-result-present="false" data-result-identity="withheld" data-result-withheld-reason="${escapeHtml(identity.reason || "identity_mismatch")}">
        <div>
          <span>${escapeHtml(translate("workSessionResultEyebrow"))}</span>
          <h3>${escapeHtml(translate("reviewResultWithheldTitle"))}</h3>
          ${task ? `<small>${escapeHtml(translate("reviewResultTask"))}: ${escapeHtml(shortText(task, 180))}</small>` : ""}
          <p>${escapeHtml(translate("reviewResultWithheldBody"))}</p>
          ${sourceIds.length ? `<small class="review-result-provenance">${sourceIds.map((value) => escapeHtml(value)).join(" · ")}</small>` : ""}
        </div>
      </section>`;
    }
    if (!result) {
      return `<section class="unified-inbox-hero review-current-result is-empty" data-review-current-result data-result-present="false">
        <div>
          <span>${escapeHtml(translate("workSessionResultEyebrow"))}</span>
          <h3>${escapeHtml(translate("reviewResultTitle"))}</h3>
          ${task ? `<small>${escapeHtml(translate("reviewResultTask"))}: ${escapeHtml(shortText(task, 180))}</small>` : ""}
          <p>${escapeHtml(translate(inbox.publicMode ? "reviewResultEmptyPublic" : "reviewResultEmptyPrivate"))}</p>
        </div>
      </section>`;
    }
    const answer = String(
      result.answer
      || result.output
      || result.result_envelope?.answer
      || result.error_envelope?.message
      || "",
    ).trim();
    const artifacts = [
      ...(Array.isArray(result.artifacts) ? result.artifacts : []),
      ...(Array.isArray(result.result_envelope?.artifacts) ? result.result_envelope.artifacts : []),
    ].map((item) => String(typeof item === "string" ? item : item?.path || item?.uri || "").trim()).filter(Boolean);
    return `<section class="unified-inbox-hero review-current-result" data-review-current-result data-result-present="true">
      <div>
        <span>${escapeHtml(translate("workSessionResultEyebrow"))}</span>
        <h3>${escapeHtml(translate("reviewResultTitle"))}</h3>
        ${task ? `<small>${escapeHtml(translate("reviewResultTask"))}: ${escapeHtml(shortText(task, 180))}</small>` : ""}
        ${answer ? `<p>${escapeHtml(shortText(answer.replace(/\s+/g, " "), 360))}</p>` : ""}
        ${artifacts.length ? `<p><strong>${escapeHtml(translate("reviewResultArtifacts"))}</strong>: ${artifacts.map((path) => `<code>${escapeHtml(path)}</code>`).join(" ")}</p>` : ""}
        <small>${escapeHtml(translate("reviewResultBoundary"))}</small>
      </div>
    </section>`;
  }

  function renderViewButtons(inbox = {}, deps = {}) {
    const { escapeHtml, segmentedButtons, translate } = normalizeDeps(deps);
    const options = [
      ["active", translate("unifiedInboxViewActive"), inbox.total],
      ["archived", translate("unifiedInboxViewArchived"), inbox.archivedTotal],
      ["all", translate("unifiedInboxViewAll"), inbox.allTotal],
    ].map(([view, label, count]) => ({
      count,
      countTag: "em",
      dataAttr: "data-unified-inbox-view",
      label,
      labelTag: "span",
      selected: inbox.view === view,
      value: view,
    }));
    return segmentedButtons(options, { escapeHtml });
  }

  function renderWorkFilterButtons(inbox = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const selected = String(inbox.workFilter || "active");
    const filters = ["ready", "active", "waiting", "needs_review", "done", "all"];
    return `<nav class="work-filter" data-work-filter aria-label="${escapeHtml(translate("workFilterLabel"))}">
      ${filters.map((filter) => {
        const count = filter === "all"
          ? Object.values(inbox.workStateCounts || {}).reduce((sum, value) => sum + Number(value || 0), 0)
          : Number(inbox.workStateCounts?.[filter] || 0);
        return `<button type="button" data-action-kind="navigation" data-work-filter-value="${filter}" aria-pressed="${selected === filter ? "true" : "false"}" class="${selected === filter ? "selected" : ""}"><span>${escapeHtml(translate(`workFilter_${filter}`))}</span><strong>${escapeHtml(String(count))}</strong></button>`;
      }).join("")}
    </nav>`;
  }

  function renderArchiveControlPanel(inbox = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (inbox.view !== "archived") return "";
    const hasArchived = Number(inbox.archivedTotal || 0) > 0;
    return `
      <section class="unified-inbox-resolve-panel" aria-label="${escapeHtml(translate("unifiedInboxArchiveExplainTitle"))}">
        <div>
          <strong>${escapeHtml(translate("unifiedInboxArchiveExplainTitle"))}</strong>
          <p>${escapeHtml(translate("unifiedInboxArchiveExplainBody"))}</p>
        </div>
        ${hasArchived ? `
          <div class="unified-inbox-resolve-actions">
            <button type="button" data-action-kind="preview-confirm" data-unified-inbox-restore-all-archived title="${escapeHtml(translate("unifiedInboxArchiveRestoreAllHint"))}">${escapeHtml(translate("unifiedInboxArchiveRestoreAll"))}</button>
            <button type="button" class="danger-soft" data-action-kind="preview-confirm" data-unified-inbox-resolve-archived title="${escapeHtml(translate("unifiedInboxArchiveResolveHint"))}">${escapeHtml(translate("unifiedInboxArchiveResolve"))}</button>
          </div>
        ` : ""}
      </section>
    `;
  }

  function renderSourceCards(inbox = {}, deps = {}) {
    const { escapeHtml, previewButton, translate } = normalizeDeps(deps);
    return (inbox.sourceEntries || [])
      .map((source) => {
        const hasPath = Boolean(source.path);
        return `
          <article class="unified-inbox-source source-${escapeHtml(source.key || "item")} ${source.count ? "has-items" : ""}">
            <span>${escapeHtml(source.label)}</span>
            <strong>${escapeHtml(String(source.count ?? 0))}</strong>
            <p>${escapeHtml(hasPath ? translate("unifiedInboxSourceReady") : translate("unifiedInboxBrowserOnly"))}</p>
            <footer>${hasPath ? previewButton(source.path, translate("openPreview")) : ""}</footer>
          </article>
        `;
      })
      .join("");
  }

  function candidateEvidenceLabel(value = "", translate = (key) => key) {
    const state = String(value || "").trim();
    if (state === "confirmed") return translate("unifiedInboxEvidenceConfirmed");
    if (state === "supported") return translate("unifiedInboxEvidenceSupported");
    if (state === "contradicted") return translate("unifiedInboxEvidenceContradicted");
    if (state === "bounded") return translate("unifiedInboxEvidenceBounded");
    if (state === "needs_evidence") return translate("unifiedInboxEvidenceNeedsEvidence");
    if (state === "blocked") return translate("unifiedInboxEvidenceBlocked");
    return translate("unifiedInboxEvidenceCandidate");
  }

  function candidateAdmissionLabel(value = {}, translate = (key) => key) {
    const decision = String(value.decision_state || "proposed").trim();
    const mutation = String(value.mutation_state || "not_requested").trim();
    const validation = String(value.validation_state || "unvalidated").trim();
    if (mutation === "rolled_back") return translate("unifiedInboxAuthorityReverted");
    if (mutation === "applied" && validation === "passed") return translate("unifiedInboxAuthorityValidated");
    if (mutation === "applied" || mutation === "staged") return translate("unifiedInboxAuthorityWrittenBack");
    if (decision === "accepted" || decision === "revised") return translate("unifiedInboxAuthorityApproved");
    return translate("unifiedInboxAuthorityProposed");
  }

  function candidateConfirmationLabel(value = "", translate = (key) => key) {
    const state = String(value || "").trim();
    if (state === "confirm") return translate("unifiedInboxRequireConfirm");
    if (state === "revise") return translate("unifiedInboxRequireRevise");
    if (state === "reject") return translate("unifiedInboxRequireReject");
    if (state === "archive") return translate("unifiedInboxRequireArchive");
    return translate("unifiedInboxRequireHandoff");
  }

  function renderCandidateMeta(entry = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const candidate = entry.candidate || {};
    const validation = candidate.validation || {};
    const admission = candidate.admission_state || {};
    if (!candidate.candidate_id) return "";
    return `
      <div class="unified-inbox-candidate-meta" aria-label="${escapeHtml(translate("unifiedInboxCandidateMeta"))}">
        <span data-candidate-evidence="${escapeHtml(validation.evidence_state || "candidate")}">${escapeHtml(candidateEvidenceLabel(validation.evidence_state, translate))}</span>
        <span data-candidate-admission="${escapeHtml(`${admission.decision_state || "proposed"}:${admission.mutation_state || "not_requested"}:${admission.validation_state || "unvalidated"}`)}">${escapeHtml(candidateAdmissionLabel(admission, translate))}</span>
        <span data-candidate-required="${escapeHtml(candidate.required_confirmation || "handoff_only")}">${escapeHtml(candidateConfirmationLabel(candidate.required_confirmation, translate))}</span>
      </div>
    `;
  }

  function renderAuthorityPreview(entry = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const candidate = entry.candidate || {};
    const transition = candidate.proposed_writeback || {};
    const currentState = String(transition.current_state || "").trim();
    const proposedState = String(transition.proposed_state || "").trim();
    if (!currentState && !proposedState) return "";
    const decisionRationale = String(transition.decision_rationale || "").trim();
    const impactScope = String(transition.impact_scope || "").trim();
    const rollbackRef = String(transition.rollback_ref || "").trim();
    const validationState = String(candidate.admission_state?.validation_state || transition.validation_state || "unvalidated").trim();
    return `
      <details class="unified-inbox-authority-preview">
        <summary>${escapeHtml(translate("unifiedInboxAuthorityPreview"))}</summary>
        <dl>
          <div><dt>${escapeHtml(translate("unifiedInboxAuthorityCurrent"))}</dt><dd>${escapeHtml(currentState || translate("unifiedInboxAuthorityNoChange"))}</dd></div>
          <div><dt>${escapeHtml(translate("unifiedInboxAuthorityProposedChange"))}</dt><dd>${escapeHtml(proposedState || translate("unifiedInboxAuthorityCandidateOnly"))}</dd></div>
          ${decisionRationale ? `<div><dt>${escapeHtml(translate("unifiedInboxAuthorityRationale"))}</dt><dd>${escapeHtml(decisionRationale)}</dd></div>` : ""}
          ${impactScope ? `<div><dt>${escapeHtml(translate("unifiedInboxAuthorityImpact"))}</dt><dd>${escapeHtml(impactScope)}</dd></div>` : ""}
          ${rollbackRef ? `<div><dt>${escapeHtml(translate("unifiedInboxAuthorityRollback"))}</dt><dd>${escapeHtml(rollbackRef)}</dd></div>` : ""}
          <div><dt>${escapeHtml(translate("unifiedInboxAuthorityValidation"))}</dt><dd>${escapeHtml(validationState)}</dd></div>
        </dl>
      </details>
    `;
  }

  function candidateBoundaryHint(candidate = {}, translate = (key) => key, options = {}) {
    const hasSaveTarget = Boolean(String(candidate.proposed_writeback?.save_target || "").trim());
    const sensitivity = String(candidate.sensitivity || "").trim();
    const saveTargetHint = hasSaveTarget
      ? translate("unifiedInboxSaveTargetReady")
      : translate(options.publicMode ? "unifiedInboxSaveTargetMissingPublic" : "unifiedInboxSaveTargetMissing");
    if (sensitivity === "private" || sensitivity === "internal") {
      return `${saveTargetHint} · ${translate("unifiedInboxBoundaryKeepLocal")}`;
    }
    return saveTargetHint;
  }

  function renderCandidateBoundary(entry = {}, deps = {}, options = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const candidate = entry.candidate || {};
    const saveTarget = candidate.proposed_writeback?.save_target || "";
    if (!candidate.candidate_id) return "";
    return `
      <small class="unified-inbox-candidate-boundary" data-candidate-save-target="${saveTarget ? "ready" : "missing"}" data-candidate-sensitivity="${escapeHtml(candidate.sensitivity || "internal")}">
        ${escapeHtml(candidateBoundaryHint(candidate, translate, options))}
      </small>
    `;
  }

  function renderCandidateDispositionControls(entry = {}, deps = {}, options = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const candidate = entry.candidate || {};
    const admission = candidate.admission_state || {};
    if (!candidate.candidate_id || entry.archived || options.itemLocal !== true) return "";
    if (options.publicMode === true) {
      return `<small class="item-local-review-non-effect" data-canonical-write="false">${escapeHtml(translate("itemReviewPublicNonEffect"))}</small>`;
    }
    const decision = String(admission.decision_state || "proposed").trim();
    if (["accepted", "revised", "rejected", "deferred"].includes(decision)) {
      return `<section class="item-local-review-decision is-recorded" data-item-review-decision-state="${escapeHtml(decision)}"><strong>${escapeHtml(translate(`itemReviewDecision_${decision}`))}</strong><small>${escapeHtml(translate("itemReviewDecisionRecordedNonEffect"))}</small></section>`;
    }
    const actionKey = `${entry.type || "task"}:${entry.actionId || ""}`;
    return `<section class="item-local-review-decision" aria-label="${escapeHtml(translate("itemReviewDecisionTitle"))}">
      <div><strong>${escapeHtml(translate("itemReviewDecisionTitle"))}</strong><small>${escapeHtml(translate("itemReviewDecisionHint"))}</small></div>
      <div class="item-local-review-decision-actions">
        ${["accepted", "revised", "rejected", "deferred"].map((value) => `<button type="button" data-action-kind="preview-confirm" data-item-review-decision="${escapeHtml(value)}" data-item-review-entry="${escapeHtml(actionKey)}">${escapeHtml(translate(`itemReviewDecision_${value}`))}</button>`).join("")}
      </div>
    </section>`;
  }

  function candidatePrimaryActionLabel(entry = {}, translate = (key) => key) {
    const candidate = entry.candidate || {};
    if (candidate.validation?.evidence_state === "needs_evidence") return translate("unifiedInboxHandoffEvidence");
    if (candidate.required_confirmation === "revise") return translate("unifiedInboxHandoffRevise");
    if (candidate.proposed_action?.target_agent === "asset_cartographer") return translate("unifiedInboxHandoffAsset");
    return translate("unifiedInboxHandoffSingle");
  }

  function renderCandidatePrimaryAction(entry = {}, deps = {}, options = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (!entry.actionId || entry.archived) return "";
    const runStatus = String(options.run?.status || "").trim();
    if (runStatus === "submitted" || runStatus === "queued" || runStatus === "running") {
      return `<button type="button" class="unified-inbox-handoff primary" data-action-kind="direct" disabled>${escapeHtml(runnerStatusLabel(runStatus, translate))}</button>`;
    }
    const publicMode = options.publicMode === true;
    const label = publicMode ? translate("unifiedInboxHandoffPublic") : candidatePrimaryActionLabel(entry, translate);
    const hint = publicMode ? translate("unifiedInboxHandoffPublicHint") : translate("unifiedInboxHandoffHint");
    const executionAvailable = options.executionAvailable === true;
    return `<button type="button" class="unified-inbox-handoff primary" data-action-kind="${publicMode || !executionAvailable ? "handoff" : "direct"}" data-canonical-write="${publicMode ? "false" : "candidate_only"}" data-mutation-state="not_requested" data-action-non-effect="${publicMode ? "durable_state_unchanged" : "awaiting_disposition"}" data-unified-inbox-handoff="${escapeHtml(entry.type)}:${escapeHtml(entry.actionId)}" title="${escapeHtml(hint)}">${escapeHtml(label)}</button>${publicMode ? `<small class="unified-inbox-public-action-boundary">${escapeHtml(translate("unifiedInboxPublicActionNonEffect"))}</small>` : ""}`;
  }

  function renderJudgmentReceiptAction(entry = {}, deps = {}, options = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (!options.available || !entry.judgmentReceiptEligible || !entry.actionId || entry.archived || options.runBusy) return "";
    const title = entry.displayTitle || entry.title || translate("unifiedInboxTask");
    const actionLabel = String(translate("unifiedInboxJudgmentDraftAria")).replace("{title}", title);
    return `
      <section class="unified-inbox-judgment-receipt" aria-label="${escapeHtml(actionLabel)}">
        <div>
          <strong>${escapeHtml(translate("unifiedInboxJudgmentDraftTitle"))}</strong>
          <p>${escapeHtml(translate("unifiedInboxJudgmentDraftBody"))}</p>
        </div>
        <button type="button" data-action-kind="navigation" data-unified-inbox-judgment="${escapeHtml(entry.type)}:${escapeHtml(entry.actionId)}" aria-label="${escapeHtml(actionLabel)}" title="${escapeHtml(translate("unifiedInboxJudgmentDraftHint"))}">${escapeHtml(translate("unifiedInboxJudgmentDraft"))}</button>
      </section>
    `;
  }

  function renderStateMigrationTable(deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const rows = [
      ["active + candidate", "candidate governance", "unifiedInboxStateMigrationCandidateNote"],
      ["accept / complete", "processed", "unifiedInboxStateMigrationProcessedNote"],
      ["archive / restore", "archived ⇄ active", "unifiedInboxStateMigrationArchivedNote"],
      ["resolve archived", "archived -> resolved trace", "unifiedInboxStateMigrationResolveArchivedNote"],
      ["withdraw / clear local", "withdrawn / dismissed", "unifiedInboxStateMigrationWithdrawnNote"],
      ["handoff evidence", "active + needs_evidence", "unifiedInboxStateMigrationEvidenceNote"],
    ];
    return `
      <details class="simple-detail-drawer unified-inbox-state-migration">
        <summary>
          <span>${escapeHtml(translate("unifiedInboxStateMigrationTitle"))}</span>
          <small>${escapeHtml(translate("unifiedInboxStateMigrationHint"))}</small>
        </summary>
        <div class="unified-inbox-state-flow">
          ${rows.map(([action, next, noteKey]) => `
            <article>
              <span>${escapeHtml(action)}</span>
              <strong>${escapeHtml(next)}</strong>
              <p>${escapeHtml(translate(noteKey))}</p>
            </article>
          `).join("")}
        </div>
      </details>
    `;
  }

  function entryIsAssetBasket(entry = {}) {
    const raw = entry.raw || {};
    const text = [entry.title, entry.displayTitle, entry.body, entry.displayBody, raw.title, raw.note].filter(Boolean).join("\n");
    return raw.source === "asset-card-basket"
      || Array.isArray(raw.source_cards)
      || (/^(找关系|重算关系|生成项目|生成调研|Find relations|Recompute relations|Create project|Create research task)/.test(String(entry.title || entry.displayTitle || "")) && basketLegacyPaths(text).length >= 2);
  }

  function basketEntryModes(raw = {}) {
    const modes = new Set(Array.isArray(raw.writeback_modes) ? raw.writeback_modes : []);
    if (raw.supplement_existing_cards) modes.add("supplement_existing");
    if (raw.create_composition_card) modes.add("new_composition_card");
    if (!modes.size && basketSourceCards(raw).length >= 2) modes.add("supplement_existing");
    return modes;
  }

  function basketLegacyPaths(text = "") {
    const pattern = /\b((?:00_identity|01_knowledge|02_decisions|03_cognition|04_people|05_workflows|06_active_context|07_archive|08_public|09_templates|distilled)\/[^\s`),\]}]+?\.md)\b/g;
    const seen = new Set();
    const paths = [];
    let match;
    while ((match = pattern.exec(String(text || ""))) && paths.length < 24) {
      const path = String(match[1] || "").trim();
      if (!path || seen.has(path)) continue;
      seen.add(path);
      paths.push(path);
    }
    return paths;
  }

  function basketSourceCards(raw = {}) {
    const structuredCards = Array.isArray(raw.source_cards) ? raw.source_cards : [];
    const legacyCards = structuredCards.length ? [] : basketLegacyPaths([raw.title, raw.note, raw.body].filter(Boolean).join("\n"))
      .map((path) => ({
        path,
        title: path.split("/").filter(Boolean).pop()?.replace(/\.md$/i, "").replaceAll("-", " ").replaceAll("_", " ") || path,
        type: path.startsWith("04_people/") ? "person" : "asset",
        type_label: "",
      }));
    return [...structuredCards, ...legacyCards]
      .map((card = {}) => ({
        path: String(card.path || "").trim(),
        title: String(card.title || card.path || "").trim(),
        type_label: String(card.type_label || card.type || "").trim(),
      }))
      .filter((card) => card.title || card.path)
      .slice(0, 24);
  }

  function renderBasketPreview(entry = {}, deps = {}) {
    if (!entryIsAssetBasket(entry)) return "";
    const { encodeDataPayload, escapeHtml, previewButton, relatedCompositionCards, shortText, translate } = normalizeDeps(deps);
    const raw = entry.raw || {};
    const basketRaw = {
      ...raw,
      body: entry.body || entry.displayBody || raw.body || "",
      note: raw.note || entry.body || entry.displayBody || "",
      title: raw.title || entry.title || entry.displayTitle || "",
    };
    const modes = basketEntryModes(basketRaw);
    const cards = basketSourceCards(basketRaw);
    const compositionCards = relatedCompositionCards(cards).slice(0, 6);
    if (!cards.length || !modes.size) return "";
    const paths = [...new Set([
      ...cards.map((card) => card.path).filter(Boolean),
      ...compositionCards.map((card) => card.path).filter(Boolean),
    ])];
    const encodedPaths = encodeDataPayload(JSON.stringify(paths));
    const countLabel = String(translate("unifiedInboxBasketCardCount")).replace("{count}", String(cards.length + compositionCards.length));
    const cardButtons = cards
      .filter((card) => card.path)
      .slice(0, 5)
      .map((card) => previewButton(card.path, shortText(card.title || card.path, 34)))
      .join("");
    return `
      <section class="unified-inbox-basket-preview" aria-label="${escapeHtml(translate("unifiedInboxBasketPreviewTitle"))}">
        <header>
          <span>${escapeHtml(translate("unifiedInboxBasketPreviewTitle"))}</span>
          <small>${escapeHtml(countLabel)}</small>
        </header>
        ${modes.has("new_composition_card") ? `
          <article class="new-card">
            <strong>${escapeHtml(translate("unifiedInboxBasketNewCard"))}</strong>
            <p>${escapeHtml(compositionCards.length ? translate("unifiedInboxBasketExistingNewCardHint") : translate("unifiedInboxBasketNewCardHint"))}</p>
            ${compositionCards.length ? `<footer>${compositionCards.map((card) => previewButton(card.path, shortText(card.title || card.path, 36))).join("")}</footer>` : ""}
          </article>
        ` : ""}
        ${modes.has("supplement_existing") ? `
          <article class="supplement-cards">
            <div>
              <strong>${escapeHtml(translate("unifiedInboxBasketSupplement"))}</strong>
              <p>${escapeHtml(translate("unifiedInboxBasketSupplementHint"))}</p>
            </div>
            ${paths.length ? `<button type="button" data-action-kind="navigation" data-unified-inbox-preview-cards="${escapeHtml(encodedPaths)}">${escapeHtml(translate("unifiedInboxBasketOpenAll"))}</button>` : ""}
            ${cardButtons ? `<footer>${cardButtons}</footer>` : ""}
          </article>
        ` : ""}
      </section>
    `;
  }

  function renderEntryCards(inbox = {}, deps = {}) {
    const { escapeHtml, previewButton, shortText, translate } = normalizeDeps(deps);
    const entries = inbox.entries || [];
    const visibleLimit = Number.isFinite(Number(inbox.visibleLimit)) ? Number(inbox.visibleLimit) : 6;
      const renderOne = (entry) => {
        const entryRun = latestRunForEntry(entry, inbox.codexRuns || []);
        const runBusy = ["queued", "running"].includes(String(entryRun?.status || ""));
        const isWorkSession = entry.raw?.source === "work-session";
        const workSessionCards = isWorkSession ? basketSourceCards(entry.raw) : [];
        const workSessionCountKey = workSessionCards.length === 1 ? "workSessionDeckCountOne" : "workSessionDeckCount";
        const workSessionCount = String(translate(workSessionCountKey)).replace("{count}", String(workSessionCards.length));
        const workSessionCardTitles = workSessionCards.slice(0, 3).map((card) => card.title).filter(Boolean).join(" · ");
        const primaryTitle = entry.displayTitle || entry.title || entry.typeLabel || translate("unifiedInboxTask");
        const primaryBody = shortText(entry.candidate?.summary || entry.displayBody || entry.body || "", 150);
        const compactBody = String(primaryBody || "").trim();
        const titleText = String(primaryTitle || "").trim();
        const bodyLooksDuplicated = compactBody && titleText && compactBody.toLowerCase().startsWith(titleText.toLowerCase());
        const technicalDetails = !entry.archived && (entry.sourcePath || entry.actionId) ? `
          <details class="unified-inbox-item-technical">
            <summary>${escapeHtml(translate("unifiedInboxTechnicalDetails"))}</summary>
            <div>
              ${entry.sourcePath ? previewButton(entry.sourcePath, translate("unifiedInboxSource")) : ""}
              ${entry.actionId ? `<code>${escapeHtml(entry.actionId)}</code>` : ""}
            </div>
          </details>
        ` : "";
        return `
          <article class="unified-inbox-item ${escapeHtml(entry.type)} ${entry.archived ? "archived" : ""}" data-unified-entry-type="${escapeHtml(entry.type)}" data-unified-entry-id="${escapeHtml(entry.actionId || "")}">
            <div class="unified-inbox-item-main">
              <header>
                <span>${escapeHtml(isWorkSession ? translate("workSessionHandoffCardLabel") : entry.typeLabel)}</span>
                <em>${escapeHtml(entry.archived ? translate("unifiedInboxArchivedStatus") : entry.statusLabel || entry.status || "")}</em>
              </header>
              <strong>${escapeHtml(primaryTitle)}</strong>
              ${compactBody && !bodyLooksDuplicated ? `<p>${escapeHtml(compactBody)}</p>` : ""}
              ${isWorkSession ? `<small class="unified-inbox-item-meta">${escapeHtml(`${translate("workSessionDeck")} · ${workSessionCount}${workSessionCardTitles ? ` · ${workSessionCardTitles}` : ""}`)}</small>` : ""}
              ${renderCandidateMeta(entry, deps)}
              ${renderCandidateBoundary(entry, deps, { publicMode: inbox.publicMode === true })}
              ${renderAuthorityPreview(entry, deps)}
              ${inbox.itemLocal ? "" : renderJudgmentReceiptAction(entry, deps, {
                available: inbox.judgmentCalibrationAvailable === true,
                runBusy,
              })}
              ${entry.displayMeta ? `<small class="unified-inbox-item-meta">${escapeHtml(entry.displayMeta)}</small>` : ""}
              ${renderBasketPreview(entry, deps)}
              ${renderEntryRunStatus(entry, entryRun, deps)}
              ${technicalDetails}
            </div>
            <footer class="unified-inbox-item-actions">
              ${entry.path ? previewButton(entry.path, translate("openPreview")) : ""}
              ${inbox.itemLocal ? renderCandidateDispositionControls(entry, deps, { itemLocal: true, publicMode: inbox.publicMode === true }) : `
                ${renderCandidatePrimaryAction(entry, deps, { executionAvailable: inbox.codexRunnerEnabled === true, publicMode: inbox.publicMode === true, run: entryRun })}
                ${entry.actionId && !entry.archived && !runBusy ? `<button type="button" class="unified-inbox-archive" data-action-kind="preview-confirm" data-unified-inbox-archive="${escapeHtml(entry.type)}:${escapeHtml(entry.actionId)}" title="${escapeHtml(translate("unifiedInboxArchiveHint"))}">${escapeHtml(translate("unifiedInboxArchive"))}</button>` : ""}
                ${entry.actionId && entry.archived ? `<button type="button" class="unified-inbox-restore" data-action-kind="preview-confirm" data-unified-inbox-restore="${escapeHtml(entry.type)}:${escapeHtml(entry.actionId)}" title="${escapeHtml(translate("unifiedInboxRestoreHint"))}">${escapeHtml(translate("unifiedInboxRestore"))}</button>` : ""}
                ${entry.actionId && !entry.archived && !runBusy ? `<button type="button" class="unified-inbox-withdraw" data-action-kind="preview-confirm" data-unified-inbox-withdraw="${escapeHtml(entry.type)}:${escapeHtml(entry.actionId)}" title="${escapeHtml(translate("unifiedInboxWithdrawHint"))}">${escapeHtml(translate("unifiedInboxWithdraw"))}</button>` : ""}
              `}
            </footer>
          </article>
        `;
      };
    const primaryEntries = entries.slice(0, visibleLimit);
    const foldedEntries = entries.slice(visibleLimit);
    const primaryHtml = primaryEntries.map(renderOne).join("");
    if (!foldedEntries.length) return primaryHtml;
    return `
      ${primaryHtml}
      <details class="unified-inbox-more">
        <summary>
          <span>${escapeHtml(String(translate("unifiedInboxMoreEntries")).replace("{count}", String(foldedEntries.length)))}</span>
          <small>${escapeHtml(translate("unifiedInboxMoreEntriesHint"))}</small>
        </summary>
        <div>${foldedEntries.map(renderOne).join("")}</div>
      </details>
    `;
  }

  function compactRunnerTime(value = "") {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value).replace("T", " ").slice(0, 19);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  function runnerStatusLabel(status = "", translate = (key) => key) {
    const normalized = String(status || "").trim();
    if (normalized === "queued") return translate("unifiedInboxRunnerStatusQueued");
    if (normalized === "running") return translate("unifiedInboxRunnerStatusRunning");
    if (normalized === "completed") return translate("unifiedInboxRunnerStatusCompleted");
    if (normalized === "failed") return translate("unifiedInboxRunnerStatusFailed");
    return translate("unifiedInboxRunnerStatusUnknown");
  }

  function latestRunForEntry(entry = {}, runs = []) {
    const actionKey = entry.actionId ? `${entry.type}:${entry.actionId}` : "";
    if (!actionKey) return null;
    return [...runs]
      .filter((run) => run.task_mode === "direct_execution" && run.action_key === actionKey)
      .sort((left, right) => runnerTimeValue(right.updated_at || right.started_at || right.created_at) - runnerTimeValue(left.updated_at || left.started_at || left.created_at))[0] || null;
  }

  function renderEntryRunStatus(entry = {}, run = null, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (!run || entry.archived) return "";
    const status = String(run.status || "unknown").trim();
    const index = run.queue_index || "";
    const total = run.queue_total || "";
    const queuePosition = index && total ? `${translate("unifiedInboxRunnerQueueItem")} ${index}/${total}` : "";
    const updatedAt = compactRunnerTime(run.updated_at || run.started_at || run.created_at || "");
    return `<section class="unified-inbox-item-run-status ${escapeHtml(status)}" data-entry-run-status="${escapeHtml(status)}" aria-label="${escapeHtml(translate("unifiedInboxRunnerProgressTitle"))}">
      <div><span>${escapeHtml(translate("unifiedInboxRunnerProgressTitle"))}</span><strong>${escapeHtml(runnerStatusLabel(status, translate))}</strong></div>
      <small>${escapeHtml([queuePosition, updatedAt].filter(Boolean).join(" · "))}</small>
      ${status === "running" ? `<i aria-hidden="true"></i>` : ""}
    </section>`;
  }

  function runnerResolutionHint(run = {}, total = 0, translate = (key) => key) {
    const status = String(run.status || "").trim();
    const directExecution = run.task_mode === "direct_execution";
    const count = String(total || 0);
    if (status === "completed") {
      return String(translate(directExecution ? "unifiedInboxRunnerCompletedResolution" : "unifiedInboxRunnerReadOnlyCompletedResolution")).replace("{count}", count);
    }
    if (status === "failed") return translate("unifiedInboxRunnerFailedResolution");
    if (status === "submitted" || status === "queued" || status === "running") return translate("unifiedInboxRunnerRunningResolution");
    return translate("unifiedInboxRunnerUnknownResolution");
  }

  function runnerTimeValue(value = "") {
    const time = new Date(value || "").getTime();
    return Number.isFinite(time) ? time : 0;
  }

  function runnerPreviewTargets(run = {}) {
    const candidate = run.candidate || {};
    const writeback = candidate.proposed_writeback || {};
    const text = [
      run.output || "",
      writeback.save_target || "",
      writeback.object_path || "",
    ].join("\n");
    const pattern = /\b((?:00_identity|01_knowledge|02_decisions|03_cognition|04_people|05_workflows|06_active_context|07_archive|08_public|09_templates|distilled)\/[^\s`),\]}]+?\.md)(?:#([^\s`),\]}]+))?/g;
    const seen = new Set();
    const targets = [];
    let match;
    while ((match = pattern.exec(text)) && targets.length < 6) {
      const path = String(match[1] || "").trim();
      const anchor = decodeURIComponent(String(match[2] || "").trim()).replace(/[-_]+/g, " ");
      const key = `${path}#${anchor}`;
      if (!path || seen.has(key)) continue;
      seen.add(key);
      targets.push({ path, anchor });
    }
    return targets;
  }

  function runnerPreviewTargetLabel(target = {}) {
    const file = String(target.path || "").split("/").filter(Boolean).pop() || target.path || "";
    return target.anchor ? `${file} · ${target.anchor}` : file;
  }

  function fillRunnerCopy(template = "", values = {}) {
    return Object.entries(values).reduce(
      (text, [key, value]) => String(text).replaceAll(`{${key}}`, String(value ?? "")),
      String(template || "")
    );
  }

  function sortQueueRuns(runs = []) {
    return [...runs].sort((left, right) => {
      const leftIndex = Number(left.queue_index || left.current_queue_index || 9999);
      const rightIndex = Number(right.queue_index || right.current_queue_index || 9999);
      if (leftIndex !== rightIndex) return leftIndex - rightIndex;
      return runnerTimeValue(left.created_at || left.updated_at) - runnerTimeValue(right.created_at || right.updated_at);
    });
  }

  function latestRunnerQueue(runs = []) {
    const directRuns = runs.filter((run) => run.task_mode === "direct_execution");
    const parentRuns = directRuns
      .filter((run) => !run.parent_id && !run.action_key)
      .sort((left, right) => runnerTimeValue(right.created_at || right.updated_at) - runnerTimeValue(left.created_at || left.updated_at));
    const parent = parentRuns[0] || null;
    const children = parent
      ? directRuns.filter((run) => run.parent_id === parent.id)
      : directRuns.filter((run) => run.action_key);
    const orderedChildren = sortQueueRuns(children);
    const runningRun = orderedChildren.find((run) => run.status === "running") || null;
    const nextQueuedRun = orderedChildren.find((run) => run.status === "queued") || null;
    const latestChild = [...orderedChildren].sort((left, right) => runnerTimeValue(right.updated_at) - runnerTimeValue(left.updated_at))[0] || null;
    const total = Number(parent?.queue_total || orderedChildren[0]?.queue_total || orderedChildren.length || 0);
    const completed = orderedChildren.filter((run) => run.status === "completed").length;
    const failed = orderedChildren.filter((run) => run.status === "failed").length;
    const queued = orderedChildren.filter((run) => run.status === "queued").length;
    const running = orderedChildren.filter((run) => run.status === "running").length;
    const lastActivity = Math.max(
      runnerTimeValue(parent?.updated_at || ""),
      ...orderedChildren.map((run) => runnerTimeValue(run.updated_at || run.started_at || run.created_at || ""))
    );
    const stale = Boolean(queued && !running && (completed || failed) && Date.now() - lastActivity > 60000);
    return { parent, children: orderedChildren, runningRun, nextQueuedRun, latestChild, total, completed, failed, queued, running, stale };
  }

  function renderRunnerProgress(runs = [], deps = {}) {
    const { escapeHtml, shortText, translate } = normalizeDeps(deps);
    const queue = latestRunnerQueue(runs);
    if (!queue.parent && !queue.children.length) return "";
    const focusRun = queue.runningRun || queue.nextQueuedRun || queue.latestChild || queue.parent || {};
    const index = focusRun.queue_index || queue.parent?.current_queue_index || "";
    const total = queue.total || focusRun.queue_total || "";
    const action = focusRun.title || focusRun.action_title || queue.parent?.title || "";
    let stateClass = "waiting";
    let stateText = translate("unifiedInboxRunnerProgressQueued");
    if (queue.runningRun) {
      stateClass = "running";
      stateText = fillRunnerCopy(translate("unifiedInboxRunnerProgressRunning"), { index, total });
    } else if (queue.queued && queue.stale) {
      stateClass = "paused";
      stateText = fillRunnerCopy(translate("unifiedInboxRunnerProgressPaused"), { index: queue.nextQueuedRun?.queue_index || index, total });
    } else if (queue.queued) {
      stateClass = "queued";
      stateText = fillRunnerCopy(translate("unifiedInboxRunnerProgressNext"), { index: queue.nextQueuedRun?.queue_index || index, total });
    } else {
      stateClass = queue.failed ? "failed" : "completed";
      stateText = translate(queue.failed ? "unifiedInboxRunnerProgressDoneWithFailure" : "unifiedInboxRunnerProgressDone");
    }
    const counts = fillRunnerCopy(translate("unifiedInboxRunnerProgressCounts"), {
      completed: queue.completed,
      running: queue.running,
      queued: queue.queued,
      failed: queue.failed,
      total: queue.total,
    });
    return `
      <section class="unified-inbox-runner-progress ${escapeHtml(stateClass)}" aria-label="${escapeHtml(translate("unifiedInboxRunnerProgressTitle"))}">
        <div>
          <span>${escapeHtml(translate("unifiedInboxRunnerProgressTitle"))}</span>
          <strong>${escapeHtml(stateText)}</strong>
          ${action ? `<p>${escapeHtml(shortText(action, 170))}</p>` : ""}
        </div>
        <small>${escapeHtml(counts)}</small>
      </section>
    `;
  }

  function renderProviderStatus(status = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (!status || typeof status !== "object") return "";
    const provider = status.provider || status.selected_adapter || "codex";
    const model = status.model || "auto";
    const keyStatus = status.key_status || "unknown";
    const runtime = status.runtime_mode || "private vault";
    const apiMode = status.public_starter_api || "";
    const warning = status.ok === false ? (status.message_zh || status.message_en || status.error_type || "") : "";
    return `
      <div class="unified-inbox-provider-status" aria-label="${escapeHtml(translate("unifiedInboxProviderStatus"))}">
        <span>${escapeHtml(translate("unifiedInboxProviderStatus"))}</span>
        <code>${escapeHtml(provider)}</code>
        <small>${escapeHtml(translate("unifiedInboxProviderModel"))}: ${escapeHtml(model)}</small>
        <small>${escapeHtml(translate("unifiedInboxProviderKeyStatus"))}: ${escapeHtml(keyStatus)}</small>
        <small>${escapeHtml(translate("unifiedInboxProviderRuntime"))}: ${escapeHtml(runtime)}</small>
        ${apiMode ? `<small>${escapeHtml(translate("unifiedInboxProviderPublicApi"))}: ${escapeHtml(apiMode)}</small>` : ""}
        ${warning ? `<p>${escapeHtml(warning)}</p>` : ""}
      </div>
    `;
  }

  function renderRunnerCard(run = {}, deps = {}, options = {}) {
    const { escapeHtml, previewButton, shortText, translate } = normalizeDeps(deps);
    const status = String(run.status || "unknown").trim();
    const startedAt = compactRunnerTime(run.started_at || run.created_at || "");
    const finishedAt = compactRunnerTime(run.finished_at || "");
    const elapsed = Number.isFinite(Number(run.seconds || run.duration_seconds)) ? `${Math.round(Number(run.seconds || run.duration_seconds))}s` : "";
    const rawOutput = String(run.output || run.message || "").replace(/\s+/g, " ").trim();
    const output = status === "failed" || status === "completed" ? rawOutput : "";
    const completionNote = status === "completed"
      ? translate(run.task_mode === "direct_execution" ? "unifiedInboxRunnerCompletedHint" : "unifiedInboxRunnerReadOnlyCompletedHint")
      : "";
    const previewTargets = status === "completed" ? runnerPreviewTargets(run) : [];
    const queueLabel = run.queue_index && run.queue_total ? `${translate("unifiedInboxRunnerQueueItem")} ${run.queue_index}/${run.queue_total}` : "";
    const modelLabel = run.model ? `${run.model}${run.reasoning_effort ? `/${run.reasoning_effort}` : ""}` : "";
    const usage = run.usage && typeof run.usage === "object" ? run.usage : {};
    const usageLabel = Number(usage.input_tokens || 0)
      ? `${translate("unifiedInboxRunnerUsage")}: ${Number(usage.input_tokens || 0).toLocaleString()} in (${Number(usage.cached_input_tokens || 0).toLocaleString()} cached) + ${Number(usage.output_tokens || 0).toLocaleString()} out`
      : "";
    const meta = [queueLabel, modelLabel, usageLabel, startedAt, finishedAt ? `${translate("unifiedInboxRunnerFinishedAt")} ${finishedAt}` : "", elapsed].filter(Boolean).join(" · ");
    const primaryClass = options.primary ? " primary" : "";
    return `
      <article class="unified-inbox-runner-card ${escapeHtml(status)}${primaryClass}">
        <header>
          <span>${escapeHtml(runnerStatusLabel(status, translate))}</span>
          <code>${escapeHtml(shortText(run.id || "", 34))}</code>
        </header>
        <strong>${escapeHtml(run.title || translate("unifiedInboxRunnerUntitled"))}</strong>
        ${run.action_key ? `
          <details class="unified-inbox-runner-technical">
            <summary>${escapeHtml(translate("unifiedInboxRunnerTechnical"))}</summary>
            <small>${escapeHtml(shortText(run.action_key, 180))}</small>
          </details>
        ` : ""}
        ${meta ? `<small>${escapeHtml(meta)}</small>` : ""}
        ${previewTargets.length ? `
          <div class="unified-inbox-runner-targets" aria-label="${escapeHtml(translate("unifiedInboxRunnerChangedTargets"))}">
            <span>${escapeHtml(translate("unifiedInboxRunnerChangedTargets"))}</span>
            ${previewTargets.map((target) => previewButton(target.path, runnerPreviewTargetLabel(target), { anchor: target.anchor })).join("")}
          </div>
        ` : ""}
        ${output || completionNote ? `<p>${escapeHtml(shortText(output || completionNote, 180))}</p>` : ""}
      </article>
    `;
  }

  function renderRunnerLog(inbox = {}, deps = {}) {
    const { escapeHtml, previewButton, translate } = normalizeDeps(deps);
    const runs = Array.isArray(inbox.codexRuns) ? inbox.codexRuns.slice(0, 40) : [];
    const queue = latestRunnerQueue(runs);
    const latestRun = queue.runningRun || queue.nextQueuedRun || queue.latestChild || queue.parent || runs[0] || null;
    const queueRuns = queue.children.filter((run) => run.id !== latestRun?.id).slice(0, 18);
    const historyRuns = runs.filter((run) => run.id !== latestRun?.id && !queueRuns.some((item) => item.id === run.id)).slice(0, 8);
    const queueCards = queueRuns.map((run) => renderRunnerCard(run, deps, { primary: run.status === "running" })).join("");
    const historyCards = historyRuns.map((run) => renderRunnerCard(run, deps)).join("");
    const shouldOpen = Boolean(queue.failed);
    const providerStatus = renderProviderStatus(inbox.codexRunnerProviderStatus, deps);
    const showOverview = Boolean(queue.running || queue.queued || queue.failed);
    return `
      <section class="unified-inbox-runner-surface">
        ${showOverview ? `<div class="unified-inbox-runner-overview">
          ${renderRunnerProgress(runs, deps)}
          <button type="button" data-action-kind="direct" data-unified-inbox-runner-refresh title="${escapeHtml(translate("unifiedInboxRunnerRefreshHint"))}">${escapeHtml(translate("unifiedInboxRunnerRefresh"))}</button>
        </div>` : ""}
      <details class="unified-inbox-runner-log" ${shouldOpen ? "open" : ""} aria-label="${escapeHtml(translate("unifiedInboxRunnerLogTitle"))}">
        <summary>
          <div>
            <span>${escapeHtml(translate("unifiedInboxRunnerLogTitle"))}</span>
            <p>${escapeHtml(translate("unifiedInboxRunnerLogHint"))}</p>
          </div>
        </summary>
        <div class="unified-inbox-runner-details">
          ${providerStatus}
          <div class="unified-inbox-runner-result-bar">
            <p class="unified-inbox-runner-log-hint">${escapeHtml(translate("unifiedInboxRunnerLogHint"))}</p>
            ${previewButton("06_active_context/work_state/runner-logs/codex-runner-log-current.md", translate("unifiedInboxRunnerOpenLog"))}
          </div>
          ${latestRun ? `
            <div class="unified-inbox-runner-current">
              ${renderRunnerCard(latestRun, deps, { primary: true })}
              <p>${escapeHtml(runnerResolutionHint(latestRun, inbox.total, translate))}</p>
            </div>
          ` : `<p class="unified-inbox-runner-empty">${escapeHtml(translate("unifiedInboxRunnerEmpty"))}</p>`}
          ${queueCards ? `
            <section class="unified-inbox-runner-queue">
              <header>
                <span>${escapeHtml(translate("unifiedInboxRunnerQueue"))}</span>
                <small>${escapeHtml(translate("unifiedInboxRunnerQueueHint"))}</small>
              </header>
              <div class="unified-inbox-runner-list">${queueCards}</div>
            </section>
          ` : ""}
          ${historyCards ? `
            <details class="unified-inbox-runner-history">
              <summary>
                <span>${escapeHtml(translate("unifiedInboxRunnerHistory"))}</span>
                <small>${escapeHtml(String(translate("unifiedInboxRunnerHistoryHint")).replace("{count}", String(historyRuns.length)))}</small>
              </summary>
              <div class="unified-inbox-runner-list">${historyCards}</div>
            </details>
          ` : ""}
        </div>
      </details>
      </section>
    `;
  }

  function renderUnifiedInboxHtml({ inbox = {}, prompt = "", deps = {} } = {}) {
    const { emptyState, escapeHtml, encodeDataPayload, translate } = normalizeDeps(deps);
    const workFilter = String(inbox.workFilter || "active");
    const workFilterButtons = inbox.itemLocal === true ? "" : renderWorkFilterButtons(inbox, deps);
    const currentResultSummary = renderCurrentResultSummary(inbox, deps);
    const runtimeProfile = global.ResearchOSRuntimeProfileView?.render(
      inbox.codexRunnerProviderStatus?.runtime_profile, { escapeHtml, translate }
    ) || "";
    const reviewRuns = Array.isArray(inbox.codexRuns) ? inbox.codexRuns : [];
    const hasActiveRunner = reviewRuns.some((run) => ["queued", "running", "failed"].includes(String(run?.status || "")));
    const hasReviewState = [inbox.total, inbox.visibleTotal, inbox.archivedTotal, inbox.allTotal]
      .some((value) => Number(value || 0) > 0) || hasActiveRunner;
    if (inbox.itemLocal === true) {
      const localRegistry = Array.isArray(inbox.sessionRegistry) ? inbox.sessionRegistry : [];
      const registryHtml = localRegistry.length ? `<section class="item-local-session-registry" data-item-local-session-registry>${localRegistry.map((entry) => `<article><strong>${escapeHtml(entry.intent || entry.session_id)}</strong><small>${escapeHtml([entry.work_state, entry.session_id, entry.run_id].filter(Boolean).join(" · "))}</small></article>`).join("")}</section>` : "";
      const localEntries = renderEntryCards(inbox, deps);
      const localReview = `<section class="item-local-review-ledger" data-item-local-review-ledger><header><strong>${escapeHtml(translate("itemReviewCandidatesTitle"))}</strong><small>${escapeHtml(translate("itemReviewCandidatesHint"))}</small></header>${localEntries || `<p>${escapeHtml(translate("itemReviewCandidatesEmpty"))}</p>`}<output data-unified-inbox-status role="status" aria-live="polite" aria-atomic="true"></output></section>`;
      return `${currentResultSummary}${registryHtml}${localReview}${runtimeProfile}`;
    }
    if (!["needs_review", "all"].includes(workFilter)) {
      const activeRunner = workFilter === "active" && hasActiveRunner
        ? renderRunnerLog(inbox, deps)
        : "";
      return `${workFilterButtons}${activeRunner}${emptyState({
        title: translate(`workFilter_${workFilter}`),
        message: translate(`workFilter_${workFilter}Empty`),
        className: "work-filter-empty-state",
        tag: "section",
      }, { escapeHtml })}${runtimeProfile}`;
    }
    if (!hasReviewState) {
      return `${workFilterButtons}${currentResultSummary}${emptyState({
        title: translate("unifiedInboxReadyEmpty"),
        message: translate("unifiedInboxEmpty"),
        className: "unified-inbox-empty-state",
        tag: "section",
      }, { escapeHtml })}${runtimeProfile}`;
    }
    const viewButtons = renderViewButtons(inbox, deps);
    const archiveControlPanel = renderArchiveControlPanel(inbox, deps);
    const sourceCards = renderSourceCards(inbox, deps);
    const entryCards = renderEntryCards(inbox, deps);
    const runnerLog = inbox.codexRunnerEnabled === false ? "" : renderRunnerLog(inbox, deps);
    const emptyKey = inbox.view === "archived" ? "unifiedInboxArchiveEmpty" : "unifiedInboxEmpty";
    const hasPending = Number(inbox.total || 0) > 0;
    const directExecution = inbox.primaryActionKind === "direct";
    const primaryAction = directExecution
      ? `<button type="button" class="focus-action-button primary" data-action-kind="direct" data-unified-inbox-generate title="${escapeHtml(translate("unifiedInboxGenerateHint"))}" ${hasPending ? "" : "disabled"}>${escapeHtml(translate("unifiedInboxGenerate"))}</button>`
      : `<button type="button" class="focus-action-button primary" data-action-kind="handoff" data-unified-inbox-copy="${escapeHtml(encodeDataPayload(prompt))}" title="${escapeHtml(translate("unifiedInboxCopyHint"))}" ${hasPending ? "" : "disabled"}>${escapeHtml(translate("unifiedInboxCopy"))}</button>`;
    const secondaryCopy = directExecution
      ? `<button type="button" data-action-kind="handoff" data-unified-inbox-copy="${escapeHtml(encodeDataPayload(prompt))}" title="${escapeHtml(translate("unifiedInboxCopyHint"))}" ${hasPending ? "" : "disabled"}>${escapeHtml(translate("unifiedInboxCopy"))}</button>`
      : "";
    return `
      ${workFilterButtons}
      ${currentResultSummary}
      <section class="unified-inbox-hero">
        <div>
          <span>${escapeHtml(translate("unifiedInboxSubtitle"))}</span>
          <h3>${escapeHtml(translate("unifiedInboxTitle"))}</h3>
          <p>${escapeHtml(translate(inbox.codexRunnerEnabled === false ? "unifiedInboxPublicBody" : "unifiedInboxBody"))}</p>
        </div>
        <div class="unified-inbox-total">
          <strong>${escapeHtml(String(inbox.total))}</strong>
          <span>${escapeHtml(translate("unifiedInboxPending"))}</span>
        </div>
      </section>
      <section class="unified-inbox-command">
        <div class="unified-inbox-command-state">
          <strong>${escapeHtml(hasPending ? String(translate(inbox.total === 1 ? "unifiedInboxReadyCountOne" : "unifiedInboxReadyCount")).replace("{count}", String(inbox.total)) : translate("unifiedInboxReadyEmpty"))}</strong>
          <span>${escapeHtml(translate(inbox.codexRunnerEnabled === false ? "unifiedInboxPublicPrinciple" : "unifiedInboxPrinciple"))}</span>
        </div>
        <div class="unified-inbox-primary-actions">
          ${primaryAction}
          ${secondaryCopy}
        </div>
        <output data-unified-inbox-status></output>
        ${inbox.codexRunnerEnabled === false && !inbox.localActiveTotal ? "" : `
          <details class="unified-inbox-tidy-controls">
            <summary>
              <span>${escapeHtml(translate("unifiedInboxListMaintenance"))}</span>
              <small>${escapeHtml(translate("unifiedInboxListMaintenanceHint"))}</small>
            </summary>
            <div>
              ${inbox.codexRunnerEnabled === false ? "" : `<button type="button" data-action-kind="preview-confirm" data-unified-inbox-clear title="${escapeHtml(translate("unifiedInboxClearHint"))}">${escapeHtml(translate("unifiedInboxClear"))}</button>`}
              ${inbox.localActiveTotal ? `<button type="button" data-action-kind="preview-confirm" data-unified-inbox-clear-local title="${escapeHtml(translate("unifiedInboxClearLocalHint"))}">${escapeHtml(translate("unifiedInboxClearLocal"))}</button>` : ""}
            </div>
          </details>
        `}
      </section>
      ${runnerLog}
      <section class="unified-inbox-filter" aria-label="${escapeHtml(translate("unifiedInboxFilterLabel"))}">
        ${viewButtons}
      </section>
      ${archiveControlPanel}
      <section class="unified-inbox-ledger" aria-label="${escapeHtml(translate("unifiedInboxReview"))}">
        <header>
          <span>${escapeHtml(translate("unifiedInboxReview"))}</span>
          <strong>${escapeHtml(String(inbox.visibleTotal))} ${escapeHtml(translate("unifiedInboxVisible"))} · ${escapeHtml(String(inbox.total))} ${escapeHtml(translate("unifiedInboxPending"))} · ${escapeHtml(String(inbox.archivedTotal))} ${escapeHtml(translate("unifiedInboxArchivedCount"))}</strong>
        </header>
        <div class="unified-inbox-list">${entryCards || emptyState({ message: translate(emptyKey) }, { escapeHtml })}</div>
      </section>
      ${renderStateMigrationTable(deps)}
      <details class="simple-detail-drawer unified-inbox-source-drawer">
        <summary>
          <span>${escapeHtml(translate("unifiedInboxPreviewFiles"))}</span>
          <small>${escapeHtml(translate("unifiedInboxPreviewFilesHint"))}</small>
        </summary>
        <section class="unified-inbox-sources" aria-label="${escapeHtml(translate("unifiedInboxPreviewFiles"))}">
          ${sourceCards}
        </section>
      </details>
      ${runtimeProfile}
    `;
  }

  global.ResearchOSUnifiedInboxView = Object.freeze({
    renderCurrentResultSummary,
    renderWorkFilterButtons,
    renderViewButtons,
    renderSourceCards,
    renderAuthorityPreview,
    renderCandidateBoundary,
    renderCandidateDispositionControls,
    renderCandidateMeta,
    renderCandidatePrimaryAction,
    renderJudgmentReceiptAction,
    renderStateMigrationTable,
    renderArchiveControlPanel,
    renderEntryCards,
    renderRunnerLog,
    renderUnifiedInboxHtml,
  });
})(window);
