<p align="right">
  <a href="RELATED_RESEARCH_TOOLS.md">English</a> | <strong>中文</strong>
</p>

# 相关科研工具与资源清单

ResearchOS 只是整个科研工具生态中的一个选择。它可能适合希望用本地文件和明确权威协议管理长期 AI 协作的科研人员，但不会适合所有人、所有任务。对有些用户来说，文献管理器、notebook、电子实验室笔记本、可复现平台、科研 Agent，或几个小工具的组合会更合适。

本页把这些选择公开出来，而不是回避相邻项目。

> **快照说明：**本页最后核查于 **2026-07-25**。它是经过筛选、没有排名的参考清单，不是完整目录、背书、采购建议，也不承诺持续更新。项目功能、许可、维护状态、数据处理和安全条件都可能变化；采用前请回到官方来源复核。收录不代表认可，遗漏也不代表否定。

## 先根据你真正的问题选择

| 主要需求 | 先看哪一类 | ResearchOS 可能增加的价值 |
| --- | --- | --- |
| 自动搜索、实验、分析或写报告 | 科研 Agent 与执行 runtime | 提供外部审阅和长期写回边界 |
| 对论文或网页做带引用问答 | 文献与来源工作台 | 把经过审阅的判断带到后续项目 |
| 给 Agent 增加跨会话记忆或知识图谱 | Memory 与知识基础设施 | 决定什么有资格成为权威科研记忆 |
| 管理引用、notebook、数据、实验或实验室记录 | 成熟的生命周期与可复现工具 | 连接少量关键判断，而不替代专用工具 |
| 交换机器可读 provenance 或研究对象包 | RO-Crate、PROV-O 等标准 | 把本地 authority transition 映射到共同 vocabulary |
| 浏览更广的 AI-for-research 生态 | Awesome 与综述型清单 | 提供一组更小、带解释的相邻入口 |

## 科研 Agent 与执行 Runtime

