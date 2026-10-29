#!/usr/bin/env python3
# ResearchOS maintenance header.
# English: Validates Agent-facing code routes, runtime reachability, frontend registration, and owner budgets.
"""Fail closed when the public code map drifts away from the executable package."""

from __future__ import annotations

import ast
import json
import re
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_MAPS = ("docs/system-reference.en.md", "docs/system-reference.zh.md")
REMOVED_PYTHON_PATHS = (
    "scripts/researchos_server/model_provider.py",
    "scripts/researchos_venue_index.py",
)
LEGACY_CASE_GLOBS = ("fake-*.md", "walkthrough*.md", "example-original-developer-*.md")
OWNER_LINE_BUDGETS = {
    "dashboard/app.js": 2600,
    "scripts/serve_dashboard.py": 650,
    "scripts/build_public_starter_data.py": 1060,
    "scripts/ros.py": 2100,
}
DEFAULT_FRONTEND_OWNER_BUDGET = 1500
FRONTEND_OWNER_BUDGETS = {"dashboard/src/core/ui-copy.js": 3200}
PYTHON_PACKAGE_BUDGETS = {"researchos_kernel": 750, "researchos_adapters": 600, "researchos_server": 1200}
# A second escapeHtml body, or an escape default that is the identity (`(value) => String(value ?? "")`
# `|| String(value || "")`, `(escapeHtml || String)`, or the same for markdownToHtml), would let a missing argument mean "no escaping".
DUPLICATE_ESCAPE_PATTERN = re.compile(r"\bfunction\s+(?:\w+EscapeHtml|escapeHtml\w+)\s*\(")
IDENTITY_ESCAPE_PATTERN = re.compile(
    r"(?:[eE]scape|markdownToHtml)\w*\b[^\n]*(?:=>|\|\|)\s*\(?\s*String\(\s*\w+\s*(?:\?\?|\|\|)\s*\"\"\s*\)"
    r"|[eE]scapeHtml\s*\|\|\s*String\)"
)
REQUIRED_MAP_TOKENS = (
    "scripts/start_researchos.py",
    "scripts/build_public_starter_data.py",
    "scripts/research_agenda_projection.py",
    "scripts/plan_context.py",
    "scripts/serve_dashboard.py",
    "dashboard/app.js",
    "scripts/validate_agent_architecture.py",
    "scripts/plan_evolution.py",
    "scripts/researchos_server/evolution_planner.py",
    "scripts/researchos_kernel/result_contract.py",
    "scripts/researchos_adapters/policy_gateway.py",
    "scripts/researchos_adapters/provider_adapter.py",
    "scripts/researchos_adapters/filesystem_staging.py",
    "scripts/researchos_adapters/run_state.py",
    "scripts/researchos_kernel/task_envelope.py",
    "scripts/validate_evolution_control.py",
)


