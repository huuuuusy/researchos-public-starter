/* ResearchOS maintenance header.
 * 中文：验证 profile-aware 客户端语义、五轴生命周期派生与 ActionSpec 的可组合合同。
 * English: Verifies the profile-aware client, five-axis lifecycle, and ActionSpec contract.
 */

"use strict";

const assert = require("node:assert/strict");
const vm = require("node:vm");

const { read } = require("./helpers/dashboard-vm.js");
const machineContract = JSON.parse(read("09_templates/data_contracts/researchos-interaction-semantics-v1.json"));
assert.equal(
  machineContract.interaction_language.action_label,
  "describe_the_immediate_user_visible_effect_never_only_the_destination_surface",
  "action labels must describe their immediate effect instead of reusing a screen name",
);
assert.equal(machineContract.task_history_identity.registered_task, "provider_id_plus_item_id_plus_next_step_signature");
assert.ok(machineContract.task_history_identity.forbidden.includes("deduplicate_by_title"));
assert.ok(machineContract.task_history_identity.forbidden.includes("discard_older_artifacts_or_sources"));
assert.equal(machineContract.handoff_record_identity.owner, "dashboard/src/services/doing-board-state.js");
assert.ok(machineContract.handoff_record_identity.forbidden.includes("title_as_new_task_identity"));
assert.ok(machineContract.handoff_record_identity.forbidden.includes("path_change_creates_second_work_session_handoff"));
assert.equal(machineContract.state_axes.admission.owner, "09_templates/data_contracts/researchos-admission-state-v1.schema.json");
assert.deepEqual(machineContract.state_axes.admission.decision_state, ["unproposed", "proposed", "accepted", "revised", "rejected", "deferred"]);
assert.deepEqual(machineContract.state_axes.admission.mutation_state, ["not_requested", "staged", "applied", "rolled_back"]);
assert.deepEqual(machineContract.state_axes.admission.validation_state, ["unvalidated", "pending", "passed", "failed"]);
assert.deepEqual(machineContract.state_axes.admission.authority_role, ["none", "informative", "interpretive", "normative"]);
assert.ok(machineContract.state_axes.admission.forbidden.includes("single_authority_state_axis"));
const window = {};
const browserContext = vm.createContext({ window });
vm.runInContext(read("dashboard/src/core/edition-profile.js"), browserContext);
vm.runInContext(read("dashboard/src/core/surface-contract.js"), browserContext);

const surfaces = window.ResearchOSSurfaceContract;
const interaction = window.ResearchOSInteractionContract;
const plain = (value) => JSON.parse(JSON.stringify(value));
const activeProfile = machineContract.client_profiles.profiles[surfaces.clientProfileId];

assert.equal(interaction.VERSION, machineContract.version);
assert.ok(activeProfile, "the compiled client shell must identify a registered profile");
assert.deepEqual(plain(surfaces.canonicalSurfaceIds), activeProfile.workspace_ids);
assert.deepEqual(plain(surfaces.surfaceAliasMap), activeProfile.surface_aliases);
assert.equal(surfaces.canonicalSurface("agent"), "now");
assert.equal(surfaces.canonicalSurface("assets"), "library");
assert.equal(surfaces.canonicalSurface("inbox"), "now");
assert.equal(surfaces.canonicalSurface("review"), "now");
assert.equal(surfaces.canonicalSurface("next"), "now");
assert.deepEqual(plain(surfaces.surfaceRoute("review")), { filter: "needs_review", item: "", panel: "review", surface: "now" });
assert.equal(surfaces.canonicalSurface("unknown"), "");
assert.equal(surfaces.runtimeWorkspace("agent"), "now", "legacy input must dual-read to the canonical runtime surface");
assert.equal(surfaces.runtimeWorkspace("assets"), "library");
assert.equal(surfaces.runtimeWorkspace("inbox"), "now");
assert.equal(activeProfile.alias_policy, "input_only_canonical_output");
assert.equal(Object.hasOwn(surfaces, "legacyWorkspace"), false, "the runtime must never emit a reverse legacy alias");
assert.deepEqual(Array.from(surfaces.workspaceTabs), activeProfile.workspace_ids);
assert.deepEqual(
  plain(Object.fromEntries(surfaces.surfaceScopes.filter((entry) => entry.kind === "workspace").map((entry) => [entry.id, entry.primaryQuestion]))),
  Object.fromEntries(activeProfile.workspace_ids.map((id) => [id, machineContract.surfaces[id].question])),
  "each workspace must expose the single primary question owned by the machine contract",
);
assert.deepEqual(
  plain(Object.fromEntries(surfaces.surfaceScopes.filter((entry) => entry.kind !== "workspace").map((entry) => [entry.id, [entry.kind, entry.parentSurface]]))),
  {
    utility: ["slot_host", "library"],
    preview: ["aside", "any"],
  },
  "Utility and Preview must remain auxiliary surfaces rather than additional workspaces",
);
assert.ok(surfaces.surfaceScopes.filter((entry) => entry.kind !== "workspace").every((entry) => !entry.tabI18n && !entry.primaryQuestion));
assert.ok(surfaces.surfaceScopes.every((entry) => !Object.hasOwn(entry, "legacyId")), "generated surface projections must emit canonical IDs only");

