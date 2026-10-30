<p align="right">
  <strong>English</strong> | <a href="governance-guide.zh.md">中文</a>
</p>

# ResearchOS Governance and Extension Guide

This guide covers what may enter this repository, how to adapt and extend it without weakening its authority boundary, how the bundled plugins are installed and removed, and how releases, contributions, security reports and the license are handled. The short GitHub-facing files `CONTRIBUTING.md`, `SECURITY.md` and `SUPPORT.md` are at the repository root, and their Chinese versions are in `docs/reference/`; this guide keeps the fuller principles. How to use the system is in the [User Manual](user-manual.en.md), and the kernel contracts and code owners are in the [System Reference](system-reference.en.md).

## The public boundary

This repository is a separate git project that demonstrates structure, mechanisms, demo data, Dashboard files, script entrypoints and public-safe documents. It is not a copy of any non-public working system and must not copy content from a non-public Dashboard projection. Materials enter the system first, agents or scripts may produce candidates, humans confirm what becomes reusable state, and release requires safe-export checks. The starter explains that model instead of presenting itself as an autonomous scientist or an automatic memory system.

| Layer | Allowed | Not allowed |
| --- | --- | --- |
| `source material` | public-safe summaries, citation leads, public link notes | raw corpus, confidential material, unauthorized full text |
| `candidate` | unconfirmed summary, next action, demo inbox item | agent output written as confirmed fact |
| `confirmation` | human acceptance, rejection, evidence request | unsourced automatic decisions |
| `validation` | validator output, release check, boundary note | non-reproducible verbal assurance |
| `export` | public-safe cases, templates, generated starter data | sensitive real people, secrets, local paths, runtime logs |

The repository may therefore contain public-safe frontend and local server files, fictional guided-onboarding materials and card-maturity examples, a copy-only handoff configuration with no local or remote executor, paired English and Chinese core documents, public-safe templates, validators, the provider registry and startup scripts, and the short GitHub support files. It must not contain non-public working content or Dashboard projections, raw corpus, runtime logs, API keys, tokens or credentials, real people, students, collaborators, reviewers or unpublished paper details, local absolute paths or personal account information, or unreviewed agent output presented as fact.

