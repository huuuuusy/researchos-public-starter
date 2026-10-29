#!/usr/bin/env python3
"""Validate the public zero-dashboard profile without weakening safety gates."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PUBLIC_ROUTES = {
    "first_run_onboarding",
    "material_intake",
    "card_upgrade",
    "codex_handoff",
    "external_demand_response",
    "relationship_opportunity",
    "maintenance_check",
    "system_evolution_review",
    "material_understanding",
    "idea_diagnosis",
    "new_project_intake",
    "safe_export",
    "collaborative_alignment",
    "research_audit",
    "system_reflection",
    "research_self_model",
    "paper_writing",
    "proposal",
    "presentation",
    "figure_design",
}


@dataclass(frozen=True)
class Step:
    name: str
    args: tuple[str, ...]


STEPS = (
    Step("runtime_config", ("scripts/validate_runtime_config.py",)),
    Step("task_extensions", ("scripts/validate_task_extensions.py",)),
    Step("semantic_receipts", ("scripts/validate_semantic_receipts.py",)),
    Step("public_safety", ("scripts/validate_public_safety.py",)),
    Step("links", ("scripts/check_all_links.py",)),
    Step(
        "focused_tests",
        (
            "-m",
            "unittest",
            "evals.test_receipt_cli",
            "evals.test_zero_dashboard_receipt_flow",
            "evals.test_task_extensions",
            "evals.test_plugin_lifecycle",
            "evals.test_runtime_profile_cli",
            "evals.test_public_codex_runner_boundary",
            "evals.test_public_capability_alignment",
            "evals.test_admission_state",
            "evals.test_rule_evolution",
            "evals.test_runtime_profile",
        ),
    ),
)


def run_python(args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-dashboard-absent",
        action="store_true",
        help="Fail unless the dashboard directory is physically absent.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable receipt.")
    args = parser.parse_args()

    failures: list[str] = []
    receipts: list[dict[str, object]] = []

    if args.require_dashboard_absent and (ROOT / "dashboard").exists():
        failures.append("dashboard directory is present")

    startup = run_python(("scripts/start_researchos.py", "--mode", "cli"))
    startup_output = combined_output(startup)
    startup_passed = startup.returncode == 0 and all(
        token in startup_output for token in ("dashboard_required: false", "runtime: copy_only")
    )
    receipts.append(
        {
            "step": "cli_profile",
            "passed": startup_passed,
            "returncode": startup.returncode,
        }
    )
    if not startup_passed:
        failures.append(f"cli_profile: {startup_output or 'missing required profile markers'}")

    routes = run_python(("scripts/plan_context.py", "--list", "--lang", "en"))
    route_output = combined_output(routes)
    route_ids = {
        line.split(":", 1)[0].strip()
        for line in route_output.splitlines()
        if ":" in line and line.split(":", 1)[0].strip()
    }
    routes_passed = routes.returncode == 0 and route_ids == EXPECTED_PUBLIC_ROUTES
    receipts.append(
        {
            "step": "public_route_catalog",
            "passed": routes_passed,
            "returncode": routes.returncode,
            "route_count": len(route_ids),
        }
    )
    if not routes_passed:
        failures.append(
            "public_route_catalog: expected "
            f"{sorted(EXPECTED_PUBLIC_ROUTES)}, observed {sorted(route_ids)}"
        )

    for step in STEPS:
        result = run_python(step.args)
        output = combined_output(result)
        passed = result.returncode == 0
        receipts.append(
            {
                "step": step.name,
                "passed": passed,
                "returncode": result.returncode,
            }
        )
        if not passed:
            failures.append(f"{step.name}: {output or 'command failed without output'}")

    report = {
        "schema": "researchos_public_headless_validation_v1",
        "root": str(ROOT),
        "dashboard_present": (ROOT / "dashboard").exists(),
        "require_dashboard_absent": args.require_dashboard_absent,
        "passed": not failures,
        "failures": failures,
        "steps": receipts,
    }
    if args.json:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    elif failures:
        print("Public zero-dashboard validation failed:")
        for failure in failures:
            print(f"- {failure}")
    else:
        print(
            "OK: public zero-dashboard profile validated "
            f"({len(receipts)} checks; dashboard_present={report['dashboard_present']})"
        )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
