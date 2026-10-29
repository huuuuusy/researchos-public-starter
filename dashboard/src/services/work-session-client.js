/* ResearchOS maintenance header.
 * 中文：工作会话本地 HTTP client；负责用户控制的会话材料上传，不拥有长期记忆。
 * English: Local HTTP client for work sessions; uploads user-controlled session sources without owning durable memory.
 */

(function attachResearchOSWorkSessionClient(global) {
  function fileSuffix(name = "") {
    const normalized = String(name || "").toLowerCase();
    const dot = normalized.lastIndexOf(".");
    return dot >= 0 ? normalized.slice(dot) : "";
  }

  // The HTTP outcome wins: a server body cannot override ok or status with its own fields.
  async function readResult(response) {
    const result = await response.json().catch(() => ({}));
    return { ...result, ok: Boolean(response.ok && result?.ok), status: response.status };
  }

  async function uploadSourceFile(file = null, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (!file) {
      return { ok: false, message: "file unavailable" };
    }
    if (typeof fetcher !== "function") return { ok: false, message: "fetch unavailable" };
    try {
      const response = await fetcher("/work-session-upload", {
        method: "POST",
        headers: {
          "Content-Type": "application/octet-stream",
          "X-ResearchOS-Filename": encodeURIComponent(String(file.name || "source")),
        },
        body: file,
        cache: "no-store",
      });
      return await readResult(response);
    } catch (error) {
      return { ok: false, message: error?.message || "upload failed" };
    }
  }

  async function copyResult(result = null, options = {}) {
    const answer = String(result?.answer || "").trim();
    const clipboard = options.clipboard || global.navigator?.clipboard;
    if (!answer || typeof clipboard?.writeText !== "function") return false;
    try {
      await clipboard.writeText(answer);
      if (options.statusTarget) options.statusTarget.textContent = options.successMessage || "";
      return true;
    } catch {
      return false;
    }
  }

  async function completePortfolioItem(binding = {}, options = {}, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    const itemId = String(binding?.itemId || "").trim();
    if (!itemId || typeof fetcher !== "function") return { ok: false, message: "portfolio binding unavailable" };
    try {
      const response = await fetcher("/portfolio-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          completion_note: String(options.completionNote || "").trim().slice(0, 500),
          item_id: itemId,
        }),
        cache: "no-store",
      });
      return await readResult(response);
    } catch (error) {
      return { ok: false, message: error?.message || "portfolio completion failed" };
    }
  }

  async function setPortfolioState(item = {}, target = "", options = {}, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    if (!item.id || typeof fetcher !== "function") return { ok: false, message: "portfolio item unavailable" };
    try {
      const response = await fetcher("/portfolio-state", {
        method: "POST", headers: { "Content-Type": "application/json" }, cache: "no-store",
        body: JSON.stringify({ item_id: item.id, state: target, expected_state: item.state, confirmed: true, reopen: options.reopen }),
      });
      return await readResult(response);
    } catch (error) { return { ok: false, message: error.message }; }
  }

  async function applyAttentionAction(item = {}, action = {}, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    const providerId = String(item?.providerId || item?.provider_id || "").trim();
    const itemId = String(item?.id || item?.itemId || item?.item_id || "").trim();
    if (!providerId || !itemId || typeof fetcher !== "function") return { ok: false, message: "attention item unavailable" };
    try {
      const body = {
        action: String(action?.action || "").trim(),
        attention_date: String(action?.attentionDate || "").trim(),
        item_id: itemId,
        next_step: String(item?.nextStep || item?.next_step || "").trim(),
        provider_id: providerId,
        review_date: String(action?.reviewDate || "").trim(),
        today_order: Number(action?.todayOrder || 0),
      };
      if (body.action === "complete_step") {
        body.next_step_hash = String(item?.nextStepHash || item?.next_step_hash || "").trim();
      }
      const response = await fetcher("/attention-action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        cache: "no-store",
      });
      return await readResult(response);
    } catch (error) {
      return { ok: false, message: error?.message || "attention action failed" };
    }
  }

  async function undoMutation(undo = {}, deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    const token = String(undo?.token || "").trim();
    const kind = String(undo?.kind || "").trim();
    if (!token || !kind || typeof fetcher !== "function") return { ok: false, message: "undo receipt unavailable" };
    try {
      const response = await fetcher("/mutation-undo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind, token }),
        cache: "no-store",
      });
      return await readResult(response);
    } catch (error) {
      return { ok: false, message: error?.message || "undo failed" };
    }
  }

  async function openLocalFile(path = "", deps = {}) {
    const fetcher = global.ResearchOSRequestAuth.resolveFetcher(deps.fetcher);
    const normalizedPath = String(path || "").trim();
    if (!normalizedPath || typeof fetcher !== "function") return { ok: false, message: "file unavailable" };
    try {
      const response = await fetcher("/open-local-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: normalizedPath }),
        cache: "no-store",
      });
      return await readResult(response);
    } catch (error) {
      return { ok: false, message: error?.message || "open failed" };
    }
  }

  global.ResearchOSWorkSessionClient = Object.freeze({
    applyAttentionAction,
    setPortfolioState,
    completePortfolioItem,
    copyResult,
    fileSuffix,
    openLocalFile,
    undoMutation,
    uploadSourceFile,
  });
})(window);