What this repository may run and write, including the separately configured personal-vault mode and the copy-only `ros` boundary, is set out in Sections [3](user-manual.en.md#3-the-session-scheduler-and-command-line-checks) and [4](user-manual.en.md#4-the-optional-dashboard) of the User Manual. This repository's entrypoints are a subset of those of the prototype in the technical report, or demo and self-hosting stand-ins for capabilities the prototype has: the personal-vault mode, the fictional `ros_demo.py` walkthrough, research-agenda queries and the maintenance facade. Any other startup mode, provider configuration, Dashboard file, runner facade, case switch or documentation entrypoint here should also exist in the prototype. This parity rule does not make this repository a data copy; it keeps the two maintainable together, with this repository demonstrating structure and mechanisms and the prototype remaining the authority for real state.

## Customizing the starter

The starter is meant to be adapted, and the safe way to adapt it is to keep the authority boundary fixed while changing content, templates, workflows, providers or Dashboard surfaces around it. Markdown source plus human confirmation is authority; Dashboard JSON, provider responses, Codex output and generated files are projections or candidates until reviewed. Start with content, templates and workflows before changing the Dashboard: a new Dashboard button should be the last step, not the first proof that an idea matters.

| Layer | Good first change | Start here | Validation |
| --- | --- | --- | --- |
| Personal content | Replace fictional demo cards with your own public-safe cards. | `00_identity/` through `06_active_context/`, `docs/reference/WHERE_TO_PUT_NEW_MATERIALS.md` | `python3 scripts/build_public_starter_data.py --personal-vault --write` |
| Card format | Add fields to a paper, person, project, talk or decision card. | `09_templates/project-template.md`, `09_templates/paper-template.md` | Link check and one manual Dashboard review |
| Prompts | Adapt task prompts for your own assistant or model provider. | `09_templates/standard-agent-prompts.en.md` | Check that prompts still ask for boundary, evidence, candidate status and confirmation |
| Workflow | Add a task route for a repeated research operation. | `05_workflows/research_management/`, `09_templates/workflow-template.md` | Add a bilingual link and run link checks |
| Task extension | Add a repeated route without editing Dashboard orchestration. | `config/extensions/method-comparison.example.json` | `python3 scripts/validate_task_extensions.py` and `python3 scripts/plan_context.py <id> --lang en` |
| Provider | Connect a local model or provider adapter. | `config/researchos.runtime.example.json`, `scripts/researchos_adapters/provider_registry.py` | `python3 scripts/validate_runtime_config.py` |
| Dashboard | Add a filter, card box or workbench surface. | `dashboard/src/`, `scripts/build_public_starter_data.py`, the [code map](system-reference.en.md#code-map) | `python3 scripts/validate_agent_architecture.py` plus a browser smoke test |

Before adding a folder, template, script, Dashboard area, provider or export target, answer nine questions. What judgment or action does it support? Where is the raw source, and what is the authority boundary? Is the default sensitivity `public`, `internal`, `local_only` or `not_exportable`? What is the candidate flow before human confirmation? Where does confirmed Markdown live? Which existing objects can it relate to? What command, test or manual review catches drift? Can it appear in public output, or only in a private or local vault? Can it use the declarative task port instead of new frontend or storage code? If the answers are unclear, keep the change as ordinary material intake.

Some boundaries must not be customized away. Generated Dashboard JSON never becomes canonical memory. API keys, provider tokens, raw private corpus, submitted manuscripts and local machine paths stay out of tracked files. Private or boundary-unclear material does not become public-facing text. A new material class does not get its own top-level directory, and no Dashboard surface is added before there is a template, a candidate flow and a validation rule. Provider execution is never authority for memory writeback.

### Extension ladder

Use this ladder for a new repeated class such as email threads, review assignments, compute quotas, budgets, dataset access or external surveyed papers. Read `05_workflows/research_management/asset-type-extension-workflow.md` and `09_templates/data_contracts/researchos-extension-contract-v1.md` before moving beyond C1. These levels are not the change classes of the [System Reference](system-reference.en.md#evolving-the-architecture).

| Level | Meaning | User-visible result |
| --- | --- | --- |
| C0 | Repeated need noticed. | A note describing the need and boundary. |
| C1 | Two or three pilot cards exist. | Manual cards with stable fields. |
| C2 | Template and workflow exist. | A reusable card template and intake route. |
| C3 | Builder or Dashboard can read it. | It appears in Library, Work or Review without inventing state. |
| C4 | It deserves its own surface. | A dedicated Dashboard box or tab. |

To have an agent propose an extension before anything is written, use:

```text
I want to extend ResearchOS with a new repeated category: [category].

Read AGENTS.md, docs/governance-guide.en.md, 05_workflows/research_management/asset-type-extension-workflow.md, and 09_templates/data_contracts/researchos-extension-contract-v1.md. Do not edit files yet.

Return:
1. whether this is ordinary material intake or a real extension;
2. proposed asset_class and sensitivity default;
3. source authority and export boundary;
4. two pilot-card fields;
5. whether it needs an answer, artifact, write-back/Review flow, template, workflow, dashboard filter, or dedicated surface;
6. validation commands;
7. stop rules and open questions.
```

Write files only after you confirm the extension route.

## Task extensions and plugins

Plugins are optional and outside the first-use path, and there is no home-page marketplace. Without installing anything, Now, Library, item-local Work and Review, and agent tasks keep working. The plugin system is frozen: the bundled examples and the local, reversible lifecycle can be inspected and used, but they are not under feature development. An extension should carry a recurring, independently bounded capability contribution, and it can be disabled at any time; it cannot introduce another set of pages, states or source authority, and it never confirms facts for the user. A concrete task is only an entrypoint, workflow adapter or evaluation probe for that contribution, and a model or skill is an execution choice. A successful installation or task does not establish a general capability: capability claims need evidence from relevant episodes, failure cases and changed contexts. Start with the core and add an extension only for a recurring need. The [product layers](system-reference.en.md#product-layers) explain which manifests are optional extensions and which belong to the Dashboard foundation.

Use the declarative task port when the new behavior can reuse the existing Work Session, result modes, Review and storage boundaries. One descriptor under `config/extensions/` is consumed by both the Dashboard builder and `scripts/plan_context.py`; personal-only descriptors live in the git-ignored `config/extensions.local/`. The port is limited to task metadata, read tiers, result modes, workspace routing, sensitivity, authority and bilingual copy, and it cannot execute arbitrary code or create a new persistence path. Its versioned fields and compatibility rules are listed under [extension ports](system-reference.en.md#extension-ports). To design a task, start from `config/extensions/method-comparison.example.json`, put your version in `config/extensions.local/<id>.json`, update the bilingual copy, authority and read fields, and validate before enabling it; a reviewed distributable descriptor may live under `config/extensions/`.

```bash
python3 scripts/validate_task_extensions.py
python3 scripts/plan_context.py --list --lang en
python3 scripts/build_public_starter_data.py --write
```

If an ordinary task still requires edits to `dashboard/app.js`, Work Session state, Inbox stores or storage contracts, stop and reclassify it before coding.

### Installing the bundled examples

The easiest route is to ask your agent: "Install the ResearchOS method_comparison example plugin." The agent runs the repository lifecycle command, reports the permission boundary and verifies that the task appears; you do not copy a manifest or learn its folders. The deterministic command is

```bash
python3 scripts/manage_plugins.py install method_comparison
```

It prints its status line in Chinese even with `--language en`; the line names the plugin, `method_comparison`, and says that it is enabled. The task then joins the existing agent and Work Session task catalog, without creating a second chat, Dashboard page, Inbox or memory store.

The bundled `cross_domain_scientific_entry` plugin, installed the same way with `python3 scripts/manage_plugins.py install cross_domain_scientific_entry`, turns entry into an unfamiliar field into a bounded Case Pack: a Case Charter, a minimum domain map, an approach registry, a candidate ledger, an admission receipt, a retention and transfer report and a case settlement. It supplies the workflow and authority boundary, not domain expertise or private research memory, and its practical value depends on your sources, judgment, model capability, domain feedback and execution discipline. A personal vault may combine the same kernel with your local materials at runtime; those materials are never copied into the plugin.

To continue a local Codex task in ChatGPT or another MCP client, `python3 scripts/manage_plugins.py install codex_thread_handoff` installs a declarative ResearchOS task contract only. It does not expose the machine, create a tunnel, install a bridge or register a ChatGPT connector; a separately operated, authenticated, read-only MCP connector is still required. Call the integration ready only after each of the four readiness states in [its README](plugins/codex-thread-handoff/README.md#availability-and-parity) has been checked.

The manager accepts only bundled, reviewed `local_installable` `*.example.json` descriptors. It copies the public-safe variant into the git-ignored `config/extensions.local/` and re-validates the plugin host with `scripts/validate_plugins.py`; it does not rebuild the Dashboard data (run `python3 scripts/build_public_starter_data.py --write` for that). It does not manage the embedded foundation or bundled capabilities, use the network, accept a URL, download or execute remote code, or write canonical Markdown. Long-term changes still go through the exact item's Review and human confirmation. If you edit an installed manifest yourself, the manager refuses to overwrite or delete it.

```bash
python3 scripts/manage_plugins.py disable method_comparison
python3 scripts/manage_plugins.py enable method_comparison
python3 scripts/manage_plugins.py uninstall method_comparison
python3 scripts/manage_plugins.py list
```

The same commands apply to `cross_domain_scientific_entry`. `disable` keeps the local descriptor but removes its runtime contribution, and `uninstall` removes the unchanged descriptor and re-validates the plugin host. After uninstalling, `python3 scripts/validate_plugins.py` and `python3 scripts/validate_public_safety.py` confirm the clean baseline; the example stays available for later installation, and no local manifest is tracked by Git.

### Extending Dashboard results and Review

The Dashboard exposes three result modes through `dashboard/src/services/work-session-router.js`: `answer`, `artifact` and `writeback`. The Work Session accepts the goal and source hints, the working deck accepts optional cards, and Review accepts explicit durable-change proposals. For a new card type, first make it searchable, addable to the current deck and serializable into the existing task packet; do not start with another home-page module. A Dashboard action is never only a button. It must keep these interface semantics:

1. Route ordinary reading through `answer`, file-producing work through `artifact` and durable-system proposals through `writeback`. A view must not write Markdown directly.
2. Ordinary card selection only updates the working deck and never navigates. Only an explicit `Propose write-back` creates an action and opens Review.
3. Distinguish active, archived, withdrawn and completed for the same action key. Re-adding restores the active state, and its new timestamp isolates it from older runner completion records.
4. This repository may return copy-only task packets and Review briefs only. Local Codex and Claude Code CLI dispatch, Inbox or canonical writeback and arbitrary commands stay disabled, and model discovery, execution controls, runner status and maintenance actions are gated by runtime capabilities, not merely hidden with CSS.
5. Every new state updates the bilingual UI copy, the manuals, frontend contract tests, public safety checks and one desktop and mobile browser flow.
6. A new capability does not claim first-screen attention by default. It contributes a bounded Work Item or action through the extension contract, or reuses the on-demand Work Session result loop. Direct natural-language input stays collapsed while idle, and material, cards, artifacts, Review and maintenance controls appear only when the task needs them.
7. Earlier task packets in this repository may stay in page history but are never embedded recursively as assistant answers in later packets; only the prior user intent needed to understand the follow-up is carried forward.

Reuse `work-session-router.js`, `work-session-state.js`, `work-session-workbench.js`, the matching view owner, `doing-board-state.js`, `inbox.js` and `storage-contract.js`, and do not create a second result loop, localStorage key or parallel inbox. A headless integration contributes a bounded task through the existing extension manifest and Work Session contracts, without a second prompt router or Work Session; it preserves candidate-before-confirmation, the frozen template language and Review, and ordinary users still start from agent conversation or Start.

## Releases, contributions and support

| File | Responsibility |
| --- | --- |
| `README.md` | Project positioning, one try-it path, boundary, documentation map, license. |
| `README.zh.md` | Chinese-first entrypoint for readers who want the Chinese route. |
| `CONTRIBUTING.md` | Contribution scope, public-safety rules, PR checks; Chinese version in `docs/reference/CONTRIBUTING.zh.md`. |
| `SECURITY.md` | Security-sensitive reporting route and disclosure boundary; Chinese version in `docs/reference/SECURITY.zh.md`. |
| `SUPPORT.md` | Support route, issue information, support boundaries; Chinese version in `docs/reference/SUPPORT.zh.md`. |
| `docs/*.md` | The User Manual, System Reference and this guide, plus the technical report. |

Before adding a root Markdown file, ask whether GitHub users will really look for it as an entrypoint; detailed explanation belongs in the existing owner listed in the [documentation map](README.md). The onboarding files stay in the repository so users can compare placement and field shape. Users write their own content in the git-ignored `personal_vault/`, which never shows the examples, so they neither delete nor disable them; the optional maintainer switch that removes the case from the demo projection is in [Section 5 of the User Manual](user-manual.en.md#5-your-own-material).

Before a release, maintainers run every step of `.github/workflows/validate.yml` from the public repository; that workflow is the CI for this repository. The original maintainer may also run a private release-boundary gate from the prototype in the technical report. It is not shipped here, because it checks the export boundary between private sources and this package, and public contributors are not expected to have it. The checks confirm that this repository is a separate git project, that required directories and files exist, that `docs/` stays paired in English and Chinese, that disabled cases no longer feed active demo data, that the public provider capability is copy-only with local Codex and Claude Code CLI dispatch disabled and no remote provider, that local paths, secrets, sensitive people and blocked wording are absent, and that every public-only entrypoint is one of the registered demo or self-hosting stand-ins.

When reviewing a pull request, the maintainer first checks whether the change improves user understanding or operation, whether it preserves the public-safe boundary, whether the matching English and Chinese documents were updated, and whether the relevant validators passed. Large examples, real-person material, remote provider execution, commercial deployment instructions and unconfirmed agent output are usually narrowed or kept out of the public repository. Security-sensitive problems follow the private route in [SECURITY.md](../SECURITY.md), and [SUPPORT.md](../SUPPORT.md) lists what a support request should include.

The license is [LICENSE.md](../LICENSE.md); its commercial-use boundary and the reference licenses considered are explained in [COMMERCIAL_USE.md](reference/COMMERCIAL_USE.md).
