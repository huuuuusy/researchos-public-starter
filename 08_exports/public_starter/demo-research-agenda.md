---
type: demo_research_agenda
title: "Fictional Responsibility-Aware Research Agenda"
status: active_demo
sensitivity: public
reference_date: 2026-08-11
exportable_to:
  - public_template
tags:
  - demo
  - research-agenda
  - responsibility
  - fictional-data
---

# Fictional Responsibility-Aware Research Agenda

## Agent Summary

This fictional, public-safe authority example demonstrates the ResearchOS responsibility primitive: accountable lead work is counted separately from supporting work, and commitment state, priority, next action, and freshness come from one ledger. It contains no maintainer projects, people, deadlines, paths, or private execution state.

## Answer Contract

- “How many mainlines do I own?” counts only `responsibility: lead` plus `state: mainline`.
- Support work never becomes lead work merely because the user reviews or cares about it.
- Waiting, queued, paused, conditional, and closed items do not enter the active-lead count.
- `lifecycle_phase` records where the project is; the first screen shows only actionable attention, while Assets preserves every lifecycle state.
- A stale item must be reviewed before its old active label is trusted.
- Missing or invalid responsibility fails closed into `unclassified`; it never defaults to lead.
- Counts are complete only inside a declared, current coverage receipt. Otherwise the system reports registered items only.

## Coverage Receipt

- coverage_scope: The six fictional agenda items in this public demonstration file
- coverage_status: reviewed
- coverage_reviewed: 2026-07-26
- coverage_stale_after_days: 30
- coverage_sources: 08_exports/public_starter/demo-research-agenda.md
- coverage_candidates:
- coverage_exclusions: Real maintainer projects, people, deadlines, paths, and private execution state

## Responsibility Items

### Revision Claim Closeout

- id: demo-revision-claim-closeout
- responsibility: lead
- accountable_owner: You
- role_summary: Final claim and submission decision
- state: mainline
- schedule_bucket: today
- schedule_label: Close out first
- schedule_order: 10
- attention_state: today
- attention_date: 2026-08-11
- priority: P0
- project_maturity: I3_independent_project
- related_people: Methods Collaborator; Evidence Reviewer
- assistant: Chosen assistant
- lane: paper-revision
- output_type: paper-revision
- lifecycle_phase: rebuttal
- current_stage: The response structure is ready; one claim boundary still needs researcher judgment
- progress_done: 3
- progress_total: 4
- progress_label: 3 of 4 bounded milestones complete
- next_step: Review the disputed claim, freeze what the evidence supports, and prepare the final response paragraph
- self_action: Decide the final claim boundary and accept or reject the revised wording
- ai_action: Compare the claim with cited evidence and prepare a bounded paragraph candidate
- success_gate: The researcher accepts wording that does not exceed the evidence
- target_date: closeout-first
- last_verified: 2026-08-03
- stale_after_days: 14
- source_path: 08_exports/public_starter/demo-research-agenda.md
- merge_rule: Keep the revision obligation separate from new-paper ideas

### Evaluation Pilot Decision

- id: demo-evaluation-pilot
- responsibility: lead
- accountable_owner: You
- role_summary: Go/no-go decision and experiment-scope accountability
- state: mainline
- schedule_bucket: this_week
- schedule_label: This week's decision
- schedule_order: 20
- attention_state: upcoming
- attention_date: 2026-08-12
- priority: P1
- project_maturity: I2_active_mount
- related_people: Evaluation Partner; Methods Collaborator
- assistant: Chosen assistant
- lane: experiment
- output_type: experiment-gate
- lifecycle_phase: experiment_preparation
- current_stage: A small pilot exists, but its decision evidence has not been reviewed
- progress_done: 1
- progress_total: 3
- progress_label: Pilot design complete; evidence review and decision remain
- next_step: Inspect the pilot evidence and make a go/no-go decision before expanding the experiment
- self_action: Decide whether the signal justifies a larger experiment
- ai_action: Summarize evidence, failure cases, and tradeoffs without making the final decision
- success_gate: The researcher records a supported go/no-go judgment and next gate
- target_date: this-week
- last_verified: 2026-08-03
- stale_after_days: 14
- source_path: 08_exports/public_starter/demo-research-agenda.md
- merge_rule: Do not create a full project until the pilot gate passes

### Collaborator Manuscript Review

