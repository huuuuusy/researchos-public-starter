---
type: workflow
title: "ResearchOS 自我进化工作流"
status: ready
created: 2026-07-10
updated: 2026-07-10
tags:
  - self-evolution
  - system-audit
  - maintenance
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <a href="self-evolution-workflow.md">English</a> | <strong>中文</strong>
</p>

# ResearchOS 自我进化工作流

## Agent Summary

这个工作流规定 ResearchOS 如何在人类确认下复查并改进自己。“自我进化”不是系统自动改写长期记忆，而是提出候选诊断：材料缺口、过期状态、难懂入口、缺失模板、薄弱 workflow 和公开边界风险，都必须经过用户判断后才能进入稳定状态。

## 诊断维度

1. 材料理解是否覆盖代表性来源。
2. 研究判断和项目结构是否有证据。
3. 人物与关系边界是否克制、可确认。
4. 外部需求是否先路由再响应。
5. 产品和文档是否让不同背景用户看得懂。
6. 安全、隐私和导出边界是否仍然有效。

## 输出格式

```text
当前版本诊断：

覆盖缺口：

机会：

优先级：
1. P0
2. P1
3. P2

候选改动：

需要用户确认：

验证计划：
```

## 可以直接做的低风险改动

- 改善说明文档；
- 增加模板；
- 补充 workflow 描述；
- 澄清公开安全示例；
- 增加校验器或 smoke checklist。

## 必须先询问用户

- 删除或移动大量材料；
- 修改身份叙事或稳定长期记忆；
- 导出 private/local-only 内容；
- 从在投、未公开或私人材料中生成公开主张。
