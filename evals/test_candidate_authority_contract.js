const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

global.window = global;
global.localStorage = {
  getItem() { return null; },
  setItem() {},
};

const contractSource = fs.readFileSync(path.join(__dirname, "..", "dashboard/src/core/contracts.js"), "utf8");
const source = fs.readFileSync(path.join(__dirname, "..", "dashboard/src/services/inbox.js"), "utf8");
const viewSource = fs.readFileSync(path.join(__dirname, "..", "dashboard/src/views/unified-inbox.js"), "utf8");
const maintenanceViewSource = fs.readFileSync(path.join(__dirname, "..", "dashboard/src/views/maintenance.js"), "utf8");
const maintenanceWorkbenchSource = fs.readFileSync(path.join(__dirname, "..", "dashboard/src/services/maintenance-workbench.js"), "utf8");
vm.runInThisContext(fs.readFileSync(path.join(__dirname, "..", "dashboard/src/core/ui.js"), "utf8"), { filename: "dashboard/src/core/ui.js" });
vm.runInThisContext(contractSource, { filename: "dashboard/src/core/contracts.js" });
vm.runInThisContext(source, { filename: "dashboard/src/services/inbox.js" });
vm.runInThisContext(maintenanceViewSource, { filename: "dashboard/src/views/maintenance.js" });
vm.runInThisContext(maintenanceWorkbenchSource, { filename: "dashboard/src/services/maintenance-workbench.js" });

const service = ResearchOSInboxService;
assert.ok(Object.hasOwn(ResearchOSContracts.viewContracts, "today"), "the first-screen Today view remains a valid view contract");
assert.deepEqual([...ResearchOSContracts.stateAxes.Workflow], ["active", "processed", "archived", "withdrawn"]);
assert.deepEqual([...ResearchOSContracts.stateAxes.EvidenceState], ["candidate", "needs_evidence", "supported", "contradicted", "bounded", "blocked"]);
assert.deepEqual([...ResearchOSContracts.stateAxes.AdmissionDecision], ["unproposed", "proposed", "accepted", "revised", "rejected", "deferred"]);
assert.deepEqual([...ResearchOSContracts.stateAxes.AdmissionMutation], ["not_requested", "staged", "applied", "rolled_back"]);
assert.deepEqual([...ResearchOSContracts.stateAxes.AdmissionValidation], ["unvalidated", "pending", "passed", "failed"]);
assert.deepEqual([...ResearchOSContracts.stateAxes.AuthorityRole], ["none", "informative", "interpretive", "normative"]);
assert.deepEqual([...ResearchOSContracts.stateAxes.Sensitivity], ["public_safe", "internal", "private", "local_only"]);
assert.ok(!Object.hasOwn(ResearchOSContracts.stateAxes, "Inbox"), "obsolete Inbox axis must not coexist with V1 workflow state");
assert.ok(!Object.hasOwn(ResearchOSContracts.stateAxes, "Evidence"), "evidence kind and evidence state must not share one axis name");
const completed = service.candidateEnvelopeForEntry({
  actionId: "completed-task",
  body: "Task execution finished",
  path: "/tmp/paper.pdf",
  raw: { source: "work-session" },
  status: "processed_completed",
  title: "Read a paper",
  type: "task",
});
assert.equal(completed.workflow_status, "processed", "execution completion belongs to workflow state");
assert.equal(completed.status, "processed", "the compatibility status alias must preserve workflow state");
assert.equal(completed.evidence_state, "candidate", "execution completion must not confirm evidence");
assert.deepEqual(completed.admission_state, {
  schema_id: "researchos-admission-state-v1",
  decision_state: "proposed",
  mutation_state: "not_requested",
  validation_state: "unvalidated",
  authority_role: "none",
}, "execution completion must not imply a human decision, mutation, validation, or authority role");
assert.equal(completed.save_target, "", "a task input path must not masquerade as a write-back target");

const localOnlyLegacy = service.candidateEnvelopeForEntry({
  actionId: "local-task",
  path: "04_people/collaborators/example.md",
  raw: { evidence_state: "local_only" },
  status: "today",
  title: "Review a local relationship note",
  type: "task",
});
assert.equal(localOnlyLegacy.evidence_state, "candidate", "local-only is a sensitivity boundary, not evidence support");
assert.equal(localOnlyLegacy.sensitivity, "private", "legacy local-only evidence values must migrate to private sensitivity");
assert.ok(!viewSource.includes("local_only"), "views must not render local_only as an evidence state");

