/* Library card workbench: the real view renders the card boxes, a small local HTML reader turns that output into the
 * dashboard-vm element shim, and the real workbench service then drives selection, the composition basket and search.
 */
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { element, loadModules, root: repositoryRoot } = require("./helpers/dashboard-vm.js");

// Local shim additions the workbench needs beyond dashboard-vm.js: toggleAttribute and style.setProperty.
function el(tag, options) {
  const node = element(tag, options);
  node.style.setProperty = (name, value) => { node.style[name] = String(value); };
  node.toggleAttribute = (name, force) => {
    const on = force === undefined ? node.getAttribute(name) === null : Boolean(force);
    if (on) node.setAttribute(name, ""); else node.removeAttribute(name);
    if (name === "hidden") node.hidden = on;
    return on;
  };
  return node;
}

// Reads the well-formed markup the views generate (no scripts, no unquoted '>' in text) into element-shim nodes.
const VOID_TAGS = new Set(["area", "br", "col", "hr", "img", "input", "link", "meta", "source", "wbr"]);
const decode = (value) => value.replaceAll("&quot;", '"').replaceAll("&#039;", "'").replaceAll("&lt;", "<").replaceAll("&gt;", ">").replaceAll("&amp;", "&");
function parseHtml(html) {
  const host = el("div");
  const stack = [host];
  const token = /<!--[\s\S]*?-->|<\/([a-zA-Z][\w-]*)\s*>|<([a-zA-Z][\w-]*)((?:\s+[^\s=>/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?)*)\s*(\/?)>|([^<]+)/g;
  for (const [, closing, opening, attributes = "", selfClosing, text] of html.matchAll(token)) {
    const parent = stack[stack.length - 1];
    if (closing) {
      const index = stack.map((node) => node.tagName).lastIndexOf(closing.toUpperCase());
      if (index > 0) stack.length = index;
    } else if (opening) {
      const node = el(opening);
      for (const [, rawName, double, single, bare] of attributes.matchAll(/([^\s=>/]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g)) {
        const name = rawName.toLowerCase();
        const value = decode(double ?? single ?? bare ?? "");
        node.setAttribute(name, value);
        if (["checked", "disabled", "hidden", "open"].includes(name)) node[name] = true;
        if (name === "value") node.value = value;
      }
      parent.append(node);
      if (!VOID_TAGS.has(opening.toLowerCase()) && !selfClosing) stack.push(node);
    } else if (text && text.trim()) {
      parent.textContent += decode(text);
    }
  }
  return host;
}

const context = loadModules([
  "dashboard/src/core/ui.js",
  "dashboard/src/core/interactions.js",
  "dashboard/src/views/asset-overview.js",
  "dashboard/src/services/asset-overview-workbench.js",
]);
context.document.createElement = (tag) => el(tag);
const View = context.ResearchOSAssetOverviewView;
const Workbench = context.ResearchOSAssetOverviewWorkbenchService;
const translate = (key) => key;
const deps = { escapeHtml: context.ResearchOSUiCore.escapeHtml, translate };

const boxes = [{
  id: "papers",
  label: "Papers",
  type: "paper",
  count: 2,
  cards: [
    { id: "paper-1", title: "Paper One", type: "paper", path: "01_knowledge/papers/paper-one.md", hierarchy_state_label: "Fictional coverage label", relation_ids: ["paper-2"] },
    { id: "paper-2", title: "Paper Two", type: "paper", path: "01_knowledge/papers/paper-two.md", relation_ids: ["paper-1"] },
  ],
}];

// Private and public card workbenches share one renderer; only the public demo drops source, file and boundary inputs.
const privateHtml = View.renderAssetCardBoxWorkbench({ boxes, publicMode: false }, deps);
const publicHtml = View.renderAssetCardBoxWorkbench({ boxes, publicMode: true }, deps);
assert.equal(View.renderAssetCardBoxWorkbench({ boxes: [{ id: "empty", cards: [] }] }, deps), "", "an empty library must not render an empty workbench");
for (const html of [privateHtml, publicHtml]) {
  assert.ok(html.includes('class="asset-card-workbench-intro"'), "the card library header needs an explicit intro column");
  assert.ok(html.includes('data-asset-card-box="papers"') && /data-asset-card-box="papers"[^>]*\sopen>/.test(html), "material categories with content render open and stay manually collapsible");
  assert.ok(html.includes("asset-card-box-state-closed") && html.includes("asset-card-box-state-open"), "a category exposes its open and closed disclosure labels");
  assert.match(html, /data-asset-card-global-search-clear[^>]*hidden disabled/, "an empty global search must not expose a clear action");
  assert.match(html, /data-asset-card-search-clear="papers"[^>]*hidden disabled/, "an empty category search must not expose a clear action");
  assert.match(html, /data-asset-card-lower-workbench[^>]*hidden>/, "card details stay hidden until a card is selected");
}
assert.ok(privateHtml.includes('name="source_hint"') && privateHtml.includes('class="asset-create-optional"') && privateHtml.includes('type="file"'), "the private intake accepts a source hint and optional local file");
assert.ok(privateHtml.includes(">assetCreateHint<") && privateHtml.includes(">assetCreateEntry<"));
for (const html of [publicHtml, View.renderAssetOverviewHtml({ cardBoxes: boxes, publicMode: true, deps })]) {
  assert.ok(!html.includes('name="source_hint"'), "the public demo must not render a source or path field");
  assert.ok(!html.includes('name="local_file"') && !html.includes('type="file"'), "the public demo must not invite local files");
  assert.ok(!html.includes('name="boundary_note"') && !html.includes("asset-create-optional"), "the public demo must not invite durable-boundary input");
  assert.ok(html.includes(">onboardingPublicBody<"), "the public intake reuses the established no-real-material boundary");
  assert.ok(html.includes(">researchPortfolioPublicDemoLabel<"), "the public intake entry identifies itself as a fictional demo");
}
assert.ok(!privateHtml.includes("data-unified-handoff-count"), "Library must not display a global review count or imply a third Work screen");

const root = parseHtml(privateHtml);
root.dataset.assetBasketIds = "";
const cardOne = root.querySelector('[data-asset-card-id="paper-1"]');
const drawer = root.querySelector("[data-asset-card-basket-drawer]");
const lower = root.querySelector("[data-asset-card-lower-workbench]");
const reveals = [];
drawer.scrollIntoView = (options) => reveals.push(options);
assert.equal(cardOne.dataset.assetCardTitle, "Paper One");
assert.equal(lower.hidden, true);

Workbench.bindAssetCardBoxEvents(root, { translate });
Workbench.bindAssetBasketClickDelegation(root, translate);
assert.equal(root.listeners.click.length, 2, "basket delegation binds once per root next to the panel delegation");

// Selecting a card opens its details and offers an add-to-basket action created after binding.
cardOne.click();
assert.ok(cardOne.classList.contains("selected"));
assert.ok(root.querySelector('[data-asset-card-id="paper-2"]').classList.contains("connected"), "related cards stay visible as connected");
assert.equal(lower.hidden, false, "selecting a card reveals its details");
const addButton = root.querySelector('[data-asset-card-add-basket="paper-1"]');
assert.ok(addButton, "the details panel offers an add-to-basket action");

// Overflowing detail fields expose their complete value as a tooltip, and drop it once the text fits.
const detail = root.querySelector("[data-asset-card-detail-grid]").children.find((section) => section.children[1]?.textContent === "Fictional coverage label");
assert.ok(detail, "the coverage label is listed in the detail grid");
Object.assign(detail.children[1], { clientWidth: 80, scrollWidth: 240 });
detail.dispatchEvent({ type: "pointerenter" });
assert.equal(detail.dataset.overflowTooltip, "Fictional coverage label");
Object.assign(detail.children[1], { scrollWidth: 60 });
detail.dispatchEvent({ type: "focus" });
assert.equal(detail.dataset.overflowTooltip, undefined);

let prevented = false;
root.dispatchEvent({ type: "click", target: addButton, preventDefault() { prevented = true; } });
assert.equal(prevented, true);
assert.equal(root.dataset.assetBasketIds, "paper-1", "adding a card places it in the temporary composition box");
assert.ok(cardOne.classList.contains("in-basket"));
assert.equal(addButton.textContent, "assetCardAddedBasket");
assert.equal(drawer.open, true, "adding a card opens the composition drawer");
assert.deepEqual({ ...reveals[0] }, { block: "nearest", behavior: "smooth" }, "the drawer is revealed through the scroll primitive");
assert.equal(root.querySelector("[data-asset-basket-count]").textContent, "1");

const removeButton = root.querySelector('[data-asset-basket-remove="paper-1"]');
assert.ok(removeButton, "the basket lists a remove action for the added card");
prevented = false;
root.dispatchEvent({ type: "click", target: removeButton, preventDefault() { prevented = true; } });
assert.equal(prevented, true);
assert.equal(root.dataset.assetBasketIds, "", "Remove takes the card out of the composition box");
assert.equal(cardOne.classList.contains("in-basket"), false, "Remove must not leave the source card marked as selected for composition");
assert.equal(cardOne.dataset.assetCardTitle, "Paper One", "Remove must not delete or mutate the source research card");
assert.equal(root.querySelector("[data-asset-basket-remove]"), null);

// The reveal follows the reduced-motion preference.
context.matchMedia = () => ({ matches: true });
root.dispatchEvent({ type: "click", target: addButton, preventDefault() {} });
assert.equal(reveals.at(-1).behavior, "auto", "reduced motion turns the reveal into an instant scroll");
delete context.matchMedia;

// Search clear actions appear only while a query is entered, and clearing hides them again.
const globalInput = root.querySelector("[data-asset-card-global-search]");
const globalClear = root.querySelector("[data-asset-card-global-search-clear]");
globalInput.value = "paper two";
globalInput.dispatchEvent({ type: "input" });
assert.equal(globalClear.hidden, false);
assert.equal(globalClear.disabled, false);
assert.equal(cardOne.hidden, true, "a global query hides non-matching cards");
globalClear.click();
assert.equal(globalInput.value, "");
assert.equal(globalClear.hidden, true);
assert.equal(globalClear.disabled, true);
assert.equal(cardOne.hidden, false);

const boxInput = root.querySelector('[data-asset-card-search-box="papers"]');
const boxClear = root.querySelector('[data-asset-card-search-clear="papers"]');
boxInput.value = "one";
boxInput.dispatchEvent({ type: "input" });
assert.equal(boxClear.hidden, false);
assert.ok(cardOne.classList.contains("search-match"));
boxClear.click();
assert.equal(boxInput.value, "");
assert.equal(boxClear.hidden, true);
assert.equal(cardOne.classList.contains("search-match"), false);

// Layout is checked by screenshots; the structural classes and the tooltip attribute must at least be styled.
let css = "";
const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).forEach((entry) => {
  const full = path.join(dir, entry.name);
  if (entry.isDirectory()) walk(full);
  else if (entry.name.endsWith(".css")) css += fs.readFileSync(full, "utf8");
});
walk(path.join(repositoryRoot, "dashboard/styles"));
for (const name of ["asset-card-workbench-intro", "asset-card-box", "asset-card-box-state-open", "asset-card-box-state-closed", "asset-card-basket-drawer", "asset-card-detail-grid"]) {
  assert.ok(privateHtml.includes(name) || name === "asset-card-detail-grid", `${name} must be rendered`);
  assert.ok(new RegExp(`\\.${name}(?![\\w-])`).test(css), `${name} must have at least one rule under dashboard/styles`);
}
assert.ok(css.includes("[data-overflow-tooltip]"), "the overflow tooltip attribute must be styled");

console.log("Asset basket add/remove contract regression passed.");
