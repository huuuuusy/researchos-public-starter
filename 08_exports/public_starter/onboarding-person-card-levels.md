---
type: card_level_example
title: "Person Card Levels"
status: reference
relationship_maturity: R2_evidence_linked
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
  <strong>English</strong> | <a href="onboarding-person-card-levels.zh.md">中文</a>
</p>

# Person Card Levels

This example shows how a fictional user profile card can grow from an intake seed to an operational identity card.

## Level 1: Seed Person Card

```yaml
card_type: person
maturity: 1
name: Dr. Sue
status: candidate
source_materials:
  - onboarding-intake-note-example.md
known:
  - Fictional researcher working on human-confirmed AI research workflows.
  - Public homepage and publication profile were provided by the user.
missing:
  - CV evidence has not been reviewed.
  - Representative papers have not been linked.
  - Public-export exclusions need confirmation.
do_not_infer:
  - Institution, employment, collaborators, or advising relationships.
next_confirmation_question: Which public CV or resume summary should be treated as the source of record?
```

## Level 2: Sourced Person Card

```yaml
card_type: person
maturity: 2
name: Dr. Sue
status: sourced
public_anchors:
  homepage: https://example.org/sue
  publication_profile: https://scholar.example.org/sue
  cv_summary: materials/sue-public-cv-summary.md
research_themes:
  - Human confirmation in AI-assisted research workflows.
  - Evidence-bounded memory systems.
  - Public-safe knowledge export.
linked_cards:
  - onboarding-paper-card-levels.md#level-1-seed-paper-card
  - onboarding-talk-card-levels.md#level-1-seed-talk-card
evidence_boundary: Uses only the user-provided public homepage, publication profile, and CV summary.
next_action: Read the first representative paper and connect it to the profile.
```

## Level 3: Operational Person Card

```yaml
card_type: person
maturity: 3
name: Dr. Sue
status: operational
public_positioning: Fictional researcher building human-confirmed AI research workflows with explicit evidence boundaries.
confirmed_themes:
  - Human-confirmed AI assistance.
  - Research memory and card maturity.
  - Public-safe export governance.
representative_outputs:
  - Calibrated Memory Workflows for Human-AI Research Notes.
  - From Notes to Confirmed Research Memory.
linked_cards:
  papers:
    - onboarding-paper-card-levels.md#level-3-operational-paper-card
  talks:
    - onboarding-talk-card-levels.md#level-3-operational-talk-card
  collaborators:
    - onboarding-collaborator-card-levels.md#level-2-sourced-collaborator-card
  plans:
    - onboarding-plan-card-levels.md#level-2-scoped-plan-card
export_boundary:
  allow:
    - public profile summary
    - public paper and talk links
    - fictional collaborator examples
  exclude:
    - private notes
    - student or reviewer material
    - local runtime logs
update_trigger: Upgrade or revise after adding a new confirmed publication, talk, or plan outcome.
```

## Agent Summary

A three-level person card example showing intake seed, sourced profile, and operational identity state.
