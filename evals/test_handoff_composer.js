/* ResearchOS maintenance header.
 * 中文：冻结 projection-first UI 的 Codex handoff 编译合同；验证现有 owner 被组合而非复制。
 * English: Freezes the projection-first UI Codex handoff composition contract by composing existing owners rather than duplicating them.
 */

"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const context = { console, crypto: crypto.webcrypto, TextEncoder };
context.window = context;
context.ResearchOSWorkSessionState = {
  taskIdentityProjection: (session = {}) => Object.freeze({
    identity_kind: "portfolio_item",
    item_id: session.portfolioBinding?.itemId || "",
    logical_task_id: `task:${session.portfolioBinding?.itemId || "unbound"}`,
    next_step_signature: session.portfolioBinding?.nextStepHash || "step:unknown",
    provider_id: session.portfolioBinding?.providerId || "research_portfolio",
    session_id: session.id || "",
  }),
};
vm.createContext(context);
[
  "dashboard/src/services/task-intent.js",
  "dashboard/src/services/context-pack-projection.js",
  "dashboard/src/services/work-session-router.js",
  "dashboard/src/services/handoff-composer.js",
].forEach((file) => vm.runInContext(read(file), context, { filename: file }));

const Composer = context.ResearchOSHandoffComposer;
const plain = (value) => JSON.parse(JSON.stringify(value));

function handoffReceipt() {
  return Object.freeze({
    contentState: "included",
    forbiddenActions: Object.freeze({
      state: "recorded",
      items: Object.freeze(["不修改 Public", "不 commit"]),
    }),
    handoffId: `handoff:${"a".repeat(64)}`,
    lastJudgment: Object.freeze({ state: "human_recorded", text: "UI 只是 canonical state 的投影。" }),
    limitations: Object.freeze(["projection_not_authority", "target_not_delivery", "no_transcript"]),
    nextSafeAction: Object.freeze({ state: "recommended", text: "实现并验证两个纯模块。" }),
    openBoundary: Object.freeze({ state: "recorded", text: "P5 真人价值尚未验证。" }),
    runtimeScope: "private",
    sourceRevision: Object.freeze({ state: "verified", source_id: `src:${"b".repeat(64)}`, value_digest: "c".repeat(64) }),
    targetClient: Object.freeze({ kind: "codex", surface: "desktop", binding_state: "requested" }),
    taskId: `task:${"d".repeat(64)}`,
  });
}

function fixture() {
  return {
    session: {
      cards: [
        { id: "asset:paper", path: "01_knowledge/papers/example.md", title: "Example paper", type: "paper" },
        { id: "asset:plan", path: "06_active_context/example-plan.md", title: "Example plan", type: "plan" },
      ],
      evidenceBoundary: "只读现有 owner；只写当前 implementation slice。",
      goal: "完成 projection-first UI 的交接核心",
      id: "work:projection-handoff-v1",
      intent: "实现 Handoff Composer 和 Thread Router，并给出 focused tests。",
      portfolioBinding: {
        itemId: "researchos-ui",
        nextStep: "完成 P1-P4",
        nextStepHash: "step:projection-handoff",
        providerId: "research_portfolio",
        sourcePath: "06_active_context/example-interface-plan.md",
        title: "ResearchOS UI",
      },
      responseMode: "artifact",
      sensitivity: "private",
      templateLanguage: "zh-CN",
    },
    selection: {
      authority: "canonical Markdown / Git + researcher confirmation",
      definitionOfDone: ["focused tests pass", "Public paths remain unchanged"],
      excluded: [{ reason: "out_of_scope", scope: "Public UI" }],
      primaryProject: {
        id: "researchos-ui",
        path: "06_active_context/example-interface-plan.md",
        reason: "当前 implementation owner",
        title: "ResearchOS UI",
      },
      relatedProjects: [{ id: "researchos-core", path: "START_HERE.md", reason: "保持无 UI 核心闭环", title: "ResearchOS Core" }],
      saveTarget: "dashboard/src/services/",
    },
    handoffReceipt: handoffReceipt(),
    route: {
      fallback_route: "copy_only",
      intended_route: "continue_exact_thread",
      reason_codes: ["same_bounded_episode", "transport_unavailable"],
      recommended_route: "copy_only",
      thread_id: "thread:exact-1",
      transport_state: "unavailable",
    },
  };
}

async function main() {
  const result = await Composer.compose(fixture());
  const duplicate = await Composer.compose(fixture());
  assert.equal(result.digest, duplicate.digest, "the same bounded handoff must have a deterministic digest");
  assert.match(result.digest, /^[0-9a-f]{64}$/);
  assert.equal(result.envelope.schema_id, "researchos-ui-handoff-envelope-v1");
  assert.equal(result.envelope.authority_state, "projection_not_authority");
  assert.equal(result.envelope.task_intent.schema_id, "researchos-task-intent-v1");
  assert.equal(result.envelope.task_intent.input_trust, "untrusted");
  assert.equal(result.envelope.context_pack.schema_id, "researchos-context-pack-projection-v1");
  assert.equal(result.envelope.context_pack.task.item_id, "researchos-ui");
  assert.equal(result.envelope.context_pack.included.length, 2);
  assert.deepEqual(plain(result.envelope.route.reason_codes), ["same_bounded_episode", "transport_unavailable"]);
  assert.equal(result.envelope.route.recommended_route, "copy_only");
  assert.equal(result.envelope.requested_result.mode, "artifact");
  assert.equal(result.envelope.requested_result.save_target, "dashboard/src/services/");
  assert.match(result.markdown, /## Agent 交接包/);
  assert.match(result.markdown, /ResearchOS UI/);
  assert.match(result.markdown, /ResearchOS Core/);
  assert.match(result.markdown, /01_knowledge\/papers\/example\.md/);
  assert.match(result.markdown, /明确排除/);
  assert.match(result.markdown, /Public UI/);
  assert.match(result.markdown, /UI 只是 canonical state 的投影/);
  assert.match(result.markdown, /P5 真人价值尚未验证/);
  assert.match(result.markdown, /不修改 Public/);
  assert.match(result.markdown, /continue_exact_thread/);
  assert.match(result.markdown, /copy_only/);
  assert.match(result.markdown, /focused tests pass/);
  assert.ok(!result.markdown.includes("authority_granted"), "a browser handoff must not manufacture authority");
  assert.equal(Object.isFrozen(result), true);
  assert.equal(Object.isFrozen(result.envelope), true);

  await assert.rejects(
    () => Composer.compose({
      ...fixture(),
      selection: {
        ...fixture().selection,
        excluded: [{ reason: "conflict", scope: "01_knowledge/papers/example.md" }],
      },
    }),
    (error) => error.code === "handoff_source_conflict",
    "an included source may not also be explicitly excluded",
  );

  console.log("OK: projection-first handoff composer stays deterministic, exact, previewable, and non-authoritative");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
