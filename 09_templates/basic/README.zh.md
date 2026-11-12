# 基础卡片模板

一个库要用到的几类卡的空白骨架。每份骨架的 frontmatter 下面有一段简短的「填写说明」，写明文件放在哪里、每个值是什么意思；卡片写好后把说明删掉。填好的样子见[示例卡片](../../examples/starter-cards/zh-CN/README.md)，那里也讲了三层读法、成熟度和敏感性。

| 模板 | 卡片 | 放在 |
| --- | --- | --- |
| [research-identity.zh.md](research-identity.zh.md) | 研究身份摘要，整个库的入口 | `personal_vault/00_identity/` |
| [boundaries.zh.md](boundaries.zh.md) | 什么从不交给助手、什么不对外说、对 AI 工具的规定、谁来放行；任何东西外传之前读 | `personal_vault/00_identity/boundaries.md` |
| [capsule.zh.md](capsule.zh.md) | 方向摘要，一个方向的入口 | `personal_vault/01_knowledge/capsules/` |
| [project.zh.md](project.zh.md) | 项目 | `personal_vault/01_knowledge/projects/` |
| [paper.zh.md](paper.zh.md) | 论文或其他来源 | `personal_vault/01_knowledge/papers/` |
| [outputs-index.zh.md](outputs-index.zh.md) | 你所有的成果、各自的状态和能对外说什么；在 evidence 档读 | `personal_vault/01_knowledge/papers/outputs-index.md` |
| [decision.zh.md](decision.zh.md) | 决策 | `personal_vault/02_decisions/` |
| [style.zh.md](style.zh.md) | 做某一类任务的做法（写作、审稿、申请书、作图与报告、指导学生） | `personal_vault/03_cognition/style/<任务>.md` |
| [heuristic.zh.md](heuristic.zh.md) | 一条做研究的习惯 | `personal_vault/03_cognition/heuristics/` |
| [mental-model.zh.md](mental-model.zh.md) | 你对领域里某件事怎样运作的理解 | `personal_vault/03_cognition/mental_models/` |
| [person.zh.md](person.zh.md) | 人物；你自己的档案也用它 | `personal_vault/04_people/collaborators/`，或 `00_identity/profile.md` |
| [author-roles.zh.md](author-roles.zh.md) | 每项成果谁做了什么，只依据贡献声明或你自己说的；在 evidence 档读 | `personal_vault/01_knowledge/papers/author-roles.md` |
| [feedback.zh.md](feedback.zh.md) | 对学生或被指导者进展的反馈 | `personal_vault/04_people/feedback/` |
| [meeting.zh.md](meeting.zh.md) | 会议或其他事件 | `personal_vault/06_active_context/meetings/` |
| [review.zh.md](review.zh.md) | 你审一篇稿件的意见 | `personal_vault/06_active_context/reviews/` |
| [grant.zh.md](grant.zh.md) | 一份基金申请 | `personal_vault/06_active_context/grants/` |
| [message.zh.md](message.zh.md) | 一封学术邮件或消息的草稿 | `personal_vault/06_active_context/messages/` |

frontmatter 每个值写在一行里，后面不要加 `#` 注释：值后面的注释会被当成值的一部分读进去。上一层的四份完整模板（`../paper-template.md`、`../person-template.md`、`../project-template.md`、`../talk-template.md`）是同样的卡，只是多了几节可选的后期小节，等卡片跨项目使用时再加；先从这里的骨架开始。