| 项目 | 当前主要重点 | 适合什么时候看 | 采用前核对 |
| --- | --- | --- | --- |
| [ResearchClaw](https://github.com/ymx10086/ResearchClaw) | 本地优先的科研 runtime，覆盖项目、工作流、claim/evidence、实验、渠道与自动化 | 需要更宽的执行面和持久服务 | Alpha 状态、部署、provider 成本和权限范围 |
| [Agent Laboratory](https://github.com/SamuelSchmidgall/AgentLaboratory) | 文献、实验、报告写作组成的多 Agent 工作流，并提供 copilot 模式 | 想试验端到端科研流水线 | 支持的任务/模型、计算成本，以及对实验和引用的人工核验 |
| [The AI Scientist](https://github.com/SakanaAI/AI-Scientist) | 从 idea、实验和图表推进到论文与自动评审的研究原型 | 自动科学发现本身就是研究对象 | 生成结果不等于经过验证的科学结论 |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | 跨模型与数据源的深度网络调研和带来源报告 | 核心需要是一次有边界的调研报告 | 搜索/API 依赖、来源质量、引用核验和数据处理 |
| [Mira](https://github.com/MIRA-Intelligence/mira) | 面向医学 AI 研究的轻量执行助手 | 需要较窄的领域科研支持 | 领域覆盖、sandbox、依赖和医学数据边界 |

## 文献与来源工作台

| 项目 | 当前主要重点 | 适合什么时候看 | 采用前核对 |
| --- | --- | --- | --- |
| [Open Notebook](https://github.com/lfnovo/open-notebook) | 可自托管的 notebook、source、chat 和 transformation | 想围绕一组来源阅读、整理和提问 | 模型/存储配置、解析质量和引用粒度 |
| [SurfSense](https://github.com/MODSetter/SurfSense) | 面向网页和连接来源的研究工作台，提供 API 与 MCP | 需要把多种来源连接到同一个检索空间 | connector 权限、认证、外发数据和团队边界 |
| [PaperQA2](https://github.com/Future-House/paper-qa) | 科学文档 RAG 和带引用问答 | 需要围绕论文集合回答具体问题 | 语料覆盖、检索设置，以及引用是否真的支持 claim |
| [STORM / Co-STORM](https://github.com/stanford-oval/storm) | 多视角知识策展、讨论、mind map 和带引用报告 | 想探索主题或做人机共同知识策展 | 搜索来源、事实核验，以及一次讨论和长期判断的边界 |
| [OpenScholar](https://github.com/akariasai/openscholar) | 科学文献综合的 retrieval-augmented LM、检索与评测资源 | 研究或部署科学问答和文献综合方法 | 本地索引资源、API 依赖，以及已评测与计划用途的区别 |

## Agent Memory 与本地知识基础设施

这些项目大多是可组合组件或通用工作空间，不是 ResearchOS 的一对一替代品。

| 项目 | 当前主要重点 | 适合什么时候看 | 采用前核对 |
| --- | --- | --- | --- |
| [SwarmVault](https://github.com/swarmclawai/swarmvault) | 本地 Markdown/wiki、知识图谱、RAG 和持久 Agent memory | 多个 coding agent 需要共用可读的本地知识库 | 生成内容确认、索引可重建性和迁移 |
| [PilotDeck](https://github.com/OpenBMB/PilotDeck) | 任务型 Agent workspace、white-box memory 和多项目路由 | 需要跨项目、跨客户端的通用 Agent 工作空间 | always-on 权限、workspace 隔离和回滚语义 |
| [Mem0](https://github.com/mem0ai/mem0) | 用户、session 与 Agent 的记忆层 | 正在开发需要跨会话记忆的 Agent | 开源/托管能力差异、默认模型依赖、隐私和删除语义 |
| [Letta](https://github.com/letta-ai/letta) | 带高级记忆的 stateful Agent 平台 | 正在构建长期保持并修改状态的 Agent | Agent 的记忆写入权、部署形态和长期数据治理 |
| [Graphiti](https://github.com/getzep/graphiti) | 面向 Agent 的实时、时序知识图谱 | 变化中的实体关系和时间检索很重要 | 图与模型依赖、抽取错误和事实更新策略 |

## 研究生命周期与可复现性

| 项目 | 当前主要重点 | 适合什么时候看 | 采用前核对 |
| --- | --- | --- | --- |
| [Zotero](https://github.com/zotero/zotero) | 文献采集、引用管理、PDF 阅读和同步生态 | 核心问题是文献库和引用 | 同步、插件兼容、附件和团队库边界 |
| [JupyterLab](https://github.com/jupyterlab/jupyterlab) | 可扩展的交互式与可复现计算环境 | notebook、代码、终端和数据分析是日常核心 | 环境锁定、执行顺序、依赖和 notebook 可复现性 |
| [DVC](https://github.com/treeverse/dvc) | 数据版本、流水线和机器学习实验 | 需要追踪大型数据、模型和实验产物 | remote storage、团队工作流和数据访问控制 |
| [OSF](https://github.com/CenterForOpenScience/osf.io) | 开放科学项目、注册、材料和协作 | 需要共享、注册或归档研究工作 | 公开/私有设置、机构政策、合规和长期存档 |
| [Renku](https://github.com/SwissDataScienceCenter/renku) | 跨数据、代码和计算环境的协作可复现分析 | 需要为科研人员、团队或课程配置计算环境 | 部署复杂度、计算资源、connector 和平台治理 |
| [eLabFTW](https://github.com/elabftw/elabftw) | 开源电子实验室笔记本与实验室记录 | 实验、模板、库存或实验室流程是核心 | 合规、备份、访问控制、签名和机构部署 |

## Provenance 与研究对象标准

| 项目或标准 | 当前主要重点 | 适合什么时候看 | 采用前核对 |
| --- | --- | --- | --- |
| [RO-Crate](https://github.com/ResearchObject/ro-crate) | 用 JSON-LD 打包研究数据、代码、文档与上下文 | 需要机器可读、可交换的研究工件包 | profile、术语映射、验证和仓库支持 |
| [W3C PROV-O](https://www.w3.org/TR/prov-o/) | 用 entity、activity 和 agent 表达 provenance 的 W3C Recommendation | 需要跨系统 provenance 语义 | 是否需要完整 ontology，还是较小的映射子集 |

ResearchOS 不把自己的 provenance 字段表述为新标准。如果未来需要跨系统交换，优先显式映射成熟标准，而不是发明一套孤立 vocabulary。

## 更广的 Curated Lists

| 清单 | 覆盖范围 |
| --- | --- |
| [Awesome-AI-Research](https://github.com/Research-Equality/awesome-ai-scientists) | AI-native research systems、基础设施、workflow modules、benchmarks、surveys 和 datasets 的分层地图 |
| [Awesome-AI-Scientists](https://github.com/tsinghua-fib-lab/Awesome-AI-Scientists) | 结合综述组织 AI Scientist 的角色、人机协作、领域和更广影响 |
| [Awesome AI for Science](https://github.com/ai4s-research/awesome-ai-for-science) | 跨学科 AI-for-science 工具、论文、数据集、框架和应用 |

这些清单更适合浏览广而变化快的生态。ResearchOS 保留这份较小的页面，是为了公开替代选择、解释类别并帮助读者找到入口，而不是复制一个持续维护的大型 Awesome 仓库。

## 为什么 ResearchOS 仍然保持窄定位

只有当下面这份合同重要时，ResearchOS 才真正增加价值：

```text
有边界的来源和本地 Markdown
  -> 文件感知 Agent 读取并提出候选
  -> 研究者审阅证据与影响
  -> 明确批准后写回
  -> 验证
  -> 长期科研记忆
```

ResearchOS 只治理长期研究状态：谁拥有判断、什么可以变化、什么证据支持变化，以及中断后如何接续。它不与 ResearchClaw 这类广义科研 runtime 竞争覆盖面；与 SwarmVault 这类本地 Markdown/图谱工作台功能重叠很强，但把治理对象收窄为长期科研判断和写回权；不扩张成 PilotDeck 那样的通用 Agent 平台；也不像 Mira 那样提供领域实验栈。可以成立的主张是这套组合起来的权威契约：文件感知 Agent 可以读取和提出候选，只有经研究者明确批准并验证的状态变化才成为长期研究记忆。这是工程设计主张，不是效率更优的证据。

如果上面的成熟工具已经解决了你的实际问题，就直接使用它，或把它与其他工具组合。ResearchOS 不要求替代它们。它更窄的角色是：在长期 AI 协作中保留研究者对判断的所有权，并显式区分候选、证据、权威、隐私和写回边界。

欢迎通过 issue 或 pull request 提交纠错和补充。建议新增条目时，请说明类别、官方入口、主要用途，以及科研人员采用前最应该核对的边界。
