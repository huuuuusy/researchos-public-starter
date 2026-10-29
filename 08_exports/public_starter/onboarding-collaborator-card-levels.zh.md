---
type: card_level_example
title: "合作者卡片等级示例"
status: reference
relationship_maturity: R2_evidence_linked
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
  <a href="onboarding-collaborator-card-levels.md">English</a> | <strong>中文</strong>
</p>

# 合作者卡片等级示例

这个示例展示如何从论文作者列表中提出合作者卡片。它刻意保持谨慎。

## 一级：候选合作者卡片

```yaml
card_type: person
subtype: collaborator_candidate
maturity: 1
name: 合作者 A
status: candidate
source_materials:
  - onboarding-paper-card-levels.zh.md#二级有来源论文卡片
evidence:
  - 出现在一篇虚构公开论文的作者列表中。
allowed_claims:
  - 候选共同作者关系。
not_allowed_claims:
  - 私人关系。
  - 指导关系。
  - 当前合作状态。
  - 未来承诺。
next_confirmation_question: 是否应该把这位共同作者升级为你 ResearchOS 中的已确认合作者卡片？
```

## 二级：有来源合作者卡片

```yaml
card_type: person
subtype: collaborator
maturity: 2
name: 合作者 A
status: sourced
public_anchor: https://example.org/collaborator-a
evidence:
  - Calibrated Memory Workflows for Human-AI Research Notes 的共同作者。
  - 公开主页显示其宽泛方向是研究系统和评估。
confirmed_claims:
  - 一篇虚构论文的公开共同作者。
  - 和论文卡片、计划卡片相关。
evidence_boundary: 只基于公开共同署名和公开主页。
next_action: 询问用户未来联系或项目计划是否应包含这位合作者。
```

## 三级：可执行合作者卡片

```yaml
card_type: person
subtype: collaborator
maturity: 3
name: 合作者 A
status: operational
public_anchor: https://example.org/collaborator-a
confirmed_scope:
  - 一篇虚构论文上的公开共同作者关系。
  - 可以作为公开安全工作流示例的潜在反馈者。
linked_cards:
  paper: onboarding-paper-card-levels.zh.md#三级可执行论文卡片
  plan: onboarding-plan-card-levels.zh.md#三级可执行计划卡片
safe_contact_context:
  - 只使用公开项目表述。
  - 不包含敏感笔记、学生信息或未公开论文细节。
next_action: 只有在用户确认后，才起草公开安全的合作跟进。
update_trigger: 新增已确认论文、会议记录或用户明确修正后更新。
```

## Agent Summary

一个谨慎的合作者卡片示例，展示如何从作者列表抽取候选关系、建立有来源公开关系，并形成边界明确的可执行合作上下文。
