#!/usr/bin/env python3
"""Validate explicit ResearchOS Plugin Standard v1.2 cards and repo parity."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from researchos_data.plugin_docs import public_documentation_leaks
from researchos_data.plugins import validate_plugin_manifest
from researchos_data.plugin_governance import (
    DATE_PATTERN,
    HTTPS_PATTERN,
    ID_PATTERN,
    MUTABLE_VERSION_BOUNDARIES,
    REUSE_MODES,
    SOURCE_KINDS,
)
from researchos_data.task_extensions import validate_descriptor


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY = Path("config/capability-sources.json")
CAPABILITY_REGISTRY = Path("09_templates/data_contracts/researchos-capability-registry-v1.json")
SOURCE_STATUSES = frozenset({"reference_only", "under_review", "promoted", "rejected", "superseded"})
CORE_ROUTE_IDS = frozenset({"review", "system_maintenance"})
PUBLIC_RUNTIME_ROOTS = (
    Path("dashboard/src"),
    Path("scripts/researchos_data"),
    Path("scripts/researchos_server"),
    Path("config/plugins"),
    Path("config/extensions"),
)
PLUGIN_STANDARD_EN = Path("05_workflows/research_management/researchos-plugin-standard-v1.2.md")
PLUGIN_STANDARD_ZH = Path("05_workflows/research_management/researchos-plugin-standard-v1.2.zh.md")
PLUGIN_STANDARD_ANCHORS = (
    "agent_summary",
    "layer_model",
    "archetypes_and_lifecycle",
    "external_sources",
    "governance_card",
    "admission",
    "baseline_value",
    "composition",
    "distribution_parity",
    "required_gates",
    "open_questions",
)
PLUGIN_STANDARD_CRITICAL_TOKENS = (
    "researchos_plugin_task_v1",
    "researchos_plugin_capability_v1",
    "task_led",
    "capability_led",
    "foundation_projection",
    "bundled_capability",
    "optional_extension",
    "reuse_policy=native",
    "raw_copy",
    "researchos-capability-registry-v1.json",
    "researchos-plugin-admission-receipt-v1",
    "python3 scripts/validate_plugin_standard.py",
)


def _frontmatter_scalar(text: str, key: str) -> str:
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        return ""
    block = text.split("\n---\n", 1)[0].removeprefix("---\n")
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", block, re.MULTILINE)
    return match.group(1).strip().strip('"') if match else ""


def validate_plugin_standard_translation(root: Path) -> list[str]:
    """Fail when the controlled Chinese translation drifts from the normative English structure."""
    failures: list[str] = []
    paths = {"en": root / PLUGIN_STANDARD_EN, "zh": root / PLUGIN_STANDARD_ZH}
    if any(not path.is_file() for path in paths.values()):
        return [f"plugin standard translation pair missing: {path}" for path in paths.values() if not path.is_file()]
    texts = {language: path.read_text(encoding="utf-8") for language, path in paths.items()}
    expected_metadata = {
        "en": {
            "language": "en",
            "normative": "true",
            "semantic_version": "1.2.0",
            "translation_pair": PLUGIN_STANDARD_ZH.name,
        },
        "zh": {
            "language": "zh-CN",
            "normative": "false",
            "semantic_version": "1.2.0",
            "translation_of": PLUGIN_STANDARD_EN.name,
            "translation_status": "controlled",
        },
    }
    for language, fields in expected_metadata.items():
        for key, expected in fields.items():
            actual = _frontmatter_scalar(texts[language], key)
            if actual != expected:
                failures.append(f"plugin standard {language} metadata drift: {key} expected {expected!r}, found {actual!r}")
    for language, text in texts.items():
        anchors = tuple(re.findall(r"<!--\s*semantic-anchor:\s*([a-z0-9_]+)\s*-->", text))
        if anchors != PLUGIN_STANDARD_ANCHORS:
            failures.append(f"plugin standard {language} semantic anchors drifted: {anchors}")
        for token in PLUGIN_STANDARD_CRITICAL_TOKENS:
            if token not in text:
                failures.append(f"plugin standard {language} missing critical semantic token: {token}")
        sections = re.split(r"<!--\s*semantic-anchor:\s*[a-z0-9_]+\s*-->", text)[1:]
        if len(sections) == len(PLUGIN_STANDARD_ANCHORS):
            for anchor, section in zip(PLUGIN_STANDARD_ANCHORS, sections):
                if len(section.strip()) < 80:
                    failures.append(f"plugin standard {language} semantic section is empty or truncated: {anchor}")
    en_commands = set(re.findall(r"^python3\s+[^\n]+$", texts["en"], re.MULTILINE))
    zh_commands = set(re.findall(r"^python3\s+[^\n]+$", texts["zh"], re.MULTILINE))
    if en_commands != zh_commands:
        failures.append("plugin standard controlled translation command gates differ from the normative English file")
    return failures


def manifest_paths(root: Path) -> list[Path]:
    return sorted((root / "config" / "plugins").glob("*.json")) + sorted(
        (root / "config" / "extensions").glob("*.json")
    )


def _validate_one(root: Path, source: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data.get("governance"), dict):
        raise ValueError(f"{source}: checked-in manifest must declare governance")
    if data["governance"].get("archetype") not in {"task_led", "capability_led"}:
        raise ValueError(f"{source}: checked-in manifest must declare task_led or capability_led archetype")
    if data.get("schema_id") == "researchos-plugin-v1":
        normalized = validate_plugin_manifest(
            data, root=root, source=source, require_documentation=True
        )
    elif data.get("schema_id") == "researchos-task-extension-v1":
        normalized = validate_descriptor(
            data, root=root, source=source, require_documentation=True
        )
    else:
        raise ValueError(f"{source}: unsupported manifest schema_id")
    if normalized["governance"].get("compatibility_defaulted"):
        raise ValueError(f"{source}: checked-in manifest used a compatibility governance default")
    if "public_starter" in normalized["available_in"]:
        readme = root / normalized["documentation"]["readme"]
        leaks = public_documentation_leaks(readme.read_text(encoding="utf-8"))
        if leaks:
            raise ValueError(f"{source}: public plugin README contains {', '.join(leaks)}")
    actions = normalized.get("contributions", {}).get("actions", [])
    missing_effects = [action["id"] for action in actions if not action.get("effect")]
    if missing_effects:
        raise ValueError(f"{source}: checked-in actions must declare effect: {missing_effects}")
    return data, normalized


def _exact_object(data: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(data, dict) or set(data) != expected:
        raise ValueError(f"{label}: fields must be exactly {sorted(expected)}")
    return data


def _task_records(raw: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    if raw.get("schema_id") == "researchos-task-extension-v1":
        task = raw.get("task")
        return [(str(raw.get("id", "")), task)] if isinstance(task, dict) else []
    records: list[tuple[str, dict[str, Any]]] = []
    for item in raw.get("contributions", {}).get("tasks", []):
        if isinstance(item, dict) and isinstance(item.get("task"), dict):
            records.append((str(item.get("id", "")), item["task"]))
    return records


def _validate_read_ladder(root: Path, source: Path, task_id: str, task: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    ladders = [("default", task.get("read"))]
    read_locales = task.get("read_locales", {})
    if isinstance(read_locales, dict):
        ladders.extend((f"locale:{locale}", value) for locale, value in read_locales.items())
    for label, ladder in ladders:
        if ladder is None:
            continue
        if not isinstance(ladder, dict):
            failures.append(f"{source}: task {task_id} {label} read ladder must be an object")
            continue
        levels = {name: set(ladder.get(name, [])) for name in ("quick", "standard", "evidence")}
        if not levels["quick"] <= levels["standard"] or not levels["standard"] <= levels["evidence"]:
            failures.append(f"{source}: task {task_id} {label} reads must satisfy quick <= standard <= evidence")
        for value in sorted(levels["evidence"]):
            path = Path(value)
            if path.is_absolute() or ".." in path.parts or not (root / path).is_file():
                failures.append(f"{source}: task {task_id} {label} read path does not resolve safely: {value}")
    return failures


def _command_target(root: Path, command: str) -> Path | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return Path("__invalid_command__")
    if not parts:
        return Path("__invalid_command__")
    if parts[0] == "node" and len(parts) >= 2:
        return root / parts[1]
    if parts[0] in {"python", "python3"} and len(parts) >= 2:
        if parts[1] == "-m" and len(parts) >= 4 and parts[2] == "unittest":
            return root / f"{parts[3].replace('.', '/')}.py"
        if not parts[1].startswith("-"):
            return root / parts[1]
    return None


def validate_manifest_surface_contracts(root: Path, manifests: dict[str, dict[str, Any]]) -> list[str]:
    """Cross-manifest checks that a single JSON schema cannot express."""
    failures: list[str] = []
    alias_owners: dict[str, set[str]] = defaultdict(set)
    slot_owners: dict[tuple[str, str, int], list[str]] = defaultdict(list)
    namespace_owners: dict[str, list[str]] = defaultdict(list)
    for plugin_id, item in manifests.items():
        raw = item["raw"]
        source = item["source"]
        for task_id, task in _task_records(raw):
            owner = f"{plugin_id}:{task_id}"
            alias_owners[task_id.casefold()].add(owner)
            for alias in task.get("aliases", []):
                alias_owners[str(alias).strip().casefold()].add(owner)
            failures.extend(_validate_read_ladder(root, source, task_id, task))
        for slot in raw.get("contributions", {}).get("ui_slots", []):
            key = (str(slot.get("surface", "")), str(slot.get("slot", "")), int(slot.get("order", 0)))
            slot_owners[key].append(f"{plugin_id}:{slot.get('id', '')}")
        namespace = str(raw.get("state_namespace", "")).strip()
        if namespace:
            namespace_owners[namespace].append(plugin_id)
        validation = raw.get("validation", {})
        for field in ("commands", "behavior_tests"):
            for command in validation.get(field, []):
                target = _command_target(root, str(command))
                if target is not None and not target.is_file():
                    failures.append(f"{source}: {field} target does not exist: {command}")
    for alias, owners in sorted(alias_owners.items()):
        if alias and len(owners) > 1:
            failures.append(f"task alias collision {alias!r}: {sorted(owners)}")
    for key, owners in sorted(slot_owners.items()):
        if len(owners) > 1:
            failures.append(f"UI slot order collision {key}: {owners}")
    for namespace, owners in sorted(namespace_owners.items()):
        if len(owners) > 1:
            failures.append(f"state namespace collision {namespace}: {owners}")
    return failures


def validate_capability_registry(root: Path) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Validate the canonical capability-claim authority, not legacy action records."""
    failures: list[str] = []
    claims: dict[str, dict[str, Any]] = {}
    source = root / CAPABILITY_REGISTRY
    claim_fields = {
        "id", "intended_transformation", "unit_of_analysis", "context_envelope",
        "evidence_criteria", "known_failures", "authority_boundary", "review_triggers",
        "retirement_condition",
    }
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        if data.get("schema_id") != "researchos-capability-registry-v1":
            raise ValueError(f"{source}: schema_id must be researchos-capability-registry-v1")
        if not isinstance(data.get("version"), str) or not data["version"].strip():
            raise ValueError(f"{source}: version is required")
        if not isinstance(data.get("capability_claims"), list) or not data["capability_claims"]:
            raise ValueError(f"{source}: capability_claims must be a non-empty list")
        for index, raw_claim in enumerate(data["capability_claims"]):
            claim = _exact_object(raw_claim, claim_fields, f"{source}: capability_claims[{index}]")
            claim_id = str(claim["id"] or "").strip()
            if not ID_PATTERN.fullmatch(claim_id) or claim_id in claims:
                raise ValueError(f"{source}: capability claim ids must be unique lower_snake_case values")
            for field in ("intended_transformation", "unit_of_analysis", "authority_boundary", "retirement_condition"):
                if not isinstance(claim[field], str) or not claim[field].strip():
                    raise ValueError(f"{source}: {claim_id}.{field} must be a non-empty string")
            for field in ("context_envelope", "evidence_criteria", "known_failures", "review_triggers"):
                values = claim[field]
                if not isinstance(values, list) or not values or len(values) != len(set(values)):
                    raise ValueError(f"{source}: {claim_id}.{field} must be a non-empty unique string list")
                if any(not isinstance(value, str) or not value.strip() for value in values):
                    raise ValueError(f"{source}: {claim_id}.{field} contains an invalid value")
            if any(not ID_PATTERN.fullmatch(value) for value in claim["review_triggers"]):
                raise ValueError(f"{source}: {claim_id}.review_triggers must use lower_snake_case ids")
            claims[claim_id] = claim
        records = data.get("capabilities")
        if not isinstance(records, list):
            raise ValueError(f"{source}: capabilities must remain a list of implementation/action records")
        record_ids = [str(record.get("id") or "").strip() for record in records if isinstance(record, dict)]
        if len(record_ids) != len(records) or any(not ID_PATTERN.fullmatch(value) for value in record_ids):
            raise ValueError(f"{source}: implementation record ids must use lower_snake_case")
        if len(record_ids) != len(set(record_ids)):
            raise ValueError(f"{source}: implementation record ids must be unique")
        companion = source.with_suffix(".md")
        companion_text = companion.read_text(encoding="utf-8")

        def section_ids(heading: str) -> set[str]:
            match = re.search(rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)", companion_text, re.MULTILINE)
            if not match:
                raise ValueError(f"{companion}: missing section {heading!r}")
            return set(re.findall(r"^- `([a-z][a-z0-9_]*)`\s*$", match.group(1), re.MULTILINE))

        if section_ids("Canonical Capability Claims") != set(claims):
            raise ValueError(f"{companion}: canonical capability claim list differs from JSON authority")
        if section_ids("Registered Implementation Records") != set(record_ids):
            raise ValueError(f"{companion}: implementation record list differs from JSON authority")
    except Exception as error:
        failures.append(str(error))
    return failures, claims


