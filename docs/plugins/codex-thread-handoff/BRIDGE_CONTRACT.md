---
title: Codex Thread Handoff bridge contract
sensitivity: public_safe
status: active
---

<p align="right"><strong>English</strong> | <a href="BRIDGE_CONTRACT.zh.md">中文</a></p>

# Bridge contract

## Required tools

`list_codex_threads(cursor?, limit?)` returns bounded metadata, a continuation
cursor or offset, and a receipt. `read_codex_thread(thread, cursor?, bounds...)`
accepts only a canonical lower-case UUID or exact `codex://threads/<UUID>` and
returns bounded user/assistant text plus pagination and context receipts.

Equivalent parameter names such as `offset/max_chars` are acceptable when the
semantics are documented and lossless pagination can be verified.

## Required source boundary

The server derives locations from a process-owned Codex home and appends only
explicit audited subdirectories such as `sessions` and `archived_sessions`.
MCP callers cannot supply a path, glob, storage root, or alternate home. Files
must resolve below an allowed root, symlinks are rejected, and the filename UUID
must match `session_meta.payload.id`.

## Required semantic reduction

The default projection contains user and assistant text only. System/developer
messages, reasoning, raw JSONL, tool calls, tool output, attachments, auth files,
configuration, memory, databases, and logs are excluded—not merely redacted.

## Required bounds and receipts

Bound scan count, source bytes, line size, source messages, message size, page
characters, page messages, list size, and cursor size. Receipts must report at
least adapter/source version, roles included, omitted categories, redaction
count, source/page truncation, returned size, thread identity, and a page hash.
Cursors must be validated and bound to the operation and thread or to an
immutable source snapshot; a cursor must not silently continue a changed thread.
If a source exceeds the byte cap, the connector may use a documented bounded
head or tail window, but the receipt must identify the selected window, total
source bytes, scanned bytes, and truncation. Oversize must not be reported as a
UUID mismatch.

## Required redaction

Redact authorization headers, cookies, common API/access/refresh tokens,
passwords, client secrets, private-key blocks, and credential-bearing URLs.
Redaction is defense in depth: private facts that do not look like secrets may
remain, so data minimization and user-selected thread scope are mandatory.

## Required execution boundary

Thread reading makes no network request, starts no agent, executes no command,
and does not depend on the Codex CLI binary. The connector is read-only and
non-destructive. Remote HTTPS exposure, authentication, and tunnel lifecycle are
separate deployment concerns.

## Compatibility failure

Unknown storage/event formats fail closed. Compatibility work must add audited
fixtures for the new format; it must not broaden file discovery to make an old
parser appear successful.

## Bounded pagination

Keep the authorized task identity fixed across pages. Track visited continuation cursors and the remaining read budget. Stop on an exhausted budget, an absent cursor or a repeated cursor, and retain the access or truncation status in the handoff receipt. An incomplete history is a continuation gap, not permission to read unrelated tasks or a complete-history claim. These steps are obligations of the connector-using host method; the declarative extension does not run a pagination loop itself.
