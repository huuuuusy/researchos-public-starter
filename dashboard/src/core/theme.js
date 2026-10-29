/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「theme」；供 app、service、view 复用。
 * English: Browser-side core primitive for theme in the ResearchOS dashboard; shared by app, services, and views.
 */

(function () {
  const THEMES = [
    { id: "blue", swatch: "#1f6fd1" },
    { id: "green", swatch: "#24785c" },
    { id: "violet", swatch: "#6857d9" },
    { id: "slate", swatch: "#3f6fa8" },
    { id: "warm", swatch: "#b55343" },
  ];

  function resolveTheme(themeId) {
    return THEMES.some((item) => item.id === themeId) ? themeId : "blue";
  }

  function applyTheme(themeId, root = document.documentElement) {
    const selectedTheme = resolveTheme(themeId);
    root.dataset.theme = selectedTheme;
    return selectedTheme;
  }

  function setupThemePicker({ root, selectedTheme, translate, onSelect } = {}) {
    if (!root) return;
    root.innerHTML = "";
    root.title = translate("controls.theme");
    root.dataset.label = translate("controls.theme");
    THEMES.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.actionKind = "direct";
      button.className = item.id === selectedTheme ? "selected" : "";
      button.style.setProperty("--swatch", item.swatch);
      button.setAttribute("aria-label", `${translate("controls.theme")}: ${translate(`themes.${item.id}`)}`);
      button.title = translate(`themes.${item.id}`);
      button.addEventListener("click", () => {
        if (typeof onSelect === "function") onSelect(item.id);
      });
      root.appendChild(button);
    });
  }

  window.ResearchOSTheme = {
    applyTheme,
    resolveTheme,
    setupThemePicker,
    themes: THEMES,
  };
})();
