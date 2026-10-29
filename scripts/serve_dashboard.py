#!/usr/bin/env python3
# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard 服务入口；只保留 HTTP 编排，持久化、预览和命令运行规则下放到 researchos_server。
# English: Local ResearchOS dashboard server entrypoint; keeps HTTP orchestration while persistence, preview, and command-running rules live in researchos_server.

"""Serve the local ResearchOS dashboard."""

from __future__ import annotations

import argparse
import http.server
import json
import signal
import tempfile
import threading
from urllib.parse import parse_qs, unquote, urlparse
from pathlib import Path

from researchos_server.material_pipeline_store import MaterialPipelineStore
from researchos_server.auto_update_runner import AutoUpdateRunner
from researchos_server.card_group_store import CardGroupStore
from researchos_server.codex_runner import CodexRunner
from researchos_adapters.command_runner import CommandRunner
from researchos_server.dashboard_config import configured_dashboard_port
from researchos_server.dashboard_config import ReusableTCPServer, dashboard_content_security_policy
from researchos_server.evolution_planner import EvolutionPlanner
from researchos_server.inbox_cleanup_store import InboxArraySpec, InboxCleanupStore
from researchos_server.inbox_store import InboxStore
from researchos_server.http_json import RequestBodyError, read_json_object
from researchos_server.maintenance_facade import active_build_command, evolution_plan_view, maintenance_action_response
from researchos_adapters.model_catalog import ModelCatalog
from researchos_server.preview_file_server import PreviewFileServer
from researchos_adapters.provider_config import public_provider_status
from researchos_server.research_scout_runner import ResearchScoutRunner
from researchos_server.request_security import LocalRequestSecurity
from researchos_kernel.result_contract import failure_response
from researchos_server.review_inbox_store import ReviewInboxStore, ReviewInboxValidationError
from researchos_server.runtime_read_boundary import RuntimeReadBoundary
from researchos_server.source_tree_store import SourceTreeError
from researchos_server.work_session_upload import WorkSessionUploadError, WorkSessionUploadStore, upload_request_metadata


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard"
DEFAULT_DASHBOARD_DATA = DASHBOARD / "data" / "researchos-dashboard.json"
PERSONAL_VAULT_DASHBOARD_DATA = DASHBOARD / "data" / "researchos-local.json"
ACTIVE_DASHBOARD_DATA = DEFAULT_DASHBOARD_DATA
PERSONAL_VAULT_ROOT = ROOT / "personal_vault"
CODEX_RUNNER_REQUEST_MAX_BYTES = 1000000
# Created by build_services() and configure_runtime_write_root(), never at import: importing this module
# starts nothing, materializes no read copy and reads no store.
SERVICE_NAMES = (
    "COMMAND_RUNNER", "MODEL_CATALOG", "AUTO_UPDATE_RUNNER", "EVOLUTION_PLANNER", "RESEARCH_SCOUT_RUNNER",
    "PUBLIC_READ_BOUNDARY", "PUBLIC_CODEX_ROOT_OWNER", "PUBLIC_CODEX_ROOT", "REQUEST_SECURITY",
    "PREVIEW_FILE_SERVER", "SOURCE_TREE_STORE", "LOCAL_FILE_BRIDGE", "ACTIVE_WRITE_ROOT", "FEEDBACK_JSONL",
    "FEEDBACK_MD", "CONFIRMATION_JSON", "CONFIRMATION_MD", "CARD_GROUPS_JSON", "CARD_GROUPS_MD",
    "GROUP_DISSOLUTION_JSON", "GROUP_DISSOLUTION_MD", "INBOX_CLEANUP_ARCHIVE", "CODEX_RUNNER_LOG_DIR",
    "CODEX_RUNNER_JSONL", "CODEX_RUNNER_MD", "INBOX_STORE", "CODEX_RUNNER", "WORK_SESSION_UPLOAD_STORE",
    "safe_md_path", "MATERIAL_PIPELINE_STORE", "CARD_GROUP_STORE", "REVIEW_INBOX_STORE",
    "INBOX_CLEANUP_STORE", "ACTIVE_READ_BOUNDARY",
)
_services_built = False
_SERVICES_LOCK = threading.RLock()  # lazy builds on request threads: one builds, the rest wait; re-entrant


