---
type: meeting
title: 2026-09-22 benchmark protocol call (fictional)
date: 2026-09-22
participants:
  - Me
  - 04_people/collaborators/lin-ke.md
related_projects:
  - 01_knowledge/projects/occlusion-tracking.md
related_papers:
  - 01_knowledge/papers/example-benchmark.md
source: ~/Notes/2026-09-22-benchmark.txt (on this computer, not in the vault)
sensitivity: sensitive
updated: 2026-09-22
---

# 2026-09-22 benchmark protocol call (fictional)

## Agent Summary

An online meeting with Lin Ke. The main point is that version 2 of the Example Occlusion Benchmark raises the heavy-occlusion threshold from 60% to 70%, so the heavy-occlusion comparison of methods A and B waits for version 2. Read this card when scheduling the occlusion experiments or updating the benchmark card; do not quote Lin Ke from it, the original notes are authoritative. The meeting is fictional and only shows how an meeting card is written.

## Record (fact)

- When: 2026-09-22, online, 30 minutes.
- Participants: me, Lin Ke.
- Material: meeting notes on this computer; the path is in the frontmatter `source`.

## What was said (fact, by speaker)

- Lin Ke: version 2 raises the heavy-occlusion threshold from 60% to 70%, so some "heavy" samples in version 1 become "medium".
- Lin Ke: version 2 is expected before the end of the year, with the same split file format.
- Me: presented the current results of A against B (standard split, 71.2 vs 68.4).

## My view

Running the heavy-occlusion comparison on version 1 now means running it again as soon as version 2 is out, so it waits. The standard-split results are not affected by this change.

To keep this view as a durable judgment, propose it with `ros propose judgment`; it is written into a card only after I confirm it in my terminal.

## Assistant's additions (not confirmed by me)

- With a higher threshold the medium level gets more samples, which may shrink A's advantage under medium occlusion. This is a guess with no data.

## Decided

- The heavy-occlusion comparison waits for version 2. Reasons and fallback are in the [decision card](../../02_decisions/2026-09-22-wait-for-benchmark-v2.md).

## Action items

- Me: change the next_step of commitment `occlusion-paper` to "When version 2 is out, compare A and B on the heavy-occlusion split".
- Me: update the [benchmark card](../../01_knowledge/papers/example-benchmark.md) when version 2 is released.
- Lin Ke: send the protocol text once it is final (agreed verbally).

## Risks

- If version 2 comes after 11-15, the paper's 12-01 target date cannot be met.

## To verify

- The release date is only a spoken "before the end of the year".
- Check the 70% threshold against the version 2 protocol text when it is out.

## Evidence boundary

- This card summarises: the parts of the meeting notes about the benchmark protocol.
- Not checked: whether what Lin Ke said is the final protocol.
- Check before formal use (not read by default): the original meeting notes and the version 2 protocol text.
