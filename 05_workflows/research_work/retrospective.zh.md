---
type: workflow
title: "复盘"
route: system_reflection
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <a href="retrospective.md">English</a> | <strong>中文</strong>
</p>

# 复盘

## Agent Summary

一件工作结束或卡住之后用这个工作流：一次投稿、一份没批下来的申请、一个失败的实验、一轮改来改去没有进展的修改。助手帮你把实际发生的事和原先的预期对照着写清楚，找出原因而不是复述经过，并在留下教训之前先检验它。最多只有一条教训会写成草稿，你同意后才写进去。

## 读哪些卡

读取档 quick 读你的研究身份摘要 `personal_vault/00_identity/research-identity.md`。这类任务没有单独的风格卡。

standard 档再加本工作流、`personal_vault/03_cognition/heuristics/` 下你已有的启发式卡、所涉项目的方向摘要（`personal_vault/01_knowledge/capsules/<项目>.md`），以及方向摘要的表格里为这项工作列出的决策卡。

evidence 档不再加卡。助手只打开这些卡的「证据边界」里写明的原件，而且只为一个说清楚的问题，例如实验记录是否显示问题在改流程之前就出现了。

想知道助手会读你的哪些卡，可以运行 `python3 scripts/plan_context.py system_reflection --vault personal_vault`。

## 步骤

1. 用两三句话写下原先预期什么、实际发生了什么，带上日期。比如：问卷原计划三月收齐三百份，实际拖到五月，只收回九十份。
2. 把原因和经过分开。每个可能的原因，都要说清它能解释哪些别的原因解释不了的地方。
3. 看已有的启发式卡是不是早就提醒过这件事。如果提醒过而你没照做，也许并不需要再添一条新规矩。
4. 找这条教训最有力的反例：反着做却做成了的情况。再问自己：要是事先就知道这条教训，当时的做法会不会不一样？
5. 只留下一条经得住检验的教训。如果一条都留不下，就只记事实，到此为止。
6. 把这条教训写成草稿。关于研究上怎么取舍的习惯，用 `09_templates/basic/heuristic.md` 写成启发式卡，放在 `personal_vault/03_cognition/heuristics/<名字>.md`：规则、什么时候用、什么时候不用、从哪里来。关于你怎么写、怎么审、怎么讲的教训，写成你风格卡里的一条：规则、为什么、怎么用、出处。

## 产出

一份简短的复盘笔记，写明发生了什么、原因和反例；外加一张启发式卡草稿或一条风格卡条目，由你决定收下、改动还是不要。

## 哪些要你确认

日期和发生了什么是事实，可以直接写到项目卡上。教训、启发式卡和风格卡条目都先写成草稿，你同意后才写进去。如果这次复盘改变了卡上已有的判断，比如某个项目的优先级，助手用 `python3 scripts/ros.py --root personal_vault propose judgment --file <草稿> --target <卡片>` 登记，你在自己的终端里确认后才长期保留。
