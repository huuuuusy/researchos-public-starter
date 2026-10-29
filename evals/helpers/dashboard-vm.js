/* Shared loader for Dashboard behaviour tests: run classic scripts under node:vm with a minimal DOM shim.
 *
 *   const { loadModules, element, frozenDate } = require("./helpers/dashboard-vm.js");
 *   const context = loadModules(["dashboard/src/core/ui.js", ...], { ResearchOSInteractions: { bindAll() {} } });
 *
 * Paths are repository-relative. `globals` are copied onto the context before any script runs;
 * `window`, `globalThis`, `console`, `URLSearchParams` and a `document` shim are provided unless overridden.
 * Running this file directly self-checks the shim.
 */
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..", "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

function classList(node) {
  const names = () => new Set(String(node.className || "").split(/\s+/).filter(Boolean));
  const write = (set) => { node.className = [...set].join(" "); };
  return {
    add: (...values) => { const set = names(); values.forEach((value) => set.add(value)); write(set); },
    remove: (...values) => { const set = names(); values.forEach((value) => set.delete(value)); write(set); },
    contains: (value) => names().has(value),
    toggle(value, force) { const on = force === undefined ? !this.contains(value) : Boolean(force); on ? this.add(value) : this.remove(value); return on; },
  };
}

const camel = (name) => name.replace(/^data-/, "").replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
function matches(node, selector) {
  return String(selector).split(",").some((part) => {
    const [, tag = "", id = "", cls = "", attr = "", value] = part.trim().match(/^([a-z]*)(?:#([\w-]+))?((?:\.[\w-]+)*)(?:\[([\w-]+)(?:="([^"]*)")?\])?$/i) || [];
    if (!tag && !id && !cls && !attr) return false;
    if (tag && node.tagName !== tag.toUpperCase()) return false;
    if (id && node.id !== id) return false;
    if (cls && !cls.split(".").filter(Boolean).every((name) => node.classList.contains(name))) return false;
    if (attr && (value === undefined ? node.getAttribute(attr) === null : node.getAttribute(attr) !== value)) return false;
    return true;
  });
}

/** A detached element: attributes, dataset, classList, children, listeners and simple selectors. */
function element(tag = "div", { id = "", className = "", dataset = {}, attributes = {}, children = [] } = {}) {
  const listeners = {};
  const attrs = { ...attributes };
  const node = {
    tagName: String(tag).toUpperCase(), id, className, dataset: { ...dataset }, children: [], parentNode: null,
    hidden: false, disabled: false, textContent: "", innerHTML: "", value: "", style: {},
    get classList() { return classList(node); },
    setAttribute(name, value) { if (name === "id") node.id = String(value); else if (name === "class") node.className = String(value); else if (name.startsWith("data-")) node.dataset[camel(name)] = String(value); else attrs[name] = String(value); },
    getAttribute(name) { if (name === "id") return node.id || null; if (name === "class") return node.className || null; if (name.startsWith("data-")) return node.dataset[camel(name)] ?? null; return attrs[name] ?? null; },
    removeAttribute(name) { if (name.startsWith("data-")) delete node.dataset[camel(name)]; else delete attrs[name]; },
    hasAttribute(name) { return node.getAttribute(name) !== null; },
    append(...items) { items.forEach((item) => { if (item && typeof item === "object") { item.parentNode = node; node.children.push(item); } else node.textContent += String(item ?? ""); }); },
    appendChild(item) { node.append(item); return item; },
    replaceChildren(...items) { node.children = []; node.textContent = ""; node.append(...items); },
    remove() { if (node.parentNode) node.parentNode.children = node.parentNode.children.filter((child) => child !== node); node.parentNode = null; },
    addEventListener(type, callback) { (listeners[type] ||= []).push(callback); },
    removeEventListener(type, callback) { listeners[type] = (listeners[type] || []).filter((entry) => entry !== callback); },
    dispatchEvent(event) { const value = { target: node, currentTarget: node, preventDefault() { value.defaultPrevented = true; }, stopPropagation() {}, ...event }; (listeners[value.type] || []).forEach((callback) => callback(value)); return !value.defaultPrevented; },
    click() { return node.dispatchEvent({ type: "click" }); },
    focus() {}, blur() {}, scrollIntoView() {},
    contains(other) { return other === node || node.children.some((child) => child.contains(other)); },
    closest(selector) { for (let current = node; current; current = current.parentNode) if (matches(current, selector)) return current; return null; },
    querySelectorAll(selector) { return node.children.flatMap((child) => [...(matches(child, selector) ? [child] : []), ...child.querySelectorAll(selector)]); },
    querySelector(selector) { return node.querySelectorAll(selector)[0] || null; },
    getElementById(value) { return node.querySelectorAll(`#${value}`)[0] || null; },
    listeners,
  };
  children.forEach((child) => node.append(child));
  return node;
}

/** A Date subclass whose argument-less constructor returns `iso`. */
function frozenDate(iso) {
  const Native = Date;
  class FrozenDate extends Native { constructor(...args) { super(...(args.length ? args : [iso])); } static now() { return new Native(iso).getTime(); } }
  FrozenDate.parse = Native.parse;
  FrozenDate.UTC = Native.UTC;
  return FrozenDate;
}

/** Run `paths` in one fresh vm context and return it; scripts register their globals on it. */
function loadModules(paths = [], globals = {}) {
  const body = element("body");
  const documentElement = element("html", { attributes: { lang: "en" } });
  documentElement.lang = "en";
  const document = Object.assign(element("#document"), {
    body, documentElement, readyState: "complete", activeElement: null,
    createElement: (tag) => element(tag),
    createTextNode: (value) => String(value ?? ""),
    createDocumentFragment: () => element("#fragment"),
    getElementById: (value) => body.getElementById(value),
    querySelector: (selector) => body.querySelector(selector),
    querySelectorAll: (selector) => body.querySelectorAll(selector),
  });
  const context = { console, URLSearchParams, URL, setTimeout, clearTimeout, document, location: { search: "", pathname: "/", hash: "" }, ...globals };
  context.window = context;
  context.globalThis = context;
  vm.createContext(context);
  for (const relative of paths) vm.runInContext(read(relative), context, { filename: relative });
  return context;
}

module.exports = { element, frozenDate, loadModules, read, root };

if (require.main === module) {
  const assert = require("node:assert/strict");
  const button = element("button", { className: "primary", dataset: { action: "go" } });
  const host = element("section", { id: "host", children: [button] });
  assert.equal(host.querySelector('[data-action="go"]'), button);
  assert.equal(button.closest("#host"), host);
  button.classList.add("is-active");
  assert.ok(button.classList.contains("is-active") && button.classList.contains("primary"));
  let clicks = 0;
  button.addEventListener("click", () => { clicks += 1; });
  button.click();
  assert.equal(clicks, 1);
  const context = loadModules([], { Date: frozenDate("2026-01-02T03:04:05Z") });
  context.document.body.append(host);
  assert.equal(context.document.getElementById("host"), host);
  assert.equal(new context.Date().toISOString(), "2026-01-02T03:04:05.000Z");
  console.log("dashboard-vm helper self-check passed.");
}
