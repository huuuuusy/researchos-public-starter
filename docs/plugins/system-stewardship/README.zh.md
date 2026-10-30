---
title: System Stewardship 插件
sensitivity: public_safe
status: active
---

<p align="right"><a href="README.md">English</a> | <strong>中文</strong></p>

# System Stewardship

## 用途

负责受治理的系统进化审阅、维护状态、验证入口和可回滚的改动提议。

## 使用与非目标

用于架构、维护或治理改动。它不批准自己的改动、不绕过 Review，也不把诊断变成 canonical 决定。

## 可用性与一致性

本仓库与报告中的原型各自随附 scoped variants，共享同一 capability 合同，差异受 allowed-divergence-fields 约束。本仓库使用公开安全来源，不含私有 audit/reflection 权限。

## 依赖

需要 `researchos_core`；私有 audit/reflection 集成是可选的，本仓库不包含。

## 生命周期

随版本提供并默认开启。更新必须保持 scoped-variant allowlist，并通过跨仓 parity 检查。

## 数据、权限与导出

声明式，没有网络或直接 canonical-write 权限。运行时投影 local-only；公开输出另走 safe-release gate。

## 验证

运行 manifest 中的命令与测试和 `python3 scripts/validate_plugin_standard.py`；双仓修改时加 `--public-root <public-repo>`。

## 故障恢复

校验失败时保持旧 release 生效，保留候选 diff，并在重建投影前走声明的 rollback 路径。

## 价值与替代

它让系统改动可观察、可回滚。临时维护是替代方式，但缺少一个明确的权限与回滚边界。

## 退役

只有另一个已准入 owner 在两个仓库版本中同时承担系统进化、release validation 与 rollback 时才退役。

## 过程与实现

本功能的数学伪代码、控制流程与实现边界见下文。已登记维护动作与共用准入模块提供有界执行。插件本地生命周期测试覆盖版本／定制保护及恢复，不保证跨文件崩溃原子性或自主科学改进。

数学符号是插件简写，定义见[插件目录首页](../README.zh.md)。插件体系处于冻结状态，见[治理指南](../../governance-guide.zh.md#任务扩展与插件)。

| 插件、形态与部署 | 核心算子或约束 | 含义、定义与核查 |
| --- | --- | --- |
| 系统演化 (`system_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, 随附 | $\omega_{t+1}^u=\operatorname{Revise}_{\mathrm{adm}}(\omega_t^u,e_t^a,d_t)$ | 用既有准入算子处理配置变化，依据证据与研究者决定。候选须带试验及回滚依据；已观察到的改动与失败仍由执行回执保留。 |

### 配置演化

带版本的配置候选、试验依据与范围内决定 $d_t$；输出：实际效果与保留状态。

```pseudocode
将候选绑定到当前配置版本、预期改进与回滚依据
核查获准试验范围与候选前提
若仍有未决条件：返回缺失条件
通过宿主运行有界试验，将实际效果、失败核查与恢复需要记录于 $\rho_t$
// 试验成功不自动授权保留；保留时须重查同一候选与版本
在保留时复核版本与同一候选，评价准入条件
若准入条件成立：应用 $\operatorname{Revise}_{\mathrm{adm}}$
否则：保留失败或部分状态，仅进行获准恢复
```

**算法解释。** 试验回答候选在限定条件下产生了什么效果，准入回答是否保留这项变化。保留时重查同一候选与版本，避免把对旧候选的成功观察转用于已改变的提案。
