---
type: workflow
title: "Meeting Follow-up"
route: meeting_follow_up
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <strong>English</strong> | <a href="meeting-follow-up.zh.md">中文</a>
</p>

# Meeting Follow-up

## Agent Summary

Use this workflow after a project meeting, a supervision session or a call with collaborators, when you want your notes turned into decisions, action items and card updates. It works from your own notes or the key points you write down, not from a recording or a full transcript of what others said. It is not a transcript service, and it does not send anything on your behalf.

## What to read

At the quick level the assistant reads your research identity page, `personal_vault/00_identity/research-identity.md`. There is no separate style card for meetings.

At the standard level it adds this workflow, the direction summary of the project the meeting concerned (`personal_vault/01_knowledge/capsules/<project>.md`), and only the cards that summary's table names for meetings, usually the project card and the cards of the people present.

At the evidence level no new cards are opened. The assistant goes back to your own notes or the minutes that the meeting card's "Evidence boundary" names, and only for a stated question, for example what exactly was agreed about a data-sharing date. A recording or a full transcript stays with you; if the question turns on exact words, check them yourself and tell the assistant what you found.

Run `python3 scripts/plan_context.py meeting_follow_up --vault personal_vault` to see which of your cards the assistant will read.

## Steps

1. Separate what was said and decided from impressions about it. Attribute a remark to a person only when a decision depends on it.
2. List each decision with what it replaces, if anything.
3. List action items with an owner, a deliverable and a date. An item with no owner becomes a question for you.
4. Update the affected cards: the project's current stage and next step, new dates, and pointers to new materials.
5. If you ask for one, draft a short follow-up message that lists decisions and actions in plain terms. You read it and send it yourself.
6. End with the open questions and anything only you can confirm.

## What you get

A meeting card under `personal_vault/06_active_context/meetings/`, named with the date, holding the record, decisions and actions, and marked `sensitivity: sensitive` because it records what others said. Updated project cards, and a draft message if you asked for one.

## What needs your confirmation

Dates, attendees, agreed actions and the project's next step are facts and go onto cards directly. Your reading of the meeting, such as whether a collaborator's plan is realistic or whether the project's priority should change, is a judgment: the assistant drafts it and submits it with `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target <card>`, and it lasts only after you confirm it in your own terminal.
