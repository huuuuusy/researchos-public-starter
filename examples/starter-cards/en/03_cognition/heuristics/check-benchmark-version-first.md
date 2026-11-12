---
type: heuristic
title: Check the benchmark version before comparing (fictional)
domain: Experimental evaluation
confidence: medium
status: provisional
related_examples:
  - 02_decisions/2026-09-22-wait-for-benchmark-v2.md
sensitivity: internal
updated: 2026-09-22
---

# Check the benchmark version before comparing (fictional)

## Agent Summary

A working habit: before running a method comparison, check which protocol version of the benchmark is in use and whether it is about to change. Read this card when planning experiments or deciding which comparison runs first; it is a rule of thumb, not a requirement. The heuristic is fictional and only shows how a card in the cognition layer is written.

## Rule

Before comparing, check which protocol version the benchmark uses and whether it will change soon. If it will, find out what changes, then decide whether to run now or wait.

## Why

Once the split changes, results on the old version cannot be compared with the new one, and they have to be run again.

## When to use

- Someone else maintains the benchmark and it is still being updated.
- The comparison will go into a paper.

## When not to use

- A quick check that a method runs at all.
- A benchmark that has been frozen for years.

## Examples

- On 2026-09-22 the heavy-occlusion comparison was held for benchmark version 2; see the [decision card](../../02_decisions/2026-09-22-wait-for-benchmark-v2.md).

## Risks

- Waiting too long holds up the work, so every wait gets a fallback date.

## Evidence boundary

- One example supports this habit so far, so `confidence` is medium and `status` is provisional. Change it to stable once more examples show it helps.
