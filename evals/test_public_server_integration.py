from __future__ import annotations

import functools
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import serve_dashboard  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PublicServerIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        serve_dashboard.ACTIVE_DASHBOARD_DATA = serve_dashboard.DEFAULT_DASHBOARD_DATA
        handler = functools.partial(serve_dashboard.ResearchOSDashboardHandler, directory=str(serve_dashboard.DASHBOARD))
        cls.server = serve_dashboard.ReusableTCPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def get_json(self, path: str) -> dict[str, object]:
        with urllib.request.urlopen(self.base + path, timeout=5) as response:
            return json.load(response)

    def test_session_config_identifies_public_starter_runtime(self) -> None:
        session = self.get_json("/session-config")
        self.assertEqual("public_starter", session["repository_kind"])
        self.assertEqual("public_starter", session["runtime_mode"])
        self.assertEqual("runtime_only", session["write_scope"])
        self.assertEqual("X-ResearchOS-Session", session["request_header"])
        self.assertTrue(session["request_token"])
        self.assertEqual(serve_dashboard.PUBLIC_CODEX_ROOT.resolve(), serve_dashboard.CODEX_RUNNER.root)
        self.assertEqual("public_starter", serve_dashboard.CODEX_RUNNER.runtime_scope)
        self.assertNotEqual(ROOT.resolve(), serve_dashboard.CODEX_RUNNER.root)
        self.assertTrue((serve_dashboard.CODEX_RUNNER.root / "08_exports" / "public_starter").is_dir())
        self.assertFalse((serve_dashboard.CODEX_RUNNER.root / "personal_vault").exists())
        self.assertFalse((serve_dashboard.CODEX_RUNNER.root / "config").exists())
        self.assertFalse((serve_dashboard.CODEX_RUNNER.root / "06_active_context").exists())

    def test_a_burst_of_script_requests_is_served_without_resets(self) -> None:
        # The page loads about a hundred scripts at once; a short listen backlog reset some of them.
        assets = re.findall(r'(?:src|href)="([^"#:]+\.(?:js|css))"', (serve_dashboard.DASHBOARD / "index.html").read_text(encoding="utf-8"))

        def fetch(path: str) -> int:
            with urllib.request.urlopen(f"{self.base}/{path}", timeout=10) as response:
                response.read()
                return response.status

        with ThreadPoolExecutor(64) as pool:
            self.assertEqual([200] * len(assets) * 3, list(pool.map(fetch, assets * 3)))

    def test_unknown_provider_status_route_remains_copy_only(self) -> None:
        with patch("researchos_adapters.provider_config.get_provider_spec") as provider_lookup:
            result = self.get_json(
                "/provider-status?provider=not-registered&public_starter=false"
            )

        self.assertFalse(result["ok"])
        self.assertEqual("public_starter_copy_only", result["error_type"])
        self.assertEqual("not-registered", result["provider"])
        self.assertEqual("none", result["execution_scope"])
        provider_lookup.assert_not_called()

    def test_codex_runner_http_budget_accepts_max_nested_unicode_and_rejects_oversize(self) -> None:
        session = self.get_json("/session-config")
        headers = {
            "Content-Type": "application/json", "Origin": self.base,
            str(session["request_header"]): str(session["request_token"]),
        }
        instruction = "😀" * 65536
        task_intent = {
            "schema_id": "researchos-task-intent-v1", "input_trust": "untrusted",
            "goal": "Unicode boundary", "instruction": instruction, "client_request_id": "public-http-boundary",
            "client": {"kind": "dashboard", "surface": "work_session", "task_ref": "unicode-boundary"},
            "requested_result": {"mode": "answer"},
            "requested_profile": {
                "provider": "auto", "model": "auto", "reasoning_effort": "medium", "task_complexity": "standard",
            },
            "client_hints": {"recommended_reasoning_effort": "medium", "recommended_task_complexity": "standard"},
            "source_refs": [],
        }
        payload = {"prompt": instruction, "response_mode": "answer", "task_intent": task_intent}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.assertLess(len(body), serve_dashboard.CODEX_RUNNER_REQUEST_MAX_BYTES)
        runner = Mock()
        runner.submit.return_value = {"ok": False, "error_type": "public_starter_copy_only"}
        with patch.object(serve_dashboard, "CODEX_RUNNER", runner):
            request = urllib.request.Request(self.base + "/codex-runner", data=body, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=5) as response:
                result = json.load(response)
            oversized = b'{"prompt":"' + (b"x" * serve_dashboard.CODEX_RUNNER_REQUEST_MAX_BYTES) + b'"}'
            request = urllib.request.Request(self.base + "/codex-runner", data=oversized, headers=headers, method="POST")
            try:
                urllib.request.urlopen(request, timeout=5)
            except urllib.error.HTTPError as exc:
                self.assertEqual(400, exc.code)
            except urllib.error.URLError:
                pass
            else:
                self.fail("Oversized Codex runner request was accepted")
        self.assertEqual("public_starter_copy_only", result["error_type"])
        runner.submit.assert_called_once_with(payload)

    def test_browser_client_crosses_real_http_and_public_runner_stays_copy_only(self) -> None:
        session = self.get_json("/session-config")
        environment = {
            "PATH": os.environ.get("PATH", ""), "LANG": os.environ.get("LANG", "C.UTF-8"),
            "RESEARCHOS_TEST_BASE": self.base,
            "RESEARCHOS_TEST_HEADER": str(session["request_header"]),
            "RESEARCHOS_TEST_TOKEN": str(session["request_token"]),
            "RESEARCHOS_TEST_EXPECT": "copy_only",
        }
        completed = subprocess.run(
            ["node", str(ROOT / "evals/helpers/codex_runner_transport_client.js")],
            cwd=ROOT, env=environment, text=True, capture_output=True, timeout=15, check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)
        receipt = json.loads(completed.stdout.strip().splitlines()[-1])
        self.assertEqual({"ok": True, "mode": "copy_only", "post_count": 1}, receipt)
        self.assertFalse((serve_dashboard.CODEX_RUNNER.root / "06_active_context").exists())

    def test_session_config_distinguishes_personal_vault_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "personal_vault"
            local_projection = Path(directory) / "researchos-local.json"
            local_projection.write_text("{}\n", encoding="utf-8")
            try:
                serve_dashboard.configure_runtime_write_root(vault, public_starter=False)
                with patch.object(serve_dashboard, "ACTIVE_DASHBOARD_DATA", local_projection):
                    session = self.get_json("/session-config")
                    provider = self.get_json("/provider-status?public_starter=false")
            finally:
                serve_dashboard.configure_runtime_write_root(ROOT, public_starter=True)
        self.assertEqual("public_starter", session["repository_kind"])
        self.assertEqual("personal_vault", session["runtime_mode"])
        self.assertEqual("personal_vault_only", session["write_scope"])
        self.assertEqual("candidate_off", provider["runtime_profile"]["selector_state"])
        self.assertIn(provider["runtime_profile"]["verification_state"], {"local_probe_passed", "local_probe_failed"})
        serialized = json.dumps(provider, sort_keys=True)
        for forbidden in ("endpoint_ref", "credential_ref", "api_key_env", "budget_ref", "source_ref", "fix_en", "fix_zh"):
            self.assertNotIn(forbidden, serialized)

    def test_symlink_write_root_fails_before_resolution_without_mutating_runtime(self) -> None:
        original_root = serve_dashboard.ACTIVE_WRITE_ROOT
        original_runner = serve_dashboard.CODEX_RUNNER
        original_store = serve_dashboard.INBOX_STORE
        original_boundary = serve_dashboard.ACTIVE_READ_BOUNDARY
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "vault-target"
            target.mkdir()
            link = Path(directory) / "vault-link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "symbolic link"):
                serve_dashboard.configure_runtime_write_root(link, public_starter=False)
        self.assertEqual(original_root, serve_dashboard.ACTIVE_WRITE_ROOT)
        self.assertIs(original_runner, serve_dashboard.CODEX_RUNNER)
        self.assertIs(original_store, serve_dashboard.INBOX_STORE)
        self.assertIs(original_boundary, serve_dashboard.ACTIVE_READ_BOUNDARY)

    def test_personal_vault_binds_every_user_content_writer_and_codex_sandbox_to_vault(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "personal_vault"
            try:
                serve_dashboard.configure_runtime_write_root(vault, public_starter=False)
                self.assertEqual(vault.resolve(), serve_dashboard.ACTIVE_WRITE_ROOT)
                self.assertEqual(vault.resolve(), serve_dashboard.CODEX_RUNNER.root)
                self.assertFalse(serve_dashboard.CODEX_RUNNER.public_starter)
                self.assertEqual("personal_vault", serve_dashboard.CODEX_RUNNER.runtime_scope)
                self.assertEqual(serve_dashboard.PUBLIC_CODEX_ROOT.resolve(), serve_dashboard.CODEX_RUNNER.reference_root)
                self.assertNotEqual(ROOT.resolve(), serve_dashboard.CODEX_RUNNER.reference_root)
                self.assertFalse((serve_dashboard.CODEX_RUNNER.reference_root / "personal_vault").exists())
                self.assertFalse((serve_dashboard.CODEX_RUNNER.reference_root / "config").exists())
                self.assertFalse((serve_dashboard.CODEX_RUNNER.reference_root / "06_active_context").exists())
                self.assertTrue((serve_dashboard.CODEX_RUNNER.reference_root / "09_templates").is_dir())
                self.assertIs(serve_dashboard.refresh_personal_vault_projection, serve_dashboard.CODEX_RUNNER.post_run_refresh)
                self.assertEqual(vault.resolve(), serve_dashboard.INBOX_STORE.root)
                self.assertEqual(vault.resolve(), serve_dashboard.MATERIAL_PIPELINE_STORE.root)
                self.assertEqual(vault.resolve(), serve_dashboard.CARD_GROUP_STORE.root)
                self.assertEqual(vault.resolve(), serve_dashboard.REVIEW_INBOX_STORE.root)
                self.assertEqual(vault.resolve(), serve_dashboard.WORK_SESSION_UPLOAD_STORE.root)
                for path in (
                    serve_dashboard.FEEDBACK_JSONL,
                    serve_dashboard.CONFIRMATION_JSON,
                    serve_dashboard.CARD_GROUPS_JSON,
                    serve_dashboard.GROUP_DISSOLUTION_JSON,
                    serve_dashboard.INBOX_CLEANUP_ARCHIVE,
                    serve_dashboard.CODEX_RUNNER_JSONL,
                ):
                    path.resolve().relative_to(vault.resolve())
            finally:
                serve_dashboard.configure_runtime_write_root(ROOT, public_starter=True)

    def test_personal_vault_confirmation_withdraw_writes_only_below_vault(self) -> None:
        root_confirmation = ROOT / "06_active_context" / "ui-confirmation-decisions.json"
        root_before = digest(root_confirmation) if root_confirmation.exists() else ""
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "personal_vault"
            local_projection = Path(directory) / "researchos-local.json"
            local_projection.write_text("{}\n", encoding="utf-8")
            try:
                serve_dashboard.configure_runtime_write_root(vault, public_starter=False)
                with patch.object(serve_dashboard, "ACTIVE_DASHBOARD_DATA", local_projection):
                    session = self.get_json("/session-config")
                    headers = {
                        "Content-Type": "application/json",
                        "Origin": self.base,
                        str(session["request_header"]): str(session["request_token"]),
                    }
                    request = urllib.request.Request(
                        self.base + "/confirmation-withdraw",
                        data=b'{"decision_id":"vault-test"}',
                        headers=headers,
                        method="POST",
                    )
                    with urllib.request.urlopen(request, timeout=5) as response:
                        payload = json.load(response)
                self.assertTrue(payload["ok"])
                self.assertTrue((vault / "06_active_context" / "ui-confirmation-decisions.json").exists())
            finally:
                serve_dashboard.configure_runtime_write_root(ROOT, public_starter=True)
        root_after = digest(root_confirmation) if root_confirmation.exists() else ""
        self.assertEqual(root_before, root_after)
        self.assertNotIn("/confirmation", serve_dashboard.POST_ROUTES, "the confirmation submit route is retired")

    def test_public_starter_blocks_writeback_but_allows_registered_local_actions(self) -> None:
        tracked = sorted((ROOT / "06_active_context").glob("ui-*"))
        before = {path: digest(path) for path in tracked}
        session = self.get_json("/session-config")
        headers = {
            "Content-Type": "application/json",
            "Origin": self.base,
            str(session["request_header"]): str(session["request_token"]),
        }
        request = urllib.request.Request(
            self.base + "/material-intake-inbox",
            data=b'{"items": []}',
            headers=headers,
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as context:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(403, context.exception.code)
        self.assertEqual("public_starter_writeback_blocked", json.load(context.exception)["error_type"])
        self.assertEqual(before, {path: digest(path) for path in tracked})

        decision_request = urllib.request.Request(
            self.base + "/evolution-decision",
            data=b'{"plan_id":"manual-plan","decision":"rejected"}',
            headers=headers,
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as decision_context:
            urllib.request.urlopen(decision_request, timeout=5)
        self.assertEqual(403, decision_context.exception.code)
        self.assertEqual("public_starter_writeback_blocked", json.load(decision_context.exception)["error_type"])

        too_large = urllib.request.Request(self.base + "/work-session-upload", data=b"x", method="POST", headers={
            **headers, "Content-Type": "application/octet-stream", "X-ResearchOS-Filename": "big.pdf",
            "Content-Length": str(2 * 1024 * 1024 * 1024)})
        with self.assertRaises(urllib.error.HTTPError) as size_context:
            urllib.request.urlopen(too_large, timeout=5)
        self.assertEqual("upload_too_large", json.load(size_context.exception)["error_type"])

        # Writes are allowed by name: a route the public demo does not list is refused, even a new one.
        unlisted = urllib.request.Request(self.base + "/feedback", data=b"{}", headers=headers, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as unlisted_context:
            urllib.request.urlopen(unlisted, timeout=5)
        self.assertEqual(403, unlisted_context.exception.code)

        maintenance_request = urllib.request.Request(
            self.base + "/maintenance-action",
            data=b'{"action_id":"validate_agent_architecture"}',
            headers=headers,
            method="POST",
        )
        with patch.object(serve_dashboard, "AUTO_UPDATE_RUNNER") as runner:
            runner.run.return_value = {"ok": True, "steps": [{"id": "validate_agent_architecture", "ok": True}]}
            with urllib.request.urlopen(maintenance_request, timeout=5) as response:
                maintenance = json.load(response)
        self.assertTrue(maintenance["ok"])
        self.assertEqual("validate_agent_architecture", maintenance["action_id"])
        runner.run.assert_called_once_with(("validate_agent_architecture",))

        personal_projection_request = urllib.request.Request(
            self.base + "/maintenance-action",
            data=b'{"action_id":"build_personal_vault_data"}',
            headers=headers,
            method="POST",
        )
        with patch.object(serve_dashboard, "AUTO_UPDATE_RUNNER") as runner:
            with self.assertRaises(urllib.error.HTTPError) as runtime_context:
                urllib.request.urlopen(personal_projection_request, timeout=5)
        self.assertEqual(403, runtime_context.exception.code)
        self.assertEqual("maintenance_action_runtime_blocked", json.load(runtime_context.exception)["error_type"])
        runner.run.assert_not_called()

        arbitrary_request = urllib.request.Request(
            self.base + "/maintenance-action",
            data=b'{"action_id":"shell","command":"rm -rf /tmp/example"}',
            headers=headers,
            method="POST",
        )
        with patch.object(serve_dashboard, "AUTO_UPDATE_RUNNER") as runner:
            with self.assertRaises(urllib.error.HTTPError) as arbitrary_context:
                urllib.request.urlopen(arbitrary_request, timeout=5)
        self.assertEqual(400, arbitrary_context.exception.code)
        runner.run.assert_not_called()

        codex_request = urllib.request.Request(
            self.base + "/codex-runner",
            data=b'{"prompt":"Summarize the public case","task_mode":"read_only_analysis"}',
            headers=headers,
            method="POST",
        )
        with patch.object(serve_dashboard, "CODEX_RUNNER") as runner:
            runner.submit.return_value = {
                "ok": False,
                "error_type": "public_starter_copy_only",
                "message_en": "Copy the generated task packet into a private agent task (Claude Code, Codex or another file-aware client).",
            }
            with urllib.request.urlopen(codex_request, timeout=5) as response:
                submitted = json.load(response)
        self.assertFalse(submitted["ok"])
        self.assertEqual("public_starter_copy_only", submitted["error_type"])
        runner.submit.assert_called_once_with({"prompt": "Summarize the public case", "task_mode": "read_only_analysis"})

        with patch.object(type(serve_dashboard.CODEX_RUNNER), "codex_executable") as executable:
            provider = self.get_json("/provider-status?public_starter=false")
        executable.assert_not_called()
        self.assertEqual("codex", provider["provider"])
        self.assertEqual("none", provider["execution_scope"])
        self.assertIs(provider["execution_available"], False)
        self.assertEqual("public_starter_copy_only", provider["error_type"])
        self.assertEqual("copy_only", provider["runtime_profile"]["status"])
        self.assertEqual("candidate_off", provider["runtime_profile"]["selector_state"])
        with patch.object(serve_dashboard, "MODEL_CATALOG") as catalog_service:
            catalog_service.status.return_value = {
                "ok": False,
                "provider": "codex",
                "discovery": "public_copy_only",
                "models": [],
            }
            catalog = self.get_json("/model-catalog?public_starter=false&refresh=true")
        self.assertEqual("codex", catalog["provider"])
        self.assertEqual("public_copy_only", catalog["discovery"])
        catalog_service.status.assert_called_once_with(public_starter=True, refresh=True)
        runner = self.get_json("/codex-runner?limit=abc")
        self.assertEqual("", runner["log_path"])
        self.assertIn("execution_available", runner["provider_status"])

    def test_codex_runner_status_forwards_exact_reconciliation_key(self) -> None:
        runner = Mock()
        runner.status.return_value = {
            "ok": True, "runs": [], "count": 0,
            "reconciliation": {"state": "not_found", "client_request_id": "request-exact"},
        }
        with patch.object(serve_dashboard, "CODEX_RUNNER", runner):
            observed = self.get_json("/codex-runner?limit=2&client_request_id=request-exact")
        self.assertEqual("not_found", observed["reconciliation"]["state"])
        runner.status.assert_called_once_with(
            limit=2, client_request_id="request-exact", idempotency_key="")

    def test_importing_the_server_builds_no_service_and_routes_are_tables(self) -> None:
        code = "import sys; sys.path.insert(0, 'scripts'); import serve_dashboard; print(serve_dashboard._services_built)"
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual("False", result.stdout.strip(), "importing starts no runner and reads no store")
        non_json = {path for path, (_, types) in serve_dashboard.POST_ROUTES.items() if types != ("application/json",)}
        self.assertEqual({"/work-session-upload"}, non_json, "only the upload route accepts a non-JSON body")
        self.assertEqual(("*/*",), serve_dashboard.POST_ROUTES["/work-session-upload"][1])
        self.assertLessEqual(serve_dashboard.PUBLIC_DEMO_ALLOWED_POST_PATHS, set(serve_dashboard.POST_ROUTES))

    def test_concurrent_first_requests_wait_for_one_service_build(self) -> None:
        code = """
import json, sys, threading, time
sys.path.insert(0, "scripts")
import serve_dashboard as server
real, builds, errors = server.LocalRequestSecurity, [], []
class SlowSecurity:
    @staticmethod
    def create():
        builds.append(1)
        time.sleep(0.2)  # widen the window in which other threads arrive mid-build
        return real.create()
server.LocalRequestSecurity = SlowSecurity
barrier = threading.Barrier(8)
def first_request(index):
    barrier.wait()
    try:
        if index % 2:
            server.build_services()  # what handle() does
        server.REQUEST_SECURITY  # what a handler reads next
    except Exception as error:
        errors.append(repr(error))
threads = [threading.Thread(target=first_request, args=(index,)) for index in range(8)]
for thread in threads: thread.start()
for thread in threads: thread.join(10)
print(json.dumps({"builds": len(builds), "errors": errors, "alive": sum(thread.is_alive() for thread in threads)}))
"""
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=30, check=True)
        self.assertEqual({"builds": 1, "errors": [], "alive": 0}, json.loads(result.stdout.strip().splitlines()[-1]))

    def test_maintenance_runs_one_at_a_time(self) -> None:
        session = self.get_json("/session-config")
        headers = {"Content-Type": "application/json", "Origin": self.base,
                   str(session["request_header"]): str(session["request_token"])}
        active, peak, guard = [0], [0], threading.Lock()
        def slow_run(*_args, **_kwargs):
            with guard:
                active[0] += 1
                peak[0] = max(peak[0], active[0])
            threading.Event().wait(0.1)
            with guard:
                active[0] -= 1
            return {"ok": True, "steps": []}
        statuses: list[int] = []
        def post() -> None:
            request = urllib.request.Request(self.base + "/maintenance-action", headers=headers, method="POST",
                                             data=b'{"action_id":"validate_agent_architecture"}')
            with urllib.request.urlopen(request, timeout=10) as response:
                statuses.append(response.status)
        with patch.object(serve_dashboard, "AUTO_UPDATE_RUNNER") as runner:
            runner.run.side_effect = slow_run
            threads = [threading.Thread(target=post) for _ in range(4)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(15)
        self.assertEqual([200] * 4, statuses)
        self.assertEqual(1, peak[0], "two maintenance runs must not write the same generated files at once")

    def test_license_route_supports_get_and_head(self) -> None:
        with urllib.request.urlopen(self.base + "/favicon.ico", timeout=5) as response:
            self.assertEqual(204, response.status)
        with urllib.request.urlopen(self.base + "/LICENSE.md", timeout=5) as response:
            self.assertEqual(200, response.status)
            self.assertEqual("text/markdown", response.headers.get_content_type())
        request = urllib.request.Request(self.base + "/LICENSE.md", method="HEAD")
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertEqual(200, response.status)

    def test_reads_reject_forged_host_and_public_data_projection_leaks(self) -> None:
        forged = urllib.request.Request(self.base + "/source-tree", headers={"Host": "attacker.example"})
        with self.assertRaises(urllib.error.HTTPError) as host_context:
            urllib.request.urlopen(forged, timeout=5)
        self.assertEqual(403, host_context.exception.code)

        for path in ("/data/researchos-local.json", "/data/%2e%2e/data/researchos-local.json"):
            with self.subTest(path=path), self.assertRaises(urllib.error.HTTPError) as data_context:
                urllib.request.urlopen(self.base + path, timeout=5)
            self.assertEqual(404, data_context.exception.code)

    def test_binary_upload_streams_without_deleting_existing_session_material(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = serve_dashboard.WorkSessionUploadStore(root=root, working_copy_notice_bytes=1)
            store.upload_dir.mkdir(parents=True)
            existing = store.upload_dir / "existing.pdf"
            existing.write_bytes(b"keep")
            session = self.get_json("/session-config")
            headers = {
                "Content-Type": "application/x-ipynb+json",
                "Origin": self.base,
                "X-ResearchOS-Filename": urllib.parse.quote("实验分析.ipynb"),
                str(session["request_header"]): str(session["request_token"]),
            }
            request = urllib.request.Request(
                self.base + "/work-session-upload",
                data=b"streamed-pdf",
                headers=headers,
                method="POST",
            )
            with patch.object(serve_dashboard, "WORK_SESSION_UPLOAD_STORE", store):
                with urllib.request.urlopen(request, timeout=5) as response:
                    payload = json.load(response)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["name"], "实验分析.ipynb")
            self.assertTrue(str(payload["path"]).endswith(".ipynb"))
            self.assertFalse(payload["storage"]["auto_delete"])
            self.assertEqual("working_copies_large", payload["storage"]["notice_code"])
            self.assertTrue(existing.exists())

    def test_pdf_preview_allows_only_same_origin_embedding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.pdf").write_bytes(b"%PDF-test")
            with patch.object(serve_dashboard, "PREVIEW_FILE_SERVER", serve_dashboard.PreviewFileServer(root)):
                path = urllib.parse.quote("paper.pdf")
                with urllib.request.urlopen(self.base + f"/pdf?path={path}", timeout=5) as response:
                    self.assertEqual("application/pdf", response.headers.get_content_type())
                    self.assertIn("frame-ancestors 'self'", response.headers["Content-Security-Policy"])
        with urllib.request.urlopen(self.base + "/", timeout=5) as response:
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])

    def test_preview_routes_reject_traversal_absolute_and_private_corpus_paths(self) -> None:
        blocked = (
            "/preview?path=../README.md",
            "/preview?path=/tmp/outside.md",
            "/preview?path=corpus/private-note.md",
            "/preview?path=personal_vault/06_active_context/research-portfolio.md",
            "/preview?path=config/researchos.runtime.local.json",
            "/preview?path=06_active_context/work_state/runner-logs/private.md",
            "/pdf?path=../paper.pdf",
            "/pdf?path=/tmp/outside.pdf",
            "/pdf?path=corpus/private-paper.pdf",
            "/source-info?path=personal_vault",
            "/source-info?path=config",
            "/source-info?path=06_active_context/work_state",
        )
        for path in blocked:
            with self.subTest(path=path):
                with self.assertRaises(urllib.error.HTTPError) as context:
                    urllib.request.urlopen(self.base + path, timeout=5)
                self.assertEqual(404, context.exception.code)

        public_source = urllib.parse.quote("08_exports/public_starter/README.md")
        with urllib.request.urlopen(self.base + f"/preview?path={public_source}", timeout=5) as response:
            self.assertEqual(200, response.status)
        source_root = self.get_json("/source-tree")
        names = {child["name"] for child in source_root["node"]["children"]}
        self.assertIn("08_exports", names)
        self.assertIn("09_templates", names)
        self.assertNotIn("personal_vault", names)
        self.assertNotIn("config", names)
        self.assertNotIn("06_active_context", names)


if __name__ == "__main__":
    unittest.main()
