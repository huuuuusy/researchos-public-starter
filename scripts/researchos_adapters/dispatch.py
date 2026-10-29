"""Execution adapter behind ``ros run``: which local runner a run may go to, how it is launched,
and the run-state records that the dispatch and its outcome leave.

The port stays backend-neutral (CR-3): ``provider_for`` returns an object with
``execute(request)``, and nothing about the records depends on which backend ran. The two local
reference runners launch through the same launch boundary the Dashboard runner uses (the provider,
command-runner and permission modules of this package, imported when a run is launched); this module
does not carry a second, weaker copy of that boundary. Run and Observation axes live in the one
run-state owner (``run_state``); the public edition keeps none (Soul §5).
"""

from __future__ import annotations

import hashlib
import importlib
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from researchos_kernel.result_contract import PRE_DISPATCH_ERRORS
from .provider_registry import PROVIDERS
from .run_state import derive_task_state, run_state_ledger

RUN_LOG = "06_active_context/work_state/runner-logs/codex-runner-log-current.jsonl"  # the one run-state location
PROVIDER_REASONING = ("low", "medium", "high")
# What config/ros.json may say about a provider: whether and how this vault dispatches to it. The
# provider's command and default model belong to the runtime configuration's providers block.
DISPATCH_KEYS = frozenset({"dispatchable", "reasoning", "config_dir", "max_budget_usd"})


def launched_nothing(error: str) -> bool:
    """A failure before anything was launched: nothing was sent, so a retry is safe. These are the
    result-contract errors whose last safe point is before dispatch, and each provider's CLI-missing code."""
    return error in PRE_DISPATCH_ERRORS or any(error == spec.cli_missing_error for spec in PROVIDERS.values())


def run_ledger(root: Path, config: dict, runtime_scope: str):
    """The run-state ledger of this installation, or None in the public edition (Soul §5)."""
    if runtime_scope == "public_starter":
        return None
    return run_state_ledger(root / config.get("run_log", RUN_LOG), runtime_scope)


def provider_for(config: dict, runtime_scope: str, provider_id: str):
    """The provider adapter for ``provider:<id>``, or None when it cannot be dispatched from here.

    A backend is dispatchable only when it is registered in ``PROVIDERS`` and this vault declares it in
    config/ros.json `providers` (`{"codex": {"dispatchable": true}}`). Declaring it is the researcher's
    decision, not a default: dispatching sends the context pack to that backend. The registered class
    owns how its CLI is launched; its command and default model come from the runtime configuration's
    providers block (config/researchos.runtime.example.json, overlaid by researchos.runtime.local.json)."""
    spec = PROVIDERS.get(provider_id)
    declared = (config.get("providers") or {}).get(provider_id)
    if spec is None or not isinstance(declared, dict) or declared.get("dispatchable") is not True \
            or runtime_scope == "public_starter":
        return None
    misplaced = sorted(set(declared) - DISPATCH_KEYS)
    if misplaced:
        raise SystemExit(f"providers.{provider_id} in config/ros.json may set only {', '.join(sorted(DISPATCH_KEYS))}; "
                         f"{', '.join(misplaced)} belongs in config/researchos.runtime.local.json "
                         "(the former model key is default_model there)")
    from .provider_config import load_runtime_config  # read when a run is dispatched, not at every ros command
    configured = (load_runtime_config().get("providers") or {}).get(provider_id) or {}
    module, _, name = spec.adapter.partition(":")
    provider_class = getattr(importlib.import_module(module), name)
    return provider_class(runtime_scope, {**declared, "command": configured.get("command", ""),
                                          "default_model": configured.get("default_model", spec.default_model)})


class LocalCodexProvider:
    """The local Codex CLI behind the shared launch boundary, built fresh for each run: an empty
    private CODEX_HOME (auth only), an empty read-only workspace, every other path denied, credentials
    denied, network off. The boundary is the same one the dashboard runner uses. A launch that cannot
    be bounded is refused, never run unbounded."""

    def __init__(self, runtime_scope: str, declared: dict) -> None:
        self.runtime_scope = runtime_scope
        self.model = str(declared.get("default_model", "") or "")
        self.reasoning = str(declared.get("reasoning", "low") or "low")
        if self.reasoning not in PROVIDER_REASONING:
            raise SystemExit(f"providers.codex.reasoning must be one of {', '.join(PROVIDER_REASONING)}")

    def execute(self, request):
        from tempfile import TemporaryDirectory
        from researchos_adapters.command_runner import CommandRunner
        from researchos_adapters.provider_adapter import (CodexProviderAdapter, ProviderAdapterError,
                                                        ProviderDispatch)
        from researchos_adapters.runner_permissions import (RunnerPermissionError, isolated_codex_home,
                                                          runner_launch_permissions)
        from researchos_adapters.work_session_result import result_from_output
        try:
            with TemporaryDirectory(prefix="researchos-provider-") as directory, isolated_codex_home() as codex_home:
                workspace = Path(directory).resolve()
                # The filtered context is already in the prompt. Neither the source repository
                # nor the installation/reference root is part of this model's read authority.
                permissions = runner_launch_permissions(
                    root=workspace, reference_root=workspace, codex_home=codex_home,
                    authority_policy={"operation": "read_only", "allowed_write_targets": []})
                adapter = CodexProviderAdapter(root=workspace, command_runner=CommandRunner(root=workspace),
                                               runtime_scope=self.runtime_scope)
                execution = adapter.execute(ProviderDispatch(
                    cwd=permissions.cwd, config_args=permissions.config_args, codex_home=codex_home,
                    model=self.model, reasoning_effort=self.reasoning, prompt=request.prompt,
                    timeout=request.timeout, work_session_id=request.work_session_id, run_id=request.run_id))
                # CLI --json returns events, not a Markdown draft. Reuse the result parser owner;
                # only the final assistant answer may enter the candidate path, never tool logs.
                if execution.ok:
                    execution = replace(execution, stdout=str(result_from_output(execution.stdout)["answer"]))
                return execution
        except RunnerPermissionError as error:
            # The boundary could not be built, so nothing was launched: this is a pre-launch failure.
            raise ProviderAdapterError("runner_boundary_unavailable") from error


