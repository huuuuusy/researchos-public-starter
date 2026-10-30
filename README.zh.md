<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# ResearchOS

**让科研判断始终属于研究者。**

**它是什么。** 放在你自己电脑上的一个"研究记忆"文件夹，加上几条命令。你跟 AI 助手跨很多次对话做研究时，它帮你记住之前得出的判断和依据；某个来源变了，它提醒你哪些结论要重新看，改不改由你决定。

**为什么需要它。** 三周前你读了一篇论文，得出"方法 A 比 B 好"。这个结论根据哪组实验、在什么条件下成立、还有什么没验证、下一步打算做什么，都散在聊天记录里。后来论文出了更正，你已经想不起哪些结论用过它；AI 助手也可能顺手把一句没有依据的说法写进了你的笔记。

**它怎么做。**

1. **研究写成卡片。** 论文卡、项目卡、合作者卡都是普通的 Markdown 文件，存在你自己电脑上。每条判断都写明依据（哪个文件的哪个版本）和适用范围。
2. **开工先跑 `today`。** 它列出要你决定的事。某个来源文件变了，比如你换上了更正后的论文，它会把依赖这个来源的判断标为待复核。
3. **让 AI 干活，但只收候选。** `context` 只挑这次需要的材料，`run` 生成一个任务包让你贴给任何助手，`collect` 把回答收回来作为候选，它不会自己改你的卡片。
4. **由你拍板。** 哪些候选留下、哪些拒绝，你说了算；收工跑 `close`，列出这次变了什么、还有什么没做完。

本仓库做到候选为止，从不写入你的卡片；[技术报告](docs/technical-report.zh.md)描述的原型多一步：研究者在终端确认之后才写入。它适合需要长期跟踪研究判断的个人研究者。

**一句话上手：对你的 AI 助手说一句话。** 打开 Claude Code、Codex 或其他能在你电脑上运行命令的助手，发送：

```text
帮我装好 ResearchOS（https://github.com/huuuuusy/researchos-public-starter），按它 AGENTS.md 里的 First Run 一步步带我设置，用中文和我交流。
```

助手会把它下载下来，先在虚构的例子上用几句话讲清它做什么，再问你的主页或 Google Scholar、几篇论文、合作者和一个正在做的项目，据此建好你自己的库。大约十五分钟，事先什么都不用读。写入前它会先把卡片清单给你看，所有内容都留在你电脑上一个 Git 忽略的文件夹里，不会推送到任何地方。没有装 git 的话，助手也可以从同一个页面下载 ZIP。

已经下载好了？在 Codex 或 Claude Code 里打开这个文件夹，说一句：「读一下 AGENTS.md，按 First Run 带我上手。」

**或者自己动手，10 分钟**

