---
type: decision
title: 重度遮挡比较等基准第 2 版再跑（虚构）
date: 2026-09-22
status: active
related_projects:
  - 01_knowledge/projects/occlusion-tracking.md
related_papers:
  - 01_knowledge/papers/example-benchmark.md
related_people:
  - 04_people/collaborators/lin-ke.md
sensitivity: internal
updated: 2026-09-22
---

# 重度遮挡比较等基准第 2 版再跑（虚构）

## Agent Summary

方法 A、B 的重度遮挡比较，决定等 Example Occlusion Benchmark 第 2 版发布后再跑，不在第 1 版上先跑。最大的风险是第 2 版晚于论文目标日期，为此留了 11-15 这个退路。重新安排遮挡实验时读这张卡。这是一个虚构的决策，只用来演示决策卡的写法。

## 背景（事实）

2026-09-22 的线上会上，林可说第 2 版会把重度遮挡的阈值从 60% 提到 70%，预计年底前发布。见 [会议卡](../06_active_context/meetings/2026-09-22-benchmark-sync.md)。

## 要决定的问题

重度遮挡的比较现在就跑，还是等第 2 版？

## 备选方案

1. 现在在第 1 版上跑，第 2 版出来后再跑一遍。
2. 自己按 70% 的阈值重新划分第 1 版的数据。
3. 等第 2 版发布再跑。

## 选择与理由

选 3。方案 1 要跑两遍，而且第 1 版的结果最终不会用在论文里。方案 2 的划分没法和别人的结果比较。

## 接受的风险

论文目标日期是 2026-12-01，第 2 版可能来不及。退路：11-15 前第 2 版还没发布，就在第 1 版上跑，论文里写明阈值。

## 预期结果

第 2 版在 11 月中旬前发布，比较一次跑完。

## 实际结果

（事后补。）

## 证据边界

- 这张卡记录了：当时的选项和理由。
- 依据的是口头消息，第 2 版的发布时间和阈值都还没有书面确认。
