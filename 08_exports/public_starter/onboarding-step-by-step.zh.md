---
type: onboarding_guide
title: "首次上手：从示例到自己的库"
status: ready
created: 2026-06-26
updated: 2026-11-07
tags:
  - public-starter
  - onboarding
  - personal-vault
sensitivity: public
exportable_to:
  - public_template
---

# 首次上手：从示例到自己的库

[English](onboarding-step-by-step.md) | 中文

## Agent Summary：这份说明解决什么

这是唯一的首次上手路线。`python3 scripts/plan_context.py first_run_onboarding` 指向它，README 和用户手册也指向它。它带新用户从虚构示例走到一个有一项承诺、一张卡片和一条判断的个人库，共五步：跑一遍演示，在演示夹具上走一遍会话，在 Git 忽略的 `personal_vault/` 里建自己的库并加一条判断，需要时用 Dashboard 打开它，最后核对第一轮是否完成。每一步都写明做什么、应该看到什么、看到的不一样时怎么办。每一步都可以由用户在终端里完成，也可以由助手提出命令、等用户确认后执行。真实材料只进入 `personal_vault/`，本说明里的任何一步都不会在用户批准前写入长期记忆。

## 开始前

自己动手只需要 Python 3.10 或更高版本，并在仓库文件夹里打开终端；支持 macOS 与 Linux，Windows 请用 WSL，此外不需要安装别的东西。让助手陪你走，还需要一个能在你电脑上运行命令的助手：README 的「开始前要准备什么」写明了用哪个、要不要付费，「你的材料会去哪里」写明了哪些东西不能交给它。本仓库随附的内容全部是虚构的。

输出里有几个词用的是特定意思，比如承诺、候选、准入。用户手册第 1 节（`docs/user-manual.zh.md` 的「你会遇到的词」）每个用一句话说明。

最省事的是让 Claude Code、Codex 这类助手陪你走完本说明：把 README 里那一句话发给它，它会下载仓库，问你要发表清单、几篇论文或其他来源、合作者和一个项目，再据此建好你的库，依据是 `AGENTS.md` 的「First Run」一节。本说明是这一过程以及自己动手时的参考。按本说明工作的助手应说明当前在第几步，每次只提出一条命令或一处修改，用户确认前不写任何文件。

## 第 1 步：跑一遍演示

```bash
python3 scripts/ros_demo.py --lang zh-CN
```

**应该看到什么。** 六个编号步骤，每步以 `━━` 开头，最后是一小段「接下来」。演示在一份虚构研究图的临时副本上运行，不改动你 clone 里的任何东西。第 3 步里来源变化，`today` 标出依赖它的判断：

```text
━━ 3. 来源变化（基准协议改版）；ros today 标出依赖它的判断
…
    · [b5d4e33c7c] 判断「先在遮挡条件下比较 A 和 B，暂不扩大数据集。」的依据变了
```

第 5 步把重新确认打印成 diff，不写入；第 6 步收尾时复核仍待处理。「还没有准入回执」「不算准入」「复制回退」这类说法都不是报错，它们说的是什么都没有准入，本仓库本来就是这样工作的。

**看到的不一样时。** 找不到 `python3`，或者脚本报语法错误，先看 `python3 --version` 是否为 3.10 或更高。在 WSL 之外的 Windows 上跑不起来，因为缺它需要的文件锁。不带 `--lang` 时输出英文。

## 第 2 步：在夹具上走一遍会话

演示是自动跑完的。现在在 `examples/scheduler-demo-zh/` 的夹具上，一条命令一条命令地走一遍同样的会话。用户手册第 3 节的「请助手起草：context、run、collect」按顺序列出六条命令（`today`、`context`、`run`、`collect`、`admit` 和 `close`），并说明每条做什么。第一条是：

```bash
python3 scripts/ros.py --root examples/scheduler-demo-zh today
```

**应该看到什么。** `today` 开启会话，在「待判断」下列出夹具里的承诺。`run` 写出任务包并打印 run id；`collect` 读回示例回答，打印候选 id；每个 id 都要填进下一条命令。`admit` 打印一段 diff，并说明未写入、未准入。`close` 结束会话，把这个候选列为尚未决定：

