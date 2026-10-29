---
type: workflow
title: "New Project Intake Workflow"
status: ready
created: 2026-06-27
updated: 2026-06-27
tags:
  - new-project
  - project-intake
  - active-context
sensitivity: public
exportable_to:
  - public_template
---

# New Project Intake Workflow

## Agent Summary

This workflow handles early ideas before they become stable projects. A new idea, collaborator suggestion, external opportunity, or student-style project should first become a short intake card, not a confirmed project page. The `I` axis means incubation; `P0-P3` is reserved for portfolio priority. Legacy `P0_temp_analysis` values may be read as aliases, but new records use `I0-I3`.

## Status Flow

| Status | Meaning |
| --- | --- |
| I0_assessment | Temporary idea; not yet a project. |
| I1_sandbox | Worth a small sandbox or one-page framing. |
| I2_active_mount | Active enough to connect to current work. |
| I3_independent_project | Mature enough to become an independent project area. |
| I_hold | Keep but do not pursue now. |
| I_archive | Retired. |

## Intake Card Fields

Use `09_templates/new-project-intake-card-template.md`.

Minimum fields:

- source type;
- owner;
- project sentence;
- current question;
- material paths;
- relation to existing cards;
- recommended location;
- next step;
- expected deliverable;
- review date;
- promotion signal;
- risk;
- sensitivity note.

## Decision Rule

Do not promote an idea to a stable project until it has a clear problem, source material, next action, and validation condition.
