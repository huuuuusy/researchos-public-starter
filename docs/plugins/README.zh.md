---
title: ResearchOS 插件文档合同
sensitivity: public_safe
status: active
---

<p align="right"><a href="README.md">English</a> | <strong>中文</strong></p>

# ResearchOS 插件 README 合同

## 数学形态与既有插件

以下使用[技术报告](../technical-report.zh.md)的数学语法解释现行[插件标准](../../05_workflows/research_management/researchos-plugin-standard-v1.2.zh.md)。下面多数记号是当前版本报告未定义的插件简写；插件的记号以本页和各插件说明为准。

现有系统已经包含任务主导与能力主导插件。其数学形态需要区分方法本身，以及使方法可被使用的实现贡献。令 $\mathsf S$ 表示带版本的 skill，$i$ 标识带版本的插件。表中 $\mathcal C_i$ 是插件声明的实现贡献集合，每项贡献可以使用 skill、工作流、代码或投影；$\mathsf{Gov}_i$ 记录身份、依赖、路由、效果、数据边界、准入与部署。这些是结构化记录，不是能力分数。对 $c\in\mathcal C_i$，skill 引用可写为 $\mathsf S\in\operatorname{methods}(c)$：多个贡献可以复用同一 skill，一项贡献也可以使用多种方法。

| 对象 | 数学形态 | 含义与既有例子 |
| --- | --- | --- |
| Skill | $\mathsf S=(\mathcal R_{\mathsf S}^{\mathrm{skill}},\eta_{\mathsf S})$ | 可复用的方法：规则，以及对其应用的控制。方法比较 skill 检查条件，并重查受影响判断。 |
| 任务主导插件 | $\mathsf P_i^{\mathrm{task}}=(\mathsf T_i,\mathcal C_i,\mathsf{Gov}_i)$ | 一个重复任务合同 $\mathsf T_i$、相应实现及治理。`method_comparison` 和 `codex_thread_handoff` 使用此形式，无须创建能力主张。 |
| 能力主导插件 | $\mathsf P_i^{\mathrm{cap}}=(\mathcal C_i,B_i,Q_i,\mathsf{Gov}_i)$ | 实现贡献经 $B_i$ 绑定已有主张 $\mathrm{Cap}_k$，$Q_i$ 将其投影为任务。`system_stewardship` 绑定 `self_evolution`，提供 `system_evolution_review` 入口。 |

skill 控制关系 $\eta_{\mathsf S}(H_t^a,L_t,e_t^a,\kappa)$ 规定允许的下一步选择：规则 $r\in\mathcal R_{\mathsf S}^{\mathrm{skill}}$ 与绑定 $m$、询问，或停止；它可以表达分支与重试，不限于固定步骤列表。选定应用仍须满足 $\operatorname{Pre}_r$，并由 $\operatorname{Check}_r$ 核查，实际产出与效果仍记为 $y_t$ 和 $\rho_t$。任务合同 $\mathsf T_i$ 规定允许的用途、输入输出要求、保留条件、完成与恢复方式；一次任务可以包含多次规则应用及多种方法。调用已有能力，本身不改变任务主导插件的组织合同。

对能力主导插件，$B_i$ 将 $\mathcal C_i$ 中每项实现贡献关联到补充说明 3 所定义的一个或多个已登记主张 $\mathrm{Cap}_k$。若 $\mathcal T_i$ 是其声明的任务集合，则 $Q_i$ 包含三元组 $(\mathsf T,c,\mathrm{Cap}_k)$，其中 $\mathsf T\in\mathcal T_i$、$c\in\mathcal C_i$。每个声明任务恰有一个这样的投影，且必须满足 $(c,\mathrm{Cap}_k)\in B_i$。这两种关系解释 `capability_bindings` 与 `task_projections`：多个任务可以调用同一能力，一项贡献也可以绑定多个主张。仅提供投影的贡献可以有 $\mathcal T_i=\varnothing$。能力主张仍保留自己的主体、条件与证据，插件或 skill 均不代替该记录。

