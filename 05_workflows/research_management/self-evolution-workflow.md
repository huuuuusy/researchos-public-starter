---
type: workflow
title: "Self Evolution Workflow"
status: ready
created: 2026-06-27
updated: 2026-06-27
tags:
  - self-evolution
  - system-audit
  - maintenance
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="self-evolution-workflow.zh.md">中文</a>
</p>

# Self Evolution Workflow

## Agent Summary

This workflow defines how ResearchOS audits and improves itself. Self-evolution is not automatic rewriting. It is a candidate diagnosis of gaps, stale material, confusing entrypoints, missing templates, weak workflows, and public-boundary risks.

## Diagnosis Axes

1. Material understanding.
2. Research judgment and project structure.
3. Relationship and people boundary.
4. External demand response.
5. Product and documentation clarity.
6. Safety/export boundary.

## Output Format

```text
Current version diagnosis:

Coverage gaps:

Opportunities:

Priority:
1. P0
2. P1
3. P2

Candidate changes:

Requires user confirmation:

Validation plan:
```

## Directly Allowed Low-Risk Changes

- improve docs;
- add templates;
- add workflow descriptions;
- clarify public-safe examples;
- add validators or smoke checklists.

## Must Ask First

- deleting or moving large material sets;
- changing identity or stable memory;
- exporting private/local-only content;
- writing public-facing claims from submitted/unpublished material.