def validate_source_registry(root: Path) -> tuple[list[str], dict[str, dict[str, Any]]]:
    failures: list[str] = []
    source = root / SOURCE_REGISTRY
    candidates: dict[str, dict[str, Any]] = {}
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        _exact_object(data, {"schema_id", "version", "candidates"}, str(source))
        if data["schema_id"] != "researchos-capability-source-registry-v1":
            raise ValueError(f"{source}: unsupported source registry schema_id")
        if not isinstance(data["version"], str) or not re.fullmatch(r"\d+\.\d+\.\d+", data["version"]):
            raise ValueError(f"{source}: version must use semantic x.y.z form")
        if not isinstance(data["candidates"], list):
            raise ValueError(f"{source}: candidates must be a list")
        fields = {"id", "kind", "name", "url", "version", "license", "reuse_mode", "status", "retrieved_on", "note"}
        for index, candidate in enumerate(data["candidates"]):
            item = _exact_object(candidate, fields, f"{source}: candidates[{index}]")
            candidate_id = str(item["id"] or "").strip()
            if not ID_PATTERN.fullmatch(candidate_id) or candidate_id in candidates:
                raise ValueError(f"{source}: candidate ids must be unique lower_snake_case values")
            if item["kind"] not in SOURCE_KINDS or item["reuse_mode"] not in REUSE_MODES or item["status"] not in SOURCE_STATUSES:
                raise ValueError(f"{source}: candidate {candidate_id} has unsupported kind, reuse_mode, or status")
            if not all(isinstance(item[field], str) and item[field].strip() for field in ("name", "version", "license", "note")):
                raise ValueError(f"{source}: candidate {candidate_id} requires name, version, license, and note")
            if not HTTPS_PATTERN.fullmatch(str(item["url"])) or not DATE_PATTERN.fullmatch(str(item["retrieved_on"])):
                raise ValueError(f"{source}: candidate {candidate_id} requires an HTTPS URL and YYYY-MM-DD retrieval date")
            if item["status"] == "promoted":
                if item["reuse_mode"] == "reference_only":
                    raise ValueError(f"{source}: promoted candidate {candidate_id} must be adapted or composed")
                if str(item["version"]).lower() in MUTABLE_VERSION_BOUNDARIES or str(item["license"]).lower() in {"unknown", "none", "unlicensed"}:
                    raise ValueError(f"{source}: promoted candidate {candidate_id} requires pinned provenance and usable license")
            candidates[candidate_id] = item
    except Exception as error:
        failures.append(str(error))
    return failures, candidates