```text
本次会话开始以来回收或登记、尚未准入也未拒绝的候选（未写入）：
  · 候选 c-621349ea：commitment:occlusion-paper
```

**看到的不一样时。** 你的 id 和手册里的示例不同，用终端里打印的那个。按当天日期运行时，`today` 还会说承诺已有若干天未核实；新 clone 上某份来源还可能显示「在核实后有更新」。两者都来自日期，原因见手册第 3 节。`today` 什么都没列出时，检查 `--root examples/scheduler-demo-zh` 是否写在子命令之前：不写它，`ros` 读的是本仓库自己的图，其中没有承诺；写在子命令之后，会被当作无法识别的参数拒绝。走查留下的记录在 Git 忽略的 `examples/scheduler-demo-zh/06_active_context/work_state/` 里，第 3 步不会把它们复制过去。

## 第 3 步：建自己的库

1. 把演示研究图复制到 Git 忽略的库文件夹：

   ```bash
   python3 scripts/ros_demo.py --init personal_vault --lang zh-CN
   ```

   应该看到：

   ```text
   已从虚构演示图建好 personal_vault/，演示的 ros 记录、示例回答和判断没有带过来。接下来：
   ```

   后面跟着下面这三步。如果提示 `research-portfolio.md 已经存在；--init 只用于还没有承诺清单的文件夹`，说明你以前建过库：直接改那一份，或者把它挪开再重建。`personal_vault/` 已经存在但还没有承诺清单也没关系，比如你先打开过 personal-vault Dashboard。

2. 打开 `personal_vault/06_active_context/research-portfolio.md`。保留开头的 frontmatter 和标题，把两项虚构承诺，即 `### 遮挡迁移论文（虚构）` 和 `### 研讨会报告（虚构）` 连同各自的字段列表，换成你自己的一项。下面是最小的完整承诺，把值改成你自己的，`last_verified` 写今天的日期：

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

   每个字段能取哪些值，见用户手册附录 A。

3. 删掉两张虚构卡片 `personal_vault/01_knowledge/projects/occlusion-tracking.md` 和 `personal_vault/01_knowledge/papers/example-benchmark.md`，在你写的 `source_path` 上从模板建一张自己的卡片：

   ```bash
   cp 09_templates/basic/project.zh.md personal_vault/01_knowledge/projects/thesis-ch2.md
   ```

   填好 `title`，把 `# 项目名` 标题换成同一个名字；`ros` 用这个标题显示卡片。`Agent Summary` 要能单独读懂；已有结果写明出处，写一件待核的事，在「证据边界」里写明原件在哪里；最后删掉「填写说明」。论文卡片改用 `09_templates/basic/paper.zh.md`。每类卡填好的样子见 `examples/starter-cards/zh-CN/`。想先从一份简短的个人简介开始，可以请助手先起草一份[材料接入笔记示例](onboarding-intake-note-example.zh.md)那样的接入笔记。

   在项目之外，再建几张卡片，库里就有了你自己的背景：用 `09_templates/basic/person.zh.md` 在 `personal_vault/00_identity/profile.md` 建一张个人档案卡，`relationship_type: self`（姓名、单位、研究方向、代表作，取自你的主页、Google Scholar、ORCID 或 DBLP 页面，或简历里的科研部分）；用 `09_templates/basic/paper.zh.md` 在 `personal_vault/01_knowledge/papers/` 下建三到五张论文卡；这些论文里出现两次及以上的合作者，各在库的人物文件夹中的 `collaborators/` 下建一张卡，`relationship_type: candidate`，只写一起发表过的论文。项目卡片的 `related_papers` 指向它所依据的论文。

4. 建以后每次会话助手最先读的两张入口页：用 `09_templates/basic/research-identity.zh.md` 在 `personal_vault/00_identity/research-identity.md` 写研究身份摘要，用 `09_templates/basic/capsule.zh.md` 在 `personal_vault/01_knowledge/capsules/` 下写一份方向摘要，说明做什么任务读哪张卡。助手按 `AGENTS.md`「First Run」一节第 2 到 6 步走的就是这条路。论文、项目和摘要卡把 `sensitivity` 设为 `internal`，个人档案和合作者卡设为 `sensitive`：`ros context` 会把 internal 的卡交给助手；sensitive 的卡助手取不到，要你在自己的终端运行并确认，内容印在你的终端里，你再把任务需要的部分复制给助手；private 的卡从不打包。

