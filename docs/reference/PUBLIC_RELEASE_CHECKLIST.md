<p align="right">
  <strong>English</strong> | <a href="PUBLIC_RELEASE_CHECKLIST.zh.md">中文</a>
</p>

# Public Release Checklist

- [ ] Run `python3 scripts/build_public_starter_data.py --check` after the approved rebuild; do not accept hashes alone as source-freshness evidence.
- [ ] Confirm that the public repository is a separate git project.
- [ ] Confirm the root license is the custom `ResearchOS Source-Available Research License`, not a PolyForm license.
- [ ] Confirm `docs/reference/COMMERCIAL_USE.md` names an intentional public contact route for written permission.
- [ ] Confirm that `corpus/` is empty or contains only public-safe notes.
- [ ] Confirm that all demo materials are fictional, sanitized, or explicitly approved for public release.
- [ ] Confirm that key Markdown documents have separate English and Chinese versions.
- [ ] Confirm that English documents do not contain Chinese prose.
- [ ] Confirm that Chinese documents are written primarily in Chinese, except for code names, paths, commands, product names, and necessary technical identifiers.
- [ ] Run `python3 scripts/build_public_starter_data.py --write`, then run every step of `.github/workflows/validate.yml`, which is the CI for this repository: projection builds, the boundary and contract validators, and the Python and JavaScript regression suites. Locally, run its `validate_release_metadata.py` step with `--expected-commit "$(git rev-parse HEAD)" --require-clean` on a committed, clean working tree.
- [ ] From the `validate_task_extensions.py` and `validate_agent_architecture.py` results, confirm disabled examples stay inactive, no public extension bypasses authority or sensitivity rules, every frontend module is registered, server modules are reachable, removed compatibility/demo routes were not reintroduced, and owner budgets pass.
- [ ] Run `python3 scripts/plan_context.py --list --lang en` and the selected-language counterpart to confirm core and enabled extension routes are reachable without loading frozen-language task copy.
- [ ] Confirm the safety scan covers code as well as docs and catches local paths, secrets, sensitive real people, and blocked private semantics.
- [ ] Confirm there is no sibling private-repository name or path, federation/catalog metadata, operator identifier, request receipt, or shared runtime state.
- [ ] Confirm public task extensions remain local declarative descriptors and do not discover or call private systems.
- [ ] Open the dashboard locally and complete a browser smoke check.
- [ ] Complete the current Unified Desk journey: select an item, preview a date and reload, inspect components, then preview/copy the agent handoff. Check English/Chinese display, frozen content language and `390 x 844` mobile layout. Now/Library are semantic roles; the hidden compatibility workspace tabs are not part of the journey to check.
- [ ] Separately verify the existing Agent/CLI task/result boundary, explicit writeback candidate, continuity receipt and human confirmation. Check the applicable human-interaction acceptance and accessibility requirements and keep incomplete items open; the three desk tasks do not replace them. Never present an old browser task as current project truth.
- [ ] Confirm this repository's default runtime is `copy_only`, performs no local Codex probe, rejects every runner submission to the `codex` or `claude_code` provider without starting a thread or command, and emits copy-ready handoff; separately verify that personal-vault mode may expose controlled workspace-write actions.
- [ ] Confirm `dashboard/index.html` points to the public service port `8880`, not any other local service port.
- [ ] Start from a clean copied folder and verify both the one-command demo route and a small personal-vault fixture.

Before tagging a release:

- [ ] Refresh the validation snapshot in `docs/releases/v1.0.0.md` and its Chinese counterpart against the final commit; do not reuse worktree counts or digests after a release-sensitive change.
- [ ] On the final clean commit, run `python3 scripts/validate_release_metadata.py --release-date YYYY-MM-DD --expected-commit "$(git rev-parse HEAD)" --require-clean`; this binds final metadata, checked artifact digests, and release evidence to the exact ref without embedding a self-referential commit hash in generated files.
- [ ] Confirm the GitHub description no longer names an obsolete version and add public-safe topics.
- [ ] Record explicit maintainer decisions for the public project name, attribution, contact route, repository description/topics, and exact tag/Release.
- [ ] After approval, enable private vulnerability reporting, create the signed-off release tag/Release, and verify the public page while signed out.

For the Chinese version, read `docs/reference/PUBLIC_RELEASE_CHECKLIST.zh.md`.
