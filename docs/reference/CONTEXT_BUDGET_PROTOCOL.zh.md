---
type: protocol
title: "ResearchOS 上下文预算协议"
status: ready
created: 2026-06-27
updated: 2026-07-10
tags:
  - context-budget
  - token-efficiency
  - agent-protocol
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <a href="CONTEXT_BUDGET_PROTOCOL.md">English</a> | <strong>中文</strong>
</p>

# 上下文预算协议

## Agent Summary

本文件定义 ResearchOS Public Starter 的低 token 阅读协议。Agent 应先判断是否真的需要仓库上下文，再按层级读取：先路由，再读摘要，再读任务 Markdown，只有任务需要核证据时才进入 evidence 层。这样既能保持判断准确，也能减少上下文噪声和 local-only 材料暴露。

## 五级阅读阶梯

| 层级 | 目的 | 典型文件 |
| --- | --- | --- |
| L-1 No-read triage | 判断请求是否需要仓库上下文。 | 不读文件。 |
| L0 Route | 判断任务类型和安全边界。 | `AGENTS.md`、一个路由文件。 |
| L1 Summary | 用低 token 获得稳定摘要。 | frontmatter、`Agent Summary`、context capsule。 |
| L2 Task file | 读取当前任务需要的具体 workflow/template。 | 一个工作流、一个模板、一个案例。 |
| L3 Evidence | 核对事实和来源细节。 | 来源笔记、审计、原始材料路径、明确证据。 |

## 预算模式

| 模式 | 使用场景 | 阅读深度 |
| --- | --- | --- |
| `quick` | 短回答、路由、下一步。 | L-1-L1 |
| `standard` | 普通诊断、写作、计划。 | L0-L2 |
| `evidence` | 高风险判断或正式输出。 | L0-L3 |
| `export` | 公开或外部上下文包。 | L0-L1 加安全导出规则 |

默认使用 `quick`。只有创建或更新卡片、计划、工作流时才使用 `standard`。只有输出依赖事实核对时才使用 `evidence`。准备 public-facing 或可分享上下文时使用 `export`。

## 渐进式上下文契约

档位定义的是初始上下文上限，不是要求一次性读完所有候选文件。

| 模式 | 初始包 | 文件上限 | 估算总 token 上限 | 只在以下情况扩展 |
| --- | --- | ---: | ---: | --- |
| `quick` | 一个任务主文件或精确目标。 | 1 个仓库文件 | 约 10k | 首个文件无法回答已说明的缺口。 |
| `standard` | quick + 少量 task-specific workflow/template。 | 5 个仓库文件 | 约 35k | 已说明缺失的判断、状态或工作流。 |
| `evidence` | standard + 定向来源、audit 或 checklist。 | 8 个仓库文件 | 约 60k | 已说明核验问题或事实冲突。 |
| `export` | quick + safe-export policy + 目标说明。 | 3 个仓库文件 | 约 20k | 需要检查公开边界。 |

如果 Agent 环境已经自动加载 `AGENTS.md`，不要重读它或重放入口协议。用户已经给出精确来源或目标路径时，先读该文件，并计入当前档位上限。文件数或估算 token 任一超限时，按具体问题拆批，不要一次装载完整清单。

同一任务继续时沿用上一轮 context receipt，不重读未变化的入口、摘要和任务文件；只读变化或新需要的文件。跨会话继续时使用短 resume packet，记录任务、上一判断、开放问题、已用路径和变化输入，不重放完整聊天历史。

## 硬性 Token 控制

- 不要因为 `README.md` 存在就默认读取；它是给人看的概览，不是默认 agent 上下文。
- 不要同时读取中英文成对文件，除非任务是翻译、双语质检或文档同步。
- 不要读取 `dashboard/data/researchos-dashboard.json`，除非在调试 dashboard 状态或检查生成 demo 数据。
- 不要读取完整 user manual，除非用户要求完整解释。
- 不要读取全部模板，只读匹配模板。
- 超过渐进式上下文契约表中的首轮上限前，先说明缺口，以及新增每个文件解决什么问题。
- 目录不能算作一个“已选证据”；evidence 必须落到具体文件或用户提供的精确来源路径。

## 语言预算规则

一个任务默认只把一种语言算作活跃上下文。除非任务本身是翻译、双语质检或文档同步，否则不要同时读取同一 Markdown 文件的英文版和中文版。`content_language` 为 `en` 时优先读取英文基础文件；为 `zh-CN` 时优先读取存在的 `.zh.md` 文件。

## 文件设计要求

稳定 ResearchOS 文件应包含：

```text
## Agent Summary
## When to Read
## Do Not Use For
## Evidence Boundary
## Related Files
```

`Agent Summary` 应让 Agent 不阅读全文也能完成文件路由。

## 下钻问题

读取更深层前先问：

1. 当前任务真的需要更多细节吗？
2. Agent Summary 是否已经足够？
3. 下钻是否会触及 sensitive/local-only 材料？
4. 用户是否要求证据核对？
5. 输出是否会变成正式或公开材料？

如果答案是否，保持低层级。

## 汇报要求

必要时简短说明：

```text
读取层级：
初始上下文：
新增上下文及理由：
未读取上下文：
证据边界：
是否需要升档：
```
