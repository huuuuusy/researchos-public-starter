<p align="right">
  <a href="user-manual.en.md">English</a> | <strong>中文</strong>
</p>

# ResearchOS 用户手册

这份手册按你上手的顺序排，共五步：先弄清本仓库是什么，再建好你自己的库，然后经历第一次来源变化，接着让库长起来，最后补上做法、成熟度与体检。它像新手教程，先带你走一遍：每一步都写明你会用到什么、动手做什么、应该看到什么、做完之后你能做到什么，命令都可以整行复制。第 6 节收着这条主线之外的用法，包括只用浏览器、可选的 Dashboard 和中断后怎样接上；附录是查阅用的参考。只想走最短的一条路，就按[首次上手说明](../08_exports/public_starter/onboarding-step-by-step.zh.md)做：它从跑一遍演示，一直带到在自己的库里看一次来源变化，本手册是它背后的参考。状态、治理边界、架构、代码 owner 和目录的定义见[系统参考](system-reference.zh.md)；发布、自定义、插件、贡献与许可见[治理与扩展指南](governance-guide.zh.md)。

现在是 ResearchOS 的第一阶段：一个人用，材料是你电脑上的文件，拍板在你自己的终端里。第一阶段包含什么、不包含什么，本手册集中写在[附录 D](#附录-d第一阶段的范围)，[README](../README.zh.md#第一阶段包含什么不包含什么) 里也有一份，完整的清单在技术报告的补充说明 6。

## 1. 第 1 步：本仓库是什么

ResearchOS Public Starter 是 ResearchOS 的公开入门版：一个给个人研究者用的小型文件化工具。你的研究记在卡片里，卡片就是你电脑上的普通文件；随附的例子都是虚构的。它做一件事：让你下过的判断，换了工具、换了项目、隔了一段时间之后还接得上。平时你在 Claude Code、Codex 这类 AI 助手里用它，其他能读写本地文件的命令行工具也可以；这是主要执行路线，只用它就能完整地用起来：你给出一个目标和最少的来源，得到回答或成果；要长期保存的改动，都等你批准、检查过才生效。第一次不需要 Dashboard、插件或模型设置，也不需要先弄懂整个仓库。Dashboard 是一个可选的网页界面，让你看见手上的事、相关的资料和等你审阅的内容，但它不替你接受判断，也不扩大助手能做的事。

分工是这样的：选什么问题、证据到底支持什么，由你判断；模型和工具只做划定了范围的局部工作；ResearchOS 记着每个结果出自哪份来源、你接受了没有、还有什么没定、下一步做什么，某份来源变了，依赖它的判断会回来等你复核。它不是托管服务，不会自己做科研，不是完整的个人知识库，不是脱离证据也能回答的问答工具，也不是什么都包的成套产品；库是空的时候，它不会替你读懂一个领域。查文献、跑实验和通用的 Agent 运行环境交给专门的工具；有哪些相邻的工具、ResearchOS 为什么只做这一小块，见[相关科研工具](reference/RELATED_RESEARCH_TOOLS.zh.md)。

这一步不建任何东西，只看一遍演示：五分钟之内，你会看到一条判断怎样在它依据的来源变化之后回到研究者面前。

### 这一步你会用到什么

除了 Python 3.10 或更新版本，不用再装别的：不需要 Python 包、API key、数据库、Node.js、服务器或云账号；用 Dashboard 时还要一个较新的浏览器。我们在 Python 3.10 和 3.13 上做自动测试（CI）。用 Git、GitHub Desktop 或 GitHub 的 **Download ZIP** 拿到仓库，在仓库文件夹里打开终端，用 `python3` 运行。支持 macOS 与 Linux；Windows 请在 WSL（Windows Subsystem for Linux）中运行，因为它依赖的文件锁在原生 Windows 的 Python 中不可用。真实、敏感或未公开的材料不要放进受跟踪的文件；它们该放在哪里见第 2 步。

### 动手做

1. 确认 Python 的版本，应当是 3.10 或更新：

   ```bash
   python3 --version
   ```

2. 运行演示。它在一个虚构演示库的临时副本上运行，不改动你下载的仓库里的任何文件：

   ```bash
   python3 scripts/ros_demo.py --lang zh-CN
   ```

### 你应该看到什么

输出分六个编号步骤，每步以 `━━` 开头，最后是一小段「接下来」。前两步里，研究者确认了演示库里已有的一条判断。第 3 步，这条判断依据的来源卡片变了，`today` 把它标为待复核，并给出三个选项：

```text
━━ 3. 来源变化（基准协议改版）；ros today 标出依赖它的判断
…
    · [b5d4e33c7c] 判断「先在遮挡条件下比较 A 和 B，暂不扩大数据集。」的依据变了
        依据已变化：示例遮挡基准（虚构）（01_knowledge/papers/example-benchmark.md）
        A 复核后仍成立：刷新依据版本并确认 → ros admit --reconfirm j-occlusion-scope
        B 判断需要修改：写新的判断块 → ros propose judgment --file <草稿> --target <卡片或 commitment:id>
        C 维持现状，暂缓 → ros decide b5d4e33c7c defer --until <日期>
```

第 5 步，研究者提出重新确认，本仓库只把它显示为一段拟议的改动，不准入；第 6 步收尾时，这项复核仍列为待处理。你能指出来源变化、候选或计划、仍开着的工作和下一动作，这一步就可以停了。输出里的「还没有准入回执」「不算准入」「复制回退」都是正常现象，不是报错，意思见下面的词表。

### 如果看到的不一样

- **找不到 `python3`，或者脚本报语法错误。** 先看 `python3 --version` 是不是 3.10 或更新。
- **在 Windows 上跑不起来。** 请在 WSL 里运行，原因见上面「这一步你会用到什么」。
- **输出是英文。** 不带 `--lang zh-CN` 时输出英文。

### 你会遇到的词

演示输出和这几份指南里，有几个词用的是特定意思。第一次上手，看每个词旁边那一句就够了；表里列出的几句输出都是正常现象，不是报错。[技术报告](technical-report.zh.md)用的是同一套词，并给出精确定义。

| 词 | 在这里指什么 |
| --- | --- |
| 承诺（commitment） | 一个项目当前的那一个下一步或下一个判断。被排期的是它，而不是整个项目。 |
| 承诺清单 | `06_active_context/research-portfolio.md` 这个文件：每个项目一段，写着它眼下的那项承诺。 |
| 卡片（card） | 一份带 frontmatter 的 Markdown 文件，记一个项目、一篇论文、一个人或其他来源。承诺和判断都以卡片为依据。 |
| 研究状态 | 问题、证据、已接受的判断及其范围、仍未决的条件，以及下一步。`ros state` 把它们印成 Q、E、J、B、N。 |
| 候选（candidate） | 还没有被接受的模型产出或草稿。 |
| 准入（admission / admit） | 研究者把候选接受进研究状态。本仓库只显示计划中的改动，从不准入。 |
| 判断块 | 记录一条已接受判断及其依据的 `> [!judgment]` Markdown 块。 |
| 事项（item） | 一件登记在册的维护工作，例如来源变化后复核某条判断。技术文档里有时叫它「要求」。 |
| 待答与延期 | 待答的工作在等研究者回答一个问题；延期的工作在等一个触发条件，比如某个日期。 |
| 回执（receipt） | 做了什么、查了什么的记录。 |
| complete、complete_with_held、human_stopped、budget_stopped | `close` 报告的四种结果，依次是：事情都处理完了；只剩在等你回答或已经延期的事；还有事没处理完，你先收了尾；这次会话的预算用完了。带着没处理完的事收尾很正常，不是报错。 |
| 决策边界 | 每运行一条 `ros` 命令，系统就看一遍从上一条命令到现在有什么变了，再决定该提醒你什么；这个时刻叫决策边界。输出里叫「上一次 ros 命令」。 |
| 复制回退、只复制 | `ros` 只把要做的改动打印出来（例如 `admit` 打印的那段改动），由你或助手照着改进文件；它自己不运行、也不写入任何东西。 |
| 「还没有准入回执」 | 这条判断是直接写进文件的，没有经过准入这一步，所以 `today` 请你确认它。 |
| 「已事后确认」「不算准入」「未经准入」 | 判断已经在文件里了，你事后点了头：`today` 不再请你确认它，但这不算准入，也没有准入任何东西。 |
| `personal_vault/` | 下载下来的仓库里一个 Git 会忽略的文件夹，放你自己的材料。 |
| 库（vault） | `--root` 指向的那个装着卡片和承诺清单的文件夹：`personal_vault/` 是你自己的库，`examples/scheduler-demo/` 是虚构的演示库。技术文档里库也叫研究图（research graph），演示库也叫夹具（fixture）。 |
| public、internal、sensitive、private | 卡片的 `sensitivity`（敏感性）标签，决定 `ros context` 会不会把这张卡打包交给助手：public 和 internal 直接打包；sensitive 要你在自己的终端里确认后才打包，助手代你运行时不打包；private 和没写标签的从不打包。 |

### 现在你能做到

你能说出 ResearchOS 管的是哪一件事：来源变了，依赖它的判断会回来等你决定。你也认得输出里的几个词了。下一步，你会建好自己的库，写下第一项承诺、第一张论文卡和第一条判断。

## 2. 第 2 步：建好你自己的库

第 1 步看的是虚构的例子。这一步把它换成你自己的：一项承诺、它依据的卡片，以及一条写明依据的判断。大约半小时到一小时，一天之内可以做完。

你自己的材料放在下载下来的仓库里的 `personal_vault/` 文件夹。Git 忽略它，所以里面的东西不会被提交；`ros` 和 Dashboard 的 personal-vault 模式都读它。也正因为它不在 Git 里，你要自己备份：删掉的判断块或卡片没法从本仓库恢复，做法见[第 5 步](#5-第-5-步做法成熟度与体检)。即便如此，含有真实材料的 clone 也不要推送到公开远程仓库。

### 这一步你会用到什么

- 一个能在你电脑上运行命令的助手，例如 Claude Code 或 Codex；或者你自己的终端。两种做法建出的库是一样的。
- 你的发表清单、三到五篇与眼下工作最相关的论文或其他来源，以及一个正在做的项目。
- 一条界线：README 里「哪些不要交给助手」清单上的东西，不放进这个文件夹，也不发给助手。

### 动手做

**做法一：让助手带你走。** 这是最省事的做法。把 README 里「一句话上手」的那句话发给助手，它会按 `AGENTS.md` 的「First Run」（中文在 [`docs/reference/AGENTS.zh.md`](reference/AGENTS.zh.md) 的「首次上手」）一步步带你做：先跑第 1 步的演示，再问你要发表清单、几篇论文、合作者和一个项目，据此起草个人档案、论文卡、合作者卡、一项承诺和它的项目卡、研究身份摘要与方向摘要，最后写一条判断。写入之前，它会先把要建的卡片列成清单给你看，你同意后才写，而且只写在 `personal_vault/` 里。有几步要你本人在终端里输入命令，助手会把整行命令给你，并说明为什么必须是你。

还没想好走哪条路，或者还不会用终端，可以先让助手当向导，只复制它给出的命令：

```text
我还不知道怎么使用 ResearchOS Public Starter。请你作为我的向导，先只读 AGENTS.md；如果环境已经加载该文件，不要重读，也不要扫描仓库。然后用简单中文告诉我：1. 这个项目是做什么的；2. 我现在应该选哪条路线；3. 下一个文件或命令；4. 哪些内容不能放进公开仓库。暂时不要写文件；如果需要信息，最多先问我两个问题。
```

**做法二：自己动手。** 下面六步和助手做的是同一件事，只是只建最少的几样。

1. 复制演示库：

   ```bash
   python3 scripts/ros_demo.py --init personal_vault --lang zh-CN
   ```

   它复制演示库的承诺、卡片和 `config/ros.json`，不带走按第 3 步走查时留在演示库里的记录、示例回答和虚构的判断，并打印接下来的步骤。`personal_vault/` 已经存在时（例如你先启动过 personal-vault Dashboard）也可以用，文件夹里已有的文件会保留；如果其中已经有 `06_active_context/research-portfolio.md`，它会拒绝执行。

2. 写你的第一项承诺。打开承诺清单 `personal_vault/06_active_context/research-portfolio.md`，保留开头的 frontmatter 和标题，把两项虚构承诺换成你自己的一项。一项承诺需要标题、id、你的责任和状态、一个问题、一个下一步、你上次核对它的日期，以及它依据的卡片；Dashboard 还会读取最终负责人、你的角色和项目所处阶段。下面是最小的完整写法，把值改成你自己的，`last_verified` 写今天的日期：

   ```markdown
   ### 论文第二章

   - id: thesis-ch2
   - responsibility: lead
   - accountable_owner: 你
   - role_summary: 本章作者
   - lifecycle_phase: writing
   - state: mainline
   - priority: P0
   - question: 基线在新划分上还成立吗？
   - next_step: 在新划分上重跑基线
   - last_verified: 2026-10-29
   - stale_after_days: 14
   - source_path: 01_knowledge/projects/thesis-ch2.md
   ```

   id 和路径由你自己定，`source_path` 相对于 `personal_vault/`。每个字段能取哪些值，见[附录 A](#承诺的字段与取值)。

3. 建项目卡。删掉 `personal_vault/01_knowledge/` 下的两张虚构卡片（`projects/occlusion-tracking.md` 和 `papers/example-benchmark.md`），在 `source_path` 指向的路径上从骨架建一张你自己的：

   ```bash
   cp 09_templates/basic/project.zh.md personal_vault/01_knowledge/projects/thesis-ch2.md
   ```

   填好 `title`，把 `# 项目名` 标题换成同一个名字：`ros` 用 frontmatter 的 `title` 作为卡片的显示名，没有时用第一个 `#` 标题。`09_templates/basic/` 里的每份骨架都有 frontmatter、Agent Summary、事实与看法各节和证据边界，并附一段简短说明，写明文件放在哪里、每个值是什么意思。[examples/starter-cards/zh-CN/](../examples/starter-cards/zh-CN/README.md) 里是每类卡填好的样子。

4. 建一张论文卡。它是下一步那条判断的依据，也是第 3 步要用的卡：

   ```bash
   cp 09_templates/basic/paper.zh.md personal_vault/01_knowledge/papers/split-benchmark.md
   ```

   填标题、作者、发表处、你读的版本和主要结论，只写来源里写了的。这份骨架也适用于问卷、档案目录、数据集说明或实验方案。大多数卡写 `sensitivity: internal`，人物和记录别人说话的卡写 `sensitive`；这个标签的效果见[第 4 步](#4-第-4-步让库长起来)。

5. 在你的库上运行调度器，开启一次会话：

   ```bash
   python3 scripts/ros.py --root personal_vault today
   ```

   用 `--init personal_vault --lang zh-CN` 建的库，`config/ros.json` 已设为中文输出；要临时换语言，加 `--lang en` 或 `--lang zh-CN`。

6. 写下第一条判断。没有判断，来源变了 `today` 也没有东西可以交还给你。把你眼下的看法写进仓库之外的一个草稿文件，比如 `~/Desktop/judgment-draft.md`，依据写它所依赖的卡片：

   ```text
   > [!judgment] j-baseline-split
   > 结论：先在新划分上重跑基线，再决定要不要换方法。
   > 依据：01_knowledge/papers/split-benchmark.md
   ```

   登记这份草稿，它会成为一个候选，并打印下一条命令。命令里的 `thesis-ch2` 是上面示例的承诺 id，换成你自己的：

   ```bash
   python3 scripts/ros.py --root personal_vault propose judgment --file ~/Desktop/judgment-draft.md --target commitment:thesis-ch2
   ```

   ```text
   已登记 1 条候选：
     ros admit c-69115257
   ```

   运行它给出的那一行，候选编号换成你的终端里打印的：

   ```bash
   python3 scripts/ros.py --root personal_vault admit c-69115257
   ```

   `admit` 不写入任何东西。它先打印一段 diff，供你核对它会对 `research-portfolio.md` 做的改动：在承诺下加一行 `judgments`，再加上判断块，依据的版本已经填好。diff 下面是「要贴的文本」：完整的判断块和 `judgments` 一行，每一段都写明贴在文件第几行之后。把这几段文本照它说的位置贴进文件并保存，自己贴或请助手贴都可以。然后在你自己的终端里运行下面这行，回答 `y`：

   ```bash
   python3 scripts/ros.py --root personal_vault admit --confirm j-baseline-split
   ```

   最后收尾。`close` 会提醒你，新加的 `judgments` 一行是判断类字段，要单独确认，并打印带编号的命令；收尾之后，在你自己的终端里运行它，回答 `y`（编号用 `close` 打印的那个）：

   ```bash
   python3 scripts/ros.py --root personal_vault close
   python3 scripts/ros.py --root personal_vault decide 188045ccc1 confirm
   ```

第一次用不必碰下面这些，跑通第一圈之后它们都还在：插件和插件的安装、系统结构图和完整架构、维护命令和代码、把所有人物关系一次画全、事先选好模型或配置模型服务，以及一次导入全部论文、项目和人物。

### 你应该看到什么

第 5 小步的 `today` 在「待判断」下只列出你自己的承诺：

```text
待判断（1 项承诺：未安排、需定下一步、复核到期，或有判断事项等你处理）
  ■ 论文第二章  ［未安排］
    （没有要复核的事项）下一步：在新划分上重跑基线；排到今天：ros attend thesis-ch2 today
```

显示「未安排」是正常的：你还没有给它排日子，排期的做法在第 5 步。把判断贴进文件之后再运行 `today`，这项承诺下面会多出两条：新判断「尚未确认」，以及 `judgments` 字段「还没有确认」；如果你先确认了判断再运行 `today`，就只剩 `judgments` 字段这一条。确认判断时，终端里的回答是这样的：

```text
事后确认判断 j-baseline-split？ [y/N] y
已确认 j-baseline-split（06_active_context/research-portfolio.md:26）。它是直接写进文件的，没有事先授权，所以记为事后确认，不算准入
```

「事后确认，不算准入」是本仓库对所有手工贴进去的改动的记法，不是你做错了什么；第 3 步会讲它的来由。两项都确认之后，再运行 `today` 和 `close`，`close` 报告 `结果：完成（complete）；收尾时待办 0，待答或延期 0`。

### 如果看到的不一样

- **`--init` 说承诺清单已经存在**（`research-portfolio.md 已经存在；--init 只用于还没有承诺清单的文件夹`）。你以前建过库：直接改那一份，或者把它挪开再重建。
- **`today` 出现「承诺清单问题」。** 每一行都写明是哪个字段、可以取哪些值，例如 `state「active」不是可用值（mainline, waiting, queued, conditional, closed, paused）`；卡片不在你写的路径上时，写的是 `source_path … 在这个文件夹里不存在`。照着改承诺清单即可，这项承诺不会悄悄从检查中消失。`python3 scripts/ros.py --root personal_vault rules --check` 报告同样的问题，一切就位时报告 `问题 0 条`。
- **虚构承诺还在。** 它们还出现在「待判断」下，说明两段虚构承诺还留在文件里。如果只出现在「待你回答的问题」下，写着「这条事项所指的判断已不在了」，说明你在替换之前运行过 `today`，那是虚构演示留下的记录：删掉 `personal_vault/06_active_context/work_state/`，再运行一次 `today`。只在还没确认过任何判断时这样做；这个文件夹以后还存着你的确认记录和注意力安排。
- **多出几条「判断类字段……还没有确认」。** `today` 读过这项承诺之后，你又改了它的 `state`、`priority`、`question` 或 `responsibility`，比如为了改正承诺清单问题。`today` 跑过之后才加进清单的新承诺也一样，这四个字段各要确认一次。这几处都在 `close` 之后确认，做法见[附录 B](#手工改了承诺字段之后)。
- **确认了 `judgments` 一行，`today` 还列着它。** 这一条要在收尾之后确认才关得上：先运行 `close`，再运行 `close` 打印的那行 `decide … confirm`。
- **助手说它不能替你确认。** 确认判断和判断类字段，只有你本人在终端里回答才生效；由助手代为运行，只记为代理转述，这条确认请求仍然开着。

[首次上手说明](../08_exports/public_starter/onboarding-step-by-step.zh.md)把这几步再走一遍，写明每一步应该看到的输出；字段以本手册[附录 A](#承诺的字段与取值)为准。使用自己的库不需要关闭示例数据。

### 现在你能做到

你有了自己的库：一项承诺、它的项目卡、一张论文卡，和一条写明依据、由你确认过的判断。你也知道哪些事助手可以代做，哪些要你本人在终端里做。下一步，让这张论文卡变一次，看这条判断怎样回到你面前。

## 3. 第 3 步：第一次来源变化

第 2 步，你建了一张论文卡，写了一条依据它的判断。这一步讲 ResearchOS 最核心的用处：这篇论文后来变了，比如作者发了更正、基准改了协议、档案馆更正了目录，依赖它的判断会回到你面前，由你决定它还成不成立。

ResearchOS 不会自己去发现论文被更正。你知道了，就去更新那张论文卡，接下来的事它来接手：哪几条判断靠的是这张卡，它都会找出来交给你。

### 这一步你会用到什么

- 第 2 步建的一张论文卡，和一条依据它的判断。
- `ros` 的几条命令。`ros` 是会话调度器的命令行客户端；输出里打印的每个 `ros …`，在终端里都要输入 `python3 scripts/ros.py --root <文件夹> …`，而且 `--root` 要写在子命令之前。在仓库文件夹里运行，对你自己的库，完整写法是 `python3 scripts/ros.py --root personal_vault <命令>`。这一步的主线用 `today`、`admit` 和 `close` 三条；和助手配合时再加 `context`、`run`、`collect`。

下面用示例里的故事来讲：基准 Example Occlusion Benchmark 出了协议第 2 版，重度遮挡的划分重新标过了。你自己做的时候，换成你自己的论文和判断就行。

### 动手做

1. **更新论文卡。** 打开 `personal_vault/01_knowledge/papers/` 下的那张卡，把 frontmatter 里的 `version` 改成新的版本，并在「来源说了什么」一节写清楚变了什么：

   ```text
   version: 协议第 2 版
   …
   - 协议第 2 版：重度遮挡的划分重新标过，阈值从 60% 改为 70%。
   ```

   顺手把 frontmatter 里的 `updated` 改成今天。这是事实类的改动，你自己改、请助手改都可以，改完不用确认。卡片的内容只要有改动，就会触发复核，只改 `updated` 也算。

2. **运行 `today`。**

   ```bash
   python3 scripts/ros.py --root personal_vault today
   ```

   它会在「待判断」下面列出依赖这张卡的判断，告诉你是哪张卡变了，并给出三个选项。示例库里的输出是这样的；你的判断 id 和编号会不同，下面命令里的 `j-occlusion-scope` 和 `b5d4e33c7c` 都换成你的 `today` 打印的：

   ```text
   待判断（1 项承诺：未安排、需定下一步、复核到期，或有判断事项等你处理）
     ■ 遮挡迁移论文  ［未安排］
       · [b5d4e33c7c] 判断「先在遮挡条件下比较 A 和 B，暂不扩大数据集。」的依据变了
           依据已变化：示例遮挡基准（虚构）（01_knowledge/papers/example-benchmark.md）
           A 复核后仍成立：刷新依据版本并确认 → ros admit --reconfirm j-occlusion-scope
           B 判断需要修改：写新的判断块 → ros propose judgment --file <草稿> --target <卡片或 commitment:id>
           C 维持现状，暂缓 → ros decide b5d4e33c7c defer --until <日期>
   ```

3. **选一个。** 先重新读一遍论文的变化，再看这条判断。它是否仍然成立由你决定，系统判断不了。拿不准时，可以请助手把论文卡和判断一起读一遍、说说它的看法，但决定由你来下。

   - **A，仍然成立。** 运行它给出的那一行：

     ```bash
     python3 scripts/ros.py --root personal_vault admit --reconfirm j-occlusion-scope
     ```

     它先打印一段 diff 供你核对：只改依据的版本号和确认日期，结论一个字不动。本仓库不替你改文件：diff 下面印着改好的完整判断块，并写明它替换文件的第几行到第几行。把这段文本贴进 `research-portfolio.md`，整块换掉旧的判断块，自己贴或请助手贴都可以。然后在你自己的终端里运行下面这行，回答 `y`：

     ```bash
     python3 scripts/ros.py --root personal_vault admit --confirm j-occlusion-scope
     ```

     这一步要你本人在终端里做。判断成不成立是你的决定，助手代你运行，只会记为「代理转述」，这条复核也会一直开着。

   - **B，需要修改。** 比如改版后你觉得应该先只看中度遮挡。照[附录 B「替换一条判断」](#附录-b替换一条判断以及改过承诺字段之后的确认)的步骤做：写一条新的判断，登记、应用、确认，再撤掉旧的那条。新判断可以自己写，也可以请助手起草，见下面的「请助手起草：context、run、collect」。

   - **C，以后再定。** 比如你想等协议文本定稿再说：

     ```bash
     python3 scripts/ros.py --root personal_vault decide b5d4e33c7c defer --until 2026-12-01
     ```

     它会问一句，你回答 `y`，之后这条复核不再列出，过了那一天再出现在 `today` 里。这一步也要你本人在终端里做：由助手代为运行时它不提问，只打印「未生效」并记为代理转述，这条复核在 `today` 和 `close` 里照常列出、仍算待办，同时给出要你在自己的终端里运行的那一行。

4. **运行 `close` 收尾。**

   ```bash
   python3 scripts/ros.py --root personal_vault close
   ```

### 你应该看到什么

选了 A 并确认之后，再运行一次 `today`，这项承诺下面写的是「没有要复核的事项」，接着是它的下一步。`close` 的「本次的判断类改动」里会记一行：这条判断已修改，状态是「已事后确认（未经事前授权，不算准入）」。

「事后确认，不算准入」是正常的，不是你做错了什么。本仓库只把改动打印出来，由你或助手贴进文件，所以它记为「先写入、后确认」。技术报告里的原型多一步：研究者确认之后由系统自己写入，那才叫准入。

选了 C 的，`close` 会把这条复核单独列出来，标着「延期到」哪一天；在那之前，`today` 里这项承诺下面不再出现它；只有一种例外：它依据的卡片又改了，它会提前回来。

`close` 的第一行是这次会话的结果。还有没处理完的事时，它写的是「由你收尾，仍有未关闭的工作（human_stopped）」，并把它们逐条列出；带着未关闭的工作收尾很正常，下一次 `today` 会接着列。

### 如果看到的不一样

- **判断没有回来。** 先看判断块的「依据」一行有没有写这张论文卡的路径。依据只写了承诺 `commitment:<id>`、没写卡片，系统就不知道它靠的是这张卡。
- **`admit --confirm` 说这一版已经确认过**（already confirmed or admitted）。多半是打印出的那段文本还没贴进文件，文件里还是你之前确认过的旧版本。打开 `research-portfolio.md`，确认依据一行末尾的版本号已经换成新的，再运行一次。
- **多出了「久未核实」或「在核实后有更新」。** 这两处来自日期，不是来自你改的卡。承诺的 `last_verified` 过了 `stale_after_days` 天，`today` 会把它标为久未核实：核对之后把 `last_verified` 改成今天即可，这是事实类改动。新 clone 上第一次运行 `today`，还可能看到某份来源「在核实后有更新」，因为判断依据是文件的修改时间，而 clone 刚把它设成了当天，晚于承诺的 `last_verified`。`ros_demo.py` 固定了日期，所以第 1 步的演示里没有这两条。
- **`today` 什么都没列出。** 检查 `--root personal_vault` 是否写在子命令之前。不带 `--root` 时，`ros` 把本仓库本身当作库来读，其中没有承诺。
- **`close` 说今天没有开着的会话。** 收过尾的会话不能再收一次：先运行 `today` 开一个新会话，再运行 `close`。
- **还有别的提示。** 运行 `python3 scripts/ros.py --root personal_vault rules --check`，它会逐条说明问题出在哪个字段、可以取哪些值。

### 它是怎样知道的

判断的「依据」一行，在每张卡片路径后面记了一个版本号，比如 `example-benchmark.md@e2d7be3d`。这个版本号由卡片的内容算出来，卡片的内容一改，版本号就跟着变。`today` 每次都把依据里记的版本和卡片现在的版本对一遍，对不上，就把这条判断交还给你。所以卡片要写准确：论文改了什么，就在卡上写什么。卡上写得越清楚，你复核时越省事。

也因为这样，判断的依据要写它所依赖的卡片，不要写它所在的承诺：承诺的版本包含它的日期和下一步，依据写了承诺，每次更新这些内容，判断都会回来等复核。

### 请助手起草：context、run、collect

上面的三条命令由你自己运行。要请助手读材料、起草一条判断时，还有三条命令把这件事接进同一次会话，于是从 `today` 到 `close` 的一轮共六条：`today`、`context`、`run`、`collect`、`admit`、`close`。演示库随附一份示例回答，所以没有助手也能把这一轮走一遍。下面的命令都在演示库 `examples/scheduler-demo-zh/` 上运行；在你自己的库里，把 `--root` 换成 `personal_vault`，把承诺 id 和回答文件换成你自己的。

1. 开启会话，再取出这项承诺的上下文：

   ```bash
   python3 scripts/ros.py --root examples/scheduler-demo-zh today
   python3 scripts/ros.py --root examples/scheduler-demo-zh context commitment:occlusion-paper
   ```

   `today` 开启会话，列出需要你决定的事。`context` 打印这项承诺、它依据的卡片和已有的判断，倒数第二行是 `[交付 4 项；排除 0 项]`，最后一行是这次交付的回执 `[上下文回执 ctx:…]`；和你在同一个文件夹里工作的助手，就是用这条命令取材料的。

2. 把起草的任务写成任务包：

   ```bash
   python3 scripts/ros.py --root examples/scheduler-demo-zh run judgment --target commitment:occlusion-paper --executor copy_packet
   ```

   `run` 把任务包写到库里 Git 忽略的 `06_active_context/work_state/ros/packets/` 下，并打印形如 `ros-run-…` 的运行编号和对应的 `collect` 命令：

   ```text
   任务包已写到 …/06_active_context/work_state/ros/packets/ros-run-0406186c6e1b.md（运行 ros-run-0406186c6e1b）。把它交给你的 AI 助手；拿到回答后运行 ros collect ros-run-0406186c6e1b --file <回答文件>
   ```

3. 把回答收回来。平时你把任务包交给助手，把它的回答存成文件；这里用演示库随附的示例回答。下面的编号只是示例，输入时换成你的 `run` 打印出的那个：

   ```bash
   python3 scripts/ros.py --root examples/scheduler-demo-zh collect ros-run-0406186c6e1b --file examples/scheduler-demo-zh/sample-answer.md
   ```

   ```text
   运行 ros-run-0406186c6e1b 返回，产生 1 个候选（尚未准入）：
     ros admit c-d6f6cfd9
   ```

   `collect` 把回答回收为候选，并打印形如 `c-…` 的候选编号和 `admit` 命令。

4. 看这个候选会改什么，然后收尾。同样，候选编号换成你的终端里打印的：

   ```bash
   python3 scripts/ros.py --root examples/scheduler-demo-zh admit c-d6f6cfd9
   python3 scripts/ros.py --root examples/scheduler-demo-zh close
   ```

   `admit` 打印它会对 `06_active_context/research-portfolio.md` 做的改动，但不写入。在演示库上到这里就可以停，不要把改动贴进受跟踪的演示文件；这时 `close` 结束会话，并把这个候选列为尚未决定：

   ```text
   本次会话开始以来回收或登记、尚未准入也未拒绝的候选（未写入）：
     · 候选 c-d6f6cfd9：commitment:occlusion-paper
   ```

   在你自己的库里，要留下这个候选，就照第 2 步第 6 小步那样应用改动并确认；如果它是用来替换旧判断的，再照附录 B 撤掉旧的那条。

按当天日期在演示库上运行，`today` 还会列出演示库里原有的判断「尚未确认」和几条来自日期的提醒，原因见上面「如果看到的不一样」。走查留下的记录在 Git 忽略的 `examples/scheduler-demo-zh/06_active_context/work_state/` 里，不影响受跟踪的文件。

### 现在你能做到

论文、协议或材料变了，你会更新卡片，看到依赖它的判断回来，并选择保留、修改或延期；需要时，你也会让助手起草一条判断，再由你决定留不留。这也就是 ResearchOS 每天在做的事。下一步，你会把更多论文、人物和会议记进库里，并给这个方向写一份摘要，让助手知道做什么事该读哪几张卡。

## 4. 第 4 步：让库长起来

前三步之后，库里只有一个项目、一张论文卡和一条判断。接下来的一周，把平时用到的东西一点点记进来：更多论文，合作者，开过的会，做过的决定。卡片多了，助手每次读哪几张就成了问题，所以这一步还要写两页摘要，并学会两条命令：`plan_context.py` 列出一项任务该读哪些卡，`ros context` 把卡片取给助手。

卡片里写的是你或助手对材料的理解，写下来不等于它已经是确认过的长期记忆，更不等于可以公开的事实。从一份来源、一张卡片开始：卡片写清这份来源的范围、哪些内容核对过、还缺哪一个事实；核对过第一版结果，再按需要补项目历史、报告、决策理由和其他来源。也不必先攒够卡片才开始用：你给出的来源就是第一张工作卡片，眼前的证据不够时，再去库里找别的（Dashboard 里这一块叫`资料`）。

### 这一步你会用到什么

- `09_templates/basic/` 里的骨架。每类卡一份，开头的填写说明写了放在哪里、每个值是什么意思。
- [examples/starter-cards/zh-CN/](../examples/starter-cards/zh-CN/README.md) 里填好的样子：同一个虚构故事串起研究身份摘要、方向摘要、项目卡、论文卡、决策卡、启发式卡、风格卡、人物卡和会议卡，并讲了三层读法、成熟度和敏感性。
- 两条命令：`python3 scripts/plan_context.py <任务> --vault personal_vault` 和 `python3 scripts/ros.py --root personal_vault context <卡片路径>`。

### 动手做

1. **加卡片，每次几张。** 用到什么记什么，不必一次导入全部：

   | 卡片 | 骨架 | 放在哪里 | `sensitivity` |
   | --- | --- | --- | --- |
   | 论文或其他来源 | `paper.zh.md` | `personal_vault/01_knowledge/papers/` | `internal` |
   | 人物 | `person.zh.md` | `personal_vault/04_people/collaborators/`；你自己的档案放 `personal_vault/00_identity/profile.md` | `sensitive` |
   | 会议 | `meeting.zh.md` | `personal_vault/06_active_context/meetings/`，文件名以日期开头 | `sensitive` |
   | 决策 | `decision.zh.md` | `personal_vault/02_decisions/`，文件名以日期开头 | `internal` |

   `--init` 建出的库里只有 `01_knowledge/` 和 `06_active_context/`，别的目录不存在时先建，例如 `mkdir -p personal_vault/04_people/collaborators personal_vault/02_decisions`。记一次会是这样：

   ```bash
   mkdir -p personal_vault/06_active_context/meetings
   cp 09_templates/basic/meeting.zh.md personal_vault/06_active_context/meetings/2026-11-12-benchmark-sync.md
   ```

   每张卡带有 public、internal、sensitive 或 private 的敏感性标签。大多数卡写 `internal`；人物卡和记录别人说话的卡写 `sensitive`；`private` 的卡 `ros context` 从不打包，只用于你不想交给助手的卡。在 `personal_vault/` 里，简短的当前状态放入 `06_active_context/`，有来源的摘要放入 `01_knowledge/`，决策与取舍放入 `02_decisions/`，人物上下文放入 `04_people/`，可复用方法放入 `05_workflows/`；完整的放置表见[新材料放置规则](reference/WHERE_TO_PUT_NEW_MATERIALS.zh.md)。原始材料留在原处、放在仓库之外：卡片记下路径，很多时候已经足够，不要为了让 Dashboard 看见而复制原始文件。库里的任何内容，不经[安全导出规则](reference/SAFE_EXPORT_POLICY.zh.md)下的单独复查，都不会公开。`09_templates/` 里的完整模板（`project-template.md` 等）多了后期用得上的治理小节，现在用不到。

2. **写两页摘要。** 研究身份摘要是整个库的入口，写你的研究方向、当前主线和做研究的习惯；方向摘要是一个方向的入口，列出这个方向的卡片，并用一张表写明做什么任务读哪张卡：

   ```bash
   mkdir -p personal_vault/00_identity personal_vault/01_knowledge/capsules
   cp 09_templates/basic/research-identity.zh.md personal_vault/00_identity/research-identity.md
   cp 09_templates/basic/capsule.zh.md personal_vault/01_knowledge/capsules/thesis-ch2.md
   ```

   这两页都写 `sensitivity: internal`。用助手走过首次上手的，这两页已经建好；新的方向照同样方式再加一份方向摘要；它有了自己的项目，就在承诺清单里照第 2 步的写法再加一项承诺。`today` 跑过之后才加的承诺，它的四个判断类字段各要确认一次，见[附录 B](#手工改了承诺字段之后)。助手每次先读它们：`plan_context.py` 会把它们列在任务文件前面。

3. **看一项任务该读哪些卡。** 把 `<任务>` 换成任务的名字，例如 `paper_writing`（写论文）；全部任务用 `python3 scripts/plan_context.py --list` 列出：

   ```bash
   python3 scripts/plan_context.py paper_writing --vault personal_vault --mode quick
   python3 scripts/plan_context.py paper_writing --vault personal_vault --mode standard
   ```

   它按读取档列出助手要读你的哪些卡，跟着库的语言走，不用加 `--lang`。三档各读什么，见下面的「保持读取范围小」。

4. **把卡片取给助手。** 助手不直接打开你的卡片文件，而是运行下面这样的命令，路径换成你自己的卡片：

   ```bash
   python3 scripts/ros.py --root personal_vault context 01_knowledge/papers/split-benchmark.md
   ```

   `ros context` 按卡片的敏感性标签决定带不带这张卡：public 和 internal 的直接打包；sensitive 的要你在自己的终端里回答 y 才打包，助手代你运行时不打包；private 和没写标签的从不打包。

5. **在助手里做一件真实的事。** 给出一个目标和一份来源，做法见下面的「在 Agent 客户端里走一个闭环」。

### 你应该看到什么

库里有了风格卡、研究身份摘要和方向摘要之后，`plan_context.py paper_writing --mode standard` 的输出开头是这样的（示例卡片；库里的路径会印成完整路径，这里缩写为 `personal_vault/…`）：

```text
任务: 论文写作 (paper_writing)
…
读取档位: standard / 5 files / 35000 tokens

本轮只读:
- personal_vault/03_cognition/style/writing.md
- personal_vault/00_identity/research-identity.md
- personal_vault/01_knowledge/capsules/occlusion-tracking-capsule.md
- 05_workflows/research_work/paper-writing.zh.md
- 09_templates/standard-agent-prompts.zh.md

方向摘要点名的卡（任务需要哪张，就用 ros context 取哪张）：
- personal_vault/01_knowledge/projects/occlusion-tracking.md
- personal_vault/01_knowledge/papers/example-benchmark.md
…
```

还没写的卡会列在「你的库里还没有（本次跳过；想写时从模板开始）」下面，每张给出从哪份骨架开始；在它写好之前，助手先跳过。

助手用 `ros context` 取一张 sensitive 的卡时，输出是这样的：

```text
[交付 0 项；排除 1 项]
  已排除 04_people/collaborators/lin-ke.md：敏感卡片只在研究者本人的终端里显示。需要时在你自己的终端运行同一条命令，问到是否在这里显示时回答 y
[上下文回执 ctx:f0e3f4c7…；去向 session_agent:claude_code]
```

### 如果看到的不一样

**助手说某张卡被排除时。** 助手用 `ros context` 取卡片，输出快结束的地方有一行像 `[交付 1 项；排除 1 项]`，其中「排除」数的是没打包的卡，下面每张没打包的卡一行，说明原因，最后一行是上下文回执。被排除的通常是 sensitive 的卡，比如人物卡或会议卡：它们记的是别人，所以不交给助手，助手也不该改为直接打开文件。任务确实需要这张卡时，你在自己的终端运行 `python3 scripts/ros.py --root personal_vault context <卡片>`，回答 `y`，再只把任务需要的部分复制给助手。随附的承诺清单标为 internal，所以项目的问题和判断会被打包；没写标签的卡片或承诺清单不打包。要记住，标签只管 `ros context` 打包什么，管不住助手自己直接打开文件。

### 保持读取范围小

读取档位同时限制首轮文件数和估算 token：

| 档位 | 首轮文件 | 估算总 token | 适用场景 |
| --- | ---: | ---: | --- |
| `Quick` | 1 | 约 10k | 已有精确来源或窄问题。 |
| `Standard` | 最多 5 | 约 35k | 需要一份工作流程和少量项目背景。 |
| `Evidence` | 最多 8 个指定文件 | 约 60k | 正式的说法或公开的输出需要核对。 |

默认从 `Quick` 开始；你给出了具体的论文、草稿或目标路径时，Quick 就从那个文件读起。Standard 可以再加一份工作流程、项目页和少量正式卡片；Evidence 只加能回答眼前核对问题的核对记录、阅读笔记或原件。说得清缺的是哪个事实或哪个判断，才升一档；文件数或 token 快要超了，就少读几个文件、分批处理。这样既省 token、少带无关的内容，库本身又一张卡不少。读取档和助手的「思考深度」是两回事：缺材料时提高读取档；推理步骤多、判断难时，在助手里把思考深度调高（有的客户端叫推理强度或 effort）。用哪个模型、思考多深，都在助手里设置。结果是普通回答、成果文件还是要写回卡片的候选，由任务本身决定，不用你事先分类。只是讨论、推理和起草，直接在助手里按仓库说明做就行，不需要交接。

在你自己的库里，给 `python3 scripts/plan_context.py <路线> --mode quick`（或 `standard`、`evidence`）加上 `--vault personal_vault`，它会按读取档列出助手要读你的哪些卡。它跟着库的语言走，不用加 `--lang`。

- **quick 只读一张。** 对外的任务（例如回复外部请求、导出前检查）先读边界卡，其他任务读这类任务的风格卡，都没有时读研究身份摘要。
- **standard 首轮最多 5 个文件。** 研究身份摘要、风格卡、方向摘要、这项任务的工作流程，以及这条路线另外点名的卡（例如写申请前的边界卡）。方向摘要里点名的卡单独列成一组，助手需要哪张，就用 `ros context` 一张张取，它们不算在首轮这 5 个文件里。
- **evidence 首轮最多 8 个文件。** 在 standard 之外，写论文和写申请时再加两张索引卡，即成果与使用边界和论文作者角色（库里有这两张时才列）；原件只打开这些卡「证据边界」里写明的，而且要有一个说得出的核对问题。

还没写的卡也会列出名字，并给出从哪份骨架开始；在它写好之前，助手先跳过。

### 在 Agent 客户端里走一个闭环

不建库、不用调度器（`ros` 这套命令），也可以直接在助手里做事；有了库之后，同样的几步照样适用。

用 Claude Code、Codex、Gemini CLI 或其他能读写本地文件的 AI 助手打开本文件夹。第一次只需要四件事：目标，即现在要回答、整理或产出什么；来源，即一份你提供的材料或一个明确公开链接；结果，即回答、可打开的成果文件或可核对的 diff；边界与下一步，即哪些是来源事实、哪些仍是候选、接下来做什么。

有具体任务时，直接交出来源：

```text
我这里有一份 PDF：[链接或本地路径]。它是：[公开 / 在投 / 内部 / 边界不清楚]。

请用 ResearchOS 帮我理解它，并把它和[我的任务]联系起来。先读 AGENTS.md，只补充读取当前任务需要的最小工作流或目标文件。请返回材料边界、短阅读笔记、候选判断、建议保存位置和需要我确认的内容。在我批准候选内容和证据边界之前，不要写入长期记忆。
```

助手应说明读了什么、有意没读什么，哪条路线合适，涉及什么隐私或导出边界，以及结果是普通回答、成果还是拟议的长期变化。好的阅读笔记写清：原文说了什么、你怎么理解、一个局限、还缺什么、下一步；并分清原文支持什么、什么还没验证过。

普通回答已经够用就停；无论如何，说得出依据什么、还有什么没定、下一步做什么，就可以停了。只有内容值得长期留下、而且说得出该存进哪张卡时，才把它留作候选；之后你批准它、再检查一遍，仍是分开的两步。想接着用自己的材料，按第 2 步操作，并告诉助手在你确认前不写文件。

不用 Dashboard 时，每一轮都是同样几步：

```text
一个目标 + 最少的来源
  -> 助手在说好的范围内工作，或运行一条命令
  -> 得到三种结果之一：回答、成果文件，或一处等你决定的候选改动
  -> 你核对来源、还不知道的地方、敏感性和实际效果
  -> 你批准之后才改长期内容，并留下检查结果、记录和改回去的办法
```

四条规则守住这一轮：助手的输出先是候选；任务做完不等于证据确认；Dashboard 和程序生成的数据文件只是展示，一切以 Markdown 卡片为准；私人材料要单独复查才能公开。这些规则背后的几种状态见系统参考的[状态与权威模型](system-reference.zh.md#状态与权威模型)；来源路径只说明证据从哪里来，从来不是保存的位置。

### 现在你能做到

你的库里有了论文、人物、会议和决策卡，有两页摘要告诉助手先读什么；你会查一项任务该读哪些卡，知道哪些卡会交给助手、哪些不会，也会在助手里从一个目标和一份来源走完一轮。完成一个闭环就停：只有每个新文件都说得清归哪一层管、证据边界在哪里，扩大库才有意义。下一步记的不再是材料，而是你自己的做法。

## 5. 第 5 步：做法、成熟度与体检

用了一个月左右，库里记下的材料够多了，有三件事值得补上。第一，把你反复纠正助手的地方记成卡片，它下次就照你的做法来。第二，给卡片标上它长到了哪一步。第三，定期检查库本身：链接断没断，标签对不对，手上到底有几件事，备份了没有，哪件事哪天做。

### 这一步你会用到什么

- `09_templates/basic/` 里的 `style.zh.md`、`heuristic.zh.md`、`boundaries.zh.md` 等骨架。
- 三条命令：`python3 scripts/build_public_starter_data.py --personal-vault`（库体检）、`python3 scripts/query_research_agenda.py`（议程查询）和 `python3 scripts/ros.py --root personal_vault attend`（注意力安排）。

### 动手做

1. **写风格卡。** 某类工作反复出现时，从 `09_templates/basic/` 加上对应的卡。风格卡用 `style.zh.md`，放在 `personal_vault/03_cognition/style/<任务>.md`，记的是你做某一类任务的习惯，`<任务>` 取 `writing`、`review`、`proposal`、`figures-talks` 或 `mentoring` 之一；助手在读取档 quick 先读对应的那一张：

   ```bash
   mkdir -p personal_vault/03_cognition/style
   cp 09_templates/basic/style.zh.md personal_vault/03_cognition/style/writing.md
   ```

   每一条写规则、为什么、怎么用和出处；你纠正助手时，它把这次纠正起草成一条，你同意后才加进去（[示例](../examples/starter-cards/zh-CN/03_cognition/style/writing.md)）。

2. **写启发式卡。** 启发式卡记你做研究的一条习惯：规则、什么时候用、什么时候不用。用 `heuristic.zh.md`，放在 `personal_vault/03_cognition/heuristics/`（目录不存在时先 `mkdir -p personal_vault/03_cognition/heuristics`）。它和风格卡一样写的是你的做法，助手起草后先给你看，你同意才写。

3. **需要时补上其他卡。** 边界卡 `personal_vault/00_identity/boundaries.md`（`boundaries.zh.md`）用你自己的话写哪些材料从不交给助手、哪些事对外不说、机构或期刊对 AI 工具的规定、发出去前要谁点头；对外的任务先读它。写论文和申请到了 evidence 档，会再读两张索引：成果与使用边界（`outputs-index.zh.md`，放在 `01_knowledge/papers/`）和论文作者角色（`author-roles.zh.md`，也放在 `01_knowledge/papers/`），用来核对说法能不能对外讲、贡献有没有出处。同一文件夹里还有审稿意见、基金申请、学术邮件、给学生的反馈和心智模型的骨架（`review.zh.md`、`grant.zh.md`、`message.zh.md`、`feedback.zh.md`、`mental-model.zh.md`），每份的填写说明里写了放在哪里。

4. **标成熟度。** 每类卡用一个字段标它长到了哪一步：论文和报告卡用 `analysis_state`（M1 到 M3），项目卡用 `project_maturity`（I0 到 I3），人物卡用 `relationship_maturity`（R0 到 R3），方向摘要用 `group_level`（G0 到 G2）；启发式卡用 `confidence` 和 `status`，风格卡只用 `status`。只有来源、链接和确认变多了才升级，字数变多不算。这些标签都是可选的，不想管就留着骨架里的默认值：`ros` 不看它们，只有可选的 Dashboard 用它们显示一张卡长到了哪一步。需要理解 M/I/R/G 标签，或把卡片缺口变成有边界的 Work 任务时，再读[卡片成熟度与增强](reference/CARD_MATURITY_AND_ENHANCEMENT.zh.md)。

5. **给库做体检。** 每次手工改过卡片，都可以跑一遍。照体检结果改卡之前要知道一件事：被判断引用的卡，哪怕只改了一个链接，依赖它的判断都会回来等复核，已经延期的也会提前回来：

   ```bash
   python3 scripts/build_public_starter_data.py --personal-vault
   ```

   它只读不写，检查仓库里的 `personal_vault/`，在「库体检」下列出手写的库常见的问题：链接到不存在的文件、`sensitivity` 标签写错、Agent Summary 是空的、frontmatter 某行末尾带了 `#` 注释（会被当成值的一部分）、方向摘要比它列出的卡更旧、卡片 `source` 写的原件在本机找不到（只是提醒），以及注意力安排里同一项承诺有两段条目。承诺清单本身由 `ros today` 和 `ros rules --check` 检查。

6. **查手上有几件事。** 问「我当前主责多少任务」时，运行：

   ```bash
   python3 scripts/query_research_agenda.py --view lead-active
   ```

   也可以用 `lead-all`、`support-active`、`support-all`、`waiting`、`queued`、`conditional`、`paused`、`review`、`unclassified`、`all` 查看明确分层。库里有 `personal_vault/06_active_context/research-portfolio.md` 时它读你的承诺清单，否则读虚构的示例议程。某项承诺没写 `responsibility`，或者写了它不认识的值，会被归到 `unclassified`，不会被当成你主责的。报出的数量也不一定完整：只有清单的覆盖核对还有效、又没有尚未归类的候选时，才算完整的数量；输出的「覆盖」一行写着「未闭合」时，它只是已登记的数量。输出按时间分栏只是为了排序，不决定清单里有什么。

7. **备份。** `personal_vault/` 不在 Git 里，你要自己备份它（复制整个文件夹，或放进你自己的私人备份）：删掉的判断块或卡片没法从本仓库恢复。想给库做版本管理，就另建一个没有公开远程的私人仓库副本，并在那个副本的 `.gitignore` 里删掉 `personal_vault/`。无论哪种做法，都用同样的 `personal_vault/` 布局。

8. **安排哪天做哪件事。** `today` 里标着「未安排」的承诺，由你决定什么时候做：

   ```bash
   python3 scripts/ros.py --root personal_vault attend thesis-ch2 today
   ```

   `thesis-ch2` 换成你自己的承诺 id；`today` 可以换成 `tomorrow`、`date 2026-11-20`、`park`（搁置）或 `complete-step`（这一步做完）。它给出要写进注意力安排的条目和放在哪里，自己不写入；你自己贴，或你同意后让助手贴。注意力安排是库里的 `06_active_context/work_state/attention-schedule.md`，文件不存在时，从它打印出完整路径的模板建立（本仓库里是 `09_templates/attention-schedule.zh.md`）。哪件事什么时候做，始终由你定。

### 你应该看到什么

库体检没有问题时，输出是这样的：

```text
你的库：读到 3 张卡，其中 2 张会在 Dashboard 里显示。
库体检：没有发现问题。
没有写入任何文件。想刷新 Dashboard 里你的库，加上 --write 再运行一次（它写 dashboard/data/researchos-local.json，Git 会忽略这个文件）。
```

议程查询先报数，再逐项列出：

```text
已登记且核验的主责推进中 1 项 | 协作推进中 0 项 | 等待 0 项 | 排队 0 项 | 暂停 0 项 | 需关注 1 项
覆盖：未闭合，以上是已登记数量 | 已登记 1 项 | 已分类 1 项 | 覆盖候选 0 个
- [P0] 论文第二章 —— 在新划分上重跑基线
```

`attend` 打印一段条目，开头写明「未写入：本仓库只显示改动」和它要放进哪个文件：

```text
### research_portfolio:thesis-ch2

- provider_id: research_portfolio
- item_id: thesis-ch2
- attention_date: 2026-11-12
…
```

把这段贴进注意力安排之后，`today` 会在「今日」下列出这项承诺；排到以后或搁置的承诺，列在「不在今日」一行。库里还没有注意力安排时，所有承诺都读作未安排。

### 如果看到的不一样

- **库体检列出了问题。** 每一条都写明是哪张卡、哪一处，照着改，再跑一遍，直到它说「没有发现问题」；找不到原件的那一条只是提醒。
- **议程查询写着「覆盖：未闭合」。** 这时报出的数量只是已登记的数量，见上面第 6 小步。
- **想撤销一次安排。** 条目要替换原有的一段时，`attend` 会先打印被替换的那一段，留着它就能撤销；`python3 scripts/ros.py --root personal_vault attend thesis-ch2 undo` 说明怎样手工改回。删掉那一段，承诺就回到未安排。

### 现在你能做到

你的库里除了材料，还有你自己的做法：风格卡和启发式卡让助手照你的习惯来，边界卡守住不外传的东西。你会给库做体检、查自己手上有几件事、备份，并把承诺排到具体的日子。五步到这里走完了。真正有用的长期记忆仍需要你自己的论文、笔记、项目、报告、决策或关系上下文，并保留可追溯的边界，且只在当前判断需要时补充。

## 6. 其他用法

这一节收着五步主线之外的用法，各小节互相独立，需要哪个读哪个。

### 没有终端：只在浏览器里聊天

如果你在浏览器里用 ChatGPT 或 Claude，没法运行命令，`ros` 就跑不起来，来源变了把判断交回来复核的这一圈也就用不上。这是第一阶段的限制（见附录 D）。三层读法仍然有用。打开仓库的 GitHub 页面 <https://github.com/huuuuusy/researchos-public-starter>，点 **Code**，再点 **Download ZIP**，下载后解压。要用的骨架是 `09_templates/basic/research-identity.zh.md` 和 `09_templates/basic/capsule.zh.md`，填好的样子在 `examples/starter-cards/zh-CN/`。把骨架和你的发表清单一起贴进聊天，请 AI 帮你起草；方向摘要里「做什么任务读哪张卡」那张表，只列你会上传的卡。把这两页贴进聊天里项目的说明（project instructions），这是第一层；做某项任务时，只上传它需要的一两张卡，这是第二层；PDF、数据、原始笔记这类原件默认不放进聊天，这是第三层，只有要核对某个具体数字或引文时才上传一份。你贴进去和上传的内容都会发给服务商，所以 README 里「哪些不要交给助手」清单上的东西一律不要上传。

如果你自己或帮你的人偶尔能运行一条命令，`python3 scripts/plan_context.py <路线> --vault personal_vault --mode quick --pack <文件>` 会把这一档要读的卡拼成一份可以直接粘贴的文本，例如 `~/Desktop/chat-pack.md`；换成 `standard` 会再加上方向摘要点名的卡。卡片包开头有一段写给聊天里 AI 的话（这些卡是你写的，里面的路径在你电脑上，需要别的就问你），用 `standard` 时末尾还附上这类任务的做法说明。只有标为 public 或 internal 的卡会放进去；sensitive 和 private 的卡不放进来，命令会告诉你它们在哪里。它不会写进本仓库，除非写在 `personal_vault/` 下。

### 可选的 Dashboard

Dashboard 是可选的，处于冻结状态：可以按这里的说明使用，但不在开发之中。

调度器和 Dashboard 用的是两个互不相干的虚构世界。`examples/scheduler-demo/`（中文版是 `examples/scheduler-demo-zh/`）里的调度器演示库是一个关于遮挡论文的库：两项承诺、两张卡片和一条判断。Dashboard 演示显示 `08_exports/public_starter/demo-research-agenda.zh.md` 里的六个虚构议程事项。两者互不引用。

在仓库根目录启动 demo：

```bash
python3 scripts/start_researchos.py --mode dashboard --port 8880
```

![公开 Dashboard：打开事项，预览并取消关注日期，预览交接；什么都不保存，也不运行。](figures/readme/dashboard-zh.gif)

然后打开 `http://127.0.0.1:8880/`。这里显示 `08_exports/public_starter/demo-research-agenda.zh.md` 里的六个虚构议程事项，与第 3 步调度器的演示库是两个不同的虚构世界，不需要真实 API key。在 personal-vault 模式下（见下文「用 Dashboard 打开自己的库」），它显示你的论文、人物、项目和报告；决策、启发式、风格卡、方向摘要和会议卡不在这里显示，要通过助手来读。演示设在一个固定的虚构日期 2026-08-11，页面状态栏会显示这个日期，所以无论哪天打开，它的日历和时效读起来都一样。普通启动直接读取随仓发布的公开安全投影，不重写受 Git 跟踪的文件；只有投影缺失时才自动恢复。维护者修改 demo 来源后，用 `python3 scripts/build_public_starter_data.py --write` 显式重建。启动器只在 `/session-config` 确认运行时身份匹配时复用已有服务，因此公开 demo 不会被误认为 personal-vault、报告中的原型或占用同一端口的其他程序；遇到这种情况会停止并建议另一个端口。`--mode public-starter` 只报告本仓库的运行状态，不启动服务器。其余模式：

```bash
python3 scripts/start_researchos.py --mode public-starter --check --provider codex
python3 scripts/start_researchos.py --mode cli
python3 scripts/start_researchos.py --mode gui --port 8880
python3 scripts/start_researchos.py --mode public-starter
```

Dashboard 是与 Agent 客户端互补的跨会话注意力与控制面，不是第二个聊天入口，也不是 Agent 路线的前置条件。它以统一工作台呈现现在与资料两个语义区域：`现在`在多项承诺之间分配注意力并承载日历，`资料`通过一项或少量承诺 lens 连接来源与关系。Work 与 Review 是精确事项的局部状态，只在该事项的抽屉中展开，不形成第三个顶层屏幕。各界面的定义和路由规则见[系统参考](system-reference.zh.md#主要路线与辅助界面)。第一次可以判断一个虚构承诺，也可以展开可选的直接 Agent 输入、只给一个目标；默认输入框只收集目标和可选来源，Dashboard 不提供模型、推理档位或输出类型控件。第一次打开时：

1. 在统一工作台选择事项卡，核对当前依据和下一步。
2. 拖到日历日期只预览关注安排；取消或重新载入即可丢弃预览。
3. 在右侧查看关联资料，再预览并复制 Agent 交接任务包。
4. 只在独立的私有助手任务中执行。
5. 审阅返回结果，再通过研究者确认流程提出长期更新。复制本身不代表已执行或已接受结果。

月历以日为最小单位，不提供小时网格。`+N` 展开当天；“安排”卡可拖拽或用 `Alt + 方向键` 移到另一日，作为内存中的预览，界面标明未保存，刷新即恢复。只有支持写入的私有运行时才会经可撤销的排期 owner 保存日期；复查、截止和生命周期标记始终不可拖动。“完成本步”“结束 Work Session”和“结束项目”关闭的东西不同：当前承诺、执行会话和长期项目生命周期。Work Session 是与 Agent 客户端处理一个意图的有界执行会话，结束会话不等于结束项目。另外三件事也要分开：生命周期说明项目处于投稿、审稿、rebuttal、修订还是完成；进行中 / 待推进 / 暂不推进 / 已结束说明如何管理整个项目；今日 / 明日 / 未来 / 搁置只说明下一步何时再次占用注意力。审稿中的项目仍可从关联资料中找到；真实事件或复核日期到达时，它的下一动作会回到工作台。

本仓库固定为 copy-only。它不启动本机 Codex 或 Claude Code CLI，不探测本机 provider，不调用远程 API，不写长期记忆（它可能写的两类文件列在下文），不执行 Inbox 写回任务，也不接受任意 shell 命令。提交任务只生成交给独立私有助手的任务包；工作台总是只产出可复制的任务说明。受控执行路线是 personal-vault 模式和 private 运行态；private 是报告中原型的运行态，本仓库不支持。各部分的分工如下：

| 界面 | 负责 | 不负责 |
| --- | --- | --- |
| Agent 客户端 | 解释意图、深读材料、推理、修改文件、生成成果、与你反复协作、运行验证 | 代替研究者确认证据或修改长期记忆，维护 Today 投影 |
| CLI | 确定性 route、query、receipt、validation 与维护命令 | 开放研究判断或第二套 authority |
| canonical Markdown 与 Git | 长期事实、决定、provenance 与恢复坐标 | 生成或仅运行时状态 |
| Dashboard | 可重建的投影：分诊近期注意力、可视化资源与关系、按天排期、选择执行路线、显示状态与结果 | 产品事实、首次使用前置条件、开放讨论、模型选择、深度推理、跨文件编辑，或批准长期变化 |

后台准备只运行有边界、结果能原位返回的工作；开放讨论或复杂修改时，界面复制一个完整任务包，由你粘贴到 Agent 客户端的新任务中；只有确实存在可核验的绑定时，“继续已有任务”才可用。Dashboard 不复制你的聊天，只显示有界的会话状态。普通选卡保持原位，系统建议可以直接建立 Work Session。独立的私有 Codex runner 更适合深度读取、文件修改、成果生成、验证、后台队列、逐项执行或隔离写入。

```text
现在：恢复一份有边界的当前研究焦点
  -> 资料：按需补上下文
  -> 现在 / Agent：继续研究工作
  -> 需要时由 Agent 有界读取
  -> 可见回答、成果或 diff
  -> 待复核：核对结果、候选变化、回执和交接
  -> 研究者决定
  -> 在私人库中验证后写回
```

一轮工作会明确三件事。Work Session 包含当前目标、按需来源、当前结果、折叠的过程记录、工作牌组和被冻结的 prompt/模板语言；浏览器协调状态和最近任务摘要都不是长期记忆。候选交接是一个有边界的任务，带着来源卡片、证据状态、敏感性、拟议权威变化、影响范围和验证状态。待复核边界提醒你：任务完成不等于证据确认，来源路径也不是写回目标。在私人库中，后续步骤是执行、证据核对、你的决定、验证后写回和恢复包；它们保持受控，本仓库不会把它们伪装成自动完成。

待复核不只接收写回提案。它的[完整接收范围](system-reference.zh.md#共享治理边界)还包括有界未知、break-glass 确认、结果、验证失败、回滚与关闭前必须明确的交接；长期、敏感、公开或破坏性变化一律经过它。公开运行态从不执行持久写回。

页面语言选择只改变可见文案。新建 Work Session 会冻结当时的界面语言，作为该任务的回答和任务包语言；任务中途切换界面语言不会改写已有任务。内容语言在 `config/researchos.runtime.example.json` 中设置，决定生成记录和 prompt：

```json
"public_starter": {
  "content_language": "zh-CN",
  "available_content_languages": ["en", "zh-CN"],
  "alternate_language_files": "reference_only_do_not_read_by_agent"
}
```

用 `python3 scripts/build_public_starter_data.py --language en --write` 或 `--language zh-CN --write` 重建。被选中的语言进入 `08_exports/public_starter/generated-public-starter-data.json` 和 `dashboard/data/researchos-dashboard.json`。另一种语言的文件留在仓库中作为参照；除非你要求翻译、对照或双语维护，Agent 正常运行时不读取它们。

```text
浏览器 Dashboard
  -> 运行在 127.0.0.1 的本地 Python 服务器
  -> 当前选择的 demo 或 personal-vault 投影 / provider 状态
  -> 交给独立私有助手的可复制任务包
```

Agent 路线与 Dashboard 依赖同一套 Markdown 和确认规则，本仓库遵守上文说明的只复制边界，所有 `/codex-runner` 提交都被拒绝，不启动线程或命令。personal-vault 与私有运行态可以把本地回答或成果返回待复核；只有在你提交任务后才启动本地 Codex。公开 demo 中保存反馈、Inbox 条目或卡片分组、撤回确认、运行更新的本地端点都返回 403 `public_starter_writeback_blocked`，只在 personal-vault 模式下执行。公开 demo 只会写两类文件：上传到 Git 忽略的会话目录的来源，以及你运行已登记的 `build_public_starter_data` 动作时重建的示例投影（示例来源不变时字节不变）。这些本地 HTTP 端点服务 Dashboard，不是公网 API；完整列表见[系统参考](system-reference.zh.md#本地-http-端点)。

本地 **打开**/**定位** 在 macOS 使用 Finder，在 Windows 使用 Explorer，在 Linux 尝试 `xdg-open`；当前桌面环境没有可用 opener 时，服务器返回清楚的失败信息并保留路径，供手动打开。

**用 Dashboard 打开自己的库。** 需要时，在 `personal_vault/` 上打开 Dashboard：

```bash
python3 scripts/start_researchos.py --mode personal-vault --port 8881
```

然后打开 `http://127.0.0.1:8881/`。这个模式读取 `personal_vault/06_active_context/research-portfolio.md`，以及 `personal_vault/00_identity/` 到 `personal_vault/06_active_context/` 中带 frontmatter 的卡片，从不显示虚构的示例数据。服务器在启动时读取卡片，所以新建或修改的卡片要重启服务器后才出现。第一次启动只建出部分分层目录（`00_identity/`、`01_knowledge/papers/` 及其下的 `own_papers/reading_notes/` 与 `source_files/`、`01_knowledge/projects/`、`04_people/collaborators/` 和 `06_active_context/`）；`02_decisions/`、`05_workflows/` 等其他目录，需要时自己建。`ros` 不读 `lifecycle_phase` 和 `activation_trigger`，阶段写错或缺少触发条件，只会在 Dashboard 的 personal-vault 投影里标出。

personal-vault 投影写入 Git 忽略的 `dashboard/data/researchos-local.json`，因为它可能含私人派生元数据；公开 demo 与 personal-vault 不共用生成数据文件。在这个模式下，Dashboard 和本机的 Codex 都只往 `personal_vault/` 里写；公开的模板只能读，不能借这个模式改动仓库里受跟踪的演示文件（写入范围的细节见系统参考的[三种运行方式](system-reference.zh.md#三种运行方式)）。personal-vault 也不会把任务完成变成证据确认：长期变化需要明确目标、证据检查、你的批准和写回后的验证。

### 中断了怎么接上

中断后，在 `personal_vault/` 里留一份简短交接：问题、来源及版本、最后确认的判断（没有就写「无」）、还没定的候选、下一步。交接只是备忘，不等于批准了里面的候选。回来后先看来源有没有变，再接着做；你之前已经批准的事，在原来的范围内继续有效，不用再问一遍。核对交接和来源是否还对得上的命令，见系统参考的[中断后接续与 ResearchOS 之外的修改](system-reference.zh.md#中断后接续与-researchos-之外的修改)。

### 在 ResearchOS 之外改过文件

如果你或助手不经 `ros` 直接改了卡片，`ros` 没有经手这次修改，它的记录里也就没有这次批准。想留下凭据，就保存改动的 diff、你同意的那句话、改了哪些文件和检查结果。细节见同一节系统参考。

### 判断它有没有帮上忙

拿一件真实的任务来用，隔 24 到 72 小时、按平常的节奏再回来接着做。拿来对照的做法是：同一个模型、同样的材料和时间，再加一页你自己写的交接说明（问题、来源及版本、已有判断、下一步）。记下漏看了哪些证据、接上和纠正花了多少工夫、有没有严重错误、哪些判断变了、维护它费多少事，没比出好处的对比也要留着。装好了、合成测试通过了、工程检查通过了，都不等于有真人接受了它，也不等于证明了它对研究有帮助。报告解释了这条证据边界；其中的合成案例只用来说明怎么比，不能证明已测得的效率提升或研究者成长。

## 附录 A：命令与字段参考

命令行打印出的每个 `ros …`，都指 `python3 scripts/ros.py --root <文件夹> …`，而且 `--root` 要写在子命令之前。不带 `--root` 时，`ros` 把本仓库本身当作库来读，其中没有承诺。

### 本仓库里 `ros` 写什么

在出厂的 `runtime_scope: public_starter` 下：

- 每条 `ros` 命令只在 `--root` 下 git 忽略的 `06_active_context/work_state/` 里写出任务包、候选与会话记录。没有命令写长期来源。
- `run` 只接受 `--executor copy_packet`，拒绝所有 provider。personal-vault 模式（第 6 节）不改变这一点。
- `admit <candidate>` 和 `admit --reconfirm` 不先询问，直接通过复制回退显示拟议差异，并在其后打印可以直接贴进文件的文本和位置，因此不向长期来源准入任何东西。
- `admit --confirm` 只有你在自己的终端回答时，才会在 git 忽略的本地账里记一笔事后确认；由 Agent 转述时只记为转述（asserted），确认请求仍未关闭。两种情况都不写来源，也不算准入。
- `close` 列出会话开始以来回收或登记、尚未决定的候选。这里它们始终尚未决定，因为 `admit` 既不准入，也不记录拒绝；你手工应用、又确认了其判断的候选单独列出，不用再处理。

准入与派发的代码随本仓提供，但默认关闭。只有 `config/ros.json` 显式写明 `runtime_scope: "private"` 才会开启；缺这个键、拼错或写成其他值，都按只复制模式运行。`runtime_scope: "private"` 是技术报告里原型的设置，原型开启准入与派发运行；本仓库不支持这个设置，例如 `ros attend` 此时会给出说明后停止，什么也不写。从演示库复制出来的库保留它的 `config/ros.json`，所以同样按只复制运行。

13 个子命令在本仓库里都有。多数命令先跑一次边界检查，记在同一份 git 忽略的账里；`receipt`、`propose rule`、`admit --rollback`、`collect --abandon` 与 `attend` 不跑。所有命令都不写长期来源：

| 命令 | 本仓库里的行为 |
| --- | --- |
| `today` | 只复制：列出变化与待处理事项并开启会话；库里有注意力安排（`06_active_context/work_state/attention-schedule.md`）时，「今日」列出排在今天的承诺，没有时所有承诺都读作未安排；排到以后或搁置的承诺列在「不在今日」一行 |
| `close` | 与报告中的原型同语义；列出的候选始终尚未决定，你手工应用并确认过的除外；范围一行在其中有非零项时显示，或加 `--all` 显示 |
| `propose judgment`、`episode-close`、`rule` | 同语义：登记候选 |
| `admit` | 只显示拟议改动：`<candidate>` 与 `--reconfirm` 显示拟议差异，以及要贴的文本和位置；`--confirm` 只记确认、不写入，且只有你在自己的终端回答时才生效；`--rollback` 被拒绝，因为这里不写来源，也就不回滚来源 |
| `decide` | 同语义：记下决定；`cancel` 与 `confirm` 只有你在自己的终端回答时才生效；由助手转述的 `defer` 只记为代理转述，这一项照常列出，并打印要你在自己的终端运行的那一行 |
| `answer` | 同语义：记下回答；`satisfied` 与 `cancel` 会关闭这条请求，因此只有你在自己的终端回答时才生效；只有检查依据是研究者判断时才提供 `satisfied`，出厂规则里没有这样的检查 |
| `state`、`context`、`rules`、`receipt` | 同语义，只读 |
| `run` | 只复制：只接受 `--executor copy_packet`，拒绝所有 provider |
| `collect` | 同语义，只是不记 run-state 账 |
| `attend` | 给出要写进注意力安排的条目（今天、明天、某天、搁置、这一步做完）和放在哪里，不写入；你自己贴，或你同意后让助手贴，`today` 就会列出；文件从它打印出完整路径的模板建立（本仓库里是 `09_templates/attention-schedule.zh.md`）。条目要替换原有的一段时，先打印被替换的那一段，留着它就能撤销；`undo` 说明怎样手工改回 |

### 承诺的字段与取值

承诺清单（commitment list）是在声明范围内记录主责/协作、承诺状态、优先级、时效、负责人与角色、唯一下一步和权威来源的账本。承诺（commitment）是项目当前唯一的下一步或下一次判断；被排期的是它，而不是整个项目；无论用哪个客户端查看或继续，它都只保留一个有边界的状态和一个下一安全动作。一项承诺的最小写法见[第 2 步](#2-第-2-步建好你自己的库)，各字段的取值如下：

| 字段 | 取值 |
| --- | --- |
| `id` | 由你自己定的简短标识。 |
| `responsibility` | `lead` 或 `support`。 |
| `state` | `mainline`、`queued`、`conditional`、`waiting`、`paused` 或 `closed` 之一。 |
| `last_verified` | 写成 `YYYY-MM-DD` 的日期。 |
| `source_path` | 这项承诺依据的卡片，路径相对于 `personal_vault/`，由你自己定。 |
| `lifecycle_phase` | `scoping`、`planned`、`experiment_preparation`、`production`、`gated_operation`、`writing`、`release_preparation`、`submitted`、`under_review`、`rebuttal`、`decision`、`revision`、`accepted`、`published`、`paused`、`completed` 之一。 |
| `activation_trigger` | `lifecycle_phase` 取 `submitted`、`under_review` 或 `decision` 时还要写，即让这一项重新回到眼前的事件。 |

`ros` 用不了的值会列在 `today` 输出的「承诺清单问题」一栏和 `ros rules --check` 里，这项承诺不会悄悄从检查中消失。`ros` 不读 `lifecycle_phase` 和 `activation_trigger`，阶段写错或缺少触发条件，只会在 Dashboard 的 personal-vault 投影里标出。`question`、`judgments`、`responsibility`、`state` 和 `priority` 是判断类字段，手工改过之后要确认，做法见[附录 B](#附录-b替换一条判断以及改过承诺字段之后的确认)；`last_verified`、`current_stage`、`next_step` 这类事实不用确认。

### 不用 Dashboard 的入口命令

CLI 路线准备同一个“目标、来源、结果、边界”的闭环，不启动服务器或 Dashboard；第二条命令给出第一次上手要读的那一个文件，即[首次上手说明](../08_exports/public_starter/onboarding-step-by-step.zh.md)：

```bash
python3 scripts/start_researchos.py --mode cli
python3 scripts/plan_context.py first_run_onboarding --lang zh-CN
```

## 附录 B：替换一条判断，以及改过承诺字段之后的确认

第 3 步里选了 B，就是要用一条新的判断替换旧的。下面仍用示例里的故事：改版之后，你认为应该先只比较中度遮挡。命令里的承诺 id、判断 id 和编号，都换成你自己的终端里打印的。

1. **起草新判断，用一个新的 id。** 把它写进仓库之外的草稿文件，比如 `~/Desktop/judgment-draft.md`：

   ```text
   > [!judgment] j-occlusion-moderate
   > 结论：改版后先只比较中度遮挡，重度遮挡等协议定稿。
   > 依据：01_knowledge/papers/example-benchmark.md
   ```

2. **登记，并看它会改什么。** 第二条命令里的候选编号，换成第一条打印出的那个：

   ```bash
   python3 scripts/ros.py --root personal_vault propose judgment --file ~/Desktop/judgment-draft.md --target commitment:occlusion-paper
   python3 scripts/ros.py --root personal_vault admit c-6f5f2bfc
   ```

3. **贴入文本，并撤掉旧判断。** `admit` 在 diff 下面打印了要贴的文本和位置：照着把它们贴进 `research-portfolio.md`，然后删掉旧的判断块，以及承诺 `judgments` 一行里的旧 id。改完之后，这一行只剩新的 id：

   ```text
   - judgments: j-occlusion-moderate
   ```

4. **运行 `today`，在你自己的终端里确认两件事。** 它会列出新判断「尚未确认」；旧判断的复核则移到「待你回答的问题」下，因为它所指的判断已经不在了：

   ```bash
   python3 scripts/ros.py --root personal_vault today
   python3 scripts/ros.py --root personal_vault admit --confirm j-occlusion-moderate
   python3 scripts/ros.py --root personal_vault answer 2070e7ba52 cancel --reason "已由 j-occlusion-moderate 替换"
   ```

   两条都回答 `y`。旧复核用 `cancel` 回答；它的 `narrow` 选项只是让这条事项保持未关闭、留到下一个版本。编号用 `today` 在「待你回答的问题」下打印的那个。

5. **收尾，再确认 `judgments` 一行。** 你改过的 `judgments` 一行是判断类字段，要单独确认，确认新判断块并不包括它：有会话开着时，`admit` 会打印带真实编号的 `ros decide <编号> confirm`，这次会话接下来的 `today` 和 `close` 也会列出它。这一条在收尾之后确认才关得上，所以先运行 `close`，再确认：

   ```bash
   python3 scripts/ros.py --root personal_vault close
   python3 scripts/ros.py --root personal_vault decide 04f91de4bd confirm
   ```

做完之后，`close` 的「本次的判断类改动」里有三行：新判断「已事后确认」，旧判断「已删除或不再扫描」，以及 `judgments` 一行从旧 id 变成新 id。你已应用并确认的那个候选，`close` 会单独列出，不用再处理。收过尾的会话不能再收一次：确认了 `close` 列出的事项之后，先运行 `today` 开一个新会话，再运行 `close`；这时 `today` 里这项承诺下面写的是「没有要复核的事项」。

### 手工改了承诺字段之后

手工改承诺字段也是一样。`today` 读过这项承诺之后，你若改了 `state`、`priority`、`question`、`responsibility` 或 `judgments`，这次会话接下来的 `today` 和 `close` 都会把这次写入列为待确认的判断类字段，之后每次 `today` 也会列出。`today` 跑过之后才加进清单的新承诺也算：它的 `state`、`priority`、`question`、`responsibility` 四个字段各要确认一次。先运行 `close` 收尾，再在你自己的终端运行它打印的那一行，回答 `y`（下面的编号只是示例）：

```bash
python3 scripts/ros.py --root personal_vault decide 1f43c540ed confirm
```

由助手转述的调用只记为代理转述，这一条保持原状态。`last_verified`、`current_stage`、`next_step` 这类事实不用确认。

## 附录 C：安全规则与常见错误

不要把 Dashboard 暴露到公网。不要提交 API 密钥、令牌、`.env` 或本地运行配置，也不要把真实敏感人物、未公开稿件、真实关系笔记、原始语料或私人运行日志放进本仓库。发布前，`python3 scripts/validate_public_safety.py` 会检查这些内容。

公开 demo 的跟踪文件约 19 MB，连同 Git 历史约 100 MB，不复制任何私人的库。ResearchOS 不治理你的磁盘空间：在 personal-vault 与私有运行态中，本地 Work Session 接收你选择的研究材料，不设产品级文件类型、大小、数量或保存期限配额，实际上限只是本机文件系统和运行环境；公开 demo 则接受单个文件最大 1 GiB 的上传。两者都不因空间阈值自动删除你的材料。系统只约束自己产生的冗余，具体见[低冗余运行契约](system-reference.zh.md#低冗余运行契约)；本机空间较低或会话副本较大时只给出非阻断提醒。

常见错误是：任务尚未明确就扫描整个仓库；把 Agent 回答当成已确认记忆；把 Dashboard 的 JSON 数据或浏览器里的状态当作权威来源；把真实材料放在 `personal_vault/` 之外，或把含有真实材料的 clone 推送到公开远程仓库；在 Markdown 或受跟踪配置中写入密钥；删除虚构示例；期待一个空库自己理解一个研究领域。正确使用时，助手会说明读了什么、刻意没读什么；每个来源都有边界；每个解释都先成为候选；每个长期变化最后都有验证结果，或一个明确的缺失证据。

## 附录 D：第一阶段的范围

现在是 ResearchOS 的第一阶段：一个人用，材料是你电脑上的文件，拍板在你自己的终端里。这一节把本仓库做什么、不做什么集中讲清楚；手册其他地方只在用到时提一句。

本仓库只打印改动、由你复制进去，自己不写入；文档里把这叫「复制回退」或「只复制」。它和技术报告里的原型用同一套核心代码，随附的数据都是虚构的。它可以读卡片、做检查、准备交给助手的任务包、显示计划中的改动，但不会说某件事已经替你做了，也不会说你的长期记录已经改了。排期、准入后的写入、维护写入和记下「这一步做完了」，都只在原型里有。[技术报告](technical-report.zh.md)描述的就是这个原型，它能做的比本仓库多，报告里的主张不是本仓库的能力清单。同一套代码有三种用法：

| | 本仓库（出厂） | 用你自己的材料（第 2 步；Dashboard 的个人库模式见第 6 节） | 技术报告里的原型 |
| --- | --- | --- | --- |
| 里面是什么 | 虚构的例子，可以公开 | 你自己的卡片，放在 Git 忽略的 `personal_vault/` 里 | 真实的本地研究材料 |
| `ros` 命令 | 只打印改动，由你复制进去 | 一样，`ros` 仍然只打印改动 | 你在终端确认之后，由系统写进卡片（包括 `ros admit`） |
| 可选的 Dashboard | 只能看：拖动日期只是预览，把事情交给助手时只生成可复制任务包，由你贴进自己的助手 | 经你确认后会写进 `personal_vault/`；本机装了 Codex 命令行的话，还能在页面里直接拿到回答或成果 | 页面里直接拿到回答或成果，也能写入 |
| 和别的私人系统相连 | 没有 | 没有 | 只在作者自己的部署里 |
| 公开出去 | 例子本身可以公开 | 任何内容都要先单独复查（见安全导出规则） | 同左 |

三种用法都可以配 Claude Code、Codex 或其他能读写本地文件的助手，没有哪一步要求你安装 Codex。只有在 personal-vault 模式下想让 Dashboard 页面直接给出回答时，才用到本机的 Codex 命令行（附录 E「本地执行 provider」）。执行设置、写入范围这类工程细节，见系统参考的[三种运行方式](system-reference.zh.md#三种运行方式)。

第一阶段的 `ros` 要在终端里运行。只在浏览器里聊天时它跑不起来，来源变了把判断交回来复核的这一圈也就用不上；这时还能怎么用，见第 6 节的[没有终端：只在浏览器里聊天](#没有终端只在浏览器里聊天)。

### 报告里的例子：来源被纠正后保住什么

下面的虚构比较沿用[报告第 4.1 节的贯穿会话](technical-report.zh.md)，展示来源更正前后的状态。哪部分受影响，由候选指出、由你来定；系统自己算不出来。

| 阶段 | 来源、判断与未决条件 | 核对什么 |
| --- | --- | --- |
| 变化前 | 两组基准支持目标在画面内时 A 优于 B；重新出现后的情况未测试，实验已计划 | 证据、范围、未知与下一动作一起保留 |
| 来源更正 | 第二组上 A 的优势消失，第一组不变 | 来源变化触发复核，不裁定科学判断 |
| 候选 | 连同证据保留第一组说法，撤回第二组说法，重新出现的实验保持未决 | 基于更正后的来源版本审阅候选 |
| 决定边界 | 报告中的原型只在研究者决定后准入；本仓库默认只准备候选或拟议差异，不实际准入 | 分清拟议变化与已接受的长期状态 |

![构建系统自己重建，研究状态等研究者决定。](figures/architecture/researchos-r11-contrast-zh.png)

*报告图 1。构建系统自己重建，研究状态等研究者决定。论文的第二组基准被更正后，判断 J 来自第一组的证据保留，来自第二组的证据要复核，重新出现条件保持未决，另一个会话提出、论文并不支持的说法被拒绝。只有研究者的准入才写入。*

第 1 步和第 3 步能实际运行的演示用的是另一份虚构的演示库，它不执行报告里的准入，也不把判断收窄到一部分。两个例子都不能说明它比「每次手写一页交接说明」更好。

## 附录 E：给维护者

这一节的内容平时用不到：工程检查、公开 demo 的投影，以及本地执行 provider 的配置。

### 工程检查

工程检查运行 `python3 scripts/validate_headless.py`。它验证完整的无 Dashboard profile，这个 profile 必须在 `dashboard/` 目录不存在时通过：routing、receipts、runtime 与 provider 边界、task extensions、public safety、links 和 focused zero-dashboard 行为，且不为通过而放宽 authority 检查。它不是用 Agent 客户端读一份来源的前提。

### 关闭示例案例

这一步可选，只改变公开 demo 的投影。`python3 scripts/build_public_starter_data.py --disable-cases` 预览去掉虚构案例后的投影；加上 `--write` 会重写受跟踪的 `08_exports/public_starter/generated-public-starter-data.json` 和 `dashboard/data/researchos-dashboard.json`，所以除非你确实要发布不带案例的 demo，不要提交这个结果。`python3 scripts/build_public_starter_data.py --write` 会把它们恢复。关闭案例不删除任何文件；示例保留为字段和放置位置的对照。

### 本地执行 provider

除了 Agent 路线和 Dashboard，也可以在文本编辑器或 GitHub 上直接读 Markdown，了解目录、案例和手册。Codex 图形界面适合 AI 协助阅读和修改，Codex 命令行可执行小型交接并记录日志；ResearchOS 没有远程 API provider。ResearchOS 不附带 Codex，公开 Dashboard 也不会启动它。若要在独立私有 Agent 任务中执行复制出的任务包，按 OpenAI 当前官方说明安装 Codex 图形界面或命令行，并用 `command -v codex` 与 `codex --version` 检查。macOS 桌面应用可能把命令行程序放在 `/Applications/Codex.app/Contents/Resources/codex`；如果 `codex --version` 不可用而该文件存在，把它加入 `PATH`，或设置 `alias codex="/Applications/Codex.app/Contents/Resources/codex"`。不要把登录令牌、API 密钥或账号信息写入仓库。

本仓库登记了两个本地 provider：`codex` 与 `claude_code`，在这里两者都是 `copy_only`。`python3 scripts/runtime_profile_cli.py list --scope public_starter` 显示本仓库的只复制配置档，`show --profile codex --scope public_starter` 查看某个保留 provider 在本版中的投影；两者都不需要凭据或网络。公开 Dashboard 的默认配置是：

```json
{
  "provider_mode": "copy_only",
  "allow_local_codex": false,
  "execution_scope": "none",
  "maintenance_scope": "registered_actions",
  "allow_real_api": false
}
```

换成白话：本机 runner 关闭，只能运行登记过的维护动作（例如重建演示数据），也不调用真实 API。

不要把公开 Dashboard 改成执行主机。如需使用两个本地命令行 provider 之一，先切换到 personal-vault 模式（private 运行态属于报告中的原型，本仓库不支持），配置不纳入 Git，运行 provider 检查，再在那里启用它；命令行工具的登录信息留在仓库之外。检查命令是 `python3 scripts/validate_runtime_config.py` 和 `python3 scripts/start_researchos.py --mode personal-vault --check --provider codex`，后者会报告本机是否装了这个命令行工具。
