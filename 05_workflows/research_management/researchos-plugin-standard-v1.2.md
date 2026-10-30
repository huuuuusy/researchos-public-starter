---
title: ResearchOS Plugin Standard v1.2
layer: workflow
status: active
sensitivity: public_safe
owner: researchos_core
last_reviewed: 2026-08-15
language: en
normative: true
semantic_version: 1.2.0
translation_pair: researchos-plugin-standard-v1.2.zh.md
---

# ResearchOS Plugin Standard v1.2

<!-- semantic-anchor: agent_summary -->
## Agent Summary

ResearchOS is not a container for accumulating downloaded plugins. It is a task-and-capability refinery and governance system. Plugins are either **task-led**, centered on one repeatable bounded user job, or **capability-led**, centered on a stable transformation shared across tasks. Stronger models should eliminate thin skills that repeat model-native knowledge or produce no measurable gain; they do not replace private knowledge, evidence gates, tool permissions, provenance, human confirmation, or long-horizon evolution. `researchos_plugin_task_v1` and `researchos_plugin_capability_v1` are non-installable governance prototypes. Every concrete plugin must state its marginal value over the current model or host baseline and satisfy authority, effects, data, lineage, routing, validation, and retirement obligations.

Core thesis: **stronger models reduce the need for brittle skill wrappers, not for governed capability systems**. Model progress raises the admission and retention threshold for plugins; it does not justify accumulating more of them.

<!-- semantic-anchor: layer_model -->
## 0. Five layers that must not be conflated

- An **agent skill** is the authoring format for reusable instructions, references, assets, or scripts loaded by ChatGPT/Codex when relevant.
- A **Codex/OpenAI plugin** is an external install and distribution package for one or more skills, MCP connections, and resources.
- An **agent harness** is the executable environment that coordinates model, context, tools, state, policy, traces, evaluation, and recovery into an observable episode.
- A **ResearchOS plugin** is an internally governed task or capability contribution and lifecycle unit. It may be inspired by a skill or distributed inside an external plugin, but it is not the same layer.
- **ResearchOS** is the long-horizon governance system that preserves capability evidence, researcher judgment, authority consequences, and rule evolution across episodes. It may invoke a skill, plugin, or harness, but is not reducible to any of them.

Skill/Codex is the daily operational surface for reading, structuring, drafting, validation, and writeback proposals. The Dashboard is the visual discovery surface for assets, relations, evidence, Inbox state, and handoff readiness. They share Markdown authority, confirmation, and validation rules; neither is subordinate to the other.

<!-- semantic-anchor: archetypes_and_lifecycle -->
## 1. Organization contracts and deployment

The organization prototypes belong to the core project, but are not user-facing plugins. `task_led` and `capability_led` are the current schema branches, with different binding and admission obligations. Plugin names form an open catalog; a new catalog entry need not introduce a new archetype. Adding an archetype requires a contract revision and evidence that the current branches cannot express the intended lifecycle. Every concrete plugin first declares an `archetype`:

| Archetype | Stable owner | Use when | Must not pretend |
|---|---|---|---|
| `task_led` | One repeated user job and its `task_contract` | There is one primary entrypoint with explicit inputs, outputs, confirmation gates, completion criteria, failure recovery, and stop rules | Do not invent a capability claim merely to package a task |
| `capability_led` | A cross-task `capability claim` | Several tasks share one conditional transformation that needs cross-episode evidence, composition, admission, and independent retirement | Do not inflate a task name into a capability |

Classification follows the product's center of gravity, not implementation complexity. A task-led plugin may contain rigorous scripts and gates, but still serves one user job. A capability-led plugin may project into several tasks, but its stable meaning does not depend on one entrypoint. Migration from task-led to capability-led requires an observed cross-task invariant and separate Review; repetition alone is not enough.

Every plugin also chooses one product placement:

- `foundation_projection`: broadly reused, embedded projection or foundation capability; it does not own conversation tasks.
- `bundled_capability`: a bounded private or public capability shipped with the OS.
- `optional_extension`: a local, reversible, disabled-by-default installation.

Product tier is the source of placement; the host derives deployment mode through a fixed mapping. Source manifests may omit `governance.deployment_mode`. An explicit legacy value is checked against the derived value and rejected if it conflicts; normalized output always retains the field. Compact sources require the updated host; an older host must receive the explicit derived value. This input relaxation does not change runtime lifecycle or waive source parity between the prototype in the technical report and the downloadable version. A foundation projection is `embedded_foundation`; a bundled capability is `bundled_default_on`; an optional extension is `local_installable`. The lifecycle UI must not imply that an embedded capability can be installed or removed by the local example installer.

