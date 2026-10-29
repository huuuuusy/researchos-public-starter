/* ResearchOS maintenance header.
 * 中文：Research assets 第一方插件适配器；拥有 Library 投影、卡片组合候选和领域事件绑定，不创建第二套 Work Session、Review 或存储协议。
 * English: First-party research-assets plugin adapter; owns Library projection, composition candidates, and domain bindings without creating another Work Session, Review, or storage protocol.
 */

(function attachResearchOSResearchAssetsPlugin(global) {
  const PluginRuntime = global.ResearchOSPluginRuntime;
  const RenderPlan = global.ResearchOSDashboardRenderPlan;
  const AssetModel = global.ResearchOSAssetOverviewModel;
  const AssetView = global.ResearchOSAssetOverviewView;
  const AssetWorkbench = global.ResearchOSAssetOverviewWorkbenchService;
  const CardGroupState = global.ResearchOSCardGroupStateService;
  const InboxService = global.ResearchOSInboxService;
  const QueueSync = global.ResearchOSQueueSyncService;
  const StorageContract = global.ResearchOSStorageContract || {};

  const storageKeys = StorageContract.storageKeys || {};
  const activeContextPaths = StorageContract.activeContextPaths || {};
  const GROUP_STORAGE_KEY = storageKeys.cardGroups || "researchos-card-groups";
  const GROUP_SELECTED_KEY = storageKeys.cardGroupsSelected || "researchos-card-groups-selected";
  const DISSOLUTION_STORAGE_KEY = storageKeys.cardGroupDissolutions || "researchos-card-group-dissolutions";
  const GROUP_PATH = activeContextPaths.cardGroups || "06_active_context/ui-card-groups.md";
  const DISSOLUTION_PATH = activeContextPaths.cardGroupDissolutions || "06_active_context/ui-card-group-dissolution-inbox.md";
  const CANDIDATE_TYPES = Object.freeze(["group", "dissolution"]);
  let selectedGroupId = CardGroupState?.readSelectedId?.({ selectedStorageKey: GROUP_SELECTED_KEY }) || "";

  function textFrom(context = {}, key = "") {
    return context.translate?.(key) || context.text?.(key) || key;
  }

  function previewDocuments(context = {}) {
    return typeof context.previewDocuments === "function" ? context.previewDocuments() : [];
  }

  function cardGroupDeps(context = {}) {
    return {
      getDocument: (path) => context.getPreviewDocument?.(path) || null,
      normalizeItem: global.ResearchOSDoingBoardState?.normalizeItem || ((item) => item),
      resolvePath: (basePath = "", targetPath = "") => context.resolveRelativePath?.(basePath, targetPath) || targetPath,
      text: (key) => textFrom(context, key),
    };
  }

  function stateOptions(context = {}) {
    return {
      cardGroupDeps: cardGroupDeps(context),
      dissolutionStorageKey: DISSOLUTION_STORAGE_KEY,
      documents: previewDocuments(context),
      selectedId: selectedGroupId,
      selectedStorageKey: GROUP_SELECTED_KEY,
      storageKey: GROUP_STORAGE_KEY,
    };
  }

  function ensureGroups(context = {}) {
    if (!CardGroupState) return [];
    const state = CardGroupState.ensureCardGroups(stateOptions(context));
    selectedGroupId = state.selectedId;
    return state.groups;
  }

  function loadStoredGroups(context = {}) {
    return CardGroupState?.loadStoredCardGroups?.(stateOptions(context)) || [];
  }

  function loadDissolutions(context = {}) {
    return CardGroupState?.loadCardGroupDissolutions?.(stateOptions(context)) || [];
  }

  async function syncGroups(context = {}) {
    return QueueSync?.syncGroups?.(CardGroupState?.loadCardGroups?.(stateOptions(context)) || []) || "local";
  }

  async function syncDissolutions(context = {}) {
    return QueueSync?.syncCardGroupDissolutions?.(loadDissolutions(context)) || "local";
  }

  function candidateEntry(candidateType = "", item = {}, context = {}) {
    const dissolution = candidateType === "dissolution";
    const title = item.title || item.source_path || textFrom(context, dissolution ? "unifiedInboxDissolution" : "cardGroupTitle");
    const body = dissolution
      ? [item.group_level || "G1", item.source_type, item.safety_rule].filter(Boolean).join(" · ")
      : [item.group_level || "G1", `${(item.items || []).length} ${textFrom(context, "cardGroupComponents")}`, item.purpose].filter(Boolean).join(" · ");
    const path = String(item.source_path || "").trim();
    const status = item.status || (dissolution ? "pending_codex_migration_review" : "pending_codex_review");
    const sourcePath = dissolution ? DISSOLUTION_PATH : GROUP_PATH;
    return {
      type: candidateType,
      typeLabel: textFrom(context, dissolution ? "unifiedInboxDissolution" : "unifiedInboxGroup"),
      title,
      body,
      displayTitle: title,
      displayBody: body,
      displayMeta: [item.group_level || "G1", item.source_type || "custom_group"].filter(Boolean).join(" · "),
      path,
      status,
      statusLabel: InboxService.unifiedInboxStatusLabel(status, (key) => textFrom(context, key)),
      sourcePath,
      updatedAt: item.updatedAt || item.createdAt || "",
      actionId: item.id || "",
      raw: item,
      candidate: {
        candidate_id: `candidate:${candidateType}:${item.id || title}`,
        plugin_id: "research_assets",
        candidate_type: candidateType,
        source_refs: [
          { kind: "inbox", path: sourcePath },
          path ? { kind: "object", path } : null,
        ].filter(Boolean),
        summary: [title, body].filter(Boolean).join(" · "),
        proposed_action: {
          id: dissolution ? "process_group_dissolution" : "process_asset_group",
          target_agent: dissolution ? "project_steward" : "asset_cartographer",
        },
        proposed_writeback: {
          save_target: path || GROUP_PATH,
          object_type: "group",
          object_id: item.id || title,
          object_path: path,
          current_state: item.group_level || "G1",
          proposed_state: dissolution ? "withdraw_or_archive_group" : "confirm_group_composition",
          decision_rationale: item.purpose || item.safety_rule || "",
          impact_scope: path || GROUP_PATH,
          rollback_ref: "",
          validation_state: "not_run",
        },
        sensitivity: "private",
        required_confirmation: "confirm",
        validation: {
          workflow_status: "active",
          evidence_state: "candidate",
          authority_state: "proposed",
          state: "not_run",
        },
      },
    };
  }

  function collectCandidates(candidateType = "", context = {}) {
    const items = candidateType === "dissolution"
      ? loadDissolutions(context).filter((item) => InboxService.inboxStatusIsActive(item.status, true))
      : loadStoredGroups(context).filter((group) => !group.source_type && Array.isArray(group.items) && group.items.length);
    return {
      entries: items.map((item) => candidateEntry(candidateType, item, context)),
      sourceEntry: {
        key: candidateType,
        label: textFrom(context, candidateType === "dissolution" ? "unifiedInboxDissolution" : "unifiedInboxGroup"),
        path: candidateType === "dissolution" ? DISSOLUTION_PATH : GROUP_PATH,
      },
    };
  }

  async function withdrawCandidate(candidateType = "", id = "", context = {}) {
    if (!id || !CardGroupState) return null;
    if (candidateType === "dissolution") {
      const result = CardGroupState.markCardGroupDissolutionWithdrawn(id, stateOptions(context));
      await syncDissolutions(context);
      return result;
    }
    const result = CardGroupState.removeStoredCardGroup(id, stateOptions(context));
    await syncGroups(context);
    return result;
  }

  async function clearProcessedCandidates(candidateType = "", context = {}) {
    if (candidateType !== "dissolution" || !CardGroupState || !InboxService) return [];
    const resolution = InboxService.resolveClearedInboxItems({
      localItems: loadDissolutions(context),
    });
    if (resolution.shouldSave) {
      CardGroupState.saveCardGroupDissolutions(resolution.items, stateOptions(context));
      await syncDissolutions(context);
    }
    return resolution.items;
  }

  function libraryPayload(model = {}, context = {}) {
    const graph = model.payloads?.asset_graph || {};
    const overview = model.payloads?.source_overview || {};
    const publicStarter = Boolean(context.publicStarter?.());
    const runtimeMode = String(context.runtimeMode?.() || "").trim();
    const publicDemo = runtimeMode ? runtimeMode === "public_starter" : publicStarter;
    const publicDemoVisible = Boolean(context.publicDemoVisible?.());
    const displayGraph = RenderPlan.publicStarterGraphForDisplay(graph, !publicDemo || publicDemoVisible);
    const displayOverview = RenderPlan.publicStarterOverviewForDisplay(overview, displayGraph, {
      publicDemoVisible,
      publicStarter: publicDemo,
    });
    const groups = ensureGroups(context);
    const inboxTotal = Number(context.collectInbox?.(displayGraph)?.total || 0);
    const viewModel = AssetModel.buildAssetOverviewModel({
      currentDate: String(context.generatedAt?.() || "").slice(0, 10),
      graph: displayGraph,
      groups,
      inboxTotal,
      overview: displayOverview,
      previewDocuments: model.payloads?.preview_documents || [],
      recentRuns: context.recentRuns?.() || [],
      toNumber: context.toNumber || ((value) => Number(value) || 0),
      translate: (key) => textFrom(context, key),
    });
    const commitmentLens = buildCommitmentLensProjection({
      graph: displayGraph,
      lens: context.libraryLens?.() || {},
      previewDocuments: model.payloads?.preview_documents || [],
      viewModel,
    }, context);
    return { commitmentLens, displayGraph, inboxTotal, publicDemo, publicDemoVisible, publicStarter, viewModel };
  }

  function pathValue(value = "") {
    if (typeof value === "string") return value.trim();
    if (value && typeof value === "object") return String(value.path || value.source_path || "").trim();
    return "";
  }

  function explicitRelationRefs(record = {}, basePath = "", context = {}) {
    const isLocalPath = (value = "") => /(^\.{0,2}\/|\/|\.(?:md|pdf|ya?ml|json)$)/i.test(value) && !/^https?:\/\//i.test(value);
    const refFor = (value, field) => {
      const rawPath = pathValue(value);
      const rawTitle = value && typeof value === "object" ? String(value.title || value.name || "").trim() : "";
      if (rawPath && isLocalPath(rawPath)) {
        const path = context.resolveRelativePath?.(basePath, rawPath) || rawPath;
        return { field, path, title: rawTitle };
      }
      const title = rawTitle || (typeof value === "string" ? value.trim() : rawPath);
      return title ? { field, path: "", title } : null;
    };
    return ["related_papers", "related_people", "related_projects", "source_files"]
      .flatMap((field) => (Array.isArray(record?.[field]) ? record[field].map((value) => refFor(value, field)) : []))
      .filter(Boolean);
  }

  function buildCommitmentLensProjection({ graph = {}, lens = {}, previewDocuments: documents = [], viewModel = {} } = {}, context = {}) {
    const selectedIds = new Set((Array.isArray(lens.selectedIds) ? lens.selectedIds : []).map(String));
    const selectedItems = (Array.isArray(lens.items) ? lens.items : [])
      .filter((item = {}) => item.id && selectedIds.has(String(item.id)));
    if (!selectedItems.length) return { active: false, commitments: [] };

    const graphRecords = ["projects", "papers", "people", "talks"]
      .flatMap((key) => (Array.isArray(graph?.[key]) ? graph[key] : []));
    const cards = (Array.isArray(viewModel.cardBoxes) ? viewModel.cardBoxes : [])
      .flatMap((box = {}) => (Array.isArray(box.cards) ? box.cards : []));
    const byPath = (items = []) => new Map(items
      .map((item = {}) => [pathValue(item.path || item.source_path), item])
      .filter(([path]) => path));
    const documentByPath = byPath(documents);
    const recordByPath = byPath(graphRecords);
    const cardByPath = byPath(cards);
    const materialFor = (ref, relationKind) => {
      const path = typeof ref === "string" ? ref : String(ref?.path || "");
      const explicitTitle = typeof ref === "object" ? String(ref?.title || "") : "";
      const document = documentByPath.get(path) || null;
      const record = recordByPath.get(path) || null;
      const card = cardByPath.get(path) || null;
      return {
        path,
        previewable: Boolean(document || context.getPreviewDocument?.(path)),
        relationKind,
        title: card?.title || record?.title || document?.title || explicitTitle || path,
        type: card?.type || record?.type || document?.type || "asset",
      };
    };

    return {
      active: true,
      commitments: selectedItems.map((item = {}) => {
        const sourcePath = pathValue(item.sourcePath || item.source_path);
        const sourceDocument = documentByPath.get(sourcePath) || {};
        const sourceRecord = recordByPath.get(sourcePath) || {};
        const relationRefs = [
          ...explicitRelationRefs(sourceDocument, sourcePath, context),
          ...explicitRelationRefs(sourceRecord, sourcePath, context),
        ].filter((ref) => (ref.path || ref.title) && ref.path !== sourcePath);
        const uniqueRefs = [...new Map(relationRefs.map((ref) => [ref.path || `${ref.field}:${ref.title}`, ref])).values()];
        return {
          anchor: sourcePath ? materialFor(sourcePath, "canonical_anchor") : null,
          id: String(item.id),
          omittedCount: Math.max(0, uniqueRefs.length - 12),
          related: uniqueRefs.slice(0, 12).map((ref) => materialFor(ref, "canonical_relation")),
          sourcePath,
          title: item.title || item.id,
        };
      }),
    };
  }

  function handleAssetTask({ button = null, card = null, payload = null, status = null } = {}, context = {}) {
    if (!payload) return;
    const lens = context.libraryLens?.() || {};
    const selectedLensId = Array.isArray(lens.selectedIds) && lens.selectedIds.length === 1 ? String(lens.selectedIds[0]) : "";
    const selectedLensItem = (Array.isArray(lens.items) ? lens.items : []).find((item = {}) => String(item.id || "") === selectedLensId) || null;
    const lensBinding = selectedLensItem ? {
      itemId: String(selectedLensItem.id || ""),
      nextStep: String(selectedLensItem.next_step || selectedLensItem.nextStep || ""),
      nextStepHash: String(selectedLensItem.next_step_hash || selectedLensItem.nextStepHash || ""),
      providerId: String(selectedLensItem.provider_id || selectedLensItem.providerId || "research_portfolio"),
      sourcePath: String(selectedLensItem.source_path || selectedLensItem.sourcePath || ""),
      title: String(selectedLensItem.title || selectedLensItem.id || ""),
    } : null;
    if (payload.source === "asset-card-basket") {
      const cards = (Array.isArray(payload.source_cards) ? payload.source_cards : []).map((source = {}) => ({
        id: source.id || source.path || source.title,
        path: source.path || "",
        subtitle: source.subtitle || source.type_label || "",
        title: source.title || source.path || source.id || "asset",
        type: source.type || "asset",
      }));
      const result = context.draftWorkSession?.({
        cards,
        intent: payload.note || payload.title || "",
        portfolioBinding: lensBinding,
        responseMode: "auto",
        sourceHint: cards.find((item) => item.path)?.path || payload.path || "",
        title: payload.title || "",
      });
      if (result?.busy && status) status.textContent = textFrom(context, "workSessionWaitForResult");
      if (result?.ok) {
        if (status) status.textContent = textFrom(context, "assetBasketAddedStatus");
        context.rerender?.();
      }
      return;
    }
    if (payload.source === "asset-overview-card") {
      const sessionCard = context.cardFromElement?.(card, payload) || null;
      const currentSession = context.currentWorkSession?.() || null;
      const publicStarter = Boolean(context.publicStarter?.());
      const candidate = payload.candidate && typeof payload.candidate === "object"
        ? {
            ...payload.candidate,
            proposed_writeback: publicStarter ? {
              ...(payload.candidate.proposed_writeback || {}),
              save_target: "",
              proposed_state: "copy_only_review",
            } : payload.candidate.proposed_writeback,
            sensitivity: publicStarter ? "public_safe" : (payload.candidate.sensitivity || "internal"),
            required_confirmation: publicStarter ? "handoff_only" : (payload.candidate.required_confirmation || "candidate_diff"),
          }
        : null;
      const transition = payload.enhancement
        ? `${payload.enhancement.current_level || ""}${payload.enhancement.target_level ? ` -> ${payload.enhancement.target_level}` : ""}`
        : "";
      const actionLabel = textFrom(context, {
        enhance: "assetAdvancedUpgrade",
        reverify: "assetAdvancedReverify",
        use: "assetCardInspectUpgrade",
        verify: "assetAdvancedVerifyLevel",
      }[payload.enhancement?.action || "use"] || "assetCardInspectUpgrade");
      const note = String(payload.note || "");
      const boundedNote = transition && note === transition
        ? ""
        : transition && note.startsWith(`${transition} · `)
          ? note.slice(transition.length + 3)
          : note;
      const input = {
        cards: sessionCard ? [sessionCard] : [],
        candidate,
        enhancement: payload.enhancement || null,
        evidenceBoundary: publicStarter
          ? textFrom(context, "workSessionDefaultBoundaryPublic")
          : textFrom(context, "workSessionDefaultBoundaryPrivate"),
        intent: [actionLabel, payload.title || "", transition, boundedNote].filter(Boolean).join(" · "),
        path: payload.path,
        portfolioBinding: lensBinding,
        responseMode: "auto",
        title: payload.title,
      };
      const requiresBoundedEnhancement = payload.enhancement && payload.enhancement.action !== "use";
      const currentMatchesLens = !lensBinding || String(currentSession?.portfolioBinding?.itemId || "") === lensBinding.itemId;
      const result = requiresBoundedEnhancement || !currentSession || currentSession.status === "completed" || !currentMatchesLens
        ? context.draftWorkSession?.(input)
        : context.addWorkSessionCard?.(sessionCard);
      if (result?.busy && status) status.textContent = textFrom(context, "workSessionWaitForResult");
      if (result?.ok) context.rerender?.();
      return;
    }
    context.addTransientTask?.(payload, "local");
    if (button) button.textContent = textFrom(context, "assetCardAddedButton");
    if (status) {
      status.textContent = payload.source === "asset-card-basket"
        ? textFrom(context, "assetBasketAddedStatus")
        : textFrom(context, "assetCardAddedStatus");
    }
  }

  function relatedCompositionCards(cards = [], context = {}) {
    const sourcePaths = new Set(
      (Array.isArray(cards) ? cards : [])
        .map((card = {}) => String(card.path || "").trim())
        .filter(Boolean)
    );
    if (!sourcePaths.size) return [];
    return previewDocuments(context)
      .filter((doc = {}) => String(doc.type || "") === "relationship_pattern" && String(doc.path || "").trim())
      .map((doc = {}) => {
        const relatedPaths = [
          ...(Array.isArray(doc.related_people) ? doc.related_people : []),
          ...(Array.isArray(doc.source_files) ? doc.source_files : []),
        ].map((path) => context.resolveRelativePath?.(doc.path, path) || path).filter(Boolean);
        const matchCount = relatedPaths.filter((path) => sourcePaths.has(path)).length;
        return { matchCount, path: doc.path || "", title: doc.title || doc.path || "", updated: doc.updated || "" };
      })
      .filter((doc) => doc.matchCount > 0)
      .sort((left, right) => (
        right.matchCount - left.matchCount || String(right.updated || "").localeCompare(String(left.updated || ""))
      ));
  }

  function renderLibrary(model = {}, context = {}) {
    if (!AssetModel || !AssetView || !RenderPlan) return "";
    const payload = libraryPayload(model, context);
    const escapeHtml = context.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const summary = payload.viewModel.summary || {};
    const lensItems = context.libraryLens?.()?.items;
    const overviewHtml = AssetView.renderAssetOverviewHtml({
      // A model without a commitment count (the public edition) counts the commitments this Library lists.
      summary: summary.commitmentCount === undefined && Array.isArray(lensItems)
        ? { ...summary, commitmentCount: lensItems.length }
        : summary,
      cardBoxes: payload.viewModel.cardBoxes,
      focusCard: payload.viewModel.focusCard,
      publicMode: payload.publicStarter,
      publicDemoToggleHtml: payload.publicDemo
        ? AssetView.renderPublicDemoToggle({ visible: payload.publicDemoVisible }, {
            escapeHtml: context.escapeHtml,
            translate: (key) => textFrom(context, key),
          })
        : "",
      intakePanelHtml: "",
      deps: {
        escapeHtml: context.escapeHtml,
        translate: (key) => textFrom(context, key),
      },
    });
    const sourceBrowser = `<details class="library-source-browser" data-library-source-browser>
      <summary><span><strong>${escapeHtml(textFrom(context, "workSessionBrowseSources"))}</strong><small>${escapeHtml(textFrom(context, "workSessionBrowseSourcesHint"))}</small></span></summary>
      ${overviewHtml}
    </details>`;
    const commitmentLensHtml = AssetView.renderCommitmentLensProjection?.(payload.commitmentLens, {
      escapeHtml: context.escapeHtml,
      previewButton: context.previewButton,
      translate: (key) => textFrom(context, key),
    }) || "";
    return `${commitmentLensHtml}${sourceBrowser}`;
  }

  function bindLibrary({ context = {}, model = {}, root = null } = {}) {
    if (!root || !AssetWorkbench) return;
    const payload = libraryPayload(model, context);
    AssetWorkbench.bindAssetOverviewEvents(root, {
      onAddAssetTask: (event) => handleAssetTask(event, context),
      onAssetDetail: ({ detail }) => context.focusSection?.(detail || "assetOverview"),
      onOpenWorkspace: ({ workspace }) => context.openWorkspace?.(workspace || "now", { scroll: true }),
      onOpenPreview: ({ path }) => context.openPreview?.(path),
      onPublicDemoToggle: ({ visible }) => {
        context.setPublicDemoVisible?.(Boolean(visible));
        if (context.rerenderDashboard) context.rerenderDashboard();
        else context.rerender?.();
      },
      translate: (key) => textFrom(context, key),
    });
    context.bindPreviewButtons?.(root);
  }

  if (PluginRuntime) {
    CANDIDATE_TYPES.forEach((candidateType) => {
      PluginRuntime.registerCandidateAdapter(candidateType, {
        collect: ({ context = {} }) => collectCandidates(candidateType, context),
        actions: {
          clear_processed: ({ context = {} }) => clearProcessedCandidates(candidateType, context),
          withdraw: ({ context = {}, id }) => withdrawCandidate(candidateType, id, context),
        },
      });
    });
    PluginRuntime.registerOwnedAdapter("research_assets", "research_assets_library", {
      bind: bindLibrary,
      render: renderLibrary,
    });
    PluginRuntime.registerSurfaceDependency("work", "relatedCompositionCards", {
      pluginId: "research_assets",
      provide: ({ context = {} }) => (cards = []) => relatedCompositionCards(cards, context),
    });
  }

  global.ResearchOSResearchAssetsPlugin = Object.freeze({
    CANDIDATE_TYPES,
    candidateEntry,
    clearProcessedCandidates,
    collectCandidates,
    ensureGroups,
    handleAssetTask,
    loadDissolutions,
    loadStoredGroups,
    buildCommitmentLensProjection,
    relatedCompositionCards,
    renderLibrary,
    withdrawCandidate,
  });
})(window);