def refresh_personal_vault_projection() -> dict[str, object]:
    """Run the one registered derived refresh outside the user-content sandbox."""
    with ReusableTCPServer.mutation_lock:  # the Codex thread never holds it, so this cannot deadlock
        return COMMAND_RUNNER.run(active_build_command(True), timeout=90)


def configure_runtime_write_root(write_root: Path, *, public_starter: bool) -> None:
    """Bind every user-content writer and the Codex sandbox to one explicit root."""
    global ACTIVE_WRITE_ROOT, FEEDBACK_JSONL, FEEDBACK_MD, CONFIRMATION_JSON, CONFIRMATION_MD
    global CARD_GROUPS_JSON, CARD_GROUPS_MD, GROUP_DISSOLUTION_JSON, GROUP_DISSOLUTION_MD
    global INBOX_CLEANUP_ARCHIVE, CODEX_RUNNER_LOG_DIR, CODEX_RUNNER_JSONL, CODEX_RUNNER_MD
    global INBOX_STORE, CODEX_RUNNER, WORK_SESSION_UPLOAD_STORE, safe_md_path
    global MATERIAL_PIPELINE_STORE, CARD_GROUP_STORE, REVIEW_INBOX_STORE, INBOX_CLEANUP_STORE
    global ACTIVE_READ_BOUNDARY, PREVIEW_FILE_SERVER, SOURCE_TREE_STORE, LOCAL_FILE_BRIDGE

    build_services()  # the public read copy and runners it binds to; a no-op once built
    lexical_write_root = Path(write_root)
    if lexical_write_root.is_symlink():
        raise RuntimeError("Runtime write root cannot be a symbolic link")
    ACTIVE_WRITE_ROOT = lexical_write_root.resolve()
    active_context = ACTIVE_WRITE_ROOT / "06_active_context"
    FEEDBACK_JSONL = active_context / "ui-feedback-inbox.jsonl"
    FEEDBACK_MD = active_context / "ui-feedback-inbox.md"
    CONFIRMATION_JSON = active_context / "ui-confirmation-decisions.json"
    CONFIRMATION_MD = active_context / "ui-confirmation-decisions.md"
    CARD_GROUPS_JSON = active_context / "ui-card-groups.json"
    CARD_GROUPS_MD = active_context / "ui-card-groups.md"
    GROUP_DISSOLUTION_JSON = active_context / "ui-card-group-dissolution-inbox.json"
    GROUP_DISSOLUTION_MD = active_context / "ui-card-group-dissolution-inbox.md"
    INBOX_CLEANUP_ARCHIVE = active_context / "ui-inbox-cleanup-archive.jsonl"
    CODEX_RUNNER_LOG_DIR = active_context / "work_state" / "runner-logs"
    CODEX_RUNNER_JSONL = CODEX_RUNNER_LOG_DIR / "codex-runner-log-current.jsonl"
    CODEX_RUNNER_MD = CODEX_RUNNER_LOG_DIR / "codex-runner-log-current.md"

    INBOX_STORE = InboxStore(root=ACTIVE_WRITE_ROOT, cleanup_archive=INBOX_CLEANUP_ARCHIVE)
    safe_md_path = INBOX_STORE.safe_md_path
    MATERIAL_PIPELINE_STORE = MaterialPipelineStore.from_root(ACTIVE_WRITE_ROOT, safe_md_path)
    CARD_GROUP_STORE = CardGroupStore(
        root=ACTIVE_WRITE_ROOT,
        card_groups_json=CARD_GROUPS_JSON,
        card_groups_md=CARD_GROUPS_MD,
        group_dissolution_json=GROUP_DISSOLUTION_JSON,
        group_dissolution_md=GROUP_DISSOLUTION_MD,
        safe_md_path=safe_md_path,
    )
    REVIEW_INBOX_STORE = ReviewInboxStore(
        root=ACTIVE_WRITE_ROOT,
        feedback_jsonl=FEEDBACK_JSONL,
        feedback_md=FEEDBACK_MD,
        confirmation_json=CONFIRMATION_JSON,
        confirmation_md=CONFIRMATION_MD,
    )
    INBOX_CLEANUP_STORE = InboxCleanupStore(
        store=INBOX_STORE,
        confirmation_json=CONFIRMATION_JSON,
        confirmation_md=CONFIRMATION_MD,
        feedback_jsonl=FEEDBACK_JSONL,
        feedback_md=FEEDBACK_MD,
        array_specs=(
            *MATERIAL_PIPELINE_STORE.cleanup_specs(InboxArraySpec),
            InboxArraySpec("dissolution", GROUP_DISSOLUTION_JSON, GROUP_DISSOLUTION_MD, "UI Card Group Dissolution Inbox", "本文件暂存 dashboard group 解散迁移审阅请求。", "暂无 pending dissolution task。"),
        ),
    )
    WORK_SESSION_UPLOAD_STORE = WorkSessionUploadStore(root=ACTIVE_WRITE_ROOT)
    ACTIVE_READ_BOUNDARY = PUBLIC_READ_BOUNDARY if public_starter else RuntimeReadBoundary.personal_vault(ROOT, ACTIVE_WRITE_ROOT)
    PREVIEW_FILE_SERVER, SOURCE_TREE_STORE, LOCAL_FILE_BRIDGE = ACTIVE_READ_BOUNDARY.runtime_services()
    CODEX_RUNNER = ACTIVE_READ_BOUNDARY.codex_runtime(
        public_starter=public_starter,
        write_root=ACTIVE_WRITE_ROOT,
        public_codex_root=PUBLIC_CODEX_ROOT,
        codex_factory=CodexRunner,
        command_runner_factory=CommandRunner,
        model_catalog_factory=ModelCatalog,
        log_jsonl=CODEX_RUNNER_JSONL,
        log_md=CODEX_RUNNER_MD,
        post_run_refresh=refresh_personal_vault_projection,
    )


