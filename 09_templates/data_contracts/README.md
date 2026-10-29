<p align="right">
  <strong>English</strong> | <a href="README.zh.md">中文</a>
</p>

# Data Contracts

Defines public-safe field conventions across the dashboard, exports, candidate records, relation explanations, and validation scripts.

- `researchos-primitive-contract-v1.md/json`: basic objects such as source, card, relation, candidate, confirmation, action, validation, and export.
- `researchos-capability-registry-v1.md/json`: canonical `capability_claims` plus separate legacy implementation/action records; plugin contributions and task projections must bind to registered claims.
- `researchos-relation-semantics-contract-v1.md/json`: relation types, relation states, and people-relation safety rules.
- `researchos-extension-contract-v1.md`: extension contract for new asset classes, resource objects, workflow objects, dashboard surfaces, and export targets.
- `researchos-plugin-v1.schema.json`: native plugin host manifest, including the optional backward-compatible governance card.
- `researchos-plugin-governance-v1.schema.json`: shared distribution, lineage, deployment, effects, data, composition, routing, admission, and retirement contract.
- `researchos-capability-source-registry-v1.schema.json`: link-first registry for external skills, repositories, papers, and workflows before capability promotion.
- `researchos-plugin-admission-receipt-v1.schema.json`: human admission proof requiring real use, baseline evidence, accepted scope, known failures, and revalidation triggers.
- `researchos-task-extension-v1.schema.json`: executable schema for declarative task routes consumed by the dashboard builder and `scripts/plan_context.py`.
- `researchos-task-intent-v1.schema.json`: untrusted client request contract; it never grants permission, runtime scope, idempotency, or durable authority.
- `researchos-task-envelope-v1.schema.json`: server-owned pre-policy execution envelope; it separates requested values from actual runtime facts, keeps authorization unresolved, and is stripped from public projections.
- `researchos-projection-envelope-v1.schema.json`: browser-facing, versioned plugin projection boundary with explicit sensitivity, freshness, status, error, and payload.
- `researchos-client-shell-v1.json`: machine-readable boundary for the optional Dashboard application shell, its semantic surface catalog, profile-defined routing, allowed ports, plugin-host role, forbidden ownership, and headless closure.
- `researchos-metadata-profile-v1.schema.json`: strict lifecycle, authority, sensitivity, export, and owner vocabulary for new Markdown metadata; legacy reading remains a separate compatibility projection.
- `researchos-rule-evolution-v1.schema.json`: candidate, bounded-trial, review-proposal, review-due and rollback semantics; never a stable Rule disposition.
