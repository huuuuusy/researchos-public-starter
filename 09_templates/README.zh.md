<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# 模板层

保存可复用模板、标准提示词、卡片格式和数据契约，帮助本仓库与报告中的原型保持结构一致。

- [`basic/`](basic/README.zh.md)：从这里开始。每类卡的简短骨架，中英各一份：研究身份摘要、方向摘要、项目、论文、决策、做法、启发式、心智模型、人物、反馈、会议、审稿、基金申请和邮件。填好的样子见 [examples/starter-cards/](../examples/starter-cards/zh-CN/README.md)。
- `paper-template.md`、`person-template.md`、`project-template.md`、`talk-template.md`：和 `basic/` 里对应的骨架是同一张卡（报告卡沿用同样的写法），后面多几节可选的后期小节，例如公开边界、这张卡证明不了什么、下一步怎样升级。卡片跨项目使用时再加这几节；不存在第二套模板。
- `attention-schedule.md` / `attention-schedule.zh.md`：注意力安排，放在 `personal_vault/06_active_context/work_state/attention-schedule.md`。`ros attend` 给出要贴进去的条目，`ros today` 列出排在今天的承诺。
- `new-project-intake-card-template.md`、`research-expression-task-brief.md`、`safe-export-template.md`、`eval-case-template.md`、`self-evolution-report-template.md`、`memory-update-report-template.md`、`workflow-template.md`：项目接入、表达任务、安全导出、评估、自我进化和写回模板。
- `derived-work-artifact-template.md` / `derived-work-artifact-template.zh.md`：用于私人/本地 vault 中一次具体 PPT、会议、申请、分析或 revision 工作稿的工作期与归档期模板。
- `standard-agent-prompts.zh.md`：中文标准 Agent 提示词，覆盖个人接入、论文卡片、合作者抽取、报告卡片、关系卡片、计划卡片和收件箱处理。
- `standard-agent-prompts.en.md`：英文标准 Agent 提示词。
- `data_contracts/`：生成数据和前后端交互的数据契约。
  - `data_contracts/researchos-extension-contract-v1.md`：新增类别、资源对象、工作流对象和 dashboard surface 前的扩展协议。
