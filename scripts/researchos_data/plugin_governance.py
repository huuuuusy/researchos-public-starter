"""Shared ResearchOS Plugin Standard v1.2 governance contract.

The host permissions contract answers what code may access.  This module answers
the separate governance questions for both task-led and capability-led plugins:
how a contribution is distributed, deployed, composed, routed, admitted, and
what research effects it may produce.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


SCHEMA_ID = "researchos-plugin-governance-v1"
ARCHETYPES = frozenset({"task_led", "capability_led"})
VARIANTS = frozenset({"universal", "private", "public"})
PARITY_POLICIES = frozenset({"exact", "scoped_variant", "private_only"})
DEPLOYMENT_BY_TIER = {
    "foundation_projection": "embedded_foundation",
    "bundled_capability": "bundled_default_on",
    "optional_extension": "local_installable",
}
EFFECTS = frozenset({
    "read_only",
    "answer",
    "artifact",
    "bounded_runtime_state",
    "reversible_workspace_write",
    "review_candidate",
    "external_state_change",
})
DATA_SENSITIVITY = frozenset({"public", "internal", "sensitive", "private", "inherit_runtime"})
EXPORT_POLICIES = frozenset({"public_safe", "local_only", "not_exportable", "inherit_runtime"})
CAPABILITY_MATURITY_LEVELS = (
    "candidate",
    "instrumented",
    "locally_validated",
    "human_admitted",
    "deprecated",
)
TASK_MATURITY_LEVELS = (
    "draft",
    "instrumented",
    "task_validated",
    "user_adopted",
    "deprecated",
)
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
CONTRIBUTION_PATTERN = re.compile(r"^researchos\.contribution\.[a-z][a-z0-9_]*$")
FIELD_PATH_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HTTPS_PATTERN = re.compile(r"^https://[^\s]+$")
DERIVATION_MODES = frozenset({"native", "adapted_external", "composed_external"})
REUSE_POLICIES = frozenset({"native", "link_and_transform"})
REUSE_MODES = frozenset({"reference_only", "adapted", "composed"})
SOURCE_KINDS = frozenset({"skill", "repository", "paper", "workflow"})
DEPENDENCY_MODES = frozenset({"none", "optional", "runtime_required"})
CURRENT_PLACEMENTS = frozenset({"plugin", "foundation_capability"})
PROPOSED_ABSORPTION_TARGETS = frozenset({"none", "foundation_capability", "stable_kernel"})
COMPARISON_TARGETS = frozenset({"current_model_without_capability", "host_without_capability"})
TASK_COMPARISON_TARGETS = frozenset({"current_model_without_task_workflow"})
COMPARISON_STATUSES = frozenset({"planned", "evaluated", "stale"})
CAPABILITY_DELTAS = frozenset({
    "quality", "reliability", "evidence_boundary", "authority_safety", "efficiency",
    "recoverability", "personal_fit",
})
CAPABILITY_BURDENS = frozenset({
    "context_cost", "trigger_risk", "maintenance_cost", "dependency_risk", "privacy_risk",
})
PLACEMENT_DECISIONS = frozenset({"pending_comparison", "retain_plugin", "retain_foundation", "retire"})
HANDOFF_KINDS = frozenset({"capability", "task", "core_route", "workflow"})
HANDOFF_AVAILABILITY = frozenset({"required", "if_available"})
TASK_PROJECTION_ROLES = frozenset({"entrypoint", "workflow_adapter", "evaluation_probe"})
MUTABLE_VERSION_BOUNDARIES = frozenset({"latest", "main", "master", "head", "unknown", "unversioned"})


class PluginGovernanceError(ValueError):
    """Raised when a governance card violates Plugin Standard v1.2."""


def _fail(source: Path, message: str) -> PluginGovernanceError:
    return PluginGovernanceError(f"{source}: {message}")


def _string(value: Any) -> str:
    return str(value or "").strip()


def _strings(value: Any, source: Path, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise _fail(source, f"governance.{field} must be a{' non-empty' if not allow_empty else ''} string list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise _fail(source, f"governance.{field} must contain only non-empty strings")
    result = [item.strip() for item in value]
    if len(result) != len(set(result)):
        raise _fail(source, f"governance.{field} must not contain duplicates")
    return result


def _exact_fields(data: Any, source: Path, field: str, expected: set[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise _fail(source, f"governance.{field} must be an object")
    if set(data) != expected:
        missing = sorted(expected - set(data))
        extra = sorted(set(data) - expected)
        raise _fail(source, f"governance.{field} fields mismatch; missing={missing}, unsupported={extra}")
    return data


def _path_ref(value: str, *, root: Path, source: Path, field: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise _fail(source, f"governance.{field} must stay inside the repository: {value}")
    return path.as_posix()


def legacy_governance(
    *, plugin_id: str, product_tier: str, public_safe: bool, sensitivity_default: str
) -> dict[str, Any]:
    """Conservative adapter for third-party/local v1 manifests without v1.1 metadata."""
    sensitivity = "public" if sensitivity_default in {"public", "public_safe"} else "inherit_runtime"
    export_policy = "public_safe" if public_safe else "not_exportable"
    deployment = DEPLOYMENT_BY_TIER[product_tier]
    return {
        "schema_id": SCHEMA_ID,
        "contract_id": f"researchos.contribution.{plugin_id}",
        "archetype": "capability_led",
        "distribution": {
            "variant": "universal" if public_safe else "private",
            "parity_policy": "exact" if public_safe else "private_only",
            "allowed_divergence_fields": [],
        },
        "lineage": {
            "prototype_id": "researchos_plugin_capability_v1",
            "derivation_mode": "native",
            "reuse_policy": "native",
            "source_refs": [],
            "external_runtime_dependency": "none",
            "transformation_summary": "Legacy manifest adapted conservatively; provenance has not yet been reviewed.",
            "current_placement": "foundation_capability" if product_tier == "foundation_projection" else "plugin",
            "proposed_absorption_target": "none",
            "absorption_gate": "review_required",
        },
        "capability_value": {
            "comparison_target": "host_without_capability" if product_tier == "foundation_projection" else "current_model_without_capability",
            "comparison_status": "planned",
            "expected_deltas": [],
            "expected_burdens": ["maintenance_cost"],
            "evidence_refs": [],
            "placement_decision": "pending_comparison",
            "retention_rule": "Retain only after a bounded comparison shows value beyond the current model or host baseline.",
        },
        "deployment_mode": deployment,
        "effects": {"default_effect": "read_only", "allowed_effects": ["read_only"]},
        "data_policy": {
            "default_sensitivity": sensitivity,
            "default_export_policy": export_policy,
        },
        "composition": {
            "requires": ["researchos_core"],
            "provides": [plugin_id],
            "optional_integrations": [],
            "conflicts_with": [],
        },
        "capability_bindings": [
            {"contribution_id": plugin_id, "claim_ids": [plugin_id]}
        ],
        "task_projections": [],
        "routing": {
            "trigger_intents": [plugin_id],
            "non_goals": ["unbounded_authority_change"],
            "handoff_to": [{"kind": "core_route", "id": "review", "availability": "required"}],
        },
        "admission": {
            "maturity": "candidate",
            "proof_refs": [],
            "last_reviewed": "1970-01-01",
            "revalidation_triggers": ["explicit_governance_adoption"],
            "retirement_condition": "Replace the compatibility default with an explicitly reviewed governance card.",
        },
        "compatibility_defaulted": True,
    }


def validate_governance(
    data: Any,
    *,
    root: Path,
    source: Path,
    plugin_id: str,
    product_tier: str,
    enabled: bool,
    result_modes: set[str] | None = None,
    require_explicit: bool = False,
    public_safe: bool = False,
    sensitivity_default: str = "local_only",
) -> dict[str, Any]:
    if data is None:
        if require_explicit:
            raise _fail(source, "governance is required for checked-in manifests")
        return legacy_governance(
            plugin_id=plugin_id,
            product_tier=product_tier,
            public_safe=public_safe,
            sensitivity_default=sensitivity_default,
        )
    if not isinstance(data, dict):
        raise _fail(source, "governance must be an object")
    raw_governance = dict(data)
    # Product placement is authoritative; retain the old field only as a
    # checked compatibility assertion. Normalized consumers still receive it.
    expected_deployment = DEPLOYMENT_BY_TIER.get(product_tier)
    if expected_deployment is None:
        raise _fail(source, f"unsupported product_tier: {product_tier}")
    raw_governance.setdefault("deployment_mode", expected_deployment)
    raw_governance.setdefault("archetype", "capability_led")
    archetype = _string(raw_governance.get("archetype"))
    if archetype not in ARCHETYPES:
        raise _fail(source, f"governance.archetype must be one of {sorted(ARCHETYPES)}")
    common_root = {
        "schema_id", "contract_id", "archetype", "distribution", "lineage", "deployment_mode", "effects",
        "data_policy", "composition", "routing", "admission",
    }
    type_root = (
        {"capability_value", "capability_bindings", "task_projections"}
        if archetype == "capability_led"
        else {"task_contract"}
    )
    governance = _exact_fields(raw_governance, source, "", common_root | type_root)
    if governance.get("schema_id") != SCHEMA_ID:
        raise _fail(source, f"governance.schema_id must be {SCHEMA_ID}")
    contract_id = _string(governance.get("contract_id"))
    if contract_id != f"researchos.contribution.{plugin_id}" or not CONTRIBUTION_PATTERN.fullmatch(contract_id):
        raise _fail(source, f"governance.contract_id must be researchos.contribution.{plugin_id}")

    distribution = _exact_fields(
        governance.get("distribution"), source, "distribution",
        {"variant", "parity_policy", "allowed_divergence_fields"},
    )
    variant = _string(distribution.get("variant"))
    parity_policy = _string(distribution.get("parity_policy"))
    divergence = _strings(
        distribution.get("allowed_divergence_fields"), source,
        "distribution.allowed_divergence_fields", allow_empty=True,
    )
    if variant not in VARIANTS or parity_policy not in PARITY_POLICIES:
        raise _fail(source, "governance.distribution has an unsupported variant or parity_policy")
    if any(not FIELD_PATH_PATTERN.fullmatch(path) for path in divergence):
        raise _fail(source, "governance.distribution.allowed_divergence_fields must use dotted field paths")
    if parity_policy == "exact" and (variant != "universal" or divergence):
        raise _fail(source, "exact parity requires universal variant and no divergence fields")
    if parity_policy == "private_only" and (variant != "private" or divergence):
        raise _fail(source, "private_only requires private variant and no divergence fields")
    if parity_policy == "scoped_variant" and (variant == "universal" or not divergence):
        raise _fail(source, "scoped_variant requires private/public variant and explicit divergence fields")

    lineage = _exact_fields(
        governance.get("lineage"), source, "lineage",
        {
            "prototype_id", "derivation_mode", "reuse_policy", "source_refs",
            "external_runtime_dependency", "transformation_summary", "current_placement",
            "proposed_absorption_target", "absorption_gate",
        },
    )
    prototype_id = _string(lineage.get("prototype_id"))
    expected_prototype = (
        "researchos_plugin_capability_v1" if archetype == "capability_led" else "researchos_plugin_task_v1"
    )
    if prototype_id != expected_prototype:
        raise _fail(source, f"governance.lineage.prototype_id must be {expected_prototype} for {archetype}")
    derivation_mode = _string(lineage.get("derivation_mode"))
    reuse_policy = _string(lineage.get("reuse_policy"))
    dependency_mode = _string(lineage.get("external_runtime_dependency"))
    current_placement = _string(lineage.get("current_placement"))
    proposed_absorption_target = _string(lineage.get("proposed_absorption_target"))
    if derivation_mode not in DERIVATION_MODES or reuse_policy not in REUSE_POLICIES:
        raise _fail(source, "governance.lineage has unsupported derivation_mode or reuse_policy")
    if dependency_mode not in DEPENDENCY_MODES or current_placement not in CURRENT_PLACEMENTS:
        raise _fail(source, "governance.lineage has unsupported dependency or current placement")
    if proposed_absorption_target not in PROPOSED_ABSORPTION_TARGETS:
        raise _fail(source, "governance.lineage has an unsupported proposed absorption target")
    if lineage.get("absorption_gate") != "review_required":
        raise _fail(source, "governance.lineage.absorption_gate must be review_required")
    transformation_summary = _string(lineage.get("transformation_summary"))
    if not transformation_summary:
        raise _fail(source, "governance.lineage.transformation_summary is required")
    source_refs = lineage.get("source_refs")
    if not isinstance(source_refs, list):
        raise _fail(source, "governance.lineage.source_refs must be a list")
    normalized_sources: list[dict[str, str]] = []
    for index, ref in enumerate(source_refs):
        ref = _exact_fields(
            ref, source, f"lineage.source_refs.{index}",
            {"candidate_id", "kind", "name", "url", "version", "license", "reuse_mode"},
        )
        normalized_ref = {field: _string(ref.get(field)) for field in ref}
        if not ID_PATTERN.fullmatch(normalized_ref["candidate_id"]):
            raise _fail(source, f"governance.lineage.source_refs.{index}.candidate_id must use lower_snake_case")
        if normalized_ref["kind"] not in SOURCE_KINDS:
            raise _fail(source, f"governance.lineage.source_refs.{index}.kind is unsupported")
        if not normalized_ref["name"] or not normalized_ref["version"] or not normalized_ref["license"]:
            raise _fail(source, f"governance.lineage.source_refs.{index} requires name, version, and license")
        if not HTTPS_PATTERN.fullmatch(normalized_ref["url"]):
            raise _fail(source, f"governance.lineage.source_refs.{index}.url must be an https link")
        if normalized_ref["reuse_mode"] not in REUSE_MODES:
            raise _fail(source, f"governance.lineage.source_refs.{index}.reuse_mode is unsupported")
        if normalized_ref["reuse_mode"] != "reference_only":
            if normalized_ref["version"].lower() in MUTABLE_VERSION_BOUNDARIES:
                raise _fail(source, f"governance.lineage.source_refs.{index}.version must be pinned or retrieval-bounded before reuse")
            if normalized_ref["license"].lower() in {"unknown", "none", "unlicensed"}:
                raise _fail(source, f"governance.lineage.source_refs.{index}.license must permit adaptation or composition")
        normalized_sources.append(normalized_ref)
    if derivation_mode == "native" and (source_refs or reuse_policy != "native"):
        raise _fail(source, "native lineage must have no external sources and use native reuse_policy")
    if derivation_mode == "adapted_external" and (not source_refs or reuse_policy != "link_and_transform"):
        raise _fail(source, "adapted_external lineage requires linked sources and link_and_transform policy")
    if derivation_mode == "adapted_external" and (
        not any(ref["reuse_mode"] == "adapted" for ref in normalized_sources)
        or any(ref["reuse_mode"] == "composed" for ref in normalized_sources)
    ):
        raise _fail(source, "adapted_external lineage requires at least one adapted source and no composed sources")
    if derivation_mode == "composed_external" and (len(source_refs) < 2 or reuse_policy != "link_and_transform"):
        raise _fail(source, "composed_external lineage requires at least two linked sources and link_and_transform policy")
    if derivation_mode == "composed_external":
        unique_sources = {(ref["candidate_id"], ref["url"], ref["version"]) for ref in normalized_sources}
        composed_sources = [ref for ref in normalized_sources if ref["reuse_mode"] == "composed"]
        if len(unique_sources) < 2 or len(composed_sources) < 2:
            raise _fail(source, "composed_external lineage requires at least two distinct composed sources")
    expected_placement = "foundation_capability" if product_tier == "foundation_projection" else "plugin"
    if current_placement != expected_placement:
        raise _fail(source, f"governance.lineage.current_placement must be {expected_placement} for {product_tier}")
    if archetype == "task_led" and product_tier == "foundation_projection":
        raise _fail(source, "task_led plugins cannot use the foundation_projection tier")

    normalized_capability_value: dict[str, Any] | None = None
    normalized_task_contract: dict[str, Any] | None = None
    if archetype == "capability_led":
        capability_value = _exact_fields(
            governance.get("capability_value"), source, "capability_value",
            {
                "comparison_target", "comparison_status", "expected_deltas", "expected_burdens",
                "evidence_refs", "placement_decision", "retention_rule",
            },
        )
        comparison_target = _string(capability_value.get("comparison_target"))
        comparison_status = _string(capability_value.get("comparison_status"))
        expected_deltas = _strings(
            capability_value.get("expected_deltas"), source, "capability_value.expected_deltas", allow_empty=True,
        )
        expected_burdens = _strings(
            capability_value.get("expected_burdens"), source, "capability_value.expected_burdens", allow_empty=True,
        )
        value_evidence = _strings(
            capability_value.get("evidence_refs"), source, "capability_value.evidence_refs", allow_empty=True,
        )
        placement_decision = _string(capability_value.get("placement_decision"))
        retention_rule = _string(capability_value.get("retention_rule"))
        if comparison_target not in COMPARISON_TARGETS or comparison_status not in COMPARISON_STATUSES:
            raise _fail(source, "governance.capability_value has an unsupported comparison target or status")
        expected_target = "host_without_capability" if product_tier == "foundation_projection" else "current_model_without_capability"
        if comparison_target != expected_target:
            raise _fail(source, f"governance.capability_value.comparison_target must be {expected_target} for {product_tier}")
        if set(expected_deltas) - CAPABILITY_DELTAS or set(expected_burdens) - CAPABILITY_BURDENS:
            raise _fail(source, "governance.capability_value uses unsupported delta or burden ids")
        value_evidence = [
            _path_ref(value, root=root, source=source, field="capability_value.evidence_refs") for value in value_evidence
        ]
        if comparison_status == "evaluated" and (not expected_deltas or not value_evidence):
            raise _fail(source, "evaluated capability value requires at least one delta and evidence ref")
        if placement_decision not in PLACEMENT_DECISIONS or not retention_rule:
            raise _fail(source, "governance.capability_value requires a supported placement decision and retention rule")
        if placement_decision == "retain_foundation" and product_tier != "foundation_projection":
            raise _fail(source, "only foundation_projection may use retain_foundation")
        if placement_decision == "retain_plugin" and product_tier == "foundation_projection":
            raise _fail(source, "foundation_projection cannot use retain_plugin")
        normalized_capability_value = {
            "comparison_target": comparison_target,
            "comparison_status": comparison_status,
            "expected_deltas": expected_deltas,
            "expected_burdens": expected_burdens,
            "evidence_refs": value_evidence,
            "placement_decision": placement_decision,
            "retention_rule": retention_rule,
        }
    else:
        task_contract = _exact_fields(
            governance.get("task_contract"), source, "task_contract",
            {
                "task_id", "user_job", "inputs", "outputs", "invariants", "confirmation_gates",
                "completion_criteria", "failure_modes", "recovery", "comparison_target",
                "comparison_status", "expected_deltas", "expected_burdens", "evidence_refs",
                "retention_rule",
            },
        )
        task_id = _string(task_contract.get("task_id"))
        user_job = _string(task_contract.get("user_job"))
        if task_id != plugin_id or not ID_PATTERN.fullmatch(task_id):
            raise _fail(source, "governance.task_contract.task_id must equal the plugin id")
        if not user_job:
            raise _fail(source, "governance.task_contract.user_job is required")
        task_lists = {
            field: _strings(task_contract.get(field), source, f"task_contract.{field}")
            for field in (
                "inputs", "outputs", "invariants", "confirmation_gates", "completion_criteria",
                "failure_modes", "recovery",
            )
        }
        comparison_target = _string(task_contract.get("comparison_target"))
        comparison_status = _string(task_contract.get("comparison_status"))
        expected_deltas = _strings(
            task_contract.get("expected_deltas"), source, "task_contract.expected_deltas", allow_empty=True,
        )
        expected_burdens = _strings(
            task_contract.get("expected_burdens"), source, "task_contract.expected_burdens", allow_empty=True,
        )
        value_evidence = _strings(
            task_contract.get("evidence_refs"), source, "task_contract.evidence_refs", allow_empty=True,
        )
        retention_rule = _string(task_contract.get("retention_rule"))
        if comparison_target not in TASK_COMPARISON_TARGETS or comparison_status not in COMPARISON_STATUSES:
            raise _fail(source, "governance.task_contract has an unsupported comparison target or status")
        if set(expected_deltas) - CAPABILITY_DELTAS or set(expected_burdens) - CAPABILITY_BURDENS:
            raise _fail(source, "governance.task_contract uses unsupported delta or burden ids")
        value_evidence = [
            _path_ref(value, root=root, source=source, field="task_contract.evidence_refs") for value in value_evidence
        ]
        if comparison_status == "evaluated" and (not expected_deltas or not value_evidence):
            raise _fail(source, "evaluated task workflow requires at least one delta and evidence ref")
        if not retention_rule:
            raise _fail(source, "governance.task_contract.retention_rule is required")
        normalized_task_contract = {
            "task_id": task_id,
            "user_job": user_job,
            **task_lists,
            "comparison_target": comparison_target,
            "comparison_status": comparison_status,
            "expected_deltas": expected_deltas,
            "expected_burdens": expected_burdens,
            "evidence_refs": value_evidence,
            "retention_rule": retention_rule,
        }

    deployment = _string(governance.get("deployment_mode"))
    if deployment != expected_deployment:
        raise _fail(source, f"governance.deployment_mode must be {expected_deployment} for {product_tier}")
    effects = _exact_fields(governance.get("effects"), source, "effects", {"default_effect", "allowed_effects"})
    allowed_effects = _strings(effects.get("allowed_effects"), source, "effects.allowed_effects")
    default_effect = _string(effects.get("default_effect"))
    if set(allowed_effects) - EFFECTS or default_effect not in allowed_effects:
        raise _fail(source, "governance.effects must use supported effects and include default_effect")
    required_by_mode = {"answer": "answer", "artifact": "artifact", "writeback": "review_candidate"}
    for mode in sorted(result_modes or set()):
        required = required_by_mode[mode]
        if required not in allowed_effects:
            raise _fail(source, f"governance.effects must include {required} for result mode {mode}")

    data_policy = _exact_fields(
        governance.get("data_policy"), source, "data_policy",
        {"default_sensitivity", "default_export_policy"},
    )
    data_sensitivity = _string(data_policy.get("default_sensitivity"))
    export_policy = _string(data_policy.get("default_export_policy"))
    if data_sensitivity not in DATA_SENSITIVITY or export_policy not in EXPORT_POLICIES:
        raise _fail(source, "governance.data_policy has unsupported sensitivity or export policy")
    if public_safe and export_policy == "not_exportable":
        raise _fail(source, "public_safe manifests cannot default to not_exportable")
    if data_sensitivity in {"internal", "sensitive", "private"} and export_policy == "public_safe":
        raise _fail(source, "non-public default sensitivity cannot use public_safe export policy")
    if data_sensitivity == "public" and export_policy != "public_safe":
        raise _fail(source, "public default sensitivity must use public_safe export policy")

    composition = _exact_fields(
        governance.get("composition"), source, "composition",
        {"requires", "provides", "optional_integrations", "conflicts_with"},
    )
    normalized_composition: dict[str, list[str]] = {}
    for field in ("requires", "provides", "optional_integrations", "conflicts_with"):
        values = _strings(composition.get(field), source, f"composition.{field}", allow_empty=field in {"optional_integrations", "conflicts_with"})
        if any(not ID_PATTERN.fullmatch(value) for value in values):
            raise _fail(source, f"governance.composition.{field} must use lower_snake_case ids")
        normalized_composition[field] = values
    if "researchos_core" not in normalized_composition["requires"]:
        raise _fail(source, "governance.composition.requires must include researchos_core")
    if set(normalized_composition["requires"]) & set(normalized_composition["conflicts_with"]):
        raise _fail(source, "governance composition cannot both require and conflict with the same capability")

    normalized_bindings: list[dict[str, Any]] = []
    bound_claims_by_contribution: dict[str, set[str]] = {}
    normalized_task_projections: list[dict[str, str]] = []
    if archetype == "capability_led":
        capability_bindings = governance.get("capability_bindings")
        if not isinstance(capability_bindings, list) or not capability_bindings:
            raise _fail(source, "governance.capability_bindings must be a non-empty list")
        seen_claim_ids: set[str] = set()
        for index, binding in enumerate(capability_bindings):
            item = _exact_fields(
                binding, source, f"capability_bindings.{index}", {"contribution_id", "claim_ids"}
            )
            contribution_id = _string(item.get("contribution_id"))
            claim_ids = _strings(item.get("claim_ids"), source, f"capability_bindings.{index}.claim_ids")
            if not ID_PATTERN.fullmatch(contribution_id) or any(not ID_PATTERN.fullmatch(value) for value in claim_ids):
                raise _fail(source, f"governance.capability_bindings.{index} ids must use lower_snake_case")
            if contribution_id in bound_claims_by_contribution:
                raise _fail(source, "governance.capability_bindings must bind each contribution exactly once")
            duplicate_claims = seen_claim_ids & set(claim_ids)
            if duplicate_claims:
                raise _fail(source, "governance.capability_bindings must give each capability claim one contribution owner")
            bound_claims_by_contribution[contribution_id] = set(claim_ids)
            seen_claim_ids.update(claim_ids)
            normalized_bindings.append({"contribution_id": contribution_id, "claim_ids": claim_ids})
        if set(bound_claims_by_contribution) != set(normalized_composition["provides"]):
            raise _fail(source, "governance.capability_bindings must bind every composition.provides contribution exactly once")

        task_projections = governance.get("task_projections")
        if not isinstance(task_projections, list):
            raise _fail(source, "governance.task_projections must be a list")
        seen_task_ids: set[str] = set()
        for index, projection in enumerate(task_projections):
            item = _exact_fields(
                projection, source, f"task_projections.{index}",
                {"task_id", "contribution_id", "capability_id", "role"},
            )
            normalized = {field: _string(item.get(field)) for field in item}
            if any(not ID_PATTERN.fullmatch(normalized[field]) for field in ("task_id", "contribution_id", "capability_id")):
                raise _fail(source, f"governance.task_projections.{index} ids must use lower_snake_case")
            if normalized["role"] not in TASK_PROJECTION_ROLES:
                raise _fail(source, f"governance.task_projections.{index}.role is unsupported")
            if normalized["task_id"] in seen_task_ids:
                raise _fail(source, "governance.task_projections must map each task exactly once")
            if normalized["contribution_id"] not in bound_claims_by_contribution:
                raise _fail(source, "governance.task_projections contribution_id must be owned by composition.provides")
            if normalized["capability_id"] not in bound_claims_by_contribution[normalized["contribution_id"]]:
                raise _fail(source, "governance.task_projections capability_id must be bound to its contribution")
            seen_task_ids.add(normalized["task_id"])
            normalized_task_projections.append(normalized)
    elif normalized_composition["provides"] != [plugin_id]:
        raise _fail(source, "task_led plugins must provide exactly their single task id")

    routing = _exact_fields(
        governance.get("routing"), source, "routing",
        {"trigger_intents", "non_goals", "handoff_to"},
    )
    normalized_routing: dict[str, Any] = {}
    for field in ("trigger_intents", "non_goals"):
        values = _strings(routing.get(field), source, f"routing.{field}")
        if any(not ID_PATTERN.fullmatch(value) for value in values):
            raise _fail(source, f"governance.routing.{field} must use lower_snake_case ids")
        normalized_routing[field] = values
    handoffs = routing.get("handoff_to")
    if not isinstance(handoffs, list):
        raise _fail(source, "governance.routing.handoff_to must be a list")
    normalized_handoffs: list[dict[str, str]] = []
    seen_handoffs: set[tuple[str, str]] = set()
    for index, handoff in enumerate(handoffs):
        item = _exact_fields(handoff, source, f"routing.handoff_to.{index}", {"kind", "id", "availability"})
        normalized = {field: _string(item.get(field)) for field in item}
        if normalized["kind"] not in HANDOFF_KINDS or normalized["availability"] not in HANDOFF_AVAILABILITY:
            raise _fail(source, f"governance.routing.handoff_to.{index} has unsupported kind or availability")
        if not ID_PATTERN.fullmatch(normalized["id"]):
            raise _fail(source, f"governance.routing.handoff_to.{index}.id must use lower_snake_case")
        key = (normalized["kind"], normalized["id"])
        if key in seen_handoffs:
            raise _fail(source, "governance.routing.handoff_to must not repeat the same typed target")
        seen_handoffs.add(key)
        normalized_handoffs.append(normalized)
    normalized_routing["handoff_to"] = normalized_handoffs
    if set(normalized_routing["trigger_intents"]) & set(normalized_routing["non_goals"]):
        raise _fail(source, "governance routing cannot list the same intent as trigger and non-goal")

    admission = _exact_fields(
        governance.get("admission"), source, "admission",
        {"maturity", "proof_refs", "last_reviewed", "revalidation_triggers", "retirement_condition"},
    )
    maturity = _string(admission.get("maturity"))
    maturity_levels = CAPABILITY_MATURITY_LEVELS if archetype == "capability_led" else TASK_MATURITY_LEVELS
    if maturity not in maturity_levels:
        raise _fail(source, f"governance.admission.maturity must be one of {list(maturity_levels)} for {archetype}")
    proof_refs = _strings(admission.get("proof_refs"), source, "admission.proof_refs", allow_empty=True)
    if maturity not in {"candidate", "draft", "deprecated"} and not proof_refs:
        raise _fail(source, f"governance.admission.maturity={maturity} requires proof_refs")
    proof_refs = [_path_ref(value, root=root, source=source, field="admission.proof_refs") for value in proof_refs]
    last_reviewed = _string(admission.get("last_reviewed"))
    if not DATE_PATTERN.fullmatch(last_reviewed):
        raise _fail(source, "governance.admission.last_reviewed must use YYYY-MM-DD")
    revalidation = _strings(admission.get("revalidation_triggers"), source, "admission.revalidation_triggers")
    if any(not ID_PATTERN.fullmatch(value) for value in revalidation):
        raise _fail(source, "governance.admission.revalidation_triggers must use lower_snake_case ids")
    retirement = _string(admission.get("retirement_condition"))
    if not retirement:
        raise _fail(source, "governance.admission.retirement_condition is required")
    if maturity == "human_admitted" and comparison_status != "evaluated":
        raise _fail(source, "human_admitted capability requires an evaluated model/host baseline")
    if maturity == "user_adopted" and comparison_status != "evaluated":
        raise _fail(source, "user_adopted task workflow requires an evaluated current-model baseline")

    normalized_governance = {
        "schema_id": SCHEMA_ID,
        "contract_id": contract_id,
        "archetype": archetype,
        "distribution": {
            "variant": variant,
            "parity_policy": parity_policy,
            "allowed_divergence_fields": divergence,
        },
        "lineage": {
            "prototype_id": prototype_id,
            "derivation_mode": derivation_mode,
            "reuse_policy": reuse_policy,
            "source_refs": normalized_sources,
            "external_runtime_dependency": dependency_mode,
            "transformation_summary": transformation_summary,
            "current_placement": current_placement,
            "proposed_absorption_target": proposed_absorption_target,
            "absorption_gate": "review_required",
        },
        "deployment_mode": deployment,
        "effects": {"default_effect": default_effect, "allowed_effects": allowed_effects},
        "data_policy": {
            "default_sensitivity": data_sensitivity,
            "default_export_policy": export_policy,
        },
        "composition": normalized_composition,
        "routing": normalized_routing,
        "admission": {
            "maturity": maturity,
            "proof_refs": proof_refs,
            "last_reviewed": last_reviewed,
            "revalidation_triggers": revalidation,
            "retirement_condition": retirement,
        },
        "compatibility_defaulted": False,
    }
    if archetype == "capability_led":
        normalized_governance["capability_value"] = normalized_capability_value
        normalized_governance["capability_bindings"] = normalized_bindings
        normalized_governance["task_projections"] = normalized_task_projections
    else:
        normalized_governance["task_contract"] = normalized_task_contract
    return normalized_governance
