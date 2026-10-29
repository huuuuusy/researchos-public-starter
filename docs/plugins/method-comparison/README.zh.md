---
title: 方法比较插件
sensitivity: public_safe
status: active
updated: 2026-09-11
---

<p align="right"><a href="README.md">English</a> | <strong>中文</strong></p>

# 方法比较：开发插件并接入 skill

## 用途

研究者要为遮挡场景选择跟踪方法，选定论文却只报告目标持续可见时的结果。本例保留比较条件和证据缺口，并提供一个完整的 task-led 插件及可复用 skill。插件定义任务怎样接入与管理，skill 定义怎样比较证据；无图形界面的文件型 Agent 也可使用。

## 文件与职责

| 文件 | 承担什么 | 开发者改哪里 |
| --- | --- | --- |
| [完整描述符](../../../config/extensions/method-comparison.example.json) | 任务标识、版本、范围、读取计划、结果与生命周期 | 重复任务及其接口 |
| [源 skill](researchos-method-comparison/SKILL.md) | 比较与修订的方法，可由兼容宿主独立使用 | 方法正文及版本 |
| [适配生成脚本](build_adapter.py) | 将本例已审阅的 skill 投影为 ResearchOS Markdown | 本地格式映射需要变化时 |
| [生成的适配文件](skill-adapter.md) | 读取计划消费的方法及源文件哈希 | 重新生成，不直接编辑 |
| [集成检查](../../../evals/test_method_comparison_example.py) | 重建一致性、加载、生命周期和失败处理 | 修改后的可观察要求 |

