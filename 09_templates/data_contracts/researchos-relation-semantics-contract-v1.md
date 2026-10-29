---
type: data_contract
title: "ResearchOS Relation Semantics Contract v1"
status: ready
created: 2026-06-27
updated: 2026-06-27
tags:
  - data-contract
  - relations
sensitivity: public
exportable_to:
  - public_template
---

# ResearchOS Relation Semantics Contract v1

## Agent Summary

This contract defines relation labels for ResearchOS cards. Relations must distinguish confirmed evidence from candidate interpretation and must not infer private people relationships from weak signals.

## Relation States

| State | Meaning |
| --- | --- |
| `confirmed` | User or source evidence confirms the relation. |
| `candidate` | Plausible relation, not yet confirmed. |
| `needs_evidence` | Relation is useful but lacks support. |
| `local_only` | Relation may be used locally but not exported. |
| `rejected` | User rejected the relation. |

## Relation Types

- `source_of`
- `derived_from`
- `supports`
- `contrasts_with`
- `same_project_family_candidate`
- `coauthor_candidate`
- `talks_about`
- `next_action_for`

## Safety Rule

Authorship proves co-authorship only. It does not prove supervision, friendship, lab membership, seniority, or future collaboration.
