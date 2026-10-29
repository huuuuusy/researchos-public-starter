---
type: workflow
title: "External Demand Response Workflow"
status: ready
created: 2026-07-01
updated: 2026-07-01
tags:
  - external-demand
  - opportunity
  - response-drafting
  - public-safe
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="external-demand-response-workflow.zh.md">中文</a>
</p>

# External Demand Response Workflow

## Agent Summary

This workflow helps a user handle an external request, invitation, collaboration email, review request, talk request, proposal opportunity, or similar demand. It routes the request through ResearchOS assets before drafting a response, while keeping private or uncertain context as candidates only.

## When to Use

Use this workflow when the user says:

- "I received this invitation. Should I respond?"
- "Can ResearchOS help me decide whether this collaboration fits?"
- "Find my related assets before I reply."
- "Draft a response, but first check the boundary."

## Read First

1. `AGENTS.md`
2. This workflow file.
3. `docs/reference/AGENT_PROTOCOL.md` only if the response may write or update files.

Read actual cards, the task matrix, or templates only after the request category is clear.

## Process

1. Classify the request:
   - collaboration
   - talk or seminar
   - proposal or grant
   - review or service
   - media/public writing
   - teaching or mentoring
   - unclear opportunity
2. Extract source facts from the request.
3. Search for related ResearchOS assets.
4. Separate confirmed facts from candidate interpretation.
5. Identify missing information and risks.
6. Decide the response stance:
   - accept
   - decline
   - ask for clarification
   - defer
   - log as future opportunity
7. Draft a response only when the boundary is clear.
8. Suggest what to log as candidate memory.

## Output Contract

```text
Request type:
Known facts:
Relevant ResearchOS assets:
Fit judgment:
Risks or missing information:
Privacy/export boundary:
Recommended stance:
Draft response, if safe:
Candidate memory to log:
Next action:
```

## Do Not Infer

- private closeness;
- advising or student status;
- lab membership;
- unconfirmed contribution hierarchy;
- future collaboration commitment;
- availability or willingness not stated by the user.

## Validation

Before writing files, confirm the save target and boundary with the user. After writing, run the relevant local validation or link check.

## Agent Summary

Public-safe workflow for routing external requests through ResearchOS assets before response drafting, with explicit evidence, privacy, and candidate-memory boundaries.
