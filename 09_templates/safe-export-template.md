---
type: template
title: "Safe Export Template"
status: ready
created: 2026-06-27
updated: 2026-06-27
tags:
  - safe-export
  - template
sensitivity: public
exportable_to:
  - public_template
---

# Safe Export Template

## Agent Summary

Use this template to create a public-safe or external-agent context pack. It should list included files, excluded files, sensitivity decisions, intended use, and confirmation requirements.

## Export Metadata

```yaml
export_target:
created:
generated_by:
source_policy: docs/reference/SAFE_EXPORT_POLICY.md
included_sensitivity:
  - public
excluded_sensitivity:
  - sensitive
  - local_only
  - not_exportable
requires_confirmation: true
```

## Intended Use

- Target reader or agent:
- Task:
- Expected output:
- Valid until:

## Included Context

| File | Role | Sensitivity | Reason |
| --- | --- | --- | --- |
|  |  |  |  |

## Excluded Context

| File/layer | Sensitivity | Reason |
| --- | --- | --- |
|  |  |  |

## Context Pack

```text
[Insert compressed public-safe context.]
```

## Safety Boundary

- Does not include raw corpus materials.
- Does not include private people, student, reviewer, grant, or relationship judgment.
- Does not include submitted/unpublished content unless explicitly cleared.
