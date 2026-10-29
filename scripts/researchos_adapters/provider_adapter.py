# ResearchOS maintenance header.
# 中文：唯一的执行端口（与后端无关）与 Codex reference adapter（第二个本地参考适配器 Claude Code CLI 见 claude_code_adapter.py）；只执行已由上游绑定的请求，不拥有 policy、结果语义或 canonical writer。
# English: Sole backend-neutral execution port and Codex reference adapter; executes upstream-bound requests without owning policy, result semantics, or canonical writes.

"""Provider execution port with a local Codex reference implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from researchos_adapters.command_runner import CommandRunner, codex_cli_env
from researchos_adapters.model_catalog import CODEX_APP_CLI, REASONING_EFFORTS, resolve_codex_executable
from researchos_adapters.provider_config import provider_execution_status
from researchos_kernel.task_envelope import RUNTIME_SCOPES


class ProviderAdapterError(ValueError):
    """Stable adapter-boundary failure without raw provider diagnostics."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


# Who produced a result (plan v4 §v5.3). Records name one of these and nothing backend-specific:
# the session Agent inside a client, a background provider, a degraded copy packet, or a script.
EXECUTOR_KINDS = ("session_agent", "provider", "copy_packet", "script")


def executor_ref(kind: str, provider_id: str = "") -> str:
    """``session_agent`` / ``provider:<id>`` / ``copy_packet`` / ``script``."""
    if kind not in EXECUTOR_KINDS or (kind == "provider") != bool(provider_id):
        raise ProviderAdapterError("executor_ref_invalid")
    return f"provider:{provider_id}" if provider_id else kind


def parse_executor_ref(ref: str) -> tuple[str, str]:
    kind, _, provider_id = str(ref or "").partition(":")
    executor_ref(kind, provider_id)  # validates
    return kind, provider_id


@dataclass(frozen=True)
class ExecutionRequest:
    """Backend-neutral execution data, already policy-bounded; it carries no grant or authority.
    Whatever only one backend understands rides in ``extension`` and is read by that adapter alone."""

    prompt: str
    timeout: int
    model: str = ""
    work_session_id: str = ""
    run_id: str = ""
    extension: object = None


@dataclass(frozen=True)
class CodexExtension:
    """Codex-only launch parameters: sandbox profile, isolated home, reasoning effort."""

    cwd: Path
    config_args: tuple[str, ...]
    codex_home: Path
    reasoning_effort: str = "low"


def ProviderDispatch(  # noqa: N802 - the Codex constructor kept for existing callers
    cwd: Path, config_args: tuple[str, ...], codex_home: Path, model: str, reasoning_effort: str,
    prompt: str, timeout: int, work_session_id: str = "", run_id: str = "",
) -> ExecutionRequest:
    return ExecutionRequest(prompt=prompt, timeout=timeout, model=model, work_session_id=work_session_id,
                            run_id=run_id, extension=CodexExtension(cwd, config_args, codex_home,
                                                                    reasoning_effort))


def codex_request(request: object) -> tuple[ExecutionRequest, CodexExtension]:
    if not isinstance(request, ExecutionRequest) or not isinstance(request.extension, CodexExtension) \
            or request.timeout <= 0:
        raise ProviderAdapterError("provider_dispatch_invalid")
    return request, request.extension


@dataclass(frozen=True)
class ProviderExecution:
    """Bounded provider fact. ResultEnvelope/ErrorEnvelope remain separate owners."""

    provider: str
    ok: bool
    returncode: int | str
    seconds: float
    stdout: str
    error_type: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "ok": self.ok,
            "returncode": self.returncode,
            "seconds": self.seconds,
            "stdout": self.stdout,
            "error_type": self.error_type,
        }


@dataclass(frozen=True)
class ProviderCancellation:
    """Provider cancellation fact; it never infers that an existing run was cancelled."""

    provider: str
    accepted: bool
    status: str
    error_type: str

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "accepted": self.accepted,
            "status": self.status,
            "error_type": self.error_type,
        }


class ProviderAdapter(Protocol):
    def status(self) -> dict[str, object]: ...
    def execute(self, request: ExecutionRequest) -> ProviderExecution: ...
    def cancel(self, run_ref: str) -> ProviderCancellation: ...


def _clean_text(value: object, *, maximum: int) -> str:
    text = str(value or "")
    if "\x00" in text or len(text) > maximum:
        raise ProviderAdapterError("provider_dispatch_invalid")
    return text


def _config_args(values: object) -> tuple[str, ...]:
    args = tuple(str(value) for value in values) if isinstance(values, tuple) else ()
    valid = (
        len(args) == 6 and args[:3] == ("--disable", "memories", "-c")
        and args[3] == 'default_permissions="researchos-runner-v1"' and args[4] == "-c"
        and args[5].startswith("permissions.researchos-runner-v1=")
        and "network={enabled=false}" in args[5]
    )
    if not valid:
        raise ProviderAdapterError("provider_dispatch_invalid")
    return args


