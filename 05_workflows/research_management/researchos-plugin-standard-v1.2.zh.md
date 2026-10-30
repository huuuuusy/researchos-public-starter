---
title: ResearchOS 插件统一规范 v1.2
layer: workflow
status: active
sensitivity: public_safe
owner: researchos_core
last_reviewed: 2026-08-15
language: zh-CN
normative: false
semantic_version: 1.2.0
translation_of: researchos-plugin-standard-v1.2.md
translation_status: controlled
---

# ResearchOS 插件统一规范 v1.2

<!-- semantic-anchor: agent_summary -->
## Agent Summary

ResearchOS 不是一个不断下载插件的容器，而是任务与能力的精炼和治理系统。插件分为 **任务主导** 与 **能力主导** 两类：前者围绕一个可自然表达、可重复、边界清楚的用户任务形成执行闭环；后者围绕跨任务保持的稳定转化能力积累证据。更强模型会淘汰重复常识、没有可测增益的薄 skill，但不会替代私有知识、证据门禁、工具权限、来源版本、人类确认与长期演化。`researchos_plugin_task_v1` 与 `researchos_plugin_capability_v1` 都是不可安装的治理母版；具体插件必须证明相对当前裸模型或无插件宿主的边际价值，并承担 authority、作用后果、数据、来源谱系、路由、验证和退役义务。

核心命题：**stronger models reduce the need for brittle skill wrappers, not for governed capability systems**。模型越强，创建和保留插件的门槛应越高，而不是插件数量越多。

<!-- semantic-anchor: layer_model -->
## 0. 五个不能混称的层次

- **Agent skill**：供 ChatGPT/Codex 按需加载的 instructions、references、assets 或 scripts，是可复用工作流的作者格式。
- **Codex/OpenAI plugin**：把一个或多个 skills、MCP 连接器和资源打包安装与分发的外部产品容器。
- **Agent harness**：把模型、context、tools、state、policy、trace、evaluation 和 recovery 组织成可运行、可观察 episode 的环境。
- **ResearchOS plugin**：ResearchOS 内部受治理的任务或能力 contribution 与生命周期单元；它可以由 skill 启发或由外部分发包承载，但不是同一概念。
- **ResearchOS**：跨 episode 保存能力证据、研究者判断、authority 后果与规则演化的长期治理系统；它可以调用 skill、plugin 或 harness，但不等于其中任何一个。

Skill/Codex 是日常调用、阅读、结构化、起草、验证和写回建议的操作表面；Dashboard 是资产、关系、证据、Inbox 和 handoff readiness 的视觉发现表面。两者共享 Markdown authority、确认与验证规则，彼此互补而非上下级。

<!-- semantic-anchor: archetypes_and_lifecycle -->
## 1. 两类母版和衍生插件

母版属于核心项目，但它本身不是用户要安装的插件。它规定 ResearchOS 愿意接纳什么任务或能力。具体插件先声明 `archetype`：

| Archetype | 稳定 owner | 适用条件 | 不得伪装 |
|---|---|---|---|
| `task_led` | 一项重复用户任务及其 `task_contract` | 一个主入口、明确输入/输出、确认门、完成标准、失败恢复和停止条件 | 不得为了安装插件而制造 capability claim |
| `capability_led` | 跨任务 `capability claim` | 多个任务共享同一条件性转化，需要跨 episode 证据、组合、准入与独立退役 | 不得把 task 名称放大成能力 |

分类看产品重心，不看底层复杂度。任务主导插件可以有严谨脚本和验证门，但只服务一个用户 job；能力主导插件可以投影成多个 task，但其稳定语义不依赖某一个入口。任务主导插件只有在确实出现跨任务不变量并经过 Review 后，才可迁移为能力主导；重复使用本身不自动构成能力。

具体插件还必须选择一种产品位置：

- `foundation_projection`：广泛复用的嵌入式投影或基础能力，不拥有对话任务。
- `bundled_capability`：随 OS 提供、边界明确的私有或公开能力。
- `optional_extension`：本地、可逆、默认关闭的安装项。

产品位置以 `product_tier` 为唯一源字段，host 按固定映射派生部署模式：三者分别对应 `embedded_foundation`、`bundled_default_on` 和 `local_installable`。源 manifest 可省略 `governance.deployment_mode`；显式旧值必须与派生值一致，否则拒绝；归一化输出始终保留该字段。紧凑源需要更新后的 host，旧 host 须接收显式补全的派生值。这项输入放宽不改变实际生命周期，也不豁免报告中的原型与可下载版本之间的源级 parity。生命周期界面不能再把嵌入式能力伪装成可由本地示例安装器安装或卸载的插件。

生命周期由部署方式推导：foundation 是 `core_bundled`，只通过 `core_release_change` 退场；bundled capability 是 `release_bundled`，通过 `release_change` 退场；只有本地扩展使用 `manifest_present` / `remove_manifest`。旧 v1 local manifest 通过保守兼容层继续使用旧生命周期。

