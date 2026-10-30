---
type: workflow
title: "Material Intake Workflow"
status: ready
created: 2026-06-27
updated: 2026-06-27
tags:
  - material-intake
  - research-management
sensitivity: public
exportable_to:
  - public_template
---

# Material Intake Workflow

## Agent Summary

This workflow explains how new material enters ResearchOS. Raw material is not memory. First identify the source, sensitivity, intended use, target layer, and M1 registration. Only after evidence review should the material become a refined card or a cross-card relation.

If the derived output is a bounded presentation, meeting, application, analysis, or revision workbench rather than durable material knowledge, also use the [Derived Work Artifact Lifecycle](derived-work-artifact-lifecycle.md). Keep it current only while it has a consumer and next action; at closeout, distill before archiving.

## Intake Principle

ResearchOS does not need to copy every raw file. It needs a traceable record of source, boundary, interpretation, and next action.

## Step 1: Identify Source

| Source | Default handling |
| --- | --- |
| Public URL, DOI, homepage, preprint | Can be used as public evidence after checking version/status. |
| Local private file | Use locally; mark derived content `local_only`. |
| Submitted or under-review manuscript | Use locally; do not export. |
| User oral note | Treat as user-provided candidate until confirmed. |
| Dashboard upload/file name | Do not assume the file is readable until a real path exists. |

## Step 2: Classify Sensitivity

| Sensitivity | Meaning |
| --- | --- |
| `public` | Safe for demos and this repository. |
| `internal` | Local work material, not automatically public. |
| `sensitive` | People, submission, review, student, grant, or relationship content. |
| `local_only` | May be analyzed locally but not exported. |
| `not_exportable` | Must not enter public-facing output. |

## Step 3: Choose Target Layer

Use `docs/reference/WHERE_TO_PUT_NEW_MATERIALS.md`.

## Step 4: Create M1 Registration

Minimum fields:

```text
material_id:
title:
material_type:
source:
sensitivity:
public_boundary:
why_now:
target_layer:
next_question:
requires_confirmation:
```

## Step 5: Decide Whether to Upgrade

- M1 -> M2 when the material has enough evidence for a refined card.
- M2 -> M3 when it can be connected to another card, project, person, talk, or plan.
- Stay M1 if source, boundary, or relevance is unclear.

## Output Format

```text
Intake judgment:
Source and boundary:
M1 registration:
Suggested target:
Upgrade condition:
Questions for user:
```
