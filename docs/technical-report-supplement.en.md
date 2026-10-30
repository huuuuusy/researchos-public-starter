---
type: technical_report_supplement
title: "ReSearchOS Technical Report: Supplementary Material"
author_email: "shiyu.hu@ntu.edu.sg"
author_affiliation: "School of Physical and Mathematical Sciences, Nanyang Technological University, Singapore"
updated: 2026-10-30
sensitivity: public
landscape_checked: 2026-10-29
include_in_pdf: false
---

[中文](technical-report-supplement.zh.md)

# ReSearchOS Technical Report: Supplementary Material

## Agent Summary

Read the note for the question at hand. Note 1 gives the sources and examples behind the four design principles of report Section 3, together with the conditions for closing work and delivering context. Note 2 gives the session commands, record structures and responsibilities behind report Sections 2 and 5. Note 3 restates the canonical provisions with their owners and gives the contracts for capability claims, extensions, views and repository maintenance. Note 4 gives the research foundations behind the comparison in report Section 6.1. Note 5 states every definition precisely and argues the two propositions that report Section 4.4 states in words. Note 6 lists all 39 implementation gaps that report Section 5.4 groups by theme.

This material accompanies [the technical report](technical-report.en.md) and is not part of its PDF; Chinese is the primary text and this English version follows it. Apart from Notes 1, 2, 5 and 6, which hold material moved out of the report (literature behind the principles, implementation detail, the precise definitions with the arguments for the two propositions, and the list of gaps), the supplement adds no claim and no implementation acceptance beyond the report. Section, figure, table and appendix numbers refer to the report; only Note 5 numbers its own definitions and equations, as 5.1–5.21. Soul Contract, Product Manifesto, Primitive Rule Model and Product Design are internal canonical documents and are not published; a mark such as §3 identifies the provision cited. Kernel section numbers refer to the internal kernel and extension architecture, which is likewise not published.

## Supplementary Note 1. Principle sources and examples

The report states each principle of Section 3 in one paragraph. This note gives the source discussion behind each, then an example of when a piece of work counts as finished, and the conditions for closing work and delivering context that gaps 4–6 of Note 6 cite.

The principles grew out of the author's own design history, whose first request, recorded on its first day, already drew a line between understanding a research judgment and imitating wording. The rules themselves are written in six of the author's internal design documents, where each rule has a single owner and a frozen contract ties it to the test that checks it.

### Only the researcher turns a candidate into state

