---
type: workflow
title: "Cross-Domain Scientific Entry Workflow"
status: candidate
created: 2026-08-14
updated: 2026-08-14
tags:
  - cross-domain-research
  - human-ai-collaboration
  - scientific-entry
  - capability-admission
  - plugin
sensitivity: public_safe
exportable_to:
  - public_template
---

# Cross-Domain Scientific Entry Workflow

## Agent Summary

This workflow helps a researcher and AI enter an unfamiliar or partly familiar scientific domain without mistaking fluent search for valid discovery. It freezes one bounded case, builds the smallest adequate domain map, separates epistemic search roles, records candidate lineage, requires independent admission evidence, tests what the human and a fresh system retain, and settles the case without automatically promoting outputs into durable memory or public claims.

The workflow is a reusable capability kernel. The prototype in the technical report may instantiate it with owner-specific research history, judgment preferences, and private sources at runtime. Those inputs remain with the prototype's owner and are never copied into this plugin. The plugin contains only the procedure, templates, and authority boundaries; its practical power depends on the user's judgment, source quality, model capability, expert access, and execution discipline.

## What this plugin does

The plugin is designed for a bounded research-entry case, not for “learning an entire field” or repeatedly prompting until a famous problem appears solved. It supports three result modes already owned by ResearchOS:

- `answer`: give a bounded analysis or next-step judgment without saving it;
- `artifact`: produce a Case Pack for inspection;
- `writeback`: submit a candidate Case Pack through Review; the plugin never writes canonical memory directly.

It does not own storage, model providers, network access, expert authority, publication status, or release approval.

## Required inputs

Start only when the user can provide or approve:

1. the target domain and why entry is worth the cost;
2. a local phenomenon, proposition, mechanism, dataset, or design question;
3. the smallest relevant source set and its version or date boundary;
4. the accepted evidence form: proof, counterexample, experiment, executable check, behavioral study, or expert judgment;
5. the time, model, tool, and expert budget;
6. a named external admission route, or an explicit statement that none is currently available.

If the problem's open/closed status, definitions, or evidence obligation cannot be checked, stop at domain mapping. Do not start solution search.

## Capability loop

### 0. Select one admissible case

Generate at most three candidate cases. Compare them on:

- boundedness and six-month local-result plausibility;
- verifiability and availability of negative tests;
- representation richness across text, equations, diagrams, code, or experiments;
- density of plausible but wrong answers;
- availability and cost of domain feedback;
- learning value to the human researcher;
- privacy, consent, and disclosure burden.

Freeze one case. Mark the others `deferred`; do not silently run them in parallel.

### 1. Freeze the Case Charter

Record the exact object, question, known/unknown status, allowed claim strength, evidence obligation, tool boundary, cost budget, stopping rule, and external admission route. Treat proof, refutation, exact obstruction, and well-specified negative result as symmetric possible outcomes.

### 2. Build the minimum domain map

Create only enough structure to avoid solving the wrong problem:

- core objects and definitions;
- representation mappings and invariants;
- canonical examples and known counterexamples;
- major method families and documented failure modes;
- verification tools and domain evaluation standards;
- unresolved uncertainties, each tied to a source or an expert question.

AI fluency never closes an uncertainty by itself.

### 3. Run epistemically distinct search

Use roles with different evidence obligations, not decorative personas:

| Role | Required contribution |
|---|---|
| Encoding / reframing | Equivalent representations plus checks that the problem was preserved |
| Constructive | A proof, mechanism, algorithm, model, or experiment candidate |
| Counterexample / adversarial | Minimal attacks, boundary cases, circularity, or competing explanations |
| Formal / computational | Executable checks, formal subclaims, finite searches, or independent implementations |
| Historical / provenance | Nearby work, prior routes, priority, and novelty risks |
| Pedagogical / reconstruction | An explanation another person can reconstruct and interrogate |

Keep routes independent until each has exposed a real candidate, obstruction, or failure. More agents or more text are not evidence of diversity.

### 4. Maintain the Candidate Ledger

For every material candidate, record:

