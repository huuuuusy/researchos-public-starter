---
title: Research Assets 插件
sensitivity: public_safe
status: active
---

<p align="right"><a href="README.md">English</a> | <strong>中文</strong></p>

# Research Assets

## 用途

把来源概览、资产图、预览和有界的来源导航投影到共享的 ResearchOS 界面。

## 使用与非目标

用于查找和查看已登记的研究资产。它不推断来源权威、不读取任意路径，也不把预览当作 canonical 事实。

## 可用性与一致性

通用 foundation projection，私有版与 Public Starter 的 manifest 完全一致。每个运行时只投影自己允许的数据。

## 依赖

需要 `researchos_core`；provider 数据必须满足 projection envelope 和运行时读取策略。

## 生命周期

内嵌基础能力，通过 ResearchOS release 维护。

## 数据、权限与导出

声明式、local-only，没有网络、命令或 canonical-write 权限。投影导出限于各 manifest 的精确字段映射。

## 验证

运行 manifest 列出的插件与投影测试，再运行 plugin-standard gate。

## 故障恢复

未知 schema、敏感度拒绝、缺少必需字段或 stale provider 数据必须返回 empty/error envelope，而不是 raw fallback 数据。

## 价值与替代

它提供一个受治理的导航界面。直接浏览文件系统仍是由用户明确控制的后备方式。

## 退役

只有另一项基础能力保留 fail-closed 投影、预览 provenance 和公开 parity 时才退役。

## 过程与实现

本功能的数学伪代码、控制流程与实现边界见下文。资产图构建器、资产客户端和组合候选路由提供投影及明确的组合提示；尚未实现通用完备的有类型图抽取器与科学兼容性检查器。

数学符号是插件简写，定义见[插件目录首页](../README.zh.md)。插件体系处于冻结状态，见[治理指南](../../governance-guide.zh.md#任务扩展与插件)。

| 插件、形态与部署 | 核心算子或约束 | 含义、定义与核查 |
| --- | --- | --- |
| 资产导航与组合 (`research_assets`); $\mathsf P_i^{\mathrm{cap}}$, 基础 | $y_t=\mathcal G_t^a[W_t]$; $\mathcal G_t^{+}=\mathcal G_t$ | 图导航中，$\mathcal G_t^a$ 保留获准字段与关系，$W_t$ 选择其中的节点；诱导子图保留这些节点之间的关系。组合与解散另行产生待审阅的 $\Delta_t$。 |

### 资产导航与组合

获准图 $\mathcal G_t^a$ 与选择集合 $W_t$；输出：视图或另行核查的组合候选。

```pseudocode
解析选定身份与版本，移除不可访问字段
令 $y_t\leftarrow\mathcal G_t^a[W_t]$；保留边类型、根据与状态
若操作为导航：返回 $y_t$，并保持 $\mathcal G_t^{+}=\mathcal G_t$
// 视图中的成员关系和邻近位置不构成科学支持
若操作为组合或解散：
    将 $r,m,\kappa$ 绑定到选定版本
    核查角色与需保留的关系
    将 $\Delta_t$ 与视图分开返回
```

**算法解释。** 两条分支对应不同后果：导航返回已有图的获准视图，组合或解散返回需要核查的变化候选。共享选定对象，并不意味着共享修改权限，更不意味着视觉关系已经成为科学支持。
