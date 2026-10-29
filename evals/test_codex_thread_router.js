/* ResearchOS maintenance header.
 * 中文：冻结 projection-first UI 的 exact Codex task 路由与 copy-only 回退合同。
 * English: Freezes exact Codex task routing and copy-only fallback for the projection-first UI.
 */

"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const context = { console };
context.window = context;
vm.createContext(context);
vm.runInContext(
  fs.readFileSync(path.join(root, "dashboard/src/services/codex-thread-router.js"), "utf8"),
  context,
  { filename: "codex-thread-router.js" },
);

const Router = context.ResearchOSCodexThreadRouter;
const plain = (value) => JSON.parse(JSON.stringify(value));
const receipt = (overrides = {}) => ({
  identity: {
    continued_from_prior: true,
    drift_reasons: [],
    episode_id: "ep_same",
    thread_id: "thread:exact-1",
    thread_title_used_for_identity: false,
    ...(overrides.identity || {}),
  },
  status: "ready",
  ...overrides,
});

const resumable = {
  create_available: true,
  exact_thread_id: "thread:exact-1",
  thread_state: "resumable",
  transport_available: true,
};

const continued = Router.decide({ routeReceipt: receipt(), runtime: resumable });
assert.equal(continued.intended_route, "continue_exact_thread");
assert.equal(continued.recommended_route, "continue_exact_thread");
assert.equal(continued.thread_id, "thread:exact-1");
assert.deepEqual(plain(continued.reason_codes), ["same_bounded_episode", "exact_thread_resumable"]);
assert.equal(continued.requires_confirmation, true);

const copyFallback = Router.decide({
  routeReceipt: receipt(),
  runtime: { ...resumable, transport_available: false },
});
assert.equal(copyFallback.intended_route, "continue_exact_thread");
assert.equal(copyFallback.recommended_route, "copy_only");
assert.equal(copyFallback.transport_state, "unavailable");
assert.ok(copyFallback.reason_codes.includes("transport_unavailable"));

const drifted = Router.decide({
  routeReceipt: receipt({ identity: { continued_from_prior: false, drift_reasons: ["bounded_intent_or_authority_changed"], episode_id: "ep_new", thread_id: "thread:exact-1", thread_title_used_for_identity: false } }),
  runtime: resumable,
});
assert.equal(drifted.intended_route, "create_new_task");
assert.equal(drifted.recommended_route, "create_new_task");
assert.ok(drifted.reason_codes.includes("bounded_intent_or_authority_changed"));

const renamed = Router.decide({
  routeReceipt: { ...receipt(), thread_title: "A completely different title" },
  runtime: { ...resumable, thread_title: "Old title" },
});
assert.equal(renamed.recommended_route, "continue_exact_thread", "thread titles must never enter identity");
assert.equal(JSON.stringify(renamed).includes("title"), false);

const ambiguous = Router.decide({
  routeReceipt: receipt(),
  runtime: { ...resumable, exact_thread_id: "", thread_state: "ambiguous" },
});
assert.equal(ambiguous.intended_route, "copy_only");
assert.equal(ambiguous.recommended_route, "copy_only");
assert.ok(ambiguous.reason_codes.includes("thread_identity_ambiguous"));

const closed = Router.decide({
  routeReceipt: receipt(),
  runtime: { ...resumable, thread_state: "closed" },
});
assert.equal(closed.intended_route, "create_new_task");
assert.equal(closed.recommended_route, "create_new_task");
assert.ok(closed.reason_codes.includes("prior_thread_closed"));

const publicRoute = Router.decide({
  publicStarter: true,
  routeReceipt: receipt(),
  runtime: resumable,
});
assert.equal(publicRoute.intended_route, "copy_only");
assert.equal(publicRoute.recommended_route, "copy_only");
assert.equal(publicRoute.transport_state, "public_policy_blocked");

const invalidReceipt = Router.decide({
  routeReceipt: receipt({ status: "needs_clarification" }),
  runtime: resumable,
});
assert.equal(invalidReceipt.recommended_route, "copy_only");
assert.ok(invalidReceipt.reason_codes.includes("route_receipt_not_ready"));

const mismatch = Router.decide({
  routeReceipt: receipt(),
  runtime: { ...resumable, exact_thread_id: "thread:other" },
});
assert.equal(mismatch.recommended_route, "copy_only");
assert.ok(mismatch.reason_codes.includes("exact_thread_id_mismatch"));

const overridden = Router.applyOverride(continued, "copy_only", "用户希望先检查交接文本");
assert.equal(overridden.recommended_route, "copy_only");
assert.equal(overridden.override.reason, "用户希望先检查交接文本");
assert.equal(overridden.override.original_route, "continue_exact_thread");
assert.throws(
  () => Router.applyOverride(drifted, "continue_exact_thread", "same title"),
  (error) => error.code === "unsafe_thread_route_override",
);

console.log("OK: Codex thread routing uses exact episode/thread identity and always fails back to copy-only");
