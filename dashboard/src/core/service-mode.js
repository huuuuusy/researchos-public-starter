/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「service mode」；供 app、service、view 复用。
 * English: Browser-side core primitive for service mode in the ResearchOS dashboard; shared by app, services, and views.
 */

(function attachResearchOSServiceMode(global) {
  // interactions.js loads after this file, so its reduced-motion-aware scroll is resolved when the banner scrolls.
  function scrollIntoView(target, options = {}) {
    const interactionScroll = global.ResearchOSInteractions?.scrollIntoView;
    return interactionScroll ? interactionScroll(target, options) : target?.scrollIntoView?.(options);
  }
  const DEFAULT_SERVER_URL = global.ResearchOSEditionProfile?.serverUrl;

  function isServerMode(locationLike = global.location) {
    const protocol = locationLike?.protocol || "";
    return protocol === "http:" || protocol === "https:";
  }

  function serverUrl(config = {}, fallbackUrl = DEFAULT_SERVER_URL) {
    return config?.server_url || fallbackUrl;
  }

  function updateServiceModeBanner(options = {}) {
    const {
      banner = global.document?.getElementById("serviceModeBanner"),
      config = {},
      defaultServerUrl = DEFAULT_SERVER_URL,
      documentElement = global.document?.documentElement,
      locationLike = global.location,
    } = options;
    const fileMode = !isServerMode(locationLike);
    if (banner) {
      banner.hidden = !fileMode;
      banner.querySelector("a")?.setAttribute("href", serverUrl(config, defaultServerUrl));
    }
    documentElement?.classList.toggle("file-preview-mode", fileMode);
    return fileMode;
  }

  function blockedResult(options = {}) {
    const { label = "local service", message = "" } = options;
    return {
      ok: false,
      seconds: "",
      steps: [
        {
          label,
          ok: false,
          optional: false,
          output: message,
        },
      ],
    };
  }

  function researchScoutBlockedResult(message = "") {
    return {
      ok: false,
      message,
      warnings: [message],
      results: [],
      queries: [],
      search_links: [],
    };
  }

  function blockedHintHtml(options = {}) {
    const {
      body = "",
      defaultServerUrl = DEFAULT_SERVER_URL,
      escapeHtml = global.ResearchOSUiCore?.escapeHtml,
      linkLabel = "",
      title = "",
    } = options;
    return `<div class="service-mode-banner error-service-hint">
      <span>${escapeHtml(title)}</span>
      <p>${escapeHtml(body)}</p>
      <a href="${escapeHtml(defaultServerUrl)}" data-action-kind="navigation">${escapeHtml(linkLabel)}</a>
    </div>`;
  }

  function scrollServiceModeBanner(documentLike = global.document) {
    scrollIntoView(documentLike?.getElementById("serviceModeBanner"), { block: "start", behavior: "smooth" });
  }

  global.ResearchOSServiceMode = Object.freeze({
    DEFAULT_SERVER_URL,
    blockedHintHtml,
    blockedResult,
    isServerMode,
    researchScoutBlockedResult,
    scrollServiceModeBanner,
    serverUrl,
    updateServiceModeBanner,
  });
  global.document?.documentElement?.setAttribute("data-researchos-service-mode", "ready");
})(window);
