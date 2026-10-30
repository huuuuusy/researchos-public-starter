---
type: markdown
title: "Public Starter 示例材料"
status: reference
created: 2026-06-26
updated: 2026-10-29
tags:
  - public-starter
  - demo-index
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# 示例材料

本目录包含 ResearchOS Public Starter 的虚构示例材料：Dashboard 的示例议程、首次上手说明和卡片示例。它们帮助新用户理解第一步应该登记什么来源、卡片怎样写、卡片成熟度如何变化。你自己的材料不放在这里，而是放进 Git 忽略的 `personal_vault/`。登记来源是加入本地 Markdown 摘要、路径线索或公开链接；dashboard 不会上传或传输源文件。

这些文件不代表真实研究项目、真实人物、真实论文、真实合作者或任何非公开工作系统内容。

## 推荐第一路径

1. 按 `onboarding-step-by-step.zh.md` 操作，它从示例一直走到你自己的 `personal_vault/`。
2. 查看 `onboarding-intake-note-example.zh.md`。
3. 对照一级、二级和三级卡片示例：
   - `onboarding-person-card-levels.zh.md`
   - `onboarding-paper-card-levels.zh.md`
   - `onboarding-talk-card-levels.zh.md`
   - `onboarding-collaborator-card-levels.zh.md`
   - `onboarding-plan-card-levels.zh.md`
4. 阅读 `onboarding-card-maturity-rubric.zh.md`，理解一张卡片什么时候只是草稿，什么时候可以进入可执行状态。
5. 让 Codex 或其他助手创建卡片时，使用 `../../09_templates/standard-agent-prompts.zh.md` 中的标准提示词。
6. 需要时启动 Dashboard 示例，查看虚构议程。

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `onboarding-step-by-step.zh.md` | 首次上手路线：调度器演示、在 Agent 客户端里走一个闭环、建一个有一项承诺和一张卡片的个人库，以及可选的 personal-vault Dashboard。 |
| `demo-research-agenda.zh.md` | Dashboard 示例显示的六个虚构议程事项，设在一个固定的虚构日期。 |
| `onboarding-intake-note-example.zh.md` | 第一份用户接入笔记的示例回答。 |
| `onboarding-card-maturity-rubric.zh.md` | 一级、二级和三级成熟度的通用判定标准。 |
| `onboarding-person-card-levels.zh.md` | 个人画像卡片的升级示例。 |
| `onboarding-paper-card-levels.zh.md` | 论文卡片的升级示例。 |
| `onboarding-talk-card-levels.zh.md` | 报告卡片的升级示例。 |
| `onboarding-collaborator-card-levels.zh.md` | 从论文作者中抽取出的合作者卡片升级示例。 |
| `onboarding-plan-card-levels.zh.md` | 研究计划卡片的成熟度升级示例。 |
早期的 `fake-*`、`walkthrough` 和 `example-original-developer-*` 文件已在云端检查点 `d4169c3` 之后硬删除。Git 历史保留其迁移溯源；当前工作树只暴露受支持的统一接入路线。

## 案例开关

这些案例默认进入公开 demo 投影。个人库从不显示它们，所以用自己的材料不需要先关闭案例。维护者可以按用户手册第 5 节关闭它们；文件仍保留为只读放置指南。

## Agent Summary

一个公开安全的示例索引，把首次用户从虚构示例引导到自己的 `personal_vault/`，再到卡片创建和卡片成熟度。
