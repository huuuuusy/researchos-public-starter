from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import plan_context  # noqa: E402
from researchos_data.plugin_portfolio import current_plugin_portfolio  # noqa: E402
from researchos_data.task_router import TaskIntentError, route_task_intent  # noqa: E402


class PublicCapabilityAlignmentTests(unittest.TestCase):
    def test_reflection_is_public_safe_scoped_candidate_only_and_excludes_plain_writeback(self) -> None:
        manifest = json.loads(
            (ROOT / "config/plugins/reflection-stewardship.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["version"], "1.1.1")
        self.assertEqual(manifest["available_in"], ["public_starter", "personal_vault"])
        self.assertTrue(manifest["public_safe"])
        distribution = manifest["governance"]["distribution"]
        self.assertEqual(distribution["variant"], "public")
        self.assertEqual(distribution["parity_policy"], "scoped_variant")
        self.assertIn("authority", distribution["allowed_divergence_fields"])
        self.assertIn("governance.composition.optional_integrations", distribution["allowed_divergence_fields"])
        self.assertIn("contributions.tasks", distribution["allowed_divergence_fields"])
        non_goals = manifest["governance"]["routing"]["non_goals"]
        self.assertIn("plain_content_writeback", non_goals)
        self.assertIn("automatic_rule_admission", non_goals)
        self.assertFalse(manifest["permissions"]["canonical_write"])
        self.assertEqual(manifest["permissions"]["state_access"], "none")
        self.assertEqual(manifest["governance"]["composition"]["optional_integrations"], [])
        self.assertEqual(
            manifest["governance"]["routing"]["handoff_to"],
            [{"kind": "core_route", "id": "review", "availability": "required"}],
        )
        self.assertEqual(manifest["governance"]["effects"]["default_effect"], "answer")
        self.assertNotIn("external_state_change", manifest["governance"]["effects"]["allowed_effects"])
        registry = json.loads(
            (ROOT / "09_templates/data_contracts/researchos-capability-registry-v1.json").read_text(encoding="utf-8")
        )
        claim = next(item for item in registry["capability_claims"] if item["id"] == "system_reflection")
        self.assertIn("episode receipts", claim["context_envelope"])
        self.assertIn("reflection artifacts accumulate without value", claim["known_failures"])
        self.assertIn("durable cognition and rules", claim["authority_boundary"])
        self.assertIn("no distinct reflection behavior remains", claim["retirement_condition"])

    def test_registry_has_four_non_owning_groups_and_thirteen_claims(self) -> None:
        registry = json.loads(
            (ROOT / "09_templates/data_contracts/researchos-capability-registry-v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(registry["capability_claims"]), 13)
        self.assertEqual(
            [item["id"] for item in registry["capability_groups"]],
            ["foundation", "research_work", "stewardship", "experimental"],
        )
        self.assertTrue(all("ownership_boundary" in item for item in registry["capability_groups"]))

    def test_portfolio_groups_without_granting_effects(self) -> None:
        portfolio = current_plugin_portfolio(ROOT)
        groups = {item["id"]: item["plugin_ids"] for item in portfolio["groups"]}
        self.assertEqual(groups["research_work"], ["research_context", "research_expression"])
        self.assertEqual(
            groups["stewardship"],
            ["alignment_stewardship", "audit_stewardship", "reflection_stewardship", "system_stewardship"],
        )
        self.assertEqual(portfolio["execution"], "copy_only")
        self.assertFalse(portfolio["canonical_write"])
        self.assertFalse(portfolio["legacy_ui_fields_consumed"])

    def test_typed_receipt_is_copy_only_and_non_effectful(self) -> None:
        receipt = route_task_intent({
            "terminal_job": "Audit the supplied evidence",
            "primary_family_candidate": "stewardship",
            "requested_effect": "answer",
            "destination": "conversation",
            "claimed_currentness": "current",
            "sensitivity": "public_safe",
        })
        self.assertEqual(receipt["runtime"]["execution"], "copy_only")
        self.assertFalse(receipt["runtime"]["canonical_write"])
        self.assertFalse(receipt["route"]["authority"]["mutation_allowed_by_receipt"])
        self.assertEqual(receipt["route"]["capability_groups"], ["stewardship"])

    def test_prior_context_reuse_is_bounded_by_identity_and_egress(self) -> None:
        prior = plan_context.plan_task_intent({
            "terminal_job": "Audit the supplied evidence",
            "current_commitment_id": "audit-a",
            "exact_targets": ["README.md"],
            "primary_family_candidate": "stewardship",
            "requested_effect": "answer",
            "destination": "conversation",
            "claimed_currentness": "current",
            "sensitivity": "public_safe",
        }, "en")
        continued = plan_context.plan_task_intent({
            "terminal_job": "Continue the same audit",
            "current_commitment_id": "audit-a",
            "primary_family_candidate": "stewardship",
            "requested_effect": "answer",
            "destination": "conversation",
            "claimed_currentness": "current",
            "sensitivity": "public_safe",
        }, "en", prior_receipt=prior)
        self.assertTrue(continued["context"]["prior_context_reused"])
        self.assertEqual(continued["context"]["read_now"], ["README.md"])

        external = plan_context.plan_task_intent({
            "terminal_job": "Publish the same audit",
            "current_commitment_id": "audit-a",
            "primary_family_candidate": "stewardship",
            "requested_effect": "external_action",
            "destination": "external",
            "claimed_currentness": "current",
            "sensitivity": "public_safe",
        }, "en", prior_receipt=prior)
        self.assertFalse(external["context"]["prior_context_reused"])

    def test_invalid_family_fails_closed(self) -> None:
        with self.assertRaises(TaskIntentError):
            route_task_intent({
                "terminal_job": "Do something",
                "primary_family_candidate": "private_route",
                "sensitivity": "public_safe",
            })

    def test_all_public_routes_and_private_compatibility_aliases_resolve(self) -> None:
        expected = {
            "first_run_onboarding", "material_intake", "card_upgrade", "codex_handoff",
            "external_demand_response", "relationship_opportunity", "maintenance_check",
            "system_evolution_review", "material_understanding", "idea_diagnosis",
            "new_project_intake", "safe_export", "collaborative_alignment", "research_audit",
            "system_reflection", "research_self_model", "paper_writing", "proposal",
            "presentation", "figure_design",
        }
        self.assertEqual({str(item["id"]) for item in plan_context.task_routes("en")}, expected)
        aliases = {
            "relationship_network": "relationship_opportunity",
            "self_evolution": "system_evolution_review",
            "system_maintenance": "maintenance_check",
            "memory_update": "card_upgrade",
            "codex_thread_handoff": "codex_handoff",
        }
        for alias, target in aliases.items():
            self.assertEqual(plan_context.route_for(alias, "en")["id"], target)

    def test_headless_routes_are_public_safe_and_do_not_require_ui(self) -> None:
        for task in plan_context.task_routes("en"):
            payload = plan_context.route_payload(task, "en", "quick", include_legacy_client_fields=False)
            self.assertNotIn("primary_surface", payload)
            self.assertNotIn("dashboard_role", payload)
            self.assertEqual(payload["sensitivity_default"], "local_only")
            for source in payload["read_now"]:
                self.assertTrue((ROOT / source).is_file(), source)

    def test_missing_or_escaping_source_fails_closed(self) -> None:
        base = {
            "terminal_job": "Understand the selected source",
            "primary_family_candidate": "understanding",
            "requested_effect": "answer",
            "destination": "conversation",
            "claimed_currentness": "current",
            "sensitivity": "public_safe",
        }
        with self.assertRaises(TaskIntentError):
            route_task_intent({**base, "exact_targets": ["missing-source.md"]})
        with self.assertRaises(TaskIntentError):
            route_task_intent({**base, "exact_targets": ["../private/source.md"]})

    def test_sensitive_external_destination_is_blocked(self) -> None:
        receipt = route_task_intent({
            "terminal_job": "Publish the selected source",
            "primary_family_candidate": "expression",
            "requested_effect": "external_action",
            "destination": "external",
            "claimed_currentness": "current",
            "sensitivity": "local_only",
        })
        self.assertEqual(receipt["status"], "blocked")
        self.assertFalse(receipt["route"]["authority"]["external_effect_allowed_by_receipt"])

    def test_target_symlink_cannot_escape_public_vault(self) -> None:
        import tempfile
        from unittest import mock
        from researchos_data import task_router
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory); root = parent / "vault"; root.mkdir()
            outside = parent / "outside.md"; outside.write_text("Synthetic outside")
            (root / "linked.md").symlink_to(outside)
            nested = root / "nested"; nested.symlink_to(parent, target_is_directory=True)
            (root / "inside.md").write_text("Synthetic inside")
            with mock.patch.object(task_router, "ROOT", root):
                for target in ("linked.md", "nested/outside.md", "../outside.md", str(outside)):
                    with self.assertRaises(TaskIntentError):
                        task_router.normalize_task_intent({"terminal_job": "read source", "exact_targets": [target]})
                self.assertEqual(task_router.normalize_task_intent({"terminal_job": "read source", "exact_targets": ["inside.md"]})["exact_targets"], ["inside.md"])


if __name__ == "__main__":
    unittest.main()