def _validate_human_admission_receipt(
    root: Path, plugin_id: str, capability_ids: set[str], proof_refs: list[str]
) -> list[str]:
    failures: list[str] = []
    receipt_fields = {
        "schema_id", "capability_id", "decision", "decided_at", "authority_role",
        "real_use_refs", "baseline_evidence_ref", "accepted_scope", "known_failures",
        "revalidation_triggers",
    }
    receipts = []
    for proof_ref in proof_refs:
        path = root / proof_ref
        if path.suffix != ".json" or not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("schema_id") == "researchos-plugin-admission-receipt-v1":
            receipts.append((path, data))
    if not receipts:
        return [f"{plugin_id}: human_admitted requires one researchos-plugin-admission-receipt-v1 proof per bound capability claim"]
    admitted_ids: set[str] = set()
    for path, receipt in receipts:
        try:
            _exact_object(receipt, receipt_fields, str(path))
            if receipt["capability_id"] not in capability_ids or receipt["decision"] != "admit":
                raise ValueError(f"{path}: receipt capability_id must name a capability claim bound by {plugin_id}")
            admitted_ids.add(receipt["capability_id"])
            if not DATE_PATTERN.fullmatch(str(receipt["decided_at"])) or not str(receipt["authority_role"] or "").strip():
                raise ValueError(f"{path}: receipt requires a date and human authority role")
            if not isinstance(receipt["real_use_refs"], list) or not receipt["real_use_refs"]:
                raise ValueError(f"{path}: receipt requires real_use_refs")
            referenced = [*receipt["real_use_refs"], receipt["baseline_evidence_ref"]]
            if not all(isinstance(value, str) and value.strip() and (root / value).is_file() for value in referenced):
                raise ValueError(f"{path}: receipt evidence refs must resolve to repository files")
            if not str(receipt["accepted_scope"] or "").strip() or not isinstance(receipt["known_failures"], list):
                raise ValueError(f"{path}: receipt requires accepted_scope and known_failures")
            triggers = receipt["revalidation_triggers"]
            if not isinstance(triggers, list) or not triggers or any(not isinstance(value, str) or not ID_PATTERN.fullmatch(value) for value in triggers):
                raise ValueError(f"{path}: receipt revalidation_triggers must be non-empty lower_snake_case ids")
        except Exception as error:
            failures.append(str(error))
    missing = sorted(capability_ids - admitted_ids)
    if missing:
        failures.append(f"{plugin_id}: human_admitted is missing capability admission receipts for {missing}")
    return failures


