---
title: Research Assets plugin
sensitivity: public_safe
status: active
---

<p align="right"><strong>English</strong> | <a href="README.zh.md">中文</a></p>

# Research Assets

## Purpose

Projects source overview, asset graph, previews, and bounded source navigation into the shared ResearchOS interface.

## Use and non-goals

Use it to find and inspect registered research assets. It does not infer source authority, fetch arbitrary paths, or make a preview canonical.

## Availability and parity

Universal foundation projection with exact private/Public Starter manifest parity. Each runtime projects only its own allowed data.

## Dependencies

Requires `researchos_core`; provider data must satisfy the projection envelope and runtime read policy.

## Lifecycle

Embedded foundation capability maintained through ResearchOS releases.

## Data, permissions, and export

Declarative, local-only, and without network, command, or canonical-write access. Projection export is limited to each manifest's exact field map.

## Verification

Run the manifest-listed plugin and projection tests, then the plugin-standard gate.

## Failure recovery

Unknown schema, denied sensitivity, missing required field, or stale provider data must yield an empty/error envelope rather than raw fallback data.

## Value and alternatives

It provides one governed navigation surface. Direct filesystem browsing remains an explicit user-controlled fallback.

## Retirement

Retire only when another foundation capability preserves fail-closed projections, preview provenance, and public parity.

## Procedure and implementation

The pseudocode, control flow and implementation boundary for this function are given below. The asset-graph builder, research-assets client and group candidate route provide projections and explicit composition prompts. A universally complete typed-graph extractor and scientific compatibility checker are not implemented.

Symbols are plugin shorthand defined in the [plugin directory README](../README.md). The plugin system is frozen; see the [governance guide](../../governance-guide.en.md#task-extensions-and-plugins).

| Plugin, form and deployment | Core operator or constraint | Meaning, definitions and checks |
| --- | --- | --- |
| Asset navigation and composition (`research_assets`); $\mathsf P_i^{\mathrm{cap}}$, foundation | $y_t=\mathcal G_t^a[W_t]$; $\mathcal G_t^{+}=\mathcal G_t$ | For graph navigation, $\mathcal G_t^a$ retains permitted fields and relations, and $W_t$ selects its vertices. The induced subgraph preserves relations among those vertices. Grouping and dissolution instead produce $\Delta_t$ for review. |

### Asset navigation and composition

A permitted graph $\mathcal G_t^a$ and selection $W_t$; output: a view or a separately checked group candidate.

```pseudocode
// Membership and visual proximity do not establish scientific support.
RESOLVE selected identities and versions; REMOVE inaccessible fields
SET $y_t\leftarrow\mathcal G_t^a[W_t]$; RETAIN edge types, grounds and status
IF operation is navigation: RETURN $y_t$ with $\mathcal G_t^{+}=\mathcal G_t$
IF operation is composition or dissolution:
    BIND $r,m,\kappa$ to selected versions
    CHECK roles and preserved relations
    RETURN $\Delta_t$ separately from the view
```

**Algorithm explanation.** The two branches have different consequences: navigation returns a permitted view of the existing graph, while composition or dissolution returns a change candidate that must be checked. Sharing the selected objects does not mean sharing the authority to modify them, still less that a visual relation has become scientific support.
