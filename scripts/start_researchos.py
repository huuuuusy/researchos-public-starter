#!/usr/bin/env python3
# ResearchOS maintenance header.
# English: Provides the CLI entrypoint for dashboard, GUI companion, and public-starter runtime checks.
"""Unified startup entrypoint for ResearchOS."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from researchos_adapters.provider_config import load_runtime_config, provider_status


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PROJECTION_FILES = (
    Path("08_exports/public_starter/generated-public-starter-data.json"),
    Path("dashboard/data/researchos-dashboard.json"),
)


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _researchos_server_identity(host: str, port: int) -> dict[str, object] | None:
    try:
        with urlopen(f"http://{host}:{port}/session-config", timeout=0.75) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("request_header") != "X-ResearchOS-Session" or not payload.get("request_token"):
            return None
        return payload
    except (OSError, URLError, ValueError):
        return None


def _is_researchos_server(host: str, port: int, expected_runtime: str = "public_starter") -> bool:
    identity = _researchos_server_identity(host, port)
    return bool(
        identity
        and identity.get("runtime_mode") == expected_runtime
        and identity.get("repository_kind") == "public_starter"
    )


def _print_status(title: str, rows: list[tuple[str, object]]) -> None:
    print(title)
    for key, value in rows:
        print(f"- {key}: {value}")


def _run_server(command: list[str]) -> int:
    try:
        return subprocess.call(command)
    except KeyboardInterrupt:
        print("\nResearchOS launcher stopped.")
        return 0


def guard_dashboard_port(host: str, port: int, expected_runtime: str = "public_starter") -> int | None:
    if not _is_port_open(host, port):
        return None
    researchos = _is_researchos_server(host, port, expected_runtime)
    _print_status(
        "ResearchOS dashboard port check",
        [
            ("dashboard", f"http://{host}:{port}/"),
            ("status", "already running" if researchos else "port belongs to another service or ResearchOS runtime"),
            ("next", "open the existing dashboard" if researchos else f"stop the other runtime or retry with --port {port + 1}"),
        ],
    )
    return 0 if researchos else 2


def ensure_public_projection() -> tuple[int, str]:
    """Create a missing shipped projection without dirtying an ordinary checkout."""
    missing = [path for path in PUBLIC_PROJECTION_FILES if not (REPO_ROOT / path).is_file()]
    if not missing:
        return 0, "using shipped tracked projection"
    build_script = REPO_ROOT / "scripts" / "build_public_starter_data.py"
    result = subprocess.call([sys.executable, str(build_script), "--write"])
    return result, "rebuilt because tracked projection was missing"


def check_runtime(provider: str, public_starter: bool = True) -> int:
    status = provider_status(provider, public_starter=public_starter)
    copy_only = public_starter and status.get("error_type") == "public_starter_copy_only"
    _print_status(
        "ResearchOS runtime check",
        [
            ("provider", status.get("provider")),
            ("ok", bool(status.get("ok") or copy_only)),
            ("model", status.get("model", "n/a")),
            ("runtime_mode", status.get("runtime_mode", "public starter" if public_starter else "private vault")),
        ],
    )
    if not status.get("ok") and not copy_only:
        print(status.get("message_en"))
        print(status.get("message_zh"))
        return 1
    return 0


def mode_dashboard(port: int, provider: str) -> int:
    config = load_runtime_config()
    host = config.get("dashboard", {}).get("host", "127.0.0.1")
    port_result = guard_dashboard_port(host, port, "public_starter")
    if port_result is not None:
        return port_result
    build_result, projection_status = ensure_public_projection()
    if build_result:
        return build_result
    status = provider_status(provider, public_starter=True)
    _print_status(
        "ResearchOS public starter dashboard",
        [
            ("mode", "dashboard"),
            ("vault", "fake/sanitized demo"),
            ("dashboard", f"http://{host}:{port}/"),
            ("provider", status.get("provider", "codex")),
            ("provider_mode", "copy_only"),
            ("execution_scope", "none"),
            ("allow_local_codex", "false"),
            ("maintenance_scope", "registered_actions"),
            ("allow_real_api", "false"),
            ("public_starter", "enabled"),
            ("projection", projection_status),
            ("next", "open the dashboard; rebuild explicitly after editing demo sources"),
        ],
    )
    serve_script = REPO_ROOT / "scripts" / "serve_dashboard.py"
    return _run_server([sys.executable, str(serve_script), "--port", str(port)])


def mode_personal_vault(port: int, provider: str) -> int:
    """Build and serve a user's own local Markdown layers without changing demo data."""
    config = load_runtime_config()
    host = config.get("dashboard", {}).get("host", "127.0.0.1")
    port_result = guard_dashboard_port(host, port, "personal_vault")
    if port_result is not None:
        return port_result
    build_script = REPO_ROOT / "scripts" / "build_public_starter_data.py"
    build_result = subprocess.call([sys.executable, str(build_script), "--personal-vault", "--write"])
    if build_result:
        return build_result
    status = provider_status(provider, public_starter=False)
    _print_status(
        "ResearchOS personal vault dashboard",
        [
            ("mode", "personal-vault"),
            ("vault", "user-provided local Markdown"),
            ("dashboard", f"http://{host}:{port}/"),
            ("provider", status.get("provider", "demo_only")),
            ("authority", "local Markdown + human confirmation"),
            ("projection", "dashboard/data/researchos-local.json (git-ignored)"),
            ("privacy", "do not push personal cards or the local projection to a public repository"),
        ],
    )
    serve_script = REPO_ROOT / "scripts" / "serve_dashboard.py"
    return _run_server(
        [
            sys.executable,
            str(serve_script),
            "--port",
            str(port),
            "--data-file",
            "dashboard/data/researchos-local.json",
        ]
    )


