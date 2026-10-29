---
type: workflow
title: "AI Agent Collaboration Workflow"
status: ready
created: 2026-06-27
updated: 2026-06-27
tags:
  - agent-collaboration
  - codex
  - handoff
sensitivity: public
exportable_to:
  - public_template
---

# AI Agent Collaboration Workflow

## Agent Summary

This workflow defines how a user should collaborate with Codex, Codex GUI, or another assistant through ResearchOS. The agent proposes candidate interpretation, candidate edits, and validation steps; the user remains the authority for confirmation and public export.

## Chain

```text
User intent -> context route -> candidate output -> inbox/handoff -> validation -> user confirmation -> durable Markdown
```

## Agent Responsibilities

- classify the task;
- state evidence boundary;
- read minimal context;
- create candidate cards or diffs;
- mark local-only and public-safe boundaries;
- run available validation after edits;
- ask confirmation questions instead of inventing missing facts.

## User Responsibilities

- confirm or reject candidate judgments;
- provide missing source paths;
- decide public export boundary;
- review sensitive people and submitted/unpublished material.

## Handoff Packet

```text
Task:
Context already read:
Source files:
Target files:
Sensitivity/export boundary:
Expected output:
Validation:
Open questions:
```

## Failure Modes

- Agent reads too much and exposes private context.
- Agent treats generated dashboard data as canonical truth.
- Agent writes public-facing text from local-only material.
- Agent upgrades candidates without user confirmation.
