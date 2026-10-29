---
type: card_level_example
title: "论文卡片等级示例"
status: reference
created: 2026-06-26
updated: 2026-06-26
tags:
  - public-starter
  - onboarding-demo
  - card-maturity
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <a href="onboarding-paper-card-levels.md">English</a> | <strong>中文</strong>
</p>

# 论文卡片等级示例

这个示例从用户登记一篇代表论文来源、本地路径线索或摘要之后开始。

## 一级：种子论文卡片

```yaml
card_type: paper
maturity: 1
title: Calibrated Memory Workflows for Human-AI Research Notes
status: candidate
source_materials:
  - onboarding-intake-note-example.zh.md
authors:
  - Sue
  - 合作者 A
  - 合作者 B
known:
  - 用户说这是第一篇要读的代表论文。
  - 这篇论文和 ResearchOS 风格的已确认研究记忆工作流相关。
missing:
  - 尚未检查完整摘要。
  - 会议、期刊或公开链接需要验证。
  - 论文主张还不能复用。
do_not_infer:
  - 贡献强度。
  - 每位作者的准确角色。
  - 任何私人合作关系。
next_action: 验证公开元数据并阅读摘要。
```

## 二级：有来源论文卡片

```yaml
card_type: paper
maturity: 2
title: Calibrated Memory Workflows for Human-AI Research Notes
status: sourced
public_source: https://example.org/papers/calibrated-memory-workflows
year: 2026
authors:
  - Sue
  - 合作者 A
  - 合作者 B
summary: 一篇虚构论文，主张 AI 辅助研究记忆应区分来源材料、候选解释、人类确认和可复用主张。
contribution_candidates:
  - 把卡片成熟度定义为可审计界面。
  - 说明为什么生成笔记不能自动变成已确认记忆。
  - 提出分享前的公开安全导出检查。
collaborator_candidates:
  - name: 合作者 A
    evidence: 这篇虚构论文的共同作者
    maturity: 1
  - name: 合作者 B
    evidence: 这篇虚构论文的共同作者
    maturity: 1
evidence_boundary: 只基于元数据和摘要；尚未做全文主张审计。
next_action: 询问用户哪些主张可以安全复用到个人卡片和报告卡片。
```

## 三级：可执行论文卡片

```yaml
card_type: paper
maturity: 3
title: Calibrated Memory Workflows for Human-AI Research Notes
status: operational
public_source: https://example.org/papers/calibrated-memory-workflows
confirmed_use:
  - 支持个人卡片中“人类确认的 AI 协助”这一主题。
  - 可以作为报告卡片的技术基础。
  - 可以为公开安全启动研究计划提供种子。
reusable_claims:
  - 研究记忆系统应区分证据、解释、确认和导出。
  - 卡片成熟度应可见，避免弱笔记伪装成稳定知识。
linked_cards:
  person: onboarding-person-card-levels.zh.md#三级可执行个人卡片
  talk: onboarding-talk-card-levels.zh.md#二级有来源报告卡片
  collaborator_candidates:
    - onboarding-collaborator-card-levels.zh.md#一级候选合作者卡片
validation:
  - 已检查公开链接。
  - 已检查摘要和作者列表。
  - 可复用主张已由用户确认。
update_trigger: 全文阅读、引用更新或发表状态变化后修订。
```

## Agent Summary

一个三级论文卡片示例，展示一篇已登记论文来源如何变成元数据、合作者候选、可复用主张和 ResearchOS 关联上下文。
