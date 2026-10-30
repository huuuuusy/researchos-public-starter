---
type: reference
title: "ResearchOS 系统参考"
status: active
updated: 2026-10-28
sensitivity: public
---

<p align="right">
  <a href="system-reference.en.md">English</a> | <strong>中文</strong>
</p>

# ResearchOS 系统参考

本参考说明本仓库 的界面、状态和治理边界各自是什么意思，内核与扩展端口怎样安排，哪个代码 owner 负责哪类问题，以及公开安全内容放在哪里。修改或调试代码前先读下面的代码地图：只选一条运行链和一个 owner 文件，不要先扫描全部 JavaScript、生成 JSON 或另一语言文档。怎样使用系统见[用户手册](user-manual.zh.md)；发布、自定义和插件见[治理与扩展指南](governance-guide.zh.md)。

## 系统是什么

ResearchOS 是给个人科研人员使用的小型文件化工具，用来让判断在工具、项目和时间之间保持连续。skill 可读 Markdown 加 Claude Code、Codex 等 Agent 客户端或其他文件感知 CLI 是主要执行路线；刻意收窄的本地 Dashboard 是跨会话的注意力与控制面。本仓库 展示机制，不保存非公开研究记忆。skill/Agent 使用、Dashboard 可视化、provider 输出和 Agent 输出都只是候选或操作界面，从来不是长期权威。

本仓库 是一个小型文件化参考工具，把研究工作流拆成几个清晰的 Markdown 层级：身份和方向、知识材料、判断记录、认知方法、人物上下文、工作流、当前状态、公开导出和模板。配置、脚本、验证器和刻意收窄的 Dashboard 为这些层级提供支持。它不是用来保存敏感内容的，展示三条机制。候选与确认分离：智能体生成内容先进入候选层。证据与行动分离：材料、解释和下一步行动分别记录。公开与非公开边界分离：可导出的内容必须来自虚构、清洗或明确授权公开的来源。

本仓库 不发现其他私人仓库，不包含 federation catalog，不执行跨系统调用，也不共享私人运行态。本仓库的 task extension 只是复用内核的本地声明式描述，不是连接维护者私人系统的 connector。某个私人方法只有在去除来源身份、本地路径、运行证据和外来 authority，并重新写成领域中性的候选机制后，才可能进入本仓库。ResearchOS 不是托管服务、自治科研系统、all-in-one 科研平台或追求消费级完成度的应用；“OS”是项目名称和显式操作规则的比喻，不代表平台广度。

```text
现在：在多项 Commitment 之间分配注意力，每项只有一个下一步
  -> 资料：以一项或少量 Commitment 为 lens 查看公开安全上下文
  -> 事项内 Work：在当前 Commitment 内打开精确对应的有界 session 和可复制任务包
  -> 需要时加入来源卡和任务条件工作牌组
  -> 事项内 Work 结果或 skill/Agent 任务
  -> 按需继续推进或生成成果
  -> 结果、拟议长期变化、验证边界与连续性交接进入当前事项内 Review
  -> 证据与敏感性复查
  -> 研究者决定
  -> 验证后的公开安全输出
```

## 主要路线与辅助界面

| 界面 | 作用 | 看什么 |
| --- | --- | --- |
| `Skill/Agent` | 日常 Agent 协助阅读、整理、草拟、验证和写回建议。 | Agent 协议、上下文预算、标准提示词和当前语言 Markdown。 |
| `现在 / Now` | 投影多项 Commitment 组成的注意力组合。 | 可以同时显示多项 Commitment；每项只保留一个处置和一个下一安全动作，不成为通用 backlog 或运行控制室。 |
| `资料 / Library` | 以一项或少量 Commitment 为 lens，查看公开安全的材料、项目、人物、报告和关系。 | lens 是临时选择，保留来源和关系类型；资料补上下文但不创建候选，不是第二个项目数据库。 |
| 事项内 Work | 在 Now 内打开精确所选 Commitment 的 Work Session、thread、run 与 result，连同事项的目标、来源、成果引用、过程记录和 working deck。 | 它是抽屉，不是第三屏；本仓库只准备可复制任务包，不启动本机或远程执行器，也不声称已执行。 |
| 事项内 Review | 展示精确所选事项的结果、成果、拟议长期变化、人工处置、验证边界、回执与连续性交接。 | 身份缺失或含混时失败关闭；本仓库不得声称已写入或验证 canonical memory。 |
| `Preview` | 文件、候选和证据片段预览。 | Markdown 如何被读取。 |
| `Agent` | 交接与能力状态。 | 本仓库固定为 copy-only；所有执行只属于 personal-vault 模式或报告中的原型。 |