def validate_repository(root: Path) -> tuple[list[str], dict[str, dict[str, Any]]]:
    failures, capability_claims = validate_capability_registry(root)
    source_failures, source_candidates = validate_source_registry(root)
    failures.extend(source_failures)
    manifests: dict[str, dict[str, Any]] = {}
    capabilities: set[str] = {"researchos_core", *capability_claims}
    capability_owners: dict[str, list[str]] = defaultdict(list)
    contribution_owners: dict[str, list[str]] = defaultdict(list)
    task_ids: set[str] = set()
    normalized_items: list[dict[str, Any]] = []
    for source in manifest_paths(root):
        try:
            raw, normalized = _validate_one(root, source)
            plugin_id = normalized["id"]
            if plugin_id in manifests:
                raise ValueError(f"duplicate checked-in plugin id: {plugin_id}")
            manifests[plugin_id] = {"raw": raw, "normalized": normalized, "source": source}
            normalized_items.append(normalized)
            governance = normalized["governance"]
            archetype = governance["archetype"]
            bound_claim_ids: set[str] = set()
            if archetype == "capability_led":
                bound_claim_ids = {
                    claim_id
                    for binding in governance["capability_bindings"]
                    for claim_id in binding["claim_ids"]
                }
                missing_claims = sorted(bound_claim_ids - set(capability_claims))
                if missing_claims:
                    raise ValueError(f"{source}: capability bindings reference unregistered claims: {missing_claims}")
                for capability in bound_claim_ids:
                    capability_owners[capability].append(plugin_id)
            for contribution in governance["composition"]["provides"]:
                contribution_owners[contribution].append(plugin_id)
            manifest_task_ids = {
                descriptor["id"] for descriptor in normalized.get("_task_descriptors", [])
            }
            if normalized.get("schema_id") == "researchos-task-extension-v1":
                manifest_task_ids.add(normalized["id"])
            if archetype == "capability_led":
                projected_task_ids = {
                    projection["task_id"] for projection in governance["task_projections"]
                }
                if manifest_task_ids != projected_task_ids:
                    raise ValueError(
                        f"{source}: task_projections must map every contributed task exactly once; "
                        f"tasks={sorted(manifest_task_ids)}, projections={sorted(projected_task_ids)}"
                    )
            else:
                task_contract_id = governance["task_contract"]["task_id"]
                if manifest_task_ids != {task_contract_id}:
                    raise ValueError(
                        f"{source}: task_led task_contract must own exactly the contributed task; "
                        f"tasks={sorted(manifest_task_ids)}, task_contract={task_contract_id}"
                    )
            task_ids.update(manifest_task_ids)
            for source_ref in governance["lineage"]["source_refs"]:
                candidate = source_candidates.get(source_ref["candidate_id"])
                if candidate is None:
                    raise ValueError(f"{source}: source candidate is not registered: {source_ref['candidate_id']}")
                for field in ("kind", "name", "url", "version", "license", "reuse_mode"):
                    if source_ref[field] != candidate[field]:
                        raise ValueError(f"{source}: source candidate snapshot differs for {source_ref['candidate_id']}.{field}")
            for proof_ref in governance["admission"]["proof_refs"]:
                proof_path = root / proof_ref
                if not proof_path.is_file():
                    raise ValueError(f"{source}: governance proof_ref does not exist: {proof_ref}")
            value_field = "capability_value" if archetype == "capability_led" else "task_contract"
            for evidence_ref in governance[value_field]["evidence_refs"]:
                if not (root / evidence_ref).is_file():
                    raise ValueError(f"{source}: {value_field} evidence_ref does not exist: {evidence_ref}")
            if archetype == "capability_led" and governance["admission"]["maturity"] == "human_admitted":
                failures.extend(_validate_human_admission_receipt(
                    root, plugin_id, bound_claim_ids, governance["admission"]["proof_refs"]
                ))
            if governance["deployment_mode"] == "local_installable" and normalized["enabled"]:
                raise ValueError(f"{source}: checked-in local_installable example must ship disabled")
        except Exception as error:
            failures.append(str(error))

    failures.extend(validate_manifest_surface_contracts(root, manifests))
    duplicate_contributions = {value: owners for value, owners in contribution_owners.items() if len(owners) > 1}
    for contribution, owners in sorted(duplicate_contributions.items()):
        failures.append(f"{contribution}: duplicate contribution providers: {owners}")
    duplicate_providers = {capability: owners for capability, owners in capability_owners.items() if len(owners) > 1}
    for capability, owners in sorted(duplicate_providers.items()):
        failures.append(f"{capability}: duplicate capability claim owners: {owners}")
    unbound_claims = sorted(set(capability_claims) - set(capability_owners))
    if unbound_claims:
        failures.append(f"capability registry has claims without a plugin contribution: {unbound_claims}")

    enabled_items = [item for item in normalized_items if item["enabled"]]
    for item in normalized_items:
        governance = item["governance"]
        missing = sorted(set(governance["composition"]["requires"]) - {"researchos_core", *contribution_owners})
        if missing:
            failures.append(f"{item['id']}: missing required contributions: {missing}")
        optional_integrations = set(governance["composition"]["optional_integrations"])
        unknown_optional = sorted(optional_integrations - set(capability_claims))
        if unknown_optional:
            failures.append(f"{item['id']}: optional integrations use unregistered capability claims: {unknown_optional}")
        for handoff in governance["routing"]["handoff_to"]:
            target = handoff["id"]
            if handoff["kind"] == "core_route" and target not in CORE_ROUTE_IDS:
                failures.append(f"{item['id']}: unknown core handoff route: {target}")
            elif handoff["kind"] == "capability" and target not in capabilities:
                if handoff["availability"] == "required" or target not in optional_integrations:
                    failures.append(f"{item['id']}: unresolved capability handoff: {target}")
            elif handoff["kind"] == "task" and target not in task_ids and handoff["availability"] == "required":
                failures.append(f"{item['id']}: unresolved task handoff: {target}")
        if item["enabled"]:
            active_conflicts = sorted(
                set(governance["composition"]["conflicts_with"])
                & {
                    claim_id
                    for other in enabled_items
                    for binding in other["governance"].get("capability_bindings", [])
                    for claim_id in binding["claim_ids"]
                }
            )
            if active_conflicts:
                failures.append(f"{item['id']}: enabled capability conflicts are active: {active_conflicts}")
    return failures, manifests


