/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 渲染计划服务；集中声明 state 准备、section 顺序、生命周期顺序和数据切片规则。
 * English: Dashboard render-plan service for ResearchOS; centralizes state preparation, section order, lifecycle order, and data-slice rules.
 */

(function attachResearchOSDashboardRenderPlan(global) {
  const DASHBOARD_RENDER_SECTIONS = Object.freeze([
    Object.freeze({ id: "homeCommandCenter", role: "today command center" }),
    Object.freeze({ id: "assetOverview", role: "declarative Library plugin slots" }),
    Object.freeze({ id: "pluginUtilitySlots", role: "declarative Utility plugin slots" }),
    Object.freeze({ id: "unifiedInbox", role: "unified inbox" }),
  ]);

  const DASHBOARD_BEFORE_RENDER_STEPS = Object.freeze([
    Object.freeze({ id: "applyTheme", role: "apply selected theme" }),
    Object.freeze({ id: "applyTranslations", role: "apply localized static text" }),
    Object.freeze({ id: "setupThemePicker", role: "render theme picker controls" }),
    Object.freeze({ id: "updateHeader", role: "update dashboard header text" }),
  ]);

  const DASHBOARD_AFTER_RENDER_STEPS = Object.freeze([
    Object.freeze({ id: "renderMarkdownPreview", role: "refresh markdown preview surface" }),
    Object.freeze({ id: "bindWorkspaceTabs", role: "bind workspace switcher" }),
    Object.freeze({ id: "bindInteractiveSurfaces", role: "bind interactive surface affordances" }),
    Object.freeze({ id: "bindButtonTooltips", role: "bind button tooltips" }),
    Object.freeze({ id: "ensureSelectedPreviewLoaded", role: "restore selected preview" }),
  ]);

  const DASHBOARD_RENDER_CALLBACK_NAMES = Object.freeze({
    assetOverview: "renderPluginLibrarySlots",
    homeCommandCenter: "renderHomeCommandCenter",
    pluginUtilitySlots: "renderPluginSlots",
    unifiedInbox: "renderUnifiedInbox",
  });

  const DASHBOARD_BEFORE_RENDER_CALLBACK_NAMES = Object.freeze({
    applyTheme: "applyTheme",
    applyTranslations: "applyTranslations",
    setupThemePicker: "setupThemePicker",
    updateHeader: "updateHeader",
  });

  const DASHBOARD_AFTER_RENDER_CALLBACK_NAMES = Object.freeze({
    bindButtonTooltips: "bindDashboardButtonTooltips",
    bindInteractiveSurfaces: "bindDashboardInteractiveSurfaces",
    bindWorkspaceTabs: "bindWorkspaceTabs",
    ensureSelectedPreviewLoaded: "ensureSelectedPreviewLoaded",
    renderMarkdownPreview: "renderMarkdownPreview",
  });

  function sourceOverview(data = {}) {
    return data?.source_overview || {};
  }

  function isPublicStarterRuntime(data = {}) {
    return data?.runtime_mode === "public_starter" || Boolean(data?.public_starter);
  }

  function isPublicStarterDemoItem(item = {}) {
    const path = String(item.path || item.id || item.summary_path || "").trim();
    if (path.startsWith("08_exports/public_starter/")) return true;
    return String(item.case_mode || item.stage_label || "").toLowerCase().includes("public starter demo");
  }

  function withoutPublicStarterDemoItems(items = []) {
    return (Array.isArray(items) ? items : []).filter((item) => !isPublicStarterDemoItem(item));
  }

  function publicStarterGraphForDisplay(graph = {}, showDemo = true) {
    if (showDemo) return graph;
    return {
      ...graph,
      papers: withoutPublicStarterDemoItems(graph.papers),
      talks: withoutPublicStarterDemoItems(graph.talks),
      people: withoutPublicStarterDemoItems(graph.people),
      projects: withoutPublicStarterDemoItems(graph.projects),
      asset_relation_matrix: withoutPublicStarterDemoItems(graph.asset_relation_matrix),
      asset_understanding_quality: {
        ...(graph.asset_understanding_quality || {}),
        items: withoutPublicStarterDemoItems(graph.asset_understanding_quality?.items),
      },
      cross_project_mounts: {
        ...(graph.cross_project_mounts || {}),
        mounts: withoutPublicStarterDemoItems(graph.cross_project_mounts?.mounts),
      },
    };
  }

  function publicStarterOverviewForDisplay(overview = {}, graph = {}, options = {}) {
    if (!options.publicStarter || options.publicDemoVisible) return overview;
    const paperCount = (graph.papers || []).length;
    const talkCount = (graph.talks || []).length;
    const peopleCount = (graph.people || []).length;
    const projectCount = (graph.projects || []).length;
    return {
      ...overview,
      materials: {
        ...(overview.materials || {}),
        reading_notes: paperCount,
        analysis_state_counts: { M1_registered: 0, M2_refined_read: 0, M3_cross_project_deepening: 0 },
      },
      people: { ...(overview.people || {}), registered_collaborators: peopleCount, active_deep_collaborators: 0 },
      research_map: {
        ...(overview.research_map || {}),
        active_projects: projectCount,
        project_pages: projectCount,
        mainlines: [],
        mainline_count: 0,
      },
      public_starter_display: {
        demo_visible: false,
        hidden_demo_hint: "Public starter examples are hidden in this browser view.",
        paper_count: paperCount,
        talk_count: talkCount,
      },
    };
  }

  function languageFreeze(data = {}) {
    return data?.language_freeze || data?.config?.language_freeze || data?.public_starter?.case_materials?.language_freeze || {};
  }

  function activeTemplateLanguage(data = {}) {
    return languageFreeze(data).active_language
      || data?.config?.content_language
      || data?.public_starter?.case_materials?.content_language
      || data?.config?.language
      || "en";
  }

  function resolveRenderLanguage(data = {}, context = {}) {
    const defaultLanguage = data?.config?.language || "en";
    if (typeof context.resolveLanguage === "function") {
      return context.resolveLanguage(defaultLanguage);
    }
    return context.currentLang || defaultLanguage;
  }

  function headerText(data = {}, lang = "", context = {}) {
    const translateFor = context.translateFor || ((key) => key);
    return {
      generatedAt: `${translateFor("status.generated", lang)} ${data?.generated_at || ""}`,
      subtitle: `${translateFor("app.subtitle", lang)} · ${data?.config?.project_name || "ResearchOS"}`,
    };
  }

  function prepareRenderState(data = {}, context = {}) {
    const lang = resolveRenderLanguage(data, context);
    return {
      header: headerText(data, lang, context),
      lang,
      templateLanguage: activeTemplateLanguage(data),
    };
  }

  function callbackRegistry(callbackNames = {}, source = {}) {
    return Object.freeze(
      Object.fromEntries(
        Object.entries(callbackNames)
          .map(([planId, sourceName]) => [planId, source[sourceName]])
          .filter(([, callback]) => typeof callback === "function")
      )
    );
  }

  function rendererCallbacks(source = {}) {
    return callbackRegistry(DASHBOARD_RENDER_CALLBACK_NAMES, source);
  }

  function beforeRenderCallbacks(source = {}) {
    return callbackRegistry(DASHBOARD_BEFORE_RENDER_CALLBACK_NAMES, source);
  }

  function afterRenderCallbacks(source = {}) {
    return callbackRegistry(DASHBOARD_AFTER_RENDER_CALLBACK_NAMES, source);
  }

  function renderSectionArgs(sectionId = "", data = {}, context = {}) {
    switch (sectionId) {
      case "homeCommandCenter":
        return [data?.home_command_center || {}];
      case "assetOverview":
        return [data];
      case "pluginUtilitySlots":
        return [data];
      default:
        return [];
    }
  }

  function runRenderPlan(data = {}, context = {}) {
    const renderers = context.renderers || {};
    DASHBOARD_RENDER_SECTIONS.forEach((section) => {
      const render = renderers[section.id];
      if (typeof render !== "function") return;
      render(...renderSectionArgs(section.id, data, context));
    });
  }

  function runBeforeRenderPlan(context = {}) {
    const callbacks = context.callbacks || {};
    DASHBOARD_BEFORE_RENDER_STEPS.forEach((step) => {
      const callback = callbacks[step.id];
      if (typeof callback === "function") callback();
    });
  }

  function runAfterRenderPlan(context = {}) {
    const callbacks = context.callbacks || {};
    DASHBOARD_AFTER_RENDER_STEPS.forEach((step) => {
      const callback = callbacks[step.id];
      if (typeof callback === "function") callback();
    });
  }

  global.ResearchOSDashboardRenderPlan = Object.freeze({
    afterRenderSteps: DASHBOARD_AFTER_RENDER_STEPS,
    activeTemplateLanguage,
    afterRenderCallbackNames: DASHBOARD_AFTER_RENDER_CALLBACK_NAMES,
    afterRenderCallbacks,
    beforeRenderCallbackNames: DASHBOARD_BEFORE_RENDER_CALLBACK_NAMES,
    beforeRenderCallbacks,
    beforeRenderSteps: DASHBOARD_BEFORE_RENDER_STEPS,
    callbackRegistry,
    headerText,
    isPublicStarterRuntime,
    prepareRenderState,
    publicStarterGraphForDisplay,
    publicStarterOverviewForDisplay,
    rendererCallbackNames: DASHBOARD_RENDER_CALLBACK_NAMES,
    rendererCallbacks,
    resolveRenderLanguage,
    runAfterRenderPlan,
    runBeforeRenderPlan,
    renderSectionArgs,
    runRenderPlan,
    sections: DASHBOARD_RENDER_SECTIONS,
    sourceOverview,
  });
})(window);
