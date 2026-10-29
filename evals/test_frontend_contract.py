from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from researchos_data.frontend_manifest import (
    APP_SCRIPT,
    FRONTEND_CLIENT_PROFILE_ID,
    FRONTEND_SURFACE_SCOPES,
    frontend_client_shell_entry,
    frontend_logical_ownership,
    frontend_script_load_order,
)
from researchos_data.style_manifest import (
    STYLE_LAYER_IMPORTS,
    ordered_style_imports,
)


ROOT = Path(__file__).resolve().parents[1]


def contrast_ratio(foreground: str, background: str) -> float:
    def luminance(color: str) -> float:
        channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


class FrontendContractTest(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def dashboard_source_files(self) -> list[Path]:
        return sorted((ROOT / "dashboard" / "src").rglob("*.js"))

    def test_ci_runs_every_javascript_regression_suite(self) -> None:
        workflow = self.read(".github/workflows/validate.yml")

        self.assertIn("for file in evals/*.js; do", workflow)
        self.assertIn('node "$file"', workflow)

    def test_ci_dependency_updates_stay_enabled(self) -> None:
        dependabot = self.read(".github/dependabot.yml")

        self.assertEqual(dependabot.count("package-ecosystem:"), 1)
        self.assertIn('package-ecosystem: "github-actions"', dependabot)
        self.assertIn('directory: "/"', dependabot)
        self.assertIn('interval: "weekly"', dependabot)
        self.assertIn("open-pull-requests-limit: 5", dependabot)

    def test_ci_actions_are_immutable_and_checkout_does_not_persist_credentials(self) -> None:
        workflow = self.read(".github/workflows/validate.yml")
        action_revisions = re.findall(r"uses:\s+actions/[^@\s]+@([0-9a-f]+)", workflow)
        self.assertTrue(action_revisions, "workflow must use official GitHub actions")
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{40}", revision) for revision in action_revisions))
        self.assertEqual(
            workflow.count("uses: actions/checkout@"),
            workflow.count("persist-credentials: false"),
            "every checkout must discard its token after checkout",
        )
        self.assertIn("contents: read", workflow)

    def test_every_rendered_button_and_link_declares_action_semantics(self) -> None:
        allowed = {"direct", "preview-confirm", "handoff", "navigation"}
        missing: list[str] = []
        invalid: list[str] = []
        tag_pattern = re.compile(r"<(button|a)\b[^>]*>", re.DOTALL)
        kind_pattern = re.compile(r'data-action-kind="([^"]+)"')

        for source_path in [ROOT / "dashboard" / "index.html", ROOT / "dashboard" / "app.js", *self.dashboard_source_files()]:
            source = source_path.read_text(encoding="utf-8")
            for match in tag_pattern.finditer(source):
                tag = match.group(0)
                if "${actionKindAttr}" in tag:
                    continue
                kind_match = kind_pattern.search(tag)
                location = f"{source_path.relative_to(ROOT)}:{source.count(chr(10), 0, match.start()) + 1}"
                if not kind_match:
                    missing.append(location)
                    continue
                value = kind_match.group(1)
                if value not in allowed and "${" not in value:
                    invalid.append(f"{location}={value}")

        self.assertEqual(missing, [], f"action semantics missing from: {missing}")
        self.assertEqual(invalid, [], f"invalid action semantics: {invalid}")
        self.assertIn('button.dataset.actionKind = "direct"', self.read("dashboard/src/core/theme.js"))

    def test_startup_error_is_localized_and_recoverable(self) -> None:
        app = self.read("dashboard/app.js")
        error_page = self.read("dashboard/src/views/error-page.js")
        i18n = self.read("dashboard/src/core/i18n.js")
        shell_workbench = self.read("dashboard/src/services/workspace-shell-workbench.js")

        self.assertIn('id="mainContent"', error_page)
        self.assertIn('data-startup-error', error_page)
        self.assertIn('aria-live="assertive"', error_page)
        self.assertIn('data-dashboard-retry', error_page)
        self.assertIn('translate("error.body")', error_page)
        self.assertIn('translate("error.details")', error_page)
        self.assertIn('[data-dashboard-retry]', app)
        self.assertIn('focusElement(errorSurface)', shell_workbench)
        self.assertIn('"error.retry": "重新加载"', i18n)
        self.assertIn('"error.retry": "Reload"', i18n)

    def test_retired_composer_preferences_are_not_reactivated(self) -> None:
        app = self.read("dashboard/app.js")
        index = self.read("dashboard/index.html")
        self.assertNotIn("normalizeStoredComposerPreferences", app)
        self.assertNotIn('src="src/views/agent-composer.js', index)

    def test_model_and_reasoning_controls_stay_outside_dashboard(self) -> None:
        app = self.read("dashboard/app.js")
        index = self.read("dashboard/index.html")
        work = self.read("dashboard/src/views/work-session.js")
        inbox = self.read("dashboard/src/views/unified-inbox.js")
        self.assertNotIn('id="agentComposer"', index)
        self.assertNotIn("renderAgentComposer", app)
        self.assertNotIn("work-session-model-options", app)
        self.assertNotIn("renderModelSettings", work)
        self.assertNotIn("renderResponseModeControl", work)
        self.assertNotIn("data-work-session-model-select", work)
        self.assertNotIn('name="response_mode"', work)
        self.assertNotIn("data-unified-inbox-model", inbox)
        self.assertNotIn("data-unified-inbox-reasoning-effort", inbox)
        self.assertIn("ModelCatalogService.createController", app)
        self.assertIn("ModelCatalogController.payloadModel()", app)

    def test_empty_personal_vault_keeps_material_intake_reachable(self) -> None:
        view = self.read("dashboard/src/views/asset-overview.js")
        app = self.read("dashboard/app.js")
        material_plugin = self.read("dashboard/src/plugins/material-pipeline.js")
        material_manifest = self.read("config/plugins/material-pipeline.json")
        workbench = self.read("dashboard/src/services/asset-overview-workbench.js")
        material_workbench = self.read("dashboard/src/services/material-intake-workbench.js")

        self.assertIn("intakePanelHtml", view)
        self.assertIn('PluginRuntime.registerOwnedAdapter("material_pipeline", "material_pipeline_library_intake"', material_plugin)
        self.assertIn('"slot": "library"', material_manifest)
        self.assertNotIn("renderMaterialIntakePanel", app)
        self.assertNotIn("MaterialPipelinePlugin", app)
        self.assertIn("[data-asset-create-panel]", workbench)
        self.assertIn("[data-material-intake-form]", material_workbench)

    def test_personal_vault_completion_refreshes_derived_projection(self) -> None:
        app = self.read("dashboard/app.js")
        server = self.read("scripts/serve_dashboard.py")
        runner = self.read("scripts/researchos_server/codex_runner.py")
        runtime_boundary = self.read("scripts/researchos_server/runtime_read_boundary.py")

        self.assertIn('dashboardData?.runtime_mode === "personal_vault"', app)
        self.assertIn("dashboardData = await loadDashboard()", app)
        self.assertIn("post_run_refresh=refresh_personal_vault_projection", server)
        self.assertIn("post_run_refresh=None if public_starter else post_run_refresh", runtime_boundary)
        self.assertIn("if ok and direct_write_authorized and self.post_run_refresh:", runner)

    def test_library_context_pack_is_shell_primary_and_task_aware(self) -> None:
        app = self.read("dashboard/app.js")
        context_pack = self.read("dashboard/src/services/context-pack-projection.js")
        work_view = self.read("dashboard/src/views/work-session.js")
        assets_plugin = self.read("dashboard/src/plugins/research-assets.js")
        portfolio_plugin = self.read("dashboard/src/plugins/research-portfolio.js")
        self.assertIn('function currentContextPackProjection()', app)
        self.assertIn('host.insertAdjacentHTML("afterbegin", contextPackHtml)', self.read("dashboard/src/services/plugin-host.js"))
        self.assertIn('reason: "explicit_selection_required"', context_pack)
        self.assertIn('data-current-context-pack', work_view)
        self.assertIn('data-context-included', work_view)
        self.assertIn('data-context-excluded', work_view)
        self.assertIn('data-context-egress', work_view)
        self.assertIn('data-library-source-browser', assets_plugin)
        self.assertNotIn('data-library-project-overview-secondary', portfolio_plugin)
        self.assertIn('context.selectLibraryLens?.(itemId)', portfolio_plugin)

    def test_default_frontend_graph_loads_active_scripts_only(self) -> None:
        index = self.read("dashboard/index.html")
        loaded = [
            urlsplit(src).path
            for src in re.findall(r'<script\s+src="([^"]+)"', index)
        ]

        self.assertEqual(loaded[-1], APP_SCRIPT)
        self.assertEqual(set(loaded[:-1]), set(frontend_script_load_order()))
        self.assertEqual(len(loaded), len(set(loaded)))
        actual = {
            path.relative_to(ROOT / "dashboard").as_posix()
            for path in (ROOT / "dashboard" / "src").rglob("*.js")
        }
        self.assertEqual(actual, set(frontend_script_load_order()))

        # serve_dashboard.py sends Cache-Control: no-store, so no asset carries a ?v= cache query.
        self.assertNotIn("?v=", index)
        self.assertNotIn("?v=", self.read("dashboard/style.css"))

    def test_runtime_workspace_ids_are_only_compatibility_aliases(self) -> None:
        semantics = json.loads(self.read("09_templates/data_contracts/researchos-interaction-semantics-v1.json"))
        profile = semantics["client_profiles"]["profiles"][FRONTEND_CLIENT_PROFILE_ID]
        aliases = profile["surface_aliases"]
        workspace_semantics = {
            surface.get("legacy_id", ""): surface["id"]
            for surface in FRONTEND_SURFACE_SCOPES
            if surface.get("kind") == "workspace"
        }
        self.assertEqual(workspace_semantics, {key: aliases[key] for key in workspace_semantics})
        self.assertEqual(set(semantics["surfaces"]), {"now", "library", "work"})

    def test_profile_questions_and_auxiliary_surfaces_are_explicit(self) -> None:
        semantics = json.loads(self.read("09_templates/data_contracts/researchos-interaction-semantics-v1.json"))
        profile = semantics["client_profiles"]["profiles"][FRONTEND_CLIENT_PROFILE_ID]
        workspaces = {
            surface["id"]: surface
            for surface in FRONTEND_SURFACE_SCOPES
            if surface.get("kind") == "workspace"
        }
        self.assertEqual(list(workspaces), profile["workspace_ids"])
        self.assertEqual(
            {surface_id: surface["primary_question"] for surface_id, surface in workspaces.items()},
            {surface_id: semantics["surfaces"][surface_id]["question"] for surface_id in profile["workspace_ids"]},
        )
        auxiliaries = {
            surface["id"]: (surface["kind"], surface["parent_surface"])
            for surface in FRONTEND_SURFACE_SCOPES
            if surface.get("kind") != "workspace"
        }
        self.assertEqual(auxiliaries, {
            "utility": ("slot_host", "library"),
            "preview": ("aside", "any"),
        })
        self.assertTrue(all(not surface.get("tab_i18n") and not surface.get("primary_question")
                            for surface in FRONTEND_SURFACE_SCOPES if surface.get("kind") != "workspace"))

    def test_dashboard_is_an_optional_client_shell_not_a_capability_plugin(self) -> None:
        contract = json.loads(self.read("09_templates/data_contracts/researchos-client-shell-v1.json"))
        identity = contract["identity"]
        self.assertEqual(contract["version"], "researchos-client-shell-v1")
        self.assertEqual(identity["kind"], "optional_client")
        self.assertEqual(identity["role"], "application_shell_and_plugin_host")
        self.assertFalse(identity["capability_plugin"])
        self.assertIn(FRONTEND_CLIENT_PROFILE_ID, contract["supported_profiles"])
        self.assertEqual(contract["surface_catalog"], ["now", "library"])
        self.assertEqual(contract["plugin_host"]["guest_protocol"], "researchos-plugin-v1")
        self.assertEqual(contract["plugin_host"]["disable_semantics"], "capability_reduction_only")
        self.assertIn("profile_defined_surface_routing", contract["owns"])
        self.assertIn("failure_containment", contract["owns"])
        for forbidden_owner in ["canonical_authority", "domain_mutation", "task_catalog", "admission_decision"]:
            self.assertIn(forbidden_owner, contract["must_not_own"])

        shell_entry = frontend_client_shell_entry()
        self.assertEqual(shell_entry["owner_path"], APP_SCRIPT)
        self.assertEqual(shell_entry["logical_owner"], "application_shell")
        self.assertEqual(shell_entry["deployment_role"], "optional_application_shell")
        ownership = {entry["owner_path"]: entry for entry in frontend_logical_ownership()}
        plugin_entries = [entry for entry in ownership.values() if entry["owner_kind"] == "plugin"]
        self.assertTrue(plugin_entries)
        self.assertTrue(all(entry["deployment_role"] == "capability_guest" for entry in plugin_entries))

        for relative in contract["headless_closure"]["required_entrypoints"]:
            target = ROOT / relative
            self.assertTrue(target.is_file(), f"headless entrypoint missing: {relative}")
            imports = "\n".join(
                line.strip()
                for line in target.read_text(encoding="utf-8").splitlines()
                if line.lstrip().startswith(("from ", "import "))
            )
            self.assertNotIn("dashboard", imports.lower(), f"headless entrypoint must not import Dashboard: {relative}")

        self.assertEqual(contract["public_runtime"], {"execution": "copy_only", "canonical_write": False})

    def test_default_style_graph_loads_active_styles_only(self) -> None:
        style = self.read("dashboard/style.css")
        preview_markdown = self.read("dashboard/styles/preview/markdown.css")

        self.assertEqual(
            re.findall(r'@import url\("[^"]+"\) layer\([^)]+\);', style),
            list(ordered_style_imports()),
        )
        actual = {
            f"./{path.relative_to(ROOT / 'dashboard').as_posix()}"
            for path in (ROOT / "dashboard" / "styles").rglob("*.css")
        }
        self.assertEqual(actual, {entry["path"] for entry in STYLE_LAYER_IMPORTS})
        self.assertIn(".markdown-body td .md-source-link", preview_markdown)
        self.assertIn(".markdown-body td .inline-preview-button", preview_markdown)
        self.assertRegex(
            preview_markdown,
            r"\.markdown-body td \.md-source-link,\s*\.markdown-body td \.inline-preview-button\s*\{[^}]*border-radius:\s*0;[^}]*box-shadow:\s*none;",
        )

    def test_home_onboarding_and_identity_anchors_stay_wired(self) -> None:
        view = self.read("dashboard/src/views/home-command-center.js")
        app = self.read("dashboard/app.js")
        index = self.read("dashboard/index.html")

        self.assertIn("function renderNowHtml", view)
        self.assertIn('data-plugin-slot-host="workbench"', view)
        self.assertNotIn("function renderNextHtml", view)
        self.assertNotIn('data-plugin-slot-host="processing"', view)
        now_chunk = view[view.index("function renderNowHtml"):view.index("global.ResearchOSHomeCommandCenterView")]
        self.assertNotIn('id="todayWorkSession"', now_chunk)
        self.assertIn("HomeCommandCenterView.renderNowHtml", app)
        self.assertNotIn("renderPluginProcessingSlots", app)
        self.assertNotIn("HomeCommandCenterController", app)
        self.assertNotIn('id="todayProcessing"', index)
        self.assertNotIn('workspace-tab-next', index)
        self.assertIn('work-surface-panel', index)
        self.assertIn('id="workSessionSurface"', index)
        self.assertNotIn("today-review-drawer", index)
        self.assertIn('id="languageSelect" data-i18n-aria-label="controls.language"', index)

    def test_asset_group_cards_recent_runs_and_inbox_composition_stay_wired(self) -> None:
        model = self.read("dashboard/src/services/asset-overview-model.js")
        app = self.read("dashboard/app.js")
        plugin = self.read("dashboard/src/plugins/research-assets.js")
        inbox = self.read("dashboard/src/views/unified-inbox.js")

        for token in (
            "recentRunPathSet",
            "assetCardDateFields",
            "String(doc.type",
            '"relationship_pattern"',
            '["group", translate("assetsBoxGroup"), translate("assetsBoxGroupRule")]',
            "previewDocuments = []",
            "recentRuns = []",
            "researcher_relation_label",
        ):
            self.assertIn(token, model)
        self.assertIn('PluginRuntime.registerOwnedAdapter("research_assets", "research_assets_library"', plugin)
        self.assertIn("renderPluginLibrarySlots(dashboardData)", app)
        self.assertIn('PluginRuntime.registerSurfaceDependency("work", "relatedCompositionCards"', plugin)
        review_workbench = self.read("dashboard/src/services/unified-inbox-workbench.js")
        self.assertIn('surface: "work"', review_workbench)
        self.assertIn("context: app.pluginContext()", review_workbench)
        self.assertIn("pluginContext: () => pluginHost.runtimeContext()", app)
        self.assertNotIn("pluginContext()", app)
        self.assertNotIn("relatedCompositionCardsForBasket", app)
        self.assertIn("relatedCompositionCards", inbox)

    def test_runner_defaults_language_and_handoff_contracts(self) -> None:
        app = self.read("dashboard/app.js")
        inbox = self.read("dashboard/src/views/unified-inbox.js")
        model_catalog = self.read("dashboard/src/services/model-catalog.js")

        self.assertIn("ModelCatalogService.createController", app)
        self.assertIn("ModelCatalogController.payloadModel()", app)
        self.assertNotIn("ModelCatalogController.selectModel(value)", app)
        self.assertNotIn('work-session-model-options', app)
        self.assertIn('"max", "ultra"', model_catalog)
        self.assertIn('storageKey("reasoning", runtimeMode)', model_catalog)
        self.assertIn("storage?.removeItem(LEGACY_TIER_KEY)", model_catalog)
        self.assertNotIn("selectedCodexRunnerTier", app)
        self.assertNotIn("selectedCodexRunnerReasoning", app)
        self.assertNotIn("refreshSecretaryAgentDraftForLanguage(previousLang, lang)", app)
        self.assertNotIn("function secretaryTaskDraftForLanguage", app)
        self.assertIn("templateLanguage: () => lang || activeTemplateLanguage()", app)
        self.assertIn("function activeTemplateLanguage", app)
        self.assertIn("language: lang", app)
        self.assertNotIn("data-unified-inbox-model", inbox)
        self.assertNotIn("data-unified-inbox-reasoning-effort", inbox)

    def test_inactive_language_prompt_templates_stay_frozen(self) -> None:
        app = self.read("dashboard/app.js")
        index = self.read("dashboard/index.html")
        render_plan = self.read("dashboard/src/services/dashboard-render-plan.js")

        self.assertIn("activeTemplateLanguage", app)
        self.assertIn("activeTemplateLanguage", render_plan)
        self.assertNotIn("selectedBudgetChoiceForLanguage(templateLanguage)", app)
        self.assertNotIn("CONTEXT_BUDGET_CHOICES[templateLanguage]", app)
        self.assertNotIn("src/views/agent-composer.js", index)
        self.assertIn("templateLanguage: () => lang || activeTemplateLanguage()", app)
        for stale_lookup in (
            "tasks_i18n?.[lang]",
            "tasks_i18n?.[language]",
            "assistant_modes_i18n?.[lang]",
        ):
            self.assertNotIn(stale_lookup, app)
            self.assertNotIn(stale_lookup, render_plan)

    def test_local_mutations_and_direct_execution_have_visible_guards(self) -> None:
        index = self.read("dashboard/index.html")
        request_auth = self.read("dashboard/src/services/request-auth.js")
        storage_contract = self.read("dashboard/src/core/storage-contract.js")
        app = self.read("dashboard/app.js")
        inbox = self.read("dashboard/src/views/unified-inbox.js")

        self.assertLess(index.index("src/services/request-auth.js"), index.index('src="app.js'))
        self.assertIn('originalFetch("/session-config"', request_auth)
        self.assertIn('session.request_header || "X-ResearchOS-Session"', request_auth)
        self.assertIn('window.confirm(confirmation)', app)
        self.assertIn("function executionRuntime", app)
        self.assertIn("ActionContract.runtimeCapabilities", app)
        self.assertIn("RuntimeProfileProjection.normalize(codexRunnerProviderStatus?.runtime_profile)", app)
        self.assertIn('profile.verification_state === "local_probe_passed"', app)
        self.assertIn("codexRunnerProviderStatus?.execution_available === true", app)
        self.assertIn("ActionContract.executionRoute", app)
        self.assertNotIn('provider.execution_scope ||', app)
        self.assertNotIn('provider.provider_mode ||', app)
        self.assertIn("workspaceWriteAvailable", app)
        self.assertIn('executionRoute.mode !== "registered_runner"', app)
        self.assertIn("codexRunnerEnabled", inbox)
        self.assertIn("function ensureRuntimeStorageBoundary", storage_contract)
        self.assertIn('mode !== "public_starter"', storage_contract)
        self.assertIn("StorageContract.ensureRuntimeStorageBoundary?.(data.runtime_mode)", app)

    def test_public_copy_matches_copy_only_runtime(self) -> None:
        ui_copy = self.read("dashboard/src/core/ui-copy.js")
        i18n = self.read("dashboard/src/core/i18n.js")
        index = self.read("dashboard/index.html")
        # Edition-specific wording lives in the copy profile; t() reads its i18nOverrides before i18n.js.
        copy_profile = self.read("dashboard/src/core/ui-copy-profile.js")

        self.assertIn("不探测或启动本机 Codex", ui_copy)
        self.assertIn("neither probes nor starts local Codex", ui_copy)
        self.assertIn("只生成可复制任务包", ui_copy)
        self.assertIn("only creates a copyable task packet", ui_copy)
        self.assertIn('"sections.agentBox": "Agent 执行与交接"', i18n)
        self.assertIn("不接受任意命令", copy_profile)
        self.assertNotIn("复制维护命令", index)
        self.assertIn('<script src="src/services/maintenance-client.js"></script>', index)
        self.assertNotIn("公开版只允许本机 Codex 在只读沙箱中", ui_copy)
        self.assertNotIn("public starter allows local Codex", ui_copy)

    def test_mobile_preview_and_keyboard_accessibility_contracts(self) -> None:
        index = self.read("dashboard/index.html")
        i18n = self.read("dashboard/src/core/i18n.js")
        i18n_runtime = self.read("dashboard/src/core/i18n-runtime.js")
        base = self.read("dashboard/styles/base.css")
        preview = self.read("dashboard/styles/preview.css")
        inbox = self.read("dashboard/styles/views/unified-inbox.css")
        tokens = self.read("dashboard/styles/tokens.css")

        self.assertIn('href="#mainContent"', index)
        self.assertIn('id="mainContent"', index)
        self.assertIn('data-i18n="a11y.skipToMain"', index)
        self.assertIn('data-i18n-aria-label="a11y.workspaceNav"', index)
        self.assertIn('"a11y.skipToMain": "Skip to main content"', i18n)
        self.assertIn('"a11y.workspaceNav": "ResearchOS workspace"', i18n)
        self.assertIn('querySelectorAll("[data-i18n-aria-label]")', i18n_runtime)
        self.assertIn('querySelectorAll("[data-i18n-title]")', i18n_runtime)
        self.assertIn("prefers-reduced-motion: reduce", base)
        mobile_preview = preview.split("@media (max-width: 640px)", 1)[1]
        self.assertIn("position: static", mobile_preview)
        self.assertIn("position: static", mobile_preview)
        self.assertIn("width: auto", mobile_preview)
        self.assertIn("margin: 0 10px 18px auto", mobile_preview)
        self.assertNotIn("bottom: max(12px, env(safe-area-inset-bottom))", mobile_preview)
        for select_rule in re.findall(r"select[^{}]*\{([^}]*)\}", inbox):
            self.assertNotIn("outline: none", select_rule)
        for token in ("muted", "muted-soft"):
            colors = set(re.findall(rf"--{token}:\s*(#[0-9a-fA-F]{{6}})", tokens))
            self.assertTrue(colors, token)
            for color in colors:
                self.assertGreaterEqual(contrast_ratio(color, "#f2f2f7"), 4.5, token)
                self.assertGreaterEqual(contrast_ratio(color, "#ffffff"), 4.5, token)

    def test_css_custom_properties_are_declared_or_explicitly_dynamic(self) -> None:
        css_files = [ROOT / "dashboard" / "style.css", *(ROOT / "dashboard" / "styles").rglob("*.css")]
        sources = {path: path.read_text(encoding="utf-8") for path in css_files}
        definitions = {
            match.group(1)
            for source in sources.values()
            for match in re.finditer(r"(--[A-Za-z0-9_-]+)\s*:", source)
        }
        dynamic = {
            "--asset-card-order",
            "--asset-node-x",
            "--asset-node-y",
            "--confirm-progress",
        }
        missing: list[str] = []
        for path, source in sources.items():
            for match in re.finditer(r"var\(\s*(--[A-Za-z0-9_-]+)([^)]*)\)", source):
                name, suffix = match.groups()
                if name not in definitions and name not in dynamic and "," not in suffix:
                    missing.append(f"{path.relative_to(ROOT)}: {name}")
        self.assertEqual(missing, [])

    def test_now_and_library_workspace_labels_have_one_authoritative_copy_source(self) -> None:
        index = self.read("dashboard/index.html")
        i18n = self.read("dashboard/src/core/i18n.js")
        ui_copy = self.read("dashboard/src/core/ui-copy.js")

        self.assertIn('aria-label="现在">现在</button>', index)
        self.assertIn('aria-label="资料">资料</button>', index)
        self.assertNotIn('aria-label="推进">推进</button>', index)
        self.assertEqual(i18n.count('"workspace.now": "现在"'), 1)
        self.assertEqual(i18n.count('"workspace.now": "Now"'), 1)
        self.assertEqual(i18n.count('"workspace.work": "推进"'), 1)
        self.assertEqual(i18n.count('"workspace.work": "Work"'), 1)
        self.assertNotIn('"workspace.review":', i18n)
        self.assertNotIn('"workspace.agent":', ui_copy)

    def test_work_session_copy_owner_loads_before_core_catalog(self) -> None:
        index = self.read("dashboard/index.html")
        owner = self.read("dashboard/src/core/ui-copy-work-session.js")
        core = self.read("dashboard/src/core/ui-copy.js")
        self.assertLess(index.index("src/core/ui-copy-work-session.js"), index.index("src/core/ui-copy.js"))
        self.assertIn("ResearchOSUICopyWorkSession", owner)
        self.assertIn("data-researchos-ui-copy-work-session", owner)
        self.assertIn("window.ResearchOSUICopyWorkSession || {}", core)
        self.assertIn('workSessionProjectionRefreshFailed:', owner)

    def test_footer_license_is_served_in_file_and_http_modes(self) -> None:
        index = self.read("dashboard/index.html")
        server = self.read("scripts/serve_dashboard.py")
        launcher = self.read("scripts/start_researchos.py")

        self.assertIn('href="../LICENSE.md"', index)
        self.assertGreaterEqual(server.count('parsed.path == "/LICENSE.md"'), 2)
        self.assertIn('self.serve_root_text_file(ROOT / "LICENSE.md")', server)
        self.assertIn("except KeyboardInterrupt:", server)
        self.assertIn("def _run_server(command: list[str])", launcher)
        self.assertIn("except KeyboardInterrupt:", launcher)

    def test_static_dashboard_references_resolve(self) -> None:
        index = self.read("dashboard/index.html")
        missing: list[str] = []
        for match in re.finditer(r'(?:href|src)="([^"]+)"', index):
            reference = match.group(1)
            parsed = urlsplit(reference)
            if parsed.scheme or reference.startswith(("#", "mailto:", "tel:")):
                continue
            target = (ROOT / "dashboard" / parsed.path).resolve()
            if not target.exists():
                missing.append(reference)
        self.assertEqual([], missing)

    def test_public_dashboard_runtime_and_privacy_contract(self) -> None:
        data = json.loads(self.read("dashboard/data/researchos-dashboard.json"))
        provider = data.get("config", {}).get("provider", {})

        self.assertEqual("public_starter", data.get("runtime_mode"))
        self.assertEqual("copy_only", provider.get("provider_mode"))
        self.assertEqual("none", provider.get("execution_scope"))
        self.assertEqual("registered_actions", provider.get("maintenance_scope"))
        self.assertFalse(provider.get("execution_probe_required"))
        self.assertFalse(provider.get("allow_local_codex"))
        self.assertFalse(provider.get("allow_real_api"))

        selected = "\n".join(
            self.read(relative)
            for relative in (
                "dashboard/app.js",
                "dashboard/src/services/asset-overview-model.js",
                "dashboard/src/views/home-command-center.js",
            )
        ).lower()
        for forbidden in ("shiyu", "relation_to_shiyu", "00_identity/cards"):
            self.assertNotIn(forbidden, selected)

    def test_select_controls_have_accessible_names(self) -> None:
        failures: list[str] = []
        for path in self.dashboard_source_files():
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"<select\b[^>]*>", text):
                tag = match.group(0)
                if "aria-label=" not in tag:
                    failures.append(f"{path.relative_to(ROOT)}: {tag}")
        self.assertEqual([], failures)

    def test_context_prompt_uses_progressive_initial_pack(self) -> None:
        catalog = self.read("scripts/researchos_data/public_conversation_catalog.py")

        self.assertIn('"file_limit": 1', catalog)
        self.assertIn('"file_limit": 5', catalog)
        self.assertIn('"file_limit": 8', catalog)
        self.assertIn('"token_ceiling": 60_000', catalog)

    def test_current_user_docs_describe_result_centered_v1(self) -> None:
        current_docs = (
            "dashboard/README.md",
            "dashboard/README.zh.md",
            "docs/user-manual.en.md",
            "docs/user-manual.zh.md",
            "08_exports/public_starter/onboarding-step-by-step.md",
            "08_exports/public_starter/onboarding-step-by-step.zh.md",
        )
        for relative in current_docs:
            text = self.read(relative)
            self.assertTrue("Now" in text or "现在" in text, relative)
            self.assertTrue("Library" in text or "资料" in text, relative)
            self.assertTrue("Review" in text or "确认" in text, relative)
            self.assertRegex(
                text,
                r"(?i)visible (?:answer|result)|returned result|inline result|可见(?:回答|结果)|返回结果|结果闭环|任务包",
                relative,
            )
            self.assertTrue(any(label in text for label in ("Review", "确认", "Handoff", "交接")), relative)
            self.assertNotRegex(
                text,
                r"`Progress`|`Card Library`|`卡片库`|`Today Work`|`今日处理`",
                relative,
            )


if __name__ == "__main__":
    unittest.main()
