<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# 当前状态层

本目录只记录公开 demo 的当前状态和下一步，应保持短、清楚、像路线图。

当前产品行为由 `docs/` 和 `05_workflows/` 中的 owner 文档负责；版本历史进入 `docs/releases/`，确有独立价值且公开安全的迁移证据进入 `07_archive/`。不要在这里新增带日期的私有系统审计或重复实现清单。

状态规则：

| 状态 | 含义 |
| --- | --- |
| `active` | 当前 demo 路线或下一步。 |
| `supporting` | 某个页面或 validator 的背景材料。 |
| `superseded` | 只作历史证据，不作为新实现清单。 |

不要把真实项目状态、私人任务、合作者策略、审稿记录或未公开论文细节写入本仓库。

一次具体 PPT、会议、申请、分析或 revision 产生的工作稿，只有在用户自己的私人/本地 vault 中仍有明确消费者、下一步或具体等待事件时，才可以留在这里。关闭时按[阶段性派生工作产物生命周期](../05_workflows/research_management/derived-work-artifact-lifecycle.zh.md)处理：先提炼长期内容，再把确有独立历史价值的完整稿归入 `07_archive/task_artifacts/`。

公开仓库不再跟踪空的 Dashboard 收件箱。personal-vault 操作会按需创建本地 `ui-*` 运行态文件；`.gitignore` 会阻止它们进入仓库。

在你自己的库里，`personal_vault/06_active_context/` 放承诺总表（`research-portfolio.md`）和 `meetings/` 下的会议记录这类短期记录。骨架：[`09_templates/basic/meeting.zh.md`](../09_templates/basic/meeting.zh.md)；示例：[会议卡](../examples/starter-cards/zh-CN/06_active_context/meetings/2026-09-22-benchmark-sync.md)。