@dataclass(frozen=True)
class CodexProviderAdapter:
    root: Path
    command_runner: CommandRunner
    runtime_scope: str
    codex_path: Path = CODEX_APP_CLI
    output_limit: int = 24000

    def __post_init__(self) -> None:
        if self.runtime_scope not in RUNTIME_SCOPES or self.output_limit <= 0:
            raise ValueError("Invalid Codex provider adapter configuration")

    def executable(self) -> Path | None:
        return None if self.runtime_scope == "public_starter" else resolve_codex_executable(self.codex_path)

    def status(self) -> dict[str, object]:
        return {
            **provider_execution_status(
            "codex", public_starter=self.runtime_scope == "public_starter",
            executable_available=bool(self.executable()), runtime_scope=self.runtime_scope,
            ),
            "adapter_family": "none" if self.runtime_scope == "public_starter" else "local_codex",
            "cancel": "unsupported",
        }

    def cancel(self, run_ref: str) -> ProviderCancellation:
        if self.runtime_scope == "public_starter":
            raise ProviderAdapterError("public_starter_copy_only")
        if not _clean_text(run_ref, maximum=240).strip():
            raise ProviderAdapterError("provider_dispatch_invalid")
        return ProviderCancellation(
            provider="codex", accepted=False, status="unsupported",
            error_type="provider_cancel_unsupported",
        )

    def execute(self, request: ExecutionRequest) -> ProviderExecution:
        if self.runtime_scope == "public_starter":
            raise ProviderAdapterError("public_starter_copy_only")
        executable = self.executable()
        if not executable:
            return ProviderExecution("codex", False, "unavailable", 0.0, "", "codex_cli_missing")
        request, codex = codex_request(request)
        model = _clean_text(request.model, maximum=240).strip()
        reasoning = _clean_text(codex.reasoning_effort, maximum=80).strip() or "low"
        prompt = _clean_text(request.prompt, maximum=1024 * 1024)
        config_args = _config_args(codex.config_args)
        if reasoning not in REASONING_EFFORTS:
            raise ProviderAdapterError("unsupported_reasoning_effort")
        args = [
            str(executable), "exec", "--ignore-user-config", "--ephemeral", "--strict-config",
            "--ignore-rules", "--skip-git-repo-check", "--cd", str(codex.cwd),
            *config_args,
        ]
        if model not in {"", "auto"}:
            args.extend(["-m", model])
        args.extend(["-c", f'model_reasoning_effort="{reasoning}"', "--json", "-"])
        launch_env = codex_cli_env()
        launch_env["CODEX_HOME"] = str(codex.codex_home)
        raw = self.command_runner.run(args, timeout=request.timeout, input_text=prompt, env=launch_env)
        stdout = str(raw.get("stdout") or raw.get("output") or "")[-self.output_limit :]
        return ProviderExecution(
            provider="codex", ok=bool(raw.get("ok")), returncode=raw.get("returncode", ""),
            seconds=max(0.0, float(raw.get("seconds", 0) or 0)), stdout=stdout,
            error_type="" if raw.get("ok") else "runner_execution_failed",
        )


def codex_adapter(
    provider: str, *, root: Path, command_runner: CommandRunner, runtime_scope: str,
    codex_path: Path = CODEX_APP_CLI, output_limit: int = 24000,
) -> CodexProviderAdapter:
    """Return the Codex reference adapter; any other provider name fails as not implemented."""
    if provider != "codex":
        raise ProviderAdapterError("provider_call_not_implemented")
    return CodexProviderAdapter(
        root=root, command_runner=command_runner, runtime_scope=runtime_scope,
        codex_path=codex_path, output_limit=output_limit,
    )


def claude_code_adapter(
    provider: str, *, root: Path, command_runner: CommandRunner, runtime_scope: str,
    command: str = "", output_limit: int = 24000,
) -> ProviderAdapter:
    """Return the second local reference adapter, the Claude Code CLI (print mode, no tools)."""
    if provider != "claude_code":
        raise ProviderAdapterError("provider_call_not_implemented")
    from researchos_adapters.claude_code_adapter import ClaudeCodeProviderAdapter
    return ClaudeCodeProviderAdapter(root=root, command_runner=command_runner, runtime_scope=runtime_scope,
                                     command=command, output_limit=output_limit)


def provider_adapter_status(
    provider: str, *, root: Path, command_runner: CommandRunner, runtime_scope: str,
    codex_path: Path = CODEX_APP_CLI, output_limit: int = 24000,
) -> dict[str, object]:
    if provider == "claude_code":
        return claude_code_adapter(provider, root=root, command_runner=command_runner,
                                   runtime_scope=runtime_scope, output_limit=output_limit).status()
    if provider != "codex":
        return provider_execution_status(
            provider, public_starter=runtime_scope == "public_starter", executable_available=False,
            runtime_scope=runtime_scope,
        )
    return codex_adapter(
        provider, root=root, command_runner=command_runner, runtime_scope=runtime_scope,
        codex_path=codex_path, output_limit=output_limit,
    ).status()

