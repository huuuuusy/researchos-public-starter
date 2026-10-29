/* ResearchOS maintenance header.
 * 中文：校验 dashboard 文案目录：中英键集与占位符一致、键名合法、英文值无中文，代码里字面写出的文案键都能查到。
 * English: Checks the dashboard copy catalogs: matching zh-CN/en keys and placeholders, legal key names,
 * no CJK in English values, and every literally referenced copy key resolves in some catalog.
 */

"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const dashboard = path.resolve(__dirname, "..", "dashboard");
// ui-copy-profile.js holds the entries whose wording differs between the editions; it loads first, as in index.html.
const CATALOG_FILES = [
  "src/core/ui-copy-profile.js",
  "src/core/i18n.js",
  "src/core/ui-copy-work-session.js",
  "src/core/ui-copy.js",
  "src/plugins/research-portfolio-copy.js",
];

const context = { window: {} };
context.global = context.window;
vm.createContext(context);
for (const relative of CATALOG_FILES) {
  vm.runInContext(fs.readFileSync(path.join(dashboard, relative), "utf8"), context, { filename: relative });
}
const loaded = context.window;
const catalogs = {
  i18n: loaded.ResearchOSI18N,
  simpleText: loaded.ResearchOSUICopy?.simpleText,
  workSession: loaded.ResearchOSUICopyWorkSession?.simpleText,
  portfolio: loaded.ResearchOSResearchPortfolioCopy?.catalog,
};
// The copy profile's t-path overrides; app.js t() reads them before i18n.js.
catalogs.i18nOverrides = loaded.ResearchOSUICopy?.i18nOverrides;

const KEY_NAME = /^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*$/;
const CJK = /[　-〿㐀-䶿一-鿿豈-﫿＀-￯]/;
const placeholders = (value) => [...new Set(String(value).match(/\{[A-Za-z_][A-Za-z0-9_]*\}/g) || [])].sort().join(",");

const failures = [];
const allKeys = new Set();
// Keys of the catalogs that can still be edited; the Portfolio catalog lives in a frozen plugin file.
const editableKeys = new Set();
for (const [name, catalog] of Object.entries(catalogs)) {
  assert.ok(catalog && catalog["zh-CN"] && catalog.en, `${name}: catalog did not load`);
  const zh = catalog["zh-CN"];
  const en = catalog.en;
  for (const key of new Set([...Object.keys(zh), ...Object.keys(en)])) {
    if (!KEY_NAME.test(key)) failures.push(`${name}: illegal key name ${JSON.stringify(key)}`);
  }
  for (const key of Object.keys(zh)) if (!(key in en)) failures.push(`${name}: ${key} has zh-CN but no en`);
  for (const key of Object.keys(en)) {
    allKeys.add(key);
    if (name !== "portfolio") editableKeys.add(key);
    if (!(key in zh)) { failures.push(`${name}: ${key} has en but no zh-CN`); continue; }
    if (typeof en[key] !== "string" || typeof zh[key] !== "string") { failures.push(`${name}: ${key} is not a string in both languages`); continue; }
    if (placeholders(en[key]) !== placeholders(zh[key])) failures.push(`${name}: ${key} placeholders differ (${placeholders(zh[key])} vs ${placeholders(en[key])})`);
    if (CJK.test(en[key])) failures.push(`${name}: ${key} English value contains CJK text`);
  }
}

// i18n.js (read through t) and the ui-copy catalogs (read through simpleText) never share a key:
// a shared key would be edited in one place while the other lookup path keeps showing the old text.
for (const key of Object.keys(catalogs.i18n.en)) {
  if (key in catalogs.simpleText.en) failures.push(`i18n and simpleText both define ${key}; keep it only in the catalog its lookup reads`);
}

