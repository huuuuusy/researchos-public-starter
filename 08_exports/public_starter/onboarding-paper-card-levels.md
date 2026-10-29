---
type: card_level_example
title: "Paper Card Levels"
status: reference
created: 2026-06-26
updated: 2026-06-26
tags:
  - public-starter
  - onboarding-demo
  - card-maturity
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="onboarding-paper-card-levels.zh.md">中文</a>
</p>

# Paper Card Levels

This example starts after the user registers one representative paper source, local path clue, or summary.

## Level 1: Seed Paper Card

```yaml
card_type: paper
maturity: 1
title: Calibrated Memory Workflows for Human-AI Research Notes
status: candidate
source_materials:
  - onboarding-intake-note-example.md
authors:
  - Sue
  - Collaborator A
  - Collaborator B
known:
  - The user says this is the first representative paper to read.
  - The paper is connected to ResearchOS-style confirmed memory workflows.
missing:
  - Full abstract has not been checked.
  - Venue and public URL need verification.
  - Claims should not be reused yet.
do_not_infer:
  - The strength of contribution.
  - The exact role of each author.
  - Any private collaboration relationship.
next_action: Verify public metadata and read the abstract.
```

## Level 2: Sourced Paper Card

```yaml
card_type: paper
maturity: 2
title: Calibrated Memory Workflows for Human-AI Research Notes
status: sourced
public_source: https://example.org/papers/calibrated-memory-workflows
year: 2026
authors:
  - Sue
  - Collaborator A
  - Collaborator B
summary: A fictional paper arguing that AI-assisted research memory should separate source material, candidate interpretation, human confirmation, and reusable claims.
contribution_candidates:
  - Defines card maturity as an audit surface.
  - Shows why generated notes should not become confirmed memory automatically.
  - Proposes public-safe export checks before sharing.
collaborator_candidates:
  - name: Collaborator A
    evidence: co-author on this fictional paper
    maturity: 1
  - name: Collaborator B
    evidence: co-author on this fictional paper
    maturity: 1
evidence_boundary: Based on metadata and abstract only; no full-paper claim audit yet.
next_action: Ask the user which claims are safe to reuse in profile and talk cards.
```

## Level 3: Operational Paper Card

```yaml
card_type: paper
maturity: 3
title: Calibrated Memory Workflows for Human-AI Research Notes
status: operational
public_source: https://example.org/papers/calibrated-memory-workflows
confirmed_use:
  - Supports the user profile theme of human-confirmed AI assistance.
  - Can be linked from the talk card as the technical foundation.
  - Can seed the plan card for a public-safe starter study.
reusable_claims:
  - Research memory systems should separate evidence, interpretation, confirmation, and export.
  - Card maturity should be visible so weak notes do not masquerade as established knowledge.
linked_cards:
  person: onboarding-person-card-levels.md#level-3-operational-person-card
  talk: onboarding-talk-card-levels.md#level-2-sourced-talk-card
  collaborator_candidates:
    - onboarding-collaborator-card-levels.md#level-1-candidate-collaborator-card
validation:
  - Public URL checked.
  - Abstract and author list checked.
  - Reusable claims confirmed by user.
update_trigger: Revise after full-paper reading, citation update, or venue status change.
```

## Agent Summary

A three-level paper card example showing how one registered paper source becomes metadata, collaborator candidates, reusable claims, and linked ResearchOS context.
