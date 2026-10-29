---
type: card_level_example
title: "Plan Card Levels"
status: reference
project_maturity: I2_active_mount
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
  <strong>English</strong> | <a href="onboarding-plan-card-levels.zh.md">中文</a>
</p>

# Plan Card Levels

This example shows how a plan card matures after person, paper, talk, and collaborator cards exist.

## Level 1: Seed Plan Card

```yaml
card_type: plan
maturity: 1
title: Build the first five ResearchOS onboarding cards
status: idea
source_materials:
  - onboarding-intake-note-example.md
objective: Help a new user create a person card, paper card, talk card, collaborator card, and plan card.
known:
  - User wants a step-by-step onboarding path.
  - Existing demo cases can be disabled.
missing:
  - Exact files and validation checks.
  - Dashboard smoke-check route.
next_action: Convert this idea into a scoped plan with outputs and checks.
```

## Level 2: Scoped Plan Card

```yaml
card_type: plan
maturity: 2
title: Build the first five ResearchOS onboarding cards
status: scoped
objective: Create public-safe onboarding examples that show which sources to register and how cards mature.
inputs:
  - user intake note
  - fictional paper metadata
  - fictional talk metadata
  - collaborator candidate extracted from authorship
outputs:
  - person card levels
  - paper card levels
  - talk card levels
  - collaborator card levels
  - plan card levels
validation_checks:
  - generated public starter data includes onboarding examples when cases are enabled
  - generated record count becomes zero when cases are disabled
  - public docs contain no secrets, local paths, or real sensitive people
blockers:
  - Need user confirmation before using any real personal material.
```

## Level 3: Operational Plan Card

```yaml
card_type: plan
maturity: 3
title: Build the first five ResearchOS onboarding cards
status: operational
owner: public starter maintainer
execution_order:
  - create paired English and Chinese onboarding examples
  - update public starter index and user manual
  - regenerate public starter data
  - run runtime, provider, package, boundary, and whitespace checks
  - verify case-disable behavior
agent_handoff:
  prompt: Update public-safe onboarding examples without adding real personal data.
  allowed_files:
    - 08_exports/public_starter/onboarding-*.md
    - docs/user-manual.en.md
    - docs/user-manual.zh.md
  forbidden:
    - real CVs
    - real unpublished papers
    - local runtime logs
    - provider credentials
validation:
  commands:
    - python3 scripts/build_public_starter_data.py --write
    - python3 scripts/build_public_starter_data.py --disable-cases
update_trigger: Revise when a new card type or onboarding surface is added.
```

## Agent Summary

A three-level plan card example showing how a vague onboarding idea becomes a scoped implementation plan and then an operational handoff card.
