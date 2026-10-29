<p align="right">
  <strong>English</strong> | <a href="docs/reference/AGENTS.zh.md">中文</a>
</p>

# AGENTS.md

This is the assistant entrypoint for ResearchOS Public Starter. Use it when helping a user operate this repository through Codex, Claude Code, Gemini CLI, or another LLM tool. The repository is the public, copy-only edition of a small, file-based tool that keeps a researcher's questions, evidence, judgments and next steps connected; everything it ships is fictional.

The default documentation language is English. Chinese is supported through paired `.zh.md` files and the Chinese assistant guide at `docs/reference/AGENTS.zh.md`.

## First Run

A new user usually arrives by pasting the setup prompt from the README into this client. They have not read any file, and they should not need to. Lead them through the six steps below, one step at a time: say in a sentence what the step does, run its command or show what you will write, and tell them in plain words what happened. Use the user's language throughout and pass `--lang zh-CN` for Chinese. Wherever the CLI prints `ros …`, it means `python3 scripts/ros.py --root <folder> …`.

1. **Show what it is.** Run `python3 --version` (3.10 or newer; on Windows continue only inside WSL, because native Windows Python lacks the file locks). Then run `python3 scripts/ros_demo.py`, which works on a temporary fictional copy and changes nothing. Do not paste its output; say in three or four sentences what it showed: a source changed, ResearchOS flagged the judgment that rested on it, the researcher decided whether to keep, update or hold it open, and nothing became durable memory without that decision. Phrases such as "no admission receipt yet" and "copy fallback" are expected in this edition, not errors. Then run `python3 scripts/ros_demo.py --init personal_vault` (with `--lang zh-CN` for Chinese), which starts the user's own vault in the git-ignored `personal_vault/`.
2. **Their profile.** Ask for a public homepage, a Google Scholar, ORCID or DBLP link, and a CV if they want to share one. Read only what they give and what is publicly reachable; Google Scholar often blocks automated reading, so if it does, ask them to paste their publication list or give an ORCID or DBLP link instead, and never work around a login or block. Draft one card for them at `personal_vault/00_identity/profile.md` from `09_templates/person-template.md`, with `relationship_type: self`: name, affiliation, research themes and a few representative works. From a CV take only the research record; leave out phone numbers, addresses, identifiers, referees and anything unrelated to research.
3. **Their papers.** Ask them to pick three to five papers that matter most to their current work, as links, DOIs or PDFs. For each, draft a card at `personal_vault/01_knowledge/papers/<short-name>.md` from `09_templates/paper-template.md`: title, authors, venue and year, the main claim, what evidence it rests on and its public boundary (published, preprint or unpublished). Write only what the paper says; mark anything you inferred as a candidate.
4. **Their collaborators.** From the authors of those papers, list the people who appear on two or more of them and ask which ones to keep. For each chosen person, draft a card at `personal_vault/04_people/collaborators/<short-name>.md` from `09_templates/person-template.md`, with `relationship_type: candidate` and only what the papers show: the papers they share. Do not write advising, lab membership, seniority or friendship unless the user states it.
5. **One current project.** Ask for the project they most want to keep track of now: a short name, whether they lead it or support it, the open question, the next concrete step, and which of the papers it builds on. Replace the two fictional commitments in `personal_vault/06_active_context/research-portfolio.md` (keep its frontmatter and the headings at the top) with one built from the answers: `id` (a short slug), `responsibility` (`lead` or `support`), `accountable_owner`, `role_summary`, `lifecycle_phase` (for example `scoping`, `experiment_preparation`, `writing` or `revision`; `submitted`, `under_review` and `decision` also need an `activation_trigger`; Section 5 of `docs/user-manual.en.md` lists all values), `state: mainline`, `priority: P0`, `question`, `next_step`, `last_verified` (today), `stale_after_days: 14` and `source_path: 01_knowledge/projects/<id>.md`. Delete the two fictional cards, `personal_vault/01_knowledge/projects/occlusion-tracking.md` and `personal_vault/01_knowledge/papers/example-benchmark.md`, and draft the project card at `source_path` from `09_templates/project-template.md`, with `project_name` and the `# ` heading set to the name and `related_papers` pointing to the paper cards it builds on. What the user currently believes goes into the card as their current view; it becomes a judgment only later, through a candidate they approve.

   Before writing anything from steps 2–5, show the user one short list of every card and the commitment you are about to create, with a line on each. Write them after they agree, all with `sensitivity` set to private unless they say a card may be public, and only inside `personal_vault/`.
6. **Check it and show the daily loop.** Run `python3 scripts/ros.py --root personal_vault today`: their project, and only theirs, should appear under "To decide", and `[unscheduled]` is normal. Fix any line under "Portfolio problems" (each names the field and the values it accepts), run `python3 scripts/ros.py --root personal_vault rules --check` until it reports `0 problems`, and end with `python3 scripts/ros.py --root personal_vault close`. Offer to open `python3 scripts/start_researchos.py --mode personal-vault --port 8881`, where Library shows their profile, papers and collaborators and Now shows the project. Then explain the daily loop in three sentences: start by asking this client to run `today`; work as usual, and when a source changes, update its card so that `today` flags what depends on it; end with `close`, and confirm only what should be kept.

Keep the first run small: one profile, a few papers, the recurring collaborators and one project. More papers, people and projects can be added the same way later, a few at a time. Never add the user's material to tracked files, and never push it, or a clone that contains it, anywhere. If a step fails, the [first-run guide](08_exports/public_starter/onboarding-step-by-step.md) says what each step should print and what to do when it does not; read it only then. When the user asks what a word in the output means, use the one-line explanations in "Words you will meet" (Section 1 of the manual). A user who would rather not set up a vault can start from one goal and one source in this client instead: the result is an answer, an artifact or a candidate, and nothing durable is written without their approval (Section 2 of the manual).

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

