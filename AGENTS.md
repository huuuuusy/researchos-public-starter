<p align="right">
  <strong>English</strong> | <a href="docs/reference/AGENTS.zh.md">中文</a>
</p>

# AGENTS.md

This is the assistant entrypoint for ResearchOS Public Starter. Use it when helping a user operate this repository through Codex, Claude Code, Gemini CLI, or another LLM tool. ResearchOS is a small tool on the researcher's own computer that keeps their questions, evidence, judgments and next steps connected in plain files. This repository is its public version: its commands print changes for the user to paste in and never write them themselves, and everything it ships is fictional.

The default documentation language is English. Chinese is supported through paired `.zh.md` files and the Chinese assistant guide at `docs/reference/AGENTS.zh.md`.

## First Run

A new user usually arrives by pasting the setup prompt from the README into this client. They have not read any file, and they should not need to; many have never used a terminal, Python or an AI coding assistant, and their field may not be computing. Lead them through the eight steps below, one step at a time: say in a sentence what the step does, run its command or show what you will write, and tell them in plain words what happened. Never paste raw `ros` output; say in one or two sentences what it means for them, and explain a word such as commitment, candidate or judgment in one sentence the first time it comes up ("Words you will meet", Section 1 of the manual). When a step needs the user to type a command in their own terminal, give the whole line, starting with `cd` into this folder, and say why it has to be them. Use the user's language throughout. For Chinese, add `--lang zh-CN` to the two `ros_demo.py` commands in step 1; the vault they create then answers in Chinese, so the `ros.py` lines for the user's terminal need no flag. During the First Run, follow these steps instead of the reply shape in "Default Behavior" and the reading-level report in "Token Economy Defaults" below. Wherever the CLI prints `ros …`, it means `python3 scripts/ros.py --root <folder> …`.

Before step 2, tell them once where their material goes: cards stay on their computer in a git-ignored folder, but what you read and what they tell you is sent to your provider, and the `sensitivity` label limits only what `ros context` packs, not what you can open. Ask them not to give you raw participant or client data, case records that identify a person, recordings or transcripts, ethics documents or consent forms with personal information, manuscripts they are reviewing, or others' unpublished work; a card may say where such material is and what it is, never its content.

