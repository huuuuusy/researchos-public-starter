---
type: decision
title: Run the heavy-occlusion comparison after benchmark version 2 (fictional)
date: 2026-09-22
status: active
related_projects:
  - 01_knowledge/projects/occlusion-tracking.md
related_papers:
  - 01_knowledge/papers/example-benchmark.md
related_people:
  - 04_people/collaborators/lin-ke.md
sensitivity: internal
updated: 2026-09-22
---

# Run the heavy-occlusion comparison after benchmark version 2 (fictional)

## Agent Summary

The heavy-occlusion comparison of methods A and B waits until version 2 of the Example Occlusion Benchmark is released, instead of running on version 1 first. The main risk is that version 2 comes after the paper's target date, so there is a fallback on 11-15. Read this card when rescheduling the occlusion experiments. The decision is fictional and only shows how a decision card is written.

## Background (fact)

At the online meeting on 2026-09-22, Lin Ke said version 2 will raise the heavy-occlusion threshold from 60% to 70% and is expected before the end of the year. See the [meeting card](../06_active_context/meetings/2026-09-22-benchmark-sync.md).

## The question

Run the heavy-occlusion comparison now, or wait for version 2?

## Options

1. Run it on version 1 now and again when version 2 is out.
2. Re-split the version 1 data at a 70% threshold ourselves.
3. Wait for version 2.

## Choice and reasons

Option 3. Option 1 runs everything twice, and the version 1 results would not end up in the paper. Option 2 gives a split nobody else's results can be compared with.

## Risks accepted

The paper's target date is 2026-12-01 and version 2 may be late. Fallback: if version 2 is not out by 11-15, run on version 1 and state the threshold in the paper.

## Expected outcome

Version 2 is released by mid-November and the comparison runs once.

## Actual outcome

(To be filled in afterwards.)

## Evidence boundary

- This card records: the options at the time and the reasons for the choice.
- The grounds are spoken information; neither the release date nor the threshold of version 2 is confirmed in writing.
