---
type: card_level_example
title: "报告卡片等级示例"
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
  <a href="onboarding-talk-card-levels.md">English</a> | <strong>中文</strong>
</p>

# 报告卡片等级示例

这个示例从用户登记一个公开报告页面、幻灯片、本地路径线索或摘要之后开始。

## 一级：种子报告卡片

```yaml
card_type: talk
maturity: 1
title: From Notes to Confirmed Research Memory
status: candidate
source_materials:
  - onboarding-intake-note-example.zh.md
known:
  - 用户把它标记为第一个代表报告。
  - 它似乎把论文转成了工作流叙事。
missing:
  - 尚未检查幻灯片。
  - 听众和日期需要确认。
  - 可复用报告主张尚未确认。
next_action: 验证报告日期、听众和公开来源。
```

## 二级：有来源报告卡片

```yaml
card_type: talk
maturity: 2
title: From Notes to Confirmed Research Memory
status: sourced
date: 2026-04-18
audience: 虚构研究生研究方法研讨课
public_source: https://example.org/talks/confirmed-research-memory
linked_paper: onboarding-paper-card-levels.zh.md#二级有来源论文卡片
key_message: 研究笔记应经过证据、候选解释、确认和导出检查。
reusable_sections:
  - 为什么原始笔记不是已确认记忆。
  - 一级卡片应包含什么。
  - 仪表盘如何帮助复查，但不成为判断权来源。
evidence_boundary: 基于公开报告页面和用户提供摘要；尚未审计逐字稿。
next_action: 询问这个报告是否可以作为工作流的第一份公开解释。
```

## 三级：可执行报告卡片

```yaml
card_type: talk
maturity: 3
title: From Notes to Confirmed Research Memory
status: operational
public_source: https://example.org/talks/confirmed-research-memory
confirmed_use:
  - ResearchOS 卡片工作流的入门公开解释。
  - 把论文转成用户可理解系统卡片的教学示例。
  - 第一份公开项目介绍的来源。
linked_cards:
  person: onboarding-person-card-levels.zh.md#三级可执行个人卡片
  paper: onboarding-paper-card-levels.zh.md#三级可执行论文卡片
  plan: onboarding-plan-card-levels.zh.md#二级有范围计划卡片
export_ready_assets:
  - 公开报告摘要
  - 三页幻灯片大纲
  - 可复用卡片成熟度说明
update_trigger: 新增录像、听众反馈或幻灯片更新后修订。
```

## Agent Summary

一个三级报告卡片示例，展示公开报告如何成为有来源的传播材料，并进一步变成可执行解释界面。
