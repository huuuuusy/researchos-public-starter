<p align="right">
  <strong>English</strong> | <a href="docs/reference/SECURITY.zh.md">中文</a>
</p>

# Security Policy

ResearchOS Public Starter is a local-primary starter project, but security-sensitive problems can still occur through unsafe examples, accidental secret exposure, provider misconfiguration, generated data, or public export checks.

## Supported Scope

Security reports should focus on the current public starter package, including:

- dashboard files and local server behavior;
- runtime configuration examples;
- provider registry, local-only execution, and read-only sandbox guardrails;
- read-only public-demo HTTP write boundaries and personal-vault write-root confinement (local writeback and `workspace-write` stay below `personal_vault/`);
- generated public starter data;
- the absence of sibling private-system discovery, execution, and shared runtime state;
- validators and safe-export checks;
- documentation that could encourage unsafe secret or data handling.

## What Counts as Security-Sensitive

Please treat the following as security-sensitive:

- a path that encourages committing provider secrets;
- a validator gap that allows obvious secrets or personal machine paths into release files;
- a demo configuration that unexpectedly enables real provider calls;
- a generated file that includes sensitive local state;
- a route, extension, or generated artifact that reveals or calls a sibling private system;
- a dashboard or server behavior that exposes files outside the intended project scope;
- documentation that tells users to publish raw corpus, credentials, or sensitive personal material.

## How to Report

Do not post exploit details, secrets, credentials, or sensitive examples in a public issue.

Preferred reporting route:

1. Use the repository security advisory or private vulnerability reporting channel if it is enabled.
2. If that channel is unavailable, email `shiyu.hu@ntu.edu.sg` with the subject `ResearchOS security report`.
3. Provide a minimal description, affected file or command, expected impact, and a redacted reproduction path.
4. Keep any sensitive sample local until the maintainer asks for a sanitized version.

## Safe Disclosure Expectations

The maintainer will try to acknowledge valid reports, assess whether the issue affects the public starter boundary, and prepare a fix or documentation update. Public discussion should wait until sensitive details have been removed or the issue is no longer exploitable.
