---
type: workflow
title: "会后跟进"
route: meeting_follow_up
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <a href="meeting-follow-up.md">English</a> | <strong>中文</strong>
</p>

# 会后跟进

## Agent Summary

开完项目会、指导会或和合作者通完话，想把笔记整理成决定、待办和卡片更新时用这个工作流。它依据你自己的笔记或你记下的要点工作，不用录音，也不用别人发言的完整逐字稿；它不是转录服务，也不会替你发出任何消息。

## 读哪些卡

读取档 quick 读你的研究身份摘要 `personal_vault/00_identity/research-identity.md`。会议没有单独的风格卡。

standard 档再加本工作流、这次会议所涉项目的方向摘要（`personal_vault/01_knowledge/capsules/<项目>.md`），以及方向摘要的表格里为会议列出的卡，一般是项目卡和与会者的人物卡。

evidence 档不再加卡。助手只回到会议卡「证据边界」里写明的你自己的笔记或纪要，而且只为一个说清楚的问题，例如当时到底约定哪天共享数据。录音和完整逐字稿留在你手里；问题要落到原话时，由你自己去查，再把结果告诉助手。

想知道助手会读你的哪些卡，可以运行 `python3 scripts/plan_context.py meeting_follow_up --vault personal_vault`。

## 步骤

1. 把会上说了什么、定了什么，和你对它的印象分开。只有某个决定取决于某人的话时，才写明是谁说的。
2. 列出每个决定；如果它取代了之前的安排，一并写上。
3. 列出待办，每条都有负责人、交付物和日期。没有负责人的，留作问题问你。
4. 更新受影响的卡：项目当前阶段和下一步、新的日期、新材料放在哪里。
5. 你需要的话，起草一封简短的跟进消息，用平实的话列出决定和待办。由你看过后自己发。
6. 最后列出悬而未决的问题，以及只有你能确认的事。

## 产出

`personal_vault/06_active_context/meetings/` 下一张以日期开头命名的会议卡，记下记录、决定和待办；因为记的是别人说的话，标为 `sensitivity: sensitive`。另有更新过的项目卡，以及你要的消息草稿。

## 哪些要你确认

日期、与会者、约定的待办、项目下一步是事实，助手直接写进卡里。你对这次会议的看法，比如某位合作者的计划现不现实、项目优先级要不要调，属于判断：助手先写成草稿，用 `python3 scripts/ros.py --root personal_vault propose judgment --file <草稿> --target <卡片>` 登记，你在自己的终端里确认后才长期保留。
