---
type: workflow
title: "Retrospective"
route: system_reflection
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <strong>English</strong> | <a href="retrospective.zh.md">中文</a>
</p>

# Retrospective

## Agent Summary

Use this workflow after a piece of work has ended or stalled: a submission, a proposal that was turned down, an experiment that failed, a revision that went in circles. The assistant helps you compare what happened with what you expected, find causes rather than retell the timeline, and test the lesson before you keep it. At most one lesson becomes a draft, written only after you agree.

## What to read

At the quick level the assistant reads your research identity page, `personal_vault/00_identity/research-identity.md`. There is no separate style card for this task.

At the standard level it adds this workflow, your existing heuristic cards under `personal_vault/03_cognition/heuristics/`, the direction summary of the project concerned (`personal_vault/01_knowledge/capsules/<project>.md`), and the decision cards that summary's table names for this work.

At the evidence level no new cards are opened. The assistant goes to the originals those cards' "Evidence boundary" names, and only for a stated question, for example whether the experiment log shows the failure began before the protocol change.

Run `python3 scripts/plan_context.py system_reflection --vault personal_vault` to see which of your cards the assistant will read.

## Steps

1. Write down in two or three sentences what you expected and what actually happened, with dates. For example: the survey was meant to close in March with three hundred responses and closed in May with ninety.
2. Separate causes from the timeline. For each candidate cause, say what it explains that the others do not.
3. Check whether an existing heuristic card already covered this. If it did and you did not follow it, you may not need a new rule.
4. Find the strongest counterexample to the lesson: a case where doing the opposite worked. Then ask whether knowing the lesson beforehand would have changed what you did.
5. Keep one lesson that survives this test. If none does, record the facts and stop there.
6. Turn the lesson into a draft. A habit about research choices becomes a heuristic card at `personal_vault/03_cognition/heuristics/<name>.md` from `09_templates/basic/heuristic.md`: the rule, when to use it, when not to, where it came from. A lesson about how you write, review or present becomes one entry for your working-style card: the rule, why, how to apply it, its source.

## What you get

A short note with what happened, the causes and the counterexample, plus one draft heuristic card or working-style entry for you to accept, change or drop.

## What needs your confirmation

Dates and what happened are facts and can be written onto the project card directly. The lesson, the heuristic card and any working-style entry are drafted and written only after you agree. If the retrospective changes a judgment already on a card, for example the priority of a project, the assistant submits it with `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target <card>`, and it lasts only after you confirm it in your own terminal.
