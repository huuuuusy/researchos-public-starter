# 示例卡片（中文）

这里有十二张虚构的卡片，讲的是同一件事：一位做视觉跟踪的研究者，在一次会上得知基准要改版，于是决定推迟一组实验；另有一张风格卡，记这位研究者怎样写这篇论文，一张边界卡记什么不能外传，两张索引记每项成果能对外说什么、谁做了什么。每张卡都可以照着改成你自己的；对应的空白骨架在 [`09_templates/basic/`](../../../09_templates/basic/README.zh.md)。这些卡只供参照，不会被复制进你的 `personal_vault/`。

**不做视觉跟踪也一样用。** 示例的领域是视觉跟踪，换成别的研究，这些卡照样对得上。做问卷调查时，一张「论文卡」可以记一版问卷，例子里的「基准改版」就相当于问卷又发了一轮或改了题目；做档案研究时，论文卡可以记一份档案目录或校勘本，「基准改版」相当于档案馆发布了更正后的目录；做实验室研究时，论文卡可以记一份实验方案，「基准改版」相当于方案做了修订。项目卡、决策卡、人物卡和会议卡不用换名字，照样记你的项目、决定、合作者和会议。

| 卡片 | 放在哪里 | 记什么 |
| --- | --- | --- |
| [研究身份摘要](00_identity/research-identity.md) | `00_identity/` | 你是谁、现在的主线、你的做法；助手每次先读这一页 |
| [边界卡](00_identity/boundaries.md) | `00_identity/` | 什么从不交给助手、什么不对外说、对 AI 工具的规定、谁来放行 |
| [方向摘要](01_knowledge/capsules/occlusion-tracking-capsule.md) | `01_knowledge/capsules/` | 一个方向的入口：现在的要点，做什么任务读哪张卡 |
| [成果索引](01_knowledge/papers/outputs-index.md) | `01_knowledge/papers/` | 每项成果的状态、能对外说什么、暂时不能说什么 |
| [项目卡](01_knowledge/projects/occlusion-tracking.md) | `01_knowledge/projects/` | 研究问题、当前进度、已有结果 |
| [论文卡](01_knowledge/papers/example-benchmark.md) | `01_knowledge/papers/` | 读的是哪个版本、论文说了什么、你的看法 |
| [决策卡](02_decisions/2026-09-22-wait-for-benchmark-v2.md) | `02_decisions/` | 备选方案、为什么这样选、接受的风险 |
| [启发式卡](03_cognition/heuristics/check-benchmark-version-first.md) | `03_cognition/heuristics/` | 你做研究的一条习惯：规则、什么时候用、什么时候不用 |
| [风格卡](03_cognition/style/writing.md) | `03_cognition/style/` | 你做某一类任务的做法，这里是写作：每条写明为什么、怎么用和出处，和助手的推测分开 |
| [人物卡](04_people/collaborators/lin-ke.md) | `04_people/collaborators/` | 有来源的基本情况、有证据的关系、交往记录 |
| [作者角色卡](01_knowledge/papers/author-roles.md) | `01_knowledge/papers/` | 每项成果谁做了什么，每条带出处 |
| [会议卡](06_active_context/meetings/2026-09-22-benchmark-sync.md) | `06_active_context/meetings/` | 一次会议：谁说了什么、你的看法、定下的事、行动项 |

边界卡在任何东西外传之前读：报告、申请书、给外面的人写信、导出、审稿。成果索引和作者角色卡在 evidence 档读，正式写作、写申请书或简历之前用来核对说法和贡献。

## 三层读法

助手读你的库时由浅入深，每一层够用就停。卡片的写法要配合这一点。

- **第一层：摘要。** frontmatter 和 `Agent Summary`。这一段要能单独读懂：是什么、现在怎样、什么时候读、不用于什么。研究身份摘要是整个库的入口，方向摘要是一个方向的入口，都把任务指到具体的卡。摘要的表格里列了卡名，但打包一页方向摘要只交出这一页；所以助手要用哪张卡，就用 `python3 scripts/ros.py --root personal_vault context <卡片路径>` 逐张取来，上下文回执里才会记上它。
- **第二层：卡片正文。** 任务需要细节时才读。
- **第三层：证据。** 原文、笔记原件、实验记录，留在原处，卡片的「证据边界」写明位置，默认不读。只有正式写作或对外使用前要核对时才去读。

这三层说的是在一张卡里读多深，和读取档 quick / standard / evidence 不是一回事。读取档决定读哪几张卡：`python3 scripts/plan_context.py <任务> --vault personal_vault --mode quick|standard|evidence` 会按档列出助手要读你的哪些卡，以及哪些卡你还没写。

## 成熟度

每类卡用一个字段标它长到了哪一步：论文和报告卡用 `analysis_state`（M1 到 M3），项目卡用 `project_maturity`（I0 到 I3），人物卡用 `relationship_maturity`（R0 到 R3），方向摘要用 `group_level`（G0 到 G2）；启发式卡用 `confidence` 和 `status`（provisional、stable），风格卡只用 `status`（provisional、confirmed）。只有来源、链接和确认变多了才升级，字数变多不算。这些代号（如 `M1_registered`、`I1_sandbox`、`G2_direction_abstraction`）都是可选的标签，不想管就留着骨架里的默认值：`ros` 不看它们，只有可选的 Dashboard 用它们显示一张卡长到了哪一步。各级的含义统一写在[卡片成熟度说明](../../../08_exports/public_starter/onboarding-card-maturity-rubric.zh.md)里。

## 敏感性

`sensitivity` 决定 `ros context` 给助手打包时带不带这张卡：

- `public`、`internal`：直接带上。论文、项目、决策、摘要、启发式卡、风格卡、边界卡和成果索引用 `internal`。
- `sensitive`：助手运行 `ros context` 时不带。写真实的人（包括作者角色卡）、记录别人在会上说的话，用这个标签。助手说某张卡被排除时，应当告诉你是这个原因，不要改为直接打开文件；任务确实需要时，你在自己的终端运行 `python3 scripts/ros.py --root personal_vault context <卡片>`，回答 `y`，再只把任务需要的部分复制给助手。
- `private`：从不打包。只用于你不想让 `ros context` 交给助手的卡。

这个标签挡不住助手直接打开文件，见 README 里「你的材料会去哪里」一段。

## 正文里的几种标记

- **（事实）**：有来源可查的内容。
- **我的看法**：你自己的理解，和别人说的分开写。
- **助手的补充（未经我确认）**：助手推测的内容，确认之前不当真。
- **待核**：还没确认的事。

想把「我的看法」留成长期判断，助手先用 `ros propose judgment` 提交；你同意后，助手把 `ros admit` 打印出的改动贴进卡片，你再在自己的终端用 `ros admit --confirm` 确认。示例卡里有意不放判断块；判断怎样在来源变化后回来等复核，见用户手册第 3 节的演示。认知层的卡（风格卡、启发式卡）、研究身份摘要和边界卡写的是你的做法，助手起草后要先给你看，你同意了才写。
