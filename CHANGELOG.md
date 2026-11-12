# Changelog

All notable changes to ResearchOS Public Starter are documented in this file.

The format follows the spirit of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

The 1.x series is the first stage of ResearchOS: one researcher, local files, decisions at the terminal. Versions 1.0.1 to 1.0.3 revised the technical report and the documentation; as their entries say, the software behaviour was unchanged.

## [Unreleased]

Release candidate `v1.2.0-rc.1`. The rules for judgments and admission are unchanged; `ros` gains the attention schedule, and its output changes are listed below. See the [V1.2 release notes](docs/releases/v1.2.0.md).

### Added

- `plan_context.py <task> --vault personal_vault --mode quick|standard|evidence` reads the user's own cards level by level: the working-style card or research identity page at quick; the identity page, the task's workflow, the direction summary and its cards at standard; only originals named in evidence boundaries at evidence. Missing cards are named with their skeleton; each level says what is not read by default and when to go up.
- Twelve fictional example cards in `examples/starter-cards/en/` and `zh-CN/` telling one story, and blank skeletons in `09_templates/basic/` for them plus review comments, grant, academic message, mentee feedback and mental model.
- Working-style cards under `03_cognition/style/`, one per kind of task, whose points (rule, why, how to apply, source) grow from the user's corrections.
- A boundary card (`00_identity/boundaries.md`) read first by outward tasks, and two evidence-level indexes: outputs and use boundary, author roles.
- Nine research workflows in `05_workflows/research_work/`, including a retrospective, and three routes: `peer_review`, `meeting_follow_up`, `mentee_feedback`.
- A read-only vault check in the dry run of `build_public_starter_data.py --personal-vault`.
- `ros attend` prints the attention-schedule entry to paste, and `ros today` lists Today from `06_active_context/work_state/attention-schedule.md` when the vault has one; template in `09_templates/attention-schedule.md`.
- `plan_context.py --vault ... --pack <file>`: a paste-ready card pack for a browser chat, public and internal cards only.

### Changed

- The First Run writes paper, project and summary cards as `internal` and profile and collaborator cards as `sensitive`; it used to write every card as `private`, which `ros context` never packs.
- The First Run adds a step for the research identity page and one direction summary; `AGENTS.md` has a section for every session after the First Run.
- `ros_demo.py --init` adds `02_decisions` and `03_cognition` to the vault's `graph_roots`; a Chinese vault's fictional commitments are in Chinese.
- `query_research_agenda.py` reads `personal_vault/` by default when it exists and prints Chinese for a Chinese vault.
- The full card templates are the basic skeletons with later sections; card maturity is explained once, in the rubric, and the level examples use the cards' own fields.
- The manual says which cards the Dashboard shows in personal-vault mode and adds a section for browser-only readers.
- `ros context` asks in the vault's language before handing over a sensitive card and says why each excluded card was left out; the hint after a judgment block is removed points to your own backup, not Git; the counts in `today` and `close` are in plain words; after a judgment is replaced, `close` explains the remaining field confirmation and prints `ros decide <id> confirm` with the real id, and no longer lists a confirmed candidate as undecided; the recheck option formerly labelled "narrow" reads "keep this item open until the next version (deferred)".
- Dashboard: in personal-vault mode the fictional demo's card-creation panel is not drawn; the material pipeline plugin's default card sensitivity matches the First Run.
- The README gives about thirty minutes to an hour for the First Run.
- A judgment block written during a session counts in that session's scope, so `close` cannot report complete while it is unconfirmed; `close` shows its outcome in plain words with the outcome name in brackets; a public install switched to `runtime_scope: private` gets a clear message from `ros attend` instead of an import error; the attention hints print the template's full path.
- README and manual: section 2 in plain words (technical detail moved to the system reference), daily commands described as used, what writes cards stated precisely, limits in one paragraph, "vault"/"demo vault" in reader-facing text; README session GIFs regenerated from current output.
- `today` keeps a parked, later or waiting commitment under "To decide" when its basis changes; `today` and `close` list the same pending confirmations; a second `close` explains how to open a new session; `close` shows short ids, prints the scope line only when it matters or with the new `close --all`, and its header count matches the listed lines; old recheck options reworded and reordered; the sensitive-card prompt asks to show the card here; `research-portfolio.md` is the "commitment list" throughout.
- Chinese demo vault `examples/scheduler-demo-zh/`; plan_context output fully localized; the card pack includes the matching commitments and judgments and drops command-line steps; vault check output in the vault's language; manual plain-language pass; README animations regenerated.

