/* ResearchOS maintenance header.
 * 中文：任务状态优先 Work Session V1 的生命周期、恢复摘要和交互状态 owner。
 * English: Lifecycle, resume-summary, and interaction-state owner for task-state-first Work Session V1.
 */

(function attachResearchOSWorkSessionWorkbench(global) {
  function createWorkSessionLifecycle(options = {}, deps = {}) {
    const state = deps.state || global.ResearchOSWorkSessionState;
    const router = deps.router || global.ResearchOSWorkSessionRouter;
    const itemKey = deps.itemKey || global.ResearchOSDoingBoardState?.itemKey || (() => "");
    const inboxStatusIsActive = deps.inboxStatusIsActive || (() => false);
    const translate = deps.translate || ((key) => key);
    const getSession = options.getSession || (() => null);
    const saveSession = options.saveSession || ((session) => session);
    const refreshSurfaces = options.refreshSurfaces || (() => {});
    const showStatus = (key) => options.showStatus?.(translate(key));
    let workItemMutationRunning = false;
    const executionAvailable = () => options.executionAvailable
      ? options.executionAvailable() !== false
      : !options.publicMode?.();

    function lifecycleProjection(session = getSession()) {
      return state.lifecycleProjection?.(session, options.getResult?.() || null) || {
        state: session?.status === "running" ? "running" : session ? "ready" : "no_task",
      };
    }

    function sessionBusy(session = getSession()) {
      return lifecycleProjection(session).state === "running";
    }

    function busyResult() {
      showStatus("workSessionWaitForResult");
      return { busy: true, ok: false };
    }

    function archiveCurrentSession(session = getSession(), status = "paused") {
      if (!session || !state.upsertHistory) return options.getHistory?.() || [];
      const history = state.upsertHistory(options.getHistory?.() || [], session, {
        result: options.getResult?.() || session.draftResult,
        status,
      });
      options.saveHistory?.(history);
      return history;
    }

    function creationDefaults() {
      return {
        evidenceBoundary: translate(options.publicMode?.()
          ? "workSessionDefaultBoundaryPublic"
          : "workSessionDefaultBoundaryPrivate"),
        sensitivity: "internal",
        templateLanguage: options.templateLanguage?.() || "",
        text: translate,
      };
    }

    function createSession(input = {}, fallbackKey = "workSessionQuick_paper") {
      const intent = String(input.intent || input.title || translate(fallbackKey)).trim();
      const defaults = creationDefaults();
      return state.createSession({
        ...defaults,
        ...input,
        intent,
        responseMode: input.responseMode || "auto",
        sourceHint: input.sourceHint || input.path,
        title: input.title || intent,
      });
    }

    function ensure(input = {}) {
      const current = getSession();
      return current || saveSession(createSession(input));
    }

    function handoffActive(session = getSession()) {
      if (session?.status !== "ready" || !session.handoffKey) return false;
      return (options.getDoingItems?.() || []).some((item) => (
        itemKey(item) === session.handoffKey &&
        inboxStatusIsActive(item.status || "local", true)
      ));
    }

    function syncHandoffStatus(type = "", id = "", status = "") {
      const synced = state.syncHandoffStatus(getSession(), type, id, status);
      return synced ? saveSession(synced) : null;
    }

    function applyMutation(nextSession) {
      const plan = state.handoffMutationPlan(getSession(), nextSession, {
        handoffActive: handoffActive(),
        itemKey,
        text: translate,
      });
      if (plan.removeKey) options.removeDoingItem?.(plan.removeKey);
      if (plan.payload) options.addDoingItem?.(plan.payload, "local");
      return saveSession(plan.session);
    }

    function finalizeCurrentSession(current) {
      if (handoffActive(current)) {
        const result = options.archiveHandoff?.("task", current.handoffKey);
        archiveCurrentSession(getSession() || current, "completed");
        return result;
      }
      const session = saveSession(state.updateSession(current, { status: "completed" }));
      archiveCurrentSession(session, "completed");
      options.renderHome?.();
      showStatus("workSessionCompleted");
      return session;
    }

    function completeBoundWorkItemStep(current) {
      if (workItemMutationRunning) {
        showStatus("workSessionPortfolioMutationRunning");
        return Promise.resolve({ busy: true, ok: false });
      }
      workItemMutationRunning = true;
      showStatus("workSessionStepCompleting");
      return Promise.resolve(options.completeWorkItemStep?.(current)).then((result) => {
        if (!result?.ok) {
          showStatus("workSessionStepCompleteFailed");
          return result || { ok: false };
        }
        refreshSurfaces();
        showStatus("workSessionStepCompleted");
        return { ...result, session: getSession() || current };
      }).finally(() => { workItemMutationRunning = false; });
    }

    function completeBoundWorkItemProject(current) {
      if (workItemMutationRunning) {
        showStatus("workSessionPortfolioMutationRunning");
        return Promise.resolve({ busy: true, ok: false });
      }
      workItemMutationRunning = true;
      showStatus("workSessionProjectCompleting");
      return Promise.resolve(options.completeWorkItemProject?.(current)).then((result) => {
        if (!result?.ok) {
          showStatus("workSessionProjectCompleteFailed");
          return result || { ok: false };
        }
        refreshSurfaces();
        showStatus("workSessionProjectCompleted");
        return { ...result, session: getSession() || current };
      }).finally(() => { workItemMutationRunning = false; });
    }

    function addCard(card = {}) {
      const current = getSession();
      if (!current) return null;
      if (sessionBusy(current)) return busyResult();
      const session = applyMutation(state.addCard(current, card));
      refreshSurfaces();
      return session;
    }

    function prepareHandoff() {
      const current = getSession();
      if (!current) return null;
      if (sessionBusy(current)) return busyResult();
      if (handoffActive(current)) {
        options.openItemPanel?.("review");
        options.scheduleInboxStatus?.(translate("workSessionReviewHandoffReady"));
        return current;
      }
      const payload = state.handoffPayload(current, translate);
      if (!payload) return null;
      options.addDoingItem?.(payload, "local");
      const session = saveSession(state.updateSession(current, {
        handoffKey: itemKey(payload),
        status: "ready",
      }));
      refreshSurfaces();
      options.openItemPanel?.("review");
      options.scheduleInboxStatus?.(translate("workSessionHandoffReady"));
      return session;
    }

    async function runSession(session = getSession(), runOptions = {}) {
      if (!session) return { ok: false };
      if (sessionBusy(session)) return busyResult();
      const presentation = lifecycleProjection(session);
      if (["verify_delivery", "verify_run", "failed_needs_impact_check", "ended_with_run_tracking", "invalid"].includes(presentation.state)) {
        showStatus("workSessionRunNeedsVerification");
        return await options.reconcileSession?.(session) || {
          ok: false,
          error_type: session.draftResult?.error_envelope?.error_type || session.draftResult?.error_type || "run_status_unverified",
          error_envelope: session.draftResult?.error_envelope || null,
          retryable: false,
        };
      }
      const reviewWasActive = handoffActive(session);
      if (reviewWasActive) options.removeDoingItem?.(session.handoffKey);
      const reopenedSession = state.updateSession(session, {
        handoffKey: "",
        status: "active",
      });
      const currentResult = options.getResult?.() || null;
      const archivedTurn = state.turnFromResult?.(reopenedSession.intent, currentResult);
      const archivedSession = archivedTurn ? state.appendTurn(reopenedSession, archivedTurn) : reopenedSession;
      const threadedSession = state.addSource?.(archivedSession, {
        attachmentName: runOptions.attachmentName,
        sourceHint: runOptions.sourceHint,
      }, translate) || archivedSession;
      const nextIntent = String(
        runOptions.intent || (runOptions.artifactFromResult ? translate("workSessionArtifactTurn") : threadedSession.intent)
      ).trim();
      const responseMode = router?.inferResponseMode?.(
        nextIntent,
        runOptions.responseMode || threadedSession.responseMode || "auto"
      ) || "answer";
      const retrySame = session.draftResult?.error_envelope?.retryable === true
        && session.draftResult?.error_envelope?.side_effects === "none";
      const nextSession = saveSession(state.updateSession(threadedSession, {
        clientRequestId: retrySame && threadedSession.clientRequestId
          ? threadedSession.clientRequestId : state.newClientRequestId?.(),
        draftResult: {
          response_mode: responseMode,
          status: "running",
          work_session_id: threadedSession.id,
        },
        intent: nextIntent,
        latestRunId: "",
        responseMode,
        status: "running",
      }));
      refreshSurfaces();
      showStatus(executionAvailable() ? "workSessionRunning" : "workSessionPreparingPacket");
      let result;
      try {
        result = await options.submitSession?.(nextSession, {
          artifactFromResult: Boolean(runOptions.artifactFromResult),
          promptSuffix: runOptions.promptSuffix || "",
          responseMode,
        });
      } catch {
        result = global.ResearchOSResultEnvelope.failureResult("submit_rejected", {
          client_request_id: nextSession.clientRequestId,
          response_mode: responseMode, work_session_id: nextSession.id,
        });
      }
      if (!result?.ok) {
        saveSession(state.updateSession(getSession() || nextSession, {
          draftResult: result?.persistResult && result?.run ? result.run : null,
          latestRunId: result?.run?.id || "",
          status: "active",
        }));
        refreshSurfaces();
        showStatus(result?.cancelled ? "workSessionRunCancelled" : "workSessionRunFailed");
        return result || { ok: false };
      }
      const run = result.run || {};
      saveSession(state.updateSession(getSession() || nextSession, {
        draftResult: result.persistResult ? run : null,
        latestRunId: run.id || "",
        responseMode,
        status: run.status === "completed"
          ? "ready"
          : ["submitted", "queued", "running"].includes(run.status)
            ? "running"
            : "active",
      }));
      refreshSurfaces();
      showStatus(reviewWasActive
        ? "workSessionReviewReopened"
        : run.status === "completed"
          ? executionAvailable() ? "workSessionResultReady" : "workSessionPacketReady"
          : "workSessionQueued");
      return result;
    }

    async function start(input = {}) {
      if (sessionBusy()) return busyResult();
      const current = getSession();
      if (current && current.status !== "completed" && input.replaceConfirmed !== true && options.confirmNew && !options.confirmNew({ current, input })) {
        return { cancelled: true, ok: false };
      }
      if (current) archiveCurrentSession(current, current.status === "completed" ? "completed" : "paused");
      const session = saveSession(createSession(input));
      refreshSurfaces();
      showStatus("workSessionCreated");
      return runSession(session, { responseMode: input.responseMode || "auto" });
    }

    function draft(input = {}) {
      if (sessionBusy()) return busyResult();
      const current = getSession();
      if (current && current.status !== "completed" && input.replaceConfirmed !== true && options.confirmNew && !options.confirmNew({ current, input })) {
        return { cancelled: true, ok: false };
      }
      if (current) archiveCurrentSession(current, current.status === "completed" ? "completed" : "paused");
      const session = saveSession(state.updateSession(createSession(input), { status: "draft" }));
      refreshSurfaces();
      showStatus("workSessionDrafted");
      return { ok: true, session };
    }

    function sessionActionAllowed(action = "", session = getSession()) {
      return options.allowSessionAction?.(session, action) !== false;
    }

    function contextBlocked() {
      showStatus("workSessionContextReadOnlyStatus");
      return { ok: false, reason: "stale_context" };
    }

    const callbacks = Object.freeze({
      onComplete: () => {
        const current = getSession();
        if (!current) return null;
        if (sessionBusy(current)) return busyResult();
        return finalizeCurrentSession(current);
      },
      onCompleteWorkItemProject: () => {
        const current = getSession();
        if (!current?.portfolioBinding?.itemId || options.publicMode?.()) return { ok: false };
        if (!sessionActionAllowed("complete_project", current)) return contextBlocked();
        if (sessionBusy(current)) return busyResult();
        return completeBoundWorkItemProject(current);
      },
      onCompleteWorkItemStep: () => {
        const current = getSession();
        const binding = current?.portfolioBinding;
        if (!binding?.itemId || !binding?.providerId || !binding?.nextStep || !binding?.nextStepHash || options.publicMode?.()) return { ok: false };
        if (!sessionActionAllowed("complete_step", current)) return contextBlocked();
        if (sessionBusy(current)) return busyResult();
        return completeBoundWorkItemStep(current);
      },
      onCopyResult: () => options.copyResult?.(options.getResult?.() || null),
      onCopyTask: () => options.copyTask?.(getSession()),
      onCreate: (input = {}) => start(input),
      onDeleteHistory: ({ historyId = "" } = {}) => {
        if (options.confirmDeleteHistory && !options.confirmDeleteHistory()) return false;
        const history = state.removeHistoryEntry?.(options.getHistory?.() || [], historyId) || [];
        options.saveHistory?.(history);
        refreshSurfaces();
        showStatus("workSessionHistoryDeleted");
        return history;
      },
      onNew: () => {
        if (sessionBusy()) return busyResult();
        const current = getSession();
        if (current && current.status !== "completed" && options.confirmNew && !options.confirmNew()) return false;
        if (current) archiveCurrentSession(current, current.status === "completed" ? "completed" : "paused");
        saveSession(null);
        refreshSurfaces();
        showStatus("workSessionArchivedLocally");
        return true;
      },
      onOpenLocalFile: async ({ path = "" } = {}) => {
        const result = await options.openLocalFile?.(path);
        showStatus(result?.ok ? "workSessionFileOpened" : "workSessionFileOpenFailed");
        return result;
      },
      onOpenWorkspace: ({ workspace } = {}) => options.openWorkspace?.(workspace || "now", { scroll: true }),
      onOpenItemPanel: ({ panel } = {}) => options.openItemPanel?.(panel || "work"),
      onPrepare: () => sessionActionAllowed("prepare_handoff") ? prepareHandoff() : contextBlocked(),
      onRequestWriteback: () => sessionActionAllowed("request_writeback") ? prepareHandoff() : contextBlocked(),
      onRetry: () => {
        const current = getSession();
        const presentation = lifecycleProjection(current);
        if (!current || options.publicMode?.() || presentation.state !== "failed_retryable" || presentation.retryAllowed !== true) return { ok: false };
        if (!sessionActionAllowed("retry", current)) return contextBlocked();
        return runSession(current);
      },
      onRunDraft: () => {
        const current = getSession();
        if (!current) return { ok: false };
        if (!sessionActionAllowed("run", current)) return contextBlocked();
        return runSession(current, {
          intent: current.intent,
          responseMode: current.responseMode || "auto",
        });
      },
      onRun: ({ attachmentName = "", intent = "", responseMode = "auto", sourceHint = "" } = {}) => {
        const current = getSession();
        if (!sessionActionAllowed("run", current)) return contextBlocked();
        return runSession(current, { attachmentName, intent, responseMode, sourceHint });
      },
      onSaveResult: () => {
        const current = getSession();
        if (!current || current.status === "completed") return { ok: false };
        if (!sessionActionAllowed("save_result", current)) return contextBlocked();
        return runSession(current, {
          artifactFromResult: true,
          intent: translate("workSessionArtifactTurn"),
          promptSuffix: translate("workSessionArtifactPromptSuffix"),
          responseMode: "artifact",
        });
      },
      onRemoveCard: ({ cardId } = {}) => {
        const current = getSession();
        if (!current) return null;
        if (!sessionActionAllowed("remove_card", current)) return contextBlocked();
        if (sessionBusy(current)) return busyResult();
        const session = applyMutation(state.removeCard(current, cardId));
        refreshSurfaces();
        showStatus("workSessionCardRemoved");
        return session;
      },
      onResume: ({ encodedPacket } = {}) => {
        const packet = options.decodePayload?.(encodedPacket || "");
        if (!packet) return null;
        if (sessionBusy()) return busyResult();
        if (getSession() && options.confirmSwitchHistory && !options.confirmSwitchHistory()) return false;
        if (getSession()) archiveCurrentSession(getSession(), getSession()?.status === "completed" ? "completed" : "paused");
        const intent = packet.nextResume || packet.title || packet.taskRunId || translate("workSessionQuick_today");
        const session = saveSession(createSession({
          intent,
          sourceHint: packet.path || "",
          title: packet.title || packet.taskRunId || intent,
        }, "workSessionQuick_today"));
        refreshSurfaces();
        showStatus("workSessionResumeCreated");
        return session;
      },
      onResumeHistory: ({ historyId = "" } = {}) => {
        const entry = (options.getHistory?.() || []).find((item) => item?.id === historyId);
        if (!entry) return null;
        const current = getSession();
        if (sessionBusy(current)) return busyResult();
        if (current && (current.historyId === historyId || current.id === historyId)) return current;
        if (current && options.confirmSwitchHistory && !options.confirmSwitchHistory()) return false;
        if (current) archiveCurrentSession(current, current.status === "completed" ? "completed" : "paused");
        const session = state.sessionFromHistory?.(entry);
        if (!session) return null;
        saveSession(session);
        refreshSurfaces();
        showStatus("workSessionHistoryResumed");
        return session;
      },
      onUpdateIntent: ({ intent } = {}) => {
        const current = getSession();
        if (!current) return null;
        if (!sessionActionAllowed("update_intent", current)) return contextBlocked();
        if (sessionBusy(current)) return busyResult();
        const session = applyMutation(state.updateSession(current, { intent, title: intent }));
        refreshSurfaces();
        return session;
      },
      onReconcile: () => sessionActionAllowed("reconcile") ? runSession(getSession()) : contextBlocked(),
      onUploadFile: (file) => options.uploadFile?.(file),
    });

    return Object.freeze({
      addCard,
      applyMutation,
      archiveCurrentSession,
      callbacks,
      creationDefaults,
      draft,
      ensure,
      handoffActive,
      prepareHandoff,
      runSession,
      sessionBusy,
      start,
      syncHandoffStatus,
    });
  }

  function bindWorkSessionEvents(root, callbacks = {}, deps = {}) {
    if (!root?.querySelectorAll) return;
    const translate = deps.translate || ((key) => key);
    const status = () => root.querySelector("[data-work-session-status]");
    const setStatus = (message = "") => {
      const node = status();
      if (node) node.textContent = message;
    };
    const form = root.querySelector("[data-work-session-form]");

    async function withSubmissionLock(targetForm, action) {
      if (!targetForm || targetForm.dataset?.workSessionSubmitting === "true") {
        return { busy: true, ok: false };
      }
      if (targetForm.dataset) targetForm.dataset.workSessionSubmitting = "true";
      const submitControls = Array.from(targetForm.querySelectorAll?.('button[type="submit"], input[type="submit"]') || []);
      submitControls.forEach((control) => { control.disabled = true; });
      try {
        return await action();
      } finally {
        if (targetForm.dataset) delete targetForm.dataset.workSessionSubmitting;
        submitControls.forEach((control) => { control.disabled = false; });
      }
    }

    function bindSourcePicker(sourceForm) {
      let selectedFile = null;
      const sourceDetails = sourceForm?.querySelector(".work-session-source-options");
      const sourceHint = sourceForm?.querySelector("[name='source_hint']");
      const fileInput = sourceForm?.querySelector("[name='source_file']");
      const fileStatus = sourceForm?.querySelector("[data-work-session-file-status]");
      const sourceSummary = sourceForm?.querySelector("[data-work-session-source-summary]");
      const sourceSummaryControl = sourceSummary?.closest?.("summary");
      const dropzone = sourceForm?.querySelector("[data-work-session-dropzone]");
      const showSelectedSource = (value = "") => {
        const label = String(value || "").trim();
        const accessibleLabel = label
          ? `${translate("workSessionSourceSelected")}: ${label}`
          : translate("workSessionAddSource");
        if (sourceSummary) {
          sourceSummary.textContent = accessibleLabel;
          sourceSummary.title = label;
        }
        sourceSummaryControl?.setAttribute("aria-label", accessibleLabel);
        sourceSummaryControl?.setAttribute("title", accessibleLabel);
        if (sourceForm?.dataset) sourceForm.dataset.workSessionSelectedSource = label ? "true" : "false";
      };
      const rememberSelectedFile = (file) => {
        selectedFile = file || null;
        if (sourceForm?.dataset) sourceForm.dataset.workSessionSelectedFile = selectedFile ? "true" : "false";
        if (fileStatus) fileStatus.textContent = selectedFile?.name || translate("workSessionFileHint");
        showSelectedSource(selectedFile?.name || sourceHint?.value);
        if (selectedFile && sourceDetails) sourceDetails.open = false;
      };
      fileInput?.addEventListener("change", () => {
        rememberSelectedFile(fileInput.files?.[0]);
      });
      sourceHint?.addEventListener("change", () => {
        const value = String(sourceHint.value || "").trim();
        showSelectedSource(value || selectedFile?.name);
        if (value && sourceDetails) sourceDetails.open = false;
      });
      dropzone?.addEventListener("dragover", (event) => {
        event.preventDefault();
        dropzone.classList.add("drag-active");
      });
      dropzone?.addEventListener("dragleave", () => dropzone.classList.remove("drag-active"));
      dropzone?.addEventListener("drop", (event) => {
        event.preventDefault();
        dropzone.classList.remove("drag-active");
        rememberSelectedFile(event.dataTransfer?.files?.[0]);
      });
      return () => selectedFile;
    }

    async function sourceInput(sourceForm, getSelectedFile) {
      let sourceHint = String(new global.FormData(sourceForm).get("source_hint") || "").trim();
      const selectedFile = getSelectedFile?.() || null;
      if (selectedFile) {
        setStatus(translate("workSessionUploading"));
        const upload = await callbacks.onUploadFile?.(selectedFile);
        if (!upload?.ok) {
          const errorKey = upload?.error_type === "storage_unavailable"
            ? "workSessionUploadStorageUnavailable"
            : "workSessionUploadFailed";
          return { errorKey, ok: false };
        }
        const noticeKey = upload?.storage?.notice_code === "low_disk_space"
          ? "workSessionStorageNoticeLowDisk"
          : upload?.storage?.notice_code === "working_copies_large"
            ? "workSessionStorageNoticeCopies"
            : "";
        const fileStatus = sourceForm?.querySelector("[data-work-session-file-status]");
        if (noticeKey && fileStatus) {
          fileStatus.textContent = `${selectedFile.name} · ${translate(noticeKey)}`;
        }
        sourceHint = upload.path || sourceHint;
      }
      return {
        attachmentName: selectedFile?.name || "",
        ok: true,
        sourceHint,
      };
    }

    root.querySelectorAll("[data-work-session-quick]").forEach((button) => {
      button.addEventListener("click", () => {
        const input = root.querySelector("[data-work-session-intent]");
        const value = translate(`workSessionQuick_${button.dataset.workSessionQuick || "idea"}`);
        if (input) {
          input.value = value;
          input.focus();
        }
      });
    });

    const selectedLaunchFile = bindSourcePicker(form);

    root.querySelectorAll("[data-work-session-popover-close]").forEach((button) => {
      button.addEventListener("click", () => {
        const details = button.closest?.("details");
        if (details) {
          details.open = false;
          details.querySelector?.("summary")?.focus?.({ preventScroll: true });
        }
      });
    });
    root.querySelectorAll("details.work-session-source-options").forEach((details) => {
      details.addEventListener("keydown", (event) => {
        if (event.key !== "Escape" || !details.open) return;
        details.open = false;
        details.querySelector?.("summary")?.focus?.();
      });
    });

    form?.addEventListener("submit", async (event) => {
      event.preventDefault();
      await withSubmissionLock(form, async () => {
        const data = new global.FormData(form);
        let intent = String(data.get("intent") || "").trim();
        const launchFile = selectedLaunchFile?.() || null;
        if (!intent && launchFile?.name) intent = String(translate("workSessionDefaultFileIntent")).replace("{file}", launchFile.name);
        if (!intent) {
          setStatus(translate("workSessionNeedIntent"));
          return;
        }
        const source = await sourceInput(form, selectedLaunchFile);
        if (!source.ok) {
          setStatus(translate(source.errorKey || "workSessionUploadFailed"));
          return;
        }
        const responseMode = String(data.get("response_mode") || "auto").trim();
        await callbacks.onCreate?.({
          attachmentName: source.attachmentName,
          intent,
          responseMode,
          sourceHint: source.sourceHint,
        });
      });
    });

    const runForm = root.querySelector("[data-work-session-run-form]");
    const selectedRunFile = bindSourcePicker(runForm);
    runForm?.addEventListener("submit", async (event) => {
      event.preventDefault();
      await withSubmissionLock(runForm, async () => {
        const data = new global.FormData(runForm);
        const intent = String(data.get("intent") || "").trim();
        const responseMode = String(data.get("response_mode") || "auto").trim();
        if (!intent) {
          setStatus(translate("workSessionNeedIntent"));
          return;
        }
        const source = await sourceInput(runForm, selectedRunFile);
        if (!source.ok) {
          setStatus(translate(source.errorKey || "workSessionUploadFailed"));
          return;
        }
        await callbacks.onRun?.({
          attachmentName: source.attachmentName,
          intent,
          responseMode,
          sourceHint: source.sourceHint,
        });
      });
    });

    root.querySelectorAll("[data-work-session-remove-card]").forEach((button) => {
      button.addEventListener("click", () => callbacks.onRemoveCard?.({ cardId: button.dataset.workSessionRemoveCard || "" }));
    });
    root.querySelector("[data-work-session-new]")?.addEventListener("click", () => callbacks.onNew?.());
    root.querySelector("[data-work-session-add-followup]")?.addEventListener("click", () => {
      const continuation = root.querySelector(".work-session-continue");
      if (continuation) continuation.open = true;
      root.querySelector("[data-work-session-intent-edit]")?.focus?.();
    });
    root.querySelector("[data-work-session-prepare]")?.addEventListener("click", () => callbacks.onPrepare?.({ status: status() }));
    root.querySelector("[data-work-session-run-draft]")?.addEventListener("click", () => callbacks.onRunDraft?.({ status: status() }));
    root.querySelector("[data-work-session-reconcile]")?.addEventListener("click", () => callbacks.onReconcile?.({ status: status() }));
    root.querySelector("[data-work-session-retry]")?.addEventListener("click", () => callbacks.onRetry?.({ status: status() }));
    root.querySelector("[data-work-session-writeback]")?.addEventListener("click", () => callbacks.onRequestWriteback?.({ status: status() }));
    root.querySelector("[data-work-session-save-result]")?.addEventListener("click", () => callbacks.onSaveResult?.({ status: status() }));
    root.querySelector("[data-work-session-copy-result]")?.addEventListener("click", () => callbacks.onCopyResult?.({ status: status() }));
    root.querySelector("[data-work-session-copy-task]")?.addEventListener("click", () => callbacks.onCopyTask?.({ status: status() }));
    root.querySelector("[data-work-session-complete]")?.addEventListener("click", () => callbacks.onComplete?.({ status: status() }));
    const bindPortfolioMutation = (selector, callback) => {
      const button = root.querySelector(selector);
      button?.addEventListener("click", async () => {
        if (button.disabled) return;
        button.disabled = true;
        try {
          await callback?.({ status: status() });
        } finally {
          if (button.isConnected) button.disabled = false;
        }
      });
    };
    bindPortfolioMutation("[data-work-session-complete-step]", callbacks.onCompleteWorkItemStep);
    bindPortfolioMutation("[data-work-session-complete-project]", callbacks.onCompleteWorkItemProject);
    root.querySelectorAll("[data-work-session-open-file]").forEach((button) => {
      button.addEventListener("click", () => callbacks.onOpenLocalFile?.({ path: button.dataset.workSessionOpenFile || "" }));
    });
    root.querySelectorAll("[data-work-session-history-resume]").forEach((button) => {
      button.addEventListener("click", () => callbacks.onResumeHistory?.({ historyId: button.dataset.workSessionHistoryResume || "" }));
    });
    root.querySelectorAll("[data-work-session-history-delete]").forEach((button) => {
      button.addEventListener("click", () => callbacks.onDeleteHistory?.({ historyId: button.dataset.workSessionHistoryDelete || "" }));
    });
    root.querySelectorAll("[data-work-session-resume]").forEach((button) => {
      button.addEventListener("click", () => callbacks.onResume?.({ encodedPacket: button.dataset.workSessionResume || "" }));
    });
    root.querySelectorAll("[data-open-workspace]").forEach((button) => {
      button.addEventListener("click", () => callbacks.onOpenWorkspace?.({ workspace: button.dataset.openWorkspace || "now" }));
    });
    root.querySelectorAll("[data-open-item-panel]").forEach((button) => {
      button.addEventListener("click", () => callbacks.onOpenItemPanel?.({ panel: button.dataset.openItemPanel || "work" }));
    });
  }

  function interactionSurface(root) {
    if (!root) return null;
    if (root.matches?.("[data-work-session-active], [data-work-session-launcher]")) return root;
    return root.querySelector?.("[data-work-session-active], [data-work-session-launcher]") || null;
  }

  function keyedDetails(surface) {
    const counts = new Map();
    return [...(surface?.querySelectorAll?.("details") || [])].map((details, index) => {
      const classes = String(details.className || "").trim().split(/\s+/).filter(Boolean).sort().join(".");
      const base = String(details.dataset?.workSessionInteraction || classes || "details");
      const occurrence = counts.get(base) || 0;
      counts.set(base, occurrence + 1);
      return { details, key: `${base}:${occurrence}`, legacyIndex: index };
    });
  }

  function captureInteraction(root) {
    const surface = interactionSurface(root);
    if (!surface) return null;
    const controls = [...surface.querySelectorAll("input, textarea, select")];
    const active = global.document?.activeElement;
    const focusedIndex = controls.indexOf(active);
    return {
      controls: controls.map((control) => ({
        checked: Boolean(control.checked),
        type: String(control.type || ""),
        value: String(control.value || ""),
      })),
      detailsOpen: Object.fromEntries(keyedDetails(surface).map(({ details, key }) => [key, Boolean(details.open)])),
      focusedIndex,
      hasSelectedFile: controls.some((control) => control.type === "file" && Number(control.files?.length || 0) > 0)
        || Boolean(surface.querySelector?.("[data-work-session-selected-file='true']")),
      selectionEnd: focusedIndex >= 0 ? Number(active?.selectionEnd ?? -1) : -1,
      selectionStart: focusedIndex >= 0 ? Number(active?.selectionStart ?? -1) : -1,
    };
  }

  function restoreInteraction(root, snapshot = null, options = {}) {
    const surface = interactionSurface(root);
    if (!surface || !snapshot) return false;
    const controls = [...surface.querySelectorAll("input, textarea, select")];
    controls.forEach((control, index) => {
      const saved = snapshot.controls?.[index];
      const skip = options.skipControlsWithin
        && (control.matches?.(options.skipControlsWithin) || control.closest?.(options.skipControlsWithin));
      if (!saved || control.type === "file" || skip) return;
      control.value = saved.value;
      if (control.type === "checkbox" || control.type === "radio") control.checked = saved.checked;
    });
    keyedDetails(surface).forEach(({ details, key, legacyIndex }) => {
      details.open = Array.isArray(snapshot.detailsOpen)
        ? Boolean(snapshot.detailsOpen[legacyIndex])
        : Boolean(snapshot.detailsOpen?.[key]);
    });
    const focused = controls[snapshot.focusedIndex];
    const skipFocused = focused && options.skipControlsWithin
      && (focused.matches?.(options.skipControlsWithin) || focused.closest?.(options.skipControlsWithin));
    if (focused && !skipFocused) {
      focused.focus?.({ preventScroll: true });
      if (snapshot.selectionStart >= 0 && typeof focused.setSelectionRange === "function") {
        focused.setSelectionRange(snapshot.selectionStart, snapshot.selectionEnd);
      }
    }
    return true;
  }

  function renderPreservingInteraction(root, render, options = {}) {
    const snapshot = captureInteraction(root);
    if (snapshot?.hasSelectedFile) return false;
    render?.();
    const restoreRoot = typeof options.resolveRoot === "function"
      ? options.resolveRoot() || root
      : root;
    restoreInteraction(restoreRoot, snapshot, options);
    return true;
  }

  global.ResearchOSWorkSessionWorkbenchService = Object.freeze({
    bindWorkSessionEvents,
    captureInteraction,
    createWorkSessionLifecycle,
    renderPreservingInteraction,
    restoreInteraction,
  });
})(window);
