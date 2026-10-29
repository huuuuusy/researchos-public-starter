---
type: data_contract
title: "ResearchOS Primitive Contract v1"
status: ready
created: 2026-06-27
updated: 2026-06-27
tags:
  - data-contract
  - primitives
sensitivity: public
exportable_to:
  - public_template
---

# ResearchOS Primitive Contract v1

## Agent Summary

This contract defines the minimal primitives used by ResearchOS Public Starter: source, card, relation, candidate, confirmation, action, validation, and export. It keeps agents, dashboard data, and Markdown files aligned.

## Primitives

| Primitive | Meaning |
| --- | --- |
| `source` | Original material or public/local source record. |
| `card` | Structured Markdown representation of a person, paper, talk, project, decision, or plan. |
| `relation` | Evidence-bounded link between cards. |
| `candidate` | Unconfirmed interpretation, action, relation, or writeback. |
| `confirmation` | User decision: accept, revise, reject, defer, or needs evidence. |
| `action` | Next step with owner, target, output, and validation. |
| `validation` | Link check, data build, safe-export check, browser smoke, or human review. |
| `export` | Public-safe or external-agent package. |

## State Rules

- Generated projection is not authority.
- Candidate is not confirmed memory.
- Relation must carry evidence and boundary.
- Export requires public-safe status.
