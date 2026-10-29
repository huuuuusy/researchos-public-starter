---
type: data_contract
title: "ResearchOS Extension Contract v1"
status: ready
created: 2026-06-27
updated: 2026-08-06
tags:
  - data-contract
  - extension
  - asset-class
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="researchos-extension-contract-v1.zh.md">中文</a>
</p>

# ResearchOS Extension Contract v1

## Agent Summary

This contract defines the gate for adding a new ResearchOS asset class, material type, resource object, workflow object, dashboard surface, or export target. A new category must declare intent, source authority, lifecycle, relations, candidate flow, save target, validation, and public-safety boundary before it becomes first-class.

## Core Rule

Add a new category only when it changes how the researcher judges, acts, validates, or allocates resources. If it is only another input file, keep it under material intake. If it becomes a repeated operating object, promote it through the extension ladder below.

## Plugin Host v1

`researchos-plugin-v1` is the shared host contract for reviewed public-safe plugins and ignored local manifests. Its schema is [researchos-plugin-v1.schema.json](researchos-plugin-v1.schema.json), reviewed manifests belong in `config/plugins/`, local manifests belong in the Git-ignored `config/plugins.local/`, and `python3 scripts/validate_plugins.py` is the fail-closed gate.

The public starter loads only declarative, public-safe manifests without network, command, canonical-write, private-path, or private-state access. Registry summaries omit source paths and permission details. V1 does not execute arbitrary plugin JavaScript or create new workspaces, result modes, storage owners, or writeback routes.

Existing `researchos-task-extension-v1` descriptors remain the current runtime input. The Plugin Host normalizes them into a `tasks` contribution and verifies output equivalence, so the host contract does not introduce a second task definition or change user-visible routes.

### Candidate Adapter Port

A plugin may register reviewed `candidate_types`, but a manifest does not load the implementation. A statically reviewed first-party adapter owns domain normalization, generation, preview metadata, withdraw/resolve calls, and domain copy. Before a record enters Review it becomes `CandidateEnvelope` v1; Unified Inbox and Codex handoff consume that envelope rather than branching on raw plugin fields.

The first proven implementation is `material_pipeline`, covering material intake, material upgrade, and research scout candidates. It reuses the existing Review, endpoint, storage-key, archive, and confirmation semantics. Disabling it removes its contribution without creating another state system. Public availability does not grant durable writeback: the public server keeps the fail-closed canonical-write boundary.

Candidate adapters must be present in the reviewed runtime registry, behavior-tested, and declared in plugin ownership validation. If adding a candidate type requires a new core Inbox branch, the envelope is incomplete or the change requires C3 kernel review.

### Work Item And Inline Action Port

Plugin v1.1 adds a backward-compatible `work_item_providers` contribution. A provider maps one domain projection into the shared `Project -> current Commitment` shape; it does not create another project database. The kernel owns attention states and action risk language, while the plugin owns domain states, stable identity, responsibility, source references, and next-step content.

Projection reads are not raw access to the Dashboard object. Each manifest projection declares `researchos-projection-envelope-v1`, sensitivity, freshness, and an exact field export map; the host returns `ready / empty / error` and withholds payload on an unknown or denied contract. UI slots declare both a legacy routing alias and one canonical `surface.region` coordinate. Referenced actions must belong to the same canonical surface, so a capability cannot quietly attach a Review or Start mutation to another screen.

If an action declares any v1.1 field, it must declare the complete contract: `confirmation_mode`, `risk`, `write_scope`, `reversible`, and `public_behavior`. `inline` requires a reviewed `platform_registered` handler. In the public starter, the Research Agenda is a fictional Work Item projection: `Start with Codex` produces a copy-ready handoff and never starts a local or remote executor, while scheduling and completion controls remain `demo_only` and never mutate packaged data.

## Executable Task Extension Port

When a repeated task can reuse the existing Work Session, result modes, Review, and storage boundaries, use `researchos-task-extension-v1` before adding dashboard code. The schema is [researchos-task-extension-v1.schema.json](researchos-task-extension-v1.schema.json); the disabled reference descriptor is `config/extensions/method-comparison.example.json`; validation is `python3 scripts/validate_task_extensions.py`.

