---
type: reference
title: "ResearchOS System Reference"
status: active
updated: 2026-10-28
sensitivity: public
---

<p align="right">
  <strong>English</strong> | <a href="system-reference.zh.md">中文</a>
</p>

# ResearchOS System Reference

This reference defines what this repository's surfaces, states and governance boundaries mean, how the kernel and its extension ports are arranged, which code owner handles which concern, and where public-safe content belongs. Read the code map below before modifying or debugging code: choose one runtime flow and one owner file, and do not begin by scanning every JavaScript file, generated JSON or alternate-language document. How to use the system is in the [User Manual](user-manual.en.md); publication, customization and plugins are in the [Governance and Extension Guide](governance-guide.en.md).

## What the system is

ResearchOS is a small, file-based tool for individual researchers who want to preserve judgment continuity across tools, projects and time. Skill-readable Markdown with an agent client such as Claude Code or Codex, or another file-aware CLI, is the primary execution route; the deliberately narrow local Dashboard is the persistent attention and control surface. This repository demonstrates mechanisms and stores no non-public research memory. Skill and agent use, Dashboard visualization, provider output and agent output are candidates or operating surfaces, never long-term authority.

This repository is a small, file-based reference tool that separates the research workflow into explicit Markdown layers: identity and direction, knowledge materials, decision records, cognition methods, people context, workflows, active state, public exports and templates. Configuration, scripts, validators and the deliberately narrow Dashboard support those layers. It is not for storing sensitive content and demonstrates three mechanisms. Candidate and confirmation are separated: agent-generated content enters a candidate layer first. Evidence and action are separated: materials, interpretations and next actions are tracked distinctly. Public and non-public boundaries are separated: exportable content must come from fictional, sanitized or explicitly approved sources.

This repository has no sibling private-repository discovery, federation catalog, cross-system execution, or shared runtime state. Its task extensions are local declarative descriptors that reuse the kernel; they are not connectors to a maintainer's private systems. A reusable private method may enter this repository only after it has been rewritten as a domain-neutral candidate with no source identity, path, runtime evidence, or transferred authority. ResearchOS is not a hosted service, autonomous scientist, all-in-one research platform or polished consumer application; “OS” names the project and its explicit operating rules and does not claim platform breadth.

```text
Now: allocate attention across several Commitments, one next step per item
  -> Library: use one or a few Commitments as a lens over public-safe context
  -> Item-local Work: open the exact Commitment's bounded session through a copyable task packet
  -> source card + task-conditioned working deck when needed
  -> item-local Work result or skill/agent task
  -> next action or optional artifact on demand
  -> Item-local Review for results, proposed durable change, validation boundary, and continuity handoff
  -> evidence + sensitivity review
  -> researcher decision
  -> validated public-safe output
```

## Primary route and supporting surfaces

| Surface | Role | What to inspect |
| --- | --- | --- |
| `Skill/Agent` | Daily agent-assisted reading, structuring, drafting, validation and writeback proposals. | Agent Protocol, context budget, standard prompts, selected-language Markdown. |
| `Now` | Projects a multi-Commitment attention portfolio. | Several Commitments may be visible; each keeps one disposition and one next safe action. It does not become a generic backlog or runtime control room. |
| `Library` | Uses one or a few Commitments as a lens over public-safe materials, projects, people, reports and relations. | Lens selection is ephemeral and preserves provenance and relation type; Library adds context without creating a candidate and is not a second project database. |
| item-local Work | Opens the exact selected Commitment's bounded session, thread, run and result inside Now, with the item's goal, sources, artifacts, process record and working deck. | It is a drawer, not a third screen. This repository only prepares copyable task packets, starts no local or remote executor and never claims execution. |
| item-local Review | Shows the exact selected item's results, artifacts, proposed durable changes, human disposition, validation boundaries, receipts and continuity handoff. | Missing or ambiguous item identity fails closed; Public never claims that it wrote or validated canonical memory. |
| `Preview` | File, candidate and evidence preview. | How Markdown is read. |
| `Agent` | Handoff and capability state. | This repository is copy-only; all execution belongs to personal-vault mode or the prototype in the technical report. |

