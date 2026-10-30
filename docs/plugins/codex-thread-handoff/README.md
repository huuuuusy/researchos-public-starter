---
title: Thread Handoff plugin (id codex_thread_handoff)
sensitivity: public_safe
status: instrumented
---

<p align="right"><strong>English</strong> | <a href="README.zh.md">中文</a></p>

# Thread Handoff (`codex_thread_handoff`)

This optional ResearchOS plugin defines how an agent-client task is continued in
ChatGPT or another MCP client. Its documentation directory spells the id with
hyphens (`codex-thread-handoff/`). The plugin id keeps the name of the first client it was
built for, Codex; the handoff packet itself is client-neutral. It deliberately separates two control planes:

1. ResearchOS installs a declarative task contract.
2. The user separately configures a read-only MCP connector that can reach the
   local Codex session store.

Installing the plugin does not expose a computer, create a tunnel, or make the
connector ready.

## Purpose

Read one selected Codex thread as bounded, redacted user/assistant context and
continue the work without manual copy/paste or arbitrary `~/.codex` access.

## Use and non-goals

Use it when the user supplies a canonical UUID or `codex://threads/<UUID>` and
wants another client to understand or continue that task. It is not a session
browser, agent runner, shell, workspace reader, hidden-reasoning exporter,
thread editor, or automatic ResearchOS memory writer.

## Availability and parity

The same manifest and task semantics apply to the prototype in the technical
report, this repository, and a personal vault. The prototype may already have a
domain and connector; users of this repository supply their own. No private
endpoint, token, path, thread ID, or content is included in this repository.

Readiness has four separate states:

- `installed`: the local manifest is present and enabled;
- `connector_configured`: the MCP endpoint is registered in the client;
- `connector_verified`: the client sees the required tools and a health/read
  probe succeeds;
- `ready`: the selected thread can be read under the contract.

ChatGPT tool availability is also conversation-scoped. After a connector schema
change, open the installed plugin's management page and refresh its actions,
then start a plugin-enabled conversation with **Try in chat** (or select the
plugin in the conversation composer). An older conversation may discover the
new tool name yet still report that the plugin is disabled in that conversation
runtime; this is not evidence that the bridge itself is unavailable.

## Dependencies

Required: ResearchOS core plus an independently operated MCP connector exposing
`list_codex_threads` and `read_codex_thread` as defined in
[BRIDGE_CONTRACT.md](BRIDGE_CONTRACT.md). The connector may be the user's
existing private bridge or another conforming local implementation. Thread
reading must not depend on locating or starting the Codex CLI executable.

## Lifecycle

Install locally and reversibly:

```bash
python3 scripts/manage_plugins.py install codex_thread_handoff
```

`disable`, `enable` and `uninstall` take the same id; see
[Installing the bundled examples](../../governance-guide.en.md#installing-the-bundled-examples). These commands only manage a reviewed
manifest under a Git-ignored local directory and re-validate the plugin host.
They do not install the connector, open network access, or write canonical memory.

## Data, permissions, and export

The ResearchOS plugin is declarative and requests no network, command, or
canonical-write permission. The external connector owns local session access
and must use a fixed storage allowlist, strict UUID parsing, bounded pagination,
role reduction, redaction, and receipts. Thread-derived content is `local_only`
by default and is never part of an automatic export. Public reuse requires a
separate user review.

## Verification

Run:

```bash
python3 scripts/validate_task_extensions.py
python3 -m unittest evals.test_codex_thread_handoff_extension
python3 scripts/validate_plugin_standard.py
```

Then follow [SETUP.md](SETUP.md) and verify the connector contract with a thread
the user explicitly selects. Never commit that real UUID to a public fixture.

## Failure recovery

If the tool is missing after a bridge update, restart the local service and
refresh/recreate the client connector so its cached MCP schema is replaced. If
the tool exists but the current conversation runtime disables the plugin, enter
through **Try in chat** or explicitly select the plugin for that conversation.
If the thread is not found, validate the canonical UUID and fixed session roots.
If a receipt reports truncation, continue with its cursor; do not infer that the
omitted content was reviewed. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Value and alternatives

The comparison target is manual copy/paste. The plugin should be retained only
if real handoffs preserve provenance and reduce context loss enough to justify
connector setup, local maintenance, format drift, and residual redaction risk.
Manual excerpts remain the safest fallback for one-off or highly sensitive work.

## Retirement

Retire when a supported host-native handoff provides equal local-only authority,
bounded pagination, redaction/omission receipts, and semantic parity with the
prototype in the technical report at lower burden—or if real use shows no net advantage over manual transfer.

## Procedure and implementation

The pseudocode, control flow and implementation boundary for this function are given below. The extension, bridge contract and readiness checks define connector use. The host performs the read; pagination and redaction obligations remain part of that method contract. Installation alone does not establish a ready connector.

Symbols are plugin shorthand defined in the [plugin directory README](../README.md). The plugin system is frozen; see the [governance guide](../../governance-guide.en.md#task-extensions-and-plugins).

| Plugin, form and deployment | Core operator or constraint | Meaning, definitions and checks |
| --- | --- | --- |
| Task handoff (`codex_thread_handoff`); $\mathsf P_i^{\mathrm{task}}$, optional | $H_{t,h}^a:=H_t^a\vert_h$; $Z_t=D_{\omega_t^u}(H_{t,h}^a,q_t)$ | Restrict permitted history to task $h$, then select continuation context. The connector and receipt record access, redaction and truncation; unrelated task history is excluded. |

### Task handoff

An explicitly identified task $h$, a continuation question and connector readiness; output: a bounded continuation packet with access and truncation status.

```pseudocode
// Reading and handing off history does not execute continuation.
VALIDATE target task identity and connector readiness before requesting history
RESTRICT reads to $H_{t,h}^a\leftarrow H_t^a\vert_h$ and the approved access budget
WHILE needed pages remain AND budget remains:
    IF completion or a repeated cursor is detected: BREAK
    FETCH the needed page; RECORD its cursor and access cost
REDACT excluded fields; RETAIN omitted or truncated status
SET $Z_t\leftarrow D_{\omega_t^u}(H_{t,h}^a,q_t)$
RETURN current intent, decisions, unresolved work and source references
```

**Algorithm explanation.** Identity and access checks precede pagination. Cursor tracking and the read budget bound retrieval, while redaction and truncation status preserve what was actually available for the returned handoff.
