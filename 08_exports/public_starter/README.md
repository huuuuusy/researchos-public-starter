---
type: markdown
title: "Public Starter Demo Materials"
status: reference
created: 2026-06-26
updated: 2026-10-29
tags:
  - public-starter
  - demo-index
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="README.zh.md">中文</a>
</p>

# Public Starter Demo Materials

This directory contains fictional demo materials for ResearchOS Public Starter: the Dashboard's demo agenda, the first-run guide and card examples. The examples help a new user understand what source to register first, how cards are written and how card maturity changes. Your own material does not go here; it goes in the git-ignored `personal_vault/`. Registering a source means adding a local Markdown summary, path clue, or public link; the dashboard does not upload or transmit source files.

These files do not represent real research projects, real people, real papers, real collaborators, or content from any non-public working system.

## Recommended First Path

1. Follow `onboarding-step-by-step.md`, which goes from the demo to your own `personal_vault/`.
2. Inspect `onboarding-intake-note-example.md`.
3. Compare the Level 1, Level 2, and Level 3 card examples:
   - `onboarding-person-card-levels.md`
   - `onboarding-paper-card-levels.md`
   - `onboarding-talk-card-levels.md`
   - `onboarding-collaborator-card-levels.md`
   - `onboarding-plan-card-levels.md`
4. Read `onboarding-card-maturity-rubric.md` to understand when a card is only a draft and when it becomes operational.
5. Use `../../09_templates/standard-agent-prompts.en.md` when asking Codex or another assistant to create each card.
6. Optionally, run the Dashboard demo and inspect the fictional agenda.

## Files

| File | Description |
| --- | --- |
| `onboarding-step-by-step.md` | First-run path: the scheduler demo, one loop in an agent client, a personal vault with one commitment and one card, and the optional personal-vault Dashboard. |
| `demo-research-agenda.md` | The six fictional agenda items that the Dashboard demo shows, set on a fixed fictional date. |
| `onboarding-intake-note-example.md` | Example answers to the first intake note. |
| `onboarding-card-maturity-rubric.md` | General Level 1, Level 2, and Level 3 maturity criteria. |
| `onboarding-person-card-levels.md` | Personal profile card progression. |
| `onboarding-paper-card-levels.md` | Paper card progression. |
| `onboarding-talk-card-levels.md` | Talk card progression. |
| `onboarding-collaborator-card-levels.md` | Collaborator card progression extracted from a paper. |
| `onboarding-plan-card-levels.md` | Research plan card progression. |
The earlier `fake-*`, `walkthrough`, and `example-original-developer-*` files were hard-deleted after the `d4169c3` cloud checkpoint. Git history preserves their provenance; the current working tree intentionally exposes only the supported onboarding path.

## Case Toggle

These cases feed the public demo projection by default. A personal vault never shows them, so you do not need to disable them to use your own material. Maintainers can switch them off as described in Section 5 of the User Manual; the files stay as reference-only placement guides.

## Agent Summary

A public-safe demo index that routes first-time users from the fictional demo to their own `personal_vault/`, then to card creation and card maturity.
