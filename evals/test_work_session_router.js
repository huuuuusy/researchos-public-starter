const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const context = { window: {} };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, "dashboard/src/services/task-intent.js"), "utf8"), context);
vm.runInContext(fs.readFileSync(path.join(root, "dashboard/src/services/work-session-router.js"), "utf8"), context);

const Router = context.window.ResearchOSWorkSessionRouter;

assert.equal(Router.inferResponseMode("请读这篇 PDF 并告诉我主要问题"), "answer");
assert.equal(Router.inferResponseMode("请整理成 Markdown 阅读笔记"), "artifact");
assert.equal(Router.inferResponseMode("把这个判断写回长期记忆"), "writeback");
assert.equal(Router.inferResponseMode("帮我再更新和沉淀一下"), "writeback");
assert.equal(Router.inferResponseMode("只回答", "artifact"), "artifact");

assert.equal(Router.taskModeForResponseMode("answer"), "read_only_analysis");
assert.equal(Router.taskModeForResponseMode("artifact"), "direct_execution");
assert.equal(Router.taskModeForResponseMode("writeback"), "candidate_patch_plan");

assert.equal(Router.recommendTaskComplexity({ intent: "这是什么状态" }), "standard");
assert.equal(Router.recommendTaskComplexity({ intent: "归档这些状态" }), "economy");
assert.equal(Router.recommendTaskComplexity({ intent: "阅读并分析论文", sourceHints: ["paper.pdf"] }), "standard");
assert.equal(Router.recommendTaskComplexity({ intent: "全面重构整个交互架构" }), "deep");
assert.equal(Router.recommendReasoningEffort({ intent: "今天最值得推进什么" }), "low");
assert.equal(Router.recommendReasoningEffort({ intent: "阅读并分析论文", sourceHints: ["paper.pdf"] }), "medium");
assert.equal(Router.recommendReasoningEffort({ intent: "全面重构整个交互架构" }), "high");
assert.equal(Router.contextRoute({ intent: "今天应该做什么" }), "current_state");
assert.equal(Router.contextRoute({ intent: "理解这篇论文", sourceHints: ["paper.pdf"] }), "session_sources");
assert.equal(Router.contextRoute({ intent: "全面审计当前架构" }), "deep_audit");

const session = {
  id: "work-1",
  intent: "判断这篇论文的核心贡献是否成立",
  sourceHints: ["/tmp/paper.pdf"],
  evidenceBoundary: "只读取，不写回",
  templateLanguage: "zh-CN",
};
const prompt = Router.buildPrompt(session);
assert.ok(prompt.includes("/tmp/paper.pdf"));
assert.ok(prompt.includes("不要创建或修改文件"));
assert.ok(prompt.includes("完整、可读的结果返回当前助手会话"));
assert.ok(prompt.includes("上下文路由：session_sources"));
assert.ok(prompt.includes("首批最多 3 个"));
assert.equal(
  Router.sourceLines({ cards: [{ typeLabel: "Input source", title: "/tmp/paper.pdf", path: "/tmp/paper.pdf" }] })[0],
  "- Input source: /tmp/paper.pdf",
  "source labels must not repeat the same path as both title and path"
);
assert.ok(
  Router.buildPrompt({ ...session, intent: "请用一句话回答" }).includes("只返回一句完整的话"),
  "explicit one-sentence requests must override the default evidence structure"
);
assert.ok(
  Router.buildPrompt({ ...session, intent: "Please answer briefly" }).includes("直接给结论"),
  "explicit concise requests must suppress unnecessary answer scaffolding"
);
const englishPrompt = Router.buildPrompt({
  ...session,
  intent: "Please answer briefly",
  templateLanguage: "en",
});
assert.ok(englishPrompt.includes("User goal: Please answer briefly"), "English content mode must localize task-packet labels");
assert.ok(englishPrompt.includes("The user explicitly requested a concise answer"), "English content mode must localize response-shape instructions");
assert.ok(!englishPrompt.includes("用户目标"), "English task packets must not retain Chinese prompt labels");
assert.ok(englishPrompt.includes("Context route: session_sources"), "English task packets must localize the bounded context route");