## [1.1.0] - 2026-11-11

Tagged `v1.1.0`. This release adds no features. See the [V1.1 release notes](docs/releases/v1.1.0.md).

### What the first stage includes

- The six session commands `ros today`, `context`, `run`, `collect`, `admit` and `close`, with the two ways of running them: this repository shows the planned change for you to paste in and confirm at your terminal, and the prototype described in the report writes it after the researcher confirms at the terminal.
- Technical report V12, which describes this first stage.

### What the first stage does not include

- Supplementary Note 6 of the technical report lists the boundary item by item; the author is the only user so far, and no comparison with simpler practice or study of use has been run.

### Fixed

- `ros propose judgment --target` accepts only cards in the scanned graph; `candidates.jsonl` no longer loses the candidate written after a torn last line.
- Terminal-only answers and decisions print the `--reason` they need; an uploaded `*.tmp` file is no longer deleted at startup; damaged run-log lines no longer stop the server; the public Dashboard no longer lists `/data/`.
- A personal-vault note that is not UTF-8 is named instead of ending the build in a traceback; `start_researchos.py --mode personal-vault --check` reports a missing CLI.
- The first-run guide and `AGENTS.md` say when a hand-changed judgment-class field is listed for confirmation.
- First-run and daily-use friction: `--lang` works after the command; the first-run judgment template bases a judgment on cards only; deadline options no longer print a refused deferral; `today` shows what needs a decision first and hides bookkeeping lines with nothing to report (`--all` and `--json` keep everything); `admit` and `close` say what to do next; output terms follow the report (item, open, waiting on your answer, deferred); the manual gains "When a source changes".
- `ros context` no longer delivers a source without a sensitivity label as internal; a question asked on an obsolete basis no longer holds work once the question budget is spent; an ownership move inside an unchanged scope is attributed to the scope.

## [1.0.4] - 2026-11-07

Tagged `v1.0.4`. See the [V1.0.4 release notes](docs/releases/v1.0.4.md).

### Changed

- First run rewritten after a retest with a fictional psychology researcher new to terminals and AI assistants: the README says what is needed first and where the user's material goes, the First Run adds one judgment so that a source change brings it back, and the first-run guide adds a worked example in which a study in a meta-analysis is retracted.
- `ros_demo.py --init` adds `00_identity` and `04_people` to the vault's graph roots; `ros rules --check` drops the trailing colon when there are no problems.

## [1.0.3] - 2026-10-30

Documentation release, tagged `v1.0.3`; the software behaviour of `v1.0.2` is unchanged. See the [V1.0.3 release notes](docs/releases/v1.0.3.md).

### Changed

- Technical report V11 corrected after three independent checks: a full run of the worked session against the report, a paragraph-level comparison of the English and Chinese texts, and a check of the citations against their sources. Corrections include the statement on AI-scientist systems in Section 6, Table 4 and Figures 9 and 10.

## [1.0.2] - 2026-10-30

Documentation release, tagged `v1.0.2`; the software behaviour of `v1.0.1` is unchanged. See the [V1.0.2 release notes](docs/releases/v1.0.2.md).

### Changed

