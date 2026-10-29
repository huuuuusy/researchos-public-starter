/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「clipboard workbench」；负责 DOM 事件绑定，把副作用回调交还 app。
 * English: Workbench interaction adapter for clipboard workbench in the ResearchOS dashboard; owns DOM event binding and returns side effects to app callbacks.
 */

(function attachResearchOSClipboardWorkbenchService(global) {
  async function fallbackWriteClipboardText() {
    return false;
  }

  function fallbackDecodeDataPayload(value) {
    return String(value || "");
  }

  function normalizeDeps(deps = {}) {
    return {
      decodeDataPayload: deps.decodeDataPayload || fallbackDecodeDataPayload,
      setTimeout: deps.setTimeout || global.setTimeout?.bind(global) || (() => {}),
      writeClipboardText: deps.writeClipboardText || fallbackWriteClipboardText,
    };
  }

  async function copyPlainText(value = "", deps = {}) {
    const { writeClipboardText } = normalizeDeps(deps);
    const text = String(value ?? "");
    const copied = await writeClipboardText(text);
    return { copied, text };
  }

  async function copyEncodedPayload(encodedPayload = "", deps = {}) {
    const { decodeDataPayload } = normalizeDeps(deps);
    const text = decodeDataPayload(encodedPayload || "");
    const copied = await copyPlainText(text, deps);
    return { ...copied, text };
  }

  function resetButtonLabel(button, label = "", resetMs = 1200, deps = {}) {
    if (!button || !label) return;
    const { setTimeout } = normalizeDeps(deps);
    setTimeout(() => {
      button.textContent = label;
    }, resetMs);
  }

  function applyCopyButtonFeedback(options = {}, deps = {}) {
    const {
      button = null,
      copied = false,
      copiedLabel = "",
      fallbackLabel,
      fallbackTitle = "",
      originalLabel = "",
      resetLabel = "",
      resetMs = 1200,
      resetOnCopied = true,
      resetOnFallback = false,
    } = options;
    if (!button) return "";
    const label = originalLabel || button.textContent || "";
    if (copied) {
      button.textContent = copiedLabel || label;
      if (resetOnCopied) resetButtonLabel(button, resetLabel || label, resetMs, deps);
      return label;
    }
    if (fallbackLabel !== undefined) button.textContent = fallbackLabel;
    if (fallbackTitle) button.title = fallbackTitle;
    if (resetOnFallback) resetButtonLabel(button, resetLabel || label, resetMs, deps);
    return label;
  }

  global.ResearchOSClipboardWorkbenchService = Object.freeze({
    applyCopyButtonFeedback,
    copyEncodedPayload,
    copyPlainText,
  });
  global.document?.documentElement?.setAttribute("data-researchos-clipboard-workbench", "ready");
})(window);
