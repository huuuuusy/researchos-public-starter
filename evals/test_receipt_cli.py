from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/receipt_cli.py"


class ReceiptCliTest(unittest.TestCase):
    def run_cli(self, root: Path, *arguments: str, stdin: dict[str, object] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--root", str(root), *arguments],
            input=json.dumps(stdin, ensure_ascii=False) if stdin is not None else None,
            text=True, capture_output=True, check=False,
        )

    def context_spec(self, scope: str = "private") -> dict[str, object]:
        return {
            "task_id": "task:" + "a" * 64,
            "run_id": "run-1",
            "runtime_scope": scope,
            "producer_kind": "codex",
            "producer_surface": "desktop",
            "source_refs": [{"kind": "file", "ref": "source.md", "label": "Source"}],
        }

    def handoff_spec(self, context: dict[str, object]) -> dict[str, object]:
        return {
            "context_receipt": context,
            "source": {"kind": "file", "ref": "source.md"},
            "source_path": "source.md",
            "last_judgment": {"state": "candidate", "text": "The claim needs verification."},
            "open_boundary": {"state": "recorded", "text": "External validity remains open."},
            "next_safe_action": {"state": "recommended", "text": "Read the exact revision."},
            "forbidden_actions": {"state": "recorded", "items": ["Do not promote the candidate."]},
            "target_client": {"kind": "codex", "surface": "desktop"},
        }

    def build_context(self, root: Path, scope: str = "private") -> dict[str, object]:
        result = self.run_cli(root, "build-context", "--input", "-", "--output", "-", stdin=self.context_spec(scope))
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def test_context_build_validate_and_inspect_need_no_dashboard_or_server(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = self.build_context(root)
            (root / "context.json").write_text(json.dumps(context), encoding="utf-8")
            validated = self.run_cli(root, "validate", "--input", "context.json")
            inspected = self.run_cli(root, "inspect", "--input", "context.json")
            self.assertEqual(0, validated.returncode, validated.stderr)
            self.assertEqual(validated.stdout, inspected.stdout)
            summary = json.loads(validated.stdout)
            self.assertTrue(summary["ok"])
            self.assertEqual("researchos-context-receipt-v1", summary["schema_id"])
            self.assertEqual(1, summary["source_count"])

    def test_handoff_build_uses_file_revision_and_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text("exact source revision\n", encoding="utf-8")
            context = self.build_context(root)
            spec = self.handoff_spec(context)
            first = self.run_cli(root, "build-handoff", "--input", "-", "--output", "-", stdin=spec)
            second = self.run_cli(root, "build-handoff", "--input", "-", "--output", "-", stdin=spec)
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            receipt = json.loads(first.stdout)
            self.assertEqual("verified", receipt["source_revision"]["state"])
            self.assertTrue(receipt["source_revision"]["evidence_ref"].startswith("file_sha256:"))
            self.assertEqual("tool_recorded", receipt["producer"]["evidence_class"])
            self.assertNotIn(str(root), first.stdout)
            self.assertNotIn("exact source revision", first.stdout)

    def test_source_change_changes_handoff_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("revision one", encoding="utf-8")
            context = self.build_context(root)
            spec = self.handoff_spec(context)
            first = json.loads(self.run_cli(root, "build-handoff", "--input", "-", "--output", "-", stdin=spec).stdout)
            source.write_text("revision two", encoding="utf-8")
            second = json.loads(self.run_cli(root, "build-handoff", "--input", "-", "--output", "-", stdin=spec).stdout)
            self.assertNotEqual(first["handoff_id"], second["handoff_id"])

    def test_cli_cannot_sign_human_recorded_judgment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text("source", encoding="utf-8")
            spec = self.handoff_spec(self.build_context(root))
            spec["last_judgment"] = {"state": "human_recorded", "text": "Pretend accepted"}
            result = self.run_cli(root, "build-handoff", "--input", "-", "--output", "-", stdin=spec)
            self.assertEqual(2, result.returncode)
            self.assertIn("last_judgment_invalid", result.stderr)

    def test_absolute_traversal_symlink_and_overwrite_outputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside_directory:
            root = Path(directory)
            spec = self.context_spec()
            absolute = self.run_cli(root, "build-context", "--input", "-", "--output", str(root / "receipt.json"), stdin=spec)
            traversal = self.run_cli(root, "build-context", "--input", "-", "--output", "../receipt.json", stdin=spec)
            (root / "linked").symlink_to(Path(outside_directory), target_is_directory=True)
            symlink = self.run_cli(root, "build-context", "--input", "-", "--output", "linked/receipt.json", stdin=spec)
            (root / "receipt.json").write_text("keep", encoding="utf-8")
            overwrite = self.run_cli(root, "build-context", "--input", "-", "--output", "receipt.json", stdin=spec)
            self.assertEqual([2, 2, 2, 2], [absolute.returncode, traversal.returncode, symlink.returncode, overwrite.returncode])
            self.assertEqual("keep", (root / "receipt.json").read_text(encoding="utf-8"))
            self.assertFalse((Path(outside_directory) / "receipt.json").exists())

    def test_atomic_file_output_has_private_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.run_cli(root, "build-context", "--input", "-", "--output", "context.json", stdin=self.context_spec())
            self.assertEqual(0, result.returncode, result.stderr)
            path = root / "context.json"
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            self.assertEqual([], list(root.glob("*.tmp")))

    def test_source_ref_must_match_context_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text("source", encoding="utf-8")
            spec = self.handoff_spec(self.build_context(root))
            spec["source"] = {"kind": "file", "ref": "different.md"}
            result = self.run_cli(root, "build-handoff", "--input", "-", "--output", "-", stdin=spec)
            self.assertEqual(2, result.returncode)
            self.assertIn("handoff_receipt_source_not_in_context", result.stderr)

    def test_three_scopes_round_trip_without_implicit_runtime_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for scope in ("private", "public_starter", "personal_vault"):
                receipt = self.build_context(root, scope)
                self.assertEqual(scope, receipt["runtime_scope"])
                self.assertEqual("client_asserted", receipt["producer"]["evidence_class"])

    def test_binding_freshness_and_human_claim_are_separate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"; source.write_text("original")
            (root / "other.md").write_text("different")
            spec = self.handoff_spec(self.build_context(root))
            spec["source_path"] = "other.md"
            failed = self.run_cli(root, "build-handoff", "--input", "-", "--output", "bad.json", stdin=spec)
            self.assertEqual(failed.returncode, 2)
            self.assertIn("source_identity_path_mismatch", failed.stderr)
            self.assertFalse((root / "bad.json").exists())
            spec["source_path"] = "source.md"
            built = self.run_cli(root, "build-handoff", "--input", "-", "--output", "receipt.json", stdin=spec)
            self.assertEqual(built.returncode, 0, built.stderr)
            receipt = json.loads((root / "receipt.json").read_text())
            receipt["last_judgment"] = {"state": "human_recorded", "text": "Claimed decision", "evidence_ref": "decision:nonexistent"}
            (root / "receipt.json").write_text(json.dumps(receipt))
            checked = self.run_cli(root, "validate", "--input", "receipt.json")
            summary = json.loads(checked.stdout)
            self.assertEqual(summary["validation_scope"], "structure_only")
            self.assertFalse(summary["human_decision_verified"])
            self.assertEqual(summary["states"]["last_judgment"], "unknown")
            self.assertEqual(summary["states"]["source_revision"], "unknown")
            fresh = self.run_cli(root, "recheck-source", "--input", "receipt.json", "--source", "source.md")
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            self.assertEqual(json.loads(fresh.stdout)["source_freshness"], "matches_current_file")
            self.assertFalse(json.loads(fresh.stdout)["human_decision_verified"])
            mismatch = self.run_cli(root, "recheck-source", "--input", "receipt.json", "--source", "other.md")
            self.assertEqual(mismatch.returncode, 2)
            source.write_text("changed")
            stale = self.run_cli(root, "recheck-source", "--input", "receipt.json", "--source", "source.md")
            self.assertEqual(stale.returncode, 2)
            self.assertIn("source_revision_mismatch", stale.stderr)
            source.unlink()
            self.assertEqual(self.run_cli(root, "recheck-source", "--input", "receipt.json", "--source", "source.md").returncode, 2)


if __name__ == "__main__":
    unittest.main()