const currentStatePrompt = Router.buildPrompt({ intent: "请告诉我今天最值得推进的一项工作" });
assert.ok(currentStatePrompt.includes("上下文路由：current_state"));
assert.ok(currentStatePrompt.includes("06_active_context/research-portfolio.md"));
assert.ok(currentStatePrompt.includes("不读取带日期的旧看板、计划或审计"));
const publicCurrentStatePacket = Router.publicTaskPacket({
  intent: "What should I do today?",
  templateLanguage: "en",
});
assert.ok(publicCurrentStatePacket.answer.includes("does not own your private current state"));
assert.ok(!publicCurrentStatePacket.answer.includes("06_active_context/research-portfolio.md"));
assert.ok(!publicCurrentStatePacket.answer.includes("06_active_context/current-projects.md"));
const customModelPacket = Router.publicTaskPacket({
  intent: "Compare these methods",
  templateLanguage: "en",
}, {
  model: "company/public-model",
  reasoning: "high",
});
assert.ok(customModelPacket.answer.includes("Execution preference (not run on this page)"));
assert.ok(customModelPacket.answer.includes("- Model: company/public-model"));
assert.ok(customModelPacket.answer.includes("- Reasoning: high"));
assert.equal(customModelPacket.model, "company/public-model");
assert.equal(customModelPacket.reasoning_effort, "high");
const chinesePacket = Router.publicTaskPacket({
  intent: "审查证据边界",
  templateLanguage: "zh-CN",
});
assert.ok(chinesePacket.answer.includes("## 任务包已准备好"));
assert.ok(chinesePacket.answer.includes("回答语言：zh-CN"), "a Work Session created in the Chinese UI must keep a Chinese task packet");
assert.ok(chinesePacket.answer.includes("中等（medium）"));
assert.ok(chinesePacket.answer.includes("标准（standard）"));
assert.ok(!chinesePacket.answer.includes("Response language: en"));

const followupPrompt = Router.buildPrompt({
  ...session,
  goal: session.intent,
  intent: "那它最薄弱的证据是什么？",
  turns: [{ question: session.intent, answer: "核心贡献成立，但外部效度证据有限。" }],
});
assert.ok(followupPrompt.includes(`任务目标：${session.intent}`), "follow-up prompts must preserve the original objective separately from the current instruction");
assert.ok(followupPrompt.includes("当前处理要求：那它最薄弱的证据是什么？"));
assert.ok(followupPrompt.includes("本任务先前步骤"), "follow-up prompts must carry bounded prior steps");
assert.ok(followupPrompt.includes("外部效度证据有限"), "follow-up prompts must include the prior answer");
assert.equal(Router.conversationLines({
  turns: Array.from({ length: 9 }, (_, index) => ({ question: `Q${index}`, answer: `A${index}` })),
}).length, 6, "prompt history must use only the latest six turns");
const publicHistory = Router.conversationLines({
  turns: [{
    answer: "## Copy-ready task packet\nDo not nest this payload",
    includeInPrompt: false,
    question: "Compare these two papers",
  }],
});
assert.equal(publicHistory[0], "先前处理要求：Compare these two papers", "public follow-ups must retain prior instructions without nesting old task packets");
assert.ok(!publicHistory[0].includes("Copy-ready task packet"), "public task packets must not recursively expand prompt history");
assert.equal(
  Router.conversationLines({ turns: [{ answer: "ignored", includeInPrompt: false, question: "Compare two papers" }] }, "en")[0],
  "Prior instruction: Compare two papers",
  "English public follow-ups must localize prior-intent context"
);

