---
title: Method Comparison plugin
sensitivity: public_safe
status: active
updated: 2026-09-11
---

<p align="right"><strong>English</strong> | <a href="README.zh.md">中文</a></p>

# Method Comparison: develop a plugin and connect a skill

## Purpose

A researcher wants to choose a tracking method for occluded targets, but the selected papers report continuously visible targets. This example returns a comparison with its conditions and missing evidence. It gives developers one complete task-led plugin and a reusable skill, connected through the existing ResearchOS task contract.

## Use and non-goals

Use it for a stated research decision and user-selected sources. The plugin defines when and how to arrange the task; the skill defines how to compare evidence. Neither ranks papers without a question or establishes a capability merely by being installed. A file-aware agent can use the method without a graphical client.

## Files and responsibilities

| File | Responsibility | What a developer changes |
| --- | --- | --- |
| [Complete descriptor](../../../config/extensions/method-comparison.example.json) | Task identity, version, scope, read plan, outputs and lifecycle | The repeated job and its interface |
| [Source skill](researchos-method-comparison/SKILL.md) | Comparison and revision method, independently usable by a compatible host | Method instructions and skill revision |
| [Adapter builder](build_adapter.py) | Projects this reviewed skill into ResearchOS Markdown | Only when the local format mapping changes |
| [Generated adapter](skill-adapter.md) | Public method text and source hash consumed by the read plan | Regenerate; do not edit directly |
| [Integration checks](../../../evals/test_method_comparison_example.py) | Adapter consistency, loading, lifecycle and failure cases | Observable requirements for a change |

