---
type: work_state
title: "注意力安排"
status: runtime
created: YYYY-MM-DD
updated: YYYY-MM-DD
sensitivity: internal
schema_id: researchos-attention-schedule-v1
---

<!-- 用法（填好后删除）
把本文件复制到你的仓库（传给 ros --root 的那个文件夹）里的 06_active_context/work_state/attention-schedule.md。
ros attend <承诺> today|tomorrow|date|park|complete-step 会给出这项承诺的条目；把它贴在文件末尾，或替换这项承诺原有的那一段。
ros today 读这个文件。公开 starter 里 ros 从不写它：条目由你贴入，或你同意后由助手贴入。
-->

# 注意力安排

## Agent Summary

只记短期注意力：哪项承诺在哪天看、哪些搁置到某个复看日、哪些已做完当前这一步。事实与判断仍在承诺清单和卡片里；这里的内容不改变承诺的状态、截止日期或下一步。

## 条目格式

每项承诺一段。标题由 `research_portfolio:` 加承诺 id 组成，下面每行一个值。`ros attend` 会给出整段，照原样复制，不要手打。各字段：

- `attention_date`：哪天看这项承诺（YYYY-MM-DD）；搁置期间为空。
- `review_date`：搁置的承诺回来再定的日子；可以为空。
- `today_order`：在今日里的先后；0 表示不排先后。
- `status`：scheduled、paused、waiting、needs_next_step、unscheduled 之一。
- `completed_step_hash`：由 `complete-step` 写入；承诺的下一步改动之前一直有效。
- `updated_at` 与 `last_action`：条目最后一次改动的时间与动作。

一项虚构承诺填好后的样子（尖括号代表真实 id，所以 ros 不会把这个示例当成条目）：

```markdown
### research_portfolio:<commitment-id>

- provider_id: research_portfolio
- item_id: <commitment-id>
- attention_date: 2026-09-21
- review_date:
- today_order: 0
- status: scheduled
- completed_step_hash:
- updated_at: 2026-09-21T09:00:00+08:00
- last_action: schedule
```

## 证据边界

- 本文件记录注意力放在哪里，不记录什么是真的。这里的日期不是截止日期，搁置也不等于放弃；二者都以承诺清单为准。
- 标题与 `provider_id`、`item_id` 对不上，或 id 不是承诺 id 的条目，会被忽略。
- 删掉一段，这项承诺就回到未安排；ros 不另存副本。

## Items

把条目贴在这一行下面。
