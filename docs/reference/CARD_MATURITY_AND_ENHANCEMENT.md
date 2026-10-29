# Card Maturity And Enhancement

<p align="right">
  <strong>English</strong> | <a href="CARD_MATURITY_AND_ENHANCEMENT.zh.md">中文</a>
</p>

This reference explains how ResearchOS displays card maturity and turns a request to improve a card into a bounded task. It is not required reading for first use.

## One Level Does Not Fit Every Card

Each Library card may show one primary maturity axis with a plain-language label:

| Card | Axis | Meaning |
| --- | --- | --- |
| Paper, talk, source, or note | `M1–M3` | How deeply the material has been understood |
| Idea or project | `I0–I3` | How far it has moved from assessment to an independent project |
| Person | `R0–R3` | How complete the sourced working-relationship context is |
| Card group or direction | `G0–G2 / Research mainline` | How far separate cards have become a reusable composition |

`P0–P3` is project priority, not maturity. Lifecycle, schedule, relation confidence, and context budget are separate. ResearchOS never ranks a person's value: an R label describes the completeness of the relationship record only.

## Where Levels Appear

- **Now** allocates attention across several Commitments and does not repeat the full maturity system.
- **Library** shows the primary maturity label, direct relations, and the card-focused enhancement preview.
- **Work** distinguishes multiple bounded sessions; its **Needs Review** state shows returned results or candidate changes and controls any durable change. Needs Review is not a fourth screen or a notification inbox.

The item placement and result/candidate examples here describe part of Review. Its [full reception scope](../system-reference.en.md#shared-governance-boundaries) also includes bounded unknowns, break-glass confirmation, validation failures, rollback, and handoffs required before closure. The same reference distinguishes requirement waiting/defer from portfolio state and explains completion and context delivery. These definitions do not enable private writes in the public release.

A card face shows at most one primary maturity label, one decision-relevant secondary status, one date, one action summary, and a small relation preview. A project may show up to two confirmed people plus `+N`; candidate relations remain separate.

## Enhance Card

`Enhance card` does not change a level immediately. It opens the existing card sidecar and shows:

1. the current level and its source;
2. up to three gaps to the next level;
3. a bounded set of confirmed direct relations and explicitly marked candidates;
4. one task preview with read scope, output, save target, and confirmation requirement.

The task returns to Work for bounded continuation or agent handoff; a returned result or candidate change then enters Needs Review inside Work. Completion produces an artifact and a proposed change. A level may change only after review, confirmation, writeback, validation, and projection rebuild.

At the highest maturity, the action becomes `Reverify` when sources are stale or `Use in current task` when the card is current. If the level is heuristic or conflicting, the action is `Verify level`. If no traceable source exists, it is `Add source`.

## Bounded Context

By default, an enhancement task reads only the selected canonical card, up to five confirmed one-hop relations, up to three candidate relations required for the next-level decision, and the relevant maturity rule. It does not scan the full library or read private/sensitive material without an explicit need and user confirmation. Every result should report what was read, what was intentionally not read, remaining gaps, and whether a maturity change is recommended.

## Public And Personal Boundaries

| Capability | Public demo | Personal vault |
| --- | --- | --- |
| Cards and relations | Fictional only | User-controlled local material |
| Enhancement preview | Available | Available |
| Execution | Copyable task packet only; the public starter only offers a copy fallback and admits nothing into the durable sources | Explicit local controlled execution |
| Durable change | Disabled | Candidate first; user confirmation required |
| External download | Disabled | Only from a user-provided source and explicit confirmation |

The public demo never probes a private provider, reads a private repository, or writes canonical memory. Shared UI and state contracts remain the same; only data and permissions differ.

## Compatibility

- Existing material `upgrade` candidates map to `card_enhancement` on the M axis.
- Existing `Person-M1–M3` view data maps compatibly to relationship context `R1–R3`; it does not become a value judgment about a person.
- Missing project I maturity is shown as `Needs verification`; it is never inferred from priority, active status, schedule, or file count.
- Enhancement reuses the existing CandidateEnvelope, Work, and Review flow. It does not create another inbox, fourth screen, or graph workspace.

## Accessibility And Acceptance

Levels always include text, not color alone. Truncated labels and relations reveal their full value on hover and keyboard focus. The mobile view keeps one person plus `+N` visible without horizontal scrolling. An implementation is not accepted if a user confuses maturity with priority, interprets a relationship label as human worth, or believes enhancement writes durable state immediately.
