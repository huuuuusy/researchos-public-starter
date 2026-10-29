/* ResearchOS maintenance header.
 * 中文：本地 dashboard 状态修改请求的同源会话认证 owner。
 * English: Same-origin session-authentication owner for state-changing dashboard requests.
 */

(function attachResearchOSRequestAuth(global) {
  const originalFetch = typeof global.fetch === "function" ? global.fetch.bind(global) : null;
  let sessionPromise = null;

  async function loadSession(forceRefresh = false) {
    if (!originalFetch || global.location?.protocol === "file:") return null;
    if (forceRefresh) sessionPromise = null;
    if (!sessionPromise) {
      sessionPromise = originalFetch("/session-config", { cache: "no-store", credentials: "same-origin" })
        .then((response) => (response.ok ? response.json() : null))
        .catch(() => null);
    }
    const session = await sessionPromise;
    if (!session) sessionPromise = null;
    return session;
  }

  function requestMethod(input, init = {}) {
    return String(init?.method || input?.method || "GET").toUpperCase();
  }

  function requestUrl(input) {
    try {
      return new URL(typeof input === "string" ? input : input?.url || String(input), global.location?.href);
    } catch {
      return null;
    }
  }

  function isSameOrigin(input) {
    const url = requestUrl(input);
    return Boolean(url && url.origin === global.location?.origin);
  }

  async function sendWithSession(input, init, session) {
    const isRequest = typeof Request === "function" && input instanceof Request;
    const requestInput = isRequest ? input.clone() : input;
    const headers = new Headers(isRequest ? input.headers : undefined);
    new Headers(init.headers || {}).forEach((value, key) => headers.set(key, value));
    if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    headers.set(session.request_header || "X-ResearchOS-Session", session.request_token);
    const nextInit = {
      ...init,
      credentials: "same-origin",
      headers,
    };
    if (!isRequest && init.body === undefined) nextInit.body = "{}";
    return originalFetch(requestInput, nextInit);
  }

  async function authenticatedFetch(input, init = {}) {
    if (!originalFetch) throw new Error("Fetch is unavailable");
    if (!["POST", "PUT", "PATCH", "DELETE"].includes(requestMethod(input, init))) {
      return originalFetch(input, init);
    }
    if (!isSameOrigin(input)) return originalFetch(input, init);
    const session = await loadSession();
    if (!session?.request_token) {
      throw new Error("ResearchOS local session is unavailable");
    }
    const response = await sendWithSession(input, init, session);
    if (response.status !== 403) return response;
    const refreshed = await loadSession(true);
    if (!refreshed?.request_token || refreshed.request_token === session.request_token) return response;
    return sendWithSession(input, init, refreshed);
  }

  function resolveFetcher(candidate) {
    if (typeof candidate === "function") return candidate;
    return typeof global.fetch === "function" ? global.fetch.bind(global) : null;
  }

  if (originalFetch) global.fetch = authenticatedFetch;
  global.ResearchOSRequestAuth = Object.freeze({ resolveFetcher });
})(window);
