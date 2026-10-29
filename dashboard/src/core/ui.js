/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「UI」；供 app、service、view 复用。
 * English: Browser-side core primitive for UI in the ResearchOS dashboard; shared by app, services, and views.
 */

(function attachResearchOSUiCore(global) {
  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function safeClassList(value = "") {
    return String(value || "")
      .split(/\s+/)
      .map((item) => item.replace(/[^a-zA-Z0-9_-]/g, ""))
      .filter(Boolean)
      .join(" ");
  }

  function encodeDataPayload(value) {
    const text = String(value ?? "");
    try {
      const bytes = new TextEncoder().encode(text);
      const binary = Array.from(bytes, (byte) => String.fromCharCode(byte)).join("");
      return btoa(binary);
    } catch {
      return encodeURIComponent(text);
    }
  }

  function decodeDataPayload(value) {
    const text = String(value || "");
    try {
      const binary = atob(text);
      const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
      return new TextDecoder().decode(bytes);
    } catch {
      try {
        return decodeURIComponent(text);
      } catch {
        return text;
      }
    }
  }

  async function writeClipboardText(value) {
    const text = String(value ?? "");
    if (global.navigator?.clipboard?.writeText) {
      try {
        await global.navigator.clipboard.writeText(text);
        return true;
      } catch {
        // Fall through to the textarea fallback.
      }
    }
    const textarea = global.document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";
    global.document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    let copied = false;
    try {
      copied = global.document.execCommand("copy");
    } finally {
      textarea.remove();
    }
    return copied;
  }

  window.ResearchOSUiCore = Object.freeze({
    escapeHtml,
    safeClassList,
    encodeDataPayload,
    decodeDataPayload,
    writeClipboardText,
  });
})(window);
