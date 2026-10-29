<p align="right">
  <strong>English</strong> | <a href="docs/reference/CONTRIBUTING.zh.md">中文</a>
</p>

# Contributing

Thank you for considering a contribution. ResearchOS Public Starter accepts public-safe improvements to documentation, examples, templates, validators, dashboard behavior, and copy-only handoff surfaces.

## Contribution Scope

Good contribution areas include:

- clearer documentation;
- public-safe example cases and templates;
- dashboard usability improvements;
- validation scripts that catch unsafe exports, broken docs, or config drift;
- copy-only handoff and fail-closed capability improvements;
- bug reports with reproducible local commands;
- non-commercial workflow examples that do not expose sensitive material.

## Public-Safety Rules

Before opening an issue or pull request, use fictional or redacted examples, and make sure your contribution does not include:

- real sensitive people, students, collaborators, reviewers, or relationship notes;
- private research memory or other personal data;
- unreleased manuscripts, confidential project plans, or raw corpus files;
- provider secrets, tokens, credentials, or account identifiers;
- local absolute paths or machine-specific runtime logs;
- unreviewed agent output presented as confirmed knowledge;
- commercial redistribution instructions that conflict with the license boundary.

Contributions must preserve the [license](LICENSE.md) and the [commercial-use boundary](docs/reference/COMMERCIAL_USE.md). Report security vulnerabilities through [Security](SECURITY.md), not a public issue.

## Documentation Standards

- Keep root documentation concise.
- Put detailed explanations in the existing owner identified by the [documentation map](docs/README.md).
- Keep key public-facing documents in separate English and Chinese files.
- Use concrete commands and paths instead of vague setup advice.
- Explain authority boundaries: source material, candidate interpretation, confirmation, validation, and export are different layers.
- Prefer small examples over large sample datasets.

## Local Checks

Before submitting a pull request, run every step of `.github/workflows/validate.yml`, which is the CI for this repository. Because `CITATION.cff` already carries the release date, `validate_release_metadata.py` checks final release metadata and fails without `--expected-commit` and `--require-clean`; locally, commit your change and run `python3 scripts/validate_release_metadata.py --expected-commit "$(git rev-parse HEAD)" --require-clean` on a clean working tree.

If your change affects documentation, check that the documentation map still points to the right files. If your change affects providers or startup modes, update `docs/user-manual.en.md` and `docs/user-manual.zh.md`.

## Issue and Pull Request Guidance

A useful bug report includes:

- operating system and Python version;
- command you ran;
- expected behavior;
- actual behavior;
- a short, redacted log excerpt when needed;
- whether case materials were enabled or disabled.

A useful pull request includes:

- a short explanation of the user problem;
- the files changed;
- the checks run;
- any public-safety assumptions;
- screenshots only when UI behavior changed.

## Maintainer Review

The maintainer may ask for narrower scope, smaller examples, stronger public-safety wording, or additional validation. This is normal for a project whose value depends on clean boundaries between research material, interpretation, confirmation, and release.
