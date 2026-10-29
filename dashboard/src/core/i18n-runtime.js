/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「i18n runtime」；供 app、service、view 复用。
 * English: Browser-side core primitive for i18n runtime in the ResearchOS dashboard; shared by app, services, and views.
 */

(function () {
  function translate(catalog, language, key, fallbackLanguage = "en") {
    return catalog?.[language]?.[key] || catalog?.[fallbackLanguage]?.[key] || key;
  }

  function resolveLanguage(catalog, requestedLanguage, configuredLanguage = "en", fallbackLanguage = "en") {
    if (catalog?.[requestedLanguage]) return requestedLanguage;
    if (catalog?.[configuredLanguage]) return configuredLanguage;
    if (catalog?.[fallbackLanguage]) return fallbackLanguage;
    return Object.keys(catalog || {})[0] || fallbackLanguage;
  }

  function applyTranslations({ language, root = document, translateText, onAfterApply } = {}) {
    document.documentElement.lang = language;
    root.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = translateText(node.dataset.i18n);
    });
    root.querySelectorAll("[data-i18n-aria-label]").forEach((node) => {
      node.setAttribute("aria-label", translateText(node.dataset.i18nAriaLabel));
    });
    root.querySelectorAll("[data-i18n-title]").forEach((node) => {
      node.setAttribute("title", translateText(node.dataset.i18nTitle));
    });
    if (typeof onAfterApply === "function") onAfterApply();
  }

  function setupLanguageSelect({ select, languages = ["zh-CN", "en"], selectedLanguage, onChange } = {}) {
    if (!select) return;
    select.innerHTML = "";
    languages.forEach((language) => {
      const option = document.createElement("option");
      option.value = language;
      option.textContent = ({ "zh-CN": "简体中文", en: "English" })[language] || language;
      option.selected = language === selectedLanguage;
      select.appendChild(option);
    });
    select.onchange = () => {
      if (typeof onChange === "function") onChange(select.value);
    };
  }

  window.ResearchOSI18NRuntime = {
    applyTranslations,
    resolveLanguage,
    setupLanguageSelect,
    translate,
  };
})();