vm.runInContext(read("dashboard/src/core/view-state.js"), browserContext);
const stored = new Map([["researchos-workspace-tab", "assets"]]);
const storage = {
  getItem: (key) => stored.has(key) ? stored.get(key) : null,
  setItem: (key, value) => stored.set(key, String(value)),
};
assert.equal(window.ResearchOSViewState.read(storage).workspaceTab, "library", "legacy persisted state must remain readable");
assert.equal(window.ResearchOSViewState.writeWorkspaceTab("inbox", storage), "now");
assert.equal(stored.get("researchos-workspace-tab"), "now", "legacy input must be persisted only as its canonical surface");
assert.equal(window.ResearchOSViewState.writeWorkspaceTab("unknown", storage), "now", "unknown persisted state must fail to Now");
assert.equal(window.ResearchOSViewState.normalizeWorkFilter("needs_review"), "needs_review");
assert.equal(window.ResearchOSViewState.normalizeWorkFilter("not-a-filter"), "active", "invalid ephemeral Work filters must fail closed to the active projection");
assert.equal(window.ResearchOSViewState.writeWorkFilter, undefined, "Work filtering is an ephemeral projection preference, not durable domain or browser state");
assert.equal(Object.hasOwn(window.ResearchOSViewState.storageKeys, "workFilter"), false);

vm.runInContext(read("dashboard/src/core/workspace-routing.js"), browserContext);
assert.equal(window.ResearchOSWorkspaceRouting.workspaceForTarget("todayWorkSession"), "now");
assert.equal(window.ResearchOSWorkspaceRouting.workspaceForTarget("unifiedInbox"), "now");
for (const axis of ["session", "run", "observation", "result"]) {
  assert.deepEqual(plain(interaction.STATE_AXES[axis]), machineContract.state_axes[axis]);
}
for (const axis of ["decision_state", "mutation_state", "validation_state", "authority_role"]) {
  assert.deepEqual(plain(interaction.STATE_AXES.admission[axis]), machineContract.state_axes.admission[axis]);
}
assert.deepEqual(plain(interaction.ACTION_SPEC.required), machineContract.action_spec.required);
assert.deepEqual(
  plain(interaction.PREDICTION_CONTRACT.requiredVisibleQuestions),
  machineContract.prediction_contract.required_visible_questions,
);
assert.equal(interaction.PREDICTION_CONTRACT.beforeAction, machineContract.prediction_contract.before_action);
assert.equal(interaction.PREDICTION_CONTRACT.afterFailure, machineContract.prediction_contract.after_failure);
assert.deepEqual(Object.keys(machineContract.objects).sort(), ["action_feedback", "candidate", "commitment", "context_pack", "project", "receipt", "result", "run", "task_envelope", "work_session"]);
assert.equal(machineContract.objects.action_feedback.meaning, "ephemeral_client_feedback_not_a_durable_receipt_authority_or_recovery_coordinate");
assert.equal(machineContract.surfaces.library.mode_rule, "one_or_few_commitments_select_relevant_objects_with_provenance_and_relation_kind");
assert.equal(machineContract.surfaces.now.focus_invariant, "many_commitments_may_be_visible_each_with_one_disposition_and_one_next_step");
assert.equal(machineContract.surfaces.work.session_invariant, "one_bounded_intent_per_session_many_sessions_per_researchos");
assert.ok(machineContract.surfaces.work.filters.includes("needs_review"));
assert.equal(machineContract.objects.context_pack.owner, "work_session_kernel_and_context_receipt");
assert.deepEqual(machineContract.authority.precedence, [
  "canonical_source_and_human_decision",
  "stable_kernel_ledger",
  "capability_owned_source",
  "generated_projection",
  "client_preference_and_dom",
]);
assert.deepEqual(Object.keys(machineContract.legacy_v9_migration), ["draft", "active", "running", "ready", "completed"]);
assert.equal(machineContract.legacy_v9_migration.running.requires[0], "exact_run_binding");
assert.equal(machineContract.recovery_rules.delivery_unknown, "reconcile_by_client_request_id_never_resubmit");
assert.equal(machineContract.recovery_rules.late_result, "attach_recoverable_receipt_without_reopening_session_or_rerunning");
assert.equal(machineContract.result_action_matrix.answer.primary, "finish_session");
assert.equal(machineContract.result_action_matrix.artifact.primary, "open_artifact");
assert.equal(machineContract.result_action_matrix.writeback.primary, "open_review");
assert.deepEqual(machineContract.result_action_matrix.delivery_unknown.forbidden, ["resubmit", "retry_same_request"]);
assert.deepEqual(machineContract.element_hierarchy, ["domain", "surface", "region", "block", "primitive", "action", "feedback"]);
assert.deepEqual(machineContract.prediction_contract.required_visible_questions, ["actor", "location", "effect", "non_effect", "fallback"]);

