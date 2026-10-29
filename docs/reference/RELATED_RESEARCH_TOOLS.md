<p align="right">
  <strong>English</strong> | <a href="RELATED_RESEARCH_TOOLS.zh.md">中文</a>
</p>

# Related Research Tools and Resource Lists

ResearchOS is one option among many research tools. It may fit researchers who want a local, file-based authority protocol around long-term AI-assisted work. It will not fit every researcher or every task. A literature manager, notebook, electronic lab notebook, reproducibility platform, research agent, or smaller combination of tools may fit better.

This page makes that choice space visible instead of treating adjacent projects as something to hide.

> **Snapshot:** last reviewed on **2026-07-25**. This is a selective, non-ranked reference list, not an exhaustive directory, endorsement, procurement recommendation, or promise of continuous updates. Project capabilities, licenses, maintenance status, data practices, and security conditions can change. Check each official source before adopting it. Inclusion is not approval; omission is not criticism.

## Choose by the problem you actually have

| Primary need | Start with | Where ResearchOS may add value |
| --- | --- | --- |
| Automate search, experiments, analysis, or report writing | Research agents and execution runtimes | An external review and durable-writeback boundary |
| Ask cited questions over papers or web sources | Literature and source workspaces | Carrying reviewed judgments across projects |
| Give an agent cross-session memory or a knowledge graph | Memory and knowledge infrastructure | Deciding what may become authoritative research memory |
| Manage references, notebooks, data, experiments, or lab records | Mature lifecycle and reproducibility tools | Linking selected decisions without replacing those tools |
| Exchange machine-readable provenance or research packages | RO-Crate, PROV-O, and related standards | Mapping local authority transitions to shared vocabularies |
| Survey the wider AI-for-research landscape | Curated Awesome and survey repositories | A smaller, explained set of adjacent choices |

## Research agents and execution runtimes

