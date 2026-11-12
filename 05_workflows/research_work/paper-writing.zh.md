---
type: workflow
title: "写论文"
route: paper_writing
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <a href="paper-writing.md">English</a> | <strong>中文</strong>
</p>

# 写论文

## Agent Summary

当你在起草或修改自己论文的某一节，想让助手帮你理清论证、打磨文字时用这个工作流。它只用项目卡里已经记下的结果，不会生出新发现，也不能代替合作者读稿。

## 读哪些卡

读取档 quick 读你的写作风格卡 `personal_vault/03_cognition/style/writing.md`。如果你还没写这张卡，助手改读你的研究身份摘要 `personal_vault/00_identity/research-identity.md`。

standard 档再加 `personal_vault/00_identity/research-identity.md`、本工作流、这个项目的方向摘要（`personal_vault/01_knowledge/capsules/<项目>.md`），以及方向摘要的表格里为写作列出的卡，通常是项目卡和这一节引用的论文卡。

evidence 档不再加卡。助手只打开这些卡的「证据边界」里写明的原件，而且只为一个说清楚的问题，例如投稿前逐个核对结果部分的数字。助手能打开的原件，是你自己的论文和笔记、已发表的来源，以及不含可识别参与者信息的分析输出。访谈逐字稿、原始数据和 README「哪些不要交给助手」清单上的其他东西都留在你手里；核对要用到它们时，由你自己来核。

想知道助手会读你的哪些卡，可以运行 `python3 scripts/plan_context.py paper_writing --vault personal_vault`。

## 步骤

1. 先用一句话说清这一节要做什么：读者读完应该相信什么。
2. 动笔之前，把论证写成一条短链：问题是什么，已有工作为什么没解决，你做了什么，证据说明了什么，由此能得出什么。每一环都要能指到卡里记下的某个结果。
3. 每个数字、引文和参考文献都和来源卡核对一遍。找不到出处的，标成问题，不要替它补上。
4. 按风格卡描述的口吻起草。文章里已经用过的说法照用，不给同一个东西另起新名字。
5. 原稿里写明的限定保留下来。改写如果让某个说法超出了证据，标出来，不要放过。
6. 新稿和上一版按主张逐条对照，不只看句子改了哪里，然后列出改动。

## 产出

改好的一节，或者一份提纲，附一小段说明：哪些主张变了，哪些数字对照哪张卡核过，还有哪些问题要你或合作者回答。

## 哪些要你确认

稿子的事实，比如当前是哪一版、计划哪天投、下一步做什么，助手直接写进项目卡。某个说法够不够格写进去、文章怎么和相关工作定位、写作上新形成的规矩，这些是判断：助手先写成草稿，用 `python3 scripts/ros.py --root personal_vault propose judgment --file <草稿> --target <卡片>` 登记，你在自己的终端里确认后才长期保留。你的风格卡助手不会直接改。
