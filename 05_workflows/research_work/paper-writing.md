---
type: workflow
title: "Paper Writing"
route: paper_writing
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <strong>English</strong> | <a href="paper-writing.zh.md">中文</a>
</p>

# Paper Writing

## Agent Summary

Use this workflow when you are drafting or revising a section of your own paper and want the assistant to help shape the argument and the prose. It works from results your project cards already record. It does not produce findings, and it does not stand in for your co-authors' reading of the draft.

## What to read

At the quick level the assistant reads your writing style card, `personal_vault/03_cognition/style/writing.md`. If you have not written one yet, the assistant reads your research identity page, `personal_vault/00_identity/research-identity.md`, instead.

At the standard level it adds `personal_vault/00_identity/research-identity.md`, this workflow, the direction summary of the project (`personal_vault/01_knowledge/capsules/<project>.md`), and only the cards that summary's table names for writing, typically the project card and the paper cards the section cites.

At the evidence level no new cards are opened. The assistant goes to the originals those cards' "Evidence boundary" names, and only for a stated question, for example checking each number in the results section before submission. The originals it may open are your own papers and notes, published sources, and analysis outputs that contain no identifiable participants. Interview transcripts, raw data and anything else on the README's "What to keep away from the assistant" list stay with you; if a check needs them, you do it yourself.

Run `python3 scripts/plan_context.py paper_writing --vault personal_vault` to see which of your cards the assistant will read.

## Steps

1. Name the section and its job in one sentence: what the reader should believe after reading it.
2. Before any prose, write the argument as a short chain: the problem, why existing work leaves it open, what you did, what the evidence shows, what follows. Each link should point to a result recorded on a card.
3. Check every number, quotation and citation against the card it comes from. Anything without a source is marked as a question, not filled in.
4. Draft in the voice your style card describes, and keep the terms the paper already uses rather than introducing new names for the same thing.
5. Keep the limits the earlier draft states. If a revision makes a claim broader than the evidence, flag it instead of letting it through.
6. Compare the new version with the previous one claim by claim, not only sentence by sentence, and list what changed.

## What you get

A revised section, or an outline of one, with a short note that lists which claims changed, which numbers were checked against which card, and which questions remain for you or your co-authors.

## What needs your confirmation

Facts about the manuscript, such as which version is current, the target submission date and the next step, go onto the project card directly. Whether a claim is strong enough to make, how to position the paper against related work, or a new rule for how you write is a judgment: the assistant drafts it and submits it with `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target <card>`, and it lasts only after you confirm it in your own terminal. The assistant never edits your style card directly.