- Technical report V11: the claim is narrowed to what the prototype supports (when a source changes, the system follows the recorded dependency and hands the judgment back to the researcher). The report now has eight sections; bounded goals, composition, the two propositions and the four historical requests moved to the supplementary notes; terms changed to item, evidence, waiting on the researcher and deferred. Figures were rebuilt as `researchos-r11-*`.
- The report and the documentation now call the two versions the prototype and the downloadable version, or this repository.

## [1.0.1] - 2026-10-30

Documentation release, tagged `v1.0.1`; the software behaviour of `v1.0.0` is unchanged. See the [V1.0.1 release notes](docs/releases/v1.0.1.md).

### Changed

- README opens with what the project is, why it exists and how it works in four steps, and gives a one-sentence prompt for an agent; a how-to-cite section and a citation in `CITATION.cff` carry the Zenodo DOI.
- First-run fixes from a fresh-clone walk-through, in the onboarding guide, the user manual, `AGENTS.md` and the person template.
- Technical report restructured for readability, with no change to its claims. It now opens with the research scenario, the pain and why the design follows. The worked session moved to Section 2, followed by principles (3), definitions (4), architecture and gaps (5), and comparison and counter-case (6); Figures 2-9 and Tables 2-3 were renumbered. "Model" now means only an AI model, and the report's formal part is called the definitions. Captions were shortened, and literature and implementation detail moved to Supplementary Notes 1 and 2.
- Section 6.1 and Table 5 add a provenance system for LLM-maintained wikis as the nearest mechanism for carrying a retraction to dependent claims.

## [1.0.0] - 2026-10-29

First stable release, tagged `v1.0.0`; citation metadata carries version `1.0.0` and release date 2026-10-29.

### Included and Changed

