from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_data.plugin_governance import PluginGovernanceError, validate_governance
from validate_plugin_standard import (
    _validate_human_admission_receipt,
    validate_capability_claim_parity,
    validate_capability_registry,
    validate_parity,
    validate_plugin_standard_translation,
    validate_repository,
)


class PluginGovernanceContractTest(unittest.TestCase):
    def test_controlled_plugin_standard_translation_fails_on_anchor_drift(self) -> None:
        self.assertEqual([], validate_plugin_standard_translation(ROOT))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative_dir = Path("05_workflows/research_management")
            target = root / relative_dir
            target.mkdir(parents=True)
            for name in ("researchos-plugin-standard-v1.2.md", "researchos-plugin-standard-v1.2.zh.md"):
                text = (ROOT / relative_dir / name).read_text(encoding="utf-8")
                if name.endswith(".zh.md"):
                    text = text.replace("<!-- semantic-anchor: governance_card -->\n", "", 1)
                (target / name).write_text(text, encoding="utf-8")
            failures = validate_plugin_standard_translation(root)
        self.assertIn("semantic anchors drifted", "\n".join(failures))

    def governance(self) -> dict[str, object]:
        return {
            "schema_id": "researchos-plugin-governance-v1",
            "contract_id": "researchos.contribution.fixture_plugin",
            "archetype": "capability_led",
            "distribution": {"variant": "private", "parity_policy": "private_only", "allowed_divergence_fields": []},
            "lineage": {
                "prototype_id": "researchos_plugin_capability_v1",
                "derivation_mode": "native",
                "reuse_policy": "native",
                "source_refs": [],
                "external_runtime_dependency": "none",
                "transformation_summary": "Native fixture derived from the shared capability prototype.",
                "current_placement": "plugin",
                "proposed_absorption_target": "none",
                "absorption_gate": "review_required",
            },
            "capability_value": {
                "comparison_target": "current_model_without_capability",
                "comparison_status": "planned",
                "expected_deltas": ["reliability"],
                "expected_burdens": ["maintenance_cost"],
                "evidence_refs": [],
                "placement_decision": "pending_comparison",
                "retention_rule": "Retain only after a bounded comparison demonstrates value.",
            },
            "deployment_mode": "bundled_default_on",
            "effects": {"default_effect": "answer", "allowed_effects": ["read_only", "answer", "artifact", "review_candidate"]},
            "data_policy": {"default_sensitivity": "internal", "default_export_policy": "not_exportable"},
            "composition": {"requires": ["researchos_core"], "provides": ["fixture_capability"], "optional_integrations": [], "conflicts_with": []},
            "capability_bindings": [{"contribution_id": "fixture_capability", "claim_ids": ["fixture_claim"]}],
            "task_projections": [],
            "routing": {"trigger_intents": ["fixture_request"], "non_goals": ["direct_authority_write"], "handoff_to": [{"kind": "core_route", "id": "review", "availability": "required"}]},
            "admission": {
                "maturity": "instrumented",
                "proof_refs": ["proof.txt"],
                "last_reviewed": "2026-08-14",
                "revalidation_triggers": ["contract_change"],
                "retirement_condition": "Retire when the fixture no longer tests the contract.",
            },
        }

    def task_governance(self) -> dict[str, object]:
        governance = self.governance()
        governance["archetype"] = "task_led"
        governance["lineage"]["prototype_id"] = "researchos_plugin_task_v1"
        governance.pop("capability_value")
        governance.pop("capability_bindings")
        governance.pop("task_projections")
        governance["composition"]["provides"] = ["fixture_plugin"]
        governance["task_contract"] = {
            "task_id": "fixture_plugin",
            "user_job": "Complete one bounded fixture task with explicit evidence and recovery.",
            "inputs": ["fixture input"],
            "outputs": ["fixture output"],
            "invariants": ["source authority remains external"],
            "confirmation_gates": ["confirm before durable writeback"],
            "completion_criteria": ["output and validation status are reported"],
            "failure_modes": ["fixture input is missing"],
            "recovery": ["request the missing input"],
            "comparison_target": "current_model_without_task_workflow",
            "comparison_status": "planned",
            "expected_deltas": ["reliability"],
            "expected_burdens": ["maintenance_cost"],
            "evidence_refs": [],
            "retention_rule": "Retain only while the bounded workflow shows net task-level value.",
        }
        return governance

    def validate(self, governance: dict[str, object]) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "proof.txt").write_text("proof", encoding="utf-8")
            return validate_governance(
                governance,
                root=root,
                source=root / "manifest.json",
                plugin_id="fixture_plugin",
                product_tier="bundled_capability",
                enabled=True,
                result_modes={"answer", "artifact", "writeback"},
                public_safe=False,
                sensitivity_default="internal",
            )

    def test_explicit_governance_validates(self) -> None:
        self.assertFalse(self.validate(self.governance())["compatibility_defaulted"])

    def test_native_plugin_may_require_an_external_runtime_without_external_derivation(self) -> None:
        governance = self.task_governance()
        governance["lineage"]["external_runtime_dependency"] = "runtime_required"
        normalized = self.validate(governance)
        self.assertEqual("native", normalized["lineage"]["derivation_mode"])
        self.assertEqual("runtime_required", normalized["lineage"]["external_runtime_dependency"])

    def test_task_led_governance_uses_task_contract_without_capability_claim(self) -> None:
        normalized = self.validate(self.task_governance())
        self.assertEqual("task_led", normalized["archetype"])
        self.assertEqual("fixture_plugin", normalized["task_contract"]["task_id"])
        self.assertNotIn("capability_bindings", normalized)

    def test_task_led_governance_rejects_capability_fields(self) -> None:
        governance = self.task_governance()
        governance["capability_bindings"] = []
        with self.assertRaisesRegex(PluginGovernanceError, "unsupported=.*capability_bindings"):
            self.validate(governance)

    def test_task_led_draft_does_not_require_false_proof(self) -> None:
        governance = self.task_governance()
        governance["admission"]["maturity"] = "draft"
        governance["admission"]["proof_refs"] = []
        normalized = self.validate(governance)
        self.assertEqual("draft", normalized["admission"]["maturity"])

    def test_task_led_user_adoption_requires_evaluated_baseline(self) -> None:
        governance = self.task_governance()
        governance["admission"]["maturity"] = "user_adopted"
        with self.assertRaisesRegex(PluginGovernanceError, "requires an evaluated current-model baseline"):
            self.validate(governance)

    def test_external_skill_must_be_linked_transformed_and_licensed(self) -> None:
        governance = self.governance()
        governance["lineage"].update({
            "derivation_mode": "adapted_external",
            "reuse_policy": "link_and_transform",
            "source_refs": [{
                "candidate_id": "upstream_research_skill",
                "kind": "skill",
                "name": "Upstream research skill",
                "url": "https://example.org/upstream-skill",
                "version": "retrieved-2026-08-14",
                "license": "Apache-2.0",
                "reuse_mode": "adapted",
            }],
            "external_runtime_dependency": "optional",
            "transformation_summary": "Retained the upstream link and rebuilt its method around ResearchOS authority and Review contracts.",
        })
        normalized = self.validate(governance)
        self.assertEqual("adapted_external", normalized["lineage"]["derivation_mode"])

    def test_raw_copy_is_not_a_supported_reuse_mode(self) -> None:
        governance = self.governance()
        governance["lineage"].update({
            "derivation_mode": "adapted_external",
            "reuse_policy": "link_and_transform",
            "source_refs": [{
                "candidate_id": "unsafe_copy", "kind": "skill", "name": "Unsafe copy", "url": "https://example.org/skill",
                "version": "1", "license": "unknown", "reuse_mode": "raw_copy",
            }],
        })
        with self.assertRaisesRegex(PluginGovernanceError, "reuse_mode is unsupported"):
            self.validate(governance)

    def test_composed_external_requires_multiple_sources(self) -> None:
        governance = self.governance()
        governance["lineage"].update({
            "derivation_mode": "composed_external",
            "reuse_policy": "link_and_transform",
            "source_refs": [{
                "candidate_id": "only_one", "kind": "skill", "name": "Only one", "url": "https://example.org/one",
                "version": "1", "license": "MIT", "reuse_mode": "composed",
            }],
        })
        with self.assertRaisesRegex(PluginGovernanceError, "at least two linked sources"):
            self.validate(governance)

    def test_adapted_external_rejects_reference_only_source(self) -> None:
        governance = self.governance()
        governance["lineage"].update({
            "derivation_mode": "adapted_external",
            "reuse_policy": "link_and_transform",
            "source_refs": [{
                "candidate_id": "reference_only_source", "kind": "skill", "name": "Reference only",
                "url": "https://example.org/reference", "version": "1.0.0", "license": "MIT",
                "reuse_mode": "reference_only",
            }],
        })
        with self.assertRaisesRegex(PluginGovernanceError, "at least one adapted source"):
            self.validate(governance)

    def test_composed_external_rejects_duplicate_source(self) -> None:
        governance = self.governance()
        source = {
            "candidate_id": "same_source", "kind": "skill", "name": "Same source",
            "url": "https://example.org/same", "version": "1.0.0", "license": "MIT", "reuse_mode": "composed",
        }
        governance["lineage"].update({
            "derivation_mode": "composed_external", "reuse_policy": "link_and_transform",
            "source_refs": [source, copy.deepcopy(source)],
        })
        with self.assertRaisesRegex(PluginGovernanceError, "distinct composed sources"):
            self.validate(governance)

    def test_adapted_external_rejects_mutable_version_and_unknown_license(self) -> None:
        governance = self.governance()
        governance["lineage"].update({
            "derivation_mode": "adapted_external", "reuse_policy": "link_and_transform",
            "source_refs": [{
                "candidate_id": "mutable_source", "kind": "skill", "name": "Mutable source",
                "url": "https://example.org/mutable", "version": "latest", "license": "unknown", "reuse_mode": "adapted",
            }],
        })
        with self.assertRaisesRegex(PluginGovernanceError, "version must be pinned"):
            self.validate(governance)

    def test_human_admission_rejects_unit_test_without_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "test.py").write_text("pass", encoding="utf-8")
            failures = _validate_human_admission_receipt(root, "fixture_plugin", {"fixture_claim"}, ["test.py"])
        self.assertIn("requires one researchos-plugin-admission-receipt-v1 proof per bound capability claim", "\n".join(failures))

    def test_human_admission_receipt_uses_capability_claim_not_plugin_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "real-use.md").write_text("episode", encoding="utf-8")
            (root / "baseline.md").write_text("baseline", encoding="utf-8")
            receipt = {
                "schema_id": "researchos-plugin-admission-receipt-v1",
                "capability_id": "fixture_plugin",
                "decision": "admit",
                "decided_at": "2026-08-14",
                "authority_role": "researcher",
                "real_use_refs": ["real-use.md"],
                "baseline_evidence_ref": "baseline.md",
                "accepted_scope": "bounded fixture",
                "known_failures": [],
                "revalidation_triggers": ["model_change"],
            }
            (root / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            failures = _validate_human_admission_receipt(
                root, "fixture_plugin", {"fixture_claim"}, ["receipt.json"]
            )
            receipt["capability_id"] = "fixture_claim"
            (root / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            accepted = _validate_human_admission_receipt(
                root, "fixture_plugin", {"fixture_claim"}, ["receipt.json"]
            )
        self.assertIn("must name a capability claim bound by fixture_plugin", "\n".join(failures))
        self.assertEqual([], accepted)

    def test_routing_rejects_untyped_handoff(self) -> None:
        governance = self.governance()
        governance["routing"]["handoff_to"] = ["review"]
        with self.assertRaisesRegex(PluginGovernanceError, "must be an object"):
            self.validate(governance)

    def test_task_projection_must_target_owned_capability(self) -> None:
        governance = self.governance()
        governance["task_projections"] = [{
            "task_id": "fixture_task", "contribution_id": "fixture_capability",
            "capability_id": "unowned_capability", "role": "entrypoint",
        }]
        with self.assertRaisesRegex(PluginGovernanceError, "must be bound"):
            self.validate(governance)

    def test_task_projection_rejects_plugin_id_as_capability_claim(self) -> None:
        governance = self.governance()
        governance["task_projections"] = [{
            "task_id": "fixture_task", "contribution_id": "fixture_capability",
            "capability_id": "fixture_plugin", "role": "entrypoint",
        }]
        with self.assertRaisesRegex(PluginGovernanceError, "must be bound"):
            self.validate(governance)

    def test_result_modes_require_declared_research_effects(self) -> None:
        governance = self.governance()
        governance["effects"] = {"default_effect": "answer", "allowed_effects": ["answer"]}
        with self.assertRaisesRegex(PluginGovernanceError, "include artifact"):
            self.validate(governance)

    def test_checked_in_repository_has_no_implicit_governance(self) -> None:
        registry_failures, claims = validate_capability_registry(ROOT)
        self.assertEqual([], registry_failures)
        self.assertIn("material_intake", claims)
        self.assertNotIn("method_comparison", claims)
        failures, manifests = validate_repository(ROOT)
        self.assertEqual([], failures)
        self.assertGreaterEqual(len(manifests), 6)
        self.assertTrue(all("governance" in item["raw"] for item in manifests.values()))
        self.assertEqual("task_led", manifests["method_comparison"]["normalized"]["governance"]["archetype"])
        for item in manifests.values():
            normalized = item["normalized"]
            deployment = normalized["governance"]["deployment_mode"]
            if deployment == "embedded_foundation":
                self.assertEqual("core_bundled", normalized["lifecycle"]["install"])
                self.assertEqual("core_release_change", normalized["lifecycle"]["uninstall"])
            elif deployment == "bundled_default_on":
                self.assertEqual("release_bundled", normalized["lifecycle"]["install"])
                self.assertEqual("release_change", normalized["lifecycle"]["uninstall"])

    def test_exact_parity_rejects_same_version_semantic_drift(self) -> None:
        raw = json.loads((ROOT / "config" / "plugins" / "material-pipeline.json").read_text(encoding="utf-8"))
        changed = copy.deepcopy(raw)
        changed["governance"]["effects"]["default_effect"] = "read_only"
        private = {raw["id"]: {"raw": raw}}
        public = {raw["id"]: {"raw": changed}}
        self.assertIn("exact private/public manifests differ", "\n".join(validate_parity(private, public)))

    def test_public_capability_claim_must_match_private_authority(self) -> None:
        claim = {
            "id": "fixture_claim",
            "intended_transformation": "bounded transformation",
            "unit_of_analysis": "one episode",
            "context_envelope": ["bounded context"],
            "evidence_criteria": ["bounded evidence"],
            "known_failures": ["known failure"],
            "authority_boundary": "human authority",
            "review_triggers": ["model_change"],
            "retirement_condition": "retire when redundant",
        }
        public_claim = copy.deepcopy(claim)
        public_claim["authority_boundary"] = "weaker public boundary"
        failures = validate_capability_claim_parity({"fixture_claim": claim}, {"fixture_claim": public_claim})
        self.assertIn("differs from private authority", "\n".join(failures))

    def test_capability_registry_markdown_cannot_drift_from_json_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "09_templates" / "data_contracts"
            target.mkdir(parents=True)
            claim = {
                "id": "fixture_claim",
                "intended_transformation": "bounded transformation",
                "unit_of_analysis": "one episode",
                "context_envelope": ["bounded context"],
                "evidence_criteria": ["bounded evidence"],
                "known_failures": ["known failure"],
                "authority_boundary": "human authority",
                "review_triggers": ["model_change"],
                "retirement_condition": "retire when redundant",
            }
            registry = {
                "schema_id": "researchos-capability-registry-v1",
                "version": "1.0.0",
                "capability_claims": [claim],
                "capabilities": [],
            }
            (target / "researchos-capability-registry-v1.json").write_text(
                json.dumps(registry), encoding="utf-8"
            )
            (target / "researchos-capability-registry-v1.md").write_text(
                "## Canonical Capability Claims\n\n- `wrong_claim`\n\n"
                "## Registered Implementation Records\n",
                encoding="utf-8",
            )
            failures, _ = validate_capability_registry(root)
        self.assertIn("claim list differs from JSON authority", "\n".join(failures))

    def test_scoped_parity_allows_only_declared_fields(self) -> None:
        raw = json.loads((ROOT / "config" / "extensions" / "method-comparison.example.json").read_text(encoding="utf-8"))
        private_raw = copy.deepcopy(raw)
        private_raw["available_in"] = ["private", "personal_vault"]
        private_raw["public_safe"] = False
        private_raw["governance"]["distribution"]["variant"] = "private"
        private_raw["governance"]["data_policy"]["default_export_policy"] = "not_exportable"
        public_raw = copy.deepcopy(raw)
        public_raw["available_in"] = ["private", "public_starter", "personal_vault"]
        public_raw["public_safe"] = True
        public_raw["governance"]["distribution"]["variant"] = "public"
        public_raw["governance"]["data_policy"]["default_export_policy"] = "public_safe"
        private = {raw["id"]: {"raw": private_raw}}
        public = {raw["id"]: {"raw": public_raw}}
        self.assertEqual([], validate_parity(private, public))
        public_raw["governance"]["effects"]["default_effect"] = "artifact"
        self.assertIn("outside declared fields", "\n".join(validate_parity(private, public)))


if __name__ == "__main__":
    unittest.main()
