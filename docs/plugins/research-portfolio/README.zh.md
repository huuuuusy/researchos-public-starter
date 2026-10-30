---
title: Research Portfolio 插件
sensitivity: public_safe
status: active
---

<p align="right"><a href="README.md">English</a> | <strong>中文</strong></p>

# Research Portfolio

## 用途

把已登记的研究责任和 attention state 投影到`现在`（Now），自身不成为计数权威。

## 使用与非目标

用于浏览已登记的 lead、support、waiting、queued、paused 和 attention 状态。它不从最近活动或生成数据推断责任。

## 可用性与一致性

通用 foundation projection，本仓库与报告中的原型的 manifest 完全一致。私有数据与 demo 数据保持分离。

## 依赖

需要 `researchos_core`，以及满足共享 envelope 的运行时 portfolio 投影。

## 生命周期

内嵌基础能力，通过 release 维护。

## 数据、权限与导出

声明式、local-only，没有网络、命令或 canonical-write 权限。生成数据和 Dashboard 状态只是投影，不是 canonical 权威。

## 验证

运行 manifest 行为测试和 `python3 scripts/query_research_agenda.py`（报告 portfolio 覆盖情况），再运行 plugin-standard 校验器。

## 故障恢复

覆盖过期或责任字段无效时，报告 registered count，并保留 `unclassified` 与重叠的 attention 状态。

## 价值与替代

它提供一致的责任导航。直接读取 canonical portfolio 文件仍是权威后备。

## 退役

只有另一个 foundation owner 保留计数权威、coverage receipt 和公开/demo 分离时才退役。

## 过程与实现

本功能的数学伪代码、控制流程与实现边界见下文。项目行动合同和既有工作会话路由区分这些效果。可行集符号规定选择边界；按前提与依赖构造 $\mathcal A_{i,t}$ 的完整科研组合调度尚未实现（报告第 4.5 节），报告也不提供最优调度器；Public 行动仍为预览或仅复制的交接。

数学符号是插件简写，定义见[插件目录首页](../README.zh.md)。插件体系处于冻结状态，见[治理指南](../../governance-guide.zh.md#任务扩展与插件)。

| 插件、形态与部署 | 核心算子或约束 | 含义、定义与核查 |
| --- | --- | --- |
| 项目组合与注意力 (`research_portfolio`); $\mathsf P_i^{\mathrm{cap}}$, 基础 | $a_t=(r,m)\in\mathcal A_{i,t}$ | 选用该插件时，$\mathcal A_{i,t}$ 是当前输入、前提、权限与资源约束允许启动的应用集合。从中选择项目下一动作；集合成员条件尚不规定最优排序。 |

### 项目注意与下一行动

选定工作项、当前依赖与范围内权限；输出：可行应用或明确的未满足条件。

```pseudocode
恢复工作项、责任、依赖与请求效果
枚举已登记应用 $(r,m)$
// 可行性先于偏好：排除过期、越权或前提未知的修改
筛除不合条件的修改
在声明资源限制下构造 $\mathcal A_{i,t}$
若 $\mathcal A_{i,t}$ 为空：返回阻碍条件
按明确的用户选择或策略选取 $a_t\in\mathcal A_{i,t}$，并记录根据
通过宿主派发工件、有界注意状态或生命周期候选
将实际效果保留在 $\rho_t$ 中
```

**算法解释。** 选择偏好的行动之前，先确定哪些行动在当前责任、依赖与资源下确实可行。空集合说明需要解除阻碍；选中行动之后仍要观察宿主实际产生的效果。
