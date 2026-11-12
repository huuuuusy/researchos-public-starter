---
type: workflow
title: "Peer Review"
route: peer_review
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <strong>English</strong> | <a href="peer-review.zh.md">中文</a>
</p>

# Peer Review

## Agent Summary

Use this workflow when you review a manuscript, a thesis chapter or a grant application for someone else and want help writing a fair and specific report. The assistant works from your own notes and the points you quote, and helps you test the submission's claims against its evidence. By default the manuscript itself is not given to the assistant and is not copied into your vault. The assistant does not make the recommendation for you.

## What to read

At the quick level the assistant reads your review style card, `personal_vault/03_cognition/style/review.md`. If you have not written one yet, the assistant reads your research identity page, `personal_vault/00_identity/research-identity.md`, instead.

At the standard level it adds `personal_vault/00_identity/research-identity.md`, this workflow, the direction summary closest to the submission's topic (`personal_vault/01_knowledge/capsules/<project>.md`), and only the cards that summary's table names for reviewing, usually paper cards for the work the submission builds on.

At the evidence level no new cards are opened. The assistant goes to the originals those cards' "Evidence boundary" names, which never include the submission, and only for a stated question, for example whether a cited study really reports what the submission says it does.

Run `python3 scripts/plan_context.py peer_review --vault personal_vault` to see which of your cards the assistant will read.

## Steps

1. Check what the journal, funder or committee allows on AI tools. By default, do not give the assistant the manuscript: it works from your own notes and the points you quote. Share more only if the venue explicitly allows AI tools, and then follow its rules.
2. From your notes, summarize the submission in three or four neutral sentences: the question, the material, the main claim. If this is hard to do, note why.
3. Say what kind of contribution it claims (a new question, a method, a dataset, a replication, a synthesis) and judge it as that kind.
4. For each central claim, find the evidence that carries it and ask whether the design, sample or sources can support it. Note the page, table or figure.
5. Rank the problems by how much they affect the central claim, say whether a revision can fix each one, and merge points that come from the same underlying issue.
6. Before finishing, look for passages that already answer your criticism and withdraw any point the submission addresses.

## What you get

A draft report in the order the venue expects, usually a short summary, the main concerns and then minor points, each with a concrete request. Your reasoning for the recommendation is kept in a separate note that only you see.

## What needs your confirmation

Facts such as the due date, the date you submitted and the editor's decision can go onto a card directly. The recommendation is yours to make and send. If the review leaves you with a lasting view, for example a standard you want to apply to every future review, the assistant drafts it and submits it with `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target <card>`, and it lasts only after you confirm it in your own terminal.
