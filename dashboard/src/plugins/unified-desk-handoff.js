/* ResearchOS maintenance header.
 * 中文：Unified Desk 的交接组装；由当前事项与人工选取的材料组成 session 与 selection，经路由与 composer 生成只供复制的交接文本。
 * English: Handoff assembly for the Unified Desk: builds the session and selection from the open item and explicitly selected material, then routes and composes copy-only handoff text.
 */

(function attachResearchOSUnifiedDeskHandoff(global) {
  "use strict";

  const clean = (value = "") => String(value ?? "").trim();
  const safeArray = (value) => Array.isArray(value) ? value : [];

  // deps are owned by the desk: its state and runtime profile, item/material selectors, content language,
  // copy lookup and the small DOM helpers used to present the dialog.
  function create({ state, profile, selectedTask, selectedAssets, contentLanguage, deskText, status, text, byId, element }) {
    function definitionOfDone(task = selectedTask()) {
      return clean(task?.successGate || deskText("deskReturnAReviewableResult"))
        .split("\n").map(clean).filter(Boolean);
    }

    function buildSession() {
      const task = selectedTask();
      const assets = selectedAssets();
      const sourcePath = task ? (task.sourcePath || state.portfolioModel?.path || "") : "";
      const continuationSource = task ? (task.continuationSource || sourcePath) : "";
      const sourceHints = [...new Set([continuationSource, sourcePath].filter(Boolean))];
      const intent = task?.nextStep || task?.title || clean(state.explorationIntent);
      return {
        cards: assets.map((card) => ({
          id: card.id,
          identity_state: card.identity_state || "",
          identity_scope: card.identity_scope || "",
          path: card.path || "",
          title: card.title || card.id,
          type: card.type || "asset",
          typeLabel: card.boxLabel || card.type || "asset",
        })),
        evidenceBoundary: deskText("deskUseOnlyTheCurrent", {}, contentLanguage()),
        goal: intent,
        id: `unified-desk:${task?.id || "unbound"}`,
        intent: intent,
        portfolioBinding: task ? {
          itemId: task.id,
          nextStep: task.nextStep,
          nextStepHash: task.nextStepHash,
          providerId: task.providerId,
          continuationSource,
          sourcePath,
          title: task.title,
        } : null,
        responseMode: "answer",
        sensitivity: profile.publicStarter ? "public" : "private",
        sourceHints,
        templateLanguage: contentLanguage(),
        title: task?.title || "ResearchOS handoff",
      };
    }

    function selectionFor(session = {}) {
      const task = selectedTask();
      return {
        authority: profile.authority,
        definitionOfDone: definitionOfDone(task),
        excluded: profile.publicStarter
          ? [{ reason: "public_copy_only", scope: "provider execution and canonical write" }]
          : [{ reason: "out_of_scope", scope: "public distribution" }],
        primaryProject: task ? {
          id: task.id,
          path: task.sourcePath || state.portfolioModel?.path || "",
          reason: deskText("deskTheExactPortfolioItem"),
          title: task.title,
        } : null,
        relatedProjects: selectedAssets().filter((card) => card.type === "project").map((card) => ({
          id: card.id,
          identity_state: card.identity_state || "",
          identity_scope: card.identity_scope || "",
          path: card.path || "",
          reason: deskText("deskExplicitlySelectedSupportingSource"),
          title: card.title,
        })),
        saveTarget: "",
      };
    }

    function normalizedHandoffReceipt() {
      return global.ResearchOSHandoffReceiptProjection?.normalize?.(state.data?.handoff_receipt_projection) || null;
    }

    function routeDecision() {
      const receipt = selectedTask() ? (state.data?.execution_route_receipt || null) : null;
      const threadId = clean(receipt?.identity?.thread_id);
      return global.ResearchOSCodexThreadRouter.decide({
        publicStarter: profile.publicStarter,
        routeReceipt: receipt,
        runtime: {
          create_available: false,
          exact_thread_id: threadId,
          thread_state: threadId ? "unknown" : "missing",
          transport_available: false,
        },
      });
    }

    async function prepareHandoff() {
      const session = buildSession();
      if (!session.portfolioBinding && (!clean(state.explorationIntent) || !selectedAssets().length)) {
        return status(deskText("deskSelectMaterialAndDescribe"));
      }
      return presentHandoff(session, selectionFor(session), normalizedHandoffReceipt(), selectedTask()?.id || "");
    }

    async function presentHandoff(session, selection, receipt, itemId = "") {
      const route = session.portfolioBinding?.itemId ? routeDecision() : global.ResearchOSCodexThreadRouter.decide({publicStarter: profile.publicStarter, routeReceipt: null, runtime: {create_available:false, transport_available:false, exact_thread_id:"", thread_state:"missing"}});
      const revision = ++state.handoffRevision;
      state.lastHandoff = null;
      const result = await global.ResearchOSHandoffComposer.compose({
        handoffReceipt: session.portfolioBinding?.itemId ? receipt : null,
        route,
        selection,
        session,
      }, {
        generatedAt: new Date().toISOString(),
        language: contentLanguage(),
        displayLanguage: profile.language,
        previewDocuments: state.data?.preview_documents || [],
        publicStarter: profile.publicStarter,
        responseMode: session.responseMode,
        runtimeMode: profile.runtimeScope,
      });
      if (revision !== state.handoffRevision || (selectedTask()?.id || "") !== itemId) return;
      state.lastHandoff = result;
      text(byId("handoff-preview"), result.markdown);
      const overview = byId("handoff-overview");
      if (overview) {
        overview.replaceChildren();
        const goal = element("section");
        goal.append(element("h3", "", deskText("deskGoal")), element("p", "", session.goal || session.intent || deskText("deskReviewTheFullHandoff")));
        const sources = element("section");
        sources.append(element("h3", "", deskText("deskSelectedSources")));
        const list = element("ul");
        const sessionSources = safeArray(session.cards);
        sessionSources.forEach((source) => {
          const row = element("li", "", source.title || source.path || String(source));
          const projected = result.envelope?.context_pack?.included?.find((entry) => entry.id === source.id);
          const warnings = [];
          if (source.identity_state === "unresolved_reference") warnings.push(deskText("deskIdentityUnresolved"));
          if (projected?.preview_state === "needs_confirmation") warnings.push(deskText("deskSourceLocationUnverified"));
          if (warnings.length) row.append(element("small", "", ` · ${warnings.join(" · ")}`));
          list.append(row);
        });
        if (!sessionSources.length) { const hints = safeArray(session.sourceHints).filter(Boolean).map((hint) => String(hint).replace(/^-\s*/, "")); (hints.length ? hints : [deskText("deskCheckSourcesAndScope")]).forEach((line) => list.append(element("li", "", line))); }
        sources.append(list);
        overview.append(goal, sources);
      }
      text(byId("route-summary"), deskText("deskThisPreparesHandoffText"));
      text(byId("copy-status"), deskText("deskReviewThenCopyTo"));
      byId("handoff-dialog")?.showModal();
    }

    async function copyHandoff() {
      const target = byId("copy-status");
      if (!state.lastHandoff?.markdown) return text(target, deskText("deskNoHandoffPacketIs"));
      try {
        if (typeof global.navigator?.clipboard?.writeText !== "function") throw new Error("clipboard unavailable");
        await global.navigator.clipboard.writeText(state.lastHandoff.markdown);
        text(target, deskText("deskHandoffTextCopiedCopying"));
      } catch {
        const details = byId("handoff-preview")?.closest?.("details");
        if (details) details.open = true;
        byId("handoff-preview")?.focus();
        text(target, deskText("deskAutomaticCopyFailedThe"));
      }
    }

    return Object.freeze({ buildSession, copyHandoff, prepareHandoff, presentHandoff, routeDecision, selectionFor });
  }

  global.ResearchOSUnifiedDeskHandoff = Object.freeze({ create });
})(window);
