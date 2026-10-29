/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 视图「material intake」的纯 HTML 渲染层；不保存持久状态、不直接执行写入副作用。
 * English: Pure HTML rendering layer for the material intake dashboard view; stores no durable state and performs no write side effects.
 */

(function attachResearchOSMaterialIntakeView(global) {
  function fallbackSimpleList(items = [], mapper = () => "", empty = "") {
    const emptyList = global.ResearchOSEmptyStateComponent?.renderEmptyList;
    if (emptyList) return emptyList(items, mapper, empty, { escapeHtml: global.ResearchOSUiCore?.escapeHtml });
    const list = Array.isArray(items) ? items.filter(Boolean) : [];
    return list.length ? list.map(mapper).join("") : global.ResearchOSUiCore?.escapeHtml(empty || "");
  }

  function fallbackPreviewButton(path = "", label = "", deps = {}) {
    const previewButton = global.ResearchOSPreviewLinksComponent?.previewButton;
    return previewButton ? previewButton(path, label, deps) : "";
  }

  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      materialIntakeTypeLabel: deps.materialIntakeTypeLabel || ((type) => type || ""),
      previewButton: deps.previewButton || ((path = "", label = "") => fallbackPreviewButton(path, label, deps)),
      simpleList: deps.simpleList || fallbackSimpleList,
      translate: deps.translate || ((key) => key),
    };
  }

  function intakeOptions(deps = {}) {
    const { translate } = normalizeDeps(deps);
    return {
      privacyOptions: [
        ["local_only", translate("intakePrivacyLocal")],
        ["internal", translate("intakePrivacyInternal")],
        ["public_candidate", translate("intakePrivacyPublicCandidate")],
      ],
      sourceOptions: [
        ["user_provided", translate("intakeSourceUser")],
        ["link", translate("intakeSourceLink")],
        ["local_file", translate("intakeSourceLocal")],
        ["candidate", translate("intakeSourceCandidate")],
      ],
      typeOptions: [
        ["paper", translate("intakeTypePaper")],
        ["talk", translate("intakeTypeTalk")],
        ["person", translate("intakeTypePerson")],
        ["project", translate("intakeTypeProject")],
        ["group", translate("intakeTypeGroup")],
        ["other", translate("intakeTypeOther")],
      ],
    };
  }

  function renderOptionList(options = [], deps = {}) {
    const { escapeHtml } = normalizeDeps(deps);
    return (options || [])
      .map(([value, label]) => `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`)
      .join("");
  }

  function renderIntakeCard(item = {}, deps = {}) {
    const { escapeHtml, materialIntakeTypeLabel, translate } = normalizeDeps(deps);
    return `
      <article class="material-intake-item">
        <header>
          <span>${escapeHtml(item.type_label || materialIntakeTypeLabel(item.material_type))}</span>
          <em>${escapeHtml(item.status || "pending_codex_review")}</em>
        </header>
        <strong>${escapeHtml(item.title || "")}</strong>
        <p>${escapeHtml(item.note || item.target_hint || "")}</p>
        <footer>
          <span>${escapeHtml(String((item.attachments || []).length))} ${escapeHtml(translate("intakeFiles"))}</span>
          <button type="button" data-action-kind="direct" data-withdraw-intake="${escapeHtml(item.id || "")}">${escapeHtml(translate("intakeWithdraw"))}</button>
        </footer>
      </article>
    `;
  }

  function renderMaterialIntakePanelHtml({
    context = "materials",
    defaultTarget = "",
    inboxPath = "",
    intakeItems = [],
    statusText = "",
  } = {}, deps = {}) {
    const { escapeHtml, previewButton, simpleList, translate } = normalizeDeps(deps);
    const { privacyOptions, sourceOptions, typeOptions } = intakeOptions(deps);
    return `
      <details class="material-intake-panel" data-material-intake-panel data-asset-create-panel ${context === "materials" ? "open" : ""}>
        <summary>
          <div>
            <strong>${escapeHtml(translate("intakeTitle"))}</strong>
            <span>${escapeHtml(translate("intakeHint"))}</span>
          </div>
          <b>${escapeHtml(String(intakeItems.length))}</b>
        </summary>
        <form class="material-intake-form" data-material-intake-form>
          <div class="material-intake-grid">
            <label>
              <span>${escapeHtml(translate("intakeType"))}</span>
              <select name="material_type" data-intake-type aria-label="${escapeHtml(translate("intakeType"))}">
                ${renderOptionList(typeOptions, deps)}
              </select>
            </label>
            <label>
              <span>${escapeHtml(translate("intakeTitleField"))}</span>
              <input name="title" type="text" aria-label="${escapeHtml(translate("intakeTitleField"))}" placeholder="${escapeHtml(translate("intakeTitlePlaceholder"))}" required>
            </label>
            <label>
              <span>${escapeHtml(translate("intakeTarget"))}</span>
              <input name="target_hint" type="text" aria-label="${escapeHtml(translate("intakeTarget"))}" value="${escapeHtml(defaultTarget)}">
            </label>
            <label>
              <span>${escapeHtml(translate("intakeRelatedProject"))}</span>
              <input name="related_project" type="text" aria-label="${escapeHtml(translate("intakeRelatedProject"))}" placeholder="${escapeHtml(translate("intakeRelatedProjectPlaceholder"))}">
            </label>
            <label>
              <span>${escapeHtml(translate("intakeMainline"))}</span>
              <input name="mainline_hint" type="text" aria-label="${escapeHtml(translate("intakeMainline"))}" placeholder="${escapeHtml(translate("intakeMainlinePlaceholder"))}">
            </label>
            <label>
              <span>${escapeHtml(translate("intakeSourceLevel"))}</span>
              <select name="source_level" aria-label="${escapeHtml(translate("intakeSourceLevel"))}">
                ${renderOptionList(sourceOptions, deps)}
              </select>
            </label>
            <label>
              <span>${escapeHtml(translate("intakePrivacy"))}</span>
              <select name="privacy" aria-label="${escapeHtml(translate("intakePrivacy"))}">
                ${renderOptionList(privacyOptions, deps)}
              </select>
            </label>
          </div>
          <label>
            <span>${escapeHtml(translate("intakeLinks"))}</span>
            <textarea name="links" rows="3" aria-label="${escapeHtml(translate("intakeLinks"))}" placeholder="${escapeHtml(translate("intakeLinksPlaceholder"))}"></textarea>
          </label>
          <label>
            <span>${escapeHtml(translate("intakeNote"))}</span>
            <textarea name="note" rows="3" aria-label="${escapeHtml(translate("intakeNote"))}" placeholder="${escapeHtml(translate("intakeNotePlaceholder"))}"></textarea>
          </label>
          <div class="material-intake-dropzone" data-intake-dropzone>
            <input type="file" multiple data-intake-files aria-label="${escapeHtml(translate("intakeFiles"))}">
            <strong>${escapeHtml(translate("intakeDropTitle"))}</strong>
            <span>${escapeHtml(translate("intakeDropHint"))}</span>
            <div class="material-intake-file-list" data-intake-file-list>${escapeHtml(translate("intakeNoFiles"))}</div>
          </div>
          <footer>
            <button type="submit" class="focus-action-button primary" data-action-kind="direct">${escapeHtml(translate("intakeAdd"))}</button>
            <button type="button" data-action-kind="handoff" data-process-intake-inbox>${escapeHtml(translate("intakeProcess"))}</button>
            ${previewButton(inboxPath, translate("intakeOpenInbox"))}
            <output data-intake-status>${escapeHtml(statusText)}</output>
          </footer>
        </form>
        <div class="material-intake-list">${simpleList(intakeItems.slice(0, 4), (item) => renderIntakeCard(item, deps), translate("intakeEmpty"))}</div>
      </details>
    `;
  }

  global.ResearchOSMaterialIntakeView = Object.freeze({
    intakeOptions,
    renderIntakeCard,
    renderMaterialIntakePanelHtml,
    renderOptionList,
  });
})(window);
