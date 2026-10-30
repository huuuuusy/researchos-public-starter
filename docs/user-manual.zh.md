<p align="right">
  <a href="user-manual.en.md">English</a> | <strong>中文</strong>
</p>

# ResearchOS 用户手册

这份手册按读者的使用顺序展开：本仓库是什么、输出里的词是什么意思，怎样在 Agent 客户端里走一个研究闭环，怎样试用会话调度器，可选 Dashboard 显示什么，以及怎样用自己的材料替换虚构 demo。第一次上手请按[首次上手说明](../08_exports/public_starter/onboarding-step-by-step.zh.md)走，本手册是它背后的参考。状态、治理边界、架构、代码 owner 和目录的定义见[系统参考](system-reference.zh.md)；发布、自定义、插件、贡献与许可见[治理与扩展指南](governance-guide.zh.md)。

## 1. 本仓库是什么

ResearchOS Public Starter 是一个面向个人科研人员的小型文件化工具的公开安全参考实现，用来让判断在工具、项目和时间之间保持连续。Claude Code、Codex 等 Agent 客户端或其他文件感知 CLI 是主要执行路线，也是完整的默认路线：给出一个目标和最少来源，得到回答或成果，长期变化留在你的批准与验证之后。第一圈不需要 Dashboard、插件、模型设置，也不需要先理解整个仓库。可选 Dashboard 让注意力、关联资料和审阅边界可见，但不替研究者接受判断，也不扩大执行权限。

研究者选择问题，判断证据究竟支持什么；模型和工具完成有边界的局部工作；ResearchOS 把结果与来源、接受状态、未决依赖和下一动作连在一起，某份来源变化后，依赖它的判断会回来等待复核。它不是托管服务、自治科研系统、完整个人知识库、脱离证据的万能问答，也不是精致的 all-in-one 产品；空 vault 不会替你理解一个研究领域。文献检索、实验执行和通用 Agent runtime 交给专门工具；相邻工具以及 ResearchOS 为什么保持窄定位，见[相关科研工具](reference/RELATED_RESEARCH_TOOLS.zh.md)。

本次发布是只复制版本。它与技术报告中的原型共享内核，随附虚构数据，`config/ros.json` 设为 `runtime_scope: public_starter`：它可以阅读、校验、准备交接、显示拟议变化，但不能声称工作已经执行或长期记忆已经改变。注意力写入、准入写回、维护写入和完成记录仍属于报告中的原型。[技术报告](technical-report.zh.md)描述的就是这个原型，其执行路径比本版更广，其中的主张不是本仓库能力清单。下表对比运行这套代码的三种方式：

| 能力 | 本仓库 | personal-vault 模式（第 5 节） | 报告中的原型 |
| --- | --- | --- | --- |
| 数据 | 虚构、公开安全 | git 忽略的 `personal_vault/` 下你的真实材料 | 你的真实本地研究材料 |
| 项目组合、任务处理和资料卡片 | 有 | 有 | 有 |
| 即时结果 | 只生成可复制任务包；不在页面内执行 | 由本机 Codex 给出的页面内本地回答或成果 | 页面内本地回答或成果 |
| 待复核动作 | 只交接候选，不执行持久写回 | 复制或受控执行 | 复制或受控执行 |
| 本地 runner 和执行设置 | 不启动本机 runner；仅登记维护动作 | 本机安装的 Codex CLI，只写 `personal_vault/` | 支持 workspace-write 的受控执行 |
| 私人系统联动 | 不包含：不发现、不调用、不共享运行态 | 不包含 | 只属于私人部署，并服从本地 authority |
| 长期写回 | 无 | Dashboard 经你确认后写入 `personal_vault/`；`ros` 仍只复制 | 只有研究者批准并验证后才允许，包括 `ros admit` |
| 公开导出 | demo 安全内容 | 必须单独经过 safe-export 复查 | 必须单独经过 safe-export 复查 |

需要 Python 3.10 或更高版本；使用 Dashboard 时还需要现代浏览器。CI 在 CPython 3.10 和 3.13 上测试。无需安装任何东西：不需要 Python 包、API key、数据库、Node.js、服务器或云账号。通过 Git、GitHub Desktop 或 GitHub 的 **Download ZIP** 获取仓库，在仓库文件夹中打开终端，使用 `python3`。支持 macOS 与 Linux；Windows 请在 WSL（Windows Subsystem for Linux）中运行，因为它依赖的文件锁在原生 Windows 的 Python 中不可用。真实、敏感或未公开的材料不要放进受跟踪的文件；它们该放在哪里见第 5 节。

### 你会遇到的词

演示输出和这几份指南里，有几个词用的是特定意思。第一次上手，看每个词旁边那一句就够了；[技术报告](technical-report.zh.md)用的是同一套词，并给出精确定义。

