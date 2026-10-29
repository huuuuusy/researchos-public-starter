# Changelog

All notable changes to ResearchOS Public Starter are documented in this file.

The format follows the spirit of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

Private-repository CI (repository not public), run `39708102808` at commit `ad6903328c28c8e96c7e2f0b3c40f5979efbf701`, ubuntu-24.04 and CPython 3.11.17: the 101-file default Python regression set reported `Ran 972 tests` / `OK (skipped=30)`, the 19-file JavaScript default set passed, and the release gate `run_public_release_gate.py --ci` passed. Public CI run `39708093367` at commit `49f95789422231c4aee737912b53d73ce199e94e`, same environment: `Ran 670 tests` / `OK (skipped=4)`, with all 39 JavaScript contract suites passing. Both runs are dated 22 October 2026. See the [V1.0 release notes](docs/releases/v1.0.0.md) for commands, inventory counts and artifact hashes. These receipts cover only their specified commits.

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