5. 检查这个库：

   ```bash
   python3 scripts/ros.py --root personal_vault today
   ```

   应该在「待判断」下看到你的承诺，而且只有你的：

   ```text
   待判断（1 项承诺：未安排、需定下一步、复核到期，或有判断事项等你处理）
     ■ 论文第二章  ［未安排］
       （没有要复核的事项）下一步：在新划分上重跑基线；排到今天：ros attend thesis-ch2 today
   ```

   显示「未安排」是正常的：还没有排期。你决定什么时候做之后，`ros attend <id> today` 会给出要放进注意力安排的条目，贴进去之后 `today` 会在「今日」下列出这项承诺；排到以后或搁置的，列在「不在今日」那一行。用 `python3 scripts/ros.py --root personal_vault close` 结束会话；新建的库会报告 `结果：完成（complete）；收尾时待办 0，…`。如果在 `today` 读过之后又改了 `state`、`priority`、`question` 或 `responsibility`（比如为了改正承诺清单问题），这次会话接下来的 `today` 和 `close` 都会把这次写入列为待确认的判断类字段，之后每次 `today` 也会列出；在你自己的终端运行 `python3 scripts/ros.py --root personal_vault decide <编号> confirm` 并回答 `y` 即可（由助手转述的调用只记为代理转述）。

   `today` 出现「承诺清单问题」时，每一行都写明是哪个字段、可以取哪些值，例如 `state「active」不是可用值（mainline, waiting, queued, conditional, closed, paused）`，照着改承诺清单即可。虚构承诺还出现在「待判断」下，说明它们的块还留在文件里；如果只出现在「待你回答的问题」下并标着 `subject_absent`，说明你在替换之前运行过 `today`，那是虚构演示留下的记录：删掉 `personal_vault/06_active_context/work_state/`，再运行一次 `today`。卡片不在你写的路径上时，这里会显示 `source_path … 在这个文件夹里不存在`；`python3 scripts/ros.py --root personal_vault rules --check` 报告同样的问题，一切就位时报告 `问题 0 条`。用 `--init personal_vault --lang zh-CN` 建的库，`config/ros.json` 已设为中文输出。

### 加一条判断，看来源变化时会发生什么

库里没有判断时，来源变了 `today` 也没有东西可标。下面用一个虚构的心理学例子走一遍。假设你的项目依据一张元分析卡片 `01_knowledge/papers/reappraisal-meta.md`，你眼下的看法是认知重评训练对焦虑症状有中等程度的改善。把这个看法写进仓库之外的一个草稿文件（比如系统的临时文件夹）：

```text
> [!judgment] j-reappraisal-effect
> 结论：认知重评训练对焦虑症状有中等程度的改善。
> 依据：01_knowledge/papers/reappraisal-meta.md
```

用 `python3 scripts/ros.py --root personal_vault propose judgment --file <草稿> --target commitment:<你的 id>` 登记，再运行它打印的那行 `ros admit <候选编号>`；这时它提示今天没有开着的会话，是正常的。在本仓库里 `admit` 不写入任何东西，只打印它会对 `research-portfolio.md` 做的改动，依据的版本已经填好。照原样应用这段改动（或者请助手代为应用），之后 `today` 会显示这条判断是新的、尚未确认；在你自己的终端运行 `python3 scripts/ros.py --root personal_vault admit --confirm j-reappraisal-effect` 并回答 `y`。回复会说这条判断是直接写进文件的，记为事后确认，不算准入：本仓库对所有手工贴进去的改动都这样记录，不是你做错了什么。依据像这里一样写卡片，不要写它所在的承诺：承诺的日期或下一步一更新，依据写了承诺的判断就会回来。

现在假设这篇元分析纳入的一项研究被撤稿了。在论文卡片里记下这件事，比如加一节「## 更正」，再运行一次 `today`：