任务主导插件以 `task_contract` 为稳定单元，至少声明 user job、输入、输出、不变量、确认门、完成标准、失败模式、恢复、相对裸模型的比较和退役条件。它不进入 capability registry，也不填写 `capability_bindings` 或 `task_projections`。创建它的理由不是“多一个 task”，而是同一任务反复出现，且私有规则、执行纪律或确定性验证相对裸模型产生可测增益。

能力主导插件仍以 capability claim 为稳定单元。Capability claim 拥有语义、证据、准入和退役条件；plugin contribution 拥有实现、权限、装配和部署生命周期；task 是 capability 面向某个对象或情境的入口、工作流适配器或评价探针。Capability 不是给现有 task 换一个更大的名字。每项 claim 至少声明 intended transformation、unit of analysis、context envelope、evidence criteria、known failures/counterexamples、authority boundary、review trigger 和 retirement condition。

两条身份链必须分开：

- 任务主导：`task contract -> task contribution -> episode evidence -> task validation/adoption -> retirement`；
- 能力主导：`canonical capability claim -> capability contribution -> task projection -> episode evidence -> capability admission receipt`。

Canonical claim 只属于能力主导插件，由 `researchos-capability-registry-v1.json` 的 `capability_claims` 拥有。任务主导插件不得为了通过 validator 建立同名假 claim。两类插件中，单次任务成功、skill 已安装、plugin 已启用、harness 已运行或测试绿色，都只增加局部证据，不能自动升级成熟度。

<!-- semantic-anchor: external_sources -->
## 2. 外部 skill 是来源，不是直接搬运的包

外部 skill 可以先以链接进入候选台账，之后 ResearchOS 可以：

1. 只保留 `reference_only` 链接；
2. 把一个来源改造成 `adapted_external` 插件；
3. 把两个或以上来源组合成 `composed_external` 插件；
4. 经独立证据和 Review 后，把形成的能力吸收到 foundation，极少数情况下进入 stable kernel。

协议故意不提供 `raw_copy`。外部来源必须声明 HTTPS 链接、固定版本或检索边界、许可、复用方式、改造摘要和残留运行时依赖。除非许可允许且另有实现决策，源代码与原始 instructions 继续由上游拥有。

在 manifest 产生之前，先使用 `09_templates/external-capability-source-candidate.md`。可检索链接进入 `config/capability-sources.json`；它是来源候选台账，不是安装清单。只有 `promoted` 来源才能进入 adapted/composed manifest，并且 manifest 的来源快照必须与台账一致。

“吸收”不是“安装”。一个起源于 skill 的能力，如果其稳定部分已经成为 OS 原生规律，可以不再作为独立插件存在。进入 stable kernel 的门槛最高：跨能力反复需要、本地验证、人工准入、明确 owner、兼容计划、回滚和 Review 缺一不可；仅仅因为方便不构成理由。

<!-- semantic-anchor: governance_card -->
## 3. 一张治理卡，两个分支

每个仓库内置 native plugin 和 task extension 必须显式声明 `governance`：

1. `archetype`：`task_led` 或 `capability_led`，不得由文件类型或名字猜测。
2. `distribution`：通用、私有或公开变体；精确一致、有限变体或仅私有。
3. `lineage`：对应母版、衍生方式、候选来源、改造、依赖、当前放置位置和拟吸收目标。
4. `deployment_mode`：真实属于嵌入、随附还是本地安装。
5. `effects`：独立于代码权限的研究作用后果；每个 action 必须声明一个允许的 effect。
6. `data_policy`：保密级别和导出策略分轴表达，并拒绝矛盾组合。
7. `composition`：`requires / provides` 使用 contribution ID；`optional_integrations / conflicts_with` 只引用已登记 capability claim。
8. `routing`：使用 `capability / task / core_route / workflow` 类型化 handoff。
9. `admission`：与 archetype 对应的成熟度、proof、复核日期、重验触发和退役条件。
10. 既有 `validation`：可执行命令和行为测试。

Lineage 与 runtime dependency 是两条不同的轴。Native plugin 没有外部来源复用，因此保持 `reuse_policy=native`，但它仍可能依赖由用户操作的 MCP connector 等 runtime；这种运行依赖不表示复制了外部代码。Adapted 或 composed plugin 仍必须记录 pinned source、license 和 transformation。

类型分支：

- `task_led` 必须填写一个 `task_contract`，不得填写 `capability_value`、`capability_bindings` 或 `task_projections`；`composition.provides` 只提供这一个 task contribution。
- `capability_led` 必须填写 `capability_value`、`capability_bindings` 和 `task_projections`；每个 contribution 且只绑定一次到 canonical claim，每个 task 且只投影一次。

宿主 `permissions` 回答代码可以读什么、执行什么；`effects` 回答能力可以对研究和工作区造成什么后果。一个没有命令权限的声明式任务，仍可能通过既有 owner 形成 Review 候选或执行可恢复清理；这两种边界不能再混写。