// Minimal JavaScript lexer: strings, template literals (with substitutions as
// virtual parentheses), regex literals, identifiers and punctuation. It exists so
// that key literals inside comments, regexes and nested templates are classified
// correctly instead of by a single regular expression.
function lex(source) {
  const tokens = [];
  const templateDepths = [];
  let braceDepth = 0;
  let index = 0;
  const regexAllowed = () => {
    const previous = tokens[tokens.length - 1];
    if (!previous) return true;
    if (previous.type === "punct") return !")]}".includes(previous.value);
    if (previous.type === "ident") return ["return", "typeof", "case", "in", "of", "void", "delete", "throw", "else", "do"].includes(previous.value);
    return false;
  };
  const readTemplate = () => {
    let text = "";
    while (index < source.length) {
      const char = source[index];
      if (char === "\\") { text += source.slice(index, index + 2); index += 2; continue; }
      if (char === "`") { index += 1; return { text, closed: true }; }
      if (char === "$" && source[index + 1] === "{") { index += 2; return { text, closed: false }; }
      text += char;
      index += 1;
    }
    return { text, closed: true };
  };
  while (index < source.length) {
    const char = source[index];
    if (/\s/.test(char)) { index += 1; continue; }
    if (char === "/" && source[index + 1] === "/") { const end = source.indexOf("\n", index); index = end < 0 ? source.length : end; continue; }
    if (char === "/" && source[index + 1] === "*") { const end = source.indexOf("*/", index + 2); index = end < 0 ? source.length : end + 2; continue; }
    if (char === "\"" || char === "'") {
      let cursor = index + 1;
      let value = "";
      while (cursor < source.length && source[cursor] !== char) {
        if (source[cursor] === "\\") { value += source[cursor + 1]; cursor += 2; continue; }
        value += source[cursor];
        cursor += 1;
      }
      tokens.push({ type: "str", value });
      index = cursor + 1;
      continue;
    }
    if (char === "`") {
      index += 1;
      const part = readTemplate();
      if (part.closed) tokens.push({ type: "str", value: part.text });
      else {
        tokens.push({ type: "tmpl", prefix: part.text }, { type: "punct", value: "(" });
        templateDepths.push(braceDepth);
        braceDepth = 0;
      }
      continue;
    }
    if (char === "}" && templateDepths.length && braceDepth === 0) {
      tokens.push({ type: "punct", value: ")" });
      index += 1;
      const part = readTemplate();
      tokens.push({ type: "quasi", value: part.text });
      if (part.closed) braceDepth = templateDepths.pop();
      else tokens.push({ type: "punct", value: "(" });
      continue;
    }
    if (char === "/" && regexAllowed()) {
      let cursor = index + 1;
      let inClass = false;
      while (cursor < source.length && (inClass || source[cursor] !== "/")) {
        if (source[cursor] === "\\") cursor += 1;
        else if (source[cursor] === "[") inClass = true;
        else if (source[cursor] === "]") inClass = false;
        cursor += 1;
      }
      index = cursor + 1;
      while (/[a-z]/.test(source[index] || "")) index += 1;
      tokens.push({ type: "regex" });
      continue;
    }
    const word = /^[A-Za-z_$][\w$]*/.exec(source.slice(index, index + 200));
    if (word) { tokens.push({ type: "ident", value: word[0] }); index += word[0].length; continue; }
    if (char === "{") braceDepth += 1;
    if (char === "}") braceDepth -= 1;
    tokens.push({ type: "punct", value: char });
    index += 1;
  }
  return tokens;
}

// Functions whose string arguments are copy keys. They all end in a catalog lookup
// (t, simpleText, the plugin `translate`/`text`, the desk `uiText`, or helpers that
// forward their key argument to one of those).
const LOOKUPS = new Set([
  "t", "simpleText", "simpleTextForLanguage", "translate", "translateFor", "translateText", "sectionTranslate",
  "translated", "translatedTemplate", "uiText", "text", "textFrom", "showStatus",
]);
// A copy-key-shaped literal: lowerCamel with at least one capital, or a dotted key.
const KEY_SHAPE = /^(?:[a-z][a-z0-9]*(?:[A-Z][A-Za-z0-9]*)+(?:_[A-Za-z0-9_]+)?|[a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9_]+)+)$/;

