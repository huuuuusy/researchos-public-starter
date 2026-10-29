/* ResearchOS maintenance header.
 * 中文：首次接入向导的纯 HTML 视图；公开 demo 只给启动指引，personal-vault 才接收真实材料。
 * English: Pure HTML view for first-run onboarding; the public demo only guides launch while personal-vault accepts real material.
 */

(function attachResearchOSOnboardingView(global) {
  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      guidePath: deps.guidePath || "08_exports/public_starter/onboarding-step-by-step.md",
      previewButton: deps.previewButton || (() => ""),
      translate: deps.translate || ((key) => key),
    };
  }

  function value(draft = {}, key = "") {
    const raw = draft[key];
    return Array.isArray(raw) ? raw.join("\n") : String(raw ?? "");
  }

  function renderSteps(deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    return `
      <ol class="onboarding-steps" aria-label="${escapeHtml(translate("onboardingProgress"))}">
        ${[1, 2, 3, 4].map((step) => `
          <li data-onboarding-step-indicator="${step}" class="${step === 1 ? "is-active" : ""}" ${step === 1 ? 'aria-current="step"' : ""}>
            <span>${step}</span><strong>${escapeHtml(translate(`onboardingStep${step}`))}</strong>
          </li>
        `).join("")}
      </ol>
      <progress data-onboarding-progress max="4" value="1"></progress>
    `;
  }

  function renderPublicStart(deps = {}) {
    const { escapeHtml, guidePath, previewButton, translate } = normalizeDeps(deps);
    return `
      <section class="onboarding-launch" data-onboarding-public>
        <div>
          <span>${escapeHtml(translate("onboardingEyebrow"))}</span>
          <h3>${escapeHtml(translate("onboardingPublicTitle"))}</h3>
          <p>${escapeHtml(translate("onboardingPublicBody"))}</p>
        </div>
        <footer>
          <button type="button" class="primary" data-action-kind="direct" data-onboarding-copy-command>${escapeHtml(translate("onboardingCopyCommand"))}</button>
          ${previewButton(guidePath, translate("onboardingOpenGuide"))}
          <output id="onboarding-public-status" data-onboarding-status role="status" aria-live="polite" aria-atomic="true"></output>
        </footer>
        <ol>
          <li>${escapeHtml(translate("onboardingPublicStep1"))}</li>
          <li>${escapeHtml(translate("onboardingPublicStep2"))}</li>
          <li>${escapeHtml(translate("onboardingPublicStep3"))}</li>
          <li>${escapeHtml(translate("onboardingPublicStep4"))}</li>
        </ol>
      </section>
    `;
  }

  function renderPersonalWizard({ draft = {}, recordCount = 0 } = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    return `
      <section class="onboarding-wizard" data-onboarding-personal data-onboarding-step="1">
        <details class="onboarding-disclosure" data-onboarding-disclosure="${recordCount ? "collapsed" : "open"}" ${recordCount ? "" : "open"}>
          <summary>
          <div>
            <span>${escapeHtml(translate("onboardingEyebrow"))}</span>
            <h3>${escapeHtml(recordCount ? translate("onboardingRefreshTitle") : translate("onboardingPersonalTitle"))}</h3>
          </div>
          <small>${escapeHtml(String(recordCount))} ${escapeHtml(translate("onboardingExistingCards"))}</small>
          </summary>
          <div class="onboarding-wizard-body">
            <p>${escapeHtml(translate("onboardingPersonalBody"))}</p>
            ${renderSteps(deps)}
            <form data-onboarding-form>
          <section data-onboarding-step-panel="1" tabindex="-1" aria-labelledby="onboarding-step-title-1">
            <div class="onboarding-step-copy"><strong id="onboarding-step-title-1">${escapeHtml(translate("onboardingBasicsTitle"))}</strong><span>${escapeHtml(translate("onboardingBasicsHint"))}</span></div>
            <div class="onboarding-grid">
              <label class="wide"><span>${escapeHtml(translate("onboardingName"))}</span><input name="name" required maxlength="160" value="${escapeHtml(value(draft, "name"))}"></label>
            </div>
            <details class="onboarding-optional">
              <summary>${escapeHtml(translate("onboardingOptionalProfile"))}</summary>
              <div class="onboarding-grid">
                <label><span>${escapeHtml(translate("onboardingRole"))}</span><input name="role" maxlength="240" value="${escapeHtml(value(draft, "role"))}"></label>
                <label><span>${escapeHtml(translate("onboardingAffiliation"))}</span><input name="affiliation" maxlength="240" value="${escapeHtml(value(draft, "affiliation"))}"></label>
                <label class="wide"><span>${escapeHtml(translate("onboardingThemes"))}</span><textarea name="themes" rows="3" maxlength="2500">${escapeHtml(value(draft, "themes"))}</textarea></label>
                <label class="wide"><span>${escapeHtml(translate("onboardingBio"))}</span><textarea name="bio" rows="3" maxlength="3000">${escapeHtml(value(draft, "bio"))}</textarea></label>
              </div>
            </details>
            <footer><button type="button" class="primary" data-action-kind="navigation" data-onboarding-next>${escapeHtml(translate("onboardingNext"))}</button></footer>
          </section>
          <section data-onboarding-step-panel="2" tabindex="-1" aria-labelledby="onboarding-step-title-2" hidden>
            <div class="onboarding-step-copy"><strong id="onboarding-step-title-2">${escapeHtml(translate("onboardingSourcesTitle"))}</strong><span>${escapeHtml(translate("onboardingSourcesHint"))}</span></div>
            <div class="onboarding-grid">
              <label><span>Google Scholar</span><input name="scholar_url" type="url" value="${escapeHtml(value(draft, "scholarUrl"))}" placeholder="https://scholar.google.com/..."></label>
              <label><span>ResearchGate</span><input name="researchgate_url" type="url" value="${escapeHtml(value(draft, "researchGateUrl"))}" placeholder="https://www.researchgate.net/..."></label>
            </div>
            <label class="onboarding-file-picker">
              <input type="file" multiple data-onboarding-files accept=".pdf,.doc,.docx,.md,.txt">
              <strong>${escapeHtml(translate("onboardingFilesTitle"))}</strong>
              <span>${escapeHtml(translate("onboardingFilesHint"))}</span>
            </label>
            <div class="onboarding-file-list" data-onboarding-file-list></div>
            <details class="onboarding-optional">
              <summary>${escapeHtml(translate("onboardingOptionalLinks"))}</summary>
              <div class="onboarding-grid">
                <label class="wide"><span>${escapeHtml(translate("onboardingHomepage"))}</span><input name="homepage_url" type="url" value="${escapeHtml(value(draft, "homepageUrl"))}" placeholder="https://..."></label>
                <label class="wide"><span>${escapeHtml(translate("onboardingOtherLinks"))}</span><textarea name="other_urls" rows="3" placeholder="ORCID, DBLP, Semantic Scholar, DOI, arXiv...">${escapeHtml(value(draft, "otherUrls"))}</textarea></label>
              </div>
            </details>
            <footer><button type="button" data-action-kind="navigation" data-onboarding-back>${escapeHtml(translate("onboardingBack"))}</button><button type="button" class="primary" data-action-kind="navigation" data-onboarding-next>${escapeHtml(translate("onboardingNext"))}</button></footer>
          </section>
          <section data-onboarding-step-panel="3" tabindex="-1" aria-labelledby="onboarding-step-title-3" hidden>
            <div class="onboarding-step-copy"><strong id="onboarding-step-title-3">${escapeHtml(translate("onboardingBoundaryTitle"))}</strong><span>${escapeHtml(translate("onboardingBoundaryHint"))}</span></div>
            <div class="onboarding-review-grid">
              <article><span>${escapeHtml(translate("onboardingReviewName"))}</span><strong data-onboarding-review-name></strong></article>
              <article><span>${escapeHtml(translate("onboardingReviewLinks"))}</span><strong data-onboarding-review-sources>0</strong></article>
              <article><span>${escapeHtml(translate("onboardingReviewFiles"))}</span><strong data-onboarding-review-files>0</strong></article>
            </div>
            <div class="onboarding-source-review">
              <section>
                <strong>${escapeHtml(translate("onboardingSelectedSources"))}</strong>
                <ul data-onboarding-review-source-list></ul>
              </section>
              <section>
                <strong>${escapeHtml(translate("onboardingSelectedFiles"))}</strong>
                <ul data-onboarding-review-file-list></ul>
              </section>
            </div>
            <details class="onboarding-optional">
              <summary>${escapeHtml(translate("onboardingOptionalBoundary"))}</summary>
              <label class="wide"><span>${escapeHtml(translate("onboardingPrivateNotes"))}</span><textarea name="private_notes" rows="3" maxlength="2000">${escapeHtml(value(draft, "privateNotes"))}</textarea></label>
            </details>
            <label class="onboarding-consent"><input type="checkbox" name="consent"><span>${escapeHtml(translate("onboardingConsent"))}</span></label>
            <footer><button type="button" data-action-kind="navigation" data-onboarding-back>${escapeHtml(translate("onboardingBack"))}</button><button type="button" class="primary" data-action-kind="navigation" data-onboarding-next>${escapeHtml(translate("onboardingNext"))}</button></footer>
          </section>
          <section data-onboarding-step-panel="4" tabindex="-1" aria-labelledby="onboarding-step-title-4" hidden>
            <div class="onboarding-step-copy"><strong id="onboarding-step-title-4">${escapeHtml(translate("onboardingBuildTitle"))}</strong><span>${escapeHtml(translate("onboardingBuildHint"))}</span></div>
            <ul class="onboarding-output-list">
              <li>${escapeHtml(translate("onboardingOutputPerson"))}</li>
              <li>${escapeHtml(translate("onboardingOutputPublications"))}</li>
              <li>${escapeHtml(translate("onboardingOutputPapers"))}</li>
              <li>${escapeHtml(translate("onboardingOutputTheme"))}</li>
            </ul>
            <aside>${escapeHtml(translate("onboardingDownloadBoundary"))}</aside>
            <footer><button type="button" data-action-kind="navigation" data-onboarding-back>${escapeHtml(translate("onboardingBack"))}</button><button type="submit" class="primary" data-action-kind="direct">${escapeHtml(translate("onboardingStart"))}</button></footer>
          </section>
              <output id="onboarding-personal-status" data-onboarding-status role="status" aria-live="polite" aria-atomic="true"></output>
            </form>
          </div>
        </details>
      </section>
    `;
  }

  global.ResearchOSOnboardingView = Object.freeze({ renderPersonalWizard, renderPublicStart, renderSteps, value });
})(window);
