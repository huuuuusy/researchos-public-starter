---
type: protocol
title: "ResearchOS Public Agent Protocol"
status: ready
created: 2026-06-27
updated: 2026-10-28
tags:
  - agent-protocol
  - context-routing
  - public-starter
sensitivity: public
exportable_to:
  - public_template
---

<p align="right">
  <strong>English</strong> | <a href="AGENT_PROTOCOL.zh.md">中文</a>
</p>

# Agent Protocol

## Agent Summary

This file defines how an agent should use ResearchOS Public Starter. Core rule: identify the task first, load the smallest sufficient context, distinguish source facts from candidate judgment, keep private/submitted/sensitive material local-only by default, and complete explicitly authorized edits with appropriate validation. Unaccepted judgments remain candidates; editing a file does not imply human acceptance.

## Core Principles

Routing, reading budgets, the default response shape and the general safety rules are in [`AGENTS.md`](../../AGENTS.md). This protocol adds three principles:

1. Separate source fact, user-confirmed judgment, and agent inference.
2. Preserve raw evidence.
3. Do not turn one-off chat into durable memory.

## Language Routing

Use the selected project language before following ordinary file links. In the public starter, English files usually use the base filename or `.en.md`, and Chinese files use `.zh.md`. If `public_starter.content_language` is `en`, read `README.md`, `docs/user-manual.en.md`, `docs/reference/AGENT_PROTOCOL.md`, and other English files. If it is `zh-CN`, read `README.zh.md`, `docs/user-manual.zh.md`, `docs/reference/AGENT_PROTOCOL.zh.md`, and other `.zh.md` files when they exist.

Do not read the alternate-language counterpart by default. Read it only when the user asks for translation, bilingual comparison, or language-maintenance work.

## Default Task Flow

```text
Identify task type
  -> choose context budget mode
  -> load required context
  -> check sensitivity and export boundary
  -> produce the requested output or apply authorized edits
  -> validate and report actual completion, uncertainty and evidence boundary
  -> propose additional durable writeback only when justified
```

When `AGENTS.md` is not loaded, the single route file is Section 2 of `docs/user-manual.en.md`, this protocol, the context-budget protocol, or the relevant task-matrix row. Do not preload all entry files.

## Authorization And Completion

A request to update a specified document or source-backed fact authorizes the bounded edit and its necessary validation. If the user asks only for a proposal, return a proposal. Changes to stable identity, sensitive judgments, authority, permissions or public boundaries need authorization for the concrete change; reuse existing authorization instead of asking again. A reviewable diff is evidence, not a new approval gate.

Reading limits control batches, not permission. Explain the missing evidence and continue necessary in-scope investigation. If one action lacks authorization, pause that action and complete independent authorized work. Do not stop at a plan when implementation was requested. Repository editing does not enable Dashboard/provider execution or authorize commit, push, publication or external messages.

## Safety Rules

- Private, submitted, under-review, unpublished, person-sensitive, student, reviewer, grant, and relationship material defaults to `local_only`.
- Public-facing output requires explicit `public_safe` approval.

## Session Context Delivery

The [shared governance boundaries](../system-reference.en.md#shared-governance-boundaries) distinguish session context delivery from publication: public/internal delivery within a researcher-started session, terminal confirmation for each sensitive delivery, private/unknown exclusion, and the narrow source-declared field exception. The section also states what delivery records cannot observe. These semantics do not enable provider execution in the public `copy_only` release.

## Output Rules

For judgment tasks, state the conclusion, supporting evidence and material uncertainty. For edits, report what changed, how it was validated and any unresolved action. Use a candidate label only for unaccepted judgments or unapplied proposals; distinguish local changes, human acceptance and external delivery. Short tasks do not need a fixed multi-field receipt.

## Related Files

- `docs/reference/CONTEXT_BUDGET_PROTOCOL.md`
- `docs/reference/WHERE_TO_PUT_NEW_MATERIALS.md`
- `09_templates/project-template.md`
- `09_templates/standard-agent-prompts.en.md`
- `05_workflows/research_management/material-intake-workflow.md`