Lifecycle is deployment-derived: foundation capabilities are `core_bundled` and retire only through `core_release_change`; bundled capabilities are `release_bundled` and retire through `release_change`; only local extensions use `manifest_present` / `remove_manifest`. Old v1 local manifests keep the legacy lifecycle through the conservative compatibility adapter.

A task-led plugin treats its `task_contract` as the stable unit. It declares the user job, inputs, outputs, invariants, confirmation gates, completion criteria, failure modes, recovery, model-baseline comparison, and retirement. It does not enter the capability registry or declare `capability_bindings` or `task_projections`. Its justification is not merely that a task exists, but that the same bounded task recurs and private procedure, execution discipline, or deterministic validation produces measurable gain over the current model alone.

A capability-led plugin still treats the capability claim as the stable unit. A capability claim owns meaning, evidence, admission, and retirement conditions; a plugin contribution owns implementation, permissions, assembly, and deployment lifecycle. A task is an entrypoint, workflow adapter, or evaluation probe that projects the capability into a particular situation. A capability is not a larger label pasted onto an existing task.

The identity chains remain separate:

- task-led: `task contract -> task contribution -> episode evidence -> task validation/adoption -> retirement`;
- capability-led: `canonical capability claim -> capability contribution -> task projection -> episode evidence -> capability admission receipt`.

Only capability-led plugins use canonical claims in `researchos-capability-registry-v1.json`. A task-led plugin must not create a same-name placeholder claim merely to satisfy validation. In both archetypes, a successful task, installation, enablement, harness execution, or green tests only contribute local evidence and cannot automatically advance maturity.

<!-- semantic-anchor: external_sources -->
## 2. External skills are sources, not packages to copy

External skills may enter a candidate ledger as links. ResearchOS can then:

1. keep a `reference_only` link;
2. transform one source into an `adapted_external` plugin;
3. combine two or more sources into a `composed_external` plugin;
4. after separate evidence and Review, absorb the resulting idea into a foundation capability or, exceptionally, the stable kernel.

There is deliberately no `raw_copy` reuse mode. An external source must declare HTTPS URL, pinned version or retrieval boundary, license, reuse mode, transformation summary, and whether runtime dependency remains. Source code and instructions stay with the upstream owner unless their license and a separate implementation decision justify vendoring.

Use `09_templates/external-capability-source-candidate.md` before any manifest exists. Searchable links enter `config/capability-sources.json`, which is a source-candidate ledger rather than an install list. Only promoted sources may enter adapted/composed manifests, and the manifest provenance snapshot must match the ledger.

Absorption is not installation. A skill-shaped source may disappear as an independent plugin when its validated invariant becomes a native OS capability. Stable-kernel absorption has the highest bar: repeated cross-capability need, local validation, human admission, explicit owner, compatibility plan, rollback, and Review. Convenience alone is not enough.

<!-- semantic-anchor: governance_card -->
## 3. One governance card, two branches

Every checked-in native plugin and task extension must explicitly declare `governance`:

1. `archetype`: explicit `task_led` or `capability_led`, never inferred from a filename or label.
2. `distribution`: universal, private, or public variant; exact, scoped, or private-only parity.
3. `lineage`: matching prototype, derivation, candidate sources, transformation, dependency, placement, and absorption target.
4. `deployment_mode`: what is actually embedded, bundled, or locally installable.
5. `effects`: research consequences allowed independently of code-host permissions.
6. `data_policy`: confidentiality and export policy as separate axes.
7. `composition`: contribution dependencies; optional integrations and conflicts use registered capability claims.
8. `routing`: typed `capability / task / core_route / workflow` handoffs.
9. `admission`: archetype-specific maturity, proof, review date, revalidation triggers, and retirement.
10. existing `validation`: executable commands and behavior tests.

Lineage and runtime dependency are separate. A native plugin has no external
source reuse and keeps `reuse_policy=native`, but it may still require a
user-operated runtime such as an MCP connector. That operational dependency does
not imply that external code was copied. Adapted or composed plugins still need
pinned sources, licenses, and transformation records.

Type branches:

- `task_led` requires one `task_contract` and forbids `capability_value`, `capability_bindings`, and `task_projections`; `composition.provides` contains only that task contribution.
- `capability_led` requires `capability_value`, `capability_bindings`, and `task_projections`; every contribution binds exactly once to claims and every task projects exactly once.

Host `permissions` still answer what code may read or execute. `effects` answer what the capability may do to research or workspace state. A declarative task can have no command permission yet still be allowed to propose a Review candidate or perform a recoverable workspace cleanup through an existing owner; that distinction must be explicit.