Claude Code、Codex 或其他文件感知 Agent 是主要执行面。Dashboard 是跨会话注意力与控制面，按下一步何时再次占用注意力（今日 / 明日 / 未来 / 搁置）显示虚构或本地 Work Item，Markdown 仍是 authority。Dashboard 不是第二个聊天入口，也不是使用 Agent 的前置条件。生成的 JSON 文件为 Dashboard 提供数据，验证脚本检查配置、模型提供方注册表、生成的启动数据和公开发布边界。本仓库固定为 copy-only，见[用户手册第 4 节](user-manual.zh.md#4-可选的-dashboard)；排期、完成和长期写回保持禁用，按钮只演示同一交互语法，不假装已经修改数据。

skill/Agent 是深度读取、修改、成果生成和验证的执行路线，ChatGPT 类通用助手可以辅助开放讨论。Dashboard 以统一工作台呈现现在与资料两个语义区域，而不是第二个编辑器。`现在`负责分配注意力：完整的 Today 列表、一个当前研究焦点、月/周日历、全部活动或等待项目，以及精确事项内的 Work/Review 抽屉；复核日或外部事件到达时，等待或暂停的项目可以回到这里供判断，但不会因此变成可执行任务。`资料`只通过最多少量明确选择的 Commitment lens 连接公开安全的来源、人物、论断、证据、线程和成果，不承载日历或项目状态板。项目是长期容器，当天可安排的是它当前唯一的下一步 Work Item。月历只消费显式日期，点击事件只返回精确事项，不拥有生命周期写入。Work/Review 只在精确事项内区分有界执行、返回结果、候选变化、研究者处置、写回与验证状态、回执和连续性交接，抽屉保存精确的 session 与 run 身份。

核心 authority 协议和长期记忆不依赖 Dashboard。插件只能贡献领域投影和受控动作。导航由应用壳拥有；Work Session、Review、准入和存储安全是内核协议；Project/Commitment 生命周期与 attention 由 `research_portfolio` 能力层拥有。`现在`与日历只投影这些状态，不拥有其持久权威；本仓库的日历变化仍是不保存的预览。`Start / Today / Agent`、`Assets`、`Next`、`Work` 与 `Review / Inbox` 只作输入 alias；携带 item 的 Work/Review 路由进入 `Now?item=<id>&panel=<work|review>`，身份缺失时失败关闭，输出只使用 canonical ID。公开 demo 只使用虚构事项和 copy-only 交接；它与 personal-vault 模式能运行和写入什么，见用户手册第 [3](user-manual.zh.md#3-会话调度器与命令行检查) 节和第 [4](user-manual.zh.md#4-可选的-dashboard) 节。

待复核状态带有时间边界：重新加入会清除同一 action 的 archive/resolved 遮罩，旧的 completed run 不能处理后来加入的请求。界面语言是浏览器偏好；活跃 prompt/模板语言在生成投影时冻结。

## 共享治理边界

本节解释共享协议与当前内核行为。公开发布仍是使用虚构数据、采用 `copy_only` 交接的只复制版本；描述协议不代表开放私有写入服务。

**Needs Review 接收范围。** 包括结果、成果、候选、验证失败、回滚，以及任务关闭前必须明确的交接边界；也接收证据无法裁定的有界问题和 break-glass 确认要求。有界问题向研究者提供有限答案。break-glass 确认只关闭该要求，不把修改追认为事前授权。普通通知、全部任务、材料浏览、plugin/provider 状态、原始运行日志、日程排序、改期和可逆短期状态，不因其存在就进入 Review。

**要求状态与完成。** `open / deferred / waiting / resolved / cancelled` 是独立的要求轴，与 Run、Session、Attention、Portfolio 分开。延期和等待都仍未关闭，须登记重开触发；触发到点回到 `open`，没有触发的按 open 计。协议只允许研究者直接决定进入 `deferred`，附理由及日期或事件触发，并在本机终端确认；Agent 代给参数不算研究者确认。非终端的 `decide defer` 照常写入，渠道记为 `invoker_asserted`，不计入完成；终端确认记为 `researcher_decision`。

账本用状态 `waiting` 记录三种情形：有界问题已提出、尚未回答，报告称挂起；研究者带触发延期或收窄范围；阻塞依赖在冻结范围之外。后两类才是报告所说的等待，当前内核尚无“范围外阻塞依赖等待”的产生路径。提问未答属于等待人工判断的挂起，不等于已获准延期。因范围内依赖而等待、执行方自行延期，都不计入完成。Done 的等待集承认研究者渠道的延期或收窄范围，包括终端确认的 `decide defer`。前次规格不可重算要求（`spec:`）、break-glass 确认要求（`field:` 等现有 binding）和范围内覆盖未知要求，只要未关闭，Done 一律为假，即使已延期、等待或提问未答。合法等待不代表要求已解决。

**上下文外发。** `ros context` 包被云端会话 Agent 读取时会离开本机，尽管该 Agent 不是 provider。研究者启动的会话可为所请求的承诺或卡片交付 public/internal 来源，无须再次确认。sensitive 来源每次须研究者本人在本机终端确认；Agent 代给参数不算确认。private 和未知级别一律排除。private 承诺总表可在来源自身声明哪些字段按 internal 交付；未声明字段与标题仍属 private，请求所用承诺 id 随请求交付，声明不降低来源级别。sensitive 和未知来源不适用该例外。

每次交付记录去向服务、用途、已交付与已排除来源；无法识别去向时记为未知。Agent 直接读文件，以及 `ros today`、`ros state` 等其他命令输出，不在这条交付记录内；其外发情况是未知，不能声称已覆盖。撤销只阻止后续交付，不能收回已交付内容。会话交付许可不等于公开发布许可；本仓库的安全导出规则与 `copy_only` 边界继续适用。

## 状态与权威模型

ResearchOS 不用一个含混的 status 同时表达所有含义：

| 状态轴 | 代表状态 | 权威含义 |
| --- | --- | --- |
| 工作流 | `active`、`processed`、`archived`、`withdrawn` | 只说明操作进度。 |
| 证据 | `candidate`、`needs_evidence`、`supported`、`contradicted`、`bounded` | 说明支持和不确定性，不代表已经写回。 |
| 权威 | `proposed`、`approved`、`written_back`、`validated`、`reverted` | 说明 canonical memory 是否改变，以及改变是否通过验证。 |
| 敏感性 | `public_safe`、`internal`、`private`、`local_only` | 说明材料或派生判断可以流向哪里。 |

来源路径表示输入证据，不是保存目标。任务完成后，证据仍是候选，除非另有证据判断记录；候选获批后，也必须有明确写回目标和验证结果，才成为 validated write-back。Workflow、EvidenceState、Authority、Sensitivity 和 EvidenceKind 只由 `researchos-primitive-contract-v1.json` 定义；view 和 app 不得维护另一套状态枚举。

## 内核与扩展架构

稳定内核是 authority 与结果协议，不是 Dashboard 的功能数量。普通任务路线使用声明式扩展；经过审查的第一方能力使用静态 adapter、candidate registry 与稳定的 Utility、Library、Workbench 或 Review 端口。两者都复用现有 Work Session、`answer / artifact / writeback` 模式、Review 边界、语言冻结和公开安全门禁，都不能另建执行器、Inbox、存储或写回链。本仓库 同样以对话为先：`conversation_contract.py` 统一结果和确认边界，`repository_layout.py` 声明 personal-vault 层，`plan_context.py` 是直接 Agent 路由，Dashboard 只显示公开安全投影和交接。生成 JSON、demo 数据和 Agent 输出都不取得长期 authority；写回个人材料库前必须由用户确认。

### 产品层

最小产品是直接对话核心：目标、最小相关来源、`answer / artifact / writeback` 结果协议与人工确认。它不需要 Dashboard，也不需要安装扩展。`researchos-plugin-v1` 是统一技术宿主，不代表每个 manifest 都是用户眼中的可选插件；`config/plugins/` 下每个 native manifest 都登记 `product_tier`：

| 产品层 | 含义 | 当前例子 |
| --- | --- | --- |
| 最小对话核心 | 不启动 Dashboard 也能完成`目标 → 最小来源 → 回答/成果/diff → 用户确认`；它不是插件 | context router、source authority、`answer / artifact / writeback`、确认与安全边界 |
| `foundation_projection` | 为可选 Dashboard 提供统一工作台、语义区域与事项呈现；不拥有对话任务或 canonical authority | `material_pipeline`、`research_assets`、`research_portfolio` |
| `bundled_capability` | 随版本提供、按需调用；关闭后最小对话闭环仍成立 | 折叠的 `system_stewardship` |
| `optional_extension` | 只在用户用自然语言明确要求后安装；默认不存在、可逆 | `method_comparison` 示例 |

因此，“零插件可用”的准确含义是：直接对话完成工作时不需要任何 `optional_extension`；不是删除 Dashboard 的 foundation owner 后界面仍然完整。`system_stewardship` 是折叠的维护能力，不是首次使用 owner。可安装扩展必须保持本地、可逆、不联网，不能写 canonical memory，也不能增加顶层页面、第二个对话入口或平行的状态 owner。普通用户不需要理解这些层；manifest、验证器和本参考负责守住边界。

核心拥有的 `researchos_plugin_capability_v1` 是不可安装的母版。canonical capability claim 是稳定身份；具体 manifest 提供可替换的 contribution，task 只是入口、工作流适配器或评价探针。机器强制的身份链是 `claim -> contribution -> task projection -> episode evidence -> admission receipt`，字符串同名不形成隐式身份。外部 skill 在出现一个真实能力缺口、且当前裸模型基线足以支持改造或多来源组合之前，只作为带版本与许可的来源候选链接保留。ResearchOS 没有原样搬运模式，也不把自己变成插件堆。验证后的 contribution 以后可以被 foundation owner 吸收，或经过独立架构 Review 进入稳定内核。详见 [Plugin Standard v1.2](../05_workflows/research_management/researchos-plugin-standard-v1.2.zh.md)。插件系统处于冻结状态，相关模块保留现有 owner；冻结允许做什么只在[治理指南](governance-guide.zh.md#任务扩展与插件)中说明。

### 稳定内核

按技术报告的说法，这里是目标中的稳定内核（第 4.2 节，差距 3）；原型里的会话内核是 `scripts/ros.py` 与 `scripts/researchos_kernel/`。

| 不变量 | 稳定含义 | 扩展不得做什么 |
| --- | --- | --- |
| 来源权威 | 已确认 Markdown 和明确的人类确认才是 authority。 | 把生成 JSON、provider 输出或插件状态当作事实。 |
| 单一工作链 | 意图进入一个 Work Session，并返回可见结果。 | 新建第二套 composer、结果循环或交接队列。 |
| 结果协议 | `answer` 只读，`artifact` 按要求生成文件，`writeback` 只提出长期修改。 | 发明另一种结果模式，或把普通回答静默变成写回。 |
| 候选协议 | 长期、敏感、公开或破坏性变化必须经过 Review。 | 从 view 或 provider 直接写 canonical memory。 |
| 状态 owner | UI 偏好、runtime ledger、canonical Markdown 和投影分开管理。 | 临时增加 storage key 或平行 Inbox。 |
| 注意力语法 | 一个当前 Work Item 可处于今日、顺延、之后、未安排、等待、暂停、待定下一步或已完成。 | 把整个项目当作日历事件，或静默改掉原始安排日期。 |
| 语言与发布边界 | 只输出当前模板语言；公开扩展失败关闭。 | 加载冻结语言的 prompt 或暴露不安全内容。 |

候选协议一行只描述 Review 的一种用途；它的完整接收范围见[共享治理边界](#共享治理边界)，还包括有界未知与 break-glass 确认。

### 扩展端口

| 端口 | Owner | 预期改动半径 |
| --- | --- | --- |
| 重复任务 | `config/extensions/*.json` 或被忽略的 `config/extensions.local/*.json` | 一份 descriptor、验证、重建。 |
| 插件宿主、治理与 ownership overlay | `scripts/researchos_data/plugins.py`、`plugin_governance.py`、`plugin_ownership.py`、前端与样式 manifest | 失败关闭的 manifest、来源、作用、准入、runtime availability、ownership 与 contribution 元数据；不从 manifest 加载任意代码。 |
| 经审查的 candidate adapter | `plugin-runtime.js`、经审查的第一方插件模块与 `candidate_envelope.py` | 插件拥有领域 normalize/generate/withdraw；Review 只消费统一 envelope。 |
| manifest 控制的 surface dependency | `plugin-runtime.js` 与一个具名 surface/dependency provider | 插件只向既有界面提供有界只读领域计算；manifest 禁用即移除。 |
| Work Item provider | 插件 manifest 与一个经审查的投影 adapter | 向共享的`现在`界面提供 identity、lifecycle、唯一下一步和可选真实截止日期，不创建新路由。 |
| 注册式原位动作 | 完整五字段 action contract 与平台 owner handler | 低风险、可撤销的 session/attention 写入可以原位执行；长期内容仍进入 Review。 |
| 直接对话路由 | `scripts/plan_context.py` | 有效 descriptor 不再增加任务专用 Python 分支。 |
| Provider | `scripts/researchos_adapters/provider_registry.py` 与 provider config | 只改 adapter、config 和测试。 |
| 数据投影 | 一个 builder owner | builder、contract、fixture、projection test。 |
| 独立 UI | model、workbench、view、style 与注册的 render adapter | 仅限[扩展阶梯](governance-guide.zh.md#扩展阶梯)的 C4；不得新建 Work Session、Inbox 或存储协议。 |

一份 JSON descriptor 同时声明任务、读取档位、结果模式、workspace、敏感度、authority 边界和双语文案，Dashboard builder 与 `scripts/plan_context.py` 读取同一份描述。没有这个端口时，新增一个重复任务即使不改变 authority 模型，也要同时修改任务目录、prompt 路由、workspace 映射、文案、验证和文档。随附示例默认禁用，因此新复制的 starter 不带任何扩展任务。task extension v1 刻意保持声明式，不加载任意 Python 或 JavaScript 插件；代码插件 API 需要新的 core API 主版本、迁移计划、沙箱与安全模型以及发布测试。扩展会进入现有任务选择和直接上下文路由，但不获得首屏位置或独立 panel。

descriptor 与 manifest 的兼容规则：

- `core_api_version` 必须是 `"1"`；未知主版本直接失败。
- 旧 v1 action 保持兼容；如果 action 声明任一 v1.1 动作字段，就必须同时声明 `confirmation_mode`、`risk`、`write_scope`、`reversible` 和 `public_behavior`。
- `confirmation_mode: inline` 必须使用 `execution: platform_registered`；manifest 不能把任意客户端代码提升为受信写入器。
- 公开 Work Item 动作只能声明 `demo_only` 或 `disabled`，除非另有经过审查的公开安全 handler。
- 扩展版本使用 `x.y.z`，ID 和 alias 不得覆盖核心路由。
- 空读取档位、重复 route 或 alias、目录目标，以及解析后逃出仓库的符号链接，都在构建前失败。
- `requires_human_confirmation: true`、`writeback_route: review`、`storage_owner: researchos_core` 是机器强制常量，不是提示性文案。
- `quick`、`standard`、`evidence` 保持首轮 1/5/8 文件上限，后一级保留前一级的读取项。
- 可用于 `public_starter` 的 descriptor 必须是 `public_safe`，默认敏感度只能是 `public`、`public_safe` 或 `local_only`。
- 一旦声明 `task.read_locales` 或 `authority.locales`，就必须同时提供 `en` 与 `zh-CN`，任务包只接收选定语言的读取路径和 authority 文案。两种任务文案都存于 descriptor，但生成任务数据只包含选定语言。
- 公开扩展若有任何声明的 Markdown 读取目标在 frontmatter 中明确标为 `internal`、`sensitive`、`private` 或 `not_exportable`，就失败关闭。
- 所有长期写回继续走既有 Review 与确认链。
- 仓库内置 manifest 必须显式声明分发一致性、来源与改造、真实部署、研究作用、数据与导出政策、组合、路由、成熟度证据和退役；旧 local manifest 只得到保守的兼容默认值。

如果一个普通任务扩展仍要求修改 `dashboard/app.js`、`dashboard/index.html`、Work Session state、Inbox store 或 storage contract，就停下来：它要么其实是扩展阶梯上 C4 的界面或数据能力，要么说明任务端口还不完整。这道改动半径门禁，是判断用户定制时内核是否仍然稳定的操作性标准。

### 演化架构

继续拆文件不是默认的重构策略。目标依赖方向是：

```text
Application Shell
  -> Capability Slices
       -> Platform Adapters
            -> Stable Kernel
```

稳定内核只拥有 authority、result、准入、运行状态、上下文外发、Work Session、Review、request 和存储安全合同；platform adapter 拥有 source reader、projection builder、HTTP client 和共享 UI primitive；一个 capability slice 完整拥有一个 user job 的 model、view、workbench、copy key、style、payload schema、行为测试与退场条件；application shell 只负责启动、workspace 组合、渲染调度和失败恢复。`core/services/components/views` 目录可以保持现状：先在 manifest 中声明每个模块属于哪个 capability、platform 或 kernel 边界，依赖图稳定后再考虑物理移动。只有安全不变量，或至少三个 capability 以相同语义复用的逻辑，才提升为 shared/core。一个 feature 不得直接读取另一个 feature 的 DOM、浏览器状态或内部 model。

`material_pipeline` 是第一个在 candidate adapter 边界上验证过的跨前后端 capability plugin。材料接入、材料升级和 research scout 保留各自的领域输入，但进入 Review 前由经审查的第一方 adapter 归一化为统一的 `CandidateEnvelope`；统一 Inbox 与 Codex handoff 只消费 envelope，不按原始字段分支。registry 不是任意代码加载器：manifest 只声明 runtime availability、安全、权限与 candidate type，adapter 实现仍是静态加载、经过审查的第一方模块。本仓库 共享宿主、adapter、envelope、endpoint 形状和浏览器行为，服务器仍拒绝长期 canonical 材料写回。禁用插件只移除它的 contribution，不新建第二套 Inbox、Review 或存储 owner。registry 之外没有旧 rule module、`ActionInboxStore` owner 或核心 type 分支，因此它不是永久双写层。另有两个端口在同一边界上验证过：`research_assets` 拥有资料投影、组合动作和 group/dissolution 候选，`research_portfolio` 拥有首屏可行动投影与资料中的完整生命周期板；`现在`与`资料`的壳层不计算这些领域状态。外部连接器尚未验证：Zotero/iPad 或证据阅读 bridge 必须单独审查 source adapter、权限和卸载边界。

更新分类与扩展阶梯的层级不是一回事，它决定每次改动走哪条路：

| 类型 | 默认路线 | 边界 |
| --- | --- | --- |
| C0 内容或投影刷新 | canonical source -> 既有 builder | 不改内核或前端；generated diff 单独显示 |
| C1 重复任务 | task-extension descriptor | 不改 app、index、Inbox 或存储 |
| C2 能力演化 | 一个 capability slice | slice owner、payload contract、行为测试 |
| C3 内核变化 | 显式架构审查 | 不变量、迁移、兼容层移除、发布证明 |

C2/C3 必须记录 user job、现有 owner、替换或合并决定、依赖方向、人工与生成的改动半径、移除条件、公私边界和验证。以下信号用来发现沉积，不是机械追求更小数字的目标。活动前端 owner 数量是观测信号，不是固定上限：每个 owner 都必须已注册、符合单文件预算并处于有界的 capability 改动半径内，C3 新增项还必须说明它替代、拆分或独立启停了哪个 owner。`app.js` 的全局依赖与顶层函数只能减少，而且不能靠包装或隐藏的 service locator 假装减少。新验证优先检查行为、schema、authority 和安全边界；源码 token 检查只保护加载顺序、禁止项和发布边界。生成投影与人工 diff 分开，parity 分叉 allowlist 必须精确对应真实分叉。

迁移有先后。保持 capability slice 由 manifest 声明，不为显示“有架构”而移动文件；新增端口前先复用已验证的 Utility、Library、Workbench、candidate 与 surface-dependency 端口；首屏投影以小型 bootstrap envelope 为目标保持精简，只有证据充分时才按需加载重型 payload；与报告中的原型共享的文件分步同步，任何公开写入前先运行公开安全与 parity 检查，绝不自动推送；slice 迁移时用行为、schema 或 authority 测试替换实现 token 检查，并在同一批删除旧检查；只有物理移动能解决已测得的依赖问题时，才考虑 feature 目录或 bundler。一次迁移若同时触及内核、多于一个 capability、存储语义和公私分叉，必须拆批。说不出要删除哪个旧 owner 时不新增抽象；新抽象在两个真实需求内没有第二个消费者，就退回 capability slice。

## 代码地图

`scripts/ros.py` → `scripts/researchos_kernel/` + `scripts/researchos_adapters/` → 带版本的记录与回执。内核拥有状态转移规则与纯协议合同（准入状态、候选信封、上下文与交接回执、任务信封、结果与规则演化）；适配器提供来源快照、暂存写入（`filesystem_staging.py`）、运行状态（`run_state.py`）、上下文包（`context_pack.py`）、provider 派发（`dispatch.py`），以及派发与 Dashboard runner 共用的启动边界（provider 登记、配置与 profile，执行端口及其本地 CLI 适配器，权限配置与 Policy Gateway）；`ros.py` 是二者之上的命令行客户端。依赖只向内：内核不引用自身以外的模块，适配器不引用 `researchos_server/`，由 `scripts/validate_agent_architecture.py` 校验。可选 Dashboard 沿 `scripts/serve_dashboard.py` → `dashboard/src/services/` → 视图运行。生成数据是投影，视图或 provider 不成为来源权威。

修改代码时，先通过公开入口复现问题，从下表选出 owner，只读该 owner 和它的直接协作者，把生成数据、provider 输出、Dashboard 状态与 Markdown 权威分开，先跑最小相关测试；改动跨越公开边界时再跑发布门禁。默认代码阅读深度为 L1：本地图、入口和一个 owner 模块。需要直接协作者时升到 L2；只有明确的架构审计或发布审计才做 L3 广泛读取。

```text
Demo 或 personal 启动
  scripts/start_researchos.py
    -> scripts/build_public_starter_data.py
    -> scripts/researchos_data/task_extensions.py
    -> scripts/researchos_data/plugins.py
    -> scripts/researchos_data/plugin_governance.py
    -> scripts/serve_dashboard.py
    -> dashboard/index.html
    -> dashboard/src/* owner 模块
    -> dashboard/app.js 编排

自动维护
  dashboard maintenance client
    -> scripts/researchos_server/evolution_planner.py
    -> scripts/researchos_server/auto_update_runner.py
    -> scripts/researchos_data/maintenance_pipeline.py
    -> 已记录的公开命令
```

Demo 写入 `08_exports/public_starter/generated-public-starter-data.json` 和 `dashboard/data/researchos-dashboard.json`。personal-vault 模式写入本地专用、Git 忽略的 `dashboard/data/researchos-local.json`，它绝不能提交。这些文件都是投影，不是编辑权威。默认公开 demo 可以显示只针对公开仓库的演化计划，但不能执行。personal-vault 模式与报告中的原型使用同一 UI 动作契约：白名单内的本地维护动作与本机安装的 Codex CLI 可以执行，长期写回仍遵守当前确认边界。维护靠[受控自我演化控制面](self-evolution-control-plane.zh.md)扩展，不靠自主修改自身。

| 问题 | 主要 owner | 只有需要时才继续读 |
| --- | --- | --- |
| 模式选择和一条命令启动 | `scripts/start_researchos.py` | `scripts/serve_dashboard.py`、运行配置校验器 |
| Demo 和 personal-vault 投影 | `scripts/build_public_starter_data.py` | 接入 Markdown、data-contract 模板 |
| Research Agenda 投影 | `scripts/research_agenda_projection.py` | 虚构 demo agenda 或本地 `06_active_context/research-portfolio.md` |
| 受控维护计划 | `scripts/plan_evolution.py`、`scripts/researchos_server/evolution_planner.py` | `scripts/validate_evolution_control.py`、维护 manifest |
| HTTP 路由和服务器组合 | `scripts/serve_dashboard.py` | 一个对应的 `scripts/researchos_server/*.py` 模块 |
| HTTP 认证和 JSON 请求边界 | `scripts/researchos_server/request_security.py`、`http_json.py` | `dashboard/src/services/request-auth.js`、handler 集成 eval |
| Provider schema 和状态 | `scripts/researchos_adapters/provider_registry.py`、`provider_config.py` | `config/researchos.runtime.example.json` |
| 跨客户端执行合同 | `dashboard/src/services/task-intent.js`、`dashboard/src/services/result-envelope.js`、`scripts/researchos_kernel/task_envelope.py`、`scripts/researchos_adapters/policy_gateway.py`、`scripts/researchos_adapters/provider_adapter.py`、`scripts/researchos_adapters/filesystem_staging.py`、`scripts/researchos_adapters/run_state.py`、`scripts/researchos_kernel/result_contract.py` | TaskIntent 是不可信请求；TaskEnvelope 分开请求与实际 runtime；只有 Policy Gateway 签发并复验短期机器 grant；Provider Adapter 只执行有界 provider 请求；Filesystem Staging 拥有 working copy、promotion、补偿与 rollback receipt；Run State 在 provider dispatch 前持久保留幂等键，并只按精确 correlation 恢复；Result/Error 只表达机器结果与公开安全的失败恢复；公开投影必须剥离私人 envelope。以上合同都不拥有长期 authority |
| 对话能力、typed routing 与材料边界 | `scripts/researchos_data/conversation_contract.py`、`task_router.py`、`capability_registry.py`、`repository_layout.py`、`public_conversation_catalog.py` | `scripts/plan_context.py` 为主入口；route receipt 不授予执行或写入权 |
| Markdown 元数据 profile | `scripts/researchos_data/metadata_profiles.py` | metadata-profile 数据合同及其 eval；只读投影，不写 Markdown |
| 声明式任务 DIY | `config/extensions/*.json`、`scripts/researchos_data/task_extensions.py` | `scripts/plan_context.py`、任务扩展 schema 与 validator |
| 插件宿主、治理、文档、portfolio 与逻辑归属 | `scripts/researchos_data/plugins.py`、`plugin_governance.py`、`plugin_docs.py`、`plugin_ownership.py`、`plugin_portfolio.py` | `scripts/query_plugin_portfolio.py`、插件与治理 schema、`docs/plugins/`、前端与样式 manifest、`scripts/validate_plugin_standard.py`、`scripts/validate_plugins.py` |
| 随附示例生命周期 | `scripts/manage_plugins.py`、`scripts/researchos_data/plugin_lifecycle.py` | Git 忽略的本地 manifest、插件校验、Dashboard 重建 |
| Codex 执行和用量报告 | `scripts/researchos_server/codex_runner.py` | `scripts/researchos_adapters/command_runner.py`、前端 runner client |
| 低冗余运行与空间提醒 | `work_session_upload.py`、`runtime_retention.py` | 用户附件不设任意配额、不自动删除；仅压缩日志和清理 owner 生成的 `.tmp` |
| 本地 Markdown 预览与写回 bridge | `scripts/researchos_server/local_file_bridge.py` | preview file server 和对应 eval |
| Runtime-read 白名单与文件投影 | `scripts/researchos_server/runtime_read_boundary.py`、`config/public-runtime-read-manifest.json` | preview/source-tree 消费者和 runtime-read eval |
| Inbox、卡组、清理和复查状态 | `scripts/researchos_server/` 中对应的 `*_store.py` | 对应前端 client 或 workbench |
| 前端数据读取和服务调用 | `dashboard/src/services/*-client.js` 或 `dashboard-data-client.js` | 后端路由 owner |
| 前端状态和持久偏好 | `dashboard/src/core/*.js` | 使用该状态的 view 或 workbench |
| 用户交互逻辑 | 对应 `dashboard/src/services/*-workbench.js` | 对应 view |
| 界面渲染 | 对应 `dashboard/src/views/*.js` | 对应 component 和 style |
| 共用视觉原语 | `dashboard/src/components/*.js` | 使用它的 view |
| 插件前端贡献 | `dashboard/src/plugins/*.js` | `config/plugins/` 中对应的 manifest、前端 manifest |
| 文案和语言 | `dashboard/src/core/ui-copy*.js`、`i18n*.js` | 只有语义变化时才读成对文档 |
| 页面组合 | `dashboard/index.html` | 被引用的 source 模块 |
| 应用编排 | `dashboard/app.js` | 功能 owner；不要先把新逻辑写进 app.js |
| 公开安全 | `scripts/validate_public_safety.py` | 治理和安全导出文档 |
| Agent 架构漂移 | `scripts/validate_agent_architecture.py` | 本地图和受影响 owner |

### 常见改动

新增或修改卡片字段时，一起更新相关 Markdown 或 data contract、投影 builder、对应前端 model、workbench 与 view，以及一个回归测试，继续区分来源事实、候选解释、人类确认和生成展示状态。新增 HTTP endpoint 时，在 `scripts/serve_dashboard.py` 注册路由，把行为放入一个 `researchos_server` owner 模块，再加一个前端 client，并测试成功路径与边界失败；路由不能把生成数据变成权威。修改 Dashboard 交互时，从对应 view 和 workbench 开始，可复用状态放 `core`，网络与文件行为放 client，渲染原语放 `components`，`app.js` 只负责组合和事件接线。新增 provider 时，同步更新 provider registry、provider config 校验、运行配置示例、用户手册的 provider 部分和测试；provider 只是执行适配器，不拥有记忆写回或确认权。新增公开工作流时，先判断现有工作流或模板能否承接；确实需要时只加一对语言文件，接到最小路由表，不另造第二条接入路径。新增重复任务路线时，从 `config/extensions/method-comparison.example.json` 开始；有效 descriptor 会同时被 `build_public_starter_data.py` 和 `scripts/plan_context.py` 读取，不要为普通任务在 `dashboard/app.js`、Work Session、Inbox 或存储中增加专用分支。

### 冻结规则与边界

新功能必须扩展或替换一个现有 owner，不得并行创建第二条`现在`、`资料`、Review 或接入主路径。兼容层必须同时带迁移回归和删除条件；迁移完成后删除旧分支，不长期保留两种语义。与报告中的原型共享的模块默认逐字节一致；只有在该原型的一致性登记表中、因隐私、示例或运行差异登记为分叉的文件可以不同。新增代码前先看能否删除或合并旧分支；若 `app.js`、某个 owner 或某条文档路线持续增长，应抽取职责或收敛路线，而不是提高预算。

Markdown 材料、用户明确确认和已记录规则是权威输入；Dashboard JSON、运行时 store、provider response 和 Agent 输出只是投影或候选，`dashboard/data/researchos-dashboard.json` 是生成的 demo 数据。`scripts/researchos_data/` 包含受支持的 runtime owner：`maintenance_pipeline.py`、`task_extensions.py`、`plugins.py`、`plugin_governance.py`、`plugin_docs.py`、`plugin_lifecycle.py`、`plugin_ownership.py`、`conversation_contract.py`、`capability_registry.py`、`plugin_portfolio.py`、`task_router.py`、`repository_layout.py`、`metadata_profiles.py`、`public_conversation_catalog.py`，以及供架构验证使用的只读前端与样式 manifest。三个 headless owner `capability_registry.py`、`plugin_portfolio.py` 与 `task_router.py` 只读取声明式合同并输出无副作用的 receipt 或分组投影，不拥有 provider、command、存储、Dashboard 或 canonical write。`plugin_docs.py` 负责机器校验的逐插件 README 合同与公开文档泄漏检查，不读取插件运行数据。`plugin_governance.py` 验证能力来源、作用、组合、路由和准入，不拥有运行时状态。`plugin_lifecycle.py` 只能经 `scripts/manage_plugins.py` 进入，并且只管理 Git 忽略目录中的随附示例。Research Agenda 解析是有文档的顶层投影 owner，不是兼容层。不要加入 `fake-*`、`walkthrough` 或 `example-original-developer-*` 案例：架构验证器会拒绝它们，starter 只保留一条接入路线。

`frontend_manifest.py` 声明全部活动 JavaScript owner；源码树必须与活动 manifest 完全一致，每个 owner 在 `index.html` 中只注册一次并先于 `app.js` 加载；数量由架构验证实时计算，文档不重复维护。`style_manifest.py` 拥有 `dashboard/styles/` 下全部样式，不允许未被引用的旁路样式。重新引入已移除的 UI 模块，需要提交 user job、替换关系、公私边界和回归证据。

### 可维护性预算

`dashboard/app.js` 可以编排，但不得超过 2,600 行，门禁不为容纳新补丁而放宽；Work Session 生命周期与首屏动作编排已经下沉到现有 workbench owner，新行为应继续下沉或替换旧分支。`scripts/serve_dashboard.py` 应保持在 650 行以内，路由行为放入 `researchos_server`。`scripts/build_public_starter_data.py` 应保持在 1,060 行以内；增加第二类职责前先抽出公开、有测试的 owner。普通前端 owner 不超过 1,500 行，纯双语文案 owner `ui-copy.js` 不超过 3,200 行。`scripts/ros.py` 不超过 2,100 行。`researchos_kernel` owner 不超过 750 行，`researchos_adapters` owner 不超过 600 行，`researchos_server` owner 不超过 1,200 行。每个 `dashboard/src/**/*.js` 必须在 `dashboard/index.html` 中且只注册一次；公开 Python 入口不得导入已删除或不受支持的兼容模块。

### 低冗余运行契约

Work Session 恢复历史最多保留 10 项摘要，而不是完整聊天；其他浏览器列表也必须有明确条目上限。在 personal-vault 模式与报告中的原型中，用户选择的会话附件不设产品级大小、数量或保存期限配额，上限只是本机文件系统和运行环境；公开 demo 接受单个不超过 1 GiB 的文件。附件不因空间阈值自动删除，上传采用流式写盘。runner JSONL 超过 5 MB 后压缩为最近 80 个 run 的合并状态，移除 prompt，并限制保留的输出。公开 demo 拒绝所有 runner 提交（见[用户手册第 4 节](user-manual.zh.md#4-可选的-dashboard)）。Demo JSON 与 Dashboard JSON 是覆盖式、可重建的投影，不是不断追加的历史数据库。已完成的会话附件由用户控制，启动时只清除上传 owner 自己留下的 `.tmp` 残片。会话副本较大或本机可用空间较低时，只返回非阻断的空间回执；提醒不得删除材料，也不得联动停用其他功能。

### 本地 HTTP 端点

本地端点在 `127.0.0.1` 上服务 Dashboard，不是公网 API。公开 demo 中，所有写入或运行更新的端点都返回 403 `public_starter_writeback_blocked`，只在 personal-vault 模式下执行；所有 `/codex-runner` 提交都失败关闭。会启动本地工作的读取端点（`/model-catalog`、`/evolution-plan`、`/provider-status`、`/codex-runner`、`/source-tree` 与 `/source-info`）会拒绝浏览器标明来自其他站点的请求。公开 demo 可能写入哪些文件，见[用户手册第 4 节](user-manual.zh.md#4-可选的-dashboard)。

| 端点 | 方法 | 作用 |
| --- | --- | --- |
| `/session-config` | GET | 返回运行模式与本次会话的请求令牌。 |
| `/data/researchos-dashboard.json` | GET | 返回示例投影（personal-vault 模式下返回个人库投影）。 |
| `/preview` | GET | 预览 Markdown。 |
| `/pdf`、`/corpus/*.pdf` | GET | 返回白名单内的 PDF 供预览。 |
| `/source-tree` | GET | 查看示例来源树。 |
| `/source-info` | GET | 查看文件信息。 |
| `/provider-status` | GET | 返回本仓库的 `copy_only` 能力，不探测本机 provider。 |
| `/model-catalog` | GET | 列出可选模型；本仓库 不为刷新它启动任何进程。 |
| `/evolution-plan` | GET | 显示只读的维护计划。 |
| `/codex-runner` | GET/POST | GET 只返回清理后的状态；本仓库所有 POST 都以 `public_starter_copy_only` 关闭。 |
| `/maintenance-action` | POST | 运行一个已登记的维护动作 ID；拒绝任意命令。 |
| `/work-session-upload` | POST | 把选择的来源保存到本机、Git 忽略的会话目录；本仓库不会把它发送给模型。 |
| `/open-local-file`、`/reveal-local-file` | POST | 用默认应用打开白名单内的文档，或在文件管理器中定位。脚本只能定位，不会被打开。 |
| `/feedback` | POST | 保存示例反馈。公开 demo：403；仅 personal-vault 执行。 |
| `/material-intake-inbox` | POST | 保存本地材料线索和交接说明，不上传或复制源文件。公开 demo：403；仅 personal-vault 执行。 |
| `/auto-update` | POST | 运行本地维护更新。公开 demo：403；仅 personal-vault 执行。 |
| `/confirmation-withdraw`、`/upgrade-inbox`、`/scout-inbox`、`/card-groups`、`/group-dissolutions`、`/clear-inbox`、`/evolution-decision`、`/research-scout` | POST | personal-vault 的写入与动作。公开 demo：403。 |

## 文件与目录

| 路径 | 用途 | 注意 |
| --- | --- | --- |
| `README.md` / `README.zh.md` | 项目是什么、一条上手路径、边界、文档地图、许可。 | 保持一屏，指向 docs。 |
| `AGENTS.md` / `docs/reference/AGENTS.zh.md` | Agent/LLM 入口。 | 英文版保留在仓库根目录，方便助手自动发现。 |
| `docs/user-manual.zh.md`、`docs/system-reference.zh.md`、`docs/governance-guide.zh.md` | 三份指南，各自与 `.en.md` 成对。 | 每个主题只有一个 owner，不新增平行指南。 |
| `docs/reference/AGENT_PROTOCOL.zh.md` | Agent 阅读、安全和写回协议。 | 不绕过确认流程。 |
| `docs/reference/CONTEXT_BUDGET_PROTOCOL.zh.md` | L-1–L3 阅读阶梯和上下文预算模式。 | 不默认下钻 evidence 或原始层。 |
| `docs/reference/WHERE_TO_PUT_NEW_MATERIALS.zh.md` | 原始、派生、工作流、当前、导出和模板层的放置指南。 | 不混用原始材料和派生笔记。 |
| `docs/reference/SAFE_EXPORT_POLICY.zh.md` | 公开安全准入规则。 | 不写任何允许导出敏感材料的例外。 |
| `docs/reference/PUBLIC_RELEASE_CHECKLIST.zh.md` | 发布前检查清单。 | 与 validator 一起使用。 |
| `LICENSE.md` / `docs/reference/COMMERCIAL_USE.zh.md` | source-available research license、学术再分发许可范围和商业授权边界。 | 与 README 保持一致。 |
| `researchos.config.yml` | Dashboard 主机、端口和语言。 | 不放 API 密钥。 |

| 目录 | 放什么 | 不放什么 |
| --- | --- | --- |
| `00_identity/` | 公开项目定位、原则和画像模板。 | 真实身份、机构关系、私人联系方式。 |
| `01_knowledge/` | 公开安全的材料索引、阅读笔记、项目知识。 | 原始语料、未公开论文、邮件或聊天记录。 |
| `02_decisions/` | 公开安全的决策日志、判断与取舍、确认/拒绝/需证据记录。 | 真实合作、学生、评审或申请策略。 |
| `03_cognition/` | 方法与协议：证据边界、确认流程和上下文预算。 | 私人思考流水账。 |
| `04_people/` | 虚构人物、公开安全角色、去身份化角色模板。 | 真实关系记录或私人联系方式。 |
| `05_workflows/` | 材料接入、资产类别扩展、生命周期、任务路由、Agent 协作、卡片组合、表达和自我演化流程。 | 依赖私人账号或密钥的流程。 |
| `06_active_context/` | 公开示例的当前状态、下一步、风险。 | 真实私人任务列表或长历史。 |
| `07_archive/` | 旧版公开说明、替换的模板、过期示例。 | 原本不能公开的材料。 |
| `08_exports/` | 经过安全导出的公开演示、教学和发布材料。 | 未经过安全导出审查的内容。 |
| `08_exports/public_starter/` | 一条统一接入案例和卡片成熟度示例。 | 真实姓名、机构、未公开论文、本地路径。 |
| `09_templates/` | Markdown skill 格式、frontmatter、卡片、提示词和验证模板。 | 已填入敏感真实内容的模板。 |
| `09_templates/data_contracts/` | Dashboard、案例、验证、关系、能力和扩展字段约定。 | 真实运行数据或密钥。 |
| `config/` | 无凭据的运行配置（`ros.json` 设为 `runtime_scope: public_starter`：本仓库 只走复制回退，不向长期来源准入）、报告中的原型所用的 provider 字段和案例开关。 | `.env`、API 密钥、私人端点。 |
| `config/plugins/` + `scripts/manage_plugins.py` | 本地、可逆的插件 manifest 与生命周期。 | 远程安装或 canonical 写回权。 |
| `corpus/` | 原始材料边界的空目录说明。 | PDF、邮件、聊天记录、网页抓取。 |
| `distilled/` | 公开安全的短摘要和可迁移原则。 | 私人长期记忆的压缩包。 |
| `evals/` | 公开安全的验证样例和冒烟测试格式。 | 用真实敏感材料构造的评估。 |
| `dashboard/` | 本地前端：`data/` 放 demo 投影，`src/` 放模块化源码，`styles/` 放样式。 | 私人投影。 |
| `scripts/` | 启动、生成、验证与维护；`researchos_kernel/` 是状态转换规则与协议合同，`researchos_adapters/` 是来源快照、暂存写入、run state、context pack 与 provider 启动边界，`researchos_server/` 是 Dashboard 服务器的 store 与 runner，`researchos_data/` 是上文列出的收窄 owner 集合。 | 密钥或本机路径。 |
| `docs/` | 中英成对的指南、报告与参考政策。 | 不成对的读者文档。 |

`08_exports/public_starter/` 案例默认进入公开 demo 投影；维护者可以按[用户手册第 5 节](user-manual.zh.md#5-用自己的材料)关闭，关闭后示例文件保留为只读对照。新用户自己的材料放进 Git 忽略的 `personal_vault/`，它沿用同样的分层布局；`08_exports/public_starter/onboarding-step-by-step.zh.md` 是从示例走到个人库的首次上手说明。其他人物、项目、报告和深读，等第一批结果复核之后再加。邮件、外部调研论文、审稿任务、预算、算力、数据集权限等重复出现、需要自己生命周期的新类别，先走[扩展阶梯](governance-guide.zh.md#扩展阶梯)，并读 `05_workflows/research_management/asset-type-extension-workflow.zh.md` 和 `09_templates/data_contracts/researchos-extension-contract-v1.zh.md`，再决定是否新增目录、模板、脚本或 Dashboard 界面。

官方入口文档按语言成对维护，不在同一个 Agent 可读文件里放两套语言；每个成对文件右上角都有指向另一语言的切换链接。底层 demo/case 记录由 `public_starter.content_language` 选择：`en` 使用英文文件，`zh-CN` 使用 `.zh.md` 文件，中性文件两边都保留。另一种语言的文件只作参照。生成器也把任务模板和 assistant prompt 冻结在所选内容语言；生成的 Dashboard 数据不携带非活跃语言的 prompt/模板变体，所以切换界面语言不会把它们悄悄带进上下文。需要切换模板语言时，修改 `content_language` 或传入 `--language`，然后重建。

ResearchOS 文件应写成 skill 可读的 Markdown，而不只是给人看的笔记。使用 `09_templates/` 中现行的 `project-template.md`、`paper-template.md` 等卡片模板，沿用其中的 frontmatter、Agent Summary 与证据边界。

## 验证

编辑时先跑最小相关 eval。架构与扩展改动的核心检查是：

```bash
python3 scripts/validate_task_extensions.py
python3 scripts/validate_plugins.py
python3 scripts/validate_plugin_standard.py
python3 scripts/validate_agent_architecture.py
python3 scripts/validate_public_safety.py
python3 scripts/plan_context.py --list --lang zh-CN
python3 scripts/build_public_starter_data.py
python3 -m unittest discover -s evals -p 'test_*.py'
```

发布前逐条运行 `.github/workflows/validate.yml` 中的步骤，即本仓库的 CI；`CITATION.cff` 已写入发布日期，所以在本机要在已提交、没有未提交改动的工作树上，带 `--expected-commit "$(git rev-parse HEAD)" --require-clean` 运行 `validate_release_metadata.py`，不带这两项就会失败。最后从全新复制的目录启动一次 Dashboard，并跑一次小型 personal-vault 流程。