const runnerPayload = Router.runPayload({
  ...session,
  clientRequestId: "request-router",
  turns: [{ answer: "Visible prior answer", question: session.intent, runId: "run-visible" }],
}, {
  artifactFromResult: true,
  promptSuffix: "Create the requested Markdown artifact.",
  responseMode: "artifact",
}, {
  language: "en",
  runs: [],
  selectedModel: "gpt-5.6-sol",
  selectedReasoning: "high",
  text: (key) => key,
});
assert.equal(runnerPayload.task_mode, "direct_execution", "artifact requests must keep their runner task mode in the router owner");
assert.equal(runnerPayload.candidate.candidate_type, "work_session", "artifact execution must use the registered Work Session entry type");
assert.equal(runnerPayload.candidate.proposed_action.id, "work_session_artifact", "artifact execution must request the fixed server action id");
assert.equal(runnerPayload.candidate.proposed_writeback.save_target, "", "client candidates must not declare the server-owned write root");
assert.equal(runnerPayload.candidate.proposed_writeback.object_path, "", "an artifact path does not exist before server staging");
assert.equal(runnerPayload.task_complexity, "auto");
assert.equal(runnerPayload.recommended_task_complexity, "standard");
assert.equal(runnerPayload.model, "gpt-5.6-sol");
assert.equal(runnerPayload.reasoning_effort, "high");
assert.equal(runnerPayload.recommended_reasoning_effort, "medium");
assert.equal(runnerPayload.task_intent.client_request_id, "request-router", "the persisted pre-dispatch correlation must enter TaskIntent unchanged");
assert.equal(runnerPayload.task_intent.schema_id, "researchos-task-intent-v1");
assert.equal(runnerPayload.task_intent.input_trust, "untrusted");
assert.equal(runnerPayload.task_intent.goal, session.intent);
assert.equal(runnerPayload.task_intent.instruction, session.intent);
assert.equal(runnerPayload.task_intent.client.task_ref, "work-1");
assert.equal(runnerPayload.task_intent.requested_result.mode, "artifact");
assert.equal(runnerPayload.task_intent.requested_profile.model, "gpt-5.6-sol");
assert.equal(runnerPayload.task_intent.requested_profile.reasoning_effort, "high");
assert.deepEqual(
  Object.keys(runnerPayload).filter((key) => key !== "task_intent"),
  [
    "source", "task_mode", "response_mode", "work_session_id", "task_complexity", "model",
    "recommended_task_complexity", "reasoning_effort", "recommended_reasoning_effort", "title", "prompt", "candidate",
  ],
  "TaskIntent v1 must be additive to the legacy runner payload",
);
assert.ok(runnerPayload.prompt.includes("Visible prior answer"), "artifact creation must retain the latest visible answer after app extraction");
const craftedArtifactPayload = Router.runPayload({
  ...session,
  candidate: {
    candidate_type: "arbitrary",
    proposed_action: { id: "shell" },
    proposed_writeback: { save_target: "/tmp/escape.md", object_path: "/tmp/forged.md" },
  },
}, { responseMode: "artifact" }, { language: "en", text: (key) => key });
assert.equal(craftedArtifactPayload.candidate.candidate_type, "work_session");
assert.equal(craftedArtifactPayload.candidate.proposed_action.id, "work_session_artifact");
assert.equal(craftedArtifactPayload.candidate.proposed_writeback.save_target, "");
assert.equal(craftedArtifactPayload.candidate.proposed_writeback.object_path, "");

const defaultPayload = Router.runPayload({ id: "work-current", intent: "今天最值得推进什么" }, {}, {
  language: "zh-CN",
  selectedModel: "auto",
  selectedReasoning: "auto",
  text: (key) => key,
});
assert.equal(defaultPayload.recommended_task_complexity, "standard");
assert.equal(defaultPayload.model, "auto");
assert.equal(defaultPayload.recommended_reasoning_effort, "low");

const runs = [
  { id: "old", work_session_id: "work-1", status: "completed" },
  { id: "latest", work_session_id: "other", status: "completed" },
];
assert.equal(Router.resultForSession(runs, { id: "work-1", latestRunId: "old" }).id, "old");

const outOfOrderRuns = [
  { id: "older-same-session", work_session_id: "work-1", status: "completed" },
  { id: "newest-same-session", work_session_id: "work-1", status: "completed" },
];
assert.equal(
  Router.resultForSession(outOfOrderRuns, { id: "work-1", latestRunId: "newest-same-session" }).id,
  "newest-same-session"
);

console.log("Work session router regression passed.");
