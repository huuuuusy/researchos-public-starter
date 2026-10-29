# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard server 中关于「Codex CLI runner」的辅助 owner；把前端交接任务转成受控的本地 Codex 执行记录。
# English: Helper owner for the local Codex CLI runner in the ResearchOS dashboard server; turns frontend handoff tasks into controlled local Codex run records.
"""Controlled Codex CLI runner for ResearchOS UI handoff tasks."""
from __future__ import annotations
import json
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable
from researchos_kernel.atomic_files import append_text, atomic_write_text, lock_path_for, runtime_state_transaction
from researchos_kernel.candidate_envelope import normalize_candidate_envelope
from researchos_adapters.command_runner import CommandRunner
from researchos_adapters.filesystem_staging import (
    FilesystemStagingError, finalize_artifact_staging, staging_for_policy,
)
from researchos_adapters.model_catalog import (
    CODEX_APP_CLI,
    ModelCatalog,
    resolve_model_config,
    task_complexity_fields,
)
from researchos_adapters.provider_config import (enforce_runtime_submission_boundary, load_runtime_config,
    project_public_runtime_run, provider_status, public_provider_status, sanitize_public_runtime_output)
from researchos_adapters.runtime_profile import RuntimeProfileError, resolve_runtime_profile_route
from researchos_adapters.provider_adapter import (
    CodexProviderAdapter, ProviderAdapterError, ProviderDispatch, codex_adapter, provider_adapter_status,
)
from researchos_adapters.policy_gateway import PolicyGateway, PolicyGatewayError, policy_receipt_ref
from researchos_kernel.result_contract import build_error_envelope, failure_response, result_projection
from researchos_adapters.work_session_result import result_from_output
from researchos_adapters.run_state import (RunStateError, claim_run_dispatch, now_iso, reconciled_run_record,
    run_for_id, run_lease_expired, run_state_ledger, runner_status)
