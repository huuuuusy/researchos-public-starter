#!/usr/bin/env python3
"""Validate the runtime configuration and the provider registry it names, in one place.

The tracked config/researchos.runtime.example.json must declare every registered provider with its
registered adapter family, keep the public starter copy-only (no local Codex, allow_real_api false,
no task execution, registered maintenance only) and keep the case-materials switch explicit; no
registered provider may run in the public starter; local runtime config and .env files stay untracked.
This is the one assertion of the public-starter provider flags.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from researchos_adapters.provider_registry import PROVIDERS  # noqa: E402

CONFIG = REPO_ROOT / "config" / "researchos.runtime.example.json"
LOCAL_CONFIG = "config/researchos.runtime.local.json"
ENV_FILES = {".env", ".env.local"}


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def git_tracked(path: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    if not CONFIG.exists():
        return fail("config/researchos.runtime.example.json is missing")
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail(f"runtime config is not valid JSON: {exc}")

    for key in ["schema_id", "default_provider", "providers"]:
        if key not in config:
            return fail(f"runtime config missing {key}")

    providers = config.get("providers", {})
    missing = set(PROVIDERS) - set(providers)
    if missing:
        return fail(f"runtime config missing providers: {', '.join(sorted(missing))}")
    unknown = set(providers) - set(PROVIDERS)
    if unknown:
        return fail(f"runtime config names unregistered providers: {', '.join(sorted(unknown))}")
    for name, spec in PROVIDERS.items():
        if providers[name].get("type", spec.type) != spec.type:
            return fail(f"providers.{name}.type must be the registered adapter family {spec.type}")
        if spec.public_starter_allowed:
            return fail(f"{name}: no execution provider may be allowed in the copy-only public starter")

    public_starter = config.get("public_starter", {})
    if public_starter.get("provider_mode") != "copy_only":
        return fail("public starter must use copy_only provider mode")
    if public_starter.get("allow_local_codex") is not False or public_starter.get("allow_real_api") is not False:
        return fail("public starter must disable local Codex and keep allow_real_api=false")
    if public_starter.get("execution_scope") != "none" or public_starter.get("maintenance_scope") != "registered_actions":
        return fail("public starter must expose no task execution and only registered maintenance actions")
    case_materials = public_starter.get("case_materials", {})
    if not isinstance(case_materials.get("enabled"), bool):
        return fail("public starter case_materials.enabled must be an explicit boolean")
    if case_materials.get("source") != "08_exports/public_starter":
        return fail("public starter case_materials.source must point to 08_exports/public_starter")
    if case_materials.get("disabled_behavior") != "keep_files_as_reference_only":
        return fail("public starter case_materials.disabled_behavior must keep case files as reference-only")

    if git_tracked(LOCAL_CONFIG):
        return fail("local runtime config is tracked by Git")
    for env_file in ENV_FILES:
        if git_tracked(env_file):
            return fail(f"{env_file} is tracked by Git")

    print("OK: runtime config and provider registry are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
