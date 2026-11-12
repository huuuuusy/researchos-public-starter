---
type: work_state
title: "Attention schedule"
status: runtime
created: YYYY-MM-DD
updated: YYYY-MM-DD
sensitivity: internal
schema_id: researchos-attention-schedule-v1
---

<!-- How to use (delete when done)
Copy this file to 06_active_context/work_state/attention-schedule.md inside your vault (the folder you pass to ros --root).
ros attend <commitment> today|tomorrow|date|park|complete-step prints the entry for that commitment; paste it at the end of the file, or in place of the commitment's existing block.
ros today reads this file. In the public starter ros never writes it: you, or the assistant once you say so, paste the entries.
-->

# Attention schedule

## Agent Summary

Short-term attention only: which commitment to look at on which day, which ones are parked until a review date, and which ones have finished their current step. Facts and judgments stay in the commitment list (`06_active_context/research-portfolio.md`) and cards; nothing here changes a commitment's state, deadline or next step.

## Entry format

One block per commitment. It starts with a heading made of `research_portfolio:` and the commitment id, and has one value per line. `ros attend` prints the whole block; copy it as printed rather than typing it. The fields are:

- `attention_date`: the day to look at the commitment (YYYY-MM-DD); empty while it is parked.
- `review_date`: for a parked commitment, the day it comes back to decide; may be empty.
- `today_order`: its place within Today; 0 means no particular order.
- `status`: one of scheduled, paused, waiting, needs_next_step, unscheduled.
- `completed_step_hash`: written by `complete-step`; it stays valid until the commitment's next step changes.
- `updated_at` and `last_action`: when and through which action the entry last changed.

A filled-in block for a fictional commitment (the angle brackets stand for the real id, so ros ignores this example):

```markdown
### research_portfolio:<commitment-id>

- provider_id: research_portfolio
- item_id: <commitment-id>
- attention_date: 2026-09-21
- review_date:
- today_order: 0
- status: scheduled
- completed_step_hash:
- updated_at: 2026-09-21T09:00:00+01:00
- last_action: schedule
```

## Evidence boundary

- This file records where attention goes, not what is true. A date here is not a deadline, and a parked commitment is not abandoned; both live in the commitment list.
- An entry whose heading does not match its `provider_id` and `item_id`, or whose id is not a commitment id, is ignored.
- Removing an entry returns the commitment to unscheduled; ros keeps no other copy of it.

## Items

Paste entries below this line.