def parse_imports(path: Path) -> list[tuple[int, str, tuple[str, ...]]]:
    """Return (relative level, module, imported names) without importing code."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[int, str, tuple[str, ...]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((0, alias.name, ()) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.level, node.module or "", tuple(alias.name for alias in node.names)))
    return imports


REACHABILITY_PACKAGES = ("researchos_kernel", "researchos_adapters", "researchos_server")


def package_dependencies(path: Path, package: str) -> set[str]:
    """Modules of ``package`` that ``path`` imports, absolute or (inside the package) relative."""
    dependencies: set[str] = set()
    for level, module, names in parse_imports(path):
        if module.startswith(f"{package}."):
            dependencies.add(module.split(".", 1)[1].split(".", 1)[0])
        elif module == package:
            dependencies.update(name.split(".", 1)[0] for name in names)
        elif level == 1 and path.parent.name == package:
            if module:
                dependencies.add(module.split(".", 1)[0])
            else:
                dependencies.update(name.split(".", 1)[0] for name in names)
    return dependencies


def validate_dependency_direction(root: Path) -> list[str]:
    """Dependencies point inward: the kernel imports nothing outside itself, the adapters nothing from the server."""
    scripts = root / "scripts"
    local = {path.stem for path in scripts.glob("*.py")} | {
        path.name for path in scripts.iterdir() if (path / "__init__.py").is_file()
    }
    failures: list[str] = []
    for package, forbidden in (
        ("researchos_kernel", local - {"researchos_kernel"}),
        ("researchos_adapters", {"researchos_server"}),
    ):
        for path in sorted((scripts / package).glob("*.py")):
            for level, module, _ in parse_imports(path):
                top = module.split(".", 1)[0]
                if level == 0 and top in forbidden:
                    failures.append(f"{path.relative_to(root)}: imports {module}; {package} must not depend on {top}")
    return failures


def validate_python_routes(root: Path) -> tuple[list[str], dict[str, int], int]:
    failures: list[str] = []
    scripts = root / "scripts"
    # The supported data helpers are the modules in scripts/researchos_data/; each must be named in both code
    # maps, so a helper cannot be added (or reintroduced) without being documented.
    supported_data = {path.name for path in (scripts / "researchos_data").glob("*.py") if path.name != "__init__.py"}
    maps = {relative: (root / relative).read_text(encoding="utf-8") for relative in AGENT_MAPS if (root / relative).exists()}
    unsupported_data = [name for name in sorted(supported_data) if any(name not in text for text in maps.values())]
    for name in unsupported_data:
        failures.append(f"scripts/researchos_data/{name}: data helper is not named in the code maps {', '.join(AGENT_MAPS)}")
    removed_python = [root / relative for relative in REMOVED_PYTHON_PATHS if (root / relative).exists()]
    for path in removed_python:
        failures.append(f"{path.relative_to(root)}: removed compatibility module was reintroduced")

    public_python = [
        path
        for path in scripts.rglob("*.py")
        if "__pycache__" not in path.parts
        and path.parent.name != "researchos_data"
    ]
    maintenance_import_seen = False
    for path in public_python:
        try:
            imports = parse_imports(path)
        except SyntaxError as error:
            failures.append(f"{path.relative_to(root)}: cannot parse Python: {error}")
            continue
        for level, module, names in imports:
            if module == "researchos_data":
                failures.append(f"{path.relative_to(root)}: broad researchos_data import bypasses the supported-module boundary")
            elif module.startswith("researchos_data."):
                imported = f"{module.split('.', 1)[1].split('.', 1)[0]}.py"
                if imported not in supported_data:
                    failures.append(f"{path.relative_to(root)}: imports removed/unsupported module {module}")
                else:
                    maintenance_import_seen = True
            if module == "researchos_venue_index" or module.startswith("researchos_venue_index."):
                failures.append(f"{path.relative_to(root)}: imports removed module {module}")
            if module == "researchos_server.model_provider" or module.startswith("researchos_server.model_provider."):
                failures.append(f"{path.relative_to(root)}: imports removed module {module}")
            if level == 1 and path.parent.name == "researchos_server" and module == "model_provider":
                failures.append(f"{path.relative_to(root)}: imports removed module .model_provider")
            if level == 1 and path.parent.name == "researchos_server" and not module and "model_provider" in names:
                failures.append(f"{path.relative_to(root)}: imports removed module .model_provider")
    if not maintenance_import_seen:
        failures.append("supported maintenance_pipeline.py is not imported by a public runtime module")

    # Reachability runs over every module of the three packages: a kernel or adapter module is reached
    # through a script, a server module or another package's module, never only through a test.
    modules = {
        (package, path.stem): path
        for package in (*REACHABILITY_PACKAGES, "researchos_data")
        for path in (scripts / package).glob("*.py")
        if path.name != "__init__.py"
    }
    graph = {
        key: {(package, name) for package in REACHABILITY_PACKAGES
              for name in package_dependencies(path, package) if (package, name) in modules}
        for key, path in modules.items()
    }
    roots = {
        (package, name)
        for path in scripts.glob("*.py")
        for package in REACHABILITY_PACKAGES
        for name in package_dependencies(path, package)
        if (package, name) in modules
    }
    roots |= {key for key in modules if key[0] == "researchos_data"}  # each one is documented in the code maps
    reachable: set[tuple[str, str]] = set()
    queue = deque(sorted(roots))
    while queue:
        key = queue.popleft()
        if key in reachable:
            continue
        reachable.add(key)
        queue.extend(sorted(graph.get(key, set()) - reachable))
    for package, name in sorted(set(modules) - reachable):
        if package != "researchos_data":
            failures.append(f"scripts/{package}/{name}.py: no supported top-level runtime or validator can reach this module")
    reached = {package: sum(1 for key in reachable if key[0] == package) for package in REACHABILITY_PACKAGES}

    return failures, reached, len(unsupported_data) + len(removed_python)


def validate_module_docstrings(root: Path) -> list[str]:
    """Every Python module under scripts/ opens with a docstring saying what it owns; the templated
    bilingual maintenance header is required of dashboard JavaScript only."""
    failures: list[str] = []
    for path in sorted((root / "scripts").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            documented = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) is not None
        except SyntaxError:
            continue  # reported by the reachability check
        if not documented:
            failures.append(f"{path.relative_to(root)}: missing module docstring")
    return failures


def validate_frontend_registration(root: Path) -> tuple[list[str], int]:
    failures: list[str] = []
    dashboard = root / "dashboard"
    index_text = (dashboard / "index.html").read_text(encoding="utf-8")
    sources = [source.split("?", 1)[0].removeprefix("./") for source in re.findall(r'<script[^>]+src="([^"]+)"', index_text)]
    registered = [source for source in sources if source.startswith("src/") and source.endswith(".js")]
    actual = sorted(path.relative_to(dashboard).as_posix() for path in (dashboard / "src").rglob("*.js"))
    counts = Counter(registered)
    for source in sorted(set(actual) - set(registered)):
        failures.append(f"dashboard/{source}: JavaScript owner is not registered in dashboard/index.html")
    for source in sorted(set(registered) - set(actual)):
        failures.append(f"dashboard/index.html: registered JavaScript file does not exist: dashboard/{source}")
    for source, count in sorted(counts.items()):
        if count != 1:
            failures.append(f"dashboard/index.html: {source} is registered {count} times")
    for relative in actual:
        text = (dashboard / relative).read_text(encoding="utf-8")
        if relative == "src/views/unified-inbox.js":
            for retired in ("renderModelSelect", "renderReasoningEffortSelect"):
                if retired in text:
                    failures.append(f"dashboard/{relative}: retired Dashboard execution control is still exported: {retired}")
        if "ResearchOS maintenance header." not in "\n".join(text.splitlines()[:8]):
            failures.append(f"dashboard/{relative}: missing maintenance owner header")
        if DUPLICATE_ESCAPE_PATTERN.search(text):
            failures.append(
                f"dashboard/{relative}: duplicates the shared ResearchOSUiCore.escapeHtml implementation"
            )
        if IDENTITY_ESCAPE_PATTERN.search(text):
            failures.append(
                f"dashboard/{relative}: an escape default returns text unescaped; fall back to ResearchOSUiCore.escapeHtml"
            )
    return failures, len(registered)


FRONTEND_GLOBAL_PATTERN = re.compile(r"\b(ResearchOS[A-Za-z0-9_]+)\b")
FRONTEND_GLOBAL_OWNER_PATTERN = re.compile(r"global\.(ResearchOS[A-Za-z0-9_]+)\s*=")
# Services that compose views: *-workbench.js controllers and the plugin host.
FRONTEND_CONTROLLER_SERVICES = ("-workbench.js", "/plugin-host.js")
FRONTEND_VIEW_DATA_SUFFIXES = ("View", "Projection", "Model", "State")


def validate_frontend_layering(root: Path) -> list[str]:
    """core references no services/views/plugins; views reference only views, components, core and
    *Projection/*Model/*State globals; only controller services (*-workbench.js, plugin-host.js)
    reference views or plugins. Layers are the dashboard/src directory of the file that assigns
    the global."""
    src = root / "dashboard" / "src"
    files = sorted(src.rglob("*.js"))
    owner_layer: dict[str, str] = {}
    for path in files:
        for name in FRONTEND_GLOBAL_OWNER_PATTERN.findall(path.read_text(encoding="utf-8")):
            owner_layer[name] = path.relative_to(src).parts[0]
    failures: list[str] = []
    for path in files:
        relative = path.relative_to(src).as_posix()
        layer = relative.split("/", 1)[0]
        controller = layer == "services" and relative.endswith(FRONTEND_CONTROLLER_SERVICES)
        for name in sorted(set(FRONTEND_GLOBAL_PATTERN.findall(path.read_text(encoding="utf-8")))):
            target = owner_layer.get(name)
            if target is None or target == layer:
                continue
            if layer == "core" and target in {"services", "views", "plugins"}:
                failures.append(f"dashboard/src/{relative}: core must not reference {target} global {name}")
            elif layer == "views" and target not in {"views", "components", "core"} and not name.endswith(FRONTEND_VIEW_DATA_SUFFIXES):
                failures.append(f"dashboard/src/{relative}: views may reference only views, components, core and *Projection/*Model/*State globals, not {name}")
            elif layer == "services" and not controller and target in {"views", "plugins"}:
                failures.append(f"dashboard/src/{relative}: only controller services (*-workbench.js, plugin-host.js) may reference {target} global {name}")
    return failures


def validate_frontend_lifecycle_callbacks(root: Path) -> list[str]:
    app_text = (root / "dashboard" / "app.js").read_text(encoding="utf-8")
    adapter_text = (root / "dashboard" / "src" / "services" / "dashboard-lifecycle-adapter.js").read_text(encoding="utf-8")
    callback_map = re.search(
        r"DASHBOARD_LIFECYCLE_CALLBACK_SOURCE_NAMES\s*=\s*Object\.freeze\(\{(.*?)\}\);",
        adapter_text,
        flags=re.DOTALL,
    )
    if callback_map is None:
        return ["dashboard-lifecycle-adapter.js: lifecycle callback registry is missing or unreadable"]
    required = set(re.findall(r':\s*"([A-Za-z0-9_$]+)"', callback_map.group(1)))
    declared = set(re.findall(r"^(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", app_text, flags=re.MULTILINE))
    return [
        f"dashboard/app.js: lifecycle callback {name} is registered by name but not declared"
        for name in sorted(required - declared)
    ]


def validate_agent_docs_and_budgets(root: Path) -> list[str]:
    failures: list[str] = []
    for relative in AGENT_MAPS:
        path = root / relative
        if not path.exists():
            failures.append(f"missing Agent code map: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in REQUIRED_MAP_TOKENS:
            if token not in text:
                failures.append(f"{relative}: missing owner token {token}")
    for relative, budget in OWNER_LINE_BUDGETS.items():
        path = root / relative
        if not path.exists():
            failures.append(f"missing owner file: {relative}")
            continue
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count > budget:
            failures.append(f"{relative}: {count} lines exceeds Agent owner budget {budget}; extract behavior before adding more")
    for path in sorted((root / "dashboard" / "src").rglob("*.js")):
        relative = path.relative_to(root).as_posix()
        budget = FRONTEND_OWNER_BUDGETS.get(relative, DEFAULT_FRONTEND_OWNER_BUDGET)
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count > budget:
            failures.append(f"{relative}: {count} lines exceeds frontend owner budget {budget}")
    for package, budget in PYTHON_PACKAGE_BUDGETS.items():
        for path in sorted((root / "scripts" / package).glob("*.py")):
            if path.name == "__init__.py":
                continue
            count = len(path.read_text(encoding="utf-8").splitlines())
            if count > budget:
                failures.append(f"{path.relative_to(root)}: {count} lines exceeds Python owner budget {budget}")
    return failures


def validate_removed_cases(root: Path) -> tuple[list[str], int]:
    failures: list[str] = []
    starter = root / "08_exports" / "public_starter"
    legacy = sorted({path for pattern in LEGACY_CASE_GLOBS for path in starter.glob(pattern)})
    for path in legacy:
        failures.append(f"{path.relative_to(root)}: legacy case was reintroduced after the hard-delete checkpoint")
    generated_paths = (
        root / "08_exports" / "public_starter" / "generated-public-starter-data.json",
        root / "dashboard" / "data" / "researchos-dashboard.json",
    )
    generated_text = "\n".join(path.read_text(encoding="utf-8") for path in generated_paths if path.exists())
    for marker in ("/fake-", "example-original-developer-", "/walkthrough.md", "/walkthrough.zh.md"):
        if marker in generated_text:
            failures.append(f"generated data contains removed legacy marker: {marker}")
    return failures, len(legacy)


def validate_conversation_material_boundaries(root: Path) -> list[str]:
    failures: list[str] = []
    planner = (root / "scripts" / "plan_context.py").read_text(encoding="utf-8")
    if "with_conversation_contract" not in planner:
        failures.append("scripts/plan_context.py: missing shared conversation authority contract")
    if "researchos_data.public_conversation_catalog" not in planner:
        failures.append("scripts/plan_context.py: built-in public conversation catalog is not explicit")
    if "build_public_starter_data" in planner:
        failures.append("scripts/plan_context.py: conversation entrypoint must not depend on the projection builder")
    payload = json.loads((root / "dashboard" / "data" / "researchos-dashboard.json").read_text(encoding="utf-8"))
    for task in payload.get("tasks", []):
        task_id = str(task.get("id", "unknown"))
        if task.get("primary_surface") != "conversation":
            failures.append(f"dashboard task {task_id}: primary_surface must remain conversation")
        if task.get("dashboard_role") != "projection_and_handoff":
            failures.append(f"dashboard task {task_id}: dashboard_role must remain projection_and_handoff")
        authority = task.get("authority", {})
        if authority.get("requires_human_confirmation") is not True or authority.get("writeback_route") != "review":
            failures.append(f"dashboard task {task_id}: durable writeback must remain human-confirmed Review")
    return failures


def validate(root: Path = ROOT) -> tuple[list[str], dict[str, int]]:
    failures, reached, removed_python_count = validate_python_routes(root)
    failures.extend(validate_dependency_direction(root))
    failures.extend(validate_module_docstrings(root))
    frontend_failures, frontend_count = validate_frontend_registration(root)
    removed_case_failures, removed_case_count = validate_removed_cases(root)
    failures.extend(frontend_failures)
    failures.extend(validate_frontend_lifecycle_callbacks(root))
    failures.extend(validate_frontend_layering(root))
    failures.extend(validate_agent_docs_and_budgets(root))
    failures.extend(validate_conversation_material_boundaries(root))
    failures.extend(removed_case_failures)
    return failures, {
        "frontend_modules": frontend_count,
        "reachable_kernel_modules": reached["researchos_kernel"],
        "reachable_adapter_modules": reached["researchos_adapters"],
        "reachable_server_modules": reached["researchos_server"],
        "removed_python_reintroduced": removed_python_count,
        "legacy_cases_reintroduced": removed_case_count,
    }


def main() -> int:
    failures, counts = validate()
    if failures:
        print("Agent architecture validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "OK: Agent architecture validated "
        f"({counts['frontend_modules']} frontend modules; "
        f"{counts['reachable_kernel_modules']} kernel, {counts['reachable_adapter_modules']} adapter and "
        f"{counts['reachable_server_modules']} server modules reachable; "
        f"{counts['removed_python_reintroduced']} removed Python files reintroduced; "
        f"{counts['legacy_cases_reintroduced']} legacy cases reintroduced)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
