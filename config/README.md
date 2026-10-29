<p align="right">
  <strong>English</strong> | <a href="README.zh.md">中文</a>
</p>

# Configuration

Stores credential-free runtime configuration. The public starter is `copy_only` with `execution_scope: none`: it starts neither the local Codex nor the Claude Code CLI and enables no real API calls. Private and personal-vault runtimes may separately configure controlled local execution without committing secrets.

## Case Materials Switch

`public_starter.case_materials.enabled` controls whether public example cases enter active demo data. When set to `false`, files under `08_exports/public_starter/` remain in the repository but are no longer emitted as active records by the data builder.

## Public Runtime Read Boundary

`public-runtime-read-manifest.json` is the single exact-file allowlist for public preview, source-tree, and copy-only projection reads. The boundary fails closed when the manifest is missing or malformed, or when an entry is duplicated, absolute, outside the repository, a symlink, or not a regular file. Allowing one file never grants directory-wide or sibling access.