The dashboard builder and `scripts/plan_context.py` consume the same descriptor. It may declare task copy, read tiers, result modes, workspace routing, sensitivity, and authority. It may not execute arbitrary code, create persistence, bypass Review, or add a dashboard surface. See [Kernel and extension architecture](../../docs/system-reference.en.md#kernel-and-extension-architecture) in the System Reference.

Core API v1 keeps `task.read` as the required backward-compatible fallback. A bilingual extension may additionally declare `task.read_locales.en` / `task.read_locales.zh-CN` and `authority.locales` so `active_language_only` selects source paths and authority copy from one language. Every read target used by a `public_starter` extension must be Markdown with an explicit `sensitivity: public` or `public_safe` frontmatter value; missing sensitivity fails closed.

## Extension Kinds

| Kind | Examples | Default treatment |
| --- | --- | --- |
| Material asset | paper, external paper, email export, review manuscript, meeting note | Start as M1 registration under material intake. |
| Research object | project, plan, decision, relation, person, collaborator candidate | Use a card template and confirmation flow. |
| Resource object | funding, compute, time, dataset access, equipment, service quota | Track allocation, constraints, owner, refresh date, and decision boundary. |
| Workflow object | peer-review assignment, grant cycle, experiment run, public release, inbox batch | Track stage, action, blocker, validation, and handoff. |
| Dashboard surface | new tab, new workbench, new card box, new filter | Add only after a stable source and candidate contract exist. |
| Export target | public profile, context capsule, release package, teaching demo | Must pass safe-export policy and allowlist review. |

## Promotion Ladder

| Level | Name | Requirement | Example |
| --- | --- | --- | --- |
| C0 | Category idea | A repeated need is identified, but no template exists. | "I often need to track compute allocation." |
| C1 | Pilot records | 2-3 manually written cards show stable fields. | `compute-allocation-note.md`, `budget-allocation-note.md`. |
| C2 | Template and workflow | A template, lifecycle, and placement rule exist. | `resource-template.md` plus resource intake workflow. |
| C3 | Script/dashboard projection | Builder or dashboard can read the category without inventing state. | Resource cards appear in Assets or Today. |
| C4 | First-class surface | The category has enough volume and action value to deserve its own box or tab. | Resources, Reviews, or Emails become dashboard surfaces. |

## Required Fields

Every extension proposal must answer:

| Field | Meaning |
| --- | --- |
| `asset_class` | Stable category name, for example `email`, `review_item`, `external_paper`, `resource_budget`, `compute_resource`. |
| `intent` | What judgment or action does this category support? |
| `source_authority` | Where does the raw source live, and what can be trusted? |
| `sensitivity_default` | `public`, `internal`, `sensitive`, `local_only`, or `not_exportable`. |
| `lifecycle` | Which lifecycle applies: M1/M2/M3 material maturity, I0-I3 project incubation, R0-R3 relationship maturity, or a new ladder? Record P0-P3 separately as priority, never as maturity. |
| `canonical_location` | Where confirmed Markdown lives. |
| `candidate_location` | Where unconfirmed records wait. |
| `relations` | Which existing cards it can connect to. |
| `template` | Which template or field schema creates new cards. |
| `dashboard_behavior` | Hidden, folded into Assets, shown in Today, or given a new surface. |
| `validation` | Which command, checklist, or manual review catches drift. |
| `export_boundary` | Whether and how this category may appear in public output. |

## Routing Examples

| New class | Suggested location | Notes |
| --- | --- | --- |
| Email | `06_active_context/` for actions, `02_decisions/` for confirmed decisions, local private source for raw mail | Do not store raw inbox dumps in the public starter. |
| External paper being surveyed | `01_knowledge/literature/` or a public-safe reading note | It is not an "own paper"; mark relation to active projects. |
| Paper under peer review | `05_workflows/review_writing/` for workflow, `06_active_context/` for active review state | Default `local_only` or `not_exportable`. |
| Budget or funding allocation | `02_decisions/` for allocation decisions, `06_active_context/` for current budget state | Keep amounts public-safe or use placeholders in public starter. |
| Compute allocation | `06_active_context/` for current quota, `02_decisions/` for tradeoffs, `05_workflows/` for scheduling workflow | Track refresh date, owner, limit, and risk. |

## Stop Rules

- Do not add a dashboard button before the category has a template and candidate flow.
- Do not create a new top-level directory for every new class.
- Do not let generated dashboard data become canonical memory.
- Do not mix raw private material with derived cards.
- Do not make sensitive classes public by adding them to demo data.
- Do not hand-code a task across catalog, prompt, and workspace files when the declarative port is sufficient.
