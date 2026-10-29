---
type: demo_research_agenda
title: "虚构责任感知研究议程"
status: active_demo
sensitivity: public
reference_date: 2026-08-11
exportable_to:
  - public_template
tags:
  - demo
  - research-agenda
  - responsibility
  - fictional-data
---

# 虚构责任感知研究议程

## Agent Summary

这是公开安全的虚构权威示例，用来演示 ResearchOS 的责任原语：第一负责人任务与协作支持分开计数，责任、承诺状态、优先级、下一步和新鲜度来自同一份账本。它不包含维护者的真实项目、人物、截止日、路径或私有执行状态。

## Answer Contract

- “我有多少主线”只统计 `responsibility: lead` 且 `state: mainline`。
- 用户关心或审阅一个项目，不会让协作事项自动变成主责。
- 等待、排队、暂停、条件和关闭事项不进入主责推进数。
- `lifecycle_phase` 记录项目走到哪里；第一屏只显示当前可行动事项，资产页保留全部生命周期。
- 过期状态必须先复核，不能继续把旧 active 标签当作当前事实。
- 缺失或非法责任会失败关闭到 `unclassified`，绝不默认算作主责。
- 只有覆盖回执当前且完整时才能声明完整计数，否则只报告已登记事项。

## Coverage Receipt

- coverage_scope: 本公开演示文件中的 6 个虚构议程事项
- coverage_status: reviewed
- coverage_reviewed: 2026-07-26
- coverage_stale_after_days: 30
- coverage_sources: 08_exports/public_starter/demo-research-agenda.zh.md
- coverage_candidates:
- coverage_exclusions: 维护者真实项目、人物、截止日、路径和私有执行状态

## Responsibility Items

### 返修论断收尾

- id: demo-revision-claim-closeout
- responsibility: lead
- accountable_owner: 你
- role_summary: 最终论断和提交决策负责人
- state: mainline
- schedule_bucket: today
- schedule_label: 优先收尾
- schedule_order: 10
- attention_state: today
- attention_date: 2026-08-11
- priority: P0
- project_maturity: I3_independent_project
- related_people: 方法合作者; 证据审阅者
- assistant: 自选助手
- lane: paper-revision
- output_type: paper-revision
- lifecycle_phase: rebuttal
- current_stage: 回复结构已经完成，但仍有一条论断边界需要研究者判断
- progress_done: 3
- progress_total: 4
- progress_label: 4 个有界里程碑中已完成 3 个
- next_step: 核对争议论断，冻结证据实际支持的范围，并准备最终回复段落
- self_action: 决定最终论断边界并接受或否决修订措辞
- ai_action: 对照引用证据检查论断并准备有边界的候选段落
- success_gate: 最终措辞由研究者接受且不超出证据
- target_date: closeout-first
- last_verified: 2026-08-03
- stale_after_days: 14
- source_path: 08_exports/public_starter/demo-research-agenda.zh.md
- merge_rule: 把返修义务与新论文想法分开

### 评估 Pilot 判断

- id: demo-evaluation-pilot
- responsibility: lead
- accountable_owner: 你
- role_summary: Go/no-go 判断和实验范围负责人
- state: mainline
- schedule_bucket: this_week
- schedule_label: 本周判断
- schedule_order: 20
- attention_state: upcoming
- attention_date: 2026-08-12
- priority: P1
- project_maturity: I2_active_mount
- related_people: 评估合作者; 方法合作者
- assistant: 自选助手
- lane: experiment
- output_type: experiment-gate
- lifecycle_phase: experiment_preparation
- current_stage: 最小 pilot 已存在，但决策证据尚未审阅
- progress_done: 1
- progress_total: 3
- progress_label: Pilot 设计完成；仍需证据审阅和判断
- next_step: 检查 pilot 证据，并在扩大实验前作出 go/no-go 判断
- self_action: 判断信号是否足以支持更大实验
- ai_action: 汇总证据、失败案例和取舍，但不替研究者作决定
- success_gate: 研究者记录有证据的 go/no-go 判断和下一道 gate
- target_date: this-week
- last_verified: 2026-08-03
- stale_after_days: 14
- source_path: 08_exports/public_starter/demo-research-agenda.zh.md
- merge_rule: Pilot 过门前不新建完整项目

### 合作者稿件审阅

