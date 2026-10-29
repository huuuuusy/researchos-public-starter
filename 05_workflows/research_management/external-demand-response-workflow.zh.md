---
type: workflow
title: "外部需求响应工作流"
status: ready
created: 2026-07-01
updated: 2026-07-01
tags:
  - external-demand
  - opportunity
  - response-drafting
  - public-safe
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <a href="external-demand-response-workflow.md">English</a> | <strong>中文</strong>
</p>

# 外部需求响应工作流

## Agent Summary

这个工作流帮助用户处理外部请求、邀请、合作邮件、审稿请求、报告邀请、proposal 机会或类似需求。它要求先通过 ResearchOS 找已有资产和边界，再决定是否起草回复；任何私人或不确定上下文都只能作为候选判断。

## 什么时候使用

当用户说下面这些话时使用：

- “我收到这个邀请，要不要回应？”
- “ResearchOS 能不能帮我判断这个合作是否合适？”
- “回复前先找一下我已有相关资产。”
- “可以帮我起草回复，但先检查边界。”

## 先读什么

1. `AGENTS.md`
2. 本工作流文件。
3. 只有可能写入或更新文件时，才读 `docs/reference/AGENT_PROTOCOL.zh.md`。

只有在请求类型清楚后，再读取具体卡片、任务矩阵或模板。

## 处理流程

1. 判断请求类型：
   - 合作
   - 报告或 seminar
   - proposal 或 grant
   - 审稿或服务
   - 媒体/公开写作
   - 教学或 mentoring
   - 不明确机会
2. 抽取请求中的来源事实。
3. 搜索相关 ResearchOS 资产。
4. 区分已确认事实和候选解释。
5. 找出缺失信息和风险。
6. 判断回应 stance：
   - 接受
   - 婉拒
   - 先问清楚
   - 推迟
   - 记录为未来机会
7. 只有边界清楚时才起草回复。
8. 建议哪些内容可以作为候选记忆记录。

## 输出格式

```text
请求类型：
已知事实：
相关 ResearchOS 资产：
适配判断：
风险或缺失信息：
隐私/导出边界：
推荐回应 stance：
回复草稿，如安全：
候选记忆记录：
下一步行动：
```

## 不要推断

- 私人亲近程度；
- 指导关系或学生身份；
- 实验室成员关系；
- 未确认贡献层级；
- 未来合作承诺；
- 用户没有说明的可用时间或意愿。

## 验证

写文件前先让用户确认保存目标和边界。写入后运行相关本地验证或链接检查。

## Agent Summary

公开安全的外部请求响应工作流，用来在起草回复前通过 ResearchOS 资产完成适配判断、证据边界、隐私边界和候选记忆路由。
