/* ResearchOS maintenance header.
 * 中文：验证 Action Gateway 的规格、策略、确认、namespaced owner、回执和插件启停边界。
 * English: Verifies Action Gateway spec, policy, confirmation, namespaced ownership, receipts, and plugin enablement boundaries.
 */

"use strict";

const assert = require("node:assert/strict");
const vm = require("node:vm");

const { read } = require("./helpers/dashboard-vm.js");
const context = { console };
context.window = context;
vm.runInNewContext(read("dashboard/src/core/surface-contract.js"), context);
vm.runInNewContext(read("dashboard/src/services/action-gateway.js"), context);
vm.runInNewContext(read("dashboard/src/services/plugin-runtime.js"), context);

const service = context.ResearchOSActionGateway;
const runtime = context.ResearchOSPluginRuntime;
const feedbackSchema = JSON.parse(read("09_templates/data_contracts/researchos-action-feedback-v1.schema.json"));
const plain = (value) => JSON.parse(JSON.stringify(value));
const safeSpec = {
  actor: "human",
  confirmation: "none",
  effect: "handoff",
  fallback: "show_copy_failure",
  id: "fixture.copy_packet",
  location: "codex",
  reversible: true,
  risk: "low",
  target: "task_packet",
  verb: "copy",
};
const data = {
  plugins: {
    core_api_version: "1",
    schema_id: "researchos-plugin-v1",
    loaded: [{ id: "fixture", version: "1.0.0" }],
    contributions: {
      actions: [{ id: "copy_packet", handler: "copy_task_packet", plugin_id: "fixture" }],
    },
  },
};

