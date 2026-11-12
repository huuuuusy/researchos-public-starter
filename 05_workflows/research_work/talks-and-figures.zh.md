---
type: workflow
title: "报告与作图"
route: presentation
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <a href="talks-and-figures.md">English</a> | <strong>中文</strong>
</p>

# 报告与作图

## Agent Summary

准备学术报告、幻灯片、海报或论文配图时，想让助手帮你定下每一部分该讲什么、并检查它有没有讲到，就用这个工作流。`presentation` 和 `figure_design` 两条路由共用它。它不会给图编造数据，也不能代替你自己看渲染出来的效果。

## 读哪些卡

quick 档读你的作图与报告风格卡 `personal_vault/03_cognition/style/figures-talks.md`。如果你还没写这张卡，助手改读你的研究身份摘要 `personal_vault/00_identity/research-identity.md`。

standard 档再加 `personal_vault/00_identity/research-identity.md`、本工作流、报告或图所讲项目的方向摘要（`personal_vault/01_knowledge/capsules/<项目>.md`），以及方向摘要的表格里为报告或作图列出的卡。

evidence 档不再加卡。助手只打开这些卡的「证据边界」里写明的原件，比如图背后的数据文件或照片的出处，而且只为一个说清楚的问题，例如柱状图上的数值和已发表的表格是否一致。

想知道助手会读你的哪些卡，可以运行 `python3 scripts/plan_context.py presentation --vault personal_vault`（单张图用 `figure_design`）。

## 步骤

1. 先说清听众是谁，他们听完应该记住哪一点。系里的研讨会、面向公众的讲座和学术会议，要讲的那一点通常不一样。
2. 做报告时，按听众会依次提出的问题排章节，一个问题一节。
3. 每页幻灯片或每张图，用一句话写出它要说明的那一点。不服务于这一点的内容删掉，或放进备用页。
4. 已有的图只有在支撑当前这一点时才复用；否则用原始数据重画，或者画一张新的。
5. 每个数字、标注和出处都和卡片及其来源核对。手里有真实材料时，比如田野点照片、扫描页面或标本图像，优先用它而不是示意图，并写明出处。
6. 渲染出来后，按实际尺寸看过每一页改动过的幻灯片或图，才算完成；如果没法看，就照实说明。

## 产出

一份每页或每个子图一句话的提纲，接着是幻灯片或图的草稿，再附一小段说明：哪些内容对照哪张卡核过，哪些还要你亲自看。

## 哪些要你确认

报告日期、听众、时长和文件放在哪里是事实，助手直接写进项目卡。报告的核心信息、怎么把你的工作和别人的工作放在一起讲、长期的视觉风格选择，这些是判断：助手先写成草稿，用 `python3 scripts/ros.py --root personal_vault propose judgment --file <草稿> --target <卡片>` 登记，你在自己的终端里确认后才长期保留。
