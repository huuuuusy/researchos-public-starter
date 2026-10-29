<p align="right">
  <strong>English</strong> | <a href="README.zh.md">中文</a>
</p>

# Scripts

This directory contains the public starter runtime and validation scripts. Start from the entrypoints below instead of treating every helper as a user-facing command.

| Entrypoint | Use it for | Boundary |
| --- | --- | --- |
| `python3 scripts/start_researchos.py` | Inspect or start dashboard, CLI, GUI, and public-starter modes. | Runtime entrypoint only; providers are execution adapters, not memory authority. |
| `python3 scripts/receipt_cli.py --help` | Build, validate, or inspect ContextReceipt/HandoffReceipt JSON from an agent client or a terminal without Dashboard/server. | Explicit relative files or stdin/stdout only; no discovery, provider call, egress, canonical write, overwrite, or human-decision signing. |
| `python3 scripts/build_public_starter_data.py --write` | Generate demo records and the dashboard projection from fictional case files. | Reads public starter material only; does not read non-demo workspace material. |
| `python3 scripts/build_public_starter_data.py --disable-cases --write` | Rebuild with demo cases disabled while keeping the example files as references. | Use before replacing the starter with user-owned public-safe material. |
| `python3 scripts/plan_context.py <task-id> --lang en` | Print the minimal route for one of 20 public-safe task IDs or 13 compatibility aliases; `--intent-json`, `--prior-receipt-json`, and `--headless-json` provide typed, bounded continuity. | Read-only and copy-only; a route receipt never grants mutation, external effect, network, command, or canonical write. |
| `python3 scripts/query_plugin_portfolio.py` | Query the four non-owning capability groups and their declarative contributions without reading Dashboard fields. | Grouping projection only; registration, enablement, or a passing test does not admit a capability. |
| `python3 scripts/query_research_agenda.py` | Answer the active-lead count and return coverage/integrity evidence. Explicit views are `lead-active`, `lead-all`, `support-active`, `support-all`, `waiting`, `queued`, `conditional`, `paused`, `review`, `unclassified`, and `all`; legacy `lead`/`support` mean active only. | Read-only projection from the chosen agenda Markdown; missing/invalid responsibility fails closed and ownership is never inferred from activity. |
| `python3 scripts/validate_task_extensions.py` | Validate task extension API version, read limits, authority, language, and public-safety fields. | Fails closed; does not enable or execute extensions. |
| `python3 scripts/validate_plugin_standard.py` | Validate explicit governance, lineage/licensing, deployment, effects, composition, routing, maturity proof, and retirement; add `--public-root` for semantic variant parity. | Fails closed; does not install, execute, or absorb capabilities. |
| `python3 scripts/manage_plugins.py install method_comparison` | Install, validate, disable, enable, or uninstall a bundled example plugin. | Git-ignored local state only; reversible, no network, remote code, or canonical write. |
| `python3 scripts/plan_evolution.py` | Show a path-bounded maintenance candidate and, after exact plan-ID confirmation, run only its fixed safe subset. | Public demo stays read-only; personal-vault checkpoints are local and Git-ignored. |
| `python3 scripts/validate_evolution_control.py` | Validate planning, fixed-step, confirmation, runtime-mode, and public/private isolation contracts. | Report-only; does not run maintenance. |
| `python3 scripts/check_all_links.py` | Check local Markdown links across the public starter. | Report-only; does not rewrite docs. |
| `python3 scripts/validate_runtime_config.py` | Check the runtime config and provider registry boundaries. | Public starter remains demo-first; do not commit local API keys. |
| `python3 scripts/validate_public_safety.py` | Scan docs, code, config, and demo data for private semantic residue, user paths, secrets, and raw corpus payloads. | Release gate; does not upload or publish anything. |
| `python3 scripts/validate_docs_bilingual.py` | Confirm that reader-facing English and Chinese documents remain paired and cross-linked; also keep the related-tools names, project URLs, ordering, snapshot date, and non-endorsement boundary aligned. | Documentation gate; does not translate, verify that an external source is still official or available, or rewrite files. |
| `python3 scripts/validate_positioning_consistency.py` | Keep active English/Chinese entry docs aligned on a small file-based tool, Agent/CLI primary execution, and Dashboard as the narrow persistent attention/control surface. | Positioning gate; rejects equal-surface, dashboard-first, Workbench-first, and vague “secondary dashboard” wording. |
| `python3 scripts/validate_release_metadata.py` | Keep release notes, citation, changelog, visible license wording, and declared generated-artifact SHA-256 digests aligned. | Release metadata gate; does not tag or publish. Once `CITATION.cff` declares `date-released`, it requires `--expected-commit <full-sha> --require-clean` (`--release-date YYYY-MM-DD` is optional and must match). |
| `python3 scripts/validate_agent_architecture.py` | Check Agent code routes, supported imports, frontend script registration, and owner-file size budgets. | Architecture gate; does not rewrite code. |
| `python3 -m unittest discover -s evals -p 'test_*.py'` | Run builder, frontend, runner, file-bridge, and safety regressions, including the schema/owner alignment of metadata profiles, Rule evolution, admission state and RuntimeProfile. | Local test only. |

Helper packages:

- `researchos_data/`: supported data owners include maintenance, declarative tasks, plugin host/ownership/lifecycle, conversation authority, repository layout, public catalog, and read-only frontend/style manifests; `validate_agent_architecture.py` rejects unregistered helpers.
- `researchos_kernel/` and `researchos_adapters/`: what each owns and which way their imports point are described once, in the [code map](../docs/system-reference.en.md#code-map).
- `researchos_server/`: local dashboard server owners for stores, the Codex runner, preview/source bridges, and maintenance; `serve_dashboard.py` keeps only HTTP routing and dependency assembly.

Before changing code, read the code map in `docs/system-reference.en.md`; do not scan every helper or generated JSON first.
