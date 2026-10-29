from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/receipt_cli.py"


class ZeroDashboardReceiptFlowTest(unittest.TestCase):
    def run_cli(self, root: Path, *arguments: str, stdin: dict[str, object] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--root", str(root), *arguments],
            input=json.dumps(stdin, ensure_ascii=False) if stdin is not None else None,
            text=True, capture_output=True, check=False,
        )

    def test_three_scopes_complete_source_to_next_action_without_dashboard_server_or_provider(self) -> None:
        source_code = SCRIPT.read_text(encoding="utf-8")
        for forbidden_import in ("serve_dashboard", "provider_config", "provider_adapter", "urllib", "requests", "socket"):
            self.assertNotIn(forbidden_import, source_code)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Fictional evidence revision for a local receipt smoke.\n", encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            for index, scope in enumerate(("private", "public_starter", "personal_vault"), start=1):
                task_id = "task:" + str(index) * 64
                context_spec = {
                    "task_id": task_id,
                    "run_id": f"run-{index}",
                    "runtime_scope": scope,
                    "producer_kind": "cli",
                    "producer_surface": "terminal",
                    "source_refs": [{"kind": "file", "ref": "source.md", "label": "Fictional source"}],
                }
                context_path = f"context-{scope}.json"
                context_result = self.run_cli(
                    root, "build-context", "--input", "-", "--output", context_path, stdin=context_spec,
                )
                self.assertEqual(0, context_result.returncode, context_result.stderr)
                context = json.loads((root / context_path).read_text(encoding="utf-8"))
                handoff_spec = {
                    "context_receipt": context,
                    "source": {"kind": "file", "ref": "source.md"},
                    "source_path": "source.md",
                    "last_judgment": {"state": "candidate", "text": "The claim still needs exact-source verification."},
                    "open_boundary": {"state": "recorded", "text": "Generalization remains unresolved."},
                    "next_safe_action": {"state": "recommended", "text": "Inspect the bound revision before changing the claim."},
                    "forbidden_actions": {"state": "recorded", "items": ["Do not admit the candidate to durable memory."]},
                    "target_client": {"kind": "codex", "surface": "desktop"},
                }
                handoff_path = f"handoff-{scope}.json"
                handoff_result = self.run_cli(
                    root, "build-handoff", "--input", "-", "--output", handoff_path, stdin=handoff_spec,
                )
                self.assertEqual(0, handoff_result.returncode, handoff_result.stderr)
                receipt = json.loads((root / handoff_path).read_text(encoding="utf-8"))
                self.assertEqual(scope, receipt["runtime_scope"])
                self.assertEqual(f"file_sha256:{digest}", receipt["source_revision"]["evidence_ref"])
                self.assertRegex(receipt["source_revision"]["value_digest"], r"^[0-9a-f]{64}$")
                self.assertEqual(
                    "Inspect the bound revision before changing the claim.", receipt["next_safe_action"]["text"],
                )
                validated = self.run_cli(root, "validate", "--input", handoff_path)
                inspected = self.run_cli(root, "inspect", "--input", handoff_path)
                self.assertEqual(0, validated.returncode, validated.stderr)
                self.assertEqual(validated.stdout, inspected.stdout)
                output = validated.stdout + validated.stderr + inspected.stdout + inspected.stderr
                for forbidden in ("127.0.0.1", "localhost", "http://", "https://", str(ROOT)):
                    self.assertNotIn(forbidden, output)

    def test_missing_explicit_source_fails_without_dashboard_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = {
                "task_id": "task:" + "a" * 64,
                "run_id": "run-1",
                "runtime_scope": "private",
                "producer_kind": "cli",
                "producer_surface": "terminal",
                "source_refs": [{"kind": "file", "ref": "missing.md", "label": "Missing"}],
            }
            built = self.run_cli(root, "build-context", "--input", "-", "--output", "-", stdin=context)
            receipt = json.loads(built.stdout)
            spec = {
                "context_receipt": receipt,
                "source": {"kind": "file", "ref": "missing.md"},
                "source_path": "missing.md",
                "last_judgment": {"state": "unknown", "text": ""},
                "open_boundary": {"state": "unknown", "text": ""},
                "next_safe_action": {"state": "unknown", "text": ""},
                "forbidden_actions": {"state": "unknown", "items": []},
                "target_client": {"kind": "cli", "surface": "terminal"},
            }
            failed = self.run_cli(root, "build-handoff", "--input", "-", "--output", "-", stdin=spec)
            self.assertEqual(2, failed.returncode)
            self.assertIn("path_not_allowed", failed.stderr)
            self.assertNotIn("Dashboard", failed.stderr)

    def test_explicit_reroute_discards_foreign_classification_and_authority(self) -> None:
        intent = {"terminal_job": "Understand a material", "primary_family_candidate": "foreign_runtime_family",
                  "secondary_family_candidates": ["foreign_secondary"], "current_commitment_id": "foreign-commitment",
                  "thread_id": "foreign-thread", "authority_owner": "foreign-owner", "sensitivity": "public"}
        command = ["python3", str(ROOT / "scripts/plan_context.py"), "--intent-json", "-", "--lang", "en"]
        rejected = subprocess.run(command, input=json.dumps(intent), text=True, capture_output=True)
        self.assertNotEqual(rejected.returncode, 0)
        rerouted = subprocess.run([*command, "--reroute-intent"], input=json.dumps(intent), text=True, capture_output=True)
        self.assertEqual(rerouted.returncode, 0, rerouted.stderr)
        receipt = json.loads(rerouted.stdout)
        self.assertIsNone(receipt["intent"]["primary_family_candidate"])
        self.assertIsNone(receipt["identity"]["commitment_id"])
        self.assertIsNone(receipt["identity"]["thread_id"])
        self.assertFalse(receipt["route"]["authority"]["mutation_allowed_by_receipt"])
        self.assertFalse(receipt["route"]["authority"]["external_effect_allowed_by_receipt"])
        invalid = subprocess.run([*command, "--reroute-intent", "--prior-receipt-json", "missing.json"], input=json.dumps(intent), text=True, capture_output=True)
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("cannot reuse a prior receipt", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