**Division of roles.** Models explain accessible material and propose candidates; researchers assess sufficiency, worthwhile questions and changes of direction. Both rely on evidence about the research object; human acceptance does not remove later checks. Decisions retain grounds and scope: the QOC notation [Questions, Options, and Criteria](https://doi.org/10.1207/s15327051hci0603&4_2) records questions, options and criteria, such as preferring reproducibility to a small accuracy difference; decision-provenance tracing [Decision Provenance](https://doi.org/10.1109/ACCESS.2018.2887201) traces inputs, decisions and effects, separating why a choice was accepted from what followed.

**When review is required.** Before retaining recommendations, widening scope or sharing with new recipients, the system must identify the targets, grounds, effects and recovery paths. Routine organization can continue within existing authorization. Overreliance and interaction burdens in the tasks studied by cognitive-forcing research [To Trust or to Think](https://doi.org/10.1145/3449287) motivate selective review, as do accountability and safety in trustworthy AI for education [Trustworthy AI in education](https://doi.org/10.1142/S2737599425500264). Neither establishes an optimal approval frequency. Authority to revise a research judgment does not authorize changing who may accept it.

**Sufficient understanding.** Clark and Brennan's account of grounding [Grounding in communication](https://doi.org/10.1037/10096-006) motivates understanding sufficient for the purpose: a concrete interpretation, output or counterexample can distinguish comparing reproducibility from ranking performance. Repeated confirmation is less useful. This account assumes no human-like mutual beliefs on the part of the model, and agreement does not establish scientific correctness.

Of the work this principle draws on, three lines stand out. Cognitive-forcing research [To Trust or to Think](https://doi.org/10.1145/3449287) shows that accepting output unselectively invites overreliance. Clark and Brennan's account of grounding [Grounding in communication](https://doi.org/10.1037/10096-006) sets the standard of understanding at what the purpose needs, rather than at confirming again and again. As in the QOC notation, which records questions, options and criteria [Questions, Options, and Criteria](https://doi.org/10.1207/s15327051hci0603&4_2), a decision is kept with its grounds and scope: in choosing a method, for instance, what is kept is why reproducibility mattered more than a small reported difference in accuracy. Acceptance belongs to the researcher rather than to the AI model that made the proposal, which is why review comes before a recommendation is retained, a scope widens or material reaches new recipients, and the authority to revise a judgment stops short of changing who may accept it.

### A successor runs only on an established result

**Stopping decomposition.** Decomposition identifies the decisive unknowns and the checks needed to address them, then asks what action the results jointly support. Further decomposition stops when it no longer changes that judgment: a method comparison checks evaluation conditions, metrics and the reasons for differences, and a research email separates known facts, commitments not yet made and intended recipients. Domain understanding identifies scientific bottlenecks, while organization coordinates work across them. Simon's bounded rationality [A Behavioral Model of Rational Choice](https://doi.org/10.2307/1884852) motivates defensible decisions with manageable evidence. Malone and Crowston's coordination theory [The Interdisciplinary Study of Coordination](https://ccs.mit.edu/papers/CCSWP157.html) treats coordination as managing dependencies among activities; this report turns that view into three requirements: prior agreement, independently feasible work and triggers for revising the division. Search may change an experimental hypothesis or reveal a construct problem, and assigning work to different executors does not make it independent.

**Delegation.** Delegating execution leaves the researcher responsible for synthesizing results, recognizing bottlenecks and seeking expertise, without making a technical career background a universal qualification for leadership. Human collaborators retain agency, accountability and learning needs. Team-formation work [Finding a team of experts](https://cs-people.bu.edu/evimaria/cs591/lappas09finding.pdf) supplies a communication-cost baseline when requirements and skills are known; unknown experience, availability and willingness, and question revision, remain explicit. Prior collaboration supplies a lead for inquiry; it neither establishes suitability nor authorizes assignment.

**Revising a division of work.** Agreement under a shared contested assumption is not independent confirmation. A changed question requires plan review; retaining why a decomposition worked or failed permits revision or retirement after models or harnesses change. Argyris's single-loop and double-loop models [Single-Loop and Double-Loop Models](https://doi.org/10.2307/2391848) separate correcting actions from reconsidering guiding assumptions. When conditions are omitted repeatedly, a method that only asks for a ranking should be checked, and the grounds linking each failure to a revision of tasks, criteria or roles retained. Methods, checks and the division of work can be revised, while changes to governance still require separate review. Composition retains conditions, unknowns and failure results. Matching fields enables information transfer, but does not establish scientific validity or permission for subsequent use.

Independence is a separate matter. Handing a literature search and an experiment to different executors does not make them independent, because the search may change the hypothesis or show that the experiment measures the wrong construct. Decomposition therefore looks for the decisive unknowns and their checks, asks what the results jointly support, and stops when dividing further no longer changes that judgment.

Stopping there is Simon's bounded rationality [A Behavioral Model of Rational Choice](https://doi.org/10.2307/1884852) applied to the evidence a researcher can manage. Coordination theory [The Interdisciplinary Study of Coordination](https://ccs.mit.edu/papers/CCSWP157.html) treats coordination as managing dependencies among activities, and the principles take three things from it: agree first on what is being decided, divide the work into parts that are each feasible on their own, and set in advance what will trigger revising the division, so that a changed question sends the plan back for review. Execution can be delegated; synthesis stays the researcher's responsibility. Outputs that agree because they share one contested assumption do not confirm each other independently.

### Records outlast the tools that wrote them

Durable sources, temporary runtime data and reconstructible views have distinct roles: records remain understandable after tool changes, displayed completion grants no acceptance authority, and caches create no second factual source. Ownership of records by the researcher is taken from local-first software [Local-first software](https://doi.org/10.1145/3359591.3359737); maintainable conventions from good-enough practices for scientific computing [Good enough practices](https://doi.org/10.1371/journal.pcbi.1005510); boundaries drawn around changeable decisions from Parnas's criteria for decomposing systems [Parnas](https://doi.org/10.1145/361598.361623). Local-primary storage does not claim the full local-first replication model. Walsh and Ungson's organizational memory [Organizational Memory](https://doi.org/10.5465/amr.1991.4278992) distinguishes acquisition, retention, retrieval and misuse, motivating retained conditions of use so later work can assess relevance and continuing applicability. Recovery is scoped to the current decision. Concurrent comparisons and quality checks may use different records, with their connections retained; summaries restore the direction of work, while sources support examination.

The researcher's sources, temporary runtime data and views that can be rebuilt from the sources, such as the Dashboard's cards and calendars, each keep their own role.

The researcher's ownership of records follows local-first software [Local-first software](https://doi.org/10.1145/3359591.3359737), although local-primary storage does not claim the full local-first replication model. Boundaries are drawn around the decisions most likely to change, following Parnas [Parnas](https://doi.org/10.1145/361598.361623). Retention is not retrieval: a record is kept with its conditions of use so that later work can judge whether it still applies, and recovery is scoped to the current decision.

### Correction narrows a claim; it does not erase history

**What correction keeps.** Correction preserves a record of what changed, why it changed and which parts remain useful. Retained assets include conclusions, methods, decompositions and lessons from failures. March's exploration–exploitation analysis [Exploration and Exploitation](https://doi.org/10.1287/orsc.2.1.71) warns that reuse can undermine exploration, motivating alternatives, counterexamples and revision of rules that hide unsupported assumptions or exclude relevant directions. Methods retain supporting instances, scope, review triggers and retirement paths. A single success provides no basis for establishing a stable rule.

**Learning versus artifact.** Research on generative AI and human learning [GenAI and human learning](https://doi.org/10.1038/s41562-024-02004-5) separates artifact performance from cognition, metacognition and learning. Flavell's account of metacognition [Metacognition and cognitive monitoring](https://doi.org/10.1037/0003-066X.34.10.906) links knowledge, experiences, goals and strategies; the reasons given before and after a task, together with later questions and checks, can reveal whether researchers recognize missing evidence or a need for assistance and whether they change their checking strategy. Initial judgment, conflicting cases and reflection are task-dependent scaffolds, not compulsory lessons; artifact production and judgment practice are different goals.

**Feedback and assistance.** Human–AI feedback loops [Human–AI feedback loops](https://doi.org/10.1038/s41562-024-02077-2) may reinforce bias, so no benefit from adaptation is assumed. Feedback may help researchers revise methods, and reviewed records, contributions or support strategies may alter later work. The grounds for reducing, replacing or stopping assistance must remain, even if the system itself is simplified.

Beyond the example, a retired recommendation may still supply a valuable counterexample, so conclusions, methods and lessons from failure are retained with their scope, their review triggers and a path to retirement.

March's analysis of exploration and exploitation [Exploration and Exploitation](https://doi.org/10.1287/orsc.2.1.71) warns that reuse can crowd out exploration, which is why alternatives and counterexamples are kept. Research on generative AI and human learning [GenAI and human learning](https://doi.org/10.1038/s41562-024-02004-5) separates how well an artifact performs from what the researcher comes to understand. On this view a single success establishes no rule; the report assumes no benefit to the researcher's understanding, and the grounds for reducing or stopping assistance are kept as well.

### When a cleanup is finished

The early prototype repeatedly exposed the same problem: a cleanup would be declared finished, then another inspection would find more work. A historical classification of ten cleanup rounds across nearly two hundred commits found 39 recurring issues. Six of them (about 15%) were classified as previously missed checks; this is a share of observed records, and without complete independent adjudication it establishes neither recall nor a miss rate. The other issues arose from competing owners, changed sources, newly introduced checks, scope changes and pending human decisions. Cleanup was not a function with fixed inputs and a computable completion condition, so the canon added the four convergence provisions restated in Supplementary Note 3, which report Section 4.4 turns into bounded goals and Note 5 states precisely.

**Example: when is a cleanup finished?** The researcher asks for every citation in the method-comparison card to be checked. At the start the specification of the bounded goal is frozen: the purpose is citation checking; the scope is the project's unclosed records; the rule is that every citation resolves and its version matches, while whether a citation to a retracted paper may stay is the researcher's judgment; and the budget is twenty decision boundaries and three questions. The run finds twelve citations. Ten pass. One points to a retracted paper, and whether it may stay is for the researcher to judge, so it becomes one bounded question. One is written in a shared card from another scope and only displayed in this card; that card is outside the frozen scope, so it derives no requirement and is listed in the report as out of scope. If the researcher establishes that the citation may stay and gives a reason, the goal ends complete. If instead the researcher establishes that it may not, the requirement returns to open work and the goal does not complete; other answers follow Definition 5.9 of Note 5. If the question is not answered, the goal ends complete_with_held and lists the question with its reopening trigger. If someone edits the card during the session, the requirements that edit derives belong to the next bounded goal.

### Closing work and delivering context

**Closure and confirmation.** Soul Contract §3 requires every declared check to pass before a requirement closes. Only a check explicitly based on human judgment may be satisfied by a reasoned human decision; a vanished trigger, a local scan or passing tests cannot replace a check. An unauthorized direct edit is break-glass: later confirmation closes its confirmation requirement without making the edit a prior-authorized admission, and this includes directly changing a commitment judgment from “A is better” to “A is better with visible targets.” The specification covers all judgment content, while the implementation covers only judgment blocks tracked by block hash and commitment judgment fields tracked by written-value digests. A close report is not confirmation, and a later value change creates a new generation beyond the old confirmation. Unconfirmed edits, unreconstructable earlier specifications and in-scope work that was never evaluated block completion even when their questions are unanswered or deferred (the definition of Done, Definition 5.20 of Note 5); work that was never evaluated is never a passing check. Requirement states are `open`, `deferred`, `waiting`, `resolved` and `cancelled`. Client and projection aliases must declare their mapping to these states, while Run, Session, Attention and Portfolio are independent axes that need no mapping.

**Context delivery.** Important tasks distinguish authorization, delivery, observation, exclusion and outbound disclosure. Without a means of observation, delivered must not be reported as observed (Soul Contract §4). A session agent driven by a cloud model is not a provider, but a context packet delivered to it through `ros context` still leaves the local machine. Source sensitivity governs this route. Public and internal material may be delivered within a researcher-started session for the requested commitment or card. Sensitive material requires the researcher to confirm personally in the local terminal each time; parameters an agent supplies are not confirmation. Private and unrecognized levels are excluded. A private commitment portfolio may declare in its frontmatter which commitment fields are deliverable as internal, for example question, next step and current stage; undeclared fields and titles remain private, and the commitment id travels as the requested key. This declaration does not apply to sensitive or unrecognized sources. Each delivery records its destination service, purpose, delivered sources and exclusions; an unrecognized destination is recorded as unknown, not as an observed disclosure. Revocation stops later delivery but cannot retract content already delivered. Report Section 5.4 and Note 6 give the implementation status of these conditions.

## Supplementary Note 2. Session operations and implementation mappings

The coordination kernel computes changes and unresolved requirements over source-adapter snapshots; clients present them, and platform adapters handle files, execution and receipts. Researcher-held Markdown remains the durable source, `scripts/ros.py` connects existing services without creating another fact store, and model output grants no write authority. Report Section 5.2 describes admission channels and bypasses, and Section 5.4 lists them as gaps 1 and 2.

| Command | Operation, record and boundary |
| --- | --- |
| `ros today` | Restores attention arrangements, pending judgments and attention proposals, and reports node changes observed since the checkpoint. Registered relations identify commitments worth checking, not ones proved to require modification. On the initial scan the change list counts every node as newly found; what marks it as initial is the attribution field `cause=initial` on the requirements. Focusing one commitment does not make the graph-wide cursor its exclusive history. |
| `ros context` | Creates a permitted source packet for the selected item under the delivery conditions of Supplementary Note 1 and retains a receipt. |
| `ros run judgment`; `ros propose judgment` | The former starts model-assisted judgment; the latter registers an existing draft. Execution explicitly selects a provider or a copyable packet; the downloadable version permits only the packet. |
| `ros collect` | Collects a packet result from an external executor. Only a structurally valid candidate can proceed to admission; failure, invalid output or unknown side effects do not become a successful judgment. |
| `ros close`; `ros admit` | Closure compares the starting snapshot with current sources and reports file and factual-field changes, admitted judgments, refused and still-undecided candidates, and unresolved requirements; without a starting snapshot, comparison is reported as unavailable. A judgment draft not yet written into a file is registered with `ros propose` and admitted with `ros admit` after the researcher's decision. A judgment block already written into a file can only be confirmed afterwards with `ros admit --confirm` at the researcher's terminal (report Section 5.2), which is not admission. Closure substitutes neither for admission nor for completion of the research. |
| `ros answer` | Records the researcher's answer to one bounded question that `ros today` asked, choosing among the options that question offers: satisfied, unsatisfied, narrow, cancel or defer. Satisfied closes the check and resolves the requirement, unsatisfied returns it to open, cancel cancels it, and narrow or defer leaves it waiting on a registered trigger. Satisfied and cancel need a reason and are accepted only at the terminal; an agent's relay is recorded as asserted by the invoker and the question stays open (report Section 5.2). |
| `ros decide` | Defers a requirement to a date, cancels it with a reason, reopens it, or confirms a judgment-class field that was written directly. Cancel and confirm are accepted only at the terminal; an agent's relay is recorded as asserted by the invoker and the requirement keeps its state (report Section 5.2). A deferral or reopening relayed by an agent is applied and recorded as asserted by the invoker. |
| `ros attend` | Sets the attention schedule of one commitment: today, tomorrow, a date, parked, or its next step completed; `undo` reverses the last such action. It writes only the attention schedule, never the commitment portfolio, and records each action so that it can be undone. The downloadable version only shows the planned action. |
| `ros state` | Shows the question, evidence, judgments, open items and next step of one commitment, and marks each judgment as admitted, confirmed afterwards or not admitted. |
| `ros rules` | Lists the rule table with the number of open requirements per rule; `--check` also lists rule and boundary problems and exits nonzero when a rule file has problems. |
| `ros receipt` | Looks up, in the local ledger, the receipt for closing one episode card: the effect, the checks that support it, the candidate, and whether a rollback has revoked it. |

Report Section 5.1 names four logical structures. The table gives their current carriers and what each does not establish.

<!-- table: Record structures: carriers and what they do not establish -->
| Structure | Existing carrier and role | What it does not establish |
| --- | --- | --- |
| Graph and source snapshot | Adapters read sources, relations and versions; the kernel consumes the snapshot | A missing graph edge does not prove the absence of a real dependency |
| Rule set | Task-extension descriptors carry declarations; rule files under `config/extensions/rules/` carry the rule checks | A valid descriptor does not establish arbitrary scientific conditions |
| Unresolved requirements | The context-impact ledger family retains identity, generation, checks and dispositions | Runtime records do not become a second authority for durable facts |
| Execution trace | Decisions, attempts, effects, checks and feedback remain distinct | Successful exit or an answer does not establish acceptance of a scientific conclusion |

The prototype's remaining vocabulary and its contracts are as follows.

| Responsibility or route | Retained contract |
| --- | --- |
| Task, rule, skill and policy | Tasks bind purpose, sources, scope and result requirements and may compose applications. Rules define conditions and checks; skills organize selection, branches, retries and stopping; policies choose among ready applications under resource constraints. |
| Execution, capability and plugins | Harnesses and adapters connect tools and models with effects, failures and execution conditions. Capability claims link evidence across instances to a scope and remain reviewable after acceptance (Supplementary Note 3). Plugins assemble task or capability contributions that share a lifecycle: one plugin may serve several tasks, and a task may use several plugins. Ordinary new tasks first compose existing objects and methods; only a distinct contract or an independent lifecycle requires a new category. |
| Clients and results | Clients and views retain source identity, results and access scope. Common results retain evidence, proposed and adopted conclusions, human decisions, changes, lifecycle, sensitivity and durable owner. Answers, artifacts and candidate writebacks use the same contract and are admitted as in report Section 4.1. |
| Runtime route | Researcher goal and minimum sources → Agent/CLI/optional Unified Desk → TaskIntent, normalized task and policy-bound action in implemented controlled paths → ResultEnvelope (answer, artifact, writeback candidate) or ErrorEnvelope → optional Candidate, HumanDecision, Mutation, Validation, Receipt → researcher-held files and the next safe action. |
| Component dependencies | Clients call tasks/capabilities through platform adapters for files, context and supported execution services; common governance defines results, permissions and receipts. Durable records, temporary runtime data and generated views are managed separately so owners remain locatable after component replacement. [Information hiding](https://doi.org/10.1145/361598.361623) and [Local-first](https://doi.org/10.1145/3359591.3359737) motivate isolating volatile components and reading user-held data without the execution service. Implementation compliance still needs checking. |

**Figure 2 commands and two rejection paths.** The table records each step of the worked session of report Section 2 with the command that runs it; the scientific boundaries of the example are stated in report Sections 2 and 5.4.

| Step | Command, result and boundary |
| --- | --- |
| 1 Observe | `ros today` detects that the paper changed from $v_1$ to $v_2$ and registers the recheck of the judgment $J$, which depends on it, as open work, without asking a question. |
| 2 Deliver | `ros context commitment:tracking-comparison` supplies permitted sources and current state under the delivery conditions of Supplementary Note 1 and retains a context receipt. |
| 3 Dispatch | `ros run judgment --target <card carrying J> --executor copy_packet` produces a copyable packet without invoking a model service. The downloadable version supplies only a candidate or planned difference and changes no commitment source. |
| 4 Collect | `ros collect <run_id> --file draft.md` (or `ros propose judgment` directly) registers the candidate and freezes its grounds, here the paper at $v_2$. General non-cascading preservation is unimplemented, so the candidate itself states which parts of $J$ survive. A second candidate in the same session, “$A$ is better after re-appearance as well”, is collected the same way. |
| 5 Admit | `ros admit <candidate>` records the decision channel without blocking execution by an agent (report Section 5.4). Confirmed at the terminal, it writes the narrowed judgment as a new block beside $J$, which the prototype can neither replace nor withdraw (gap 11), and refuses the second candidate. If the paper changes again during review, admission rejects the $v_2$ candidate and requires a new proposal; if another actor edited the file after the write plan, the preimage check refuses to overwrite it. |
| 6 Close | `ros close` retains the old grounds, the new decision, the actual changes, undecided candidates and unresolved requirements. A complete admission receipt avoids confirming the same field change twice, while later direct edits still require confirmation. The recheck of $J$ stays open. The unknown under the re-appearance condition and the experiment are not listed, because no prototype rule registers them (gap 12); without a terminal-confirmed `ros decide … defer` the experiment is not waiting (gap 17), and it must not be closed merely to display completion. |

**Staged writes and the preimage.** A write must land on the content it was planned against (report Section 5.2). On four paths, admission, reconfirmation, closing an episode card (`ros propose episode-close`) and rule revision, the write goes in two stages: the staging service holds the planned write before it touches the source, and promotion then writes it in. An episode card is a Markdown card whose recorded state marks an episode of work open or closed. When the write is planned, these paths hand the staging service the original file digest, a fingerprint of the content the plan was formed on; this content is the preimage. Promotion refuses a mismatching preimage, keeps the intervening edits and issues no success receipt; this is the refusal described in report Section 2. These checks protect the built-in writeback paths, though they do not verify what an arbitrary rule must preserve (gap 9). On the judgment route of report Figure 11a, the candidate's basis is frozen by `ros collect` or `ros propose`, the researcher decides at the terminal (`ros admit`), and the staged write, promotion and receipt follow.

**Local runners.** The session kernel of the author's prototype can hand a bounded run to a local runner, the Codex CLI or the Claude Code CLI, each only when declared dispatchable under `providers` (report Section 5.3). Both runners start in an empty temporary workspace: Codex uses a temporary configuration directory that holds only its login and runs in a read-only sandbox with network off, and Claude Code runs in restricted mode, so it reads no user settings and enables no tools.

## Supplementary Note 3. Process and component contracts

This note restates the canonical provisions that report Section 3 summarizes, with their owners, and then gives the contracts for capability claims, extensions, views and repository maintenance.

### Canonical provisions in full

**Defining completion: four convergence provisions.** Four provisions govern bounded completion. The first freezes purpose, scope, versions, preservation, authority and budgets at the start, so that a change forms a new specification; intent contracts and supersession follow Kernel §1.1. The second counts completion against the frozen requirements and does not treat an exhausted budget or a human stop as completion; exhausting one check's acquisition allowance is not exhausting the goal's budget (Primitive Rule Model's bounded-completion contract; Kernel and Extension Architecture §2.1). The third routes evidence that cannot be decided only through legitimate entry points as bounded questions. Under Product Design §6, item-level Needs Review presents one question with finite options and does not repeat it at the same basis version; an unanswered item stays unknown with a reopening condition and does not block other authorized work. The fourth requires a rerun under an unchanged specification and unchanged sources, with no new evidence and no due trigger, to add nothing, and every new requirement to be traceable to a change (Primitive Rule Model's occurrence contract). Organization, archiving and cleanup report new items only within the frozen scope and checks (Product Manifesto §4.2), and checks added during review belong to the next run without revising its predecessor's conclusion. Report Section 4.4 states them in words, and Note 5 gives the mathematical conditions (Definitions 5.4–5.10 and 5.13–5.20); resolution, cancellation, holding, waiting and the exclusions from completion follow those definitions rather than a second rule set. Supplementary Note 1 gives the cleanup history behind the provisions and the citation-checking example.

**Three graph axes: ownership, dependency and bounded goals.** The research graph answers three different questions, and no axis substitutes for another (Primitive Rule Model, “Three graph axes”); Figure 9 draws them. Ownership specifies scope. It is a single-parent tree derived from source location with explicit source overrides, needs no separate scope registry and says nothing about who is responsible. Dependency records the grounds for a result, in a many-to-many graph owned by the relation index and judgment-basis fields; sharing an owner does not imply evidential support. The axis of bounded goals defines freezing and closure. Neither ownership nor a bounded goal is a status axis. Scope is frozen extensionally: scan configuration does not change ownership, moving records or closing child goals cannot shrink the frozen scope, and cross-scope interface keys must be declared and frozen. Closure neither establishes nor invalidates findings and cannot be inferred from renaming or location; the source and its closure receipt are authoritative for closure, and runtime records can only refute it (Kernel §2; Definition 5.13 of Note 5). Internal cross-scope references are counted rather than blocked, the disclosed limitation of gap 8.

**Closure and context delivery.** Soul Contract §3 governs closure: every check must hold, only a check declared to need human judgment accepts a reasoned decision, break-glass confirmation confers no prior authorization, and unconfirmed edits, unreconstructable earlier specifications and unevaluated in-scope work block completion (the definition of Done, Definition 5.20 of Note 5). Soul Contract §4 governs context delivery: authorization, delivery, observation, exclusion and outbound disclosure are recorded separately, and source sensitivity bounds each delivery. Supplementary Note 1 gives both sets of conditions in full.

### Capability claims and evidence

Capability describes a researcher's, model's or human–AI combination's disposition to perform a task and respond to change under declared conditions; a task instance supplies observational evidence. Following the ownership specified in Kernel §1.1, ReSearchOS retains a capability claim $k$ and its grounds for revision as the tuple $\mathrm{Cap}_k=(s_k,T_k,\Omega_k,M_k,\mathcal{E}_k,\mathcal{F}_k,\mathcal{U}_k)$. $s_k$ identifies whether the subject is a researcher, model or human–AI arrangement; $T_k$ states the work to perform, $\Omega_k$ the claimed domain of applicability, and $M_k$ the evidence criteria. The remaining fields retain observed instances, known failures, and review or retirement conditions; each instance also records its strategy, execution and observation conditions, and relevant versions. A comparison completed by a person with model assistance can at first count only as evidence about that human–AI arrangement; evaluations of human–AI combinations [Human–AI combinations](https://doi.org/10.1038/s41562-024-02024-1) likewise distinguish individual and combined performance. $k$ identifies the claim independently of any research commitment. The tuple organizes evidence without converting it into a capability score or presuming transfer or a benefit from combination. Kernel §1.1 also requires a capability claim to declare its authority boundary, which the tuple does not list; however much evidence supports a claim, it confers no execution or admission authority, which is still decided as in report Section 4.1.

For method comparison, $T_k$ may be producing a source-grounded comparison that preserves applicability conditions. Correctly comparing two papers on one test set supplies one performance observation; with different metrics and missing re-appearance results, the next comparison must identify comparable items, missing evidence and why ranking is unsupported, and the first success does not establish general capability. $\Omega_k$ specifies the source types and variations to which the claim is intended to apply; the instances record which of those conditions were actually examined, and the difference makes untested coverage visible. $M_k$ specifies how omissions, unsupported recommendations and uncertainty are judged; known failures link to the relevant instances rather than forming a disjoint set of observations. A plugin install adds no evidence, a correct comparison in one case does not establish transfer to another, and an updated provider may require renewed evaluation. Capability claims therefore follow the same revision cycle as research judgments: accumulate informative instances, inspect contrary cases and narrow or retire the claim when its grounds no longer hold.

This documentation has a precedent in Model Cards [Model Cards](https://doi.org/10.1145/3287560.3287596), which connects reported model performance to intended uses and evaluation conditions; the capability claim applies a related discipline to a specified subject, including a human–AI arrangement, while retaining the instances that may revise it. CheckList [CheckList](https://aclanthology.org/2020.acl-main.442/) further motivates testing particular behaviors. For method comparison, recognizing an unsupported recommendation and responding correctly to a source correction should be examined separately: success at producing a plausible comparison need not imply either.

When a research task serves as a probe of capability, evidence selection and representation affect what it measures. MGIT [MGIT](https://proceedings.nips.cc/paper_files/paper/2023/hash/4ea14e6090343523ddcd5d3ca449695f-Abstract-Datasets_and_Benchmarks.html) introduces richer spatiotemporal and causal descriptions, CausalStep [CausalStep](https://ojs.aaai.org/index.php/AAAI/article/view/37582) examines sequentially constrained reasoning, and Select Less, Reason More [Select Less, Reason More](https://openaccess.thecvf.com/content/CVPR2026/html/Li_Select_Less_Reason_More_Prioritizing_Evidence_Purity_for_Video_Reasoning_CVPR_2026_paper.html) studies selective visual evidence acquisition. FIOVA [FIOVA](https://arxiv.org/abs/2410.15270) incorporates variation in human annotation. These lines motivate retaining the conditions and interpretive alternatives that distinguish a supported judgment from an overly broad one. The connection is methodological: the same discipline of conditioning a claim on available evidence informs the research-state model, although the tasks and implementations differ.

### System extension and invariant preservation

Researchers may organize interviews, simulations or experiments using different cards, interfaces and methods. The common grammar specifies roles and permitted changes without enumerating scientific objects, claiming a complete scientific ontology or imposing one template: objects need source identity, relations need meaning and grounds, and methods must declare inputs and outputs while following the common result and admission protocols. An interview card, for instance, must still link a theme to its source excerpts and distinguish a method's candidate from a researcher-accepted judgment; a new card type cannot turn a proposed theme into a confirmed finding. [Refinement mappings](https://research.google/pubs/the-existence-of-refinement-mappings-2/) provide a precedent for relating implementations to abstract specifications. Shared field names or a compatibility claim do not prove property preservation; the mapping of local objects and operations to the core must be explicit.

Let $\mathcal X_0,\mathsf{Init}_0$ be the core state and initial-state sets, with $\mathcal X_\lambda,\mathsf{Init}_\lambda$ their counterparts for instance $\lambda$ and $p_\lambda$ the interpretation map. States include governance records and observed effects beyond the research state of report Section 4.1. A concrete step may correspond to finitely many core steps, including zero.

**Proposition: an extension preserves a shared property.** Fix a projection $p_\lambda:\mathcal X_\lambda\to\mathcal X_0$ and property $\varphi$, and require:

1. Initial states correspond: $p_\lambda(\mathsf{Init}_\lambda)\subseteq\mathsf{Init}_0$.

2. Each extension transition is simulated by zero or more shared-model steps: $x\to_\lambda x'\Rightarrow p_\lambda(x)\to_0^*p_\lambda(x')$.

3. Every shared-model initial state satisfies the property: $\forall z\in\mathsf{Init}_0:\varphi(z)$.

4. Every shared-model transition preserves it: $z\to_0 z'\Rightarrow(\varphi(z)\Rightarrow\varphi(z'))$.

Then every state reachable in the extension maps to a state that satisfies the property, $\forall x\in\mathsf{Reach}_\lambda:\ \varphi(p_\lambda(x))$, where $\mathsf{Reach}_\lambda$ comprises the states reachable from $\mathsf{Init}_\lambda$ by finite local paths. The mapped initial state satisfies $\varphi$, the finite core sequence corresponding to each concrete step preserves it, and induction along the path gives the result. This refinement-mapping argument gives conditional preservation of a state invariant, not a new verification theorem; full behavioral refinement also requires checks of observable behavior and liveness.

**Construction and limits.** Choose any local workspace $\mathcal L_\lambda$ and set $\mathcal X_\lambda=\mathcal X_0\times\mathcal L_\lambda$, $p_\lambda(z,l)=z$, with initial states from $\mathsf{Init}_0\times\mathcal L_\lambda$. Local updates change only $l$ and core updates change $z$ only through allowed transitions, which satisfies the step condition. $\mathcal L_\lambda$ may hold layouts, temporary compositions or method workspace data only if their effects on the invariant are not omitted; new acceptance rules or private disclosure cannot be hidden as layout preferences. The map must preserve the observations relevant to $\varphi$: source identity, acceptance, access scope, persistent effects and recorded authorization or failure, so omitting files or outbound requests cannot conceal unauthorized writes or disclosure. Only operations preserving these observations may count as zero steps: rearranging a view can, whereas accepting a relation requires corresponding core decisions and effects. Failures and partial effects also need interpretations; otherwise the property holds only in a deliberately incomplete model.

The result establishes neither research benefit, scientific truth, termination nor complete privacy protection. An endlessly looping extension that preserves core observations may satisfy safety while remaining unusable, so task acceptance, failure recovery and evidence of benefit are still required. Separately valid extensions may interfere through shared state; their composition needs renewed checks against actual dependencies and effects.

### Feedback, views and repository maintenance

Feedback may change the current question, a reusable method or the researcher's practice. Horvitz's [mixed-initiative principles](https://doi.org/10.1145/302979.303030) address uncertain goals, intervention timing and correction opportunities. Here a question is warranted when missing information would change the action, and routine work keeps its valid authorization, since confirming every step returns the burden of coordination to the researcher. None of these changes updates model parameters; within-task revision, cross-task retention of strategies and foundation-model training are separate processes. Self-Refine [Self-Refine](https://proceedings.neurips.cc/paper_files/paper/2023/hash/91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference.html) and Reflexion [Reflexion](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html) provide AI mechanisms for feedback-based revision and experience use; ReSearchOS additionally requires identifying who judged, what supported the feedback and how a revision enters later work. A successfully executed process can still perpetuate a misunderstanding, so counterexamples, source checks and subsequent tasks remain necessary.

A view selects and organizes, for one reading purpose, a permitted snapshot of source records and receipts together with the existing session, run and admission state. The snapshot specifies a read boundary; it creates no new database, and the layout a view produces is an observation, not a measurement of human understanding. A pure view event, such as a selection, a filter or a rearrangement, changes only the local working state of selection, focus, filters and unsubmitted drafts, and changes neither research state nor history; an independent source update may still refresh the view.

Repository cleanup transforms the carriers of research state; its objective is not a smaller file count. A maintenance plan is ready only when it is authorized, its evidence is fresh, the coverage of its declared scope is established, and every fact, condition, independent ground, unresolved requirement, piece of history and recovery property it must keep is established in the staged post-state. Each of these checks returns pass (1), fail (0) or cannot yet tell (?), as in report Section 4.3, and one satisfied requirement cannot compensate for another that fails or is unknown. Acceptance rechecks readiness at the application boundary, requires the observed files and permissions to match the plan, and re-evaluates the same preservation conditions on the state read back after execution. Archiving or merging carriers or objects additionally needs identity, consumer and recovery checks bound to the planned objects, their consumers and versions; earlier plan readiness does not replace verification of the actual post-state. A purge proceeds only when every gate is 1: a zero rejects it, and an unknown keeps the carrier.

## Supplementary Note 4. Research foundations in detail

The narrative synthesis behind the comparison in report Section 6.1.

### Reading the design through existing mechanisms

[Engelbart](https://www.dougengelbart.org/content/view/138/) and [Distributed cognition](https://hci.ucsd.edu/hollan/Pubs/tochi-revised.pdf) treat people, methods and external representations as jointly organizing thought. We apply this to revisitable records, drawing on correction and intermediate-operation editing in [Guidelines for Human-AI Interaction](https://doi.org/10.1145/3290605.3300233) and [AI Chains](https://doi.org/10.1145/3491102.3517582).

Dependency tracking [Provenance as Dependency Analysis](https://doi.org/10.1017/S0960129511000211), separation of changing decisions [Parnas](https://doi.org/10.1145/361598.361623), design rationale [Questions, Options, and Criteria](https://doi.org/10.1207/s15327051hci0603&4_2) and decision–effect links [Decision Provenance](https://doi.org/10.1109/ACCESS.2018.2887201) inform question-bound state and replaceable execution in report Sections 2–5. Reasons and dependencies in [Truth maintenance](https://doi.org/10.1016/0004-3702%2879%2990008-0) and memoization and change propagation in [Self-adjusting computation](https://doi.org/10.1007/978-3-540-71316-6_31) motivate versioned grounds, reverse indexes and invalidation.

Compare four responsibilities: judgment and authority govern framing, acceptance and authorization; state and evidence govern retention and revision; execution and extension govern decomposition and replacement; interaction and presentation govern human understanding and intervention. They constrain each other and are neither independent mathematical axes nor quality scores.

[AI Chains](https://doi.org/10.1145/3491102.3517582) supports strategy comparison and editing faulty steps; report Section 4.4 additionally checks whether a previously checked result supports a new experimental use.

[Co-STORM](https://aclanthology.org/2024.emnlp-main.554/) offers user-guided discussion and dynamic mind maps before questions are fixed; ReSearchOS likewise permits question formation while distinguishing exploration from supporting evidence.

Textual computation and annotations in [Potluck](https://www.inkandswitch.com/potluck/) and ownership and long-term access in [Local-first](https://doi.org/10.1145/3359591.3359737) inform the record and integration boundaries in report Section 5.3. The former still requires programming; our descriptors and plugins need adaptation studies that count customization cost and preserve the interpretation of earlier sources and decisions after replacement.

[Steps Towards an Infrastructure for Scholarly Synthesis](https://arxiv.org/abs/2407.20666) already expresses evidence-based opportunities, constraints and solutions through adaptable grammars; field observations find useful informal links without exhaustive relation encoding. This supports retrieval before gradual structuring. We examine connections to bounded tasks, result review and revision, without claiming to originate opportunity formation or adaptable graph grammars.

[A-MEM](https://proceedings.neurips.cc/paper_files/paper/2025/hash/19909c36f51abc4856b4560aff3d36d6-Abstract-Conference.html) offers vector retrieval, model-assessed links and attribute updates. Integration must retain source and computation versions, distinguish inference from accepted judgments, check incremental results against recomputation, and measure cost and errors in the target research task.

Denario, OmniScientist, EvoScientist and MemOS already combine responsibilities, as report Section 6.1 shows. This overlap requires comparing the added value and cost of organizing them around judgment continuity.

### Interaction, organization and execution strategies

Handoffs and incremental checks in [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) and planning, generation and evaluation with removal of obsolete scaffolding in [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps) are coding experience, not controlled evidence of research benefit. [Why Do Multi-Agent LLM Systems Fail?](https://papers.nips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html) identifies design, coordination and verification failures. ReSearchOS must therefore re-evaluate coordination and verification after executor changes. Project rule files such as AGENTS.md are now read natively by coding agents: since Claude Code 2.1.277 [source](https://github.com/anthropics/claude-code/releases/tag/v2.1.277) (18 September 2026) a project without CLAUDE.md is read through AGENTS.md directly, except at that release on Bedrock, Vertex and Foundry, so a repository can usually keep its agent instructions in one file; whether a `CLAUDE.md → @AGENTS.md` bridge is still needed depends on the provider and on which instruction files exist.

[Chain-of-thought](https://proceedings.neurips.cc/paper_files/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4-Abstract.html), [Self-consistency](https://openreview.net/forum?id=1PL1NIMMrw), [Tree of Thoughts](https://proceedings.neurips.cc/paper/2023/hash/271db9922b8d1f4dd7aaef84ed5ac703-Abstract.html) and [Self-Refine](https://proceedings.neurips.cc/paper_files/paper/2023/hash/91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference.html) supply reasoning, search and feedback strategies; [ReAct](https://openreview.net/forum?id=WE_vluYUL-X), [Toolformer](https://proceedings.neurips.cc/paper/2023/hash/d842425e4bf79ba039352da0f658a906-Abstract-Conference.html) and [Gorilla](https://proceedings.neurips.cc/paper_files/paper/2024/hash/e4c61f578ff07830f5c37378dd3ecb0d-Abstract-Conference.html) supply action and tool mechanisms. These executors are replaceable, but retained research grounds must identify evidence and alternatives; generated reasoning is not presumed faithful to model computation.

[AutoGen](https://openreview.net/forum?id=BAakY1hNKS), [MetaGPT](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html), [ChatDev](https://aclanthology.org/2024.acl-long.810/) and [AgentScope](https://arxiv.org/abs/2402.14034) provide coordination precedents; [Reflexion](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html) and [Voyager](https://openreview.net/forum?id=ehfRiF0R3a) retain feedback or skills, and foundation models [Foundation models](https://arxiv.org/abs/2108.07258) affect downstream behavior. Plugin contracts separate contribution identity and lifecycle without equating compatibility with unchanged capability.

### Evidence selection and revisable memory

Retrieval learning in [DPR](https://aclanthology.org/2020.emnlp-main.550/) and [REALM](https://proceedings.mlr.press/v119/guu20a.html), evidence-based generation in [RAG](https://papers.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html) and [Fusion-in-Decoder](https://aclanthology.org/2021.eacl-main.74/), and retrieval-based training and adaptation in [RETRO](https://proceedings.mlr.press/v162/borgeaud22a.html) and [Atlas](https://jmlr.org/papers/v24/23-0037.html) supply relevant candidates. Research state additionally specifies what must survive selection.

The retrieval survey [RAG survey](https://arxiv.org/abs/2312.10997), evidence acquisition and use in [IRCoT](https://aclanthology.org/2023.acl-long.557/), [Self-RAG](https://proceedings.iclr.cc/paper_files/paper/2024/hash/25f7be9694d7b32d5cc670927b8091e1-Abstract-Conference.html) and [RAFT](https://openreview.net/forum?id=rzQGHXNReU), and unit and relation organization in [Dense X Retrieval](https://aclanthology.org/2024.emnlp-main.845/), [GraphRAG](https://arxiv.org/abs/2404.16130) and [HippoRAG](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6ddc001d07ca4f319af96a3024f6dbd1-Abstract.html) motivate selecting both passages and relations. Local relevance can still omit necessary qualifications elsewhere.

[MemGPT](https://arxiv.org/abs/2310.08560) manages memory tiers; [MemoryBank](https://ojs.aaai.org/index.php/AAAI/article/view/29946) retains interactions; [Generative Agents](https://doi.org/10.1145/3586183.3606763) combines retrieval and reflection; [A-MEM](https://proceedings.neurips.cc/paper_files/paper/2025/hash/19909c36f51abc4856b4560aff3d36d6-Abstract-Conference.html) revises notes and links; [Mem0](https://doi.org/10.3233/FAIA251160) selects updates with a graph variant. These are candidate memory implementations requiring adaptation; researcher-accepted judgment status and scope still need separate retention. Git-backed Markdown memory that agents edit directly is now a product feature (Letta Code MemFS [source](https://docs.letta.com/concepts/memfs), with memory upkeep routed to a background worker in Letta Code 0.33.0 [source](https://github.com/letta-ai/letta-code/releases/tag/v0.33.0)); our contribution is not the storage form but the admission boundary between agent-proposed candidates and researcher-accepted judgment, and the cost accounting around it.

[CoALA](https://openreview.net/forum?id=1i6ZCyf1QJ), [Memory in the Age of AI Agents](https://arxiv.org/abs/2512.13564) and [Memory for Autonomous LLM Agents](https://arxiv.org/abs/2603.07670) distinguish memory, action, decision and evolution; provenance-oriented [Agent Zero Memory](https://arxiv.org/abs/2608.29606) is a neighboring approach. Representation alone cannot answer whether explicit judgment status improves on strong dynamic memory after upkeep is counted.

[FAIR](https://doi.org/10.1038/sdata.2016.18), [RO-Crate](https://doi.org/10.3233/DS-210053) and [Provenance as Dependency Analysis](https://doi.org/10.1017/S0960129511000211) inform provenance and derivation records, implemented here through source references and change receipts. RO-Crate 1.3 [source](https://www.researchobject.org/ro-crate/specification/1.3/) (June 2026) is the current release. Traceability locates review grounds without establishing support for an interpretation or standardized RO-Crate interoperability; our receipts are not RO-Crate conformant.

Tool-mediated adversarial instructions in [Indirect prompt injection](https://doi.org/10.1145/3605764.3623985), [InjecAgent](https://aclanthology.org/2024.findings-acl.624/) and [AgentDojo](https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html), and retained-information authority errors in [Authorization laundering](https://arxiv.org/abs/2609.01836), show why accurate retrieval is not authorization. Admission (report Section 4.1) must bind the current operation and scope; hosts that are not integrated remain outside it.

### Scientific work and conditional capabilities

[Global Instance Tracking](https://doi.org/10.1109/TPAMI.2022.3153312) varies tracking assumptions, while [BioDrone](https://doi.org/10.1007/s11263-023-01937-0) varies physical disturbances, and [SOTVerse](https://doi.org/10.1007/s11263-023-01908-5) separates Environment, Evaluation and Executor. They motivate testing capability across changed conditions. A task episode supplies conditional behavior evidence; a strategy or installed plugin alone establishes no capability.

Method comparison keeps our case inspectable. More complex tasks can draw on scientific automation [Automated Scientific Discovery](https://doi.org/10.1007/s10994-025-06955-2), tool assistance [ChemCrow](https://www.nature.com/articles/s42256-024-00832-8) and Coscientist (Boiko et al.) [source](https://doi.org/10.1038/s41586-023-06792-0), and workflows [The AI Scientist](https://doi.org/10.1038/s41586-026-10265-5), [Agent Laboratory](https://aclanthology.org/2025.findings-emnlp.320/), the AI co-scientist (Gottweis et al.) [source](https://www.nature.com/articles/s41586-026-10644-y), [SciAgents](https://advanced.onlinelibrary.wiley.com/doi/10.1002/adma.202413523) and [Robin](https://www.nature.com/articles/s41586-026-10652-y), treating artifacts as inputs to further inquiry. The AI Scientist is published in Nature as “Towards end-to-end automation of AI research”. Git-like research protocols such as XScientist [source](https://arxiv.org/abs/2607.12301) also version research state and gate on human authority; ReSearchOS differs in placing the researcher’s admitted judgment, rather than the autonomous run, at the center of continuation, and in formalizing bounded goals and scope freezing over that record. Our synthetic case neither integrates all these systems nor compares discovery ability.

### Evaluation, transfer and human development

[SOEI](https://arxiv.org/abs/2410.15701), [EduVerse](https://arxiv.org/abs/2510.05650) and [EduPersona](https://arxiv.org/abs/2510.04648) introduce participant/episode variation through simulated teaching, configurable environments and differentiated learners; behavioral testing [CheckList](https://aclanthology.org/2020.acl-main.442/) and interaction performance/progress [AgentBench](https://proceedings.iclr.cc/paper_files/paper/2024/hash/e9df36b21ff4ee211a8b71ee8b7e9f57-Abstract-Conference.html), [AgentBoard](https://proceedings.neurips.cc/paper_files/paper/2024/hash/877b40688e330a0e2a3fc24084208dfa-Abstract-Datasets_and_Benchmarks_Track.html) provide complementary evaluation.

[FActScore](https://aclanthology.org/2023.emnlp-main.741/), [ALCE](https://aclanthology.org/2023.emnlp-main.398/), [Ragas](https://aclanthology.org/2024.eacl-demo.16/), [RGB](https://ojs.aaai.org/index.php/AAAI/article/view/29728) and [CRAG](https://proceedings.neurips.cc/paper_files/paper/2024/hash/1435d2d0fca85a84d83ddcb754f58c29-Abstract-Datasets_and_Benchmarks_Track.html) distinguish factual support, citation quality and evidence use; [LLM-as-a-judge](https://proceedings.neurips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html) and [VerifyBench](https://ojs.aaai.org/index.php/AAAI/article/view/40448) scrutinize evaluators. Report source support, applicability, acceptance-state errors and critical mistakes separately; a model score cannot certify judgment quality.

Better assisted output does not establish collaboration or researcher development. [Human–AI combinations](https://doi.org/10.1038/s41562-024-02024-1) distinguishes improvement over a person from improvement over the stronger component; [Generative AI and human learning](https://doi.org/10.1038/s41562-024-02004-5), [Collective intelligence](https://doi.org/10.1038/s41562-024-01959-9) and [Human–AI feedback loops](https://doi.org/10.1038/s41562-024-02077-2) raise transfer, dependence and bias-accumulation concerns. Evaluation must allow retained material to support judgment, add upkeep or perpetuate errors.

### Further related work

Behind the agent-memory and AI-scientist rows of report Table 5 stand several lines of work. Retrieval and memory systems such as RAG [RAG](https://papers.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html), A-MEM [A-MEM](https://proceedings.neurips.cc/paper_files/paper/2025/hash/19909c36f51abc4856b4560aff3d36d6-Abstract-Conference.html), Mem0 [Mem0](https://doi.org/10.3233/FAIA251160) and MemOS [MemOS](https://arxiv.org/abs/2505.22101) supply mechanisms for acquiring, retaining and migrating context. MemGPT [MemGPT](https://arxiv.org/abs/2310.08560) manages memory tiers within a continuing dialogue. The AI Scientist [The AI Scientist](https://doi.org/10.1038/s41586-026-10265-5) and Agent Laboratory [Agent Laboratory](https://aclanthology.org/2025.findings-emnlp.320/) organize it into hypotheses, experiments and artifacts, while OpenScholar [OpenScholar](https://www.nature.com/articles/s41586-025-10072-4) and PaperQA2 [PaperQA2](https://arxiv.org/abs/2409.13740) synthesize literature with cited evidence. Co-Scientist [Co-Scientist](https://www.nature.com/articles/s41586-026-10644-y) and Denario [Denario](https://arxiv.org/abs/2510.26887) extend assistance to hypothesis exploration and modular workflows, and EvoScientist [EvoScientist](https://arxiv.org/abs/2603.08127) accumulates strategies across runs.

Other work supplies parts of the design. Provenance as dependency analysis [Provenance as Dependency Analysis](https://doi.org/10.1017/S0960129511000211) motivates retaining the supporting relations, and AI Chains [AI Chains](https://doi.org/10.1145/3491102.3517582) supports editable intermediate steps. Interaction guidelines [Guidelines for Human-AI Interaction](https://doi.org/10.1145/3290605.3300233) and cognitive-forcing research [To Trust or to Think](https://doi.org/10.1145/3449287) motivate review at consequential transitions. VIKI [VIKI](https://people.engr.tamu.edu/shipman/abstracts/echt94-abstract.html), DiscourseGraphs [DiscourseGraphs](https://arxiv.org/abs/2407.20666), Co-STORM [Co-STORM](https://aclanthology.org/2024.emnlp-main.554/) and Potluck [Potluck](https://www.inkandswitch.com/potluck/) let users shape semi-structured objects, claims and evidence, discourse and computational relations. AutoGen [AutoGen](https://openreview.net/forum?id=BAakY1hNKS) leaves research semantics to the application. Local-first software [Local-first software](https://doi.org/10.1145/3359591.3359737) ties ownership to availability beyond a service, and organizational memory [Organizational Memory](https://doi.org/10.5465/amr.1991.4278992) separates retention from retrieval.

## Supplementary Note 5. Formal specification

Report Section 4 explains the definitions in words on the running example, and report Appendix A lists their objects with their states and draws the lifecycle of a requirement. This note states every definition precisely, with its equation. It now also holds the two propositions of report Section 4.4: their full hypotheses, their arguments, and what they do and do not prove. It also collects the formal conditions and edge cases that Section 4 leaves out, among them version branches and late-arriving records, eligible receipt bundles, the full conditions for held and waiting work, live questions, the non-exempt kinds of work, the scope tree and the rules for scans. Research state and admission are stated first and unnumbered; the remaining definitions and equations are numbered 5.1–5.21, and Definition 5.k carries Equation 5.k.

Each numbered definition says what it is for and states it; where report Section 4 does not already do so, it reads the definition on the example of report Section 1 and gives its limits. In the example, “the paper” is the paper corrected from $v_1$ to $v_2$, the first and second sets are its two benchmark sets, and $J$ is the judgment that $A$ is better than $B$ while the target stays in view. A symbol used inside a definition inherits that definition's object, purpose, rule version and cutoff even when those arguments are omitted. Throughout, $t$ indexes a declared sequence of decision boundaries, the subscript $t+1$ marks the next one, $\vartheta_t$ is the clock value at boundary $t$, its cutoff, and $\varepsilon$ is a bounded goal.

### Decision boundaries, research state and admission

A decision boundary is a moment at which the system looks at what has arrived and decides what to do next; it is not an hour or a day. Boundaries follow one another in a declared sequence, and each has a clock value, its cutoff. Work does not stop between boundaries: concurrent activity appears as delivered observations. A record that arrives after a boundary's cutoff cannot enter the decision at that boundary.

**Research state.** *What it is for:* it says what must be kept for the researcher to resume work (report Section 4.1). The research state at boundary $t$ is a reconstruction from records:

$$
\widehat R_t := (Q_t,E_t,J_t,B_t,N_t).
$$

$Q_t$ through $N_t$ hold, in order, the question, the evidence with its relations, the accepted judgments with their scope, the open conditions and the next step. $B_t$ also records conflicts and the cases in which a judgment does not apply. The hat marks a reconstruction from records rather than a summary: its sources and its status can be checked and corrected. Keep, update and hold are statements about this tuple. A kept judgment stays in $J_t$ with its grounds and scope. A judgment whose grounds are touched also stays in $J_t$, but a requirement in the unresolved set (Definition 5.3) marks it for recheck, and it is updated only when a candidate that narrows or replaces it, pinned to the changed source version, is admitted. A scientific condition the evidence cannot settle stays among the open conditions in $B_t$, apart from held maintenance work (Definition 5.6). Three parties act on the state: the environment selects context from the history it may use, reconstructs $\widehat R_t$ and presents it with any candidate; a model proposes an output $y_t$ and a change $\Delta_t$; and the researcher's decision $d_t$ chooses what happens next.

**Admission.** *What it is for:* it is the only route by which a candidate becomes state, and no single party can take it alone. A candidate is admitted when five conditions hold together:

$$
\begin{aligned}
\operatorname{Admitted}_t&:=\operatorname{Accept}(d_t,\Delta_t)
\land\operatorname{Authorized}(\rho_t,\Delta_t)\\
&\quad\land\operatorname{Applied}(\rho_t,\Delta_t)
\land\operatorname{Passed}(\rho_t,\Delta_t)\\
&\quad\land\operatorname{Recorded}(H_{t+1},\rho_t).
\end{aligned}
$$

The researcher's decision $d_t$ accepts the change $\Delta_t$. A trusted host or an actual instruction within scope authorizes it, which the candidate's own text cannot do. The change has actually been applied and its checks have passed. Finally, a receipt $\rho_t$, the record of what was done and checked, is kept in the history $H_{t+1}$ that the next boundary reads. *Limits:* a change that never ran, or one without a receipt, does not count as applied or checked. A failed or partial application may leave effects without its intended result, so its effects and whether it reached its result are recorded separately. Reconstruction and presentation must give the same state on the same permitted inputs and must show a missing source as unknown rather than fill it in. They may neither rewrite the record nor preselect acceptance. Accept means only that the operational decision requirement is met; it does not make the judgment scientifically true.

Two lines of work bear on the idea of research state. Distributed cognition [Distributed cognition](https://hci.ucsd.edu/hollan/Pubs/tochi-revised.pdf) studies reasoning that runs through external representations, and a research record is one; provenance as dependency analysis [Provenance as dependency analysis](https://doi.org/10.1017/S0960129511000211) studies how a result depends on its inputs, and these dependencies are what the evidence in research state must keep.

### Versions and touched requirements

A decision at a boundary may use only the observations that are permitted for the task and were available by its cutoff. These observations may describe several versions of the same object, and the current version is not simply the newest file. An object's current version candidates are the recorded revisions with no known successor, and a successor counts as known only when the visible history establishes it. The candidates can therefore be none, a single revision or several unresolved branches, and a late-arriving ancestor cannot replace its known descendant. Changing content from one version to another and back creates a new revision; a repeated snapshot creates none. A revision is identified by the observation that records it, and pins and receipts bind to the revision and record its content digest. The prototype identifies versions differently (report Section 5.4).

**Definition 5.1 (current version candidates).** *What it is for:* it says which versions of an object a decision treats as current (Section 4.2). With $\mathcal O_t^a$ the observations permitted for the task (the superscript marks permission) and available by $\vartheta_t$, the current candidates of object $v$ are:

$$
\mathcal S_t(v)
:=\operatorname{Max}_{\prec_t}\!
\left(\bigcup_{o\in\mathcal O_t^a}\operatorname{States}(o,v)\right). \tag{5.1}
$$

$\operatorname{States}(o,v)$ contains the revisions of object $v$ recorded in observation $o$, and the order $\prec_t$ contains only the predecessor relations established in the visible history.

**Definition 5.2 (touched requirements).** *What it is for:* it says which requirements a change touches. $\mathcal J_t^\kappa$ is the set of requirements, each with a stable identity $j$, registered for the current purpose $\kappa_t$; $\operatorname{dep}_t(j)$ is the set of recorded inputs of $j$, including the versions of its rule and purpose; $\mathcal C_t$ contains the inputs whose current version candidates changed since the previous boundary, compared by revision digest; and $\mathcal F_t^{\mathrm{scan}}$ contains the needs found when work is first set up or a scoped check is rerun, missing dependencies included:

$$
\mathcal F_t:=\mathcal F_t^{\mathrm{scan}}
\cup\{j\in \mathcal J_t^\kappa:
\operatorname{dep}_t(j)\cap\mathcal C_t\ne\varnothing\}. \tag{5.2}
$$

**Definition 5.3 (unresolved requirements).** *What it is for:* it keeps a touched requirement in view until it is closed on the record. With $\mathcal Z_t^{\mathrm{res}}$ the requirements resolved at $t$ (Definition 5.5), $\mathcal Z_t^{\mathrm{cancel}}$ those cancelled by a recorded decision, and union taken by requirement identity:

$$
\mathcal U_{t+1}:=(\mathcal U_t\cup\mathcal F_t)
\setminus\bigl(\mathcal Z_t^{\mathrm{res}}
\cup\mathcal Z_t^{\mathrm{cancel}}\bigr). \tag{5.3}
$$

*Limits:* because the set holds each requirement once, by its identity, repeated observations do not multiply a need, and a requirement that nobody examined survives the next boundary. With a fixed dependency index, finding the touched requirements is a lookup on the changed inputs rather than an inspection of every record, but the lookup cannot discover a dependency that was never recorded. Whether a requirement is touched depends only on which inputs changed. Whether grounds are joint or alternative is kept in the judgment's basis and decided by the researcher, and a shared path or participant alone does not show that a summary must change; in the example, the re-appearance experiment is not touched merely because it shares a path with the corrected paper. Deferral, waiting (Definition 5.6) and an unsupported report of completion are neither resolution nor cancellation. A scan run for a bounded goal cannot add requirements that its frozen specification does not imply (Definitions 5.18–5.19).

### Three-valued checks, held and waiting work

**Definition 5.4 (check value).** *What it is for:* it keeps an unknown apart from a failure (Section 4.3). Each check $\chi$ in the nonempty check set $D_{t+1}(j)$ of requirement $j$, declared and frozen with the versions of the requirement's rule and purpose rather than derived at run time, is assessed on a bundle of receipts $\rho$; 1 and 0 mean established satisfaction and non-satisfaction, and ? evidence that is missing, stale or in unresolved conflict:

$$
s_{\chi,t}(\rho)\in\{1,0,?\}. \tag{5.4}
$$

A 1 or a 0 requires a qualified, currently valid check. The ? is not a zero, and the closing rule accepts only 1.

**Definition 5.5 (resolution).** *What it is for:* it is the only way checks close a requirement. With $\mathcal E_{t+1}(j)$ the eligible bundles available by the end of the round, each bound to one rule application, purpose and requirement on versions that are still current:

$$
\mathcal Z_t^{\mathrm{res}}
:=\left\{j\in\mathcal U_t\cup\mathcal F_t:
\exists\rho\in\mathcal E_{t+1}(j),\quad
\forall\chi\in D_{t+1}(j),\ s_{\chi,t+1}(\rho)=1\right\}. \tag{5.5}
$$

All checks of a requirement are evaluated on one bundle, so later formulas omit the receipt argument of $s_{\chi,t+1}$. Cancellation is a separate decision to stop pursuing the need and does not count as a repair.

**Definition 5.6 (held and waiting work).** *What it is for:* it says which unresolved work of a bounded goal $\varepsilon$ is held on a question to the researcher or waiting on a trigger. With $\mathcal U^\varepsilon_t:=\mathcal U_t\cap\widehat{\mathcal Q}_\varepsilon$:

$$
\begin{aligned}
\mathcal Z^{\mathrm{held}}_t&:=\bigl\{j\in\mathcal U^\varepsilon_t\cup\mathcal F^\varepsilon_t:
\operatorname{Trig}_t(j)\neq\bot\ \land\ (\exists\chi\in D(j):s_{\chi,t+1}=?)\\
&\qquad{}\land\ \forall\chi\in D(j):\bigl[s_{\chi,t+1}=1\ \lor\ (s_{\chi,t+1}=?\ \land\ \operatorname{Undecidable}_{\varepsilon,t}(\chi)\\
&\qquad\qquad{}\land\ \operatorname{Asked}^{\mathrm{live}}_t(j,\chi))\bigr]\bigr\},\\
\mathcal Z^{\mathrm{wait}}_t&:=\bigl\{j\in\mathcal U^\varepsilon_t\cup\mathcal F^\varepsilon_t:
j\in\mathcal W_t\ \land\ \operatorname{Trig}_t(j)\neq\bot\\
&\qquad{}\land\ \bigl(\operatorname{Ext}_\varepsilon(j)\lor\operatorname{Defer}^u_t(j)\bigr)\bigr\}.
\end{aligned} \tag{5.6}
$$

$\mathcal U^\varepsilon_t$ and $\mathcal F^\varepsilon_t$ (Definition 5.19) thus restrict the unresolved and touched sets to the goal's registered requirements $\widehat{\mathcal Q}_\varepsilon$ (Definition 5.18). $\operatorname{Trig}_t(j)$ is the trigger that reopens held or waiting work, $\bot$ when there is none. $\operatorname{Undecidable}_{\varepsilon,t}(\chi)$ says that the ? cannot be removed without the researcher (Definition 5.8), and $\operatorname{Asked}^{\mathrm{live}}_t(j,\chi)$ that the bounded question about it, on the same basis version, is pending or asked by the boundary's cutoff (Definition 5.10). $\mathcal W_t$ is the set of requirements whose last recorded transition is a wait or a deferral. $\operatorname{Ext}_\varepsilon(j)$ says that a check is blocked outside the frozen scope; such a block also makes a ? undecidable, but it makes work waiting only once the work is in $\mathcal W_t$ with a trigger. $\operatorname{Defer}^u_t(j)$ says that the researcher deferred or narrowed the work with a trigger, or confirmed a deferral at the terminal. Held and waiting work remains unresolved. *In the example:* by the definitions, the recheck of $J$ has one check that only the researcher can decide; once the system has asked the bounded question about it, the recheck is held until the researcher answers.

*Limits:* a trigger that vanished, a local scan that passed and tests that are green are not checks and cannot produce a 1. Checks pooled from incompatible attempts or obsolete versions cannot close anything either. A check that was never evaluated has no value at all: it is recorded as unevaluated work that blocks completion (Definitions 5.19–5.20), not as an unknown. A justified inspection may conclude that no edit is needed, but that conclusion still needs evidence. Closure is never permanent, because old receipts cannot answer for new versions and a later source change can touch the same requirement again; closing the recheck of $J$ on the old receipt for $v_1$ is therefore no resolution. Holding has its own limits: a 0 among the checks, or two unknowns with only one question, prevents it. Likewise, an executor's deferral or a wait on something inside the scope does not make work waiting, so such work, unless held, simply stays unresolved. Holding and waiting never resolve or cancel a requirement.

### Undecidable checks and bounded questions

**Definition 5.7 (check basis).** *What it is for:* it says who can give a check its value, a mechanism or the researcher. Each check has a basis, mechanical or human, which belongs to its version:

$$
\operatorname{basis}:\ \mathsf{Ver}\text{-indexed checks}\to\{\mathrm{mech},u\},\qquad \chi^u:=\{\chi:\operatorname{basis}(\chi)=u\}. \tag{5.7}
$$

$\chi^u$ is the set of checks whose basis is the researcher $u$. A human-basis check obtains its receipt and its value 1 or 0 from the researcher's decision and reason. *In the example:* whether the first-set result still supports $J$ is a human-basis check, and it is the only check of the recheck of $J$. Whether $J$'s basis is pinned to the current version of the paper is not a check of its own, because Equation 5.5 admits only bundles on current versions. The prototype instead declares that version condition as its one mechanical check, which returns 0, so in report Section 2 the recheck stays open rather than held. *Limits:* the basis is frozen with $\mathsf{Ver}_\varepsilon$ and cannot be changed during the run. The researcher's answer does not close a requirement by itself: closure still requires one current bundle on which every check of the requirement passes (Equation 5.5).

**Definition 5.8 (undecidable check).** *What it is for:* it says when an unknown cannot be removed without the researcher, which is when Equation 5.6 lets work be held. A check is undecidable when it requires human judgment, has spent its acquisition allowance, or is blocked by a dependency outside the scope:

$$
\operatorname{Undecidable}_{\varepsilon,t}(\chi):=[\operatorname{basis}(\chi)=u]\ \lor\ [\mathrm{spent}_t(\chi)\ge\mathrm{alloc}_\varepsilon(\chi)]\ \lor\ [\operatorname{blockdep}(\chi)\not\subseteq\mathrm{Sc}_\varepsilon]. \tag{5.8}
$$

$\mathrm{spent}_t(\chi)$ is the nonnegative acquisition spent by the cutoff, in the units of $\mathrm{alloc}_\varepsilon(\chi)$ (Definition 5.16), and $\operatorname{blockdep}(\chi)$ returns the blocking inputs. *In the example:* the check whether the first-set result still supports $J$ is undecidable from the start, because its basis is the researcher.

**Definition 5.9 (bounded question).** *What it is for:* it turns an undecidable unknown into one question that the researcher answers from a fixed set of options:

$$
\begin{aligned}
\operatorname{Ask}(j,\chi)&:=\bigl(\operatorname{class}(j,\chi),\ \operatorname{basisVer}(\chi),\ \mathcal O^{\mathrm{ask}}\bigr),\\
\mathcal O^{\mathrm{ask}}&=\{\text{establish satisfied},\ \text{establish unsatisfied},\ \text{narrow scope},\ \text{cancel},\ \text{defer with trigger}\}.
\end{aligned} \tag{5.9}
$$

The question class comprises the rule, the bound subject, the check and the reason the check is undecidable. The basis version comes from the versions of the rule and the check, so the researcher is asked once for each version of a check. *Properties:* an answer that establishes satisfaction with reasons gives 1. One that establishes non-satisfaction gives 0, returns the requirement to open and prevents completion unless the requirement is separately cancelled. Cancellation enters the cancelled set, narrowing takes effect at the next specification and, with a trigger, makes the work waiting meanwhile, and a deferral by the researcher with a trigger makes the work waiting. *In the example:* the researcher is asked once whether the first-set result still supports $J$, and an answer of “unsatisfied” would return the recheck to open work. *Limits:* a mechanical check cannot be answered “establish satisfied”, cancellation needs a reason, and narrowing requires a new specification. A change in what a check reads is no reason to ask again; a new version is.

**Definition 5.10 (live question).** *What it is for:* it tells Equation 5.6 whether an unknown is covered by a question at this boundary. A question is live when, by the boundary's cutoff, it is queued for the researcher (`pending`) or presented and not yet answered (`asked`):

$$
\begin{aligned}
\operatorname{Asked}^{\mathrm{live}}_t(j,\chi):=\exists A\in H^a_t:\;&
\operatorname{class}(A)=\operatorname{class}(j,\chi)\\
&{}\land\ \operatorname{basisVer}(A)=\operatorname{basisVer}(\chi)\\
&{}\land\ \overline\tau_{\mathrm{avail}}(A)\le\vartheta_t\\
&{}\land\ \operatorname{state}_t(A)\in\{\texttt{pending},\texttt{asked}\}.
\end{aligned} \tag{5.10}
$$

The first two conditions match the question to this check and this basis version, and the third requires the question to be available no later than the cutoff. *In the example:* the recheck of $J$ counts as held only from the first boundary whose cutoff follows the question about it, and only until the researcher answers. *Limits:* a question registered after the cutoff counts from the next boundary, and every unknown needs its own live question. A question invalidated by a version change has not been answered, and it is asked again if the check is still undecidable. An executor's deferral grants no exemption from completion, and all waiting needs a trigger.

### Composition and established results

**Definition 5.11 (composition).** *What it is for:* it says when one application may build on the result of another (Section 4.4). Let $f$ and $g$ be applications, $x$ the input, $y$ the result of $f$, and $\kappa$ the purpose with its scientific conditions and review basis. The application $g$ is ready only when the conditions that $f$'s result carries and those that $g$ requires of its input are both established:

$$
\begin{aligned}
\operatorname{Ready}_{f\to g}(x,y\mid\kappa):={}&
\operatorname{Established}_{\kappa}\!\left(\operatorname{Post}_{f}(x,y)\right)\\
&\land\operatorname{Established}_{\kappa}\!\left(\operatorname{Pre}_{g}(y;\kappa)\right).
\end{aligned} \tag{5.11}
$$

*Limits:* an unchecked condition is not false, but it cannot authorize the next step, and compatibility of format is not a scientific premise. Universal composition would need more: a proved contract for the first application, satisfied premises, and outputs guaranteed to imply the premises of the second.

**Definition 5.12 (established result).** *What it is for:* composition (Equation 5.11) lets one result support the next only if that result is established for the purpose at hand. A proposition $\varphi$ is established for purpose $\kappa$ when one compatible bundle of current-version receipts passes every check the purpose declares for it:

$$
\operatorname{Established}_\kappa(\varphi):=\exists\rho\in\mathcal E_t(\varphi)\ \forall\chi\in D_\kappa(\varphi):\ s_{\chi,t}(\rho)=1 . \tag{5.12}
$$

$\mathcal E_t(\varphi)$ holds the qualified receipt bundles for the proposition, and $D_\kappa(\varphi)$ is its nonempty check set. As in resolution (Equation 5.5), the bundle is bound to one application, purpose and question. *In the example:* $A$'s advantage on the first set can motivate the re-appearance experiment only while receipts on the current version of the paper pass, and nothing established supports $A$ after re-appearance. *Limits:* a changed purpose or basis requires rechecking, and a vacuous implication from a false postcondition cannot authorize the next step. A check that vanished because a rule was switched off, a field became unreadable or a filter changed has not been evaluated.

### Scope, specification and requirements

**Definition 5.13 (ownership closure).** *What it is for:* it fixes the records a goal on a scope node is responsible for. Ownership $\operatorname{own}$ maps each record to one node of the scope tree. It follows from where the record lives, allows record-level overrides, and does not depend on how a scan is configured. $\operatorname{anc}^{*}(n)$ is a node with all its ancestors, and $\operatorname{ep}(k)$ says whether a record of a bounded goal is open or closed; other records count as open. The closure of node $n$ is the set of unclosed records owned by $n$ or its descendants:

$$
\operatorname{cl}(n):=\{\,k:\ \operatorname{own}(k)\ \text{is defined}\ \land\ n\in\operatorname{anc}^{*}(\operatorname{own}(k))\ \land\ \operatorname{ep}(k)\neq\mathrm{closed}\,\}. \tag{5.13}
$$

*Properties:* nodes that are not ancestors of each other have disjoint closures, and an ancestor's closure contains its descendant's. A closed goal generates no new requirements but remains available as evidence. *Limits:* a goal counts as closed only when its source records the closure and its closure receipt exists, so a bare closed flag is not enough. Moving a record changes neither its identity nor whether it is closed. The local ledger can refute a closure receipt but cannot establish one; a receipt missing from it is reported as unverifiable, not refuted. This definition does not prevent a forged receipt identifier, which is a deliberate source edit.

**Definition 5.14 (scope of a goal).** *What it is for:* it fixes everything a goal may read: the records it owns and a few declared inputs from elsewhere. The scope of $\varepsilon$ is the closure of its node $n_\varepsilon$ plus a finite, explicit set of cross-scope keys $\mathrm{Cr}_\varepsilon$. These keys may point only at the interface nodes $\operatorname{iface}(n')$ that other scopes declare, and the whole is evaluated at the moment of freezing:

$$
\mathrm{Sc}_\varepsilon:=\Bigl[\operatorname{cl}(n_\varepsilon)\ \cup\ \mathrm{Cr}_\varepsilon\Bigr]_{\vartheta_{\mathrm{freeze}}},\qquad
\mathrm{Cr}_\varepsilon\subseteq\bigcup_{n'\neq n_\varepsilon}\operatorname{iface}(n'),\qquad |\mathrm{Cr}_\varepsilon|<\infty . \tag{5.14}
$$

Freezing records the scope's extension and digest. A cross-scope key freezes together with the version of the interface it points at. Interface nodes come from record declarations, not from a registry. *In the example:* a goal that rechecks $J$ covers the unclosed records under its own node. A record of another project enters only as a cross-scope key, through an interface that project declares; a read that bypasses the interface lies outside the frozen scope.

**Definition 5.15 (specification).** *What it is for:* it fixes what a goal is answering and under which rules, so that completion is judged against something that cannot move during the run. The specification is compiled from the question, the permitted evidence and the permitted history, admitted like any candidate under the five conditions of admission above, and then frozen as an eight-tuple:

$$
\widetilde\Phi_\varepsilon=\operatorname{Compile}_{\omega_t}(q_t,\ e_t^a,\ H_t^a),\qquad
\Phi_\varepsilon=\bigl(q,\ \kappa,\ \mathrm{Sc},\ \mathsf{Ver},\ \mathcal P^{\mathrm{keep}},\ \alpha,\ \beta,\ \mathrm{sv}\bigr)_\varepsilon . \tag{5.15}
$$

The eight entries are the question $q$, purpose $\kappa$, scope $\mathrm{Sc}$, rule and check versions $\mathsf{Ver}$, preserved set $\mathcal P^{\mathrm{keep}}$, authority $\alpha$, budget $\beta$, and source versions with cutoff $\mathrm{sv}$. *In the example:* the specification fixes the question whether $J$ still holds after the correction, and its source versions record the paper at $v_2$. *Limits:* a specification cannot self-sign the authority and budget it carries. Broadening or narrowing a request, or adding a preservation condition, is the researcher's decision; otherwise existing authority applies.

**Definition 5.16 (budget).** *What it is for:* it bounds what a goal may spend before it must stop. The budget is specified componentwise. It has a finite allowance of decision boundaries, which also charges for waiting; allowances for questions and reopenings, and further components such as calls and tokens; and a frozen acquisition allowance $\mathrm{alloc}_\varepsilon(\chi)$ for each check:

$$
\beta_\varepsilon=\bigl(\beta^{\mathrm{bnd}},\ \beta^{\mathrm{ask}},\ \beta^{\mathrm{reopen}},\ \beta^{\mathrm{call}},\ \beta^{\mathrm{tok}},\dots;\ \mathrm{alloc}_\varepsilon\bigr). \tag{5.16}
$$

*In the example:* while the researcher has not yet answered the question about $J$, each boundary still spends the boundary allowance.

**Definition 5.17 (exhaustion).** *What it is for:* it is the exhaustion in Stop (Equation 5.20). A budget component is exhausted when its spent amount reaches its allocation:

$$
\operatorname{Exhausted}(\beta_\varepsilon,t):=\bigvee_{i\in\mathrm{comp}(\beta_\varepsilon)}\bigl[\mathrm{spent}^i_t\ge\beta^i_\varepsilon\bigr],\qquad \mathrm{bnd}\in\mathrm{comp}(\beta_\varepsilon). \tag{5.17}
$$

$\mathrm{comp}(\beta_\varepsilon)$ lists the components, and the boundary allowance is always among them. *In the example:* if the boundary allowance runs out while the re-appearance experiment is still simply unresolved, Stop holds and the outcome is budget_stopped.

**Definition 5.18 (requirement set).** *What it is for:* it makes a goal's work a function of what was frozen, so that a scan cannot add work the specification does not imply. The requirement set is given by a pure function $\operatorname{Req}$ of four frozen parameters. Here $\operatorname{gen}_{\kappa,r}$ generates a rule's requirements for one match $m$, and $\operatorname{keys}(m)$ is the set of inputs the match reads:

$$
\begin{aligned}
\mathcal Q_\varepsilon&:=\operatorname{Req}\bigl(\kappa_\varepsilon,\mathrm{Sc}_\varepsilon,\mathsf{Ver}_\varepsilon,\mathrm{sv}_\varepsilon\bigr),\\
\operatorname{Req}(\kappa,\mathrm{Sc},\mathsf{Ver},\mathrm{sv})&:=\bigl\{\,j:\exists r\in\mathsf{Ver},\ \exists m,\ \operatorname{keys}(m)\subseteq\mathrm{Sc},\ j\in\operatorname{gen}_{\kappa,r}(m\mid\mathrm{sv})\,\bigr\}.
\end{aligned} \tag{5.18}
$$

At run time, completion is computed over the registered set $\widehat{\mathcal Q}_\varepsilon\subseteq\mathcal Q_\varepsilon$. *In the example:* the recheck of $J$ belongs to $\mathcal Q_\varepsilon$ because a rule generates it from a match whose keys, $J$ and its source, the paper, lie in the scope. *Limits:* purity of $\operatorname{Req}$ in its four arguments is an implementation obligation, not a proved property, and the difference between $\mathcal Q_\varepsilon$ and $\widehat{\mathcal Q}_\varepsilon$ belongs to evaluation.

**Definition 5.19 (touched requirements of a goal).** *What it is for:* Equation 5.6 needs the touched set of Equation 5.2 restricted to one goal. It is:

$$
\mathcal F^{\varepsilon}_t:=\Bigl(\mathcal F^{\mathrm{scan},\varepsilon}_t\cup\{\,j\in\mathcal J^\kappa_t:\operatorname{dep}_t(j)\cap\mathcal C_t\neq\varnothing\,\}\Bigr)\cap\widehat{\mathcal Q}_\varepsilon,\qquad
\mathcal F^{\mathrm{scan},\varepsilon}_t\subseteq\mathcal Q_\varepsilon . \tag{5.19}
$$

Here $\mathcal F^{\mathrm{scan},\varepsilon}_t$ is what a scan run for this goal finds, and the second condition keeps it inside what the frozen specification implies. *In the example:* the correction to $v_2$ places the recheck of $J$ in $\mathcal F^\varepsilon_t$, and the re-appearance experiment, whose grounds do not involve the paper, stays out. *Limits:* an in-scope match that the run never evaluated is recorded as unevaluated work, $\mathcal Q^{\mathrm{cov}}_\varepsilon$ in Equation 5.20, which blocks completion. Touched requirements outside the scope stay unresolved globally, for a later goal.

**Definition 5.20 (Done and Stop).** *What it is for:* it says when a bounded goal is complete and when it stops (Section 4.4). With $\mathcal Q^{\mathrm{nr}}_\varepsilon$, $\mathcal Q^{\mathrm{bg}}_\varepsilon$ and $\mathcal Q^{\mathrm{cov}}_\varepsilon$ the requirements whose earlier specification cannot be reconstructed, the confirmations owed for direct edits that bypassed admission and the in-scope work the run never evaluated, exhaustion as in Equation 5.17 and $d_t$ the researcher's decision:

$$
\begin{aligned}
\operatorname{Done}_\varepsilon(t)&:=\bigl[\mathcal U^\varepsilon_{t+1}\subseteq\mathcal Z^{\mathrm{held}}_t\cup\mathcal Z^{\mathrm{wait}}_t\bigr]\\
&\qquad{}\land\ \bigl[\mathcal U^\varepsilon_{t+1}\cap(\mathcal Q^{\mathrm{nr}}_\varepsilon\cup\mathcal Q^{\mathrm{bg}}_\varepsilon\cup\mathcal Q^{\mathrm{cov}}_\varepsilon)=\varnothing\bigr],\\
\operatorname{Stop}_\varepsilon(t)&:=\operatorname{Done}_\varepsilon(t)\lor\operatorname{Exhausted}(\beta_\varepsilon,t)\lor[d_t=\mathrm{stop}].
\end{aligned} \tag{5.20}
$$

The outcome is read off at the first Stop. If Done holds, it is complete when nothing is unresolved and complete_with_held, with the share of $\widehat{\mathcal Q}_\varepsilon$ resolved, when held or waiting work remains, but deferred when that share is zero; otherwise it is budget_stopped or human_stopped. *Limits:* Done means that at the next boundary nothing in the goal is simply unresolved. The three non-exempt kinds may be held or waiting for a while but must close before completion, so a goal cannot end by default acceptance of its own conclusion. Later changes of ownership affect only the next goal, so closing a child goal or moving unfinished work out of scope cannot make the present one complete. Neither budget_stopped nor human_stopped reports completion.

**Example (a second bounded goal).** Take a request to check every citation in the method-comparison card. Its frozen specification sets the purpose, citation checking, the scope, the project's unclosed records, and the budget, twenty boundaries and three questions. The rule is that every citation resolves and its version matches; whether a retracted paper's citation may stay is the researcher's judgment. The run finds twelve citations: ten pass, and one, pointing to a retracted paper, becomes one bounded question. Another, in a shared card from another scope and only displayed here, derives no requirement and is listed as out of scope. If the researcher establishes with a reason that it may stay, the goal ends complete; if the researcher establishes that it may not, the requirement returns to open work and the goal does not complete. Unanswered, the question is listed with its reopening trigger and the goal ends complete_with_held; other answers follow Definition 5.9.

### Arguments for scope independence and finite progress

This subsection argues the two propositions of Section 4.4. The scope $\mathrm{Sc}_\varepsilon$, the frozen versions $\mathsf{Ver}_\varepsilon$ and the requirement function $\operatorname{Req}$ below are those of Equations 5.14, 5.15 and 5.18.

**Proposition 1 (scope independence).** Assume (i) $\mathrm{Sc}_{\varepsilon_1}\cap\mathrm{Sc}_{\varepsilon_2}=\varnothing$; (ii) each requirement identity carries its generating keys, with $\varnothing\neq\operatorname{keys}(j)\subseteq\operatorname{keys}(m)$; and (iii) rules do not use empty-key matches. Then $\mathcal Q_{\varepsilon_1}\cap\mathcal Q_{\varepsilon_2}=\varnothing$: completion accounting for either goal does not depend on requirements belonging only to the other. *Proof.* By (iii) and the definition of $\operatorname{Req}$, every $j\in\mathcal Q_{\varepsilon_i}$ arises from a nonempty match $m$ with $\operatorname{keys}(m)\subseteq\mathrm{Sc}_{\varepsilon_i}$. By (ii), $\operatorname{keys}(j)$ is nonempty and contained in $\mathrm{Sc}_{\varepsilon_i}$. By (i), no requirement belongs to both sets.

These conditions are sufficient, not individually necessary, and the premise concerns the full scopes, cross-scope keys included. When one goal reads the other's interface nodes, the two share inputs and must be checked together; when one scope is an ancestor of the other, their closures are nested. Global rules with empty-key matches apply to every scope and must be declared and counted separately. $\operatorname{keys}(m)$ must cover everything that match enumeration, requirement generation and checks read, with no hidden reads outside the scope. Under (i)–(iii), a new disjoint subtree that changes neither the four frozen parameters nor the inputs an existing goal reads leaves that goal's requirement set unchanged. In the example, a goal on an unrelated project neither adds to nor removes from the requirements of the goal that rechecks $J$. If it read the paper through an interface, the two goals would share an input and have to be checked together.

**Bounded stopping.** If $\beta^{\mathrm{bnd}}_\varepsilon<\infty$, $\operatorname{Stop}_\varepsilon$ holds within at most that many decision boundaries, because each boundary consumes one unit of that allowance.

**Definition 5.21 (progress measure).** *What it is for:* it counts the work still open, so that a run can be said to make progress. The measure is lexicographic:

$$
\begin{aligned}
\mu_t=\bigl(&|\widehat{\mathcal Q}_\varepsilon\setminus(\mathcal Z^{\mathrm{res}}\cup\mathcal Z^{\mathrm{cancel}}\cup\mathcal Z^{\mathrm{held}}\cup\mathcal Z^{\mathrm{wait}})_{\le t}|,\\
&\text{remaining acquisition budget},\ \text{remaining reopening allowance}\bigr).
\end{aligned} \tag{5.21}
$$

where $(\cdot)_{\le t}$ denotes the sets as they stand at boundary $t$. The first component counts the registered requirements that are not yet resolved, cancelled, held or waiting; the other two are what remains of the acquisition budget and of the reopening allowance. *In the example:* the recheck of $J$ leaves the first component once it is held, and returns to it if the researcher answers “unsatisfied”.

**Proposition 2 (finite progress, conditional).** Suppose the following. (H1) The frozen scope $\mathrm{Sc}_\varepsilon$ is finite: the scope tree is finite, each scope node holds finitely many records, and $\mathrm{Cr}_\varepsilon$ is explicit and finite. (H2) $\mathsf{Ver}_\varepsilon$ is fixed. (H3) Each check has a finite acquisition budget, requires human judgment, or has an out-of-scope blocking dependency. (H4) Dependency inputs do not change after freezing. (H5) Reopening is bounded by $\beta^{\mathrm{reopen}}$. (H6) Registration finishes in finitely many steps. (H7) Scope remains fixed until stopping. Suppose further the scheduling condition (S): the generated requirement set is finite, remaining budgets and reopening allowances are nonnegative integers, and every decision boundary returns. (S) also bounds effective steps consuming no boundary: none increases $\mu_t$ lexicographically, only finitely many leave it unchanged, and one that changes it decreases at least one component by 1. Then the run makes finite progress to Done, to the exhaustion of a budget component or to the researcher's decision to stop.

*Argument.* Under (S), an effective step consuming no boundary either leaves $\mu_t$ unchanged or lowers one of its nonnegative integer components by at least 1, without raising it lexicographically. Only finitely many steps leave it unchanged, so infinitely many steps without progress are excluded. The measure therefore yields finite progress to Done or to exhaustion. Bounded stopping comes separately from the boundary budget, not from the measure. The argument uses only (S); H1–H7 describe settings in which (S) is plausible, and H4 also rules out an admission inside the goal, such as the narrowed block of the example. Two steps the definitions allow show what the hypotheses guard against. Without a fixed scope, closing a child goal can artificially shrink the requirement set, while opening one can increase the first component. An answer establishing “unsatisfied” need not decrease that component either: it confirms real unfinished work, and the proper outcome remains budget_stopped or human_stopped until that work is resolved or legitimately cancelled.

**What is proved and what is not.** Proposition 1 proves that under (i)–(iii) two goals share no requirement, so that completion accounting for either does not depend on the other. It gives no cost bound: it does not establish that maintenance cost grows linearly with the number of projects, and this report makes no such claim. That cost also depends on the number of matches in each scope, the cost of each check, global rules and contention for shared resources. Bounded stopping guarantees stopping, not completion. Proposition 2 proves finite progress only under H1–H7 together with (S), and H1–H7 alone do not establish (S). Neither result shows that Done is reachable. Held items are excluded from the first component, while Done (Equation 5.20) still requires some held requirements to close, so the first component reaching zero does not by itself give Done. Completion would additionally require that every unresolved requirement can be decided within scope and budget without intervening source changes. These conditions generally fail in real research, so the report does not claim that completion is reachable.

## Supplementary Note 6. Implementation gaps in full


Table 4 in report Section 5.4 groups the most important of these by theme, with the same numbers. Each entry states the mechanism observed in the prototype and the validation that is still missing.

| No. | Gap and claim boundary |
| --- | --- |
| 1 | `ros admit` run outside a terminal, for example by an agent, on a judgment candidate or a reconfirmation, or an agent closing an episode card (`ros propose episode-close`), records `invoker_asserted` and writes, whereas terminal calls record the researcher's decision. Rule revision and closing a requirement with `ros decide … cancel/confirm` or `ros answer … cancel/satisfied` are accepted only at the terminal, and an agent's relay is recorded as `invoker_asserted` while the requirement stays open. An agent's after-the-fact `ros admit --confirm` of a block written without admission is likewise recorded as `invoker_asserted`, and that block's confirmation requirement stays open. Recording the channel does not enforce exclusive human admission. The terminal channel is recognized by an interactive prompt, so it attests the channel, not the person: a process that allocates a pseudo-terminal can answer it. |
| 2 | Dashboard lifecycle writes change state (and priority on reopening and on completion) without candidate, admission or preimage staging; shared client protection remains a target. |
| 3 | The contracts of governance and the code of coordination share one package, but admission is still carried out by `ros.py` rather than by that package; the stable kernel of Section 5.1 remains a target. |
| 4 | Confirmation uses differences at session end: unclosed edits enter the next baseline, cancellation does not roll back, and identity, cognition and confirmed-memory files receive only a summary line, without version-bound confirmation. The uniform tracking until confirmation required by Supplementary Note 1 is incomplete. |
| 5 | Notifications keep pending_review/closed rather than the kernel vocabulary; the alias mapping of Supplementary Note 1 is incomplete. |
| 6 | Unlabeled frontmatter travels as internal; the exclusion of unknown sensitivity required by Supplementary Note 1 is incomplete. |
| 7 | `ros today/state` outputs and agents' direct reads and disclosures lack receipts and remain unknown; disclosure receipts cover limited routes. |
| 8 | Internal cross-scope references are counted and reported, not blocked; the interface restriction on cross-scope keys (Definition 5.14 of Note 5) remains specified only. |
| 9 | Frozen bases and preimages protect the built-in conditions but do not verify preservation under arbitrary rules (Sections 4.1 and 5.2). |
| 10 | No complete execution consumer supports general successor, parallel or join checks. Blocking in a fixed pipeline cannot establish them: tests of chains, joins, exceptions, optional steps and invalid dependencies establish that pipeline's behavior, not scientific postconditions or the composition condition of Section 4.4. |
| 11 | Correction does not fully protect independently supported alternatives (Sections 2 and 5.4). Admission only adds judgment blocks, so the prototype can neither replace nor withdraw an existing judgment; the researcher has to edit or remove it by hand (Section 2). |
| 12 | A new kind of executable check requires a kernel change that needs architecture review; unsupported coverage blocks completion, and directories or examples establish neither end-to-end execution nor arbitrary composition. No built-in rule registers a condition the researcher states or an experiment the researcher plans, so such items stay in the definitions only and `ros close` does not list them (Section 5.4). |
| 13 | Six acceptance tasks remain uncompleted: recovering the mainline and next step, distinguishing waiting from staleness, understanding triggers, relation status, cancelling a no-write preview or refreshing its date, and exact-item Review with evidence and copy-only handoff. Historical captures and headless tests establish neither client integration nor usability. |
| 14 | Isolation of real models, long-run recovery experience and natural research benefit remain unverified by synthetic regressions. |
| 15 | Sessions only approximate bounded goals; specification freezing is incomplete (report Appendix B.2; Section 4.4). |
| 16 | The implementation requires a nonempty scope, so it may reject empty-scope completion that the definitions permit when no other requirements or unreturned runs remain. |
| 17 | No producer exists for waiting on an out-of-scope dependency, so that branch of the waiting definition (Definition 5.6 of Note 5) remains specified only; a deferral confirmed at the terminal does produce waiting (report Appendix B.2). |
| 18 | Unvalidated `answer:` holds can survive exhaustion of the question budget and yield complete_with_held on obsolete bases, violating the held condition (Definitions 5.6 and 5.10 of Note 5). The outcome also reports complete_with_held without testing the resolved share, so the zero-share rule (Definition 5.20 of Note 5) is specified only. |
| 19 | Evidence acquisition, calls and tokens are not fully metered, so the budget and exhaustion rules (Definitions 5.16–5.17 of Note 5) are not fully enforced. |
| 20 | Shared boundaries use the smallest session allowance; budgets of separate goals are not independently executed. |
| 21 | Only `ros` counts boundaries; direct callers self-report question allowances, without the same accounting guarantee. |
| 22 | Post-write boundaries exist for `ros admit` of a judgment or a rule, for closing an episode card (`ros propose episode-close`) and for `ros close` of a newly registered field confirmation, but not for `ros answer`, `ros attend` or `ros decide`. A manual `ros decide … reopen` has no cutoff, records `researcher_decision:reopen` at the terminal and `invoker_asserted:reopen` otherwise, and lies outside the budgeted reopening causes. The attribution and accounting of new requirements are therefore incomplete (report Appendix B.2). |
| 23 | When roots and members stay unchanged, an internal ownership move can be attributed to a source change, although the attribution rule gives a scope change priority. |
| 24 | Missing consumer hashes limit the attribution of source changes. |
| 25 | Only script checks are executed and semantic caching is absent, so semantic reruns remain specified only. |
| 26 | The satisfaction relation for scoring bounded goals with frozen sources and the final- or deadline-satisfaction relation of the development experiments have not been unified; both belong to the evaluation work left for later (Section 6.2). |
| 27 | The diagnostic interfaces proposed for evaluating a coordination policy specify inputs and outputs, not a complete benchmark or policy; general refutation, semantic dependencies and selection still need implementation and evaluation. |
| 28 | Deriving deployment fields and normalizing manifests cover only a subset of the specified obligation, without full acceptance of identity, versions, bases, authority, failures or effects; the obligation remains a specification. |
| 29 | Simplification, delegation and retirement have not been accepted through comparison with equally effective handoffs to strong models; the obligation remains a specification (Section 6.2). |
| 30 | Governance checks for duplicate semantic stores, queues and directories are incomplete, and parallel main plans are reviewed manually (Section 3). |
| 31 | The change classes C0–C3 of the architecture contract, C3 being a kernel change that needs architecture review, are unverified. Kernel admission requires safety or authority invariants, or at least three real capabilities sharing semantics plus C3 review, which acceptance stubs do not establish. The obligation remains a specification. |
| 32 | The context optimizer and the scientific-truth resolver are unimplemented. |
| 33 | Complete multi-user organization is absent; personal contracts do not specify team responsibility, consent or access arrangements. |
| 34 | File watching, recursive propagation, generic graph editing and Desk relation writeback, semantic support and compatibility checks and autonomous optimization lack a complete loop; bounded continuation establishes none of these. |
| 35 | Heuristics and extraction defects leave the semantic requirements of card maturity unimplemented. In the card inventory of 13 September 2026, 47 of 132 cards lacked I/R witnesses, which does not negate their recorded facts, and this result and the related tests are bounded evidence. |
| 36 | Pareto and cost-vector computation is absent; duplicate counts establish neither multidimensional preservation nor savings. |
| 37 | No general placement classifier exists; disposition based on ownership, identity, consumers and sensitivity remains a design contract. |
| 38 | Descriptor validation derives no complete semantics from arbitrary skill text; plugin integration remains a specification. |
| 39 | Joint-adaptation optimization and models of human development are unimplemented. |
