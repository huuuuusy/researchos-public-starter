---
type: workflow
title: "Topic Change"
route: idea_diagnosis
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <strong>English</strong> | <a href="topic-change.zh.md">中文</a>
</p>

# Topic Change

## Agent Summary

Use this workflow when you are deciding whether to continue, narrow, redirect, pause or stop a project or an early idea. The assistant lays out what the evidence supports for each option and what each would cost. The decision is yours, and nothing is recorded as decided until you make it.

## What to read

At the quick level the assistant reads your research identity page, `personal_vault/00_identity/research-identity.md`. There is no separate style card for this task.

At the standard level it adds this workflow, the direction summary of the project concerned (`personal_vault/01_knowledge/capsules/<project>.md`), only the cards that summary's table names for this decision, and your heuristic cards under `personal_vault/03_cognition/heuristics/`.

At the evidence level no new cards are opened. The assistant goes to the originals those cards' "Evidence boundary" names, and only for a stated question, for example whether the pilot data really showed no effect or simply too few cases.

Run `python3 scripts/plan_context.py idea_diagnosis --vault personal_vault` to see which of your cards the assistant will read.

## Steps

1. Restate the original question and check whether it still stands: has someone else answered it, or has your own evidence changed what the question should be?
2. Collect what the results so far actually show, from the project card, and keep results apart from expectations.
3. Check the means: skills, access to data, sites or archives, time, and how long current funding lasts.
4. Check the link to your long-term direction as your research identity page states it, and to any heuristic card that applies.
5. Lay out the options side by side. For each, say what it keeps from the work done, what it costs, and what you would see within a set time that would show it was the wrong choice.
6. Once you decide, the assistant drafts the decision with its reasons and the alternatives you set aside, and submits it for your confirmation.

## What you get

A one-page comparison of the options with the evidence behind each, and, after you decide, a draft decision card for `personal_vault/02_decisions/`, named with the date, that becomes a card once you confirm it.

## What needs your confirmation

What has been done, what the data show and the current dates are facts and can be updated on the project card directly. The choice itself, a change of priority or state, and any new rule of thumb that comes out of it are judgments: the assistant drafts them and submits them with `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target <card>`, and they last only after you confirm them in your own terminal.