def build_services() -> None:
    """Build runners, planner, public read copy and stores once, at start or first request; never at import."""
    global _services_built, COMMAND_RUNNER, MODEL_CATALOG, AUTO_UPDATE_RUNNER, EVOLUTION_PLANNER, RESEARCH_SCOUT_RUNNER
    global PUBLIC_READ_BOUNDARY, PUBLIC_CODEX_ROOT_OWNER, PUBLIC_CODEX_ROOT, REQUEST_SECURITY
    global PREVIEW_FILE_SERVER, SOURCE_TREE_STORE, LOCAL_FILE_BRIDGE
    with _SERVICES_LOCK:
        if _services_built:
            return
        _services_built = True  # set first, so a nested call on this thread returns at once
        COMMAND_RUNNER = CommandRunner(root=ROOT)
        MODEL_CATALOG = ModelCatalog(root=ROOT, command_runner=COMMAND_RUNNER)
        AUTO_UPDATE_RUNNER = AutoUpdateRunner(command_runner=COMMAND_RUNNER)
        EVOLUTION_PLANNER = EvolutionPlanner(root=ROOT, runtime_mode="public_starter")
        RESEARCH_SCOUT_RUNNER = ResearchScoutRunner(command_runner=COMMAND_RUNNER)
        PUBLIC_READ_BOUNDARY = RuntimeReadBoundary.public_starter(ROOT)
        PUBLIC_CODEX_ROOT_OWNER = tempfile.TemporaryDirectory(prefix="researchos-public-read-")
        PUBLIC_CODEX_ROOT = PUBLIC_READ_BOUNDARY.materialize(Path(PUBLIC_CODEX_ROOT_OWNER.name))
        PREVIEW_FILE_SERVER, SOURCE_TREE_STORE, LOCAL_FILE_BRIDGE = PUBLIC_READ_BOUNDARY.runtime_services()
        configure_runtime_write_root(ROOT, public_starter=True)
        REQUEST_SECURITY = LocalRequestSecurity.create()


