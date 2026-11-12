---
type: workflow
title: "给学生的反馈"
route: mentee_feedback
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <a href="mentee-feedback.md">English</a> | <strong>中文</strong>
</p>

# 给学生的反馈

## Agent Summary

学生或年轻同事发来一份草稿、研究计划或进展汇报，你想给出能帮对方迈出下一步的反馈时，用这个工作流。助手帮你找到主要问题和一个可行的下一步。它不给人打分，也不决定项目要不要继续。

## 读哪些卡

quick 档读你的指导风格卡 `personal_vault/03_cognition/style/mentoring.md`。如果你还没写这张卡，助手改读你的研究身份摘要 `personal_vault/00_identity/research-identity.md`。

standard 档再加 `personal_vault/00_identity/research-identity.md`、本工作流、所涉项目的方向摘要（`personal_vault/01_knowledge/capsules/<项目>.md`），以及方向摘要的表格里为反馈列出的卡，一般是项目卡和这位学生的人物卡。

evidence 档不再加卡。助手只打开这些卡的「证据边界」里写明的原件，而且只为一个说清楚的问题，例如上次会上约定的计划原话是什么。

想知道助手会读你的哪些卡，可以运行 `python3 scripts/plan_context.py mentee_feedback --vault personal_vault`。

## 步骤

1. 读完材料，先给主判断：这份工作想说明什么，现在的讲法能不能说明它。
2. 写出你理解的核心研究问题。如果和学生自己写的不一样，直接说出来。
3. 指出讲法强在哪里、弱在哪里，落到具体的页码、表格或图上。
4. 建议一个更清楚的问题，以及检验它所需的最小一步，比如补一项分析、做一小轮试访谈、加一个对照条件，先别急着要求更多工作。
5. 对照现有的时间、数据渠道和技能判断可行性，说出现实的产出是什么，比如学位论文的一章、一张海报或一篇文章。
6. 反馈写得短而直接，口吻照你的指导风格卡。

## 产出

一段你可以直接发出或稍作修改的反馈：主判断、重新表述的问题、一两个具体的下一步、一句可行性判断。另有几行写进项目卡，记下这次约定了什么。

## 哪些要你确认

反馈日期、约定的下一步和截止时间是事实，助手直接写进项目卡；人物卡标为 `sensitive`，只记你愿意让对方看到的内容。对学生能力的看法、题目要不要换，是判断：助手先写成草稿，用 `python3 scripts/ros.py --root personal_vault propose judgment --file <草稿> --target <卡片>` 登记，你在自己的终端里确认后才长期保留。
