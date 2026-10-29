/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 前端服务「preview markdown」；承接可复用逻辑，避免 app.js 重新变成大杂烩。
 * English: Frontend service for preview markdown in the ResearchOS dashboard; owns reusable logic so app.js stays from becoming a catch-all again.
 */

(function attachResearchOSPreviewMarkdownService(global) {
  function rendererOptions(options = {}) {
    const previewService = global.ResearchOSPreviewService || {};
    return {
      escapeHtml: typeof options.escapeHtml === "function" ? options.escapeHtml : global.ResearchOSUiCore?.escapeHtml,
      resolveDocument: typeof options.resolveDocument === "function" ? options.resolveDocument : () => null,
      resolvePreviewLink: typeof options.resolvePreviewLink === "function"
        ? options.resolvePreviewLink
        : (basePath, href, linkOptions = {}) => (
            typeof previewService.resolvePreviewLink === "function"
              ? previewService.resolvePreviewLink(basePath, href, linkOptions)
              : null
          ),
    };
  }

  function slugifyMarkdownHeading(text) {
    return String(text || "")
      .trim()
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s-]/gu, "")
      .replace(/\s+/g, "-")
      .slice(0, 80);
  }

  function inlineLinkLabelToHtml(text = "", escapeHtml = global.ResearchOSUiCore?.escapeHtml) {
    const codeFragments = [];
    let value = escapeHtml(String(text || "")).replace(/`([^`]+)`/g, (_, code) => {
      const token = `\u0000label-code-${codeFragments.length}\u0000`;
      codeFragments.push(`<code>${code}</code>`);
      return token;
    });
    value = value
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/__([^_]+)__/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>");
    codeFragments.forEach((html, index) => {
      value = value.replaceAll(`\u0000label-code-${index}\u0000`, html);
    });
    return value;
  }

  function inlineMarkdownToHtml(text, basePath = "", options = {}) {
    const { escapeHtml, resolveDocument, resolvePreviewLink } = rendererOptions(options);
    const placeholders = [];
    const reserve = (html) => {
      const token = `\u0000${placeholders.length}\u0000`;
      placeholders.push(html);
      return token;
    };
    const sourceTokenPattern = /^(?:(?:0[0-9]|1[0-9])_[A-Za-z0-9_./-]+\/?|corpus\/[A-Za-z0-9_./-]*|[A-Za-z0-9_./-]+\.(?:md|pdf|json|yml|yaml))$/i;
    const relativeSourceTokenPattern = /^(?:\.{1,2}\/)+[A-Za-z0-9_./-]+\.(?:md|pdf|json|yml|yaml)$/i;
    const sourceTokenLabel = (token = "") => {
      const clean = String(token || "").trim().replace(/\/+$/, "");
      if (!clean) return "";
      const parts = clean.split("/").filter(Boolean);
      return parts[parts.length - 1] || clean;
    };
    const readableSourceLabel = (token = "") => {
      const base = sourceTokenLabel(token);
      if (!base) return "";
      const withoutExtension = base.replace(/\.(md|pdf|json|ya?ml)$/i, "");
      return withoutExtension
        .replace(/[_-]+/g, " ")
        .replace(/\s+/g, " ")
        .trim();
    };
    const sourceTokenTarget = (token = "") => {
      const raw = String(token || "").trim();
      const clean = raw.replace(/\/+$/, "");
      if (!clean || raw === "corpus" || raw.startsWith("corpus/")) return null;
      if (
        clean.toLowerCase().endsWith(".pdf") &&
        !clean.startsWith("/") &&
        !clean.split("/").includes("..")
      ) {
        return { pdf: true, path: clean, anchor: "" };
      }
      const directDoc = clean.toLowerCase().endsWith(".md") ? resolveDocument(clean) : null;
      if (directDoc) return { path: clean, anchor: "" };
      return resolvePreviewLink(basePath, clean, { resolveDocument });
    };
    const sourceTokenDisplayLabel = (token = "", link = null) => {
      const doc = link?.path ? resolveDocument(link.path) : null;
      return doc?.title || doc?.name || readableSourceLabel(token) || sourceTokenLabel(token);
    };
    const sourceLinkHtml = ({
      anchor = "",
      label = "",
      linkPath = "",
      pdf = false,
      token = "",
    } = {}) => {
      const cleanToken = String(token || label || linkPath || "").trim();
      const safeLabel = sourceTokenDisplayLabel(label || token || linkPath, { path: linkPath, pdf });
      if (pdf) {
        return `<button type="button" class="md-source-link pdf-inline-preview" data-action-kind="navigation" data-source-token="${escapeHtml(cleanToken)}" data-pdf-preview-path="${escapeHtml(linkPath)}" title="${escapeHtml(cleanToken)}">${escapeHtml(safeLabel)}</button>`;
      }
      if (linkPath) {
        const anchorAttr = anchor ? ` data-preview-anchor="${escapeHtml(anchor)}"` : "";
        return `<a href="#" class="md-source-link" data-action-kind="navigation" data-source-token="${escapeHtml(cleanToken)}" data-preview-path="${escapeHtml(linkPath)}"${anchorAttr} title="${escapeHtml(cleanToken)}">${escapeHtml(safeLabel)}</a>`;
      }
      return `<code class="md-source-token" data-source-token="${escapeHtml(cleanToken)}" title="${escapeHtml(cleanToken)}">${escapeHtml(safeLabel)}</code>`;
    };
    const sourceTokenLinkHtml = (token = "") => {
      const clean = String(token || "").trim();
      const link = sourceTokenTarget(clean);
      const label = sourceTokenDisplayLabel(clean, link);
      if (link?.pdf) {
        return sourceLinkHtml({ label, linkPath: link.path, pdf: true, token: clean });
      }
      if (link?.path) {
        return sourceLinkHtml({ anchor: link.anchor || "", label, linkPath: link.path, token: clean });
      }
      return sourceLinkHtml({ label, token: clean });
    };
    let value = String(text || "");
    value = value.replace(/`([^`]+)`/g, (_, code) => (
      sourceTokenPattern.test(String(code || "").trim()) || relativeSourceTokenPattern.test(String(code || "").trim())
        ? reserve(sourceTokenLinkHtml(String(code || "").trim()))
        : reserve(`<code>${escapeHtml(code)}</code>`)
    ));
    value = value.replace(/\[([^\]]+)\]\(\s*(?:<([^>]+)>|((?:[^()\s]+|\([^)]*\))+)(?:\s+["'][^"']*["'])?)\s*\)/g, (_, label, angleHref, plainHref) => {
      const href = angleHref || plainHref || "";
      const link = resolvePreviewLink(basePath, href, { resolveDocument });
      const cleanLabel = String(label || "").trim();
      const labelIsSourceToken = sourceTokenPattern.test(cleanLabel) || relativeSourceTokenPattern.test(cleanLabel);
      const labelText = labelIsSourceToken ? sourceTokenDisplayLabel(cleanLabel, link) : cleanLabel;
      if (link?.pdf && labelIsSourceToken) {
        return reserve(sourceLinkHtml({ label: labelText, linkPath: link.path, pdf: true, token: cleanLabel }));
      }
      if (link?.path && labelIsSourceToken) {
        return reserve(sourceLinkHtml({ anchor: link.anchor || "", label: labelText, linkPath: link.path, token: cleanLabel }));
      }
      // Link labels may contain a filename. Render their inline emphasis without
      // auto-linking that filename again, which would create invalid nested links.
      const safeLabel = inlineLinkLabelToHtml(label, escapeHtml);
      if (link?.external) {
        return reserve(`<a href="${escapeHtml(link.href)}" data-action-kind="navigation" target="_blank" rel="noreferrer">${safeLabel}</a>`);
      }
      if (link?.pdf) {
        return reserve(`<button type="button" class="inline-preview-button pdf-inline-preview" data-action-kind="navigation" data-pdf-preview-path="${escapeHtml(link.path)}">${safeLabel}</button>`);
      }
      if (link?.path) {
        const anchor = link.anchor ? ` data-preview-anchor="${escapeHtml(link.anchor)}"` : "";
        return reserve(`<a href="#" data-action-kind="navigation" data-preview-path="${escapeHtml(link.path)}"${anchor}>${safeLabel}</a>`);
      }
      return reserve(`<span class="md-unresolved-link">${safeLabel}</span>`);
    });
    value = value.replace(
      /(^|[\s（(：:])((?:0[0-9]|1[0-9])_[A-Za-z0-9_./-]+\/?|corpus\/[A-Za-z0-9_./-]*|[A-Za-z0-9_./-]+\.(?:md|pdf|json|yml|yaml))(?![A-Za-z0-9_/-])/gi,
      (match, prefix, token) => `${prefix}${reserve(sourceTokenLinkHtml(token))}`
    );
    value = escapeHtml(value)
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/__([^_]+)__/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>");
    placeholders.forEach((html, index) => {
      value = value.replaceAll(`\u0000${index}\u0000`, html);
    });
    return value;
  }

  function markdownToHtml(markdown, basePath = "", options = {}) {
    const { escapeHtml, resolveDocument, resolvePreviewLink } = rendererOptions(options);
    const lines = String(markdown || "").replace(/\r\n/g, "\n").split("\n");
    const html = [];
    let inCode = false;
    let listTag = "";
    let inTable = false;
    let inFrontmatter = false;

    const closeList = () => {
      if (listTag) {
        html.push(`</${listTag}>`);
        listTag = "";
      }
    };
    const closeTable = () => {
      if (inTable) {
        html.push("</tbody></table>");
        inTable = false;
      }
    };
    const inline = (value) => inlineMarkdownToHtml(value, basePath, {
      escapeHtml,
      resolveDocument,
      resolvePreviewLink,
    });

    lines.forEach((line, index) => {
      if (index === 0 && line.trim() === "---") {
        inFrontmatter = true;
        html.push('<details class="md-frontmatter"><summary>Frontmatter</summary>');
        return;
      }
      if (inFrontmatter && line.trim() === "---") {
        inFrontmatter = false;
        html.push("</details>");
        return;
      }
      if (line.trim().startsWith("```")) {
        closeList();
        closeTable();
        html.push(inCode ? "</code></pre>" : "<pre><code>");
        inCode = !inCode;
        return;
      }
      if (inCode) {
        html.push(`${escapeHtml(line)}\n`);
        return;
      }
      const trimmed = line.trim();
      if (!trimmed) {
        closeList();
        closeTable();
        return;
      }
      if (inFrontmatter) {
        html.push(`<div>${inline(line)}</div>`);
        return;
      }
      // A line of purely presentational HTML (a README's language switch, say) shows its text, not the tags.
      // Anything else, a <script> above all, falls through and stays visible as escaped text.
      const tags = trimmed.startsWith("<") ? [...trimmed.matchAll(/<\/?([a-z][a-z0-9]*)\b[^>]*>/gi)].map((match) => match[1]) : [];
      if (tags.length && tags.every((tag) => /^(?:p|div|span|strong|b|em|i|a|br|img|picture|source|sub|sup|center)$/i.test(tag))) {
        const textOnly = trimmed.replace(/<[^>]*>/g, "").trim();
        if (!textOnly) return;
        closeList();
        closeTable();
        html.push(`<p>${escapeHtml(textOnly)}</p>`);
        return;
      }
      const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
      if (heading) {
        closeList();
        closeTable();
        const level = heading[1].length;
        const title = heading[2];
        html.push(`<h${level} id="${escapeHtml(slugifyMarkdownHeading(title))}">${inline(title)}</h${level}>`);
        return;
      }
      if (trimmed === "---" || trimmed === "***") {
        closeList();
        closeTable();
        html.push("<hr>");
        return;
      }
      if (trimmed.startsWith("> ")) {
        closeList();
        closeTable();
        html.push(`<blockquote>${inline(trimmed.slice(2))}</blockquote>`);
        return;
      }
      if (/^\|.+\|$/.test(trimmed)) {
        closeList();
        const cells = trimmed
          .slice(1, -1)
          .split("|")
          .map((cell) => cell.trim());
        const next = String(lines[index + 1] || "").trim();
        const nextCells = /^\|.+\|$/.test(next)
          ? next.slice(1, -1).split("|").map((cell) => cell.trim())
          : [];
        const nextIsSeparator = nextCells.length === cells.length
          && nextCells.every((cell) => /^:?-{3,}:?$/.test(cell));
        if (nextIsSeparator) {
          closeTable();
          html.push(`<table><thead><tr>${cells.map((cell) => `<th scope="col">${inline(cell)}</th>`).join("")}</tr></thead><tbody>`);
          inTable = true;
          return;
        }
        if (cells.every((cell) => /^:?-{3,}:?$/.test(cell))) return;
        if (!inTable) {
          html.push("<table><tbody>");
          inTable = true;
        }
        html.push(`<tr>${cells.map((cell) => `<td>${inline(cell)}</td>`).join("")}</tr>`);
        return;
      }
      const bullet = trimmed.match(/^[-*+]\s+(.+)$/);
      const ordered = trimmed.match(/^\d+[.)]\s+(.+)$/);
      if (bullet || ordered) {
        closeTable();
        const desiredTag = ordered ? "ol" : "ul";
        if (listTag && listTag !== desiredTag) closeList();
        if (!listTag) {
          html.push(`<${desiredTag}>`);
          listTag = desiredTag;
        }
        html.push(`<li>${inline((bullet || ordered)[1])}</li>`);
        return;
      }
      closeList();
      closeTable();
      html.push(`<p>${inline(line)}</p>`);
    });
    closeList();
    closeTable();
    if (inCode) html.push("</code></pre>");
    if (inFrontmatter) html.push("</details>");
    return html.join("");
  }

  global.ResearchOSPreviewMarkdownService = Object.freeze({
    slugifyMarkdownHeading,
    inlineMarkdownToHtml,
    markdownToHtml,
  });
})(typeof window !== "undefined" ? window : globalThis);
