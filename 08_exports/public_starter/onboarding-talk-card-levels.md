---
type: card_level_example
title: "Talk Card Levels"
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
  <strong>English</strong> | <a href="onboarding-talk-card-levels.zh.md">中文</a>
</p>

# Talk Card Levels

This example starts after the user registers one public talk page, slide deck, local path clue, or summary.

## Level 1: Seed Talk Card

```yaml
card_type: talk
maturity: 1
title: From Notes to Confirmed Research Memory
status: candidate
source_materials:
  - onboarding-intake-note-example.md
known:
  - The user identifies this as the first representative talk.
  - It appears to translate the paper into a workflow narrative.
missing:
  - Slide deck has not been checked.
  - Audience and date need confirmation.
  - Reusable talk claims are not confirmed.
next_action: Verify talk date, audience, and public source.
```

## Level 2: Sourced Talk Card

```yaml
card_type: talk
maturity: 2
title: From Notes to Confirmed Research Memory
status: sourced
date: 2026-04-18
audience: Fictional graduate research methods seminar
public_source: https://example.org/talks/confirmed-research-memory
linked_paper: onboarding-paper-card-levels.md#level-2-sourced-paper-card
key_message: Research notes should move through evidence, candidate interpretation, confirmation, and export checks.
reusable_sections:
  - Why raw notes are not confirmed memory.
  - What a Level 1 card should contain.
  - How a dashboard helps review but does not become the authority.
evidence_boundary: Based on public talk page and user-provided summary; no transcript audit yet.
next_action: Ask whether this talk can be used as the first public explanation of the workflow.
```

## Level 3: Operational Talk Card

```yaml
card_type: talk
maturity: 3
title: From Notes to Confirmed Research Memory
status: operational
public_source: https://example.org/talks/confirmed-research-memory
confirmed_use:
  - Introductory public explanation of the ResearchOS card workflow.
  - Teaching example for turning papers into user-facing system cards.
  - Source for the first public project pitch.
linked_cards:
  person: onboarding-person-card-levels.md#level-3-operational-person-card
  paper: onboarding-paper-card-levels.md#level-3-operational-paper-card
  plan: onboarding-plan-card-levels.md#level-2-scoped-plan-card
export_ready_assets:
  - public talk summary
  - three-slide outline
  - reusable explanation of card maturity
update_trigger: Revise after new recording, audience feedback, or slide update.
```

## Agent Summary

A three-level talk card example showing how a public talk becomes a sourced communication asset and then an operational explanation surface.
