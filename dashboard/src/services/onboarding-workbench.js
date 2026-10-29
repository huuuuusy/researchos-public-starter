/* ResearchOS maintenance header.
 * 中文：首次接入向导的纯交互 owner；只管理四步表单、临时草稿与用户触发回调。
 * English: Pure interaction owner for the four-step first-run onboarding form and user-triggered callbacks.
 */

(function attachResearchOSOnboardingWorkbench(global) {
  const scrollIntoView = global.ResearchOSInteractions?.scrollIntoView || ((target, options = {}) => target?.scrollIntoView?.(options));
  const CONSENT_BOUNDARY_FIELDS = new Set(["scholar_url", "researchgate_url", "homepage_url", "other_urls"]);

  function text(value = "") {
    return String(value ?? "").trim();
  }

  function lines(value = "") {
    return String(value ?? "")
      .split(/\n+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function draftFromForm(form = null) {
    if (!form) return {};
    const data = new FormData(form);
    return {
      name: text(data.get("name")),
      role: text(data.get("role")),
      affiliation: text(data.get("affiliation")),
      bio: text(data.get("bio")),
      themes: lines(data.get("themes")),
      scholarUrl: text(data.get("scholar_url")),
      researchGateUrl: text(data.get("researchgate_url")),
      homepageUrl: text(data.get("homepage_url")),
      otherUrls: lines(data.get("other_urls")),
      privateNotes: text(data.get("private_notes")),
      consent: data.get("consent") === "on",
    };
  }

  function sourceEntries(draft = {}, translate = (key) => key) {
    return [
      { label: "Google Scholar", value: draft.scholarUrl },
      { label: "ResearchGate", value: draft.researchGateUrl },
      { label: translate("onboardingSourceHomepageLabel"), value: draft.homepageUrl },
      ...(draft.otherUrls || []).map((value, index) => ({ label: `${translate("onboardingSourceOtherLabel")} ${index + 1}`, value })),
    ].map((entry) => ({ ...entry, value: text(entry.value) })).filter((entry) => entry.value);
  }

  function sourceUrls(draft = {}) {
    return sourceEntries(draft).map((entry) => entry.value);
  }

  function invalidSourceUrl(draft = {}) {
    return sourceUrls(draft).find((value) => {
      try {
        const parsed = new URL(value);
        return !["http:", "https:"].includes(parsed.protocol) || !parsed.hostname;
      } catch {
        return true;
      }
    }) || "";
  }

  function isPrivateIpv4(hostname = "") {
    const parts = hostname.split(".");
    if (parts.length !== 4 || parts.some((part) => !/^\d+$/.test(part) || Number(part) > 255)) return false;
    const [a, b] = parts.map(Number);
    return a === 0 || a === 10 || a === 127 || (a === 100 && b >= 64 && b <= 127)
      || (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31)
      || (a === 192 && (b === 0 || b === 168)) || (a === 198 && (b === 18 || b === 19)) || a >= 224;
  }

  function unsafePublicSourceUrl(draft = {}) {
    return sourceUrls(draft).find((value) => {
      try {
        const parsed = new URL(value);
        const hostname = parsed.hostname.toLowerCase().replace(/^\[|\]$/g, "").replace(/\.$/, "");
        const localName = hostname === "localhost" || hostname.endsWith(".localhost")
          || hostname.endsWith(".local") || hostname.endsWith(".internal");
        const localIpv6 = hostname === "::1" || hostname === "::" || hostname.startsWith("::ffff:")
          || /^(fc|fd|fe[89ab])/i.test(hostname);
        return Boolean(parsed.username || parsed.password || localName || localIpv6 || isPrivateIpv4(hostname));
      } catch {
        return false;
      }
    }) || "";
  }

  function invalidSourceService(draft = {}) {
    const rules = [
      { value: text(draft.scholarUrl), valid: (hostname) => hostname === "scholar.google.com" },
      { value: text(draft.researchGateUrl), valid: (hostname) => hostname === "researchgate.net" || hostname.endsWith(".researchgate.net") },
    ];
    return rules.find((rule) => {
      if (!rule.value) return false;
      try {
        return !rule.valid(new URL(rule.value).hostname.toLowerCase());
      } catch {
        return false;
      }
    })?.value || "";
  }

  function setStatus(status = null, message = "", tone = "") {
    if (!status) return;
    status.textContent = message;
    status.dataset.tone = tone;
  }

  function clearValidationState(root = null) {
    if (!root) return;
    const statusId = root.querySelector("[data-onboarding-status]")?.id || "";
    root.querySelectorAll("[aria-invalid='true']").forEach((control) => {
      control.removeAttribute("aria-invalid");
      if (statusId && control.getAttribute("aria-describedby") === statusId) {
        control.removeAttribute("aria-describedby");
      }
    });
  }

  function resetConsent(root = null) {
    const consent = root?.querySelector?.("[name='consent']");
    if (!consent) return false;
    const changed = Boolean(consent.checked);
    consent.checked = false;
    return changed;
  }

  function resetMountedConsents(documentRoot = global.document) {
    const roots = Array.from(documentRoot?.querySelectorAll?.("[data-onboarding-personal]") || []);
    return roots.reduce((count, root) => count + (resetConsent(root) ? 1 : 0), 0);
  }

  function resetConsentForBoundaryChange(root = null, target = null) {
    if (!root || !target) return false;
    const changesSource = CONSENT_BOUNDARY_FIELDS.has(String(target.name || ""))
      || Boolean(target.matches?.("[data-onboarding-files]"));
    if (!changesSource) return false;
    return resetConsent(root);
  }

  function focusStepError(root = null, step = 1, draft = {}, files = []) {
    if (!root) return null;
    clearValidationState(root);
    let control = null;
    if (step === 1 && !draft.name) {
      control = root.querySelector("[name='name']");
    } else if (step === 2) {
      const invalidUrl = invalidSourceUrl(draft);
      const unsafeUrl = unsafePublicSourceUrl(draft);
      const mismatchedService = invalidSourceService(draft);
      if (invalidUrl || unsafeUrl || mismatchedService) {
        const invalidValue = invalidUrl || unsafeUrl || mismatchedService;
        control = Array.from(root.querySelectorAll("[name='scholar_url'], [name='researchgate_url'], [name='homepage_url'], [name='other_urls']"))
          .find((candidate) => lines(candidate.value).includes(invalidValue)) || null;
      } else if (!sourceUrls(draft).length && !files.length) {
        control = root.querySelector("[name='scholar_url']");
      }
    } else if (step === 3 && !draft.consent) {
      control = root.querySelector("[name='consent']");
    }
    if (!control) return null;
    control.setAttribute("aria-invalid", "true");
    const statusId = root.querySelector("[data-onboarding-status]")?.id || "";
    if (statusId) control.setAttribute("aria-describedby", statusId);
    control.focus({ preventScroll: true });
    scrollIntoView(control, { block: "center", behavior: "smooth" });
    return control;
  }

  function setBusy(root = null, busy = false) {
    if (!root) return false;
    const locked = Boolean(busy);
    root.setAttribute("aria-busy", locked ? "true" : "false");
    root.querySelectorAll("[data-onboarding-back], [data-onboarding-next], [data-onboarding-files], button[type='submit']").forEach((control) => {
      control.disabled = locked;
    });
    return locked;
  }

  function renderFiles(target = null, files = [], deps = {}) {
    if (!target) return;
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const translate = deps.translate || ((key) => key);
    target.innerHTML = files.length
      ? files.map((file) => `<span><strong>${escapeHtml(file.name || "")}</strong><small>${escapeHtml(file.type || translate("onboardingFileUnknown"))}</small></span>`).join("")
      : `<span>${escapeHtml(translate("onboardingNoFiles"))}</span>`;
  }

  function updateReview(root = null, draft = {}, files = [], deps = {}) {
    if (!root) return;
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const translate = deps.translate || ((key) => key);
    const name = root.querySelector("[data-onboarding-review-name]");
    const sources = root.querySelector("[data-onboarding-review-sources]");
    const filesNode = root.querySelector("[data-onboarding-review-files]");
    const sourceList = root.querySelector("[data-onboarding-review-source-list]");
    const reviewFileList = root.querySelector("[data-onboarding-review-file-list]");
    if (name) name.textContent = draft.name || translate("onboardingMissing");
    if (sources) sources.textContent = String(sourceUrls(draft).length);
    if (filesNode) filesNode.textContent = String(files.length);
    if (sourceList) {
      const entries = sourceEntries(draft, translate);
      sourceList.innerHTML = entries.length
        ? entries.map((entry) => `<li><strong>${escapeHtml(entry.label)}</strong><span>${escapeHtml(entry.value)}</span></li>`).join("")
        : `<li>${escapeHtml(translate("onboardingNoneSelected"))}</li>`;
    }
    if (reviewFileList) {
      reviewFileList.innerHTML = files.length
        ? files.map((file) => `<li><strong>${escapeHtml(file.name || translate("onboardingFileUnknown"))}</strong><span>${escapeHtml(file.type || translate("onboardingFileUnknown"))}</span></li>`).join("")
        : `<li>${escapeHtml(translate("onboardingNoneSelected"))}</li>`;
    }
  }

  function setStep(root = null, step = 1, deps = {}, options = {}) {
    if (!root) return 1;
    const translate = deps.translate || ((key) => key);
    const next = Math.max(1, Math.min(4, Number(step) || 1));
    root.querySelectorAll("[data-onboarding-step-panel]").forEach((panel) => {
      panel.hidden = Number(panel.dataset.onboardingStepPanel) !== next;
    });
    root.querySelectorAll("[data-onboarding-step-indicator]").forEach((indicator) => {
      const active = Number(indicator.dataset.onboardingStepIndicator) === next;
      indicator.classList.toggle("is-active", active);
      if (active) indicator.setAttribute("aria-current", "step");
      else indicator.removeAttribute("aria-current");
    });
    const progress = root.querySelector("[data-onboarding-progress]");
    if (progress) {
      progress.value = next;
      progress.setAttribute("aria-label", `${translate("onboardingProgress")} ${next}/4`);
    }
    root.dataset.onboardingStep = String(next);
    const wizard = root.matches?.("[data-onboarding-personal]")
      ? root
      : root.querySelector("[data-onboarding-personal]");
    if (wizard && wizard !== root) wizard.dataset.onboardingStep = String(next);
    if (options.focus) {
      root.querySelector(`[data-onboarding-step-panel="${next}"]`)?.focus({ preventScroll: true });
    }
    return next;
  }

  function validateStep(step = 1, draft = {}, files = [], translate = (key) => key) {
    if (step === 1 && !draft.name) return translate("onboardingNeedName");
    if (step === 2 && !sourceUrls(draft).length && !files.length) return translate("onboardingNeedSource");
    if (step === 2 && invalidSourceUrl(draft)) return translate("onboardingInvalidUrl");
    if (step === 2 && unsafePublicSourceUrl(draft)) return translate("onboardingUnsafePublicUrl");
    if (step === 2 && invalidSourceService(draft)) return translate("onboardingSourceServiceMismatch");
    if (step === 3 && !draft.consent) return translate("onboardingNeedConsent");
    return "";
  }

  function bind(root = null, callbacks = {}, deps = {}) {
    if (!root) return;
    resetConsent(root);
    const translate = deps.translate || ((key) => key);
    const form = root.querySelector("[data-onboarding-form]");
    const status = root.querySelector("[data-onboarding-status]");
    const fileInput = root.querySelector("[data-onboarding-files]");
    const fileList = root.querySelector("[data-onboarding-file-list]");
    let files = callbacks.onGetFiles?.() || [];
    let step = setStep(root, Number(root.dataset.onboardingStep || 1), deps);
    let submitting = false;

    const snapshot = () => draftFromForm(form);
    const sync = () => {
      const draft = snapshot();
      callbacks.onDraftChange?.(draft);
      updateReview(root, draft, files, deps);
      return draft;
    };

    form?.addEventListener("input", (event) => {
      resetConsentForBoundaryChange(root, event.target);
      clearValidationState(root);
      setStatus(status, "", "");
      sync();
    });
    form?.addEventListener("change", (event) => {
      resetConsentForBoundaryChange(root, event.target);
      clearValidationState(root);
      setStatus(status, "", "");
      sync();
    });
    fileInput?.addEventListener("change", () => {
      resetConsentForBoundaryChange(root, fileInput);
      files = Array.from(fileInput.files || []);
      files = callbacks.onFilesChange?.(files) || files;
      renderFiles(fileList, files, deps);
      sync();
    });
    root.querySelectorAll("[data-onboarding-next]").forEach((button) => {
      button.addEventListener("click", () => {
        const draft = sync();
        const error = validateStep(step, draft, files, translate);
        if (error) {
          setStatus(status, error, "risk");
          focusStepError(root, step, draft, files);
          return;
        }
        clearValidationState(root);
        setStatus(status, "", "");
        step = setStep(root, step + 1, deps, { focus: true });
      });
    });
    root.querySelectorAll("[data-onboarding-back]").forEach((button) => {
      button.addEventListener("click", () => {
        setStatus(status, "", "");
        step = setStep(root, step - 1, deps, { focus: true });
      });
    });
    root.querySelectorAll("[data-onboarding-copy-command]").forEach((button) => {
      button.addEventListener("click", () => callbacks.onCopyCommand?.({ button, status }));
    });
    form?.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (submitting) return;
      const draft = sync();
      for (const requiredStep of [1, 2, 3]) {
        const error = validateStep(requiredStep, draft, files, translate);
        if (error) {
          step = setStep(root, requiredStep, deps);
          setStatus(status, error, "risk");
          focusStepError(root, requiredStep, draft, files);
          return;
        }
      }
      submitting = true;
      setBusy(root, true);
      setStatus(status, translate("onboardingStarting"), "progress");
      let result = null;
      try {
        result = await callbacks.onStart?.({ draft, files, status });
      } catch {
        result = { ok: false };
      }
      if (result?.ok) {
        setStatus(status, translate("onboardingQueued"), "ok");
        return;
      }
      submitting = false;
      setBusy(root, false);
      if (result?.cancelled) setStatus(status, "", "");
      else setStatus(status, result?.message || translate("onboardingStartFailed"), "risk");
    });

    renderFiles(fileList, files, deps);
    sync();
  }

  global.addEventListener?.("pageshow", () => {
    resetMountedConsents(global.document);
  });

  global.ResearchOSOnboardingWorkbench = Object.freeze({
    bind,
    clearValidationState,
    renderFiles,
    setBusy,
    setStatus,
    sourceEntries,
    sourceUrls,
    invalidSourceUrl,
    unsafePublicSourceUrl,
    invalidSourceService,
    focusStepError,
    resetConsent,
    resetConsentForBoundaryChange,
    validateStep,
  });
})(window);