<!-- semantic-anchor: admission -->
## 4. 准入不等于启用

`enabled` 只表示运行时是否加载，不能证明任务质量或能力质量。成熟度按 archetype 独立推进：

- 任务主导：`draft -> instrumented -> task_validated -> user_adopted -> deprecated`
- 能力主导：`candidate -> instrumented -> locally_validated -> human_admitted -> deprecated`

从 `instrumented` 开始必须有 proof refs。任务主导插件只有在 `task_contract.comparison_status=evaluated` 且真实任务证据证明相对裸模型有净增益时，才能成为 `user_adopted`。能力主导插件的 `human_admitted` 仍要求 `capability_value.comparison_status=evaluated`，并且每个已绑定 claim 都有一份 `researchos-plugin-admission-receipt-v1` 人工准入回执。合同、authority、公开变体、依赖、模型基线或行为变化会触发重验。

<!-- semantic-anchor: baseline_value -->
## 5. 相对裸模型的任务或能力价值门禁

每个插件都要回答：**如果不用这套任务流程或能力，直接让当前模型或宿主完成工作，会损失什么？**

任务主导插件在 `task_contract` 中比较完整 workflow；能力主导插件在 `capability_value` 中比较跨任务 transformation。两者都区分预期与证实，不允许用“模型更聪明了”或“skill 看起来有用”代替比较。可声明的增益包括质量、可靠性、证据边界、authority safety、效率、恢复和个人适配；负担包括上下文、误触发、维护、外部依赖和隐私。`planned` 只是比较计划，`evaluated` 才能支持采纳；模型、任务、合同或依赖变化后转为 `stale`，必须重验。

处置规则：

- 当前模型已经稳定完成：不创建 skill；
- 偶尔参考：只保留来源链接；
- 一个边界清楚的重复 user job 有可测增益：建立 task-led plugin；
- 多个任务共享同一稳定转化且有跨 episode 证据：建立 capability-led plugin；
- 已成为跨能力稳定规律：Review 后吸收到 foundation/kernel，原插件退役；
- 增益消失或负担超过收益：退役，而不是因历史投入继续保留。

<!-- semantic-anchor: composition -->
## 6. 组合能力，但不形成插件堆

发现一个有用 skill 或新任务时，先问：

- 它是一个可以一句话说清、有固定完成门的重复任务，还是跨多个任务仍成立的能力？
- 现有 task-led plugin、capability-led plugin 或 foundation owner 是否已经提供了所需结果？
- 它能否成为现有任务的一步、现有能力的可选联动或改造，而不新增插件？
- 它是否真的需要独立路由、生命周期或证据边界？
- 多个 skill 是否应当组合成一个能力，而不是各装一个？
- 它只是现有 capability 的新 task projection，还是确实出现了新的可复用能力？
- 重复使用是否已经说明它应当被 OS 吸收？

目标是以尽可能少的任务插件和能力插件获得最清楚的 owner。任务主导插件不因流程复杂而升级成能力；能力主导插件也不拆成一堆单任务包。组合依赖必须机器可读；插件仍不得直接读取另一个插件的私有状态。

<!-- semantic-anchor: distribution_parity -->
## 7. 报告中的原型与可下载版本

同一 `id@version` 不能在报告中的原型和可下载版本悄悄表达不同含义。`exact` 指 JSON 解析后的语义对象一致；`scoped_variant` 必须声明 private/public 两侧，并逐项列出允许变化的字段；其他差异一律验证失败。`private_only` 不得进入可下载版本的 manifest，其 runtime source 也不得保留私有 capability ID 的休眠实现。静态门禁检查的是能力语义边界，不等于声称发现了私人数据泄露。

Scoped variant 在共享身份、API、bindings 与失败边界一致时，可以采用独立 minor version。跨仓验证可在已审阅合同中登记额外字段差异；每个字段必须有理由及两侧精确值的 digest。值变化使该审阅失效，不产生新 effect 授权；运行时和隐私门仍必须独立通过。

<!-- semantic-anchor: required_gates -->
## 8. 必须通过的门禁

```bash
python3 scripts/validate_plugin_standard.py
python3 scripts/validate_plugins.py
python3 scripts/validate_task_extensions.py
python3 -m unittest evals.test_plugin_governance
```

双仓发布时再加入 `--public-root <公开仓库>`。门禁同时检查 archetype 分支、task contract 或 capability binding、来源台账、外部衍生一致性、重复 owner、类型化 handoff、action-effect、人工准入回执、manifest parity 和可下载版本 runtime source 中的私有符号。只有本地行为、负向测试、回滚/卸载与这些边界全部通过，插件才达到可发布状态。

<!-- semantic-anchor: open_questions -->
## Open questions

- 当前 capability 的裸模型/无插件宿主比较仍为 `planned`；在获得真实纵向证据前，不得把 `locally_validated` 解释为已经证明研究增益。
- 当前哪些 bundled capability 实际已经是 foundation invariant，哪些反而应该变成 optional，仍需由比较证据决定。
