---
type: workflow
title: "Material Analysis Lifecycle Standard"
status: ready
created: 2026-06-27
updated: 2026-06-27
tags:
  - material-lifecycle
  - card-maturity
  - research-management
sensitivity: public
exportable_to:
  - public_template
---

# Material Analysis Lifecycle Standard

## Agent Summary

This file defines the M1/M2/M3 lifecycle for ResearchOS materials. M1 registers a material with source and boundary, M2 creates a refined reading or card with evidence, and M3 connects the material across projects, people, talks, and plans. Do not skip M1, and do not promote a card without evidence and export boundary.

## Lifecycle

| Level | Name | Meaning | Minimum output |
| --- | --- | --- | --- |
| M1 | Registered | The material exists, its source and boundary are known. | Intake note or seed card. |
| M2 | Refined read | The material has been interpreted with evidence. | Paper/talk/person/project card with evidence boundary. |
| M3 | Cross-card deepening | The material is connected to other cards or a plan. | Relation/project/plan card with validation check. |

## M1 Requirements

- title or working title;
- material type;
- source path, URL, or local source note;
- sensitivity and export boundary;
- why it matters now;
- proposed target layer;
- next analysis question.

## M2 Requirements

- concise summary;
- core contribution or message;
- evidence used;
- what the material does not prove;
- missing evidence;
- related cards;
- boundary: `public_safe`, `local_only`, or `not_exportable`.

## M3 Requirements

- relation to at least one other card;
- role in a project, theme, collaborator map, talk, or plan;
- candidate vs confirmed relation labels;
- next action;
- validation check;
- export boundary.

## Promotion Rule

A material can move upward only when the new level adds real structure. Writing a longer summary does not make M1 into M2. A relation inferred from title similarity does not make M2 into M3.

## Public Boundary

Private, submitted, under-review, unpublished, person-sensitive, or confidential materials may be analyzed locally, but their derived cards remain `local_only` unless explicitly cleared.
