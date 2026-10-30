---
type: workflow
title: "阶段性派生工作产物生命周期"
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
  <a href="derived-work-artifact-lifecycle.md">English</a> | <strong>中文</strong>
</p>

# 阶段性派生工作产物生命周期

## Agent Summary

本工作流管理为一次具体任务产生的 Markdown，例如 PPT 或面试准备、会议交接、申请工作台、临时合作分析和 revision 计划。只有在仍有明确消费者、下一步或具体等待事件时，文档才留在 `06_active_context/`。任务关闭时，先把稳定事实、判断或方法提炼到 `01–05`；只有完整反馈链或决策语境仍有独立价值时，才把全文移入 `07_archive/task_artifacts/`。

归档不是隐私或公开决定。涉及真实人物、未公开工作、申请、审稿和本机路径的材料继续保持 `local_only` 或 `not_exportable`，不得提交到 本仓库。

## 适用对象

- PPT、面试、申请或答辩准备；
- 会议和交接工作台；
- 一次性的机会或合作分析；
- revision、rebuttal 或报告工作台；
- 为某个具体任务形成的临时研究叙事。

本规范不替代论文、项目、人物、决策、工作流、原始材料、运行态或机器报告的 canonical 文件。

## 生命周期

### 1. Working

位置：用户自己的私人或本地 vault 中的 `06_active_context/`。

至少写明：

- `artifact_kind`；
- `lifecycle_stage: working`；
- `current_consumer`；
- `next_action`；
- `closure_gate`；
- `retention_policy: review_at_close`；
- 敏感性和来源边界。

`waiting` 只有在等待一个具体外部事件时才仍属当前状态。“以后也许有用”不能作为活跃状态。

### 2. Closeout Review

任务、会议、投稿、面试或决策结束后，选择一种处置：

| 处置 | 适用条件 | 动作 |
| --- | --- | --- |
| `promote` | 文档本身已经成为稳定权威。 | 移入 `01–05` 的正确层级，只保留一个 canonical 副本。 |
| `distill_then_archive` | 少量内容可长期复用，完整过程仍有追溯价值。 | 先提炼，再归档全文。 |
| `archive_only` | 过程独特，但没有形成可复用规则。 | 直接归档。 |
| `git_only` | 最终成品或 Git 历史已经完整替代它。 | 删除工作副本。 |

不要把完整文档复制到多个层级。每个 canonical 层只接收它负责的最小事实、判断、关系或方法。

### 3. Archived

位置：`07_archive/task_artifacts/`。

至少写明：

- `status: archived`；
- `lifecycle_stage: archived`；
- `archived`；
- `archive_reason`；
- `retention_reason`；
- `superseded_by` 或 `distilled_to`；
- `next_call_condition`；
- 原有敏感级别。

如果出现新任务，应新建当前工作稿，并用 `derived_from` 指向历史文件；不要直接把归档快照改回当前权威。

## 归档目录边界

| 归档区 | 用途 |
| --- | --- |
| `task_artifacts/` | 一次具体 PPT、会议、申请、分析或 revision 形成的派生工作稿。 |
| `project_plans/` | 项目级研究计划、实验路线和停止的方法分支。 |
| `runtime_evidence/` | 运行回执与历史机器状态。 |
| `technical_reports/` | 历史技术报告版本。 |

如果文档主要回答“这个项目以后怎么推进”，通常属于 project plan；如果主要回答“这一次任务怎样准备和修改”，通常属于 task artifact。

## 本仓库的边界

- 公开仓库可以提供本工作流、模板以及虚构或经脱敏的示例。
- 真实任务产物默认只保存在用户自己的私人/本地 vault，除非另有明确公开许可。
- 把文件移入 archive 不会把 `sensitive`、`local_only` 或 `not_exportable` 自动变成 `public`。
- 公开安全示例不得包含真实合作者、在投材料、申请信息、私人审稿文本或本机专属路径。

## 关闭检查清单

- [ ] 已经没有当前消费者、下一步或具体等待事件。
- [ ] 稳定事实和判断已经提炼到各自 authority。
- [ ] 所谓可复用方法不只是从单个个案过早泛化。
- [ ] 完整原稿具有最终成品或 Git 历史无法替代的价值。
- [ ] 已写明归档和保留理由。
- [ ] 当前链接指向 canonical authority，而不是历史快照。
- [ ] 敏感性和导出边界没有改变。
- [ ] 仓库校验和链接检查通过。

## 相关文件

- [新增材料放置指南](../../docs/reference/WHERE_TO_PUT_NEW_MATERIALS.zh.md)
- [材料接入工作流](material-intake-workflow.md)
- [当前状态层](../../06_active_context/README.zh.md)
- [阶段性任务产物归档](../../07_archive/task_artifacts/README.zh.md)
- [阶段性派生工作产物模板](../../09_templates/derived-work-artifact-template.zh.md)
- [安全导出策略](../../docs/reference/SAFE_EXPORT_POLICY.zh.md)
