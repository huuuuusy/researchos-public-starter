---
type: governance
title: "受控自我进化控制面"
status: active
updated: 2026-08-04
sensitivity: public
---

<p align="right">
  <a href="self-evolution-control-plane.en.md">English</a> | <strong>中文</strong>
</p>

# 受控自我进化控制面

## Agent Summary

ResearchOS 通过受控维护扩展，而不是让模型自治修改系统。它可以检测仓库内的变化路径、计算受影响的固定维护步骤、运行只读检查；在 personal-vault 模式下，也只能在用户对具体 plan ID 确认后刷新可再生投影。它不能自动修改来源知识、研究判断、代码、schema、provider、公开导出、Git 或外部系统。公开 demo 始终只读，也不得寻找私人 sibling repo、私人 provider 或私人运行态。

## 为什么需要这个控制面

随着材料、关系、任务和投影增加，每次都全量重建会越来越慢，也越来越难解释。但无边界自动化更危险：一次错误推断可能被快速扩散到许多文件。控制面的目标是自动完成影响分析和验证，同时保留人的最终 authority。

```text
变化信号
  -> 只看路径的检测器
  -> 依赖计划器
  -> 候选计划
  -> 权限门
  -> 固定步骤执行器
  -> 验证
  -> 本地 checkpoint 或保持原 authority
```

## 三种不同操作

| 操作 | 含义 | 默认 authority |
| --- | --- | --- |
| 派生刷新 | 重建公开 demo、本地投影或其他可再生输出。 | 可再生，永不成为 canonical。 |
| 进化诊断 | 发现维护压力或可能的系统改进。 | 仅为候选。 |
| 治理变更 | 修改代码、schema、routing、provider、长期记忆、导出或外部状态。 | 仅在人工明确确认后执行。 |

不能用“刷新”的名称绕过治理权限。

## 风险等级

- **E0 Observe：** 路径检测、影响计划和只读检查；不写文件。
- **E1 Derived refresh：** 对具体计划确认后，运行固定、本地、可再生的写入。
- **E2 Candidate writeback：** 通过现有 Review 流程提出候选；不会自动升级。
- **E3 Canonical change：** 来源知识、研究判断或稳定工作流变更；始终人工。
- **E4 System or external change：** 代码、schema、provider、公开发布、Git、网络或其他外部动作；始终人工。

“自动维护”偏好永远不能授权 E3/E4。确认只覆盖页面显示的 plan ID；change token 或携带的未决候选来源变化后，旧确认必须被拒绝。风险级别按计划实际触及的最高权限边界计算，manifest 必须如实声明写入 owner。

checkpoint 记录执行后的 change token，因此派生输出不会再次触发同一轮安全刷新。如果安全子集完成后仍有人工任务，checkpoint 会保留仅含人工步骤的 pending candidate，并禁用再次安全运行。后续无关变化会继续携带该候选，不会静默覆盖。personal-vault 用户对当前精确 plan ID 选择“保留，稍后处理”时，只停止同一 change token 的重复提醒，候选仍会保留并在后续变化中继续带入；只有“拒绝候选”会清除它。公开 demo 仍为只读。

每次 E1 执行前，runner 只快照 manifest 声明的派生写入目标。如果必需步骤失败且无法归因写入，保留已变化的目标及快照、恢复清单以待核对；未变化目标无须重写。越界或符号链接写入目标会在任何命令运行前被拒绝。已选前提失败会阻断其依赖步骤，独立的已选工作可继续；直接选择子集不会启动未选前提。代码、schema 和人工审阅文档仍由 Git 负责回滚，不进入这套本地恢复机制。

## 固定步骤契约

每个维护步骤都声明路径触发条件、依赖、允许写入的位置、验证项、执行策略和成本。执行器只接受 `scripts/researchos_data/maintenance_pipeline.py` 中有版本记录的步骤 ID，不接受任意 shell 命令。

计划最多显示 40 条路径。变化超过 200 条、达到 tracked Markdown 的 25%，或控制契约本身变化时，计划升级为 full-review candidate。网络和高成本语义任务不会在启动时或安全刷新确认中执行。

## 本仓库与个人模式

- **公开 demo：** 只展示公开仓库自身的变化计划；刷新按钮禁用，所有写入 endpoint 继续被阻止。
- **Personal vault：** 只能运行本仓库 自己的、已确认的固定安全步骤；checkpoint 和本地投影由 Git 忽略。
- **永不允许：** 定位私人 sibling repo、发现私人 provider、读取私人原始材料，或把私人路径、checkpoint、日志复制进本仓库。

公开与私人安装可以共享协议，但不能共享运行态或来源集合。

## 用户界面

不增加新的聊天页。高级维护只显示一个折叠的系统任务对象：计划为什么出现、哪些路径受影响、哪些步骤可执行、哪些仍需人工、会安全写入哪里、哪些动作被阻止，以及验证结果。需要深度诊断时，通过随附 `system_stewardship` 能力的 `system_evolution_review` 任务复用现有 Work Session 和 Review。

## V1 边界与升级证据

V1 明确不包含后台 daemon、模型自改代码、自动长期写回、自动公开同步或自动 Git/网络动作。只有至少 20 次真实计划没有漏选依赖、失败可原子回退、确认负担可接受、公开安全检查持续通过，而且维护时间显著下降后，才考虑开放 opt-in 的定时 E1 刷新。

只要写入 owner 无法解释、plan 已过期、验证失败、公私来源混合，或系统维护开始挤占研究工作，就应停止自动化。

## 验证

```bash
python3 scripts/validate_evolution_control.py
python3 scripts/plan_evolution.py --changed dashboard/app.js
python3 -m unittest evals.test_evolution_control
python3 scripts/validate_public_safety.py
```