const presentation = (snapshot) => plain(interaction.deriveTaskPresentation(snapshot));
const valid = (snapshot) => plain(interaction.validateLifecycleSnapshot(snapshot));

assert.equal(presentation({ session: "none" }).state, "no_task");
assert.equal(presentation({ session: "open" }).state, "ready");
for (const run of ["submitted", "queued", "running"]) {
  assert.equal(presentation({ session: "open", run, observation: "fresh" }).state, "running");
}
assert.equal(
  presentation({ session: "open", run: "submitted", observation: "delivery_unknown" }).state,
  "verify_delivery",
  "unknown delivery must never be rendered as running",
);
assert.equal(
  presentation({ session: "open", run: "running", observation: "lease_expired" }).state,
  "verify_run",
  "an expired observation lease must require verification instead of an infinite spinner",
);
assert.equal(
  presentation({ session: "open", run: "running", observation: "reconcile_failed" }).state,
  "verify_run",
);
assert.deepEqual(
  presentation({ session: "open", run: "failed", observation: "fresh", sideEffects: "none" }),
  { allowedActions: ["retry_same_request", "finish_session_keep_receipt"], errors: [], primaryAction: "retry_same_request", retryAllowed: true, state: "failed_retryable" },
);
assert.equal(
  presentation({ session: "open", run: "failed", observation: "fresh", sideEffects: "unknown" }).state,
  "failed_needs_impact_check",
);
const answerReady = presentation({ session: "open", run: "completed", observation: "fresh", result: "answer" });
assert.equal(answerReady.state, "result_ready");
assert.equal(answerReady.primaryAction, "finish_session");
assert.deepEqual(answerReady.allowedActions.slice(0, 3), ["finish_session", "add_followup", "copy_result"]);
assert.equal(presentation({ session: "open", run: "completed", observation: "fresh", result: "artifact" }).primaryAction, "open_artifact");
assert.deepEqual(valid({
  session: "open", run: "completed", observation: "fresh", result: "answer",
  admission: { decision_state: "unproposed", mutation_state: "not_requested", validation_state: "unvalidated", authority_role: "none" },
}), [], "answer-only completion must remain independent of candidate admission");
assert.deepEqual(valid({
  session: "open", run: "completed", observation: "fresh", result: "artifact",
  admission: { decision_state: "unproposed", mutation_state: "not_requested", validation_state: "unvalidated", authority_role: "none" },
}), [], "artifact-only completion must remain independent of candidate admission");
assert.equal(presentation({
  session: "open", run: "completed", observation: "fresh", result: "writeback",
  admission: { decision_state: "proposed", mutation_state: "not_requested", validation_state: "unvalidated", authority_role: "none" },
}).primaryAction, "open_review");
assert.equal(
  presentation({ session: "open", run: "completed", observation: "fresh", result: "invalid" }).state,
  "failed_needs_impact_check",
  "an invalid result envelope must not appear as a reviewable result",
);
assert.equal(
  presentation({ session: "ended", run: "running", observation: "fresh" }).state,
  "ended_with_run_tracking",
  "ending the session must not erase a still-bound run receipt",
);
assert.equal(
  presentation({ session: "ended", run: "completed", observation: "fresh", result: "answer" }).state,
  "late_result_ready",
  "a late result must remain reviewable without reopening the ended session",
);
assert.equal(presentation({ session: "ended" }).state, "ended");

