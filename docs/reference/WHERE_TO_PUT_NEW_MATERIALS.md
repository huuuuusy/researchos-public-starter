---
type: guide
title: "Where to Put New Materials"
status: ready
created: 2026-06-27
updated: 2026-10-29
tags:
  - material-intake
  - repository-maintenance
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="WHERE_TO_PUT_NEW_MATERIALS.zh.md">中文</a>
</p>

# Where to Put New Materials

## Agent Summary

This guide explains where new ResearchOS material should go. Core rule: raw material, derived knowledge, decisions, cognition, people, workflows, active context, exports, and templates are different layers. Do not mix them. Your own material goes in the git-ignored `personal_vault/` inside your clone, which uses the same layer folders. If a material is private, submitted, unpublished, or sensitive, it may be analyzed there, but it must not be placed in the tracked files of this repository.

## Your Own Material Goes in `personal_vault/`

Your own cards live in `personal_vault/`, a folder inside your clone that Git ignores; the layer paths below are relative to it, so a paper note goes in `personal_vault/01_knowledge/` and the current state in `personal_vault/06_active_context/`. The layer folders at the repository root hold this repository's own notes and fictional examples; do not add your material there. Never push a clone that contains real material to a public remote; to version the vault, keep a private copy of the repository without a public remote. To create the vault, follow "Start your own" in [Section 5 of the User Manual](../user-manual.en.md#5-your-own-material).

## One-Line Rule

Raw material stays where it is, in a local source folder outside the repository, and a card records its path; `corpus/` in this repository stays empty. Derived knowledge goes to `01_knowledge/`; decisions to `02_decisions/`; reusable judgment patterns to `03_cognition/`; people context to `04_people/`; workflows to `05_workflows/`; current state to `06_active_context/`; exports to `08_exports/` only after safe-export review; templates to `09_templates/`.

## Placement Table

| Material | Put here | Boundary |
| --- | --- | --- |
| Raw PDF, slides, document, webpage dump | Local source folder outside the repository; the card records the path | Do not treat as confirmed memory. |
| Paper note, material summary, project facts | `01_knowledge/` | Keep source links. |
| Research identity page; direction summaries | `00_identity/research-identity.md`; `01_knowledge/capsules/` | Level-1 entry pages an assistant reads first; each links to cards and states nothing the cards do not. |
| Tradeoff, confirmation, rejected option | `02_decisions/` | Sensitive by default if it involves people or strategy. |
| Mental model, heuristic, writing principle | `03_cognition/`; a mental model in `03_cognition/mental_models/` | Only after repeated or confirmed usefulness. |
| Working-style card: how you do writing, review, a proposal, figures and talks, or mentoring | `03_cognition/style/<task>.md`, one per kind of task | An assistant reads the matching one first; it describes how you work, so the assistant drafts it and writes it only after you agree. |
| Review comments, grant application, academic message, feedback to a mentee | `06_active_context/reviews/`, `grants/` or `messages/`; feedback in `04_people/feedback/` | Start from `review.md`, `grant.md`, `message.md` or `feedback.md` in `09_templates/basic/`, which also has `style.md` and `mental-model.md`. |
| Your limits: material never given to an assistant, things not said outside, rules on AI tools, who approves | `00_identity/boundaries.md` | Start from `09_templates/basic/boundaries.md`; outward tasks read it first. |
| Which outputs may be cited outside, and who did what on each | `01_knowledge/papers/outputs-index.md` and `01_knowledge/papers/author-roles.md` | Start from `outputs-index.md` and `author-roles.md`; read at the evidence level for papers and proposals. |
| Person or collaborator card | `04_people/` | Tracked starter files use fictional or public-safe examples only. |
| Reusable workflow or SOP | `05_workflows/` | Keep generic, not one private project's full history. |
| Current tasks, pending questions, handoff | `06_active_context/` | Short-lived operating state, not full history. |
| Bounded presentation, meeting, application, analysis, or revision work product | Working: `06_active_context/`; closed history: `07_archive/task_artifacts/` | Distill durable content first; archive only if the complete process has independent value. |
| Public-safe demo or context pack | `08_exports/` | Must pass safe export boundary. |
| Template, prompt, data contract | `09_templates/` | Do not fill templates with sensitive real data. |

## Private and Submitted Materials

ResearchOS can process private, submitted, under-review, and unpublished material in `personal_vault/`. Mark derived cards as `local_only` or `not_exportable` unless explicitly cleared. Do not commit those real materials to this repository.

For bounded work products, follow the [Derived Work Artifact Lifecycle](../../05_workflows/research_management/derived-work-artifact-lifecycle.md). Moving a file into an archive never changes its sensitivity or grants public permission.

## When a New Material Becomes a New Category

Do not create a new top-level directory or dashboard tab just because a new material type appears. If a repeated class such as email, external surveyed papers, peer-review assignments, budget, compute, or dataset access needs its own lifecycle, read `05_workflows/research_management/asset-type-extension-workflow.md` and `09_templates/data_contracts/researchos-extension-contract-v1.md`.

Use the extension workflow when the class has repeated records, stable fields, relation links, confirmation needs, or resource-allocation consequences. Otherwise, keep it as ordinary M1 material intake.

## When Unsure

1. Keep raw material where it is.
2. Create a small M1 registration note.
3. Mark sensitivity and export boundary.
4. Ask what question this material answers.
5. Route the derived note to the correct layer.
6. Keep uncertain claims as candidates.
