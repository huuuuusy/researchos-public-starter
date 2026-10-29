from __future__ import annotations

import json
from datetime import date
from unittest import mock
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "build_public_starter_data",
    ROOT / "scripts" / "build_public_starter_data.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class PublicStarterBuilderBoundaryTest(unittest.TestCase):
    def test_private_authority_repo_preserves_main_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "START_HERE.md").write_text("# Start\n", encoding="utf-8")
            (root / "00_identity").mkdir()
            self.assertFalse(MODULE.should_write_public_dashboard(root))

    def test_standalone_public_repo_writes_public_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(MODULE.should_write_public_dashboard(Path(directory)))

    def test_public_projection_is_copy_only(self) -> None:
        data, failures = MODULE.build_public_starter_data()
        self.assertEqual([], failures)
        projection = MODULE.build_dashboard_projection(data)
        provider = projection["config"]["provider"]
        self.assertEqual("copy_only", provider["provider_mode"])
        self.assertEqual("none", provider["execution_scope"])
        self.assertFalse(provider["execution_probe_required"])
        self.assertFalse(provider["allow_local_codex"])
        self.assertFalse(provider["allow_real_api"])
        self.assertEqual(
            {"handoff_admit_candidate": False, "runtime_profile_selector": False},
            projection["config"]["surface_candidates"],
        )

    def test_personal_projection_preserves_controlled_local_execution(self) -> None:
        data, failures = MODULE.build_personal_vault_data()
        self.assertEqual([], failures)
        projection = MODULE.build_personal_dashboard_projection(data)
        provider = projection["config"]["provider"]
        self.assertEqual("local_codex", provider["provider_mode"])
        self.assertEqual("workspace_write", provider["execution_scope"])
        self.assertTrue(provider["execution_probe_required"])
        self.assertTrue(provider["allow_local_codex"])
        self.assertFalse(provider["allow_real_api"])
        self.assertFalse(projection["config"]["surface_candidates"]["runtime_profile_selector"])

    def test_freshness_rejects_stale_task_and_policy_payloads(self) -> None:
        data, failures = MODULE.build_public_starter_data()
        self.assertEqual(failures, [])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "08_exports/public_starter/generated-public-starter-data.json"
            output = root / "dashboard/data/researchos-dashboard.json"
            source.parent.mkdir(parents=True)
            output.parent.mkdir(parents=True)
            source.write_text(json.dumps(data))
            projection = MODULE.build_dashboard_projection(data)
            output.write_text(json.dumps(projection))
            self.assertEqual([], MODULE.projection_freshness_failures(data, root))
            projection["tasks"] = []
            output.write_text(json.dumps(projection))
            self.assertTrue(MODULE.projection_freshness_failures(data, root))
            projection = MODULE.build_dashboard_projection(data)
            projection["config"]["provider"]["allow_real_api"] = True
            output.write_text(json.dumps(projection))
            self.assertTrue(MODULE.projection_freshness_failures(data, root))

    def test_unchanged_source_keeps_timestamp_and_check_writes_nothing(self) -> None:
        data, _ = MODULE.build_public_starter_data()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            old = {**data, "generated_at": "2026-08-25"}
            source.write_text(json.dumps(old))
            before = source.read_bytes()
            retained = MODULE.retain_source_timestamp(data, source)
            self.assertEqual(retained["generated_at"], "2026-08-25")
            self.assertEqual(source.read_bytes(), before)
            projection = MODULE.build_dashboard_projection(retained)
            with mock.patch("research_agenda_projection.date") as clock:
                clock.today.return_value = date(2099, 1, 1)
                self.assertEqual(projection, MODULE.build_dashboard_projection(retained))
            changed = {**data, "record_count": -1}
            self.assertEqual(MODULE.retain_source_timestamp(changed, source), changed)

    def test_missing_projection_fails_closed(self) -> None:
        data, _ = MODULE.build_public_starter_data()
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(len(MODULE.projection_freshness_failures(data, Path(directory))), 2)


if __name__ == "__main__":
    unittest.main()
