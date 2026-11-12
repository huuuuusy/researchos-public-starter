---
type: workflow
title: "要不要换题"
route: idea_diagnosis
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <a href="topic-change.md">English</a> | <strong>中文</strong>
</p>

# 要不要换题

## Agent Summary

当你在考虑一个项目或一个早期想法是继续做、收窄、转向、暂停还是放弃时，用这个工作流。助手把每个选项有什么证据支持、各要付出什么代价摆出来。决定由你来做，你做决定之前，什么都不会记成已定。

## 读哪些卡

quick 档读你的研究身份摘要 `personal_vault/00_identity/research-identity.md`。这类任务没有单独的风格卡。

standard 档再加本工作流、所涉项目的方向摘要（`personal_vault/01_knowledge/capsules/<项目>.md`）、方向摘要的表格里为这类决定列出的卡，以及 `personal_vault/03_cognition/heuristics/` 下你的启发式卡。

evidence 档不再加卡。助手只打开这些卡的「证据边界」里写明的原件，而且只为一个说清楚的问题，例如预实验数据到底是没有效应，还是只是样本太少。

想知道助手会读你的哪些卡，可以运行 `python3 scripts/plan_context.py idea_diagnosis --vault personal_vault`。

## 步骤

1. 重新写出最初的问题，看它是否还成立：别人是不是已经回答了，或者你自己的证据是不是已经改变了这个问题该怎么问。
2. 从项目卡里整理到目前为止的结果实际说明了什么，把结果和期望分开。
3. 看条件：技能、数据或田野点或档案的获取、时间，以及现有经费还能撑多久。
4. 对照研究身份摘要里写的长期方向，以及适用的启发式卡，看它们之间的联系。
5. 把几个选项并排列出。每个选项写明：能保留已做的哪些工作，要付出什么，以及在多长时间内看到什么就说明选错了。
6. 你做出决定后，助手把决定连同理由和放弃的方案写成草稿，交给你确认。

## 产出

一页选项对比，写明每个选项背后的证据；你决定之后，再出一张以日期开头命名、准备放进 `personal_vault/02_decisions/` 的决策卡草稿，你确认后才成为正式的卡。

## 哪些要你确认

做过什么、数据显示了什么、当前的日期，这些是事实，可以直接更新到项目卡。选哪个、优先级或状态的变化、由此得出的新经验法则，这些是判断：助手先写成草稿，用 `python3 scripts/ros.py --root personal_vault propose judgment --file <草稿> --target <卡片>` 登记，你在自己的终端里确认后才长期保留。
