---
type: project
title: Occlusion-robust tracking (fictional)
status: active
project_maturity: I2_active_mount
role: First author; owns the method comparison and the paper's claim
related_people:
  - 04_people/collaborators/lin-ke.md
related_papers:
  - 01_knowledge/papers/example-benchmark.md
sensitivity: internal
updated: 2026-09-22
---

# Occlusion-robust tracking (fictional)

## Agent Summary

Compares methods A and B for tracking under occlusion, aiming at a paper. On the standard split A beats B; heavy occlusion has not been measured and waits for version 2 of the benchmark. Read this card to plan experiments, write the paper or answer what A is better at; do not use it to report numbers externally, the experiment log is authoritative. The project is fictional and only shows how a project card is written.

## Core question

Does method A still beat method B under heavy occlusion?

## Current state (2026-09-22)

- The standard-split comparison is done.
- The heavy-occlusion comparison is on hold until version 2 of the benchmark; the reason is in the [decision card](../../02_decisions/2026-09-22-wait-for-benchmark-v2.md).

## Results so far (fact)

- Standard split: A 71.2, B 68.4 (experiment log run-0915, 2026-09-15).
- Heavy occlusion: not measured yet.

## People and materials

- Benchmark: [Example Occlusion Benchmark](../papers/example-benchmark.md), maintained by [Lin Ke](../../04_people/collaborators/lin-ke.md).
- Direction entry: [occlusion tracking summary](../capsules/occlusion-tracking-capsule.md).

## To verify

- Does A's advantage come from how it handles occlusion or from better initialisation? The current results cannot tell these apart.

## Evidence boundary

- This card summarises: the project question, current progress and one set of standard-split results.
- Not checked: whether run-0915 used the same random seeds as B.
- Check before formal use (not read by default): the experiment log `~/Experiments/occlusion/run-0915/`.
