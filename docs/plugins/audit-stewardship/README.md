---
title: Audit Stewardship plugin
sensitivity: public_safe
status: instrumented
---

<p align="right"><strong>English</strong> | <a href="README.zh.md">中文</a></p>

# Audit Stewardship

## Purpose

Audit one bounded claim or transition with evidence, counterevidence, and a reversible repair candidate.

## Use and non-goals

Use with an exact baseline and scope. It does not perform irreversible cleanup or admit its own findings.

## Availability and parity

The public variant operates only on public-safe or explicitly selected local sources.

## Dependencies

Requires the declarative core; reflection and system evolution are optional handoffs.

## Lifecycle

Release-bundled and default-on; direct read-only inspection remains the fallback.

## Data, permissions, and export

No network, command, state, or canonical-write permission; all repairs remain Review candidates.

## Verification

Run `python3 scripts/validate_plugins.py` and the public capability alignment tests.

## Failure recovery

Stop on unclear authority, retain the baseline, and return the smallest reproducible finding.

## Value and alternatives

Retain only if the bounded audit catches consequential errors beyond ordinary review.

## Retirement

Retire when the invariant is absorbed by a smaller stable owner.

## Procedure and implementation

The pseudocode, control flow and implementation boundary for this function are given below. The audit route and validation scripts implement bounded contracts and technical checks. Scientific evidence appraisal is supplied by the auditor; the three-way partition does not determine it automatically.

Symbols are plugin shorthand defined in the [plugin directory README](../README.md). The plugin system is frozen; see the [governance guide](../../governance-guide.en.md#task-extensions-and-plugins).

| Plugin, form and deployment | Core operator or constraint | Meaning, definitions and checks |
| --- | --- | --- |
| Research and system audit (`audit_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, bundled | $D_t^b(j)=\{\chi\in D(j):s_{\chi,t}(\rho)=b\}$; $b\in\{1,0,?\}$ | Partition the checks in the check set $D(j)$ of requirement $j$ by their receipt-based assessments: satisfied, unsatisfied or unknown. Unsatisfied and unknown checks require different dispositions; repairing either still requires a new check. |

### Bounded audit

An audit question, the check set $D(j)$ and a bound receipt $\rho$; output: satisfied, unmet and unknown checks with grounds.

```pseudocode
// Missing, stale or ambiguous evidence yields unknown unless failure is established.
FREEZE audit question, source scope, target versions and success criteria
FOR each $\chi\in D(j)$:
    INSPECT supporting and contrary evidence for the same bound attempt
    ASSIGN $s_{\chi,t}(\rho)\in\{1,0,?\}$ from the evidence
PARTITION $D(j)$ into $D_t^1(j),D_t^0(j),D_t^?(j)$; RETAIN grounds and next checks
IF repair is authorized:
    DISPATCH a separately bound application
    RE-AUDIT its receipt before closing the finding
```

**Algorithm explanation.** Three-valued assessment distinguishes an established failure from a lack of evidence. Repair creates a new bound attempt whose receipt must be audited, preserving the distinction between intending a correction and verifying it.
