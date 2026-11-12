---
type: workflow
title: "Mentee Feedback"
route: mentee_feedback
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <strong>English</strong> | <a href="mentee-feedback.zh.md">中文</a>
</p>

# Mentee Feedback

## Agent Summary

Use this workflow when a student or junior colleague sends you a draft, a research plan or a progress update and you want to give feedback that helps them take the next step. The assistant helps you find the main issue and a feasible next move. It does not grade the person, and it does not decide whether a project should continue.

## What to read

At the quick level the assistant reads your mentoring style card, `personal_vault/03_cognition/style/mentoring.md`. If you have not written one yet, the assistant reads your research identity page, `personal_vault/00_identity/research-identity.md`, instead.

At the standard level it adds `personal_vault/00_identity/research-identity.md`, this workflow, the direction summary of the project concerned (`personal_vault/01_knowledge/capsules/<project>.md`), and only the cards that summary's table names for feedback, usually the project card and the mentee's person card.

At the evidence level no new cards are opened. The assistant goes to the originals those cards' "Evidence boundary" names, and only for a stated question, for example what the agreed plan from the last meeting actually said.

Run `python3 scripts/plan_context.py mentee_feedback --vault personal_vault` to see which of your cards the assistant will read.

## Steps

1. Read the material and state the main judgment first: what the work is trying to show, and whether its current framing gets there.
2. Write the core research question as you understand it. If it differs from the one the mentee states, say so plainly.
3. Point to where the framing is strong and where it is weak, tied to specific pages, tables or figures.
4. Suggest a sharper question and the smallest next step that would test it, such as one more analysis, a short pilot round of interviews or one control condition, before asking for more work.
5. Check feasibility against the time, data access and skills available, and say what a realistic output would be, such as a thesis chapter, a poster or a paper.
6. Write the feedback short and direct, in the voice your mentoring style card describes.

## What you get

A short feedback note you can send or adapt: the main judgment, a restated question, one or two concrete next steps and a feasibility remark. Separately, a few lines for the project card on what was agreed.

## What needs your confirmation

The date of the feedback, the agreed next step and the deadline are facts and go onto the project card directly; person cards are `sensitive` and record only what you would be comfortable showing the person. Views about the mentee's abilities, or whether the topic should change, are judgments: the assistant drafts them and submits them with `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target <card>`, and they last only after you confirm them in your own terminal.