def _drop_path(data: dict[str, Any], dotted: str) -> None:
    cursor: Any = data
    parts = dotted.split(".")
    for part in parts[:-1]:
        if not isinstance(cursor, dict) or part not in cursor:
            return
        cursor = cursor[part]
    if isinstance(cursor, dict):
        cursor.pop(parts[-1], None)


def validate_parity(
    private: dict[str, dict[str, Any]], public: dict[str, dict[str, Any]]
) -> list[str]:
    failures: list[str] = []
    for plugin_id, private_item in private.items():
        private_raw = private_item["raw"]
        distribution = private_raw["governance"]["distribution"]
        policy = distribution["parity_policy"]
        public_item = public.get(plugin_id)
        if policy == "private_only":
            if public_item is not None:
                failures.append(f"{plugin_id}: private_only plugin must not appear in public starter")
            continue
        if public_item is None:
            failures.append(f"{plugin_id}: {policy} plugin is missing from public starter")
            continue
        public_raw = public_item["raw"]
        if private_raw.get("version") != public_raw.get("version"):
            failures.append(f"{plugin_id}: private/public versions differ")
            continue
        public_distribution = public_raw["governance"]["distribution"]
        if public_distribution["parity_policy"] != policy:
            failures.append(f"{plugin_id}: private/public parity_policy differs")
            continue
        if policy == "exact":
            if private_raw != public_raw:
                failures.append(f"{plugin_id}: exact private/public manifests differ")
            continue
        allowed = distribution["allowed_divergence_fields"]
        if public_distribution["allowed_divergence_fields"] != allowed:
            failures.append(f"{plugin_id}: scoped variants disagree on allowed divergence fields")
            continue
        if distribution["variant"] != "private" or public_distribution["variant"] != "public":
            failures.append(f"{plugin_id}: scoped variants must declare private/public sides")
        private_compare = deepcopy(private_raw)
        public_compare = deepcopy(public_raw)
        for path in allowed:
            _drop_path(private_compare, path)
            _drop_path(public_compare, path)
        if private_compare != public_compare:
            failures.append(f"{plugin_id}: scoped variant differs outside declared fields")

    for plugin_id, public_item in public.items():
        if plugin_id not in private:
            policy = public_item["raw"]["governance"]["distribution"]["parity_policy"]
            failures.append(f"{plugin_id}: public-only plugin has no private authority ({policy})")
    return failures


