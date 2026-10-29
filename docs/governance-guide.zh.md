<p align="right">
  <a href="governance-guide.en.md">English</a> | <strong>中文</strong>
</p>

# ResearchOS 治理与扩展指南

这份指南说明哪些内容可以进入公开 starter，怎样在不削弱权威边界的前提下改造和扩展它，随附插件怎样安装和移除，以及发布、贡献、安全报告和许可如何处理。面向 GitHub 的简短文件 `CONTRIBUTING.md`、`SECURITY.md` 和 `SUPPORT.md` 在仓库根目录，中文版在 `docs/reference/`；本指南保存更完整的原则。怎样使用系统见[用户手册](user-manual.zh.md)，内核合同和代码 owner 见[系统参考](system-reference.zh.md)。

## 公开边界

公开 starter 是独立的 Git 项目，只展示结构、机制、示例数据、Dashboard 文件、脚本入口和公开安全文档。它不是任何非公开工作系统的复制品，也不能从非公开 Dashboard 投影复制内容。材料先进入系统，Agent 或脚本只能形成候选，人类确认后才成为可复用状态，发布前还要经过安全导出检查。公开 starter 要把这个模型讲清楚，而不是把自己说成自治科学家或自动记忆库。

| 层级 | 可以放什么 | 不可以放什么 |
| --- | --- | --- |
| `source material` | 公开安全摘要、引用线索、公开链接说明 | 原始语料、保密材料、未授权全文 |
| `candidate` | 未确认摘要、下一步建议、示例收件箱条目 | 被写成确定事实的 Agent 输出 |
| `confirmation` | 人类确认、拒绝、补证据要求 | 无来源的自动决策 |
| `validation` | 验证脚本输出、发布检查、边界说明 | 无法复现的口头保证 |
| `export` | 公开安全案例、模板、生成的 starter 数据 | 真实敏感人物、密钥、本地路径、运行日志 |

因此，仓库可以包含公开安全的前端和本地服务器文件、虚构的统一接入材料和卡片成熟度示例、不含本机或远程执行器的 copy-only 交接配置、中英成对的核心文档、公开安全模板、验证脚本、provider 注册表和启动脚本，以及简短的 GitHub 支持文件。仓库不得包含非公开工作内容或 Dashboard 投影、原始语料、运行日志、API 密钥、令牌或凭据、真实人物、学生、合作者、评审或未公开论文细节、本地绝对路径或个人账号信息，以及未经审查却被写成事实的 Agent 输出。

