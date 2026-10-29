/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「asset overview workbench」；负责 DOM 事件绑定，把副作用回调交还 app。
 * English: Workbench interaction adapter for asset overview workbench in the ResearchOS dashboard; owns DOM event binding and returns side effects to app callbacks.
 */

(function attachResearchOSAssetOverviewWorkbenchService(global) {
  const { bindAll } = global.ResearchOSInteractions;
  const scrollIntoView = global.ResearchOSInteractions?.scrollIntoView || ((target, options = {}) => target?.scrollIntoView?.(options));
  const scrollTo = global.ResearchOSInteractions?.scrollTo || ((target, options = {}) => target?.scrollTo?.(options));

  function fallbackTranslate(key) {
    return key;
  }

  function splitAssetCardRelations(card) {
    return String(card?.dataset?.assetCardRelations || "")
      .split("|")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function normalizeAssetSearchText(value = "") {
    return String(value || "").toLowerCase().replace(/\s+/g, " ").trim();
  }

  function parseAssetCardRelationRanks(card) {
    const ranks = new Map();
    String(card?.dataset?.assetCardRelationRanks || "")
      .split("||")
      .map((item) => item.trim())
      .filter(Boolean)
      .forEach((item) => {
        const [id = "", rank = "9999"] = item.split("::");
        if (!id) return;
        const numericRank = Number(rank);
        ranks.set(id, Number.isFinite(numericRank) ? numericRank : 9999);
      });
    return ranks;
  }

  function assetCardRelationCards(root, relationIds = [], relationRanks = new Map()) {
    const relationSet = new Set(relationIds);
    return [...root.querySelectorAll("[data-asset-box-card]")]
      .filter((card) => relationSet.has(card.dataset.assetCardId || ""))
      .sort((a, b) => {
        const aRank = Number(relationRanks.get(a.dataset.assetCardId || "") ?? 9999);
        const bRank = Number(relationRanks.get(b.dataset.assetCardId || "") ?? 9999);
        if (aRank !== bRank) return aRank - bRank;
        return cardOriginalOrder(a) - cardOriginalOrder(b);
      });
  }

  function isOverflowAssetCard(card) {
    const index = Number(card?.dataset?.assetCardIndex || 0);
    const limit = Number(card?.dataset?.assetCardDisplayLimit || 6);
    return Number.isFinite(index) && Number.isFinite(limit) && index >= limit;
  }

  function cardOriginalOrder(card) {
    const index = Number(card?.dataset?.assetCardIndex || 0);
    return Number.isFinite(index) ? index : 0;
  }

  function applyAssetCardOrder(root) {
    if (!root?.querySelectorAll) return;
    root.querySelectorAll("[data-asset-card-box]").forEach((box) => {
      const activeFilter = box.dataset.assetCardActiveFilter || "all";
      const filterActive = activeFilter !== "all";
      const searchActive = Boolean(box.dataset.assetCardSearchQuery || "");
      box.querySelectorAll("[data-asset-box-card]").forEach((card) => {
        const originalIndex = cardOriginalOrder(card);
        const selectedRank = 0;
        const focusRank = Number(card.dataset.assetCardFocusRank || 9999);
        const connectedRank = card.classList.contains("connected") ? -7000 + Math.min(2200, Number.isFinite(focusRank) ? focusRank : 9999) : 0;
        const searchRank = searchActive
          ? card.classList.contains("search-match")
            ? -5000
            : 2400
          : 0;
        const maturityRank = filterActive
          ? card.dataset.assetCardMaturityLevel === activeFilter
            ? -2200
            : 1200
          : 0;
        card.style.setProperty("--asset-card-order", String(selectedRank + connectedRank + searchRank + maturityRank + originalIndex));
      });
    });
  }

  function scrollAssetBoxToStart(box) {
    scrollAssetCardDeckToStart(box?.querySelector?.("[data-asset-card-box-deck]"));
  }

  function assetTaskPayloadFromCard(card) {
    if (!card?.dataset) return null;
    const cardType = card.dataset.assetCardType || "asset";
    const typeMap = {
      action: "paper",
      asset: "source",
      boundary: "paper",
      paper: "paper",
      person: "person",
      project: "project",
      talk: "talk",
    };
    const title = card.dataset.assetCardTitle || "";
    const path = card.dataset.assetCardPath || "";
    if (!title && !path) return null;
    const maturityAction = card.dataset.assetCardMaturityAction || "verify";
    const currentLevel = card.dataset.assetCardMaturityLevel || `${card.dataset.assetCardMaturityAxis || "M"}?`;
    const targetLevel = card.dataset.assetCardMaturityTarget || "";
    const enhancement = {
      action: maturityAction,
      axis: card.dataset.assetCardMaturityAxis || "M",
      confirmed: card.dataset.assetCardMaturityConfirmed === "true",
      current_level: currentLevel,
      source: card.dataset.assetCardMaturitySource || "missing",
      target_level: targetLevel,
    };
    const proposedAction = maturityAction === "use" ? "use_card_in_current_task" : "enhance_card_maturity";
    return {
      action: proposedAction,
      candidate: {
        candidate_id: `candidate:card-enhancement:${card.dataset.assetCardId || path || title}`,
        plugin_id: "research_assets",
        candidate_type: "card_enhancement",
        source_refs: path ? [{ kind: "object", path }] : [],
        summary: [title, `${currentLevel}${targetLevel ? ` -> ${targetLevel}` : ""}`].filter(Boolean).join(" · "),
        proposed_action: { id: proposedAction, target_agent: "asset_cartographer" },
        proposed_writeback: {
          save_target: path,
          object_type: typeMap[cardType] || "source",
          object_id: card.dataset.assetCardId || path || title,
          object_path: path,
          current_state: currentLevel,
          proposed_state: targetLevel || currentLevel,
          decision_rationale: card.dataset.assetCardMaturityReason || card.dataset.assetCardPreview || "",
          impact_scope: path,
          rollback_ref: "",
          validation_state: "not_run",
        },
        sensitivity: "internal",
        required_confirmation: "candidate_diff",
        validation: {
          workflow_status: "active",
          evidence_state: "candidate",
          authority_state: "proposed",
          state: "not_run",
        },
      },
      enhancement,
      note: [
        `${currentLevel}${targetLevel ? ` -> ${targetLevel}` : ""}`,
        card.dataset.assetCardMaturityReason || "",
        card.dataset.assetCardPreview || "",
      ].filter(Boolean).join(" · "),
      path,
      source: "asset-overview-card",
      title,
      type: typeMap[cardType] || "source",
    };
  }

  function encodeAssetCardPayload(card) {
    const payload = assetTaskPayloadFromCard(card);
    if (!payload) return "";
    try {
      return encodeURIComponent(JSON.stringify(payload));
    } catch {
      return "";
    }
  }

  function basketCards(root) {
    const ids = String(root?.dataset?.assetBasketIds || "")
      .split("|")
      .map((item) => item.trim())
      .filter(Boolean);
    return ids
      .map((id) => [...root.querySelectorAll("[data-asset-box-card]")]
        .find((card) => card.dataset.assetCardId === id))
      .filter(Boolean);
  }

  function assetBasketCardsPayload(cards = []) {
    return (Array.isArray(cards) ? cards : [])
      .map((card) => ({
        id: String(card?.dataset?.assetCardId || "").trim(),
        path: String(card?.dataset?.assetCardPath || "").trim(),
        preview: String(card?.dataset?.assetCardPreview || "").trim(),
        subtitle: String(card?.dataset?.assetCardSubtitle || "").trim(),
        title: String(card?.dataset?.assetCardTitle || "").trim(),
        type: String(card?.dataset?.assetCardType || "asset").trim(),
        type_label: String(card?.dataset?.assetCardTypeLabel || "").trim(),
      }))
      .filter((card) => card.title || card.path || card.id);
  }

  function assetBasketWritebackModes(root) {
    return [...(root?.querySelectorAll?.("[data-asset-basket-writeback]") || [])]
      .filter((input) => input.checked)
      .map((input) => String(input.dataset.assetBasketWriteback || "").trim())
      .filter(Boolean);
  }

  function assetBasketWritebackSummary(modes = [], translate = fallbackTranslate) {
    const modeSet = new Set(modes);
    const supplement = modeSet.has("supplement_existing");
    const newCard = modeSet.has("new_composition_card");
    if (supplement && newCard) return translate("assetBasketModeHybrid");
    if (supplement) return translate("assetBasketModeSupplementOnly");
    if (newCard) return translate("assetBasketModeNewOnly");
    return translate("assetBasketNoWritebackMode");
  }

  function assetBasketPayload(root, action = "relation", translate = fallbackTranslate) {
    const cards = basketCards(root);
    if (cards.length < 2) return null;
    const writebackModes = assetBasketWritebackModes(root);
    if (!writebackModes.length) return null;
    const sourceCards = assetBasketCardsPayload(cards);
    const targetExistingPaths = sourceCards.map((card) => card.path).filter(Boolean);
    const actionLabel = {
      project: translate("assetBasketNewProject"),
      recompute: translate("assetBasketRecomputeRelation"),
      relation: translate("assetBasketFindRelation"),
      research: translate("assetBasketResearchTask"),
    }[action] || translate("assetBasketFindRelation");
    return {
      action: action === "project"
        ? "generate_project_from_asset_cards"
        : action === "research"
          ? "generate_research_task_from_asset_cards"
          : action === "recompute"
            ? "recompute_asset_relation_candidates"
            : "inspect_asset_card_relations",
      create_composition_card: writebackModes.includes("new_composition_card"),
      note: [
        `${translate("assetBasketWritebackTitle")}: ${assetBasketWritebackSummary(writebackModes, translate)}`,
        sourceCards.map((card) => [
          card.type_label || card.type || "asset",
          card.title || "",
          card.path || "",
        ].filter(Boolean).join(": ")).join("\n"),
      ].filter(Boolean).join("\n"),
      path: sourceCards.find((card) => card.path)?.path || "",
      source: "asset-card-basket",
      source_cards: sourceCards,
      supplement_existing_cards: writebackModes.includes("supplement_existing"),
      target_existing_paths: targetExistingPaths,
      title: `${actionLabel}: ${sourceCards.map((card) => card.title || "").filter(Boolean).slice(0, 3).join(" / ")}`,
      type: "task",
      writeback_modes: writebackModes,
    };
  }

  function assetCreatePayload(form, translate = fallbackTranslate) {
    if (!form) return null;
    const data = new global.FormData(form);
    const assetType = String(data.get("asset_type") || "paper").trim();
    const title = String(data.get("title") || "").trim();
    const sourceHint = String(data.get("source_hint") || "").trim();
    const targetHint = String(data.get("target_hint") || "").trim();
    const boundaryNote = String(data.get("boundary_note") || "").trim();
    const localFile = data.get("local_file");
    const localFileName = localFile && typeof localFile === "object" && localFile.name ? String(localFile.name).trim() : "";
    if (!title) return null;
    const typeLabel = {
      other: translate("assetsTypeOther"),
      paper: translate("assetsTypePaper"),
      person: translate("assetsTypePerson"),
      project: translate("assetsTypeProject"),
      talk: translate("assetsTypeTalk"),
    }[assetType] || translate("assetsTypeAsset");
    return {
      action: "create_asset_candidate",
      note: [
        `${translate("assetCreateType")}: ${typeLabel}`,
        sourceHint ? `${translate("assetCreateSource")}: ${sourceHint}` : "",
        localFileName ? `${translate("assetCreateLocalFile")}: ${localFileName}` : "",
        targetHint ? `${translate("assetCreateTarget")}: ${targetHint}` : "",
        boundaryNote ? `${translate("assetCreateBoundary")}: ${boundaryNote}` : "",
      ].filter(Boolean).join("\n"),
      path: sourceHint,
      source: "asset-create-form",
      title: `${translate("assetCreateEntry")}: ${title}`,
      type: assetType === "talk" || assetType === "other" ? "source" : assetType,
    };
  }

  function applyAssetCardVisibility(root, translate = fallbackTranslate) {
    if (!root?.querySelectorAll) return;
    root.querySelectorAll("[data-asset-card-box]").forEach((box) => {
      const isExpanded = box.classList.contains("user-expanded");
      const hasActiveMaturityFilter = (box.dataset.assetCardActiveFilter || "all") !== "all";
      const hasActiveSearch = Boolean(box.dataset.assetCardSearchQuery || "");
      box.querySelectorAll("[data-asset-box-card]").forEach((card) => {
        const shouldShow = isExpanded || hasActiveMaturityFilter || hasActiveSearch || !isOverflowAssetCard(card) || card.classList.contains("selected") || card.classList.contains("connected") || card.classList.contains("maturity-highlighted") || card.classList.contains("search-match");
        card.toggleAttribute("hidden", !shouldShow);
      });
      const overflow = box.querySelector("[data-asset-card-expand-box]");
      if (overflow) {
        overflow.setAttribute("aria-expanded", String(isExpanded));
        const countLabel = overflow.querySelector("strong");
        if (countLabel) {
          const hiddenCount = overflow.dataset.assetCardHiddenCount || "";
          countLabel.textContent = isExpanded ? translate("assetsCardFilterAll") : `+${hiddenCount}`;
        }
        const label = overflow.querySelector("span");
        if (label) label.textContent = isExpanded ? translate("assetsCardBoxCollapse") : translate("assetsCardBoxMore");
      }
    });
  }

  function syncAssetCardFilter(root, box, filter = "all", translate = fallbackTranslate) {
    if (!box) return;
    box.dataset.assetCardActiveFilter = filter;
    box.classList.toggle("maturity-highlight-active", filter !== "all");
    box.querySelectorAll("[data-asset-card-filter]").forEach((button) => {
      button.setAttribute("aria-pressed", String((button.dataset.assetCardFilter || "all") === filter));
    });
    box.querySelectorAll("[data-asset-box-card]").forEach((card) => {
      const cardState = card.dataset.assetCardMaturityLevel || "";
      const active = filter !== "all";
      const highlighted = active && cardState === filter;
      const dimmed = active && cardState !== filter;
      card.classList.toggle("maturity-highlighted", highlighted);
      card.classList.toggle("maturity-fronted", highlighted);
      card.classList.toggle("maturity-dimmed", dimmed);
      card.classList.toggle("maturity-filtered-out", false);
      if (active) card.toggleAttribute("hidden", false);
    });
    applyAssetCardOrder(root);
    applyAssetCardVisibility(root, translate);
    scrollAssetBoxToStart(box);
  }

  function syncAssetCardSearch(root, box, query = "", translate = fallbackTranslate) {
    if (!box) return;
    const normalizedQuery = normalizeAssetSearchText(query);
    const clearButton = box.querySelector("[data-asset-card-search-clear]");
    if (clearButton) {
      clearButton.hidden = !normalizedQuery;
      clearButton.disabled = !normalizedQuery;
    }
    box.dataset.assetCardSearchQuery = normalizedQuery;
    box.classList.toggle("search-active", Boolean(normalizedQuery));
    const cards = [...box.querySelectorAll("[data-asset-box-card]")];
    let matchCount = 0;
    cards.forEach((card) => {
      const haystack = normalizeAssetSearchText([
        card.dataset.assetCardSearchText,
        card.dataset.assetCardTitle,
        card.dataset.assetCardSubtitle,
        card.dataset.assetCardAffinityLabel,
        card.dataset.assetCardPath,
      ].filter(Boolean).join(" "));
      const matched = Boolean(normalizedQuery) && haystack.includes(normalizedQuery);
      if (matched) matchCount += 1;
      card.classList.toggle("search-match", matched);
      card.classList.toggle("search-miss", Boolean(normalizedQuery) && !matched);
      if (matched) card.toggleAttribute("hidden", false);
    });
    const status = box.querySelector("[data-asset-card-search-status]");
    if (status) {
      status.textContent = normalizedQuery
        ? translate("assetsCardSearchResult").replace("{count}", String(matchCount))
        : translate("assetsCardSearchIdle");
    }
    applyAssetCardOrder(root);
    applyAssetCardVisibility(root, translate);
    if (normalizedQuery) scrollAssetBoxToStart(box);
  }

  function syncGlobalAssetCardSearch(root, query = "", translate = fallbackTranslate) {
    const normalizedQuery = normalizeAssetSearchText(query);
    const clearButton = root.querySelector("[data-asset-card-global-search-clear]");
    if (clearButton) {
      clearButton.hidden = !normalizedQuery;
      clearButton.disabled = !normalizedQuery;
    }
    let matchCount = 0;
    root.querySelectorAll("[data-asset-card-box]").forEach((box) => {
      let boxMatches = 0;
      box.querySelectorAll("[data-asset-box-card]").forEach((card) => {
        const haystack = normalizeAssetSearchText([
          card.dataset.assetCardSearchText,
          card.dataset.assetCardTitle,
          card.dataset.assetCardSubtitle,
          card.dataset.assetCardAffinityLabel,
          card.dataset.assetCardPath,
        ].filter(Boolean).join(" "));
        const matched = Boolean(normalizedQuery) && haystack.includes(normalizedQuery);
        if (matched) {
          boxMatches += 1;
          matchCount += 1;
        }
        card.classList.toggle("global-search-match", matched);
        card.classList.toggle("global-search-miss", Boolean(normalizedQuery) && !matched);
        if (normalizedQuery) card.toggleAttribute("hidden", !matched);
      });
      box.toggleAttribute("hidden", Boolean(normalizedQuery) && boxMatches === 0);
      if (normalizedQuery && boxMatches > 0 && !box.open) {
        box.open = true;
        box.dataset.assetGlobalSearchOpened = "true";
      } else if (!normalizedQuery && box.dataset.assetGlobalSearchOpened === "true") {
        box.open = false;
        delete box.dataset.assetGlobalSearchOpened;
      }
    });
    root.classList.toggle("global-search-active", Boolean(normalizedQuery));
    const status = root.querySelector("[data-asset-card-global-search-status]");
    if (status) {
      status.textContent = normalizedQuery
        ? translate("assetsCardGlobalSearchResult").replace("{count}", String(matchCount))
        : translate("assetsCardGlobalSearchIdle");
    }
    if (!normalizedQuery) applyAssetCardVisibility(root, translate);
  }

  function renderAssetRelatedCards(related, relatedCards = [], translate = fallbackTranslate, filter = "all") {
    if (!related) return;
    related.replaceChildren();
    related.dataset.assetCardRelatedFilter = filter || "all";
    const filteredCards = (filter && filter !== "all")
      ? relatedCards.filter((item) => (item.dataset.assetCardType || "asset") === filter)
      : relatedCards;
    const title = global.document.createElement("strong");
    title.className = "asset-card-related-title";
    title.textContent = translate("assetCardRelatedTitle").replace("{count}", String(filteredCards.length));
    related.append(title);
    if (filteredCards.length) {
      filteredCards.slice(0, 8).forEach((item) => {
        const button = global.document.createElement("button");
        button.type = "button";
        button.dataset.assetCardJump = item.dataset.assetCardId || "";
        button.setAttribute("data-asset-related-type", item.dataset.assetCardTypeLabel || item.dataset.assetCardType || "");
        button.textContent = item.dataset.assetCardTitle || item.dataset.assetCardId || "";
        button.title = item.dataset.assetCardTitle || "";
        related.append(button);
      });
      if (filteredCards.length > 8) {
        const overflow = global.document.createElement("span");
        overflow.textContent = translate("assetCardMoreRelations").replace("{count}", String(filteredCards.length - 8));
        related.append(overflow);
      }
      return;
    }
    const empty = global.document.createElement("p");
    empty.textContent = translate("assetCardNoViewportRelations");
    related.append(empty);
  }

  function plainRelationReason(reason = "") {
    return String(reason || "")
      .replace(/\s+/g, " ")
      .replace(/当前包含\s*\d+\s*个簇，?/, "")
      .replace(/其中\s*\d+\s*个偏孤立，?/, "")
      .replace(/覆盖\s*\d+\s*篇论文、\s*\d+\s*个项目页、\s*\d+\s*个相关人物、\s*\d+\s*个报告。?/, "")
      .replace(/方向总结应优先覆盖\s*\d+\s*个非孤立簇。?/, "")
      .replace(/适合抽象为更高层研究方向。?/, "")
      .trim();
  }

  function friendlyJudgmentText(value = "", translate = fallbackTranslate) {
    const clean = plainRelationReason(value);
    if (!clean) return "";
    if (/G0\s*孤立元素/.test(clean)) {
      return translate("assetCardJudgmentIsolated");
    }
    if (/G1\s*局部关系/.test(clean)) {
      return translate("assetCardJudgmentLocal");
    }
    if (/G2\s*方向候选/.test(clean)) {
      return translate("assetCardJudgmentDirection");
    }
    if (/G3\s*方向主干|G4\s*研究主线/.test(clean)) {
      return translate("assetCardJudgmentMainline");
    }
    return compactCardText(clean, 190);
  }

  function compactRelationReasons(reasons = []) {
    const seen = new Set();
    return reasons
      .map(plainRelationReason)
      .filter(Boolean)
      .filter((reason) => {
        const key = reason.toLowerCase();
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .slice(0, 2);
  }

  function compactCardText(value = "", limit = 190) {
    const clean = String(value || "")
      .replace(/\s+/g, " ")
      .replace(/当前包含\s*\d+\s*个簇，?/, "")
      .replace(/其中\s*\d+\s*个偏孤立，?/, "")
      .trim();
    if (!clean || clean.length <= limit) return clean;
    return `${clean.slice(0, Math.max(0, limit - 1)).trim()}…`;
  }

  function renderAssetBasket(root, translate = fallbackTranslate) {
    const list = root?.querySelector?.("[data-asset-basket-list]");
    const count = root?.querySelector?.("[data-asset-basket-count]");
    const status = root?.querySelector?.("[data-asset-basket-status]");
    const cards = basketCards(root);
    const writebackModes = assetBasketWritebackModes(root);
    if (count) count.textContent = String(cards.length);
    root?.querySelectorAll?.("[data-asset-basket-action], [data-asset-basket-clear]").forEach((button) => {
      button.disabled = button.hasAttribute("data-asset-basket-clear") ? !cards.length : cards.length < 2 || !writebackModes.length;
    });
    root?.querySelectorAll?.("[data-asset-box-card]").forEach((card) => {
      card.classList.toggle("in-basket", cards.includes(card));
    });
    if (!list) return;
    list.replaceChildren();
    if (!cards.length) {
      const empty = global.document.createElement("p");
      empty.textContent = translate("assetBasketEmpty");
      list.append(empty);
      if (status) status.textContent = translate("assetBasketSafeHint");
      return;
    }
    cards.forEach((card) => {
      const item = global.document.createElement("article");
      const type = global.document.createElement("span");
      const title = global.document.createElement("strong");
      const remove = global.document.createElement("button");
      type.textContent = card.dataset.assetCardTypeLabel || card.dataset.assetCardType || "";
      title.textContent = card.dataset.assetCardTitle || "";
      remove.type = "button";
      remove.dataset.assetBasketRemove = card.dataset.assetCardId || "";
      remove.textContent = translate("assetBasketRemove");
      item.append(type, title, remove);
      list.append(item);
    });
    if (status) {
      status.textContent = cards.length < 2
        ? translate("assetBasketNeedTwo")
        : writebackModes.length
          ? `${translate("assetBasketReady")} ${assetBasketWritebackSummary(writebackModes, translate)}`
          : translate("assetBasketNoWritebackMode");
    }
  }

  function openAssetBasketDrawer(root) {
    const drawer = root?.querySelector?.("[data-asset-card-basket-drawer]");
    if (!drawer) return;
    drawer.open = true;
    const reveal = () => scrollIntoView(drawer, { block: "nearest", behavior: "smooth" });
    if (typeof global.requestAnimationFrame === "function") {
      global.requestAnimationFrame(reveal);
      return;
    }
    reveal();
  }

  function addAssetCardToBasket(root, card, translate = fallbackTranslate) {
    if (!root || !card) return;
    const ids = new Set(String(root.dataset.assetBasketIds || "").split("|").filter(Boolean));
    ids.add(card.dataset.assetCardId || "");
    ids.delete("");
    root.dataset.assetBasketIds = [...ids].join("|");
    const lowerWorkbench = root.querySelector("[data-asset-card-lower-workbench]");
    if (lowerWorkbench) lowerWorkbench.hidden = false;
    openAssetBasketDrawer(root);
    renderAssetBasket(root, translate);
  }

  function removeAssetCardFromBasket(root, cardId = "", translate = fallbackTranslate) {
    const normalizedId = String(cardId || "").trim();
    if (!root?.dataset || !normalizedId) return false;
    const ids = new Set(String(root.dataset.assetBasketIds || "").split("|").filter(Boolean));
    if (!ids.delete(normalizedId)) return false;
    root.dataset.assetBasketIds = [...ids].join("|");
    renderAssetBasket(root, translate);
    const lowerWorkbench = root.querySelector("[data-asset-card-lower-workbench]");
    if (lowerWorkbench && !ids.size && !root.querySelector("[data-asset-box-card].selected")) lowerWorkbench.hidden = true;
    return true;
  }

  function assetCardFromDragEvent(root, event) {
    const transferId = event?.dataTransfer?.getData?.("text/researchos-asset-card")
      || event?.dataTransfer?.getData?.("text/plain")
      || "";
    const normalizedId = String(transferId || "").trim();
    if (normalizedId) {
      const directCard = [...root.querySelectorAll("[data-asset-box-card]")]
        .find((card) => card.dataset.assetCardId === normalizedId);
      if (directCard) return directCard;
    }
    return root.querySelector("[data-asset-box-card].dragging") || null;
  }

  function dragEventHasAssetCard(event) {
    const types = Array.from(event?.dataTransfer?.types || []);
    return types.includes("text/researchos-asset-card") || types.includes("application/researchos-doing");
  }

  function setBasketDragActive(root, active = false) {
    root?.querySelector?.("[data-asset-card-basket-drawer]")?.classList.toggle("drag-active", Boolean(active));
    root?.querySelector?.("[data-asset-card-basket-panel]")?.classList.toggle("drag-active", Boolean(active));
  }

  function bindAssetBasketClickDelegation(root, translate = fallbackTranslate) {
    if (!root || root.dataset.assetBasketClickDelegated === "true") return;
    root.dataset.assetBasketClickDelegated = "true";
    root.addEventListener("click", (event) => {
      const addBasketButton = event.target?.closest?.("[data-asset-card-add-basket]");
      if (addBasketButton && root.contains(addBasketButton)) {
        event.preventDefault();
        const cardId = addBasketButton.dataset.assetCardAddBasket || "";
        const card = [...root.querySelectorAll("[data-asset-box-card]")]
          .find((item) => item.dataset.assetCardId === cardId);
        addAssetCardToBasket(root, card, translate);
        addBasketButton.textContent = translate("assetCardAddedBasket");
        return;
      }
      const removeBasketButton = event.target?.closest?.("[data-asset-basket-remove]");
      if (removeBasketButton && root.contains(removeBasketButton)) {
        event.preventDefault();
        removeAssetCardFromBasket(root, removeBasketButton.dataset.assetBasketRemove || "", translate);
      }
    });
  }

  function renderAssetCardFocusPanel(root, card, relatedCards = [], translate = fallbackTranslate) {
    const panel = root.querySelector("[data-asset-card-focus-panel]");
    if (!panel || !card) return;
    panel.classList.remove("is-empty");
    const grouped = new Map();
    relatedCards.forEach((item) => {
      const type = item.dataset.assetCardType || "asset";
      const label = item.dataset.assetCardTypeLabel || type;
      if (!grouped.has(type)) grouped.set(type, { items: [], label });
      grouped.get(type).items.push(item);
    });
    panel.replaceChildren();

    const heading = global.document.createElement("div");
    heading.className = "asset-card-focus-heading";
    const title = global.document.createElement("strong");
    title.textContent = card.dataset.assetCardTitle || "";
    const meta = global.document.createElement("span");
    const maturityAxis = card.dataset.assetCardMaturityAxis || "M";
    meta.textContent = [
      card.dataset.assetCardTypeLabel || card.dataset.assetCardType || "",
      card.dataset.assetCardMaturityDisplay || card.dataset.assetCardMaturityLevel || "",
      maturityAxis === "M" ? (card.dataset.assetCardStateLabel || card.dataset.assetCardState || "") : "",
      card.dataset.assetCardUpdatedDate ? `${translate("assetDateUpdated")}: ${card.dataset.assetCardUpdatedDate}` : "",
    ].filter(Boolean).join(" · ");
    heading.append(title, meta);

    const maturitySummary = global.document.createElement("section");
    maturitySummary.className = "asset-card-maturity-summary";
    const maturityHeading = global.document.createElement("div");
    const maturityCurrent = global.document.createElement("strong");
    const maturityTarget = global.document.createElement("span");
    const maturityReason = global.document.createElement("p");
    const currentMaturity = card.dataset.assetCardMaturityDisplay || card.dataset.assetCardMaturityLevel || "";
    const targetMaturity = card.dataset.assetCardMaturityTarget || "";
    maturityCurrent.textContent = currentMaturity;
    maturityTarget.textContent = targetMaturity ? `→ ${targetMaturity}` : "";
    maturityReason.textContent = compactCardText(
      card.dataset.assetCardMaturityReason
        || (card.dataset.assetCardMaturityConfirmed === "true" ? translate("assetCardInspectUpgradeHint") : translate("assetLineagePendingHint")),
      180
    );
    maturityHeading.append(maturityCurrent, maturityTarget);
    maturitySummary.append(maturityHeading, maturityReason);

    const preview = global.document.createElement("small");
    preview.textContent = compactCardText(card.dataset.assetCardPreview || translate("assetCardNoPreview"), 220);

    const maturityNote = global.document.createElement("p");
    maturityNote.className = "asset-card-maturity-note";
    maturityNote.textContent = compactCardText(card.dataset.assetCardMaturityReason || "", 180);

    const levelGrid = global.document.createElement("div");
    levelGrid.className = "asset-card-detail-grid";
    levelGrid.dataset.assetCardDetailGrid = "";
    const overflowSyncers = [];
    [
      [translate("assetCardDetailResearcherRelation"), card.dataset.assetCardResearcherRelationLabel || card.dataset.assetCardPersonMaturityLabel || card.dataset.assetCardAnalysisLabel || ""],
      [translate("assetCardDetailProjectCoverage"), card.dataset.assetCardHierarchyLabel || ""],
      [translate("assetCardDetailCluster"), card.dataset.assetCardClusterLabel || ""],
      [translate("assetCardDetailMainline"), card.dataset.assetCardMainline || ""],
      [translate("assetLineagePeople"), String(card.dataset.assetCardRelatedPeople || "").split("||").map((item) => item.split("::")[1] || "").filter(Boolean).slice(0, 3).join(" / ")],
    ].filter(([, value]) => value).forEach(([label, value]) => {
      const item = global.document.createElement("section");
      const itemLabel = global.document.createElement("span");
      const itemValue = global.document.createElement("strong");
      itemLabel.textContent = label;
      itemValue.textContent = value;
      const syncOverflowTooltip = () => {
        const isOverflowing = itemValue.scrollWidth > itemValue.clientWidth;
        if (isOverflowing) {
          item.dataset.overflowTooltip = value;
          item.tabIndex = 0;
          return;
        }
        delete item.dataset.overflowTooltip;
        item.removeAttribute("tabindex");
      };
      item.addEventListener("pointerenter", syncOverflowTooltip);
      item.addEventListener("focus", syncOverflowTooltip);
      overflowSyncers.push(syncOverflowTooltip);
      item.append(itemLabel, itemValue);
      levelGrid.append(item);
    });

    const hierarchyPanel = global.document.createElement("div");
    hierarchyPanel.className = "asset-card-hierarchy-panel";
    hierarchyPanel.dataset.assetCardHierarchyPanel = "";
    const hierarchyTitle = global.document.createElement("strong");
    hierarchyTitle.textContent = translate("assetCardHierarchyTitle");
    const hierarchyText = global.document.createElement("p");
    hierarchyText.textContent = friendlyJudgmentText([
      card.dataset.assetCardHierarchySummary || "",
      card.dataset.assetCardHierarchyRecommendation || "",
      card.dataset.assetCardClusterSummary || "",
      card.dataset.assetCardClusterRecommendation || "",
      card.dataset.assetCardDirectionSummary || "",
      card.dataset.assetCardResearcherRelationReason || "",
    ].filter(Boolean).slice(0, 2).join(" "), translate);
    hierarchyPanel.append(hierarchyTitle, hierarchyText);

    const relationSummary = global.document.createElement("div");
    relationSummary.className = "asset-card-focus-summary";
    grouped.forEach(({ items, label }) => {
      const pill = global.document.createElement("button");
      pill.type = "button";
      pill.dataset.assetRelationFilter = items[0]?.dataset?.assetCardType || "asset";
      pill.setAttribute("aria-pressed", "false");
      pill.textContent = `${label} ${items.length}`;
      relationSummary.append(pill);
    });
    if (!grouped.size) {
      const emptyPill = global.document.createElement("span");
      emptyPill.textContent = translate("assetCardNoRelations");
      relationSummary.append(emptyPill);
    }

    const related = global.document.createElement("div");
    related.dataset.assetCardRelated = "";
    renderAssetRelatedCards(related, relatedCards, translate, "all");

    const actions = global.document.createElement("footer");
    actions.className = "asset-card-focus-actions";
    if (card.dataset.assetCardPath) {
      const preview = global.document.createElement("button");
      preview.type = "button";
      preview.className = "evidence-primary";
      preview.dataset.previewPath = card.dataset.assetCardPath || "";
      preview.textContent = translate("assetCardViewEvidence");
      preview.title = translate("assetCardEvidenceHint");
      actions.append(preview);
    }
    const addBasket = global.document.createElement("button");
    addBasket.type = "button";
    addBasket.className = "basket-secondary";
    addBasket.dataset.assetCardAddBasket = card.dataset.assetCardId || "";
    addBasket.textContent = translate("assetCardAddBasket");
    addBasket.title = translate("assetBasketHint");
    actions.append(addBasket);
    const addTask = global.document.createElement("button");
    addTask.type = "button";
    addTask.className = "secondary enhancement-primary";
    addTask.dataset.assetCardAddTask = card.dataset.assetCardId || "";
    addTask.textContent = translate({
      enhance: "assetAdvancedUpgrade",
      reverify: "assetAdvancedReverify",
      use: "assetCardInspectUpgrade",
      verify: "assetAdvancedVerifyLevel",
    }[card.dataset.assetCardMaturityAction || "verify"] || "assetCardInspectUpgrade");
    addTask.title = translate("assetCardInspectUpgradeHint");
    actions.append(addTask);
    const clear = global.document.createElement("button");
    clear.type = "button";
    clear.dataset.assetCardClear = "true";
    clear.textContent = translate("assetCardClearSelection");
    actions.append(clear);
    const relationReasons = String(card.dataset.assetCardRelationReasons || "")
      .split("||")
      .map((item) => item.trim())
      .filter(Boolean);
    const compactReasons = compactRelationReasons(relationReasons);
    const relationExplanation = global.document.createElement("div");
    relationExplanation.className = "asset-card-relation-explanation";
    relationExplanation.dataset.assetCardRelationExplanation = "";
    const relationSummaryTitle = global.document.createElement("button");
    relationSummaryTitle.type = "button";
    relationSummaryTitle.dataset.assetCardToggleSection = "relation";
    relationSummaryTitle.setAttribute("aria-expanded", "false");
    relationSummaryTitle.textContent = translate("assetRelationExplainTitle");
    const relationBody = global.document.createElement("div");
    relationBody.hidden = true;
    if (compactReasons.length) {
      const list = global.document.createElement("ul");
      compactReasons.forEach((reason) => {
        const item = global.document.createElement("li");
        item.textContent = reason;
        list.append(item);
      });
      relationBody.append(list);
    } else {
      const empty = global.document.createElement("p");
      empty.textContent = translate("assetRelationExplainEmpty");
      relationBody.append(empty);
    }
    relationExplanation.append(relationSummaryTitle, relationBody);
    const status = global.document.createElement("output");
    status.dataset.assetCardActionStatus = "";
    status.textContent = "";
    const panelNodes = [heading, maturitySummary, preview];
    panelNodes.push(actions);
    if (maturityNote.textContent) panelNodes.push(maturityNote);
    if (levelGrid.children.length) panelNodes.push(levelGrid);
    if (hierarchyText.textContent) panelNodes.push(hierarchyPanel);
    panel.append(...panelNodes, relationSummary, related, relationExplanation, status);
    if (typeof global.requestAnimationFrame === "function") {
      global.requestAnimationFrame(() => overflowSyncers.forEach((sync) => sync()));
    } else {
      overflowSyncers.forEach((sync) => sync());
    }
  }

  function scrollAssetCardFocusPanelIntoView(root) {
    const panel = root?.querySelector?.("[data-asset-card-focus-panel]");
    if (!panel || typeof panel.scrollIntoView !== "function") return;
    const viewportWidth = Number(global.innerWidth || root?.ownerDocument?.documentElement?.clientWidth || 0);
    if (!viewportWidth || viewportWidth > 980) return;
    const scroll = () => scrollIntoView(panel, { block: "start", behavior: "smooth" });
    if (typeof global.requestAnimationFrame === "function") {
      global.requestAnimationFrame(scroll);
      return;
    }
    scroll();
  }

  function scrollAssetCardDeckToStart(deck) {
    if (!deck) return;
    if (typeof deck.scrollTo === "function") {
      scrollTo(deck, { left: 0, behavior: "smooth" });
      if (typeof global.setTimeout === "function") {
        global.setTimeout(() => {
          deck.scrollLeft = 0;
        }, 180);
      }
      return;
    }
    deck.scrollLeft = 0;
  }

  function scrollFocusedAssetCardDecks(root, selectedBoxId = "", relationSet = new Set()) {
    if (!root?.querySelectorAll) return;
    const applyScroll = () => {
      root.querySelectorAll("[data-asset-card-box]").forEach((box) => {
        const isSelectedBox = box.dataset.assetCardBox === selectedBoxId;
        const hasRelated = [...box.querySelectorAll("[data-asset-box-card]")]
          .some((item) => relationSet.has(item.dataset.assetCardId || ""));
        if (isSelectedBox || !hasRelated) return;
        scrollAssetCardDeckToStart(box.querySelector("[data-asset-card-box-deck]"));
      });
    };
    if (typeof global.requestAnimationFrame === "function") {
      global.requestAnimationFrame(applyScroll);
      return;
    }
    applyScroll();
  }

  function clearAssetCardFocus(root, translate = fallbackTranslate) {
    if (!root?.querySelectorAll) return;
    root.querySelector("[data-asset-card-boxes]")?.classList.remove("focus-active");
    root.querySelectorAll("[data-asset-box-card]").forEach((card) => {
      card.classList.remove("selected", "connected", "dimmed", "relation-filtered", "relation-muted", "maturity-highlighted", "maturity-fronted", "maturity-dimmed", "maturity-filtered-out");
      card.style.setProperty("--asset-card-order", card.dataset.assetCardIndex || "0");
      delete card.dataset.assetCardFocusRank;
      card.setAttribute("aria-pressed", "false");
    });
    root.querySelectorAll("[data-asset-card-box]").forEach((box) => {
      box.classList.remove("expanded", "focus-filtered", "has-focus", "user-expanded", "maturity-highlight-active");
      delete box.dataset.assetCardActiveFilter;
      box.querySelectorAll("[data-asset-card-filter]").forEach((button) => {
        button.setAttribute("aria-pressed", String((button.dataset.assetCardFilter || "all") === "all"));
      });
    });
    applyAssetCardVisibility(root, translate);
    const panel = root.querySelector("[data-asset-card-focus-panel]");
    if (panel) {
      panel.classList.add("is-empty");
      panel.replaceChildren();
      const heading = global.document.createElement("div");
      heading.className = "asset-card-focus-heading";
      const title = global.document.createElement("strong");
      const hint = global.document.createElement("span");
      const related = global.document.createElement("div");
      title.textContent = translate("assetsCardBoxSelectTitle");
      hint.textContent = translate("assetCardClearHint");
      related.dataset.assetCardRelated = "";
      heading.append(title, hint);
      panel.append(heading, related);
    }
    const lowerWorkbench = root.querySelector("[data-asset-card-lower-workbench]");
    if (lowerWorkbench && !String(root.dataset.assetBasketIds || "").trim()) lowerWorkbench.hidden = true;
  }

  function selectAssetCard(root, card, translate = fallbackTranslate) {
    if (!root?.querySelectorAll || !card) return;
    const selectedId = card.dataset.assetCardId || "";
    const selectedBoxId = card.dataset.assetCardBoxId || "";
    const relationIds = splitAssetCardRelations(card);
    const relationSet = new Set(relationIds);
    const relationRanks = parseAssetCardRelationRanks(card);
    const relatedCards = assetCardRelationCards(root, relationIds, relationRanks);
    const lowerWorkbench = root.querySelector("[data-asset-card-lower-workbench]");
    if (lowerWorkbench) lowerWorkbench.hidden = false;
    root.querySelector("[data-asset-card-boxes]")?.classList.toggle("focus-active", Boolean(selectedId));

    root.querySelectorAll("[data-asset-card-box]").forEach((box) => {
      const isSelectedBox = box.dataset.assetCardBox === selectedBoxId;
      const hasRelated = [...box.querySelectorAll("[data-asset-box-card]")]
        .some((item) => relationSet.has(item.dataset.assetCardId || ""));
      box.classList.toggle("expanded", isSelectedBox);
      box.classList.toggle("has-focus", isSelectedBox);
      box.classList.toggle("focus-filtered", !isSelectedBox && hasRelated);
      if (isSelectedBox) box.open = true;
    });

    root.querySelectorAll("[data-asset-box-card]").forEach((item) => {
      const itemId = item.dataset.assetCardId || "";
      const originalIndex = Number(item.dataset.assetCardIndex || 0);
      const isSelected = itemId === selectedId;
      const isConnected = relationSet.has(itemId);
      item.classList.toggle("selected", isSelected);
      item.classList.toggle("connected", isConnected);
      item.classList.toggle("dimmed", Boolean(selectedId) && !isSelected && !isConnected);
      item.classList.remove("relation-filtered", "relation-muted");
      if (isConnected) {
        item.dataset.assetCardFocusRank = String(relationRanks.get(itemId) ?? originalIndex);
      } else {
        delete item.dataset.assetCardFocusRank;
      }
      item.setAttribute("aria-pressed", String(isSelected));
    });
    applyAssetCardOrder(root);
    applyAssetCardVisibility(root, translate);
    scrollFocusedAssetCardDecks(root, selectedBoxId, relationSet);
    renderAssetCardFocusPanel(root, card, relatedCards, translate);
    scrollAssetCardFocusPanelIntoView(root);
  }

  function toggleAssetCardSelection(root, card, translate = fallbackTranslate) {
    if (!root?.querySelectorAll || !card) return;
    if (card.classList.contains("selected")) {
      clearAssetCardFocus(root, translate);
      return;
    }
    selectAssetCard(root, card, translate);
  }

  function bindAssetCardBoxEvents(root, callbacks = {}) {
    if (!root?.querySelectorAll) return;
    const {
      onAddAssetTask = () => {},
      onOpenPreview = () => {},
      onOpenWorkspace = () => {},
      translate = fallbackTranslate,
    } = callbacks;
    bindAssetBasketClickDelegation(root, translate);
    bindAll(root, "[data-asset-card-global-search]", "input", (event, input) => {
      syncGlobalAssetCardSearch(root, input.value || "", translate);
    });
    bindAll(root, "[data-asset-card-global-search-clear]", "click", () => {
      const input = root.querySelector("[data-asset-card-global-search]");
      if (input) input.value = "";
      syncGlobalAssetCardSearch(root, "", translate);
    });
    bindAll(root, "[data-asset-box-card]", "click", (event, button) => {
      event.preventDefault();
      toggleAssetCardSelection(root, button, translate);
    });
    bindAll(root, "[data-asset-card-search]", "input", (event, input) => {
      const boxId = input.dataset.assetCardSearchBox || "";
      const box = root.querySelector(`[data-asset-card-box="${boxId}"]`);
      syncAssetCardSearch(root, box, input.value || "", translate);
    });
    bindAll(root, "[data-asset-card-search-clear]", "click", (event, button) => {
      const boxId = button.dataset.assetCardSearchClear || "";
      const box = root.querySelector(`[data-asset-card-box="${boxId}"]`);
      const input = box?.querySelector?.("[data-asset-card-search]");
      if (input) input.value = "";
      syncAssetCardSearch(root, box, "", translate);
    });
    bindAll(root, "[data-asset-box-card]", "dragstart", (event, card) => {
      const cardId = card.dataset.assetCardId || "";
      if (!cardId || !event.dataTransfer) return;
      const payload = encodeAssetCardPayload(card);
      event.dataTransfer.effectAllowed = "copy";
      event.dataTransfer.setData("text/researchos-asset-card", cardId);
      if (payload) event.dataTransfer.setData("application/researchos-doing", payload);
      event.dataTransfer.setData("text/plain", cardId);
      card.classList.add("dragging");
    });
    bindAll(root, "[data-asset-box-card]", "dragend", (event, card) => {
      card.classList.remove("dragging");
      setBasketDragActive(root, false);
    });
    bindAll(root, "[data-asset-card-expand-box]", "click", (event, button) => {
      event.preventDefault();
      const boxId = button.dataset.assetCardExpandBox || "";
      const box = [...root.querySelectorAll("[data-asset-card-box]")]
        .find((item) => item.dataset.assetCardBox === boxId);
      if (!box) return;
      box.classList.toggle("user-expanded");
      applyAssetCardVisibility(root, translate);
    });
    bindAll(root, "[data-asset-card-filter]", "click", (event, button) => {
      event.preventDefault();
      const boxId = button.dataset.assetCardFilterBox || "";
      const box = [...root.querySelectorAll("[data-asset-card-box]")]
        .find((item) => item.dataset.assetCardBox === boxId);
      const nextFilter = button.dataset.assetCardFilter || "all";
      const activeFilter = box?.dataset?.assetCardActiveFilter || "all";
      syncAssetCardFilter(root, box, nextFilter === activeFilter && nextFilter !== "all" ? "all" : nextFilter, translate);
    });
    applyAssetCardVisibility(root, translate);
    if (root.dataset.assetCardPanelDelegated === "true") return;
    root.dataset.assetCardPanelDelegated = "true";
    root.addEventListener("click", (event) => {
      const jumpButton = event.target?.closest?.("[data-asset-card-jump]");
      if (jumpButton && root.contains(jumpButton)) {
        event.preventDefault();
        const targetId = jumpButton.dataset.assetCardJump || "";
        const target = [...root.querySelectorAll("[data-asset-box-card]")]
          .find((card) => card.dataset.assetCardId === targetId);
        if (target) {
          const targetBox = target.closest?.("[data-asset-card-box]");
          if (targetBox) targetBox.open = true;
          target.toggleAttribute("hidden", false);
          scrollIntoView(target, { block: "nearest", inline: "center", behavior: "smooth" });
          toggleAssetCardSelection(root, target, translate);
        }
        return;
      }
      const clearButton = event.target?.closest?.("[data-asset-card-clear]");
      if (clearButton && root.contains(clearButton)) {
        event.preventDefault();
        clearAssetCardFocus(root, translate);
        return;
      }
      const openInboxButton = event.target?.closest?.("[data-asset-card-open-inbox]");
      if (openInboxButton && root.contains(openInboxButton)) {
        event.preventDefault();
        onOpenWorkspace({ event, button: openInboxButton, workspace: "review" });
        return;
      }
      const toggleSectionButton = event.target?.closest?.("[data-asset-card-toggle-section]");
      if (toggleSectionButton && root.contains(toggleSectionButton)) {
        event.preventDefault();
        const section = toggleSectionButton.closest(".asset-card-relation-explanation");
        const body = section?.querySelector("div");
        const nextOpen = body?.hidden;
        if (body) body.hidden = !nextOpen;
        toggleSectionButton.setAttribute("aria-expanded", String(Boolean(nextOpen)));
        section?.classList.toggle("is-open", Boolean(nextOpen));
        return;
      }
      const previewButton = event.target?.closest?.("[data-preview-path]");
      if (previewButton && root.contains(previewButton)) {
        event.preventDefault();
        callbacks.onOpenPreview?.({
          event,
          button: previewButton,
          path: previewButton.dataset.previewPath || "",
        });
        return;
      }
      const relationFilterButton = event.target?.closest?.("[data-asset-relation-filter]");
      if (relationFilterButton && root.contains(relationFilterButton)) {
        event.preventDefault();
        const selectedCard = root.querySelector("[data-asset-box-card].selected");
        const related = root.querySelector("[data-asset-card-related]");
        if (!selectedCard || !related) return;
        const pressedNow = relationFilterButton.getAttribute("aria-pressed") === "true";
        const filter = pressedNow ? "all" : (relationFilterButton.dataset.assetRelationFilter || "all");
        const relationIds = splitAssetCardRelations(selectedCard);
        const relationRanks = parseAssetCardRelationRanks(selectedCard);
        const relatedCards = assetCardRelationCards(root, relationIds, relationRanks);
        root.querySelectorAll("[data-asset-relation-filter]").forEach((button) => {
          const pressed = filter !== "all" && (button.dataset.assetRelationFilter || "all") === filter;
          button.setAttribute("aria-pressed", String(pressed));
          button.classList.toggle("selected", pressed);
        });
        root.querySelectorAll("[data-asset-box-card].connected").forEach((item) => {
          const active = filter === "all" || (item.dataset.assetCardType || "asset") === filter;
          item.classList.toggle("relation-filtered", active);
          item.classList.toggle("relation-muted", !active);
          if (active) item.toggleAttribute("hidden", false);
        });
        renderAssetRelatedCards(related, relatedCards, translate, filter);
        applyAssetCardOrder(root);
        const firstMatch = relatedCards.find((item) => filter === "all" || (item.dataset.assetCardType || "asset") === filter);
        if (firstMatch) scrollIntoView(firstMatch, { block: "nearest", inline: "center", behavior: "smooth" });
        return;
      }
      const addTaskButton = event.target?.closest?.("[data-asset-card-add-task]");
      if (addTaskButton && root.contains(addTaskButton)) {
        event.preventDefault();
        const cardId = addTaskButton.dataset.assetCardAddTask || "";
        const card = [...root.querySelectorAll("[data-asset-box-card]")]
          .find((item) => item.dataset.assetCardId === cardId);
        const payload = assetTaskPayloadFromCard(card);
        const status = root.querySelector("[data-asset-card-action-status]");
        onAddAssetTask({ event, button: addTaskButton, card, payload, status });
        return;
      }
    });
  }

  function openAssetIntakeDrawer(root) {
    const slotHost = root?.closest?.('[data-plugin-slot-host="library"]') || root;
    const panel = slotHost?.querySelector?.("[data-asset-create-panel]");
    if (panel) {
      panel.open = true;
      scrollIntoView(panel, { block: "nearest", behavior: "smooth" });
      const input = panel.querySelector("[name='title']");
      if (input?.focus) input.focus();
    }
  }

  function bindAssetOverviewEvents(root, callbacks = {}) {
    if (!root) return;
    const {
      onAssetDetail = () => {},
      onAddAssetTask = () => {},
      onOpenWorkspace = () => {},
      onOpenPreview = () => {},
      onPublicDemoToggle = () => {},
      translate = fallbackTranslate,
    } = callbacks;
    bindAssetBasketClickDelegation(root, translate);

    bindAll(root, "[data-open-workspace]", "click", (event, button) => {
      onOpenWorkspace({ event, button, workspace: button.dataset.openWorkspace || "now" });
    });
    bindAll(root, "[data-asset-detail]", "click", (event, button) => {
      onAssetDetail({ event, button, detail: button.dataset.assetDetail || "assetOverview" });
    });
    bindAll(root, "[data-public-demo-toggle]", "click", (event, button) => {
      onPublicDemoToggle({ event, button, visible: button.getAttribute("aria-pressed") !== "true" });
    });
    bindAll(root, "[data-asset-open-intake]", "click", () => {
      openAssetIntakeDrawer(root);
    });
    bindAssetCardBoxEvents(root, { onAddAssetTask, onOpenPreview, onOpenWorkspace, translate });
    renderAssetBasket(root, translate);
    bindAll(root, "[data-asset-card-basket-drawer]", "dragover", (event) => {
      if (!dragEventHasAssetCard(event) && !root.querySelector("[data-asset-box-card].dragging")) return;
      event.preventDefault();
      if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
      setBasketDragActive(root, true);
    });
    bindAll(root, "[data-asset-card-basket-drawer]", "dragleave", (event) => {
      if (event.currentTarget?.contains?.(event.relatedTarget)) return;
      setBasketDragActive(root, false);
    });
    bindAll(root, "[data-asset-card-basket-drawer]", "drop", (event) => {
      const card = assetCardFromDragEvent(root, event);
      if (!card) return;
      event.preventDefault();
      addAssetCardToBasket(root, card, translate);
      selectAssetCard(root, card, translate);
      setBasketDragActive(root, false);
      const status = root.querySelector("[data-asset-basket-status]");
      if (status) status.textContent = translate("assetCardAddedBasket");
    });
    bindAll(root, "[data-asset-basket-action]", "click", (event, button) => {
      const payload = assetBasketPayload(root, button.dataset.assetBasketAction || "relation", translate);
      const status = root.querySelector("[data-asset-basket-status]");
      if (!payload && status) status.textContent = translate("assetBasketNoWritebackMode");
      onAddAssetTask({ event, button, card: null, payload, status });
      if (status && payload) status.textContent = translate("assetBasketAddedStatus");
    });
    bindAll(root, "[data-asset-basket-writeback]", "change", () => {
      renderAssetBasket(root, translate);
    });
    bindAll(root, "[data-asset-basket-clear]", "click", (event) => {
      event.preventDefault();
      root.dataset.assetBasketIds = "";
      renderAssetBasket(root, translate);
    });
    root.querySelectorAll("[data-asset-create-form]").forEach((form) => {
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        const status = form.querySelector("[data-asset-create-status]");
        const button = form.querySelector("button[type='submit']");
        const payload = assetCreatePayload(form, translate);
        if (!payload) {
          if (status) status.textContent = translate("assetCreateNeedTitle");
          return;
        }
        onAddAssetTask({ event, button, card: null, payload, status });
        if (status) status.textContent = translate("assetCreateAddedStatus");
        form.reset();
      });
    });
  }

  global.ResearchOSAssetOverviewWorkbenchService = Object.freeze({
    addAssetCardToBasket,
    assetTaskPayloadFromCard,
    assetCreatePayload,
    bindAssetBasketClickDelegation,
    bindAssetCardBoxEvents,
    bindAssetOverviewEvents,
    clearAssetCardFocus,
    openAssetIntakeDrawer,
    removeAssetCardFromBasket,
    renderAssetBasket,
    selectAssetCard,
    syncAssetCardFilter,
    syncAssetCardSearch,
  });
})(window);
