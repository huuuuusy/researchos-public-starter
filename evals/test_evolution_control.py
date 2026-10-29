from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_data.maintenance_pipeline import maintenance_plan, normalize_changed_paths
from researchos_server.auto_update_runner import AutoUpdateRunner, AutoUpdateStep, WriteSnapshot
from researchos_server.evolution_planner import EvolutionPlanner


class FakeCommandRunner:
    def __init__(self) -> None:
        self.labels: list[str] = []

    def run_step(self, label: str, args: list[str], timeout: int = 90, optional: bool = False) -> dict[str, object]:
        self.labels.append(label)
        return {"label": label, "ok": True, "required_ok": True, "optional": optional, "output": "ok"}


class FailingWriteRunner:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.labels: list[str] = []

    def run_step(self, label: str, args: list[str], timeout: int = 90, optional: bool = False) -> dict[str, object]:
        self.labels.append(label)
        output = self.root / "generated" / "result.txt"
        if label == "write":
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("partial\n", encoding="utf-8")
            ok = True
        else:
            ok = False
        return {"label": label, "ok": ok, "required_ok": ok, "optional": optional, "output": label}


class SymlinkSwapRunner:
    def __init__(self, root: Path, outside: Path) -> None:
        self.root = root
        self.outside = outside

    def run_step(self, label: str, args: list[str], timeout: int = 90, optional: bool = False) -> dict[str, object]:
        owner = self.root / "generated"
        if label == "write":
            shutil.rmtree(owner)
            owner.symlink_to(self.outside, target_is_directory=True)
            ok = True
        else:
            ok = False
        return {"label": label, "ok": ok, "required_ok": ok, "optional": optional, "output": label}


