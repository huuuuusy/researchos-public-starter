---
title: Codex Thread Handoff troubleshooting
sensitivity: public_safe
status: active
---

<p align="right"><strong>English</strong> | <a href="TROUBLESHOOTING.zh.md">中文</a></p>

# Troubleshooting

## Plugin installed but tools are absent

The ResearchOS plugin and MCP connector are separate. Verify the local bridge,
restart it after code changes, and refresh or recreate the client connector to
replace a cached tool schema.

## Tool appears but the current ChatGPT conversation disables it

Tool discovery and conversation runtime enablement are different checks. Open
the installed plugin's management page and refresh its actions. Then use **Try
in chat** or explicitly select the plugin in the conversation composer. Retest
in that plugin-enabled conversation; an older conversation may retain its prior
runtime even after the global action list is refreshed.

## Tool exists but thread is not found

Use a canonical lower-case hyphenated UUID or exact `codex://threads/<UUID>`.
Confirm the thread is stored below an allowed `sessions` or
`archived_sessions` root. Do not add an arbitrary path argument as a workaround.

## Reading stops early

Inspect `next_cursor`/`next_offset`, source truncation, and page truncation in
the receipt. Continue only with the returned cursor. If the source exceeded a
hard limit, report that the full thread was not reviewed.

## Connector works locally but not from ChatGPT

Verify authenticated HTTPS reachability, the exact MCP endpoint, tunnel health,
and client connector status. Keep secrets in an authorization mechanism, not a
query string.

## Format changed

Fail closed and add a synthetic fixture for the new Codex event shape. Do not
scan unrelated files or expose raw JSONL to recover compatibility.

## Safe fallback

Ask the user to paste the smallest relevant excerpt and label it as manually
provided context. The handoff can continue without pretending the connector was
verified.