function closing(tokens, start) {
  let depth = 0;
  for (let cursor = start; cursor < tokens.length; cursor += 1) {
    const token = tokens[cursor];
    if (token.type !== "punct") continue;
    if ("([{".includes(token.value)) depth += 1;
    if (")]}".includes(token.value)) { depth -= 1; if (depth === 0) return cursor; }
  }
  return tokens.length - 1;
}

const FRAGMENT = /^[A-Za-z0-9_.]{3,}$/;

function references(tokens) {
  const keys = [];
  const prefixes = [];
  const fragments = { namespaces: [], prefixes: [], suffixes: [] };
  for (let cursor = 0; cursor < tokens.length; cursor += 1) {
    const token = tokens[cursor];
    const next = tokens[cursor + 1];
    // Static pieces from which any template or string concatenation could build a key.
    if (token.type === "tmpl" && FRAGMENT.test(token.prefix)) fragments.prefixes.push(token.prefix);
    if (token.type === "quasi" && FRAGMENT.test(token.value)) fragments.suffixes.push(token.value);
    if (token.type === "str" && next?.value === "+" && FRAGMENT.test(token.value)) fragments.prefixes.push(token.value);
    if (token.value === "+" && next?.type === "str" && FRAGMENT.test(next.value)) fragments.suffixes.push(next.value);
    // A namespace handed to a helper that builds `${namespace}.${value}` (external-evidence, preview-links).
    if (token.type === "str" && FRAGMENT.test(token.value)) fragments.namespaces.push(token.value);
    // lookup("key"), lookup(flag ? "a" : "b"), textFrom(context, "key"), lookup(`prefix.${part}`)
    if (token.type === "ident" && LOOKUPS.has(token.value) && next?.value === "(" && tokens[cursor - 1]?.value !== "function") {
      const end = closing(tokens, cursor + 1);
      for (const inner of tokens.slice(cursor + 2, end)) {
        if (inner.type === "str" && KEY_SHAPE.test(inner.value)) keys.push(inner.value);
        // translated() returns its explicit fallback for a missing key, so its dynamic keys may be absent.
        if (inner.type === "tmpl" && token.value !== "translated" && /^[a-z][A-Za-z0-9_.]+$/.test(inner.prefix)) prefixes.push(inner.prefix);
      }
    }
    // Indexed key maps: { state: "someCopyKey", ... }[value] || "fallbackKey"
    if (token.value === "{" && token.type === "punct") {
      const end = closing(tokens, cursor);
      const body = tokens.slice(cursor + 1, end);
      const isMap = body.length >= 3 && body.every((inner, position) => {
        const slot = position % 4;
        if (slot === 0) return inner.type === "ident" || inner.type === "str";
        if (slot === 1) return inner.value === ":";
        if (slot === 2) return inner.type === "str";
        return inner.value === ",";
      });
      if (isMap && tokens[end + 1]?.value === "[") {
        body.filter((_, position) => position % 4 === 2).forEach((inner) => KEY_SHAPE.test(inner.value) && keys.push(inner.value));
        const after = closing(tokens, end + 1);
        const fallback = tokens[after + 3];
        if (tokens[after + 1]?.value === "|" && tokens[after + 2]?.value === "|" && fallback?.type === "str" && KEY_SHAPE.test(fallback.value)) keys.push(fallback.value);
      }
    }
  }
  return { keys, prefixes, fragments };
}

function sourceFiles(directory, pattern = /\.(?:js|html)$/) {
  if (!fs.existsSync(directory)) return [];
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) return ["data", "__pycache__", "node_modules"].includes(entry.name) ? [] : sourceFiles(full, pattern);
    return pattern.test(entry.name) ? [full] : [];
  });
}

