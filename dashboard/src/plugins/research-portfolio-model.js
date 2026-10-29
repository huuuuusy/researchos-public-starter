/* ResearchOS maintenance header.
 * 中文：Research portfolio 插件模型；独占责任分类、freshness 与 lead/support/waiting 统计。
 * English: Research-portfolio plugin model; exclusively owns responsibility, freshness, and lead/support/waiting projections.
 */
(function attachResearchOSResearchPortfolioModel(global) {
  const Contracts = global.ResearchOSContracts || {};
  const safeArray = (value) => Array.isArray(value) ? value : [];
  const backgroundPhases = new Set(["submitted", "under_review", "decision"]);
  const lifecyclePhases = new Set([
    "scoping", "planned", "experiment_preparation", "production", "presentation_preparation", "gated_operation",
    "writing", "release_preparation", "submitted", "under_review", "rebuttal",
    "decision", "revision", "accepted", "published", "paused", "completed",
  ]);

  function managementBucketForItem(item = {}) {
    const state = String(item.state || "").trim();
    const lifecycleState = String(item.lifecycleState || item.lifecycle_state || "").trim();
    const lifecyclePhase = String(item.lifecyclePhase || item.lifecycle_phase || "").trim();
    if (lifecyclePhase === "unclassified") return "unclassified";
    if (state === "closed" || lifecycleState === "completed") return "closed";
    if (state === "paused" || lifecycleState === "paused") return "paused";
    if (state === "waiting" || lifecycleState === "waiting") return "waiting";
    if (state === "conditional") return "project_candidate";
    if (state === "queued") return "queued";
    if (state === "mainline" && lifecycleState === "open") return "active";
    return "unclassified";
  }

  function managementZoneForBucket(bucket = "unclassified") {
    return {
      active: "active",
      queued: "pending",
      project_candidate: "pending",
      waiting: "inactive",
      paused: "inactive",
      closed: "closed",
      unclassified: "pending",
    }[String(bucket || "unclassified")] || "pending";
  }

  function managementZoneForItem(item = {}) {
    return managementZoneForBucket(item.managementBucket || managementBucketForItem(item));
  }

  function localizedValue(item = {}, key = "", language = "en", fallback = "") {
    const localized = item?.localized?.[language];
    const value = localized && typeof localized === "object" ? localized[key] : undefined;
    return String(value ?? item?.[key] ?? fallback ?? "");
  }

  function liveFreshness(lastVerified = "", staleAfterDays = 14, now = new Date()) {
    const value = String(lastVerified || "").trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return { ageDays: null, freshness: "unverified" };
    const verified = Date.parse(`${value}T00:00:00Z`);
    if (!Number.isFinite(verified)) return { ageDays: null, freshness: "unverified" };
    const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
    const ageDays = Math.floor((today - verified) / 86400000);
    const threshold = Math.max(1, Number(staleAfterDays) || 14);
    if (ageDays < 0) return { ageDays, freshness: "unverified" };
    if (ageDays > threshold) return { ageDays, freshness: "stale" };
    if (ageDays === threshold) return { ageDays, freshness: "review_due" };
    return { ageDays, freshness: "current" };
  }

  function liveAttention(attentionState = "unscheduled", attentionDate = "", carryoverDays = 0, now = new Date()) {
    const state = String(attentionState || "unscheduled");
    const value = String(attentionDate || "").trim();
    const existingDays = Math.max(0, Number(carryoverDays) || 0);
    if (!["today", "carryover", "upcoming"].includes(state) || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return { attentionState: state, carryoverDays: existingDays };
    }
    const scheduled = Date.parse(`${value}T00:00:00Z`);
    const current = now && typeof now.getFullYear === "function" ? now : new Date(now);
    if (!Number.isFinite(scheduled) || !Number.isFinite(current?.getTime?.())) {
      return { attentionState: state, carryoverDays: existingDays };
    }
    const today = Date.UTC(current.getFullYear(), current.getMonth(), current.getDate());
    const elapsedDays = Math.floor((today - scheduled) / 86400000);
    if (elapsedDays < 0) return { attentionState: "upcoming", carryoverDays: 0 };
    if (elapsedDays === 0) return { attentionState: "today", carryoverDays: 0 };
    return {
      attentionState: "carryover",
      carryoverDays: Math.max(1, existingDays, elapsedDays),
    };
  }

  function build(portfolio = {}, text = (key) => key, language = "en") {
    // A fictional demo fixes its own date so its schedule never drifts into the past; real portfolios use today.
    const referenceDate = /^\d{4}-\d{2}-\d{2}$/.test(String(portfolio?.reference_date || "")) ? String(portfolio.reference_date) : "";
    const now = referenceDate ? new Date(`${referenceDate}T12:00:00`) : new Date();
    const sensitivity = String(portfolio?.sensitivity || "").trim();
    const presentationMode = String(portfolio?.presentation_mode || (sensitivity === "private" ? "private_authority" : "")).trim();
    const items = safeArray(portfolio?.items)
      .filter((item) => item && typeof item === "object" && item.title)
      .map((item) => {
        const live = liveFreshness(item.last_verified, item.stale_after_days, now);
        const attention = liveAttention(item.attention_state, item.attention_date, item.carryover_days, now);
        const qualityIssues = safeArray(item.quality_issues).map((issue) => String(issue));
        const rawLifecyclePhase = String(item.lifecycle_phase || "").trim();
        const lifecyclePhase = lifecyclePhases.has(rawLifecyclePhase)
          ? rawLifecyclePhase
          : "unclassified";
        const lifecycleState = String(item.lifecycle_state || "open");
        const responsibility = ["lead", "support"].includes(String(item.responsibility))
          ? String(item.responsibility)
          : "unclassified";
        const rawEngagement = String(item.engagement || "").trim();
        const engagement = responsibility === "lead"
          ? "ongoing"
          : (responsibility === "support" && ["ongoing", "temporary"].includes(rawEngagement)
            ? rawEngagement
            : "unclassified");
        const managementBucket = managementBucketForItem({ ...item, lifecyclePhase, lifecycleState });
        const managementZone = managementZoneForBucket(managementBucket);
        const explicitlyActionable = ["today", "carryover", "upcoming", "needs_next_step", "review_due"].includes(attention.attentionState);
        const resurfacingTrigger = Boolean(item.event_triggered)
          || ["needs_next_step", "review_due"].includes(attention.attentionState);
        const leadMainlineNeedsDecision = item.responsibility === "lead"
          && item.state === "mainline"
          && lifecycleState === "open"
          && lifecyclePhase !== "unclassified"
          && !backgroundPhases.has(lifecyclePhase)
          && attention.attentionState === "unscheduled";
        const cardMaturity = Contracts.cardMaturityProfile?.("project", item) || null;
        const relatedPeople = safeArray(item.related_people).map((person) => {
          if (typeof person === "string") return { name: person, path: "" };
          return {
            id: String(person?.id || "").trim(),
            name: String(person?.name || person?.title || person?.path || person?.id || "").trim(),
            path: String(person?.path || "").trim(),
          };
        }).filter((person) => person.name);
        return {
          adjustPrompt: localizedValue(item, "adjust_prompt", language),
          actionPrompt: localizedValue(item, "action_prompt", language),
          aiAction: localizedValue(item, "ai_action", language),
          accountableOwner: localizedValue(item, "accountable_owner", language, item.owner),
          assistant: localizedValue(item, "assistant", language),
          currentStage: localizedValue(item, "current_stage", language),
          currentStageCanonical: String(item.current_stage || "").trim(),
          activationTrigger: localizedValue(item, "activation_trigger", language),
          freshness: live.freshness,
          ageDays: live.ageDays,
          hasNumericProgress: Boolean(item.has_numeric_progress),
          id: String(item.id || ""),
          lane: String(item.lane || "research"),
          mergeRule: localizedValue(item, "merge_rule", language),
          nextStep: localizedValue(item, "next_step", language),
          nextStepCanonical: String(item.next_step || "").trim(),
          owner: localizedValue(item, "owner", language, item.accountable_owner),
          outputType: String(item.output_type || "research-output"),
          priority: String(item.priority || "P2"),
          priorityRank: Number(item.priority_rank ?? 99),
          progressDone: Number(item.progress_done || 0),
          progressLabel: localizedValue(item, "progress_label", language),
          progressPercent: Math.max(0, Math.min(100, Number(item.progress_percent || 0))),
          progressTotal: Number(item.progress_total || 0),
          providerId: String(item.provider_id || "research_portfolio"),
          responsibility,
          engagement,
          roleSummary: localizedValue(item, "role_summary", language),
          scheduleBucket: String(item.schedule_bucket || "later"),
          scheduleLabel: localizedValue(item, "schedule_label", language),
          scheduleOrder: Number(item.schedule_order || 999),
          selfAction: localizedValue(item, "self_action", language),
          sourceAnchor: String(item.source_anchor || ""),
          sourceAvailable: Boolean(item.source_available),
          sourcePath: localizedValue(item, "source_path", language),
          sourcePathAvailable: Object.prototype.hasOwnProperty.call(item, "source_path_available")
            ? Boolean(item.source_path_available)
            : Boolean(item.source_available),
          sourceRoot: localizedValue(item, "source_root", language),
          sourceRootAvailable: Object.prototype.hasOwnProperty.call(item, "source_root_available")
            ? Boolean(item.source_root_available)
            : false,
          continuationSource: localizedValue(item, "continuation_source", language)
            || localizedValue(item, "source_path", language),
          state: String(item.state || "conditional"),
          lifecycleNote: String(item.lifecycle_note || ""),
          successGate: localizedValue(item, "success_gate", language),
          staleAfterDays: Math.max(1, Number(item.stale_after_days) || 14),
          lastVerified: String(item.last_verified || ""),
          targetDate: String(item.target_date || ""),
          historicalTargetDate: String(item.historical_target_date || ""),
          targetDateBasis: localizedValue(item, "target_date_basis", language),
          lifecyclePhase,
          lifecycleState,
          managementBucket,
          managementZone,
          backgroundPhase: backgroundPhases.has(lifecyclePhase),
          eventTriggered: resurfacingTrigger,
          actionable: lifecycleState !== "completed" && (
            resurfacingTrigger
            || (managementBucket === "active" && !backgroundPhases.has(lifecyclePhase) && (explicitlyActionable || leadMainlineNeedsDecision))
          ),
          attentionState: attention.attentionState,
          attentionDate: String(item.attention_date || ""),
          reviewDate: String(item.review_date || ""),
          deadline: String(item.deadline || ""),
          todayOrder: Number(item.today_order || 0),
          carryoverDays: attention.carryoverDays,
          nextStepHash: String(item.next_step_hash || ""),
          attentionSource: String(item.attention_source || "unassigned"),
          lastAttentionAction: String(item.last_attention_action || ""),
          cardMaturity,
          relatedPeople,
          title: localizedValue(item, "title", language),
          publicDemo: presentationMode === "public_demo",
          qualityIssues,
          needsAttention: Boolean(item.needs_attention)
            || qualityIssues.length > 0
            || ["review_due", "stale", "unverified"].includes(live.freshness),
        };
      })
      .sort((a, b) => (
        ({ lead: 0, support: 1, unclassified: 2 }[a.responsibility] ?? 2)
        - ({ lead: 0, support: 1, unclassified: 2 }[b.responsibility] ?? 2)
      ) || (a.state === "mainline" ? 0 : 1) - (b.state === "mainline" ? 0 : 1)
        || a.todayOrder - b.todayOrder
        || a.scheduleOrder - b.scheduleOrder
        || a.title.localeCompare(b.title));
    const counts = ["mainline", "queued", "conditional", "waiting", "paused", "closed"].reduce((result, state) => {
      result[state] = items.filter((item) => item.state === state).length;
      return result;
    }, {});
    const managementCounts = ["active", "queued", "project_candidate", "waiting", "paused", "closed", "unclassified"].reduce((result, bucket) => {
      result[bucket] = items.filter((item) => item.managementBucket === bucket).length;
      return result;
    }, {});
    const managementZoneCounts = ["active", "pending", "inactive", "closed"].reduce((result, zone) => {
      result[zone] = items.filter((item) => item.managementZone === zone).length;
      return result;
    }, {});
    const phaseCounts = items.reduce((result, item) => {
      result[item.lifecyclePhase] = Number(result[item.lifecyclePhase] || 0) + 1;
      return result;
    }, {});
    const actionItems = items.filter((item) => item.actionable);
    const scheduleCounts = ["today", "this_week", "later"].reduce((result, bucket) => {
      result[bucket] = items.filter((item) => item.scheduleBucket === bucket).length;
      return result;
    }, {});
    const attentionCounts = ["today", "carryover", "unscheduled", "upcoming", "waiting", "paused", "review_due", "needs_next_step", "completed"].reduce((result, state) => {
      result[state] = items.filter((item) => item.attentionState === state).length;
      return result;
    }, {});
    const answer = {
      leadActive: items.filter((item) => item.responsibility === "lead" && item.state === "mainline").length,
      leadOpen: items.filter((item) => item.responsibility === "lead" && item.state !== "closed").length,
      supportActive: items.filter((item) => item.responsibility === "support" && item.state === "mainline").length,
      supportOpen: items.filter((item) => item.responsibility === "support" && item.state !== "closed").length,
      unclassified: items.filter((item) => item.responsibility === "unclassified").length,
      waiting: counts.waiting,
      queued: counts.queued,
      paused: counts.paused,
      needsReview: items.filter((item) => item.needsAttention && item.state !== "closed").length,
      needsAttention: items.filter((item) => item.needsAttention && item.state !== "closed").length,
      registeredTotal: items.length,
      classifiedTotal: items.filter((item) => item.responsibility !== "unclassified").length,
    };
    const rawCoverage = portfolio?.coverage && typeof portfolio.coverage === "object" ? portfolio.coverage : {};
    const coverageLive = liveFreshness(rawCoverage.reviewed, rawCoverage.stale_after_days, now);
    const candidateEvidencePackets = safeArray(rawCoverage.candidate_evidence_packets)
      .filter((packet) => packet && typeof packet === "object" && packet.candidate_id)
      .map((packet) => ({
        affectedObjects: safeArray(packet.affected_objects).map(String),
        automaticWritebackAllowed: Boolean(packet.automatic_writeback_allowed),
        candidateId: String(packet.candidate_id || ""),
        conflictSignals: safeArray(packet.conflict_signals).map(String),
        directStatementCount: Number(packet.direct_statement_count || 0),
        evidenceBoundary: String(packet.evidence_boundary || ""),
        humanOnlyFields: safeArray(packet.human_only_fields).map(String),
        projectableFields: safeArray(packet.projectable_fields).map((field) => ({
          field: String(field?.field || ""),
          sourcePaths: safeArray(field?.source_paths).map(String),
          value: String(field?.value || ""),
        })).filter((field) => field.field),
        recursivePropagationAllowed: Boolean(packet.recursive_propagation_allowed),
        safeNextStep: String(packet.safe_next_step || ""),
        sourceRefs: safeArray(packet.source_refs).map((reference) => ({
          excerpts: safeArray(reference?.excerpts).map(String),
          kind: String(reference?.kind || "source"),
          path: String(reference?.path || ""),
        })).filter((reference) => reference.path),
        staleSignals: safeArray(packet.stale_signals).map(String),
        status: String(packet.status || "identity_or_source_unresolved"),
      }));
    const coverage = {
      ageDays: coverageLive.ageDays,
      candidates: safeArray(rawCoverage.candidates).map(String),
      candidateEvidencePackets,
      complete: Boolean(rawCoverage.complete)
        && coverageLive.freshness === "current"
        && safeArray(rawCoverage.candidates).length === 0
        && safeArray(rawCoverage.missing_sources).length === 0,
      exclusions: safeArray(rawCoverage.exclusions).map(String),
      freshness: coverageLive.freshness,
      issues: safeArray(rawCoverage.issues).map(String),
      reviewed: String(rawCoverage.reviewed || ""),
      scope: String(rawCoverage.scope || ""),
      evidenceReadyCount: Number(rawCoverage.evidence_ready_count || 0),
      sourceUnresolvedCount: Number(rawCoverage.source_unresolved_count || 0),
      sources: safeArray(rawCoverage.sources).map(String),
      status: String(rawCoverage.status || "unverified"),
    };
    answer.coverageVerified = coverage.complete;
    answer.coverageCandidates = coverage.candidates.length;
    const defaultFilter = answer.leadActive ? "lead_active" : (answer.leadOpen ? "lead_all" : "all");
    const filters = [
      ["lead_active", answer.leadActive, "researchPortfolioFilterLeadMainline"],
      ["lead_all", answer.leadOpen, "researchPortfolioFilterLeadAll"],
      ["support_active", answer.supportActive, "researchPortfolioFilterSupportActive"],
      ["support_all", answer.supportOpen, "researchPortfolioFilterSupport"],
      ["waiting", answer.waiting, "researchPortfolioFilterWaiting"],
      ["queued", answer.queued, "researchPortfolioFilterQueued"],
      ["conditional", counts.conditional, "researchPortfolioFilterConditional"],
      ["paused", answer.paused, "researchPortfolioFilterPaused"],
      ["review", answer.needsReview, "researchPortfolioFilterReview"],
      ["unclassified", answer.unclassified, "researchPortfolioFilterUnclassified"],
      ["all", items.length, "researchPortfolioFilterAll"],
    ].map(([id, count, label]) => ({ id, count, label: text(label) }));
    return {
      available: Boolean(portfolio?.available && ["private_authority", "public_demo", "personal_vault"].includes(presentationMode) && items.length),
      answer,
      actionItems,
      boundary: String(portfolio?.boundary || ""),
      coverage,
      counts,
      phaseCounts,
      backgroundCount: items.filter((item) => item.backgroundPhase && item.lifecycleState !== "completed").length,
      defaultFilter,
      filters,
      items,
      path: String(portfolio?.path || "06_active_context/research-portfolio.md"),
      presentationMode,
      publicDemo: presentationMode === "public_demo",
      referenceDate,
      integrity: portfolio?.integrity && typeof portfolio.integrity === "object" ? portfolio.integrity : { status: coverage.complete ? "pass" : "needs_attention", issues: [] },
      managementCounts,
      managementZoneCounts,
      scheduleCounts,
      attentionCounts,
      selectedItemId: items.find((item) => item.responsibility === "lead" && item.state === "mainline")?.id || items[0]?.id || "",
      sensitivity,
      updated: String(portfolio?.updated || ""),
    };
  }

  global.ResearchOSResearchPortfolioModel = Object.freeze({
    build,
    liveAttention,
    liveFreshness,
    managementBucketForItem,
    managementZoneForBucket,
    managementZoneForItem,
  });
})(window);
