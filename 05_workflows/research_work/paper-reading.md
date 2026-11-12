---
type: workflow
title: "Paper Reading"
route: material_understanding
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <strong>English</strong> | <a href="paper-reading.zh.md">中文</a>
</p>

# Paper Reading

## Agent Summary

Use this workflow when you want an assistant to read one paper, report or book chapter with you and turn it into a short paper card: the question it asks, what its evidence shows, and how it bears on your own work. It is for understanding a single source. It is not a literature search, and it does not settle whether the source is right.

## What to read

At the quick level the assistant reads only the paper card itself, if one already exists under `personal_vault/01_knowledge/papers/`, together with the text you give it.

At the standard level it adds `personal_vault/00_identity/research-identity.md`, this workflow, the direction summary of the project the paper serves (`personal_vault/01_knowledge/capsules/<project>.md`), and only the cards that summary's table names for reading.

At the evidence level no new cards are opened. The assistant goes to the originals that those cards' "Evidence boundary" names, such as the full PDF or a supplementary table, and only to answer a stated question, for example whether the sample size in the abstract matches the methods section.

Run `python3 scripts/plan_context.py material_understanding --vault personal_vault` to see which of your cards the assistant will read.

## Steps

1. Record the basic facts: authors, year, where it appeared, and what kind of work it is (a field study, an archival analysis, an experiment, a review).
2. State the paper's question in one sentence, in your words rather than the abstract's.
3. Trace the evidence: which data or sources, what was compared with what, and which result carries the main claim. Note the page, table or figure.
4. Separate what the paper shows from what it suggests. A claim that rests on one site, one cohort or one collection is written down with that limit attached.
5. Note what you might reuse: a design choice, a measure, a way of coding sources, a figure layout.
6. Say how it relates to your current project, if it does, and mark this part as your view rather than the paper's.

## What you get

A paper card under `personal_vault/01_knowledge/papers/` with the bibliographic facts, the question in one sentence, the evidence and its limits, and a short note on relevance to your work. Its evidence boundary says where the original file lives, so later sessions do not need to reopen it.

## What needs your confirmation

What the paper says, its details and where its files are kept are facts, and the assistant writes them onto the card directly. Whether the central claim holds, whether the paper changes one of your plans, or whether its method should become a habit of yours is a judgment: the assistant drafts it and submits it with `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target <card>`, and it becomes durable only after you confirm it in your own terminal.
