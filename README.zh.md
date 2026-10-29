<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# ResearchOS

**让科研判断始终属于研究者。**

**最简单的用法：对你的 AI 助手说一句话。** 打开 Claude Code、Codex 或其他能在你电脑上运行命令的助手，发送：

```text
帮我装好 ResearchOS（https://github.com/huuuuusy/researchos-public-starter），按它 AGENTS.md 里的 First Run 一步步带我设置，用中文和我交流。
```

助手会把它下载下来，先在虚构的例子上用几句话讲清它做什么，再问你的主页或 Google Scholar、几篇论文、合作者和一个正在做的项目，据此建好你自己的库。大约十五分钟，事先什么都不用读。写入前它会先把卡片清单给你看，所有内容都留在你电脑上一个 Git 忽略的文件夹里，不会推送到任何地方。没有装 git 的话，助手也可以从同一个页面下载 ZIP。

已经下载好了？在 Codex 或 Claude Code 里打开这个文件夹，说一句：「读一下 AGENTS.md，按 First Run 带我上手。」

ResearchOS 让长期研究中的问题、证据、判断和下一步保持相连，这些内容都以普通文件存在你自己的电脑上。它面向个人科研人员，用来让判断在工具、项目和时间之间保持连续。

**或者自己动手，10 分钟**

1. 在虚构数据上跑一遍演示：`python3 scripts/ros_demo.py --lang zh-CN`。
2. 自己逐条命令走一遍同样的会话（[用户手册第 3 节](docs/user-manual.zh.md#3-会话调度器与命令行检查)）。
3. 开始自己的库：`python3 scripts/ros_demo.py --init personal_vault --lang zh-CN`。

[首次上手说明](08_exports/public_starter/onboarding-step-by-step.zh.md)带你走完这三步，并写明每一步应该看到什么。

![来源变了，哪部分保留、更新或挂起，由研究者决定：一个虚构的例子。](docs/figures/readme/keep-update-hold-zh.gif)

## 为什么要有它

研究跨过许多会话，只把眼下这一步做对还不够：从前面带下来的东西是否仍然成立，必须核查。某份来源一变，ResearchOS 会显示它影响哪些判断和下一步，再由你决定保留、更新还是挂起。任何 Agent 或模型都可以读取和提出候选，但只有你决定什么成为长期研究记忆。

按文档里的说法，ResearchOS 是一个持续维护研究状态、本地为主的系统（研究状态指什么，见[你会遇到的词](docs/user-manual.zh.md#你会遇到的词)）。它是小型文件化工具，不是托管服务、自治科研系统、完整个人知识库、脱离证据的万能问答，也不是精致的 all-in-one 产品。

## 上手试一下

只需要 Python 3.10 或更高版本，不需要安装依赖、API key、数据库或服务器；CI 在 CPython 3.10 和 3.13 上测试。支持 macOS 与 Linux；Windows 请在 WSL（Windows Subsystem for Linux）中运行，因为它依赖的文件锁在原生 Windows 的 Python 中不可用。在仓库文件夹里运行演示，它在一份虚构研究图的临时副本上运行：

```bash
python3 scripts/ros_demo.py --lang zh-CN
```

![虚构演示上的一次会话，内容取自 python3 scripts/ros_demo.py --lang zh-CN 的输出。](docs/figures/readme/session-zh.gif)

来源卡片变化，依赖它的判断被标为待复核。研究者提出重新确认，公开 starter 只把它显示为拟议变化，不实际准入。收尾时复核仍待处理。输出里有几个词用的是特定意思，比如候选、准入、要求、挂起；[你会遇到的词](docs/user-manual.zh.md#你会遇到的词)每个用一句话说明。输出里写的 `ros …`，指 `python3 scripts/ros.py --root <文件夹> …`，文件夹就是存放研究图的那个目录。

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

## 公开版的边界

本仓库是 ResearchOS 公开 starter，即私有原型的只复制公开版，随附数据都是虚构的。它从不准入任何东西：私有原型会写入已接受改动的地方，starter 只显示计划中的改动，由你自己复制，文档里把这叫作复制回退。出厂 `config/ros.json` 设为 `runtime_scope: public_starter`。`ros` 写什么、`admit` 做什么、`runtime_scope` 取什么值才开启准入与派发、personal-vault 模式有何不同，见[用户手册第 3 节](docs/user-manual.zh.md#3-会话调度器与命令行检查)。可选的 Dashboard 和插件体系处于冻结状态。

## 接下来读什么

[文档索引](docs/README.zh.md)按新手需要的顺序列出各份指南，每份用一句话说明什么时候读。[AGENTS.md](docs/reference/AGENTS.zh.md) 约束文件感知助手在这里怎样工作。

技术报告（[中文源稿](docs/technical-report.zh.md) · [中文 PDF](docs/technical-report.zh.pdf) · [English PDF](docs/technical-report.en.pdf)）以风格化拼写 *ReSearchOS* 描述私有原型，包含正文第 1–5 节与附录 A–B；[补充说明 1–6](docs/technical-report-supplement.zh.md) 单独提供，不进入 PDF。报告未经同行评审，其中的主张不是公开版的能力清单。

## 状态

本仓库是 V1.0，已于 2026-10-29 以 `v1.0.0` 发布（见 [V1.0 发布说明](docs/releases/v1.0.0.zh.md)与[更新记录](CHANGELOG.md)）。

## 许可与引用

ResearchOS 公开 starter 允许个人学习、个人研究、学术研究、教学、非商业评估，以及非商业学术再分发或二次开发；它不是采用 OSI 认可开源许可证发布的项目。超出上述范围的任何使用，包括任何商业使用，都需要事先取得书面许可；完整条款见 [LICENSE.md](LICENSE.md)，中文说明见 [COMMERCIAL_USE.zh.md](docs/reference/COMMERCIAL_USE.zh.md)。引用软件请用 [CITATION.cff](CITATION.cff)；贡献、支持与安全渠道见[贡献指南](docs/reference/CONTRIBUTING.zh.md)、[支持](docs/reference/SUPPORT.zh.md)和[安全政策](docs/reference/SECURITY.zh.md)。这里的名字只指本项目，与使用相同或相近名字的其他项目、产品或公司没有关联。

由 [Shiyu Hu](https://huuuuusy.github.io/) 创建并维护。
