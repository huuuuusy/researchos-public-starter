---
title: Material Pipeline 插件
sensitivity: public_safe
status: active
---

<p align="right"><a href="README.md">English</a> | <strong>中文</strong></p>

# Material Pipeline

## 用途

把材料线索整理成用于 intake、upgrade、scout 和 Review 的有界候选，不绕过来源权威。

## 使用与非目标

在添加或升级研究材料时使用。它不认证来源质量、不直接创建 canonical memory，也不发布 intake 记录。

## 可用性与一致性

通用 foundation projection，私有版与 Public Starter 的 manifest 完全一致。运行时数据不同：每个安装只提供自己的本地来源。

## 依赖

需要 `researchos_core`；research-asset 导航是可选的。

## 生命周期

内嵌基础能力，随 ResearchOS release 变化，不由可选插件管理器安装或移除。

## 数据、权限与导出

只做声明，没有网络、命令或 canonical-write 权限。本地候选数据留在本地；只有单独审阅过的安全导出才能离开运行时。

## 验证

运行 `config/plugins/material-pipeline.json` 中的校验命令与行为测试，以及 plugin-standard gate。

## 故障恢复

来源缺失或含糊时，把条目保留为 lead 并记录缺口，不自动扩大读取；等用户提供最小的权威来源后重试。

## 价值与替代

好处是一条可见的“候选到 Review”边界。直接手工录入文件仍然可行，但权威与一致性风险更大。

## 退役

只有另一个 foundation owner 保留双语 intake、候选权威、公开安全与恢复行为时才退役。

## 过程与实现

本功能的数学伪代码、控制流程与实现边界见下文。材料管线声明和客户端候选权限模块实现引入路由与候选边界。来源解释仍是方法步骤；现有成熟度投影使用启发式规则（技术报告附录 B.3，差距 35）。

数学符号是插件简写，定义见[插件目录首页](../README.zh.md)。插件体系处于冻结状态，见[治理指南](../../governance-guide.zh.md#任务扩展与插件)。

| 插件、形态与部署 | 核心算子或约束 | 含义、定义与核查 |
| --- | --- | --- |
| 材料接入 (`material_pipeline`); $\mathsf P_i^{\mathrm{cap}}$, 基础 | $\forall v\in V(\Delta_t):\ \sigma_t(v)\ne\varnothing$ | $V(\Delta_t)$ 是接入候选涉及的材料对象，$\sigma_t(v)$ 记录其来源引用与版本。逐对象核对可追溯来源；登记本身不确立内容理解。 |

### 材料引入

选定来源及其版本、$q_t$ 与 $\kappa$；输出：有来源依据的材料候选与未决来源问题。

```pseudocode
对每项选定来源：
    绑定获准位置与来源版本
    若无法定位：返回来源缺失问题
// 定位成功后才构造候选；来源陈述与解释分别保留
构造 $\Delta_t$
对每个 $v\in V(\Delta_t)$：
    保留 $\sigma_t(v)$，区分来源陈述与解释
核查来源支持与复用条件；将不确定属性保留为未决
// 成熟度按报告附录 B.3（差距 35）单独评价
通过宿主返回候选及核查结果
```

**算法解释。** 可追溯的候选必须同时说明内容来自哪里，以及哪些部分属于解释。定位失败时停止构造该来源的内容，证据不足时保留未决属性；材料是否成熟则由独立评价决定。
