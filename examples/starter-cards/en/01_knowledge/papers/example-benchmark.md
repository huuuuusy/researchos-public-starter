---
type: paper
title: Example Occlusion Benchmark (fictional)
authors: Lin Ke et al. (fictional)
venue: A conference, 2025 (fictional)
version: Protocol version 1
public_boundary: published
analysis_state: M2_refined_read
related_people:
  - 04_people/collaborators/lin-ke.md
related_projects:
  - 01_knowledge/projects/occlusion-tracking.md
source: ~/Papers/example-occlusion-benchmark-v1.pdf (on this computer, not in the vault)
sensitivity: internal
updated: 2026-09-22
---

# Example Occlusion Benchmark (fictional)

## Agent Summary

A tracking benchmark split into light, medium and heavy occlusion, used here at protocol version 1 and read closely. All comparisons in the occlusion tracking project run on it. When the protocol changes, update this card first, and the judgments that rest on it come back for review. Not for questions about re-finding a target after a long disappearance. The benchmark is fictional and only shows how a paper card is written.

## Basic information (fact)

- Authors: Lin Ke et al. Published at a conference in 2025.
- Version: protocol version 1. Heavy occlusion means more than 60% of the target is covered.
- Original: a PDF on this computer; the path is in the frontmatter `source`.

## What the paper says (fact)

- Three occlusion levels, each with its own test split (Section 3).
- Standard success and precision metrics, no new metric (Section 4).
- Occlusion ratios are hand-labelled, and samples near the level boundaries are disputed (Section 5 says so itself).

## My view

Its occlusion levels make it suited to asking whether a method still works under occlusion. Scenes are mostly street views, so indoor results do not carry over directly.

## Relation to my project

- The standard-split results of the occlusion tracking project come from here. The heavy-occlusion comparison waits for version 2; see the [decision card](../../02_decisions/2026-09-22-wait-for-benchmark-v2.md).

## To verify

- The version 2 threshold (70%, heard at the meeting): check it against the protocol text when it is out, then update the "Version" line above.

## Evidence boundary

- This card summarises: how protocol version 1 splits the data and the limits the paper itself admits.
- Not checked: per-level sample counts in the supplementary material.
- Check before citing (not read by default): Sections 3 to 5 of the PDF.
