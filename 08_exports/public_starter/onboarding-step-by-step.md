---
type: onboarding_guide
title: "First Run: From the Demo to Your Own Vault"
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

# First Run: From the Demo to Your Own Vault

[English] | [Chinese](onboarding-step-by-step.zh.md)

## Agent Summary: What this guide does

This is the single first-run path. `python3 scripts/plan_context.py first_run_onboarding` points to it, and so do the README and the User Manual. It takes a new user from the fictional demo to a personal vault with one commitment and one card, in five steps: run the demo, walk through one session on the demo fixture, start your own vault in the git-ignored `personal_vault/`, optionally open it in the Dashboard, and check that the first run is done. Each step says what to do, what you should see and what to do if it looks different. The user can run every step in a terminal, or an assistant can propose each command and wait for confirmation. Real material goes only into `personal_vault/`, and nothing in this guide writes durable memory without the user's approval.

## Before you begin

You need Python 3.10 or newer and a terminal in the repository folder, on macOS or Linux; on Windows, use WSL. Nothing else has to be installed. Everything shipped in this repository is fictional.

The output uses a few words in a narrow sense, such as commitment, candidate and admission. Section 1 of the User Manual (`docs/user-manual.en.md`, "Words you will meet") explains each in one line.

The easiest way through this guide is to let an assistant such as Claude Code or Codex do it with you: paste the setup prompt at the top of the README, and it downloads the repository, asks about one of your projects and builds your vault from the answers, following the "First Run" section of `AGENTS.md`. This guide is the reference for that walk-through and for doing it by hand. An assistant following it should name the step it is on, propose one command or edit at a time, and write no file until the user confirms.

## Step 1: Run the demo

```bash
python3 scripts/ros_demo.py
```

**What you should see.** Six numbered steps, each starting with `━━`, then a short "What next" list. The demo works on a temporary copy of a fictional research graph and changes nothing in your clone. In step 3 a source changes and `today` flags the judgment that depends on it:

```text
━━ 3. A source changes (the benchmark protocol is revised); ros today flags the judgment that depends on it
…
    · [b5d4e33c7c] The basis of judgment "Compare A and B under occlusion first; do not enlarge the dataset yet." changed
```

In step 5 the reconfirmation is printed as a diff and not written, and in step 6 the recheck is still pending at close. Phrases such as "no admission receipt yet", "not an admission" and "copy fallback" are not errors: they say that nothing was admitted, which is how this repository works.

**If it looks different.** If `python3` is not found or the script stops with a syntax error, check that `python3 --version` reports 3.10 or newer. On Windows outside WSL it cannot run, because the file locks it needs are missing. For Chinese output, add `--lang zh-CN`. The counter lines, such as "scope / | … keys", are bookkeeping; the demo itself says you can skip them on a first read.

## Step 2: Walk through one session on the fixture

The demo ran by itself. Now run the same kind of session one command at a time on the fixture in `examples/scheduler-demo/`. Section 3 of the User Manual, "Walk through a session", lists the six commands in order (`today`, `context`, `run`, `collect`, `admit` and `close`) and says what each does. The first is:

```bash
python3 scripts/ros.py --root examples/scheduler-demo today
```

**What you should see.** `today` opens a session and lists the fixture's commitment under "To decide". `run` writes a task packet and prints a run id; `collect` reads the sample answer back and prints a candidate id; you type each id into the next command. `admit` prints a diff and says that nothing was written or admitted. `close` ends the session and lists the candidate as undecided:

```text
Candidates returned or proposed since this session started that are neither admitted nor declined (nothing written):
  · candidate c-2d0dd56c: commitment:occlusion-paper
```

**If it looks different.** Your ids differ from the manual's examples; use the ones your terminal printed. Run on today's date, `today` also says the commitments are "not verified for" some days, and on a fresh clone a source may read "changed after verification"; both come from the date, and Section 3 explains why. If `today` lists nothing, check that `--root examples/scheduler-demo` comes before the subcommand: without it, `ros` reads the repository's own graph, which has no commitments, and after the subcommand it is refused as an unrecognized argument. The records this walk-through leaves stay in the git-ignored `examples/scheduler-demo/06_active_context/work_state/`, and step 3 does not copy them.

## Step 3: Start your own vault

1. Copy the demo graph into the git-ignored vault folder:

   ```bash
   python3 scripts/ros_demo.py --init personal_vault
   ```

   You should see:

   ```text
   Started personal_vault/ from the fictional demo graph, without the demo's ros records, sample answer and judgment. Next:
   ```

   followed by the three next steps below. If it says `research-portfolio.md already exists; --init only starts a folder that has no portfolio yet`, you have started a vault before: edit that one, or move it aside to start again. It is fine if `personal_vault/` already exists without a portfolio, for example because you opened the personal-vault Dashboard first.

2. Open `personal_vault/06_active_context/research-portfolio.md`. Keep the frontmatter and the headings at the top, and replace the two fictional commitments, `### Occlusion Transfer Paper` and `### Workshop Talk` with their field lists, by one of your own. This is the smallest complete commitment; change the values to yours, with today's date as `last_verified`:

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

   Section 5 of the User Manual lists the values each field accepts.

