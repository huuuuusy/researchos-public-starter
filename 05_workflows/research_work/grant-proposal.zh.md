---
type: workflow
title: "写基金申请"
route: proposal
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <a href="grant-proposal.md">English</a> | <strong>中文</strong>
</p>

# 写基金申请

## Agent Summary

当你在构思或起草基金申请、人才项目申请或单位内部的经费申请，想把理由讲清楚、把计划做得可行时用这个工作流。助手依据你提供的申请指南和卡里的记录工作。经费怎么分、人员怎么配由你定，你没有的结果它不会写进去。

## 读哪些卡

quick 档读你的申请书风格卡 `personal_vault/03_cognition/style/proposal.md`。如果你还没写这张卡，助手改读你的研究身份摘要 `personal_vault/00_identity/research-identity.md`。

standard 档再加 `personal_vault/00_identity/research-identity.md`、本工作流、申请所依托项目的方向摘要（`personal_vault/01_knowledge/capsules/<项目>.md`），以及方向摘要的表格里为申请书列出的卡，比如项目卡和作为前期基础引用的论文卡。

evidence 档不再加卡。助手只打开这些卡的「证据边界」里写明的原件，而且只为一个说清楚的问题，例如提交前核对某个预实验结果或发表记录。

想知道助手会读你的哪些卡，可以运行 `python3 scripts/plan_context.py proposal --vault personal_vault`。

## 步骤

1. 先读申请指南和评审标准。列出每一部分要回答什么、篇幅限制是多少、评审大概是哪些人。
2. 从领域里或实践中真实存在的问题讲起，再说清现有研究或工具为什么解决不了。项目就是对这个缺口的回应。
3. 定下时间和经费撑得起的目标。每个目标都写明：什么样的证据能说明它做到了。
4. 把评估方案放在中心位置：测什么，和什么比，用哪些样本、地点或材料，什么时候做。
5. 把目标、工作包、时间表和预算连起来，让评审能从每一笔开支找到它服务的目标。具体金额和人员安排留给你定。
6. 关于前期工作和个人履历的每一句话，都和卡片核对。只写评审能查证的内容。
7. 站在相邻领域评审的角度通读一遍，标出需要用通俗例子解释的术语和步骤。

## 产出

一份按评审标准排好的章节提纲，或一份完整草稿，附一小张待办清单：要确认的数字、范围或预算上要你拍板的事、还缺的材料。

## 哪些要你确认

申请截止日期、提交状态和下一步是事实，助手直接写进项目卡。项目范围多大、和你其他工作相比排第几、目标定得多远，这些是判断：助手先写成草稿，用 `python3 scripts/ros.py --root personal_vault propose judgment --file <草稿> --target <卡片>` 登记，你在自己的终端里确认后才长期保留。
