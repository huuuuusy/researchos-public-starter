---
type: workflow
title: "关系机会工作流"
status: ready
created: 2026-07-01
updated: 2026-07-01
tags:
  - relationship
  - opportunity
  - collaborator-candidates
  - public-safe
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <a href="relationship-opportunity-workflow.md">English</a> | <strong>中文</strong>
</p>

# 关系机会工作流

## Agent Summary

这个工作流帮助用户判断一个人、一篇论文、一个活动、一个项目或一个弱信号是否构成研究机会。它把零散上下文转成候选路线，但不推断私人关系或未来承诺。

## 什么时候使用

当用户问下面这些问题时使用：

- “这个人和我的工作有关系吗？”
- “这个活动值得跟进吗？”
- “哪些资产支持这个合作想法？”
- “我应该创建 person、relation、project 还是 plan card？”

## 先读什么

1. `AGENTS.md`
2. 本工作流文件。
3. 只有用户希望写入或更新卡片时，才读 `docs/reference/AGENT_PROTOCOL.zh.md`。

只有当用户给出具体姓名、论文、项目、活动或主题，并要求创建/更新卡片时，再读取模板、任务矩阵或具体源卡片。

## 处理流程

1. 判断信号类型：
   - 人物
   - 论文
   - 共同主题
   - 活动
   - 项目
   - 机构或群体
2. 列出已确认公开事实。
3. 列出本地-only 或敏感上下文，如有。
4. 搜索相关 ResearchOS 资产。
5. 提出机会路线：
   - 继续阅读
   - 创建候选人物卡
   - 创建关系卡
   - 创建项目或计划卡
   - 起草联系
   - 暂缓并观察
6. 说明不能得出哪些结论。
7. 写入或公开前请求用户确认。

## 输出格式

```text
信号：
已确认公开事实：
候选连接：
相关资产：
机会路线：
不能推断什么：
敏感性/导出边界：
推荐下一步：
候选卡片或更新目标：
```

## 不要推断

共同署名、共同主题、机构重叠或会议同场不证明：

- 指导关系；
- 学生身份；
- 私人亲近程度；
- 实验室成员关系；
- 贡献层级；
- 未来合作；
- 对方愿意被联系。

## 验证

如果该流程创建卡片，在用户确认关系和边界前保持 `candidate`。

## Agent Summary

公开安全的关系机会工作流，用来把人物、论文、活动、项目或主题信号转成候选机会路线，同时避免过度推断私人关系。