| 词 | 在这里指什么 |
| --- | --- |
| 承诺（commitment） | 一个项目当前的那一个下一步或下一个判断，写在 `06_active_context/research-portfolio.md` 里。被排期的是它，而不是整个项目。 |
| 卡片（card） | 一份带 frontmatter 的 Markdown 文件，记一个项目、一篇论文、一个人或其他来源。承诺和判断都以卡片为依据。 |
| 研究状态 | 问题、证据、已接受的判断及其范围、仍未决的条件，以及下一步。`ros state` 把它们印成 Q、E、J、B、N。 |
| 候选（candidate） | 还没有被接受的模型产出或草稿。 |
| 准入（admission / admit） | 研究者把候选接受进研究状态。本仓库只显示计划中的改动，从不准入。 |
| 判断块 | 记录一条已接受判断及其依据的 `> [!judgment]` Markdown 块。 |
| 要求（requirement） | 一件登记在册的维护工作，例如来源变化后复核某条判断。 |
| 挂起与等待 | 挂起的工作在等研究者回答一个问题；等待的工作在等一个触发条件，比如某个日期。 |
| 回执（receipt） | 做了什么、查了什么的记录。 |
| 决策边界 | 系统查看已到达的内容、决定下一步的时刻。输出里叫「ros 边界」。 |
| 复制回退、只复制 | 本仓库只准备好文字，由你复制到自己的助手里，它自己不运行、也不写入任何东西。 |
| `personal_vault/` | clone 里被 Git 忽略的文件夹，放你自己的材料。 |

演示输出里有三种说法由这些词而来，都不是报错。「还没有准入回执」是说夹具里的判断是直接写进文件的：没有人准入过它，所以没有准入的回执，`today` 会请你确认它。「已事后确认」后面跟着「不算准入」或「未经准入」，是说你对一条已经写进去的判断点了头；这只关闭「请确认」这个请求，并没有准入任何东西。「复制回退」是说 `ros` 把 `admit` 会做的改动以 diff 的形式打印出来，什么都没写。

## 2. 在 Agent 客户端里走一个闭环

用 Claude Code、Codex、Gemini CLI 或其他文件感知助手打开本文件夹。第一次只需要四件事：目标，即现在要回答、整理或产出什么；来源，即一份你提供的材料或一个明确公开链接；结果，即回答、可打开的成果文件或可核对的 diff；边界与下一步，即哪些是来源事实、哪些仍是候选、接下来做什么。不确定从哪里开始，或者还不会用终端时，先让助手带你走，只复制它给出的命令：

```text
我还不知道怎么使用 ResearchOS Public Starter。请你作为第一次上手向导，先只读 AGENTS.md；如果环境已经加载该文件，不要重读，也不要扫描仓库。然后用简单中文告诉我：1. 这个项目是做什么的；2. 我现在应该选哪条路线；3. 下一个文件或命令；4. 哪些内容不能放进公开仓库。暂时不要写文件；如果需要信息，最多先问我两个问题。
```

有具体任务时，直接交出来源：

```text
我这里有一份 PDF：[链接或本地路径]。它是：[公开 / 在投 / 内部 / 边界不清楚]。

请用 ResearchOS 帮我理解它，并把它和[我的任务]联系起来。先读 AGENTS.md，只补充读取当前任务需要的最小工作流或目标文件。请返回材料边界、短阅读笔记、候选判断、建议保存位置和需要我确认的内容。在我批准候选内容和证据边界之前，不要写入长期记忆。
```

助手应说明读了什么、有意没读什么，哪条路线合适，涉及什么隐私或导出边界，以及结果是普通回答、成果还是拟议的长期变化。合格的阅读笔记给出来源事实、候选解释、一个限制、一个缺失事实和一个下一动作，并分清来源支持什么、什么仍未测试。

普通回答已经够用就停；无论如何，能指出来源、候选、未决条件和下一安全动作即可停。只有存在值得保留的长期增量和明确保存目标时才保留候选；批准与验证仍是独立步骤。想接着用自己的材料，按第 5 节操作，并告诉助手在你确认前不写文件。

下面这些不进入第一次使用，第一个闭环跑通后它们仍然可用：插件 marketplace 与安装教学、系统地图与完整架构、维护命令与代码、全量人物关系图、强制模型或 provider 配置，以及一次导入全部论文、项目和关系记录。

不用 Dashboard 时，路线固定为：

```text
目标 + 最少来源
  -> 有边界的 Agent 客户端工作或确定性 CLI 动作
  -> answer | artifact | writeback candidate
  -> 研究者核对来源、未知、敏感性和实际效果
  -> 可选的已批准 mutation -> validation -> receipt -> rollback coordinate
```