1. **Show what it is.** Run `python3 --version` (3.10 or newer; on a Mac with an older version, help them install Python from python.org; on Windows continue only inside WSL, because native Windows Python lacks the file locks). Then run `python3 scripts/ros_demo.py` (with `--lang zh-CN` for Chinese), which works on a temporary fictional copy and changes nothing. Say in three or four sentences what it showed: a source changed, ResearchOS flagged the judgment that rested on it, the researcher chose whether the judgment still holds, needs changing or waits (options A, B and C in the output), and nothing became durable memory without that decision. Phrases such as "no admission receipt yet" and "copy fallback" are expected in this repository, not errors. Then run `python3 scripts/ros_demo.py --init personal_vault` (with `--lang zh-CN` for Chinese), which starts the user's own vault in the git-ignored `personal_vault/`.
2. **Their profile.** Ask for their publication list in whatever form they have: a public homepage, Google Scholar, ORCID, a university or CNKI page, or a list they paste, plus a CV if they want to share one. Read only what they give and what is publicly reachable; Google Scholar often blocks automated reading, so if it does, ask them to paste the list, and never work around a login or block. Draft one card for them at `personal_vault/00_identity/profile.md` from `09_templates/basic/person.md`, with `relationship_type: self`: name, affiliation, research themes and a few representative works. From a CV take only the research record; leave out phone numbers, addresses, identifiers, referees and anything unrelated to research.
3. **Their papers and sources.** Ask them to pick three to five papers or other sources that matter most to their current work, such as an archive catalogue, a critical edition or a dataset's documentation, as links, DOIs or PDFs. For each, draft a card at `personal_vault/01_knowledge/papers/<short-name>.md` from `09_templates/basic/paper.md`, which also fits a questionnaire, catalogue, dataset or protocol: title, authors (or editors or issuing body), venue and year (or where it is held), the version they read, the main claim, what evidence it rests on and its public boundary (published, preprint or unpublished). Write only what the source says; mark anything you inferred as a candidate.
4. **Their collaborators.** From the authors of those papers, list the people who appear on two or more of them and ask which ones to keep, and whether someone they work with closely is missing, such as a supervisor or a partner at another institution. For each chosen person, draft a card at `personal_vault/04_people/collaborators/<short-name>.md` from `09_templates/basic/person.md`, with `relationship_type: candidate` and only what the papers show or the user states: the papers they share, or the relation in the user's own words. Do not infer advising, lab membership, seniority or friendship.
5. **One current project.** Ask for the project they most want to keep track of now: a short name, whether they lead it or support it, the open question, the next concrete step, which of the papers it builds on, and what they currently believe about it. Replace the two fictional commitments in the commitment list, `personal_vault/06_active_context/research-portfolio.md` (keep its frontmatter and the headings at the top) with one built from the answers: `id` (a short slug), `responsibility` (`lead` or `support`), `accountable_owner`, `role_summary`, `lifecycle_phase`, `state: mainline`, `priority: P0`, `question`, `next_step`, `last_verified` (today), `stale_after_days: 14` and `source_path: 01_knowledge/projects/<id>.md`. Choose `lifecycle_phase` yourself and tell them in a word: `scoping` while the question is still being shaped; `planned` for ethics approval or preregistration; `experiment_preparation` for recruiting and data collection; `production` once the data are collected and being analysed, or the work is being produced; `writing` for a paper or grant being written; `submitted`, `under_review` or `decision` once it is out, with an `activation_trigger` such as "reviews arrive" (Appendix A of `docs/user-manual.en.md` lists all values). Delete the two fictional cards, `personal_vault/01_knowledge/projects/occlusion-tracking.md` and `personal_vault/01_knowledge/papers/example-benchmark.md`, and draft the project card at `source_path` from `09_templates/basic/project.md`, with `title` and the `# ` heading set to the name and `related_papers` pointing to the paper cards it builds on.
6. **Two entry pages.** Draft the two pages an assistant reads first in every later session: `personal_vault/00_identity/research-identity.md` from `09_templates/basic/research-identity.md` (their research area, this project as the current mainline, and any working habit they state in their own words), and a direction summary at `personal_vault/01_knowledge/capsules/<id>.md` from `09_templates/basic/capsule.md` that lists the project, paper and collaborator cards and which to read for which task. Both pages get `sensitivity: internal`. Each card's `Agent Summary` must make sense on its own and say when to read the card; its "Evidence boundary" says where the originals are, which are not read by default. [examples/starter-cards/en/](examples/starter-cards/en/README.md) shows every card filled in.

   Before writing anything from steps 2–6, show the user one short list of every card and the commitment you are about to create, with a line on each. Write them after they agree, only inside `personal_vault/`, with `sensitivity: internal` for the paper, project and summary cards and `sensitivity: sensitive` for the profile and collaborator cards, unless they choose otherwise. `ros context` packs internal cards for you, holds back a sensitive one (the user can print it in their own terminal and copy you the part a task needs), and never packs a private one, so `private` is only for a card they never want handed to you.
7. **One judgment.** Turn what they currently believe into one judgment block, so that a later change to a paper card brings it back for review; without a judgment, `today` has nothing to flag. Write it to a draft file outside the repository, for example in the system's temporary folder, in this form, with the cards it rests on as its basis:

   ```text
   > [!judgment] j-<short-id>
   > Conclusion: <one sentence in the user's words>
   > Basis: 01_knowledge/papers/<short-name>.md
   ```

   Do not add `commitment:<id>` to the basis: the commitment's version includes its dates and next step, so the judgment would come back for recheck every time those are updated. Run `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target commitment:<id>` (its note that no session is open today is expected at this point), then `python3 scripts/ros.py --root personal_vault admit <candidate id>`. In this repository `admit` writes nothing; it prints the change it would make, with the basis versions filled in. Show the user the conclusion, and after they agree, apply that printed change to `research-portfolio.md` exactly as printed, then delete the draft.
8. **Check it.** Run `python3 scripts/ros.py --root personal_vault today`: their project, and only theirs, should appear under "To decide", with their new judgment marked as not yet confirmed; `[unscheduled]` is normal. Ask them to confirm it in their own terminal with `python3 scripts/ros.py --root personal_vault admit --confirm <judgment id>` and to answer `y`; if you run it, it is recorded only as relayed by an agent and the request stays open. The reply says the judgment was written into the file directly and is recorded as a confirmation after the fact, not an admission; tell them this is how this repository records every change pasted in by hand, not a mistake on their part. Fix any line under "Commitment list problems" (each names the field and the values it accepts), run `python3 scripts/ros.py --root personal_vault rules --check` until it reports `0 problems`. Then check the vault with `python3 scripts/build_public_starter_data.py --personal-vault`: it reads only and lists links to files that do not exist, wrong `sensitivity` labels, empty Agent Summaries, trailing `#` comments in frontmatter, direction summaries older than the cards they list, and originals not found on this computer; fix them until it reports no problems (a missing original is only a reminder). End with `python3 scripts/ros.py --root personal_vault close`.

