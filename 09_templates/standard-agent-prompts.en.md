---
type: prompt_template
title: "Standard ResearchOS Agent Prompts"
status: ready
created: 2026-06-27
updated: 2026-07-01
tags:
  - templates
  - prompts
  - onboarding
  - local-first
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="standard-agent-prompts.zh.md">中文</a>
</p>

# Standard ResearchOS Agent Prompts

These are the standard prompt templates for ResearchOS Public Starter. They are intentionally written as reusable protocols, not one-off experiment prompts.

Use them when you run the public starter with Codex CLI, Codex GUI, another local assistant, or an API-backed provider. Keep the same governance rule across all providers: materials can be private in your local workspace, but public-facing output requires an explicit export boundary.

## Prompt 0: Let An LLM Onboard You

Use this when you have just cloned the repository and want Codex, Claude Code, Gemini CLI, or another LLM assistant to guide you through the project.

### Short Default Prompt

Use this first when you want to save tokens.

```text
Read AGENTS.md only. Do not scan the repository.

Tell me:
1. my route;
2. the privacy/export boundary;
3. the one next file or command;
4. what you intentionally did not read.
```

```text
I just cloned ResearchOS Public Starter. Read AGENTS.md only, then decide whether Section 2 of docs/user-manual.en.md is needed. Guide me through the smallest safe first step.

Do not write files yet. First tell me:
1. What route I should take: learn the demo, start the dashboard, replace examples with my own material, create cards, process Inbox, or validate release readiness.
2. Which 0-3 files you need to read and why.
3. What privacy, evidence, or export boundary applies.
4. The next command or question, if any.
5. What you intentionally did not read to save tokens.
```

## Core Operating Protocol

Use this block at the start of any ResearchOS task.

```text
Use ResearchOS as a small, file-based research tool whose durable authority remains with the researcher.

Follow this order:
0. First decide whether the task needs repository context at all.
1. First give a concise judgment: what this task is asking for and why it matters.
2. Then state the evidence boundary: what comes from source material, what is candidate interpretation, and what needs user confirmation.
3. Then propose the next action: what to read, what to create, what to validate, and what should remain pending.
4. If the task involves long-term memory, people relationships, public export, submitted manuscripts, unpublished work, sensitive material, or private notes, produce candidate conclusions or candidate diffs only. Do not turn them into confirmed memory or public-facing content without explicit user confirmation.

Do not infer private relationships, advising status, student status, lab membership, future commitments, or contribution level unless the user provides explicit evidence.

Always mark each output with one of these states:
- candidate
- needs_evidence
- confirmed_by_user
- local_only
- public_safe
- not_exportable
```

## Prompt 1: First Profile Intake

Use this after the user fills an intake note.

```text
Read my intake note and create a Level 1 person card.

Use only the sources I listed. If a source is private, under review, unpublished, or local-only, you may use it for my local card, but mark every derived claim as local_only or not_exportable unless I explicitly say it can be public.

Output:
1. Person card title.
2. Public identity anchors.
3. Local/private identity anchors, if any, clearly marked local_only.
4. Candidate research themes.
5. Evidence used for each theme.
6. Missing evidence.
7. Export boundary.
8. Next smallest upgrade action.

Do not infer private relationships or future commitments.
```

## Prompt 2: First Paper Card

Use this for the first paper the user uploads or links.

```text
Create a Level 1 paper card from this paper material.

The paper may be public, private, submitted, under review, unpublished, or local-only. First classify its boundary:
- public_safe
- preprint_public
- submitted_local_only
- unpublished_local_only
- confidential_not_exportable
- unknown_boundary

If the paper is submitted, unpublished, private, or unknown_boundary, keep all analysis local_only and do not generate public-facing wording.

Output:
1. Title, year, authors, venue/status if known.
2. Source and boundary classification.
3. Short summary.
4. Contribution claims supported by the material.
5. Connection to the person card.
6. Candidate collaborator cards from the author list.
7. What cannot be inferred.
8. Next evidence needed.

Authorship only proves co-authorship. It does not prove supervision, friendship, lab membership, seniority, or future collaboration.
```

## Prompt 3: Collaborator Candidate Extraction

Use this after a paper card exists.

```text
Extract collaborator candidate cards from this paper's author list.

Use only authorship evidence and public metadata unless I provide additional evidence. Keep every person as a candidate until I confirm the relationship.

Output one candidate card per person:
1. Name.
2. Source paper.
3. Evidence type: co-author candidate.
4. What is known.
5. What is not known.
6. Sensitivity/export boundary.
7. Confirmation question for the user.

Do not infer advising, student status, private closeness, institutional relationship, or future work.
```

## Prompt 4: Second Paper Comparison

Use this when the user uploads a second paper.

```text
Create a card for the second paper and compare it with the first paper card.

First classify the boundary of the second paper. If it is submitted, unpublished, private, or unknown_boundary, keep the analysis local_only.

Compare:
1. Shared research themes.
2. Repeated authors or collaborator candidates.
3. Shared methods, datasets, problems, or evaluation ideas.
4. Possible project-family relation.
5. Evidence for each relation.
6. What remains only a candidate interpretation.
7. Smallest next action.

Do not upgrade a relation to confirmed unless the evidence or user confirmation supports it.
```

## Prompt 5: Talk Card

Use this for a public talk, slide deck, seminar abstract, or private talk note.

