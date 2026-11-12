---
type: workflow
title: "读论文"
route: material_understanding
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <a href="paper-reading.md">English</a> | <strong>中文</strong>
</p>

# 读论文

## Agent Summary

当你想让助手陪你读一篇论文、一份报告或一章书，并整理成一张简短的论文卡时用这个工作流：它问了什么问题，证据到底说明了什么，和你自己的研究有什么关系。它只管读懂一份材料，不做文献检索，也不替你裁定这篇文章对不对。

## 读哪些卡

quick 档只读这篇论文自己的卡（如果 `personal_vault/01_knowledge/papers/` 下已经有），再加上你交给它的原文。

standard 档再加 `personal_vault/00_identity/research-identity.md`、本工作流、这篇论文所服务项目的方向摘要（`personal_vault/01_knowledge/capsules/<项目>.md`），以及方向摘要的表格里为读论文列出的那几张卡，别的不读。

evidence 档不再加卡。助手只打开这些卡的「证据边界」里写明的原件，比如 PDF 全文或补充表格，而且只为回答一个说清楚的问题，例如摘要里的样本量和方法部分对不对得上。

想知道助手会读你的哪些卡，可以运行 `python3 scripts/plan_context.py material_understanding --vault personal_vault`。

## 步骤

1. 记下基本信息：作者、年份、发表在哪里，属于哪类工作（田野研究、档案分析、实验、综述等）。
2. 用一句话写出这篇文章的问题，用你自己的话，不照抄摘要。
3. 理清证据：用了哪些数据或材料，拿什么和什么比，主要结论靠的是哪一个结果。标出页码、表号或图号。
4. 分开「文章证明了什么」和「文章暗示了什么」。只基于一个地点、一批样本或一处馆藏的结论，连同这个限制一起写下。
5. 记下可以借用的东西：某个研究设计、某个测量方式、材料编码的办法、某张图的排法。
6. 如果和你手头的项目有关，写清楚关系在哪里，并标明这是你的看法，不是文章的说法。

## 产出

`personal_vault/01_knowledge/papers/` 下的一张论文卡：基本信息、一句话问题、证据及其限度，以及一小段和你研究的关系。卡上的证据边界写明原文放在哪里，以后的会话不必重新打开原文。

## 哪些要你确认

文章说了什么、文献信息、文件放在哪里，这些是事实，助手直接写进卡里。核心结论站不站得住、它会不会改变你的某个计划、它的方法要不要变成你的习惯，这些是判断：助手先写成草稿，用 `python3 scripts/ros.py --root personal_vault propose judgment --file <草稿> --target <卡片>` 登记，你在自己的终端里确认之后才会长期保留。
