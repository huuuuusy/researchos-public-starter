---
type: style
title: How I write papers (fictional)
task: writing
status: provisional
related_examples:
  - 01_knowledge/projects/occlusion-tracking.md
sensitivity: internal
updated: 2026-09-22
---

# How I write papers (fictional)

## Agent Summary

How this researcher writes a paper, drawn from the draft of the occlusion tracking paper, two earlier comments on their writing and one correction of an assistant's draft. The points that matter most: a paragraph opens with its claim, every number names its split and protocol version, and a caption states the one thing to see. Read this card before drafting or revising any part of that paper; the assistant's additions below are not rules. The card is fictional and only shows how a working-style card is written.

## What I do (with source)

- A paragraph opens with its claim; the evidence and the numbers follow.
  - Why: readers and reviewers skim the first sentences, so the argument has to be there.
  - How to apply: introduction, results and discussion paragraphs. Not a paragraph that only describes the setup (data, implementation details), where there is no claim to put first.
  - Source: 2026-09-20, my own introduction draft, paragraph 2, which I marked as good.
- Every number in the text names its split and protocol version, e.g. "71.2 on the standard split, protocol version 1".
  - Why: the benchmark is changing version, and a number without its version cannot be compared later; a reviewer of my previous paper asked which split a number came from.
  - How to apply: every number in the text and captions. In a table the column header can carry the split and version once instead of each cell.
  - Source: 2025, a reviewer comment on my previous paper (review file on this computer).
- What we have not measured is said plainly: "we have not yet measured heavy occlusion", not a hedge.
  - Why: a hedge leaves the reader guessing whether it was measured; my former supervisor marked such hedges as hiding the gap.
  - How to apply: any result that is missing or pending. Not a result that was measured but varies a lot; there, give the spread.
  - Source: 2024, my former supervisor's comments on a draft.
- A figure caption says what to look at and the one conclusion, so the figure can be read without the text.
  - Why: many readers look at the figures before the text.
  - How to apply: result figures. Not an overview figure of the method, whose caption names the parts instead.
  - Source: 2026-09-20, my own caption for Figure 2 of the draft.
- Give the two numbers, not a size word such as "by a large margin".
  - Why: a size word cannot be checked; this came from correcting an assistant's draft.
  - How to apply: results paragraphs and the abstract. In a talk, saying "about three points" aloud is fine.
  - Source: 2026-09-21, my correction of an assistant's draft of the results paragraph (comment in the draft).

## What I cut or avoid (with source)

- An opening sentence that only says the field is important.
  - Why: it tells the reader nothing they do not know, and delays the question.
  - How to apply: the first sentence of a paper's introduction and abstract. In a talk to people outside the field, one sentence of context may stay.
  - Source: 2026-09-20, cut from both of my last two introductions; see the draft's revision history.
- "Novel", and "significantly" when no test is reported.
  - Why: whether something is novel is the reader's call, and "significantly" reads as a statistical claim.
  - How to apply: the whole paper; "significantly" is fine where a test is reported.
  - Source: 2024, my former supervisor's comments on a draft.
- "Robust" without saying to what; in this paper it is always "robust to occlusion".
  - Why: this paper only measures occlusion, so a bare "robust" claims more than was tested.
  - How to apply: this paper. In other papers, name what the method is robust to.
  - Source: 2026-09-20, my own edits to the draft.

## Examples from my own text

- Introduction, paragraph 2 of the draft: "Method A beats method B on the standard split (71.2 vs 68.4, protocol version 1). Whether it still does under heavy occlusion, where most failures happen, we have not yet measured." It works because the claim comes first, the numbers carry their protocol, and the open question is stated as open.

## Assistant's additions (not confirmed by me)

- Results paragraphs in the draft seem to end with the limit of the result in one sentence. Seen in three paragraphs; not yet confirmed as a habit.

## To verify

- Whether the rule on "novel" also holds for the abstract, where the draft still uses it once.

## Evidence boundary

- This card is based on: my introduction draft and caption for Figure 2 (`~/Papers/occlusion-draft/`), one reviewer comment on my previous paper, my former supervisor's comments on a 2024 draft (both on this computer, not in the vault) and my comment correcting an assistant's draft (in the draft).
- Not checked: whether the same points hold for writing outside this field. `status` stays provisional until I have gone through every point.
