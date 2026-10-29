/* ResearchOS maintenance header.
 * 中文：版本运行配置；从 index.html 根元素的 data-* 属性读取客户端配置、默认界面语言和本地服务地址，缺失时一律按公开版取值。
 *   它只决定这三项展示与连接默认值；能否写入仍只看 dashboardData.runtime_mode。必须在 head 中最先加载。
 * English: Edition runtime profile; reads the client profile, default interface language and local server URL from data-*
 *   attributes on index.html's root element, falling back to the public_starter values for any missing attribute.
 *   It sets only these presentation and connection defaults; mutation gating stays with dashboardData.runtime_mode.
 *   Load it first in <head>.
 */

(function attachResearchOSEditionProfile(global) {
  "use strict";

  const PUBLIC_STARTER = Object.freeze({
    clientProfileId: "public_explanatory_v1",
    defaultLanguage: "en",
    serverUrl: "http://127.0.0.1:8880/",
  });

  function editionProfile(root = global.document?.documentElement) {
    const value = (name, fallback) => String(root?.dataset?.[name] || "").trim() || fallback;
    const language = value("defaultLanguage", PUBLIC_STARTER.defaultLanguage);
    return Object.freeze({
      clientProfileId: value("clientProfile", PUBLIC_STARTER.clientProfileId),
      defaultLanguage: ["en", "zh-CN"].includes(language) ? language : PUBLIC_STARTER.defaultLanguage,
      serverUrl: value("serverUrl", PUBLIC_STARTER.serverUrl),
    });
  }

  global.ResearchOSEditionProfile = editionProfile();
})(window);