部署是记录在 $\mathsf{Gov}_i$ 中的另一项选择。下面列出公开参考目录中的全部十二种插件：三种基础插件、六种随版本提供的插件及三种可选扩展。`config/plugins/` 中的插件 manifest 把 `product_tier` 声明为 `foundation_projection` 或 `bundled_capability`，任务扩展安装后统一归为 `optional_extension`。治理记录把它们分别记为部署方式 `embedded_foundation`、`bundled_default_on` 和 `local_installable`；只有最后一种使用本地示例安装器。目录包含未安装的示例，不能据此推断某台机器的启用状态。

下面把插件功能写成核心算子或约束。集合选择、图投影、差异、规则替换与状态递推分别表达不同作用；表中关系须在用途 $\kappa$ 及其证据条件下解释。每项插件可组织多次规则应用，不对应一个包办所有工作的函数。

表中的 $\sigma_t$、$\operatorname{assert}$ 与 $\operatorname{supp}_{\kappa}$ 需要具体来源解析或语义核查过程。把其约束写清，能够指出实现和评估应检查什么，但没有由此给出通用语义判定算法。下表同时保留可直接计算的结构运算和需要证据裁定的条件。

| 插件、形态与部署 | 核心算子或约束 | 含义、定义与核查 |
| --- | --- | --- |
| 材料接入 (`material_pipeline`); $\mathsf P_i^{\mathrm{cap}}$, 基础 | $\forall v\in V(\Delta_t):\ \sigma_t(v)\ne\varnothing$ | $V(\Delta_t)$ 是接入候选涉及的材料对象，$\sigma_t(v)$ 记录其来源引用与版本。逐对象核对可追溯来源；登记本身不确立内容理解。 |
| 资产导航与组合 (`research_assets`); $\mathsf P_i^{\mathrm{cap}}$, 基础 | $y_t=\mathcal G_t^a[W_t]$; $\mathcal G_t^{+}=\mathcal G_t$ | 图导航中，$\mathcal G_t^a$ 保留获准字段与关系，$W_t$ 选择其中的节点；诱导子图保留这些节点之间的关系。组合与解散另行产生待审阅的 $\Delta_t$。 |
| 项目组合与注意力 (`research_portfolio`); $\mathsf P_i^{\mathrm{cap}}$, 基础 | $a_t=(r,m)\in\mathcal A_{i,t}$ | 选用该插件时，$\mathcal A_{i,t}$ 是当前输入、前提、权限与资源约束允许启动的应用集合。从中选择项目下一动作；集合成员条件尚不规定最优排序。 |
| 研究上下文 (`research_context`); $\mathsf P_i^{\mathrm{cap}}$, 随附 | $Z_t=D_{\omega_t^u}(H_t^a,q_t)$; $\widehat R_t=C_{\omega_t^u}(Z_t,q_t)$ | 直接复用报告第 3.1 节的上下文选择与状态重建。结果为 $\widehat R_t$，须能恢复问题、证据、判断、未决条件和下一步。 |
| 科研表达 (`research_expression`); $\mathsf P_i^{\mathrm{cap}}$, 随附 | $\operatorname{assert}(y_t)\subseteq\operatorname{supp}_{\kappa}(E_t)$ | $\operatorname{assert}$ 取出工件作出的事实断言，$\operatorname{supp}_{\kappa}$ 表示证据在本次用途与范围下支持的断言集合。用集合包含约束表达；假设与计划仍须标明其性质。 |
| 协作对齐 (`alignment_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, 随附 | $\mathcal B_t^{\mathrm{align}}=\mathcal M_t^{\mathrm{OS}}\triangle\mathcal M_t^{u,\mathrm{stated}}$ | 两集合以共同命题标识与范围记录 OS 工作假设和用户明确表达的假设。对称差定位含遗漏在内的待澄清项，不读取人的内部状态，也不判定谁对。 |
| 研究与系统审计 (`audit_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, 随附 | $D_t^b(j)=\{\chi\in D(j):s_{\chi,t}(\rho)=b\}$; $b\in\{1,0,?\}$ | 按回执评价，将要求 $j$ 的检查集 $D(j)$ 中的各项检查分为满足、未满足和未知。未满足与未知的检查需要不同处置，修复后仍须重新核查。 |
| 经历反思 (`reflection_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, 随附 | $\widetilde\omega_t^u=\omega_t^u[r\mapsto r^{\prime}]$ | 方括号表示只替换方法配置中的一项规则条目，保留其他条目。结果是依据具体经历和反例提出、附有检查的候选配置；是否保留另经准入。 |
| 系统演化 (`system_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, 随附 | $\omega_{t+1}^u=\operatorname{Revise}_{\mathrm{adm}}(\omega_t^u,e_t^a,d_t)$ | 用既有准入算子处理配置变化，依据证据与研究者决定。候选须带试验及回滚依据；已观察到的改动与失败仍由执行回执保留。 |
| 方法比较 (`method_comparison`); $\mathsf P_i^{\mathrm{task}}$, 可选 | $M_{ab}=\begin{cases}\operatorname{sgn}(\mu_a-\mu_b),&\gamma_{ab}=1,\\\bot,&\gamma_{ab}=0.\end{cases}$ | 以标量比较为例，$\mu_a,\mu_b$ 是已统一为越大越好的观测值。只有条件、指标、单位一致且有合格证据时 $\gamma_{ab}=1$；否则用 $\bot$ 保留不排序结果。其他比较另定规则。 |
| 任务交接 (`codex_thread_handoff`); $\mathsf P_i^{\mathrm{task}}$, 可选 | $H_{t,h}^a:=H_t^a\vert_h$; $Z_t=D_{\omega_t^u}(H_{t,h}^a,q_t)$ | 先把获准历史限制到指定任务 $h$，再选择续接所需上下文。连接器与回执记录访问、脱敏和截断；受限定义域排除无关任务历史。 |
| 跨域科研入域 (`cross_domain_scientific_entry`); $\mathsf P_i^{\mathrm{cap}}$, 可选 | $\mathcal U_{t+1}=(\mathcal U_t\cup\mathcal F_t)\setminus(\mathcal Z_t^{\mathrm{res}}\cup\mathcal Z_t^{\mathrm{cancel}})$ | 在一个冻结案例内持续携带未决义务，加入受影响要求，仅移除已核查解决或获准取消的项。领域准入、学习与方法保持仍为不同要求。 |

基础投影这一放置位置不使所有贡献动作都成为纯视图，项目插件的动作也有声明的效果；补充说明 3 中纯视图的状态保持条件适用于纯视图操作。本仓库与报告中的原型可以在同一声明贡献下提供不同任务集合，因此表格描述组织形式，不意味着运行覆盖完全相同。宿主校验描述符结构与引用，目前尚不从任意 skill 文本推导或证明完整的规则和控制语义。这些数学形态提供了检查具体接入方式的共同规格。

[方法比较开发指南](method-comparison/README.zh.md)提供完整任务主导示例及 skill；原生能力主导结构见[系统维护描述符](../../config/plugins/system-stewardship.json)，可安装的能力主导结构见[跨领域科研进入描述符](../../config/extensions/cross-domain-scientific-entry.example.json)。抽象原型是规格，不是可安装包。

## README 要求

每个已检入的插件或任务扩展都必须拥有 `docs/plugins/<id-with-hyphens>/README.md`（id 中的下划线换成连字符），并由 manifest 的 `documentation.readme` 精确指向。加载器会拒绝缺失、越界、symlink 或结构不完整的文档。

README 是插件合同，不是宣传页。它必须说明：插件负责什么任务、明确不做什么、可用性与一致性、依赖、安装和退役、数据与权限、验证、失败恢复，以及相对替代方案的价值。英文 `README.md` 须逐字使用以下二级标题：`Purpose`、`Use and non-goals`、`Availability and parity`、`Dependencies`、`Lifecycle`、`Data, permissions, and export`、`Verification`、`Failure recovery`、`Value and alternatives`、`Retirement`。

foundation 与随发布附带的 capability 只通过经过审查的 ResearchOS 发布改变。`local_installable` 只通过 `scripts/manage_plugins.py` 把仓库随附且已审计的 manifest 复制到 Git 忽略目录；不下载代码、不联网、不写 canonical memory。若依赖 MCP/provider，必须按 [Thread Handoff](codex-thread-handoff/README.zh.md#可用性与一致性) 定义的就绪状态分别报告，不能把安装 manifest 等同于已经接通。

## 过程与实现

上表给出十二项功能的数学形态；各插件 README 逐项给出输入、伪代码、控制流程和实现边界。确定性宿主检查与需要解释证据的方法步骤分开。插件目录查询与运行时共用清单校验；本地生命周期使用独占临时文件进行替换与恢复。这些是有边界的实现细节，不表示已经实现自动科学判断。
