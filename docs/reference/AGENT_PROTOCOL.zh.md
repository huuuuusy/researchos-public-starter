---
type: protocol
title: "ResearchOS 公开版 Agent 协议"
status: ready
created: 2026-06-27
updated: 2026-10-28
tags:
  - agent-protocol
  - context-routing
  - public-starter
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <a href="AGENT_PROTOCOL.md">English</a> | <strong>中文</strong>
</p>

# Agent 协议

## Agent Summary

本文件定义 Agent 应如何使用 ResearchOS 公开 starter。核心规则是：先识别任务，再读取最小充分上下文；区分来源事实、用户确认判断和 Agent 推断；私人、在投、敏感材料默认 local-only；明确授权的编辑应完成必要验证；未接受的判断仍保持候选，写入文件不等于本人接受。

## 核心原则

路由、读取预算、默认输出形状和一般安全规则见 [`AGENTS.md`](../../AGENTS.md)（中文版 [AGENTS.zh.md](AGENTS.zh.md)）。本协议补充三条原则：

1. 区分来源事实、用户确认判断和 Agent 推断。
2. 保留原始证据。
3. 不把一次性对话直接写成长期记忆。

## 语言路由

先按项目选择的语言读取文件，再按普通链接下钻。公开版中，英文通常使用基础文件名或 `.en.md`，中文使用 `.zh.md`。如果 `public_starter.content_language` 是 `en`，读取 `README.md`、`docs/user-manual.en.md`、`docs/reference/AGENT_PROTOCOL.md` 和其他英文文件。如果是 `zh-CN`，读取 `README.zh.md`、`docs/user-manual.zh.md`、`docs/reference/AGENT_PROTOCOL.zh.md` 和存在的 `.zh.md` 文件。

默认不要读取另一套语言的对应文件。只有用户明确要求翻译、双语对照或语言维护时，才读取另一套语言。

## 默认任务流程

```text
识别任务类型
  -> 选择上下文预算
  -> 读取必要上下文
  -> 检查敏感性和导出边界
  -> 输出所请求的成果或执行已授权编辑
  -> 验证并报告实际完成情况、不确定性与证据边界
  -> 只有确有必要时才建议额外的长期写回
```

`AGENTS.md` 未加载时，唯一的路由文件是 `docs/user-manual.zh.md` 第 2 节、本协议、上下文预算协议或任务矩阵相关行之一。不要预加载所有入口文件。

## 授权与完成

用户要求更新指定文档或有来源的事实时，已授权该范围内的编辑与必要验证；只要求方案时则交付方案。改变稳定身份、敏感判断、权威、权限或公开边界，需要具体变更的授权；同一变更已有授权时不重复索取。可审查 diff 是证据，不是新的审批门。

读取上限约束批次，不产生权限要求。说明缺失证据后继续范围内的必要调查。若某项动作缺少授权，只暂停该动作，其余独立已授权工作继续；不能把实施请求停在计划。仓库编辑不启用 Dashboard/provider 执行，也不授权 commit、push、发布或对外发送消息。

## 安全规则

- 私人、在投、审稿中、未公开、人物敏感、学生、评审、基金和关系材料默认 `local_only`。
- public-facing 输出需要明确 `public_safe` 批准。

## 会话上下文交付

[共享治理边界](../system-reference.zh.md#共享治理边界)区分会话上下文交付与公开发布：研究者启动会话内的 public/internal 交付、sensitive 每次终端确认、private/未知排除，以及狭窄的来源声明字段例外；也写明交付记录无法观测的范围。这些语义不在公开 `copy_only` 发布中启用 provider 执行。

## 输出规则

判断类任务说明结论、必要依据和实质不确定性；编辑任务报告实际改动、验证和未关闭动作。只有未接受判断或尚未应用的方案才标为候选，明确区分本地修改、本人接受与外部交付。短任务不必填充固定多字段回执。

## 相关文件

- `docs/reference/CONTEXT_BUDGET_PROTOCOL.zh.md`
- `docs/reference/WHERE_TO_PUT_NEW_MATERIALS.zh.md`
- `09_templates/project-template.md`
- `09_templates/standard-agent-prompts.zh.md`
- `05_workflows/research_management/material-intake-workflow.md`