- The copy-only edition of the reference implementation, with fictional data, the shared kernel, scripts, contracts and synthetic tests. Provider mode remains `copy_only`, and the shipped `config/ros.json` sets `runtime_scope: public_starter`, so `ros admit` only shows the planned difference through copy fallback and writes no source; the admission and dispatch code stays off unless `runtime_scope` is explicitly `"private"` (see [User Manual Section 3](docs/user-manual.en.md#3-the-session-scheduler-and-command-line-checks)). Attention scheduling, admission writeback, maintenance writes, completion records and the live diagnostic chain remain private-prototype capabilities.
- Agent/CLI entry and one Unified Desk with Now and Library semantic areas support reading public-safe sources, inspecting fictional projections, previewing attention dates and copying task packets. Public mode is credential-free and copy-only: it never starts local Codex or a remote provider. The separately configured personal-vault mode can start a locally installed Codex CLI; `ros` itself does not change with that mode. Copying does not accept a durable change.
- The repository includes the Claude Code CLI reference adapter and its `claude_code` provider registration for reading and tests only; `ros` in the public edition dispatches to no local CLI.
- Shared kernel behavior for completion, deferral, rule validation, maintenance-failure handling and dependency blocking is available for code inspection and temporary synthetic tests; it does not enable private write workflows publicly.
- A bilingual technical report, not peer reviewed, describes the private prototype around keeping, updating and holding research state. Sections 1–5 and Appendices A–B occupy 39 English PDF pages and 33 Chinese pages; Supplementary Notes 1–6, supplied outside the PDFs, hold the principle sources and examples, the session operations and implementation mappings, the process and component contracts, the research foundations in detail, the formal specification and the full list of implementation gaps.
- Existing plugin examples and lifecycle contracts can be inspected and used locally. The plugin system is frozen and not under feature development.
- Bilingual routing and governance documentation, source-available/non-commercial licensing boundaries, and privacy and release checks remain part of the package.
- Fixes from the pre-release review of the Dashboard: the server refuses an unknown or missing `--data-file` instead of switching to personal-vault mode; Open never hands a script to its default app (Reveal still works); stopping the server with a plain `kill` removes its temporary read copy; the Dashboard keeps working when the browser blocks site data; focus rings meet 3:1 contrast and focus stays on the date field after a preview; an empty calendar period says where the items are; Markdown preview shows presentational HTML as text; the handoff summary lists the session sources; and the read-only lifecycle shows no Save control. The user manual now lists every local endpoint and the two files the public demo may write.
- Fixes from the pre-release code review: `ros admit --confirm` relayed by an agent is recorded as asserted and leaves the confirmation request open, as `ros decide … confirm` already did; reads that start local work (model catalog, evolution plan, provider and runner status, source tree, source info) refuse requests that the browser marks as coming from another site; the public demo accepts writes only on a named list of routes, and uploads of up to 1 GiB per file; `ros attend` shows a copy fallback in the public starter and stops with a clear message in a private installation that does not ship the attention schedule owner; native Windows is documented as unsupported (run it inside WSL).
- Pre-release cleanup: the frozen remote API provider placeholders (OpenAI-compatible, Anthropic and DeepSeek adapters, the egress policy and its schemas) and the unused Codex entry-queue and legacy upload code are removed, so the two registered providers are the local `codex` and `claude_code`; file writes go through one atomic-write helper and HTML escaping through one function, with no unescaped fallback; redirect-only documents and the separate system overview are folded into the User Manual and System Reference, and the contribution, support and security policies live once at the repository root with their Chinese versions in `docs/reference/`.

### Validation Evidence

Public CI run `40890605519` at commit `f541cb6d161af29c8fe172ab264e214bd492ae45`, ubuntu-24.04 with CPython 3.10.22 and 3.13.17: `Ran 661 tests` / `OK (skipped=4)` on each, with all 39 JavaScript contract suites passing. Private-repository CI (repository not public), run `40883029378` at commit `4a9f696a6ebc0b042be0136a7c4e943991330519`, ubuntu-24.04 and CPython 3.11.17: the 107-file default Python regression set reported `Ran 1006 tests` / `OK (skipped=30)`, the 19-file JavaScript default set passed, and all 17 CI checks passed. Both runs are dated 29 October 2026. See the [V1.0 release notes](docs/releases/v1.0.0.md) for commands, inventory counts and artifact hashes. These receipts cover only their specified commits.

### Known Limitations

- Software checks do not establish scientific validity, human acceptance or public availability.
- This is a local reference implementation, not a hosted service or production multi-user system. Windows and Linux bridges lack the same native visual acceptance evidence as macOS. Native Windows Python is not supported; see the README for the WSL route.

## [0.1.1] - 2026-07-01

### Added

- Added GitHub-recognized community and project metadata: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `CITATION.cff`, issue templates, and a pull request template.
- Added this changelog to make release changes easier to review without reading raw git history.
- Added public-safe issue forms for bug reports, documentation feedback, and research-use feedback.

### Changed

- Updated README links so GitHub-facing project health files are easy to find from the repository root.

## [0.1.0] - 2026-07-01

### Added

- First fixed public-starter baseline for ResearchOS Public Starter.
- Bilingual README and reference entry points, with English as the default documentation language and Chinese through paired `.zh.md` files.
- Local dashboard workflow with demo data, asset overview, Today page, inbox, and handoff surfaces. This route is retained as the `0.1.0` historical baseline and is superseded by the Unified Desk in `1.0.0`.
- LLM-friendly first-run prompts for Codex, Claude Code, Gemini CLI, and similar local assistants.
- Bilingual handoff generation for English and Chinese UI users.
- Public/private boundary documentation for keeping private memory, unpublished work, raw corpus files, relationship notes, secrets, and local runtime state out of public release material.
- Source-available research license with explicit academic, personal, non-commercial, and commercial-use boundaries.

### Removed

- Removed in-repository user-study questionnaire files in favor of future external survey or feedback entry points.

### Known Limitations

- This is an independent V0 starter baseline, not a production system.
- The public starter uses fictional demo data and demo-only provider behavior by default.
- The public starter does not include private ResearchOS memory, unpublished manuscripts, raw local corpora, provider keys, personal runtime logs, or personal machine paths.
- A fuller technical report is planned for a later update.