1. 在虚构数据上跑一遍演示：`python3 scripts/ros_demo.py --lang zh-CN`。
2. 自己逐条命令走一遍同样的会话（[用户手册第 3 节](docs/user-manual.zh.md#3-会话调度器与命令行检查)）。
3. 开始自己的库：`python3 scripts/ros_demo.py --init personal_vault --lang zh-CN`。

[首次上手说明](08_exports/public_starter/onboarding-step-by-step.zh.md)带你走完这三步，并写明每一步应该看到什么。

![来源变化时，系统把判断交回，保留、收窄或撤回由研究者决定：一个虚构的例子。](docs/figures/readme/keep-update-hold-zh.gif)

## 它是什么、不是什么

按文档里的说法，ResearchOS 是一个持续维护研究状态、本地为主的系统（研究状态指什么，见[你会遇到的词](docs/user-manual.zh.md#你会遇到的词)）。它是小型文件化工具，不是托管服务、自治科研系统、完整个人知识库、脱离证据的万能问答，也不是精致的 all-in-one 产品。

## 上手试一下

只需要 Python 3.10 或更高版本，不需要安装依赖、API key、数据库或服务器；CI 在 CPython 3.10 和 3.13 上测试。支持 macOS 与 Linux；Windows 请在 WSL（Windows Subsystem for Linux）中运行，因为它依赖的文件锁在原生 Windows 的 Python 中不可用。在仓库文件夹里运行演示，它在一份虚构研究图的临时副本上运行：

```bash
python3 scripts/ros_demo.py --lang zh-CN
```

![虚构演示上的一次会话，内容取自 python3 scripts/ros_demo.py --lang zh-CN 的输出。](docs/figures/readme/session-zh.gif)

来源卡片变化，依赖它的判断被标为待复核。研究者提出重新确认，输出只把它显示为拟议变化，不实际准入。收尾时复核仍待处理。输出里有几个词用的是特定意思，比如候选、准入、要求、挂起；[你会遇到的词](docs/user-manual.zh.md#你会遇到的词)每个用一句话说明。输出里写的 `ros …`，指 `python3 scripts/ros.py --root <文件夹> …`，文件夹就是存放研究图的那个目录。

也可以不用调度器，直接用 Claude Code、Codex 或其他文件感知 Agent 打开本文件夹，给出一个目标和一份来源；提示词见[用户手册第 2 节](docs/user-manual.zh.md#2-在-agent-客户端里走一个闭环)。

## 开始自己的

你自己的材料放在 `personal_vault/`，这是 clone 里一个被 Git 忽略的文件夹。下面这条命令从演示研究图复制出一份作为起点，不带演示留下的记录，也不带虚构的判断：

```bash
python3 scripts/ros_demo.py --init personal_vault --lang zh-CN
```

接着把虚构的承诺和卡片换成你自己的一项和一张，再运行 `python3 scripts/ros.py --root personal_vault today`。每一步怎么做、应该看到什么，见[首次上手说明](08_exports/public_starter/onboarding-step-by-step.zh.md)；字段说明见[用户手册第 5 节](docs/user-manual.zh.md#5-用自己的材料)。可选的 Dashboard 读取同一个文件夹。含有真实材料的 clone 不要推送到公开远程仓库。

## 文件夹里有什么

- `examples/scheduler-demo/` 和 `08_exports/public_starter/` 是虚构演示：前者是调度器用的研究图，后者是 Dashboard 的示例议程和上手示例。
- `personal_vault/` 放你自己的材料，由你创建，Git 忽略它。
- `00_identity/` 到 `06_active_context/` 是一个库的各层（身份、知识、决策、认知、人物、工作流、当前状态）。这里放的是各层说明和公开安全的方法笔记；`personal_vault/` 用同样的布局。
- `07_archive/` 存公开安全的历史，`09_templates/` 存卡片模板和数据契约，`corpus/` 保持为空（原始材料从不提交），`distilled/` 存简短的公开安全方法摘要。
- `scripts/`、`config/`、`dashboard/` 和 `evals/` 分别是命令行工具、运行配置、可选 Dashboard 和测试。

## 本仓库不做什么

本仓库只复制，随附数据都是虚构的。它从不准入任何东西：报告中的原型会写入已接受改动的地方，这里只显示计划中的改动，由你自己复制，文档里把这叫作复制回退。出厂 `config/ros.json` 设为 `runtime_scope: public_starter`。`ros` 写什么、`admit` 做什么、`runtime_scope` 取什么值才开启准入与派发、personal-vault 模式有何不同，见[用户手册第 3 节](docs/user-manual.zh.md#3-会话调度器与命令行检查)。可选的 Dashboard 和插件体系处于冻结状态。

## 接下来读什么

[文档索引](docs/README.zh.md)按新手需要的顺序列出各份指南，每份用一句话说明什么时候读。[AGENTS.md](docs/reference/AGENTS.zh.md) 约束文件感知助手在这里怎样工作。

技术报告（[中文源稿](docs/technical-report.zh.md) · [中文 PDF](docs/technical-report.zh.pdf) · [English PDF](docs/technical-report.en.pdf)）以风格化拼写 *ReSearchOS* 描述原型，包含正文第 1–8 节与附录 A–B；[补充说明 1–6](docs/technical-report-supplement.zh.md) 单独提供，不进入 PDF。报告未经同行评审，其中的主张不是本仓库的能力清单。

## 状态

本仓库是 V1.0.2，已于 2026-10-30 以 `v1.0.2` 发布（见 [V1.0.2 发布说明](docs/releases/v1.0.2.zh.md)与[更新记录](CHANGELOG.md)）。

## 如何引用

技术报告和本仓库一起存档在 Zenodo 的同一条记录里，Zenodo 把这条记录列为软件，标题是「ResearchOS Public Starter」。引用时请用 DOI [10.5281/zenodo.23769799](https://doi.org/10.5281/zenodo.23769799)，它始终指向最新版本；如果要精确引用这一版，用 [10.5281/zenodo.23806125](https://doi.org/10.5281/zenodo.23806125)。

> Hu, S. (2026). *ReSearchOS: A Reference Architecture for Sustained Human–AI Research* (Technical report, version 1.0.2). Zenodo. https://doi.org/10.5281/zenodo.23769799

```bibtex
@misc{hu2026researchos,
  author       = {Hu, Shiyu},
  title        = {{ReSearchOS}: A Reference Architecture for Sustained Human--{AI} Research},
  howpublished = {Technical report (not peer reviewed), version 1.0.2, Zenodo},
  year         = {2026},
  doi          = {10.5281/zenodo.23769799},
  url          = {https://github.com/huuuuusy/researchos-public-starter}
}
```

GitHub 页面上的「Cite this repository」按钮会根据 [CITATION.cff](CITATION.cff) 以它自己的 APA 和 BibTeX 格式给出这条引用。

## 许可与引用

ResearchOS 公开 starter 允许个人学习、个人研究、学术研究、教学、非商业评估，以及非商业学术再分发或二次开发；它不是采用 OSI 认可开源许可证发布的项目。超出上述范围的任何使用，包括任何商业使用，都需要事先取得书面许可；完整条款见 [LICENSE.md](LICENSE.md)，中文说明见 [COMMERCIAL_USE.zh.md](docs/reference/COMMERCIAL_USE.zh.md)。引用方式见[如何引用](#如何引用)；贡献、支持与安全渠道见[贡献指南](docs/reference/CONTRIBUTING.zh.md)、[支持](docs/reference/SUPPORT.zh.md)和[安全政策](docs/reference/SECURITY.zh.md)。这里的名字只指本项目，与使用相同或相近名字的其他项目、产品或公司没有关联。

由 [Shiyu Hu](https://huuuuusy.github.io/) 创建并维护。
