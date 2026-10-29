---
type: data_contract
title: "ResearchOS 扩展契约 v1"
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
  <a href="researchos-extension-contract-v1.md">English</a> | <strong>中文</strong>
</p>

# ResearchOS 扩展契约 v1

## Agent Summary

本契约定义 ResearchOS 新增资产类别、材料类型、资源对象、工作流对象、dashboard 界面或导出目标前的准入规则。新类别必须先说明意图、来源权威、生命周期、关系、候选流、写回目标、验证方式和公开安全边界，才能成为一等能力。

## 核心规则

新增类别不是“多建一个文件夹”。只有当它改变研究者如何判断、行动、验证或分配资源时，才值得成为 ResearchOS 的新类别。如果它只是另一个输入文件，先走材料接入；如果它反复出现并需要稳定操作，再按扩展阶梯升级。

## Plugin Host v1

`researchos-plugin-v1` 是公开安全插件和本地忽略 manifest 共用的宿主合同。Schema 是 [researchos-plugin-v1.schema.json](researchos-plugin-v1.schema.json)；经过审查的 manifest 放在 `config/plugins/`；机器或个人专用 manifest 放在 Git 忽略的 `config/plugins.local/`；`python3 scripts/validate_plugins.py` 是默认拒绝的验证门。

公开版只加载声明式、`public_safe` 且不申请网络、命令、canonical 写入、私有路径或私有状态权限的 manifest。Registry summary 不暴露来源路径和权限细节。V1 不执行任意插件 JavaScript，也不创建新工作区、结果模式、storage owner 或写回路线。

现有 `researchos-task-extension-v1` 仍是当前运行时输入。Plugin Host 只把它规范化为 `tasks` contribution，并核验输出等价，因此不会形成第二套任务定义，也不会改变用户可见路由。

### Candidate Adapter 端口

插件可以登记经过审查的 `candidate_types`，但 manifest 不负责加载实现。静态加载、经过源码审查的 first-party adapter 拥有领域规范化、生成、预览元数据、撤回/解决调用和领域文案。记录进入 Review 前必须变成 `CandidateEnvelope` v1；Unified Inbox 与 Codex handoff 只消费 envelope，不按插件原始字段增加分支。

首个已验证实现是 `material_pipeline`，覆盖材料接入、材料升级与 research scout candidate。它复用现有 Review、endpoint、storage key、archive 和确认语义；禁用后只移除自身 contribution，不创建另一套状态系统。公开可用不等于取得长期写回权限：公开 server 继续在 canonical write 边界 fail closed。

Candidate adapter 必须进入经过审查的 runtime registry，具备行为测试，并由 plugin ownership validation 声明。若新增 candidate type 仍要求修改核心 Inbox branch，说明 envelope 不完整，或该改动应进入 C3 kernel review。

### Work Item 与原位动作端口

Plugin v1.1 以向后兼容方式增加 `work_item_providers` contribution。Provider 把一个领域投影映射为共享的 `Project -> current Commitment` 形状，不创建第二套项目数据库。内核拥有注意力状态与动作风险语言；插件拥有领域状态、稳定 identity、责任、来源引用和下一步内容。

Projection 读取不是对 Dashboard 整体对象的原始访问。每项 manifest projection 都声明 `researchos-projection-envelope-v1`、敏感度、新鲜度和精确字段导出表；未知或被拒绝的合同只返回 `ready / empty / error` 中的受限状态，不提供 payload。UI slot 同时声明旧 routing alias 与唯一 canonical `surface.region` 坐标；引用的 action 必须属于同一 canonical surface，插件不能把 Review 或 Start mutation 暗中挂到另一屏。

Action 一旦声明任一 v1.1 字段，就必须完整声明 `confirmation_mode`、`risk`、`write_scope`、`reversible` 和 `public_behavior`。`inline` 必须由经过审查的 `platform_registered` handler 执行。公开版的 Research Agenda 只是虚构 Work Item 投影：`交给 Codex` 只生成可复制交接，不启动本地或远程执行器；排期与完成控件保持 `demo_only`，绝不修改打包数据。

## 可执行任务扩展端口

当重复任务可以复用现有 Work Session、结果模式、待确认和存储边界时，先使用 `researchos-task-extension-v1`，不要直接增加 dashboard 代码。Schema 是 [researchos-task-extension-v1.schema.json](researchos-task-extension-v1.schema.json)；默认禁用示例是 `config/extensions/method-comparison.example.json`；验证命令是 `python3 scripts/validate_task_extensions.py`。