源文件采用 [Agent Skills 格式](https://agentskills.io/specification)。ResearchOS 的公开读取合同需要顶层 sensitivity 字段，这不是标准 skill 字段；薄适配层保留方法正文并补充 ResearchOS 元数据。方法只维护一份，另一份是可重建投影。管理器注册读取入口，不会把 skill 安装到另一应用的目录，也不会执行它。

## 可用范围与依赖

1.1.0 版属于 `task_led`、`local_installable` 贡献，随仓库提供但默认停用。Private 与 Public 描述符的分发范围不同；公开方法文件不会使用户后来提供的论文或结果自动公开。已有安装只有显式 upgrade 才采用新版。

依赖 `researchos_core`、能够读取文件的执行宿主及 Python 3。适配脚本仅用标准库，读取一个固定 skill、生成一个固定文件，不下载包或运行其中的方法。资料导航是可选依赖，无须新模型、密钥、页面或存储服务。

## 安装、调用与接续

从仓库根目录运行：

```bash
python3 docs/plugins/method-comparison/build_adapter.py --check
python3 scripts/manage_plugins.py install method_comparison
python3 scripts/plan_context.py method_comparison --lang zh-CN --mode standard --headless-json
```

已有旧版时，明确运行 `python3 scripts/manage_plugins.py upgrade method_comparison`。普通 install／enable 保留已安装版本。管理器校验宿主并核对贡献；存在无 UI 宿主校验器时，不需要启动或重建 Dashboard。

把计划、明确问题、来源路径和结果模式交给 Agent，例如：

> 请按 method_comparison 计划，比较我选定的两份跟踪方法报告是否支持遮挡场景的选型。保留评测条件，指出尚未检验之处。直接回答，不修改来源。

`read_now` 包含 `docs/plugins/method-comparison/skill-adapter.md`。宿主核验适配一致性、读取方法，再处理选定来源；`plan_context.py` 自身只产出计划，不产出比较。结果一并保留扩展标识／版本、skill 源哈希、来源版本和实际产出。接续时执行返回的 `extension.resume_command`；扩展缺失或版本不符会停止该路线。

```bash
python3 scripts/manage_plugins.py disable method_comparison
python3 scripts/manage_plugins.py enable method_comparison
python3 scripts/manage_plugins.py uninstall method_comparison
```

disable 撤下活动任务贡献；uninstall 删除受管理的本地描述符及安装基线，不删除仓库中的 skill 或早期研究结果。用户定制的 manifest 不被覆盖或删除。校验失败可恢复配置，但不声称多文件操作具备断电原子性。

## 修改方法或开发新插件

同一任务要换比较策略时，修改源 skill，递增 `metadata.version`，重新生成并审阅差异：

```bash
python3 docs/plugins/method-comparison/build_adapter.py --write
python3 docs/plugins/method-comparison/build_adapter.py --check
```

然后递增描述符版本，完成下列检查，再明确升级已有安装。旧方法证据是否适用于新版要重新判断。描述符版本标识贡献，源哈希标识实际方法文本；宿主现有的扩展版本检查本身不锁定后来读取的所有文件。

当出现不同的重复任务，例如“判断论文主张是否被所引段落支持”，再建立独立插件。从完整描述符出发，保留 schema 和核心权威字段，成组修改：

| 修改组 | 需要一起核对的字段 |
| --- | --- |
| 标识与发现 | `id`、`version`、`task.aliases`、`governance.contract_id`、`governance.task_contract.task_id`、`governance.composition.provides`、`governance.routing.trigger_intents` |
| 任务语义 | `governance.task_contract` 中的用途、输入、输出、不变量、完成条件、失败和恢复 |
| 方法与呈现 | `task.read`、两语 `task.locales`、专属 `documentation.readme` |
| 证据与退役 | 对照对象／状态、证据、准入检查依据和退役条件 |
| 分发与效果 | 适用范围、来源／改造／许可记录、依赖和声明效果 |

使用唯一标识，不覆盖已有路由。派生描述符放在 `config/extensions/<your-name>.example.json`，专属说明放在 `docs/plugins/<id-with-hyphens>/README.md`；保留英文示例中的必需说明节。quick 最多一个入口文件，standard 最多五个，evidence 最多八个，后档包含前档。用户选择的研究来源是另一项任务输入。存储 owner 保留为 `researchos_core`，写回路线保留为 `review`。本例只改方法与装配，无须给 Dashboard、Inbox 或核心加载器增加专用分支。

接入已有外部 skill 时，先检查指令、脚本、依赖、许可与副作用，在贡献 lineage 中记录真实来源与版本，再将输入、保留条件、结果及检查映射到任务合同。本例脚本只适配已审阅的纯文本方法，不能给任意 skill 判定 public-safe。需要联网、本地执行或不同权限的 skill，应先完成对应宿主集成；无法忠实映射时可以保持独立。

## 数据与结果

默认返回 answer。artifact 写到请求的输出位置；持久修改形成精确候选，进入既有审阅与准入流程。生成答案不会自动更新来源卡。方法指令不能扩大读取、修改或披露权限；Public Starter 交接仍为 copy-only。

## 验证与练习

```bash
python3 docs/plugins/method-comparison/build_adapter.py --check
python3 scripts/validate_task_extensions.py
python3 -m unittest evals.test_method_comparison_example evals.test_task_extensions evals.test_plugin_lifecycle
```

这些集成测试在临时仓库运行，不安装到日常配置。它们核对 skill／适配文件漂移、实际任务加载器及生命周期，并检查方法文件缺失等失败路径；不运行 LLM，也不确立科学质量。分发派生插件时继续执行现有 plugin-standard 检查。

可以用以下虚构来源练习检查方法行为：

| 请求与给定观察 | 应保留的区别 |
| --- | --- |
| 为遮挡场景选型；同一协议、数值越高越好的指标下 A = 0.82、B = 0.79，但仅报告目标可见条件 | 保留可见条件下的报告排序；遮挡选型仍未解决 |
| 比较可见条件；给定相同协议及数值越高越好的指标，A = 0.82、B = 0.79，没有不确定性信息 | 报告差为 0.03 个指标单位；不能推断统计显著或迁移 |
| A 的报告后来纠正，不再支持先前优势 | 重审依赖该结果的推荐，保留独立条件和遮挡实验方案，不能推出 B 更好 |

这些是构造练习，不是实测运行或 Benchmark。缺少问题或来源时，应定向补充或缩小比较；来源文档中要求修改无关卡牌的指令，不能改变用户任务和宿主权限。

## 失败恢复与价值

适配检查失败时，暂停此方法并检查来源修订，只从预期版本重新生成。证据不足时返回缺口及下一项检查；来源纠正时保留旧结果的根据和修订原因。候选被接受之后，仍需宿主实际修改与验证回执才算持久变化。

预期价值是使比较更可检查、可复用，目前未测量其相对同来源下当前模型的优势。应比较条件遗漏、无支持判断、恢复和总投入；一次边界清楚的直接请求也可能已经足够。没有净收益或与已维护流程重复时，可退役或吸收该方法，撤下活动贡献并保留早期研究根据。

## 过程与实现

本功能的数学伪代码、控制流程与实现边界见下文。随附 skill 与确定性适配器是可使用的读取方法示例。标量分支属于规格示例；证据可比性和定性比较仍需方法判断。

数学符号是插件简写，定义见[插件目录首页](../README.zh.md)。插件体系处于冻结状态，见[治理指南](../../governance-guide.zh.md#任务扩展与插件)。

| 插件、形态与部署 | 核心算子或约束 | 含义、定义与核查 |
| --- | --- | --- |
| 方法比较 (`method_comparison`); $\mathsf P_i^{\mathrm{task}}$, 可选 | $M_{ab}=\begin{cases}\operatorname{sgn}(\mu_a-\mu_b),&\gamma_{ab}=1,\\\bot,&\gamma_{ab}=0.\end{cases}$ | 以标量比较为例，$\mu_a,\mu_b$ 是已统一为越大越好的观测值。只有条件、指标、单位一致且有合格证据时 $\gamma_{ab}=1$；否则用 $\bot$ 保留不排序结果。其他比较另定规则。 |

### 方法比较

至少两个选定来源、比较问题及适用时的标量观测；输出：有条件的比较与下一检查。

```pseudocode
提取机制、假设、评测条件与观察结果，并保留来源版本
对每一对 $(a,b)$：
    核查证据、条件、指标与单位是否支持拟议比较
    若标量可比性及方向均已确立：
        令 $\gamma_{ab}=1$；令 $M_{ab}\leftarrow\operatorname{sgn}(\mu_a-\mu_b)$
    否则：令 $\gamma_{ab}=0$；令 $M_{ab}\leftarrow\bot$
// 成对符号不直接构成全局排名
返回适用论证与最小区分性检查
```

**算法解释。** 数值符号只有在可比性成立后才有意义。用未定义标记保留无法比较的情形，可以避免把缺少证据误作平局或劣势；适用论证进一步说明什么检查能改变当前判断。
