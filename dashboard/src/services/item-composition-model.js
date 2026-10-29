/* ResearchOS maintenance header.
 * 中文：从 Portfolio exact item、Project Hub/Asset Graph 与资产卡牌盒子派生只读产品—组件双向关系。
 * English: Derives a read-only product-component dual lens from exact Portfolio items, Project Hub/Asset Graph data, and asset card boxes.
 */
(function attachResearchOSItemCompositionModel(global) {
  "use strict";

  const safeArray = (value) => Array.isArray(value) ? value : [];
  const clean = (value = "") => String(value ?? "").trim();
  const relationStrength = Object.freeze({ candidate: 1, confirmed: 2 });
  const typeOrder = Object.freeze({ paper: 0, project: 1, person: 2, talk: 3, group: 4, material: 5, asset: 6 });
  const repoRootSegments = new Set([
    "00_identity", "01_knowledge", "02_decisions", "03_cognition", "04_people",
    "05_workflows", "06_active_context", "07_archive", "08_exports", "09_templates",
    "config", "corpus", "dashboard", "docs", "evals", "scripts",
    "AGENT_PROTOCOL.md", "README.md", "ROADMAP.md", "SAFE_EXPORT_POLICY.md", "START_HERE.md", "SYSTEM_OVERVIEW.md",
  ]);

  function normalizePath(value = "", basePath = "") {
    const raw = clean(value).replace(/\\/g, "/");
    if (!raw) return "";
    const absolute = raw.startsWith("/");
    const firstSegment = raw.split("/")[0];
    const repoRootPath = raw.startsWith("/") || repoRootSegments.has(firstSegment);
    const relativeToOwner = Boolean(clean(basePath)) && !repoRootPath;
    const base = relativeToOwner ? clean(basePath).replace(/\\/g, "/").split("/").slice(0, -1).join("/") : "";
    const parts = `${base ? `${base}/` : ""}${raw}`.split("/");
    const resolved = [];
    parts.forEach((part) => {
      if (!part || part === ".") return;
      if (part === "..") resolved.pop();
      else resolved.push(part);
    });
    return `${absolute ? "/" : ""}${resolved.join("/")}`;
  }

  function inferredType(path = "", fallback = "asset") {
    const value = normalizePath(path);
    if (value.startsWith("04_people/")) return "person";
    if (value.includes("/papers/") || value.includes("reading_notes/")) return "paper";
    if (value.includes("/talks/") || value.includes("deck_reading_notes/")) return "talk";
    if (value.includes("/projects/")) return "project";
    return fallback || "material";
  }

  function basenameTitle(path = "") {
    return normalizePath(path).split("/").pop()?.replace(/\.md$/i, "").replace(/[_-]+/g, " ") || "未命名组件";
  }

  function referenceId(path = "", type = "asset") {
    return `reference:${type}:${encodeURIComponent(normalizePath(path))}`;
  }

  function dedupeStrings(values = []) {
    return [...new Set(safeArray(values).map(clean).filter(Boolean))];
  }

  const genericPersonAliases = new Set([
    "collaborator", "collaborators", "manuscript team", "project owner", "research team", "team", "待核对", "未登记",
  ]);
  function personAliases(value = "") {
    const raw = clean(value).normalize("NFKC").toLowerCase();
    if (!raw) return [];
    const normalizeAlias = (alias = "") => alias
      .replace(/^(?:dr|prof|professor)\.?\s+/i, "")
      .replace(/[^a-z0-9\u4e00-\u9fff]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    return dedupeStrings([raw, ...raw.split(/\s*(?:\/|\||;|,|·|＆|&|\band\b)\s*/i)])
      .map(normalizeAlias)
      .filter((alias) => alias && !genericPersonAliases.has(alias));
  }

  function shouldCreateOwnerCandidate(value = "", selfPersonAliases = new Set()) {
    const raw = clean(value).normalize("NFKC").toLowerCase();
    const aliases = personAliases(raw);
    if (!aliases.length || aliases.every((alias) => selfPersonAliases.has(alias))) return false;
    if (/(?:\bteams?\b|团队)/i.test(raw) && !/[\/|;,·]/.test(raw)) return false;
    return true;
  }

  function relationSort(left = {}, right = {}) {
    return (typeOrder[left.type] ?? 99) - (typeOrder[right.type] ?? 99)
      || clean(left.title).localeCompare(clean(right.title));
  }

  function build(options = {}) {
    const portfolioItems = safeArray(options.portfolioItems);
    const assetBoxes = safeArray(options.assetBoxes);
    const graph = options.graph && typeof options.graph === "object" ? options.graph : {};
    const selfPersonAliases = new Set(safeArray(options.selfPersonAliases).flatMap(personAliases));
    const components = new Map();
    const componentsByPath = new Map();
    const libraryIds = new Set();
    let anonymousReference = 0;

    function upsertComponent(raw = {}, settings = {}) {
      const path = normalizePath(raw.path || "", settings.basePath || "");
      const type = clean(raw.type) || inferredType(path, settings.typeHint || "asset");
      const existingByPath = path ? componentsByPath.get(path) : null;
      const unresolved = !path && !clean(raw.id);
      // A local reference label is not a resolved person/object identity.
      // Keep exact spelling and scope; punctuation folding and truncation can collide.
      const localReference = unresolved ? `unresolved:${encodeURIComponent(JSON.stringify([
        settings.referenceScope || `anonymous:${++anonymousReference}`, type, clean(raw.title || raw.name),
      ]))}` : "";
      const id = existingByPath?.id || clean(raw.id) || (path ? referenceId(path, type) : localReference);
      const existing = components.get(id) || existingByPath || {};
      const component = {
        ...existing,
        ...raw,
        id,
        identity_state: unresolved ? "unresolved_reference" : "identified",
        identity_scope: unresolved ? (settings.referenceScope || localReference) : "",
        libraryAvailable: Boolean(existing.libraryAvailable || settings.libraryAvailable),
        path,
        relation_ids: dedupeStrings([...(existing.relation_ids || []), ...(raw.relation_ids || [])]),
        relation_reasons: dedupeStrings([...(existing.relation_reasons || []), ...(raw.relation_reasons || [])]),
        title: clean(raw.title || raw.name || existing.title) || basenameTitle(path),
        type,
      };
      components.set(id, component);
      if (path) componentsByPath.set(path, component);
      if (component.libraryAvailable) libraryIds.add(id);
      return component;
    }

    assetBoxes.forEach((box) => safeArray(box.cards).forEach((card) => upsertComponent({
      ...card,
      boxLabel: box.label || card.boxLabel || "",
    }, { libraryAvailable: true })));

    const projectNodes = safeArray(graph.projects);
    const projectActions = safeArray(graph.project_action_cards);
    const matrix = safeArray(graph.asset_relation_matrix);
    const edges = safeArray(graph.asset_relation_evidence).length
      ? graph.asset_relation_evidence : safeArray(graph.asset_relation_explanations);
    const edgesByNode = new Map();
    const edgesByPaths = new Map();
    const edgeKey = (from, to, type) => JSON.stringify([type, ...[normalizePath(from), normalizePath(to)].sort()]);
    edges.forEach((edge) => {
      [edge.source_id, edge.target_id].map(clean).filter(Boolean).forEach((id) => {
        if (!edgesByNode.has(id)) edgesByNode.set(id, []);
        edgesByNode.get(id).push(edge);
      });
      if (edge.source_path && edge.target_path) {
        const key = edgeKey(edge.source_path, edge.target_path, edge.edge_type);
        if (!edgesByPaths.has(key)) edgesByPaths.set(key, []);
        edgesByPaths.get(key).push(edge);
      }
    });

    const edgeConfirmed = (edge) => edge.evidence_state === "confirmed" && !edge.needs_confirmation;

    function componentForReference(raw = {}, settings = {}) {
      if (typeof raw === "string") raw = { path: raw };
      const path = normalizePath(raw.path || "", settings.basePath || "");
      const existing = clean(raw.id) ? components.get(clean(raw.id)) : null;
      const existingByPath = path ? componentsByPath.get(path) : null;
      return existingByPath || existing || upsertComponent({
        ...raw,
        path,
        type: clean(raw.type) || inferredType(path, settings.typeHint || "material"),
      }, settings);
    }

    function compositionForItem(item = {}) {
      const itemId = clean(item.id);
      const sourcePath = normalizePath(item.sourcePath || item.source_path || "");
      const sourceRoot = normalizePath(item.sourceRoot || item.source_root || "");
      const project = projectNodes.find((node) => normalizePath(node.path) === sourcePath) || null;
      const matrixRoot = matrix.find((node) => normalizePath(node.path) === sourcePath) || null;
      const libraryRoot = sourcePath ? componentsByPath.get(sourcePath) || null : null;
      const rootSource = project || matrixRoot || libraryRoot || (sourcePath ? {
        id: `item-root:${itemId}`,
        path: sourcePath,
        title: item.title || basenameTitle(sourcePath),
        type: inferredType(sourcePath, "project"),
      } : null);
      const root = rootSource ? componentForReference(rootSource, {
        libraryAvailable: Boolean(libraryRoot),
        typeHint: project ? "project" : matrixRoot ? "paper" : "asset",
      }) : null;
      const relationMap = new Map();
      const evidenceGaps = [];

      function referenceState(raw = {}, edgeType = "") {
        const targetPath = normalizePath(raw.path || "", sourcePath);
        const matching = sourcePath && targetPath
          ? safeArray(edgesByPaths.get(edgeKey(sourcePath, targetPath, edgeType))) : [];
        if (matching.length) {
          if (matching.every((edge) => edge.evidence_state === "rejected")) return null;
          return matching.some(edgeConfirmed) ? "confirmed" : "candidate";
        }
        if (raw.evidence_state === "rejected") return null;
        if (raw.evidence_state) return edgeConfirmed(raw) ? "confirmed" : "candidate";
        // Legacy records may lack an edge. Confidence alone is not provenance.
        const directSources = {
          project_membership: "project_frontmatter",
          collaborator_role: "collaboration_index",
          report_context: "talk_mapping",
        };
        return raw.confidence === "high" && raw.source === directSources[edgeType]
          && !raw.needs_confirmation ? "confirmed" : "candidate";
      }

      function addRelation(raw = {}, state = "candidate", metadata = {}) {
        if (state === null) return;
        const component = componentForReference(raw, {
          referenceScope: JSON.stringify([itemId, metadata.relationType || "reference"]),
          basePath: metadata.basePath || sourcePath,
          typeHint: metadata.typeHint || "material",
        });
        if (!component || component.id === root?.id) return;
        const nextState = state === "confirmed" ? "confirmed" : "candidate";
        const existing = relationMap.get(component.id);
        const strongest = !existing || relationStrength[nextState] > relationStrength[existing.state] ? nextState : existing.state;
        relationMap.set(component.id, {
          componentId: component.id,
          identityState: component.identity_state,
          libraryAvailable: component.libraryAvailable,
          path: component.path,
          reasons: dedupeStrings([...(existing?.reasons || []), metadata.reason]),
          relationTypes: dedupeStrings([...(existing?.relationTypes || []), metadata.relationType]),
          sources: dedupeStrings([...(existing?.sources || []), metadata.source]),
          state: strongest,
          title: component.title,
          type: component.type,
        });
      }

      if (sourceRoot && sourceRoot !== sourcePath) addRelation({
        path: sourceRoot,
        title: `${clean(item.title) || itemId} · 主文件`,
        type: "material",
      }, "confirmed", {
        reason: "Portfolio source_root 的明确文件入口",
        relationType: "stable_source",
        source: sourcePath || "research-portfolio",
        typeHint: "material",
      });

      if (project) {
        safeArray(project.source_files).forEach((path) => addRelation({ path }, "confirmed", {
          basePath: project.path,
          reason: "Project Hub source_files 的稳定引用",
          relationType: "stable_source",
          source: project.path,
        }));
        safeArray(project.resolved_papers).forEach((paper) => addRelation(paper, referenceState(paper, "project_membership"), {
          reason: paper.match ? `${paper.match} · ${paper.confidence || "confidence unknown"}` : "Project Hub resolved paper",
          relationType: "paper_evidence",
          source: project.path,
          typeHint: "paper",
        }));
        safeArray(project.candidate_papers).forEach((paper) => addRelation(paper,
          referenceState(paper, "project_membership") === null ? null : "candidate", {
          reason: paper.match || paper.confidence || "Project Hub candidate paper",
          relationType: "paper_candidate",
          source: project.path,
          typeHint: "paper",
        }));
        safeArray(project.related_people).forEach((person) => addRelation(person, referenceState(person, "collaborator_role"), {
          reason: person.confidence ? `Project Hub related_people · ${person.confidence}` : "Project Hub related_people",
          relationType: "collaborator",
          source: project.path,
          typeHint: "person",
        }));
        if (project.project_status_summary && !safeArray(project.source_files).length && !safeArray(project.resolved_papers).length) {
          evidenceGaps.push(project.project_status_summary);
        }
      }

      if (matrixRoot) {
        safeArray(matrixRoot.projects).forEach((entry) => addRelation(entry, referenceState(entry, "project_membership"), {
          reason: entry.match || entry.confidence || "Asset Graph project relation",
          relationType: "project_context",
          source: matrixRoot.path,
          typeHint: "project",
        }));
        safeArray(matrixRoot.people).forEach((entry) => addRelation(entry, referenceState(entry, "collaborator_role"), {
          reason: entry.relation_to_paper_reason_cn || entry.match || entry.confidence || "Asset Graph person relation",
          relationType: "collaborator",
          source: matrixRoot.path,
          typeHint: "person",
        }));
        safeArray(matrixRoot.talks).forEach((entry) => addRelation(entry, referenceState(entry, "report_context"), {
          reason: entry.relation_to_researcher_reason_cn || entry.match || entry.confidence || "Asset Graph talk relation",
          relationType: "expression",
          source: matrixRoot.path,
          typeHint: "talk",
        }));
        safeArray(matrixRoot.evidence_needed).forEach((gap) => evidenceGaps.push(clean(gap)));
        safeArray(matrixRoot.missing_links).forEach((gap) => evidenceGaps.push(clean(gap)));
      }

      safeArray(item.relatedPeople || item.related_people).forEach((person) => addRelation(person, "confirmed", {
        reason: "Portfolio related_people 的明确关系",
        relationType: "responsibility_context",
        source: sourcePath || "research-portfolio",
        typeHint: "person",
      }));

      const accountableOwner = clean(item.accountableOwner || item.accountable_owner || item.owner);
      if (accountableOwner) {
        const ownerAliases = new Set(personAliases(accountableOwner));
        const matches = [...components.values()].filter((component) => component.type === "person"
          && (component.libraryAvailable || component.path.startsWith("04_people/"))
          && personAliases(component.title || component.name)
          .some((alias) => ownerAliases.has(alias)));
        if (matches.length === 1) addRelation(matches[0], "confirmed", {
          reason: "Portfolio accountable_owner 与人物卡唯一匹配",
          relationType: "accountable_owner",
          source: sourcePath || "research-portfolio",
          typeHint: "person",
        });
        else if (matches.length || shouldCreateOwnerCandidate(accountableOwner, selfPersonAliases)) {
          addRelation({ title: accountableOwner, type: "person" }, "candidate", {
            reason: matches.length ? "accountable_owner 匹配到多个人物卡，需人工消歧" : "accountable_owner 尚未匹配到人物卡",
            relationType: "accountable_owner_candidate",
            source: sourcePath || "research-portfolio",
            typeHint: "person",
          });
          evidenceGaps.push(matches.length
            ? `负责人「${accountableOwner}」匹配到多个人物卡；未自动确认。`
            : `负责人「${accountableOwner}」尚未匹配到人物卡；保留为候选。`);
        }
      }

      if (libraryRoot) {
        safeArray(libraryRoot.relation_ids).forEach((neighborId) => {
          const neighbor = components.get(neighborId);
          if (!neighbor) return;
          const matchingEdges = safeArray(edgesByNode.get(libraryRoot.id)).filter((edge) => [edge.source_id, edge.target_id].includes(neighborId));
          if (matchingEdges.length && matchingEdges.every((edge) => edge.evidence_state === "rejected")) return;
          const confirmed = matchingEdges.some(edgeConfirmed);
          addRelation(neighbor, confirmed ? "confirmed" : "candidate", {
            reason: matchingEdges.map((edge) => edge.reason_cn || edge.reason).filter(Boolean).join("；") || "Asset Graph relation",
            relationType: matchingEdges.map((edge) => edge.edge_type).filter(Boolean).join("+") || "asset_relation",
            source: matchingEdges.map((edge) => edge.source).filter(Boolean).join("+") || "asset_graph",
          });
        });
      }

      const action = projectActions.find((entry) => normalizePath(entry.path) === sourcePath);
      if (action) {
        safeArray(action.related_papers).forEach((paper) => addRelation(paper, referenceState(paper, "project_membership"), {
          reason: paper.match || paper.confidence || "Project action evidence",
          relationType: "paper_evidence",
          source: action.path,
          typeHint: "paper",
        }));
        safeArray(action.related_people).forEach((person) => addRelation(person, referenceState(person, "collaborator_role"), {
          reason: person.confidence || "Project action related person",
          relationType: "collaborator",
          source: action.path,
          typeHint: "person",
        }));
        safeArray(action.experience_links).forEach((entry) => addRelation(entry, "candidate", {
          reason: "可复用经验链接；仍需在当前事项下确认",
          relationType: "reuse_candidate",
          source: action.path,
          typeHint: entry.source_type || "material",
        }));
        safeArray(action.evidence_gaps).forEach((gap) => evidenceGaps.push(clean(gap)));
      }

      const relations = [...relationMap.values()].sort(relationSort);
      const baseIdentityState = project ? "exact_project" : matrixRoot ? "exact_asset_matrix" : libraryRoot ? "exact_asset_card" : sourcePath ? "source_only" : "unbound";
      const identityState = ["source_only", "unbound"].includes(baseIdentityState) && relations.length ? "portfolio_relations" : baseIdentityState;
      if (!relations.length && identityState === "source_only") evidenceGaps.push("当前 source_path 尚未连接到 Project Hub 或 Asset Graph；未按标题猜测关系。");
      if (!relations.length && identityState === "unbound") evidenceGaps.push("当前事项缺少可用于关系投影的 exact source identity。");
      return {
        candidateComponents: relations.filter((relation) => relation.state === "candidate"),
        confirmedComponents: relations.filter((relation) => relation.state === "confirmed"),
        evidenceGaps: dedupeStrings(evidenceGaps),
        identityState,
        itemId,
        itemTitle: clean(item.title) || itemId,
        rootComponentId: root?.id || "",
        sourcePath,
        sourceRoot,
      };
    }

    const compositions = Object.create(null);
    portfolioItems.forEach((item) => {
      const composition = compositionForItem(item);
      if (composition.itemId) compositions[composition.itemId] = composition;
    });

    const reverse = Object.create(null);
    function reverseEntry(componentId = "") {
      if (!reverse[componentId]) reverse[componentId] = { candidateItems: [], confirmedItems: [], rootItems: [] };
      return reverse[componentId];
    }
    Object.values(compositions).forEach((composition) => {
      const item = { id: composition.itemId, title: composition.itemTitle };
      if (composition.rootComponentId) reverseEntry(composition.rootComponentId).rootItems.push(item);
      composition.confirmedComponents.forEach((relation) => reverseEntry(relation.componentId).confirmedItems.push({ ...item, reasons: relation.reasons }));
      composition.candidateComponents.forEach((relation) => reverseEntry(relation.componentId).candidateItems.push({ ...item, reasons: relation.reasons }));
    });

    const componentList = [...components.values()].sort(relationSort);
    return Object.freeze({
      componentForId: (id = "") => components.get(clean(id)) || null,
      components: componentList,
      compositionForItem: (itemId = "") => compositions[clean(itemId)] || null,
      compositions,
      libraryIds: [...libraryIds],
      reverse,
      reverseForComponent: (componentId = "") => reverse[clean(componentId)] || { candidateItems: [], confirmedItems: [], rootItems: [] },
    });
  }

  global.ResearchOSItemCompositionModel = Object.freeze({
    build,
    inferredType,
    normalizePath,
  });
})(typeof window !== "undefined" ? window : globalThis);