四条规则守住这个闭环：Agent 输出首先是候选内容；任务完成不等于证据确认；Dashboard 和生成 JSON 是投影，不是权威来源；私人材料必须单独经过公开审查才能进入公开导出。这些规则背后的工作流、证据、权威和敏感性状态见[状态与权威模型](system-reference.zh.md#状态与权威模型)；来源路径只表示输入证据，从来不是保存目标。

### 保持读取范围小

读取档位同时限制首轮文件数和估算 token：

| 档位 | 首轮文件 | 估算总 token | 适用场景 |
| --- | ---: | ---: | --- |
| `Quick` | 1 | 约 10k | 已有精确来源或窄问题。 |
| `Standard` | 最多 5 | 约 35k | 需要一个 workflow 和少量项目背景。 |
| `Evidence` | 最多 8 个定向文件 | 约 60k | 正式 claim 或公开输出需要核证。 |

默认从 `Quick` 开始；给出精确论文、草稿或目标路径时，Quick 直接从那里开始。Standard 可以加入一个 workflow、项目页和少量 canonical 文件；Evidence 只加入能回答当前核验问题的 audit、reading note 或来源文件。只有能说清缺少哪个事实或判断时才升档；文件数或 token 将要超限时，缩小文件子集并分批处理。这样能减少 token 和无关信息，同时保留长期资料库的完整性。读取档位与推理投入解决不同问题：缺少上下文时提高读取档位，判断链复杂时在 Agent 客户端提高推理投入。模型与推理投入属于 Agent 客户端或已配置的本地运行时；输出类型（回答、成果或写回候选）由任务和结果协议自动判断，不需要你预先分类。开放讨论、推理和起草直接在助手里按仓库说明进行，不需要交接。

### 来源被纠正后保住什么

下面的虚构比较沿用[报告第 4.1 节的贯穿会话](technical-report.zh.md)，展示来源更正前后的状态。受影响部分由候选说明、研究者决定；原型不会自动计算局部语义影响。

| 阶段 | 来源、判断与未决条件 | 核对什么 |
| --- | --- | --- |
| 变化前 | 两组基准支持目标在画面内时 A 优于 B；重新出现后的情况未测试，实验已计划 | 根据、范围、未知与下一动作一起保留 |
| 来源更正 | 第二组上 A 的优势消失，第一组不变 | 来源变化触发复核，不裁定科学判断 |
| 候选 | 连同根据保留第一组说法，撤回第二组说法，让重新出现的实验继续开着 | 基于更正后的来源版本审阅候选 |
| 决定边界 | 报告中的原型只在研究者决定后准入；本仓库默认只准备候选或拟议差异，不实际准入 | 分清拟议变化与已接受的长期状态 |

![构建系统自己重建，研究状态等研究者决定。](figures/architecture/researchos-r9-contrast-zh.png)

*报告图 1。构建系统自己重建，研究状态等研究者决定。论文的第二组基准被更正后，判断 J 来自第一组的根据保留，来自第二组的根据要复核；未决的重新出现条件仍然悬着，另一个会话提出、论文并不支持的说法被拒绝。只有研究者的准入才写入。*

第 3 节可运行的公开检查使用另一份虚构夹具，不执行报告中的准入或局部收窄。两个例子都不证明优于版本化交接。

### 中断后接续

需要跨中断保留有价值的工作时，在 `personal_vault/` 中保留成果和一份简短交接：问题；来源及版本；最后确认的判断（没有就写无）；候选及其未解决边界；下一安全动作；实际的决定、修改与验证证据。交接不授权把候选升级为正典。回来后先复核变化的来源再继续；既有有效授权在原范围内继续适用，不因流程换阶段而重复询问。

回执不需要 Dashboard 或浏览器状态就能读取和核对。`receipt_cli.py validate` 和 `inspect` 只检查结构，输出区分 asserted states 与 checked states：生产者可信度未验证，来源新鲜度未检查，人类决定未认证。旧回执在来源更新后仍可读取，但不能证明当前文件与当时相同。从交接继续之前，运行

```bash
python3 scripts/receipt_cli.py --root . recheck-source --input handoff.json --source result.md
```

并传入构建交接时同一个相对文件引用。命令核对身份和当前哈希，拒绝缺失、已变更或错配的来源；哈希相符既不认证回执作者，也不认证人类决定。把结果文件、任务计划（含扩展版本和 resume 命令）与交接放在一起；它们是产物和证据，不自动成为已准入记忆。

不同 runtime 的任务族 ID 不能当作完全相同而直接重放。需要在目标 runtime 重新分类一个可移植意图时，使用 `python3 scripts/plan_context.py --intent-json intent.json --reroute-intent`。它清除旧的分类建议、authority owner、承诺和 thread 身份，不能复用先前回执，也不授予写入或外部权限；目标 runtime 重新检查来源，必要时请求澄清。这是一次新的路由裁决，不是无缝接续，也不授权外发私人材料。

### 在 ResearchOS 之外做的修改

无界面 CLI 负责规划、核对来源和记录候选交接，不签署人类决定，也不执行正典升级。policy/staging 内核可以支持受控的宿主动作，但任意 Agent 编辑不会自动经过它。外部 Agent 做出的已授权修改，要保留候选 diff、宿主中的明确用户决定、精确目标、前后 revision、验证结果和回滚坐标。没有可信绑定时，把执行证据标为 external-host，或标为未经 ResearchOS machine gateway 管理。这个标记不否认用户授权，只防止事后伪造机器授权；构造出来的决定引用绝不能称为已核验。完整的机器治理外部宿主写入链需要可信宿主集成，本版不声称已经具备。

### 判断它有没有帮上忙

用真实任务，并在 24—72 小时后自然返回。对照基线是同一当前模型、材料和预算，加一页版本化交接。记录证据遗漏、恢复与纠正成本、严重错误、判断变化和维护负担，并保留不成功的对比。安装成功、合成测试或工程检查都不算真人接受，也不算已证明的研究收益。报告解释了这条证据边界；其中的合成案例只用于说明协议，不能证明已测得的生产率提升或研究者成长。

## 3. 会话调度器与命令行检查

`python3 scripts/ros_demo.py --lang zh-CN`（不带 `--lang` 时为英文）在一份虚构研究图的临时副本上运行：来源卡片变化，依赖它的判断被标为待复核；研究者随后提出重新确认，本仓库只把它显示为拟议变化而不准入，收尾时复核仍列为待处理。能指出来源变化、候选或计划、仍开着的工作和下一动作即可停。输出里的词看不懂时，见第 1 节的[你会遇到的词](#你会遇到的词)。

调度器和 Dashboard 用的是两个互不相干的虚构世界。`examples/scheduler-demo/` 里的调度器夹具是一份关于遮挡论文的研究图：两项承诺、两张卡片和一条判断。第 4 节的 Dashboard 演示显示 `08_exports/public_starter/demo-research-agenda.zh.md` 里的六个虚构议程事项。两者互不引用。

### 自己走一遍会话

`ros` 是调度器的命令行客户端。命令行打印出的每个 `ros …`，都指 `python3 scripts/ros.py --root <文件夹> …`，而且 `--root` 要写在子命令之前。在仓库文件夹里运行：

```bash
python3 scripts/ros.py --root examples/scheduler-demo today
python3 scripts/ros.py --root examples/scheduler-demo context commitment:occlusion-paper
python3 scripts/ros.py --root examples/scheduler-demo run judgment --target commitment:occlusion-paper --executor copy_packet
```

`today` 开启会话，列出需要你决定的事；`context` 打印这项承诺及其依据的卡片；`run` 写出交给你自己助手的任务包。`run` 最后会打印形如 `ros-run-…` 的 run id 和对应的 `collect` 命令。平时你把任务包交给助手，把它的回答存成文件；没有助手也想试一下，就用夹具随附的示例回答。下面的 id 只是示例：`ros-run-aee8c1335137` 代表你的 `run` 打印出的 run id，输入时换成你自己的：

```bash
python3 scripts/ros.py --root examples/scheduler-demo collect ros-run-aee8c1335137 --file examples/scheduler-demo/sample-answer.md
```

`collect` 把回答回收为候选，并打印形如 `c-…` 的候选 id 和 `admit` 命令。同样，`c-3f9a1d20` 代表你的 `collect` 打印出的 id：

```bash
python3 scripts/ros.py --root examples/scheduler-demo admit c-3f9a1d20
python3 scripts/ros.py --root examples/scheduler-demo close
```

`admit` 打印它会对 `06_active_context/research-portfolio.md` 做的改动，但不写入；`close` 结束会话，并把这个候选列为尚未决定。

输出里有两处来自日期，而不是夹具本身。按当天日期运行时，夹具里的承诺会被标为久未核实；`ros_demo.py` 固定了日期。新 clone 上第一次运行 `today`，还可能看到某份来源「在核实后有更新」，因为判断依据是文件的修改时间，而 clone 刚把它设成了当天，晚于承诺的 `last_verified`。不带 `--root` 时，`ros` 读的是本仓库自己的图，其中没有承诺。

### 本仓库里 `ros` 写什么

在出厂的 `runtime_scope: public_starter` 下：

- 每条 `ros` 命令只在 `--root` 下 git 忽略的 `06_active_context/work_state/` 里写出任务包、候选与会话记录。没有命令写长期来源。
- `run` 只接受 `--executor copy_packet`，拒绝所有 provider。personal-vault 模式（第 5 节）不改变这一点。
- `admit <candidate>` 和 `admit --reconfirm` 不先询问，直接通过复制回退显示拟议差异，因此不向长期来源准入任何东西。
- `admit --confirm` 只有你在自己的终端回答时，才会在 git 忽略的本地账里记一笔事后确认；由 Agent 转述时只记为转述（asserted），确认要求保持开着。两种情况都不写来源，也不算准入。
- `close` 列出会话开始以来回收或登记、尚未决定的候选。这里它们始终尚未决定，因为 `admit` 既不准入，也不记录拒绝。

准入与派发的代码随本仓提供，但默认关闭。只有 `config/ros.json` 显式写明 `runtime_scope: "private"` 才会开启；缺这个键、拼错或写成其他值，都按只复制模式运行。技术报告里的原型是开启准入与派发运行的。从夹具复制出来的库保留夹具的 `config/ros.json`，所以同样按只复制运行。

13 个子命令在本仓库里都有。多数命令先跑一次边界检查，记在同一份 git 忽略的账里；`receipt`、`propose rule`、`admit --rollback`、`collect --abandon` 与 `attend` 不跑。所有命令都不写长期来源：

| 命令 | 本仓库里的行为 |
| --- | --- |
| `today` | 只复制降级：列出变化与待处理要求并开启会话，但不随附注意力安排，所有承诺都读作未排期 |
| `close` | 与报告中的原型同语义；列出的候选始终尚未决定 |
| `propose judgment`、`episode-close`、`rule` | 同语义：登记候选 |
| `admit` | 只复制降级：`<candidate>` 与 `--reconfirm` 显示拟议差异；`--confirm` 只记确认、不写入，且只有你在自己的终端回答时才生效；`--rollback` 被拒绝，因为这里不写来源，也就不回滚来源 |
| `decide` | 同语义：记下决定；`cancel` 与 `confirm` 只有你在自己的终端回答时才生效 |
| `answer` | 同语义：记下回答；`satisfied` 与 `cancel` 会关闭要求，因此只有你在自己的终端回答时才生效；只有检查依据是研究者判断时才提供 `satisfied`，出厂规则里没有这样的检查 |
| `state`、`context`、`rules`、`receipt` | 同语义，只读 |
| `run` | 只复制降级：只接受 `--executor copy_packet`，拒绝所有 provider |
| `collect` | 同语义，只是不记 run-state 账 |
| `attend` | 只复制降级：显示拟议的注意力动作，不写入 |

工程检查运行 `python3 scripts/validate_headless.py`。它验证完整的无 Dashboard profile，这个 profile 必须在 `dashboard/` 目录不存在时通过：routing、receipts、runtime 与 provider 边界、task extensions、public safety、links 和 focused zero-dashboard 行为，且不为通过而放宽 authority 检查。它不是用 Agent 客户端读一份来源的前提。CLI 路线准备同一个“目标、来源、结果、边界”的闭环，不启动服务器或 Dashboard；第二条命令给出第一次上手要读的那一个文件，即[首次上手说明](../08_exports/public_starter/onboarding-step-by-step.zh.md)：

```bash
python3 scripts/start_researchos.py --mode cli
python3 scripts/plan_context.py first_run_onboarding --lang zh-CN
```

责任组合（responsibility portfolio）是在声明范围内记录主责/协作、承诺状态、优先级、时效、负责人与角色、唯一下一步和权威来源的账本。承诺（commitment）是项目当前唯一的下一步或下一次判断；被排期的是它，而不是整个项目；无论用哪个客户端查看或继续，它都只保留一个有边界的状态和一个下一安全动作。问“我当前主责多少任务”时，运行 `python3 scripts/query_research_agenda.py --view lead-active`，或用 `lead-all`、`support-active`、`support-all`、`waiting`、`queued`、`conditional`、`paused`、`review`、`unclassified`、`all` 查看明确分层。责任缺失或非法时失败关闭到 `unclassified`。只有覆盖回执当前有效且没有未决候选，数量才可称为完整；否则只代表已登记事项。时间栏只用于排序，不定义任务组合。

## 4. 可选的 Dashboard

Dashboard 是可选的，处于冻结状态：可以按这里的说明使用，但不在开发之中。在仓库根目录启动 demo：

```bash
python3 scripts/start_researchos.py --mode dashboard --port 8880
```

![公开 Dashboard：打开事项，预览并取消关注日期，预览交接；什么都不保存，也不运行。](figures/readme/dashboard-zh.gif)

然后打开 `http://127.0.0.1:8880/`。这里显示 `08_exports/public_starter/demo-research-agenda.zh.md` 里的六个虚构议程事项，与第 3 节的调度器夹具是两个不同的虚构世界，不需要真实 API key。演示设在一个固定的虚构日期 2026-08-11，页面状态栏会显示这个日期，所以无论哪天打开，它的日历和时效读起来都一样。普通启动直接读取随仓发布的公开安全投影，不重写受 Git 跟踪的文件；只有投影缺失时才自动恢复。维护者修改 demo 来源后，用 `python3 scripts/build_public_starter_data.py --write` 显式重建。启动器只在 `/session-config` 确认运行时身份匹配时复用已有服务，因此公开 demo 不会被误认为 personal-vault、报告中的原型或占用同一端口的其他程序；遇到这种情况会停止并建议另一个端口。`--mode public-starter` 只报告本仓库的运行状态，不启动服务器。其余模式：

```bash
python3 scripts/start_researchos.py --mode public-starter --check --provider codex
python3 scripts/start_researchos.py --mode cli
python3 scripts/start_researchos.py --mode gui --port 8880
python3 scripts/start_researchos.py --mode public-starter
```

Dashboard 是与 Agent 客户端互补的跨会话注意力与控制面，不是第二个聊天入口，也不是 Agent 路线的前置条件。它以统一工作台呈现现在与资料两个语义区域：`现在`在多项承诺之间分配注意力并承载日历，`资料`通过一项或少量承诺 lens 连接来源与关系。Work 与 Review 是精确事项的局部状态，只在该事项的抽屉中展开，不形成第三个顶层屏幕。各界面的定义和路由规则见[系统参考](system-reference.zh.md#主要路线与辅助界面)。第一次可以判断一个虚构承诺，也可以展开可选的直接 Agent 输入、只给一个目标；默认输入框只收集目标和可选来源，Dashboard 不提供模型、推理档位或输出类型控件。第一次打开时：

1. 在统一工作台选择事项卡，核对当前依据和下一步。
2. 拖到日历日期只预览关注安排；取消或重新载入即可丢弃预览。
3. 在右侧查看关联资料，再预览并复制 Agent 交接任务包。
4. 只在独立的私有助手任务中执行。
5. 审阅返回结果，再通过研究者确认流程提出长期更新。复制本身不代表已执行或已接受结果。

月历以日为最小单位，不提供小时网格。`+N` 展开当天；“安排”卡可拖拽或用 `Alt + 方向键` 移到另一日，作为内存中的预览，界面标明未保存，刷新即恢复。只有支持写入的私有运行时才会经可撤销的排期 owner 保存日期；复查、截止和生命周期标记始终不可拖动。“完成本步”“结束 Work Session”和“结束项目”关闭的东西不同：当前承诺、执行会话和长期项目生命周期。Work Session 是与 Agent 客户端处理一个意图的有界执行会话，结束会话不等于结束项目。另外三件事也要分开：生命周期说明项目处于投稿、审稿、rebuttal、修订还是完成；进行中 / 待推进 / 暂不推进 / 已结束说明如何管理整个项目；今日 / 明日 / 未来 / 搁置只说明下一步何时再次占用注意力。审稿中的项目仍可从关联资料中找到；真实事件或复核日期到达时，它的下一动作会回到工作台。

本仓库固定为 copy-only。它不启动本机 Codex 或 Claude Code CLI，不探测本机 provider，不调用远程 API，不写长期记忆（它可能写的两类文件列在本节末尾），不执行 Inbox 写回任务，也不接受任意 shell 命令。提交任务只生成交给独立私有助手的任务包；工作台总是只产出可复制的任务说明。private 和 personal-vault 才是受控执行路线。各部分的分工如下：

| 界面 | 负责 | 不负责 |
| --- | --- | --- |
| Agent 客户端 | 解释意图、深读材料、推理、修改文件、生成成果、与你反复协作、运行验证 | 代替研究者确认证据或修改长期记忆，维护 Today 投影 |
| CLI | 确定性 route、query、receipt、validation 与维护命令 | 开放研究判断或第二套 authority |
| canonical Markdown 与 Git | 长期事实、决定、provenance 与恢复坐标 | 生成或仅运行时状态 |
| Dashboard | 可重建的投影：分诊近期注意力、可视化资源与关系、按天排期、选择执行路线、显示状态与结果 | 产品事实、首次使用前置条件、开放讨论、模型选择、深度推理、跨文件编辑，或批准长期变化 |

后台准备只运行有边界、结果能原位返回的工作；开放讨论或复杂修改时，界面复制一个完整任务包，由你粘贴到 Agent 客户端的新任务中；只有确实存在可核验的绑定时，“继续已有任务”才可用。Dashboard 不复制你的聊天，只显示有界的会话状态。普通选卡保持原位，系统建议可以直接建立 Work Session。独立的私有 Codex runner 更适合深度读取、文件修改、成果生成、验证、后台队列、逐项执行或隔离写入。

```text
现在：恢复一份有边界的当前研究焦点
  -> 资料：按需补上下文
  -> 现在 / Agent：继续研究工作
  -> 需要时由 Agent 有界读取
  -> 可见回答、成果或 diff
  -> 待复核：核对结果、候选变化、回执和交接
  -> 研究者决定
  -> 在私人库中验证后写回
```

一轮工作会明确三件事。Work Session 包含当前目标、按需来源、当前结果、折叠的过程记录、工作牌组和被冻结的 prompt/模板语言；浏览器协调状态和最近任务摘要都不是长期记忆。候选交接是一个有边界的任务，带着来源卡片、证据状态、敏感性、拟议权威变化、影响范围和验证状态。待复核边界提醒你：任务完成不等于证据确认，来源路径也不是写回目标。在私人库中，后续步骤是执行、证据核对、你的决定、验证后写回和恢复包；它们保持受控，本仓库不会把它们伪装成自动完成。

待复核不只接收写回提案。它的[完整接收范围](system-reference.zh.md#共享治理边界)还包括有界未知、break-glass 确认、结果、验证失败、回滚与关闭前必须明确的交接；长期、敏感、公开或破坏性变化一律经过它。公开运行态从不执行持久写回。

页面语言选择只改变可见文案。新建 Work Session 会冻结当时的界面语言，作为该任务的回答和任务包语言；任务中途切换界面语言不会改写已有任务。内容语言在 `config/researchos.runtime.example.json` 中设置，决定生成记录和 prompt：

```json
"public_starter": {
  "content_language": "zh-CN",
  "available_content_languages": ["en", "zh-CN"],
  "alternate_language_files": "reference_only_do_not_read_by_agent"
}
```

用 `python3 scripts/build_public_starter_data.py --language en --write` 或 `--language zh-CN --write` 重建。被选中的语言进入 `08_exports/public_starter/generated-public-starter-data.json` 和 `dashboard/data/researchos-dashboard.json`。另一种语言的文件留在仓库中作为参照；除非你要求翻译、对照或双语维护，Agent 正常运行时不读取它们。

```text
浏览器 Dashboard
  -> 运行在 127.0.0.1 的本地 Python 服务器
  -> 当前选择的 demo 或 personal-vault 投影 / provider 状态
  -> 交给独立私有助手的可复制任务包
```

Agent 路线与 Dashboard 依赖同一套 Markdown 和确认规则，本仓库遵守上文说明的只复制边界，所有 `/codex-runner` 提交都被拒绝，不启动线程或命令。personal-vault 与私有运行态可以把本地回答或成果返回待复核；只有在你提交任务后才启动本地 Codex。公开 demo 中保存反馈、Inbox 条目或卡片分组、撤回确认、运行更新的本地端点都返回 403 `public_starter_writeback_blocked`，只在 personal-vault 模式下执行。公开 demo 只会写两类文件：上传到 Git 忽略的会话目录的来源，以及你运行已登记的 `build_public_starter_data` 动作时重建的示例投影（示例来源不变时字节不变）。这些本地 HTTP 端点服务 Dashboard，不是公网 API；完整列表见[系统参考](system-reference.zh.md#本地-http-端点)。

本地 **打开**/**定位** 在 macOS 使用 Finder，在 Windows 使用 Explorer，在 Linux 尝试 `xdg-open`；当前桌面环境没有可用 opener 时，服务器返回清楚的失败信息并保留路径，供手动打开。

## 5. 用自己的材料

你自己的材料放在 clone 里的 `personal_vault/` 文件夹。Git 忽略它，所以里面的东西不会被提交；`ros` 和 Dashboard 的 personal-vault 模式都读它。即便如此，含有真实材料的 clone 也不要推送到公开远程仓库。想给库做版本管理，就另建一个没有公开远程的私人仓库副本，并在那个副本的 `.gitignore` 里删掉 `personal_vault/`。无论哪种做法，下面都用同样的 `personal_vault/` 布局。

### 开始自己的

1. 复制调度器夹具：

   ```bash
   python3 scripts/ros_demo.py --init personal_vault --lang zh-CN
   ```

   它复制夹具的承诺、卡片和 `config/ros.json`，不带走按第 3 节走查时留在夹具里的记录、示例回答和虚构的判断，并打印接下来的步骤。`personal_vault/` 已经存在时（例如你先启动过 personal-vault Dashboard）也可以用，文件夹里已有的文件会保留；如果其中已经有 `06_active_context/research-portfolio.md`，它会拒绝执行。

2. 编辑 `personal_vault/06_active_context/research-portfolio.md`。把两项虚构承诺换成你自己的一项；你自己的判断以后按第 3 节的方式作为候选进入。一项承诺需要标题、id、你的责任和状态、一个问题、一个下一步、你上次核对它的日期，以及它依据的卡片；Dashboard 还会读取最终负责人、你的角色和项目所处阶段：

   ```markdown
   ### 论文第二章

   - id: thesis-ch2
   - responsibility: lead
   - accountable_owner: 你
   - role_summary: 本章作者
   - lifecycle_phase: writing
   - state: mainline
   - priority: P0
   - question: 基线在新划分上还成立吗？
   - next_step: 在新划分上重跑基线
   - last_verified: 2026-10-29
   - stale_after_days: 14
   - source_path: 01_knowledge/projects/thesis-ch2.md
   ```

   `responsibility` 取 `lead` 或 `support`；`state` 取 `mainline`、`queued`、`conditional`、`waiting`、`paused` 或 `closed` 之一；`last_verified` 写成 `YYYY-MM-DD` 日期，`source_path` 相对于 `personal_vault/`。`lifecycle_phase` 取 `scoping`、`planned`、`experiment_preparation`、`production`、`gated_operation`、`writing`、`release_preparation`、`submitted`、`under_review`、`rebuttal`、`decision`、`revision`、`accepted`、`published`、`paused`、`completed` 之一；取 `submitted`、`under_review` 或 `decision` 时还要写 `activation_trigger`，即让这一项重新回到眼前的事件。id 和路径由你自己定。`ros` 用不了的值会列在 `today` 的「任务总表问题」和 `ros rules --check` 里，这项承诺不会悄悄从检查中消失。`ros` 不读 `lifecycle_phase` 和 `activation_trigger`，阶段写错或缺少触发条件，只会在 Dashboard 的 personal-vault 投影里标出。

3. 把 `personal_vault/01_knowledge/` 下的两张虚构卡片换成你自己的一张，放在 `source_path` 指向的路径。从 `09_templates/` 里的模板起步，例如 `project-template.md` 或 `paper-template.md`；模板里已有卡片需要的 frontmatter、Agent Summary 和证据边界各节。`ros` 用 frontmatter 的 `title` 作为卡片的显示名，没有时用第一个 `#` 标题；Dashboard 还接受模板里的 `name` 或 `project_name`。所以填好 `project_name` 并替换模板的 `# Project Name` 标题，或者加一行 `title:`。

4. 在你的库上运行调度器：

   ```bash
   python3 scripts/ros.py --root personal_vault today
   ```

   用 `--init personal_vault --lang zh-CN` 建的库，`config/ros.json` 已设为中文输出；要临时换语言，在子命令前加 `--lang en` 或 `--lang zh-CN`。

5. 需要时，在同一个文件夹上打开 Dashboard：

   ```bash
   python3 scripts/start_researchos.py --mode personal-vault --port 8881
   ```

   然后打开 `http://127.0.0.1:8881/`。这个模式读取 `personal_vault/06_active_context/research-portfolio.md`，以及 `personal_vault/00_identity/` 到 `personal_vault/06_active_context/` 中带 frontmatter 的卡片，从不显示虚构的示例数据。服务器在启动时读取卡片，所以新建或修改的卡片要重启服务器后才出现。第一次启动只建出部分分层目录（`00_identity/`、`01_knowledge/papers/` 及其下的 `own_papers/reading_notes/` 与 `source_files/`、`01_knowledge/projects/`、`04_people/collaborators/` 和 `06_active_context/`）；`02_decisions/`、`05_workflows/` 等其他目录，需要时自己建。

使用个人库不需要关闭示例数据。[首次上手说明](../08_exports/public_starter/onboarding-step-by-step.zh.md)把这几步再走一遍，写明每一步应该看到的输出，以及看到的不一样时怎么办；字段仍以本节为准。

### 让库慢慢长大

候选卡片是解释，写下它并不使它成为长期记忆或公开事实。从一个来源和一张卡片开始，卡片写明来源边界、证据状态和一个缺失的事实；核对第一版结果之后，再按需要补项目历史、报告、决策理由和其他来源。需要理解 M/I/R/G 标签，或把卡片缺口变成有边界的 Work 任务时，再读[卡片成熟度与增强](reference/CARD_MATURITY_AND_ENHANCEMENT.zh.md)。

在 `personal_vault/` 里，简短当前状态放入 `06_active_context/`，有来源的摘要放入 `01_knowledge/`，决策与取舍放入 `02_decisions/`，人物上下文放入 `04_people/`，可复用方法放入 `05_workflows/`。完整的放置表见[新材料放置规则](reference/WHERE_TO_PUT_NEW_MATERIALS.zh.md)。原始材料留在原处、放在仓库之外：卡片记下路径，很多时候已经足够，不要为了让 Dashboard 看见而复制原始文件。库里的任何内容，不经[安全导出规则](reference/SAFE_EXPORT_POLICY.zh.md)下的单独复查，都不会公开。

卡片是上下文对象，不是前置条件。你提供的来源会成为第一张工作卡片；只有当前证据不足时才搜索`资料`。每张卡片带有 public、internal、sensitive 或 private 的敏感性标签。personal-vault 投影写入 Git 忽略的 `dashboard/data/researchos-local.json`，因为它可能含私人派生元数据；公开 demo 与 personal-vault 不共用生成数据文件。在这个模式下，服务端 Review 状态、选择的工作副本、runner 回执和本机 Codex 的可写 sandbox 都以 `personal_vault/` 为写入根；Agent 可以把公开模板当作只读参照，但不能借个人模式的 `workspace-write` 修改受跟踪的 demo 文件。personal-vault 也不会把任务完成变成证据确认：长期变化需要明确目标、证据检查、你的批准和写回后的验证。

完成一个闭环就停：只有每个新文件都有明确 owner 和证据边界时，扩大 vault 才有意义。真正有用的长期记忆仍需要你自己的论文、笔记、项目、报告、决策或关系上下文，并保留可追溯的边界，且只在当前判断需要时补充。

### 关闭示例案例（维护者）

这一步可选，只改变公开 demo 的投影。`python3 scripts/build_public_starter_data.py --disable-cases` 预览去掉虚构案例后的投影；加上 `--write` 会重写受跟踪的 `08_exports/public_starter/generated-public-starter-data.json` 和 `dashboard/data/researchos-dashboard.json`，所以除非你确实要发布不带案例的 demo，不要提交这个结果。`python3 scripts/build_public_starter_data.py --write` 会把它们恢复。关闭案例不删除任何文件；示例保留为字段和放置位置的对照。

### 本地执行 provider

除了 Agent 路线和 Dashboard，也可以在文本编辑器或 GitHub 上直接读 Markdown，了解目录、案例和手册。Codex 图形界面适合 AI 协助阅读和修改，Codex 命令行可执行小型交接并记录日志；ResearchOS 没有远程 API provider。ResearchOS 不附带 Codex，公开 Dashboard 也不会启动它。若要在独立私有 Agent 任务中执行复制出的任务包，按 OpenAI 当前官方说明安装 Codex 图形界面或命令行，并用 `command -v codex` 与 `codex --version` 检查。macOS 桌面应用可能把命令行程序放在 `/Applications/Codex.app/Contents/Resources/codex`；如果 `codex --version` 不可用而该文件存在，把它加入 `PATH`，或设置 `alias codex="/Applications/Codex.app/Contents/Resources/codex"`。不要把登录令牌、API 密钥或账号信息写入仓库。

本仓库登记了两个本地 provider：`codex` 与 `claude_code`，在这里两者都是 `copy_only`。`python3 scripts/runtime_profile_cli.py list --scope public_starter` 显示本仓库的只复制配置档，`show --profile codex --scope public_starter` 查看某个保留 provider 在本版中的投影；两者都不需要凭据或网络。公开 Dashboard 的默认配置是：

```json
{
  "provider_mode": "copy_only",
  "allow_local_codex": false,
  "execution_scope": "none",
  "maintenance_scope": "registered_actions",
  "allow_real_api": false
}
```

不要把公开 Dashboard 改成执行主机。如需使用两个本地命令行 provider 之一，先切换到 private 或 personal-vault 运行态，配置不纳入 Git，运行 provider 检查，再在那里启用它；命令行工具的登录信息留在仓库之外。检查命令是 `python3 scripts/validate_runtime_config.py` 和 `python3 scripts/start_researchos.py --mode public-starter --check --provider codex`。

## 6. 安全规则与常见错误

不要把 Dashboard 暴露到公网。不要提交 API 密钥、令牌、`.env` 或本地运行配置，也不要把真实敏感人物、未公开稿件、真实关系笔记、原始语料或私人运行日志放进本仓库。发布前，`python3 scripts/validate_public_safety.py` 会检查这些内容。

公开 demo 的跟踪文件约 19 MB，连同 Git 历史约 100 MB，不复制私人 vault。ResearchOS 不治理你的磁盘空间：在 personal-vault 与私有运行态中，本地 Work Session 接收你选择的研究材料，不设产品级文件类型、大小、数量或保存期限配额，实际上限只是本机文件系统和运行环境；公开 demo 则接受单个文件最大 1 GiB 的上传。两者都不因空间阈值自动删除你的材料。系统只约束自己产生的冗余，具体见[低冗余运行契约](system-reference.zh.md#低冗余运行契约)；本机空间较低或会话副本较大时只给出非阻断提醒。

常见错误是：任务尚未明确就扫描整个仓库；把 Agent 回答当成已确认记忆；把 Dashboard JSON 或浏览器状态当作 authority；把真实材料放在 `personal_vault/` 之外，或把含有真实材料的 clone 推送到公开远程仓库；在 Markdown 或受跟踪配置中写入密钥；删除虚构示例；期待空 vault 自己理解一个研究领域。正确使用时，助手会说明读了什么、刻意没读什么；每个来源都有边界；每个解释都先成为候选；每个长期变化最后都有验证结果，或一个明确的缺失证据。
