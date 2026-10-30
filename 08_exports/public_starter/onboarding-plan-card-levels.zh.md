---
type: card_level_example
title: "计划卡片等级示例"
status: reference
project_maturity: I2_active_mount
created: 2026-06-26
updated: 2026-06-26
tags:
  - public-starter
  - onboarding-demo
  - card-maturity
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <a href="onboarding-plan-card-levels.md">English</a> | <strong>中文</strong>
</p>

# 计划卡片等级示例

这个示例展示个人卡片、论文卡片、报告卡片和合作者卡片出现后，计划卡片如何成熟。

## 一级：种子计划卡片

```yaml
card_type: plan
maturity: 1
title: 建立前五张 ResearchOS 接入卡片
status: idea
source_materials:
  - onboarding-intake-note-example.zh.md
objective: 帮助新用户创建个人卡片、论文卡片、报告卡片、合作者卡片和计划卡片。
known:
  - 用户需要分步接入路径。
  - 现有示例案例可以关闭。
missing:
  - 具体文件和验证检查。
  - 仪表盘冒烟检查路径。
next_action: 把这个想法转成有输出和检查的范围化计划。
```

## 二级：有范围计划卡片

```yaml
card_type: plan
maturity: 2
title: 建立前五张 ResearchOS 接入卡片
status: scoped
objective: 创建公开安全的接入示例，展示应该登记什么来源以及卡片如何成熟。
inputs:
  - 用户接入笔记
  - 虚构论文元数据
  - 虚构报告元数据
  - 从作者列表抽取的合作者候选
outputs:
  - 个人卡片等级
  - 论文卡片等级
  - 报告卡片等级
  - 合作者卡片等级
  - 计划卡片等级
validation_checks:
  - 案例开启时，生成的示例数据包含接入示例
  - 案例关闭时，生成记录数变成零
  - 公开文档不包含密钥、本地路径或真实敏感人物
blockers:
  - 使用任何真实个人材料前，需要用户确认。
```

## 三级：可执行计划卡片

```yaml
card_type: plan
maturity: 3
title: 建立前五张 ResearchOS 接入卡片
status: operational
owner: 仓库维护者
execution_order:
  - 创建成对英文和中文接入示例
  - 更新仓库索引和用户手册
  - 重新生成示例数据
  - 运行运行配置、模型提供方、公开包、边界和空白字符检查
  - 验证案例关闭行为
agent_handoff:
  prompt: 更新公开安全接入示例，不加入真实个人数据。
  allowed_files:
    - 08_exports/public_starter/onboarding-*.md
    - docs/user-manual.en.md
    - docs/user-manual.zh.md
  forbidden:
    - 真实简历
    - 真实未公开论文
    - 本地运行日志
    - 模型提供方凭据
validation:
  commands:
    - python3 scripts/build_public_starter_data.py --write
    - python3 scripts/build_public_starter_data.py --disable-cases
update_trigger: 新增卡片类型或接入界面后修订。
```

## Agent Summary

一个三级计划卡片示例，展示模糊接入想法如何变成有范围实施计划，再变成可执行交接卡片。
