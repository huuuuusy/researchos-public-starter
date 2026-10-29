from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_data.plugin_lifecycle import (  # noqa: E402
    PluginLifecycleError,
    apply_action,
    catalog,
)


class PluginLifecycleTest(unittest.TestCase):
    def fixture(self) -> tempfile.TemporaryDirectory[str]:
        context = tempfile.TemporaryDirectory()
        root = Path(context.name)
        source = root / "config/extensions/method-comparison.example.json"
        source.parent.mkdir(parents=True)
        guide = root / "guide.md"
        guide.write_text("---\nsensitivity: public\n---\n# Guide\n", encoding="utf-8")
        manifest = {
            "schema_id": "researchos-task-extension-v1",
            "core_api_version": "1",
            "id": "method_comparison",
            "version": "1.0.0",
            "enabled": False,
            "available_in": ["private"],
            "public_safe": False,
            "sensitivity_default": "local_only",
            "authority": {
                "source": "Selected sources remain authoritative.",
                "candidate": "Results remain candidate-only.",
                "confirmation": "Human confirmation is required.",
                "save_target": "Use Review.",
                "requires_human_confirmation": True,
                "writeback_route": "review",
                "storage_owner": "researchos_core",
            },
            "task": {
                "aliases": ["compare_methods"],
                "workspace": "agent",
                "result_modes": ["answer"],
                "default_result_mode": "answer",
                "budget": "quick/standard/evidence",
                "read": {"quick": ["guide.md"], "standard": ["guide.md"], "evidence": ["guide.md"]},
                "locales": {
                    "en": {"name": "Compare methods", "goal": "Compare.", "user_input_hint": "Choose sources.", "output": "Comparison.", "next_steps": ["Choose sources."]},
                    "zh-CN": {"name": "研究方法对比", "goal": "比较。", "user_input_hint": "选择来源。", "output": "对比。", "next_steps": ["选择来源。"]},
                },
            },
        }
        source.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        return context

    def test_install_disable_enable_and_uninstall_are_reversible(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            self.assertFalse(catalog(root)[0]["installed"])
            installed = apply_action(root, "method_comparison", "install")
            self.assertTrue(installed["enabled"])
            disabled = apply_action(root, "method_comparison", "disable", rebuild=False)
            self.assertFalse(disabled["enabled"])
            enabled = apply_action(root, "method_comparison", "enable", rebuild=False)
            self.assertTrue(enabled["enabled"])
            removed = apply_action(root, "method_comparison", "uninstall", rebuild=False)
            self.assertFalse(removed["installed"])

    def test_local_customization_is_never_overwritten_or_deleted(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            apply_action(root, "method_comparison", "install", rebuild=False)
            local = root / "config/extensions.local/method-comparison.json"
            value = json.loads(local.read_text(encoding="utf-8"))
            value["version"] = "9.9.9"
            local.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(PluginLifecycleError, "differs from the bundled example"):
                apply_action(root, "method_comparison", "uninstall", rebuild=False)
            self.assertTrue(local.is_file())

    def test_unknown_or_unsafe_plugin_id_fails_closed(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(PluginLifecycleError, "lower_snake_case"):
                apply_action(root, "../method", "install", rebuild=False)
            with self.assertRaisesRegex(PluginLifecycleError, "unknown bundled"):
                apply_action(root, "missing_plugin", "install", rebuild=False)

    def test_failed_rebuild_restores_manifest_and_projection(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            builder = root / "scripts/build_dashboard_data.py"
            builder.parent.mkdir(parents=True)
            builder.write_text("# fixture\n", encoding="utf-8")
            failure = __import__("subprocess").CalledProcessError(1, ["builder"])
            with mock.patch(
                "researchos_data.plugin_lifecycle.subprocess.run",
                side_effect=[failure, mock.Mock(returncode=0)],
            ) as run:
                with self.assertRaises(__import__("subprocess").CalledProcessError):
                    apply_action(root, "method_comparison", "install", rebuild=True)
            self.assertFalse((root / "config/extensions.local/method-comparison.json").exists())
            self.assertEqual(run.call_count, 2, "rollback must also rebuild the previous projection")

    def test_upgrade_preserves_disabled_state_and_old_version_can_be_removed(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            apply_action(root, "method_comparison", "install", rebuild=False)
            apply_action(root, "method_comparison", "disable", rebuild=False)
            source = root / "config/extensions/method-comparison.example.json"
            data = json.loads(source.read_text()); data["version"] = "1.0.1"
            source.write_text(json.dumps(data))
            self.assertTrue(catalog(root)[0]["managed"])
            self.assertTrue(catalog(root)[0]["upgrade_available"])
            result = apply_action(root, "method_comparison", "upgrade", rebuild=False)
            self.assertEqual(result["installed_version"], "1.0.1")
            self.assertFalse(result["enabled"])
            data["version"] = "1.0.2"; source.write_text(json.dumps(data))
            apply_action(root, "method_comparison", "enable", rebuild=False)
            self.assertEqual(catalog(root)[0]["installed_version"], "1.0.1")
            apply_action(root, "method_comparison", "uninstall", rebuild=False)
            baseline = root / "config/extensions.local/method-comparison.installed-baseline"
            self.assertFalse(baseline.exists())
            # An orphaned receipt must not poison a fresh install.
            baseline.write_text(json.dumps({"id": "old", "version": "0.0.0"}))
            self.assertTrue(apply_action(root, "method_comparison", "install", rebuild=False)["managed"])

    def test_failed_upgrade_restores_manifest_and_baseline(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            apply_action(root, "method_comparison", "install", rebuild=False)
            local = root / "config/extensions.local/method-comparison.json"
            baseline = local.with_suffix(".installed-baseline")
            before = (local.read_bytes(), baseline.read_bytes())
            source = root / "config/extensions/method-comparison.example.json"
            data = json.loads(source.read_text()); data["version"] = "1.0.1"
            data["authority"]["requires_human_confirmation"] = False
            source.write_text(json.dumps(data))
            with self.assertRaises(PluginLifecycleError):
                apply_action(root, "method_comparison", "upgrade", rebuild=False)
            self.assertEqual((local.read_bytes(), baseline.read_bytes()), before)

    def test_legacy_unknown_baseline_and_customized_install_stay_protected(self) -> None:
        with self.fixture() as directory:
            root = Path(directory)
            apply_action(root, "method_comparison", "install", rebuild=False)
            local = root / "config/extensions.local/method-comparison.json"
            baseline = local.with_suffix(".installed-baseline")
            baseline.unlink()
            # Matching legacy install acquires a baseline without replacing content.
            apply_action(root, "method_comparison", "disable", rebuild=False)
            self.assertTrue(baseline.exists())
            value = json.loads(local.read_text()); value["task"]["locales"]["en"]["goal"] = "My custom goal"
            local.write_text(json.dumps(value)); before = local.read_bytes()
            for action in ("install", "upgrade", "disable", "enable", "uninstall"):
                with self.assertRaises(PluginLifecycleError):
                    apply_action(root, "method_comparison", action, rebuild=False)
                self.assertEqual(local.read_bytes(), before)
            baseline.unlink()
            with self.assertRaises(PluginLifecycleError):
                apply_action(root, "method_comparison", "upgrade", rebuild=False)

    def test_headless_result_remove_resume_and_reinstall_chain(self) -> None:
        import contextlib
        import io
        import subprocess
        import plan_context

        def command(*args):
            stdout = io.StringIO()
            with mock.patch.object(sys, "argv", ["plan_context.py", *args]), contextlib.redirect_stdout(stdout):
                plan_context.main()
            return json.loads(stdout.getvalue())

        with self.fixture() as directory:
            root = Path(directory)
            # Real bundled descriptor and documentation; only research sources are synthetic.
            source = root / "config/extensions/method-comparison.example.json"
            descriptor = json.loads((ROOT / "config/extensions/method-comparison.example.json").read_text())
            # Keep the version-change fixture stable as the bundled example evolves.
            descriptor["version"] = "1.0.0"
            groups = [descriptor["task"]["read"], *descriptor["task"].get("read_locales", {}).values()]
            for relative in {p for group in groups for tier in group.values() for p in tier}:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("---\nsensitivity: public\n---\n# Synthetic source\n")
            readme = descriptor["documentation"]["readme"]
            (root / readme).parent.mkdir(parents=True, exist_ok=True)
            (root / readme).write_bytes((ROOT / readme).read_bytes())
            source.write_text(json.dumps(descriptor))
            with mock.patch.object(plan_context, "ROOT", root):
                apply_action(root, "method_comparison", "install", rebuild=False)
                packet = command("method_comparison", "--lang", "en", "--headless-json")
                self.assertEqual(packet["extension"]["version"], "1.0.0")
                self.assertIn("--expected-extension-version 1.0.0", packet["extension"]["resume_command"])
                # Fake answer is a test result, never a provider or research-value claim.
                answer = "Synthetic A supports X; B is unresolved. Next: verify B."
                apply_action(root, "method_comparison", "uninstall", rebuild=False)
                with self.assertRaisesRegex(SystemExit, "cannot resume"):
                    command("method_comparison", "--expected-extension-version", "1.0.0", "--headless-json")
                # Headless result recovery uses the receipt CLI, never browser state.
                (root / "result.md").write_text(answer)
                (root / "task-plan.json").write_text(json.dumps(packet))
                def receipt_cli(*args, spec=None):
                    result = subprocess.run([sys.executable, str(ROOT / "scripts/receipt_cli.py"), "--root", str(root), *args], input=json.dumps(spec) if spec else None, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    return json.loads(result.stdout) if result.stdout.strip() else None
                context = receipt_cli("build-context", "--input", "-", "--output", "-", spec={
                    "task_id": "task:" + "a" * 64, "run_id": "synthetic-run", "runtime_scope": "public_starter",
                    "producer_kind": "cli", "producer_surface": "terminal",
                    "source_refs": [{"kind": "file", "ref": "result.md", "label": "Synthetic result"}],
                })
                receipt_cli("build-handoff", "--input", "-", "--output", "handoff.json", spec={
                    "context_receipt": context, "source": {"kind": "file", "ref": "result.md"}, "source_path": "result.md",
                    "last_judgment": {"state": "candidate", "text": answer},
                    "open_boundary": {"state": "recorded", "text": "Synthetic result, not research evidence"},
                    "next_safe_action": {"state": "recommended", "text": packet["extension"]["resume_command"]},
                    "forbidden_actions": {"state": "recorded", "items": ["No durable writeback"]},
                    "target_client": {"kind": "cli", "surface": "terminal"},
                })
                verified = receipt_cli("recheck-source", "--input", "handoff.json", "--source", "result.md")
                self.assertEqual(verified["source_freshness"], "matches_current_file")
                self.assertEqual((root / "result.md").read_text(), answer)
                self.assertEqual(json.loads((root / "task-plan.json").read_text())["extension"]["version"], "1.0.0")
                apply_action(root, "method_comparison", "install", rebuild=False)
                self.assertEqual(command("method_comparison", "--expected-extension-version", "1.0.0", "--headless-json")["extension"]["version"], "1.0.0")
                descriptor["version"] = "1.0.1"; source.write_text(json.dumps(descriptor))
                apply_action(root, "method_comparison", "upgrade", rebuild=False)
                with self.assertRaisesRegex(SystemExit, "version changed"):
                    command("method_comparison", "--expected-extension-version", "1.0.0", "--headless-json")
                self.assertEqual(command("method_comparison", "--headless-json")["extension"]["version"], "1.0.1")


if __name__ == "__main__":
    unittest.main()
