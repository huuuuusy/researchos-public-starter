from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_data.plugins import (
    PluginManifestError,
    load_plugin_registry,
    ownership_overlay_failures,
    ownership_registry_summary,
    validate_plugin_files,
    validate_plugin_manifest,
)
from researchos_data.task_extensions import load_task_extensions


TASK_EXAMPLE = ROOT / "config" / "extensions" / "method-comparison.example.json"


class PluginHostContractTest(unittest.TestCase):
    def manifest(self, *, plugin_id: str = "fixture_plugin", enabled: bool = True) -> dict[str, object]:
        return {
            "schema_id": "researchos-plugin-v1",
            "core_api_version": "1",
            "id": plugin_id,
            "version": "1.0.0",
            "enabled": enabled,
            "available_in": ["private"],
            "execution_profile": "declarative",
            "product_tier": "bundled_capability",
            "public_safe": False,
            "sensitivity_default": "internal",
            "authority": {
                "source": "Confirmed ResearchOS sources remain authoritative.",
                "candidate": "Plugin output remains candidate-only.",
                "confirmation": "Human confirmation is required before durable change.",
                "save_target": "Use the existing Review route.",
                "requires_human_confirmation": True,
                "writeback_route": "review",
                "storage_owner": "researchos_core",
            },
            "permissions": {
                "read_paths": ["fixture.md"],
                "network_domains": [],
                "command_ids": [],
                "state_access": "none",
                "canonical_write": False,
            },
            "contributions": {
                "tasks": [],
                "actions": [{
                    "id": "fixture_action",
                    "handler": "fixture_handler",
                    "surface": "utility",
                    "execution": "client",
                }],
                "candidate_types": [],
                "asset_types": [],
                "source_adapters": [],
                "previewers": [],
                "projections": [],
                "ui_slots": [],
            },
            "state_namespace": f"researchos.plugin.{plugin_id}",
            "lifecycle": {
                "install": "manifest_present",
                "enable": "manifest_flag",
                "disable": "manifest_flag",
                "uninstall": "remove_manifest",
                "migrations": [],
            },
            "validation": {
                "commands": ["python3 scripts/validate_plugins.py"],
                "behavior_tests": ["python3 -m unittest evals.test_plugins"],
            },
        }

    def fixture_root(self, manifests: list[dict[str, object]]) -> tempfile.TemporaryDirectory[str]:
        context = tempfile.TemporaryDirectory()
        root = Path(context.name)
        (root / "fixture.md").write_text("---\nsensitivity: public\n---\nfixture\n", encoding="utf-8")
        plugin_dir = root / "config" / "plugins"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        for index, manifest in enumerate(manifests):
            (plugin_dir / f"plugin-{index}.json").write_text(
                json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
            )
        return context

    def test_valid_manifest_loads_and_summary_omits_paths_and_permissions(self) -> None:
        with self.fixture_root([self.manifest()]) as directory:
            root = Path(directory)
            self.assertEqual(validate_plugin_files(root), [])
            result = load_plugin_registry(root, runtime_scope="private", language="zh-CN")
        self.assertEqual(result["loaded_count"], 1)
        self.assertEqual(result["loaded"][0]["id"], "fixture_plugin")
        self.assertEqual(result["loaded"][0]["product_tier"], "bundled_capability")
        rendered = json.dumps(result["loaded"], ensure_ascii=False)
        self.assertNotIn(directory, rendered)
        self.assertNotIn("read_paths", rendered)
        self.assertNotIn("network_domains", rendered)

    def test_disabled_manifest_is_valid_but_not_loaded(self) -> None:
        with self.fixture_root([self.manifest(enabled=False)]) as directory:
            result = load_plugin_registry(Path(directory), runtime_scope="private", language="en")
        self.assertEqual(result["loaded_count"], 0)
        self.assertEqual(result["disabled_count"], 1)

    def test_duplicate_plugin_id_fails_closed(self) -> None:
        with self.fixture_root([self.manifest(), self.manifest()]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "already belongs"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_unknown_core_api_major_fails_closed(self) -> None:
        manifest = self.manifest()
        manifest["core_api_version"] = "2"
        with self.fixture_root([manifest]) as directory:
            root = Path(directory)
            source = root / "config" / "plugins" / "plugin-0.json"
            with self.assertRaisesRegex(PluginManifestError, "unknown core_api_version"):
                validate_plugin_manifest(manifest, root=root, source=source)

    def test_missing_product_tier_fails_closed(self) -> None:
        manifest = self.manifest()
        manifest.pop("product_tier")
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "product_tier"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_foundation_projection_cannot_own_conversation_task(self) -> None:
        manifest = self.manifest()
        manifest["product_tier"] = "foundation_projection"
        descriptor = json.loads(TASK_EXAMPLE.read_text(encoding="utf-8"))
        manifest["permissions"]["read_paths"] = []
        manifest["contributions"]["actions"] = []
        manifest["contributions"]["tasks"] = [{"id": "fixture_task", "task": descriptor["task"]}]
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "must not own conversation tasks"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_public_unsafe_manifest_fails_closed(self) -> None:
        manifest = self.manifest()
        manifest["available_in"] = ["public_starter"]
        manifest["public_safe"] = False
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "must be public_safe"):
                load_plugin_registry(Path(directory), runtime_scope="public_starter", language="en")

    def test_public_manifest_cannot_request_execution_permissions(self) -> None:
        manifest = self.manifest()
        manifest["available_in"] = ["public_starter"]
        manifest["public_safe"] = True
        manifest["sensitivity_default"] = "public_safe"
        manifest["execution_profile"] = "external_bridge"
        manifest["permissions"]["network_domains"] = ["example.org"]
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "must be declarative"):
                load_plugin_registry(Path(directory), runtime_scope="public_starter", language="en")

    def test_private_bridge_and_trusted_local_permissions_never_enter_browser_registry(self) -> None:
        bridge = self.manifest(plugin_id="bridge_fixture")
        bridge["execution_profile"] = "external_bridge"
        bridge["permissions"]["network_domains"] = ["example.org"]
        bridge["contributions"]["actions"][0]["execution"] = "platform_registered"
        trusted = self.manifest(plugin_id="trusted_fixture")
        trusted["execution_profile"] = "trusted_local"
        trusted["permissions"]["command_ids"] = ["registered_command"]
        trusted["contributions"]["actions"][0]["execution"] = "platform_registered"
        with self.fixture_root([bridge, trusted]) as directory, \
                patch("subprocess.run") as command, \
                patch("socket.create_connection") as network:
            registry = load_plugin_registry(Path(directory), runtime_scope="private", language="en")
        command.assert_not_called(); network.assert_not_called()
        rendered = json.dumps(registry, ensure_ascii=False)
        self.assertIn("external_bridge", rendered)
        self.assertIn("trusted_local", rendered)
        self.assertNotIn("example.org", rendered)
        self.assertNotIn("registered_command", rendered)
        self.assertNotIn("network_domains", rendered)
        self.assertNotIn("command_ids", rendered)
        loaded = {item["id"]: item for item in registry["loaded"]}
        self.assertEqual("host_disabled", loaded["bridge_fixture"]["execution_boundary"]["state"])
        self.assertEqual("host_disabled", loaded["trusted_fixture"]["execution_boundary"]["state"])
        self.assertIn("researchos-authorization-grant-v1", loaded["bridge_fixture"]["execution_boundary"]["required_contracts"])
        self.assertFalse(any(
            item.get("plugin_id") in {"bridge_fixture", "trusted_fixture"}
            for items in registry["contributions"].values() for item in items
        ))

    def test_executable_profile_actions_must_be_platform_registered(self) -> None:
        manifest = self.manifest()
        manifest["execution_profile"] = "trusted_local"
        manifest["permissions"]["command_ids"] = ["registered_command"]
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "platform_registered"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_execution_profiles_cannot_mix_trust_zones(self) -> None:
        cases = (
            ("trusted_local", [], [], "require command_ids"),
            ("trusted_local", ["example.org"], ["registered_command"], "cannot request network"),
            ("external_bridge", [], [], "require network_domains"),
            ("external_bridge", ["example.org"], ["registered_command"], "cannot request command"),
        )
        for profile, domains, commands, message in cases:
            with self.subTest(profile=profile, domains=domains, commands=commands):
                manifest = self.manifest()
                manifest["execution_profile"] = profile
                manifest["permissions"]["network_domains"] = domains
                manifest["permissions"]["command_ids"] = commands
                with self.fixture_root([manifest]) as directory:
                    with self.assertRaisesRegex(PluginManifestError, message):
                        load_plugin_registry(Path(directory), runtime_scope="private", language="en")
        schema = json.loads((ROOT / "09_templates/data_contracts/researchos-plugin-v1.schema.json").read_text())
        profiles = {
            rule["if"]["properties"]["execution_profile"]["const"]: rule
            for rule in schema["allOf"]
        }
        self.assertEqual({"declarative", "trusted_local", "external_bridge"}, set(profiles))
        self.assertEqual(1, profiles["trusted_local"]["then"]["properties"]["permissions"]["properties"]["command_ids"]["minItems"])
        self.assertEqual(1, profiles["external_bridge"]["then"]["properties"]["permissions"]["properties"]["network_domains"]["minItems"])
        action_surfaces = schema["$defs"]["action_contribution"]["properties"]["surface"]["enum"]
        self.assertNotIn("next", action_surfaces)
        self.assertNotIn("processing", action_surfaces)
        self.assertIn("start", action_surfaces)

    def test_plugin_manifest_cannot_declare_provider_credential_or_egress_ports(self) -> None:
        for field, value in (
            ("provider", "claude"), ("credential_ref", "env:SECRET"),
            ("egress_decision", {"authorization_state": "authorized"}),
        ):
            with self.subTest(field=field):
                manifest = self.manifest(); manifest[field] = value
                with self.fixture_root([manifest]) as directory:
                    with self.assertRaisesRegex(PluginManifestError, "unsupported fields"):
                        load_plugin_registry(Path(directory), runtime_scope="private", language="en")
        manifest = self.manifest()
        manifest["contributions"]["providers"] = [{"id": "claude"}]
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "unsupported types"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_provider_platform_owners_do_not_import_plugin_host(self) -> None:
        for relative in (
            "scripts/researchos_adapters/provider_registry.py",
            "scripts/researchos_adapters/provider_adapter.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("researchos_data.plugins", source)
            self.assertNotIn("load_plugin_registry", source)

    def test_read_path_cannot_escape_repository(self) -> None:
        manifest = self.manifest()
        manifest["permissions"]["read_paths"] = ["../outside.md"]
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "stay inside the repository"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_illegal_canonical_write_permission_fails_closed(self) -> None:
        manifest = self.manifest()
        manifest["permissions"]["canonical_write"] = True
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "canonical_write must be false"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_plugin_identifier_cannot_shadow_core_route(self) -> None:
        manifest = self.manifest(plugin_id="material_intake")
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "already belongs to core"):
                load_plugin_registry(
                    Path(directory),
                    runtime_scope="private",
                    language="en",
                    base_task_ids={"material_intake"},
                )

    def test_task_extension_v1_adapter_preserves_task_output(self) -> None:
        descriptor = json.loads(TASK_EXAMPLE.read_text(encoding="utf-8"))
        descriptor.pop("governance", None)
        descriptor.pop("documentation", None)
        descriptor["enabled"] = True
        with self.fixture_root([]) as directory:
            root = Path(directory)
            extension_dir = root / "config" / "extensions"
            extension_dir.mkdir(parents=True, exist_ok=True)
            (extension_dir / "method-comparison.json").write_text(
                json.dumps(descriptor, ensure_ascii=False), encoding="utf-8"
            )
            read_groups = [descriptor["task"]["read"]]
            read_groups.extend(descriptor["task"].get("read_locales", {}).values())
            for relative in {path for tiers in read_groups for tier in tiers.values() for path in tier}:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("---\nsensitivity: public\n---\nfixture\n", encoding="utf-8")
            legacy = load_task_extensions(root, runtime_scope="private", language="zh-CN")
            registry = load_plugin_registry(root, runtime_scope="private", language="zh-CN")
        compatible_tasks = [task for task in registry["tasks"] if task["plugin_origin"] == "task_extension_v1"]
        self.assertEqual(len(compatible_tasks), len(legacy["tasks"]))
        stripped = [
            {key: value for key, value in task.items() if key not in {"plugin_id", "plugin_version", "plugin_origin", "plugin_tier"}}
            for task in compatible_tasks
        ]
        self.assertEqual(stripped, legacy["tasks"])

    def test_native_system_stewardship_exposes_localized_runtime_contributions(self) -> None:
        manifest = json.loads((ROOT / "config" / "plugins" / "system-stewardship.json").read_text(encoding="utf-8"))
        runtime_scope = "public_starter" if "public_starter" in manifest["available_in"] else "private"
        registry = load_plugin_registry(ROOT, runtime_scope=runtime_scope, language="zh-CN")
        slots = [
            item for item in registry["contributions"]["ui_slots"]
            if item.get("plugin_id") == "system_stewardship"
        ]
        self.assertEqual([item["id"] for item in slots], ["system_stewardship_utility"])
        self.assertEqual(slots[0]["title"], "系统维护")
        self.assertNotIn("locales", slots[0])
        self.assertEqual({
            item["id"] for item in registry["contributions"]["projections"]
            if item.get("plugin_id") == "system_stewardship"
        }, {
            "asset_graph", "external_evidence", "maintenance_commands", "safe_export", "source_overview", "system_health"
        })
        projection_keys = {
            item["contribution_key"] for item in registry["contributions"]["projections"]
            if item["id"] in {"asset_graph", "source_overview"}
        }
        self.assertEqual(len(projection_keys), 4)
        self.assertIn("system_stewardship:asset_graph", projection_keys)
        self.assertIn("research_assets:asset_graph", projection_keys)
        rendered = json.dumps(registry["contributions"], ensure_ascii=False)
        self.assertNotIn("config/plugins", rendered)
        self.assertNotIn("permissions", rendered)

    def test_material_pipeline_candidate_types_are_public_safe_and_independently_declared(self) -> None:
        manifest = json.loads((ROOT / "config" / "plugins" / "material-pipeline.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["public_safe"])
        self.assertEqual(manifest["available_in"], ["private", "public_starter", "personal_vault"])
        self.assertEqual(
            [item["id"] for item in manifest["contributions"]["candidate_types"]],
            ["material_intake", "upgrade", "scout"],
        )
        for scope in ["private", "public_starter", "personal_vault"]:
            registry = load_plugin_registry(ROOT, runtime_scope=scope, language="zh-CN")
            material_candidates = [
                item for item in registry["contributions"]["candidate_types"]
                if item["plugin_id"] == "material_pipeline"
            ]
            self.assertEqual([item["id"] for item in material_candidates], ["material_intake", "upgrade", "scout"])
            self.assertTrue(all(item["plugin_version"] == "1.1.0" for item in material_candidates))
            onboarding_slots = [
                item for item in registry["contributions"]["ui_slots"]
                if item["plugin_id"] == "material_pipeline" and item["id"] == "material_pipeline_onboarding"
            ]
            self.assertEqual(len(onboarding_slots), 1)

    def test_disabled_native_slot_removes_tasks_actions_projections_and_ui(self) -> None:
        manifest = self.manifest(enabled=False)
        manifest["contributions"]["projections"] = [{"id": "fixture_projection", "source": "health"}]
        manifest["contributions"]["ui_slots"] = [{
            "id": "fixture_slot",
            "slot": "utility",
            "adapter": "fixture_adapter",
            "order": 10,
            "projection_ids": ["fixture_projection"],
            "action_ids": ["fixture_action"],
            "locales": {
                "en": {"title": "Fixture", "hint": "Fixture hint"},
                "zh-CN": {"title": "测试", "hint": "测试说明"},
            },
        }]
        with self.fixture_root([manifest]) as directory:
            registry = load_plugin_registry(Path(directory), runtime_scope="private", language="en")
        self.assertEqual(registry["tasks"], [])
        self.assertTrue(all(not items for items in registry["contributions"].values()))

    def test_projection_envelope_and_slot_coordinate_are_normalized(self) -> None:
        manifest = self.manifest()
        manifest["contributions"]["projections"] = [{
            "id": "fixture_projection",
            "source": "health",
            "schema_id": "researchos-projection-envelope-v1",
            "version": "1",
            "sensitivity": "internal",
            "freshness": "snapshot",
            "export_fields": ["validation.ok"],
        }]
        manifest["contributions"]["ui_slots"] = [{
            "id": "fixture_slot",
            "slot": "utility",
            "surface": "overlay",
            "region": "utility",
            "adapter": "fixture_adapter",
            "order": 10,
            "projection_ids": ["fixture_projection"],
            "action_ids": ["fixture_action"],
            "locales": {
                "en": {"title": "Fixture", "hint": "Fixture hint"},
                "zh-CN": {"title": "测试", "hint": "测试说明"},
            },
        }]
        with self.fixture_root([manifest]) as directory:
            registry = load_plugin_registry(Path(directory), runtime_scope="private", language="en")
        projection = registry["contributions"]["projections"][0]
        slot = registry["contributions"]["ui_slots"][0]
        action = registry["contributions"]["actions"][0]
        self.assertEqual(projection["export_fields"], ["validation.ok"])
        self.assertEqual((slot["surface"], slot["region"]), ("overlay", "utility"))
        self.assertEqual(action["surface"], "overlay", "legacy utility action input must emit only the canonical surface")

    def test_projection_export_and_cross_surface_action_fail_closed(self) -> None:
        manifest = self.manifest()
        manifest["contributions"]["projections"] = [{
            "id": "fixture_projection", "source": "health", "export_fields": ["$", "validation"],
        }]
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "export_fields"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")
        manifest = self.manifest()
        manifest["contributions"]["actions"][0]["surface"] = "start"
        manifest["contributions"]["ui_slots"] = [{
            "id": "fixture_slot", "slot": "utility", "surface": "overlay", "region": "utility",
            "adapter": "fixture_adapter", "order": 10, "projection_ids": [], "action_ids": ["fixture_action"],
            "locales": {"en": {"title": "Fixture", "hint": "Fixture hint"}, "zh-CN": {"title": "测试", "hint": "测试说明"}},
        }]
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "another surface"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_public_summary_does_not_disclose_manifest_source_or_permissions(self) -> None:
        registry = load_plugin_registry(ROOT, runtime_scope="public_starter", language="en")
        rendered = json.dumps(registry["loaded"], ensure_ascii=False)
        self.assertNotIn("config/", rendered)
        self.assertNotIn(str(ROOT), rendered)
        self.assertNotIn("read_paths", rendered)
        self.assertNotIn("permissions", rendered)

    def test_native_task_contribution_uses_existing_task_contract(self) -> None:
        manifest = self.manifest(plugin_id="method_pack")
        descriptor = json.loads(TASK_EXAMPLE.read_text(encoding="utf-8"))
        descriptor["id"] = "method_pack_task"
        descriptor["task"]["aliases"] = ["method_pack_alias"]
        manifest["permissions"]["read_paths"] = []
        manifest["contributions"]["actions"] = []
        manifest["contributions"]["tasks"] = [{"id": "method_pack_task", "task": descriptor["task"]}]
        with self.fixture_root([manifest]) as directory:
            root = Path(directory)
            read_groups = [descriptor["task"]["read"]]
            read_groups.extend(descriptor["task"].get("read_locales", {}).values())
            for relative in {path for tiers in read_groups for tier in tiers.values() for path in tier}:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("---\nsensitivity: public\n---\nfixture\n", encoding="utf-8")
            registry = load_plugin_registry(root, runtime_scope="private", language="zh-CN")
        self.assertEqual([task["id"] for task in registry["tasks"]], ["method_pack_task"])
        self.assertEqual(registry["tasks"][0]["plugin_id"], "method_pack")
        self.assertEqual(registry["tasks"][0]["plugin_tier"], "bundled_capability")

    def test_product_tiers_distinguish_dashboard_foundation_from_optional_extensions(self) -> None:
        runtime_scope = "public_starter" if (ROOT / "README.zh.md").exists() else "private"
        registry = load_plugin_registry(ROOT, runtime_scope=runtime_scope, language="zh-CN")
        tiers = {item["id"]: item["product_tier"] for item in registry["loaded"]}
        self.assertEqual(tiers["research_portfolio"], "foundation_projection")
        self.assertEqual(tiers["research_assets"], "foundation_projection")
        self.assertEqual(tiers["material_pipeline"], "foundation_projection")
        self.assertEqual(tiers["system_stewardship"], "bundled_capability")
        for private_only_id in ("audit_stewardship", "reflection_stewardship", "alignment_stewardship", "research_context", "research_expression"):
            if private_only_id in tiers:
                self.assertEqual(tiers[private_only_id], "bundled_capability")
        descriptor = json.loads(TASK_EXAMPLE.read_text(encoding="utf-8"))
        descriptor.pop("governance", None)
        descriptor.pop("documentation", None)
        descriptor["enabled"] = True
        with self.fixture_root([]) as directory:
            root = Path(directory)
            extension_dir = root / "config" / "extensions"
            extension_dir.mkdir(parents=True, exist_ok=True)
            (extension_dir / "method-comparison.json").write_text(json.dumps(descriptor, ensure_ascii=False), encoding="utf-8")
            read_groups = [descriptor["task"]["read"], *descriptor["task"].get("read_locales", {}).values()]
            for relative in {path for tiers_by_depth in read_groups for paths in tiers_by_depth.values() for path in paths}:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("---\nsensitivity: public\n---\nfixture\n", encoding="utf-8")
            optional_registry = load_plugin_registry(root, runtime_scope="private", language="zh-CN")
        self.assertEqual(optional_registry["loaded"][0]["product_tier"], "optional_extension")
        self.assertEqual(optional_registry["tasks"][0]["primary_surface"], "conversation")

    def test_unknown_contribution_type_cannot_smuggle_frontend_code(self) -> None:
        manifest = self.manifest()
        manifest["contributions"]["frontend_js"] = [{"id": "unsafe_bundle"}]
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "unsupported types"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_research_portfolio_declares_bounded_gateway_actions_and_work_items(self) -> None:
        manifest = json.loads((ROOT / "config" / "plugins" / "research-portfolio.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "2.0.0")
        self.assertFalse(any(item.get("surface") == "next" for item in manifest["contributions"]["ui_slots"]))
        self.assertNotIn("copy_portfolio_task_packet", {item["id"] for item in manifest["contributions"]["actions"]})
        inline_actions = [
            item for item in manifest["contributions"]["actions"]
            if item.get("confirmation_mode") == "inline"
        ]
        self.assertEqual(
            [item["id"] for item in inline_actions],
            ["update_portfolio_attention", "complete_portfolio_step"],
        )
        self.assertTrue(all(item["execution"] == "platform_registered" for item in inline_actions))
        self.assertTrue(all(set(item) >= {
            "confirmation_mode", "risk", "write_scope", "reversible", "public_behavior"
        } for item in inline_actions))
        project_action = next(item for item in manifest["contributions"]["actions"] if item["id"] == "complete_portfolio_project")
        self.assertEqual(project_action["confirmation_mode"], "review")
        self.assertEqual(project_action["risk"], "high")
        self.assertTrue(project_action["reversible"])
        registry = load_plugin_registry(ROOT, runtime_scope="private", language="en")
        providers = [
            item for item in registry["contributions"]["work_item_providers"]
            if item["plugin_id"] == "research_portfolio"
        ]
        self.assertEqual([item["id"] for item in providers], ["research_portfolio_items"])
        self.assertEqual(providers[0]["projection_id"], "research_portfolio")

    def test_partial_inline_action_contract_fails_closed(self) -> None:
        manifest = self.manifest()
        manifest["contributions"]["actions"][0].update({
            "confirmation_mode": "inline",
            "risk": "low",
        })
        with self.fixture_root([manifest]) as directory:
            with self.assertRaisesRegex(PluginManifestError, "v1.2 contract is incomplete"):
                load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_inline_action_contract_rejects_unbounded_irreversible_or_public_writes(self) -> None:
        invalid_overrides = (
            ({"write_scope": "durable_content"}, "bounded state scope"),
            ({"write_scope": "none"}, "bounded state scope"),
            ({"reversible": False}, "must be reversible"),
            ({"public_behavior": "enabled"}, "cannot be enabled in public runtime"),
        )
        for override, message in invalid_overrides:
            with self.subTest(override=override):
                manifest = self.manifest()
                manifest["contributions"]["actions"][0].update({
                    "execution": "platform_registered",
                    "confirmation_mode": "inline",
                    "risk": "low",
                    "write_scope": "attention_state",
                    "reversible": True,
                    "public_behavior": "demo_only",
                    **override,
                })
                with self.fixture_root([manifest]) as directory:
                    with self.assertRaisesRegex(PluginManifestError, message):
                        load_plugin_registry(Path(directory), runtime_scope="private", language="en")

    def test_every_active_owner_has_one_complete_logical_owner(self) -> None:
        self.assertEqual(ownership_overlay_failures(ROOT), [])
        summary = ownership_registry_summary(ROOT)
        self.assertEqual(
            summary["frontend"]["active_owner_count"],
            sum(summary["frontend"]["change_radius_by_owner"].values()),
        )
        self.assertEqual(
            summary["style"]["active_owner_count"],
            sum(summary["style"]["change_radius_by_owner"].values()),
        )
        self.assertGreaterEqual(summary["data"]["active_owner_count"], 8)
        self.assertIn("system_stewardship", summary["frontend"]["change_radius_by_owner"])
        self.assertEqual(summary["frontend"]["change_radius_by_owner"]["material_pipeline"], 5)
        self.assertEqual(summary["style"]["change_radius_by_owner"]["material_pipeline"], 1)
        self.assertLessEqual(summary["frontend"]["change_radius_by_owner"]["research_assets"], 10)
        self.assertEqual(summary["frontend"]["change_radius_by_owner"]["research_portfolio"], 5)
        self.assertIn("stable_kernel", summary["data"]["change_radius_by_owner"])


if __name__ == "__main__":
    unittest.main()
