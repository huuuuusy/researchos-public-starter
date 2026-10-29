/* ResearchOS maintenance header.
 * 中文：RuntimeProfileProjection 的只读视图；不执行命令、不编辑配置，也不提供远程 dispatch 控件。
 * English: Read-only RuntimeProfileProjection view; it runs no command, edits no config, and exposes no remote-dispatch control.
 */

(function attachResearchOSRuntimeProfileView(global) {
  function render(value, deps = {}) {
    const profile = global.ResearchOSRuntimeProfileProjection?.normalize(value);
    if (!profile) return "";
    const escapeHtml = deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml;
    const translate = deps.translate || ((key) => key);
    if (typeof escapeHtml !== "function") return "";
    const capability = profile.result_modes.length ? profile.result_modes.join(" / ") : translate("runtimeProfileNoExecution");
    return `
      <section class="unified-inbox-provider-status" data-runtime-profile-projection aria-label="${escapeHtml(translate("runtimeProfileTitle"))}">
        <span>${escapeHtml(translate("runtimeProfileTitle"))}</span>
        <code>${escapeHtml(profile.profile_id)}</code>
        <small>${escapeHtml(translate("runtimeProfileProvider"))}: ${escapeHtml(profile.provider)}</small>
        <small>${escapeHtml(translate("runtimeProfileAdapter"))}: ${escapeHtml(profile.adapter_family)}</small>
        <small>${escapeHtml(translate("runtimeProfileModel"))}: ${escapeHtml(profile.model)}</small>
        <small>${escapeHtml(translate("runtimeProfileReasoning"))}: ${escapeHtml(profile.reasoning_effort)}</small>
        <small>${escapeHtml(translate("runtimeProfileCapabilities"))}: ${escapeHtml(capability)} · cancel=${escapeHtml(profile.cancel)}</small>
        <small>${escapeHtml(translate("runtimeProfileVerification"))}: ${escapeHtml(profile.verification_state)}</small>
        <small>${escapeHtml(translate("runtimeProfileExecution"))}: ${escapeHtml(profile.execution_scope)}</small>
        <details>
          <summary>${escapeHtml(translate("runtimeProfileConfigureElsewhere"))}</summary>
          <code>${escapeHtml(profile.configuration_handoff.command)}</code>
          <small>${escapeHtml(profile.configuration_handoff.config_target)}</small>
        </details>
        <p>${escapeHtml(translate("runtimeProfileBoundary"))}</p>
      </section>
    `;
  }

  global.ResearchOSRuntimeProfileView = Object.freeze({ render });
})(window);
