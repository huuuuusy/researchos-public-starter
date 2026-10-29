"""The provider seam: a new local CLI provider is one ``ProviderSpec`` entry plus its adapter class.

Adding one touches about three files: the entry in ``scripts/researchos_adapters/provider_registry.py``,
the module holding its adapter class, and its test. Dispatch, the CLI-missing status and the pre-launch
error set derive from the entry; nothing else in the launch boundary lists provider ids. (Offering it
as a Dashboard runtime profile also needs its family in the runtime-profile schema enum.)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters import provider_registry  # noqa: E402
from researchos_adapters.dispatch import launched_nothing, provider_for  # noqa: E402
from researchos_adapters.provider_adapter import ExecutionRequest, ProviderExecution  # noqa: E402
from researchos_adapters.provider_config import provider_execution_status  # noqa: E402
from researchos_adapters.provider_registry import PROVIDERS, ProviderSpec  # noqa: E402


class EchoProvider:
    """The adapter class a new provider brings: built from (runtime_scope, declared), run with execute()."""

    def __init__(self, runtime_scope: str, declared: dict) -> None:
        self.runtime_scope = runtime_scope
        self.declared = declared

    def execute(self, request: ExecutionRequest) -> ProviderExecution:
        return ProviderExecution("echo", True, 0, 0.0, "echo: " + request.prompt)


ECHO = ProviderSpec(
    name="echo", type="local_echo", label="Echo", default_model="auto", cli_missing_error="echo_cli_missing",
    endpoint_ref="local:echo-cli", adapter=f"{__name__}:EchoProvider", public_starter_allowed=False,
    description_zh="测试用的本地 provider。", description_en="A local provider used by this test.",
)
DECLARED = {"providers": {"echo": {"dispatchable": True, "reasoning": "low"}}}


class ProviderRegistryTest(unittest.TestCase):
    def test_every_spec_names_its_own_error_endpoint_and_an_importable_adapter_class(self) -> None:
        self.assertEqual({"codex", "claude_code"}, set(PROVIDERS))
        for name, spec in PROVIDERS.items():
            with self.subTest(provider=name):
                self.assertEqual(name, spec.name)
                self.assertEqual(f"{name}_cli_missing", spec.cli_missing_error)
                self.assertTrue(spec.endpoint_ref.startswith("local:"))
                self.assertFalse(spec.public_starter_allowed, "the public starter launches no provider")
                self.assertTrue(launched_nothing(spec.cli_missing_error), "a missing CLI sent nothing")
                self.assertIsNotNone(provider_for({"providers": {name: {"dispatchable": True}}}, "private", name))
        with self.assertRaises(KeyError):
            provider_registry.get_provider_spec("not-registered")

    def test_a_new_provider_needs_only_a_spec_entry_and_its_adapter_class(self) -> None:
        self.assertIsNone(provider_for(DECLARED, "private", "echo"), "unregistered: never dispatchable")
        self.assertFalse(launched_nothing("echo_cli_missing"))
        with mock.patch.dict(PROVIDERS, {"echo": ECHO}):
            adapter = provider_for(DECLARED, "private", "echo")
            self.assertIsInstance(adapter, EchoProvider)
            self.assertEqual("low", adapter.declared["reasoning"], "ros.json says whether and how to dispatch")
            self.assertEqual("auto", adapter.declared["default_model"], "the model comes from the registry default")
            result = adapter.execute(ExecutionRequest(prompt="hello", timeout=5))
            self.assertEqual("echo: hello", result.stdout)
            self.assertIsNone(provider_for(DECLARED, "public_starter", "echo"), "the public starter only copies")

            status = provider_execution_status("echo", executable_available=False)
            self.assertEqual("echo_cli_missing", status["error_type"])
            self.assertIn("Echo CLI is unavailable", status["message_en"])
            self.assertTrue(launched_nothing("echo_cli_missing"), "its CLI-missing failure is pre-launch")
        self.assertFalse(launched_nothing("runner_execution_failed"), "a failure after launch has unknown effects")

    def test_ros_json_declares_dispatch_only_and_names_where_the_rest_belongs(self) -> None:
        with self.assertRaisesRegex(SystemExit, "model belongs in config/researchos.runtime.local.json"):
            provider_for({"providers": {"codex": {"dispatchable": True, "model": "x"}}}, "private", "codex")


if __name__ == "__main__":
    unittest.main()