assert.ok(valid({ session: "open", run: "running" }).includes("active_run_requires_observation"));
assert.ok(valid({ session: "open", run: "completed", observation: "fresh" }).includes("completed_run_requires_result"));
assert.ok(valid({ session: "open", run: "completed", observation: "delivery_unknown", result: "answer" }).includes("terminal_run_cannot_have_uncertain_observation"));
assert.ok(valid({ session: "open", run: "running", observation: "fresh", result: "answer" }).includes("active_run_cannot_have_result"));
assert.ok(valid({ session: "open", run: "completed", observation: "fresh", result: "writeback" }).includes("writeback_requires_proposed_admission"));
assert.ok(valid({
  session: "open",
  run: "completed",
  observation: "fresh",
  result: "answer",
  admission: { decision_state: "proposed" },
}).includes("non_writeback_result_cannot_claim_admission"));
assert.ok(valid({
  session: "open",
  run: "completed",
  observation: "fresh",
  result: "writeback",
  admission: { decision_state: "accepted", mutation_state: "applied", validation_state: "unvalidated", authority_role: "none" },
}).includes("applied_validation_invalid"));
assert.ok(valid({
  session: "open",
  run: "completed",
  observation: "fresh",
  result: "writeback",
  admission: { decision_state: "proposed", mutation_state: "not_requested", validation_state: "passed", authority_role: "none" },
}).includes("validation_requires_mutation"));
assert.deepEqual(valid({
  session: "open",
  run: "completed",
  observation: "fresh",
  result: "writeback",
  admission: { decision_state: "accepted", mutation_state: "applied", validation_state: "passed", authority_role: "interpretive" },
}), []);
assert.deepEqual(valid({
  session: "open", run: "completed", observation: "fresh", result: "writeback",
  admission: { decision_state: "rejected", mutation_state: "not_requested", validation_state: "unvalidated", authority_role: "none" },
}), [], "candidate rejection must not imply mutation or validation");
assert.deepEqual(valid({
  session: "open", run: "completed", observation: "fresh", result: "writeback",
  admission: { decision_state: "accepted", mutation_state: "applied", validation_state: "failed", authority_role: "interpretive" },
}), [], "an applied mutation with failed validation must remain a valid non-success receipt");

const safeAction = {
  id: "next.open-codex",
  verb: "open",
  target: "current_task",
  actor: "human",
  location: "codex",
  effect: "handoff",
  confirmation: "none",
  risk: "low",
  reversible: true,
  fallback: "copy_task_packet",
};
assert.deepEqual(plain(interaction.validateActionSpec(safeAction)), []);
for (const field of machineContract.action_spec.required) {
  const incomplete = { ...safeAction };
  delete incomplete[field];
  assert.ok(
    plain(interaction.validateActionSpec(incomplete)).some((error) => error === `missing_or_invalid:${field}`),
    `ActionSpec must fail closed when ${field} is absent`,
  );
}
assert.ok(plain(interaction.validateActionSpec({
  ...safeAction,
  effect: "mutate_canonical",
  confirmation: "inline",
  risk: "medium",
})).includes("canonical_mutation_requires_high_risk_preview"));
assert.deepEqual(plain(interaction.validateActionSpec({
  ...safeAction,
  id: "review.apply",
  verb: "apply",
  location: "review",
  effect: "mutate_canonical",
  confirmation: "preview_confirm",
  risk: "high",
})), []);

console.log("Interaction semantic contract passed.");