async function main() {
  assert.equal(service.create({ interactionContract: {} }).register("fixture", "copy_packet", { execute() {}, spec: safeSpec }), false, "registration must fail closed without the semantic contract owner");
  let executions = 0;
  assert.equal(runtime.registerActionHandler("fixture", "copy_packet", {
    execute: async ({ context: ports, input }) => {
      executions += 1;
      return { copied: ports.copy(input.packet), ok: true };
    },
    handlerId: "copy_task_packet",
    spec: safeSpec,
  }), true);
  assert.equal(runtime.registerActionHandler("fixture", "copy_packet", { execute() {}, handlerId: "duplicate", spec: safeSpec }), false);
  const gateway = service.create({
    authorize: () => ({ allowed: true }),
    confirm: () => true,
    interactionContract: context.ResearchOSInteractionContract,
    gatewayId: "fixture-gateway",
    now: () => "2026-08-13T00:00:00Z",
  });
  assert.equal(runtime.configureActionGateway(gateway), true);
  assert.equal(runtime.configureActionGateway(gateway), false, "the plugin host must have exactly one gateway owner");
  const completed = await runtime.dispatchAction({
    actionId: "copy_packet",
    context: { copy: (value) => value === "bounded packet" },
    data,
    input: { packet: "bounded packet" },
    pluginId: "fixture",
    requestId: "request-1",
  });
  assert.deepEqual(plain(completed), {
    action: { action_id: "copy_packet", plugin_id: "fixture" },
    durability: "ephemeral_ui_feedback",
    effect: "handoff",
    feedback_id: "action-feedback:fixture-gateway:1",
    gateway_instance_id: "fixture-gateway",
    limitations: ["not_durable_receipt", "not_authority", "not_recovery_coordinate"],
    ok: true,
    outcome: { copied: true, ok: true },
    reason: "",
    request_id: "request-1",
    reversible: true,
    schema_id: "researchos-action-feedback-v1",
    sequence: 1,
    status: "completed",
    timestamp: "2026-08-13T00:00:00Z",
  });
  assert.ok(feedbackSchema.required.includes("feedback_id"));
  assert.ok(!feedbackSchema.required.includes("receipt_id"));
  const siblingGateway = service.create({
    authorize: () => true,
    gatewayId: "sibling-gateway",
    interactionContract: context.ResearchOSInteractionContract,
    now: () => "2026-08-13T00:00:00Z",
  });
  siblingGateway.register("fixture", "copy_packet", { execute: async () => ({ ok: true }), spec: safeSpec });
  const siblingFeedback = await siblingGateway.dispatch({ actionId: "copy_packet", pluginId: "fixture", requestId: "request-1" });
  assert.notEqual(completed.feedback_id, siblingFeedback.feedback_id, "gateway instance identity must prevent sequence collisions across mounts or reloads");
  assert.ok(!Object.hasOwn(completed, "receipt_id"), "ephemeral browser feedback must not masquerade as a durable receipt");
  assert.equal(executions, 1);

  const disabled = structuredClone(data);
  disabled.plugins.loaded = [];
  disabled.plugins.contributions.actions = [];
  assert.equal((await runtime.dispatchAction({ actionId: "copy_packet", data: disabled, pluginId: "fixture" })).reason, "action_contribution_unavailable");
  assert.equal(executions, 1, "a disabled contribution must never reach its owner");
  const mismatched = structuredClone(data);
  mismatched.plugins.contributions.actions[0].handler = "forged_handler";
  assert.equal((await runtime.dispatchAction({ actionId: "copy_packet", data: mismatched, pluginId: "fixture" })).reason, "action_handler_mismatch");
  assert.equal((await runtime.dispatchAction({ actionId: "unknown", data, pluginId: "fixture" })).reason, "action_contribution_unavailable");

  const guarded = service.create({ interactionContract: context.ResearchOSInteractionContract, now: () => "fixed" });
  const attentionSpec = { ...safeSpec, confirmation: "inline", effect: "mutate_attention", id: "fixture.schedule", location: "current_surface", target: "attention_date", verb: "schedule" };
  assert.equal(guarded.register("fixture", "schedule", { execute: async () => ({ ok: true }), spec: attentionSpec }), true);
  assert.equal((await guarded.dispatch({ actionId: "schedule", confirmed: true, pluginId: "fixture" })).reason, "policy_owner_missing");
  const inlineGateway = service.create({ authorize: () => true, interactionContract: context.ResearchOSInteractionContract, now: () => "fixed" });
  inlineGateway.register("fixture", "schedule", { execute: async () => ({ ok: true }), spec: attentionSpec });
  assert.equal((await inlineGateway.dispatch({ actionId: "schedule", pluginId: "fixture" })).reason, "confirmation_required");
  assert.equal((await inlineGateway.dispatch({ actionId: "schedule", confirmed: true, pluginId: "fixture" })).status, "completed");

  let confirmations = 0;
  const canonicalSpec = { ...safeSpec, confirmation: "preview_confirm", effect: "mutate_canonical", id: "fixture.complete", location: "review", risk: "high", target: "project", verb: "complete" };
  const cancelledGateway = service.create({
    authorize: () => ({ allowed: true }),
    confirm: () => { confirmations += 1; return false; },
    interactionContract: context.ResearchOSInteractionContract,
    now: () => "fixed",
  });
  cancelledGateway.register("fixture", "complete", { execute: async () => ({ ok: true }), spec: canonicalSpec });
  assert.equal((await cancelledGateway.dispatch({ actionId: "complete", pluginId: "fixture" })).status, "cancelled");
  assert.equal(confirmations, 1);
  assert.equal(gateway.register("fixture", "invalid", { execute() {}, spec: { ...safeSpec, id: "wrong.id" } }), false);
  assert.equal(runtime.unregisterActionHandler("fixture", "copy_packet", "other_owner"), false, "a sibling owner cannot remove a registered handler");
  assert.equal(runtime.unregisterActionHandler("fixture", "copy_packet", "fixture"), true, "handler uninstall must retire both plugin and gateway registrations");
  assert.equal((await gateway.dispatch({ actionId: "copy_packet", pluginId: "fixture" })).reason, "unregistered_action");

  context.ResearchOSResearchPortfolioModel = {};
  context.ResearchOSResearchPortfolioView = {};
  context.ResearchOSResearchPortfolioWorkbench = {};
  context.ResearchOSResearchPortfolioCopy = { text: (_language, key) => key };
  const portfolioCalls = [];
  context.ResearchOSWorkSessionClient = {
    applyAttentionAction: async (item, action) => {
      portfolioCalls.push({ action: action.action, itemId: item.id });
      return { ok: true, undo: { token: "attention-undo" } };
    },
    completePortfolioItem: async (binding) => {
      portfolioCalls.push({ action: "complete_project", itemId: binding.itemId });
      return { ok: true, undo: { token: "project-undo" } };
    },
  };
  vm.runInNewContext(read("dashboard/src/plugins/research-portfolio.js"), context);
  assert.equal(runtime.workItemActionId("research_portfolio", "completeStepActionId"), "complete_portfolio_step", "legacy Work Session bindings must resolve actions through the plugin-owned WorkItem adapter");
  assert.equal(runtime.workItemActionId("research_portfolio", "completeProjectActionId"), "complete_portfolio_project");
  const portfolioManifest = JSON.parse(read("config/plugins/research-portfolio.json"));
  const projectedAction = (id) => ({
    ...portfolioManifest.contributions.actions.find((entry) => entry.id === id),
    plugin_id: "research_portfolio",
  });
  const portfolioActionData = {
    plugins: {
      core_api_version: "1",
      schema_id: "researchos-plugin-v1",
      loaded: [{ id: "research_portfolio", version: portfolioManifest.version }],
      contributions: { actions: [projectedAction("update_portfolio_attention"), projectedAction("complete_portfolio_project")] },
    },
  };
  const attentionReceipt = await runtime.dispatchAction({
    actionId: "update_portfolio_attention",
    confirmed: true,
    context: { language: "en" },
    data: portfolioActionData,
    input: { action: { action: "schedule", attentionDate: "2026-08-14" }, item: { id: "project-1" } },
    pluginId: "research_portfolio",
  });
  assert.equal(attentionReceipt.status, "completed");
  assert.equal(attentionReceipt.outcome.projection_refresh_required, true);
  const projectReceipt = await runtime.dispatchAction({
    actionId: "complete_portfolio_project",
    context: { language: "en" },
    data: portfolioActionData,
    input: { item: { id: "project-1" } },
    pluginId: "research_portfolio",
  });
  assert.equal(projectReceipt.status, "completed");
  assert.deepEqual(portfolioCalls, [
    { action: "schedule", itemId: "project-1" },
    { action: "complete_project", itemId: "project-1" },
  ]);
  const shippedData = JSON.parse(read("dashboard/data/researchos-dashboard.json"));
  const shippedWorkItems = runtime.workItemProviderModels(shippedData)
    .find((provider) => provider.plugin_id === "research_portfolio")?.projection;
  assert.equal(shippedWorkItems?.schema_id, "researchos-work-item-projection-v1");
  assert.equal(shippedWorkItems?.status, "ready", "the shipped Portfolio provider must execute its namespaced adapter instead of exposing raw payload.items");
  assert.ok(shippedWorkItems?.items.every((item) => item.provider_id === "research_portfolio"));

  console.log("Action Gateway contract passed.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
