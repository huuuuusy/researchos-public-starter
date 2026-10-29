---
type: workflow
title: "Relationship Opportunity Workflow"
status: ready
created: 2026-07-01
updated: 2026-07-01
tags:
  - relationship
  - opportunity
  - collaborator-candidates
  - public-safe
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="relationship-opportunity-workflow.zh.md">中文</a>
</p>

# Relationship Opportunity Workflow

## Agent Summary

This workflow helps a user evaluate whether a person, paper, event, project, or weak signal creates a research opportunity. It turns scattered context into candidate routes without inferring private relationships or future commitments.

## When to Use

Use this workflow when the user asks:

- "Does this person connect to my work?"
- "Is this event worth following up on?"
- "Which assets support this collaboration idea?"
- "Should I create a person, relation, project, or plan card?"

## Read First

1. `AGENTS.md`
2. This workflow file.
3. `docs/reference/AGENT_PROTOCOL.md` only if the user wants a card written or updated.

Read templates, task matrix rows, or source cards only when the user gives a concrete name, paper, project, event, or topic and asks for a card/update.

## Process

1. Identify the signal:
   - person
   - paper
   - shared topic
   - event
   - project
   - institution or group
2. List confirmed public facts.
3. List local-only or sensitive context, if any.
4. Search for related ResearchOS assets.
5. Propose opportunity routes:
   - read more
   - create candidate person card
   - create relation card
   - create project or plan card
   - draft outreach
   - defer and watch
6. State what cannot be concluded.
7. Ask for confirmation before writing or publicizing.

## Output Contract

```text
Signal:
Confirmed public facts:
Candidate links:
Related assets:
Opportunity routes:
What cannot be inferred:
Sensitivity/export boundary:
Recommended next action:
Candidate card or update target:
```

## Do Not Infer

Authorship, shared topic, institutional overlap, or conference co-presence does not prove:

- advising;
- student status;
- private closeness;
- lab membership;
- contribution hierarchy;
- future collaboration;
- willingness to be contacted.

## Validation

If the workflow creates a card, mark it as `candidate` until the user confirms the relationship and boundary.

## Agent Summary

Public-safe workflow for converting person, paper, event, project, or topic signals into candidate opportunity routes without over-inferring private relationships.
