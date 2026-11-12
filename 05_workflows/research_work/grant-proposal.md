---
type: workflow
title: "Grant Proposal"
route: proposal
status: active
sensitivity: public
updated: 2026-11-11
---

<p align="right">
  <strong>English</strong> | <a href="grant-proposal.zh.md">中文</a>
</p>

# Grant Proposal

## Agent Summary

Use this workflow when you are planning or drafting a grant application, a fellowship proposal or an internal funding request and want help making the case clear and the plan feasible. The assistant works from the call text you provide and what your cards record. It does not decide budget shares or staffing, and it does not claim results you do not have.

## What to read

At the quick level the assistant reads your proposal style card, `personal_vault/03_cognition/style/proposal.md`. If you have not written one yet, the assistant reads your research identity page, `personal_vault/00_identity/research-identity.md`, instead.

At the standard level it adds `personal_vault/00_identity/research-identity.md`, this workflow, the direction summary of the project the proposal grows from (`personal_vault/01_knowledge/capsules/<project>.md`), and only the cards that summary's table names for proposals, such as the project card and the papers you cite as prior work.

At the evidence level no new cards are opened. The assistant goes to the originals those cards' "Evidence boundary" names, and only for a stated question, for example confirming a pilot result or a publication record before you submit.

Run `python3 scripts/plan_context.py proposal --vault personal_vault` to see which of your cards the assistant will read.

## Steps

1. Read the call and its review criteria first. List what each section must answer, the page or word limits, and who the reviewers are likely to be.
2. Open with the problem as it exists in the field or in practice, then say why current work or tools leave it open. The project is the response to that gap.
3. Set aims that the time and money can carry. For each aim, name what evidence would show it was achieved.
4. Put the evaluation plan near the centre: what will be measured, compared with what, on which sample, sites or sources, and when.
5. Connect aims, work packages, timeline and budget so a reviewer can trace each cost to an aim. Leave the amounts and staffing for you to set.
6. Check every statement about prior work and track record against your cards. Only items a reviewer could verify go in.
7. Read the draft once as a reviewer from a neighbouring field would, and mark terms or steps that need a plain example.

## What you get

A section outline mapped to the review criteria, or a full draft, with a short list of open items: numbers to confirm, decisions about scope or budget, and missing documents.

## What needs your confirmation

The call deadline, submission status and next step are facts and go onto the project card directly. The scope of the project, its priority against your other work and how far the aims reach are judgments: the assistant drafts them and submits them with `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target <card>`, and they last only after you confirm them in your own terminal.
