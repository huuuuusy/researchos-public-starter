---
title: 跨域科研入域插件
sensitivity: public_safe
status: active
---

<p align="right"><a href="README.md">English</a> | <strong>中文</strong></p>

# 跨域科研入域

## 用途

把进入陌生科学领域组织为一个有边界的 case，分别检验搜索、领域准入、人的学习、系统保持和领域结果主张。

## 使用与非目标

当一个具体的本地问题必须按另一领域的标准检验时使用。它不转移私有专业性、不替代领域专家，也不只凭类比主张能力。

## 可用性与一致性

私有 ResearchOS、Public Starter 和 personal vault 中都有可选的 scoped variants。工作流共享，只有可选的私有 handoff 不同。

## 依赖

需要 `researchos_core`、案例工作流/模板，以及一条指名的领域准入路线。audit/reflection 交接在私有使用中是可选的。

## 生命周期

用 `python3 scripts/manage_plugins.py install cross_domain_scientific_entry` 安装；对应的 `disable`、`enable` 或 `uninstall` 动作可以撤回。

## 数据、权限与导出

安装只在本地复制一份已审阅的 manifest，不运行远程代码，也不写长期记忆。来源仍归用户所有；输出在 Review 前都是候选，公开主张需要另行批准。

## 验证

运行 `python3 scripts/validate_task_extensions.py`、manifest proof 测试和 `python3 scripts/validate_plugin_standard.py`。它的跨仓 parity 模式（`--public-root`）只能在私有仓库中运行。

## 故障恢复

问题状态、证据义务或专家准入不可得时，缩小或暂停案例并报告缺口，不强行给出结果。

## 价值与替代

好处是双向压力测试和明确的准入。不评估迁移与保持时，普通文献综述是更简单的替代。

## 退役

当工作流无法再区分搜索、准入、学习、保持和领域结果证据时退役。

## 过程与实现

本功能的数学伪代码、控制流程与实现边界见下文。可选描述符、工作流和案例包模板提供结构化宿主方法。受影响范围与持续未决集的更新属于数学规格，尚无完整自动入域调度器。

数学符号是插件简写，定义见[插件目录首页](../README.zh.md)。插件体系处于冻结状态，见[治理指南](../../governance-guide.zh.md#任务扩展与插件)。

| 插件、形态与部署 | 核心算子或约束 | 含义、定义与核查 |
| --- | --- | --- |
| 跨域科研入域 (`cross_domain_scientific_entry`); $\mathsf P_i^{\mathrm{cap}}$, 可选 | $\mathcal U_{t+1}=(\mathcal U_t\cup\mathcal F_t)\setminus(\mathcal Z_t^{\mathrm{res}}\cup\mathcal Z_t^{\mathrm{cancel}})$ | 在一个冻结案例内持续携带未决义务，加入受影响要求，仅移除已核查解决或获准取消的项。领域准入、学习与方法保持仍为不同要求。 |

### 跨域科研入域

冻结案例、领域来源、要求与预算；输出：候选方案、准入发现及持续保留的未决要求。

```pseudocode
固定研究现象、领域问题、证据要求与停止预算
依据获准证据构造最小领域图与候选方法
在停止预算内，对每次新观察：
    推导 $\mathcal F_t$，对照当前版本核查未决要求
    仅由合格解决回执形成 $\mathcal Z_t^{\mathrm{res}}$
    仅由授权取消形成 $\mathcal Z_t^{\mathrm{cancel}}$
    令 $\mathcal U_{t+1}\leftarrow(\mathcal U_t\cup\mathcal F_t)\setminus(\mathcal Z_t^{\mathrm{res}}\cup\mathcal Z_t^{\mathrm{cancel}})$
// 预算终止不等于要求解决；三类积累也不能相互替代
收尾时分别报告领域发现、人的学习与保留方法
```

**算法解释。** 新观察可以把要求加入未决集，移出则需要更强的根据：合格解决回执或授权取消。停止预算只终止本次处理，尚未解决的要求仍被保留；收尾分别说明领域结果、人的学习与方法积累。
