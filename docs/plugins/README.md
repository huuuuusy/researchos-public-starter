---
title: ResearchOS plugin documentation contract
sensitivity: public_safe
status: active
---

<p align="right"><strong>English</strong> | <a href="README.zh.md">中文</a></p>

# ResearchOS plugin README contract

## Mathematical forms and existing plugins

The notation below interprets the current [Plugin Standard](../../05_workflows/research_management/researchos-plugin-standard-v1.2.md) using the mathematical grammar in the [technical report](../technical-report.en.md). Most of the symbols below are plugin shorthand that the current report does not define; for plugins, this page and each plugin's README are their reference.

The existing system already contains task-led and capability-led plugins. Their mathematical forms distinguish a method from the contribution that makes it available. Let $\mathsf S$ denote a versioned skill and $i$ a versioned plugin. In the table, $\mathcal C_i$ is the set of implementation contributions declared by a plugin; a contribution may use skills, workflows, code or projections. $\mathsf{Gov}_i$ records identity, dependencies, routing, effects, data boundaries, admission and deployment. These are structured records, not capability scores. A skill reference can be written $\mathsf S\in\operatorname{methods}(c)$ for $c\in\mathcal C_i$: contributions can reuse a skill, and one contribution can use several methods.

| Object | Mathematical form | Meaning and existing example |
| --- | --- | --- |
| Skill | $\mathsf S=(\mathcal R_{\mathsf S}^{\mathrm{skill}},\eta_{\mathsf S})$ | A reusable method: rules, with control over their application. The method-comparison skill checks conditions and revisits affected judgments. |
| Task-led plugin | $\mathsf P_i^{\mathrm{task}}=(\mathsf T_i,\mathcal C_i,\mathsf{Gov}_i)$ | One recurring task contract $\mathsf T_i$, its implementation and governance. `method_comparison` and `codex_thread_handoff` use this form without creating capability claims. |
| Capability-led plugin | $\mathsf P_i^{\mathrm{cap}}=(\mathcal C_i,B_i,Q_i,\mathsf{Gov}_i)$ | Contributions bind to existing claims $\mathrm{Cap}_k$ through $B_i$; $Q_i$ projects them into tasks. `system_stewardship` binds to `self_evolution` and exposes `system_evolution_review`. |

The skill control relation $\eta_{\mathsf S}(H_t^a,L_t,e_t^a,\kappa)$ specifies allowed next choices: a rule $r\in\mathcal R_{\mathsf S}^{\mathrm{skill}}$ and binding $m$, an inquiry, or stopping. It can express branching and retries, rather than only a fixed list of steps. A selected application must satisfy $\operatorname{Pre}_r$ and be assessed by $\operatorname{Check}_r$; its actual output and effects remain $y_t$ and $\rho_t$. The task contract $\mathsf T_i$ specifies admissible purposes, input and output requirements, preservation, completion and recovery. One task episode may involve several rule applications and methods. Calling an existing capability does not by itself change a task-led plugin's organizing contract.

For a capability-led plugin, $B_i$ relates each contribution in $\mathcal C_i$ to one or more registered claims $\mathrm{Cap}_k$ defined in Supplementary Note 3 (capability claims and evidence). If $\mathcal T_i$ is its set of declared tasks, $Q_i$ contains triples $(\mathsf T,c,\mathrm{Cap}_k)$ with $\mathsf T\in\mathcal T_i$ and $c\in\mathcal C_i$. Every declared task has exactly one such projection, and $(c,\mathrm{Cap}_k)\in B_i$ must hold. These relations interpret `capability_bindings` and `task_projections`: several tasks may exercise one capability, and one contribution may bind to several claims. A projection-only contribution can have $\mathcal T_i=\varnothing$. The claim retains its own subject, conditions and evidence; neither the plugin nor a skill substitutes for that record.

Deployment is another choice recorded in $\mathsf{Gov}_i$. The table lists all twelve plugins in the public reference catalog: three foundation plugins, six release-bundled plugins and three optional extensions. The plugin manifests in `config/plugins/` declare their `product_tier` as `foundation_projection` or `bundled_capability`, and task-extension installs normalize to `optional_extension`. Governance records them as the deployment modes `embedded_foundation`, `bundled_default_on` and `local_installable`; only the last uses the local example installer. The catalog includes uninstalled examples and does not establish which plugins are enabled on a particular machine.

