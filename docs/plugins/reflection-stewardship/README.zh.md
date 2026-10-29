---
title: Reflection Stewardship 插件
sensitivity: public_safe
status: instrumented
---

<p align="right"><a href="README.md">English</a> | <strong>中文</strong></p>

# Reflection Stewardship

## 用途

把一个明确提供的 episode 转成因果教训、可证伪 gate 和一个候选 owner。

## 使用与非目标

在完成、失败、中断或被更正的 episode 之后，用户想要因果教训、改动后的规则或可执行 gate 时使用。普通项目、事实、决定或状态写回仍走 Core `writeback / Review`；单独出现“沉淀”并不会把请求变成反思。本能力不创建并行记忆，也不准入规则。

## 可用性与一致性

这是经审阅的 scoped variant 的公开侧。它与私有侧共享 capability identity、版本、因果/non-goal 语义与 Review 边界，但只接受用户显式提供的 episode receipt，并且只返回可复制或进入 Review 的候选。它不接收私有 episode 证据、长期判断、路径、runtime state 或 canonical-write 权限。

## 依赖

需要声明式核心，持久候选只送入 Review。私有 audit 或 alignment 集成不是公开版的依赖。

## 生命周期

随版本提供并默认开启；禁用后仍可做普通的任务后复盘。更新必须保持 scoped-variant allowlist，并通过跨仓 parity 校验。

## 数据、权限与导出

无 network、command、state 或 canonical-write 权限。公开版的 `writeback` 结果只是可复制或 Review 候选，不证明个人 vault 已经改变。

## 验证

运行 `python3 scripts/validate_plugins.py` 和公开能力对齐测试。

## 故障恢复

无法把原因与时间线分开时，只报告不确定性，不提出持久规则。如果请求只是记录内容，就退回普通写回路径，不补造因果链。

## 价值与替代

只有有界反思能产出可复用 gate、又不累积产物时才保留。

## 退役

有用不变量被稳定 owner 吸收后退役。

## 过程与实现

本功能的数学伪代码、控制流程与实现边界见下文。反思方法与合同检查已经存在。它提出因果性经验，不从单次经历估计因果效应，也不自主写入配置。

数学符号是插件简写，定义见[插件目录首页](../README.zh.md)。插件体系处于冻结状态，见[治理指南](../../governance-guide.zh.md#任务扩展与插件)。

| 插件、形态与部署 | 核心算子或约束 | 含义、定义与核查 |
| --- | --- | --- |
| 经历反思 (`reflection_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, 随附 | $\widetilde\omega_t^u=\omega_t^u[r\mapsto r^{\prime}]$ | 方括号表示只替换方法配置中的一项规则条目，保留其他条目。结果是依据具体经历和反例提出、附有检查的候选配置；是否保留另经准入。 |

### 基于经历的方法修订

有界经历与当前 $\omega_t^u$；输出：带因果依据和检查的候选规则修改。

```pseudocode
恢复预期动作、观察结果与证据范围
提出可能原因和错过的信号，检查竞争性解释或反例
若没有值得保留的新因果教训：返回不修改规则
若证据不足：仅保留与用途有关的未决问题，返回不修改规则
// 将原因解释转为可检验候选，而非直接改写配置
构造带可执行门禁和唯一责任主体的 $r^{\prime}$
令 $\widetilde\omega_t^u\leftarrow\omega_t^u[r\mapsto r^{\prime}]$
通过既有配置准入路径返回候选与检验
```

**算法解释。** 反思的产物是可检验的方法候选。竞争性解释用于判断这次经历是否足以支持规则修改，门禁、责任主体与检验则把因果猜测转为可以审阅和尝试的改进。