from researchos_adapters.runner_permissions import RunnerPermissionError, isolated_codex_home, runner_launch_permissions
from researchos_adapters.runner_authority import DirectExecutionRegistry
from researchos_server.runner_prompt_policy import with_local_file_link_instruction, worker_prompt
from researchos_server.runtime_retention import compact_jsonl_run_log
from researchos_kernel.task_envelope import RUNTIME_SCOPES, build_task_envelope, normalize_task_intent_result, task_envelope_ref
@dataclass(frozen=True)
class CodexRunner:
    root: Path
    command_runner: CommandRunner
    log_jsonl: Path
    log_md: Path
    runtime_scope: str
    codex_path: Path = CODEX_APP_CLI
    timeout: int = 900
    output_limit: int = 24000
    log_max_bytes: int = 5 * 1024 * 1024
    log_max_runs: int = 80
    model_catalog: ModelCatalog | None = None
    public_starter: bool = True
    reference_root: Path | None = None
    post_run_refresh: Callable[[], dict[str, object]] | None = None
    allowed_task_modes = {"read_only_analysis", "candidate_patch_plan", "direct_execution"}
    result_from_output = staticmethod(result_from_output)
    with_local_file_link_instruction = staticmethod(with_local_file_link_instruction)
    def __post_init__(self) -> None:
        if self.runtime_scope not in RUNTIME_SCOPES:
            raise ValueError("Invalid Codex runner runtime scope")
        if self.public_starter != (self.runtime_scope == "public_starter"):
            raise ValueError("Codex runner runtime scope conflicts with public boundary")
        if self.runtime_scope == "personal_vault" and not callable(self.post_run_refresh): raise ValueError("Personal-vault runner requires post-run refresh")
    def submit(self, payload: object) -> dict[str, object]:
        if not isinstance(payload, dict):
            raise ValueError("Invalid Codex runner payload")
        payload, boundary_error = enforce_runtime_submission_boundary(payload, public_starter=self.public_starter)
        if boundary_error:
            return failure_response(boundary_error)
        task_intent, task_error = normalize_task_intent_result(payload)
        if task_error:
            return failure_response(task_error)
        assert task_intent is not None
        try: profile_id, provider = resolve_runtime_profile_route(load_runtime_config(), payload, runtime_scope=self.runtime_scope)
        except RuntimeProfileError as exc: return failure_response({"error_type": exc.code})
        base_provider_status = provider_status(provider, public_starter=self.public_starter)
        if not base_provider_status.get("ok"):
            return self.provider_failure(base_provider_status)
        task_mode = str(payload.get("task_mode", "read_only_analysis")).strip() or "read_only_analysis"
        if task_mode not in self.allowed_task_modes: task_mode = "read_only_analysis"
        try:
            prepared_policy = self.policy_gateway().prepare(payload, task_mode)
        except PolicyGatewayError as exc:
            return failure_response({"error_type": exc.code})
        status = self.executor_provider_status(provider)
        if not status.get("ok"): return self.provider_failure(status)
        complexity = task_complexity_fields(payload)
        recommended_complexity = complexity["recommended_task_complexity"] or "standard"
        requested_complexity = complexity["task_complexity"] or "auto"
        recommended_reasoning = payload.get("recommended_reasoning_effort", "auto")
        requested_reasoning = payload.get("reasoning_effort", "auto")
        model_config = self.model_config(
            payload.get("model", "auto"),
            recommended_complexity if requested_complexity == "auto" else requested_complexity,
            recommended_reasoning if requested_reasoning == "auto" else requested_reasoning,
        )
        prompt = str(payload.get("prompt", "")).strip() or str(task_intent["instruction"]).strip()
        candidate = payload.get("candidate", {})
        if not prompt and isinstance(candidate, dict):
            prompt = str(candidate.get("summary", "") or candidate.get("claim_or_task", "")).strip()
        if not prompt:
            return failure_response({"error_type": "task_intent_invalid_value"})
        prompt = prompt if self.public_starter else self.with_local_file_link_instruction(prompt)
        created_at = now_iso()
        run = {
            "id": f"codex-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}",
            "status": "queued",
            "task_mode": task_mode,
            "response_mode": str(payload.get("response_mode") or task_intent["requested_result"]["mode"]).strip()[:80],
            "work_session_id": str(payload.get("work_session_id", "")).strip()[:240],
            "title": str(payload.get("title", "")).strip()[:300],
            "task_complexity": model_config["task_complexity"],
            "task_complexity_mode": "auto_recommended" if requested_complexity == "auto" else "manual_override",
            "recommended_task_complexity": str(recommended_complexity).strip()[:80],
            "model": model_config["model"],
            "model_mode": model_config["model_mode"],
            "reasoning_effort": model_config["reasoning_effort"],
            "reasoning_effort_mode": "auto_recommended" if requested_reasoning == "auto" else "manual_override",
            "recommended_reasoning_effort": str(recommended_reasoning).strip()[:80],
            "requested_runtime_profile_id": str(payload.get("runtime_profile_id") or task_intent["requested_profile"]["provider"]),
            "runtime_profile_id": profile_id,
            "provider": provider,
            "provider_status": public_provider_status(status, public_starter=self.public_starter),
            "prompt": prompt,
            "candidate": self.normalize_candidate(candidate),
            "source": str(payload.get("source", "dashboard-unified-inbox")).strip()[:120],
            "created_at": created_at,
            "updated_at": created_at,
        }
        run["task_envelope"] = build_task_envelope(
            task_intent, run=run, runtime_scope=self.runtime_scope, idempotency_namespace=str(self.root.resolve()))
        try:
            reservation, reserved = run_state_ledger(self.log_jsonl, self.runtime_scope).reserve(run)
        except RunStateError as exc:
            return failure_response({"error_type": exc.code})
        if reservation == "replay":
            existing = run_for_id(self.reduced_runs(), reserved["run_id"])
            if reserved["state"] in {"running", "completed", "failed"}:
                return {"ok": True, "replayed": True, "run": existing or self.public_run(reconciled_run_record(reserved))}
            run["id"] = reserved["run_id"]
            run["task_envelope"] = build_task_envelope(task_intent, run=run, runtime_scope=self.runtime_scope,
                                                       idempotency_namespace=str(self.root.resolve()))
        try:
            run.update(self.policy_gateway().issue(prepared_policy, run["task_envelope"]))
        except PolicyGatewayError as exc:
            failed = self.failed_run(run, now_iso(), exc.code)
            return {"ok": False, "error_type": failed["error_type"], "error_envelope": failed["error_envelope"]}
        self.append_event({**run, "event": "queued"})
        threading.Thread(target=self.run_codex, args=(run,), daemon=True).start()
        return {"ok": True, "run": self.public_run(run)}
    def status(self, limit: int = 20, *, client_request_id: str = "", idempotency_key: str = "") -> dict[str, object]:
        try:
            return runner_status(
                ledger=None if self.public_starter else run_state_ledger(self.log_jsonl, self.runtime_scope),
                runs=self.reduced_runs(), limit=limit, client_request_id=client_request_id,
                idempotency_key=idempotency_key,
                log_path="" if self.public_starter else str(self.log_md.relative_to(self.root)),
                provider_status=public_provider_status(self.executor_provider_status("codex"), public_starter=self.public_starter))
        except RunStateError as exc:
            return failure_response({"error_type": exc.code})
    def run_codex(self, run: dict[str, object]) -> dict[str, object]:
        started_at = now_iso()
        if self.public_starter:
            return self.failed_run(run, started_at, "public_starter_copy_only")
        try:
            authority_policy = self.validated_authority_policy(run)
        except PolicyGatewayError as exc:
            return self.failed_run(run, started_at, exc.code)
        try:
            adapter = self.provider_adapter(str(run.get("provider", "codex")))
        except ProviderAdapterError as exc:
            return self.failed_run(run, started_at, exc.code)
        adapter_status = adapter.status()
        if not adapter_status.get("ok"):
            return self.failed_run(run, started_at, str(adapter_status.get("error_type", "codex_cli_missing")))
        try:
            ledger = run_state_ledger(self.log_jsonl, self.runtime_scope) if isinstance(run.get("task_envelope"), dict) else None
            if ledger and not claim_run_dispatch(ledger, run):
                observed = ledger.reconcile(idempotency_key=run.get("task_envelope", {}).get("idempotency_key", ""))
                return run_for_id(self.reduced_runs(), run.get("id")) or self.public_run(reconciled_run_record(observed))
        except RunStateError as exc:
            return self.failed_run(run, started_at, exc.code)
        self.append_event({**run, "status": "running", "event": "started", "updated_at": started_at, "started_at": started_at})
        reference_root = self.reference_root or self.root
        artifact_staging = None
        try:
            artifact_staging = staging_for_policy(
                root=self.root, runtime_scope=self.runtime_scope, run_id=run.get("id"), authority_policy=authority_policy)
            with isolated_codex_home() as codex_home:
                launch_permissions = runner_launch_permissions(
                    root=self.root,
                    reference_root=reference_root,
                    authority_policy=authority_policy,
                    codex_home=codex_home,
                    artifact_staging=artifact_staging,
                )
                direct_write_authorized = launch_permissions.direct_write
                result = adapter.execute(ProviderDispatch(
                    cwd=launch_permissions.cwd, config_args=tuple(launch_permissions.config_args),
                    codex_home=codex_home, model=str(run.get("model", "")),
                    reasoning_effort=str(run.get("reasoning_effort") or "low"),
                    prompt=self.worker_prompt(run, authority_policy, launch_permissions.cwd if direct_write_authorized else None), timeout=self.timeout,
                )).to_dict()
        except ProviderAdapterError as exc:
            if artifact_staging: artifact_staging.abort()
            return self.failed_run(run, started_at, exc.code)
        except FilesystemStagingError as exc:
            if artifact_staging: artifact_staging.abort()
            return self.failed_run(run, started_at, exc.code, filesystem_receipt=exc.receipt or {})
        except RunnerPermissionError:
            if artifact_staging: artifact_staging.abort()
            return self.failed_run(run, started_at, "runner_permission_boundary_failed")
        except Exception:
            if artifact_staging: artifact_staging.abort()
            return self.failed_run(run, started_at, "runner_execution_failed")
        finished_at = now_iso()
        output = str(result.get("stdout") or result.get("output") or "")[-self.output_limit :]
        if self.public_starter:
            output = sanitize_public_runtime_output(output, self.root)
        usage = self.usage_from_output(output)
        result_fields = self.result_from_output(output)
        blocked = result_fields.get("execution_status") == "blocked"
        ok = bool(result.get("ok")) and not blocked
        ok, result_fields, filesystem_receipt = finalize_artifact_staging(
            artifact_staging, execution_ok=ok, result_fields=result_fields)
        refresh: dict[str, object] = {}
        if ok and direct_write_authorized and self.post_run_refresh:
            try:
                refresh_result = self.post_run_refresh()
                refresh = {
                    "ok": bool(refresh_result.get("ok")),
                    "returncode": refresh_result.get("returncode"),
                    "seconds": refresh_result.get("seconds"),
                }
                if not refresh["ok"]:
                    refresh["error_type"] = "post_run_refresh_failed"
            except Exception:
                refresh = {"ok": False, "error_type": "post_run_refresh_failed"}
        if not ok:
            output = ""
            failure_type = str(result_fields.get("error_type") or "runner_execution_failed")
            failure_message = str(result_fields.get("message") or "Execution failed after dispatch; inspect the run before trying again.")
            result_fields = {
                "answer": "", "artifacts": [], "changed_files": [], "change_summary": [],
                "error_type": failure_type, "message": failure_message,
            }
        event = {
            **run,
            "status": "completed" if ok else "failed",
            "event": "completed" if ok else "failed",
            "updated_at": finished_at,
            "started_at": started_at,
            "finished_at": finished_at,
            "returncode": result.get("returncode"),
            "seconds": result.get("seconds"),
            "output": output,
            "usage": usage,
            "post_run_refresh": refresh,
            **result_fields,
        }
        if filesystem_receipt: event["filesystem_receipt"] = filesystem_receipt
        self.append_event(event)
        return event
    def provider_adapter(self, provider: str = "codex") -> CodexProviderAdapter:
        return codex_adapter(
            provider, root=self.root, command_runner=self.command_runner, runtime_scope=self.runtime_scope,
            codex_path=self.codex_path, output_limit=self.output_limit,
        )
    def codex_executable(self) -> Path | None: return self.provider_adapter().executable()
    def executor_provider_status(self, provider: str = "codex") -> dict[str, object]:
        return provider_adapter_status(
            provider, root=self.root, command_runner=self.command_runner, runtime_scope=self.runtime_scope,
            codex_path=self.codex_path, output_limit=self.output_limit,
        )
    def worker_prompt(
        self, run: dict[str, object], authority_policy: dict[str, object] | None = None,
        execution_write_root: Path | None = None,
    ) -> str:
        reference_root = self.reference_root or self.root
        return worker_prompt(
            run,
            root=self.root,
            reference_root=reference_root,
            authority_policy=authority_policy or self.validated_authority_policy(run),
            execution_write_root=execution_write_root,
        )
    def direct_execution_registry(self) -> DirectExecutionRegistry: return DirectExecutionRegistry(root=self.root, public_starter=self.public_starter)
    def policy_gateway(self) -> PolicyGateway: return PolicyGateway(root=self.root, runtime_scope=self.runtime_scope, action_registry=self.direct_execution_registry())
    def validated_authority_policy(self, run: dict[str, object]) -> dict[str, object]: return self.policy_gateway().launch_policy(run)
    def append_event(self, record: dict[str, object]) -> None:
        with runtime_state_transaction(lock_path=lock_path_for(self.log_jsonl)):
            ledger = None if self.public_starter else run_state_ledger(self.log_jsonl, self.runtime_scope)
            if ledger: ledger.validate_observation(record)
            retained_record = dict(record)
            retained_record.pop("prompt", None)
            if retained_record.get("status") == "failed": retained_record = result_projection(retained_record, runtime_scope=self.runtime_scope)
            if retained_record.get("event") != "queued" and "task_envelope" in retained_record:
                retained_record["task_envelope_ref"] = task_envelope_ref(retained_record.pop("task_envelope"))
            if retained_record.get("event") != "queued":
                for key in ("policy_decision", "authorization_grant"):
                    if key in retained_record: retained_record[f"{key}_ref"] = policy_receipt_ref(retained_record.pop(key))
            append_text(self.log_jsonl, json.dumps(retained_record, ensure_ascii=False, sort_keys=True) + "\n")
            if ledger: ledger.observe(record)
            self.compact_log()
            try:
                self.render_markdown()
            except Exception as exc:
                self.write_markdown_render_error(exc)
    def compact_log(self, *, force: bool = False) -> dict[str, int]:
        return compact_jsonl_run_log(
            self.log_jsonl, max_bytes=self.log_max_bytes, max_runs=self.log_max_runs,
            output_limit=self.output_limit, force=force,
        )
    def reduced_runs(self) -> list[dict[str, object]]:
        records: dict[str, dict[str, object]] = {}
        if not self.log_jsonl.exists():
            return []
        for line in self.log_jsonl.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            run_id = str(event.get("id", "")).strip()
            if not run_id:
                continue
            records[run_id] = {**records.get(run_id, {}), **event}
        return sorted((self.public_run(record) for record in records.values()), key=lambda item: str(item.get("updated_at", "")), reverse=True)

    def public_run(self, run: dict[str, object]) -> dict[str, object]:
        output = str(run.get("output", ""))[-self.output_limit :]
        if self.public_starter:
            output = sanitize_public_runtime_output(output, self.root)
        raw_refresh = run.get("post_run_refresh", {})
        refresh = {}
        if isinstance(raw_refresh, dict) and raw_refresh:
            refresh = {
                "attempted": True,
                "ok": bool(raw_refresh.get("ok")),
                "error_type": str(raw_refresh.get("error_type", "")),
            }
        usage = run.get("usage", {})
        if not isinstance(usage, dict) or not usage:
            usage = self.usage_from_output(output)
        result_fields = self.result_from_output(output)
        status = str(run.get("status", "queued"))
        envelope = run.get("task_envelope") if isinstance(run.get("task_envelope"), dict) else {}; reference = run.get("task_envelope_ref") if isinstance(run.get("task_envelope_ref"), dict) else {}
        client = envelope.get("client") if isinstance(envelope.get("client"), dict) else {}
        lease_expired = status in {"submitted", "queued", "running"} and run_lease_expired(run, self.timeout)
        projection = {
            "id": str(run.get("id", "")),
            "client_request_id": str(client.get("request_id") or reference.get("client_request_id") or ""),
            "status": status,
            "lease_expired": lease_expired,
            "task_mode": str(run.get("task_mode", "read_only_analysis")),
            "response_mode": str(run.get("response_mode", "answer")),
            "work_session_id": str(run.get("work_session_id", "")),
            "title": str(run.get("title", "")),
            "candidate": self.normalize_candidate(run.get("candidate", {})),
            "authority_policy": self.policy_gateway().projection_policy(run),
            "policy_decision_ref": policy_receipt_ref(run.get("policy_decision")) or run.get("policy_decision_ref", {}),
            "authorization_grant_ref": policy_receipt_ref(run.get("authorization_grant")) or run.get("authorization_grant_ref", {}),
            "created_at": str(run.get("created_at", "")),
            "updated_at": str(run.get("updated_at", "")),
            "started_at": str(run.get("started_at", "")),
            "finished_at": str(run.get("finished_at", "")),
            "returncode": run.get("returncode", ""),
            "seconds": run.get("seconds", ""),
            "message": str(run.get("message", "")),
            "output": output,
            "usage": usage,
            **task_complexity_fields(run),
            "model": str(run.get("model", "")),
            "model_mode": str(run.get("model_mode", "")),
            "provider": str(run.get("provider", "codex")),
            "provider_status": public_provider_status(run.get("provider_status", {}), public_starter=self.public_starter),
            "reasoning_effort": str(run.get("reasoning_effort", "")),
            "reasoning_effort_mode": str(run.get("reasoning_effort_mode", "")),
            "recommended_reasoning_effort": str(run.get("recommended_reasoning_effort", "")),
            "parent_id": str(run.get("parent_id", "")),
            "entry_type": str(run.get("entry_type", "")),
            "entry_id": str(run.get("entry_id", "")),
            "action_key": str(run.get("action_key", "")),
            "queue_index": run.get("queue_index", ""),
            "queue_total": run.get("queue_total", ""),
            "queue_completed": run.get("queue_completed", ""),
            "queue_failed": run.get("queue_failed", ""),
            "current_item_id": str(run.get("current_item_id", "")),
            "current_action_key": str(run.get("current_action_key", "")),
            "current_queue_index": run.get("current_queue_index", ""),
            "answer": sanitize_public_runtime_output(
                run.get("answer", result_fields.get("answer", "")), self.root
            ) if self.public_starter else str(run.get("answer", result_fields.get("answer", ""))),
            "artifacts": run.get("artifacts", result_fields.get("artifacts", [])),
            "changed_files": run.get("changed_files", result_fields.get("changed_files", [])),
            "preview_anchors": run.get("preview_anchors", result_fields.get("preview_anchors", [])),
            "change_summary": run.get("change_summary", result_fields.get("change_summary", [])),
            "execution_status": str(run.get("execution_status", result_fields.get("execution_status", ""))),
            "post_run_refresh": refresh,
            "task_envelope": run.get("task_envelope", {}),
            "task_envelope_ref": run.get("task_envelope_ref", {}),
        }
        projection = result_projection(projection, runtime_scope=self.runtime_scope)
        return project_public_runtime_run(projection, self.root) if self.public_starter else projection

    @staticmethod
    def usage_from_output(output: str) -> dict[str, int]:
        for line in reversed(str(output or "").splitlines()):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            usage = event.get("usage") if event.get("type") == "turn.completed" else None
            if not isinstance(usage, dict):
                continue
            keys = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
            return {key: int(usage.get(key, 0) or 0) for key in keys}
        return {}

    def model_config(self, model: object, task_complexity: object, reasoning_effort: object = "auto") -> dict[str, str]:
        catalog = self.model_catalog or ModelCatalog(root=self.root, command_runner=self.command_runner, codex_path=self.codex_path)
        return resolve_model_config(
            model,
            reasoning_effort,
            task_complexity,
            catalog.status(public_starter=self.public_starter),
        )

    def provider_failure(self, status: dict[str, object]) -> dict[str, object]:
        visible_status = public_provider_status(status, public_starter=True) if self.public_starter else status
        return failure_response({**status, "provider_status": visible_status})

    def failed_run(self, run: dict[str, object], started_at: str, error_type: str, **extra: object) -> dict[str, object]:
        error = build_error_envelope(error_type, run=run)
        event = {**run, "status": "failed", "event": "failed", "updated_at": now_iso(), "started_at": started_at,
                 "error_type": error["error_type"], "error_envelope": error, "message": error["message"], "output": "", **extra}
        self.append_event(event)
        return event

    @staticmethod
    def normalize_candidate(candidate: object) -> dict[str, object]:
        return normalize_candidate_envelope(candidate)

    def render_markdown(self) -> None:
        today = datetime.now().date().isoformat()
        lines = [
            "---",
            "type: active_context",
            'title: "UI Codex Runner Log"',
            "status: active",
            f"created: {today}",
            f"updated: {today}",
            "tags:",
            "  - dashboard",
            "  - codex-runner",
            "  - local-execution",
            "sensitivity: internal",
            "---",
            "",
            "# UI Codex Runner Log",
            "",
            "## Agent Summary",
            "",
            "本文件由 ResearchOS dashboard 的本地 Codex Runner 自动生成，记录前端交接任务何时被提交给本机 Codex CLI、逐条执行状态、输出摘要和权限边界。它不是长期研究记忆；直接执行仅可写入服务端登记的成果目录，并保留失败项供排查。",
            "",
            "## Handling Protocol",
            "",
            "1. `direct_execution` runner 使用服务端生成的严格权限配置，仅可写入登记的成果目录。",
            "2. 成功条目会从 dashboard 当前待处理列表移出；失败条目继续保留，便于重新执行或人工排查。",
            "3. `read_only_analysis` 历史记录只表示候选分析，不会自动清理待处理项。",
            "4. 失败记录通常表示本地 Codex CLI 登录、网络、权限、证据不足或执行阻塞，不代表任务本身无效。",
            "",
            "## Recent Runs",
            "",
        ]
        runs = self.reduced_runs()
        if not runs:
            lines.extend(["暂无 Codex runner 记录。", ""])
        for run in runs[:40]:
            candidate = run.get("candidate", {}) if isinstance(run.get("candidate", {}), dict) else {}
            proposed_action = candidate.get("proposed_action", {}) if isinstance(candidate.get("proposed_action", {}), dict) else {}
            proposed_writeback = candidate.get("proposed_writeback", {}) if isinstance(candidate.get("proposed_writeback", {}), dict) else {}
            policy = run.get("authority_policy", {}) if isinstance(run.get("authority_policy", {}), dict) else {}
            trusted_save_target = next((str(target.get("path", "")) for target in policy.get("allowed_write_targets", []) if isinstance(target, dict)), "")
            lines.extend(
                [
                    f"### {run.get('id', '')}",
                    "",
                    f"- status: {run.get('status', '')}",
                    f"- task_mode: {run.get('task_mode', '')}",
                    f"- model: {run.get('model', '') or 'default'} / reasoning `{run.get('reasoning_effort', '') or 'default'}`",
                    f"- task_complexity: {run.get('task_complexity', '') or 'legacy'}",
                    f"- title: {run.get('title', '') or candidate.get('summary', '') or '未命名'}",
                    f"- candidate_id: `{candidate.get('candidate_id', '') or '未标注'}`",
                    f"- target_agent: {proposed_action.get('target_agent', '') or '未标注'}",
                    f"- object: {proposed_writeback.get('object_type', '') or 'unknown'} / `{proposed_writeback.get('object_path', '') or proposed_writeback.get('object_id', '')}`",
                    f"- save_target: `{trusted_save_target or 'none'}`",
                    f"- required_confirmation: {candidate.get('required_confirmation', '') or 'handoff_only'}",
                    f"- updated_at: `{run.get('updated_at', '')}`",
                    "",
                    "#### Output Summary",
                    "",
                    "````text",
                    self.markdown_safe_output(str(run.get("output", "")).strip()[-2000:] or "暂无输出。"),
                    "````",
                    "",
                ]
            )
        atomic_write_text(self.log_md, "\n".join(lines))

    def write_markdown_render_error(self, exc: Exception) -> None:
        today = datetime.now().date().isoformat()
        atomic_write_text(
            self.log_md,
            "\n".join(
                [
                    "---",
                    "type: active_context",
                    'title: "UI Codex Runner Log"',
                    "status: active",
                    f"created: {today}",
                    f"updated: {today}",
                    "tags:",
                    "  - dashboard",
                    "  - codex-runner",
                    "  - local-execution",
                    "sensitivity: internal",
                    "---",
                    "",
                    "# UI Codex Runner Log",
                    "",
                    "Markdown render failed, but JSONL execution records are still preserved. Inspect the structured run receipt.",
                    "",
                ]
            ),
        )

    @staticmethod
    def markdown_safe_output(text: str) -> str:
        return str(text).replace("[", "［").replace("]", "］")