Then explain the daily loop in four sentences: start by asking this client to run `today`; when a source changes, for example a study in their meta-analysis is retracted, a protocol is amended or an archive publishes a corrected catalogue, ask this client to update that card, and `today` brings back the judgment that rests on it; whether it still holds or must change is their call, and in either case this repository prints the change, you apply it after they agree, and they confirm in their terminal what `today` or `close` then lists; end with `close`. When that happens, follow Section 3, "The first source change", and Appendix B of `docs/user-manual.en.md`: they give the steps for keeping, replacing or deferring a judgment, and the confirmation a hand-changed `state`, `priority`, `question`, `responsibility` or `judgments` field needs. If they want to browse their cards, offer the optional Dashboard last: start `python3 scripts/start_researchos.py --mode personal-vault --port 8881` in the background, tell them that Library shows their profile, papers and collaborators and Now shows the project, and that it keeps running until it is stopped (Ctrl-C in its terminal, or ask you to stop it).

Keep the first run small: one profile, a few papers, the recurring collaborators, one project, its two entry pages and one judgment. More papers, people and projects can be added the same way later, a few at a time. Never add the user's material to tracked files, and never push it, or a clone that contains it, anywhere. If a step fails, the [first-run guide](08_exports/public_starter/onboarding-step-by-step.md) says what each step should print and what to do when it does not; read it only then. A user who would rather not set up a vault can start from one goal and one source in this client instead: the result is an answer, an artifact or a candidate, and nothing durable is written without their approval ("One loop in your agent client", Section 4 of the manual).

## Every Session After the First Run

When a request touches the user's projects, commitments or cards, open and close the session with `ros`; a quick rewrite or a code question needs neither. Start with `python3 scripts/ros.py --root personal_vault today`, adding `--for <commitment id>` when the session is about one commitment, and tell the user in a sentence or two what is waiting for their decision. When each item gets attention is their call, not yours.

Before the task, run `python3 scripts/plan_context.py <route> --vault personal_vault --mode quick` (the route ids are in the Route Table below) and read what it lists, in that order; it follows the vault's language, so no `--lang` is needed. Move to `--mode standard` only when you can name the gap the quick read left, and to `--mode evidence` only for a stated verification question. At quick it lists the task's working-style card, or the research identity page when there is none. For an outward task (an external request, an export check) quick reads the boundary card first. At standard the first pass holds at most five files: the research identity page, the working-style card, the direction summary, the task's workflow and any card the route names; the cards the direction summary names are listed separately and do not count toward the five, and packing the summary hands over only that page, so fetch the named cards the task needs one by one. At evidence the first pass holds at most eight: paper writing and proposals add the two index cards, the outputs index and author roles (listed only when they exist), with one instruction: open only the originals named in the "Evidence boundary" of those cards, and only for a stated check. Cards not written yet are named with their skeleton.

When the user decides when to work on a commitment, run `python3 scripts/ros.py --root personal_vault attend <id> today` (or `tomorrow`, `date <YYYY-MM-DD>`, `park`, `complete-step`). It writes nothing and prints the entry for `personal_vault/06_active_context/work_state/attention-schedule.md`; paste it after the user agrees (start the file from `09_templates/attention-schedule.md` if it is missing), and `today` then lists the commitment under Today. Which item gets attention, and when, is always the user's call.

Fetch a card with `python3 scripts/ros.py --root personal_vault context <card path>`, which applies its sensitivity label. When it reports a card excluded, tell the user the reason it prints for that card; a sensitive card, such as a person or meeting card, is held back because it records other people. Do not open the file directly instead. If the task really needs a sensitive card, the user runs `python3 scripts/ros.py --root personal_vault context <card path>` in their own terminal, answers `y`, and copies to you only the part the task needs.

Facts may be written directly: a card's body, status and evidence, and a commitment's `current_stage`, `last_verified` and `next_step`. Judgments may not: a judgment block, and a commitment's `question`, `judgments`, `responsibility`, `state` and `priority`. Draft at most three judgments in a session and submit each with `python3 scripts/ros.py --root personal_vault propose judgment --file <draft> --target <card or commitment:id>`; it becomes durable only after the user confirms it in their own terminal, as in steps 7 and 8 above and Section 3 of the manual, "The first source change". Working-style cards, heuristics and the research identity page describe how the user works: draft them, show the draft, and write only after the user agrees.

