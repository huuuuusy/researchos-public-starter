---
type: workflow
title: "Task to Context Matrix"
status: ready
created: 2026-06-27
updated: 2026-07-10
tags:
  - task-routing
  - context-budget
  - agent-protocol
sensitivity: public
exportable_to:
  - public_template
---

# Task to Context Matrix

## Agent Summary

This matrix routes common ResearchOS tasks to the smallest useful context. Each cell is a candidate pool, not a preload list: start with one primary task file or exact target, add only the workflow/template that closes a named gap, and escalate to exact evidence files only for a verification question.

## Matrix

| Task | Start with | Then read | Output |
| --- | --- | --- | --- |
| First onboarding | User Manual Section 2, onboarding guide | `markdown-skill-format`, standard prompts | first profile/paper/talk/plan cards |
| New material | `WHERE_TO_PUT_NEW_MATERIALS` | material intake, lifecycle standard | M1 registration |
| Paper card | paper template | standard prompt 2 | M1/M2 paper card |
| Collaborator candidates | person template | standard prompt 3 | candidate person cards |
| Project/relation card | project template | group composition standard | candidate relation/project card |
| Plan card | project template | standard prompt 8 | scoped plan card |
| External request | external demand workflow | relevant assets and templates | fit judgment + response stance |
| Relationship opportunity | relationship opportunity workflow | person/project/paper templates | candidate opportunity route |
| Public export | safe export policy | safe export template | public-safe context pack |
| System cleanup | self-evolution workflow | system reference, templates | candidate improvements |
| Dashboard/provider use | operations guide | agent protocol | local execution instructions |

## Default Escalation

Use `quick` for routing (1 file), `standard` for normal card creation (up to 5 first-pass files), `evidence` for formal claims (up to 8 targeted files), and `export` for public-facing packages (up to 3 files). Reuse the prior context receipt in a continuing task and read only changed or newly required files.
