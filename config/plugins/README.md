---
type: plugin_registry_readme
title: "ResearchOS Reviewed Plugin Manifests"
status: active
created: 2026-08-05
updated: 2026-08-07
sensitivity: public_safe
---

# Reviewed Plugin Manifests

`config/plugins/*.json` is the reviewed, repository-owned input port for `researchos-plugin-v1` manifests. Personal or machine-specific manifests belong in the Git-ignored `config/plugins.local/` directory.

This directory now holds reviewed first-party capability manifests as well as the host contract. `product_tier` prevents the technical word “plugin” from flattening the product architecture: `material_pipeline`, `research_assets`, and `research_portfolio` are `foundation_projection` owners for the optional Dashboard; `system_stewardship` is a folded `bundled_capability`; task-extension v1 installs normalize to `optional_extension`. `research_portfolio` deliberately splits the actionable Start projection from the complete lifecycle board in Library. A private authority repository may register additional private-only task packs; Public Starter omits unavailable private packs rather than copying their paths or research context.

All checked-in manifests implement [ResearchOS Plugin Standard v1.2](../../05_workflows/research_management/researchos-plugin-standard-v1.2.md). The core-owned `researchos_plugin_capability_v1` is a non-installable prototype; concrete plugins are replaceable contributions. Canonical claim identity lives in `researchos-capability-registry-v1.json`; `composition.provides` names contribution IDs, `capability_bindings` links them to claims, and every task projection names both. Equal plugin, contribution, and claim strings never replace an explicit binding. External skills remain linked candidates in `config/capability-sources.json` until version, license, transformation, dependency, composition, baseline value, evidence, and destination owner are reviewed. The standard deliberately has no raw-copy mode.

A manifest may not inject arbitrary frontend JavaScript, create a workspace, own canonical storage, or bypass Review. Public Starter accepts only declarative, public-safe manifests without network or command permissions. Task packs must keep one source owner rather than duplicating paths, copy, details, and aliases across a manifest and a legacy catalog.

Plugin Standard v1.2 keeps host `core_api_version: "1"` backward compatible and adds optional `work_item_providers` plus a complete action contract: `effect`, `confirmation_mode`, `risk`, `write_scope`, `reversible`, and `public_behavior`. Public Starter exposes fictional Work Items and copy-only handoff; its scheduling and completion actions stay `demo_only`, and the public plugin gains neither execution nor canonical write access.

Every projection declares the v1 envelope, sensitivity, freshness mode, and an exact `export_fields` map. Browser code receives `researchos-projection-envelope-v1`; an unknown version, missing generation time, denied sensitivity, missing field, or unavailable required source produces `empty/error` and no payload. UI contributions keep the legacy `slot` only as a routing alias and also declare the canonical `surface.region`: `start.primary`, `library.context`, `next.task`, `overlay.governance`, or `overlay.utility`. An action may be attached only to a slot on the same canonical surface.

Every manifest also owns a machine-checked `documentation.readme` at `docs/plugins/<plugin-id>/README.md`. The README must cover purpose/non-goals, availability and parity, dependencies, lifecycle, data/permissions/export, verification, recovery, comparative value, and retirement. Missing, escaping, symlinked, or incomplete references fail the Plugin Standard gate. See [the documentation contract](../../docs/plugins/README.md).

Validate the host and ownership overlays with:

```bash
python3 scripts/validate_plugin_standard.py
python3 scripts/validate_plugins.py
python3 -m unittest evals.test_plugin_governance
```

## Lowest-Burden Installation

Only `optional_extension` is locally installable. Foundation and bundled capabilities are product components, not entries managed by the example installer. The dashboard does not require a plugin marketplace or a setup step. Ask Codex:

> Install the ResearchOS method_comparison example plugin.

The deterministic fallback is:

```bash
python3 scripts/manage_plugins.py install method_comparison
```

This command copies only the bundled, reviewed public-safe descriptor into the Git-ignored `config/extensions.local/`, validates the host, and rebuilds the dashboard. It does not use the network, download or execute remote code, or write canonical memory. Disable, re-enable, or remove it with the same local lifecycle:

```bash
python3 scripts/manage_plugins.py disable method_comparison
python3 scripts/manage_plugins.py enable method_comparison
python3 scripts/manage_plugins.py uninstall method_comparison
```

If the local manifest was customized, the manager refuses to overwrite or delete it.

The optional Codex thread handoff uses the same local lifecycle:

```bash
python3 scripts/manage_plugins.py install codex_thread_handoff
```

This installs only the ResearchOS task contract. It does not expose the user's computer, create a tunnel, install a bridge, or register a ChatGPT connector. Readiness is reported as four distinct states: `installed`, `connector_configured`, `connector_verified`, and `ready`. Public users supply their own authenticated, read-only MCP access line conforming to the [Codex Thread Handoff README](../../docs/plugins/codex-thread-handoff/README.md); no private endpoint, token, path, thread ID, or session data is included here.
