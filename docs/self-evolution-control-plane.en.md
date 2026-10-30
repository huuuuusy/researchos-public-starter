---
type: governance
title: "Controlled Self-Evolution Control Plane"
status: active
updated: 2026-08-04
sensitivity: public
---

<p align="right">
  <strong>English</strong> | <a href="self-evolution-control-plane.zh.md">中文</a>
</p>

# Controlled Self-Evolution Control Plane

## Agent Summary

ResearchOS scales through controlled maintenance, not autonomous self-modification. It may detect changed repository paths, calculate the affected fixed maintenance steps, run read-only checks, and—only after a plan-specific confirmation in personal-vault mode—refresh reproducible projections. It must never automatically change source knowledge, judgment, code, schemas, providers, public exports, Git state, or external systems. The public demo remains read-only and never searches for another private repository, private provider, or private runtime state.

## Why This Exists

As materials, relationships, tasks, and projections grow, rebuilding everything after every change becomes slow and hard to trust. Unbounded automation is worse: it can amplify one wrong inference across many files. The control plane therefore automates impact analysis and validation while preserving human authority.

```text
change signal
  -> path-only detector
  -> dependency planner
  -> candidate plan
  -> policy gate
  -> fixed-step runner
  -> validation
  -> local checkpoint or unchanged authority
```

## Three Different Operations

| Operation | Meaning | Default authority |
| --- | --- | --- |
| Derived refresh | Rebuild a generated demo, local projection, or other reproducible output. | Reproducible, never canonical. |
| Evolution diagnosis | Identify maintenance pressure or a possible system improvement. | Candidate only. |
| Governance change | Change code, schema, routing, provider, durable memory, export, or external state. | Explicit human confirmation only. |

Calling a change a “refresh” does not grant it governance authority.

## Risk Tiers

- **E0 Observe:** path detection, impact planning, and read-only checks; no writes.
- **E1 Derived refresh:** a fixed, local, reproducible write after exact-plan confirmation.
- **E2 Candidate writeback:** a proposal routed through the existing Review flow; never promoted automatically.
- **E3 Canonical change:** source knowledge, judgment, or durable workflow changes; always manual.
- **E4 System or external change:** code, schema, provider, public release, Git, network, or other external action; always manual.

An “automatic maintenance” preference can never authorize E3 or E4. Confirmation applies only to the displayed plan ID; when the change token or a carried-candidate source changes, the old confirmation is refused. Risk reflects the highest boundary actually touched, and the manifest must truthfully declare each write owner.

The checkpoint records the post-execution change token, so generated outputs do not trigger the same safe refresh again. If a safe subset finishes while manual work remains, the checkpoint keeps a manual-only pending candidate and disables another safe run. Later unrelated changes carry that candidate forward rather than silently replacing it. In personal-vault mode, “Keep for later” suppresses repeated prompts for the same change token but retains the candidate for later changes; only an exact “Reject candidate” decision clears it. The public demo remains read-only.

Before each E1 run, the runner snapshots only the derived write owners declared by the manifest. If a required step fails and write attribution is unavailable, changed targets are preserved and the snapshot plus recovery manifest is retained for reconciliation; unchanged targets require no rewrite. Escaping or symlinked write targets are rejected before any command runs. Failed selected prerequisites block their dependents; independent selected work may continue. Direct subsets never start omitted prerequisites. Git remains the rollback owner for code, schema, and reviewed documents.

## Fixed-Step Contract

Every maintenance step declares its path triggers, dependencies, allowed writes, validations, execution policy, and cost. The runner accepts only versioned step IDs from `scripts/researchos_data/maintenance_pipeline.py`; it does not accept arbitrary shell commands.

Plans show at most 40 paths. More than 200 changed paths, at least 25% of tracked Markdown, or a control-contract change escalates to a full-review candidate. Network and expensive semantic work never run from startup or a safe-refresh confirmation.

## Repository and Personal Modes

- **Public demo:** shows a public-repository-only change plan. The refresh action is disabled and all write endpoints remain blocked.
- **Personal vault:** may run only this repository's own confirmed fixed safe steps. Its checkpoint and local projection are Git-ignored.
- **Never:** locate a sibling private repository, discover private providers, read raw private material, or copy private paths/checkpoints/logs into this repository.

The protocol can be shared with a private installation; runtime state and source sets are never shared.

## User Surface

No new chat or page is added. Advanced Maintenance shows one folded task object: why the plan exists, affected paths, executable steps, manual candidates, safe writes, blocked actions, and validation results. A deeper diagnosis uses the existing Work Session and Review flow through the `system_evolution_review` task of the bundled `system_stewardship` capability.

## V1 Boundary and Promotion Evidence

V1 deliberately has no background daemon, model-authored code changes, automatic durable writeback, automatic public sync, or automatic Git/network action. Opt-in scheduled E1 refresh should be considered only after at least 20 real plans show no missed dependencies, atomic failure behavior, manageable review load, sustained public-safety checks, and a material reduction in maintenance time.

Stop automation whenever a write owner is unclear, a plan becomes stale, validation fails, public and personal sources mix, or maintenance work begins to displace research work.

## Validation

```bash
python3 scripts/validate_evolution_control.py
python3 scripts/plan_evolution.py --changed dashboard/app.js
python3 -m unittest evals.test_evolution_control
python3 scripts/validate_public_safety.py
```