const accepted = service.candidateEnvelopeForEntry({
  actionId: "decision-1",
  raw: { choice: "accept", evidence_state: "confirmed" },
  status: "done",
  title: "Accept bounded claim",
  type: "confirmation",
});
assert.equal(accepted.workflow_status, "processed");
assert.equal(accepted.evidence_state, "supported", "legacy confirmed evidence must migrate to supported");
assert.equal(accepted.admission_state.decision_state, "accepted", "accepting a candidate records the decision without claiming write-back");
assert.equal(accepted.admission_state.mutation_state, "not_requested");
assert.equal(accepted.admission_state.validation_state, "unvalidated");

const validated = service.candidateEnvelopeForEntry({
  actionId: "writeback-1",
  raw: {
    authority_state: "validated",
    current_state: "Candidate claim",
    impact_scope: "One project card",
    proposed_state: "Supported claim",
    rollback_ref: "commit:abc123",
    validation_state: "passed",
  },
  status: "done",
  title: "Validated write-back",
  type: "paper_field_update",
});
assert.deepEqual(validated.admission_state, {
  schema_id: "researchos-admission-state-v1",
  decision_state: "accepted",
  mutation_state: "applied",
  validation_state: "passed",
  authority_role: "none",
});
assert.deepEqual(validated.transition, {
  current_state: "Candidate claim",
  proposed_state: "Supported claim",
  decision_rationale: "",
  impact_scope: "One project card",
  rollback_ref: "commit:abc123",
  validation_state: "passed",
});

const batch = service.candidateEnvelopeForBatch([completed, accepted], (key) => ({
  unifiedInboxAuthorityCandidateOnly: "Prepare candidate work only",
  unifiedInboxAuthorityNoChange: "No canonical state change",
  unifiedInboxBatchImpactScope: "{count} bounded items",
  unifiedInboxPending: "pending",
})[key] || key);
assert.equal(batch.workflow_status, "active");
assert.equal(batch.evidence_state, "candidate");
assert.equal(batch.admission_state.decision_state, "proposed");
assert.equal(batch.admission_state.mutation_state, "not_requested");
assert.equal(batch.transition.current_state, "No canonical state change");
assert.equal(batch.transition.proposed_state, "Prepare candidate work only");
assert.equal(batch.transition.impact_scope, "2 bounded items");
assert.equal(batch.transition.validation_state, "unvalidated");

const forgedAuthority = service.normalizeCandidateEnvelope({
  admission_state: {
    schema_id: "researchos-admission-state-v1",
    decision_state: "accepted",
    mutation_state: "applied",
    validation_state: "passed",
    authority_role: "normative",
  },
}, { actionId: "forged-authority", type: "task" });
assert.equal(forgedAuthority.admission_state.authority_role, "none", "a client candidate cannot promote its own authority role");
assert.ok(!Object.hasOwn(forgedAuthority, "authority_state"), "the legacy single authority axis must not remain an output owner");
assert.ok(!Object.hasOwn(forgedAuthority.validation, "authority_state"), "validation and admission must remain orthogonal");