- candidate ID and parent lineage;
- exact claim and applicable scope;
- producing role, model/tool, and source dependencies;
- tests attempted and results;
- known gaps, counterevidence, and unresolved assumptions;
- human disposition: `accept`, `revise`, `reject`, or `defer`, with reason;
- time, calls, expert minutes, and other material costs.

Never delete failed routes merely to make the final path appear clean.

### 5. Issue an Admission Receipt

A candidate may advance only when the receipt distinguishes:

- `T+`: meaning-preserving transformations under which the result should remain stable;
- `T-`: minimal meaning-breaking transformations under which the result should change in the predicted direction;
- independent evidence: a fresh model, separate implementation, formal system, external dataset, or domain expert that adds genuinely different constraints;
- provenance and novelty status;
- cost- and coverage-matched comparison with the strongest practical baseline;
- residual uncertainty and calibrated abstention.

Formal verification checks a formalized object; it does not by itself prove that the object matches the original question, is novel, or matters to the domain. A second model's agreement is not independent evidence when it shares the same prompt, sources, or failure mode.

### 6. Test retention and transfer separately

Do not infer learning from collaborative performance.

- Human retention: before AI use, record the human's model and unknowns; later test unaided reconstruction, error diagnosis, delayed recall, and transfer to a nearby unseen case.
- System retention: use a fresh model instance and a frozen, inspectable Case Pack. If success requires the original conversation, label it `context-dependent assistance`, not system learning.
- Domain result: keep correctness, novelty, usefulness, and independent reproducibility separate from either human or system retention.

### 7. Settle the case

Produce a Case Settlement with four independent judgments:

1. domain result and admission state;
2. human retention and transfer state;
3. fresh-system retention and transfer state;
4. workflow value, cost, and failure modes.

Choose one next state: `close`, `revise`, `continue`, `defer`, or `promote for human review`. Promotion never means canonical acceptance or public release.

## Evidence ladder

| Level | Minimum evidence | Permitted claim |
|---|---|---|
| E0 instrumented case | Reconstructable charter, ledger, costs, failures, and gates | A replayable human–AI research case |
| E1 admission effect | Incremental admission value over a strong cost-matched baseline | A local method result about AI evaluation or search |
| E2 retention / transfer | Scaffold removal, delay, and unseen-task performance | Bounded evidence of human or system retention |
| E3 domain result | Independent domain review of correctness, novelty, and usefulness | A domain contribution with explicit scope |
| E4 cross-domain recurrence | Comparable evidence in at least two materially different domains | Preliminary evidence of a transferable entry capability |

One case must not be packaged as all five levels at once.

## Stop and rollback conditions

Stop, narrow, or roll back when:

- the question status or evidence obligation remains unverifiable;
- gains disappear after matching model calls, wall time, coverage, or expert labor;
- roles change wording but not candidates, tests, or decisions;
- transformations cannot be judged as semantically valid by the target domain;
- retention exists only inside the original chat;
- audit work costs more than the errors or recovery burden it prevents;
- private sources, people data, unpublished claims, or release authority would cross into a public artifact.

Rollback removes the installed task contribution and preserves the user's source materials and any separately reviewed canonical records. It does not rewrite or delete research history.

## Runtime boundary

The same capability kernel serves the prototype in the technical report and the downloadable version:

```text
public-safe workflow + public-safe Case Pack
        + user-supplied sources and constraints
        + host ResearchOS judgment and Review flow
        = one runtime instance
```

In the prototype in the technical report, owner-specific history and private evidence may improve selection and judgment, but remain private inputs. In the downloadable version, the user supplies their own sources and expertise. The plugin must never infer that the prototype owner's capability, identity, collaborators, or project facts transfer with the downloadable version.

## Output contract

Use the [Cross-Domain Scientific Entry Case Pack](../../09_templates/cross-domain-scientific-entry-case-pack.md). A complete artifact contains:

1. Case Charter;
2. Case Selection record;
3. Minimum Domain Map;
4. Approach Registry;
5. Candidate Ledger;
6. Admission Receipt;
7. Human/System Retention Report;
8. Transfer Report;
9. Case Settlement.

All judgments remain candidate-only until the named human or domain authority confirms them through the host system's Review route.
