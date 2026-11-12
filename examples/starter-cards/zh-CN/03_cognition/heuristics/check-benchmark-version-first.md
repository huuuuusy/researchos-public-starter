---
type: heuristic
title: 比较之前先确认基准版本（虚构）
domain: 实验评测
confidence: medium
status: provisional
related_examples:
  - 02_decisions/2026-09-22-wait-for-benchmark-v2.md
sensitivity: internal
updated: 2026-09-22
---

# 比较之前先确认基准版本（虚构）

## Agent Summary

一条做实验时的习惯：跑方法比较之前，先确认基准的协议版本，以及近期会不会改版。规划实验、决定先跑哪组比较时读这张卡；它是经验做法，不是规定。这是一条虚构的启发式，只用来演示认知层卡片的写法。

## 规则

比较之前，先确认基准用的是哪一版协议、近期会不会改。会改的，先问清改什么，再决定现在跑还是等。

## 为什么

划分一变，旧版本上的结果就不能直接和新版本比，跑了也要重跑。

## 什么时候用

- 基准由别人维护，而且还在更新。
- 比较结果要写进论文。

## 什么时候不用

- 只是快速试一下方法能不能跑通。
- 基准已经冻结，多年没有改过。

## 例子

- 2026-09-22 决定重度遮挡比较等基准第 2 版，见 [决策卡](../../02_decisions/2026-09-22-wait-for-benchmark-v2.md)。

## 风险

- 等得太久会拖住进度，所以每次等都要定一个退路日期。

## 证据边界

- 这条习惯目前只有一个例子支撑，`confidence` 是 medium，`status` 是 provisional。例子多了、被证实有用，再改成 stable。
