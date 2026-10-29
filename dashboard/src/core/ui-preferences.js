/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「UI preferences」；供 app、service、view 复用。
 * English: Browser-side core primitive for UI preferences in the ResearchOS dashboard; shared by app, services, and views.
 */

(function attachResearchOSUiPreferences(global) {
  const storageKeys = Object.freeze({
    dashboardLanguage: "researchos-dashboard-language",
    dashboardTask: "researchos-dashboard-task",
    dashboardTheme: "researchos-dashboard-theme",
    uiVersion: "researchos-dashboard-ui-version",
    unfinishedCurrent: "researchos-unfinished-current",
  });

  const defaults = Object.freeze({
    dashboardLanguage: global.ResearchOSEditionProfile?.defaultLanguage,
    dashboardTheme: "blue",
  });

  const validChoices = Object.freeze({
    dashboardLanguage: Object.freeze(["zh-CN", "en"]),
    dashboardTheme: Object.freeze(["blue", "green", "violet", "slate", "warm"]),
  });

  function choiceOrDefault(value, choices, fallback) {
    const text = String(value || "").trim();
    return choices.includes(text) ? text : fallback;
  }

  function read(storage = global.localStorage) {
    return {
      language: choiceOrDefault(storage.getItem(storageKeys.dashboardLanguage), validChoices.dashboardLanguage, defaults.dashboardLanguage),
      selectedUnfinishedKey: storage.getItem(storageKeys.unfinishedCurrent) || "",
      theme: choiceOrDefault(storage.getItem(storageKeys.dashboardTheme), validChoices.dashboardTheme, defaults.dashboardTheme),
    };
  }

  function hasLanguagePreference(storage = global.localStorage) {
    return Boolean(storage.getItem(storageKeys.dashboardLanguage));
  }

  function needsUiVersionReset(version = "", storage = global.localStorage) {
    return storage.getItem(storageKeys.uiVersion) !== String(version || "");
  }

  function writeString(keyName, value = "", storage = global.localStorage) {
    const text = String(value || "");
    storage.setItem(storageKeys[keyName], text);
    return text;
  }

  function remove(keyName, storage = global.localStorage) {
    storage.removeItem(storageKeys[keyName]);
  }

  global.ResearchOSUiPreferences = Object.freeze({
    defaults,
    validChoices,
    storageKeys,
    hasLanguagePreference,
    needsUiVersionReset,
    read,
    removeSelectedTask: (storage) => remove("dashboardTask", storage),
    removeUnfinishedCurrent: (storage) => remove("unfinishedCurrent", storage),
    writeLanguage: (value, storage) => writeString("dashboardLanguage", choiceOrDefault(value, validChoices.dashboardLanguage, defaults.dashboardLanguage), storage),
    writeTheme: (value, storage) => writeString("dashboardTheme", choiceOrDefault(value, validChoices.dashboardTheme, defaults.dashboardTheme), storage),
    writeUiVersion: (value, storage) => writeString("uiVersion", value, storage),
  });
})(window);
