---
title: System Stewardship plugin
sensitivity: public_safe
status: active
---

<p align="right"><strong>English</strong> | <a href="README.zh.md">中文</a></p>

# System Stewardship

## Purpose

Owns governed system-evolution review, maintenance status, validation surfaces, and rollback-aware change proposals.

## Use and non-goals

Use it for architecture, maintenance, or governance changes. It does not approve its own changes, bypass Review, or turn diagnostics into canonical decisions.

## Availability and parity

Bundled private/public scoped variants share the same capability contract. Public Starter uses public-safe sources and omits private audit/reflection authority.

## Dependencies

Requires `researchos_core`; private audit/reflection integrations are optional and absent from the public variant.

## Lifecycle

Release-bundled and default-on. Updates must preserve the scoped-variant allowlist and pass cross-repository parity checks.

## Data, permissions, and export

Declarative with no network or direct canonical-write permission. Runtime projections are local-only; public outputs require the separate safe-release gate.

## Verification

Run the manifest commands/tests, `python3 scripts/validate_plugin_standard.py`, and for dual-repo work add `--public-root <public-repo>`.

## Failure recovery

On failed validation, keep the previous release active, retain the candidate diff, and use the declared rollback path before rebuilding projections.

## Value and alternatives

It makes system changes observable and reversible. Ad hoc maintenance is the alternative but lacks one explicit authority and rollback envelope.

## Retirement

Retire only when system evolution, release validation, and rollback have another admitted owner in both repository variants.

## Procedure and implementation

The pseudocode, control flow and implementation boundary for this function are given below. Registered maintenance actions and the shared admission owners provide bounded execution. Local plugin lifecycle tests cover version/customization checks and restoration, not crash-atomic multi-file updates or autonomous scientific self-improvement.

Symbols are plugin shorthand defined in the [plugin directory README](../README.md). The plugin system is frozen; see the [governance guide](../../governance-guide.en.md#task-extensions-and-plugins).

| Plugin, form and deployment | Core operator or constraint | Meaning, definitions and checks |
| --- | --- | --- |
| System evolution (`system_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, bundled | $\omega_{t+1}^u=\operatorname{Revise}_{\mathrm{adm}}(\omega_t^u,e_t^a,d_t)$ | Apply the existing admission operator using evidence and the decision of the researcher. The candidate includes trial and rollback grounds; execution receipts retain observed changes and failures. |

### Configuration evolution

A versioned configuration candidate, trial evidence and scoped decision $d_t$; output: observed effects and retention status.

```pseudocode
// A successful trial alone does not establish permission to retain the change.
BIND candidate to current configuration version, intended improvement and rollback basis
CHECK authorized trial scope and candidate prerequisites
IF unresolved: RETURN missing condition
RUN bounded trial through the host; RECORD actual effects, failed checks and recovery needs in $\rho_t$
RECHECK versions and the same candidate at retention; EVALUATE admission conditions
IF admission conditions hold: APPLY $\operatorname{Revise}_{\mathrm{adm}}$
ELSE: RETAIN failed or partial status; PERFORM only authorized recovery
```

**Algorithm explanation.** Trial authorization and retention authorization are checked at different moments. Rechecking the same candidate and versions before retention prevents a successful trial from admitting a changed proposal or concealing partial effects.
