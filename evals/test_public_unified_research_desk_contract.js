/* Public-safe production contract for Unified Desk: one anonymous desk, registered scripts, and no private or networked
 * code in any Unified Desk plugin file. Desk behaviour is covered by the test_unified_research_desk_*.js tests.
 */
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { read, root } = require("./helpers/dashboard-vm.js");

const index = read("dashboard/index.html");

// One public desk with its fixed DOM anchors; the two-workspace switcher stays hidden on the public desk.
assert.match(index, /data-public-unified-desk/);
assert.match(index, /data-runtime-scope="public_starter"/);
assert.equal((index.match(/data-unified-desk(?:\s|>)/g) || []).length, 1);
for (const id of ["desk-tray", "desk-calendar", "resource-library", "resource-card-boxes"]) {
  assert.equal((index.match(new RegExp(`id="${id}"`, "g")) || []).length, 1, `#${id} must exist exactly once`);
}
assert.match(index, /id="resource-library"[\s\S]*?id="resource-card-boxes"/, "the card boxes live inside the resource library");
assert.match(index, /class="workspace-switcher"[^>]*hidden/);
assert.match(index, /id="workspace-panel-now"[^>]*hidden/);
assert.match(index, /id="workspace-panel-library"[^>]*hidden/);
assert.doesNotMatch(index, /data-private-unified-desk|data-runtime-scope="private"|data-self-person-aliases="Shiyu/);

// Script and stylesheet registration.
const registered = [...index.matchAll(/<script src="([^"]+)"><\/script>/g)].map((match) => match[1]);
for (const file of [
  "src/services/item-composition-model.js",
  "src/services/codex-thread-router.js",
  "src/services/handoff-composer.js",
]) assert.ok(registered.includes(file), `${file} must be registered`);
const deskScripts = registered.filter((file) => /^src\/plugins\/unified-[\w-]*desk[\w-]*\.js$/.test(file));
assert.ok(deskScripts.length > 0, "the Unified Desk plugin must be registered");
for (const file of registered.filter((file) => !/^https?:/.test(file))) {
  assert.ok(fs.existsSync(path.join(root, "dashboard", file)), `registered script ${file} must exist`);
}
assert.ok(read("dashboard/style.css").includes("./styles/unified-desk.css"), "the desk stylesheet must be imported");

// Privacy and copy-only boundary across every Unified Desk plugin file, however the plugin is split.
const pluginDir = path.join(root, "dashboard/src/plugins");
const deskFiles = fs.readdirSync(pluginDir).filter((name) => /^unified-[\w-]*desk[\w-]*\.js$/.test(name));
assert.ok(deskFiles.length > 0);
for (const name of deskFiles) {
  const source = fs.readFileSync(path.join(pluginDir, name), "utf8");
  assert.doesNotMatch(source, /fetch\([^)]*https?:\/\//i, `${name} must not fetch a network URL`);
  assert.doesNotMatch(source, /Shiyu|\/Users\//, `${name} must not carry a real name or home path`);
}

console.log("OK: Public production exposes one anonymous copy-only Unified Desk");