def validate_capability_claim_parity(
    private_claims: dict[str, dict[str, Any]], public_claims: dict[str, dict[str, Any]]
) -> list[str]:
    failures: list[str] = []
    for claim_id, public_claim in sorted(public_claims.items()):
        private_claim = private_claims.get(claim_id)
        if private_claim is None:
            failures.append(f"{claim_id}: public capability claim has no private authority")
        elif private_claim != public_claim:
            failures.append(f"{claim_id}: public capability claim differs from private authority")
    return failures


def _string_values(value: Any) -> set[str]:
    values: set[str] = set()
    if isinstance(value, str):
        values.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            values.update(_string_values(item))
    elif isinstance(value, list):
        for item in value:
            values.update(_string_values(item))
    return values


def validate_public_private_boundary(
    private: dict[str, dict[str, Any]], public: dict[str, dict[str, Any]], public_root: Path
) -> list[str]:
    failures: list[str] = []
    private_symbols: set[str] = set()
    for plugin_id, item in private.items():
        governance = item["raw"]["governance"]
        if governance["distribution"]["parity_policy"] != "private_only":
            continue
        private_symbols.add(plugin_id)
        private_symbols.update(governance["composition"]["provides"])

    for plugin_id, item in public.items():
        leaked = sorted(private_symbols & _string_values(item["raw"]))
        if leaked:
            failures.append(f"{plugin_id}: public manifest references private-only capability symbols: {leaked}")

    token_patterns = {
        symbol: re.compile(rf"(?<![a-z0-9_]){re.escape(symbol)}(?![a-z0-9_])")
        for symbol in private_symbols
    }
    for relative_root in PUBLIC_RUNTIME_ROOTS:
        base = public_root / relative_root
        if not base.exists():
            continue
        for path in sorted(p for p in base.rglob("*") if p.suffix in {".js", ".py", ".json"} and p.is_file()):
            text = path.read_text(encoding="utf-8")
            leaked = sorted(symbol for symbol, pattern in token_patterns.items() if pattern.search(text))
            if leaked:
                failures.append(f"{path}: public runtime source contains private-only capability symbols: {leaked}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-root", type=Path)
    args = parser.parse_args()
    failures, private = validate_repository(ROOT)
    failures.extend(validate_plugin_standard_translation(ROOT))
    private_claim_failures, private_claims = validate_capability_registry(ROOT)
    failures.extend(private_claim_failures)
    if args.public_root:
        public_root = args.public_root.resolve()
        public_failures, public = validate_repository(public_root)
        public_failures.extend(validate_plugin_standard_translation(public_root))
        public_claim_failures, public_claims = validate_capability_registry(public_root)
        failures.extend(public_failures)
        failures.extend(public_claim_failures)
        failures.extend(validate_capability_claim_parity(private_claims, public_claims))
        failures.extend(validate_parity(private, public))
        failures.extend(validate_public_private_boundary(private, public, public_root))
    if failures:
        print("ResearchOS Plugin Standard v1.2 validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    scope = " with private/public semantic parity" if args.public_root else ""
    print(f"OK: {len(private)} checked-in plugins satisfy ResearchOS Plugin Standard v1.2{scope}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
