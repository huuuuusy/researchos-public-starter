---
title: Codex Thread Handoff setup
sensitivity: public_safe
status: active
---

<p align="right"><strong>English</strong> | <a href="SETUP.zh.md">中文</a></p>

# Setup

## 1. Install the ResearchOS task plugin

From the ResearchOS repository:

```bash
python3 scripts/manage_plugins.py install codex_thread_handoff
python3 scripts/manage_plugins.py status codex_thread_handoff
```

This establishes only the task contract.

## 2. Operate a conforming local connector

Use an existing private MCP bridge or a separately audited implementation of
[BRIDGE_CONTRACT.md](BRIDGE_CONTRACT.md). Bind the local service to loopback.
Keep tokens out of URLs and source control. Confirm locally that the required
tools are advertised and that an explicitly selected synthetic or private test
thread can be paged without exposing hidden roles or tool payloads.

## 3. Connect the private MCP server to the client

For personal or developer-mode use, the preferred current OpenAI path is
[Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).
Its `tunnel-client` runs beside the private server, opens an outbound HTTPS path,
and can forward to a local MCP server over stdio or HTTP without creating a
public listener or opening inbound firewall ports.

Secure MCP Tunnel is for private connections and developer-mode testing; it is
not a public plugin-submission endpoint. A user-owned authenticated HTTPS tunnel
or gateway remains an alternative for a persistent personal connector. In both
cases, keep secrets out of URLs and never expose an unauthenticated listener.

## 4. Register or refresh the client connector

Create a custom MCP connector in the supported client using the authenticated
HTTPS MCP endpoint. After any tool-schema change, restart the local service and
refresh or recreate the connector because clients may cache advertised tools.

In ChatGPT, confirm the refreshed actions on the installed plugin's management
page. Then use **Try in chat** or select the plugin in the conversation composer
to create a plugin-enabled conversation. Do not use an older conversation as
the only deployment test: its runtime may remain stale even when the global
tool schema is current.

## 5. Verify readiness

Check in order:

1. the plugin status reports installed and enabled;
2. the client lists `list_codex_threads` and `read_codex_thread`;
3. the test conversation visibly has the plugin attached;
4. a bounded list call returns a receipt;
5. an explicitly selected thread reads through at least two pages when long;
6. hidden roles/tool records are absent and fake secrets are redacted;
7. stopping the connector or removing the thread fails closed.

Only then call the integration `ready`.
