#!/usr/bin/env python3
"""Validate declarative ResearchOS task extension packs."""

from __future__ import annotations

from pathlib import Path

from plan_context import task_routes
from researchos_data.task_extensions import validate_extension_files
from researchos_kernel.rules import EVALUATORS, delegation_problems, evaluator_for, load_registry, write_class


ROOT = Path(__file__).resolve().parents[1]


def validate_scheduler_rules(root: Path) -> list[str]:
    """v2 descriptors are admitted by the kernel registry, so the gate and the scheduler cannot drift."""
    descriptors, problems = load_registry(root)
    failures = [f"config/extensions/rules/{problem}" for problem in problems]
    for rule_id, descriptor in sorted(descriptors.items()):
        if descriptor["executor"] == "script" and evaluator_for(descriptor) is None:
            failures.append(f"config/extensions/rules: {rule_id} declares executor=script but the kernel has no evaluator")
    classes = write_class(root)
    for rule_id, descriptor in sorted(descriptors.items()):
        reasons = delegation_problems(descriptor, classes)
        if reasons:  # HJ-7: a script resolver the kernel would not delegate is refused at the gate
            failures.append(f"config/extensions/rules: {rule_id} asks for resolver=script but is not delegable: "
                            + "; ".join(reasons))
    declared = {descriptor["trigger"]["when"] for descriptor in descriptors.values()}
    for when in sorted(set(EVALUATORS) - declared):
        failures.append(f"scripts/researchos_kernel/rules.py: evaluator for trigger {when} has no v2 descriptor")
    return failures


def main() -> int:
    failures = validate_extension_files(ROOT)
    failures.extend(validate_scheduler_rules(ROOT))
    for language in ("en", "zh-CN"):
        try:
            task_routes(language)
        except Exception as error:  # The gate must fail closed on any route-assembly error.
            failures.append(f"{language} task-route assembly failed: {error}")
    if failures:
        print("Task extension validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK: declarative task extension packs satisfy core API v1 and the scheduler rule contract v2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