def __getattr__(name: str) -> object:
    """Module attributes such as CODEX_RUNNER exist once the services are built (PEP 562)."""
    if name in SERVICE_NAMES:
        build_services()  # waits for a build running on another thread
    if name in globals():
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# The public demo accepts only these writes (uploads to the ignored session folder, registered maintenance,
# the copy-only runner and local opening); any other route, including a new one, is refused.
PUBLIC_DEMO_ALLOWED_POST_PATHS = frozenset(
    {"/work-session-upload", "/maintenance-action", "/codex-runner", "/open-local-file", "/reveal-local-file"}
)
PUBLIC_DEMO_UPLOAD_LIMIT = 1024 * 1024 * 1024  # the personal vault has no quota, only a notice past 1 GiB


def current_evolution_plan() -> dict[str, object]:
    return evolution_plan_view(EVOLUTION_PLANNER, ACTIVE_DASHBOARD_DATA == DEFAULT_DASHBOARD_DATA)


class ResearchOSDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Security-Policy", dashboard_content_security_policy(self.path))
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()
    def handle(self) -> None:
        build_services()
        super().handle()
    def do_GET(self) -> None:
        if not REQUEST_SECURITY.enforce_read(self):
            return
        parsed = urlparse(self.path)
        if parsed.path == "/LICENSE.md":
            self.serve_root_text_file(ROOT / "LICENSE.md")
            return
        route = GET_ROUTES.get(parsed.path)
        if route:
            route(self, parsed.query)
            return
        if parsed.path == "/data/researchos-dashboard.json" and ACTIVE_DASHBOARD_DATA != DEFAULT_DASHBOARD_DATA:
            self.serve_active_dashboard_data()
            return
        if PUBLIC_READ_BOUNDARY.public_dashboard_data_blocked(unquote(parsed.path), ACTIVE_DASHBOARD_DATA == DEFAULT_DASHBOARD_DATA):
            self.send_error(404, "Dashboard runtime data is not available in public mode")
            return
        if parsed.path.startswith("/corpus/") and parsed.path.lower().endswith(".pdf"):
            self.serve_pdf_file(unquote(parsed.path).lstrip("/"))
            return
        super().do_GET()
    def do_HEAD(self) -> None:
        if not REQUEST_SECURITY.enforce_read(self):
            return
        parsed = urlparse(self.path)
        if PUBLIC_READ_BOUNDARY.public_dashboard_data_blocked(unquote(parsed.path), ACTIVE_DASHBOARD_DATA == DEFAULT_DASHBOARD_DATA):
            self.send_error(404, "Dashboard runtime data is not available in public mode")
            return
        if parsed.path == "/LICENSE.md":
            self.serve_root_text_file(ROOT / "LICENSE.md", head_only=True)
            return
        if parsed.path == "/pdf":
            self.serve_pdf_preview(parsed.query, head_only=True)
            return
        if parsed.path.startswith("/corpus/") and parsed.path.lower().endswith(".pdf"):
            self.serve_pdf_file(unquote(parsed.path).lstrip("/"), head_only=True)
            return
        super().do_HEAD()
    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        handler, content_types = POST_ROUTES.get(parsed.path, (None, JSON_BODY))
        error = REQUEST_SECURITY.mutation_error(self.headers, self.server.server_address[1], content_types)
        if error:
            self.send_error(*error)
            return
        if ACTIVE_DASHBOARD_DATA == DEFAULT_DASHBOARD_DATA and parsed.path not in PUBLIC_DEMO_ALLOWED_POST_PATHS:
            self.send_json(
                {
                    "ok": False,
                    "error_type": "public_starter_writeback_blocked",
                    "message_en": "The public starter blocks durable writeback and local model execution. You can still copy a task packet or run registered public-safe maintenance actions.",
                    "message_zh": "公开版禁止持久写回和本地模型执行；你仍可复制任务包，或运行登记过的公开安全维护动作。",
                },
                status=403,
            )
            return
        if handler is None:
            self.send_error(404, "Endpoint not found")
            return
        if parsed.path in {"/work-session-upload", "/codex-runner", "/open-local-file", "/reveal-local-file"}:
            return handler(self)  # uploads and file reveals write nothing a rebuild reads; /codex-runner only queues a run, whose refresh takes the lock
        with self.server.mutation_lock:  # see ReusableTCPServer
            handler(self)

    def do_OPTIONS(self) -> None:
        self.send_error(403, "Cross-origin preflight rejected")

    def no_content(self, query: str) -> None:
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def session_config(self, query: str) -> None:
        public_demo = ACTIVE_DASHBOARD_DATA == DEFAULT_DASHBOARD_DATA
        self.send_json({
            **REQUEST_SECURITY.session_config(),
            "repository_kind": "public_starter",
            "runtime_mode": "public_starter" if public_demo else "personal_vault",
            "write_scope": "runtime_only" if public_demo else "personal_vault_only",
        })

    def serve_markdown_preview(self, query: str) -> None:
        PREVIEW_FILE_SERVER.serve_markdown_preview(self, query)

    def serve_active_dashboard_data(self) -> None:
        if not ACTIVE_DASHBOARD_DATA.exists():
            self.send_error(404, "Personal vault data not found. Run the personal-vault build first.")
            return
        data = ACTIVE_DASHBOARD_DATA.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_pdf_preview(self, query: str, head_only: bool = False) -> None:
        PREVIEW_FILE_SERVER.serve_pdf_preview(self, query, head_only=head_only)

    def serve_pdf_file(self, requested: str, head_only: bool = False) -> None:
        PREVIEW_FILE_SERVER.serve_pdf_file(self, requested, head_only=head_only)

    def serve_root_text_file(self, target: Path, head_only: bool = False) -> None:
        if not target.exists() or not target.is_file():
            self.send_error(404, "Root document not found")
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def json_object_body(self, maximum: int, label: str, allow_empty: bool = False) -> dict[str, object] | None:
        try:
            return read_json_object(self.headers, self.rfile, maximum=maximum, label=label, allow_empty=allow_empty)
        except RequestBodyError as exc:
            self.send_error(400, str(exc))
            return None

    def clear_inbox(self) -> None:
        if self.json_object_body(5000, "clear request", allow_empty=True) is None:
            return

        cleanup = INBOX_CLEANUP_STORE.clear_processed()
        rebuilt = bool(COMMAND_RUNNER.run(active_build_command(ACTIVE_DASHBOARD_DATA != DEFAULT_DASHBOARD_DATA), timeout=90).get("ok"))
        self.send_json({"ok": True, **cleanup, "rebuilt": rebuilt})

    def save_feedback(self) -> None:
        payload = self.json_object_body(20000, "feedback")
        if payload is None:
            return

        try:
            record = REVIEW_INBOX_STORE.save_feedback(payload)
        except ReviewInboxValidationError as exc:
            self.send_error(400, str(exc))
            return

        self.send_json({"ok": True, "record": record})

    def withdraw_confirmation(self) -> None:
        payload = self.json_object_body(5000, "confirmation withdraw")
        if payload is None:
            return

        try:
            record = REVIEW_INBOX_STORE.withdraw_confirmation(payload)
        except ReviewInboxValidationError as exc:
            self.send_error(400, str(exc))
            return
        self.send_json({"ok": True, "record": record})

    def save_card_groups(self) -> None:
        payload = self.json_object_body(300000, "card groups")
        if payload is None:
            return
        groups = payload.get("groups", [])
        if not isinstance(groups, list):
            self.send_error(400, "Invalid groups")
            return
        self.send_json(CARD_GROUP_STORE.save_groups(groups))

    def save_group_dissolutions(self) -> None:
        payload = self.json_object_body(160000, "group dissolution")
        if payload is None:
            return
        items = payload.get("items", [])
        if not isinstance(items, list):
            self.send_error(400, "Invalid dissolution items")
            return
        self.send_json(CARD_GROUP_STORE.save_dissolutions(items))

    def save_material_pipeline_candidate(self, route: str) -> None:
        spec = MATERIAL_PIPELINE_STORE.route_specs[route]
        payload = self.json_object_body(int(spec["limit"]), str(spec["label"]))
        if payload is None:
            return
        items = payload.get("items", [])
        if not isinstance(items, list):
            self.send_error(400, "Invalid items")
            return
        self.send_json(MATERIAL_PIPELINE_STORE.save_candidate(str(spec["candidate_type"]), items))

    def send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def source_tree(self, query: str) -> None:
        params = parse_qs(query)
        try:
            self.send_json(SOURCE_TREE_STORE.tree(params.get("path", [""])[0]))
        except SourceTreeError as exc:
            self.send_error(404, str(exc))

    def source_info(self, query: str) -> None:
        params = parse_qs(query)
        try:
            self.send_json(SOURCE_TREE_STORE.info(params.get("path", [""])[0]))
        except SourceTreeError as exc:
            self.send_error(404, str(exc))

    def local_file_payload(self) -> dict[str, object] | None:
        payload = self.json_object_body(5000, "local file request")
        if payload is None:
            return None
        if not isinstance(payload, dict) or not isinstance(payload.get("path", ""), str):
            self.send_error(400, "Invalid local file path")
            return None
        return payload

    def open_local_file(self) -> None:
        payload = self.local_file_payload()
        if payload is None:
            return
        try:
            result = LOCAL_FILE_BRIDGE.open_file(payload.get("path", ""))
        except SourceTreeError as exc:
            self.send_error(404, str(exc))
            return
        self.send_json(result, status=200 if result.get("ok") else 500)

    def reveal_local_file(self) -> None:
        payload = self.local_file_payload()
        if payload is None:
            return
        try:
            result = LOCAL_FILE_BRIDGE.reveal_file(payload.get("path", ""))
        except SourceTreeError as exc:
            self.send_error(404, str(exc))
            return
        self.send_json(result, status=200 if result.get("ok") else 500)

    def auto_update(self) -> None:
        request = self.json_object_body(5000, "evolution plan confirmation")
        if request is None:
            return
        plan = current_evolution_plan()
        plan_id = str(request.get("plan_id") or "")
        if not plan.get("execution_allowed") or not EVOLUTION_PLANNER.confirmed(plan, plan_id):
            self.send_json(
                {
                    "ok": False,
                    "confirmation_required": True,
                    "message": "Evolution plan changed or execution is unavailable; review the current plan.",
                    "plan": plan,
                    "steps": [],
                }
            )
            return
        step_ids = list(plan.get("auto_eligible_step_ids", []))
        payload = AUTO_UPDATE_RUNNER.run(step_ids)
        payload["plan"] = plan
        payload["pending_manual_step_ids"] = list(plan.get("manual_step_ids", []))
        if payload.get("ok"):
            payload["checkpoint"] = EVOLUTION_PLANNER.mark_applied(plan, payload)
        self.send_json(payload, status=200 if payload.get("ok") else 500)

    def run_maintenance_action(self) -> None:
        request = self.json_object_body(2000, "maintenance action")
        if request is None:
            return
        runtime_mode = "public_starter" if ACTIVE_DASHBOARD_DATA == DEFAULT_DASHBOARD_DATA else "personal_vault"
        payload, status = maintenance_action_response(request, AUTO_UPDATE_RUNNER, runtime_mode=runtime_mode)
        self.send_json(payload, status=status)

    def evolution_plan(self, query: str) -> None:
        self.send_json(current_evolution_plan())

    def evolution_decision(self) -> None:
        request = self.json_object_body(5000, "manual evolution decision")
        if request is None:
            return
        try:
            checkpoint = EVOLUTION_PLANNER.decide_manual(
                str(request.get("plan_id") or ""),
                str(request.get("decision") or ""),
            )
        except ValueError as error:
            self.send_json({"ok": False, "message": str(error), "plan": current_evolution_plan()}, status=200)
            return
        self.send_json({"ok": True, "decision": checkpoint.get("decision"), "checkpoint": checkpoint, "plan": current_evolution_plan()})

    def research_scout(self) -> None:
        request = self.json_object_body(20000, "research scout request")
        if request is None:
            return
        raw = json.dumps(request, ensure_ascii=False)
        payload, status = RESEARCH_SCOUT_RUNNER.run(raw)
        self.send_json(payload, status=status)

    def codex_runner_status(self, query: str) -> None:
        params = parse_qs(query)
        try:
            limit = int((params.get("limit") or ["20"])[0] or "20")
        except ValueError:
            limit = 20
        self.send_json(CODEX_RUNNER.status(
            limit=limit, client_request_id=(params.get("client_request_id") or [""])[0][:160],
            idempotency_key=(params.get("idempotency_key") or [""])[0][:80]))

    def provider_status(self, query: str) -> None:
        params = parse_qs(query)
        provider = (params.get("provider") or [""])[0] or None
        default_public_starter = ACTIVE_DASHBOARD_DATA == DEFAULT_DASHBOARD_DATA
        requested_public_starter = (params.get("public_starter") or [str(default_public_starter)])[0].lower() in {"1", "true", "yes"}
        public_starter = default_public_starter or requested_public_starter
        status = CODEX_RUNNER.executor_provider_status(provider or "codex")
        self.send_json(public_provider_status(status, public_starter=public_starter))
    def model_catalog(self, query: str) -> None:
        params = parse_qs(query)
        public_starter = ACTIVE_DASHBOARD_DATA == DEFAULT_DASHBOARD_DATA or (
            (params.get("public_starter") or ["false"])[0].lower() in {"1", "true", "yes"}
        )
        refresh = (params.get("refresh") or ["false"])[0].lower() in {"1", "true", "yes"}
        self.send_json(MODEL_CATALOG.status(public_starter=public_starter, refresh=refresh))

    def codex_runner_submit(self) -> None:
        payload = self.json_object_body(CODEX_RUNNER_REQUEST_MAX_BYTES, "Codex runner request")
        if payload is None:
            return
        try:
            self.send_json(CODEX_RUNNER.submit(payload))
        except ValueError:
            self.send_json(failure_response({"error_type": "runtime_failure"}), status=400)

    def work_session_upload(self) -> None:
        try:
            filename, content_length = upload_request_metadata(self.headers)
            if ACTIVE_DASHBOARD_DATA == DEFAULT_DASHBOARD_DATA and content_length > PUBLIC_DEMO_UPLOAD_LIMIT:
                raise WorkSessionUploadError("The public demo accepts files up to 1 GiB", "upload_too_large")
            self.send_json(WORK_SESSION_UPLOAD_STORE.save_stream(filename, self.rfile, content_length))
        except WorkSessionUploadError as exc:
            status = 507 if exc.error_type == "storage_unavailable" else 400
            self.send_json({"error_type": exc.error_type, "message": str(exc), "ok": False}, status=status)
        except ValueError as exc:
            self.send_error(400, str(exc))


