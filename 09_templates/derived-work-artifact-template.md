---
type: template
title: "Derived Work Artifact Template"
status: ready
created: 2026-08-07
updated: 2026-08-07
tags:
  - template
  - derived-artifact
  - active-context
  - archive
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="derived-work-artifact-template.zh.md">中文</a>
</p>

# Derived Work Artifact Template

## Agent Summary

Use this public-safe template for a bounded presentation, meeting, application, analysis, or revision work product in a user's private/local vault. The placeholders are not facts. Do not commit a filled template containing real people, unpublished work, applications, private review text, or local paths to this repository.

## Working Frontmatter

```yaml
---
type: derived_work_artifact
artifact_kind: presentation_preparation # meeting_handoff | one_off_analysis | application_preparation | revision_workbench
title: ""
status: draft # candidate | active | waiting | pending_confirmation
lifecycle_stage: working
created: YYYY-MM-DD
updated: YYYY-MM-DD
sensitivity: local_only
current_consumer: ""
next_action: ""
closure_gate: ""
retention_policy: review_at_close
related_people: []
related_projects: []
source_files: []
tags: []
---
```

## Agent Summary Template

```markdown
## Agent Summary

This document supports [current task]. Its current consumer is [person or task], its next action is [action], and it must be reviewed when [closure gate] occurs. It is not the authority for [paper/project/person/status]; verify those facts in [canonical path].
```

## Suggested Body

```markdown
## Task Goal
## Current Version and Use
## Sources and Evidence Boundary
## Working Content
## Open Questions
## Next Action and Closure Gate
```

## Archived Frontmatter

```yaml
---
type: archived_task_artifact
artifact_kind: presentation_preparation
title: ""
status: archived
lifecycle_stage: archived
created: YYYY-MM-DD
updated: YYYY-MM-DD
archived: YYYY-MM-DD
sensitivity: local_only
archive_reason: ""
retention_reason: ""
superseded_by: []
distilled_to: []
next_call_condition: ""
related_people: []
related_projects: []
source_files: []
tags: []
---
```

## Archive Note Template

```markdown
## Archive Note

- Current state is owned by [canonical file].
- This artifact retains [feedback trail, tradeoff, or historical context].
- Dates, roles, submission states, and next steps may be stale; verify before reuse.
- Read only when [specific call condition] occurs.
```

## Related Files

- [Derived Work Artifact Lifecycle](../05_workflows/research_management/derived-work-artifact-lifecycle.md)
- [Archived Task Artifacts](../07_archive/task_artifacts/README.md)