| Project | Current emphasis | Consider it when | Check before adopting |
| --- | --- | --- | --- |
| [ResearchClaw](https://github.com/ymx10086/ResearchClaw) | Local-first research runtime for projects, workflows, claims, evidence, experiments, channels, and automation | You need a broader execution surface and persistent service | Alpha status, deployment, provider cost, and permission scope |
| [Agent Laboratory](https://github.com/SamuelSchmidgall/AgentLaboratory) | Multi-agent workflow for literature review, experimentation, and report writing, with a copilot mode | You want to explore an end-to-end research pipeline | Supported tasks and models, compute cost, and human verification of experiments and citations |
| [The AI Scientist](https://github.com/SakanaAI/AI-Scientist) | Research prototype spanning ideas, experiments, figures, papers, and automated review | Automated scientific discovery is itself your research subject | Generated outputs are not validated scientific findings |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | Deep web research and source-linked report generation across model and data providers | Your main need is a bounded research report | Search/API dependencies, source quality, citation checking, and data handling |
| [Mira](https://github.com/MIRA-Intelligence/mira) | Lightweight assistant tailored to medical-AI research execution | You want narrower domain-specific support | Domain coverage, sandbox behavior, dependencies, and medical-data boundaries |

## Literature and source workspaces

| Project | Current emphasis | Consider it when | Check before adopting |
| --- | --- | --- | --- |
| [Open Notebook](https://github.com/lfnovo/open-notebook) | Self-hostable notebooks, sources, chat, and transformations | You want to read, organize, and ask questions over a source collection | Model/storage configuration, parsing quality, and citation granularity |
| [SurfSense](https://github.com/MODSetter/SurfSense) | Research workspace over web and connected sources, with API and MCP access | You need many source connectors in one searchable space | Connector permissions, authentication, external data transfer, and team boundaries |
| [PaperQA2](https://github.com/Future-House/paper-qa) | Scientific-document RAG and cited question answering | You need answers grounded in a paper collection | Corpus coverage, retrieval settings, and whether each citation supports the claim |
| [STORM / Co-STORM](https://github.com/stanford-oval/storm) | Multi-perspective knowledge curation, discussion, mind maps, and cited reports | You want to explore a topic or curate it with an AI system | Search sources, factual review, and the boundary between one discussion and durable judgment |
| [OpenScholar](https://github.com/akariasai/openscholar) | Retrieval-augmented scientific literature synthesis, retrieval, and evaluation resources | You study or deploy scientific QA and synthesis methods | Index resource requirements, API dependencies, and evaluated versus intended use |

## Agent memory and local knowledge infrastructure

These are mostly components or general workspaces, not one-for-one ResearchOS substitutes.

| Project | Current emphasis | Consider it when | Check before adopting |
| --- | --- | --- | --- |
| [SwarmVault](https://github.com/swarmclawai/swarmvault) | Local Markdown/wiki, knowledge graph, RAG, and durable agent memory | Multiple coding agents need a readable local knowledge base | Confirmation of generated content, rebuildable indexes, and migration |
| [PilotDeck](https://github.com/OpenBMB/PilotDeck) | Task-oriented agent workspaces, white-box memory, and multi-project routing | You need a general agent workspace across projects and clients | Always-on permissions, workspace isolation, and rollback semantics |
| [Mem0](https://github.com/mem0ai/mem0) | User, session, and agent memory layer | You are developing an agent that needs cross-session memory | Open-source versus hosted features, default model dependencies, privacy, and deletion semantics |
| [Letta](https://github.com/letta-ai/letta) | Platform for stateful agents with advanced memory | You are building agents that preserve and modify long-term state | Agent memory-write authority, deployment mode, and long-term data governance |
| [Graphiti](https://github.com/getzep/graphiti) | Real-time, temporal knowledge graphs for agents | Changing entity relationships and time-aware retrieval matter | Graph/model dependencies, extraction errors, and fact-update policy |

## Research lifecycle and reproducibility

| Project | Current emphasis | Consider it when | Check before adopting |
| --- | --- | --- | --- |
| [Zotero](https://github.com/zotero/zotero) | Reference collection, citation management, PDF reading, and sync ecosystem | Your main problem is a literature library and citations | Sync, plugin compatibility, attachments, and group-library boundaries |
| [JupyterLab](https://github.com/jupyterlab/jupyterlab) | Extensible interactive and reproducible computing environment | Notebooks, code, terminals, and data analysis are central | Environment locking, execution order, dependencies, and notebook reproducibility |
| [DVC](https://github.com/treeverse/dvc) | Data versioning, pipelines, and ML experiments | You need to track large data, models, and experiment artifacts | Remote storage, team workflow, and data access control |
| [OSF](https://github.com/CenterForOpenScience/osf.io) | Open-science projects, registrations, materials, and collaboration | You need to share, register, or archive research work | Public/private settings, institutional policy, compliance, and preservation |
| [Renku](https://github.com/SwissDataScienceCenter/renku) | Collaborative, reproducible analysis across data, code, and compute | You need configured compute environments for researchers, teams, or courses | Deployment complexity, compute resources, connectors, and platform governance |
| [eLabFTW](https://github.com/elabftw/elabftw) | Open-source electronic lab notebook and laboratory records | Experiments, templates, inventory, or lab operations are central | Compliance, backups, access control, signatures, and institutional deployment |

## Provenance and research-object standards

| Project or standard | Current emphasis | Consider it when | Check before adopting |
| --- | --- | --- | --- |
| [RO-Crate](https://github.com/ResearchObject/ro-crate) | JSON-LD packaging of research data, code, documents, and context | You need machine-readable, exchangeable research packages | Profile selection, vocabulary mapping, validation, and repository support |
| [W3C PROV-O](https://www.w3.org/TR/prov-o/) | W3C Recommendation for provenance using entities, activities, and agents | You need cross-system provenance semantics | Whether the full ontology or a smaller mapped subset is appropriate |

ResearchOS does not present its provenance fields as a new standard. If cross-system exchange becomes necessary, explicit mappings to established standards are preferable to inventing an isolated vocabulary.

## Broader curated lists

| Collection | Coverage |
| --- | --- |
| [Awesome-AI-Research](https://github.com/Research-Equality/awesome-ai-scientists) | Layered map of AI-native research systems, infrastructure, workflow modules, benchmarks, surveys, and datasets |
| [Awesome-AI-Scientists](https://github.com/tsinghua-fib-lab/Awesome-AI-Scientists) | Survey-linked organization of AI Scientist roles, human-AI collaboration, domains, and broader impacts |
| [Awesome AI for Science](https://github.com/ai4s-research/awesome-ai-for-science) | Broad cross-disciplinary collection of AI-for-science tools, papers, datasets, frameworks, and applications |

These collections are better places to browse a broad and changing field. ResearchOS keeps this smaller page to disclose alternatives, explain categories, and help a reader decide where to start. It does not duplicate a continuously maintained Awesome repository.

## Why ResearchOS remains narrow

ResearchOS is useful only when this contract matters:

```text
bounded sources and local Markdown
  -> file-aware agent reads and proposes
  -> researcher reviews evidence and impact
  -> explicit approved writeback
  -> validation
  -> durable research memory
```

ResearchOS governs durable research state: who owns a judgment, what may change, what evidence supports the change and how work resumes after an interruption. It does not compete with broad research runtimes such as ResearchClaw, overlaps strongly with local Markdown and graph workspaces such as SwarmVault while narrowing governance to long-term judgment and writeback authority, avoids becoming a general agent platform such as PilotDeck, and supplies no domain experiment stack such as Mira's. Its defensible claim is the assembled authority contract: a file-aware agent may read and propose, but only an explicit, researcher-approved, validated transition becomes durable research memory. That is an engineering design claim, not evidence of superior productivity.

If a mature tool above already solves your actual problem, use it or combine it with other tools. ResearchOS does not require replacing them. Its narrower role is to preserve researcher-owned judgment across AI-assisted tasks and to make candidate, evidence, authority, privacy, and writeback boundaries explicit.

Corrections and additions are welcome through an issue or pull request. A proposed entry should identify its category, official source, main use, and the main adoption boundary a researcher should check.
