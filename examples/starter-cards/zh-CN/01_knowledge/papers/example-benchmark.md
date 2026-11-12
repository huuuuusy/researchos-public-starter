---
type: paper
title: Example Occlusion Benchmark（虚构）
authors: 林可等（虚构）
venue: 某会议 2025（虚构）
version: 协议第 1 版
public_boundary: published
analysis_state: M2_refined_read
related_people:
  - 04_people/collaborators/lin-ke.md
related_projects:
  - 01_knowledge/projects/occlusion-tracking.md
source: ~/Papers/example-occlusion-benchmark-v1.pdf（本机，不放进库里）
sensitivity: internal
updated: 2026-09-22
---

# Example Occlusion Benchmark（虚构）

## Agent Summary

一个按轻度、中度、重度三档遮挡划分的跟踪基准，现在用的是协议第 1 版，已精读。遮挡跟踪项目的比较都在它上面做。协议改版时先更新这张卡，依赖它的判断会回来等复核。不用于回答目标长时间消失后重新找回的问题。这是一个虚构的基准，只用来演示论文卡的写法。

## 基本信息（事实）

- 作者：林可等。发表于某会议 2025。
- 版本：协议第 1 版。重度遮挡指目标被遮住 60% 以上。
- 原文：本机 PDF，路径见 frontmatter 的 `source`。

## 论文说了什么（事实）

- 三档遮挡，每档各有一个测试划分（原文第 3 节）。
- 评价指标沿用标准的成功率和精度，没有新指标（原文第 4 节）。
- 遮挡比例是人工标注的，档与档的边界附近有争议样本（原文第 5 节自己提到）。

## 我的看法

它按遮挡程度分了档，适合回答「方法在遮挡下还好不好」。场景以街景为主，室内结果不能直接外推。

## 和我的项目的关系

- 遮挡跟踪项目的标准划分结果来自这里。重度遮挡比较等第 2 版，见 [决策卡](../../02_decisions/2026-09-22-wait-for-benchmark-v2.md)。

## 待核

- 第 2 版的阈值（会上听说是 70%），等协议文本出来后核对，再改上面的「版本」一条。

## 证据边界

- 这张卡概括了：协议第 1 版的划分方式和论文自己承认的局限。
- 没有核对：补充材料里的逐档样本数。
- 引用前要查（默认不读）：PDF 原文第 3 至 5 节。
