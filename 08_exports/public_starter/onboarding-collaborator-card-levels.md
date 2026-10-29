---
type: card_level_example
title: "Collaborator Card Levels"
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
  <strong>English</strong> | <a href="onboarding-collaborator-card-levels.zh.md">中文</a>
</p>

# Collaborator Card Levels

This example shows how a collaborator card may be proposed from a paper author list. It is deliberately cautious.

## Level 1: Candidate Collaborator Card

```yaml
card_type: person
subtype: collaborator_candidate
maturity: 1
name: Collaborator A
status: candidate
source_materials:
  - onboarding-paper-card-levels.md#level-2-sourced-paper-card
evidence:
  - Listed as a co-author on a fictional public paper.
allowed_claims:
  - Candidate co-author relation.
not_allowed_claims:
  - Personal relationship.
  - Advising relationship.
  - Current collaboration status.
  - Future commitment.
next_confirmation_question: Should this co-author become a confirmed collaborator card in your ResearchOS?
```

## Level 2: Sourced Collaborator Card

```yaml
card_type: person
subtype: collaborator
maturity: 2
name: Collaborator A
status: sourced
public_anchor: https://example.org/collaborator-a
evidence:
  - Co-author on Calibrated Memory Workflows for Human-AI Research Notes.
  - Public homepage confirms broad area: research systems and evaluation.
confirmed_claims:
  - Public co-author on one fictional paper.
  - Relevant to the paper card and plan card.
evidence_boundary: Public co-authorship and public profile only.
next_action: Ask the user whether future outreach or project planning should include this collaborator.
```

## Level 3: Operational Collaborator Card

```yaml
card_type: person
subtype: collaborator
maturity: 3
name: Collaborator A
status: operational
public_anchor: https://example.org/collaborator-a
confirmed_scope:
  - Public co-author relation on one fictional paper.
  - Possible reviewer of public-safe workflow examples.
linked_cards:
  paper: onboarding-paper-card-levels.md#level-3-operational-paper-card
  plan: onboarding-plan-card-levels.md#level-3-operational-plan-card
safe_contact_context:
  - Use only public project framing.
  - Do not include sensitive notes, student information, or unpublished manuscript details.
next_action: Draft a public-safe collaboration check-in only after user confirmation.
update_trigger: Revise after confirmed new paper, meeting note, or explicit user correction.
```

## Agent Summary

A cautious collaborator-card example showing candidate extraction from authorship, sourced public relation, and operational but bounded collaboration context.