公开版能运行和写入什么，包括单独配置的 personal-vault 模式和只复制的 `ros` 边界，见用户手册第 [3](user-manual.zh.md#3-会话调度器与命令行检查) 节和第 [4](user-manual.zh.md#4-可选的-dashboard) 节。公开版的入口是非公开工作版的子集，或是该版已有能力的演示与自托管替身：personal-vault 模式、虚构的 `ros_demo.py` 演练、研究议程查询与维护门面。除此之外，这里出现的启动模式、provider 配置、Dashboard 文件、运行器门面、案例开关和文档入口，都应在非公开工作版中保留同名能力。这条一致性规则不是让公开版复制数据，而是让两边可以长期一起维护：公开版展示结构和机制，非公开工作版保留真实状态的权威。

## 改造 starter

公开 starter 本来就允许用户改造。安全的改法是固定权威边界，只调整它周围的内容、模板、工作流、provider 或 Dashboard 界面。Markdown 来源加人类确认才是权威；Dashboard JSON、provider 返回、Codex 输出和生成文件，在复核前都只是投影或候选。先改内容、模板和工作流，再改 Dashboard：新的 Dashboard 按钮应该是最后一步，而不是证明一个想法重要的第一步。

| 层级 | 适合先改什么 | 从哪里开始 | 验证 |
| --- | --- | --- | --- |
| 个人内容 | 用自己的公开安全卡片替换虚构 demo。 | `00_identity/` 到 `06_active_context/`，`docs/reference/WHERE_TO_PUT_NEW_MATERIALS.zh.md` | `python3 scripts/build_public_starter_data.py --personal-vault --write` |
| 卡片格式 | 给论文、人物、项目、报告或决策卡增加字段。 | `09_templates/project-template.md`，`09_templates/paper-template.md` | 链接检查和一次 Dashboard 人工复查 |
| 提示词 | 改成适合自己助手或模型 provider 的任务提示词。 | `09_templates/standard-agent-prompts.zh.md` | 确认仍然要求边界、证据、候选状态和人类确认 |
| 工作流 | 为重复研究操作增加一条任务路线。 | `05_workflows/research_management/`，`09_templates/workflow-template.md` | 增加中英链接并跑链接检查 |
| 任务扩展 | 不修改 Dashboard 编排，增加一条重复任务路线。 | `config/extensions/method-comparison.example.json` | `python3 scripts/validate_task_extensions.py` 和 `python3 scripts/plan_context.py <id> --lang zh-CN` |
| Provider | 接入本地模型或 provider adapter。 | `config/researchos.runtime.example.json`，`scripts/researchos_adapters/provider_registry.py` | `python3 scripts/validate_runtime_config.py` |
| Dashboard | 增加筛选器、卡片盒或工作台界面。 | `dashboard/src/`，`scripts/build_public_starter_data.py`，[代码地图](system-reference.zh.md#代码地图) | `python3 scripts/validate_agent_architecture.py` 加一次浏览器冒烟测试 |

新增文件夹、模板、脚本、Dashboard 区域、provider 或导出目标之前，先回答九个问题：它支持什么判断或行动？原始来源在哪里，权威边界是什么？默认敏感性是 `public`、`internal`、`local_only` 还是 `not_exportable`？人类确认前的候选流是什么？已确认的 Markdown 放在哪里？它能连接哪些现有对象？用什么命令、测试或人工复查发现漂移？它能进入公开输出，还是只能留在私人或本地库？它能否使用声明式任务端口，而不是新增前端或存储代码？这些答案还不清楚时，就先按普通材料接入处理。

有些边界不能被改掉。生成的 Dashboard JSON 永远不是权威记忆。API 密钥、provider 令牌、原始私人语料、在投稿件和本机路径都不进入受跟踪文件。私人或边界不清的材料不能写成公开文本。新材料类别不单独占一个顶层目录；没有模板、候选流和验证规则之前，不加 Dashboard 界面。provider 的执行结果从来不是记忆写回的权威。

### 扩展阶梯

邮件线程、审稿任务、算力额度、预算、数据集权限、外部调研论文等反复出现的新类别，用这个阶梯判断走到哪一步。超过 C1 之前，先读 `05_workflows/research_management/asset-type-extension-workflow.zh.md` 和 `09_templates/data_contracts/researchos-extension-contract-v1.zh.md`。这里的层级不是[系统参考](system-reference.zh.md#演化架构)里的更新分类。

| 层级 | 含义 | 用户能看到什么 |
| --- | --- | --- |
| C0 | 发现重复需求。 | 一条说明需求和边界的笔记。 |
| C1 | 已有 2—3 张试点卡片。 | 字段开始稳定的手写卡片。 |
| C2 | 已有模板和流程。 | 可复用的卡片模板和接入路线。 |
| C3 | Builder 或 Dashboard 能读取。 | 它进入`资料`、Work 或待复核，且不自己发明状态。 |
| C4 | 值得成为独立界面。 | 独立的 Dashboard 卡片盒或 tab。 |

想让 Agent 在写任何文件之前先给出扩展提案，可以用：

```text
我想为 ResearchOS 增加一个反复出现的新类别：[类别]。

请读取 AGENTS.md、docs/governance-guide.zh.md、05_workflows/research_management/asset-type-extension-workflow.zh.md 和 09_templates/data_contracts/researchos-extension-contract-v1.zh.md。暂时不要编辑文件。

请返回：
1. 这只是普通材料接入，还是确实需要扩展；
2. 建议的 asset_class 和默认敏感性；
3. 来源权威和导出边界；
4. 两张试点卡应该有哪些字段；
5. 是否需要 answer、artifact、writeback/待复核、模板、工作流、dashboard 筛选或独立界面；
6. 验证命令；
7. 停止规则和未决问题。
```

确认扩展路线之后再写文件。

## 任务扩展与插件

插件是可选的，不在首次使用路线里，首页也没有插件商店。即使什么都不安装，`现在 / 资料`、事项内 Work/Review 和 Agent 任务仍然完整可用。插件系统处于冻结状态：随附示例和本地、可逆的生命周期可以查看和使用，但不在功能开发之中。扩展只应承载反复需要、边界独立的能力贡献，并且随时可以关闭；它不能增加另一套页面、状态或资料权威，也从不替用户确认事实。具体任务只是这项贡献的入口、工作流适配器或评价探针，模型或 skill 是执行选择。安装成功或完成一次任务不能证明一般能力；能力主张需要相关任务经历、失败案例和变化情境中的证据。先用核心，只有反复出现的需求才引入扩展。哪些 manifest 属于可选扩展、哪些属于 Dashboard 基础投影，见[产品层](system-reference.zh.md#产品层)。

当新行为可以复用现有 Work Session、结果模式、待复核和存储边界时，使用声明式任务端口。放在 `config/extensions/` 下的一份 descriptor 同时被 Dashboard builder 和 `scripts/plan_context.py` 读取；只供个人使用的 descriptor 放在 Git 忽略的 `config/extensions.local/`。这个端口只声明任务元数据、读取档位、结果模式、workspace 路由、敏感度、authority 和双语文案，不能执行任意代码，也不能创建新的持久化路径。版本字段和兼容规则见[扩展端口](system-reference.zh.md#扩展端口)。设计自己的任务时，从 `config/extensions/method-comparison.example.json` 开始，把个人版本放到 `config/extensions.local/<id>.json`，修改双语文案、authority 和读取字段，验证后再启用；经审查、可分发的 descriptor 可以放入 `config/extensions/`。

```bash
python3 scripts/validate_task_extensions.py
python3 scripts/plan_context.py --list --lang zh-CN
python3 scripts/build_public_starter_data.py --write
```

如果普通任务仍然要求修改 `dashboard/app.js`、Work Session state、Inbox store 或 storage contract，先停下来重新分类，不要直接写代码。

### 安装随附示例

最简单的做法是对 Agent 客户端说：“请安装 ResearchOS 的 method_comparison 示例插件。”Agent 会运行仓库内的生命周期命令，说明权限边界，并确认任务已经出现；你不需要复制 manifest，也不需要了解它的目录。确定性命令是

```bash
python3 scripts/manage_plugins.py install method_comparison
```

结果应显示 `method_comparison · 研究方法对比 · 已启用`。这个任务进入既有的 Agent / Work Session 任务目录，不会新建第二个聊天、Dashboard 页面、Inbox 或记忆存储。

随附的 `cross_domain_scientific_entry` 插件用同样方式安装（`python3 scripts/manage_plugins.py install cross_domain_scientific_entry`），它把进入陌生领域组织成一个有边界的 Case Pack：Case Charter、最小领域地图、路线注册表、候选谱系、准入回执、保持/迁移报告和案例结算。它提供的是工作流和权威边界，不提供领域专业性，也不携带任何私有研究记忆；它的实际价值取决于你的来源、判断、模型能力、领域反馈和执行纪律。私有或 personal-vault 运行时可以在运行时把同一内核与你的本地材料结合，但这些材料不会被复制进插件。

如果希望在 ChatGPT 或另一个 MCP 客户端中续接本地 Codex task，`python3 scripts/manage_plugins.py install codex_thread_handoff` 只安装声明式 ResearchOS 任务合同。它不会暴露本机、创建 tunnel、安装 bridge 或注册 ChatGPT 连接器；还需要由用户独立运行并配置一个经过验证、带认证的只读 MCP 连接器。只有[其 README](plugins/codex-thread-handoff/README.zh.md#可用性与一致性)中的四个就绪状态都分别核对过，才可称为已就绪。

管理器只接受仓库随附、经过审查的 `local_installable` `*.example.json` descriptor。它把公开安全版本复制到 Git 忽略的 `config/extensions.local/`，再用 `scripts/validate_plugins.py` 重新校验插件宿主；它不重建 Dashboard 数据，需要时运行 `python3 scripts/build_public_starter_data.py --write`。它不管理内嵌的 foundation 或 bundled capability，不联网、不接受 URL、不下载或执行远程代码，也不写 canonical Markdown。长期变化仍须通过精确事项内的 Review 和人类确认。如果你手动修改了已安装的 manifest，管理器会拒绝覆盖或删除它。

```bash
python3 scripts/manage_plugins.py disable method_comparison
python3 scripts/manage_plugins.py enable method_comparison
python3 scripts/manage_plugins.py uninstall method_comparison
python3 scripts/manage_plugins.py list
```

同样的命令也适用于 `cross_domain_scientific_entry`。`disable` 保留本地 descriptor，但撤下其运行时贡献；`uninstall` 删除未被修改的本地 descriptor 并重新校验插件宿主。卸载后运行 `python3 scripts/validate_plugins.py` 和 `python3 scripts/validate_public_safety.py` 确认恢复干净基线；示例以后仍可再次安装，不会有本地 manifest 被 Git 跟踪。

### 扩展 Dashboard 的结果与待复核

Dashboard 通过 `dashboard/src/services/work-session-router.js` 暴露三种结果模式：`answer`、`artifact` 和 `writeback`。Work Session 接收目标和来源提示，working deck 接收按需卡片，待复核接收明确的长期变化提案。新增卡片类型时，先让它能被搜索、能加入当前牌组、能写进现有任务包；不要先加新的首页模块。Dashboard 动作从来不只是一个按钮，它必须保持以下接口语义：

1. 普通阅读走 `answer`，需要文件成果走 `artifact`，拟议的长期系统变化走 `writeback`；view 不得直接写 Markdown。
2. 普通选卡只更新 working deck，不导航；只有明确的“提出写回”才创建行动并打开待复核。
3. 同一 action key 区分 active、archived、withdrawn 和 completed；重新加入恢复 active，并以新的时间戳与旧的 runner completion 记录隔开。
4. 公开 starter 只返回 copy-only 任务包和待复核说明；本机 Codex 与 Claude Code CLI 派发、Inbox/canonical 写回和任意命令保持关闭，模型目录、执行控件、runner 状态和维护动作都由 runtime capability 控制，不能只靠 CSS 隐藏。
5. 每个新状态都要同步更新双语 UI 文案、手册、前端契约测试、公开安全检查和一次桌面与移动端浏览器流程。
6. 新能力默认不占首屏：通过扩展契约贡献有界的 Work Item 或动作，或者复用按需展开的 Work Session 结果闭环。空闲时直接自然语言输入保持折叠；只有任务需要时，才展开材料、卡片、成果、待复核或维护控件。
7. 公开版旧任务包可以留在页面历史中，但不得作为 assistant 回答递归嵌入后续任务包；只带上理解追问所需的先前用户意图。

复用 `work-session-router.js`、`work-session-state.js`、`work-session-workbench.js`、对应 view owner、`doing-board-state.js`、`inbox.js` 和 `storage-contract.js`，不要创建第二套结果闭环、localStorage key 或平行收件箱。无界面集成通过现有扩展 manifest 和 Work Session 合同贡献有界任务，不另建提示词路由器或第二套 Work Session；它保留候选先于确认、冻结的模板语言和待复核边界，普通用户仍从 Agent 对话或“开始”页进入。

## 发布、贡献与支持

| 文件 | 职责 |
| --- | --- |
| `README.md` | 项目定位、一条上手路径、边界、文档地图、许可。 |
| `README.zh.md` | 中文优先入口，帮助中文读者走中文路线。 |
| `CONTRIBUTING.md` | 贡献范围、公开安全规则、拉取请求检查；中文版在 `docs/reference/CONTRIBUTING.zh.md`。 |
| `SECURITY.md` | 安全相关问题的报告方式和披露边界；中文版在 `docs/reference/SECURITY.zh.md`。 |
| `SUPPORT.md` | 求助路径、问题应提供的信息、支持边界；中文版在 `docs/reference/SUPPORT.zh.md`。 |
| `docs/*.md` | 用户手册、系统参考和本指南，以及技术报告。 |

新增根目录 Markdown 文件前，先判断它是否真是 GitHub 用户会去找的入口；详细解释应放进[文档地图](README.zh.md)里对应的现有 owner。接入文件保留在仓库中，方便用户对照放置位置和字段。用户把自己的内容写进 Git 忽略的 `personal_vault/`，那里从不显示这些示例，所以既不删除也不关闭它们；把案例移出 demo 投影的可选维护者开关见[用户手册第 5 节](user-manual.zh.md#5-用自己的材料)。

发布前，维护者在公开仓库逐条运行 `.github/workflows/validate.yml` 中的步骤，即本仓库的 CI。原始维护者还可以从非公开工作版运行私有的发布边界检查；它不随公开 starter 发布，因为它核对的是私有来源与本公开包之间的导出边界，公开贡献者不需要拥有它。检查确认：公开 starter 是独立的 Git 项目；必要目录和文件都在；`docs/` 保持中英成对；关闭的案例不再进入活跃示例数据；公开 provider 能力是 copy-only，本机 Codex 与 Claude Code CLI 派发关闭、不存在远程 provider；没有本地路径、密钥、敏感人物或禁止出现的边界词；公开独有的入口都属于已登记的演示或自托管替身。

审查拉取请求时，维护者先看四件事：是否真的改善用户理解或运行体验，是否维持公开安全边界，是否更新了对应的中英文档，相关验证脚本是否通过。大型示例、真实人物材料、远程 provider 调用、商业部署说明和未经确认的 Agent 输出，通常要缩小范围或移出公开仓库。安全相关问题按 [SECURITY.zh.md](reference/SECURITY.zh.md) 的私下报告路径处理，求助应提供的信息见 [SUPPORT.zh.md](reference/SUPPORT.zh.md)。

许可见 [LICENSE.md](../LICENSE.md)；商业使用边界和参考过的现成协议见 [COMMERCIAL_USE.zh.md](reference/COMMERCIAL_USE.zh.md)。
