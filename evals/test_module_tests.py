"""Every kernel, adapter and server module has a test of its own name or a listed exemption.

The owner -> test index in evals/README.md is generated from the same table and must match it:

    python3 evals/test_module_tests.py --write-index

rewrites the block between the index markers; running the file without arguments runs the tests.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
README = EVALS / "README.md"
PACKAGES = ("researchos_kernel", "researchos_adapters", "researchos_server")
BEGIN, END = "<!-- module-test-index:begin -->", "<!-- module-test-index:end -->"

# Modules without a test_<name>.py, and where they are tested instead (or why they are not).
# The table covers both editions; an entry for a module this edition does not ship is ignored.
EXEMPT = {
    "researchos_kernel/atomic_files.py": "covered by test_runtime_state_atomicity.py and test_filesystem_staging.py",
    "researchos_kernel/boundary.py": "covered by test_ros_kernel.py (the kernel's end-to-end suite) and test_scope_axis.py",
    "researchos_kernel/candidate_envelope.py": "covered by test_admission_state.py",
    "researchos_kernel/judgments.py": "covered by test_ros_kernel.py",
    "researchos_kernel/ledger.py": "covered by test_requirement_ledger.py and test_ros_kernel.py",
    "researchos_kernel/messages.py": "covered by test_ros_kernel.py",
    "researchos_kernel/rules.py": "covered by test_ros_kernel.py, including a JSON-only second rule of an existing kind",
    "researchos_kernel/scope.py": "covered by test_scope_axis.py and test_ros_kernel.py",
    "researchos_kernel/triage.py": "covered by test_ros_kernel.py (`ros today` triage)",
    "researchos_adapters/command_runner.py": "covered by test_command_runner_security.py",
    "researchos_adapters/context_pack.py": "covered by test_ros_kernel.py (`ros context` and `ros run`)",
    "researchos_adapters/dispatch.py": "covered by test_provider_registry.py and test_ros_kernel.py (`ros run`)",
    "researchos_adapters/markdown_repo.py": "covered by test_ros_kernel.py and test_scope_axis.py",
    "researchos_adapters/provider_config.py": "covered by test_public_codex_runner_boundary.py and test_provider_registry.py",
    "researchos_adapters/runner_authority.py": "covered by test_policy_gateway.py",
    "researchos_adapters/runner_permissions.py": "covered by test_codex_runner_usage.py and test_ros_kernel.py",
    "researchos_adapters/work_session_result.py": "no direct test; the private edition exercises it in test_composition_result_recovery.py",
    "researchos_adapters/writeback.py": "covered by test_ros_kernel.py (`ros admit` and `ros close`)",
    "researchos_server/attention_schedule_store.py": "covered by test_attention_schedule.py",
    "researchos_server/auto_update_runner.py": "covered by test_evolution_control.py and test_maintenance_composition.py",
    "researchos_server/card_group_store.py": "no direct test; a Dashboard server store",
    "researchos_server/codex_runner.py": "covered by test_codex_runner_usage.py",
    "researchos_server/dashboard_config.py": "no direct test; port and content-security-policy helpers of the Dashboard server",
    "researchos_server/evolution_planner.py": "covered by test_evolution_control.py",
    "researchos_server/inbox_cleanup_store.py": "frozen Inbox store",
    "researchos_server/inbox_store.py": "frozen Inbox store",
    "researchos_server/maintenance_facade.py": "no direct test; public evolution view checked by validate_evolution_control.py",
    "researchos_server/material_pipeline_store.py": "no direct test; a Dashboard server store",
    "researchos_server/research_scout_runner.py": "frozen Research Scout",
    "researchos_server/review_inbox_store.py": "frozen Inbox store; atomic writes in test_runtime_state_atomicity.py",
    "researchos_server/runner_prompt_policy.py": "no direct test; read by codex_runner.py and covered only through test_codex_runner_usage.py",
    "researchos_server/runtime_retention.py": "no direct test; log retention behind the Dashboard runner",
    "researchos_server/source_tree_store.py": "covered by test_local_file_bridge.py and test_runtime_read_boundary.py",
}


def owner_modules(root: Path = ROOT) -> list[str]:
    return sorted(
        f"{package}/{path.name}"
        for package in PACKAGES
        for path in (root / "scripts" / package).glob("*.py")
        if path.name != "__init__.py"
    )


def own_test(module: str, root: Path = ROOT) -> str:
    name = f"test_{Path(module).stem}.py"
    return name if (root / "evals" / name).is_file() else ""


def render_index(root: Path = ROOT) -> str:
    rows = ["| Module | Test |", "| --- | --- |"]
    for module in owner_modules(root):
        test = own_test(module, root)
        rows.append(f"| `scripts/{module}` | {f'`evals/{test}`' if test else EXEMPT.get(module, '**missing**')} |")
    return "\n".join([BEGIN, *rows, END])


def write_index(root: Path = ROOT) -> None:
    text = README.read_text(encoding="utf-8")
    start, end = text.index(BEGIN), text.index(END) + len(END)
    README.write_text(text[:start] + render_index(root) + text[end:], encoding="utf-8")


class ModuleTestsTest(unittest.TestCase):
    def test_every_owner_module_has_its_own_test_or_a_listed_exemption(self) -> None:
        missing = [module for module in owner_modules() if not own_test(module) and module not in EXEMPT]
        self.assertEqual([], missing, "add evals/test_<name>.py or an EXEMPT entry naming where it is tested")
        stale = [module for module in EXEMPT if (ROOT / "scripts" / module).is_file() and own_test(module)]
        self.assertEqual([], stale, "a module with its own test needs no exemption")

    def test_the_readme_index_is_generated_from_this_table(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn(BEGIN, text)
        start, end = text.index(BEGIN), text.index(END) + len(END)
        self.assertEqual(render_index(), text[start:end], "run: python3 evals/test_module_tests.py --write-index")


if __name__ == "__main__":
    if sys.argv[1:] == ["--write-index"]:
        write_index()
    else:
        unittest.main()