3. Delete the two fictional cards, `personal_vault/01_knowledge/projects/occlusion-tracking.md` and `personal_vault/01_knowledge/papers/example-benchmark.md`, and create your own card at the `source_path` you wrote, starting from a template:

   ```bash
   cp 09_templates/project-template.md personal_vault/01_knowledge/projects/thesis-ch2.md
   ```

   Fill in `project_name` and replace the `# Project Name` heading with the same name; `ros` shows the card under that heading. Then record the source boundary, the evidence state and one missing fact. For a paper, start from `09_templates/paper-template.md` instead. If you would rather start from a short profile, ask the assistant to draft an intake note like the [material-intake note example](onboarding-intake-note-example.md) first.

   Around the project, a few more cards give the vault your own context: a profile card at `personal_vault/00_identity/profile.md` from `09_templates/person-template.md` with `relationship_type: self` (name, affiliation, themes, representative works, taken from your homepage, Google Scholar, ORCID or DBLP page or the research part of your CV), three to five paper cards under `personal_vault/01_knowledge/papers/` from `09_templates/paper-template.md`, and a card in the vault's people folder, under `collaborators/`, for each coauthor who appears on two or more of those papers, with `relationship_type: candidate` and only the papers you share. Point the project card's `related_papers` to the papers it builds on. This is the walk-through an assistant follows from the "First Run" section of `AGENTS.md`; keep their `sensitivity` set to private unless you decide otherwise.

4. Check the vault:

   ```bash
   python3 scripts/ros.py --root personal_vault today
   ```

   You should see your commitment, and only yours, under "To decide":

   ```text
   To decide (1: unscheduled, needing a next step, or due for review)
     ■ Thesis chapter 2  [unscheduled]
       (no requirements to review; carry on with the next step)
   ```

   `[unscheduled]` is normal, because this repository ships no attention schedule. End the session with `python3 scripts/ros.py --root personal_vault close`; for a fresh vault it reports `Outcome: complete (0 to do; …)`. If you changed `state`, `priority`, `question` or `responsibility` after `today` had already read them, for example to fix a portfolio problem, `today` and `close` list that write as a judgment-class field to confirm; confirm it in your own terminal with `python3 scripts/ros.py --root personal_vault decide <id> confirm` and answer `y` (a call relayed by an assistant is only recorded as asserted).

   If `today` shows a "Portfolio problems" block, each line names the field and the values it accepts, for example `state "active" is not a valid value (mainline, waiting, queued, conditional, closed, paused)`; fix it in the portfolio. If the fictional commitments still appear under "To decide", their blocks are still in the file. If they appear only under "Questions for you", marked `subject_absent`, you ran `today` before replacing them: these are records of the fictional run, so delete `personal_vault/06_active_context/work_state/` once and run `today` again. A card that is not at the path you wrote shows there as `source_path … does not exist in this folder`; `python3 scripts/ros.py --root personal_vault rules --check` reports the same problems and says `0 problems` when everything is in place.

Judgments you form later enter as candidates: ask the assistant to write them in the format that `ros close` prints, and register them with `ros propose judgment`.

## Step 4: Open the vault in the Dashboard (optional)

```bash
python3 scripts/start_researchos.py --mode personal-vault --port 8881
```

**What you should see.** The server prints a short banner and keeps running until you press Ctrl+C:

```text
ResearchOS personal vault dashboard
- mode: personal-vault
- vault: user-provided local Markdown
- dashboard: http://127.0.0.1:8881/
```

Open `http://127.0.0.1:8881/`. This mode reads only your vault and never shows the fictional demo data, so there is nothing to disable. Now shows your commitment and Library shows your cards. When you start work on an item, ResearchOS creates a bounded Work Session and routes it from Now into Work, the drawer of that item; a locally installed Codex CLI runs only after you submit the task, and only inside `personal_vault/`. Needs Review shows the returned result explicitly, with its evidence boundary, artifact paths, decision state and continuity handoff; nothing becomes durable memory until you confirm it.

**If it looks different.** The server reads the cards when it starts, so restart it after adding or editing a card. If the port is already in use, pass another number to `--port`. Section 5 of the User Manual lists the folders the first start creates. To reopen the fictional demo separately, run `python3 scripts/start_researchos.py --mode dashboard --port 8880`.

## Step 5: Check that the first run is done

The first run is done when:

- `python3 scripts/ros.py --root personal_vault today` lists one commitment of your own and none of the fictional ones;
- its card exists at `source_path` with a source boundary, and `ros rules --check` reports `0 problems`;
- `git status` shows no change caused by your material. `personal_vault/` is git-ignored, so it does not appear there at all.

### What stays out of a public clone

- Real material goes only into `personal_vault/`. Never push a clone that contains it to a public remote.
- Read only the files and public links the user supplied; do not bypass login, paywalls, robots restrictions or other access controls.
- Keep private, submitted, unpublished or unknown-boundary material `local_only`.
- Keep phone numbers, home addresses, identifiers, signatures and unrelated CV details out of cards.
- Treat coauthorship as a coauthor candidate only, not as supervision, friendship or future collaboration.
- Keep every generated interpretation a candidate until the user confirms it.
- Keep the first run to one profile, a few papers, the recurring coauthors and one project; leave bulk imports, plugins and deeper reading until one loop has worked.

## Only after the first run

Use these as optional references:

- [Card maturity rubric](onboarding-card-maturity-rubric.md);
- [Person card levels](onboarding-person-card-levels.md);
- [Paper card levels](onboarding-paper-card-levels.md);
- [Collaborator candidate example](onboarding-collaborator-card-levels.md);
- [Talk card example](onboarding-talk-card-levels.md);
- [Plan card example](onboarding-plan-card-levels.md);
- example plugin installation and system maintenance.

These are advanced references, not onboarding prerequisites.
