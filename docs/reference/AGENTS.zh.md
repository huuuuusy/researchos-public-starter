<p align="right">
  <a href="../../AGENTS.md">English</a> | <strong>中文</strong>
</p>

# AGENTS.zh.md

这是 ResearchOS Public Starter 给助手看的入口文件。Codex、Claude Code、Gemini CLI 或其他 LLM 工具在这个仓库里工作时，先读这里。本仓库是一个小型文件化工具的只复制版本，这个工具让研究者的问题、证据、判断和下一步保持相连；随附内容全部是虚构的。

默认文档语言是英文。中文通过成对的 `.zh.md` 文件支持；根目录的 `AGENTS.md` 保留给 Agent 客户端/LLM 自动识别，本文件提供中文说明。

## 首次上手

新用户通常是把 README 里的安装提示粘贴到这个客户端里来的。他们还没读过任何文件，也不需要去读。带他们走下面六步，每次一步：先用一句话说这一步做什么，再运行命令或展示要写的内容，最后用平常话告诉他们发生了什么。对中文用户全程用中文，命令加 `--lang zh-CN`。命令行打印的 `ros …` 都指 `python3 scripts/ros.py --root <文件夹> …`。

1. **讲清楚是什么。** 运行 `python3 --version`（须为 3.10 或更新；Windows 上只能在 WSL 里继续，原生 Windows Python 缺少所需的文件锁）。再运行 `python3 scripts/ros_demo.py --lang zh-CN`，它在一份临时的虚构副本上运行，不改动任何东西。不要把输出原样贴给用户，用三四句话说清它演示了什么：一份来源变了，ResearchOS 标出了依赖它的判断，由研究者决定保留、更新还是挂起，没有研究者的决定，什么都不会成为长期记忆。「还没有准入回执」「复制回退」这类说法在本仓库里是正常的，不是报错。然后运行 `python3 scripts/ros_demo.py --init personal_vault --lang zh-CN`，在 Git 忽略的 `personal_vault/` 里建好用户自己的库。
2. **个人档案。** 请用户给公开主页、Google Scholar、ORCID 或 DBLP 链接，愿意的话再给一份简历。只读用户给的、公开能访问的内容；Google Scholar 常常拦截自动读取，读不到时请用户粘贴论文列表，或改给 ORCID、DBLP 链接，不要绕过登录或拦截。用 `09_templates/person-template.md` 在 `personal_vault/00_identity/profile.md` 起草一张用户自己的卡片，`relationship_type: self`：姓名、单位、研究方向和几项代表作。简历只取科研经历，电话、住址、证件号、推荐人以及与科研无关的内容都不写。
3. **论文。** 请用户挑三到五篇与眼下工作最相关的论文，给链接、DOI 或 PDF。每篇用 `09_templates/paper-template.md` 在 `personal_vault/01_knowledge/papers/<简短英文名>.md` 起草一张卡片：标题、作者、发表处与年份、主要结论、依据的证据，以及公开边界（已发表、预印本或未发表）。只写论文里写了的；自己推断的内容标为候选。
4. **合作者。** 从这几篇论文的作者中，列出出现两次及以上的人，问用户保留哪些。每位选中的人用 `09_templates/person-template.md` 在 `personal_vault/04_people/collaborators/<简短英文名>.md` 起草一张卡片，`relationship_type: candidate`，只写论文能说明的：一起发表过哪几篇。师生、同组、资历、私交这类关系，除非用户亲口说明，否则不写。
5. **一个当前项目。** 问用户现在最想管起来的一个项目：简短的名字、自己主导还是协助、还没解决的问题、下一步具体做什么、建立在上面哪几篇论文之上。在 `personal_vault/06_active_context/research-portfolio.md` 里保留开头的 frontmatter 和标题，把两项虚构承诺换成按回答写成的一项：`id`（简短英文标识）、`responsibility`（`lead` 或 `support`）、`accountable_owner`、`role_summary`、`lifecycle_phase`（例如 `scoping`、`experiment_preparation`、`writing` 或 `revision`；`submitted`、`under_review` 和 `decision` 还需要 `activation_trigger`；全部取值见 `docs/user-manual.zh.md` 第 5 节）、`state: mainline`、`priority: P0`、`question`、`next_step`、`last_verified`（今天）、`stale_after_days: 14` 和 `source_path: 01_knowledge/projects/<id>.md`。删掉两张虚构卡片 `personal_vault/01_knowledge/projects/occlusion-tracking.md` 和 `personal_vault/01_knowledge/papers/example-benchmark.md`，再用 `09_templates/project-template.md` 在 `source_path` 处起草项目卡片：`project_name` 和 `# ` 标题填项目名，`related_papers` 指向它所依据的论文卡片。用户目前的看法写进卡片，标明是眼下的看法；它要以后经用户批准的候选才成为判断。

   第 2 到 5 步的内容写入之前，先把要建的每张卡片和这项承诺列成一张简短清单给用户看，每项一行。用户同意后再写；除非用户说某张卡可以公开，`sensitivity` 一律设为 private，而且只写在 `personal_vault/` 里。
