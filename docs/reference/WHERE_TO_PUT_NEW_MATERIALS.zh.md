---
type: guide
title: "新增材料放置指南"
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
  <a href="WHERE_TO_PUT_NEW_MATERIALS.md">English</a> | <strong>中文</strong>
</p>

# 新增材料放置指南

## Agent Summary

本指南说明 ResearchOS 新材料应该放在哪里。核心规则是：原始材料、派生知识、决策、认知模型、人物、工作流、当前上下文、导出和模板是不同层级，不要混用。你自己的材料放进 clone 里被 Git 忽略的 `personal_vault/`，它用同样的分层目录。私人、在投、未公开或敏感材料可以在那里分析，但不能放进本仓库 受跟踪的文件。

## 自己的材料放进 `personal_vault/`

你自己的卡片放在 `personal_vault/`，这是 clone 里一个被 Git 忽略的文件夹；下面的分层路径都相对于它，例如论文笔记放进 `personal_vault/01_knowledge/`，当前状态放进 `personal_vault/06_active_context/`。仓库根目录下的分层目录存放本仓库 自己的说明和虚构示例，不要把你的材料放在那里。含有真实材料的 clone 不要推送到公开远程仓库；想给库做版本管理，就另建一个没有公开远程的私人仓库副本。建库步骤见[用户手册第 5 节](../user-manual.zh.md#5-用自己的材料)的“开始自己的”。

## 一句话规则

原始材料留在原处，即仓库之外的本地来源目录，卡片记下它的路径；本仓库 里的 `corpus/` 保持为空。派生知识进入 `01_knowledge/`；判断和取舍进入 `02_decisions/`；可复用认知进入 `03_cognition/`；人物上下文进入 `04_people/`；流程进入 `05_workflows/`；当前状态进入 `06_active_context/`；经安全导出复查后才进入 `08_exports/`；模板进入 `09_templates/`。

## 放置表

| 材料 | 放置位置 | 边界 |
| --- | --- | --- |
| 原始 PDF、slides、文档、网页导出 | 仓库之外的本地来源目录；卡片记下路径 | 不当作已确认记忆。 |
| 论文笔记、材料摘要、项目事实 | `01_knowledge/` | 保留来源链接。 |
| 取舍、确认、被拒方案 | `02_decisions/` | 涉及人物或策略时默认敏感。 |
| mental model、heuristic、写作原则 | `03_cognition/` | 只有反复有用或已确认后才沉淀。 |
| 人物或合作者卡片 | `04_people/` | 受跟踪的 starter 文件只放虚构或公开安全示例。 |
| 可复用工作流或 SOP | `05_workflows/` | 保持通用，不写单个私人项目全历史。 |
| 当前任务、待确认问题、交接 | `06_active_context/` | 短期操作状态，不是完整历史。 |
| 一次具体 PPT、会议、申请、分析或 revision 工作产物 | 工作期：`06_active_context/`；结束后：`07_archive/task_artifacts/` | 先提炼长期内容；只有完整过程有独立价值时才归档。 |
| 公开安全 demo 或上下文包 | `08_exports/` | 必须通过安全导出边界。 |
| 模板、提示词、数据契约 | `09_templates/` | 模板中不要填入敏感真实数据。 |

## 私人和在投材料

ResearchOS 可以在 `personal_vault/` 里处理私人、在投、审稿中和未公开材料。由这些材料生成的卡片默认标为 `local_only` 或 `not_exportable`，除非用户明确解锁公开边界。不要把真实材料提交到本仓库。

一次性工作产物应遵循[阶段性派生工作产物生命周期](../../05_workflows/research_management/derived-work-artifact-lifecycle.zh.md)。把文件移入 archive 不会改变其敏感级别，也不构成公开许可。

## 当新材料变成新类别时

不要因为出现一种新材料，就直接创建新的顶层目录或 dashboard tab。如果邮件、外部调研论文、审稿任务、预算、算力、数据集权限等类别开始反复出现，并且需要自己的生命周期，请先读 `05_workflows/research_management/asset-type-extension-workflow.md` 和 `09_templates/data_contracts/researchos-extension-contract-v1.md`。

当这个类别有重复记录、稳定字段、关系连接、确认需求或资源分配影响时，才走扩展流程。否则继续作为普通 M1 材料接入。

## 不确定时

1. 原始材料保留原位。
2. 先建立一条小型 M1 登记。
3. 标明敏感性和导出边界。
4. 判断这个材料回答什么问题。
5. 把派生笔记放到正确层级。
6. 不确定判断保持候选。
