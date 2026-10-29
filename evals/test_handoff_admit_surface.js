const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const context = {};
context.window = context;
vm.runInNewContext(read("dashboard/src/services/handoff-admit-surface.js"), context);
vm.runInNewContext(read("dashboard/src/views/handoff-receipt.js"), context);
vm.runInNewContext(read("dashboard/src/views/handoff-admit-surface.js"), context);

const owner = context.ResearchOSHandoffAdmitSurface;
const view = context.ResearchOSHandoffAdmitSurfaceView;
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;",
}[char]));
const translate = (key) => key;
const session = { id: "session-1", intent: "Inspect <claim> safely", responseMode: "answer", status: "active" };

for (const config of [undefined, null, {}, { handoff_admit_candidate: false }, { handoff_admit_candidate: "true" }]) {
  const legacy = owner.project({ config, session });
  assert.equal(legacy.mode, "legacy_work_session", "candidate mode must remain exact-boolean and default-off");
  assert.equal(view.render(legacy, {}, { escapeHtml, translate }), "");
}

const candidate = owner.project({
  backgroundPreparationAvailable: false,
  config: { handoff_admit_candidate: true, authority: "forged", provider: "remote" },
  handoffActive: false,
  result: { response_mode: "writeback", status: "completed", authority: "validated" },
  session,
});
assert.equal(candidate.mode, "handoff_admit_candidate");
assert.equal(candidate.routes.codex.outcome, "copy_task_packet");
assert.equal(candidate.routes.background.available, false);
assert.equal(candidate.routes.review.outcome, "create_handoff_review_item");
assert.equal(candidate.result.mode, "writeback");
assert.equal("authority" in candidate, false);
assert.equal(Object.isFrozen(candidate), true);

const html = view.render(candidate, {}, { escapeHtml, translate });
assert.match(html, /data-handoff-admit-candidate/);
assert.match(html, /Inspect &lt;claim&gt; safely/);
assert.match(html, /data-work-session-copy-task/);
assert.match(html, /data-work-session-prepare/);
assert.match(html, /handoffAdmitBackgroundUnavailable/);
assert.match(html, /handoffAdmitResultStatus_completed · handoffAdmitResultMode_writeback/);
assert.doesNotMatch(html, /textarea|data-work-session-run-form|data-work-session-run-draft|data-work-session-complete-project|data-work-session-complete-step/);
assert.doesNotMatch(html, /authority="validated"|remote/);

const withExistingReview = owner.project({ config: { handoff_admit_candidate: true }, handoffActive: true, session });
assert.equal(withExistingReview.routes.review.outcome, "open_existing_review");
assert.match(view.render(withExistingReview, {}, { escapeHtml, translate }), /handoffAdmitReviewOpen/);

const workSessionContext = { ResearchOSHandoffAdmitSurfaceView: view };
workSessionContext.window = workSessionContext;
vm.runInNewContext(read("dashboard/src/views/work-session.js"), workSessionContext);
const workView = workSessionContext.ResearchOSWorkSessionView;
const candidateRendered = workView.renderWorkSessionHtml({
  handoffAdmitSurface: candidate, session,
}, { escapeHtml, translate });
assert.match(candidateRendered, /data-handoff-admit-candidate/);
assert.doesNotMatch(candidateRendered, /data-work-session-run-form|work-session-recent-panel|work-session-process-log/);

const legacyRendered = workView.renderWorkSessionHtml({
  handoffAdmitSurface: owner.project({ config: {}, session }), session,
}, { escapeHtml, translate });
assert.match(legacyRendered, /data-work-session-active/);
assert.match(legacyRendered, /data-work-session-run-form/);
assert.doesNotMatch(legacyRendered, /data-handoff-admit-candidate/);

console.log("OK: default-off Handoff/Admit candidate replaces no legacy path and claims no authority");
