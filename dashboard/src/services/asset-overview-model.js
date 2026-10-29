/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端模型「asset overview model」；负责纯数据投影与排序选择，不绑定 DOM。
 * English: Frontend model for asset overview model in the ResearchOS dashboard; owns pure data projection and ordering, not DOM binding.
 */

(function attachResearchOSAssetOverviewModel(global) {
  const Contracts = global.ResearchOSContracts || {};
  function safeArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function numberValue(value) {
    return Number(value) || 0;
  }

  function assetCounts({ overview = {}, graph = {}, groups = [] } = {}, { toNumber = numberValue } = {}) {
    const materials = overview.materials || {};
    const researchMap = overview.research_map || {};
    const people = overview.people || {};
    const paperCount = toNumber(materials.reading_notes || safeArray(graph.papers).length);
    const talkCount = safeArray(graph.talks).length;
    const peopleCount = toNumber(people.registered_collaborators || safeArray(graph.people).length);
    const projectCount = toNumber(researchMap.project_pages || safeArray(graph.projects).length);
    return {
      activePeopleCount: toNumber(people.active_deep_collaborators || 0),
      activeProjectCount: toNumber(researchMap.active_projects || 0),
      atomTotal: paperCount + talkCount + peopleCount + projectCount,
      directionCount: toNumber(researchMap.mainline_count || safeArray(researchMap.mainlines).length),
      groupCount: safeArray(groups).length,
      paperCount,
      peopleCount,
      projectCount,
      talkCount,
    };
  }

  function assetRelationNodeId(type = "node", item = {}) {
    const raw = item.path || item.id || item.title || item.name || type;
    return `${type}:${String(raw).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 72)}`;
  }

  function normalizeDashboardPath(path = "", basePath = "") {
    const raw = String(path || "").trim();
    if (!raw) return "";
    if (!raw.startsWith(".")) return raw.replace(/^\/+/, "");
    const baseParts = String(basePath || "").split("/").filter(Boolean);
    if (baseParts.length) baseParts.pop();
    raw.split("/").forEach((part) => {
      if (!part || part === ".") return;
      if (part === "..") {
        baseParts.pop();
        return;
      }
      baseParts.push(part);
    });
    return baseParts.join("/");
  }

  function basenameTitle(path = "") {
    return String(path || "")
      .split("/")
      .filter(Boolean)
      .pop()
      ?.replace(/\.(md|json|jsonl|txt)$/i, "")
      .replaceAll("_", " ")
      .replaceAll("-", " ")
      .trim() || path;
  }

  function extractMarkdownPaths(text = "") {
    const pattern = /\b((?:00_identity|01_knowledge|02_decisions|03_cognition|04_people|05_workflows|06_active_context|07_archive|08_exports|09_templates|distilled|docs)\/[^\s`),\]}]+?\.md)(?:#[^\s`),\]}]+)?/g;
    const seen = new Set();
    const paths = [];
    let match;
    while ((match = pattern.exec(String(text || ""))) && paths.length < 80) {
      const path = String(match[1] || "").trim();
      if (!path || seen.has(path)) continue;
      seen.add(path);
      paths.push(path);
    }
    return paths;
  }

  function recentRunPathSet(runs = []) {
    const paths = new Set();
    safeArray(runs).forEach((run) => {
      [
        run.output,
        run.message,
        run.title,
        run.action_title,
        run.candidate?.save_target,
        run.candidate?.object_ref?.path,
      ].filter(Boolean).forEach((text) => {
        extractMarkdownPaths(text).forEach((path) => paths.add(path));
      });
    });
    return paths;
  }

  function documentIsRecent(doc = {}, recentPaths = new Set(), currentDate = "") {
    const path = String(doc.path || "").trim();
    if (path && recentPaths.has(path)) return true;
    const updated = String(doc.updated || "").slice(0, 10);
    return Boolean(currentDate && updated === currentDate && path.startsWith("08_exports/public_starter/"));
  }

  function assetDateValue(...values) {
    const found = values
      .map((value) => String(value || "").trim())
      .find(Boolean);
    return found ? found.slice(0, 10) : "";
  }

  function assetCardDateFields(item = {}) {
    return {
      card_created_date: assetDateValue(item.created, item.created_at, item.date_created),
      card_updated_date: assetDateValue(item.updated, item.updated_at, item.last_updated, item.modified),
    };
  }

  function assetRelationLevel(item = {}, fallback = 2) {
    if (item.needs_confirmation) return 1;
    if (item.confidence === "candidate" || item.confidence === "unknown") return 1;
    if (item.confidence === "medium") return 2;
    if (item.confidence === "high") return 3;
    return fallback;
  }

  function assetCardState(item = {}) {
    const confidence = String(item.confidence || "").toLowerCase();
    if (item.needs_confirmation || safeArray(item.missing_links).length || safeArray(item.evidence_needed).length) return "needs_evidence";
    if (confidence === "candidate" || confidence === "unknown") return "candidate";
    if (confidence === "high" || confidence === "source") return "confirmed";
    if (String(item.stage || "").includes("submitted")) return "local_only";
    return confidence === "medium" ? "candidate" : "confirmed";
  }

  function assetCardPreview(item = {}) {
    return item.next_step
      || safeArray(item.evidence_needed)[0]
      || safeArray(item.missing_links)[0]
      || safeArray(item.open_questions)[0]
      || item.reading_depth
      || item.match
      || item.mainline
      || "";
  }

  function assetCardBadgeList(item = {}, fallback = "") {
    return [
      item.stage_label || item.stage || "",
      item.mainline || "",
      item.confidence || fallback,
      item.match || "",
    ].filter(Boolean).slice(0, 3);
  }

  function assetCardLineageChips(paper = {}, translate = (key) => key) {
    const chips = [];
    const add = (kind, label, hint = "") => {
      if (!label || chips.some((item) => item.label === label)) return;
      chips.push({ kind, label, hint });
    };
    const stageLabel = paper.stage_label || paper.stage || "";
    const lowerStage = String(paper.stage || "").toLowerCase();
    if (stageLabel) {
      add(
        lowerStage.includes("submitted") || lowerStage.includes("active") ? "active" : "stage",
        stageLabel,
        translate("assetLineageStageHint"),
      );
    }
    if (paper.mainline) add("mainline", paper.mainline, translate("assetLineageMainlineHint"));
    const projects = safeArray(paper.projects || paper.related_projects);
    if (projects.length) {
      add("project", translate("assetLineageSameProject"), projects.slice(0, 2).map((item) => item.title || item.name || "").filter(Boolean).join(" / "));
    }
    if (safeArray(paper.people).length) {
      add("people", translate("assetLineagePeople"), safeArray(paper.people).slice(0, 2).map((item) => item.title || item.name || "").filter(Boolean).join(" / "));
    }
    if (safeArray(paper.talks).length) add("talk", translate("assetLineageReport"), translate("assetLineageReportHint"));
    if (!chips.length) add("pending", translate("assetLineagePending"), translate("assetLineagePendingHint"));
    return chips.slice(0, 5);
  }

  function materialLevelLookup(items = []) {
    const lookup = new Map();
    safeArray(items).forEach((item) => {
      const state = item.analysis_state || "";
      const short = item.analysis_state_short_label || String(state).slice(0, 2) || "";
      const label = item.analysis_state_label || item.level_label || short || "";
      [item.path, item.title, item.id].filter(Boolean).forEach((key) => {
        lookup.set(String(key), {
          analysis_state: state,
          analysis_state_label: label,
          analysis_state_short_label: short,
        });
      });
    });
    return lookup;
  }

  function compactAssetIntelligence(profile = {}) {
    const material = profile.material_maturity || {};
    const person = profile.person_maturity || null;
    const analysisState = material.level || "";
    return {
      analysis_state: analysisState,
      analysis_state_label: material.label_zh || "",
      analysis_state_short_label: material.short_label || String(analysisState).slice(0, 2) || "",
      asset_importance: profile.asset_importance || {},
      asset_intelligence: profile,
      material_maturity: material,
      maturity_reason_cn: material.reason_cn || "",
      person_maturity: person,
      person_maturity_label: person?.label_zh || "",
      person_maturity_level: person?.level || "",
    };
  }

  function assetIntelligenceLookup(items = []) {
    const lookup = new Map();
    safeArray(items).forEach((item) => {
      const compact = compactAssetIntelligence(item);
      [
        item.asset_id,
        item.path,
        item.title,
      ].filter(Boolean).forEach((key) => {
        lookup.set(String(key), compact);
      });
    });
    return lookup;
  }

  function assetHierarchyLookups(hierarchy = {}) {
    const researcherByPath = new Map();
    const projectCoverageByPath = new Map();
    const clusterByPath = new Map();
    const directionByMainline = new Map();
    safeArray(hierarchy.researcher_relation_profiles).forEach((item) => {
      const relation = item.relation_to_researcher || {};
      const compact = {
        researcher_relation_label: relation.label_zh || "",
        researcher_relation_level: relation.level || "",
        researcher_relation_reason: relation.reason_cn || "",
        researcher_relation_score: relation.score || 0,
      };
      [item.path, item.title, item.asset_id].filter(Boolean).forEach((key) => researcherByPath.set(String(key), compact));
    });
    safeArray(hierarchy.project_coverage_profiles).forEach((item) => {
      const compact = {
        hierarchy_recommendation_cn: item.recommendation_cn || "",
        hierarchy_state: item.coverage_state || "",
        hierarchy_state_label: item.coverage_label_zh || "",
        hierarchy_summary_cn: item.summary_cn || "",
        project_promotion_status: item.promotion_status || "",
        project_promotion_label: item.promotion_label_zh || "",
      };
      [item.path, item.title, item.project_id].filter(Boolean).forEach((key) => projectCoverageByPath.set(String(key), compact));
    });
    safeArray(hierarchy.directions).forEach((direction) => {
      if (direction.mainline) {
        directionByMainline.set(String(direction.mainline), {
          direction_level: direction.direction_level || "",
          direction_summary_cn: direction.summary_cn || "",
        });
      }
    });
    safeArray(hierarchy.clusters).forEach((cluster) => {
      const compact = {
        cluster_label_zh: cluster.cluster_label_zh || "",
        cluster_level: cluster.cluster_level || "",
        cluster_recommendation_cn: cluster.recommendation_cn || "",
        cluster_summary_cn: cluster.summary_cn || "",
        direction_level: directionByMainline.get(String(cluster.mainline || ""))?.direction_level || "",
        direction_summary_cn: directionByMainline.get(String(cluster.mainline || ""))?.direction_summary_cn || "",
        mainline: cluster.mainline || "",
        project_family: cluster.project_family || "",
      };
      safeArray(cluster.papers).forEach((item) => {
        [item.path, item.title].filter(Boolean).forEach((key) => clusterByPath.set(String(key), compact));
      });
      safeArray(cluster.projects).forEach((item) => {
        [item.path, item.title].filter(Boolean).forEach((key) => clusterByPath.set(String(key), compact));
      });
      safeArray(cluster.people).forEach((item) => {
        [item.path, item.name, item.title].filter(Boolean).forEach((key) => clusterByPath.set(String(key), compact));
      });
      safeArray(cluster.talks).forEach((item) => {
        [item.path, item.title].filter(Boolean).forEach((key) => clusterByPath.set(String(key), compact));
      });
    });
    const match = (item = {}) => {
      const keys = [item.path, item.title, item.name, item.id].filter(Boolean).map(String);
      const merged = {};
      keys.forEach((key) => {
        Object.assign(merged, researcherByPath.get(key) || {}, projectCoverageByPath.get(key) || {}, clusterByPath.get(key) || {});
      });
      return merged;
    };
    return { match };
  }

  function assetCardMaturity(item = {}, maturityLookup = new Map(), intelligenceLookup = new Map(), assetType = "") {
    const intelligenceId = assetRelationNodeId(assetType || item.type || "asset", item);
    const intelligenceMatched = intelligenceLookup.get(intelligenceId)
      || intelligenceLookup.get(String(item.path || ""))
      || intelligenceLookup.get(String(item.title || item.name || ""))
      || intelligenceLookup.get(String(item.id || ""));
    if (intelligenceMatched) return intelligenceMatched;
    const matched = maturityLookup.get(String(item.path || ""))
      || maturityLookup.get(String(item.title || item.name || ""))
      || maturityLookup.get(String(item.id || ""));
    if (matched) return matched;
    return {
      analysis_state: item.analysis_state || "",
      analysis_state_label: item.analysis_state_label || "",
      analysis_state_short_label: item.analysis_state_short_label || "",
      asset_importance: {},
      asset_intelligence: null,
      material_maturity: null,
      maturity_reason_cn: "",
      person_maturity: null,
      person_maturity_label: item.person_maturity_label || "",
      person_maturity_level: item.person_maturity_level || "",
    };
  }

  function relationEvidenceLookup(items = [], evidence = []) {
    const lookup = new Map();
    const rawById = new Map(safeArray(evidence).filter((item) => item.edge_id).map((item) => [item.edge_id, item]));
    const stateLabels = { confirmed: "已确认", candidate: "候选关系", weak_inferred: "弱推断", rejected: "已排除" };
    safeArray(items).forEach((explanation) => {
      const raw = rawById.get(explanation.edge_id);
      const item = raw || explanation;
      const sameState = !raw || (raw.evidence_state === explanation.evidence_state
        && raw.weight === explanation.weight && raw.needs_confirmation === explanation.needs_confirmation);
      const score = Number(item.weight ?? item.relation_score);
      const summary = [
        explanation.edge_type_label_zh || item.edge_type || "",
        Number.isFinite(score) ? `排序分 ${score}` : "",
        item.evidence_state === "confirmed" && item.needs_confirmation
          ? "待复核关系" : stateLabels[item.evidence_state] || "关系状态待核对",
        item.confidence || "",
        item.reason || item.reason_cn || "",
        sameState ? explanation.why_not_stronger_cn || "" : "",
      ].filter(Boolean).join(" · ");
      [item.source_id, item.target_id].filter(Boolean).forEach((id) => {
        if (!lookup.has(id)) lookup.set(id, []);
        lookup.get(id).push(summary);
      });
    });
    return lookup;
  }

  function relationReasonsFor(id = "", lookup = new Map(), limit = 4) {
    return safeArray(lookup.get(id)).slice(0, limit);
  }

  function addRelation(cardMap, fromId, toId) {
    if (!fromId || !toId || fromId === toId) return;
    const from = cardMap.get(fromId);
    const to = cardMap.get(toId);
    if (!from || !to) return;
    from.relationSet.add(toId);
    to.relationSet.add(fromId);
  }

  function addRankedRelation(cardMap, fromId, toId, fromRank = 9999, toRank = 9999) {
    addRelation(cardMap, fromId, toId);
    const from = cardMap.get(fromId);
    const to = cardMap.get(toId);
    const normalizedFromRank = Number(fromRank);
    const normalizedToRank = Number(toRank);
    if (from) {
      from.relationRankMap.set(toId, Math.min(Number(from.relationRankMap.get(toId) ?? 9999), Number.isFinite(normalizedFromRank) ? normalizedFromRank : 9999));
    }
    if (to) {
      to.relationRankMap.set(fromId, Math.min(Number(to.relationRankMap.get(fromId) ?? 9999), Number.isFinite(normalizedToRank) ? normalizedToRank : 9999));
    }
  }

  function upsertAssetCard(cardMap, rawCard = {}) {
    if (!rawCard.id) return null;
    const existing = cardMap.get(rawCard.id);
    if (existing) {
      existing.score = Math.max(existing.score || 0, rawCard.score || 0);
      existing.relation_count = Math.max(existing.relation_count || 0, rawCard.relation_count || 0);
      existing.badges = [...new Set([...(existing.badges || []), ...(rawCard.badges || [])])].slice(0, 4);
      if (!existing.preview && rawCard.preview) existing.preview = rawCard.preview;
      if (!existing.affinity_source && rawCard.affinity_source) existing.affinity_source = rawCard.affinity_source;
      if (!existing.relationship_group && rawCard.relationship_group) existing.relationship_group = rawCard.relationship_group;
      [
        "cluster_label_zh",
        "cluster_level",
        "cluster_recommendation_cn",
        "cluster_summary_cn",
        "direction_level",
        "direction_summary_cn",
        "hierarchy_recommendation_cn",
        "hierarchy_state",
        "hierarchy_state_label",
        "hierarchy_summary_cn",
        "mainline",
        "operational_status",
        "portfolio_binding",
        "project_family",
        "project_promotion_label",
        "project_promotion_status",
        "researcher_relation_label",
        "researcher_relation_level",
        "researcher_relation_reason",
        "researcher_relation_score",
      ].forEach((key) => {
        if (!existing[key] && rawCard[key]) existing[key] = rawCard[key];
      });
      if (rawCard.mainline_priority !== undefined) {
        const nextPriority = Number(rawCard.mainline_priority);
        if (Number.isFinite(nextPriority)) existing.mainline_priority = Math.min(Number(existing.mainline_priority ?? 99), nextPriority);
      }
      if (rawCard.relation_priority !== undefined) {
        const nextRelationPriority = Number(rawCard.relation_priority);
        if (Number.isFinite(nextRelationPriority)) existing.relation_priority = Math.min(Number(existing.relation_priority ?? 9999), nextRelationPriority);
      }
      const incomingResearcherScore = Number(rawCard.researcher_relation_score || rawCard.relation_to_researcher_score || 0);
      const existingResearcherScore = Number(existing.researcher_relation_score || existing.relation_to_researcher_score || 0);
      if (Number.isFinite(incomingResearcherScore) && incomingResearcherScore > existingResearcherScore) {
        existing.researcher_relation_score = incomingResearcherScore;
        existing.relation_to_researcher_score = incomingResearcherScore;
        existing.researcher_relation_label = rawCard.researcher_relation_label || rawCard.relation_to_researcher_label_zh || existing.researcher_relation_label || "";
        existing.relation_to_researcher_label_zh = rawCard.relation_to_researcher_label_zh || rawCard.researcher_relation_label || existing.relation_to_researcher_label_zh || "";
        existing.researcher_relation_reason = rawCard.researcher_relation_reason || rawCard.relation_to_researcher_reason_cn || existing.researcher_relation_reason || "";
        existing.relation_to_researcher_reason_cn = rawCard.relation_to_researcher_reason_cn || rawCard.researcher_relation_reason || existing.relation_to_researcher_reason_cn || "";
        if (rawCard.subtitle) existing.subtitle = rawCard.subtitle;
        if (rawCard.preview) existing.preview = rawCard.preview;
      }
      return existing;
    }
    const created = {
      affinity_source: "",
      badges: [],
      box_id: "",
      level: 2,
      mainline_priority: 99,
      path: "",
      preview: "",
      relation_priority: 9999,
      relation_count: 0,
      relationRankMap: new Map(),
      relationSet: new Set(),
      relationship_group: "",
      score: 0,
      state: "confirmed",
      subtitle: "",
      title: "",
      type: "asset",
      ...rawCard,
    };
    cardMap.set(created.id, created);
    return created;
  }

  function serializeAssetCard(card = {}) {
    const { relationRankMap, relationSet, ...rest } = card;
    const cardMaturity = Contracts.cardMaturityProfile?.(card.type || "asset", card) || null;
    return {
      ...rest,
      card_maturity: cardMaturity,
      relation_ids: [...(relationSet || new Set())],
      relation_ranks: Object.fromEntries([...(relationRankMap || new Map()).entries()]),
    };
  }

  function normalizeAssetAffinityText(value = "") {
    return String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 80);
  }

  function readableAssetAffinityLabel(value = "") {
    const text = String(value || "").trim();
    if (!text) return "";
    if (text === "high_trust_group") return "High-trust collaboration group";
    if (text === "high_trust_young_collaborators") return "High-trust young collaborators";
    return text
      .replace(/[_-]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function assetMainlinePriority(value = "") {
    const text = String(value || "").toLowerCase();
    if (text.includes("evidence") || text.includes("multimodal") || text.includes("reasoning")) return 0;
    if (text.includes("education") || text.includes("student") || text.includes("learning")) return 1;
    if (text.includes("vision") || text.includes("temporal") || text.includes("evaluation")) return 2;
    if (text.includes("application") || text.includes("hci") || text.includes("social") || text.includes("human")) return 4;
    if (text.includes("open-environment") || text.includes("reliability") || text.includes("robust")) return 3;
    if (text.includes("boundary") || text.includes("transfer") || text.includes("collaboration")) return 5;
    if (text.includes("high-trust")) return 0;
    return 6;
  }

  function assetCardRelationNeighbors(card = {}, cardMap = new Map()) {
    return [...(card.relationSet || new Set())]
      .map((id) => cardMap.get(id))
      .filter(Boolean);
  }

  function strongestAssetCardNeighbor(neighbors = [], type = "", toNumber = numberValue) {
    return safeArray(neighbors)
      .filter((item) => !type || item.type === type)
      .sort((a, b) => {
        const scoreDelta = toNumber(b.score) - toNumber(a.score);
        if (scoreDelta) return scoreDelta;
        const relationDelta = toNumber(b.relation_count) - toNumber(a.relation_count);
        if (relationDelta) return relationDelta;
        return String(a.title || "").localeCompare(String(b.title || ""));
      })[0] || null;
  }

  function assetCardAffinityGroup(card = {}, cardMap = new Map(), toNumber = numberValue) {
    const neighbors = assetCardRelationNeighbors(card, cardMap);
    const paper = card.type === "paper" ? card : strongestAssetCardNeighbor(neighbors, "paper", toNumber);
    const project = card.type === "project" ? card : strongestAssetCardNeighbor(neighbors, "project", toNumber);
    const person = card.type === "person" ? card : strongestAssetCardNeighbor(neighbors, "person", toNumber);
    const talk = card.type === "talk" ? card : strongestAssetCardNeighbor(neighbors, "talk", toNumber);
    const explicitAffinity = readableAssetAffinityLabel(card.relationship_group || card.affinity_source || "");
    const neighborAffinity = readableAssetAffinityLabel(paper?.affinity_source || project?.affinity_source || person?.relationship_group || talk?.affinity_source || "");
    const label = explicitAffinity
      || neighborAffinity
      || paper?.subtitle
      || project?.title
      || person?.title
      || talk?.title
      || card.subtitle
      || card.title
      || card.type
      || "asset";
    const key = normalizeAssetAffinityText(label) || normalizeAssetAffinityText(card.title) || "asset";
    return {
      key,
      label,
    };
  }

  function assignAssetCardAffinityGroups(cardMap = new Map(), toNumber = numberValue) {
    cardMap.forEach((card) => {
      const group = assetCardAffinityGroup(card, cardMap, toNumber);
      card.affinity_group = group.key;
      card.affinity_label = group.label;
      card.mainline_priority = Math.min(Number(card.mainline_priority ?? 99), assetMainlinePriority(`${card.affinity_label} ${card.subtitle} ${card.title}`));
      card.related_people_preview = assetCardRelationNeighbors(card, cardMap)
        .filter((item) => item.type === "person")
        .sort((left, right) => Number(left.relation_priority || 9999) - Number(right.relation_priority || 9999))
        .map((item) => ({ id: item.id, path: item.path || "", title: item.title || "" }));
    });
  }

  function sortedAssetCards(cards = [], { toNumber = numberValue } = {}) {
    const serialized = safeArray(cards).map(serializeAssetCard);
    const groupStats = new Map();
    serialized.forEach((card) => {
      const key = card.affinity_group || card.id || "";
      const current = groupStats.get(key) || {
        maxRelation: 0,
        maxScore: 0,
        maxResearcherRelation: 0,
        minPriority: 99,
      };
      current.maxRelation = Math.max(current.maxRelation, toNumber(card.relation_count));
      current.maxScore = Math.max(current.maxScore, toNumber(card.score));
      current.maxResearcherRelation = Math.max(current.maxResearcherRelation, toNumber(card.researcher_relation_score || card.relation_to_researcher_score));
      current.minPriority = Math.min(current.minPriority, toNumber(card.mainline_priority ?? 99));
      groupStats.set(key, current);
    });
    return serialized
      .sort((a, b) => {
        const aGroup = groupStats.get(a.affinity_group || a.id || "") || {};
        const bGroup = groupStats.get(b.affinity_group || b.id || "") || {};
        const groupPriorityDelta = toNumber(aGroup.minPriority ?? 99) - toNumber(bGroup.minPriority ?? 99);
        if (groupPriorityDelta) return groupPriorityDelta;
        const groupResearcherDelta = toNumber(bGroup.maxResearcherRelation) - toNumber(aGroup.maxResearcherRelation);
        if (groupResearcherDelta) return groupResearcherDelta;
        const groupScoreDelta = toNumber(bGroup.maxScore) - toNumber(aGroup.maxScore);
        if (groupScoreDelta) return groupScoreDelta;
        const groupRelationDelta = toNumber(bGroup.maxRelation) - toNumber(aGroup.maxRelation);
        if (groupRelationDelta) return groupRelationDelta;
        const affinityDelta = String(a.affinity_group || "").localeCompare(String(b.affinity_group || ""));
        if (affinityDelta) return affinityDelta;
        const researcherDelta = toNumber(b.researcher_relation_score || b.relation_to_researcher_score) - toNumber(a.researcher_relation_score || a.relation_to_researcher_score);
        if (researcherDelta) return researcherDelta;
        const scoreDelta = toNumber(b.score) - toNumber(a.score);
        if (scoreDelta) return scoreDelta;
        const relationDelta = toNumber(b.relation_count) - toNumber(a.relation_count);
        if (relationDelta) return relationDelta;
        return String(a.title || "").localeCompare(String(b.title || ""));
      });
  }

  function assetRelationItemRank(item = {}, fallbackIndex = 0, toNumber = numberValue) {
    const semanticScore = toNumber(item.relation_to_paper_score);
    if (Number.isFinite(semanticScore) && semanticScore > 0) {
      return 10000 - semanticScore * 10 + fallbackIndex;
    }
    const rolePriority = toNumber(item.role_priority);
    const authorRank = toNumber(item.author_rank);
    if (Number.isFinite(rolePriority) && rolePriority < 9999) {
      return rolePriority * 100 + (Number.isFinite(authorRank) && authorRank > 0 ? authorRank : fallbackIndex + 1);
    }
    return fallbackIndex + 1;
  }

  function shouldShowStandaloneProjectCard(card = {}) {
    if (card.project_promotion_status === "attach_to_atom") return false;
    const state = String(card.hierarchy_state || "");
    if (state === "isolated_seed" || state === "narrow_project") return false;
    return true;
  }

  function assetCardBoxesModel(matrix = [], options = {}) {
    const {
      currentDate = "",
      cardStateLookup = new Map(),
      evidenceLookup = new Map(),
      intelligenceLookup = new Map(),
      maturityLookup = new Map(),
      previewDocuments = [],
      projects = [],
      people = [],
      recentRuns = [],
      talks = [],
      toNumber = numberValue,
      translate = (key) => key,
    } = options;
    const displayLimit = 4;
    const cardMap = new Map();
    const recentPaths = recentRunPathSet(recentRuns);
    const hierarchyLookup = options.hierarchyLookup || { match: () => ({}) };
    const boxCardIds = {
      group: [],
      paper: [],
      person: [],
      project: [],
      talk: [],
    };
    const selected = safeArray(matrix)
      .slice()
      .sort((a, b) => toNumber(b.score) - toNumber(a.score));

    selected.forEach((paper) => {
      const paperId = assetRelationNodeId("paper", paper);
      const paperMaturity = assetCardMaturity(paper, maturityLookup, intelligenceLookup, "paper");
      const paperHierarchy = hierarchyLookup.match(paper);
      upsertAssetCard(cardMap, {
        id: paperId,
        badges: assetCardBadgeList(paper),
        card_maturity_level: paper.card_maturity_level || "",
        analysis_state: paperMaturity.analysis_state,
        analysis_state_label: paperMaturity.analysis_state_label,
        analysis_state_short_label: paperMaturity.analysis_state_short_label,
        asset_importance: paperMaturity.asset_importance,
        asset_intelligence: paperMaturity.asset_intelligence,
        box_id: "box:paper",
        level: paper.needs_confirmation ? 2 : 3,
        material_maturity: paperMaturity.material_maturity,
        maturity_reason_cn: paperMaturity.maturity_reason_cn,
        path: paper.path || "",
        preview: assetCardPreview(paper),
        ...assetCardDateFields(paper),
        affinity_source: paper.project_family || paper.mainline || "",
        mainline_priority: assetMainlinePriority(`${paper.mainline || ""} ${paper.project_family || ""} ${paper.title || ""}`),
        relation_count: toNumber(paper.relation_count),
        relation_reasons: relationReasonsFor(paperId, evidenceLookup),
        ...paperHierarchy,
        lineage_chips: assetCardLineageChips(paper, translate),
        score: toNumber(paper.score),
        state: assetCardState(paper),
        subtitle: paper.mainline || paper.stage_label || "",
        title: paper.title || paper.path || "",
        type: "paper",
      });
      boxCardIds.paper.push(paperId);

      safeArray(paper.projects).forEach((project, projectIndex) => {
        const id = assetRelationNodeId("project", project);
        const maturity = assetCardMaturity(project, maturityLookup, intelligenceLookup, "project");
        const projectHierarchy = hierarchyLookup.match(project);
        upsertAssetCard(cardMap, {
          id,
          badges: assetCardBadgeList(project),
          card_maturity_level: project.card_maturity_level || "",
          analysis_state: maturity.analysis_state,
          analysis_state_label: maturity.analysis_state_label,
          analysis_state_short_label: maturity.analysis_state_short_label,
          asset_importance: maturity.asset_importance,
          asset_intelligence: maturity.asset_intelligence,
          box_id: "box:project",
          level: assetRelationLevel(project),
          material_maturity: maturity.material_maturity,
          maturity_reason_cn: maturity.maturity_reason_cn,
          path: project.path || "",
          operational_status: project.operational_status || {},
          portfolio_binding: project.portfolio_binding || {},
          legacy_active_project_candidate: Boolean(project.legacy_active_project_candidate),
          active_project_candidate: Boolean(project.active_project_candidate),
          active_project_candidate_source: project.active_project_candidate_source || "",
          project_maturity: project.project_maturity || project.incubation_maturity || "",
          preview: project.match || project.confidence || "",
          ...assetCardDateFields(project),
          affinity_source: paper.project_family || paper.mainline || project.match || "",
          mainline_priority: assetMainlinePriority(`${paper.mainline || ""} ${paper.project_family || ""} ${project.title || ""}`),
          relation_priority: projectIndex + 1,
          relation_count: 1,
          relation_reasons: relationReasonsFor(id, evidenceLookup),
          ...projectHierarchy,
          score: toNumber(paper.score),
          state: assetCardState(project),
          subtitle: project.confidence || project.match || "",
          title: project.title || project.name || "",
          type: "project",
        });
        if (shouldShowStandaloneProjectCard(cardMap.get(id))) boxCardIds.project.push(id);
        addRankedRelation(cardMap, paperId, id, projectIndex + 1, toNumber(paper.score));
      });

      safeArray(paper.people).forEach((person, personIndex) => {
        const id = assetRelationNodeId("person", person);
        const maturity = assetCardMaturity(person, maturityLookup, intelligenceLookup, "person");
        const personHierarchy = hierarchyLookup.match(person);
        const relationPriority = assetRelationItemRank(person, personIndex, toNumber);
        upsertAssetCard(cardMap, {
          id,
          badges: assetCardBadgeList(person),
          card_maturity_level: person.card_maturity_level || "",
          analysis_state: maturity.analysis_state,
          analysis_state_label: maturity.analysis_state_label,
          analysis_state_short_label: maturity.analysis_state_short_label,
          asset_importance: maturity.asset_importance,
          asset_intelligence: maturity.asset_intelligence,
          box_id: "box:person",
          level: assetRelationLevel(person),
          material_maturity: maturity.material_maturity,
          maturity_reason_cn: maturity.maturity_reason_cn,
          path: person.path || "",
          person_maturity: maturity.person_maturity,
          person_maturity_label: maturity.person_maturity_label,
          person_maturity_level: maturity.person_maturity_level,
          relationship_maturity: person.relationship_maturity || person.relationship_maturity_level || "",
          relationship_maturity_reason: person.relationship_maturity_reason || "",
          preview: person.relation_to_paper_label_zh || person.role || person.match || person.confidence || "",
          ...assetCardDateFields(person),
          affinity_source: person.relationship_group || person.tags || paper.project_family || paper.mainline || "",
          mainline_priority: assetMainlinePriority(`${person.relationship_group || ""} ${person.tags || ""} ${paper.mainline || ""} ${paper.project_family || ""}`),
          relation_priority: relationPriority,
          relation_to_paper_score: person.relation_to_paper_score || "",
          relation_to_paper_label_zh: person.relation_to_paper_label_zh || "",
          relation_to_paper_reason_cn: person.relation_to_paper_reason_cn || "",
          relationship_group: person.relationship_group || "",
          relation_count: 1,
          relation_reasons: relationReasonsFor(id, evidenceLookup),
          ...personHierarchy,
          score: toNumber(paper.score),
          state: assetCardState(person),
          subtitle: person.relation_to_paper_reason_cn || readableAssetAffinityLabel(person.relationship_group || "") || person.confidence || person.match || "",
          title: person.title || person.name || "",
          type: "person",
        });
        boxCardIds.person.push(id);
        addRankedRelation(cardMap, paperId, id, relationPriority, toNumber(paper.score));
      });

      safeArray(paper.projects).forEach((project, projectIndex) => {
        const projectId = assetRelationNodeId("project", project);
        safeArray(paper.people).forEach((person, personIndex) => {
          const personId = assetRelationNodeId("person", person);
          addRankedRelation(cardMap, projectId, personId, personIndex + 1, projectIndex + 1);
        });
      });

      safeArray(paper.talks).forEach((talk, talkIndex) => {
        const id = assetRelationNodeId("talk", talk);
        const maturity = assetCardMaturity(talk, maturityLookup, intelligenceLookup, "talk");
        const talkHierarchy = hierarchyLookup.match(talk);
        const researcherRelationScore = toNumber(talk.relation_to_researcher_score || talkHierarchy.researcher_relation_score);
        const researcherRelationLabel = talk.relation_to_researcher_label_zh || talkHierarchy.researcher_relation_label || "";
        const researcherRelationReason = talk.relation_to_researcher_reason_cn || talkHierarchy.researcher_relation_reason || "";
        upsertAssetCard(cardMap, {
          id,
          badges: assetCardBadgeList(talk),
          card_maturity_level: talk.card_maturity_level || "",
          analysis_state: maturity.analysis_state,
          analysis_state_label: maturity.analysis_state_label,
          analysis_state_short_label: maturity.analysis_state_short_label,
          asset_importance: maturity.asset_importance,
          asset_intelligence: maturity.asset_intelligence,
          box_id: "box:talk",
          level: assetRelationLevel(talk),
          material_maturity: maturity.material_maturity,
          maturity_reason_cn: maturity.maturity_reason_cn,
          path: talk.path || "",
          preview: researcherRelationLabel || talk.match || talk.confidence || "",
          ...assetCardDateFields(talk),
          affinity_source: paper.project_family || paper.mainline || talk.match || "",
          mainline_priority: assetMainlinePriority(`${paper.mainline || ""} ${paper.project_family || ""} ${talk.title || ""}`),
          relation_priority: talkIndex + 1,
          relation_count: 1,
          relation_reasons: relationReasonsFor(id, evidenceLookup),
          ...talkHierarchy,
          relation_to_researcher_score: researcherRelationScore,
          relation_to_researcher_label_zh: researcherRelationLabel,
          relation_to_researcher_reason_cn: researcherRelationReason,
          researcher_relation_score: researcherRelationScore,
          researcher_relation_label: researcherRelationLabel,
          researcher_relation_reason: researcherRelationReason,
          score: toNumber(paper.score),
          state: assetCardState(talk),
          subtitle: researcherRelationReason || talk.confidence || talk.match || "",
          title: talk.title || talk.name || "",
          type: "talk",
        });
        boxCardIds.talk.push(id);
        addRankedRelation(cardMap, paperId, id, talkIndex + 1, toNumber(paper.score));
      });

    });

    // The paper relation matrix supplies relationships, not the library inventory.
    // A registered source remains discoverable even when it has no paper edge.
    [["project", projects], ["person", people]].forEach(([type, sources]) => {
      safeArray(sources).forEach((asset) => {
        const id = assetRelationNodeId(type, asset);
        if (!cardMap.has(id)) {
          const maturity = assetCardMaturity(asset, maturityLookup, intelligenceLookup, type);
          upsertAssetCard(cardMap, {
            ...asset,
            ...maturity,
            ...hierarchyLookup.match(asset),
            ...assetCardDateFields(asset),
            id,
            type,
            box_id: `box:${type}`,
            path: asset.path || "",
            title: asset.title || asset.name || "",
            badges: assetCardBadgeList(asset),
            preview: asset.summary || "",
            subtitle: asset.summary || "",
            level: assetRelationLevel(asset),
            state: assetCardState(asset),
            score: 0,
            relation_count: 0,
            relation_reasons: relationReasonsFor(id, evidenceLookup),
          });
        }
        boxCardIds[type].push(id);
      });
    });

    safeArray(talks).forEach((talk, talkIndex) => {
      const id = assetRelationNodeId("talk", talk);
      const maturity = assetCardMaturity(talk, maturityLookup, intelligenceLookup, "talk");
      const talkHierarchy = hierarchyLookup.match(talk);
      const researcherRelationScore = toNumber(talk.relation_to_researcher_score || talkHierarchy.researcher_relation_score);
      const researcherRelationLabel = talk.relation_to_researcher_label_zh || talkHierarchy.researcher_relation_label || "";
      const researcherRelationReason = talk.relation_to_researcher_reason_cn || talkHierarchy.researcher_relation_reason || "";
      upsertAssetCard(cardMap, {
        id,
        badges: [
          researcherRelationLabel,
          talk.analysis_state_short_label || maturity.analysis_state_short_label || "",
          talk.matched_paper_count ? `${talk.matched_paper_count} paper links` : "",
        ].filter(Boolean).slice(0, 3),
        card_maturity_level: talk.card_maturity_level || "",
        analysis_state: maturity.analysis_state || talk.analysis_state || "",
        analysis_state_label: maturity.analysis_state_label || talk.analysis_state_label || "",
        analysis_state_short_label: maturity.analysis_state_short_label || talk.analysis_state_short_label || "",
        asset_importance: maturity.asset_importance,
        asset_intelligence: maturity.asset_intelligence,
        box_id: "box:talk",
        level: researcherRelationScore >= 85 ? 3 : researcherRelationScore >= 65 ? 2 : 1,
        material_maturity: maturity.material_maturity,
        maturity_reason_cn: maturity.maturity_reason_cn,
        path: talk.path || "",
        preview: researcherRelationLabel || talk.talk_type || talk.status || "",
        ...assetCardDateFields(talk),
        affinity_source: talk.mainline || talk.talk_type || "",
        mainline_priority: Math.max(0, 9 - Math.floor(researcherRelationScore / 12)),
        relation_priority: talkIndex + 1,
        relation_count: toNumber(talk.matched_paper_count || talk.mapping_section_count || 0),
        relation_reasons: relationReasonsFor(id, evidenceLookup),
        ...talkHierarchy,
        relation_to_researcher_score: researcherRelationScore,
        relation_to_researcher_label_zh: researcherRelationLabel,
        relation_to_researcher_reason_cn: researcherRelationReason,
        researcher_relation_score: researcherRelationScore,
        researcher_relation_label: researcherRelationLabel,
        researcher_relation_reason: researcherRelationReason,
        score: researcherRelationScore,
        state: assetCardState(talk),
        subtitle: researcherRelationReason || talk.judgment || talk.summary || "",
        title: talk.title || "",
        type: "talk",
      });
      boxCardIds.talk.push(id);
    });

    cardMap.forEach((card) => {
      const profile = cardStateLookup.get(String(card.path || ""));
      if (!profile) return;
      for (const key of [
        "cleanup_disposition",
        "current_action",
        "operational_status",
        "portfolio_binding",
        "primary_maturity",
        "relation_status",
        "review_reasons",
        "role_state",
        "source_material_maturity",
        "source_type",
      ]) {
        if (profile[key] !== undefined) card[key] = profile[key];
      }
    });

    assignAssetCardAffinityGroups(cardMap, toNumber);

    safeArray(previewDocuments)
      .filter((doc) => String(doc.type || "").trim() === "relationship_pattern" && String(doc.path || "").trim())
      .forEach((doc, index) => {
        const id = assetRelationNodeId("group", doc);
        const relatedPeople = safeArray(doc.related_people)
          .map((path) => normalizeDashboardPath(path, doc.path))
          .filter(Boolean);
        const sourceFiles = safeArray(doc.source_files)
          .map((path) => normalizeDashboardPath(path, doc.path))
          .filter(Boolean);
        const isRecent = documentIsRecent(doc, recentPaths, currentDate);
        upsertAssetCard(cardMap, {
          id,
          badges: [
            translate("assetsTypeGroup"),
            doc.sensitivity || "",
          ].filter(Boolean),
          analysis_state: "M3_cross_project_deepening",
          analysis_state_label: translate("assetRelationshipPatternState"),
          analysis_state_short_label: "G",
          group_level: "G1",
          box_id: "box:group",
          level: isRecent ? 3 : 2,
          mainline_priority: 0,
          path: doc.path || "",
          ...assetCardDateFields(doc),
          preview: relatedPeople.length
            ? `${translate("assetRelationshipPatternRelatedPeople")}: ${relatedPeople.map(basenameTitle).join(" / ")}`
            : translate("assetRelationshipPatternPreview"),
          relation_count: relatedPeople.length + sourceFiles.length,
          score: isRecent ? 1000 - index : 320 - index,
          state: "confirmed",
          subtitle: doc.status || doc.sensitivity || "",
          title: doc.title || basenameTitle(doc.path),
          type: "group",
        });
        boxCardIds.group.push(id);
        relatedPeople.forEach((personPath, personIndex) => {
          const personId = assetRelationNodeId("person", { path: personPath });
          addRankedRelation(cardMap, id, personId, personIndex + 1, isRecent ? 0 : 20 + personIndex);
        });
        sourceFiles.forEach((sourcePath, sourceIndex) => {
          const sourceId = assetRelationNodeId(sourcePath.startsWith("04_people/") ? "person" : "project", { path: sourcePath });
          addRankedRelation(cardMap, id, sourceId, 20 + sourceIndex, 40 + sourceIndex);
        });
      });

    const boxDefinitions = [
      ["paper", translate("assetsBoxPaper"), translate("assetsBoxPaperRule")],
      ["group", translate("assetsBoxGroup"), translate("assetsBoxGroupRule")],
      ["project", translate("assetsBoxProject"), translate("assetsBoxProjectRule")],
      ["person", translate("assetsBoxPeople"), translate("assetsBoxPeopleRule")],
      ["talk", translate("assetsBoxTalk"), translate("assetsBoxTalkRule")],
    ];

    return boxDefinitions.map(([type, label, sortRule]) => {
      const cards = sortedAssetCards([...new Set(boxCardIds[type])].map((id) => cardMap.get(id)).filter(Boolean), { toNumber });
      const boxDisplayLimit = type === "talk" ? Math.max(displayLimit, 6) : type === "group" ? Math.max(displayLimit, 5) : displayLimit;
      return {
        id: `box:${type}`,
        type,
        label,
        count: cards.length,
        sort_rule: sortRule,
        display_limit: boxDisplayLimit,
        top_card_id: cards[0]?.id || "",
        cards,
        hidden_count: Math.max(0, cards.length - boxDisplayLimit),
        maturity_filters: {
          group: ["all", "G0", "G1", "G2", "R_research_mainline"],
          paper: ["all", "M1", "M2", "M3"],
          person: ["all", "R0", "R1", "R2", "R3"],
          project: ["all", "I0", "I1", "I2", "I3", "M1", "M2", "M3"],
          talk: ["all", "M1", "M2", "M3"],
        }[type] || ["all"],
      };
    });
  }

  function buildAssetOverviewModel(options = {}) {
    const {
      graph = {},
      groups = [],
      currentDate = "",
      inboxTotal = 0,
      overview = {},
      previewDocuments = [],
      recentRuns = [],
      toNumber = numberValue,
      translate = (key) => key,
    } = options;
    const understanding = graph.asset_understanding_quality || {};
    const understandingItems = safeArray(understanding.items);
    const intelligenceLookup = assetIntelligenceLookup(graph.asset_intelligence || []);
    const hierarchyLookup = assetHierarchyLookups(graph.asset_hierarchy || {});
    const maturityLookup = materialLevelLookup(understandingItems);
    const cardStateLookup = new Map(
      safeArray(graph.card_state_projection?.items)
        .filter((item) => item && item.path)
        .map((item) => [String(item.path), item]),
    );
    const evidenceLookup = relationEvidenceLookup(
      safeArray(graph.asset_relation_explanations).length ? graph.asset_relation_explanations : graph.asset_relation_evidence || [],
      graph.asset_relation_evidence || []);
    const counts = assetCounts({ overview, graph, groups }, { toNumber });
    const cardBoxes = assetCardBoxesModel(graph.asset_relation_matrix || [], { cardStateLookup, currentDate, evidenceLookup, hierarchyLookup, intelligenceLookup, maturityLookup, previewDocuments, recentRuns, projects: graph.projects || [], people: graph.people || [], talks: graph.talks || [], toNumber, translate });
    const visiblePeopleCount = cardBoxes.find((box) => box.type === "person")?.count;
    return {
      cardBoxes,
      focusCard: null,
      summary: {
        directionCount: counts.directionCount,
        inboxTotal,
        // The public edition has no card-view consolidation; count what this model was given and leave
        // commitmentCount to the Library, which holds the commitment items.
        archivedDocumentCount: 0,
        paperCount: counts.paperCount,
        peopleCount: Number.isFinite(Number(visiblePeopleCount)) ? Number(visiblePeopleCount) : counts.peopleCount,
        previewDocumentCount: safeArray(previewDocuments).length,
        semanticObjectCount: counts.atomTotal,
      },
    };
  }

  global.ResearchOSAssetOverviewModel = Object.freeze({
    assignAssetCardAffinityGroups,
    assetCardAffinityGroup,
    assetCardBoxesModel,
    assetCardRelationNeighbors,
    assetIntelligenceLookup,
    assetHierarchyLookups,
    assetMainlinePriority,
    assetCounts,
    buildAssetOverviewModel,
    materialLevelLookup,
    relationEvidenceLookup,
  });
})(window);
