# ResearchOS maintenance header.
# 中文：第二个本地参考适配器——Claude Code CLI；与 Codex 适配器共用同一执行端口与同一道启动边界，不拥有 policy、结果语义或 canonical writer。
# English: Second local reference adapter, the Claude Code CLI; shares the execution port and launch boundary with the Codex adapter without owning policy, result semantics, or canonical writes.

"""Local Claude Code CLI reference adapter.

The researcher's own Claude Code login is the only credential: the adapter forwards no API key,
loads no user, project or local settings files and therefore none of their hooks or plugins, no
slash commands and no MCP servers (``--restricted --disable-slash-commands --strict-mcp-config``),
gives the run no tools at all (``--tools ""``: the filtered context pack is already inside the
prompt), and runs from an empty workspace under a private ``CLAUDE_CONFIG_DIR`` unless the login
lives in a keychain only the researcher's own config directory can read; then ``config_dir`` is None
and the variable stays unset, because setting it, even to the default directory, makes the CLI look
for a different keychain entry. ``--bare`` is not used: it accepts only an API key and never reads a
subscription login. A run that cannot be bounded
is refused, never run unbounded; the Dashboard runner is unchanged and remains Codex-only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from researchos_adapters.command_runner import CommandRunner, codex_cli_env
from researchos_adapters.model_catalog import REASONING_EFFORTS
from researchos_adapters.provider_adapter import (ExecutionRequest, ProviderAdapterError, ProviderCancellation,
                                                ProviderExecution, _clean_text)
from researchos_adapters.provider_config import provider_execution_status
from researchos_kernel.task_envelope import RUNTIME_SCOPES


PROVIDER_ID = "claude_code"
ADAPTER_FAMILY = "local_claude_code"
# The desktop app bundles the CLI; standalone installs put `claude` on PATH.
DESKTOP_BUNDLE_ROOT = Path("Library/Application Support/Claude/claude-code")
DESKTOP_BUNDLE_GLOB = "*/*/claude.app/Contents/MacOS/claude"
NOT_LOGGED_IN = "claude_code_not_logged_in"


class ClaudeCodePermissionError(ValueError):
    """Raised when the isolated configuration directory cannot be proven safe."""


def _version_key(path: Path) -> tuple[int, ...]:
    parts = re.findall(r"\d+", path.parents[4].name) if len(path.parents) > 4 else []
    return tuple(int(part) for part in parts)


def resolve_claude_executable(preferred: Path | str | None = None) -> Path | None:
    """Configured command first, then PATH, then the newest desktop-bundled CLI."""
    if preferred:
        candidate = Path(os.path.expanduser(str(preferred)))
        if candidate.is_absolute():
            return candidate if candidate.is_file() and os.access(candidate, os.X_OK) else None
        found = shutil.which(str(preferred))
        if found:
            return Path(found)
    found = shutil.which("claude")
    if found:
        return Path(found)
    bundled = sorted((Path.home() / DESKTOP_BUNDLE_ROOT).glob(DESKTOP_BUNDLE_GLOB), key=_version_key)
    for candidate in reversed(bundled):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def configured_claude_config_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))


@contextmanager
def isolated_claude_config() -> Iterator[Path]:
    """An empty private config directory: no user settings, hooks, memory or MCP servers.

    Only a file-based login (``.credentials.json``) is linked in, with the same ownership checks the
    Codex boundary applies to ``auth.json``; a keychain-based login needs nothing copied."""
    source_credentials = Path(os.path.abspath(os.fspath(configured_claude_config_dir() / ".credentials.json")))
    with tempfile.TemporaryDirectory(prefix="researchos-claude-") as directory:
        isolated = Path(directory)
        isolated.chmod(0o700)
        if source_credentials.exists():
            metadata = source_credentials.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                raise ClaudeCodePermissionError("Claude Code credentials file is not a regular non-symlink file")
            if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
                raise ClaudeCodePermissionError("Claude Code credentials file is not owned by the current user")
            (isolated / ".credentials.json").symlink_to(source_credentials)
        yield isolated


@dataclass(frozen=True)
class ClaudeCodeExtension:
    """Claude Code-only launch parameters: empty workspace, private config directory (None: the CLI's
    own default, for a keychain login), effort, budget."""

    cwd: Path
    config_dir: Path | None
    effort: str = "low"
    max_budget_usd: str = ""


def answer_from_claude_output(output: str) -> tuple[str, str]:
    """(final answer, error code) from ``--output-format json``; tool logs never enter the answer."""
    text = str(output or "").strip()
    document: object = None
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        for line in reversed(text.splitlines()):
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict) and candidate.get("type") == "result":
                document = candidate
                break
    if not isinstance(document, dict) or document.get("type") != "result":
        return "", "runner_output_unparseable"
    result = str(document.get("result") or "").strip()
    if document.get("is_error"):
        return result, NOT_LOGGED_IN if "not logged in" in result.lower() else "runner_execution_failed"
    return result, ""


@dataclass(frozen=True)
class ClaudeCodeProviderAdapter:
    root: Path
    command_runner: CommandRunner
    runtime_scope: str
    command: str = ""
    output_limit: int = 24000

    def __post_init__(self) -> None:
        if self.runtime_scope not in RUNTIME_SCOPES or self.output_limit <= 0:
            raise ValueError("Invalid Claude Code provider adapter configuration")

    def executable(self) -> Path | None:
        return None if self.runtime_scope == "public_starter" else resolve_claude_executable(self.command or None)

    def status(self) -> dict[str, object]:
        public = self.runtime_scope == "public_starter"
        return {
            **provider_execution_status(
                PROVIDER_ID, public_starter=public, executable_available=bool(self.executable()),
                runtime_scope=self.runtime_scope,
            ),
            "adapter_family": "none" if public else ADAPTER_FAMILY,
            "selected_adapter": "none" if public else "cli_print",
            "cancel": "unsupported",
        }

    def cancel(self, run_ref: str):
        if self.runtime_scope == "public_starter":
            raise ProviderAdapterError("public_starter_copy_only")
        if not _clean_text(run_ref, maximum=240).strip():
            raise ProviderAdapterError("provider_dispatch_invalid")
        return ProviderCancellation(provider=PROVIDER_ID, accepted=False, status="unsupported",
                                    error_type="provider_cancel_unsupported")

    def execute(self, request):
        if self.runtime_scope == "public_starter":
            raise ProviderAdapterError("public_starter_copy_only")
        executable = self.executable()
        if not executable:
            return ProviderExecution(PROVIDER_ID, False, "unavailable", 0.0, "", "claude_code_cli_missing")
        if not isinstance(request, ExecutionRequest) or not isinstance(request.extension, ClaudeCodeExtension) \
                or request.timeout <= 0:
            raise ProviderAdapterError("provider_dispatch_invalid")
        extension = request.extension
        if not (extension.cwd.is_absolute() and (extension.config_dir is None or extension.config_dir.is_absolute())):
            raise ProviderAdapterError("provider_dispatch_invalid")
        model = _clean_text(request.model, maximum=240).strip()
        effort = _clean_text(extension.effort, maximum=80).strip() or "low"
        budget = _clean_text(extension.max_budget_usd, maximum=20).strip()
        prompt = _clean_text(request.prompt, maximum=1024 * 1024)
        if effort not in REASONING_EFFORTS:
            raise ProviderAdapterError("unsupported_reasoning_effort")
        if budget and not re.fullmatch(r"\d{1,6}(\.\d{1,2})?", budget):
            raise ProviderAdapterError("provider_dispatch_invalid")
        args = [
            str(executable), "--print", "--output-format", "json",
            "--restricted", "--disable-slash-commands", "--strict-mcp-config", "--tools", "", "--no-session-persistence",
            "--max-turns", "1", "--permission-mode", "dontAsk", "--effort", effort,
        ]
        if model not in {"", "auto"}:
            args.extend(["--model", model])
        if budget:
            args.extend(["--max-budget-usd", budget])
        launch_env = codex_cli_env()  # the same credential-free projection; no API key is ever forwarded
        launch_env.pop("CODEX_HOME", None)
        if os.environ.get("USER"):
            launch_env["USER"] = os.environ["USER"]  # a macOS keychain login is looked up by user name
        if extension.config_dir is not None:
            launch_env["CLAUDE_CONFIG_DIR"] = str(extension.config_dir)
        raw = self.command_runner.run(args, timeout=request.timeout, input_text=prompt, env=launch_env)
        stdout = str(raw.get("stdout") or raw.get("output") or "")
        answer, error = answer_from_claude_output(stdout) if raw.get("ok") else ("", "runner_execution_failed")
        ok = bool(raw.get("ok")) and not error
        return ProviderExecution(
            provider=PROVIDER_ID, ok=ok, returncode=raw.get("returncode", ""),
            seconds=max(0.0, float(raw.get("seconds", 0) or 0)),
            stdout=(answer if ok else (answer or stdout))[-self.output_limit:],
            error_type="" if ok else error,
        )
