---
type: card_maturity_rubric
title: "Card Maturity Rubric"
status: reference
created: 2026-06-26
updated: 2026-08-11
tags:
  - public-starter
  - onboarding-demo
  - card-maturity
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="onboarding-card-maturity-rubric.zh.md">中文</a>
</p>

# Card Maturity Rubric

Every ResearchOS card should make its maturity visible. A weak card is allowed, but it must not pretend to be stronger than its evidence.

The three levels below are an onboarding pattern, not one universal runtime code. The Library uses a type-specific primary axis: materials use `M1–M3`, projects use `I0–I3`, relationship records use `R0–R3`, and groups use `G0–G2 / Research mainline`. Project `P0–P3` is priority rather than maturity. See [Card Maturity And Enhancement](../../docs/reference/CARD_MATURITY_AND_ENHANCEMENT.md) for display, enhancement, and compatibility rules.

## Level 1: Seed Card

A Level 1 card is a first capture.

It should contain:

- the card type;
- source material used;
- a short summary;
- what is missing;
- what must not be inferred;
- the next confirmation question.

It should not contain:

- strong claims without evidence;
- assumed relationships;
- hidden private context;
- long-term conclusions.

## Level 2: Sourced Card

A Level 2 card has enough evidence to be useful.

It should contain:

- public source anchors;
- confirmed or clearly marked candidate claims;
- links to related cards;
- an evidence boundary;
- at least one next action or validation check.

It should not claim operational readiness unless the next action is concrete.

## Level 3: Operational Card

A Level 3 card is ready to guide work.

It should contain:

- confirmed scope;
- stable links to related cards;
- reusable claims or decisions;
- explicit exclusions;
- owner or maintainer;
- validation route;
- update trigger.

It should be safe to use in planning, writing, dashboard review, or agent handoff.

## Upgrade Rule

A card upgrades only when evidence, links, and confirmation improve. More text alone does not increase maturity.

## Agent Summary

A maturity rubric for Level 1 seed cards, Level 2 sourced cards, and Level 3 operational cards.
