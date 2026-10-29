---
type: audit
title: "Public Core Skill Migration Audit"
status: superseded
created: 2026-06-27
updated: 2026-06-27
tags:
  - public-starter
  - migration-audit
  - skill-core
sensitivity: public
exportable_to:
  - public_template
---

# Public Core Skill Migration Audit

> Historical migration receipt. Current users and agents should start from `AGENTS.md`, `README.md`, or Section 2 of `docs/user-manual.en.md`; this audit no longer defines the active route.

## Agent Summary

This audit records the public-safe migration of ResearchOS core skill concepts into the public starter. The public package should not only show a dashboard and demo cases; it must preserve the Markdown skill interface, context-budget protocol, material lifecycle, task routing, card templates, and relation semantics.

## Migrated Core

| Core area | Public files |
| --- | --- |
| Agent use protocol | `docs/reference/AGENT_PROTOCOL.md`, `docs/reference/AGENT_PROTOCOL.zh.md` |
| Context budget | `docs/reference/CONTEXT_BUDGET_PROTOCOL.md`, `docs/reference/CONTEXT_BUDGET_PROTOCOL.zh.md` |
| Material placement | `docs/reference/WHERE_TO_PUT_NEW_MATERIALS.md`, `docs/reference/WHERE_TO_PUT_NEW_MATERIALS.zh.md` |
| Markdown skill format | `09_templates/markdown-skill-format.en.md`, `09_templates/markdown-skill-format.zh.md` |
| Card templates | `09_templates/paper-template.md`, `person-template.md`, `project-template.md`, `talk-template.md`, `decision-template.md`, `context-capsule-template.md` |
| Task templates | `research-expression-task-brief.md`, `new-project-intake-card-template.md`, `safe-export-template.md`, `eval-case-template.md`, `self-evolution-report-template.md`, `memory-update-report-template.md`, `workflow-template.md` |
| Standard prompts | `09_templates/standard-agent-prompts.en.md`, `09_templates/standard-agent-prompts.zh.md` |
| Material lifecycle | `05_workflows/research_management/material-intake-workflow.md`, `material-analysis-lifecycle-standard.md` |
| Task routing | `05_workflows/research_management/task-to-context-matrix.md` |
| Agent collaboration | `05_workflows/research_management/ai-agent-collaboration-workflow.md` |
| Group/relation lifecycle | `05_workflows/research_management/group-composition-lifecycle-standard.md` |
| Project intake | `05_workflows/research_management/new-project-intake-workflow.md` |
| Expression workflow | `05_workflows/research_management/research-expression-engine-playbook.md` |
| Self-evolution | `05_workflows/research_management/self-evolution-workflow.md` |
| Data contracts | primitive, capability, and relation-semantics contracts under `09_templates/data_contracts/` |

## Not Migrated Directly

The following private categories should not be copied into the public starter:

- real private identity, agenda, and non-public research narratives;
- real collaborator, student, reviewer, grant, and relationship records;
- unpublished manuscript details and submission strategy;
- raw corpus, local machine paths, and private runtime logs;
- private distilled memory and project-specific evidence notes.

Where useful, these were replaced with public-safe protocols, templates, fictional cases, or de-identified examples.

## Public Boundary Decision

The public starter may teach users how to analyze private, submitted, under-review, or unpublished material in their own local workspace. It must not include real examples of those materials. Derived cards from such sources default to `local_only` or `not_exportable` unless the user explicitly clears a public-safe version.

## Verification

Validated after migration:

```bash
python3 scripts/build_public_starter_data.py --write
python3 scripts/check_all_links.py
git diff --check
```

Latest observed result: generated public starter data rebuilt, dashboard projection rebuilt, Markdown link check passed, and whitespace check passed.

2026-06-27 new-user smoke audit found and corrected public-specific friction: the startup banner and provider check no longer describe the public starter as a private vault, CLI companion recommendations point to shipped public scripts, dashboard server hints use port `8880`, first-open dashboard language defaults to English when no user preference exists, and governance docs no longer imply that public contributors are missing a private release-gate script, and dashboard maintenance/command surfaces now point only to scripts shipped with the public starter.