JSON_BODY = ("application/json",)
# Path -> handler(self, query). Every route passes REQUEST_SECURITY.enforce_read first; none is under /data/.
GET_ROUTES = {
    "/favicon.ico": ResearchOSDashboardHandler.no_content,
    "/session-config": ResearchOSDashboardHandler.session_config,
    "/preview": ResearchOSDashboardHandler.serve_markdown_preview,
    "/pdf": ResearchOSDashboardHandler.serve_pdf_preview,
    "/codex-runner": ResearchOSDashboardHandler.codex_runner_status,
    "/provider-status": ResearchOSDashboardHandler.provider_status,
    "/model-catalog": ResearchOSDashboardHandler.model_catalog,
    "/source-tree": ResearchOSDashboardHandler.source_tree,
    "/source-info": ResearchOSDashboardHandler.source_info,
    "/evolution-plan": ResearchOSDashboardHandler.evolution_plan,
}
# Path -> (handler(self), accepted request content types). Every route passes REQUEST_SECURITY.mutation_error
# with its content types, then the public demo allowlist (PUBLIC_DEMO_ALLOWED_POST_PATHS); an unknown path
# is checked as JSON and then refused or answered 404.
POST_ROUTES = {
    "/feedback": (ResearchOSDashboardHandler.save_feedback, JSON_BODY),
    "/confirmation-withdraw": (ResearchOSDashboardHandler.withdraw_confirmation, JSON_BODY),
    **{route: (lambda handler, route=route: handler.save_material_pipeline_candidate(route), JSON_BODY)
       for route in MaterialPipelineStore.route_specs},
    "/card-groups": (ResearchOSDashboardHandler.save_card_groups, JSON_BODY),
    "/group-dissolutions": (ResearchOSDashboardHandler.save_group_dissolutions, JSON_BODY),
    "/clear-inbox": (ResearchOSDashboardHandler.clear_inbox, JSON_BODY),
    "/auto-update": (ResearchOSDashboardHandler.auto_update, JSON_BODY),
    "/maintenance-action": (ResearchOSDashboardHandler.run_maintenance_action, JSON_BODY),
    "/evolution-decision": (ResearchOSDashboardHandler.evolution_decision, JSON_BODY),
    "/research-scout": (ResearchOSDashboardHandler.research_scout, JSON_BODY),
    "/codex-runner": (ResearchOSDashboardHandler.codex_runner_submit, JSON_BODY),
    "/work-session-upload": (ResearchOSDashboardHandler.work_session_upload, ("*/*",)),
    "/open-local-file": (ResearchOSDashboardHandler.open_local_file, JSON_BODY),
    "/reveal-local-file": (ResearchOSDashboardHandler.reveal_local_file, JSON_BODY),
}