The table expresses plugin functions through selection, graph projection, difference, rule replacement and state recurrence. Each operates under purpose $\kappa$ and its evidence conditions; a plugin can organize several such rule applications.

Alongside computable structural operations, source resolution $\sigma_t$ and semantic checks $\operatorname{assert}$ and $\operatorname{supp}_{\kappa}$ remain implementation obligations. Their constraints identify what to evaluate without supplying a general semantic decision procedure.

| Plugin, form and deployment | Core operator or constraint | Meaning, definitions and checks |
| --- | --- | --- |
| Material intake (`material_pipeline`); $\mathsf P_i^{\mathrm{cap}}$, foundation | $\forall v\in V(\Delta_t):\ \sigma_t(v)\ne\varnothing$ | $V(\Delta_t)$ contains the candidate material objects; $\sigma_t(v)$ records their source references and versions. Require resolvable provenance for each object; registration does not establish understanding. |
| Asset navigation and composition (`research_assets`); $\mathsf P_i^{\mathrm{cap}}$, foundation | $y_t=\mathcal G_t^a[W_t]$; $\mathcal G_t^{+}=\mathcal G_t$ | For graph navigation, $\mathcal G_t^a$ retains permitted fields and relations, and $W_t$ selects its vertices. The induced subgraph preserves relations among those vertices. Grouping and dissolution instead produce $\Delta_t$ for review. |
| Portfolio attention (`research_portfolio`); $\mathsf P_i^{\mathrm{cap}}$, foundation | $a_t=(r,m)\in\mathcal A_{i,t}$ | For the selected plugin, $\mathcal A_{i,t}$ contains applications allowed by current inputs, prerequisites, authority and resources. Select a portfolio action within this set; membership specifies no optimal ranking. |
| Context routing (`research_context`); $\mathsf P_i^{\mathrm{cap}}$, bundled | $Z_t=D_{\omega_t^u}(H_t^a,q_t)$; $\widehat R_t=C_{\omega_t^u}(Z_t,q_t)$ | Reuse context selection and state reconstruction from Section 3.1 of the report. The result is $\widehat R_t$, whose questions, evidence, judgments, unresolved conditions and next steps must remain recoverable. |
| Research expression (`research_expression`); $\mathsf P_i^{\mathrm{cap}}$, bundled | $\operatorname{assert}(y_t)\subseteq\operatorname{supp}_{\kappa}(E_t)$ | $\operatorname{assert}$ extracts the factual assertions of an artifact; $\operatorname{supp}_{\kappa}$ contains those supported by evidence for the stated purpose and scope. Inclusion constrains expression; hypotheses and plans remain qualified. |
| Collaborative alignment (`alignment_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, bundled | $\mathcal B_t^{\mathrm{align}}=\mathcal M_t^{\mathrm{OS}}\triangle\mathcal M_t^{u,\mathrm{stated}}$ | Compare OS working assumptions with assumptions explicitly stated by the user, under common proposition identities and scope. Symmetric difference locates clarification needs, including omissions; it neither reads internal human state nor decides who is right. |
| Research and system audit (`audit_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, bundled | $D_t^b(j)=\{\chi\in D(j):s_{\chi,t}(\rho)=b\}$; $b\in\{1,0,?\}$ | Partition the checks in the check set $D(j)$ of requirement $j$ by their receipt-based assessments: satisfied, unsatisfied or unknown. Unsatisfied and unknown checks require different dispositions; repairing either still requires a new check. |
| Episode reflection (`reflection_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, bundled | $\widetilde\omega_t^u=\omega_t^u[r\mapsto r^{\prime}]$ | Replace one rule entry while preserving other configuration entries. The candidate must be grounded in an episode and counterexamples, with a proposed check. Retaining it requires a separate admission step. |
| System evolution (`system_stewardship`); $\mathsf P_i^{\mathrm{cap}}$, bundled | $\omega_{t+1}^u=\operatorname{Revise}_{\mathrm{adm}}(\omega_t^u,e_t^a,d_t)$ | Apply the existing admission operator using evidence and the decision of the researcher. The candidate includes trial and rollback grounds; execution receipts retain observed changes and failures. |
| Method comparison (`method_comparison`); $\mathsf P_i^{\mathrm{task}}$, optional | $M_{ab}=\begin{cases}\operatorname{sgn}(\mu_a-\mu_b),&\gamma_{ab}=1,\\\bot,&\gamma_{ab}=0.\end{cases}$ | For a scalar comparison, $\mu_a,\mu_b$ are observed values oriented so larger is better. Set $\gamma_{ab}=1$ only with qualified evidence under the same conditions, metric and units. Otherwise $\bot$ withholds a ranking; other kinds of comparison need their own rule. |
| Task handoff (`codex_thread_handoff`); $\mathsf P_i^{\mathrm{task}}$, optional | $H_{t,h}^a:=H_t^a\vert_h$; $Z_t=D_{\omega_t^u}(H_{t,h}^a,q_t)$ | Restrict permitted history to task $h$, then select continuation context. The connector and receipt record access, redaction and truncation; unrelated task history is excluded. |
| Cross-domain scientific entry (`cross_domain_scientific_entry`); $\mathsf P_i^{\mathrm{cap}}$, optional | $\mathcal U_{t+1}=(\mathcal U_t\cup\mathcal F_t)\setminus(\mathcal Z_t^{\mathrm{res}}\cup\mathcal Z_t^{\mathrm{cancel}})$ | Within one frozen case, carry unresolved obligations forward, add affected requirements, and remove only checked resolutions or authorized cancellations. Domain admission, learning and retention remain distinct obligations. |

A foundation placement does not make every contributed action a pure view: portfolio actions also have declared effects. The state-preservation condition for pure views in Supplementary Note 3 (feedback, views and repository maintenance) applies to pure view operations. Public and private variants can expose different task sets under the same declared contribution, so the table describes their organizing form rather than identical runtime coverage. The host checks descriptor structure and references; it does not yet derive or prove the full rule and control semantics of arbitrary skill text. These forms provide a common specification against which a concrete integration can be examined.

The [method-comparison development guide](method-comparison/README.md) supplies the complete task-led example and skill. For a native capability-led structure, inspect [system stewardship](../../config/plugins/system-stewardship.json); for an installable capability-led structure, inspect [cross-domain scientific entry](../../config/extensions/cross-domain-scientific-entry.example.json). The abstract prototypes are specifications rather than installable packages.

## README obligations

Every checked-in plugin and task extension owns one README at
`docs/plugins/<id-with-hyphens>/README.md` (the plugin id with `_` replaced by
`-`). The manifest's `documentation.readme`
field must point to that exact file. The loader rejects missing, escaping,
symlinked, or structurally incomplete documentation.

A README is part of the plugin contract, not marketing copy. It must let a user
answer four questions before enabling anything: what job the plugin owns, what
it cannot do, which data and permissions cross its boundary, and how to verify
or recover the installation.

## Required sections

Use these exact level-two headings:

1. `Purpose`
2. `Use and non-goals`
3. `Availability and parity`
4. `Dependencies`
5. `Lifecycle`
6. `Data, permissions, and export`
7. `Verification`
8. `Failure recovery`
9. `Value and alternatives`
10. `Retirement`

The content must describe the actual manifest and runtime. A public README must
never contain private paths, domains, tokens, thread IDs, people, projects, or
claims that private data ships with the plugin.

## Lifecycle language

Foundation and release-bundled capabilities are changed only through a reviewed
ResearchOS release. `local_installable` examples use `scripts/manage_plugins.py`
and install only a reviewed manifest into a Git-ignored local directory. That
operation is local and reversible; it does not download code, contact a service,
or write canonical memory.

## External providers

If a plugin depends on an MCP server or another provider, report its readiness
states separately, as defined for
[Thread Handoff](codex-thread-handoff/README.md#availability-and-parity). A
manifest cannot claim runtime access merely because its README describes a
connector. Provider credentials and endpoints stay outside the manifest.

## Procedures and implementation

The table above gives the twelve functional forms; each plugin's README gives their inputs, pseudocode, control flow and implementation boundaries. Structural host checks are distinguished from evidence-interpretation steps. Headless portfolio queries and runtime loading share manifest validation; local lifecycle writes and restoration use exclusive temporary files. These are implementation details of bounded scope, not automated scientific judgment.
