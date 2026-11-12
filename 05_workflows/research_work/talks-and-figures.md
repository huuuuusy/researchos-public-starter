---
type: workflow
title: "Talks and Figures"
route: presentation
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <strong>English</strong> | <a href="talks-and-figures.zh.md">中文</a>
</p>

# Talks and Figures

## Agent Summary

Use this workflow when you prepare a talk, a slide deck, a poster or a figure for a paper, and want help deciding what each part should say and checking that it says it. The same workflow serves the `presentation` and `figure_design` routes. It does not invent data for a figure, and it does not replace looking at the rendered result yourself.

## What to read

At the quick level the assistant reads your figures and talks style card, `personal_vault/03_cognition/style/figures-talks.md`. If you have not written one yet, the assistant reads your research identity page, `personal_vault/00_identity/research-identity.md`, instead.

At the standard level it adds `personal_vault/00_identity/research-identity.md`, this workflow, the direction summary of the project the talk or figure presents (`personal_vault/01_knowledge/capsules/<project>.md`), and only the cards that summary's table names for talks or figures.

At the evidence level no new cards are opened. The assistant goes to the originals those cards' "Evidence boundary" names, such as the data file behind a chart or the source of a photograph, and only for a stated question, for example whether the values on a bar chart match the published table.

Run `python3 scripts/plan_context.py presentation --vault personal_vault` (or `figure_design` for a single figure) to see which of your cards the assistant will read.

## Steps

1. Name the audience and the one point they should leave with. A departmental seminar, a public lecture and a conference session usually need different points.
2. For a talk, order the sections by the questions the audience would ask in turn, one section per question.
3. For each slide or figure, write the single point it makes in one sentence. Anything that does not serve a point is cut or moved to backup.
4. Reuse an existing figure only when it supports the current point. Otherwise rebuild it from the original data or draw a new one.
5. Check every number, label and credit against the cards and their sources. Where you have real material, such as a site photograph, a scanned page or a specimen image, prefer it to a sketch and state where it comes from.
6. Render the result and look at every changed slide or figure at its real size before calling it finished; if you cannot view it, say so.

## What you get

An outline with one sentence per slide or panel, then the draft slides or figure, and a short note of what was checked against which card and what still needs your eye.

## What needs your confirmation

The talk date, the audience, the length and where the files are stored are facts and go onto the project card directly. The main message of a talk, how to present your work against others, and a lasting choice about your visual style are judgments: the assistant drafts them and submits them with `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target <card>`, and they last only after you confirm them in your own terminal.
