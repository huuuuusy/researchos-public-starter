"""Fixed-step composition: no provider, network or canonical writes."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_data.maintenance_pipeline import RESEARCHOS_MAINTENANCE_STEPS, maintenance_plan
from researchos_server.auto_update_runner import AutoUpdateRunner, AutoUpdateStep, default_auto_update_steps
from researchos_adapters.command_runner import CommandRunner
from researchos_server.evolution_planner import EvolutionPlanner


class Commands:
    def __init__(self, failures=(), raises=()):
        self.calls = []
        self.failures = failures
        self.raises = raises

    def run_step(self, label, args, timeout=90, optional=False):
        self.calls.append(label)
        if label in self.raises:
            raise RuntimeError("execution outcome failed")
        ok = label not in self.failures
        return dict(label=label, ok=ok, required_ok=ok, optional=optional, output=label)


def step(name, dependencies=(), optional=False):
    return AutoUpdateStep(name, ("synthetic", name), id=name, depends_on=dependencies, optional=optional)


class MaintenanceCompositionTest(unittest.TestCase):
    def test_failure_blocks_transitive_dependents_but_independent_work_continues(self):
        commands = Commands(failures={"source"})
        runner = AutoUpdateRunner(commands, (
            step("source"), step("left", ("source",)), step("independent"),
            step("right", ("source",)), step("join", ("left", "right")),
        ))
        result = runner.run()
        self.assertFalse(result["ok"])
        self.assertEqual(["source", "independent"], commands.calls)
        self.assertEqual(commands.calls, result["executed_step_ids"])
        self.assertEqual(["left", "right", "join"], result["blocked_step_ids"])
        self.assertEqual(["left", "right"], result["steps"][-1]["blocked_by"])

    def test_successful_chain_and_join_keep_declared_order(self):
        commands = Commands()
        runner = AutoUpdateRunner(commands, (step("a"), step("b", ("a",)), step("c", ("a", "b"))))
        result = runner.run(["c", "b", "a"])
        self.assertTrue(result["ok"])
        self.assertEqual(["a", "b", "c"], commands.calls)
        self.assertEqual([], result["blocked_step_ids"])

    def test_optional_failure_is_not_a_successful_prerequisite(self):
        commands = Commands(failures={"optional"})
        result = AutoUpdateRunner(commands, (step("optional", optional=True), step("required", ("optional",)))).run()
        self.assertFalse(result["ok"])
        self.assertTrue(result["external_partial"])
        self.assertEqual(["optional"], commands.calls)
        self.assertEqual(["required"], result["blocked_step_ids"])

    def test_exception_blocks_dependent_without_retry(self):
        commands = Commands(raises={"a"})
        result = AutoUpdateRunner(commands, (step("a"), step("b", ("a",)))).run()
        self.assertEqual(["a"], commands.calls)
        self.assertEqual("runner_error", result["steps"][0]["returncode"])
        self.assertEqual("dependency_blocked", result["steps"][1]["returncode"])

    def test_direct_subset_does_not_start_omitted_prerequisite(self):
        commands = Commands()
        result = AutoUpdateRunner(commands, (step("existing_source"), step("read", ("existing_source",)))).run(["read"])
        self.assertTrue(result["ok"])
        self.assertEqual(["read"], commands.calls)

    def test_invalid_selected_order_cycles_unknown_dependencies_and_duplicate_ids_run_nothing(self):
        cases = [
            (step("b", ("a",)), step("a")),
            (step("a", ("b",)), step("b", ("a",))),
            (step("a", ("missing",)),),
            (step("a"), step("a")),
        ]
        for steps in cases:
            with self.subTest(steps=steps):
                commands = Commands()
                result = AutoUpdateRunner(commands, steps).run()
                self.assertFalse(result["ok"])
                self.assertEqual([], commands.calls)
                self.assertEqual([], result["executed_step_ids"])

    def test_manifest_dependencies_survive_runner_and_plan_projection(self):
        expected = {s["id"]: tuple(s["depends_on"]) for s in RESEARCHOS_MAINTENANCE_STEPS}
        self.assertEqual(expected, {s.id: s.depends_on for s in default_auto_update_steps()})
        # Public steps have no prerequisites; an omitted projection field means an empty list.
        plan = maintenance_plan(["01_knowledge/papers/example.md"])
        for item in plan["steps"]:
            self.assertEqual(expected[item["id"]], tuple(item.get("depends_on", ())))
        resumed = EvolutionPlanner.refresh_pending_manual(plan)
        for item in resumed["steps"]:
            self.assertEqual(expected[item["id"]], tuple(item.get("depends_on", ())))

    def test_real_local_command_failure_prevents_child_write_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = AutoUpdateRunner(CommandRunner(root), (
                AutoUpdateStep("check", (sys.executable, "-c", "raise SystemExit(7)"), id="check"),
                AutoUpdateStep("child", (sys.executable, "-c", "from pathlib import Path; Path('child.txt').write_text('unexpected')"),
                               id="child", depends_on=("check",), writes=("child.txt",)),
                AutoUpdateStep("independent", (sys.executable, "-c", "print('independent check')"), id="independent"),
            ))
            result = runner.run()
            self.assertFalse((root / "child.txt").exists())
            self.assertEqual(7, result["steps"][0]["returncode"])
            self.assertEqual("dependency_blocked", result["steps"][1]["returncode"])
            self.assertIn("independent check", result["steps"][2]["output"])
            self.assertEqual(["check", "independent"], result["executed_step_ids"])
            with self.assertRaises(ValueError):
                EvolutionPlanner(root).mark_applied({"plan_id": "fixture"}, result)


if __name__ == "__main__":
    unittest.main()