Claude Code, Codex or another file-aware agent is the primary execution surface. The Dashboard is the persistent attention and control surface: it shows fictional or local Work Items by when their next step should take attention again (Today, Tomorrow, Future and Parked), while Markdown remains authoritative. It is not a second chat or an Agent prerequisite. Generated JSON files feed the Dashboard, and validators check configuration, the provider registry, generated starter data and public-release boundaries. This repository is copy-only, as set out in [User Manual Section 4](user-manual.en.md#4-the-optional-dashboard): scheduling, completion and durable writeback remain disabled, and its controls demonstrate the same interaction grammar without pretending to mutate data.

Skill and agent work is the execution route for deep reading, edits, artifacts and validation; ChatGPT-style assistants may support open discussion. The Dashboard has one Unified Desk with Now and Library semantic areas rather than becoming a second editor. Now allocates attention: it holds the complete Today list, one current research focus, the month and week calendar, every active or waiting project and the exact item-local Work and Review drawers. A review date or external event may bring a waiting or paused project back for judgment without making it executable. Library connects public-safe sources, people, claims, evidence, threads and artifacts through at most a few explicit Commitment lenses and contains no calendar or project-status board. A project remains a long-lived container, and its single current next step is the schedulable Work Item. The calendar consumes explicit dates only, and selecting an event returns to its exact item without owning lifecycle writes. Work/Review separates bounded execution, returned results, candidate changes, human disposition, mutation and validation state, receipts and continuity handoff only inside an exact item, and the drawer preserves the exact session and run identity.

The authority protocol and durable memory do not depend on the Dashboard. Plugins may contribute domain projections and bounded actions only. The shell owns navigation; Work Session, Review, admission and storage safety are kernel protocols; the `research_portfolio` capability owns Project and Commitment lifecycle and attention. Now and the calendar project those states without owning their persistent authority, and a public calendar change remains an unsaved preview. `Start / Today / Agent`, `Assets`, `Next`, `Work` and `Review / Inbox` are input-only aliases. Item-bearing Work and Review routes open `Now?item=<id>&panel=<work|review>`; missing identity fails closed, and output uses canonical IDs. The public demo uses fictional items and a copy-only handoff; what it and the personal-vault mode may run and write is set out in Sections [3](user-manual.en.md#3-the-session-scheduler-and-command-line-checks) and [4](user-manual.en.md#4-the-optional-dashboard) of the User Manual.

Review state is time-bounded: re-adding an action clears its archive or resolved mask, and an older completed run must not process a request added later. The UI language is a browser preference, while the active prompt and template language is frozen when the projection is generated.

## Shared governance boundaries

This section explains the shared protocol and its current kernel behavior. This repository remains copy-only with fictional data and a `copy_only` handoff; describing a protocol does not enable private write services.

**Needs Review.** Reception includes results, artifacts, candidates, validation failures, rollback, and handoff boundaries that must be settled before task closure. It also includes bounded questions that evidence cannot decide and break-glass confirmation requests. A bounded question offers finite answers for the researcher. Break-glass confirmation closes that requirement only; it does not retroactively authorize the modification. Ordinary notifications, all tasks, material browsing, plugin or provider status, raw run logs, calendar ordering, rescheduling and reversible short-term states do not enter Review merely because they exist.

**Requirement states and completion.** `open / deferred / waiting / resolved / cancelled` form a requirement axis separate from Run, Session, Attention and Portfolio. Deferred and waiting requirements remain unclosed and need a reopening trigger; a due trigger returns them to `open`, and a missing trigger counts as open. The protocol permits `deferred` only through a direct researcher decision with a reason and a date or event trigger, confirmed at the local terminal. Agent-supplied parameters are not researcher confirmation. A non-terminal `decide defer` is recorded as `invoker_asserted`, rather than rejected, and does not count toward completion; terminal confirmation records `researcher_decision`.

The ledger records three cases under the status `waiting`: a bounded question awaiting an answer, which the report calls held; a researcher's triggered deferral or narrowed scope; and a blocking dependency outside the frozen scope. Only the last two are waiting in the report's sense, and the current kernel has no producer for the outside-scope dependency case. An unanswered question is held for human judgment; it is not an authorized deferral. Waiting because of an in-scope dependency and executor-asserted deferral do not count toward completion. For Done, the waiting set recognizes researcher-channel deferral or narrowing, including terminal-confirmed `decide defer`. An unclosed requirement for an unrecomputable previous specification (`spec:`), break-glass confirmation (`field:` and the existing bindings), or unknown in-scope coverage always keeps Done false, even if deferred, waiting, or awaiting an answer. A permitted wait does not resolve the requirement.

**Context egress.** When a cloud session agent reads a `ros context` packet, the packet leaves the machine even though that agent is not a provider. Public and internal sources may be delivered within a researcher-started session for the requested commitment or card, without another confirmation. Sensitive sources require the researcher's own confirmation at the local terminal each time; agent-supplied flags do not count. Private and unknown sensitivity are excluded. A private commitment ledger may explicitly declare selected fields as internal on the source itself; undeclared fields and titles remain private, the requested commitment id travels with the request, and the declaration does not downgrade the source. Sensitive or unknown sources cannot use that exception.

Each delivery records the destination service, purpose, included sources and excluded sources. An unidentified destination remains unknown. Direct agent file reads and other command outputs, including `ros today` and `ros state`, are outside this delivery record; their egress is unknown, not proven covered. Revocation stops later deliveries and cannot retrieve prior ones. Session delivery permission does not authorize publication; this repository's safe-export policy and `copy_only` boundary still apply.

## State and authority model

ResearchOS does not use one overloaded status field to mean everything:

| Axis | Representative states | Authority meaning |
| --- | --- | --- |
| Workflow | `active`, `processed`, `archived`, `withdrawn` | Operational progress only. |
| Evidence | `candidate`, `needs_evidence`, `supported`, `contradicted`, `bounded` | Support and uncertainty, not write-back. |
| Authority | `proposed`, `approved`, `written_back`, `validated`, `reverted` | Whether canonical memory changed and whether that change passed validation. |
| Sensitivity | `public_safe`, `internal`, `private`, `local_only` | Where the material or derived claim may travel. |

A source path identifies input evidence; it is not a save target. A completed task remains candidate evidence unless a separate evidence decision is recorded. Approval does not become validated write-back without an explicit target and validation result. Workflow, EvidenceState, Authority, Sensitivity and EvidenceKind are defined only by `researchos-primitive-contract-v1.json`; views and app orchestration must not own another state enumeration.

## Kernel and extension architecture

The stable kernel is the authority and result protocol, not the number of Dashboard features. Ordinary task routes use declarative extensions; reviewed first-party capabilities use static adapters, candidate registries and stable Utility, Library, Workbench or Review ports. Both reuse the existing Work Session, the `answer / artifact / writeback` modes, the Review boundary, the language freeze and the public-safety gate, and neither may create a second executor, Inbox, storage system or writeback path. This repository is conversation-first: `conversation_contract.py` owns result and confirmation boundaries, `repository_layout.py` declares the personal-vault layers and `plan_context.py` is the direct agent route, while the Dashboard only displays a public-safe projection and handoff. Generated JSON, demo data and agent output never gain durable authority, and writeback to a personal vault requires user confirmation.

### Product layers

The minimum product is the direct conversation core: a goal, the minimum relevant sources, the `answer / artifact / writeback` result protocol and human confirmation. It needs neither the Dashboard nor an installed extension. `researchos-plugin-v1` is one shared technical host, not proof that every manifest is an optional user plugin, and every native manifest under `config/plugins/` declares its `product_tier`:

| Product layer | Meaning | Current examples |
| --- | --- | --- |
| Minimum conversation core | Completes `goal → minimum source → answer/artifact/diff → human confirmation` without starting the Dashboard; it is not a plugin | context router, source authority, `answer / artifact / writeback`, confirmation and safety boundaries |
| `foundation_projection` | Supplies the optional Dashboard's Unified Desk, semantic areas and item presentation; owns neither conversation tasks nor canonical authority | `material_pipeline`, `research_assets`, `research_portfolio` |
| `bundled_capability` | Ships with a distribution and is invoked on demand; disabling it leaves the minimum conversation loop intact | folded `system_stewardship` |
| `optional_extension` | Installed only from explicit natural-language intent; absent by default and reversible | the `method_comparison` example |

"Works with zero plugins" therefore means that direct conversation work requires zero `optional_extension` entries. It does not mean the Dashboard stays complete after its foundation owners are removed. `system_stewardship` is a folded maintenance capability, not a first-run owner. Installable extensions must remain local, reversible and network-free, cannot write canonical memory, and cannot add a top-level page, a second conversation loop or a parallel state owner. Ordinary users do not need these labels; manifests, validators and this reference enforce the boundary.

The core-owned `researchos_plugin_capability_v1` is a non-installable prototype. Canonical capability claims are stable identities; concrete manifests contribute replaceable implementations, and tasks are entrypoints, workflow adapters or evaluation probes. The enforced chain is `claim -> contribution -> task projection -> episode evidence -> admission receipt`, and equal strings never create an implicit identity edge. External skills stay as linked, versioned, licensed source candidates until one real capability gap and a current-model baseline justify adaptation or multi-source composition. ResearchOS has no raw-copy mode and does not become a plugin pile. A validated contribution may later be absorbed by a foundation owner or, through separate architecture review, by the stable kernel. See [Plugin Standard v1.2](../05_workflows/research_management/researchos-plugin-standard-v1.2.md). The plugin system is frozen and its modules keep their current owners; what that permits is stated once in the [governance guide](governance-guide.en.md#task-extensions-and-plugins).

### Stable kernel

In the technical report's terms this is the target stable kernel (Section 4.2, gap 3). In the prototype the session kernel is `scripts/ros.py` with `scripts/researchos_kernel/`.

| Invariant | Stable meaning | Extensions must not |
| --- | --- | --- |
| Source authority | Confirmed Markdown plus explicit human confirmation is authoritative. | Treat generated JSON, provider output or plugin state as truth. |
| One work loop | Intent enters one Work Session and returns a visible result. | Add a parallel composer, result loop or handoff queue. |
| Result protocol | `answer` is read-only, `artifact` creates a requested file, `writeback` proposes durable change. | Invent another result mode or turn an answer into silent writeback. |
| Candidate protocol | Durable, sensitive, public or destructive changes pass Review. | Write canonical memory directly from a view or provider. |
| State ownership | UI preferences, runtime ledgers, canonical Markdown and projections have separate owners. | Add ad hoc storage keys or a parallel Inbox. |
| Attention grammar | One current Work Item may be today, carryover, upcoming, unscheduled, waiting, paused, needs-next-step or completed. | Treat the whole project as a calendar event or silently replace the original scheduled date. |
| Language and release boundary | Only the active template language is emitted; public extensions fail closed. | Load frozen-language prompts or expose unsafe content. |

The Candidate protocol row describes one use of Review; its full reception scope, given under [shared governance boundaries](#shared-governance-boundaries), also covers bounded unknowns and break-glass confirmation.

### Extension ports

| Port | Owner | Expected change radius |
| --- | --- | --- |
| Repeated task | `config/extensions/*.json` or ignored `config/extensions.local/*.json` | One descriptor, validation, rebuild. |
| Plugin host, governance and ownership overlay | `scripts/researchos_data/plugins.py`, `plugin_governance.py`, `plugin_ownership.py`, frontend and style manifests | Fail-closed manifest, lineage, effects, admission, runtime availability, ownership and contribution metadata; no arbitrary manifest-loaded code. |
| Reviewed candidate adapter | `plugin-runtime.js`, a reviewed first-party plugin module and `candidate_envelope.py` | The plugin owns domain normalization, generation and withdrawal; Review consumes one envelope. |
| Manifest-gated surface dependency | `plugin-runtime.js` plus one named surface or dependency provider | A plugin supplies bounded read-only domain computation to an existing surface; disabling the manifest removes it. |
| Work Item provider | Plugin manifest plus one reviewed projection adapter | Supplies identity, lifecycle, single next step and optional real deadline to the shared Now surface without creating a route. |
| Registered inline action | Complete five-field action contract plus a platform-owned handler | Low-risk reversible session or attention writes may execute inline; durable content still routes to Review. |
| Direct-dialogue route | `scripts/plan_context.py` | No task-specific Python branch for a valid descriptor. |
| Provider | `scripts/researchos_adapters/provider_registry.py` and provider config | Provider adapter, config and tests only. |
| Data projection | One builder owner | Builder, contract, fixture and projection test. |
| Dedicated UI | model, workbench, view and style plus a registered render adapter | Only at level C4 of the [extension ladder](governance-guide.en.md#extension-ladder); no new Work Session, Inbox or storage protocol. |

One JSON descriptor declares the task, read tiers, result modes, workspace, sensitivity, authority boundary and paired language copy, and both the Dashboard builder and `scripts/plan_context.py` consume it. Without this port a repeated task would require edits to a task catalog, prompt routing, workspace mapping, copy, validation and documentation even when the authority model does not change. The bundled example is disabled by default, so a fresh starter runs without any extension task. Task extension v1 is deliberately declarative and does not load arbitrary Python or JavaScript plugins; a code-plugin API would require a new major core API, a migration plan, a sandbox and security model and release tests. An extension appears in the existing task selector and direct context router, without first-screen prominence or a dedicated panel.

Compatibility rules for descriptors and manifests:

- `core_api_version` must be `"1"`; unknown major versions fail closed.
- Existing v1 actions remain compatible. If an action declares any v1.1 action field, it must declare all of `confirmation_mode`, `risk`, `write_scope`, `reversible` and `public_behavior`.
- `confirmation_mode: inline` requires `execution: platform_registered`; a manifest cannot make arbitrary client code a trusted writer.
- Public Work Item actions must declare `demo_only` or `disabled` behavior unless a separately reviewed public-safe handler exists.
- Extension versions use semantic `x.y.z` form, and IDs and aliases cannot shadow core routes.
- Empty read tiers, duplicate routes or aliases, directory targets and symlinks that resolve outside the repository fail before build.
- `requires_human_confirmation: true`, `writeback_route: review` and `storage_owner: researchos_core` are machine-enforced constants, not advisory prose.
- `quick`, `standard` and `evidence` retain 1/5/8 first-pass file limits; later tiers retain earlier reads.
- A descriptor available in `public_starter` must be `public_safe` and default to `public`, `public_safe` or `local_only`.
- When `task.read_locales` or `authority.locales` is present, both `en` and `zh-CN` are required, and only the selected language's reads and authority wording enter the task packet. Both task-copy language blocks are stored, but only the selected language enters generated task data.
- A public extension fails closed if any declared Markdown read target explicitly carries `internal`, `sensitive`, `private` or `not_exportable` frontmatter.
- All durable writeback continues through the existing Review and confirmation path.
- Checked-in manifests explicitly declare distribution parity, source lineage and transformation, real deployment, research effects, data and export policy, composition, routing, maturity proof and retirement. Legacy local manifests receive only conservative compatibility defaults.

If an ordinary task extension requires edits to `dashboard/app.js`, `dashboard/index.html`, Work Session state, Inbox stores or storage contracts, stop. Either the feature is a C4 interface or data capability on the extension ladder, or the task port is incomplete. This change-radius gate is the practical test that the kernel stays stable as users customize the starter.

### Evolving the architecture

Splitting files further is not the default refactoring strategy. The target dependency direction is:

```text
Application Shell
  -> Capability Slices
       -> Platform Adapters
            -> Stable Kernel
```

The stable kernel owns only the authority, result, admission, run-state, context-release, Work Session, Review, request and storage-safety contracts. Platform adapters own source readers, projection builders, HTTP clients and shared UI primitives. One capability slice owns the model, view, workbench, copy keys, style, payload schema, behavior tests and retirement condition for one user job. The application shell owns only startup, workspace composition, render scheduling and failure recovery. The `core/services/components/views` directories can stay as they are: first declare in the manifest which capability, platform or kernel boundary owns every module, and consider physical moves only after the dependency graph is stable. Promote logic into shared or core code only when it is a security invariant or at least three capabilities reuse it with the same meaning. A feature must not read another feature's DOM, browser state or internal model directly.

`material_pipeline` is the first cross-stack capability plugin validated on the candidate-adapter boundary. Material intake, material upgrade and research scout keep their domain inputs, but a reviewed first-party adapter normalizes them into one `CandidateEnvelope` before Review, and the unified Inbox and Codex handoff consume the envelope rather than branching on raw fields. The registry is not an arbitrary code loader: manifests declare runtime availability, safety, permissions and candidate types, while adapter implementations remain statically loaded, reviewed first-party modules. This repository shares the host, adapter, envelope, endpoint shape and browser behavior, and its server still rejects durable canonical material writeback. Disabling the plugin removes its contribution without creating another Inbox, Review flow or storage owner. No old rule module, `ActionInboxStore` owner or core type branch exists beside the registry, so it is not a permanent dual-write layer. Two other ports have been validated on the same boundary: `research_assets` owns the Library projection, composition actions and group and dissolution candidates, and `research_portfolio` owns the actionable first-screen projection and the full lifecycle board in Library; the Now and Library shells do not calculate those domain states. No external connector has been validated: a Zotero or iPad bridge, or an evidence-reading bridge, needs its own source-adapter, permission and uninstall review.

Change classes, which are distinct from the extension-ladder levels, route each change:

| Class | Default route | Boundary |
| --- | --- | --- |
| C0 content or projection refresh | canonical source -> existing builder | no kernel or frontend edit; generated diff shown separately |
| C1 repeated task | task-extension descriptor | no app, index, Inbox or storage edit |
| C2 capability evolution | one capability slice | slice owners, payload contract, behavior test |
| C3 kernel change | explicit architecture review | invariant, migration, compatibility removal, release proof |

C2 and C3 changes record the user job, existing owner, replace or merge decision, dependency direction, human and generated change radius, removal condition, private and public boundary, and verification. The following signals detect accumulation and are not targets for mechanical code golf. The active frontend count is an observed signal, not a fixed ceiling: every owner must stay registered, within its line budget and inside a bounded capability change radius, and C3 additions must name the owner they replace, split or make independently switchable. `app.js` global dependencies and top-level functions may only decrease, and not by hiding them behind wrapper or service-locator indirection. New validation prefers behavior, schema, authority and safety boundaries; source-token checks are reserved for load order, forbidden constructs and release boundaries. Generated projections stay separate from human-authored diffs, and the parity divergence allowlist must exactly match real divergences.

Migrations follow an order. Keep capability slices declared in the manifest rather than moving files to signal architecture. Reuse the proven Utility, Library, Workbench, candidate and surface-dependency ports before adding a new port. Keep the startup projection small, with a bootstrap envelope as the target, and load heavy capability payloads only when evidence justifies it. Sync files shared with the prototype in the technical report in a staged step, run public safety and parity checks before any public write, and never push automatically. When a slice migrates, replace implementation-token checks with behavior, schema or authority tests and delete the obsolete check in the same batch. Consider feature directories or a bundler only when physical movement reduces a measured dependency problem. Split a migration that simultaneously changes the kernel, more than one capability, storage semantics and private or public divergence. Do not add an abstraction without naming the owner it removes, and return an abstraction to its capability slice if no second real consumer appears within two requests.

## Code map

`scripts/ros.py` → `scripts/researchos_kernel/` + `scripts/researchos_adapters/` → versioned records and receipts. The kernel owns state-transition rules and the pure protocol contracts (admission state, candidate envelope, context and handoff receipts, task envelope, result and rule evolution); adapters supply source snapshots, staged writes (`filesystem_staging.py`), run state (`run_state.py`), the context pack (`context_pack.py`), provider dispatch (`dispatch.py`) and the launch boundary that dispatch and the Dashboard runner share (provider registry, configuration and profiles, the execution port and its local CLI adapters, permission profiles and the Policy Gateway); `ros.py` is the command-line client over both. Dependencies point inward: the kernel imports nothing outside itself and the adapters import nothing from `researchos_server/`, which `scripts/validate_agent_architecture.py` enforces. The optional Dashboard follows `scripts/serve_dashboard.py` → `dashboard/src/services/` → views. Generated data is a projection, and a view or provider cannot become a source of authority.

To change code, reproduce the problem through a public entrypoint, select the owner from the table below, read that owner and only its direct collaborators, keep generated data, provider output and Dashboard state separate from Markdown authority, and run the smallest relevant test before the release gates if the change crosses a public boundary. The default code-reading depth is L1: this map, the entrypoint and one owner module. Use L2 for direct collaborators, and a broad L3 read only for an explicit architecture or release audit.

```text
Demo or personal startup
  scripts/start_researchos.py
    -> scripts/build_public_starter_data.py
    -> scripts/researchos_data/task_extensions.py
    -> scripts/researchos_data/plugins.py
    -> scripts/researchos_data/plugin_governance.py
    -> scripts/serve_dashboard.py
    -> dashboard/index.html
    -> dashboard/src/* owner modules
    -> dashboard/app.js orchestration

Auto-update
  dashboard maintenance client
    -> scripts/researchos_server/evolution_planner.py
    -> scripts/researchos_server/auto_update_runner.py
    -> scripts/researchos_data/maintenance_pipeline.py
    -> documented public commands
```

The demo writes `08_exports/public_starter/generated-public-starter-data.json` and `dashboard/data/researchos-dashboard.json`. Personal-vault mode writes `dashboard/data/researchos-local.json`, which is local-only, git-ignored and must never be committed. These files are projections, not editing authorities. The default public demo may display a public-repository-only evolution plan but cannot execute it. Personal-vault mode uses the same UI action contract as the prototype in the technical report: allowlisted local maintenance and a locally installed Codex CLI may execute, while durable writeback still follows the current confirmation boundary. Maintenance grows through the [controlled self-evolution control plane](self-evolution-control-plane.en.md), not autonomous self-modification.

| Concern | Primary owner | Read next only when needed |
| --- | --- | --- |
| Mode selection and one-command startup | `scripts/start_researchos.py` | `scripts/serve_dashboard.py`, runtime config validator |
| Demo and personal-vault projection | `scripts/build_public_starter_data.py` | onboarding Markdown, data-contract templates |
| Research Agenda projection | `scripts/research_agenda_projection.py` | fictional demo agenda or local `06_active_context/research-portfolio.md` |
| Controlled maintenance planning | `scripts/plan_evolution.py`, `scripts/researchos_server/evolution_planner.py` | `scripts/validate_evolution_control.py`, maintenance manifest |
| HTTP routes and server composition | `scripts/serve_dashboard.py` | one matching `scripts/researchos_server/*.py` module |
| HTTP authentication and JSON request boundaries | `scripts/researchos_server/request_security.py`, `http_json.py` | `dashboard/src/services/request-auth.js`, handler integration evals |
| Provider schema and status | `scripts/researchos_adapters/provider_registry.py`, `provider_config.py` | `config/researchos.runtime.example.json` |
| Cross-client execution contracts | `dashboard/src/services/task-intent.js`, `dashboard/src/services/result-envelope.js`, `scripts/researchos_kernel/task_envelope.py`, `scripts/researchos_adapters/policy_gateway.py`, `scripts/researchos_adapters/provider_adapter.py`, `scripts/researchos_adapters/filesystem_staging.py`, `scripts/researchos_adapters/run_state.py`, `scripts/researchos_kernel/result_contract.py` | TaskIntent is untrusted; TaskEnvelope separates request from actual runtime; Policy Gateway alone issues and revalidates short-lived machine grants; Provider Adapter executes bounded provider requests; Filesystem Staging owns the working copy plus promotion, compensation and rollback receipts; Run State durably reserves idempotency before provider dispatch and reconciles only by exact correlation; Result/Error expresses machine outcomes and public-safe recovery; public projections strip private envelopes. None of these contracts owns long-term authority |
| Conversation capability, typed routing and material boundary | `scripts/researchos_data/conversation_contract.py`, `task_router.py`, `capability_registry.py`, `repository_layout.py`, `public_conversation_catalog.py` | `scripts/plan_context.py` is primary; route receipts never grant execution or write authority |
| Markdown metadata profile | `scripts/researchos_data/metadata_profiles.py` | metadata-profile data contract and its eval; read-only projection, never a Markdown writer |
| Declarative task DIY | `config/extensions/*.json`, `scripts/researchos_data/task_extensions.py` | `scripts/plan_context.py`, task extension schema and validator |
| Plugin host, governance, documentation, portfolio and logical ownership | `scripts/researchos_data/plugins.py`, `plugin_governance.py`, `plugin_docs.py`, `plugin_ownership.py`, `plugin_portfolio.py` | `scripts/query_plugin_portfolio.py`, plugin and governance schemas, `docs/plugins/`, frontend and style manifests, `scripts/validate_plugin_standard.py`, `scripts/validate_plugins.py` |
| Bundled example lifecycle | `scripts/manage_plugins.py`, `scripts/researchos_data/plugin_lifecycle.py` | Git-ignored local manifests, plugin validation, Dashboard rebuild |
| Codex execution and usage reporting | `scripts/researchos_server/codex_runner.py` | `scripts/researchos_adapters/command_runner.py`, frontend runner client |
| Low-redundancy runtime and storage advisories | `work_session_upload.py`, `runtime_retention.py` | no arbitrary attachment quota or auto-deletion; compact logs and clean only owner-generated `.tmp` files |
| Local Markdown preview and write bridge | `scripts/researchos_server/local_file_bridge.py` | preview file server and matching eval |
| Runtime-read allowlist and file projection | `scripts/researchos_server/runtime_read_boundary.py`, `config/public-runtime-read-manifest.json` | preview and source-tree consumers and runtime-read evals |
| Inbox, card groups, cleanup and review state | matching `*_store.py` in `scripts/researchos_server/` | matching frontend client or workbench |
| Frontend data loading and service calls | `dashboard/src/services/*-client.js` or `dashboard-data-client.js` | server route owner |
| Frontend state and durable preferences | `dashboard/src/core/*.js` | the view or workbench consuming that state |
| User interaction logic | matching `dashboard/src/services/*-workbench.js` | matching view |
| Rendered surface | matching `dashboard/src/views/*.js` | component and style file for that view |
| Shared visual primitive | `dashboard/src/components/*.js` | the consuming view |
| Plugin frontend contributions | `dashboard/src/plugins/*.js` | the matching manifest in `config/plugins/`, frontend manifest |
| Copy and language | `dashboard/src/core/ui-copy*.js`, `i18n*.js` | paired documentation only if meaning changes |
| Page composition | `dashboard/index.html` | referenced source module |
| Application orchestration | `dashboard/app.js` | owner module; do not add feature logic here first |
| Public safety | `scripts/validate_public_safety.py` | governance and safe-export docs |
| Agent architecture drift | `scripts/validate_agent_architecture.py` | this map and the affected owner |

### Common changes

To add or change a card field, update the relevant Markdown or data contract, the projection builder, the matching frontend model, workbench and view, and one regression test, keeping source fact, candidate interpretation, confirmation and generated display state distinct. To add an HTTP endpoint, register the route in `scripts/serve_dashboard.py`, put its behavior in one `researchos_server` owner module, add one frontend client, and test both success and boundary failure; the route must not make generated data authoritative. To change a Dashboard interaction, start in the matching view and workbench, put reusable state in `core`, network and file behavior in a client and rendering primitives in `components`, and keep `app.js` to composition and event wiring. To add a provider, update the provider registry, provider config validation, the runtime example, the provider section of the User Manual and the tests together; a provider is an execution adapter and never owns memory writeback or confirmation. To add a public workflow, first ask whether an existing workflow or template can absorb it; if not, add one selected-language pair, link it from the smallest route table and do not create a second onboarding path. To add a repeated task route, start from `config/extensions/method-comparison.example.json`; a valid descriptor is consumed by both `build_public_starter_data.py` and `scripts/plan_context.py`, so do not add task-specific branches to `dashboard/app.js`, Work Session, Inbox or storage.

### Freeze rules and boundaries

A new feature must extend or replace one existing owner and must not create a parallel Work, Library, Review or onboarding main path. A compatibility adapter must include a migration regression and a removal condition, and the old branch is deleted after migration instead of keeping two meanings indefinitely. Modules shared with the prototype in the technical report are byte-identical by default; only files registered as divergent in that prototype's parity registry may differ, for privacy, fixture or runtime reasons. Before adding code, check whether an old branch can be removed or merged, and if `app.js`, an owner or a documentation route keeps growing, extract responsibility or converge the route instead of raising its budget.

Markdown materials, explicit user confirmation and documented rules are authority inputs; Dashboard JSON, runtime stores, provider responses and agent output are projections or candidates, and `dashboard/data/researchos-dashboard.json` is generated demo data. `scripts/researchos_data/` contains the supported runtime owners `maintenance_pipeline.py`, `task_extensions.py`, `plugins.py`, `plugin_governance.py`, `plugin_docs.py`, `plugin_lifecycle.py`, `plugin_ownership.py`, `conversation_contract.py`, `capability_registry.py`, `plugin_portfolio.py`, `task_router.py`, `repository_layout.py`, `metadata_profiles.py` and `public_conversation_catalog.py`, plus the read-only frontend and style manifests used by validation. The three headless owners `capability_registry.py`, `plugin_portfolio.py` and `task_router.py` only read declarative contracts and emit non-effectful receipts or grouping projections; they own no provider, command, storage, Dashboard or canonical write. `plugin_docs.py` owns the machine-checked per-plugin README contract and public-documentation leak checks and does not read plugin runtime data. `plugin_governance.py` validates capability lineage, effects, composition, routing and admission but owns no runtime state. `plugin_lifecycle.py` is reachable only through `scripts/manage_plugins.py` and manages only bundled examples in Git-ignored local directories. Research Agenda parsing is a documented top-level projection owner, not a compatibility helper. Do not add `fake-*`, `walkthrough` or `example-original-developer-*` cases: the architecture validator rejects them, and the starter keeps a single onboarding route.

`frontend_manifest.py` declares every active JavaScript owner. The source tree must exactly match the active manifest, and each owner is registered once in `index.html` and loads before `app.js`; architecture validation computes the count, so documentation does not repeat it. `style_manifest.py` owns every stylesheet under `dashboard/styles/`, and unreferenced side-path styles are forbidden. Reintroducing a removed UI module requires a user job, a replacement map, private and public boundaries and regression evidence.

### Maintainability budgets

`dashboard/app.js` may orchestrate but must stay at or below 2,600 lines, and the gate is not relaxed to make room for new patches; Work Session lifecycle and first-screen action sequencing live in existing workbench owners, so new behavior keeps moving down or replaces an old branch. `scripts/serve_dashboard.py` should stay below 650 lines, with route behavior in `researchos_server`. `scripts/build_public_starter_data.py` should stay below 1,060 lines; extract a public, tested owner before adding a second responsibility. A normal frontend owner stays at or below 1,500 lines, and the bilingual literal-data owner `ui-copy.js` has a 3,200-line ceiling. `scripts/ros.py` stays at or below 2,100 lines. A `researchos_kernel` owner stays at or below 750 lines, a `researchos_adapters` owner at or below 600 and a `researchos_server` owner at or below 1,200. Every `dashboard/src/**/*.js` file is registered exactly once in `dashboard/index.html`, and a public Python entrypoint must not import removed or unsupported compatibility modules.

### Low-redundancy runtime contract

Work Session resume history keeps at most ten summaries rather than full chat transcripts, and other browser-side lists also need explicit item limits. In personal-vault mode and the prototype in the technical report, user-selected session attachments have no product-level size, count or age quota, and the ceiling is the local filesystem and runtime; the public demo accepts files of up to 1 GiB each. Attachments are never deleted automatically because of a storage threshold, and uploads stream to disk. Runner JSONL compacts after 5 MB to the newest 80 merged run states, drops prompts and limits retained outputs. Public demo mode rejects every runner submission ([User Manual Section 4](user-manual.en.md#4-the-optional-dashboard)). Demo and Dashboard JSON are overwriteable, rebuildable projections, not append-only history databases. Completed session attachments remain under the user's control, and startup removes only `.tmp` fragments created by the upload owner. Substantial session copies or low local free space produce a non-blocking storage receipt, and an advisory must never delete material or disable adjacent features.

### Local HTTP endpoints

The local endpoints serve the Dashboard on `127.0.0.1` and are not internet APIs. In the public demo, every endpoint that writes or runs an update returns 403 `public_starter_writeback_blocked` and runs only in personal-vault mode, and every `/codex-runner` submission fails closed. The reads that start local work (`/model-catalog`, `/evolution-plan`, `/provider-status`, `/codex-runner`, `/source-tree` and `/source-info`) refuse requests that the browser marks as coming from another site. What the public demo may write is in [Section 4 of the User Manual](user-manual.en.md#4-the-optional-dashboard).

| Endpoint | Method | Role |
| --- | --- | --- |
| `/session-config` | GET | Report the runtime mode and the per-session request token. |
| `/data/researchos-dashboard.json` | GET | Serve the demo projection (the personal-vault projection in personal-vault mode). |
| `/preview` | GET | Preview Markdown. |
| `/pdf`, `/corpus/*.pdf` | GET | Serve an allowlisted PDF for preview. |
| `/source-tree` | GET | Inspect the demo source tree. |
| `/source-info` | GET | Inspect file metadata. |
| `/provider-status` | GET | Report this repository's `copy_only` capability; no local provider is probed. |
| `/model-catalog` | GET | List model choices; this repository starts no process to refresh it. |
| `/evolution-plan` | GET | Show the read-only maintenance plan. |
| `/codex-runner` | GET/POST | GET exposes sanitized status; every POST here fails closed with `public_starter_copy_only`. |
| `/maintenance-action` | POST | Run one registered maintenance action ID; arbitrary commands are rejected. |
| `/work-session-upload` | POST | Save a selected source into the local Git-ignored session workspace; this repository does not send it to a model. |
| `/open-local-file`, `/reveal-local-file` | POST | Open an allowlisted document with its default app, or show it in the file manager. Scripts are never opened, only revealed. |
| `/feedback` | POST | Save demo feedback. Public demo: 403; personal-vault only. |
| `/material-intake-inbox` | POST | Save a local material clue and handoff without uploading or copying the source file. Public demo: 403; personal-vault only. |
| `/auto-update` | POST | Run a local maintenance update. Public demo: 403; personal-vault only. |
| `/confirmation-withdraw`, `/upgrade-inbox`, `/scout-inbox`, `/card-groups`, `/group-dissolutions`, `/clear-inbox`, `/evolution-decision`, `/research-scout` | POST | Personal-vault writes and actions. Public demo: 403. |

## Files and directories

| Path | Purpose | Note |
| --- | --- | --- |
| `README.md` / `README.zh.md` | What the project is, one try-it path, boundary, document map, license. | Keep to one screen and link to docs. |
| `AGENTS.md` | Agent and LLM entrypoint. | Keep at the repository root so assistants can find it. |
| `docs/user-manual.en.md`, `docs/system-reference.en.md`, `docs/governance-guide.en.md` | The three guides, each paired with `.zh.md`. | One owner per topic; do not add a parallel guide. |
| `docs/reference/AGENT_PROTOCOL.md` | Agent reading, safety and writeback protocol. | Do not bypass confirmation. |
| `docs/reference/CONTEXT_BUDGET_PROTOCOL.md` | L-1–L3 reading ladder and budget modes. | Do not default to evidence or raw layers. |
| `docs/reference/WHERE_TO_PUT_NEW_MATERIALS.md` | Placement for raw, derived, workflow, active, export and template layers. | Do not mix raw material and derived notes. |
| `docs/reference/SAFE_EXPORT_POLICY.md` | Public-safe admission rules. | Contains no exception for sensitive export. |
| `docs/reference/PUBLIC_RELEASE_CHECKLIST.md` | Pre-release checklist. | Use with validators. |
| `LICENSE.md` / `docs/reference/COMMERCIAL_USE.md` | Source-available research license, academic redistribution allowance and commercial authorization boundary. | Keep consistent with the README. |
| `researchos.config.yml` | Dashboard host, port and language. | No API keys. |

| Directory | Put here | Do not put here |
| --- | --- | --- |
| `00_identity/` | Public positioning, principles, profile templates. | Real identity, institutions, private contact details. |
| `01_knowledge/` | Public-safe material indexes, reading notes, project knowledge. | Raw corpus, unpublished manuscripts, email or chat logs. |
| `02_decisions/` | Public-safe decision logs, judgments, tradeoffs and confirmation records. | Real collaboration, student, review or grant strategy. |
| `03_cognition/` | Methods and protocols: evidence boundary, confirmation flow, context budgeting. | Private streams of thought. |
| `04_people/` | Fictional people, public-safe personas, de-identified role templates. | Real relationship records or private contact details. |
| `05_workflows/` | Material intake, asset-type extension, lifecycle, task routing, agent collaboration, group composition, expression and self-evolution workflows. | Workflows that require private accounts or secrets. |
| `06_active_context/` | Public demo current state, next steps, risks. | Real private task lists or long history. |
| `07_archive/` | Older public notes, replaced templates, expired demos. | Material that was not public-safe originally. |
| `08_exports/` | Public demo, teaching and release materials, after safe export. | Content that has not passed safe-export review. |
| `08_exports/public_starter/` | One guided onboarding case plus card-maturity examples. | Real names, institutions, unpublished manuscripts, local paths. |
| `09_templates/` | Markdown skill format, frontmatter, card, prompt and validation templates. | Templates filled with sensitive real content. |
| `09_templates/data_contracts/` | Dashboard, case, validation, relation, capability and extension field conventions. | Real runtime data or secrets. |
| `config/` | Credential-free runtime configuration (`ros.json` sets `runtime_scope: public_starter`, so this repository only offers a copy fallback and admits nothing into the durable sources), provider fields for the prototype in the technical report, case switch. | `.env`, API keys, private endpoints. |
| `config/plugins/` + `scripts/manage_plugins.py` | Local, reversible plugin manifests and lifecycle. | Remote installation or canonical write authority. |
| `corpus/` | Empty boundary notes for raw materials. | PDFs, email, chat logs, webpage dumps. |
| `distilled/` | Public-safe short summaries and transferable principles. | Compressed private long-term memory. |
| `evals/` | Public-safe validation examples and smoke-test formats. | Evaluations built from sensitive real materials. |
| `dashboard/` | Local frontend: `data/` holds the demo projection, `src/` the modular source, `styles/` the styling. | Private projections. |
| `scripts/` | Startup, generation, validation and maintenance; `researchos_kernel/` holds the state-transition rules and protocol contracts, `researchos_adapters/` the source snapshots, staged writes, run state, context pack and provider launch boundary, `researchos_server/` the Dashboard server's stores and runner, `researchos_data/` the narrow set of reachable owners listed above. | Secrets or machine-specific paths. |
| `docs/` | Paired English and Chinese guides, the report and reference policies. | Unpaired reader documents. |

The `08_exports/public_starter/` cases feed the public demo projection by default; maintainers can switch them off as described in [Section 5 of the User Manual](user-manual.en.md#5-your-own-material), and disabled examples remain as reference-only guides. A new user's own material goes in the git-ignored `personal_vault/`, which uses the same layer layout; `08_exports/public_starter/onboarding-step-by-step.md` is the first-run guide from the demo to a personal vault. Add people, projects, talks and deeper reading only after the first result has been reviewed. A repeated new class such as email, external surveyed papers, peer-review assignments, budget, compute or dataset access that needs its own lifecycle goes through the [extension ladder](governance-guide.en.md#extension-ladder), `05_workflows/research_management/asset-type-extension-workflow.md` and `09_templates/data_contracts/researchos-extension-contract-v1.md` before any directory, template, script or Dashboard surface is added.

Official entry documents are paired by language instead of duplicated inside one agent-readable file, and each paired file carries a top-right language switch to its counterpart. Lower-level demo and case records are selected by `public_starter.content_language`: the builder includes English files for `en`, Chinese `.zh.md` files for `zh-CN` and neutral files for both. Alternate-language files remain reference-only. The builder also freezes task templates and assistant prompts to the selected content language, and generated Dashboard data does not carry the inactive language's prompt and template variants, so switching the UI language cannot silently add them to context. Change `content_language` or pass `--language`, then rebuild, to move prompts and templates to another language.

ResearchOS files are written as skill-readable Markdown, not only as human notes. Use the current card templates in `09_templates/`, such as `project-template.md` and `paper-template.md`, for frontmatter, the Agent Summary and evidence boundaries.

## Validation

Run the smallest relevant eval while editing. For architecture and extension changes the core checks are:

```bash
python3 scripts/validate_task_extensions.py
python3 scripts/validate_plugins.py
python3 scripts/validate_plugin_standard.py
python3 scripts/validate_agent_architecture.py
python3 scripts/validate_public_safety.py
python3 scripts/plan_context.py --list --lang en
python3 scripts/build_public_starter_data.py
python3 -m unittest discover -s evals -p 'test_*.py'
```

Before release, run every step of `.github/workflows/validate.yml`, which is the CI for this repository; because `CITATION.cff` already carries the release date, run `validate_release_metadata.py` locally with `--expected-commit "$(git rev-parse HEAD)" --require-clean` on a committed, clean working tree, since without them it fails. Then start a clean copied folder and complete one Dashboard run and one small personal-vault run.
