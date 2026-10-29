---
type: data_contract
title: "ResearchOS Capability Registry v1"
status: ready
created: 2026-06-27
updated: 2026-08-25
tags:
  - data-contract
  - capabilities
sensitivity: public
exportable_to:
  - public_template
---

# ResearchOS Capability Registry v1

## Agent Summary

This contract separates canonical capability claims from replaceable plugin contributions, task projections, and legacy implementation/action records. A claim is a conditional transformation under context variation; it must state its unit of analysis, context envelope, evidence criteria, known failures, authority boundary, review triggers, and retirement condition. A task, installed skill, enabled plugin, or passing test cannot establish the claim by itself.

The enforced identity chain is `capability claim -> plugin contribution -> task projection -> episode evidence -> admission receipt`. Claim identity lives in `capability_claims` in the JSON authority. The older `capabilities` array remains an implementation/action record only.

## Legacy Implementation Record Fields

```yaml
id:
user_intent:
required_context: []
input_schema:
output_schema:
candidate_output:
save_target:
confirmation_required:
sensitivity_rule:
agent_owner:
dashboard_surface:
validation:
```

## Canonical Capability Claims

- `material_intake`
- `research_asset_navigation`
- `research_portfolio_attention`
- `research_context_routing`
- `research_expression`
- `paper_writing`
- `proposal_framing`
- `visual_style_support`
- `research_audit`
- `system_reflection`
- `collaborative_alignment`
- `self_evolution`
- `cross_domain_scientific_entry`

## Registered Implementation Records

- `material_intake`
- `card_creation`
- `relation_explanation`
- `safe_export_check`

## Capability Groups

Groups organize claims without becoming a second capability owner. Each claim belongs to exactly one group in the JSON authority.

- `foundation`: `material_intake`, `research_asset_navigation`, `research_portfolio_attention`.
- `research_work`: `research_context_routing`, `research_expression`, `paper_writing`, `proposal_framing`, `visual_style_support`.
- `stewardship`: `research_audit`, `system_reflection`, `collaborative_alignment`, `self_evolution`.
- `experimental`: `cross_domain_scientific_entry`.
