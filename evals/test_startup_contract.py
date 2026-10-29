import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("start_researchos", ROOT / "scripts" / "start_researchos.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.path.insert(0, str(ROOT / "scripts"))
SPEC.loader.exec_module(MODULE)


class StartupContractTest(unittest.TestCase):
    def test_free_port_allows_startup(self) -> None:
        with mock.patch.object(MODULE, "_is_port_open", return_value=False):
            self.assertIsNone(MODULE.guard_dashboard_port("127.0.0.1", 8880))

    def test_existing_researchos_is_treated_as_already_running(self) -> None:
        with mock.patch.object(MODULE, "_is_port_open", return_value=True), mock.patch.object(MODULE, "_is_researchos_server", return_value=True) as probe, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(MODULE.guard_dashboard_port("127.0.0.1", 8880), 0)
        self.assertIn("already running", output.getvalue())
        probe.assert_called_once_with("127.0.0.1", 8880, "public_starter")

    def test_unrelated_listener_gets_a_clear_port_conflict(self) -> None:
        with mock.patch.object(MODULE, "_is_port_open", return_value=True), mock.patch.object(MODULE, "_is_researchos_server", return_value=False), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(MODULE.guard_dashboard_port("127.0.0.1", 8880), 2)
        self.assertIn("port belongs to another service", output.getvalue())

    def test_other_researchos_runtime_is_not_reused(self) -> None:
        with mock.patch.object(MODULE, "_is_port_open", return_value=True), mock.patch.object(MODULE, "_is_researchos_server", return_value=False) as probe, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(MODULE.guard_dashboard_port("127.0.0.1", 8880, "personal_vault"), 2)
        self.assertIn("port belongs to another service", output.getvalue())
        probe.assert_called_once_with("127.0.0.1", 8880, "personal_vault")

    def test_existing_shipped_projection_is_not_rebuilt_on_startup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in MODULE.PUBLIC_PROJECTION_FILES:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("{}\n", encoding="utf-8")
            with mock.patch.object(MODULE, "REPO_ROOT", root), mock.patch.object(MODULE.subprocess, "call") as call:
                result, status = MODULE.ensure_public_projection()
            self.assertEqual(result, 0)
            self.assertIn("shipped", status)
            call.assert_not_called()

    def test_missing_projection_is_rebuilt_for_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(MODULE, "REPO_ROOT", root), mock.patch.object(MODULE.subprocess, "call", return_value=0) as call:
                result, status = MODULE.ensure_public_projection()
            self.assertEqual(result, 0)
            self.assertIn("missing", status)
            self.assertIn("--write", call.call_args.args[0])

    def test_cli_and_gui_are_zero_dashboard_copy_only_companions(self) -> None:
        output = io.StringIO()
        with mock.patch.object(
            MODULE, "_is_port_open", side_effect=AssertionError("dashboard probe is forbidden")
        ), redirect_stdout(output):
            self.assertEqual(MODULE.mode_cli("codex"), 0)
            self.assertEqual(MODULE.mode_gui(8880, "codex"), 0)
        rendered = output.getvalue()
        self.assertIn("dashboard_required: false", rendered)
        self.assertIn("runtime: copy_only", rendered)
        self.assertEqual(rendered.count("provider: codex (copy-only: nothing is run)"), 2)
        self.assertIn("cancel: unsupported", rendered)


if __name__ == "__main__":
    unittest.main()
