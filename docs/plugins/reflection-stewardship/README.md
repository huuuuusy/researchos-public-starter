---
title: Reflection Stewardship plugin
sensitivity: public_safe
status: instrumented
---

<p align="right"><strong>English</strong> | <a href="README.zh.md">中文</a></p>

# Reflection Stewardship

## Purpose

Convert one supplied episode into a causal lesson, falsifiable gate, and one candidate owner.

## Use and non-goals

Use after a completed, failed, interrupted, or corrected episode when the user wants a causal lesson, changed rule, or executable gate. Ordinary project, fact, decision, or status writeback remains the Core `writeback / Review` path; the word “distill” alone does not turn it into reflection. This capability does not create parallel memory or admit rules.

## Availability and parity

This is the side of a reviewed scoped variant that ships in this repository. It shares capability identity, version, causal/non-goal semantics, and the Review boundary with the prototype in the technical report, but requires an explicitly supplied episode receipt and remains copy-only or candidate-only. It never receives private episode evidence, longitudinal judgment, paths, runtime state, or canonical-write authority.

## Dependencies

Requires the declarative core and routes durable candidates only to Review. Private audit or alignment integrations are not dependencies of this repository.

## Lifecycle

Release-bundled and default-on; disablement leaves ordinary post-task review available. Updates must preserve the scoped-variant allowlist and pass cross-repository parity validation.

## Data, permissions, and export

No network, command, state, or canonical-write permission. A public `writeback` result is only a copyable or Review candidate; it is not proof that a personal vault changed.

## Verification

Run `python3 scripts/validate_plugins.py` and the public capability alignment tests.

## Failure recovery

If cause cannot be separated from chronology, return the uncertainty and do not propose a durable rule. If the request only asks to record content, route it back to plain writeback instead of inventing a causal chain.

## Value and alternatives

Retain only if bounded reflection yields reusable gates without accumulating artifacts.

## Retirement

Retire after the useful invariant is absorbed by its stable owner.

## Procedure and implementation

The pseudocode, control flow and implementation boundary for this function are given below. The reflection method and its contract checks are present. It proposes a causal lesson; it neither estimates a causal effect from one episode nor writes the configuration autonomously.

Symbols are plugin shorthand defined in the [plugin directory README](../README.md). The plugin system is frozen; see the [governance guide](../../governance-guide.en.md#task-extensions-and-plugins).

| Plugin, form and deployment | Core operator or constraint | Meaning, definitions and checks |
| --- | --- | --- |
| Episode reflection (`reflection_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, bundled | $\widetilde\omega_t^u=\omega_t^u[r\mapsto r^{\prime}]$ | Replace one rule entry while preserving other configuration entries. The candidate must be grounded in an episode and counterexamples, with a proposed check. Retaining it requires a separate admission step. |

### Episode-based method revision

A bounded episode and current $\omega_t^u$; output: a candidate rule change with causal grounds and a test.

```pseudocode
// The proposed rule is a candidate, not an already retained configuration change.
RECOVER intended action, observed outcome and evidence limits
IDENTIFY possible cause and missed signal; CHECK a competing explanation or counterexample
IF no new causal lesson is warranted: RETURN no rule change
IF evidence is insufficient: RETAIN only a purpose-relevant unresolved question; RETURN no rule change
CONSTRUCT $r^{\prime}$ with an executable gate and one responsible owner
SET $\widetilde\omega_t^u\leftarrow\omega_t^u[r\mapsto r^{\prime}]$
RETURN candidate and test through the existing configuration-admission route
```

**Algorithm explanation.** Reflection tests the causal interpretation before proposing a reusable rule. The output couples a candidate change with a test and owner; the normal configuration-admission process decides whether to retain it.
