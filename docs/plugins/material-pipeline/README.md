---
title: Material Pipeline plugin
sensitivity: public_safe
status: active
---

<p align="right"><strong>English</strong> | <a href="README.zh.md">中文</a></p>

# Material Pipeline

## Purpose

Turns a material lead into a bounded candidate for intake, upgrade, scouting, and Review without bypassing source authority.

## Use and non-goals

Use it when adding or upgrading research material. It does not certify source quality, create canonical memory directly, or publish an intake record.

## Availability and parity

Universal foundation projection with exact private/Public Starter manifest parity. Runtime data differs: each installation supplies its own local sources.

## Dependencies

Requires `researchos_core`; research-asset navigation is optional.

## Lifecycle

Embedded foundation capability. It follows the ResearchOS release and is not installed or removed with the optional-plugin manager.

## Data, permissions, and export

Declarative only: no network, command, or canonical-write permission. Local candidate data stays local; only a separately reviewed safe export may leave the runtime.

## Verification

Run the validation commands and behavior tests in `config/plugins/material-pipeline.json` plus the plugin-standard gate.

## Failure recovery

If a source is missing or ambiguous, keep the item as a lead, record the gap, and retry after the user provides the smallest authoritative source.

## Value and alternatives

The benefit is a visible candidate-to-Review boundary. Direct manual file entry remains possible but carries more authority and consistency risk.

## Retirement

Retire only if another foundation owner preserves bilingual intake, candidate authority, public safety, and recovery behavior.

## Procedure and implementation

The pseudocode, control flow and implementation boundary for this function are given below. The material-pipeline manifest and candidate-authority client implement intake routing and candidate boundaries. Source interpretation remains a method step; the existing maturity projection is heuristic (technical report Appendix B.3, gap 35).

Symbols are plugin shorthand defined in the [plugin directory README](../README.md). The plugin system is frozen; see the [governance guide](../../governance-guide.en.md#task-extensions-and-plugins).

| Plugin, form and deployment | Core operator or constraint | Meaning, definitions and checks |
| --- | --- | --- |
| Material intake (`material_pipeline`); $\mathsf P_i^{\mathrm{cap}}$, foundation | $\forall v\in V(\Delta_t):\ \sigma_t(v)\ne\varnothing$ | $V(\Delta_t)$ contains the candidate material objects; $\sigma_t(v)$ records their source references and versions. Require resolvable provenance for each object; registration does not establish understanding. |

### Material intake

A selected source, its version, $q_t$ and $\kappa$; output: a grounded material candidate and unresolved source questions.

```pseudocode
// An unresolved locator supplies no evidence about source contents.
FOR each selected source:
    BIND permitted locator and source version
    IF locator cannot be resolved: RETURN missing-source question
CONSTRUCT $\Delta_t$
FOR each $v\in V(\Delta_t)$:
    RETAIN $\sigma_t(v)$; DISTINGUISH source statements from interpretation
CHECK source support and reuse conditions; KEEP uncertain attributes unresolved
// Maturity is assessed separately under report Appendix B.3 (gap 35)
RETURN candidate and checks through the host
```

**Algorithm explanation.** A traceable candidate must state both where its content comes from and which parts are interpretation. When a source cannot be located, no content is constructed from that source; when evidence is insufficient, the affected attributes remain unresolved. Whether the material is mature is decided by a separate evaluation.