```text
Create a talk card from this talk material.

First classify the talk boundary:
- public_safe
- internal_local_only
- confidential_not_exportable
- unknown_boundary

Output:
1. Title, date, venue/audience if known.
2. Boundary classification.
3. Key message.
4. Linked person, paper, project, or theme cards.
5. Reusable claims, separated from paper evidence.
6. Evidence boundary.
7. Next use.

If the talk is internal or private, do not generate public-facing wording.
```

## Prompt 6: Project or Relation Card

Use this after there are at least three cards.

```text
Using the current person card, paper cards, talk card, and collaborator candidates, create one narrow project or relation card.

Separate confirmed facts from candidate interpretation.

Output:
1. Card title.
2. Cards used.
3. Evidence-backed links.
4. Candidate links.
5. Boundary of each source.
6. What this relation means in ordinary language.
7. What cannot be concluded.
8. One next action.
9. Validation check.

If any source is local_only or not_exportable, the resulting relation card is local_only unless I explicitly approve a public-safe version.
```

## Prompt 7: Card Maturity Review

Use this before writing a card into durable state.

```text
Review these cards using the ResearchOS maturity rubric.

For each card, classify it as:
- Level 1: seed card, useful but incomplete.
- Level 2: sourced card, main claims have evidence.
- Level 3: operational card, has relationships, next action, validation check, and export boundary.

Output:
1. Current level.
2. Evidence supporting the level.
3. Missing evidence.
4. Smallest upgrade action.
5. Whether it can be public_safe, local_only, or not_exportable.

Do not promote a card only because it is well written. Promote it only when the evidence and boundary are sufficient.
```

## Prompt 8: First Plan Card

Use this to turn cards into one actionable loop.

```text
Create one narrow plan card from the current person, paper, collaborator, talk, and relation cards.

Output:
1. Objective.
2. Cards used.
3. Evidence used.
4. Candidate interpretation.
5. Next action.
6. Owner.
7. Time window.
8. Blocker.
9. Validation check.
10. Export boundary.
11. Maturity level.

Keep the plan small enough to execute. If any input is submitted, unpublished, private, or not_exportable, keep the plan local_only.
```

## Prompt 9: Inbox / Handoff Processing

Use this when the dashboard or user creates a set of pending candidates.

```text
Process the ResearchOS inbox or handoff queue.

First summarize every pending item:
- type
- title
- target file or target card
- user instruction
- evidence state
- sensitivity/export boundary
- whether it can be safely executed now

Processing rules:
1. Process only pending items. Do not revive archived, withdrawn, or completed items unless the user asks.
2. For confirmations: accept can write to a candidate target; reject must follow the user's correction; uncertain stays as needs_evidence.
3. For new material: register first; do not treat an attachment filename as readable evidence unless the file path is available.
4. For paper fields: verify stage, public boundary, and evidence before writing.
5. For people: check sensitivity and boundary before writing any relationship card.
6. For groups: preserve useful experience before dissolving or restructuring.
7. Submitted, unpublished, sensitive, and private materials default to local_only.
8. Public-facing output requires explicit public_safe approval.
9. After writing, rebuild generated data and run validation.

Output:
- inbox overview
- execution plan
- item-by-item result
- files changed
- validation result
- questions for the user
```

## Prompt 10: External Request Routing

Use this before replying to an invitation, collaboration request, talk request, review request, proposal opportunity, or similar external demand.

```text
I received this external request: [paste request].

Use ResearchOS to decide how I should respond. Read AGENTS.md, docs/reference/AGENT_PROTOCOL.md, and 05_workflows/research_management/external-demand-response-workflow.md.

Output:
1. Request type.
2. Source facts from the request.
3. Relevant ResearchOS assets.
4. Fit judgment.
5. Missing information and risks.
6. Privacy/export boundary.
7. Recommended response stance.
8. Draft response only if safe.
9. Candidate memory to log.

Do not infer availability, private closeness, advising status, contribution hierarchy, or future commitment unless the user gives explicit evidence.
```

## Prompt 11: Relationship Opportunity Routing

Use this when a person, paper, event, institution, topic, or project might become a research opportunity.

```text
I want to know whether this signal creates a research opportunity: [person/paper/event/project/topic].

Read AGENTS.md and 05_workflows/research_management/relationship-opportunity-workflow.md first. Add docs/reference/AGENT_PROTOCOL.md and one matching template only if a card/update is needed.

Output:
1. Confirmed public facts.
2. Candidate links.
3. Related assets.
4. Opportunity routes.
5. What cannot be inferred.
6. Sensitivity/export boundary.
7. Recommended next action.
8. Candidate card or update target.

Do not infer advising, student status, lab membership, private closeness, contribution hierarchy, future collaboration, or willingness to be contacted.
```

## Boundary Rule for Private and Submitted Materials

ResearchOS can help you work with private, submitted, under-review, or unpublished material in your own local/private workspace. That is different from committing the material to a public repository or exporting public-facing claims.

Use this default:

| Material state | Local analysis | Public export |
| --- | --- | --- |
| Public paper/page | Allowed | Allowed after evidence check |
| Public preprint | Allowed | Allowed with version/status label |
| Submitted or under review | Allowed locally | Not allowed unless explicitly cleared |
| Unpublished draft | Allowed locally | Not allowed by default |
| Confidential review/student/person material | Allowed only if appropriate locally | Not allowed |
| Unknown boundary | Treat as local_only | Not allowed |

When unsure, mark the card `local_only` and ask the user to confirm the export boundary.

## Agent Summary

Standard public-safe ResearchOS prompt templates for profile intake, paper cards, collaborator extraction, second-paper comparison, talk cards, relation cards, maturity review, plan cards, inbox/handoff processing, external request routing, and relationship opportunity routing.