<!-- semantic-anchor: admission -->
## 4. Admission is not enablement

`enabled` only says whether the runtime loads a plugin. It proves neither task nor capability quality. Maturity depends on archetype:

- task-led: `draft -> instrumented -> task_validated -> user_adopted -> deprecated`
- capability-led: `candidate -> instrumented -> locally_validated -> human_admitted -> deprecated`

`instrumented` and higher require proof references. A task-led plugin reaches `user_adopted` only after `task_contract.comparison_status=evaluated` and real task evidence shows net gain over the current model. Capability-led `human_admitted` still requires an evaluated model/host baseline and one `researchos-plugin-admission-receipt-v1` per bound claim. Contract, authority, public-variant, dependency, model-baseline, or behavior changes trigger revalidation.

<!-- semantic-anchor: baseline_value -->
## 5. Task or capability value over the current model

Every plugin must answer: **what is lost if the current model or host performs the work without this task workflow or capability?**

Task-led plugins compare the whole workflow in `task_contract`; capability-led plugins compare the cross-task transformation in `capability_value`. Both separate expectation from evidence. Allowed deltas cover quality, reliability, evidence boundaries, authority safety, efficiency, recovery, and personal fit. Burdens cover context, trigger, maintenance, dependency, and privacy costs. `planned` is only a comparison plan; `evaluated` is required for adoption or admission; model, task, contract, or dependency changes make prior evidence `stale`.

- If the current model already performs reliably, do not create a skill.
- If a source is occasionally useful, keep only a reference.
- If one bounded user job repeatedly shows measurable gain, create a task-led plugin.
- If several tasks share one stable transformation with cross-episode evidence, create a capability-led plugin.
- If a rule becomes a cross-capability invariant, absorb it after Review and retire the plugin.
- If gain disappears or burden exceeds it, retire rather than preserve sunk cost.

<!-- semantic-anchor: composition -->
## 6. Composition without a plugin heap

A new source or task should not become a plugin merely because it is useful. First ask:

- Is this one repeatable task with a clear completion gate, or a transformation that remains stable across several tasks?
- Does an existing task-led plugin, capability-led plugin, or foundation owner already provide the needed result?
- Can it be one step in an existing task or an optional integration/transformation of an existing capability?
- Does it need its own route, lifecycle, or evidence boundary?
- Would two linked skills be better expressed as one composed capability?
- Is this only a new task projection of an existing capability, or a genuinely new reusable capability?
- Has repeated use shown that it should be absorbed into the OS instead?

The preferred result is the smallest number of task and capability plugins with the clearest owners. A task-led plugin does not become a capability merely because its implementation is complex; a capability-led plugin is not fragmented into one package per task. Composition dependencies remain machine-readable, and direct reads of another plugin's private state remain forbidden.

<!-- semantic-anchor: distribution_parity -->
## 7. Parity between the prototype and the downloadable version

The same `id@version` cannot silently mean different things. `exact` means semantic equality after JSON parsing. `scoped_variant` capabilities declare both sides and every allowed divergent field. Any other difference fails validation. `private_only` capabilities must not appear in the downloadable version's manifests, and its runtime source must not retain dormant implementations keyed by private capability IDs. This is a semantic distribution boundary, not by itself a claim of private-data leakage.

Scoped variants may have independent minor versions when the shared identity, API, bindings and failure boundaries remain equal. Cross-repository validation may record additional field differences in a reviewed contract: each field must carry a reason and exact value digests for both sides. A digest change invalidates that review; it never authorizes a new effect. The separate runtime and privacy gates remain mandatory.

<!-- semantic-anchor: required_gates -->
## 8. Required gates

Run:

```bash
python3 scripts/validate_plugin_standard.py
python3 scripts/validate_plugins.py
python3 scripts/validate_task_extensions.py
python3 -m unittest evals.test_plugin_governance
```

For a dual-repository release, add `--public-root <public-repository>`. The gate also checks archetype branches, task contracts or capability bindings, source-ledger consistency, external derivation modes, duplicate owners, typed handoffs, action effects, human admission receipts, manifest parity, and private symbols in the downloadable version's runtime source. A plugin is release-ready only after those boundaries, local behavior, negative tests, and rollback or uninstall behavior all pass.

<!-- semantic-anchor: open_questions -->
## Open questions

- Current capabilities still mark model/host comparison as `planned`; `locally_validated` must not be misread as proven research gain before longitudinal evidence exists.
- Which bundled capabilities are foundation invariants, and which should remain optional, must be decided by comparison evidence.