When the user corrects you on how something should be written, reviewed or presented, draft the correction as one point of their working-style card for that kind of task (`personal_vault/03_cognition/style/<task>.md`: the rule, why, how to apply it and its source, such as today's date and what was corrected), show it, and add it only after they agree; this is how the card grows. Before any outward task, such as a reply to an external request, a proposal, a talk, a review or an export, read `personal_vault/00_identity/boundaries.md` if it exists and keep to it; `plan_context` lists it first for those routes. For formal writing and proposals, the evidence level adds the outputs index (`01_knowledge/papers/outputs-index.md`) and the author-roles index (`01_knowledge/papers/author-roles.md`): check that every claim you use is allowed outside and that every contribution you state has a source. The author-roles index is sensitive, so it reaches you only as described above.

End with `python3 scripts/ros.py --root personal_vault close` (with the same `--for` if the session was opened with one), and tell the user in a sentence what it lists as still open.

## Core Idea

ResearchOS is a local-primary system for continuously maintaining research state. It connects questions, evidence, judgments, responsibilities and next steps so long-running research remains recoverable, understandable and actionable as context changes. Individual researchers can operate it with repository-aware agents through this bounded loop:

```text
Researcher intent + source -> bounded Agent/CLI read -> answer, artifact, or diff
  -> candidate only when durable memory may change
  -> researcher approval -> validation -> confirmed memory
```

The primary execution workflow is Markdown plus a file-aware agent or CLI. The deliberately narrow local dashboard has one Unified Desk with Now and Library semantic areas: **Now** owns every Today item, week/month scheduling, active or waiting project state, and exact item-local Work/Review drawers; **Library** connects public-safe sources, people, claims, evidence, threads, artifacts, and relations through one or a few explicit Commitment lenses, without owning calendar or project status. Work and Needs Review distinguish bounded sessions and candidate handling only inside an exact item. The dashboard is not a second chat, is not required before ordinary Agent work, and does not hold authority.

ResearchOS is material-grounded. Do not imply that prompts alone make an empty vault intelligent. Ask the user for the smallest relevant source bundle, then help them expand coverage over time with traceable evidence, explicit sensitivity, and confirmed interpretation.

## Code Writing

Prefer in-place edits in existing functions and modules. Extract a new function, class, or module only when the same logic already has at least three real uses, or when it enforces a security or permission invariant. Do not reserve abstractions, parameters, or configuration for possible future use. Do not add pass-through wrappers. Every new layer of indirection must explain the problem it prevents now.

## Default Behavior

Do not scan the whole repository first. When the user has not asked for the First Run and the request is unclear, do three things:

1. Identify the route.
2. State the privacy/evidence/export boundary.
3. Give one next action.

Use this short response shape:

```text
Route:
Boundary:
What I will read:
Next action:
```

Keep all durable updates as candidates until the user confirms them.

## Token Economy Defaults

Default to the smallest possible read. Many user requests can be answered by routing first, not by reading manuals.

1. L-1 no-read triage: decide whether the request needs repository context.
2. L0 route: use the already-loaded `AGENTS.md`; if it is unavailable, choose at most one route file.
3. L1 / quick: use frontmatter and `Agent Summary` before reading full files, then read one primary task file, capsule, or exact target. In the user's vault, quick reads the working-style card for the task under `personal_vault/03_cognition/style/`, or the research identity page when there is none; `python3 scripts/plan_context.py <route> --vault personal_vault` lists the user's cards for each level, in the vault's language.
4. L2 / standard: add only the specific workflow, template, case, or script that closes a named gap. In the user's vault, this lists the research identity page, the working-style card, one direction summary and the task's workflow, and separately the cards that summary names, which you fetch one by one with `ros context`; they do not count toward the first-pass file limit.
5. L3 / evidence: add exact evidence or checks only for a stated verification question, such as a release audit, a bug fix, or an explicit full check. In the user's vault, the paper-writing and proposal routes add the outputs index and author roles cards here (when they exist), with the instruction to open the originals named in those cards' "Evidence boundary", such as notes and logs outside the vault, for a stated check.

Do not read both English and Chinese files, generated dashboard JSON, full manuals, or all templates unless the user asks for that scope, such as bilingual work. Report the reading level and what you intentionally did not read.

Default to `quick` reading. Model choice and reasoning depth are separate: `Auto` follows the available runtime catalog, and task routing must not silently replace a model the user pinned or customized. Treat model tier and reasoning depth as task-dependent recommendations: simple setup can use `economy + low`, substantive analysis usually needs `standard + medium`, and only complex multi-source work should escalate further. Keep these settings folded unless they affect the task, and explain any material increase in expected token use.

The first-pass file and estimated-token limits of each tier are in the [Context Budget Protocol](docs/reference/CONTEXT_BUDGET_PROTOCOL.md#progressive-context-contract). If the user gives an exact source or target path, read it directly instead of replaying entry files. In a continuing task, reuse the prior context receipt and read only changed or newly required files. Before exceeding either limit, name the missing fact, judgment, workflow, or verification question and split the work into question-specific batches.

## Route Table

| User intent | Read first | Do next |
| --- | --- | --- |
| "Help me start" | The First Run section above, then `08_exports/public_starter/onboarding-step-by-step.md` if needed | Recommend one first route: the scheduler demo, one loop in the agent client, or the user's own `personal_vault/`. |
| "Show me how the scheduler works" | `docs/user-manual.en.md` (Section 3) | Run `python3 scripts/ros_demo.py`, then offer the command-by-command walk-through on `examples/scheduler-demo`. |
| "I do not know whether to use chat, dashboard, or my own material" | `docs/user-manual.en.md` (Sections 2, 4 and 6) | Match the user background to one route and give one next action. |
| "Use Chinese" | `docs/user-manual.zh.md` | Continue with `.zh.md` files when available. |
| "Show me the dashboard" | `docs/user-manual.en.md` (Section 6), `scripts/README.md` | Offer the dashboard commands. |
| "Use my own material" | `docs/user-manual.en.md` (Section 2), `docs/reference/WHERE_TO_PUT_NEW_MATERIALS.md` | Use `personal_vault/`: copy the demo vault if it does not exist, then add one commitment, one source and one candidate card; use `--mode personal-vault` to view local cards. Demo data does not need to be disabled. |
| "How many tasks am I currently leading?" | `06_active_context/research-portfolio.md` in a personal vault, or the fictional demo agenda in this starter | Run `python3 scripts/query_research_agenda.py`. Count only `responsibility: lead` plus `state: mainline`; report support, waiting, queued, conditional, paused, needs-attention, and unclassified items separately. Check the coverage receipt before calling a count complete. Never infer ownership from project count or recent activity, and never default missing/invalid responsibility to lead. |
| "Read this paper", "Help me write or revise", "Review this manuscript", "Plan a grant proposal" | The matching workflow in `05_workflows/research_work/`: `paper-reading.md`, `paper-writing.md`, `peer-review.md`, `grant-proposal.md` | Follow "Every Session After the First Run" with the route `material_understanding`, `paper_writing`, `peer_review` or `proposal`. |
| "Follow up this meeting", "Give feedback to my student", "Should I change topic?", "Prepare a talk or figure" | `meeting-follow-up.md`, `mentee-feedback.md`, `topic-change.md` or `talks-and-figures.md` in the same folder | The same, with `meeting_follow_up`, `mentee_feedback`, `idea_diagnosis`, or `presentation` and `figure_design`. |
| "Create a card" | `docs/reference/AGENT_PROTOCOL.md`, the matching skeleton in `09_templates/basic/` and its example in `examples/starter-cards/en/` | Separate source facts, the user's view, your additions and what is still to verify; write the `Agent Summary` so it stands alone, and set sensitivity as in the First Run. |
| "Respond to an external request" | `docs/reference/AGENT_PROTOCOL.md`, `05_workflows/research_management/external-demand-response-workflow.md` | Classify the request, find related assets, state the boundary, and draft only if safe. |
| "Check a relationship or opportunity" | `docs/reference/AGENT_PROTOCOL.md`, `05_workflows/research_management/relationship-opportunity-workflow.md` | List confirmed facts, candidate links, what cannot be inferred, and one next action. |
| "Process Review or handoff" | `docs/reference/AGENT_PROTOCOL.md`, relevant file in `06_active_context/` or `08_exports/public_starter/` | Summarize pending decisions before any writeback. |
| "Modify or debug code" | The code map in `docs/system-reference.en.md`, then one public entrypoint and one owner module | Reproduce first, change the owner, and run the matching eval. |
| "Add my own repeated task" | Task extensions in `docs/governance-guide.en.md`, then `config/extensions/method-comparison.example.json` | Prefer one declarative descriptor; do not add another Work Session, Inbox, or storage path. |
| "Install the example plugin" | Installing the bundled examples in `docs/governance-guide.en.md` | Run `python3 scripts/manage_plugins.py install method_comparison`, report its local/no-network/no-canonical-write boundary, and verify the generated task. Do not ask the user to copy a manifest. |
| "Check release readiness" | `docs/reference/PUBLIC_RELEASE_CHECKLIST.md`, `docs/reference/SAFE_EXPORT_POLICY.md` | Run validators and look for secrets, local paths, raw corpus, and private material. |

`README.md` is a human overview. Read it when the user asks for project positioning or documentation navigation; it is not required for every task.

## Code and Language Routing

For code changes, the code map in `docs/system-reference.en.md` is the routing authority. Do not start from generated JSON or recreate removed compatibility/demo routes. New behavior needs one documented owner, one public entrypoint, and one regression test.

In the Dashboard, the legacy `Start / Today / Agent`, `Assets`, `Next / Work`, and `Review / Inbox` route names are input aliases; item-bearing aliases open `Now?item=<id>&panel=<work|review>`, while missing identity fails closed.

The active demo/dashboard language is configured in `config/researchos.runtime.example.json` under `public_starter.content_language`. Valid values are `en` and `zh-CN`.

Treat that value as the frozen template language for the current generated build. Read `tasks` and `assistant_modes` only; do not load inactive-language prompt/template variants. A UI-language change does not change template language. Only a deliberate `--language en|zh-CN` rebuild may synchronize prompts and templates to another language.

## Safe Commands

Run these only when the user asks for a demo, setup, dashboard, or validation work:

```bash
python3 scripts/ros_demo.py
python3 scripts/ros.py --root examples/scheduler-demo today
python3 scripts/ros.py --root personal_vault today
python3 scripts/start_researchos.py --mode dashboard --port 8880
python3 scripts/start_researchos.py --mode personal-vault --port 8881
python3 scripts/plan_context.py --list --lang en
python3 scripts/query_research_agenda.py
python3 scripts/manage_plugins.py list
python3 scripts/start_researchos.py --mode public-starter --check --provider codex
python3 scripts/build_public_starter_data.py --personal-vault --write
```

`python3 scripts/build_public_starter_data.py --write` rebuilds the tracked demo projection and is a maintainer step after demo sources change. The optional switch that removes the fictional case from that projection is described once in Appendix E of the User Manual; it also rewrites tracked files, and a personal vault never needs it.

For validation, run the steps of `.github/workflows/validate.yml`, which is the CI for this repository.

This repository defaults to credential-free, copy-only handoff; ordinary onboarding must not need real API keys. Agent and Work Session produce copy-ready packets and never start the local Codex or Claude Code CLI or a remote API. Inbox/canonical write-back remains copy-only, and only registered maintenance action IDs may run. Controlled execution belongs to the prototype in the technical report or to personal-vault mode. Personal-vault is a Dashboard mode and does not change `scripts/ros.py`; what `ros` does under the shipped `runtime_scope: public_starter` is in [Appendix A of the User Manual](docs/user-manual.en.md#what-ros-writes-in-this-repository).

## Safety Rules

- Do not treat generated JSON or dashboard data as canonical authority. They are projections from Markdown and demo records.
- Do not commit secrets, provider tokens, raw corpus files, unpublished manuscripts, sensitive person notes, local machine paths, or runtime logs.
- Do not infer private relationships, advising or student status, lab membership, contribution hierarchy, or future commitments from weak evidence.
- Do not run Codex CLI handoff, provider/API calls, or write-producing commands without clear user intent.
- Keep state axes separate: `candidate` / `needs_evidence` is evidence state; `sensitivity` (`public` / `internal` / `sensitive` / `private`) decides what `ros context` packs; `public_boundary` (for example `local_only` / `public_safe` / `not_exportable`) decides whether something may be exported.

## First Prompt To Suggest

If the user is unsure what to do, suggest this (the same prompt as Section 2 of the User Manual):

```text
I do not know how to use ResearchOS Public Starter yet. Act as my guide. Read AGENTS.md only; if the environment already loaded it, do not reread it or scan the repository. Then explain in plain language: 1. what this project is for; 2. which path I should take now; 3. the next file or command; 4. what I should not put into a public repository. Do not write files yet; ask me at most two questions if needed.
```
