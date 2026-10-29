---
title: Codex Thread Handoff security
sensitivity: public_safe
status: active
---

<p align="right"><strong>English</strong> | <a href="SECURITY.zh.md">中文</a></p>

# Security boundary

The protected assets are conversation text, local identity and paths,
credentials accidentally pasted into messages, hidden instructions/reasoning,
tool payloads, and unrelated files under the Codex home.

The MCP caller and every byte in a session file are untrusted. The local user
controls process configuration. The caller never controls storage roots.

Required controls are listed in [BRIDGE_CONTRACT.md](BRIDGE_CONTRACT.md).
Particular release blockers are arbitrary path input, symlink escape, raw-event
fallback, unbounded scans/pages, reusable cursors not bound to source identity,
credentials in URLs, and any claim that regex redaction makes private text safe
for public release.

The public ResearchOS package contains protocol, tests, and setup guidance only.
It must not contain a real endpoint, token, username, home path, thread UUID,
session fixture, project label, or output captured from a private connector.

If a connector is remotely reachable, use authenticated HTTPS, least-privilege
credentials, rotation, local loopback binding, and a service lifecycle the user
can stop. A tunnel supplies reachability, not multi-tenant isolation or content
safety.
