/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 视图「external evidence」的纯 HTML 渲染层；不保存持久状态、不直接执行写入副作用。
 * English: Pure HTML rendering layer for the external evidence dashboard view; stores no durable state and performs no write side effects.
 */

(function attachResearchOSExternalEvidenceView(global) {
  function fallbackPreviewButton(path = "", label = "", deps = {}) {
    const previewButton = global.ResearchOSPreviewLinksComponent?.previewButton;
    return previewButton ? previewButton(path, label, deps) : "";
  }

  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      previewButton: deps.previewButton || ((path = "", label = "") => fallbackPreviewButton(path, label, deps)),
      translate: deps.translate || ((key) => key),
    };
  }

  function isScholarSource(source = {}) {
    return source.id === "google_scholar" || source.source_type === "scholar_profile";
  }

  function sourceRole(source = {}, deps = {}) {
    const { translate } = normalizeDeps(deps);
    return isScholarSource(source) ? translate("external.citationProfile") : translate("external.publicProfile");
  }

  function sourceGlyph(source = {}) {
    return isScholarSource(source) ? "G" : "H";
  }

  function sourceLabel(source = {}, deps = {}) {
    const key = `external.sourceLabel.${source.id || ""}`;
    const { translate } = normalizeDeps(deps);
    const translated = translate(key);
    return translated && translated !== key ? translated : String(source.label || source.id || "");
  }

  function sourceUseChips(source = {}) {
    return Array.isArray(source.use_for) ? source.use_for.slice(0, 3) : [];
  }

  function translatedValue(prefix = "", value = "", deps = {}) {
    const { translate } = normalizeDeps(deps);
    const key = `${prefix}.${value}`;
    const translated = translate(key);
    return translated && translated !== key ? translated : String(value || "").replaceAll("_", " ");
  }

  function statusLabel(status = "", deps = {}) {
    return translatedValue("external.status", status, deps);
  }

  function refreshLabel(mode = "", deps = {}) {
    return translatedValue("external.refresh", mode, deps);
  }

  function sourceNotes(source = {}, deps = {}) {
    const key = `external.notes.${source.id || ""}`;
    const { translate } = normalizeDeps(deps);
    const translated = translate(key);
    return translated && translated !== key ? translated : String(source.notes || "");
  }

  function metricValue(value, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    return escapeHtml(String(value || translate("external.pendingMetric")));
  }

  function renderScholarMetrics(source = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    if (!isScholarSource(source)) return "";
    return `
      <div class="external-metric-grid">
        <div><strong>${metricValue(source.total_citations, deps)}</strong><span>${escapeHtml(translate("external.totalCitations"))}</span></div>
        <div><strong>${metricValue(source.h_index, deps)}</strong><span>${escapeHtml(translate("external.hIndex"))}</span></div>
        <div><strong>${metricValue(source.i10_index, deps)}</strong><span>${escapeHtml(translate("external.i10Index"))}</span></div>
      </div>
      ${
        source.metrics_checked_at
          ? `<div class="external-checked-at">${escapeHtml(translate("external.checkedAt"))}: ${escapeHtml(source.metrics_checked_at)}</div>`
          : `<div class="external-checked-at">${escapeHtml(translate("external.checkedAt"))}: ${escapeHtml(translate("external.pendingMetric"))}</div>`
      }
    `;
  }

  function renderSourceCard(source = {}, deps = {}) {
    const { escapeHtml, translate } = normalizeDeps(deps);
    return `
      <article class="external-source-card ${escapeHtml(source.status || "")}">
        <div class="external-source-head">
          <div class="external-source-glyph">${escapeHtml(sourceGlyph(source))}</div>
          <div>
            <strong>${escapeHtml(sourceLabel(source, deps))}</strong>
            <span>${escapeHtml(sourceRole(source, deps))}</span>
          </div>
        </div>
        <div class="external-source-meta">
          <span>${escapeHtml(statusLabel(source.status || "", deps))}</span>
          <span>${escapeHtml(refreshLabel(source.refresh_mode || "", deps))}</span>
          ${source.last_checked ? `<span>${escapeHtml(source.last_checked)}</span>` : ""}
        </div>
        <div class="external-use-chips">
          ${sourceUseChips(source)
            .map((item) => `<span>${escapeHtml(translatedValue("external.use", item, deps))}</span>`)
            .join("")}
        </div>
        ${renderScholarMetrics(source, deps)}
        <p>${escapeHtml(sourceNotes(source, deps))}</p>
        ${
          source.url
            ? `<a class="external-open-link" href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer" data-action-kind="navigation">${escapeHtml(translate("external.openSource"))}</a>`
            : ""
        }
      </article>
    `;
  }

  function renderExternalEvidenceHtml({ external = {}, sources = [] } = {}, deps = {}) {
    const { escapeHtml, previewButton, translate } = normalizeDeps(deps);
    return `
      <div class="external-visual-summary">
        <div class="external-score">
          <strong>${escapeHtml(String(external.configured || 0))}/${escapeHtml(String(sources.length || 0))}</strong>
          <span>${escapeHtml(translate("external.trackedSources"))}</span>
        </div>
        <div class="external-policy">
          <strong>${escapeHtml(translate("external.snapshotPolicy"))}</strong>
          <span>${escapeHtml(translate("external.policy"))}</span>
          ${previewButton(external.path || "01_knowledge/metadata/external-profile-sources.yml", translate("external.openConfig"))}
        </div>
      </div>
      <div class="external-source-grid visual">
        ${sources.map((source) => renderSourceCard(source, deps)).join("")}
      </div>
    `;
  }

  global.ResearchOSExternalEvidenceView = Object.freeze({
    isScholarSource,
    renderExternalEvidenceHtml,
    renderScholarMetrics,
    renderSourceCard,
    sourceGlyph,
    sourceRole,
  });
})(window);