class EvolutionControlTest(unittest.TestCase):
    def test_live_evolution_validator_rejects_cache_queries_and_missing_assets(self) -> None:
        import validate_evolution_control as validator
        self.assertEqual([], validator.failures())
        with tempfile.TemporaryDirectory() as directory:
            index = Path(directory) / "index.html"
            source = validator.INDEX_PATH.read_text()
            index.write_text(source.replace('src="src/plugins/unified-research-desk.js"', 'src="src/plugins/unified-research-desk.js?v=stale"'))
            with patch.object(validator, "INDEX_PATH", index):
                self.assertIn("public dashboard assets must not carry hand-maintained ?v= cache queries", validator.failures())
            index.write_text(source.replace('<script src="src/plugins/unified-research-desk.js"></script>', ""))
            with patch.object(validator, "INDEX_PATH", index):
                self.assertIn("public evolution-specific UI assets must stay loaded by index.html", validator.failures())

    def test_change_token_detects_metadata_replacement_with_same_size_and_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "draft.md"
            path.write_text("first\n", encoding="utf-8")
            original = path.stat()
            planner = EvolutionPlanner(root, runtime_mode="personal_vault")
            before = planner.change_token("head", ("draft.md",))
            time.sleep(0.002)
            path.write_text("other\n", encoding="utf-8")
            os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
            after = planner.change_token("head", ("draft.md",))
            self.assertEqual(original.st_size, path.stat().st_size)
            self.assertEqual(original.st_mtime_ns, path.stat().st_mtime_ns)
            self.assertNotEqual(before, after)

    def test_paths_fail_closed_and_public_plan_is_deterministic(self) -> None:
        self.assertEqual(normalize_changed_paths(["./docs/a.md", "../escape.md", "/absolute.md"]), ("docs/a.md",))
        first = maintenance_plan(["docs/a.md"], runtime_mode="public_starter")
        second = maintenance_plan(["docs/a.md"], runtime_mode="public_starter")
        self.assertEqual(first["plan_id"], second["plan_id"])
        self.assertIn("build_public_starter_data", first["selected_step_ids"])
        self.assertNotIn("build_personal_vault_data", first["selected_step_ids"])
        self.assertTrue(first["requires_confirmation"])
        self.assertEqual(first["risk_tier"], "E1")

    def test_runtime_mode_selects_only_its_projection(self) -> None:
        public = maintenance_plan(["docs/a.md"], runtime_mode="public_starter")
        personal = maintenance_plan(["docs/a.md"], runtime_mode="personal_vault")
        self.assertIn("build_public_starter_data", public["selected_step_ids"])
        self.assertNotIn("build_personal_vault_data", public["selected_step_ids"])
        self.assertIn("build_personal_vault_data", personal["selected_step_ids"])
        self.assertNotIn("build_public_starter_data", personal["selected_step_ids"])

    def test_code_change_selects_validation(self) -> None:
        plan = maintenance_plan(["dashboard/app.js"], runtime_mode="public_starter")
        self.assertIn("validate_agent_architecture", plan["selected_step_ids"])
        self.assertIn("validate_public_safety", plan["selected_step_ids"])
        self.assertEqual(plan["risk_tier"], "E0")

    def test_runner_executes_only_requested_fixed_steps(self) -> None:
        command_runner = FakeCommandRunner()
        runner = AutoUpdateRunner(
            command_runner=command_runner,
            steps=(
                AutoUpdateStep("first", ("python3", "first.py"), id="first"),
                AutoUpdateStep("second", ("python3", "second.py"), id="second"),
            ),
        )
        result = runner.run(["second"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["executed_step_ids"], ["second"])
        self.assertEqual(command_runner.labels, ["second"])
        rejected = runner.run(["unknown"])
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["executed_step_ids"], [])

    def test_checkpoint_requires_success_and_exact_plan_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checkpoint_path = root / "06_active_context/work_state/evolution/evolution-checkpoint.json"
            planner = EvolutionPlanner(root, runtime_mode="personal_vault", checkpoint_path=checkpoint_path)
            plan = planner.plan(["dashboard/app.js"])
            self.assertFalse(planner.confirmed(plan, "wrong"))
            self.assertTrue(planner.confirmed(plan, plan["plan_id"]))
            with self.assertRaises(ValueError):
                planner.mark_applied(plan, {"ok": False})
            checkpoint = planner.mark_applied(plan, {"ok": True, "executed_step_ids": plan["auto_eligible_step_ids"]})
            self.assertEqual(checkpoint["plan_id"], plan["plan_id"])
            self.assertEqual(checkpoint["state"], "complete")
            self.assertEqual(checkpoint["change_token"], planner.detect()["change_token"])
            self.assertEqual(json.loads(checkpoint_path.read_text(encoding="utf-8"))["schema_id"], "researchos-evolution-checkpoint-v1")

    def test_failed_refresh_retains_changes_and_recovery_material(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "generated" / "result.txt"
            output.parent.mkdir(parents=True)
            output.write_text("stable\n", encoding="utf-8")
            command_runner = FailingWriteRunner(root)
            runner = AutoUpdateRunner(
                command_runner=command_runner,
                steps=(
                    AutoUpdateStep("write", ("python3", "write.py"), id="write", execution_policy="safe_refresh", writes=("generated/result.txt",)),
                    AutoUpdateStep("validate", ("python3", "validate.py"), id="validate"),
                ),
            )
            result = runner.run(["write", "validate"])
            self.assertFalse(result["ok"])
            self.assertTrue(result["rollback"]["attempted"])
            self.assertFalse(result["rollback"]["ok"])
            self.assertEqual(output.read_text(encoding="utf-8"), "partial\n")
            recovery = Path(result["rollback"]["recovery_directory"])
            self.addCleanup(shutil.rmtree, recovery)
            self.assertEqual((recovery / "0").read_text(), "stable\n")
            self.assertEqual(json.loads((recovery / "recovery-manifest.json").read_text())[0]["target"], "generated/result.txt")


    def test_refresh_rejects_write_target_escape_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            command_runner = FailingWriteRunner(Path(temp_dir))
            runner = AutoUpdateRunner(
                command_runner=command_runner,
                steps=(AutoUpdateStep("write", ("python3", "write.py"), id="write", execution_policy="safe_refresh", writes=("../escape.txt",)),),
            )
            result = runner.run(["write"])
            self.assertFalse(result["ok"])
            self.assertEqual(command_runner.labels, [])
            self.assertIn("unsafe maintenance write target", result["message"])

    def test_rollback_preserves_changed_parent_symlink_and_external_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as outside_dir:
            root = Path(temp_dir)
            outside = Path(outside_dir)
            output = root / "generated" / "result.txt"
            output.parent.mkdir(parents=True)
            output.write_text("stable\n", encoding="utf-8")
            external = outside / "result.txt"
            external.write_text("external\n", encoding="utf-8")
            runner = AutoUpdateRunner(
                command_runner=SymlinkSwapRunner(root, outside),
                steps=(
                    AutoUpdateStep("write", ("python3", "write.py"), id="write", execution_policy="safe_refresh", writes=("generated/result.txt",)),
                    AutoUpdateStep("validate", ("python3", "validate.py"), id="validate"),
                ),
            )
            result = runner.run(["write", "validate"])
            self.assertFalse(result["ok"])
            self.assertFalse(result["rollback"]["ok"])
            self.addCleanup(shutil.rmtree, result["rollback"]["recovery_directory"])
            self.assertTrue(output.parent.is_symlink())
            self.assertEqual(external.read_text(encoding="utf-8"), "external\n")


    def test_snapshot_never_reverts_independent_directory_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "generated").mkdir()
            old = root / "generated/old.txt"
            old.write_text("initial")
            snapshot = WriteSnapshot.capture(root, (Path("generated"),))
            old.write_text("independent edit")
            new = root / "generated/new.txt"
            new.write_text("independent creation")
            result = snapshot.restore()
            snapshot.close()
            self.addCleanup(shutil.rmtree, result["recovery_directory"])
            self.assertFalse(result["ok"])
            self.assertEqual(old.read_text(), "independent edit")
            self.assertEqual(new.read_text(), "independent creation")
            self.assertEqual((Path(result["recovery_directory"]) / "0/old.txt").read_text(), "initial")


    def test_unchanged_snapshot_requires_no_mutation_and_cleans_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "old.txt").write_text("unchanged")
            snapshot = WriteSnapshot.capture(root, (Path("old.txt"), Path("missing.txt")))
            result = snapshot.restore()
            self.assertTrue(result["ok"])
            self.assertEqual(result["restored"], [])
            self.assertEqual(result["unchanged"], ["old.txt", "missing.txt"])
            snapshot.close()
            self.assertFalse(snapshot.temporary.exists())


    def test_pending_manual_merge_keeps_candidate_visible(self) -> None:
        current = maintenance_plan([], runtime_mode="personal_vault")
        pending = {
            "plan_id": "older-plan",
            "manual_step_ids": ["manual_review"],
            "manual_writes": ["dashboard/data/manual.json"],
            "validates": ["manual review"],
            "steps": [{"id": "manual_review", "label": "Manual review", "writes": ["dashboard/data/manual.json"], "validates": ["manual review"]}],
            "changed_paths": ["docs/older.md"],
        }
        merged = EvolutionPlanner.merge_pending_manual(current, pending)
        self.assertEqual(merged["status"], "candidate")
        self.assertEqual(merged["manual_step_ids"], ["manual_review"])
        self.assertEqual(merged["pending_source_plan_id"], "older-plan")
        self.assertEqual(merged["manual_writes"], [])
        self.assertEqual(merged["risk_tier"], "E4")

    def test_retired_pending_step_fails_closed_without_stale_writes(self) -> None:
        refreshed = EvolutionPlanner.refresh_pending_manual(
            {
                "plan_id": "old-plan",
                "manual_step_ids": ["retired_manual_step"],
                "manual_writes": ["retired/location/"],
                "steps": [{"id": "retired_manual_step", "writes": ["retired/location/"]}],
            }
        )
        self.assertEqual(refreshed["risk_tier"], "E4")
        self.assertEqual(refreshed["manual_writes"], [])
        self.assertEqual(refreshed["unavailable_manual_step_ids"], ["retired_manual_step"])


    def test_missing_git_executable_degrades_to_explicit_only_without_crashing(self) -> None:
        # A Download-ZIP checkout has no git: the dashboard imports plan() at startup and must not crash.
        with tempfile.TemporaryDirectory() as tmp:
            planner = EvolutionPlanner(Path(tmp), runtime_mode="public_starter")
            with patch("researchos_server.evolution_planner.subprocess.run", side_effect=FileNotFoundError("git")):
                detection = planner.detect()
                plan = planner.plan()
        self.assertFalse(detection["git_available"])
        self.assertEqual(detection["detector"], "explicit_only")
        self.assertEqual(detection["head_sha"], "")
        self.assertIsInstance(plan, dict)


if __name__ == "__main__":
    unittest.main()