const catalogPaths = new Set(CATALOG_FILES.map((relative) => path.join(dashboard, relative)));
let referenceCount = 0;
const mentions = [];
const dynamicPrefixes = new Set();
const dynamicSuffixes = new Set();
for (const file of sourceFiles(dashboard)) {
  if (catalogPaths.has(file)) continue;
  const source = fs.readFileSync(file, "utf8");
  mentions.push(source);
  const relative = path.relative(dashboard, file);
  const keys = [...source.matchAll(/data-i18n(?:-aria-label|-title)?="([^"$]+)"/g)].map((match) => match[1]);
  const prefixes = [];
  if (file.endsWith(".js")) {
    const found = references(lex(source));
    keys.push(...found.keys);
    prefixes.push(...found.prefixes);
    found.fragments.prefixes.forEach((prefix) => dynamicPrefixes.add(prefix));
    found.fragments.suffixes.forEach((suffix) => dynamicSuffixes.add(suffix));
    found.fragments.namespaces.forEach((namespace) => { dynamicPrefixes.add(`${namespace}.`); dynamicPrefixes.add(`${namespace}_`); });
  }
  for (const key of keys) {
    referenceCount += 1;
    if (!allKeys.has(key)) failures.push(`${relative}: copy key ${key} is not defined in any catalog`);
  }
  for (const prefix of prefixes) {
    if (![...allKeys].some((key) => key.startsWith(prefix))) failures.push(`${relative}: no copy key starts with the dynamic prefix ${prefix}`);
  }
}

// Every key must stay reachable: its name is mentioned in non-catalog dashboard code or in
// scripts/, config/, 09_templates/ or evals/ (a builder or server may emit it), a dashboard
// template, string concatenation or Python f-string can build it from a static prefix or suffix,
// or a test or validator pins part of its wording. A key that fails all of these is dead and
// should be deleted from both languages.
const repository = path.resolve(dashboard, "..");
const pinnedTexts = new Set();
for (const [directory, pattern] of [["scripts", /\.(?:py|js|mjs|json)$/], ["config", /\.(?:json|ya?ml)$/], ["09_templates", /\.json$/], ["evals", /\.(?:py|js)$/]]) {
  for (const file of sourceFiles(path.join(repository, directory), pattern)) {
    if (file === __filename) continue;
    const source = fs.readFileSync(file, "utf8");
    mentions.push(source);
    for (const match of source.matchAll(/\bf["']([A-Za-z][A-Za-z0-9_.]{2,})\{/g)) dynamicPrefixes.add(match[1]);
    if (directory === "evals" || file.endsWith(".py")) {
      for (const match of source.matchAll(/"((?:[^"\\\n]|\\.){6,})"|'((?:[^'\\\n]|\\.){6,})'/g)) {
        const literal = (match[1] || match[2]).replace(/\\(["'])/g, "$1");
        if (/[^\x00-\x7f]|\s/.test(literal)) pinnedTexts.add(literal);
      }
    }
  }
}
const corpus = mentions.join("\n");
const pinnedList = [...pinnedTexts];
for (const key of editableKeys) {
  if (corpus.includes(key)) continue;
  if ([...dynamicPrefixes].some((prefix) => key.startsWith(prefix))) continue;
  if ([...dynamicSuffixes].some((suffix) => key.endsWith(suffix))) continue;
  const values = Object.values(catalogs).flatMap((catalog) => [catalog["zh-CN"]?.[key], catalog.en?.[key]]).filter((value) => typeof value === "string");
  if (values.some((value) => pinnedList.some((text) => value.includes(text)))) continue;
  failures.push(`unreferenced copy key ${key}: no code mentions it and no dynamic prefix or suffix can build it`);
}

assert.ok(referenceCount > 1000, `expected the literal copy-key scan to find the dashboard references, found ${referenceCount}`);
const uniqueFailures = [...new Set(failures)];
if (uniqueFailures.length) console.error(uniqueFailures.join("\n"));
assert.equal(uniqueFailures.length, 0, `${uniqueFailures.length} copy catalog failure(s); see the list above`);
console.log(`dashboard copy catalog checks passed (${allKeys.size} keys, ${referenceCount} literal references)`);
