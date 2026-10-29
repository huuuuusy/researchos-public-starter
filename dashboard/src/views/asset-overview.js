/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 视图「asset overview」的纯 HTML 渲染层；不保存持久状态、不直接执行写入副作用。
 * English: Pure HTML rendering layer for the asset overview dashboard view; stores no durable state and performs no write side effects.
 */

(function attachResearchOSAssetOverviewView(global) {
  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      shortText: deps.shortText || ((value) => String(value ?? "")),
      translate: deps.translate || ((key) => key),
    };
  }

  function assetCardTypeLabel(type = "", translate = (key) => key) {
    const value = String(type || "").trim();
    if (value === "paper") return translate("assetsTypePaper");
    if (value === "project") return translate("assetsTypeProject");
    if (value === "knowledge") return translate("assetsTypeKnowledge");
    if (value === "person") return translate("assetsTypePerson");
    if (value === "group") return translate("assetsTypeGroup");
    if (value === "talk") return translate("assetsTypeTalk");
    if (value === "action") return translate("assetsTypeAction");
    if (value === "boundary") return translate("assetsTypeBoundary");
    return translate("assetsTypeAsset");
  }

  function assetCardStateLabel(state = "", translate = (key) => key) {
    const value = String(state || "").trim();
    if (value === "needs_evidence") return translate("assetsStateNeedsEvidence");
    if (value === "candidate") return translate("assetsStateCandidate");
    if (value === "local_only") return translate("assetsStateLocalOnly");
    return translate("assetsStateConfirmed");
  }

  function projectOperationalStatusLabel(card = {}, translate = (key) => key) {
    if (String(card.type || "") !== "project") return "";
    const binding = card.portfolio_binding && typeof card.portfolio_binding === "object"
      ? card.portfolio_binding : {};
    const bindingState = String(binding.state || "");
    if (!bindingState) return "";
    if (bindingState === "uncovered") return translate("researchPortfolioCardBindingUncovered");
    if (bindingState === "ambiguous") return translate("researchPortfolioCardBindingAmbiguous");
    if (bindingState === "not_applicable") return translate("researchPortfolioCardBindingNotApplicable");
    const operational = card.operational_status && typeof card.operational_status === "object"
      ? card.operational_status : {};
    const responsibilityKey = {
      lead: "researchPortfolioResponsibilityLead",
      support: "researchPortfolioResponsibilitySupport",
      unclassified: "researchPortfolioResponsibilityUnclassified",
    }[String(operational.responsibility || "unclassified")] || "researchPortfolioResponsibilityUnclassified";
    const engagementKey = {
      ongoing: "researchPortfolioEngagementOngoing",
      temporary: "researchPortfolioEngagementTemporary",
      unclassified: "researchPortfolioEngagementUnclassified",
    }[String(operational.engagement || "unclassified")] || "researchPortfolioEngagementUnclassified";
    const stateKey = {
      mainline: "researchPortfolioStateMainline",
      queued: "researchPortfolioStateQueued",
      conditional: "researchPortfolioStateConditional",
      waiting: "researchPortfolioStateWaiting",
      paused: "researchPortfolioStatePaused",
      closed: "researchPortfolioStateClosed",
    }[String(operational.state || "")];
    const phaseLabel = global.ResearchOSResearchPortfolioView?.phaseLabel
      ? global.ResearchOSResearchPortfolioView.phaseLabel(operational.lifecycle_phase, translate)
      : String(operational.lifecycle_phase || "");
    return [
      `${translate(responsibilityKey)} + ${translate(engagementKey)}`,
      stateKey ? translate(stateKey) : String(operational.state || ""),
      phaseLabel,
    ].filter(Boolean).join(" · ");
  }

  function assetCardSearchText(card = {}, typeLabel = "", stateLabel = "") {
    return [
      typeLabel,
      stateLabel,
      card.card_created_date,
      card.card_updated_date,
      card.title,
      card.subtitle,
      card.preview,
      card.path,
      card.affinity_label,
      card.affinity_source,
      card.analysis_state_label,
      card.analysis_state_short_label,
      card.card_maturity?.axis,
      card.card_maturity?.display_level,
      card.card_maturity?.level,
      card.maturity_reason_cn,
      card.person_maturity_label,
      card.person_maturity_level,
      card.researcher_relation_label,
      card.hierarchy_state_label,
      card.cluster_label_zh,
      card.direction_level,
      card.relationship_group,
      projectOperationalStatusLabel(card, (key) => key),
      card.operational_status?.responsibility,
      card.operational_status?.engagement,
      card.operational_status?.state,
      card.operational_status?.lifecycle_phase,
      card.operational_status?.freshness,
      ...(Array.isArray(card.related_people_preview) ? card.related_people_preview.map((person) => person.title || "") : []),
      ...(Array.isArray(card.badges) ? card.badges : []),
    ].filter(Boolean).join(" ");
  }

  function shortAssetDate(value = "") {
    const raw = String(value || "").trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw.slice(5);
    return raw;
  }

  function assetCardDateStamp(card = {}, translate = (key) => key) {
    const created = String(card.card_created_date || "").trim();
    const updated = String(card.card_updated_date || "").trim();
    if (!created && !updated) return { label: "", title: "" };
    const label = updated
      ? `${translate("assetDateUpdatedShort")} ${shortAssetDate(updated)}`
      : `${translate("assetDateCreatedShort")} ${shortAssetDate(created)}`;
    const title = [
      created ? `${translate("assetDateCreated")}: ${created}` : "",
      updated ? `${translate("assetDateUpdated")}: ${updated}` : "",
    ].filter(Boolean).join(" · ");
    return { label, title };
  }

  function renderHero({ summary = {}, selectedInboxTotal = 0 } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const objectCount = summary.semanticObjectCount ?? 0;
    const commitmentCount = summary.commitmentCount ?? 0;
    const documentCount = summary.previewDocumentCount ?? 0;
    const archiveCount = summary.archivedDocumentCount ?? 0;
    const typedCount = String(translate("assetsTypedCountSummary"))
      .replace("{objects}", String(objectCount))
      .replace("{commitments}", String(commitmentCount))
      .replace("{documents}", String(documentCount))
      .replace("{archive}", String(archiveCount));
    return `
      <section class="asset-overview-hero">
        <div>
          <span>${escapeHtml(translate("assetsWhatTitle"))}</span>
          <h3>${escapeHtml(typedCount)}</h3>
          <p>${escapeHtml(translate("assetsWhatBody"))}</p>
          <small data-card-view-contract="${summary.viewSafe ? "safe" : "needs-review"}">${escapeHtml(translate(summary.viewSafe ? "assetsViewSafe" : "assetsViewNeedsReview"))}</small>
        </div>
      </section>
    `;
  }

  function renderCommitmentLens({ items = [], selectedIds = [] } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    const selected = new Set((Array.isArray(selectedIds) ? selectedIds : []).map(String));
    const available = (Array.isArray(items) ? items : []).filter((item) => item?.id);
    const mandatory = available.filter((item) => item.mandatory_visibility === true);
    const promotedIds = new Set([
      ...mandatory.map((item) => String(item.id)),
      ...selected,
    ]);
    const promoted = available.filter((item) => promotedIds.has(String(item.id)));
    const optionalCapacity = Math.max(0, 12 - promoted.length);
    const mandatoryOverflow = Math.max(0, mandatory.length - 12);
    const defaultCommitments = [
      ...promoted,
      ...available.filter((item) => !promotedIds.has(String(item.id))).slice(0, optionalCapacity),
    ];
    if (!available.length) return "";
    const defaultIds = new Set(defaultCommitments.map((item) => String(item.id)));
    const regionOrder = ["Current", "Review", "Waiting", "Incubating", "Paused", "Knowledge", "Archive"];
    const chinese = String(translate("libraryLensTitle")).includes("研究");
    const regionLabels = chinese
      ? { Current: "当前", Review: "待复核", Waiting: "等待触发", Incubating: "孵化与排队", Paused: "暂停", Knowledge: "知识", Archive: "历史与归档视图" }
      : { Current: "Current", Review: "Review", Waiting: "Waiting", Incubating: "Incubating and queued", Paused: "Paused", Knowledge: "Knowledge", Archive: "History and archive view" };
    const renderButton = (item, index) => {
      const id = String(item.id);
      const active = selected.has(id);
      const ordinal = String(index + 1).padStart(2, "0");
      const required = item.mandatory_visibility === true;
      return `<button type="button" data-action-kind="navigation" data-library-lens-item="${escapeHtml(id)}" data-library-lens-mandatory="${required ? "true" : "false"}" data-library-region="${escapeHtml(item.primary_region || "Review")}" aria-pressed="${active ? "true" : "false"}" class="${active ? "selected" : ""}"><span class="library-commitment-lens-card-heading"><span aria-hidden="true">${ordinal}</span><strong>${escapeHtml(item.title || id)}</strong></span><small>${escapeHtml(item.next_step || item.nextStep || translate("libraryLensUnknownStep"))}</small>${required ? `<em>${escapeHtml(translate("libraryLensMandatory"))}</em>` : ""}</button>`;
    };
    const regionGroups = regionOrder.map((region) => ({
      region,
      items: available.filter((item) => String(item.primary_region || "Review") === region),
    })).filter((group) => group.items.length);
    return `<section class="library-commitment-lens" data-library-commitment-lens aria-label="${escapeHtml(translate("libraryLensTitle"))}">
      <header><div><strong>${escapeHtml(translate("libraryLensTitle"))}</strong><p>${escapeHtml(translate("libraryLensHint"))}</p></div><div class="library-commitment-lens-counts"><small class="library-commitment-lens-count" aria-live="polite">${escapeHtml(String(translate("libraryLensSelected")).replace("{count}", String(selected.size)))}</small>${mandatory.length ? `<small class="library-commitment-lens-count is-mandatory">${escapeHtml(String(translate("libraryLensMandatorySummary")).replace("{count}", String(mandatory.length)).replace("{overflow}", String(mandatoryOverflow)))}</small>` : ""}</div></header>
      <div class="library-commitment-regions">
        ${regionGroups.map((group) => {
          const visible = group.items.filter((item) => defaultIds.has(String(item.id)));
          const remaining = group.items.filter((item) => !defaultIds.has(String(item.id)));
          const open = visible.length > 0;
          const moreLabel = chinese ? `展开其余 ${remaining.length} 项` : `Show ${remaining.length} more`;
          return `<details class="library-commitment-region" data-library-region="${escapeHtml(group.region)}"${open ? " open" : ""}><summary><strong>${escapeHtml(regionLabels[group.region] || group.region)}</strong><span>${group.items.length}</span></summary>${visible.length ? `<div class="library-commitment-lens-options">${visible.map(renderButton).join("")}</div>` : ""}${remaining.length ? `<details class="library-commitment-region-more"><summary>${escapeHtml(moreLabel)}</summary><div class="library-commitment-lens-options">${remaining.map(renderButton).join("")}</div></details>` : ""}</details>`;
        }).join("")}
      </div>
      <small class="library-commitment-lens-boundary">${escapeHtml(translate("libraryLensBoundary"))}</small>
    </section>`;
  }

  function renderCommitmentLensProjection({ active = false, commitments = [] } = {}, deps = {}) {
    if (!active || !Array.isArray(commitments) || !commitments.length) return "";
    const { escapeHtml, translate } = normalizeDeps(deps);
    const previewButton = deps.previewButton || (() => "");
    const renderMaterial = (material = {}) => {
      const label = material.relationKind === "canonical_anchor"
        ? translate("libraryLensCanonicalAnchor")
        : translate("libraryLensCanonicalRelation");
      const title = material.previewable
        ? previewButton(material.path, material.title || material.path)
        : `<strong>${escapeHtml(material.title || material.path || "")}</strong>`;
      return `<li data-library-relation-kind="${escapeHtml(material.relationKind || "")}" data-library-relation-path="${escapeHtml(material.path || "")}">${title}<small>${escapeHtml(label)}</small></li>`;
    };
    return `<section class="library-lens-projection" data-library-lens-projection aria-label="${escapeHtml(translate("libraryLensProjectionTitle"))}">
      <header><strong>${escapeHtml(translate("libraryLensProjectionTitle"))}</strong><small>${escapeHtml(translate("libraryLensProjectionHint"))}</small></header>
      <div class="library-lens-projection-groups">
        ${commitments.map((commitment = {}) => `<article data-library-lens-commitment="${escapeHtml(commitment.id || "")}">
          <header><h4>${escapeHtml(commitment.title || commitment.id || "")}</h4><button type="button" data-action-kind="direct" data-library-open-execution="${escapeHtml(commitment.id || "")}">${escapeHtml(translate("libraryLensOpenExecution"))}</button></header>
          ${commitment.anchor ? `<ul class="library-lens-anchor">${renderMaterial(commitment.anchor)}</ul>` : `<p class="library-lens-empty">${escapeHtml(translate("libraryLensMissingAnchor"))}</p>`}
          ${Array.isArray(commitment.related) && commitment.related.length
            ? `<ul class="library-lens-relations">${commitment.related.map(renderMaterial).join("")}</ul>`
            : `<p class="library-lens-empty">${escapeHtml(translate("libraryLensNoExplicitRelation"))}</p>`}
          ${Number(commitment.omittedCount || 0) > 0 ? `<p class="library-lens-empty">${escapeHtml(String(translate("libraryLensMoreExplicitRelations")).replace("{count}", String(commitment.omittedCount)))}</p>` : ""}
        </article>`).join("")}
      </div>
    </section>`;
  }

  function renderAssetCardBoxWorkbench({ boxes = [], focusCard = null, publicMode = false } = {}, deps = {}) {
    const { escapeHtml, shortText, translate } = normalizeDeps(deps);
    const activeFocusId = focusCard?.id || "";
    const activeRelationIds = new Set(Array.isArray(focusCard?.relation_ids) ? focusCard.relation_ids : []);
    const totalCards = boxes.reduce((sum, box) => sum + Number(box.count || 0), 0);
    const visibleBoxes = boxes.filter((box) => Array.isArray(box.cards) && box.cards.length);
    if (!visibleBoxes.length) return "";
    return `
      <section class="asset-card-workbench" aria-label="${escapeHtml(translate("assetsCardBoxTitle"))}">
        <header>
          <div class="asset-card-workbench-intro">
            <strong>${escapeHtml(translate("assetsCardBoxTitle"))}</strong>
            <span>${escapeHtml(translate("assetsCardBoxHint"))}</span>
          </div>
          <div class="asset-card-workbench-actions">
            <label class="asset-card-global-search">
              <span>${escapeHtml(translate("assetsCardGlobalSearchLabel"))}</span>
              <input type="search" data-asset-card-global-search aria-label="${escapeHtml(translate("assetsCardGlobalSearchLabel"))}" placeholder="${escapeHtml(translate("assetsCardGlobalSearchPlaceholder"))}" autocomplete="off" />
              <button type="button" data-action-kind="direct" data-asset-card-global-search-clear aria-label="${escapeHtml(translate("assetsCardSearchClear"))}" hidden disabled>×</button>
              <small data-asset-card-global-search-status>${escapeHtml(translate("assetsCardGlobalSearchIdle"))}</small>
            </label>
            <small>${escapeHtml(`${visibleBoxes.length} ${translate("assetsCardBoxUnit")} · ${totalCards} ${translate("assetsCardUnit")} · ${translate("assetsCardBoxCompactRule")}`)}</small>
            <button type="button" data-action-kind="navigation" data-asset-open-intake>${escapeHtml(translate(publicMode ? "researchPortfolioPublicDemoLabel" : "assetCreateEntry"))}</button>
          </div>
        </header>
        <div class="asset-card-workspace-layout">
          <div class="asset-card-box-grid" data-asset-card-boxes>
            ${visibleBoxes.map((box) => `
            <details class="asset-card-box type-${escapeHtml(box.type || "asset")}" data-asset-card-box="${escapeHtml(box.id || "")}" data-asset-card-box-type="${escapeHtml(box.type || "")}" data-asset-card-display-limit="${escapeHtml(String(box.display_limit || 6))}" open>
              <summary>
                <div class="asset-card-box-title">
                  <strong>${escapeHtml(box.label || box.type || "")}</strong>
                  <span>${escapeHtml(String(box.count || 0))}</span>
                </div>
                <small>
                  <span class="asset-card-box-state-closed">${escapeHtml(translate("assetsCardBoxMore"))}</span>
                  <span class="asset-card-box-state-open">${escapeHtml(translate("assetsCardBoxCollapse"))}</span>
                </small>
              </summary>
              <div class="asset-card-box-content">
                <details class="asset-card-box-advanced">
                  <summary>${escapeHtml(translate("assetsCardBoxAdvanced"))}</summary>
                  ${box.sort_rule ? `<small class="asset-card-box-sort-rule">${escapeHtml(box.sort_rule)}</small>` : ""}
                  <div class="asset-card-box-filters" aria-label="${escapeHtml(translate("assetsCardMaturityFilter"))}">
                    ${(Array.isArray(box.maturity_filters) ? box.maturity_filters : ["all"]).map((filter) => `
                      <button type="button" data-action-kind="navigation" data-asset-card-filter="${escapeHtml(filter)}" data-asset-card-filter-box="${escapeHtml(box.id || "")}" aria-pressed="${filter === "all" ? "true" : "false"}">${escapeHtml(filter === "all" ? translate("assetsCardFilterAll") : filter === "R_research_mainline" ? "R" : filter.slice(0, 2))}</button>
                    `).join("")}
                  </div>
                  <label class="asset-card-box-search">
                    <span>${escapeHtml(translate("assetsCardSearchLabel"))}</span>
                    <input
                      type="search"
                      data-asset-card-search
                      data-asset-card-search-box="${escapeHtml(box.id || "")}"
                      aria-label="${escapeHtml(`${translate("assetsCardSearchLabel")}: ${box.label || box.type || ""}`)}"
                      placeholder="${escapeHtml(translate("assetsCardSearchPlaceholder"))}"
                      autocomplete="off"
                    />
                    <button type="button" data-action-kind="direct" data-asset-card-search-clear="${escapeHtml(box.id || "")}" aria-label="${escapeHtml(translate("assetsCardSearchClear"))}" hidden disabled>×</button>
                    <small data-asset-card-search-status>${escapeHtml(translate("assetsCardSearchIdle"))}</small>
                  </label>
                </details>
              <div class="asset-card-box-deck" data-asset-card-box-deck>
                ${box.cards.map((card, index) => {
                  const relationIds = Array.isArray(card.relation_ids) ? card.relation_ids : [];
                  const relationRanks = card.relation_ranks && typeof card.relation_ranks === "object" ? card.relation_ranks : {};
                  const isSelected = activeFocusId === card.id;
                  const isConnected = activeRelationIds.has(card.id);
                  const typeLabel = assetCardTypeLabel(card.type || box.type || "asset", translate);
                  const stateLabel = assetCardStateLabel(card.state || "confirmed", translate);
                  const dateStamp = assetCardDateStamp(card, translate);
                  const cardMaturity = card.card_maturity || {};
                  const maturityLevel = cardMaturity.display_level || cardMaturity.level || "";
                  const maturityDisplay = maturityLevel && !cardMaturity.confirmed
                    ? `${maturityLevel} · ${translate("assetMaturityPendingShort")}`
                    : maturityLevel;
                  const relatedPeople = Array.isArray(card.related_people_preview) ? card.related_people_preview : [];
                  const relatedPeopleLabel = card.type === "project" && relatedPeople.length
                    ? `${translate("assetLineagePeople")}: ${relatedPeople.slice(0, 2).map((person) => person.title || "").filter(Boolean).join(" / ")}${relatedPeople.length > 2 ? ` +${relatedPeople.length - 2}` : ""}`
                    : "";
                  const projectOperationalLabel = projectOperationalStatusLabel(card, translate);
                  const faceSubtitle = ["paper", "talk", "source"].includes(card.type || box.type || "")
                    ? (card.mainline || card.subtitle || "")
                    : "";
                  const faceFooter = [projectOperationalLabel, faceSubtitle, relatedPeopleLabel].filter(Boolean);
                  return `
                    <button
                      type="button"
                      data-action-kind="navigation"
                      class="asset-box-card type-${escapeHtml(card.type || box.type || "asset")} state-${escapeHtml(card.state || "confirmed")} depth-${escapeHtml(String(card.level || 2))} ${isSelected ? "selected" : ""} ${isConnected ? "connected" : ""}"
                      title="${escapeHtml([card.title || "", maturityLevel, ...faceFooter].filter(Boolean).join(" · "))}"
                      draggable="true"
                      data-asset-box-card
                      data-asset-card-id="${escapeHtml(card.id || "")}"
                      data-asset-card-box-id="${escapeHtml(box.id || "")}"
                      data-asset-card-type="${escapeHtml(card.type || box.type || "")}"
                      data-asset-card-type-label="${escapeHtml(typeLabel)}"
                      data-asset-card-state="${escapeHtml(card.state || "")}"
                      data-asset-card-state-label="${escapeHtml(stateLabel)}"
                      data-asset-card-analysis-state="${escapeHtml(card.analysis_state || "")}"
                      data-asset-card-analysis-label="${escapeHtml(card.analysis_state_label || card.analysis_state_short_label || "")}"
                      data-asset-card-maturity-axis="${escapeHtml(cardMaturity.axis || "")}"
                      data-asset-card-maturity-level="${escapeHtml(cardMaturity.level || "")}"
                      data-asset-card-maturity-display="${escapeHtml(maturityLevel)}"
                      data-asset-card-maturity-source="${escapeHtml(cardMaturity.source || "")}"
                      data-asset-card-maturity-confirmed="${cardMaturity.confirmed ? "true" : "false"}"
                      data-asset-card-maturity-review-needed="${cardMaturity.review_needed ? "true" : "false"}"
                      data-asset-card-maturity-action="${escapeHtml(cardMaturity.action || "verify")}"
                      data-asset-card-maturity-target="${escapeHtml(cardMaturity.target_level || "")}"
                      data-asset-card-maturity-reason="${escapeHtml(cardMaturity.reason || "")}"
                      data-asset-card-person-maturity-level="${escapeHtml(card.person_maturity_level || "")}"
                      data-asset-card-person-maturity-label="${escapeHtml(card.person_maturity_label || "")}"
                      data-asset-card-researcher-relation-level="${escapeHtml(card.researcher_relation_level || "")}"
                      data-asset-card-researcher-relation-label="${escapeHtml(card.researcher_relation_label || "")}"
                      data-asset-card-researcher-relation-reason="${escapeHtml(card.researcher_relation_reason || "")}"
                      data-asset-card-hierarchy-state="${escapeHtml(card.hierarchy_state || "")}"
                      data-asset-card-hierarchy-label="${escapeHtml(card.hierarchy_state_label || "")}"
                      data-asset-card-hierarchy-summary="${escapeHtml(card.hierarchy_summary_cn || "")}"
                      data-asset-card-hierarchy-recommendation="${escapeHtml(card.hierarchy_recommendation_cn || "")}"
                      data-asset-card-cluster-level="${escapeHtml(card.cluster_level || "")}"
                      data-asset-card-cluster-label="${escapeHtml(card.cluster_label_zh || "")}"
                      data-asset-card-cluster-summary="${escapeHtml(card.cluster_summary_cn || "")}"
                      data-asset-card-cluster-recommendation="${escapeHtml(card.cluster_recommendation_cn || "")}"
                      data-asset-card-direction-level="${escapeHtml(card.direction_level || "")}"
                      data-asset-card-direction-summary="${escapeHtml(card.direction_summary_cn || "")}"
                      data-asset-card-mainline="${escapeHtml(card.mainline || "")}"
                      data-asset-card-project-family="${escapeHtml(card.project_family || "")}"
                      data-asset-card-level="${escapeHtml(String(card.level || 2))}"
                      data-asset-card-created-date="${escapeHtml(card.card_created_date || "")}"
                      data-asset-card-updated-date="${escapeHtml(card.card_updated_date || "")}"
                      data-asset-card-title="${escapeHtml(card.title || "")}"
                      data-asset-card-subtitle="${escapeHtml(card.subtitle || "")}"
                      data-asset-card-affinity-group="${escapeHtml(card.affinity_group || "")}"
                      data-asset-card-affinity-label="${escapeHtml(card.affinity_label || "")}"
                      data-asset-card-preview="${escapeHtml(card.preview || "")}"
                      data-asset-card-path="${escapeHtml(card.path || "")}"
                      data-asset-card-portfolio-binding="${escapeHtml(card.portfolio_binding?.state || "")}"
                      data-asset-card-operational-responsibility="${escapeHtml(card.operational_status?.responsibility || "")}"
                      data-asset-card-operational-engagement="${escapeHtml(card.operational_status?.engagement || "")}"
                      data-asset-card-operational-state="${escapeHtml(card.operational_status?.state || "")}"
                      data-asset-card-operational-lifecycle="${escapeHtml(card.operational_status?.lifecycle_phase || "")}"
                      data-asset-card-operational-freshness="${escapeHtml(card.operational_status?.freshness || "")}"
                      data-asset-card-search-text="${escapeHtml(assetCardSearchText(card, typeLabel, stateLabel))}"
                      data-asset-card-relations="${escapeHtml(relationIds.join("|"))}"
                      data-asset-card-relation-ranks="${escapeHtml(Object.entries(relationRanks).map(([id, rank]) => `${id}::${rank}`).join("||"))}"
                      data-asset-card-relation-reasons="${escapeHtml((card.relation_reasons || []).join("||"))}"
                      data-asset-card-lineage-chips="${escapeHtml((card.lineage_chips || []).map((chip) => [chip.kind || "", chip.label || "", chip.hint || ""].join("::")).join("||"))}"
                      data-asset-card-related-people="${escapeHtml(relatedPeople.map((person) => [person.id || "", person.title || "", person.path || ""].join("::")).join("||"))}"
                      data-asset-card-index="${escapeHtml(String(index))}"
                      data-asset-card-display-limit="${escapeHtml(String(box.display_limit || 6))}"
                      style="--asset-card-order: ${escapeHtml(String(index))}"
                      aria-pressed="${isSelected ? "true" : "false"}"
                      ${index >= Number(box.display_limit || 6) ? "hidden" : ""}
                    >
                      <span>
                        <b>${escapeHtml(typeLabel)}</b>
                        <small class="asset-card-top-meta">
                          ${maturityLevel ? `<i class="asset-card-maturity-chip ${cardMaturity.confirmed ? "is-confirmed" : "is-pending"}" title="${escapeHtml(cardMaturity.reason || maturityLevel)}">${escapeHtml(maturityDisplay)}</i>` : ""}
                          ${dateStamp.label ? `<em class="asset-card-date-stamp" title="${escapeHtml(dateStamp.title)}">${escapeHtml(dateStamp.label)}</em>` : ""}
                        </small>
                      </span>
                      <strong>${escapeHtml(shortText(card.title || "", 58))}</strong>
                      ${faceFooter.length ? `<footer>${faceFooter.map((item) => `<em>${escapeHtml(shortText(item, 42))}</em>`).join("")}</footer>` : ""}
                    </button>
                  `;
                }).join("")}
                ${box.hidden_count ? `
                  <button
                    type="button"
                    data-action-kind="navigation"
                    class="asset-card-box-overflow"
                    data-asset-card-expand-box="${escapeHtml(box.id || "")}"
                    data-asset-card-hidden-count="${escapeHtml(String(box.hidden_count || 0))}"
                    aria-expanded="false"
                  >
                    <strong>${escapeHtml(`+${box.hidden_count}`)}</strong>
                    <span>${escapeHtml(translate("assetsCardBoxMore"))}</span>
                  </button>
                ` : ""}
              </div>
              </div>
            </details>
            `).join("")}
          </div>
          <aside class="asset-card-lower-workbench" data-asset-card-lower-workbench aria-label="${escapeHtml(translate("assetCardSidecarTitle"))}" hidden>
            <section class="asset-card-focus-panel asset-card-detail-panel is-empty" data-asset-card-focus-panel>
              <strong>${escapeHtml(translate("assetsCardBoxSelectTitle"))}</strong>
              <span>${escapeHtml(translate("assetsCardBoxSelectHint"))}</span>
              <div data-asset-card-related></div>
            </section>
            <details class="asset-card-basket-drawer" data-asset-card-basket-drawer>
              <summary>
                <strong>${escapeHtml(translate("assetBasketCollapsedTitle"))}</strong>
                <span>${escapeHtml(translate("assetBasketCollapsedHint"))}</span>
                <small data-asset-basket-count>0</small>
              </summary>
              <section class="asset-card-basket-panel" data-asset-card-basket-panel aria-label="${escapeHtml(translate("assetBasketTitle"))}">
                <header>
                  <div>
                    <strong>${escapeHtml(translate("assetBasketTitle"))}</strong>
                    <span>${escapeHtml(translate("assetBasketHint"))}</span>
                  </div>
                </header>
                <div class="asset-card-basket-dropzone" data-asset-basket-list data-asset-basket-dropzone>
                  <p>${escapeHtml(translate("assetBasketEmpty"))}</p>
                </div>
                <div class="asset-card-basket-writeback" data-asset-basket-writeback-options aria-label="${escapeHtml(translate("assetBasketWritebackTitle"))}">
                  <span>${escapeHtml(translate("assetBasketWritebackTitle"))}</span>
                  <label>
                    <input type="checkbox" data-asset-basket-writeback="supplement_existing" checked>
                    ${escapeHtml(translate("assetBasketWritebackSupplement"))}
                  </label>
                  <label>
                    <input type="checkbox" data-asset-basket-writeback="new_composition_card" checked>
                    ${escapeHtml(translate("assetBasketWritebackNewCard"))}
                  </label>
                </div>
                <footer>
                  <button type="button" data-action-kind="preview-confirm" data-asset-basket-action="relation" title="${escapeHtml(translate("assetBasketFindRelationHint"))}" disabled>${escapeHtml(translate("assetBasketFindRelation"))}</button>
                  <button type="button" data-action-kind="preview-confirm" data-asset-basket-action="recompute" title="${escapeHtml(translate("assetBasketRecomputeRelationHint"))}" disabled>${escapeHtml(translate("assetBasketRecomputeRelation"))}</button>
                  <button type="button" data-action-kind="preview-confirm" data-asset-basket-action="project" title="${escapeHtml(translate("assetBasketNewProjectHint"))}" disabled>${escapeHtml(translate("assetBasketNewProject"))}</button>
                  <button type="button" data-action-kind="preview-confirm" data-asset-basket-action="research" title="${escapeHtml(translate("assetBasketResearchTaskHint"))}" disabled>${escapeHtml(translate("assetBasketResearchTask"))}</button>
                  <button type="button" data-action-kind="direct" data-asset-basket-clear title="${escapeHtml(translate("assetBasketClearHint"))}" disabled>${escapeHtml(translate("assetBasketClear"))}</button>
                </footer>
                <output data-asset-basket-status>${escapeHtml(translate("assetBasketSafeHint"))}</output>
              </section>
            </details>
          </aside>
        </div>
        <details class="asset-create-panel" data-asset-create-panel>
          <summary>
            <span>${escapeHtml(translate(publicMode ? "researchPortfolioPublicDemoLabel" : "assetCreateTitle"))}</span>
            <small>${escapeHtml(translate(publicMode ? "onboardingPublicBody" : "assetCreateHint"))}</small>
          </summary>
          <form data-asset-create-form>
            <label>
              <span>${escapeHtml(translate("assetCreateType"))}</span>
              <select name="asset_type" data-asset-create-type aria-label="${escapeHtml(translate("assetCreateType"))}">
                <option value="paper">${escapeHtml(translate("assetsTypePaper"))}</option>
                <option value="project">${escapeHtml(translate("assetsTypeProject"))}</option>
                <option value="person">${escapeHtml(translate("assetsTypePerson"))}</option>
                <option value="talk">${escapeHtml(translate("assetsTypeTalk"))}</option>
                <option value="other">${escapeHtml(translate("assetsTypeOther"))}</option>
              </select>
            </label>
            <label>
              <span>${escapeHtml(translate("assetCreateName"))}</span>
              <input name="title" type="text" autocomplete="off" aria-label="${escapeHtml(translate("assetCreateName"))}" placeholder="${escapeHtml(translate("assetCreateNamePlaceholder"))}" required>
            </label>
            ${publicMode ? "" : `<label>
              <span>${escapeHtml(translate("assetCreateSource"))}</span>
              <input name="source_hint" type="text" autocomplete="off" aria-label="${escapeHtml(translate("assetCreateSource"))}" placeholder="${escapeHtml(translate("assetCreateSourcePlaceholder"))}">
            </label>`}
            ${publicMode ? "" : `<details class="asset-create-optional">
              <summary>${escapeHtml(translate("assetCreateOptional"))}</summary>
              <div>
                <label class="asset-create-local-file">
                  <span>${escapeHtml(translate("assetCreateLocalFile"))}</span>
                  <input name="local_file" type="file" aria-label="${escapeHtml(translate("assetCreateLocalFile"))}">
                  <small>${escapeHtml(translate("assetCreateLocalFileHint"))}</small>
                </label>
                <label>
                  <span>${escapeHtml(translate("assetCreateTarget"))}</span>
                  <input name="target_hint" type="text" autocomplete="off" aria-label="${escapeHtml(translate("assetCreateTarget"))}" placeholder="${escapeHtml(translate("assetCreateTargetPlaceholder"))}">
                </label>
                <label class="asset-create-boundary">
                  <span>${escapeHtml(translate("assetCreateBoundary"))}</span>
                  <textarea name="boundary_note" rows="2" aria-label="${escapeHtml(translate("assetCreateBoundary"))}" placeholder="${escapeHtml(translate("assetCreateBoundaryPlaceholder"))}"></textarea>
                </label>
              </div>
            </details>`}
            <footer>
              <button type="submit" class="primary" data-action-kind="preview-confirm">${escapeHtml(translate("assetCreateSubmit"))}</button>
              <output data-asset-create-status>${escapeHtml(translate("assetCreateSafeHint"))}</output>
            </footer>
          </form>
        </details>
      </section>
    `;
  }

  function renderPublicDemoToggle({ visible = true } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    return `
      <section class="asset-demo-toggle" aria-label="${escapeHtml(translate("publicDemoToggleTitle"))}">
        <div>
          <strong>${escapeHtml(translate("publicDemoToggleTitle"))}</strong>
          <span>${escapeHtml(translate(visible ? "publicDemoToggleVisibleHint" : "publicDemoToggleHiddenHint"))}</span>
        </div>
        <button type="button" data-action-kind="navigation" data-public-demo-toggle aria-pressed="${visible ? "true" : "false"}">
          ${escapeHtml(translate(visible ? "publicDemoToggleHide" : "publicDemoToggleShow"))}
        </button>
      </section>
    `;
  }

  function renderAssetOverviewHtml({
    summary = {},
    cardBoxes = [],
    focusCard = null,
    publicMode = false,
    publicDemoToggleHtml = "",
    workSessionTrayHtml = "",
    intakePanelHtml = "",
    deps = {},
  } = {}) {
    return [
      renderHero({ summary, selectedInboxTotal: summary.inboxTotal || 0 }, deps),
      workSessionTrayHtml,
      publicDemoToggleHtml,
      intakePanelHtml,
      renderAssetCardBoxWorkbench({ boxes: cardBoxes, focusCard, publicMode }, deps),
    ].join("");
  }

  global.ResearchOSAssetOverviewView = Object.freeze({
    projectOperationalStatusLabel,
    renderHero,
    renderCommitmentLens,
    renderCommitmentLensProjection,
    renderAssetCardBoxWorkbench,
    renderPublicDemoToggle,
    renderAssetOverviewHtml,
  });
})(window);
