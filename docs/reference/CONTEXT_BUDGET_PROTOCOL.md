---
type: protocol
title: "ResearchOS Public Context Budget Protocol"
status: ready
created: 2026-06-27
updated: 2026-07-10
tags:
  - context-budget
  - token-efficiency
  - agent-protocol
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="CONTEXT_BUDGET_PROTOCOL.zh.md">中文</a>
</p>

# Context Budget Protocol

## Agent Summary

This file defines the low-token reading protocol for ResearchOS Public Starter. Agents should first decide whether repository context is needed at all, then read in layers: route first, summary second, task Markdown third, and evidence only when the task requires verification. This preserves accuracy while reducing context noise and avoiding unnecessary exposure of local-only material.

## Five-Level Reading Ladder

| Level | Purpose | Typical files |
| --- | --- | --- |
| L-1 No-read triage | Decide whether the request needs repository context. | No files. |
| L0 Route | Determine task type and safety boundary. | `AGENTS.md`, one route file. |
| L1 Summary | Get a low-token stable summary. | Frontmatter, `Agent Summary`, context capsules. |
| L2 Task file | Read the specific workflow/template needed. | One workflow, one template, one case. |
| L3 Evidence | Verify facts and source details. | Source notes, audits, raw material paths, explicit evidence. |

## Budget Modes

| Mode | Use when | Read depth |
| --- | --- | --- |
| `quick` | Short answer, routing, next step. | L-1-L1 |
| `standard` | Normal diagnosis, writing, planning. | L0-L2 |
| `evidence` | High-risk claim or formal output. | L0-L3 |
| `export` | Public or external context package. | L0-L1 plus safe-export policy |

Default to `quick`. Use `standard` only when creating or updating a card, plan, or workflow. Use `evidence` only when the output depends on verified facts. Use `export` when preparing public-facing or shareable context.

## Progressive Context Contract

Budget modes are initial-pack limits, not instructions to preload every candidate file.

| Mode | Initial pack | File cap | Estimated total ceiling | Expand only when |
| --- | --- | ---: | ---: | --- |
| `quick` | One primary task file or exact target. | 1 repository file | About 10k | The first file cannot answer a named gap. |
| `standard` | Quick plus a few task-specific workflows/templates. | 5 repository files | About 35k | A missing judgment, state, or workflow is named. |
| `evidence` | Standard plus targeted source/audit/checklist files. | 8 repository files | About 60k | A verification question or conflict is named. |
| `export` | Quick plus safe-export policy and target brief. | 3 repository files | About 20k | A public boundary needs checking. |

When an agent environment already loaded `AGENTS.md`, do not reread it or replay the entry protocol. If the user supplies an exact source or target path, read that file first and count it against the current limit. If either the file cap or estimated token ceiling is exceeded, split the work into question-specific batches instead of loading the full list.

For a continuing task, reuse the previous context receipt. Do not reread unchanged entry files, summaries, or task files; read only changed or newly required files. Across sessions, use a short resume packet containing the task, last judgment, open questions, paths already used, and changed inputs instead of replaying the full chat.

## Hard Token Controls

- Do not read `README.md` just because it is present; it is a human overview, not the default agent context.
- Do not read both English and Chinese paired files unless the task is translation, bilingual QA, or documentation sync.
- Do not read `dashboard/data/researchos-dashboard.json` unless debugging dashboard state or checking generated demo data.
- Do not read the full user manual unless the user asks for a complete explanation.
- Do not read all templates; read only the matching template.
- Before exceeding a first-pass limit in the Progressive Context Contract table, name the gap and explain what each added file will resolve.
- A directory is not a selected evidence item. Evidence mode must resolve to exact files or an exact source path supplied by the user.

## Language Budget Rule

One language counts as the active context. Do not read both English and Chinese versions of the same Markdown file unless the task is translation, bilingual QA, or documentation synchronization. When `content_language` is `en`, prefer base English files. When `content_language` is `zh-CN`, prefer `.zh.md` files when they exist.

## File Design Requirement

Durable ResearchOS files should include:

```text
## Agent Summary
## When to Read
## Do Not Use For
## Evidence Boundary
## Related Files
```

The `Agent Summary` should allow an agent to route the file without reading the whole document.

## Escalation Questions

Before reading deeper, ask:

1. Does the task really need more detail?
2. Is the Agent Summary enough?
3. Would deeper reading touch sensitive/local-only material?
4. Did the user ask for evidence verification?
5. Will the output become formal or public-facing?

If not, stay at the lower level.

## Reporting Requirement

When useful, report:

```text
Reading level:
Initial context:
Added context and reason:
Context not read:
Evidence boundary:
Escalation needed:
```