The skill uses the [Agent Skills file format](https://agentskills.io/specification). ResearchOS's public read contract requires a top-level sensitivity field, which is not a standard skill field. The small adapter preserves the method body and adds ResearchOS metadata. There is one authored method; the second file is a reproducible projection. The manager registers a read-plan entry: it does not install a skill into another application's catalog or execute its instructions.

## Availability and parity

Version 1.1.0 is a `task_led`, `local_installable` contribution. The descriptors in this repository and in the prototype in the technical report differ in distribution scope. This repository accepts public-safe method documentation; this does not make a user's selected papers or results public. The example ships disabled. Existing installations change only through an explicit upgrade.

## Dependencies

Requires `researchos_core`, a file-aware execution host and Python 3 for the local adapter check. The builder uses the standard library. It reads one fixed skill file and writes one fixed adapter, without fetching packages or running the method. Asset navigation is optional. No new model, API credential, page or storage service is required.

## Lifecycle

From the repository root:

```bash
python3 docs/plugins/method-comparison/build_adapter.py --check
python3 scripts/manage_plugins.py install method_comparison
python3 scripts/plan_context.py method_comparison --lang en --mode standard --headless-json
```

If already installed at an earlier version, use `python3 scripts/manage_plugins.py upgrade method_comparison` explicitly. `install` and `enable` preserve an existing version. The manager validates the host and verifies the contribution; it does not need to launch or rebuild the dashboard when the headless host validator is available.

Give the plan to your agent with the question, selected source paths and desired result mode. For example:

> Use the method_comparison plan. Compare my two selected tracker reports for occluded targets. Preserve evaluation conditions and tell me what remains untested. Return an answer; do not modify the sources.

The plan's `read_now` includes `docs/plugins/method-comparison/skill-adapter.md`. The host checks its consistency, reads the method and works on the supplied sources. `plan_context.py` itself produces a plan, not a comparison. Retain the extension ID/version, method source hash, source versions and actual output with the result. Before resuming, run the returned `extension.resume_command`; a version mismatch or missing extension stops that route.

```bash
python3 scripts/manage_plugins.py disable method_comparison
python3 scripts/manage_plugins.py enable method_comparison
python3 scripts/manage_plugins.py uninstall method_comparison
```

Disable removes the active task contribution. Uninstall removes a managed local descriptor and its installation baseline, not the repository's skill or earlier research results. Customized manifests are protected from overwrite/deletion. Recovery restores configuration after validation failure; it is not a crash-safe multi-file transaction.

## Develop a method or a new plugin

For a different comparison strategy under the same job, edit the source skill, advance its `metadata.version`, rebuild the adapter and review the generated diff:

```bash
python3 docs/plugins/method-comparison/build_adapter.py --write
python3 docs/plugins/method-comparison/build_adapter.py --check
```

Then advance the descriptor version, run the checks below and explicitly upgrade the installed example. Recheck old evidence against the new method. The descriptor version identifies the contribution; the recorded skill hash identifies the actual method text. The current host's extension-version check alone does not lock every file the host might subsequently read.

Create a separate plugin when it owns a different recurring job, such as checking whether a manuscript claim is supported by its cited passage. Start from the complete descriptor and keep the existing schema and core authority fields. Change these groups together:

| Group | Fields to review |
| --- | --- |
| Identity and discovery | `id`, `version`, `task.aliases`, `governance.contract_id`, `governance.task_contract.task_id`, `governance.composition.provides`, `governance.routing.trigger_intents` |
| Task semantics | User job, inputs, outputs, invariants, completion, failure and recovery in `governance.task_contract` |
| Method and presentation | `task.read`, both `task.locales`, and the plugin-specific `documentation.readme` |
| Evidence and retirement | Comparison target/status, evidence references, admission proof references and retirement condition |
| Distribution and effects | Applicable runtime scope, source/derivation/license record, dependencies and declared effects |

Use a unique ID; do not shadow an existing route. Put the derivative descriptor at `config/extensions/<your-name>.example.json` and its README at `docs/plugins/<id-with-hyphens>/README.md`. Preserve the required README sections shown here. `quick` allows one entry file; `standard` up to five and `evidence` up to eight, with each tier retaining the preceding one. User source selection is a separate task input. Keep `researchos_core` as storage owner and `review` as the writeback route. Change content and assembly first; this example needs no branch in the dashboard, Inbox or core loader.

For an existing external skill, first inspect its instructions, scripts, dependencies, license and side effects. Preserve its source and revision in the contribution's lineage, then map its required inputs, preservation conditions, outputs and checks to the task contract. The supplied builder is specific to this already reviewed, text-only example; it is not a public-safety classifier for arbitrary skills. A skill requiring network access, native code or a different permission contract needs the corresponding host integration before execution. Leave it independent if the task cannot be mapped faithfully.

## Data, permissions, and export

The plugin defaults to an answer. An artifact uses the requested output location; a durable edit becomes an exact candidate for the existing review/admission path. A generated answer does not update a source card. No method instruction grants broader read, write or disclosure permission. This repository's handoff remains copy-only.

## Verification

```bash
python3 docs/plugins/method-comparison/build_adapter.py --check
python3 scripts/validate_task_extensions.py
python3 -m unittest evals.test_method_comparison_example evals.test_task_extensions evals.test_plugin_lifecycle
```

These integration tests use temporary repositories; they do not install the plugin in your daily configuration. They check source/adapter drift, the actual task loader and lifecycle, including a missing method file. They do not run an LLM or establish scientific quality. Keep the ordinary plugin-standard checks for a distributed derivative.

Try these fictional source bundles to inspect the method's behavior:

| Request and supplied observations | Expected distinction |
| --- | --- |
| Choose for occlusion; A = 0.82 and B = 0.79 are reported only for visible targets under the same protocol and higher-is-better metric | Preserve the reported visible-target ordering; leave the occlusion choice unresolved |
| Compare visible targets; both share the supplied protocol and higher-is-better metric, with A = 0.82 and B = 0.79; no uncertainty is reported | The reported difference is 0.03 in metric units; do not claim significance or transfer |
| A's report is corrected and no longer supports its earlier advantage | Revisit the dependent recommendation; retain independent conditions and the proposed occlusion test; do not infer B is superior |

These are constructed exercises, not measured runs or a benchmark. Missing question/source should trigger a targeted clarification or a narrower comparison. A document asking the agent to change unrelated cards must not change the user's task or the host's authority.

## Failure recovery

If the adapter check fails, stop this method and inspect the source revision; regenerate only from the intended version. If inputs are insufficient, return the gap and next check rather than invent evidence. If a source is corrected after a result, preserve the old result's grounds and record the reason for revision. An accepted candidate still needs the host's mutation and validation receipt before it counts as a retained change.

## Value and alternatives

The intended benefit is more inspectable, reusable comparison. Its advantage over the current model with the same sources remains unmeasured. Compare them on missing conditions, unsupported judgments, recovery and total effort; a well-scoped direct request may already suffice.

## Retirement

Retire or absorb the method when it adds no net benefit or duplicates a maintained workflow. Remove its active contribution while preserving source versions and the grounds of earlier results. Retiring a method does not delete the research it helped produce.

## Procedure and implementation

The pseudocode, control flow and implementation boundary for this function are given below. The bundled skill and deterministic adapter are executable reading-method examples. The scalar branch is a specification example: evidence comparability and qualitative comparison remain method judgments.

Symbols are plugin shorthand defined in the [plugin directory README](../README.md). The plugin system is frozen; see the [governance guide](../../governance-guide.en.md#task-extensions-and-plugins).

| Plugin, form and deployment | Core operator or constraint | Meaning, definitions and checks |
| --- | --- | --- |
| Method comparison (`method_comparison`); $\mathsf P_i^{\mathrm{task}}$, optional | $M_{ab}=\begin{cases}\operatorname{sgn}(\mu_a-\mu_b),&\gamma_{ab}=1,\\\bot,&\gamma_{ab}=0.\end{cases}$ | For a scalar comparison, $\mu_a,\mu_b$ are observed values oriented so larger is better. Set $\gamma_{ab}=1$ only with qualified evidence under the same conditions, metric and units. Otherwise $\bot$ withholds a ranking; other kinds of comparison need their own rule. |

### Method comparison

At least two selected sources, a comparison question and scalar observations when applicable; output: a conditional comparison and next check.

```pseudocode
// Pairwise signs do not establish a global ranking.
EXTRACT mechanisms, assumptions, evaluation conditions and observed results with source versions
FOR each pair $(a,b)$:
    CHECK evidence, conditions, metric and units for the proposed comparison
    IF scalar comparability and direction are established:
        SET $\gamma_{ab}=1$; SET $M_{ab}\leftarrow\operatorname{sgn}(\mu_a-\mu_b)$
    ELSE: SET $\gamma_{ab}=0$; SET $M_{ab}\leftarrow\bot$
RETURN applicability argument and smallest discriminating check
```

**Algorithm explanation.** Comparability is decided before a numerical sign is computed. The undefined marker preserves noncomparability; the final applicability argument and discriminating check explain what evidence would make the comparison useful.