```text
    · [d2db02806a] 判断「认知重评训练对焦虑症状有中等程度的改善。」的依据变了
        依据已变化：……（01_knowledge/papers/reappraisal-meta.md）
        A 复核后仍成立：刷新依据版本并确认 → ros admit --reconfirm j-reappraisal-effect
        B 判断需要修改：写新的判断块 → ros propose judgment --file <草稿> --target <卡片或 commitment:id>
        C 维持现状，暂缓 → ros decide d2db02806a defer --until <日期>
```

剔除那项研究后效应是否还成立，系统判断不了，由你决定选哪一项。选 A，本仓库打印出刷新依据版本的改动，照原样应用后再在终端确认。选 B，用一个新的 id 起草替代的判断，照[用户手册附录 B](../../docs/user-manual.zh.md#附录-b替换一条判断以及改过承诺字段之后的确认)「替换一条判断」去做，那里列出了随后要做的确认。编号和你的输出不同时，用终端里打印的那个。伦理方案修订、预注册更新或者数据替换，也都按同样的方式处理：更新对应卡片，`today` 会把依赖它的判断交回来。

## 第 4 步：用 Dashboard 打开这个库（可选）

```bash
python3 scripts/start_researchos.py --mode personal-vault --port 8881
```

**应该看到什么。** 服务器打印一小段说明，然后一直运行，按 Ctrl+C 停止：

```text
ResearchOS personal vault dashboard
- mode: personal-vault
- vault: user-provided local Markdown
- dashboard: http://127.0.0.1:8881/
```

打开 `http://127.0.0.1:8881/`。这个模式只读你的库，从不显示虚构示例数据，所以没有什么需要关闭。`现在`显示你的承诺，`资料`显示你的卡片。在某个事项上开始工作时，ResearchOS 会建立一个有边界的 Work Session，并从`现在`进入`推进`，也就是该事项的抽屉；本机安装的 Codex CLI 只在你提交任务后运行，而且只在 `personal_vault/` 内写入。`待复核`会明确显示返回结果，连同证据边界、成果路径、决定状态和接续交接；你确认之前，什么都不会成为长期记忆。

**看到的不一样时。** 服务器在启动时读取卡片，新建或修改卡片后要重启它。端口被占用时，给 `--port` 换一个数。第一次启动会建哪些文件夹，见用户手册第 6 节的「可选的 Dashboard」。想另外打开虚构示例，运行 `python3 scripts/start_researchos.py --mode dashboard --port 8880`。

## 第 5 步：核对第一轮是否完成

满足下面四条，第一轮就完成了：

- `python3 scripts/ros.py --root personal_vault today` 列出一项你自己的承诺，没有虚构承诺；
- 它的卡片在 `source_path` 上，写明了来源边界，`ros rules --check` 报告问题 0 条；
- 承诺清单里有你的一条判断，你已在自己的终端确认过它；没有判断，来源变了也不会有提醒；
- `git status` 里没有因你的材料产生的改动。`personal_vault/` 被 Git 忽略，根本不会出现在那里。

### 哪些东西不进公开 clone

- 真实材料只放进 `personal_vault/`。含有它的 clone 不要推送到公开远程仓库。
- 只读取用户提供的文件和公开链接；不绕过登录、付费墙、robots 限制或其他访问控制。
- 私人、在投、未公开或边界不明的材料保持 `local_only`。
- 电话、住址、证件号、签名和与研究无关的 CV 信息不写入卡片。
- 合著关系只说明对方是「合著者候选」，不推断指导、私交或未来合作。
- 每个生成的解释在用户确认前都是候选。
- 第一次只建一份档案、几篇论文、反复出现的合作者和一个项目；批量导入、插件和深读等一个闭环跑通后再做。

## 第一轮之后

下面这些只作为可选参考：

- [卡片成熟度标准](onboarding-card-maturity-rubric.zh.md)；
- [个人卡片分级](onboarding-person-card-levels.zh.md)；
- [论文卡片分级](onboarding-paper-card-levels.zh.md)；
- [合作者候选示例](onboarding-collaborator-card-levels.zh.md)；
- [报告卡片示例](onboarding-talk-card-levels.zh.md)；
- [计划卡片示例](onboarding-plan-card-levels.zh.md)；
- 示例插件安装和系统维护。

这些是进阶参考，不是上手前提。
