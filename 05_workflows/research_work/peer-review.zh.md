---
type: workflow
title: "审稿"
route: peer_review
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <a href="peer-review.md">English</a> | <strong>中文</strong>
</p>

# 审稿

## Agent Summary

当你替别人审一篇稿件、一章学位论文或一份基金申请，想写出公正而具体的意见时用这个工作流。助手依据你自己的笔记和你引出的要点工作，帮你拿稿件的证据去检验它的主张。默认不把稿件本身交给助手，也不复制进你的库。最终建议由你来下。

## 读哪些卡

读取档 quick 读你的审稿风格卡 `personal_vault/03_cognition/style/review.md`。如果你还没写这张卡，助手改读你的研究身份摘要 `personal_vault/00_identity/research-identity.md`。

standard 档再加 `personal_vault/00_identity/research-identity.md`、本工作流、和稿件主题最接近的方向摘要（`personal_vault/01_knowledge/capsules/<项目>.md`），以及方向摘要的表格里为审稿列出的卡，一般是稿件所依托的那些工作的论文卡。

evidence 档不再加卡。助手只打开这些卡的「证据边界」里写明的原件，其中从不包括所审的稿件，而且只为一个说清楚的问题，例如稿件引用的某项研究是否真的报告了它所说的结果。

想知道助手会读你的哪些卡，可以运行 `python3 scripts/plan_context.py peer_review --vault personal_vault`。

## 步骤

1. 先查期刊、基金方或委员会对使用 AI 工具的规定。默认不把稿件交给助手：它只依据你自己的笔记和你引出的要点工作。只有刊物明确允许使用 AI 工具时，才可以多给一些，并照它的规定做。
2. 根据你的笔记，用三四句中性的话概括稿件：问题、材料、主要结论。如果概括不出来，记下原因。
3. 判断它声称的是哪类贡献（新问题、新方法、新数据、重复研究、综合），按这一类的标准来评。
4. 对每个核心主张，找到撑起它的证据，问研究设计、样本或材料能不能支撑它。标出页码、表号或图号。
5. 按对核心主张的影响排出问题的轻重，逐条说明能不能靠修改解决；同一个根本问题引出的几点合成一条。
6. 收尾前，回头找稿件里有没有已经回应了你批评的段落，已经回应的那条撤掉。

## 产出

一份按刊物惯例排好的意见草稿，通常是简短概述、主要问题、次要问题，每条都带具体的修改要求。你下建议的理由另写一份笔记，只给你自己看。

## 哪些要你确认

截止日期、你提交的日期、编辑的决定，这些是事实，可以直接写进卡里。审稿建议由你自己定、自己发。如果这次审稿让你形成了一个长期的看法，比如以后每次审稿都想用的一条标准，助手先写成草稿，用 `python3 scripts/ros.py --root personal_vault propose judgment --file <草稿> --target <卡片>` 登记，你在自己的终端里确认后才长期保留。
