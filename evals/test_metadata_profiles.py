from __future__ import annotations

import json
import hashlib
import tempfile
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_data.metadata_profiles import (
    AUTHORITY_ROLES,
    EXPORT_POLICIES,
    PROFILE_FIELDS,
    PROFILE_IDS,
    RECORD_STATES,
    SCHEMA_ID,
    SENSITIVITY_LEVELS,
    MetadataProfileError,
    apply_metadata_migration,
    normalize_metadata_record,
    parse_frontmatter_raw,
    prepare_metadata_migration,
    read_metadata_profile,
    rollback_metadata_migration,
)


SCHEMA_PATH = ROOT / "09_templates/data_contracts/researchos-metadata-profile-v1.schema.json"


def valid_record() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_ID,
        "metadata_profile": "template_schema",
        "type": "template",
        "title": "Workflow Template",
        "record_state": "active",
        "authority_role": "none",
        "sensitivity": "internal",
        "export_policy": "internal_only",
        "owner": "09_templates/README.md",
        "created": "2026-08-13",
        "updated": "2026-08-13",
        "relations": ["09_templates/workflow-template.md"],
        "template_for": "workflow",
        "governed_by": ["05_workflows/research_management/researchos-soul-contract.md"],
    }


class MetadataProfileContractTest(unittest.TestCase):
    def test_schema_and_runtime_vocabulary_are_exact(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual(SCHEMA_ID, schema["$id"])
        self.assertEqual(list(PROFILE_IDS), properties["metadata_profile"]["enum"])
        self.assertEqual(list(RECORD_STATES), properties["record_state"]["enum"])
        self.assertEqual(list(AUTHORITY_ROLES), properties["authority_role"]["enum"])
        self.assertEqual(list(SENSITIVITY_LEVELS), properties["sensitivity"]["enum"])
        self.assertEqual(list(EXPORT_POLICIES), properties["export_policy"]["enum"])
        self.assertEqual({key: list(value) for key, value in PROFILE_FIELDS.items()}, schema["x-profile-fields"])
        self.assertIs(False, schema.get("additionalProperties"))

    def test_blank_line_does_not_end_a_block_list_and_inline_lists_stay_text(self) -> None:
        text = "---\nsensitivity: internal\ntags:\n  - a\n\n  - human-sensitive\nexportable_to: [public_template]\n---\n"
        self.assertEqual(
            {"sensitivity": "internal", "tags": ["a", "human-sensitive"], "exportable_to": "[public_template]"},
            parse_frontmatter_raw(text),
        )

    def test_runtime_accepts_the_canonical_template_fixture(self) -> None:
        normalize_metadata_record(
            {
                "schema_version": SCHEMA_ID,
                "metadata_profile": "template_schema",
                "type": "template",
                "title": "Metadata Profile Fixture",
                "record_state": "active",
                "authority_role": "none",
                "sensitivity": "internal",
                "export_policy": "internal_only",
                "owner": "09_templates/data_contracts/README.md",
                "template_for": "metadata contract",
            }
        )

    def test_strict_record_is_deterministic_and_does_not_mutate_input(self) -> None:
        raw = valid_record()
        before = deepcopy(raw)
        first = normalize_metadata_record(raw)
        second = normalize_metadata_record(first)
        self.assertEqual(first, second)
        self.assertEqual(before, raw)
        self.assertEqual("template_schema", first["metadata_profile"])

    def test_partial_v1_unknown_fields_and_mixed_axes_fail_closed(self) -> None:
        cases = [
            {**valid_record(), "schema_version": "research-os-v0.2"},
            {**valid_record(), "metadata_profile": "all_documents"},
            {**valid_record(), "confirmed": True},
            {**valid_record(), "authority_role": "validated"},
            {key: value for key, value in valid_record().items() if key != "export_policy"},
        ]
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(MetadataProfileError):
                    normalize_metadata_record(case)

    def test_profile_specific_fields_cannot_leak_between_profiles(self) -> None:
        with self.assertRaisesRegex(MetadataProfileError, "unknown_metadata_field"):
            normalize_metadata_record({**valid_record(), "decision_state": "accepted"})

    def test_admission_is_referenced_not_reencoded_as_document_lifecycle(self) -> None:
        decision = {
            **valid_record(),
            "metadata_profile": "decision_cognition",
            "type": "decision",
            "record_state": "draft",
            "admission_ref": "06_active_context/work_state/receipts/decision-1.json",
            "source_episodes": ["episode-1"],
        }
        decision.pop("template_for")
        decision.pop("governed_by")
        normalized = normalize_metadata_record(decision)
        self.assertEqual("draft", normalized["record_state"])
        self.assertEqual("none", normalized["authority_role"])
        self.assertEqual(decision["admission_ref"], normalized["admission_ref"])
        for forbidden in ("decision_state", "mutation_state", "validation_state", "confirmed"):
            with self.assertRaises(MetadataProfileError):
                normalize_metadata_record({**decision, forbidden: "accepted"})

    def test_legacy_read_is_projection_not_silent_migration(self) -> None:
        raw = {
            "type": "task_run",
            "title": "Current Slice",
            "status": "in_progress",
            "authority_role": "informative",
            "sensitivity": "internal",
            "current_consumer": "Codex",
        }
        before = deepcopy(raw)
        projection = read_metadata_profile(raw)
        self.assertEqual(before, raw)
        self.assertEqual("legacy", projection["source_mode"])
        self.assertEqual("legacy", projection["profile"]["schema_version"])
        self.assertEqual("active_context_task_run", projection["profile"]["metadata_profile"])
        self.assertEqual("active", projection["profile"]["record_state"])
        self.assertEqual("informative", projection["profile"]["authority_role"])
        self.assertEqual(["current_consumer", "sensitivity", "status"], projection["legacy_fields"])

    def test_legacy_status_never_becomes_decision_or_validation_state(self) -> None:
        projection = read_metadata_profile({"type": "decision", "title": "Candidate", "status": "confirmed"})
        self.assertEqual("draft", projection["profile"]["record_state"])
        self.assertEqual("none", projection["profile"]["authority_role"])
        self.assertNotIn("decision_state", projection["profile"])
        self.assertEqual(["owner"], projection["missing_required"])

    def test_explicit_profile_hint_is_bounded(self) -> None:
        projection = read_metadata_profile({"type": "custom", "title": "Export", "owner": "test"}, profile_hint="export_public_safe")
        self.assertEqual("export_public_safe", projection["profile"]["metadata_profile"])
        with self.assertRaisesRegex(MetadataProfileError, "unknown_metadata_profile"):
            read_metadata_profile({"type": "custom"}, profile_hint="everything")

    def test_legacy_source_sensitivity_and_export_policy_are_dual_read(self) -> None:
        expected = {
            "public": ("public", "public"),
            "public_safe": ("public", "allowlisted"),
            "internal": ("internal", "internal_only"),
            "local_only": ("internal", "local_only"),
            "not_exportable": ("internal", "no_export"),
            "no-export": ("internal", "no_export"),
            "sensitive": ("sensitive", "no_export"),
            "private": ("private", "no_export"),
        }
        for legacy, boundary in expected.items():
            with self.subTest(legacy=legacy):
                profile = read_metadata_profile({"type": "template", "title": "T", "owner": "O", "sensitivity": legacy})["profile"]
                self.assertEqual(boundary, (profile["sensitivity"], profile["export_policy"]))

    def test_plugin_descriptor_default_never_relabels_source_record(self) -> None:
        profile = read_metadata_profile(
            {"type": "template", "title": "Public fixture", "owner": "O", "sensitivity": "public", "sensitivity_default": "local_only"}
        )["profile"]
        self.assertEqual("public", profile["sensitivity"])
        self.assertEqual("public", profile["export_policy"])

    def test_new_boundary_combinations_fail_closed(self) -> None:
        for sensitivity, export_policy in (("internal", "public"), ("sensitive", "public"), ("private", "allowlisted")):
            with self.subTest(sensitivity=sensitivity, export_policy=export_policy):
                with self.assertRaisesRegex(MetadataProfileError, "invalid_metadata_boundary"):
                    normalize_metadata_record({**valid_record(), "sensitivity": sensitivity, "export_policy": export_policy})

    def test_one_file_migration_is_idempotent_and_body_preserving(self) -> None:
        before = """---
type: template
title: "Capsule"
status: active
created: 2026-01-01
updated: 2026-01-02
tags:
  - template
sensitivity: internal
agent_reading_level: entry
context_budget: quick
capsule_of: []
exportable_to:
  - codex
---

# Capsule

Body stays exact.
"""
        overrides = {"template_for": "context_capsule", "export_policy": "allowlisted"}
        receipt = prepare_metadata_migration(before, profile_hint="template_schema", owner="09_templates/README.md", overrides=overrides)
        self.assertTrue(receipt.changed)
        self.assertEqual(before.split("\n---\n", 1)[1], receipt.after_text.split("\n---\n", 1)[1])
        record = parse_frontmatter_raw(receipt.after_text)
        self.assertEqual("researchos-metadata-profile-v1", record["schema_version"])
        self.assertEqual("active", record["record_state"])
        self.assertEqual("allowlisted", record["export_policy"])
        second = prepare_metadata_migration(receipt.after_text, profile_hint="template_schema", owner="ignored", overrides=overrides)
        self.assertFalse(second.changed)

    def test_exact_base_apply_and_rollback_are_atomic_and_conflict_safe(self) -> None:
        before = "---\ntype: template\ntitle: T\nstatus: active\nsensitivity: internal\n---\n\n# T\n"
        receipt = prepare_metadata_migration(
            before,
            profile_hint="template_schema",
            owner="09_templates/README.md",
            overrides={"template_for": "test", "export_policy": "internal_only"},
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "template.md"
            target.write_text(before, encoding="utf-8")
            self.assertTrue(apply_metadata_migration(target, receipt, root=root))
            self.assertFalse(apply_metadata_migration(target, receipt, root=root))
            self.assertEqual(receipt.after_sha256, hashlib.sha256(target.read_bytes()).hexdigest())
            target.write_text(target.read_text(encoding="utf-8") + "drift", encoding="utf-8")
            with self.assertRaisesRegex(MetadataProfileError, "metadata_rollback_conflict"):
                rollback_metadata_migration(target, receipt, root=root)
            target.write_text(receipt.after_text, encoding="utf-8")
            self.assertTrue(rollback_metadata_migration(target, receipt, root=root))
            self.assertFalse(rollback_metadata_migration(target, receipt, root=root))
            self.assertEqual(before, target.read_text(encoding="utf-8"))

    def test_symlink_and_out_of_root_targets_fail_closed(self) -> None:
        before = "---\ntype: template\ntitle: T\nstatus: active\nsensitivity: internal\n---\n\n# T\n"
        receipt = prepare_metadata_migration(before, profile_hint="template_schema", owner="owner", overrides={"template_for": "test"})
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "root"
            root.mkdir()
            outside = Path(temp) / "outside.md"
            outside.write_text(before, encoding="utf-8")
            link = root / "link.md"
            link.symlink_to(outside)
            for target in (link, outside):
                with self.subTest(target=target):
                    with self.assertRaisesRegex(MetadataProfileError, "unsafe_metadata_target"):
                        apply_metadata_migration(target, receipt, root=root)


if __name__ == "__main__":
    unittest.main()