Dashboard builder 与 `scripts/plan_context.py` 读取同一份 descriptor。它可以声明任务文案、读取层级、结果模式、workspace、敏感度和 authority；不能执行任意代码、创建持久化、绕过待确认或增加独立界面。详见系统参考中的[内核与扩展架构](../../docs/system-reference.zh.md#内核与扩展架构)。

Core API v1 继续把 `task.read` 作为必需的向后兼容回退。双语扩展可以额外声明 `task.read_locales.en` / `task.read_locales.zh-CN` 与 `authority.locales`，让 `active_language_only` 同时冻结来源路径和 authority 文案。凡是可用于 `public_starter` 的扩展，其读取目标必须是 frontmatter 明确标注 `sensitivity: public` 或 `public_safe` 的 Markdown；缺失标注时门禁默认拒绝。

## 类别类型

| 类型 | 例子 | 默认处理 |
| --- | --- | --- |
| 材料资产 | 论文、外部调研论文、邮件导出、审稿论文、会议记录 | 先作为 M1 材料登记。 |
| 研究对象 | 项目、计划、决策、关系、人物、候选合作者 | 使用卡片模板和确认流。 |
| 资源对象 | 经费、算力、时间、数据集权限、设备、服务额度 | 记录分配、约束、owner、刷新时间和决策边界。 |
| 工作流对象 | 审稿任务、基金周期、实验运行、公开发布、收件箱批次 | 记录阶段、行动、阻塞、验证和交接。 |
| Dashboard 界面 | 新 tab、新 workbench、新卡片盒、新筛选器 | 只有稳定来源和候选契约后才加入。 |
| 导出目标 | 公开主页、上下文 capsule、发布包、教学 demo | 必须通过安全导出和 allowlist。 |

## 升级阶梯

| 层级 | 名称 | 要求 | 示例 |
| --- | --- | --- | --- |
| C0 | 类别想法 | 发现重复需求，但还没有模板。 | “我经常需要跟踪算力分配。” |
| C1 | 试点记录 | 手写 2-3 张卡片，字段开始稳定。 | `compute-allocation-note.md`、`budget-allocation-note.md`。 |
| C2 | 模板和流程 | 有模板、生命周期和放置规则。 | `resource-template.md` 加资源接入流程。 |
| C3 | 脚本或界面投影 | builder 或 dashboard 能读取，不自己发明状态。 | 资源卡进入 Assets 或 Today。 |
| C4 | 一等界面 | 数量和行动价值足够，值得有自己的盒子或 tab。 | Resources、Reviews、Emails 成为独立界面。 |

## 必填字段

每个扩展提案必须回答：

| 字段 | 含义 |
| --- | --- |
| `asset_class` | 稳定类别名，例如 `email`、`review_item`、`external_paper`、`resource_budget`、`compute_resource`。 |
| `intent` | 它支持什么判断或行动。 |
| `source_authority` | 原始来源在哪里，哪些内容可信。 |
| `sensitivity_default` | `public`、`internal`、`sensitive`、`local_only` 或 `not_exportable`。 |
| `lifecycle` | 使用 M1/M2/M3 材料成熟度、I0-I3 项目孵化度、R0-R3 关系成熟度，还是需要新生命周期；P0-P3 必须另存为优先级，不能冒充成熟度。 |
| `canonical_location` | 已确认 Markdown 放哪里。 |
| `candidate_location` | 未确认记录在哪里等待。 |
| `relations` | 可以连接到哪些现有卡片。 |
| `template` | 用哪个模板或字段 schema 建卡。 |
| `dashboard_behavior` | 隐藏、并入 Assets、显示在 Today，还是独立界面。 |
| `validation` | 用什么命令、清单或人工复查防漂移。 |
| `export_boundary` | 是否以及如何进入公开输出。 |

## 路由例子

| 新类别 | 建议位置 | 注意 |
| --- | --- | --- |
| 邮件 | 行动进入 `06_active_context/`，确认决策进入 `02_decisions/`，原始邮件留在本地私人来源 | 不把原始邮箱导出放进公开版。 |
| 外部调研论文 | `01_knowledge/literature/` 或公开安全阅读笔记 | 不等同于本人论文；要标注和当前项目的关系。 |
| 审稿论文 | `05_workflows/review_writing/` 放流程，`06_active_context/` 放当前审稿状态 | 默认 `local_only` 或 `not_exportable`。 |
| 经费或预算分配 | `02_decisions/` 放分配决策，`06_active_context/` 放当前预算状态 | 公开版用占位金额或示意字段。 |
| 算力分配 | `06_active_context/` 放当前额度，`02_decisions/` 放取舍，`05_workflows/` 放排程流程 | 记录刷新日期、owner、限制和风险。 |

## 停止规则

- 没有模板和候选流之前，不加 dashboard 按钮。
- 不为每个新类别都创建顶层目录。
- 不让生成的 dashboard 数据变成权威记忆。
- 不混合原始私人材料和派生卡片。
- 不把敏感类别加入公开 demo 数据。
- 声明式任务端口足够时，不要在 catalog、prompt 和 workspace 文件中手工重复接线。
