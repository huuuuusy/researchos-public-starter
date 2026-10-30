---
type: onboarding_guide
title: "首次上手：从示例到自己的库"
status: ready
created: 2026-06-26
updated: 2026-10-29
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

这是唯一的首次上手路线。`python3 scripts/plan_context.py first_run_onboarding` 指向它，README 和用户手册也指向它。它带新用户从虚构示例走到一个有一项承诺、一张卡片的个人库，共五步：跑一遍演示，在演示夹具上走一遍会话，在 Git 忽略的 `personal_vault/` 里建自己的库，需要时用 Dashboard 打开它，最后核对第一轮是否完成。每一步都写明做什么、应该看到什么、看到的不一样时怎么办。每一步都可以由用户在终端里完成，也可以由助手提出命令、等用户确认后执行。真实材料只进入 `personal_vault/`，本说明里的任何一步都不会在用户批准前写入长期记忆。

## 开始前

需要 Python 3.10 或更高版本，并在仓库文件夹里打开终端；支持 macOS 与 Linux，Windows 请用 WSL。不需要安装别的东西。本仓库随附的内容全部是虚构的。

输出里有几个词用的是特定意思，比如承诺、候选、准入。用户手册第 1 节（`docs/user-manual.zh.md` 的「你会遇到的词」）每个用一句话说明。

最省事的是让 Claude Code、Codex 这类助手陪你走完本说明：把 README 开头的安装提示粘贴给它，它会下载仓库、问你一个项目的情况，再按回答建好你的库，依据是 `AGENTS.md` 的「First Run」一节。本说明是这一过程以及自己动手时的参考。按本说明工作的助手应说明当前在第几步，每次只提出一条命令或一处修改，用户确认前不写任何文件。

## 第 1 步：跑一遍演示

```bash
python3 scripts/ros_demo.py --lang zh-CN
```

**应该看到什么。** 六个编号步骤，每步以 `━━` 开头，最后是一小段「接下来」。演示在一份虚构研究图的临时副本上运行，不改动你 clone 里的任何东西。第 3 步里来源变化，`today` 标出依赖它的判断：

```text
━━ 3. 来源变化（基准协议改版）；ros today 标出依赖它的判断
…
    · [b5d4e33c7c] 判断「Compare A and B under occlusion first; do not enlarge the dataset yet.」的依据变了
```

第 5 步把重新确认打印成 diff，不写入；第 6 步收尾时复核仍待处理。「还没有准入回执」「不算准入」「复制回退」这类说法都不是报错，它们说的是什么都没有准入，本仓库 本来就是这样工作的。

**看到的不一样时。** 找不到 `python3`，或者脚本报语法错误，先看 `python3 --version` 是否为 3.10 或更高。在 WSL 之外的 Windows 上跑不起来，因为缺它需要的文件锁。不带 `--lang` 时输出英文。「范围 /｜… 个键」这类计数行是记账用的，演示自己也说了第一次读可以跳过。

## 第 2 步：在夹具上走一遍会话

演示是自动跑完的。现在在 `examples/scheduler-demo/` 的夹具上，一条命令一条命令地走一遍同样的会话。用户手册第 3 节的「自己走一遍会话」按顺序列出六条命令（`today`、`context`、`run`、`collect`、`admit` 和 `close`），并说明每条做什么。第一条是：

```bash
python3 scripts/ros.py --root examples/scheduler-demo --lang zh-CN today
```

**应该看到什么。** `today` 开启会话，在「待判断」下列出夹具里的承诺。`run` 写出任务包并打印 run id；`collect` 读回示例回答，打印候选 id；每个 id 都要填进下一条命令。`admit` 打印一段 diff，并说明未写入、未准入。`close` 结束会话，把这个候选列为尚未决定：

```text
本次会话开始以来回收或登记、尚未准入也未拒绝的候选（未写入）：
  · 候选 c-621349ea：commitment:occlusion-paper
```

**看到的不一样时。** 手册里的命令不带 `--lang zh-CN`，输出是英文；想看中文，就在每条命令的 `--root …` 后面加上它。你的 id 和手册里的示例不同，用终端里打印的那个。按当天日期运行时，`today` 还会说承诺已有若干天未核实；新 clone 上某份来源还可能显示「在核实后有更新」。两者都来自日期，原因见手册第 3 节。`today` 什么都没列出时，检查 `--root examples/scheduler-demo` 是否写在子命令之前：不写它，`ros` 读的是本仓库自己的图，其中没有承诺；写在子命令之后，会被当作无法识别的参数拒绝。走查留下的记录在 Git 忽略的 `examples/scheduler-demo/06_active_context/work_state/` 里，第 3 步不会把它们复制过去。

## 第 3 步：建自己的库

1. 把演示研究图复制到 Git 忽略的库文件夹：

   ```bash
   python3 scripts/ros_demo.py --init personal_vault --lang zh-CN
   ```

   应该看到：

   ```text
   已从虚构演示图建好 personal_vault/，演示的 ros 记录、示例回答和判断没有带过来。接下来：
   ```

   后面跟着下面这三步。如果提示 `research-portfolio.md 已经存在；--init 只用于还没有任务总表的文件夹`，说明你以前建过库：直接改那一份，或者把它挪开再重建。`personal_vault/` 已经存在但还没有任务总表也没关系，比如你先打开过 personal-vault Dashboard。

