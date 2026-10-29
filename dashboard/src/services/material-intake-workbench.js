/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 工作台交互「material intake workbench」；负责 DOM 事件绑定，把副作用回调交还 app。
 * English: Workbench interaction adapter for material intake workbench in the ResearchOS dashboard; owns DOM event binding and returns side effects to app callbacks.
 */

(function attachResearchOSMaterialIntakeWorkbenchService(global) {
  const { bindAll } = global.ResearchOSInteractions;

  function normalizeDeps(deps = {}) {
    return {
      escapeHtml: deps.escapeHtml || global.ResearchOSUiCore?.escapeHtml,
      normalizeAttachment: deps.normalizeAttachment || ((file) => file),
      translate: deps.translate || ((key) => key),
    };
  }

  function renderIntakeFileList(fileList, files = [], deps = {}) {
    if (!fileList) return;
    const { escapeHtml, normalizeAttachment, translate } = normalizeDeps(deps);
    const normalizedFiles = (files || []).map(normalizeAttachment).filter((item) => item && item.name);
    fileList.innerHTML = normalizedFiles.length
      ? normalizedFiles.map((file) => `<span>${escapeHtml(file.name)}<em>${escapeHtml(file.type || translate("intakeFileUnknown"))}</em></span>`).join("")
      : escapeHtml(translate("intakeNoFiles"));
  }

  function setMaterialIntakeStatus(status = null, message = "") {
    if (status) status.textContent = message;
  }

  function materialIntakeFormNodes(form) {
    return {
      dropzone: form.querySelector("[data-intake-dropzone]"),
      fileInput: form.querySelector("[data-intake-files]"),
      fileList: form.querySelector("[data-intake-file-list]"),
      status: form.querySelector("[data-intake-status]"),
      targetInput: form.querySelector('[name="target_hint"]'),
      typeSelect: form.querySelector("[data-intake-type]"),
    };
  }

  function bindMaterialIntakePanelEvents(root, callbacks = {}, deps = {}) {
    if (!root) return;
    const {
      onFilesChange = ({ files }) => files,
      onGetFiles = () => [],
      onProcessInbox = () => {},
      onSubmit = () => {},
      onTypeChange = () => "",
      onWithdraw = () => {},
    } = callbacks;

    root.querySelectorAll("[data-material-intake-form]").forEach((form) => {
      const nodes = materialIntakeFormNodes(form);
      const renderFiles = (files = onGetFiles({ form, ...nodes }) || []) => {
        renderIntakeFileList(nodes.fileList, files, deps);
      };

      nodes.typeSelect?.addEventListener("change", () => {
        const nextTarget = onTypeChange({
          form,
          targetInput: nodes.targetInput,
          typeSelect: nodes.typeSelect,
          value: nodes.typeSelect.value || "paper",
        });
        if (nodes.targetInput && typeof nextTarget === "string") {
          nodes.targetInput.value = nextTarget;
        }
      });
      nodes.fileInput?.addEventListener("change", () => {
        const files = Array.from(nodes.fileInput.files || []);
        const nextFiles = onFilesChange({ files, form, source: "input", ...nodes }) || files;
        renderFiles(nextFiles);
      });
      nodes.dropzone?.addEventListener("dragover", (event) => {
        event.preventDefault();
        nodes.dropzone.classList.add("drag-over");
      });
      nodes.dropzone?.addEventListener("dragleave", () => {
        nodes.dropzone.classList.remove("drag-over");
      });
      nodes.dropzone?.addEventListener("drop", (event) => {
        event.preventDefault();
        nodes.dropzone.classList.remove("drag-over");
        const files = Array.from(event.dataTransfer?.files || []);
        const nextFiles = onFilesChange({ files, form, source: "drop", ...nodes }) || files;
        renderFiles(nextFiles);
      });
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        await onSubmit({
          event,
          form,
          renderFiles,
          resetForm: (target = "") => {
            form.reset();
            if (nodes.targetInput && typeof target === "string") nodes.targetInput.value = target;
            renderFiles([]);
          },
          ...nodes,
        });
      });
      renderFiles();
    });

    bindAll(root, "[data-withdraw-intake]", "click", (event, button) => {
      onWithdraw({ event, button, id: button.dataset.withdrawIntake || "" });
    });
    bindAll(root, "[data-process-intake-inbox]", "click", (event, button) => {
      onProcessInbox({ event, button });
    });
  }

  global.ResearchOSMaterialIntakeWorkbenchService = Object.freeze({
    bindMaterialIntakePanelEvents,
    setMaterialIntakeStatus,
  });
})(window);