- id: demo-collaborator-review
- responsibility: support
- accountable_owner: Collaborator
- role_summary: Review framing and evidence boundaries; no delivery ownership
- state: mainline
- schedule_bucket: this_week
- schedule_label: Support window
- schedule_order: 30
- attention_state: upcoming
- attention_date: 2026-08-14
- priority: P1
- project_maturity: I2_active_mount
- related_people: Manuscript Owner; Evidence Reviewer
- assistant: Chosen assistant
- lane: collaboration
- output_type: paper-revision
- lifecycle_phase: revision
- current_stage: The collaborator owns the manuscript; a bounded review request is active
- next_step: Return a claim-boundary review to the collaborator without taking over the manuscript
- self_action: Review only the requested framing and evidence questions
- ai_action: Prepare a concise review memo from user-selected public-safe sources
- success_gate: The collaborator receives the bounded review and retains the final manuscript decision
- target_date: collaborator-led
- last_verified: 2026-08-03
- stale_after_days: 14
- source_path: 08_exports/public_starter/demo-research-agenda.md
- merge_rule: Supporting work never enters the user's accountable-mainline count

### Submitted Paper Under Review

- id: demo-external-wait
- responsibility: support
- accountable_owner: External team
- role_summary: Respond only when the external decision arrives
- state: waiting
- schedule_bucket: later
- schedule_label: Submitted · under review
- schedule_order: 40
- priority: P1-waiting
- project_maturity: I3_independent_project
- related_people: External Team; Corresponding Author
- assistant: Chosen assistant
- lane: external-obligation
- output_type: research-obligation
- lifecycle_phase: under_review
- activation_trigger: Official reviews, a rebuttal notice, an editorial decision, or a concrete author-team request arrives
- current_stage: The current package has been submitted and no action is available
- next_step: Wait for the external decision; when it arrives, verify the new responsibility and next action
- self_action: Do not create speculative work while waiting
- ai_action: Preserve the state boundary and prepare nothing until new evidence arrives
- success_gate: A real external event creates a verified next action
- target_date: external
- last_verified: 2026-07-25
- stale_after_days: 30
- source_path: 08_exports/public_starter/demo-research-agenda.md
- merge_rule: Waiting does not count as active execution

### Long-Form Draft

- id: demo-long-form-paused
- responsibility: lead
- accountable_owner: You
- role_summary: Author and only person who can reopen the draft
- state: paused
- schedule_bucket: later
- schedule_label: Keep current
- schedule_order: 50
- priority: P1-preserve
- project_maturity: I2_active_mount
- related_people: Writing Partner
- assistant: Chosen assistant
- lane: writing
- output_type: long-form-writing
- lifecycle_phase: paused
- activation_trigger: A specific reader, continuity, or publication issue is identified
- current_stage: The current draft is preserved; no concrete reading problem justifies another pass
- next_step: Reopen only after a specific reader, continuity, or publication trigger
- self_action: Name the concrete trigger or keep the draft unchanged
- ai_action: Preserve the current version and avoid manufacturing work
- success_gate: A specific trigger exists or the author accepts the current version
- target_date: wait-for-author
- last_verified: 2026-07-25
- stale_after_days: 30
- source_path: 08_exports/public_starter/demo-research-agenda.md
- merge_rule: Paused work stays owned but does not count as actively progressing

### Survey Scope Gate

- id: demo-survey-scope-gate
- responsibility: lead
- accountable_owner: You
- role_summary: Decide whether the idea deserves an independent deliverable
- state: conditional
- schedule_bucket: later
- schedule_label: After current closeout
- schedule_order: 60
- deadline: 2026-09-15
- priority: P2
- project_maturity: I0_assessment
- related_people: Methods Collaborator
- assistant: Chosen assistant
- lane: survey
- output_type: survey-paper
- lifecycle_phase: scoping
- current_stage: The topic exists, but independent reader value and overlap are unresolved
- next_step: Compare the proposed survey with existing reviews and decide whether it deserves an independent manuscript
- self_action: Decide whether the survey has a distinct question, audience, and contribution
- ai_action: Prepare a short scope-and-overlap audit from public-safe sources selected by the user
- success_gate: The researcher can state a distinct central question and reader value
- target_date: conditional
- last_verified: 2026-06-30
- stale_after_days: 14
- source_path: 08_exports/public_starter/demo-research-agenda.md
- merge_rule: Prefer reuse over a redundant manuscript

## Boundary

- Every item is fictional.
- The public dashboard projects this file; generated JSON is not authority.
- A personal vault may use the same fields with local private data, but public-demo generation never reads that data.
- Browser actions remain local and reversible; state changes remain candidates until the user confirms writeback.
