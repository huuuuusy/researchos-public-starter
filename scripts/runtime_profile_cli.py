#!/usr/bin/env python3
"""Inspect and select RuntimeProfile v1 without Dashboard, server, credentials, or network."""

from __future__ import annotations

import argparse
import json

from researchos_kernel.atomic_files import atomic_write_json
from researchos_adapters.provider_config import LOCAL_CONFIG, load_runtime_config
from researchos_adapters.runtime_profile import (
    RuntimeProfileError,
    project_runtime_profile,
    runtime_profiles_from_config,
    select_runtime_profile,
)


def _emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _local_document() -> dict[str, object]:
    if not LOCAL_CONFIG.exists():
        return {"schema_id": "researchos-runtime-config-v1"}
    if LOCAL_CONFIG.is_symlink() or not LOCAL_CONFIG.is_file() or LOCAL_CONFIG.stat().st_size > 1_048_576:
        raise RuntimeProfileError("runtime_local_config_not_allowed")
    try:
        value = json.loads(LOCAL_CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeProfileError("runtime_local_config_invalid") from exc
    if not isinstance(value, dict) or value.get("schema_id") != "researchos-runtime-config-v1":
        raise RuntimeProfileError("runtime_local_config_invalid")
    return value


def _atomic_write(value: dict[str, object]) -> None:
    parent = LOCAL_CONFIG.parent
    if parent.is_symlink() or not parent.is_dir() or LOCAL_CONFIG.is_symlink():
        raise RuntimeProfileError("runtime_local_config_not_allowed")
    atomic_write_json(LOCAL_CONFIG, value, sort_keys=True)


def _resolve(profile: dict[str, object], model: str | None, reasoning: str | None) -> dict[str, object]:
    requested_model = model or str(profile["model"])
    requested_reasoning = reasoning or str(profile["reasoning_effort"])
    if requested_model not in profile["allowed_models"]:
        raise RuntimeProfileError("runtime_profile_model_not_allowed")
    if requested_reasoning not in profile["allowed_reasoning_efforts"]:
        raise RuntimeProfileError("runtime_profile_reasoning_not_allowed")
    return {**project_runtime_profile(profile, runtime_scope="private"),
            "model": requested_model, "reasoning_effort": requested_reasoning, "dispatch": "not_started"}


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("command", choices=("list", "show", "validate", "resolve", "select"))
    value.add_argument("--profile")
    value.add_argument("--scope", choices=("private", "personal_vault", "public_starter"), default="private")
    value.add_argument("--model")
    value.add_argument("--reasoning")
    value.add_argument("--write", action="store_true")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config = load_runtime_config(include_local=True)
        profiles = runtime_profiles_from_config(config)
        if args.command == "validate":
            _emit({"ok": True, "profiles": len(profiles), "network": "not_used", "credentials": "not_resolved"})
        elif args.command == "list":
            if args.scope == "public_starter":
                _emit({"profiles": [project_runtime_profile({}, runtime_scope="public_starter")]})
            else:
                _emit({"profiles": [project_runtime_profile(profile, runtime_scope=args.scope) for profile in profiles.values()]})
        elif args.command == "show":
            if not args.profile or args.profile not in profiles:
                raise RuntimeProfileError("runtime_profile_unknown")
            _emit(project_runtime_profile(profiles[args.profile], runtime_scope=args.scope))
        elif args.command == "resolve":
            profile = select_runtime_profile(config, profile_id=args.profile, runtime_scope=args.scope)
            _emit(_resolve(profile, args.model, args.reasoning))
        else:
            profile = select_runtime_profile(config, profile_id=args.profile, runtime_scope=args.scope)
            plan = {"ok": True, "profile_id": profile["profile_id"], "write": bool(args.write),
                    "target": "config/researchos.runtime.local.json", "network": "not_used"}
            if args.write:
                local = _local_document()
                local["default_runtime_profile"] = profile["profile_id"]
                _atomic_write(local)
            _emit(plan)
        return 0
    except RuntimeProfileError as exc:
        _emit({"ok": False, "error_type": exc.code, "network": "not_used"})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
