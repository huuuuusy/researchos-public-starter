---
type: workflow
title: "Asset Type Extension Workflow"
status: ready
created: 2026-06-27
updated: 2026-06-27
tags:
  - asset-extension
  - material-intake
  - dashboard
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="asset-type-extension-workflow.zh.md">中文</a>
</p>

# Asset Type Extension Workflow

## Agent Summary

Use this workflow when a new repeated category such as email, external surveyed papers, peer-review assignments, budget, compute, datasets, or other resources may need ResearchOS support. Start with intent, source authority, sensitivity, lifecycle, pilot cards, template, candidate flow, validation, and public-safety boundary before adding a directory, script, or dashboard surface.

## When This Applies

Use this workflow when the new item is more than a single note:

- it appears repeatedly;
- it has its own lifecycle or status;
- it connects to existing papers, projects, people, talks, plans, or decisions;
- it affects current action, resource allocation, or public/export boundaries;
- users would naturally expect to filter, review, or hand it to Codex.

If the item is one-off, use `material-intake-workflow.md` instead.

## Step 1: Name the Class

Choose a stable `asset_class`. Good names describe the object, not the UI:

- `email_thread`
- `external_paper`
- `review_item`
- `budget_resource`
- `compute_resource`
- `dataset_access`

Avoid names such as `new_tab`, `misc`, `important`, or `box_2`.

## Step 2: Decide the Base Kind

| Question | Base kind |
| --- | --- |
| Is it a source to read? | Material asset |
| Is it something to decide or confirm? | Decision or candidate |
| Is it a current operating constraint? | Resource object |
| Is it a repeated task with stages? | Workflow object |
| Is it mainly a relation between existing cards? | Relation or group object |

## Step 3: Pick the First Location

| New class | Start here | Promote later if needed |
| --- | --- | --- |
| Email thread | `06_active_context/` for action, `02_decisions/` for confirmed decision | `01_knowledge/communications/` only if communication notes become a stable evidence class. |
| External paper | `01_knowledge/literature/` or reading note | Dashboard filter for surveyed vs own papers. |
| Peer-review item | `06_active_context/` for active review, `05_workflows/review_writing/` for process | Review workbench if volume is high. |
| Budget | `06_active_context/resources/` for current state, `02_decisions/` for allocation decisions | Resource dashboard if budget affects many projects. |
| Compute | `06_active_context/resources/` for quota, `02_decisions/` for tradeoffs | Scheduling or capacity workbench if repeated. |

## Step 4: Write 2-3 Pilot Cards

Before adding code, write small Markdown examples. Each pilot card should include:

```yaml
asset_class:
title:
status:
sensitivity:
source_authority:
lifecycle_state:
related_projects:
related_people:
related_materials:
candidate_or_confirmed:
next_action:
validation:
export_boundary:
```

## Step 5: Decide Whether It Deserves a Template

Create a template only if the pilot cards share stable fields. If each card looks different, keep the class as ordinary material intake.

## Step 6: Decide Whether It Deserves Dashboard Support

Use this threshold:

| Support level | Use when |
| --- | --- |
| No dashboard support | Rare or one-off class. |
| Assets filter | The class is useful for discovery but not daily operation. |
| Today card | The class affects current action or blockers. |
| Inbox candidate | The class needs confirmation, review, or Codex handoff. |
| Dedicated surface | The class has many records, repeated actions, and stable validation. |

## Step 7: Validate

For changes to this repository, run:

```bash
python3 scripts/build_public_starter_data.py --write
python3 scripts/check_all_links.py
python3 scripts/validate_runtime_config.py
```

If a new script or dashboard projection is added, also add or update a small validation rule.