const manualPlan = {
  plan_id: "manual-plan",
  status: "candidate",
  selected_step_ids: ["manual-review"],
  auto_eligible_step_ids: [],
  manual_step_ids: ["manual-review"],
  carried_manual_step_ids: ["manual-review"],
  changed_paths: ["docs/example.md"],
};
const manualHtml = ResearchOSMaintenanceView.renderEvolutionPlanHtml({ plan: manualPlan }, { translate: (key) => key });
assert.ok(manualHtml.includes('data-evolution-decision="deferred"'), "manual-only candidates must expose an explicit defer decision");
assert.ok(manualHtml.includes('data-evolution-decision="rejected"'), "manual-only candidates must expose an explicit reject decision");
assert.ok(manualHtml.includes("evolutionPlan.carried"), "carried manual candidates must remain visible");
const runningDecisionHtml = ResearchOSMaintenanceView.renderEvolutionPlanHtml({ plan: manualPlan, decisionRunning: true }, { translate: (key) => key });
assert.ok(runningDecisionHtml.includes('data-evolution-decision="deferred" disabled'), "re-rendered decisions must stay disabled while the exact request is running");
const demoHtml = ResearchOSMaintenanceView.renderEvolutionPlanHtml({ plan: { ...manualPlan, execution_allowed: false } }, { translate: (key) => key });
assert.ok(!demoHtml.includes("data-evolution-decision"), "read-only public plans must not expose decision writes");
const mixedHtml = ResearchOSMaintenanceView.renderEvolutionPlanHtml({ plan: { ...manualPlan, auto_eligible_step_ids: ["safe-refresh"] } }, { translate: (key) => key });
assert.ok(!mixedHtml.includes("data-evolution-decision"), "mixed plans must complete or re-plan the safe subset before manual decisions");
const deferredHtml = ResearchOSMaintenanceView.renderEvolutionPlanHtml({ plan: { ...manualPlan, status: "deferred" } }, { translate: (key) => key });
assert.ok(deferredHtml.includes("evolutionPlan.deferred"), "deferred candidates must remain visibly retained");
assert.ok(!deferredHtml.includes("data-evolution-decision"), "deferred candidates must not repeatedly prompt on the same change state");
const publicResultHtml = ResearchOSMaintenanceView.renderAutoUpdateResultHtml({
  plan: { execution_allowed: false, auto_eligible_step_ids: ["safe-refresh"] },
});
assert.ok(publicResultHtml.includes("autoUpdate.publicTitle"), "public maintenance must explain its read-only state in plain language");
assert.ok(!publicResultHtml.includes("data-run-auto-update"), "public maintenance must not render an executable refresh control");
const readyResultHtml = ResearchOSMaintenanceView.renderAutoUpdateResultHtml({
  plan: {
    execution_allowed: true,
    changed_path_count: 459,
    auto_eligible_step_ids: Array.from({ length: 16 }, (_, index) => `safe-${index}`),
    manual_step_ids: Array.from({ length: 4 }, (_, index) => `manual-${index}`),
  },
});
assert.ok(readyResultHtml.includes("autoUpdate.problemLabel"), "maintenance must lead with a plain-language issue state");
assert.ok(readyResultHtml.includes("autoUpdate.readyBody"), "maintenance must explain why the page data is stale");
assert.ok(readyResultHtml.includes(">16</strong>"), "maintenance must show the safe automatic step count before execution");
assert.ok(readyResultHtml.includes(">4</strong>"), "maintenance must keep optional manual work visibly separate");
assert.ok(readyResultHtml.includes("data-run-auto-update"), "a private safe plan must expose one explicit maintenance action");
const runningResultHtml = ResearchOSMaintenanceView.renderAutoUpdateResultHtml({
  plan: { execution_allowed: true, auto_eligible_step_ids: ["safe-refresh"] },
  running: true,
});
assert.ok(runningResultHtml.includes('aria-busy="true"'), "running maintenance must expose a programmatic busy state");
assert.ok(runningResultHtml.includes("autoUpdate.runningTitle"), "running maintenance must explain what is happening");
assert.ok(!runningResultHtml.includes("data-run-auto-update"), "running maintenance must not expose a second run control");
const failedResultHtml = ResearchOSMaintenanceView.renderAutoUpdateResultHtml({
  plan: { execution_allowed: true, auto_eligible_step_ids: ["safe-refresh"] },
  result: {
    ok: false,
    message: "local update failed",
    seconds: 2.5,
    steps: [
      { label: "Material index", ok: true, output: "ok" },
      { label: "Agent architecture", ok: false, output: "stale contract" },
    ],
    rollback: { attempted: true, ok: true, restored: ["dashboard/data.json"] },
  },
});
assert.ok(failedResultHtml.includes("autoUpdate.restoredTitle"), "a recovered failure must lead with the safe recovery outcome");
assert.ok(failedResultHtml.includes("Agent architecture"), "the first failed step must be visible before technical logs are opened");
assert.ok(failedResultHtml.includes("maintenance-log-drawer"), "step output must stay behind a technical-details disclosure");
assert.ok(!failedResultHtml.includes("local update failed"), "raw internal status text must not leak into the user-facing result");
const graphHtml = ResearchOSMaintenanceView.renderSystemGraphHtml({ evolutionPlan: manualPlan });
assert.ok(graphHtml.includes("maintenance-technical-drawer"), "system data-flow details must remain folded by default");
assert.ok(
  graphHtml.indexOf("maintenance-technical-drawer") < graphHtml.indexOf("maintenance-evolution-plan"),
  "raw evolution plans and path lists must stay inside technical details",
);
const decisionButtons = [
  { dataset: { evolutionDecision: "deferred" }, addEventListener(_type, handler) { this.handler = handler; } },
  { dataset: { evolutionDecision: "rejected" }, addEventListener(_type, handler) { this.handler = handler; } },
];
const decisions = [];
ResearchOSMaintenanceWorkbenchService.bindEvolutionDecisionEvents(
  { querySelectorAll() { return decisionButtons; } },
  { onDecision: ({ decision }) => decisions.push(decision) }
);
decisionButtons.forEach((button) => button.handler({ preventDefault() {} }));
assert.deepEqual(decisions, ["deferred", "rejected"]);

console.log("Candidate authority contract regression passed.");
