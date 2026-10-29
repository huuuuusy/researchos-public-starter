---
type: workflow
title: "Derived Work Artifact Lifecycle"
status: ready
created: 2026-08-07
updated: 2026-08-07
tags:
  - research-management
  - derived-artifact
  - active-context
  - archive
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="derived-work-artifact-lifecycle.zh.md">中文</a>
</p>

# Derived Work Artifact Lifecycle

## Agent Summary

This workflow governs Markdown created for one bounded piece of work, such as presentation preparation, a meeting handoff, an application workbench, a temporary collaboration analysis, or a revision plan. Keep it in `06_active_context/` only while a named consumer, next action, or concrete waiting event still exists. At closeout, distill durable facts, decisions, or methods into layers `01–05`; move the complete artifact to `07_archive/task_artifacts/` only when its feedback trail or decision context still has independent value.

Archiving is not a privacy or publication decision. Real people, unpublished work, applications, reviews, and local paths remain `local_only` or `not_exportable` and must not be committed to the public starter.

## Applies To

- presentation, interview, application, or defense preparation;
- meeting and handoff workbenches;
- one-off opportunity or collaboration analyses;
- revision, rebuttal, or report workbenches;
- temporary narrative syntheses created for one bounded task.

It does not replace canonical paper, project, person, decision, workflow, raw-source, runtime, or generated-report records.

## Lifecycle

### 1. Working

Location: `06_active_context/` in a user's private or local vault.

Minimum fields:

- `artifact_kind`;
- `lifecycle_stage: working`;
- `current_consumer`;
- `next_action`;
- `closure_gate`;
- `retention_policy: review_at_close`;
- sensitivity and source boundaries.

`waiting` is still current only when it names a concrete external event. "Maybe useful later" is not an active state.

### 2. Closeout Review

When the task, meeting, submission, interview, or decision ends, choose one disposition:

| Disposition | Use when | Action |
| --- | --- | --- |
| `promote` | The artifact itself became a stable authority. | Move it to the correct layer in `01–05`; keep one canonical copy. |
| `distill_then_archive` | A small durable lesson exists and the full process remains traceable evidence. | Distill first, then archive the complete artifact. |
| `archive_only` | The process is unique but does not yield a reusable rule. | Archive without promoting it. |
| `git_only` | A final artifact or Git history fully replaces it. | Remove the working copy. |

Do not copy the complete document into multiple layers. Each canonical layer receives only the smallest fact, decision, relationship, or method it owns.

### 3. Archived

Location: `07_archive/task_artifacts/`.

Minimum fields:

- `status: archived`;
- `lifecycle_stage: archived`;
- `archived`;
- `archive_reason`;
- `retention_reason`;
- `superseded_by` or `distilled_to`;
- `next_call_condition`;
- the original sensitivity.

If new work begins, create a new current artifact and link it with `derived_from`. Do not silently turn an archived snapshot back into a current authority.

## Archive Boundaries

| Archive area | Purpose |
| --- | --- |
| `task_artifacts/` | One bounded presentation, meeting, application, analysis, or revision work product. |
| `project_plans/` | Project-level research plans, experiment routes, and stopped method branches. |
| `runtime_evidence/` | Runtime receipts and historical machine state. |
| `technical_reports/` | Historical technical-report versions. |

If the document says "how this project should proceed," it is usually a project plan. If it says "how we prepared and revised this one task," it is usually a task artifact.

## Public Starter Boundary

- The public repository may ship this workflow, templates, and fictional or sanitized examples.
- Real task artifacts belong only in the user's own private/local vault unless separately approved for publication.
- Moving a file into an archive never changes `sensitive`, `local_only`, or `not_exportable` into `public`.
- Public-safe demonstrations must not contain real collaborators, submissions, applications, private review text, or machine-specific paths.

## Closeout Checklist

- [ ] No current consumer, next action, or concrete waiting event remains.
- [ ] Canonical facts and decisions have been distilled to the layer that owns them.
- [ ] Any claimed reusable method has evidence beyond one isolated example.
- [ ] The full artifact has value that a final output or Git history cannot replace.
- [ ] Archive and retention reasons are explicit.
- [ ] Links now point to current authorities rather than archived snapshots.
- [ ] Sensitivity and export boundaries are unchanged.
- [ ] Repository validators and link checks pass.

## Related Files

- [Where to Put New Materials](../../docs/reference/WHERE_TO_PUT_NEW_MATERIALS.md)
- [Material Intake Workflow](material-intake-workflow.md)
- [Active Context Layer](../../06_active_context/README.md)
- [Archived Task Artifacts](../../07_archive/task_artifacts/README.md)
- [Derived Work Artifact Template](../../09_templates/derived-work-artifact-template.md)
- [Safe Export Policy](../../docs/reference/SAFE_EXPORT_POLICY.md)