6. **确认能用，讲日常用法。** 运行 `python3 scripts/ros.py --root personal_vault today`：「待判断」下应当只有用户自己的项目，`［未安排］` 是正常的。「任务总表问题」下若有条目，每条都写明字段和可用的值，照着改（改的若是 `today` 已经读过的 `state`、`priority`、`question` 或 `responsibility`，下一次 `today` 会请用户在自己的终端运行 `python3 scripts/ros.py --root personal_vault decide <编号> confirm`，确认这次写入）；再运行 `python3 scripts/ros.py --root personal_vault rules --check`，直到报告「问题 0 条」，最后用 `python3 scripts/ros.py --root personal_vault close` 结束。可以提议运行 `python3 scripts/start_researchos.py --mode personal-vault --port 8881` 打开 Dashboard：「资料」（Library）里是用户的档案、论文和合作者，「现在」（Now）里是这个项目。最后用三句话讲日常怎么用：开始时让这个客户端运行 `today`；工作中照常用客户端，来源变了就更新对应卡片，`today` 会标出依赖它的内容；结束时运行 `close`，只确认值得留下的部分。

第一次保持小规模：一份档案、几篇论文、反复出现的合作者和一个项目。更多论文、人物和项目以后照同样的方式慢慢加，每次几个。不要把用户的材料加入受跟踪的文件，也不要把它或含有它的 clone 推送到任何地方。某一步出错时，[首次上手说明](../../08_exports/public_starter/onboarding-step-by-step.zh.md)写明了每一步应当打印什么、不一样时怎么办，到那时再读它。用户问输出里某个词是什么意思时，用手册第 1 节「你会遇到的词」里的一句话解释。不想建库的用户，也可以在这个客户端里直接给一个目标和一份来源：结果是回答、成果或候选，用户批准前不写入长期记忆（手册第 2 节）。

## 核心理解

ResearchOS 是一个持续维护研究状态、本地为主的系统。它连接问题、证据、判断、责任与下一步，使长期研究在上下文变化时仍可恢复、可理解、可推进。个人研究者可以通过以下有界循环，配合文件感知 Agent 使用它：

```text
研究者目标与来源 -> Agent/CLI 有界读取 -> 回答、成果或 diff
  -> 只有长期记忆可能改变时才提出候选
  -> 研究者批准 -> 验证 -> 已确认记忆
```

主要执行工作流是 Markdown 加文件感知 Agent 或 CLI。刻意收窄的本地 Dashboard 以统一工作台呈现现在与资料两个语义区域：`现在`完整承载 Today、周/月排期、全部活动或等待项目，以及精确事项内 Work/Review 抽屉；`资料`以一项或少量明确 Commitment lens 连接公开安全的来源、人物、claim、证据、thread、artifact 与关系，不承载日历或项目状态。Work 与待复核只在精确事项内区分有界 session 和候选处置。它不是第二个聊天入口，普通 Agent 工作不以它为前置条件，Dashboard 也不拥有判断权。

ResearchOS 以用户素材为基础。不要暗示只靠提示词就能让空库变聪明。先向用户索取当前任务所需的最小来源包，再帮助其逐步扩大素材覆盖，并保持来源、敏感性和确认状态清楚。

## 代码写法

优先在现有函数和模块里就地修改。只有同一段逻辑已经在至少三处真实使用，或者属于安全、权限不变量时，才抽出新的函数、类或模块。不为「以后可能用到」预留抽象层、参数或配置项；不写只转手调用的包装。新增的每一层间接，都要能说出它现在拦下了什么问题。

## 默认行为

不要先扫描整个仓库。面对新用户，先做三件事：

1. 判断路线。
2. 说明隐私、证据和导出边界。
3. 给一个下一步行动。

使用这个短输出形状：

```text
路线：
边界：
我会读取：
下一步：
```

所有持久更新都先保持为候选，等用户确认后再沉淀。

## Token 使用默认规则

默认使用最小读取。很多用户请求只需要先路由，不需要读完整手册。