def main() -> int:
    global ACTIVE_DASHBOARD_DATA, EVOLUTION_PLANNER
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=configured_dashboard_port(ROOT))
    parser.add_argument(
        "--data-file",
        default=str(DEFAULT_DASHBOARD_DATA.relative_to(ROOT)),
        help="Dashboard JSON to serve at /data/researchos-dashboard.json; must stay under dashboard/data/.",
    )
    args = parser.parse_args()

    candidate = (ROOT / args.data_file).resolve()
    # Fail closed: only the shipped demo projection or the git-ignored personal-vault projection is served.
    # A misspelled or missing file must not switch the server into the writable personal-vault mode.
    if candidate not in {DEFAULT_DASHBOARD_DATA, PERSONAL_VAULT_DASHBOARD_DATA}:
        raise SystemExit(f"--data-file must be {DEFAULT_DASHBOARD_DATA.relative_to(ROOT)} (public demo) "
                         f"or {PERSONAL_VAULT_DASHBOARD_DATA.relative_to(ROOT)} (personal vault)")
    if not candidate.is_file():
        raise SystemExit(f"{candidate.relative_to(ROOT)} does not exist; build it first "
                         "(python3 scripts/start_researchos.py --mode personal-vault builds the personal-vault projection)")
    ACTIVE_DASHBOARD_DATA = candidate
    runtime_mode = "public_starter" if ACTIVE_DASHBOARD_DATA == DEFAULT_DASHBOARD_DATA else "personal_vault"
    build_services()
    EVOLUTION_PLANNER = EvolutionPlanner(root=ROOT, runtime_mode=runtime_mode)
    personal_vault = ACTIVE_DASHBOARD_DATA != DEFAULT_DASHBOARD_DATA
    configure_runtime_write_root(PERSONAL_VAULT_ROOT if personal_vault else ROOT, public_starter=not personal_vault)

    WORK_SESSION_UPLOAD_STORE.cleanup_generated_temporaries()
    CODEX_RUNNER.compact_log()
    if not DASHBOARD.exists():
        raise SystemExit("dashboard/ does not exist. Run build_public_starter_data.py after creating dashboard files.")

    handler = ResearchOSDashboardHandler
    with ReusableTCPServer(("127.0.0.1", args.port), handler) as httpd:
        print(f"Serving ResearchOS dashboard at http://127.0.0.1:{args.port}/")
        print(f"Root: {DASHBOARD}")
        print(f"Data: {ACTIVE_DASHBOARD_DATA.relative_to(ROOT)}")
        import os

        os.chdir(DASHBOARD)
        # A plain `kill` (SIGTERM) skips interpreter cleanup and would leave the temporary
        # read copy behind; stop it the same way as Ctrl-C so the copy is removed.
        def stop(*_):
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, stop)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nResearchOS dashboard stopped.")
        finally:
            PUBLIC_CODEX_ROOT_OWNER.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
