---
type: template
title: "阶段性派生工作产物模板"
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
  <a href="derived-work-artifact-template.md">English</a> | <strong>中文</strong>
</p>

# 阶段性派生工作产物模板

## Agent Summary

本公开安全模板用于用户私人/本地 vault 中的一次具体 PPT、会议、申请、分析或 revision 工作稿。占位字段不是事实。填入真实人物、未公开工作、申请、私人审稿文本或本机路径后，不得把文件提交到 本仓库。

## 工作期 Frontmatter

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

## Agent Summary 模板

```markdown
## Agent Summary

本文档服务于【当前任务】。当前消费者是【人或任务】，下一步是【具体动作】，在【关闭条件】发生后重新审查。本文档不是【论文/项目/人物/状态】的权威；相关事实必须回到【canonical 路径】核对。
```

## 建议正文

```markdown
## 任务目标
## 当前版本与用途
## 来源与证据边界
## 工作内容
## 待确认问题
## 下一步与关闭条件
```

## 归档期 Frontmatter

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

## Archive Note 模板

```markdown
## Archive Note

- 当前状态由【canonical 文件】负责。
- 本文保留【反馈链、取舍理由或历史语境】。
- 日期、职责、投稿状态和下一步可能已经过期，复用前必须核对。
- 仅在【具体调用条件】出现时读取。
```

## 相关文件

- [阶段性派生工作产物生命周期](../05_workflows/research_management/derived-work-artifact-lifecycle.zh.md)
- [阶段性任务产物归档](../07_archive/task_artifacts/README.zh.md)
