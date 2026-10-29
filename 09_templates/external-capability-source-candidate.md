---
title: External Capability Source Candidate
layer: template
status: active
sensitivity: public_safe
owner: researchos_core
last_reviewed: 2026-08-14
---

# External Capability Source Candidate / 外部能力来源候选

Use this card before creating or installing a plugin. One card may contain several source skills when the likely result is one composed capability.

在创建或安装插件之前使用这张卡。如果多个来源更适合合成为一个能力，应当放在同一张卡中，而不是分别安装。

## Candidate boundary / 候选边界

- Candidate id / 候选 ID:
- User problem / 要解决的真实问题:
- Existing ResearchOS owner or overlapping capability / 现有 owner 或重叠能力:
- Why a link or existing integration is insufficient / 为什么仅链接或既有联动仍不够:
- Decision deadline and evaluation budget / 决策期限与评估预算:

## Source links / 来源链接

Repeat for each source. Do not copy source instructions or code into this card.

每个来源重复填写；不要把原始 instructions 或代码复制进本卡。

- Kind / 类型: `skill | repository | paper | workflow`
- Name / 名称:
- HTTPS URL / 链接:
- Version or retrieval boundary / 版本或检索边界:
- License / 许可:
- Reuse mode / 复用方式: `reference_only | adapted | composed`
- Useful invariant / 真正有用的稳定部分:
- Parts that must not be inherited / 不应继承的部分:

## Transformation hypothesis / 改造假设

- ResearchOS authority and Review boundary / authority 与 Review 边界:
- Proposed capability owner / 拟归属 owner:
- Proposed placement / 拟放置位置: `reference_only | adapted_plugin | composed_plugin | foundation_capability | stable_kernel`
- External runtime dependency after adaptation / 改造后的外部运行依赖: `none | optional | runtime_required`
- What becomes different from upstream / 与上游相比具体改了什么:
- How multiple sources interact / 多来源如何组合:

## Smallest test / 最小测试

- One real use case / 一个真实案例:
- Baseline without adaptation / 未改造基线:
- Expected capability gain / 预期能力增益:
- Authority, privacy, license, and failure risks / authority、隐私、许可与失败风险:
- Behavior test and rollback / 行为测试与回滚:
- Human admission signal / 人工准入信号:

## Decision / 决策

- Status / 状态: `linked | assessed | piloted | adopted | rejected | superseded`
- Decision / 处理: `keep_reference | adapt_plugin | compose_plugin | absorb_foundation | propose_kernel_change | reject`
- Evidence and counterevidence / 支持与反证:
- Destination owner / 最终 owner:
- If adopted, manifest `contract_id` / 若采用，对应 manifest:
- Stop or revisit rule / 停止或重开规则:
