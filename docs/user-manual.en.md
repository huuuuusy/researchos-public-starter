<p align="right">
  <strong>English</strong> | <a href="user-manual.zh.md">中文</a>
</p>

# ResearchOS User Manual

This manual follows a reader from the first session to a private vault of their own: what this repository is and the words its output uses, how to run one research loop in an agent client, how to try the session scheduler, what the optional Dashboard shows, and how to replace the fictional demo with your own material. For a first run, follow the [first-run guide](../08_exports/public_starter/onboarding-step-by-step.md); this manual is the reference behind it. The [System Reference](system-reference.en.md) defines states, governance boundaries, architecture, code owners and directories. The [Governance and Extension Guide](governance-guide.en.md) covers publication, customization, plugins, contribution and the license.

This is the first stage of ResearchOS: one person, files on your own computer, decisions made at your own terminal. What the first stage includes and does not include is set out once, in the [README](../README.md#what-the-first-stage-includes-and-does-not-include), with the full list in Supplementary Note 6 of the technical report.

## 1. What this repository is

ResearchOS Public Starter is the public starter edition of ResearchOS: a small, file-based tool for individual researchers, whose cards are ordinary files on your computer and whose examples are all fictional. It keeps your judgment continuous across tools, projects and time. An agent client such as Claude Code or Codex, or another file-aware CLI, is the primary execution route, and it is complete on its own: you state one goal, provide the minimum source, receive an answer or artifact, and any durable change waits for your approval and validation. The first loop needs no Dashboard, plugin, model setting or knowledge of the whole repository. The optional Dashboard makes attention, linked material and review boundaries visible, but it does not accept judgments or enlarge execution permissions.

The researcher chooses the question and judges what the evidence supports. Models and tools carry out bounded parts of the work, and ResearchOS keeps their results connected to sources, acceptance status, unresolved dependencies and the next action; when a source changes, the judgments that depend on it come back for a recheck. It is not a hosted service, an autonomous scientist, a complete personal knowledge base, a question-answering tool detached from evidence, or a polished all-in-one product, and an empty vault will not understand a research domain for you. Literature search, experiment execution and general agent runtimes belong to specialized tools; [Related Research Tools](reference/RELATED_RESEARCH_TOOLS.md) describes adjacent tools and where ResearchOS stays narrow.

This repository prints changes for you to paste in and never writes them itself; the documentation calls this copy fallback, or copy-only. It shares its core code with the prototype in the technical report, and all the data it ships is fictional. It can read cards, run checks, prepare task packets for an assistant and show planned changes, but it never claims that something was done for you or that your lasting record changed. Scheduling, writing an admitted change, maintenance writes and recording that a step is done exist only in the prototype. The [technical report](technical-report.en.md) describes that prototype, which can do more than this repository; its claims are not a list of what this repository does. The same code can be used in three ways:

| | This repository (as shipped) | Your own material (personal-vault mode, Section 5) | The prototype in the report |
| --- | --- | --- | --- |
| What is in it | Fictional examples, safe to publish | Your own cards, in the git-ignored `personal_vault/` | Real local research material |
| `ros` commands | Print the change for you to paste | The same: `ros` still only prints changes | Write into the card after you confirm at your terminal, including `ros admit` |
| The optional Dashboard | Look only: dragging a date is a preview, and handing a task to an assistant gives a copyable execution brief only; no local answer or model run. You paste it into your own assistant | Writes into `personal_vault/` after you confirm; with the Codex command-line tool installed, it can also give an answer or a file right in the page | Gives an answer or a file in the page, and can write |
| Links to other private systems | None | None | Only in the author's own setup |
| Publishing | The examples are safe to publish | Anything needs a separate review first (see the safe-export policy) | The same |

All three work with Claude Code, Codex or another assistant that can read and write files on your computer, and nothing requires you to install Codex. Only in personal-vault mode, if you want the Dashboard page itself to answer, does it use the Codex command-line tool on your computer (Section 5, "Local execution providers"). Engineering details such as execution settings and where each mode may write are in the System Reference, under [Three ways to run the code](system-reference.en.md#three-ways-to-run-the-code).

Besides Python 3.10 or newer, you install nothing else: no package, API key, database, Node.js, server or cloud account; the Dashboard also needs a modern browser. Automated tests (CI) run on Python 3.10 and 3.13. Get the repository through Git, GitHub Desktop or GitHub's **Download ZIP**, open a terminal in the folder, and use `python3`. macOS and Linux are supported; on Windows, run it inside WSL (Windows Subsystem for Linux), because the file locks it relies on are not available in native Windows Python. Keep real, sensitive or unpublished material out of the tracked files; Section 5 explains where it goes.

### Words you will meet

The demo output and these guides use a few words in a narrow sense. For a first run, the line next to each word is all you need, and the output phrases listed here are normal, not errors. The [technical report](technical-report.en.md) uses the same words and defines them precisely.

| Word | What it means here |
| --- | --- |
| commitment | A project's one current next step or next judgment. It, not the whole project, is what gets scheduled. |
| commitment list | The file `06_active_context/research-portfolio.md`: one block per project, holding its current commitment. |
| card | A Markdown file with frontmatter about one project, paper, person or other source. Commitments and judgments point to cards as their evidence. |
| research state | The question, the evidence, the accepted judgments with their scope, the open conditions and the next step. `ros state` prints them as Q, E, J, B and N. |
| candidate | A model's output or a draft that has not been accepted yet. |
| admission, admit | The researcher accepting a candidate into research state. This repository only shows the planned change; it never admits. |
| judgment block | The `> [!judgment]` Markdown block that records one accepted judgment with its basis. |
| item | A registered piece of maintenance work, such as rechecking a judgment after its source changed. |
| waiting on your answer, deferred | Work waiting on your answer waits for the researcher's answer to one question. Deferred work waits for a trigger, such as a date. |
| receipt | The record of what was done and checked. |
| complete, complete_with_held, human_stopped, budget_stopped | The outcome `close` reports: nothing open; only work waiting on your answer or deferred; you ended the session with work still open; the session's budget ran out. Ending with work open is normal and is not an error. |
| decision boundary | The moment the system looks at what has arrived and decides what to do next. The output calls it "the last ros command". |
| copy fallback, copy-only | `ros` prints the change, such as the diff `admit` would make, for you to paste; it runs and writes nothing itself. |
| "No admission receipt yet" | The judgment was written straight into the file and nobody admitted it, so `today` asks you to confirm it. |
| "Confirmed … after the fact", "not an admission", "not admitted" | You said yes to a judgment already in the file: the request to confirm it is closed, but nothing was admitted. |
| `personal_vault/` | The git-ignored folder in your clone for your own material. |
| vault | The folder of cards and the commitment list that `--root` points to: `personal_vault/` is your own vault, and `examples/scheduler-demo/` is the fictional demo vault. Technical documents also call a vault a research graph, and the demo vault the fixture. |
| public, internal, sensitive, private | A card's `sensitivity` label, which decides whether `ros context` packs the card for the assistant: public and internal cards are packed; sensitive, private and unlabeled ones are not. |

## 2. One loop in your agent client

Open the folder in Claude Code, Codex, Gemini CLI or another file-aware assistant. A first run needs four things: a goal, meaning what should be answered, organized or produced now; a source, meaning one file you provide or one explicit public link; a result, which is an answer, an openable artifact or a reviewable diff; and a boundary with a next step, saying what is sourced, what remains a candidate and what happens next. If you are unsure where to begin, or do not use a terminal yet, let the assistant guide you and copy only the command it gives:

```text
I do not know how to use ResearchOS Public Starter yet. Act as my guide. Read AGENTS.md only; if the environment already loaded it, do not reread it or scan the repository. Then explain in plain language: 1. what this project is for; 2. which path I should take now; 3. the next file or command; 4. what I should not put into a public repository. Do not write files yet; ask me at most two questions if needed.
```

With a concrete task, hand over the source directly:

```text
I have a PDF: [link or local path]. It is [public / submitted / internal / boundary unclear].

Use ResearchOS to help me understand it and relate it to [my task]. Read AGENTS.md first and only the smallest workflow or target files needed. Return the source boundary, a short reading note, candidate claims, proposed save target, and what needs my confirmation. Do not write durable memory until I approve the candidate and its evidence boundary.
```

The assistant should say what it read and what it intentionally left unread, which route fits, which privacy or export boundary applies, and whether its result is an answer, an artifact or a proposed durable change. A good reading note says what the source says, how you read it, one limitation, what is still missing and the next step, and it keeps what the source supports apart from what has not been tested.

If the ordinary answer is enough, stop there. In any case, once you can say what it rests on, what is still open and what to do next, you can stop. Keep something as a candidate only when it is worth keeping long term and you can name the card it belongs in; approving it and checking it afterwards are still two separate steps. To move on to your own material, follow Section 5, and tell the assistant not to write files until you confirm.

You can leave these alone the first time; they are all still there once the first loop works: plugins and installing them, system diagrams and the full architecture, maintenance commands and code, mapping every relationship at once, choosing a model or setting up a model service in advance, and importing every paper, project and person at once.

Without a Dashboard, every round takes the same steps:

```text
one goal + the least source material
  -> the assistant works within the agreed scope, or runs one command
  -> one of three results: an answer, a file it made, or a change waiting for your decision
  -> you check the source, what is still unknown, sensitivity and the actual effect
  -> only after you approve does lasting content change, with a check, a record and a way to undo it
```

Four rules keep the round honest. The assistant's output starts as a candidate. A finished task does not confirm the evidence. The Dashboard and the data files programs generate only display things; the Markdown cards are what counts. Private material is not made public without a separate review. The System Reference's [state and authority model](system-reference.en.md#state-and-authority-model) describes the states behind these rules; a source path says where evidence comes from and is never where something is saved.

**When the assistant says a card was excluded.** The assistant fetches cards with `ros context`, whose output ends with a line such as `[delivered 1; excluded 1]`, where "excluded" counts the cards it left out, with one line under it for each of those cards saying why. An excluded card is usually a sensitive one, such as a person or meeting card: it records other people, so it is not handed to the assistant, and the assistant should not open the file directly instead. If a task really needs it, run `python3 scripts/ros.py --root personal_vault context <card>` in your own terminal, answer `y`, and copy to the assistant only the part the task needs. The shipped commitment list is labeled internal, so a project's question and judgments are packed; a card or commitment list with no label is not packed. Keep in mind that the label decides only what `ros context` packs; it does not stop an assistant from opening a file itself.

### Keep the reading set small

Reading tiers limit both the number of files and the estimated tokens of the first pass:

| Tier | First-pass files | Estimated total tokens | Use when |
| --- | ---: | ---: | --- |
| `Quick` | 1 | about 10k | You have an exact source or a narrow question. |
| `Standard` | up to 5 | about 35k | The task needs one workflow guide and a little project context. |
| `Evidence` | up to 8 named files | about 60k | A formal claim or public output needs checking. |

Start in `Quick`; when you give an exact paper, draft or target path, Quick starts there. Standard may add one workflow guide, a project page and a few main cards. Evidence adds only check records, reading notes or original sources that answer the current checking question. Raise the tier only when you can name the missing fact or judgment, and when either limit would be exceeded, choose a smaller subset and work in batches. This keeps token use and unrelated context down while the long-term library stays complete. The reading tier and how hard the assistant thinks are separate: raise the tier when material is missing, and turn up the assistant's thinking (some clients call it reasoning effort) when the reasoning is long or the judgment is hard. Which model to use and how hard it thinks are set in the assistant. Whether the result is an ordinary answer, a file or a candidate change to a card follows from the task, so you do not have to classify it in advance. Open discussion, reasoning and drafting happen in the assistant through the repository instructions and need no handoff.

In your own vault, add `--vault personal_vault` to `python3 scripts/plan_context.py <route> --mode quick` (or `standard`, `evidence`), and it lists for each level which of your own cards the assistant reads. It follows your vault's language, so no `--lang` is needed. Quick reads one card: for an outward task (such as answering an outside request or checking before an export) the boundary card, otherwise the working-style card for the task, or your research identity page when neither exists. Standard holds at most five files on the first pass: the research identity page, the working-style card, the direction summary, the task's workflow and any card the route names (such as the boundary card before a proposal). The cards the direction summary names are listed separately; the assistant fetches the ones it needs one by one with `ros context`, and they do not count toward those five. Evidence holds at most eight on the first pass: on top of standard, paper writing and proposals add two index cards, the outputs index and author roles (listed only when you have them); originals are opened only when named in those cards' evidence boundaries, and only for a stated check. Cards you have not written yet are named in the list with the skeleton to start from; the assistant skips them until they exist.

### Without a terminal: a browser chat

If you use ChatGPT or Claude in a browser and cannot run commands, `ros` does not run, so the loop that brings a judgment back when its source changes is not available to you. That is a limit of this first stage. The three layers in a card still help. On the repository's GitHub page, <https://github.com/huuuuusy/researchos-public-starter>, choose **Code**, then **Download ZIP**, and unzip it. The skeletons are `09_templates/basic/research-identity.md` and `09_templates/basic/capsule.md`, and `examples/starter-cards/en/` shows both filled in. Paste a skeleton and your publication list into the chat and ask the AI to draft the page; in the direction summary's table of which card to read for which task, list the cards you will upload. Paste the two pages into the project instructions of your chat: that is layer 1. For a task, upload only the one or two cards it needs: layer 2. Originals such as PDFs, data and raw notes stay out of the chat by default: layer 3. Upload one only to check a specific number or quotation. What you paste or upload is sent to the provider, so never upload anything on the README's "What to keep away from the assistant" list.

If you, or someone helping you, can run one command now and then, `python3 scripts/plan_context.py <route> --vault personal_vault --mode quick --pack <file>` writes a paste-ready pack of the cards that level reads, for example `~/Desktop/chat-pack.md`; use `standard` to add the cards your direction summary names. The pack opens with a short note to the chat (the cards are yours, paths in them are on your computer, ask you for anything else), and with `standard` it ends with the workflow for that task. Only cards labelled public or internal go in; the command prints where the sensitive and private ones it left out are. It refuses to write inside this repository except under `personal_vault/`.

### Example from the report: what survives a source correction

This fictional comparison reuses the [worked session in Section 4.1 of the report](technical-report.en.md) to show the state before and after a source correction. Which part is affected is pointed out by the candidate and decided by you; the system cannot work it out on its own.

| Stage | Source, judgment and open condition | What to check |
| --- | --- | --- |
| Before | Two benchmark sets support A over B while the target stays in view; re-appearance is untested and its experiment is planned | Keep the evidence, scope, unknown and next action together |
| Source correction | A's advantage disappears on the second set; the first set is unchanged | A source change triggers recheck, not a scientific verdict |
| Candidate | Retain the first-set claim with its evidence, withdraw the second-set claim, and leave the re-appearance experiment open | Review a candidate on the corrected source version |
| Decision boundary | In the report's session a change is admitted only after the researcher decides; default public operation prepares candidates or planned differences without admission | Separate a proposed change from accepted durable state |

![A build system rebuilds on its own; research state waits for the researcher's decision.](figures/architecture/researchos-r11-contrast-en.png)

*Figure 1 of the report. A build system rebuilds on its own; research state waits for the researcher. When the paper's second benchmark set (set 2) is corrected, the evidence the judgment J draws from set 1 is kept, the evidence from set 2 must be rechecked, the re-appearance condition stays open, and another session's proposal, which the paper does not support, is refused. Only the researcher's admission writes.*

The demo you can actually run in Section 3 uses a different fictional demo vault; it does not perform the report's admission and does not narrow a judgment to a part. Neither example shows that ResearchOS does better than writing a one-page handoff note by hand each time.

### Picking up after an interruption

After an interruption, leave a short handoff in `personal_vault/`: the question, the sources and their versions, the last confirmed judgment (or "none"), the candidates not yet decided, and the next step. A handoff is only a note; it does not approve the candidates in it. When you come back, first check whether the sources changed, then carry on; what you already approved stays approved within its original scope, so nobody needs to ask again. The command that checks whether a handoff still matches its sources is in the System Reference, under [Resuming after an interruption and changes made outside ResearchOS](system-reference.en.md#resuming-after-an-interruption-and-changes-made-outside-researchos).

### Files changed outside ResearchOS

If you or an assistant edit a card directly rather than through `ros`, `ros` never handled that change, so its records hold no approval for it. To keep evidence, save the change as a diff, the words in which you agreed, which files changed and the result of any check. The same System Reference section has the details.

### Judging whether it helped

Use it on a real task and come back to it at your normal pace, 24 to 72 hours later. The practice to compare against is the same model, the same material and the same time, plus a one-page handoff note you write yourself (the question, the sources and their versions, the judgments so far, the next step). Note what evidence was missed, how much effort it took to pick up again and to correct things, any serious errors, which judgments changed and how much upkeep it needed, and keep the comparisons that showed no benefit. A successful installation, a passing synthetic test or an engineering check does not mean a person has accepted it, nor that it has been shown to help research. The report explains this evidence boundary; its synthetic example only shows how to compare and is not evidence of measured productivity or researcher growth.

## 3. The session scheduler and command-line checks

`python3 scripts/ros_demo.py` (or `--lang zh-CN`) runs on a temporary copy of a fictional demo vault. A source card changes and the dependent judgment is flagged for recheck; the researcher then requests reconfirmation, which this repository shows as a planned change without admitting it, and at session close the recheck is still listed as pending. Stop when you can identify the source change, the candidate or plan, the open work and the next action. If a word in the output is unfamiliar, see [Words you will meet](#words-you-will-meet) in Section 1.

The scheduler and the Dashboard use two separate fictional worlds. The scheduler's demo vault in `examples/scheduler-demo/` is one vault about an occlusion paper: two commitments, two cards and one judgment. The Dashboard demo in Section 4 shows six fictional agenda items from `08_exports/public_starter/demo-research-agenda.md`. Neither refers to the other.

### Walk through a session: today to close

`ros` is the scheduler's command-line client. Every `ros …` that the CLI prints stands for `python3 scripts/ros.py --root <folder> …`, and `--root` goes before the subcommand. Run these from the repository folder:

```bash
python3 scripts/ros.py --root examples/scheduler-demo today
python3 scripts/ros.py --root examples/scheduler-demo context commitment:occlusion-paper
python3 scripts/ros.py --root examples/scheduler-demo run judgment --target commitment:occlusion-paper --executor copy_packet
```

`today` opens a session and lists what needs a decision, `context` prints the commitment with the cards it rests on, and `run` writes a task packet for your own assistant. `run` ends by printing a run id of the form `ros-run-…` and the `collect` command for it. Normally you give the packet to your assistant and save its reply in a file. To try the loop without an assistant, use the sample answer that ships with the demo vault. The ids below are examples: `ros-run-aee8c1335137` stands for the run id your `run` printed, so type yours in its place:

```bash
python3 scripts/ros.py --root examples/scheduler-demo collect ros-run-aee8c1335137 --file examples/scheduler-demo/sample-answer.md
```

`collect` reads the answer back as a candidate and prints its id, of the form `c-…`, with the `admit` command. Again, `c-3f9a1d20` stands for the id your `collect` printed:

```bash
python3 scripts/ros.py --root examples/scheduler-demo admit c-3f9a1d20
python3 scripts/ros.py --root examples/scheduler-demo close
```

`admit` prints the change it would make to `06_active_context/research-portfolio.md` and writes nothing. `close` ends the session and lists the candidate as still undecided.

Two things in the output come from the date rather than from the demo vault. Run on today's date, the walk-through flags the demo vault's commitments as not recently verified, whereas `ros_demo.py` pins its date. On a fresh clone the first `today` may also report a source as "changed after verification", because the check compares the file's modification time, which the clone has just set, with the commitment's `last_verified` date. Without `--root`, `ros` reads this repository itself as the vault, and it has no commitments.

### When a source changes

When you update a card that a judgment rests on, for example because a study is retracted, a protocol is amended or an archive publishes a corrected catalogue, the next `today` lists that judgment under "To decide" with three options. Whether it still holds is your call; the system cannot tell. Where the output says `ros …`, type `python3 scripts/ros.py --root personal_vault …`.

- **A, it still holds.** Run the `ros admit --reconfirm <judgment id>` line it prints. This repository prints the change that pins the new versions; apply it as printed (or ask your assistant to), then confirm it in your own terminal with `ros admit --confirm <judgment id>` and answer `y`.
- **B, it must change.** Draft the replacement with a new id, register it with `ros propose judgment --file <draft> --target commitment:<id>`, and apply the change that `ros admit <candidate id>` prints. Then delete the old block and its id from the commitment's `judgments` line. `today` then lists two confirmations for your terminal: the new judgment (`ros admit --confirm <new id>`) and the old one's recheck (`ros answer <id> cancel --reason …`). Answer the old recheck with `cancel`; its `narrow` option only keeps the item open until the next version. The `judgments` line you edited is a judgment-class field and is confirmed on its own, because confirming the new block does not cover it: `admit` prints its `ros decide <id> confirm` with the real id when a session is open, and that session's next `today` and its `close` list it. `close` lists the candidate you applied and confirmed as needing nothing more. Once a session has closed, it does not close again: after you confirm what `close` listed, run `today` to open a new session, then `close` again.
- **C, decide later.** `ros decide <id> defer --until <date>` keeps the recheck waiting until that date.

A commitment field you change by hand works the same way. If you change `state`, `priority`, `question`, `responsibility` or `judgments` after `today` has read the commitment, the session's next `today` and its `close` list that write as a judgment-class field to confirm, and so does every `today` after it; confirm it in your own terminal with `ros decide <id> confirm` and answer `y`. A call relayed by an assistant is only recorded as asserted. Facts such as `last_verified`, `current_stage` or `next_step` need no confirmation.

Base a judgment on the cards it rests on, not on its commitment: the commitment's version includes its dates and next step, so a judgment based on it would come back each time you update them.

### What `ros` writes in this repository

Under the shipped `runtime_scope: public_starter`:

- Every `ros` command writes its packets, candidates and session records only under the git-ignored `06_active_context/work_state/` of the `--root`. No command writes a durable source.
- `run` accepts only `--executor copy_packet` and refuses every provider. Personal-vault mode (Section 5) does not change this.
- `admit <candidate>` and `admit --reconfirm` show the planned difference through copy fallback without asking first, so nothing is admitted into the durable sources.
- `admit --confirm` records an after-the-fact confirmation in the git-ignored local ledger only when you answer at your own terminal. Relayed by an agent, it is recorded as asserted and the confirmation request stays open. Either way it writes no source and is not an admission.
- `close` lists the candidates returned or proposed since the session started that are still undecided. Here they stay undecided, because `admit` neither admits nor records a refusal; one you applied by hand and whose judgment you confirmed is listed apart, as needing nothing more.

The admission and dispatch code ships but stays off. Only a `config/ros.json` that sets `runtime_scope: "private"` explicitly turns it on; a missing key, a misspelling or any other value runs as copy-only. `runtime_scope: "private"` is the setting of the prototype in the technical report, which runs with admission and dispatch on; it is not supported in this repository, and `ros attend`, for one, then stops with a message and writes nothing. A vault copied from the demo vault keeps its `config/ros.json`, so it runs copy-only as well.

All 13 subcommands exist in this repository. Most commands first run one boundary, recorded in the same git-ignored ledger; `receipt`, `propose rule`, `admit --rollback`, `collect --abandon` and `attend` do not. None writes a durable source:

| Command | In this repository |
| --- | --- |
| `today` | Copy only: lists changes and open requests and opens a session; Today lists the commitments in your attention schedule once the vault has one (`06_active_context/work_state/attention-schedule.md`), otherwise every commitment reads as unscheduled; commitments moved to a later day or parked are named on one `Not in Today` line |
| `close` | Same as the prototype in the report; the listed candidates stay undecided, except one you applied by hand and confirmed; the scope line is printed when something in it is not zero, or with `--all` |
| `propose judgment`, `episode-close`, `rule` | Same: registers a candidate |
| `admit` | Shows the planned change only: `<candidate>` and `--reconfirm` show the planned difference; `--confirm` records a confirmation without writing, and applies only when you answer at your own terminal; `--rollback` is refused, because this repository writes no source and rolls none back |
| `decide` | Same: records the decision; `cancel` and `confirm` apply only when you answer at your own terminal |
| `answer` | Same: records the answer; `satisfied` and `cancel` close the request, so they apply only when you answer at your own terminal; `satisfied` is offered only where a check's basis is the researcher's judgment, which none of the shipped rules declares |
| `state`, `context`, `rules`, `receipt` | Same; they only read |
| `run` | Copy only: `--executor copy_packet` only; every provider is refused |
| `collect` | Same, except that no run-state ledger is kept |
| `attend` | Prints the entry for your attention schedule (today, tomorrow, a date, park, step done) and where it goes; writes nothing. Paste it, or let the assistant paste it once you agree, and `today` lists it; start the file from the template whose full path it prints (`09_templates/attention-schedule.md` in this repository). When the entry replaces a block, the block it replaces is printed first, so you can keep it to undo; `undo` says how to revert by hand |

For an engineering check, run `python3 scripts/validate_headless.py`. It verifies the complete no-dashboard profile, which must pass with the `dashboard/` directory absent: routing, receipts, runtime and provider boundaries, task extensions, public safety, links and focused zero-dashboard behavior, without weakening authority checks. It is not a prerequisite for reading a source in your agent client. The CLI route prepares the same loop of goal, source, result and boundary without starting a server or Dashboard; the second command names the one file to read for a first run, the [first-run guide](../08_exports/public_starter/onboarding-step-by-step.md):

```bash
python3 scripts/start_researchos.py --mode cli
python3 scripts/plan_context.py first_run_onboarding --lang en
```

The commitment list is a declared-scope ledger of lead or support responsibility, commitment state, priority, freshness, owner and role, one next step and the authority source. A commitment is a project's one current next step or next judgment; it, not the whole project, is what gets scheduled, and it keeps one bounded state and one next safe action whichever client is used to view or continue it. To ask how many tasks you lead, run `python3 scripts/query_research_agenda.py --view lead-active`, or use `lead-all`, `support-active`, `support-all`, `waiting`, `queued`, `conditional`, `paused`, `review`, `unclassified` or `all` for an explicit slice. Missing or invalid responsibility fails closed to `unclassified`. A count is complete only while the coverage receipt is current and has no unresolved candidate; otherwise it describes registered items only. Time buckets order the list but do not define what is in it.

## 4. The optional Dashboard

The Dashboard is optional and frozen: it can be used as described here, but it is not under development. Start the demo from the repository root:

```bash
python3 scripts/start_researchos.py --mode dashboard --port 8880
```

![The public Dashboard: open an item, preview and cancel an attention date, preview the handoff. Nothing is saved or run.](figures/readme/dashboard-en.gif)

Then open `http://127.0.0.1:8880/`. It shows six fictional agenda items from `08_exports/public_starter/demo-research-agenda.md`, a different fictional world from the scheduler's demo vault in Section 3, and needs no real API key. In personal-vault mode (Section 5) it shows your papers, people, projects and talks; decisions, heuristics, working-style cards, direction summaries and meeting cards are not shown there, and you read them through your assistant. The demo is set on a fixed fictional date, 2026-08-11, shown in the page's status line, so its calendar and freshness read the same on any day you open it. Ordinary startup serves the shipped public-safe projection and does not rewrite tracked files; it rebuilds only when that projection is missing, and maintainers rebuild explicitly with `python3 scripts/build_public_starter_data.py --write` after changing demo sources. The launcher reuses a listener only when `/session-config` identifies the matching runtime, so a public demo is never mistaken for a personal vault, the prototype in the report or an unrelated process on the same port; startup stops and suggests another port instead. `--mode public-starter` only reports the public runtime status and starts no server. The remaining modes are:

```bash
python3 scripts/start_researchos.py --mode public-starter --check --provider codex
python3 scripts/start_researchos.py --mode cli
python3 scripts/start_researchos.py --mode gui --port 8880
python3 scripts/start_researchos.py --mode public-starter
```

The Dashboard is a persistent attention and control surface beside the agent client, not a second chat and not a prerequisite for the agent route. It has one Unified Desk with Now and Library semantic areas: Now allocates attention across commitments and holds the calendar, while Library connects sources and relations through one or a few commitment lenses. Work and Review are states of an exact item and open only in that item's drawer, never as a third screen. The [System Reference](system-reference.en.md#primary-route-and-supporting-surfaces) defines each surface and its route rules. You can try a first loop by judging one fictional commitment, or by opening the optional direct agent input with only a goal; the default composer asks for nothing more than a goal and an optional source, and the Dashboard exposes no model, reasoning-effort or output-type control. A first visit goes like this:

1. Select a task card in the Unified Desk and check its current evidence and next action.
2. Drag it to a calendar date to preview attention; cancel or reload to discard the preview.
3. Inspect linked resources in the right-hand rail, then preview and copy the agent handoff.
4. Execute only in your separate private assistant task.
5. Review the returned result, and propose any durable update through the normal researcher-confirmed workflow. Copying alone does not create an executed task or an accepted result.

The calendar uses days as its smallest unit and has no hourly grid. `+N` expands a day; a Plan card can be dragged, or moved with `Alt + Arrow`, to another day as an in-memory preview that is labeled unsaved and resets on refresh. Only a write-enabled private runtime persists the date through its reversible schedule owner. Review, deadline and lifecycle markers never move. `Complete step`, `End Work Session` and `Complete project` close different things: the current commitment, the execution session and the durable project lifecycle. A Work Session is one bounded execution session with your agent client, and ending it does not complete the project. Three further distinctions stay apart. Lifecycle says whether a project is submitted, under review, in rebuttal, under revision or complete. In progress, To advance, Not advancing and Closed say how the whole project is managed. Today, Tomorrow, Future and Parked say only when its next step should take attention again. A project under review stays available among the linked resources, and a real event or review date can return its next action to the desk.

This repository is copy-only. It never starts the local Codex or Claude Code CLI, probes no local provider, calls no remote API, writes no durable memory (the two kinds of file it may write are listed at the end of this section), executes no Inbox write-back task and accepts no arbitrary shell command. Submitting a task prepares a packet for a separate private assistant; the desk always produces a copyable execution brief. The controlled execution routes are personal-vault mode and the private runtime; the private runtime is the prototype's in the report and is not supported in this repository. The surfaces divide the work as follows:

| Surface | Owns | Does not own |
| --- | --- | --- |
| Agent client | Interpreting intent, deep reading, reasoning, editing files, creating artifacts, iterating with you and running validation | Confirming evidence, mutating durable memory on your behalf, maintaining Today projections |
| CLI | Deterministic route, query, receipt, validation and maintenance commands | Open-ended research judgment or a second authority |
| Canonical Markdown and Git | Durable facts, decisions, provenance and recovery coordinates | Generated or runtime-only state |
| Dashboard | A rebuildable projection: triage of near-term attention, resources and relations, scheduling by day, choosing an execution route, showing status and results | Product truth, required onboarding, open-ended discussion, model selection, deep reasoning, cross-file editing, or acceptance of durable change |

Background preparation runs only bounded work whose result can return in place. Open-ended discussion or a complex edit uses a complete copied task packet that you paste into a new agent task, and "Continue existing task" is enabled only for a verifiable binding. The Dashboard does not copy your chat; it shows bounded session state. Ordinary card selection stays in place, while a suggestion can start a Work Session directly. A separate private Codex runner suits deep reading, file changes, artifact creation, validation, background queues, item-by-item execution and isolated writes.

```text
Now: restore one bounded research focus
  -> Library: context on demand
  -> Now / your agent: continue the work
  -> bounded agent read when needed
  -> visible answer, artifact, or diff
  -> Review: inspect the result, candidate change, receipt, and handoff
  -> researcher decision
  -> validated writeback in a private vault
```

One loop makes three things explicit. The Work Session holds the current goal, on-demand sources, the current result, a collapsed process log, the working deck and the frozen prompt and template language; browser coordination state and recent-task summaries are not durable memory. The candidate handoff is a bounded task carrying source cards, evidence state, sensitivity, the proposed authority change, its impact scope and validation state. The Review boundary reminds you that task completion is not evidence confirmation and that a source path is not a write-back target. In a private vault the next steps are execution, evidence review, your decision, validated write-back and a resume packet; they stay controlled, and this repository does not pretend they are automatic.

Review is not only where proposed write-backs go. Its [full reception scope](system-reference.en.md#shared-governance-boundaries) also covers bounded unknowns, break-glass confirmation, results, validation failures, rollback and handoffs required before closure; durable, sensitive, public or destructive changes always pass through it. The public runtime never executes durable write-back.

The page language selector changes visible UI copy. A new Work Session freezes that language as its answer and task-packet language, and changing the UI language mid-task does not rewrite the task. The content language, set in `config/researchos.runtime.example.json`, controls generated records and prompts:

```json
"public_starter": {
  "content_language": "en",
  "available_content_languages": ["en", "zh-CN"],
  "alternate_language_files": "reference_only_do_not_read_by_agent"
}
```

Rebuild with `python3 scripts/build_public_starter_data.py --language en --write` or `--language zh-CN --write`. The selected language feeds `08_exports/public_starter/generated-public-starter-data.json` and `dashboard/data/researchos-dashboard.json`. Alternate-language files stay in the repository as reference, and agents do not read them during normal operation unless you ask for translation, comparison or bilingual maintenance.

```text
Browser dashboard
  -> local Python server on 127.0.0.1
  -> selected demo or personal-vault projection / provider status
  -> copyable task packet for a separate private assistant
```

The agent route and the Dashboard depend on the same Markdown and confirmation rules, and this repository keeps the copy-only boundary described above; it rejects every `/codex-runner` submission without starting a thread or command. Personal-vault and private runtimes may return a local answer or artifact to Review, and local Codex starts only after you submit a task. In the public demo every local endpoint that saves feedback, inbox entries or card groups, withdraws a confirmation or runs an update returns 403 `public_starter_writeback_blocked`; those run only in personal-vault mode. The public demo writes only two kinds of file: uploads into the Git-ignored session workspace, and the demo projection when you run the registered `build_public_starter_data` action (unchanged demo sources give the same bytes). The local HTTP endpoints serve the Dashboard and are not internet APIs; the [System Reference](system-reference.en.md#local-http-endpoints) lists them.

Local **Open** and **Reveal** use Finder on macOS, Explorer on Windows and `xdg-open` on Linux when available; without a desktop opener the server returns a clear failure and leaves the path for manual opening.

## 5. Your own material

Your own material lives in `personal_vault/`, a folder inside your clone. Git ignores it, so nothing in it is committed, and both `ros` and the Dashboard's personal-vault mode read it. Because `personal_vault/` is not in Git, back it up yourself (copy the folder, or keep it in your own private backup): a deleted judgment block or card cannot be restored from this repository. Still, never push a clone that contains real material to a public remote. If you want version control for the vault, keep a private copy of the repository instead, with no public remote, and remove `personal_vault/` from that copy's `.gitignore`. Everything below uses the same `personal_vault/` layout either way.

### Start your own

1. Copy the demo vault:

   ```bash
   python3 scripts/ros_demo.py --init personal_vault
   ```

   It copies the demo vault's commitments, cards and `config/ros.json`, leaves out the records a walk-through from Section 3 left in the demo vault, its sample answer and its fictional judgment, and prints these next steps. It also works when `personal_vault/` already exists, for example because you started the personal-vault Dashboard first, and keeps any file already there; it refuses when the folder already has a `06_active_context/research-portfolio.md`.

2. Edit the commitment list, `personal_vault/06_active_context/research-portfolio.md`. Replace the two fictional commitments with one of your own; your own judgments enter later as candidates, as in Section 3. A commitment needs a heading, an id, your responsibility and state, one question, one next step, the date you last checked it, and the card it rests on; the Dashboard also reads who is accountable, your role and the project's phase:

   ```markdown
   ### Thesis chapter 2

   - id: thesis-ch2
   - responsibility: lead
   - accountable_owner: You
   - role_summary: Author of the chapter
   - lifecycle_phase: writing
   - state: mainline
   - priority: P0
   - question: Does the baseline still hold on the new split?
   - next_step: Rerun the baseline on the new split
   - last_verified: 2026-10-29
   - stale_after_days: 14
   - source_path: 01_knowledge/projects/thesis-ch2.md
   ```

   `responsibility` is `lead` or `support`; `state` is one of `mainline`, `queued`, `conditional`, `waiting`, `paused` or `closed`; `last_verified` is a `YYYY-MM-DD` date and `source_path` is relative to `personal_vault/`. `lifecycle_phase` is one of `scoping`, `planned`, `experiment_preparation`, `production`, `gated_operation`, `writing`, `release_preparation`, `submitted`, `under_review`, `rebuttal`, `decision`, `revision`, `accepted`, `published`, `paused`, `completed`; `submitted`, `under_review` and `decision` also need an `activation_trigger`, the event that brings the item back. The ids and paths are yours to choose. A value `ros` cannot use is listed under "Commitment list problems" in the `today` output and in `ros rules --check`, instead of the commitment silently dropping out of the checks. `ros` does not read `lifecycle_phase` or `activation_trigger`, so a phase outside this list or a missing trigger is flagged only in the Dashboard's personal-vault projection.

3. Replace the two fictional cards under `personal_vault/01_knowledge/` with one card of your own at the path that `source_path` names. Start from a skeleton in `09_templates/basic/`, such as `project.md` or `paper.md`; each carries the frontmatter, an Agent Summary, the fact and view sections and an evidence boundary, with a short note on where the file goes and what each value means. [examples/starter-cards/en/](../examples/starter-cards/en/README.md) shows every kind of card filled in, one fictional story across a research identity page, a direction summary, project, paper, decision, heuristic, working-style, person and meeting cards, and explains the three layers in a card, maturity and sensitivity. `ros` shows a card under its frontmatter `title`, or else under its first `#` heading. The First Run already creates the research identity page, `00_identity/research-identity.md`, and one direction summary under `01_knowledge/capsules/`; add another direction summary the same way for each new direction. An assistant reads those first (`python3 scripts/plan_context.py <task> --vault personal_vault` lists them ahead of the task files). Use `sensitivity: internal` for most cards and `sensitive` for people and for records of what others said; `ros context` never packs a `private` card. The fuller templates in `09_templates/` (`project-template.md` and the others) add governance sections for later.

4. Run the scheduler on your vault:

   ```bash
   python3 scripts/ros.py --root personal_vault today
   ```

   A vault started with `--init personal_vault --lang zh-CN` has Chinese output set in its `config/ros.json`; to switch for one command, add `--lang en` or `--lang zh-CN`.

   Then give the vault a check:

   ```bash
   python3 scripts/build_public_starter_data.py --personal-vault
   ```

   It reads only and writes nothing. It checks the repository's `personal_vault/` and, under "Vault check", lists the problems hand-written vaults often have: links to files that do not exist, a wrong `sensitivity` label, an empty Agent Summary, a frontmatter line ending in a `#` comment (which is read as part of the value), a direction summary older than the cards it lists, an original named in a card's `source` that is not on this computer (a reminder only), and a commitment with two blocks in the attention schedule. With nothing to fix it says "no problems found". The commitment list itself is checked by `ros today` and `ros rules --check`. Run it again whenever you have edited cards by hand.

5. Optionally, open the Dashboard on the same folder:

   ```bash
   python3 scripts/start_researchos.py --mode personal-vault --port 8881
   ```

   Then open `http://127.0.0.1:8881/`. This mode reads `personal_vault/06_active_context/research-portfolio.md` and the frontmatter-bearing cards under `personal_vault/00_identity/` to `personal_vault/06_active_context/`, and it never shows the fictional demo data. The server reads the cards when it starts, so a new or edited card appears after you restart it. The first start creates only some of the layer folders (`00_identity/`, `01_knowledge/papers/` with its `own_papers/reading_notes/` and `source_files/` subfolders, `01_knowledge/projects/`, `04_people/collaborators/` and `06_active_context/`); create others such as `02_decisions/` or `05_workflows/` when you need them.

You do not need to disable the demo data to use a personal vault. The [first-run guide](../08_exports/public_starter/onboarding-step-by-step.md) walks through these steps with the output you should see at each one and what to do when it looks different; this section stays the reference for the fields.

### Growing the vault

A candidate card is an interpretation; writing it does not make it durable memory or public fact. Start with one source and one card that records its source boundary, evidence state and one missing fact, and add project history, talks, decision rationale and other sources only after reviewing that first result. [Card Maturity and Enhancement](reference/CARD_MATURITY_AND_ENHANCEMENT.md) explains the M/I/R/G labels and how to turn a card gap into a bounded Work task, once you need it.

When a kind of work recurs, add the card for it from `09_templates/basic/`. A working-style card, `personal_vault/03_cognition/style/<task>.md` from `style.md`, records how you do one kind of task, where `<task>` is `writing`, `review`, `proposal`, `figures-talks` or `mentoring`; the assistant reads the matching one first at the quick level. Each point gives the rule, why, how to apply it and its source; when you correct the assistant, it drafts the correction as one point and adds it only after you agree ([example](../examples/starter-cards/en/03_cognition/style/writing.md)). A boundary card, `personal_vault/00_identity/boundaries.md` from `boundaries.md`, says in your words what material is never given to an assistant, what is not said outside, your institution's or journal's rules on AI tools and who approves before something goes out; outward tasks read it first. For papers and proposals the evidence level also reads two indexes: outputs and use boundary (`outputs-index.md`, in `01_knowledge/papers/`) and author roles (`author-roles.md`, also in `01_knowledge/papers/`), to check that a claim may be made outside and that a stated contribution has a source. The same folder has skeletons for review comments, a grant, an academic message, feedback to a mentee and a mental model (`review.md`, `grant.md`, `message.md`, `feedback.md`, `mental-model.md`); each says in its note where it goes.

Inside `personal_vault/`, a short current state goes in `06_active_context/`, source-grounded summaries in `01_knowledge/`, decisions and tradeoffs in `02_decisions/`, people context in `04_people/` and reusable methods in `05_workflows/`. [Where to Put New Materials](reference/WHERE_TO_PUT_NEW_MATERIALS.md) has the full placement table. Raw material stays where it is, outside the repository: a card records the path, which is often enough, and raw files should not be copied merely so that the Dashboard can see them. Nothing from the vault becomes public without a separate review under the [Safe Export Policy](reference/SAFE_EXPORT_POLICY.md).

Cards are context objects, not a prerequisite. A supplied source becomes the first working card, and Library is searched only when the current evidence is insufficient. Each card carries a sensitivity label of public, internal, sensitive or private. The personal-vault projection is written to the git-ignored `dashboard/data/researchos-local.json` because it may contain private derived metadata; public demo and personal-vault modes never share a generated data file. In this mode the Dashboard and the local Codex write only inside `personal_vault/`; the public templates can be read but not changed, and this mode cannot be used to modify the repository's tracked demo files (the details of where each mode writes are in the System Reference, under [Three ways to run the code](system-reference.en.md#three-ways-to-run-the-code)). Personal-vault mode still does not turn task completion into evidence confirmation: a durable change needs a named target, an evidence check, your approval and validation after writeback.

Stop after one successful loop: a larger vault helps only when you can say which layer each new file belongs to and where its evidence boundary is. Useful long-term memory still needs your own papers, notes, projects, talks, decisions or relationship context with traceable boundaries, added only when it improves the judgment at hand.

### Turning off the demo case (maintainers)

This step is optional and only changes the public demo projection. `python3 scripts/build_public_starter_data.py --disable-cases` previews the projection without the fictional case; adding `--write` rewrites the tracked files `08_exports/public_starter/generated-public-starter-data.json` and `dashboard/data/researchos-dashboard.json`, so do not commit the result unless you mean to ship the demo without its case. `python3 scripts/build_public_starter_data.py --write` restores them. Disabling deletes no files; the examples stay as references for fields and placement.

### Local execution providers

Besides the agent route and the Dashboard, you can read the Markdown directly in an editor or on GitHub to understand the directories, cases and manuals. The Codex app suits AI-assisted reading and editing, and the Codex CLI executes small handoffs and records logs; ResearchOS has no remote API provider. ResearchOS does not include Codex, and the public Dashboard never starts it. To execute a copied packet in a separate private agent task, install OpenAI's Codex app or CLI following its current official instructions, and check it with `command -v codex` and `codex --version`. The macOS desktop app may bundle the CLI at `/Applications/Codex.app/Contents/Resources/codex`; if `codex --version` fails but that file exists, add it to `PATH` or set `alias codex="/Applications/Codex.app/Contents/Resources/codex"`. Never write login tokens, API keys or account details into the repository.

This repository registers two local providers, `codex` and `claude_code`, and both are `copy_only` here. `python3 scripts/runtime_profile_cli.py list --scope public_starter` shows the public copy-only profile and `show --profile codex --scope public_starter` shows how one reserved provider projects in this edition; neither needs credentials or network access. The public Dashboard defaults to:

```json
{
  "provider_mode": "copy_only",
  "allow_local_codex": false,
  "execution_scope": "none",
  "maintenance_scope": "registered_actions",
  "allow_real_api": false
}
```

In words: the local runner is disabled; registered maintenance actions only, such as rebuilding the demo data, can run, and no real API is called.

Do not turn the public Dashboard into an execution host. To use one of the two local CLI providers, first switch to personal-vault mode (the private runtime belongs to the prototype in the report and is not supported here), keep its configuration untracked, run the provider checks and enable it there; the CLI keeps its own login outside the repository. The checks are `python3 scripts/validate_runtime_config.py` and `python3 scripts/start_researchos.py --mode personal-vault --check --provider codex`, which reports whether that CLI is installed.

## 6. Safety and common mistakes

Do not expose the Dashboard to the public internet. Do not commit API keys, tokens, `.env` files or local runtime configuration, and do not add real sensitive people, unpublished manuscripts, real relationship notes, raw corpus payloads or personal runtime logs to this repository. Before a release, `python3 scripts/validate_public_safety.py` checks for these.

The public demo is about 19 MB of tracked files, roughly 100 MB with Git history, and does not copy a private vault. ResearchOS does not govern your disk space: in personal-vault and private runtimes the local Work Session intake accepts the research materials you select without a product-level file-type, size, count or age quota and is limited only by the local filesystem and runtime, while the public demo accepts uploads of up to 1 GiB per file. Neither deletes your materials because of a space threshold. It bounds only the debris it generates, as listed in the [low-redundancy runtime contract](system-reference.en.md#low-redundancy-runtime-contract); low free space or substantial session copies produce a non-blocking advisory.

The usual mistakes are scanning the whole repository before the task is clear, treating an agent answer as confirmed memory, treating the Dashboard's JSON data or browser state as the authoritative record, adding real material outside `personal_vault/` or pushing a clone that contains it to a public remote, writing secrets into Markdown or tracked configuration, deleting the fictional examples, and expecting an empty vault to understand a research domain. You are using the system correctly when the assistant names what it read and skipped, each source has a boundary, every interpretation begins as a candidate, and each durable change ends with either a validation result or a named missing-evidence item.
