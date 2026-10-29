import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters.model_catalog import (  # noqa: E402
    ModelCatalog,
    clean_model_id,
    configured_codex_model,
    resolve_codex_executable,
    resolve_model_config,
)


class FakeCommandRunner:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def run(self, args, *, timeout, input_text, env=None):
        self.calls.append((args, timeout, input_text, env))
        return {
            "ok": True,
            "stdout": f"warning\n{json.dumps(self.payload)}",
        }


class ModelCatalogTest(unittest.TestCase):
    def test_discovers_and_sanitizes_codex_catalog(self):
        payload = {
            "models": [
                {
                    "slug": "gpt-5.5",
                    "display_name": "GPT-5.5",
                    "priority": 2,
                    "visibility": "list",
                    "supported_reasoning_levels": [{"effort": "low"}],
                },
                {
                    "slug": "gpt-5.6-sol",
                    "display_name": "GPT-5.6-Sol",
                    "priority": 1,
                    "visibility": "list",
                    "default_reasoning_level": "low",
                    "supported_reasoning_levels": [{"effort": "low"}, {"effort": "ultra"}],
                },
                {"slug": "hidden", "visibility": "hide"},
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex = root / "codex"
            codex.write_text("fixture", encoding="utf-8")
            runner = FakeCommandRunner(payload)
            result = ModelCatalog(root=root, command_runner=runner, codex_path=codex).status(refresh=True)

        self.assertTrue(result["ok"])
        self.assertEqual(result["recommended_model"], "gpt-5.6-sol")
        self.assertEqual([item["id"] for item in result["models"]], ["gpt-5.6-sol", "gpt-5.5"])
        self.assertEqual(result["models"][0]["reasoning_efforts"], ["low", "ultra"])
        self.assertEqual(runner.calls[0][0][-2:], ["debug", "models"])
        env = runner.calls[0][3]
        self.assertIsInstance(env, dict)
        self.assertTrue(set(env).issubset({"PATH", "HOME", "CODEX_HOME", "TMPDIR", "LANG", "TZ", "SSL_CERT_FILE", "SSL_CERT_DIR"} | {key for key in os.environ if key.startswith("LC_")}))

    def test_auto_uses_runtime_recommendation_and_manual_selection_is_pinned(self):
        catalog = {"recommended_model": "gpt-5.6-sol", "configured_default_model": "gpt-5.5"}
        automatic = resolve_model_config("auto", "auto", "standard", catalog)
        manual = resolve_model_config("my-company/research-model", "ultra", "deep", catalog)
        self.assertEqual(automatic["model"], "gpt-5.6-sol")
        self.assertEqual(automatic["model_mode"], "auto_catalog")
        self.assertEqual(automatic["task_complexity"], "standard")
        self.assertEqual(automatic["reasoning_effort"], "medium")
        self.assertEqual(manual["model"], "my-company/research-model")
        self.assertEqual(manual["model_mode"], "manual_override")
        self.assertEqual(manual["reasoning_effort"], "ultra")

    def test_public_status_is_copy_only_without_local_probe_user_config_or_debug_discovery(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "researchos_adapters.model_catalog.configured_codex_model"
        ) as configured_model, patch.object(ModelCatalog, "_discover_codex") as discover:
            root = Path(temp_dir)
            codex = root / "codex"
            codex.write_text("fixture", encoding="utf-8")
            runner = FakeCommandRunner({"models": []})
            result = ModelCatalog(root=root, command_runner=runner, codex_path=codex).status(
                public_starter=True, refresh=True
            )
        configured_model.assert_not_called()
        discover.assert_not_called()
        self.assertFalse(result["ok"])
        self.assertEqual(result["discovery"], "public_copy_only")
        self.assertEqual(result["runtime_scope"], "public_copy_only")
        self.assertEqual(result["recommended_model"], "")
        self.assertEqual(result["configured_default_model"], "")
        self.assertEqual(result["models"], [])
        self.assertEqual(runner.calls, [])

    def test_model_ids_and_codex_config_are_bounded(self):
        self.assertEqual(clean_model_id("company/model-v2"), "company/model-v2")
        self.assertEqual(clean_model_id("bad model"), "")
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "config.toml"
            config.write_text('model = "gpt-5.6-sol"\nmodel_reasoning_effort = "low"\n', encoding="utf-8")
            self.assertEqual(configured_codex_model(config), "gpt-5.6-sol")

    def test_preferred_codex_executable_is_shared_by_catalog_and_runner(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex = Path(temp_dir) / "codex"
            codex.write_text("fixture", encoding="utf-8")
            self.assertEqual(resolve_codex_executable(codex), codex)


if __name__ == "__main__":
    unittest.main()
