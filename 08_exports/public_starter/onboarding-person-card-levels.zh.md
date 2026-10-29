---
type: card_level_example
title: "个人卡片等级示例"
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
  <a href="onboarding-person-card-levels.md">English</a> | <strong>中文</strong>
</p>

# 个人卡片等级示例

这个示例展示一个虚构用户画像卡片如何从接入种子，升级成可执行身份卡片。

## 一级：种子个人卡片

```yaml
card_type: person
maturity: 1
name: Sue 博士
status: candidate
source_materials:
  - onboarding-intake-note-example.zh.md
known:
  - 虚构研究者，研究人类确认的 AI 研究工作流。
  - 用户提供了公开主页和论文主页。
missing:
  - 尚未检查简历证据。
  - 尚未链接代表论文。
  - 公开导出排除项仍需确认。
do_not_infer:
  - 机构、雇佣关系、合作者或指导关系。
next_confirmation_question: 哪份公开简历或简历摘要应作为来源记录？
```

## 二级：有来源个人卡片

```yaml
card_type: person
maturity: 2
name: Sue 博士
status: sourced
public_anchors:
  homepage: https://example.org/sue
  publication_profile: https://scholar.example.org/sue
  cv_summary: materials/sue-public-cv-summary.md
research_themes:
  - AI 辅助研究工作流中的人类确认。
  - 有证据边界的记忆系统。
  - 公开安全知识导出。
linked_cards:
  - onboarding-paper-card-levels.zh.md#一级种子论文卡片
  - onboarding-talk-card-levels.zh.md#一级种子报告卡片
evidence_boundary: 只使用用户提供的公开主页、论文主页和简历摘要。
next_action: 阅读第一篇代表论文，并把它连接到个人画像。
```

## 三级：可执行个人卡片

```yaml
card_type: person
maturity: 3
name: Sue 博士
status: operational
public_positioning: 虚构研究者，构建带有明确证据边界的人类确认式 AI 研究工作流。
confirmed_themes:
  - 人类确认的 AI 协助。
  - 研究记忆和卡片成熟度。
  - 公开安全导出治理。
representative_outputs:
  - Calibrated Memory Workflows for Human-AI Research Notes.
  - From Notes to Confirmed Research Memory.
linked_cards:
  papers:
    - onboarding-paper-card-levels.zh.md#三级可执行论文卡片
  talks:
    - onboarding-talk-card-levels.zh.md#三级可执行报告卡片
  collaborators:
    - onboarding-collaborator-card-levels.zh.md#二级有来源合作者卡片
  plans:
    - onboarding-plan-card-levels.zh.md#二级有范围计划卡片
export_boundary:
  allow:
    - 公开画像摘要
    - 公开论文和报告链接
    - 虚构合作者示例
  exclude:
    - 私人笔记
    - 学生或评审材料
    - 本地运行日志
update_trigger: 新增已确认论文、报告或计划结果后更新。
```

## Agent Summary

一个三级个人卡片示例，展示接入种子、有来源画像和可执行身份状态。