1. L-1 no-read triage：先判断请求是否需要仓库上下文。
2. L0 route：使用已自动加载的 `AGENTS.md`；如果没有，最多选择一个路由文件。
3. L1 / quick：先用 frontmatter 和 `Agent Summary`，不要直接读全文；然后只读一个任务主文件、capsule 或精确目标。
4. L2 / standard：只加入能解决明确缺口的 workflow、template、case 或 script。
5. L3 / evidence：只为已说明的核验问题加入精确证据或检查项，例如发布审计、bug 修复或用户明确要求的完整检查。

除非用户明确要求（例如双语工作），不要同时读取中英文文件、生成的 dashboard JSON、完整手册或全部模板。回答中说明读取层级，以及哪些文件被刻意不读。

默认使用 `quick` 读取。模型选择和推理深度分开处理：`Auto` 跟随可用运行时目录，用户固定或自定义的模型不得被任务路由暗中替换；`economy / standard / deep` 只建议 `low / medium / high` 等推理投入：简单设置可用 `economy + low`，实质分析通常需要 `standard + medium`，只有复杂的多来源工作才进一步升级。除非设置会影响当前任务，否则保持折叠；明显增加 token 前要告诉用户原因。

各档首轮的文件数与估算 token 上限见[上下文预算协议](CONTEXT_BUDGET_PROTOCOL.zh.md#渐进式上下文契约)。用户给出精确来源或目标路径时直接读取，不重放入口文件。同一任务继续时沿用上一轮 context receipt，只读变化或新需要的文件。文件数或 token 任一超限时，先说明缺口并按具体问题拆批。

## 路线表

| 用户意图 | 先读 | 下一步 |
| --- | --- | --- |
| “帮我开始” | 上面的“首次上手”一节，需要时再读 `08_exports/public_starter/onboarding-step-by-step.zh.md` | 推荐一条第一圈路线：调度器演示、在 Agent 客户端里走一个闭环，或用户自己的 `personal_vault/`。 |
| “让我看看调度器怎么工作” | `docs/user-manual.zh.md`（第 3 节） | 运行 `python3 scripts/ros_demo.py --lang zh-CN`，再提出在 `examples/scheduler-demo` 上逐条命令走一遍。 |
| “我不知道该用对话、dashboard，还是自己的材料” | `docs/user-manual.zh.md`（第 2、4、5 节） | 根据用户背景匹配一条路线，并给一个下一步行动。 |
| “用英文” | `docs/user-manual.en.md` | 后续优先读英文文件。 |
| “让我看 dashboard” | `docs/user-manual.zh.md`（第 4 节）、`scripts/README.md` | 给出 dashboard 启动命令。 |
| “我要放自己的材料” | `docs/user-manual.zh.md`（第 5 节）、`docs/reference/WHERE_TO_PUT_NEW_MATERIALS.zh.md` | 使用 `personal_vault/`：它还不存在时先复制调度器夹具，再加入一项承诺、一份来源和一张候选卡片；用 `--mode personal-vault` 查看本地卡片。不需要关闭示例数据。 |
| “我当前主责推进多少任务？” | personal vault 中的 `06_active_context/research-portfolio.md`，或本启动版的虚构 demo agenda | 先运行 `python3 scripts/query_research_agenda.py`。只统计 `responsibility: lead` 且 `state: mainline`；协作、等待、排队、条件、暂停、需关注和责任未分类状态分开报告。覆盖回执未闭合时只能称为已登记数量；不得从项目数量或最近活动猜责任，也不得把责任缺失/非法的事项默认算作主责。 |
| “创建卡片” | `docs/reference/AGENT_PROTOCOL.zh.md`、`09_templates/` 中的相关模板 | 区分来源事实、候选判断和缺失证据。 |
| “回应外部请求” | `docs/reference/AGENT_PROTOCOL.zh.md`、`05_workflows/research_management/external-demand-response-workflow.zh.md` | 判断请求类型、寻找相关资产、说明边界，只有安全时才起草回复。 |
| “判断关系或机会” | `docs/reference/AGENT_PROTOCOL.zh.md`、`05_workflows/research_management/relationship-opportunity-workflow.zh.md` | 列出已确认事实、候选连接、不能推断什么和一个下一步行动。 |
| “处理 Review 或 handoff” | `docs/reference/AGENT_PROTOCOL.zh.md`、`06_active_context/` 或 `08_exports/public_starter/` 中的相关文件 | 先总结待确认项，再讨论写回。 |
| “修改或调试代码” | `docs/system-reference.zh.md` 中的代码地图，再读一个公开入口和一个 owner 模块 | 先复现，只改 owner，并运行对应 eval。 |
| “增加自己的重复任务” | `docs/governance-guide.zh.md` 中的任务扩展，再读 `config/extensions/method-comparison.example.json` | 优先只加一份声明式 descriptor；不要新建 Work Session、Inbox 或存储路径。 |
| “安装示例插件” | `docs/governance-guide.zh.md` 中的“安装随附示例” | 运行 `python3 scripts/manage_plugins.py install method_comparison`，说明它只在本地、不联网、不写 canonical memory，并确认生成的任务已出现。不要让用户手动复制 manifest。 |
| “检查是否可发布” | `docs/reference/PUBLIC_RELEASE_CHECKLIST.zh.md`、`docs/reference/SAFE_EXPORT_POLICY.zh.md` | 跑验证，检查密钥、本地路径、原始语料和私人材料。 |

`README.zh.md` 是给人看的项目概览。用户问项目定位或文档导航时再读；不是每个任务都必须读。

## 代码与语言路由

代码改动以 `docs/system-reference.zh.md` 中的代码地图为路由权威。不要从生成 JSON 开始，也不要重新创建已删除的兼容代码或旧演示路线。新行为必须有一个已记录 owner、一个公开入口和一个回归测试。

Dashboard 里旧的 `Start / Today / Agent`、`Assets`、`Next / Work`、`Review / Inbox` 路由名只作输入 alias；携带 item 时进入 `Now?item=<id>&panel=<work|review>`，缺少 identity 时失败关闭。

活跃 demo/dashboard 语言在 `config/researchos.runtime.example.json` 的 `public_starter.content_language` 中设置。可用值是 `en` 和 `zh-CN`。

该值是当前生成版本中被冻结的模板语言。只读取 `tasks` 和 `assistant_modes`，不要加载非活跃语言的 prompt/模板变体。切换界面语言不会改变模板语言；只有明确使用 `--language en|zh-CN` 重新生成时，才同步另一语言的 prompt 和模板。

## 安全命令

只有用户要求演示、设置、仪表盘或验证时，才运行这些命令：

```bash
python3 scripts/ros_demo.py --lang zh-CN
python3 scripts/ros.py --root examples/scheduler-demo today
python3 scripts/ros.py --root personal_vault today
python3 scripts/start_researchos.py --mode dashboard --port 8880
python3 scripts/start_researchos.py --mode personal-vault --port 8881
python3 scripts/plan_context.py --list --lang zh-CN
python3 scripts/query_research_agenda.py --language zh-CN
python3 scripts/manage_plugins.py list
python3 scripts/start_researchos.py --mode public-starter --check --provider codex
python3 scripts/build_public_starter_data.py --personal-vault --write
```

`python3 scripts/build_public_starter_data.py --write` 重建受跟踪的 demo 投影，是维护者在 demo 来源改动后的步骤。把虚构案例移出这个投影的可选开关只在用户手册第 5 节说明一次；它同样会重写受跟踪文件，个人库从不需要它。

验证时逐条运行 `.github/workflows/validate.yml` 中的步骤，即本仓库的 CI。

本仓库 默认使用无凭据的 copy-only 交接；普通上手不应该需要真实 API key。Agent 与 Work Session 只生成可复制任务包，不启动本机 Codex、Claude Code CLI 或远程 API。Inbox/canonical 写回保持复制交接，维护命令只接受登记 action ID；受控执行只属于报告中的原型或 personal-vault 模式。personal-vault 是 Dashboard 的模式，不改变 `scripts/ros.py`；出厂 `runtime_scope: public_starter` 下 `ros` 的行为见[用户手册第 3 节](../user-manual.zh.md#3-会话调度器与命令行检查)。

## 安全规则

- 不要把生成的 JSON 或 dashboard data 当作权威来源。它们只是 Markdown 和 demo records 的投影。
- 不要提交密钥、provider token、原始语料、未公开论文、敏感人物笔记、本地机器路径或运行日志。
- 不要从弱证据推断私人关系、指导关系、学生身份、实验室身份、贡献层级或未来承诺。
- 没有清晰用户意图时，不要运行 Codex CLI handoff、真实 provider/API 调用或会写文件的命令。
- 状态轴必须分开：证据状态使用 `candidate` / `needs_evidence`，敏感性或导出边界使用 `local_only` / `public_safe` / `not_exportable`。

## 可以建议用户先说

如果用户不知道怎么开始，建议他说（与用户手册第 2 节是同一段提示词）：

```text
我还不知道怎么使用 ResearchOS Public Starter。请你作为第一次上手向导，先只读 AGENTS.md；如果环境已经加载该文件，不要重读，也不要扫描仓库。然后用简单中文告诉我：1. 这个项目是做什么的；2. 我现在应该选哪条路线；3. 下一个文件或命令；4. 哪些内容不能放进公开仓库。暂时不要写文件；如果需要信息，最多先问我两个问题。
```