- id: demo-collaborator-review
- responsibility: support
- accountable_owner: 合作者
- role_summary: 只审阅 framing 和证据边界，不承担稿件交付责任
- state: mainline
- schedule_bucket: this_week
- schedule_label: 协作窗口
- schedule_order: 30
- attention_state: upcoming
- attention_date: 2026-08-14
- priority: P1
- project_maturity: I2_active_mount
- related_people: 稿件负责人; 证据审阅者
- assistant: 自选助手
- lane: collaboration
- output_type: paper-revision
- lifecycle_phase: revision
- current_stage: 合作者拥有稿件；当前有一项有边界的审阅请求
- next_step: 向合作者返回 claim boundary 审阅，不接管稿件
- self_action: 只判断请求范围内的 framing 和证据问题
- ai_action: 根据用户选择的公开安全来源准备简短审阅备忘
- success_gate: 合作者收到审阅并保留最终稿件决定
- target_date: collaborator-led
- last_verified: 2026-08-03
- stale_after_days: 14
- source_path: 08_exports/public_starter/demo-research-agenda.zh.md
- merge_rule: 协作事项永远不进入用户的主责主线数

### 已投稿论文

- id: demo-external-wait
- responsibility: support
- accountable_owner: 外部团队
- role_summary: 只在外部决定到达后响应
- state: waiting
- schedule_bucket: later
- schedule_label: 已投稿 · 评审中
- schedule_order: 40
- priority: P1-waiting
- project_maturity: I3_independent_project
- related_people: 外部团队; 通讯作者
- assistant: 自选助手
- lane: external-obligation
- output_type: research-obligation
- lifecycle_phase: under_review
- activation_trigger: 收到 official reviews、rebuttal 通知、编辑决定或作者组明确请求
- current_stage: 当前材料已提交，没有可执行动作
- next_step: 等外部决定；到达后重新核对责任和唯一下一步
- self_action: 等待期间不制造推测性工作
- ai_action: 保持状态边界，新证据到达前不准备额外任务
- success_gate: 真实外部事件产生经过核验的下一步
- target_date: external
- last_verified: 2026-07-25
- stale_after_days: 30
- source_path: 08_exports/public_starter/demo-research-agenda.zh.md
- merge_rule: 等待事项不计入当前执行数

### 长篇草稿

- id: demo-long-form-paused
- responsibility: lead
- accountable_owner: 你
- role_summary: 作者和唯一重开授权者
- state: paused
- schedule_bucket: later
- schedule_label: 保持当前
- schedule_order: 50
- priority: P1-preserve
- project_maturity: I2_active_mount
- related_people: 写作合作者
- assistant: 自选助手
- lane: writing
- output_type: long-form-writing
- lifecycle_phase: paused
- activation_trigger: 出现具体读感、连续性或发布问题
- current_stage: 当前草稿保留；没有具体读者问题支持再次修改
- next_step: 只有出现具体读感、连续性或发布触发时才重开
- self_action: 指出具体触发，否则保持不变
- ai_action: 保护当前版本，不制造新任务
- success_gate: 出现具体触发，或作者接受当前版本
- target_date: wait-for-author
- last_verified: 2026-07-25
- stale_after_days: 30
- source_path: 08_exports/public_starter/demo-research-agenda.zh.md
- merge_rule: 暂停事项仍归用户所有，但不计入推进中

### 综述范围门

- id: demo-survey-scope-gate
- responsibility: lead
- accountable_owner: 你
- role_summary: 决定想法是否值得成为独立交付物
- state: conditional
- schedule_bucket: later
- schedule_label: 当前收尾之后
- schedule_order: 60
- deadline: 2026-09-15
- priority: P2
- project_maturity: I0_assessment
- related_people: 方法合作者
- assistant: 自选助手
- lane: survey
- output_type: survey-paper
- lifecycle_phase: scoping
- current_stage: 主题已存在，但独立读者价值和重叠边界尚未解决
- next_step: 比较候选综述与既有综述，并判断是否值得成为独立稿件
- self_action: 判断是否有独立中心问题、目标读者和贡献
- ai_action: 根据用户选择的公开安全来源准备简短 scope / overlap audit
- success_gate: 研究者能够说明独立中心问题和读者价值
- target_date: conditional
- last_verified: 2026-06-30
- stale_after_days: 14
- source_path: 08_exports/public_starter/demo-research-agenda.zh.md
- merge_rule: 优先复用，不制造重复稿件

## Boundary

- 所有事项均为虚构。
- 公开 Dashboard 只投影本文件；生成 JSON 不是权威来源。
- Personal Vault 可以用相同字段保存本地私有任务，但公开 demo 生成绝不读取这些数据。
- 浏览器操作保持本地、可撤销；状态修改在用户确认写回前始终是候选。
