---
title: Research Portfolio plugin
sensitivity: public_safe
status: active
---

<p align="right"><strong>English</strong> | <a href="README.zh.md">中文</a></p>

# Research Portfolio

## Purpose

Projects registered research responsibilities and attention state into Now without becoming counting authority itself.

## Use and non-goals

Use it to navigate registered lead, support, waiting, queued, paused, and attention states. It does not infer responsibility from recent activity or generated data.

## Availability and parity

Universal foundation projection; its manifest is identical in this repository and in the prototype in the technical report. Private and demo data remain separate.

## Dependencies

Requires `researchos_core` and a runtime-specific portfolio projection that satisfies the shared envelope.

## Lifecycle

Embedded foundation capability maintained through releases.

## Data, permissions, and export

Declarative and local-only, with no network, command, or canonical-write permission. Generated/dashboard state is a projection, never canonical authority.

## Verification

Run the manifest behavior tests and `python3 scripts/query_research_agenda.py`, which reports portfolio coverage, then the plugin-standard validator.

## Failure recovery

If coverage is stale or responsibility is invalid, report a registered count and preserve `unclassified` or overlapping attention states.

## Value and alternatives

It offers consistent responsibility navigation. Reading the canonical portfolio file directly remains the authority fallback.

## Retirement

Retire only if another foundation owner preserves counting authority, coverage receipts, and public/demo separation.

## Procedure and implementation

The pseudocode, control flow and implementation boundary for this function are given below. The portfolio action contract and existing work-session routes distinguish these effects. The feasible-set notation specifies the selection boundary; complete research-task composition that forms $\mathcal A_{i,t}$ from prerequisites and dependencies is not yet implemented (report Section 4.5), and the report supplies no optimal scheduler. Public actions remain previews or copy-only handoffs.

Symbols are plugin shorthand defined in the [plugin directory README](../README.md). The plugin system is frozen; see the [governance guide](../../governance-guide.en.md#task-extensions-and-plugins).

| Plugin, form and deployment | Core operator or constraint | Meaning, definitions and checks |
| --- | --- | --- |
| Portfolio attention (`research_portfolio`); $\mathsf P_i^{\mathrm{cap}}$, foundation | $a_t=(r,m)\in\mathcal A_{i,t}$ | For the selected plugin, $\mathcal A_{i,t}$ contains applications allowed by current inputs, prerequisites, authority and resources. Select a portfolio action within this set; membership specifies no optimal ranking. |

### Project attention and next action

A selected work item, current dependencies and scoped authority; output: a feasible application or a named unmet condition.

```pseudocode
// Filter mutations by authority and prerequisites before selecting an action.
RECOVER work item, responsibility, dependencies and requested effect
ENUMERATE registered applications $(r,m)$
EXCLUDE stale, unauthorized or prerequisite-unknown mutations
FORM $\mathcal A_{i,t}$ under declared resource limits
IF $\mathcal A_{i,t}$ is empty: RETURN blocking condition
SELECT $a_t\in\mathcal A_{i,t}$ by stated user choice or policy; RECORD its basis
DISPATCH artifact, bounded attention state or lifecycle candidate through the host
RETAIN actual effects in $\rho_t$
```

**Algorithm explanation.** Eligibility is established before preference or policy selects an action. An empty feasible set yields a specific blockage; dispatch then records the kind of result and its observed effects rather than equating selection with completion.
