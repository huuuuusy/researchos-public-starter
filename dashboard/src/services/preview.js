/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「preview」；承接可复用逻辑，避免 app.js 重新变成大杂烩。
 * English: Frontend service for preview in the ResearchOS dashboard; keeps reusable logic out of app.js so it does not become a catch-all again.
 */

(function attachResearchOSPreviewService(global) {
  const DEFAULT_HISTORY_LIMIT = 40;
  const ROOT_PREFIXES = Object.freeze([
    "00_identity/",
    "01_knowledge/",
    "02_decisions/",
    "03_cognition/",
    "04_people/",
    "05_workflows/",
    "06_active_context/",
    "07_archive/",
    "08_public/",
    "08_exports/",
    "09_templates/",
    "distilled/",
  ]);

  function rendererOptions(options = {}) {
    return {
      resolveDocument: typeof options.resolveDocument === "function" ? options.resolveDocument : () => null,
    };
  }

  function normalizePreviewPath(path) {
    return String(path || "")
      .replace(/\\/g, "/")
      .replace(/^\.?\//, "");
  }

  function repositoryRelativePath(path) {
    let raw = String(path || "").trim().replace(/\\/g, "/");
    if (/^file:\/\//i.test(raw)) raw = raw.replace(/^file:\/\/(?:localhost)?/i, "");
    try {
      raw = decodeURIComponent(raw);
    } catch {
      // Keep a malformed percent-encoded path visible instead of crashing preview rendering.
    }
    if (!raw.startsWith("/")) return normalizePreviewPath(raw);
    for (const prefix of ROOT_PREFIXES) {
      const marker = `/${prefix}`;
      const markerIndex = raw.indexOf(marker);
      if (markerIndex >= 0) return normalizePreviewPath(raw.slice(markerIndex + 1));
    }
    return "";
  }

  function resolveRelativeMdPath(basePath = "", targetPath = "") {
    const raw = String(targetPath || "").trim();
    if (!raw || raw.startsWith("/") || /^https?:\/\//i.test(raw)) return "";
    const baseParts = String(basePath || "").split("/");
    baseParts.pop();
    const isRootRelative = ROOT_PREFIXES.some((prefix) => raw.startsWith(prefix));
    const parts = isRootRelative ? raw.split("/") : [...baseParts, ...raw.split("/")];
    const stack = [];
    for (const part of parts) {
      if (!part || part === ".") continue;
      if (part === "..") {
        stack.pop();
        continue;
      }
      stack.push(part);
    }
    const normalized = stack.join("/");
    if (!normalized.toLowerCase().endsWith(".md") || normalized.split("/").includes("..")) return "";
    return normalized;
  }

  function isPdfPreviewPath(path) {
    const rawPath = String(path || "").trim().replace(/\\/g, "/");
    if (!rawPath || rawPath.startsWith("/") || /^[A-Za-z][A-Za-z0-9+.-]*:/i.test(rawPath)) return false;
    const normalizedPath = normalizePreviewPath(path);
    return Boolean(
      normalizedPath &&
      normalizedPath.toLowerCase().endsWith(".pdf") &&
      !normalizedPath.startsWith("/") &&
      !normalizedPath.split("/").includes("..")
    );
  }

  function pdfPreviewLabel(path, fallback = "PDF Preview") {
    const parts = normalizePreviewPath(path).split("/");
    return parts[parts.length - 1] || fallback;
  }

  function normalizePreviewHistory(records = [], limit = DEFAULT_HISTORY_LIMIT) {
    return (Array.isArray(records) ? records : [])
      .filter((item) => item && typeof item === "object" && normalizePreviewPath(item.path))
      .map((item) => ({
        path: normalizePreviewPath(item.path),
        anchor: String(item.anchor || ""),
      }))
      .slice(-limit);
  }

  function loadPreviewHistory({
    storageKey = "researchos-preview-history",
    storage = global.localStorage,
    limit = DEFAULT_HISTORY_LIMIT,
  } = {}) {
    try {
      const parsed = JSON.parse(storage.getItem(storageKey) || "[]");
      return normalizePreviewHistory(parsed, limit);
    } catch {
      return [];
    }
  }

  function savePreviewHistory({
    history = [],
    index = -1,
    historyKey = "researchos-preview-history",
    indexKey = "researchos-preview-history-index",
    storage = global.localStorage,
    limit = DEFAULT_HISTORY_LIMIT,
  } = {}) {
    const normalizedHistory = normalizePreviewHistory(history, limit);
    storage.setItem(historyKey, JSON.stringify(normalizedHistory));
    storage.setItem(indexKey, String(index));
  }

  function pushPreviewHistory({
    history = [],
    index = -1,
    path = "",
    anchor = "",
    limit = DEFAULT_HISTORY_LIMIT,
  } = {}) {
    const normalizedPath = normalizePreviewPath(path);
    const normalizedHistory = normalizePreviewHistory(history, limit);
    if (!normalizedPath) return { history: normalizedHistory, index };
    const currentIndex = Number.isFinite(Number(index)) ? Math.trunc(Number(index)) : -1;
    const boundedIndex = Math.min(Math.max(currentIndex, -1), normalizedHistory.length - 1);
    const entry = { path: normalizedPath, anchor: String(anchor || "") };
    const current = normalizedHistory[boundedIndex];
    if (current?.path === entry.path && (current?.anchor || "") === entry.anchor) {
      return { history: normalizedHistory, index: boundedIndex };
    }
    let nextHistory = normalizedHistory.slice(0, Math.max(0, boundedIndex + 1));
    nextHistory.push(entry);
    if (nextHistory.length > limit) nextHistory = nextHistory.slice(-limit);
    return { history: nextHistory, index: nextHistory.length - 1 };
  }

  function canPreviewBack(history = [], index = -1) {
    return Number(index) > 0 && normalizePreviewHistory(history).length > 1;
  }

  function canPreviewForward(history = [], index = -1) {
    const normalizedHistory = normalizePreviewHistory(history);
    const currentIndex = Number(index);
    return currentIndex >= 0 && currentIndex < normalizedHistory.length - 1;
  }

  function navigatePreviewHistory(history = [], index = -1, direction = 0) {
    const normalizedHistory = normalizePreviewHistory(history);
    const nextIndex = Number(index) + Number(direction || 0);
    if (nextIndex < 0 || nextIndex >= normalizedHistory.length) return null;
    return { entry: normalizedHistory[nextIndex], index: nextIndex, history: normalizedHistory };
  }

  function closePreviewHistoryEntry({
    history = [],
    index = -1,
    path = "",
    anchor = "",
  } = {}) {
    const normalizedHistory = normalizePreviewHistory(history);
    const normalizedPath = normalizePreviewPath(path);
    if (!normalizedHistory.length || !normalizedPath) {
      return { closedCurrent: false, entry: null, history: normalizedHistory, index: Number(index) || -1 };
    }
    const currentIndex = Math.min(Math.max(Math.trunc(Number(index) || 0), 0), normalizedHistory.length - 1);
    const isTargetEntry = (entry) => (
      entry.path === normalizedPath &&
      (!anchor || (entry.anchor || "") === String(anchor || ""))
    );
    const targetIndex = normalizedHistory.findIndex(isTargetEntry);
    if (targetIndex < 0) {
      return { closedCurrent: false, entry: normalizedHistory[currentIndex] || null, history: normalizedHistory, index: currentIndex };
    }
    const current = normalizedHistory[currentIndex] || null;
    const closedCurrent = Boolean(current && isTargetEntry(current));
    const removedBeforeCurrent = normalizedHistory
      .slice(0, currentIndex)
      .filter(isTargetEntry)
      .length;
    const nextHistory = normalizedHistory.filter((entry) => !isTargetEntry(entry));
    if (!nextHistory.length) {
      return { closedCurrent, entry: null, history: [], index: -1 };
    }
    const nextIndex = closedCurrent
      ? Math.min(Math.max(0, currentIndex - removedBeforeCurrent), nextHistory.length - 1)
      : Math.min(Math.max(0, currentIndex - removedBeforeCurrent), nextHistory.length - 1);
    return {
      closedCurrent,
      entry: nextHistory[nextIndex] || null,
      history: nextHistory,
      index: nextIndex,
    };
  }

  function resolvePreviewLink(basePath, href, options = {}) {
    const { resolveDocument } = rendererOptions(options);
    const rawHref = String(href || "").trim();
    if (!rawHref) return null;
    if (/^(https?:|mailto:|tel:)/i.test(rawHref)) {
      return { external: true, href: rawHref };
    }
    if (rawHref.startsWith("#")) {
      return { path: basePath, anchor: rawHref.slice(1) };
    }
    const [rawPath, rawAnchor = ""] = rawHref.split("#");
    if (!rawPath) return null;
    const repositoryPath = repositoryRelativePath(rawPath);
    if (rawPath.startsWith("/") && !repositoryPath) return null;
    const baseParts = normalizePreviewPath(basePath).split("/");
    baseParts.pop();
    const absoluteLocalPath = rawPath.startsWith("/") || /^file:\/\//i.test(rawPath);
    const parts = absoluteLocalPath
      ? repositoryPath.split("/")
      : baseParts.concat(repositoryPath.split("/"));
    const normalized = [];
    parts.forEach((part) => {
      if (!part || part === ".") return;
      if (part === "..") {
        normalized.pop();
        return;
      }
      normalized.push(part);
    });
    const path = normalized.join("/");
    if (path.startsWith("corpus/")) return null;
    if (isPdfPreviewPath(path)) return { pdf: true, path, anchor: rawAnchor };
    return resolveDocument(path) ? { path, anchor: rawAnchor } : null;
  }

  global.ResearchOSPreviewService = Object.freeze({
    DEFAULT_HISTORY_LIMIT,
    normalizePreviewPath,
    repositoryRelativePath,
    resolveRelativeMdPath,
    isPdfPreviewPath,
    pdfPreviewLabel,
    normalizePreviewHistory,
    loadPreviewHistory,
    savePreviewHistory,
    pushPreviewHistory,
    canPreviewBack,
    canPreviewForward,
    closePreviewHistoryEntry,
    navigatePreviewHistory,
    resolvePreviewLink,
  });
})(typeof window !== "undefined" ? window : globalThis);