Do not scan the whole repository first. For a new user, do three things:

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
3. L1 / quick: use frontmatter and `Agent Summary` before reading full files, then read one primary task file, capsule, or exact target.
4. L2 / standard: add only the specific workflow, template, case, or script that closes a named gap.
5. L3 / evidence: add exact evidence or checks only for a stated verification question, such as a release audit, a bug fix, or an explicit full check.

Do not read both English and Chinese files, generated dashboard JSON, full manuals, or all templates unless the user asks for that scope, such as bilingual work. Report the reading level and what you intentionally did not read.

Default to `quick` reading. Model choice and reasoning depth are separate: `Auto` follows the available runtime catalog, and task routing must not silently replace a model the user pinned or customized. Treat model tier and reasoning depth as task-dependent recommendations: simple setup can use `economy + low`, substantive analysis usually needs `standard + medium`, and only complex multi-source work should escalate further. Keep these settings folded unless they affect the task, and explain any material increase in expected token use.

The first-pass file and estimated-token limits of each tier are in the [Context Budget Protocol](docs/reference/CONTEXT_BUDGET_PROTOCOL.md#progressive-context-contract). If the user gives an exact source or target path, read it directly instead of replaying entry files. In a continuing task, reuse the prior context receipt and read only changed or newly required files. Before exceeding either limit, name the missing fact, judgment, workflow, or verification question and split the work into question-specific batches.

## Route Table

| User intent | Read first | Do next |
| --- | --- | --- |
| "Help me start" | The First Run section above, then `08_exports/public_starter/onboarding-step-by-step.md` if needed | Recommend one first route: the scheduler demo, one loop in the agent client, or the user's own `personal_vault/`. |
| "Show me how the scheduler works" | `docs/user-manual.en.md` (Section 3) | Run `python3 scripts/ros_demo.py`, then offer the command-by-command walk-through on `examples/scheduler-demo`. |
| "I do not know whether to use chat, dashboard, or my own material" | `docs/user-manual.en.md` (Sections 2, 4 and 5) | Match the user background to one route and give one next action. |
| "Use Chinese" | `docs/user-manual.zh.md` | Continue with `.zh.md` files when available. |
| "Show me the dashboard" | `docs/user-manual.en.md` (Section 4), `scripts/README.md` | Offer the dashboard commands. |
| "Use my own material" | `docs/user-manual.en.md` (Section 5), `docs/reference/WHERE_TO_PUT_NEW_MATERIALS.md` | Use `personal_vault/`: copy the scheduler fixture if it does not exist, then add one commitment, one source and one candidate card; use `--mode personal-vault` to view local cards. Demo data does not need to be disabled. |
| "How many tasks am I currently leading?" | `06_active_context/research-portfolio.md` in a personal vault, or the fictional demo agenda in this starter | Run `python3 scripts/query_research_agenda.py`. Count only `responsibility: lead` plus `state: mainline`; report support, waiting, queued, conditional, paused, needs-attention, and unclassified items separately. Check the coverage receipt before calling a count complete. Never infer ownership from project count or recent activity, and never default missing/invalid responsibility to lead. |
| "Create a card" | `docs/reference/AGENT_PROTOCOL.md`, relevant template in `09_templates/` | Separate source facts, candidate judgment, and missing evidence. |
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

`python3 scripts/build_public_starter_data.py --write` rebuilds the tracked demo projection and is a maintainer step after demo sources change. The optional switch that removes the fictional case from that projection is described once in Section 5 of the User Manual; it also rewrites tracked files, and a personal vault never needs it.

For validation, run the steps of `.github/workflows/validate.yml`, which is the CI for this repository.

The public starter defaults to credential-free, copy-only handoff; ordinary onboarding must not need real API keys. Agent and Work Session produce copy-ready packets and never start the local Codex or Claude Code CLI or a remote API. Inbox/canonical write-back remains copy-only, and only registered maintenance action IDs may run. Controlled execution belongs to private or personal-vault runtime. Personal-vault is a Dashboard mode and does not change `scripts/ros.py`; what `ros` does under the shipped `runtime_scope: public_starter` is in [Section 3 of the User Manual](docs/user-manual.en.md#3-the-session-scheduler-and-command-line-checks).

## Safety Rules

- Do not treat generated JSON or dashboard data as canonical authority. They are projections from Markdown and demo records.
- Do not commit secrets, provider tokens, raw corpus files, unpublished manuscripts, sensitive person notes, local machine paths, or runtime logs.
- Do not infer private relationships, advising or student status, lab membership, contribution hierarchy, or future commitments from weak evidence.
- Do not run Codex CLI handoff, provider/API calls, or write-producing commands without clear user intent.
- Keep state axes separate: use `candidate` / `needs_evidence` for evidence state, and `local_only` / `public_safe` / `not_exportable` for sensitivity or export boundaries.

## First Prompt To Suggest

If the user is unsure what to do, suggest this (the same prompt as Section 2 of the User Manual):

```text
I do not know how to use ResearchOS Public Starter yet. Act as my first-run guide. Read AGENTS.md only; if the environment already loaded it, do not reread it or scan the repository. Then explain in plain language: 1. what this project is for; 2. which path I should take now; 3. the next file or command; 4. what I should not put into a public repository. Do not write files yet; ask me at most two questions if needed.
```
