---
type: workflow
title: "资产类别扩展流程"
status: ready
created: 2026-06-27
updated: 2026-06-27
tags:
  - asset-extension
  - material-intake
  - dashboard
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <a href="asset-type-extension-workflow.md">English</a> | <strong>中文</strong>
</p>

# 资产类别扩展流程

## Agent Summary

当邮件、外部调研论文、审稿任务、预算、算力、数据集或其他资源这类重复新类别可能需要 ResearchOS 支持时，使用本流程。新增目录、脚本或 dashboard 界面前，先确认意图、来源权威、敏感性、生命周期、试点卡片、模板、候选流、验证方式和公开安全边界。

## 什么时候使用本流程

当一个新要素不只是单篇笔记，而是反复出现、有自己的状态、会连接论文/项目/人物/报告/计划/决策，或者会影响当前行动和资源分配时，使用本流程。

如果只是一次性材料，继续使用 `material-intake-workflow.md`。

## 第一步：命名类别

先选择稳定的 `asset_class`，名称描述对象本身，不描述 UI：

- `email_thread`
- `external_paper`
- `review_item`
- `budget_resource`
- `compute_resource`
- `dataset_access`

避免 `new_tab`、`misc`、`important`、`box_2` 这类名字。

## 第二步：判断基础类型

| 问题 | 基础类型 |
| --- | --- |
| 它是不是要读的来源？ | 材料资产 |
| 它是不是要确认或取舍的东西？ | 决策或候选 |
| 它是不是当前操作约束？ | 资源对象 |
| 它是不是有阶段的重复任务？ | 工作流对象 |
| 它是不是现有卡片之间的关系？ | 关系或组合对象 |

## 第三步：选择初始位置

| 新类别 | 先放这里 | 后续升级条件 |
| --- | --- | --- |
| 邮件线程 | 行动放 `06_active_context/`，确认决策放 `02_decisions/` | 如果通信笔记成为稳定证据类别，再考虑 `01_knowledge/communications/`。 |
| 外部调研论文 | `01_knowledge/literature/` 或阅读笔记 | 需要区分 surveyed papers 和 own papers 时，再加 dashboard 筛选。 |
| 审稿任务 | 活跃审稿放 `06_active_context/`，流程放 `05_workflows/review_writing/` | 数量高时再做 review workbench。 |
| 预算 | 当前状态放 `06_active_context/resources/`，分配决策放 `02_decisions/` | 预算影响多个项目时再做资源界面。 |
| 算力 | 当前额度放 `06_active_context/resources/`，取舍放 `02_decisions/` | 反复排程时再做 capacity workbench。 |

## 第四步：先写 2-3 张试点卡

加代码前，先写小型 Markdown 示例。每张试点卡至少包含：

```yaml
asset_class:
title:
status:
sensitivity:
source_authority:
lifecycle_state:
related_projects:
related_people:
related_materials:
candidate_or_confirmed:
next_action:
validation:
export_boundary:
```

## 第五步：判断是否需要模板

只有当试点卡字段稳定时，才建立模板。如果每张卡都不一样，就继续作为普通材料接入，不升级为一等类别。

## 第六步：判断是否需要 dashboard 支持

| 支持层级 | 使用条件 |
| --- | --- |
| 不进 dashboard | 罕见或一次性类别。 |
| Assets 筛选 | 有助于发现，但不是日常操作核心。 |
| Today 卡片 | 影响当前行动、阻塞或资源。 |
| Inbox 候选 | 需要确认、复核或交给 Codex。 |
| 独立界面 | 数量多、动作重复、验证稳定。 |

## 第七步：验证

修改本仓库时至少运行：

```bash
python3 scripts/build_public_starter_data.py --write
python3 scripts/check_all_links.py
python3 scripts/validate_runtime_config.py
```

如果增加脚本或 dashboard 投影，也要增加或更新小型验证规则。
