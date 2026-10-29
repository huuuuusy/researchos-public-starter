/* ResearchOS maintenance header.
 * 中文：任务状态优先 Work Session V1 的目标、页面结果、恢复摘要和按需牌组视图。
 * English: Goal, page-result, resume-summary, and optional-deck view for task-state-first Work Session V1.
 */

(function attachResearchOSWorkSessionView(global) {
  function normalizeDeps(deps = {}) {
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const previewButton = deps.previewButton || (() => "");
    const translate = deps.translate || ((key) => key);
    return {
      artifactButton: deps.artifactButton || ((path = "", label = "", options = {}) => {
        const preview = previewButton(path, label);
        if (preview) return preview;
        if (options.publicMode) return `<code class="work-session-artifact-reference">${escapeHtml(label || path)}</code>`;
        return `<button type="button" class="inline-preview-button" data-action-kind="navigation" data-work-session-open-file="${escapeHtml(path)}" title="${escapeHtml(translate("workSessionOpenArtifact"))}">${escapeHtml(label || path)}</button>`;
      }),
      encodeDataPayload: deps.encodeDataPayload || ((value) => encodeURIComponent(JSON.stringify(value || {}))),
      escapeHtml,
      markdownToHtml: deps.markdownToHtml || ((value) => `<p>${escapeHtml(value)}</p>`),
      normalizeArtifactPath: deps.normalizeArtifactPath || ((value) => String(value || "").replace(/^\.\//, "")),
      previewButton,
      translate,
    };
  }

  function lifecycleProjection(session = null, observedRun = null) {
    return global.ResearchOSWorkSessionState?.lifecycleProjection?.(session, observedRun) || {
      state: session?.status === "running" ? "running" : session?.status === "completed" ? "ended" : session ? "ready" : "no_task",
    };
  }

  function executionRoute(options = {}) {
    const derived = global.ResearchOSActionContract?.executionRoute?.({
      localExecution: options.executionAvailable === true,
      publicStarter: options.publicMode === true,
    }) || {
      actionKind: "handoff",
      effect: "copy_task",
      mode: "copy_only",
      reason: options.publicMode === true ? "public_policy" : "runner_unavailable",
      resultLocation: "external_client",
    };
    const projected = options.executionRoute;
    return projected?.mode === derived.mode
      && projected?.reason === derived.reason
      && projected?.actionKind === derived.actionKind
      && projected?.effect === derived.effect
      && projected?.resultLocation === derived.resultLocation
      ? projected
      : derived;
  }

  function markdownExcerpt(value = "", limit = 240) {
    const plain = String(value || "")
      .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
      .replace(/^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$/gm, "")
      .replace(/^#{1,6}\s+/gm, "")
      .replace(/^[-*>]\s+/gm, "")
      .replace(/```(?:[A-Za-z0-9_-]+)?|```/g, " ")
      .replace(/[*_`|]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    return plain.length > limit ? `${plain.slice(0, limit - 1).trimEnd()}…` : plain;
  }

  function resumeSummaryMarkdown(value = "") {
    const summary = String(value || "").trim();
    if (!summary || summary.includes("\n")) return summary;
    const separator = summary.match(/\|(?:\s*:?-{3,}:?\s*\|){2,6}/);
    if (!separator || separator.index == null) return summary;
    const separatorCells = separator[0].split("|").map((cell) => cell.trim()).filter(Boolean);
    const columnCount = separatorCells.length;
    if (columnCount < 2 || columnCount > 6) return summary;
    const before = summary.slice(0, separator.index).split("|").map((cell) => cell.trim());
    while (before.length && !before[before.length - 1]) before.pop();
    if (before.length < columnCount + 1) return summary;
    const headerCells = before.slice(-columnCount);
    if (headerCells.some((cell) => !cell)) return summary;
    const prose = before.slice(0, -columnCount).join(" | ").trim();
    const after = summary.slice(separator.index + separator[0].length)
      .split("|")
      .map((cell) => cell.trim());
    while (after.length && !after[0]) after.shift();
    while (after.length && !after[after.length - 1]) after.pop();
    if (after.length < columnCount) return summary;
    const rows = [];
    for (let index = 0; index + columnCount <= after.length; index += columnCount) {
      rows.push(after.slice(index, index + columnCount));
    }
    const consumed = rows.length * columnCount;
    const remainder = after.slice(consumed).filter(Boolean).join(" | ");
    return [
      prose,
      prose ? "" : "",
      `| ${headerCells.join(" | ")} |`,
      `| ${separatorCells.join(" | ")} |`,
      ...rows.map((row) => `| ${row.join(" | ")} |`),
      remainder ? `\n${remainder}` : "",
    ].filter((line, index, lines) => line || (index > 0 && lines[index - 1])).join("\n");
  }

  function renderQuickStarts(deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const items = [
      ["paper", translate("workSessionQuickPaper")],
      ["idea", translate("workSessionQuickIdea")],
      ["request", translate("workSessionQuickRequest")],
      ["today", translate("workSessionQuickToday")],
    ];
    return `<details class="work-session-examples">
      <summary>${escapeHtml(translate("workSessionExamples"))}</summary>
      <div class="work-session-quick-starts" aria-label="${escapeHtml(translate("workSessionQuickTitle"))}">
        ${items.map(([kind, label]) => `<button type="button" data-action-kind="direct" data-work-session-quick="${escapeHtml(kind)}">${escapeHtml(label)}</button>`).join("")}
      </div>
    </details>`;
  }

  function renderSourceControl(deps = {}, options = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const addSourceLabel = escapeHtml(translate("workSessionAddSource"));
    return `<details class="work-session-source-options">
      <summary aria-label="${addSourceLabel}" title="${addSourceLabel}"><b aria-hidden="true">+</b><span data-work-session-source-summary>${addSourceLabel}</span></summary>
      <div class="work-session-source-panel">
        <button type="button" class="work-session-popover-close" data-action-kind="navigation" data-work-session-popover-close title="${escapeHtml(translate("workSessionCloseSource"))}" aria-label="${escapeHtml(translate("workSessionCloseSource"))}">×</button>
        <p>${escapeHtml(translate(options.publicMode ? "workSessionAddSourceHintPublic" : "workSessionAddSourceHint"))}</p>
        <div class="work-session-input-row">
          <label class="work-session-source-field">
            <span>${escapeHtml(translate("workSessionSourceLabel"))}</span>
            <input name="source_hint" type="text" placeholder="${escapeHtml(translate("workSessionSourcePlaceholder"))}" ${options.disabled ? "disabled" : ""} />
          </label>
          <label class="work-session-file-field" data-work-session-dropzone>
            <span>${escapeHtml(translate("workSessionFileLabel"))}</span>
            <input name="source_file" type="file" ${options.disabled ? "disabled" : ""} />
            <small data-work-session-file-status>${escapeHtml(translate("workSessionFileHint"))}</small>
          </label>
        </div>
      </div>
    </details>`;
  }

  function renderComposerTools(options = {}, deps = {}) {
    return renderSourceControl(deps, {
      disabled: options.disabled,
      publicMode: options.publicMode,
    });
  }

  function renderSurfaceRoles(options = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    return `<aside class="work-session-surface-boundary" aria-label="${escapeHtml(translate("workSessionSurfaceBoundaryTitle"))}">
      <header>
        <strong>${escapeHtml(translate("workSessionSurfaceBoundaryTitle"))}</strong>
        <span>${escapeHtml(translate("workSessionSurfaceBoundaryHint"))}</span>
      </header>
      <div>
        <p><b>ResearchOS Dashboard</b><span>${escapeHtml(translate("workSessionRoleResearchOS"))}</span></p>
        <p><b>${escapeHtml(translate(options.publicMode ? "workSessionRoleExecutorPublicLabel" : "workSessionRoleCodexLabel"))}</b><span>${escapeHtml(translate(options.publicMode ? "workSessionRoleExecutorPublic" : "workSessionRoleCodex"))}</span></p>
      </div>
    </aside>`;
  }

  function renderRecentTasks(recentSessions = [], deps = {}, options = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const entries = (Array.isArray(recentSessions) ? recentSessions : []).filter(Boolean).slice(0, 10);
    if (!entries.length) return "";
    const countLabel = String(translate("workSessionRecentCount")).replace("{count}", String(entries.length));
    const cards = entries.map((entry) => {
          const sourceCount = Array.isArray(entry.sourceHints) ? entry.sourceHints.length : 0;
          const taskTitle = entry.portfolioBinding?.title || entry.title || entry.intent || translate("workSessionUntitled");
          const nextStep = String(entry.portfolioBinding?.nextStep || "").trim();
          const resultSummary = entry.resultSummary ? markdownExcerpt(entry.resultSummary) : "";
          const meta = String(translate("workSessionRecentMeta"))
            .replace("{sources}", String(sourceCount))
            .replace("{steps}", String(entry.turnCount || 0));
          return `<article class="work-session-recent-card">
            <header><span>${escapeHtml(translate(`workSessionHistoryStatus_${entry.status || "paused"}`))}</span><time>${escapeHtml(String(entry.updatedAt || "").slice(0, 10))}</time></header>
            <strong>${escapeHtml(taskTitle)}</strong>
            ${nextStep ? `<p>${escapeHtml(`${translate("nextStep")}: ${nextStep}`)}</p>` : ""}
            ${resultSummary ? `<p>${escapeHtml(resultSummary)}</p>` : ""}
            <small>${escapeHtml(meta)}</small>
            <footer>
              <button type="button" class="primary" data-action-kind="navigation" data-work-session-history-resume="${escapeHtml(entry.id || "")}" aria-label="${escapeHtml(`${translate("workSessionRecentContinue")}: ${taskTitle}`)}">${escapeHtml(translate("workSessionRecentContinue"))}</button>
              <button type="button" data-action-kind="preview-confirm" data-work-session-history-delete="${escapeHtml(entry.id || "")}" aria-label="${escapeHtml(`${translate("workSessionRecentDelete")}: ${taskTitle}`)}">${escapeHtml(translate("workSessionRecentDelete"))}</button>
            </footer>
          </article>`;
        }).join("");
    if (options.embedded) return `<div class="work-session-recent-list">${cards}</div>`;
    return `<details class="work-session-recent-tasks" aria-label="${escapeHtml(translate("workSessionRecentTitle"))}">
      <summary>
        <strong>${escapeHtml(translate("workSessionRecentTitle"))}</strong>
        <span>${escapeHtml(`${countLabel} · ${translate("workSessionRecentHint")}`)}</span>
      </summary>
      <div class="work-session-recent-list">${cards}</div>
    </details>`;
  }

  function renderLauncher(options = {}, deps = {}) {
    const { executionAvailable = false, publicMode = false, recentSessions = [], resumePackets = [] } = options;
    const packetMode = executionRoute({ executionAvailable, publicMode }).mode === "copy_only";
    const { encodeDataPayload, escapeHtml, translate } = normalizeDeps(deps);
    return `
      <section class="work-session-launcher" data-work-session-launcher>
        <div class="work-session-launch-copy">
          <h3>${escapeHtml(translate("workSessionQuestion"))}</h3>
          <p>${escapeHtml(translate(packetMode ? "workSessionQuestionHintPublic" : "workSessionQuestionHint"))}</p>
        </div>
        <form class="work-session-form" data-work-session-form>
          <label class="work-session-primary-input">
            <span class="work-session-sr-only">${escapeHtml(translate("workSessionIntentLabel"))}</span>
            <textarea name="intent" rows="4" data-work-session-intent placeholder="${escapeHtml(translate("workSessionIntentPlaceholder"))}"></textarea>
          </label>
          <div class="work-session-composer-footer">
            <div class="work-session-composer-tools">
              ${renderComposerTools({ ...options, publicMode: packetMode }, deps)}
            </div>
            <output data-work-session-status role="status" aria-live="polite" aria-atomic="true"></output>
            <button type="submit" class="primary work-session-send" data-action-kind="${packetMode ? "handoff" : "direct"}">
              <span>${escapeHtml(translate(packetMode ? "workSessionPreparePacket" : "workSessionGetResult"))}</span><b aria-hidden="true">&uarr;</b>
            </button>
          </div>
        </form>
        ${renderQuickStarts(deps)}
        ${renderSurfaceRoles({ publicMode: packetMode }, deps)}
        ${renderRecentTasks(recentSessions, deps)}
        ${resumePackets.length ? `
          <details class="work-session-resume">
            <summary><strong>${escapeHtml(translate("workSessionResumeTitle"))}</strong><span>${escapeHtml(translate("workSessionResumeHint"))}</span></summary>
            <div class="work-session-resume-list">
              ${resumePackets.slice(0, 3).map((packet) => `
                <button type="button" data-action-kind="navigation" data-work-session-resume="${escapeHtml(encodeDataPayload(packet))}">
                  <span>${escapeHtml(packet.status || translate("workSessionResumeStatus"))}</span>
                  <strong>${escapeHtml(packet.title || packet.taskRunId || translate("workSessionUntitled"))}</strong>
                  <small>${escapeHtml(packet.nextResume || translate("workSessionResumeFallback"))}</small>
                </button>
              `).join("")}
            </div>
          </details>
        ` : ""}
      </section>
    `;
  }

  function renderDeck(cards = [], deps = {}, options = {}) {
    const { escapeHtml, previewButton, translate } = normalizeDeps(deps);
    if (!cards.length) {
      return `<div class="work-session-empty-deck">
        <strong>${escapeHtml(translate("workSessionDeckEmptyTitle"))}</strong>
        <span>${escapeHtml(translate("workSessionDeckEmptyHint"))}</span>
        <button type="button" data-action-kind="navigation" data-open-workspace="library">${escapeHtml(translate("workSessionOpenLibrary"))}</button>
      </div>`;
    }
    return `<div class="work-session-deck" data-work-session-deck>
      ${cards.map((card) => {
        const path = String(card.path || "");
        const label = translate("workSessionViewSource");
        const preview = /^https?:\/\//i.test(path)
          ? `<a href="${escapeHtml(path)}" data-action-kind="navigation" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`
          : path ? previewButton(path, label) : "";
        return `
        <article class="work-session-card type-${escapeHtml(card.type || "asset")}">
          <span>${escapeHtml(card.typeLabel || card.type || translate("workSessionAsset"))}</span>
          <strong>${escapeHtml(card.title || "")}</strong>
          <small>${escapeHtml(card.subtitle || card.preview || card.path || "")}</small>
          <footer>
            ${preview}
            <button type="button" data-action-kind="direct" data-work-session-remove-card="${escapeHtml(card.id || "")}" aria-label="${escapeHtml(translate(options.disabled ? "workSessionWaitForResult" : "workSessionRemoveCard"))}" ${options.disabled ? "disabled" : ""}>×</button>
          </footer>
        </article>
      `;
      }).join("")}
    </div>`;
  }

  function deckCountLabel(cards = [], translate = (key) => key) {
    const count = cards.length;
    const template = translate(count === 1 ? "workSessionDeckCountOne" : "workSessionDeckCount");
    return String(template).replace("{count}", String(count));
  }

  function artifactPath(artifact = {}) {
    return typeof artifact === "string" ? artifact : String(artifact?.path || "");
  }

  function renderArtifacts(paths = [], options = {}, deps = {}) {
    const { artifactButton, escapeHtml, normalizeArtifactPath, translate } = normalizeDeps(deps);
    const normalized = [...new Set((Array.isArray(paths) ? paths : [])
      .map(artifactPath)
      .map((path) => normalizeArtifactPath(path) || path)
      .filter(Boolean))];
    if (!normalized.length) return "";
    return `<div class="work-session-artifacts">
      <span>${escapeHtml(translate("workSessionArtifacts"))}</span>
      <div>${normalized.map((path) => artifactButton(path, path.split("/").pop() || translate("workSessionViewSource"), options)).join("")}</div>
    </div>`;
  }

  function renderResult(result = null, options = {}, deps = {}) {
    const { escapeHtml, markdownToHtml, translate } = normalizeDeps(deps);
    if (!result) {
      return `<section class="work-session-result is-empty" data-work-session-result>
        <span>${escapeHtml(translate(options.publicMode ? "workSessionPacketEyebrow" : "workSessionResultEyebrow"))}</span>
        <p>${escapeHtml(translate(options.publicMode ? "workSessionPacketEmpty" : "workSessionResultEmpty"))}</p>
      </section>`;
    }
    const contextReadOnly = options.contextReadOnly === true;
    const status = String(result.status || "unknown");
    const artifactCreationAvailable = options.artifactCreationAvailable == null
      ? options.publicMode !== true
      : options.artifactCreationAvailable === true;
    const explicitArtifacts = (Array.isArray(result.artifacts) ? result.artifacts : [])
      .map(artifactPath)
      .filter(Boolean);
    const lifecycleState = String(options.lifecycleState || "");
    const deliveryUnknown = lifecycleState === "verify_delivery" || result.execution_status === "delivery_unknown";
    const verificationRequired = deliveryUnknown || ["verify_run", "ended_with_run_tracking"].includes(lifecycleState);
    const failed = status === "failed" && !verificationRequired;
    const answer = deliveryUnknown
      ? translate("workSessionDeliveryUnknown")
      : lifecycleState === "failed_needs_impact_check"
        ? translate("workSessionImpactNeedsVerificationHint")
      : ["verify_run", "ended_with_run_tracking"].includes(lifecycleState)
        ? translate("workSessionRunNeedsVerificationHint")
      : failed
        ? String(result.error_envelope?.message || "").trim()
        : String(result.answer || "").trim();
    const artifacts = [...new Set(explicitArtifacts)];
    const resultMode = ["answer", "artifact", "writeback"].includes(options.resultMode)
      ? options.resultMode
      : ["answer", "artifact", "writeback"].includes(result.result_envelope?.result_mode)
        ? result.result_envelope.result_mode
        : ["answer", "artifact", "writeback"].includes(result.response_mode)
          ? result.response_mode
          : "answer";
    const busy = lifecycleState ? lifecycleState === "running" : status === "submitted" || status === "queued" || status === "running";
    const refresh = result.post_run_refresh && typeof result.post_run_refresh === "object"
      ? result.post_run_refresh
      : null;
    const refreshWarning = status === "completed" && refresh?.attempted && refresh.ok === false
      ? `<aside class="work-session-refresh-warning" role="alert">
          <strong>${escapeHtml(translate("workSessionProjectionRefreshFailed"))}</strong>
          <p>${escapeHtml(translate("workSessionProjectionRefreshFailedHint"))}</p>
        </aside>`
      : "";
    const statusKey = verificationRequired
      ? `workSessionLifecycle_${lifecycleState || "verify_delivery"}`
      : busy
      ? options.publicMode ? "workSessionPacketPreparing" : "workSessionResultRunning"
      : failed
        ? "workSessionResultFailed"
        : options.publicMode ? "workSessionPacketReady" : "workSessionResultReady";
    const publicPacketReady = options.publicMode && status === "completed";
    const completedArchive = Boolean(options.completedSession) && status === "completed" && !publicPacketReady;
    const answerHtml = answer ? `<article class="markdown-body work-session-result-body">${markdownToHtml(answer)}</article>` : "";
    const artifactHtml = renderArtifacts(artifacts, { publicMode: options.publicMode }, deps);
    const firstArtifact = artifacts[0] || "";
    const primaryResultAction = contextReadOnly
      ? `<button type="button" class="primary" data-action-kind="handoff" data-result-primary-action="copy_result" data-work-session-copy-result>${escapeHtml(translate(options.publicMode ? "workSessionCopyPacket" : "workSessionCopyResult"))}</button>`
      : options.publicMode
      ? `<button type="button" class="primary" data-action-kind="handoff" data-result-primary-action="copy_result" data-work-session-copy-result>${escapeHtml(translate("workSessionCopyPacket"))}</button>`
      : resultMode === "artifact" && firstArtifact
        ? `<button type="button" class="primary" data-action-kind="navigation" data-result-primary-action="open_artifact" data-work-session-open-file="${escapeHtml(firstArtifact)}" title="${escapeHtml(translate("workSessionOpenArtifact"))}">${escapeHtml(translate("workSessionOpenArtifact"))}</button>`
        : resultMode === "writeback"
          ? `<button type="button" class="primary" data-action-kind="navigation" data-result-primary-action="open_review" data-work-session-writeback title="${escapeHtml(translate("workSessionOpenReviewHint"))}">${escapeHtml(translate("workSessionOpenReview"))}</button>`
          : options.completedSession
            ? `<button type="button" class="primary" data-action-kind="handoff" data-result-primary-action="copy_result" data-work-session-copy-result>${escapeHtml(translate("workSessionCopyResult"))}</button>`
            : `<button type="button" class="primary" data-action-kind="preview-confirm" data-result-primary-action="finish_session" data-work-session-complete title="${escapeHtml(translate("workSessionEndSessionHint"))}">${escapeHtml(translate("workSessionEndSession"))}</button>`;
    const resultActionable = !lifecycleState || ["result_ready", "late_result_ready"].includes(lifecycleState);
    const resultFooter = status === "completed" && resultActionable ? contextReadOnly
      ? `<footer class="work-session-result-footer" data-result-mode="${escapeHtml(resultMode)}">
          ${primaryResultAction}
          ${options.completedSession ? "" : `<button type="button" data-action-kind="preview-confirm" data-work-session-complete title="${escapeHtml(translate("workSessionEndSessionHint"))}">${escapeHtml(translate("workSessionEndSession"))}</button>`}
        </footer>`
      : `<footer class="work-session-result-footer" data-result-mode="${escapeHtml(resultMode)}">
      ${primaryResultAction}
      ${options.publicMode && !options.completedSession ? `<button type="button" data-action-kind="preview-confirm" data-work-session-complete title="${escapeHtml(translate("workSessionEndSessionHint"))}">${escapeHtml(translate("workSessionEndSession"))}</button>` : ""}
      ${!options.publicMode && !options.completedSession && resultMode === "answer" ? `<button type="button" data-action-kind="navigation" data-work-session-add-followup title="${escapeHtml(translate("workSessionAddFollowupHint"))}">${escapeHtml(translate("workSessionAddFollowup"))}</button>` : ""}
      ${!options.publicMode && !options.completedSession && ["artifact", "writeback"].includes(resultMode) ? `<button type="button" data-action-kind="preview-confirm" data-work-session-complete title="${escapeHtml(translate("workSessionEndSessionHint"))}">${escapeHtml(translate("workSessionEndSession"))}</button>` : ""}
      ${options.publicMode || options.completedSession && resultMode === "answer" ? "" : `<button type="button" data-action-kind="handoff" data-work-session-copy-result>${escapeHtml(translate("workSessionCopyResult"))}</button>`}
      <details class="work-session-result-actions">
        <summary>${escapeHtml(translate("workSessionMoreActions"))}</summary>
        <div>
          ${options.completedSession || !artifactCreationAvailable || resultMode !== "answer" ? "" : `<button type="button" data-action-kind="direct" data-work-session-save-result>${escapeHtml(translate("workSessionSaveAsArtifact"))}</button>`}
          ${resultMode === "writeback" ? "" : `<button type="button" data-action-kind="preview-confirm" data-work-session-writeback>${escapeHtml(translate("workSessionRequestWriteback"))}</button>`}
        </div>
      </details>
    </footer>` : "";
    if (completedArchive) {
      return `
        <section class="work-session-result status-${escapeHtml(status)} is-completed-archive" data-work-session-result aria-busy="false">
          <header>
            <div>
              <span>${escapeHtml(translate("workSessionCompletedResultLabel"))}</span>
              <strong role="status" aria-live="polite" aria-atomic="true">${escapeHtml(translate("workSessionCompletedResultStatus"))}</strong>
            </div>
          </header>
          <details class="work-session-completed-result">
            <summary ${options.primaryAction === "view_late_result_receipt" ? 'data-result-primary-action="view_late_result_receipt"' : ""}><strong>${escapeHtml(translate("workSessionViewCompletedResult"))}</strong><span>${escapeHtml(translate("workSessionViewCompletedResultHint"))}</span></summary>
            <div>
              ${answerHtml}
              ${artifactHtml}
              ${refreshWarning}
              ${resultFooter}
            </div>
          </details>
        </section>
      `;
    }
    return `
      <section class="work-session-result status-${escapeHtml(status)}" data-work-session-result aria-busy="${busy ? "true" : "false"}">
        <header>
          <div>
            <span>${escapeHtml(translate(options.publicMode ? "workSessionPacketAssistant" : "workSessionCurrentResult"))}</span>
            <strong role="status" aria-live="polite" aria-atomic="true">${escapeHtml(translate(statusKey))}</strong>
          </div>
        </header>
        ${busy ? `<div class="work-session-result-progress"><i></i><span>${escapeHtml(translate(options.publicMode ? "workSessionPacketPreparingHint" : "workSessionResultRunningHint"))}</span></div>` : ""}
        ${publicPacketReady ? `<section class="work-session-public-outcome">
          <span>${escapeHtml(translate("workSessionPublicOutcomeEyebrow"))}</span>
          <strong>${escapeHtml(translate("workSessionPublicOutcomeTitle"))}</strong>
          <p>${escapeHtml(translate("workSessionPublicOutcomeBody"))}</p>
          <div>
            <small>${escapeHtml(translate("workSessionPublicOutcomeGoal"))}</small>
            <small>${escapeHtml(translate("workSessionPublicOutcomeContext"))}</small>
            <small>${escapeHtml(translate("workSessionPublicOutcomeBoundary"))}</small>
          </div>
        </section>` : ""}
        ${answer && publicPacketReady ? `<details class="work-session-packet-details">
          <summary><strong>${escapeHtml(translate("workSessionPacketDetails"))}</strong><span>${escapeHtml(translate("workSessionPacketDetailsHint"))}</span></summary>
          ${answerHtml}
        </details>` : answerHtml}
        ${artifactHtml}
        ${refreshWarning}
        ${resultFooter}
      </section>
    `;
  }

  function renderArchivedTurn(turn = {}, options = {}, deps = {}) {
    const { escapeHtml, markdownToHtml, translate } = normalizeDeps(deps);
    const artifacts = [...new Set(
      (Array.isArray(turn.artifacts) ? turn.artifacts : []).map(artifactPath).filter(Boolean)
    )];
    const isPublicPacket = turn.includeInPrompt === false;
    return `
      <article class="work-session-process-item">
        <header><span>${escapeHtml(String(translate("workSessionProcessStep")).replace("{step}", String(options.step || 1)))}</span><strong>${escapeHtml(turn.question || "")}</strong></header>
      <details class="work-session-archived-result">
        <summary>
          <strong>${escapeHtml(translate(isPublicPacket ? "workSessionPreviousPacket" : "workSessionPreviousAnswer"))}</strong>
        </summary>
        <div>
          ${turn.answer ? `<div class="markdown-body work-session-result-body">${markdownToHtml(turn.answer)}</div>` : ""}
          ${renderArtifacts(artifacts, { publicMode: options.publicMode }, deps)}
        </div>
      </details>
      </article>
    `;
  }

  function renderResumeSnapshot(session = {}, options = {}, deps = {}) {
    const { escapeHtml, markdownToHtml, translate } = normalizeDeps(deps);
    if (!session.resumeSummary && !session.resumeArtifacts?.length) return "";
    return `<section class="work-session-resume-snapshot">
      <header><span>${escapeHtml(translate("workSessionResumeSnapshot"))}</span><small>${escapeHtml(translate("workSessionResumeSnapshotHint"))}</small></header>
      ${session.resumeSummary ? `<div class="markdown-body work-session-resume-markdown">${markdownToHtml(resumeSummaryMarkdown(session.resumeSummary))}</div>` : ""}
      ${renderArtifacts(session.resumeArtifacts || [], { publicMode: options.publicMode }, deps)}
    </section>`;
  }

  function renderProcessLog(session = {}, options = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const turns = Array.isArray(session.turns) ? session.turns : [];
    if (!turns.length) return "";
    const countLabel = String(translate(turns.length === 1 ? "workSessionProcessCountOne" : "workSessionProcessCount"))
      .replace("{count}", String(turns.length));
    return `<details class="work-session-process-log">
      <summary><span>${escapeHtml(translate("workSessionProcessTitle"))}</span><small>${escapeHtml(countLabel)}</small></summary>
      <p>${escapeHtml(translate("workSessionProcessHint"))}</p>
      <div>${turns.map((turn, index) => renderArchivedTurn(turn, { ...options, step: index + 1 }, deps)).join("")}</div>
    </details>`;
  }

  function renderTaskProgress({ contextReadOnly = false, executionAvailable = false, lifecyclePresentation = null, lifecycleState = "", publicMode = false, result = null, session = null, workspaceWriteAvailable = false } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const packetMode = executionRoute({ executionAvailable, publicMode }).mode === "copy_only";
    const visibleGoal = session.title || session.goal || session.intent || "";
    const taskBrief = String(session.intent || session.goal || "").trim();
    const hasDistinctTaskBrief = taskBrief && taskBrief !== String(visibleGoal).trim();
    const completedSession = session.status === "completed";
    const showCurrentStep = !completedSession && !session.portfolioBinding?.itemId;
    const presentation = lifecyclePresentation || lifecycleProjection(session, result);
    return `<section class="work-session-task-progress" aria-label="${escapeHtml(translate(completedSession ? "workSessionCompletedResultRegion" : "workSessionConversation"))}">
      ${showCurrentStep ? `<article class="work-session-current-step">
        <span>${escapeHtml(translate("workSessionCurrentStep"))}</span>
        <p>${escapeHtml(visibleGoal)}</p>
      </article>` : ""}
      ${!completedSession && hasDistinctTaskBrief ? `<details class="work-session-task-brief">
        <summary><span>${escapeHtml(translate("workSessionTaskBrief"))}</span><small>${escapeHtml(translate("workSessionTaskBriefHint"))}</small></summary>
        <p>${escapeHtml(taskBrief)}</p>
      </details>` : ""}
      ${completedSession ? "" : renderResumeSnapshot(session, { publicMode: packetMode }, deps)}
      ${renderResult(result, {
        artifactCreationAvailable: workspaceWriteAvailable,
        completedSession,
        contextReadOnly,
        executionAvailable,
        lifecycleState: lifecycleState || presentation.state,
        primaryAction: presentation.primaryAction,
        publicMode: packetMode,
        resultMode: session.resultMode,
      }, deps)}
      ${renderProcessLog(session, { publicMode: packetMode }, deps)}
    </section>`;
  }

  function renderConversation(options = {}, deps = {}) {
    return renderTaskProgress(options, deps);
  }

  function renderExecutionPrediction(packetMode = false, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const mode = packetMode ? "Public" : "Private";
    return `<aside class="work-session-action-prediction" aria-label="${escapeHtml(translate("workSessionPredictionTitle"))}">
      <strong>${escapeHtml(translate("workSessionPredictionTitle"))}</strong>
      <p>${escapeHtml(translate(`workSessionPrediction${mode}Route`))}</p>
      <p>${escapeHtml(translate(`workSessionPrediction${mode}Effect`))}</p>
      <p>${escapeHtml(translate(`workSessionPrediction${mode}Boundary`))}</p>
      <p>${escapeHtml(translate(`workSessionPrediction${mode}Fallback`))}</p>
    </aside>`;
  }

  function renderLastSafePoint(lifecycleState = "", deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const key = lifecycleState === "verify_delivery"
      ? "workSessionSafePointDelivery"
      : ["verify_run", "ended_with_run_tracking"].includes(lifecycleState)
        ? "workSessionSafePointObserved"
        : lifecycleState === "failed_needs_impact_check"
          ? "workSessionSafePointImpact"
          : lifecycleState === "failed_retryable"
            ? "workSessionSafePointRetry"
            : "";
    if (!key) return "";
    return `<p class="work-session-last-safe-point"><strong>${escapeHtml(translate("workSessionLastSafePoint"))}</strong> ${escapeHtml(translate(key))}</p>`;
  }

  function renderActiveSession(options = {}, deps = {}) {
    const { executionAvailable = false, handoffActive = false, publicMode = false, recentSessions = [], result = null, session = null, workItemMutationAvailable = false, workspaceWriteAvailable = false } = options;
    const { escapeHtml, translate } = normalizeDeps(deps);
    const contextStatus = String(options.contextStatus || (session?.portfolioBinding?.itemId ? "unknown" : "unbound"));
    const contextReadOnly = Boolean(session?.portfolioBinding?.itemId) && contextStatus !== "current";
    if (!contextReadOnly && options.handoffAdmitSurface?.mode === "handoff_admit_candidate") {
      return global.ResearchOSHandoffAdmitSurfaceView?.render(options.handoffAdmitSurface, {
        handoffReceiptProjection: options.handoffReceiptProjection || null,
      }, { escapeHtml, translate }) || "";
    }
    const handoffReceiptHtml = global.ResearchOSHandoffReceiptView?.render(
      options.handoffReceiptProjection || null, { escapeHtml, translate },
    ) || "";
    const packetMode = executionRoute(options).mode === "copy_only";
    const presentation = lifecycleProjection(session, result);
    const lifecycleState = presentation.state;
    const resultBusy = lifecycleState === "running";
    const verificationRequired = ["verify_delivery", "verify_run", "failed_needs_impact_check", "ended_with_run_tracking"].includes(lifecycleState);
    const retryableFailure = lifecycleState === "failed_retryable";
    const resultReady = lifecycleState === "result_ready";
    const packetReady = packetMode && session.draftResult?.execution_status === "copy_ready";
    const completedSession = session.sessionLifecycle === "ended" || session.status === "completed";
    const displayTitle = session.portfolioBinding?.title || session.title || session.goal || session.intent || "";
    const boundPrivateItem = Boolean(session.portfolioBinding?.itemId) && !publicMode;
    const bindingState = options.workItemBindingState || {
      itemFound: true,
      projectOpen: true,
      stepCompleted: false,
      stepCurrent: true,
    };
    const boundProjectOpen = boundPrivateItem && bindingState.itemFound !== false && bindingState.projectOpen !== false;
    const boundStepSignatureAvailable = boundPrivateItem
      && Boolean(session.portfolioBinding?.providerId)
      && Boolean(session.portfolioBinding?.nextStep)
      && Boolean(session.portfolioBinding?.nextStepHash)
      && bindingState.stepCurrent !== false;
    const boundStepCompleted = boundStepSignatureAvailable && bindingState.stepCompleted === true;
    const boundStepAvailable = boundProjectOpen && boundStepSignatureAvailable && !boundStepCompleted && workItemMutationAvailable;
    const completeStepHintKey = boundStepCompleted
      ? "workSessionStepAlreadyCompletedHint"
      : !workItemMutationAvailable
      ? "workSessionPortfolioMutationUnavailableHint"
      : bindingState.stepCurrent === false
        ? "workSessionCompleteStepStaleHint"
      : boundStepSignatureAvailable
        ? "workSessionCompleteStepHint"
        : "workSessionCompleteStepUnavailableHint";
    const completeStepDisabled = resultBusy || !boundStepAvailable;
    const completeStepReasonKey = resultBusy ? "workSessionWaitForResult" : completeStepHintKey;
    const completeProjectDisabled = resultBusy || !workItemMutationAvailable;
    const completeProjectReasonKey = resultBusy
      ? "workSessionWaitForResult"
      : workItemMutationAvailable
        ? "workSessionCompleteProjectHint"
        : "workSessionPortfolioMutationUnavailableHint";
    const currentHistoryIdentity = global.ResearchOSWorkSessionState?.historyTaskIdentity?.(session) || "";
    const availableRecentSessions = (Array.isArray(recentSessions) ? recentSessions : []).filter((entry) => {
      if (!entry?.id || entry.id === session.id || entry.id === session.historyId) return false;
      const entryIdentity = global.ResearchOSWorkSessionState?.historyTaskIdentity?.(entry) || "";
      return !currentHistoryIdentity || !entryIdentity || entryIdentity !== currentHistoryIdentity;
    });
    const statusLabel = translate(packetReady ? "workSessionStatus_copy_ready" : `workSessionLifecycle_${lifecycleState}`);
    return `
      <section class="work-session-active" data-work-session-active data-work-session-id="${escapeHtml(session.id || "")}">
        <header>
          <div>
            <span>${escapeHtml(translate(completedSession ? "workSessionPreviousTask" : "workSessionCurrent"))}</span>
            <h3 title="${escapeHtml(displayTitle)}">${escapeHtml(displayTitle)}</h3>
          </div>
          <div class="work-session-state">
            <em>${escapeHtml(statusLabel)}</em>
            <button type="button" data-action-kind="direct" data-work-session-new class="${session.status === "completed" ? "primary" : ""}" ${resultBusy ? "disabled" : ""} title="${escapeHtml(translate(resultBusy ? "workSessionWaitForResult" : session.status === "completed" ? "workSessionStartAnother" : "workSessionNew"))}">${escapeHtml(translate(session.status === "completed" ? "workSessionStartAnother" : "workSessionNew"))}</button>
          </div>
        </header>
        ${completedSession ? `<aside class="work-session-completed-purpose">
          <strong>${escapeHtml(translate(packetReady ? "workSessionCompletedPacketPurposeTitle" : "workSessionCompletedPurposeTitle"))}</strong>
          <p>${escapeHtml(translate(packetReady ? "workSessionCompletedPacketPurposeBody" : "workSessionCompletedPurposeBody"))}</p>
        </aside>` : ""}
        ${handoffReceiptHtml}
        ${contextReadOnly ? `<aside class="work-session-context-read-only" data-work-session-context-read-only role="status">
          <strong>${escapeHtml(translate("workSessionContextReadOnlyTitle"))}</strong>
          <p>${escapeHtml(translate("workSessionContextReadOnlyBody"))}</p>
        </aside>` : ""}
        ${renderTaskProgress({ contextReadOnly, executionAvailable, lifecyclePresentation: presentation, lifecycleState, publicMode, result, session, workspaceWriteAvailable }, deps)}
        ${!contextReadOnly && verificationRequired ? `<section class="work-session-reconcile-callout">
          <strong>${escapeHtml(translate(lifecycleState === "failed_needs_impact_check" ? "workSessionImpactNeedsVerification" : "workSessionRunNeedsVerification"))}</strong>
          <p>${escapeHtml(translate(lifecycleState === "failed_needs_impact_check" ? "workSessionImpactNeedsVerificationHint" : "workSessionRunNeedsVerificationHint"))}</p>
          ${renderLastSafePoint(lifecycleState, deps)}
          <button type="button" class="primary" data-action-kind="direct" data-work-session-reconcile>${escapeHtml(translate(lifecycleState === "failed_needs_impact_check" ? "workSessionCheckEffects" : "workSessionCheckRunStatus"))}</button>
        </section>` : !contextReadOnly && retryableFailure ? `<section class="work-session-retry-callout">
          <strong>${escapeHtml(translate("workSessionLifecycle_failed_retryable"))}</strong>
          <p>${escapeHtml(translate("workSessionRetrySameHint"))}</p>
          ${renderLastSafePoint(lifecycleState, deps)}
          <button type="button" class="primary" data-action-kind="direct" data-work-session-retry>${escapeHtml(translate("workSessionRetrySame"))}</button>
        </section>` : completedSession || contextReadOnly ? "" : `<details class="work-session-continue" id="workSessionContinue">
          <summary><strong>${escapeHtml(translate("workSessionContinueTitle"))}</strong><span>${escapeHtml(translate("workSessionContinueHint"))}</span></summary>
          <form class="work-session-run-form" data-work-session-run-form>
            <label class="work-session-primary-input">
              <span class="work-session-sr-only">${escapeHtml(translate("workSessionFollowupLabel"))}</span>
              <textarea rows="2" name="intent" data-work-session-intent-edit placeholder="${escapeHtml(translate("workSessionFollowupPlaceholder"))}"></textarea>
            </label>
            <div class="work-session-composer-footer">
              <div class="work-session-composer-tools">
                ${renderComposerTools({ ...options, disabled: resultBusy || contextReadOnly, publicMode: packetMode }, deps)}
              </div>
              <output data-work-session-status role="status" aria-live="polite" aria-atomic="true"></output>
              <button type="submit" class="primary work-session-send" data-action-kind="${packetMode ? "handoff" : "direct"}" ${resultBusy ? "disabled" : ""}>
                <span>${escapeHtml(translate(packetMode ? "workSessionUpdatePacket" : "workSessionAskAgain"))}</span><b aria-hidden="true">&uarr;</b>
              </button>
            </div>
          </form>
        </details>`}
        <details class="work-session-context">
          <summary>
            <span>${escapeHtml(translate("workSessionContext"))}</span>
            <small>${escapeHtml(deckCountLabel(session.cards || [], translate))}</small>
          </summary>
          ${session.sourceHints?.length ? `<div class="work-session-sources"><span>${escapeHtml(translate("workSessionSources"))}</span>${session.sourceHints.map((source) => `<small>${escapeHtml(source)}</small>`).join("")}</div>` : ""}
          ${session.evidenceBoundary ? `<div class="work-session-boundary"><span>${escapeHtml(translate("workSessionBoundary"))}</span><p>${escapeHtml(session.evidenceBoundary)}</p></div>` : ""}
          <section class="work-session-deck-shell">
            ${renderDeck(session.cards || [], deps, { disabled: resultBusy || contextReadOnly })}
          </section>
        </details>
        ${availableRecentSessions.length ? `<details class="work-session-recent-panel">
          <summary><span>${escapeHtml(translate("workSessionRecentTitle"))}</span><small>${escapeHtml(String(translate("workSessionRecentCount")).replace("{count}", String(availableRecentSessions.length)))}</small></summary>
          <p>${escapeHtml(translate("workSessionRecentActiveHint"))}</p>
          ${renderRecentTasks(availableRecentSessions, deps, { embedded: true })}
        </details>` : ""}
        ${lifecycleState === "ready" && !contextReadOnly ? renderExecutionPrediction(packetMode, deps) : ""}
        <footer class="work-session-actions">
          <div>
            ${session.status === "completed"
              ? ""
              : `${session.status === "draft" && !contextReadOnly
                ? `<button type="button" class="primary" data-action-kind="${packetMode ? "handoff" : "direct"}" data-work-session-run-draft title="${escapeHtml(translate(packetMode ? "workSessionRunDraftPublicHint" : "workSessionRunDraftHint"))}">${escapeHtml(translate(packetMode ? "workSessionRunDraftPublic" : "workSessionRunDraft"))}</button>`
                : handoffActive && !contextReadOnly ? `<button type="button" data-action-kind="handoff" data-work-session-prepare>${escapeHtml(translate("workSessionReviewHandoff"))}</button>` : ""}
                 ${!contextReadOnly && boundPrivateItem && boundProjectOpen ? `<span class="work-session-bounded-action"><button type="button" class="primary" data-action-kind="direct" data-work-session-complete-step ${completeStepDisabled ? "disabled" : ""} ${completeStepDisabled ? 'aria-describedby="workSessionCompleteStepReason"' : ""} title="${escapeHtml(translate(completeStepReasonKey))}">${escapeHtml(translate(boundStepCompleted ? "workSessionStepAlreadyCompleted" : "workSessionCompleteStep"))}</button>${completeStepDisabled ? `<small id="workSessionCompleteStepReason" class="work-session-action-reason">${escapeHtml(translate(completeStepReasonKey))}</small>` : ""}</span>` : ""}
                 ${resultReady ? "" : `<button type="button" data-action-kind="preview-confirm" data-work-session-complete ${resultBusy ? "disabled" : ""} title="${escapeHtml(translate(resultBusy ? "workSessionWaitForResult" : verificationRequired ? "workSessionEndKeepTrackingHint" : retryableFailure || lifecycleState === "failed_needs_impact_check" ? "workSessionEndKeepReceiptHint" : "workSessionEndSessionHint"))}">${escapeHtml(translate(verificationRequired ? "workSessionEndKeepTracking" : retryableFailure || lifecycleState === "failed_needs_impact_check" ? "workSessionEndKeepReceipt" : "workSessionEndSession"))}</button>`}
                 ${!contextReadOnly && boundProjectOpen ? `<details class="work-session-project-closeout">
                   <summary>${escapeHtml(translate("workSessionCompleteProjectSummary"))}</summary>
                   <div>
                     <p>${escapeHtml(translate("workSessionCompleteProjectBody"))}</p>
                     <button type="button" data-action-kind="direct" data-work-session-complete-project ${completeProjectDisabled ? "disabled" : ""} ${completeProjectDisabled ? 'aria-describedby="workSessionCompleteProjectReason"' : ""} title="${escapeHtml(translate(completeProjectReasonKey))}">${escapeHtml(translate("workSessionCompleteProjectConfirm"))}</button>
                     ${completeProjectDisabled ? `<small id="workSessionCompleteProjectReason" class="work-session-action-reason">${escapeHtml(translate(completeProjectReasonKey))}</small>` : ""}
                   </div>
                 </details>` : ""}`}
          </div>
        </footer>
      </section>
    `;
  }

  function renderWorkSessionHtml(options = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (options.session) return renderActiveSession(options, deps);
    const launcher = `<details class="work-session-launcher-shell">
      <summary><strong>${escapeHtml(translate("workSessionLauncherSummary"))}</strong><span>${escapeHtml(translate("workSessionLauncherHint"))}</span></summary>
      ${renderLauncher(options, deps)}
    </details>`;
    if (!options.onboardingRequired) return launcher;
    return `<section class="work-session-onboarding-gate" aria-labelledby="workSessionOnboardingTitle">
      <span>${escapeHtml(translate("workSessionOnboardingEyebrow"))}</span>
      <strong id="workSessionOnboardingTitle">${escapeHtml(translate("workSessionOnboardingTitle"))}</strong>
      <p>${escapeHtml(translate("workSessionOnboardingBody"))}</p>
      <button type="button" class="primary" data-action-kind="navigation" data-open-workspace="now">${escapeHtml(translate("workSessionOnboardingAction"))}</button>
    </section>${launcher}`;
  }

  function renderLibraryContextPack({ projection = null } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (!projection?.active || projection.schema_id !== "researchos-context-pack-projection-v1") return "";
    const included = Array.isArray(projection.included) ? projection.included : [];
    const sourceRows = included.length
      ? included.map((source = {}) => {
          const label = source.title || source.path || source.id || "";
          const showPath = source.path && source.path !== label;
          const previewPath = source.preview_path || "";
          const boundary = global.ResearchOSContextPackProjection?.sourceBoundary(source, global.document?.documentElement?.lang || "zh-CN") || "";
          const sourceCopy = `${boundary ? `<small>${escapeHtml(boundary)}</small>` : ""}<span>${escapeHtml(source.type_label || source.type || "source")}</span><strong>${escapeHtml(label)}</strong>${showPath ? `<small>${escapeHtml(source.path)}</small>` : ""}`;
          const previewAttribute = /\.pdf(?:[?#].*)?$/i.test(previewPath)
            ? `data-pdf-preview-path="${escapeHtml(previewPath)}" data-pdf-preview-title="${escapeHtml(label)}"`
            : `data-preview-path="${escapeHtml(previewPath)}"`;
          return `<li data-context-source="${escapeHtml(source.id || source.path || label)}">
            ${previewPath
              ? `<button type="button" class="work-session-context-source-button" data-action-kind="navigation" ${previewAttribute} aria-label="${escapeHtml(`${translate("workSessionContextPreviewSource")}: ${label}`)}"><span class="work-session-context-source-copy">${sourceCopy}</span><span class="work-session-context-source-action">${escapeHtml(translate("workSessionContextPreviewSource"))}<span aria-hidden="true">→</span></span></button>`
              : `<div class="work-session-context-source-unavailable"><span class="work-session-context-source-copy">${sourceCopy}<em>${escapeHtml(translate("workSessionContextSourceUnavailable"))}</em></span></div>`}
          </li>`;
        }).join("")
      : `<li class="is-empty">${escapeHtml(translate("workSessionContextIncludedEmpty"))}</li>`;
    const publicCopyOnly = projection.egress?.state === "copy_only_user_controlled";
    const taskTitle = projection.task?.title || "";
    const taskGoal = projection.task?.goal || taskTitle;
    const showStepLabel = taskGoal && taskGoal !== taskTitle;
    const includedCount = String(translate("workSessionContextIncludedCount")).replace("{count}", String(included.length));
    return `<section class="work-session-context-pack" data-current-context-pack aria-labelledby="workSessionContextPackTitle">
      <header>
        <div><span>${escapeHtml(translate("workSessionLibraryEyebrow"))}</span><h3 id="workSessionContextPackTitle">${escapeHtml(translate("workSessionContextPackTitle"))}</h3><p>${escapeHtml(translate("workSessionContextPackHint"))}</p></div>
        <button type="button" class="primary" data-action-kind="navigation" data-open-item-panel="work">${escapeHtml(translate("workSessionBackToTask"))}</button>
      </header>
      <section class="work-session-context-task">
        <small>${escapeHtml(taskTitle)}</small>
        <strong>${showStepLabel ? `<span>${escapeHtml(translate("workSessionContextCurrentStep"))}</span>` : ""}${escapeHtml(taskGoal)}</strong>
      </section>
      <div class="work-session-context-summary" aria-label="${escapeHtml(translate("workSessionContextSummary"))}">
        <span><small>${escapeHtml(translate("workSessionContextIncluded"))}</small><strong>${escapeHtml(includedCount)}</strong></span>
        <span><small>${escapeHtml(translate("workSessionContextExcluded"))}</small><strong>${escapeHtml(translate("workSessionContextExcludedShort"))}</strong></span>
        <span><small>${escapeHtml(translate("workSessionContextEgress"))}</small><strong>${escapeHtml(translate(publicCopyOnly ? "workSessionContextEgressShortPublic" : "workSessionContextEgressShortPrivate"))}</strong></span>
      </div>
      <details class="work-session-context-details">
        <summary>${escapeHtml(translate("workSessionContextDetails"))}</summary>
        <div class="work-session-context-boundaries">
          <section data-context-included><h4>${escapeHtml(translate("workSessionContextIncluded"))}</h4><ul>${sourceRows}</ul></section>
          <section data-context-excluded><h4>${escapeHtml(translate("workSessionContextExcluded"))}</h4><p>${escapeHtml(translate("workSessionContextExcludedBody"))}</p></section>
          <section data-context-egress data-egress-state="${escapeHtml(projection.egress?.state || "not_granted_by_library")}"><h4>${escapeHtml(translate("workSessionContextEgress"))}</h4><p>${escapeHtml(translate(publicCopyOnly ? "workSessionContextEgressPublic" : "workSessionContextEgressPrivate"))}</p></section>
        </div>
        ${projection.boundary ? `<details class="work-session-context-boundary"><summary>${escapeHtml(translate("workSessionContextBoundary"))}</summary><p>${escapeHtml(projection.boundary)}</p></details>` : ""}
      </details>
    </section>`;
  }

  function renderLibraryContextMismatch({ currentTask = {}, selectedItems = [] } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const selectedTitles = (Array.isArray(selectedItems) ? selectedItems : [])
      .map((item = {}) => item.title || item.id || "")
      .filter(Boolean)
      .join(" / ");
    const body = String(translate("workSessionContextLensMismatchBody"))
      .replace("{current}", currentTask.title || currentTask.item_id || translate("workSessionContextUnboundTask"))
      .replace("{selected}", selectedTitles || translate("workSessionContextUnboundTask"));
    return `<section class="work-session-context-pack work-session-context-mismatch" data-context-lens-mismatch role="status">
      <header><div><span>${escapeHtml(translate("workSessionLibraryEyebrow"))}</span><h3>${escapeHtml(translate("workSessionContextLensMismatchTitle"))}</h3><p>${escapeHtml(body)}</p></div></header>
      <p>${escapeHtml(translate("workSessionContextLensMismatchNext"))}</p>
    </section>`;
  }

  function renderItemLauncher({ item = {} } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (!item?.id) return "";
    return `<section class="work-session-item-launcher" data-item-work-session-launcher="${escapeHtml(item.id)}">
      <header><span>${escapeHtml(translate("workSessionItemLauncherEyebrow"))}</span><h3>${escapeHtml(item.title || item.id)}</h3></header>
      <section><small>${escapeHtml(translate("workSessionItemLauncherNext"))}</small><strong>${escapeHtml(item.nextStep || item.next_step || translate("workSessionItemLauncherNoStep"))}</strong></section>
      <p>${escapeHtml(translate("workSessionItemLauncherBoundary"))}</p>
      <button type="button" class="primary" data-action-kind="direct" data-start-item-work-session="${escapeHtml(item.id)}">${escapeHtml(translate("workSessionItemLauncherAction"))}</button>
    </section>`;
  }

  global.ResearchOSWorkSessionView = Object.freeze({
    renderActiveSession,
    renderArchivedTurn,
    renderConversation,
    renderDeck,
    renderLauncher,
    renderLibraryContextPack,
    renderLibraryContextMismatch,
    renderItemLauncher,
    renderQuickStarts,
    renderRecentTasks,
    renderSourceControl,
    renderResult,
    renderSurfaceRoles,
    renderTaskProgress,
    renderWorkSessionHtml,
  });
})(window);
