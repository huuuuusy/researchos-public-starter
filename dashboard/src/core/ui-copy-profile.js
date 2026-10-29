/* ResearchOS maintenance header.
 * 中文：公开版文案配置；两版措辞不同的文案条目只放在这里（每仓一份、内容不同，登记在私有仓 config/edition-parity.json 的 divergent），
 *   其余文案目录（i18n.js、ui-copy*.js、research-portfolio-copy.js、agent-prompt.js）两仓逐字节相同。
 *   i18nOverrides 经 app.js 的 t() 先于 i18n.js 读取；simpleText 合并在 ui-copy.js 末尾；portfolio、agentPrompt
 *   分别由对应文件合并。必须在这些文件之前加载。
 * English: Public-edition copy profile. Copy entries whose wording differs between the editions live only here (one file per
 *   repository with different content, registered as divergent in the private config/edition-parity.json); the other copy
 *   catalogs are byte-identical in both repositories. i18nOverrides is read by app.js t() before i18n.js; simpleText is merged
 *   last in ui-copy.js; portfolio and agentPrompt are merged by their owners. Load it before those files.
 */

(function attachResearchOSUICopyProfile(global) {
  "use strict";

  global.ResearchOSUICopyProfile = Object.freeze({
    i18nOverrides: {
      "zh-CN": {
        "agentBox.depthControlsHint": "读取深度决定任务包包含多少上下文；推理深度是给所选助手的建议。简单任务优先复制到当前会话。",
        "agentBox.localDirect": "系统已按当前任务自动配置读取范围。可运行受控的只读分析；不接受任意命令，长期写回仍需你确认。",
        "autoUpdate.actionHint": "先说明问题和影响；私有版可点击后台安全维护，公开版仅展示状态",
        "intake.howToBody": "点‘复制启动指令’，再发给你选择的助手。助手会先判断读取顺序和安全边界，不会直接改长期记忆。",
        "maintenanceGraph.primaryHint": "告诉你发现了什么、私有版按钮会做什么，以及维护是否成功",
        "sections.agentBoxHint": "这里只生成可复制任务包；不会启动本机 Codex 或远程 API",
        "sections.commandCenterHint": "扫描多个研究承诺；每一项只保留一个当前处置和下一步",
        "sections.commandsHint": "点击即可运行预先登记的本地维护动作；不接受任意命令",
        "sections.todayProcessingHint": "核对当前问题、证据边界与下一安全动作；深度工作交给 Agent 客户端",
        "sections.todayProcessingRecordHint": "仅在需要核对材料、运行状态或历史结果时展开",
        "sections.unifiedInbox": "推进多个研究线程",
        "sections.unifiedInboxHint": "开始或接续工作；公开版只生成可复制任务包，需要人类处置的结果进入对应事项的待复核状态",
        "workspace.agentHint": "查看今天与近期事项",
        "workspace.nowHint": "查看今天与近期事项",
      },
      en: {
        "agentBox.depthControlsHint": "Reading depth controls how much context enters the task packet; reasoning depth is a recommendation for the chosen assistant. Prefer the current conversation for simple work.",
        "agentBox.localDirect": "The reading scope is configured automatically for this task. Run a controlled read-only analysis here; arbitrary commands are rejected and durable writeback still needs confirmation.",
        "autoUpdate.actionHint": "Explains the issue first. Private mode can run safe background maintenance; public mode is view-only",
        "intake.howToBody": "Copy the starter prompt into your chosen assistant. It should decide reading order and safety boundaries before proposing any durable-memory change.",
        "maintenanceGraph.primaryHint": "Explains what was found, what the private-mode action does, and whether maintenance succeeded",
        "sections.agentBoxHint": "Prepare a copy-ready task packet here; no local Codex or remote API is started",
        "sections.commandCenterHint": "Scan several research Commitments; each keeps one disposition and one next step",
        "sections.commandsHint": "Run a registered local maintenance action directly; arbitrary commands are rejected",
        "sections.todayProcessingHint": "Check the current question, evidence boundary, and next safe action; hand deep work to your agent",
        "sections.todayProcessingRecordHint": "Expand only to inspect materials, run state, or prior results",
        "sections.unifiedInbox": "Advance multiple research threads",
        "sections.unifiedInboxHint": "Start or resume work through copyable task packets; results needing human disposition stay local to the relevant work item",
        "workspace.agentHint": "Review today's and upcoming work",
        "workspace.nowHint": "Review today's and upcoming work",
      },
    },
    simpleText: {
      "zh-CN": {
        assetCardDetailResearcherRelation: "和研究者的关系",
        beginnerLlmBody: "把它交给你选择的本地助手，例如 Codex、Claude Code 或 Gemini CLI。它会先解释公开模板的用法和边界，再建议一个最小安全第一步。",
        beginnerLlmPrompt: "我还不知道怎么使用 ResearchOS Public Starter。请你作为第一次上手向导，先读 AGENTS.md 和 docs/user-manual.zh.md 第 2 节，然后用简单中文告诉我：1. 这个项目是做什么的；2. 我现在应该选哪条路线；3. 第一步应该打开哪个文件或运行哪条命令；4. 哪些内容不能放进公开仓库。暂时不要写文件；如果需要信息，最多先问我两个问题。",
        intakeRelatedProjectPlaceholder: "可选：你的项目名 / 研究主题 / 工作包 ...",
        newProjectIntakeEmpty: "当前没有已登记的新项目种子；下次有想法、学生项目或合作者项目进来时，先作为 P0 卡片记录。",
        newProjectIntakeHint: "把自己的想法、学生项目、合作者项目或外部机会先判定为 P0/P1/P2/P3，再决定登记、开沙盒、挂载或独立成项目。",
        researchPlacementArchive: "归档",
        researchPlacementBoundary: "归档区只是默认视图位置；移动或删除文件仍由 Cleanup 审计与回执单独执行。",
        researchPlacementCurrent: "当前",
        researchPlacementIncubating: "孵化",
        researchPlacementPaused: "暂停",
        researchPlacementReview: "待复核",
        researchPlacementTitle: "自动放置",
        researchPlacementWaiting: "等待",
        researchPortfolioCreatePrompt: "登记一个新的个人研究议程事项。先确认它是否由用户主责、是否有独立交付物、时间栏、协助方式和唯一下一步；只返回候选修改，不自动写回。公开版不得读取私人材料或声称已经执行。",
        researchPortfolioHint: "公开版只展示虚构项目；责任、状态和优先级来自公开示例账本。",
        unifiedInboxPublicPrinciple: "待确认区只保留浏览器内候选并生成交接说明，不直接执行或写入仓库；需要只读分析时，请使用处理页或 Agent。",
        workSessionContext: "本轮上下文",
        workSessionConversation: "当前任务",
        workSessionCurrent: "当前任务",
        workSessionCurrentStep: "任务目标",
        workSessionDrafted: "任务已进入下一步；请先检查任务和来源，再选择当前可用的执行方式。",
        workSessionLifecycle_ready: "待选择执行方式",
        workSessionNew: "新建任务",
        workSessionPacketEyebrow: "待执行任务包",
        workSessionPredictionTitle: "点击前先确认",
        workSessionRunDraft: "得到结果",
        workSessionRunDraftHint: "确认当前任务和来源后开始运行；运行前不会调用模型。",
      },
      en: {
        assetCardDetailResearcherRelation: "Relation to researcher",
        beginnerLlmBody: "Give this to a local assistant such as Codex, Claude Code, or Gemini CLI. It asks the assistant to explain the public template, its boundaries, and one smallest safe first step.",
        beginnerLlmPrompt: "I do not know how to use ResearchOS Public Starter yet. Please act as my first-run guide. Read AGENTS.md and Section 2 of docs/user-manual.en.md first, then explain in plain language: 1. what this project is for; 2. which path I should take now; 3. the first file to open or command to run; 4. what I should not put into a public repository. Do not write files yet; ask me at most two questions if needed.",
        intakeRelatedProjectPlaceholder: "Optional: your project / research theme / work package ...",
        newProjectIntakeEmpty: "No project seeds are registered yet. Add the next idea, student project, collaborator project, or external opportunity as a P0 card first.",
        newProjectIntakeHint: "Classify your own ideas, student projects, collaborator projects, or external opportunities as P0/P1/P2/P3 before deciding whether to record, sandbox, mount, or split them.",
        researchPlacementArchive: "Archive",
        researchPlacementBoundary: "Archive is a view region only. File moves and deletion remain separate Cleanup operations with audit receipts.",
        researchPlacementCurrent: "Current",
        researchPlacementIncubating: "Incubating",
        researchPlacementPaused: "Paused",
        researchPlacementReview: "Review",
        researchPlacementTitle: "Automatic placement",
        researchPlacementWaiting: "Waiting",
        researchPortfolioCreatePrompt: "Register a new personally owned Research Agenda item. First confirm that the user owns it, that it has an independent deliverable, its time bucket, support mode, and single next step. Return only a candidate change and do not write it automatically. Public mode must not read private material or claim that execution happened.",
        researchPortfolioHint: "The public starter shows fictional projects only; responsibility, state, and priority come from its public example ledger.",
        unifiedInboxPublicPrinciple: "Review keeps browser-local candidates and generates a handoff brief without executing or writing to the repository; use Next or an Agent for read-only analysis.",
        workSessionContext: "Session context",
        workSessionConversation: "Current task",
        workSessionCurrent: "Current task",
        workSessionCurrentStep: "Task goal",
        workSessionDrafted: "The task is ready in Next. Review the task and sources, then choose an available execution route.",
        workSessionLifecycle_ready: "Choose where to continue",
        workSessionNew: "New task",
        workSessionPacketEyebrow: "Task packet to run",
        workSessionPredictionTitle: "Before you continue",
        workSessionRunDraft: "Get result",
        workSessionRunDraftHint: "Review the task and sources, then start the run. No model is called before this confirmation.",
      },
    },
    portfolio: {
      "zh-CN": {
        researchAttentionEyebrow: "研究承诺",
        researchAttentionHint: "这里安排今天与未来、查看所有活动示例项目，并在原事项附近接续执行或复核。",
        researchAttentionNextSafeAction: "下一安全动作",
        researchAttentionNothingActionable: "当前没有需要你处理的新事项；月历、等待项和全部活动示例项目仍在本页。",
        researchAttentionProjectActions: "更多项目操作",
        researchAttentionScheduleTitle: "其他研究",
        researchAttentionSetReviewHint: "这里只改下一次提醒；要恢复推进，请先在资料页确认项目状态。",
        researchAttentionWhyNow: "为什么现在",
      },
      en: {
        researchAttentionEyebrow: "Research commitments",
        researchAttentionHint: "Schedule today and later work, see every active fictional project, and continue execution or review beside the originating item.",
        researchAttentionNextSafeAction: "Next safe action",
        researchAttentionNothingActionable: "Nothing new needs your attention; the calendar, waiting items, and every active fictional project remain on Now.",
        researchAttentionProjectActions: "More project actions",
        researchAttentionScheduleTitle: "Other research",
        researchAttentionSetReviewHint: "This changes only the next reminder. Confirm the project state in Library before resuming work.",
        researchAttentionWhyNow: "Why now",
      },
    },
    agentPrompt: {
      "zh-CN": {
        inboxTitle: "请使用当前 ResearchOS 项目，处理 ResearchOS 的统一收件箱。",
        inboxPreamble: [],
        inboxRules: [
          "规则：只处理 pending；执行前重读源路径；不能伪造 save_target；private/local-only 材料不能进入公开输出。",
        ],
        inboxReturn: "请返回：读取层级、条目总览、执行顺序、逐条结果、修改文件、验证结果、剩余问题。",
      },
      en: {
        inboxTitle: "Use the current ResearchOS project to process the unified handoff inbox.",
        inboxPreamble: [],
        inboxRules: [
          "Rules: process only pending items; reread source paths before acting; do not invent save targets; keep private/local-only material out of public-facing output.",
        ],
        inboxReturn: "Return: reading level, item overview, execution order, result per item, changed files, validation, and remaining questions.",
      },
    },
  });
})(window);
