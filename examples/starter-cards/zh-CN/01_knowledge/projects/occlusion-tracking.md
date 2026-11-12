---
type: project
title: 遮挡鲁棒跟踪（虚构）
status: active
project_maturity: I2_active_mount
role: 第一作者，负责方法比较和论文主张
related_people:
  - 04_people/collaborators/lin-ke.md
related_papers:
  - 01_knowledge/papers/example-benchmark.md
sensitivity: internal
updated: 2026-09-22
---

# 遮挡鲁棒跟踪（虚构）

## Agent Summary

比较方法 A 和方法 B 在遮挡条件下的跟踪表现，目标是一篇论文。标准划分上 A 好于 B；重度遮挡还没测，等基准第 2 版。安排实验、写论文、回答「A 好在哪」时读这张卡；不用于对外报告数字，数字以实验记录为准。这是一个虚构项目，只用来演示项目卡的写法。

## 核心问题

方法 A 在重度遮挡下还好于方法 B 吗？

## 当前状态（2026-09-22）

- 标准划分的比较已完成。
- 重度遮挡的比较暂缓，等基准第 2 版，原因见 [决策卡](../../02_decisions/2026-09-22-wait-for-benchmark-v2.md)。

## 已有结果（事实）

- 标准划分：A 71.2，B 68.4（实验记录 run-0915，2026-09-15）。
- 重度遮挡：尚未测。

## 相关人物与材料

- 基准：[Example Occlusion Benchmark](../papers/example-benchmark.md)，维护者 [林可](../../04_people/collaborators/lin-ke.md)。
- 方向入口：[遮挡跟踪方向摘要](../capsules/occlusion-tracking-capsule.md)。

## 待核

- A 的优势来自遮挡处理，还是来自更好的初始化？现有结果分不开这两种可能。

## 证据边界

- 这张卡概括了：项目问题、当前进度、标准划分上的一组结果。
- 没有核对：run-0915 是否用了和 B 相同的随机种子。
- 正式使用前要查（默认不读）：实验记录 `~/Experiments/occlusion/run-0915/`。