2. 打开 `personal_vault/06_active_context/research-portfolio.md`。保留开头的 frontmatter 和标题，把两项虚构承诺，即 `### Occlusion Transfer Paper` 和 `### Workshop Talk` 连同各自的字段列表，换成你自己的一项。下面是最小的完整承诺，把值改成你自己的，`last_verified` 写今天的日期：

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

   每个字段能取哪些值，见用户手册第 5 节。

3. 删掉两张虚构卡片 `personal_vault/01_knowledge/projects/occlusion-tracking.md` 和 `personal_vault/01_knowledge/papers/example-benchmark.md`，在你写的 `source_path` 上从模板建一张自己的卡片：

   ```bash
   cp 09_templates/project-template.md personal_vault/01_knowledge/projects/thesis-ch2.md
   ```

   填好 `project_name`，把 `# Project Name` 标题换成同一个名字；`ros` 用这个标题显示卡片。再写明来源边界、证据状态和一个缺失的事实。论文卡片改用 `09_templates/paper-template.md`。想先从一份简短的个人简介开始，可以请助手先起草一份[材料接入笔记示例](onboarding-intake-note-example.zh.md)那样的接入笔记。

   在项目之外，再建几张卡片，库里就有了你自己的背景：用 `09_templates/person-template.md` 在 `personal_vault/00_identity/profile.md` 建一张个人档案卡，`relationship_type: self`（姓名、单位、研究方向、代表作，取自你的主页、Google Scholar、ORCID 或 DBLP 页面，或简历里的科研部分）；用 `09_templates/paper-template.md` 在 `personal_vault/01_knowledge/papers/` 下建三到五张论文卡；这些论文里出现两次及以上的合作者，各在库的人物文件夹中的 `collaborators/` 下建一张卡，`relationship_type: candidate`，只写一起发表过的论文。项目卡片的 `related_papers` 指向它所依据的论文。助手按 `AGENTS.md` 的「First Run」一节走的就是这条路；这些卡片的 `sensitivity` 默认设为 private，除非你另有决定。

4. 检查这个库：

   ```bash
   python3 scripts/ros.py --root personal_vault today
   ```

   应该在「待判断」下看到你的承诺，而且只有你的：

   ```text
   待判断（1 项：未安排、需定下一步或复核到期）
     ■ 论文第二章  ［未安排］
       （没有待复核的要求；按下一步推进）
   ```

   显示「未安排」是正常的，因为本仓库 不带注意力安排。用 `python3 scripts/ros.py --root personal_vault close` 结束会话；新建的库会报告 `结果分类：complete（待办 0；…）`。如果在 `today` 读过之后又改了 `state`、`priority`、`question` 或 `responsibility`（比如为了改正任务总表问题），`today` 和 `close` 会把这次写入列为待确认的判断类字段；在你自己的终端运行 `python3 scripts/ros.py --root personal_vault decide <编号> confirm` 并回答 `y` 即可（由助手转述的调用只记为代理转述）。

   `today` 出现「任务总表问题」时，每一行都写明是哪个字段、可以取哪些值，例如 `state「active」不是可用值（mainline, waiting, queued, conditional, closed, paused）`，照着改任务总表即可。虚构承诺还出现在「待判断」下，说明它们的块还留在文件里；如果只出现在「待你回答的问题」下并标着 `subject_absent`，说明你在替换之前运行过 `today`，那是虚构演示留下的记录：删掉 `personal_vault/06_active_context/work_state/`，再运行一次 `today`。卡片不在你写的路径上时，这里会显示 `source_path … 在这个文件夹里不存在`；`python3 scripts/ros.py --root personal_vault rules --check` 报告同样的问题，一切就位时报告 `问题 0 条`。用 `--init personal_vault --lang zh-CN` 建的库，`config/ros.json` 已设为中文输出。

之后形成的判断以候选进入：请助手按 `ros close` 打印的格式写出，再用 `ros propose judgment` 登记。

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

**看到的不一样时。** 服务器在启动时读取卡片，新建或修改卡片后要重启它。端口被占用时，给 `--port` 换一个数。第一次启动会建哪些文件夹，见用户手册第 5 节。想另外打开虚构示例，运行 `python3 scripts/start_researchos.py --mode dashboard --port 8880`。

## 第 5 步：核对第一轮是否完成

满足下面三条，第一轮就完成了：

- `python3 scripts/ros.py --root personal_vault today` 列出一项你自己的承诺，没有虚构承诺；
- 它的卡片在 `source_path` 上，写明了来源边界，`ros rules --check` 报告问题 0 条；
- `git status` 里没有因你的材料产生的改动。`personal_vault/` 被 Git 忽略，根本不会出现在那里。

### 哪些东西不进公开 clone

- 真实材料只放进 `personal_vault/`。含有它的 clone 不要推送到公开远程仓库。
- 只读取用户提供的文件和公开链接；不绕过登录、付费墙、robots 限制或其他访问控制。
- 私人、在投、未公开或边界不明的材料保持 `local_only`。
- 电话、住址、证件号、签名和与研究无关的 CV 信息不写入卡片。
- 合著只支持“合著者候选”，不推断指导、私交或未来合作。
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
