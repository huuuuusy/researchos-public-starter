---
type: capsule
title: Occlusion tracking summary (fictional)
capsule_of: 01_knowledge/projects/occlusion-tracking.md
agent_reading_level: entry
context_budget: quick
group_level: G1_basic_group
source_files:
  - 01_knowledge/projects/occlusion-tracking.md
  - 01_knowledge/papers/example-benchmark.md
  - 01_knowledge/papers/outputs-index.md
  - 02_decisions/2026-09-22-wait-for-benchmark-v2.md
  - 04_people/collaborators/lin-ke.md
  - 03_cognition/heuristics/check-benchmark-version-first.md
  - 03_cognition/style/writing.md
sensitivity: internal
last_verified: 2026-09-22
updated: 2026-09-22
---

# Occlusion tracking summary (fictional)

## Agent Summary

The entry page for the occlusion tracking direction. An assistant working in this direction reads this page first and then only the card the table below points to, not the whole folder. The direction is fictional and only shows how a direction summary is written.

## Current points

- Question: does method A still beat method B under heavy occlusion?
- On the standard split A beats B (71.2 vs 68.4).
- The heavy-occlusion comparison waits for version 2 of the benchmark; if it is not out by 11-15, it runs on version 1.

## Which card to read for which task

| Task | Read first | Read only to verify (not by default) |
| --- | --- | --- |
| Plan the next experiment | [Project card](../projects/occlusion-tracking.md), [decision card](../../02_decisions/2026-09-22-wait-for-benchmark-v2.md) | Experiment log run-0915 |
| Describe the benchmark in the paper | [Benchmark card](../papers/example-benchmark.md) | The benchmark PDF |
| Write the related-work paragraph or a talk abstract | [Benchmark card](../papers/example-benchmark.md), [project card](../projects/occlusion-tracking.md) | [Outputs index](../papers/outputs-index.md) |
| Write to the benchmark maintainer | [Person card](../../04_people/collaborators/lin-ke.md) | The original notes of the 2026-09-22 meeting |
| Draft or revise the paper | [Writing style card](../../03_cognition/style/writing.md), [project card](../projects/occlusion-tracking.md) | The draft in `~/Papers/occlusion-draft/` |
| Decide whether a comparison runs now or waits | [Heuristic card](../../03_cognition/heuristics/check-benchmark-version-first.md) | The related decision card |

## Evidence boundary

- This page is an index and a summary; numbers and statements are authoritative only on the cards.
- When a card changes, check this page again and set `last_verified` to the date of the check.