class LocalClaudeCodeProvider:
    """The local Claude Code CLI behind the same launch boundary as the Codex provider, built fresh
    for each run: an empty workspace as cwd, a private CLAUDE_CONFIG_DIR (login only), `--restricted`
    (no user, project or local settings, so none of their hooks or plugins), `--disable-slash-commands`,
    `--strict-mcp-config` (no MCP servers), and `--tools ""` (no tools at all: the filtered context is
    already in the prompt). Declared dispatchable as `providers.claude_code` in config/ros.json; `config_dir: "shared"`
    leaves CLAUDE_CONFIG_DIR unset so the CLI uses the researcher's own directory, for a login kept in
    a keychain the isolated directory cannot see, as on macOS."""

    def __init__(self, runtime_scope: str, declared: dict) -> None:
        self.runtime_scope = runtime_scope
        self.model = str(declared.get("default_model", "") or "")
        self.reasoning = str(declared.get("reasoning", "low") or "low")
        self.command = str(declared.get("command", "") or "")
        self.max_budget_usd = str(declared.get("max_budget_usd", "") or "")
        self.config_dir = str(declared.get("config_dir", "isolated") or "isolated")
        if self.reasoning not in PROVIDER_REASONING:
            raise SystemExit(f"providers.claude_code.reasoning must be one of {', '.join(PROVIDER_REASONING)}")
        if self.config_dir not in ("isolated", "shared"):
            raise SystemExit("providers.claude_code.config_dir must be isolated or shared")

    def execute(self, request):
        from contextlib import nullcontext
        from tempfile import TemporaryDirectory
        from researchos_adapters.claude_code_adapter import (ClaudeCodeExtension, ClaudeCodePermissionError,
                                                           ClaudeCodeProviderAdapter, isolated_claude_config)
        from researchos_adapters.command_runner import CommandRunner
        from researchos_adapters.provider_adapter import ExecutionRequest, ProviderAdapterError
        config_scope = isolated_claude_config() if self.config_dir == "isolated" else nullcontext(None)
        try:
            with TemporaryDirectory(prefix="researchos-provider-") as directory, config_scope as config_dir:
                workspace = Path(directory).resolve()
                adapter = ClaudeCodeProviderAdapter(root=workspace, command_runner=CommandRunner(root=workspace),
                                                    runtime_scope=self.runtime_scope, command=self.command)
                return adapter.execute(ExecutionRequest(
                    prompt=request.prompt, timeout=request.timeout, model=self.model,
                    work_session_id=request.work_session_id, run_id=request.run_id,
                    extension=ClaudeCodeExtension(cwd=workspace, config_dir=config_dir and Path(config_dir).resolve(),
                                                  effort=self.reasoning, max_budget_usd=self.max_budget_usd)))
        except ClaudeCodePermissionError as error:
            raise ProviderAdapterError("runner_boundary_unavailable") from error


def run_lifecycle(session: str, run: str, observation: str, result: str, decision: str, side_effects: str) -> dict:
    """The five-axis snapshot of one run and the task state the run-state owner derives from it."""
    snapshot = {"session": session, "run": run, "observation": observation, "result": result,
                "side_effects": side_effects, "admission": {"decision_state": decision}}
    return {**snapshot, "derived": derive_task_state(snapshot)}


def run_record(run_id: str, status: str, task_id: str, *, side_effects: str = "") -> dict:
    """One run-state record for ``ros run``; its idempotency key is bound to the run id."""
    stamp = datetime.now().isoformat(timespec="seconds")
    record = {"id": run_id, "status": status, "created_at": stamp, "updated_at": stamp,
              "task_envelope": {"task_id": task_id, "run_id": run_id,
                                "idempotency_key": "idem:" + hashlib.sha256(run_id.encode("utf-8")).hexdigest(),
                                "client": {"request_id": run_id}}}
    if side_effects:
        record["error_envelope"] = {"side_effects": side_effects}
    return record