def mode_cli(provider: str) -> int:
    _print_status(
        "You are in ResearchOS Public Starter CLI companion mode.",
        [
            ("project", REPO_ROOT),
            ("provider", f"{provider} (copy-only: nothing is run)"),
            ("work_surface", "your private agent task or terminal"),
            ("dashboard_required", "false"),
            ("runtime", "copy_only"),
            ("cancel", "unsupported"),
            ("rebuild demo projection (after editing demo sources)", "python3 scripts/build_public_starter_data.py --write"),
            ("optional dashboard", "python3 scripts/start_researchos.py --mode dashboard --port 8880"),
            ("validation", "python3 scripts/check_all_links.py"),
            ("architecture check", "python3 scripts/validate_agent_architecture.py"),
            ("provider check", f"python3 scripts/start_researchos.py --mode public-starter --check --provider {provider}"),
        ],
    )
    return 0


def mode_gui(port: int, provider: str) -> int:
    config = load_runtime_config()
    host = config.get("dashboard", {}).get("host", "127.0.0.1")
    url = f"http://{host}:{port}/"
    _print_status(
        "ResearchOS Codex GUI companion mode",
        [
            ("work_surface", "your private Codex GUI task"),
            ("dashboard_required", "false"),
            ("optional_dashboard", url),
            ("provider", f"{provider} (copy-only: nothing is run)"),
            ("runtime", "copy_only"),
            ("cancel", "unsupported"),
            ("gui role", "copy the task packet into a private agent task (Claude Code, Codex or another file-aware client)"),
            ("dashboard role", "optional Resume / Prepare / Handoff projection"),
            ("optional command", f"python3 scripts/start_researchos.py --mode dashboard --port {port}"),
        ],
    )
    return 0


def mode_public_starter(port: int, provider: str) -> int:
    status = provider_status(provider, public_starter=True)
    _print_status(
        "ResearchOS public starter mode",
        [
            ("mode", "public-starter"),
            ("vault", "fake/sanitized demo"),
            ("dashboard", f"http://127.0.0.1:{port}/"),
            ("provider", provider),
            ("provider_mode", "copy_only"),
            ("execution_scope", "none"),
            ("allow_local_codex", "false"),
            ("allow_real_api", "false"),
            ("status", "ok" if status.get("ok") else status.get("error_type")),
            ("note", "status-only mode; use --mode dashboard to start the server"),
        ],
    )
    return 0 if status.get("ok") or status.get("error_type") == "public_starter_copy_only" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start or inspect ResearchOS runtime modes.")
    parser.add_argument("--mode", choices=["dashboard", "personal-vault", "cli", "gui", "public-starter"], default="dashboard")
    parser.add_argument("--port", type=int, default=8880)
    parser.add_argument("--provider", default=None, help="codex or claude_code")
    parser.add_argument("--check", action="store_true", help="Run configuration check instead of starting a mode.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_runtime_config()
    provider = args.provider or config.get("default_provider", "codex")
    if args.check:
        return check_runtime(provider, public_starter=args.mode in {"dashboard", "public-starter"})
    if args.mode == "dashboard":
        return mode_dashboard(args.port, provider)
    if args.mode == "personal-vault":
        return mode_personal_vault(args.port, provider)
    if args.mode == "cli":
        return mode_cli(provider)
    if args.mode == "gui":
        return mode_gui(args.port, provider)
    if args.mode == "public-starter":
        return mode_public_starter(args.port, provider)
    raise AssertionError(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
