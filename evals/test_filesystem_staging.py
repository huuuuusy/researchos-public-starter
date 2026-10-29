from __future__ import annotations

import json
import hashlib
import copy
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters.filesystem_staging import (  # noqa: E402
    FILESYSTEM_RECEIPT_SCHEMA_ID,
    MAX_FILES,
    ArtifactStaging,
    FilesystemStagingError,
    begin_artifact_staging,
    begin_canonical_staging,
    finalize_artifact_staging,
    rollback_artifact_mutation,
)


POLICY = {
    "operation": "create_artifact",
    "allowed_write_targets": [{"path": "06_active_context/work_state/outputs/", "mode": "subtree"}],
    "network_access": "disabled",
    "credential_access": "denied",
}


def begin(root: Path, scope: str = "private") -> ArtifactStaging:
    return begin_artifact_staging(root=root, runtime_scope=scope, run_id="run-filesystem-1", authority_policy=POLICY)


class FilesystemStagingTest(unittest.TestCase):
    def test_canonical_promotion_binds_the_planning_preimage(self) -> None:
        policy = {"operation": "canonical_writeback", "network_access": "disabled",
                  "credential_access": "denied", "allowed_write_targets": [{"path": "card.md", "mode": "file"}]}
        for change in ("unchanged", "edited", "deleted", "created"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / "card.md"
                if change != "created":
                    path.write_text("before", encoding="utf-8")
                expected = hashlib.sha256(b"before").hexdigest() if change != "created" else None
                staging = begin_canonical_staging(root=root, runtime_scope="private", run_id="bounded", authority_policy=policy)
                (staging.working_root / "card.md").write_text("planned", encoding="utf-8")
                if change in {"edited", "created"}:
                    path.write_text("another writer", encoding="utf-8")
                elif change == "deleted":
                    path.unlink()
                if change == "unchanged":
                    receipt = staging.promote(expected_preimages={"card.md": expected})
                    self.assertEqual(receipt["changes"][0]["prior_digest"], expected)
                    self.assertEqual("planned", path.read_text(encoding="utf-8"))
                else:
                    with self.assertRaisesRegex(FilesystemStagingError, "preimage_conflict"):
                        staging.promote(expected_preimages={"card.md": expected})
                    self.assertFalse(staging.rollback_root.exists(), "no prepared or successful receipt on conflict")
                    self.assertEqual(None if change == "deleted" else "another writer",
                                     path.read_text(encoding="utf-8") if path.exists() else None)
                    staging.abort()

    def test_preimage_map_must_cover_exactly_the_staged_files(self) -> None:
        for bindings in ({}, {"other": None}, {"06_active_context/work_state/outputs/card.md": "bad"}):
            with self.subTest(bindings=bindings), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                staging = begin(root)
                (staging.working_root / "card.md").write_text("planned", encoding="utf-8")
                with self.assertRaisesRegex(FilesystemStagingError, "filesystem_staging_invalid"):
                    staging.promote(expected_preimages=bindings)
                self.assertFalse((root / "06_active_context/work_state/outputs/card.md").exists())
                staging.abort()

    def test_runtime_lock_serializes_two_real_processes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock_path = root / "runtime.lock"
            held = root / "held"
            child = (
                "import sys,time; from pathlib import Path; "
                "sys.path.insert(0, sys.argv[1]); "
                "from researchos_kernel.atomic_files import runtime_state_transaction; "
                "lock=Path(sys.argv[2]); held=Path(sys.argv[3]); "
                "ctx=runtime_state_transaction(lock_path=lock); ctx.__enter__(); "
                "held.write_text('held'); time.sleep(0.35); ctx.__exit__(None,None,None)"
            )
            process = subprocess.Popen([
                sys.executable,
                "-c",
                child,
                str(ROOT / "scripts"),
                str(lock_path),
                str(held),
            ])
            try:
                deadline = time.monotonic() + 3
                while not held.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(held.exists(), "child process must acquire the shared lock")
                from researchos_kernel.atomic_files import runtime_state_transaction
                started = time.monotonic()
                with runtime_state_transaction(lock_path=lock_path):
                    elapsed = time.monotonic() - started
                self.assertGreaterEqual(elapsed, 0.15, "a second process must wait for the shared lock")
            finally:
                process.wait(timeout=3)
            self.assertEqual(0, process.returncode)

    def test_worker_only_receives_hidden_working_copy_until_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = begin(root)
            self.assertIn(".artifact-staging", staging.working_root.parts)
            (staging.working_root / "nested").mkdir()
            (staging.working_root / "nested" / "artifact.md").write_text("new", encoding="utf-8")
            live = root / "06_active_context/work_state/outputs/nested/artifact.md"
            self.assertFalse(live.exists())
            receipt = staging.promote()
            self.assertEqual("new", live.read_text(encoding="utf-8"))
            self.assertEqual("committed", receipt["status"])
            self.assertEqual("none", receipt["authority_effect"])
            self.assertFalse(staging.working_root.exists())

    def test_overwrite_receipt_supports_digest_checked_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = root / "06_active_context/work_state/outputs/artifact.md"
            live.parent.mkdir(parents=True)
            live.write_text("before", encoding="utf-8")
            staging = begin(root)
            (staging.working_root / "artifact.md").write_text("after", encoding="utf-8")
            receipt = staging.promote()
            self.assertEqual("replaced", receipt["changes"][0]["disposition"])
            rolled_back = rollback_artifact_mutation(root=root, receipt=receipt)
            self.assertEqual("rolled_back", rolled_back["status"])
            self.assertEqual("before", live.read_text(encoding="utf-8"))

    def test_rollback_refuses_to_overwrite_a_later_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = begin(root)
            (staging.working_root / "artifact.md").write_text("after", encoding="utf-8")
            receipt = staging.promote()
            live = root / "06_active_context/work_state/outputs/artifact.md"
            live.write_text("later", encoding="utf-8")
            with self.assertRaisesRegex(FilesystemStagingError, "filesystem_rollback_conflict"):
                rollback_artifact_mutation(root=root, receipt=receipt)
            self.assertEqual("later", live.read_text(encoding="utf-8"))

    def test_rollback_rejects_a_forged_or_untracked_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = begin(root)
            (staging.working_root / "artifact.md").write_text("after", encoding="utf-8")
            receipt = staging.promote()
            forged = copy.deepcopy(receipt)
            forged["changes"][0]["new_digest"] = "0" * 64
            with self.assertRaisesRegex(FilesystemStagingError, "filesystem_rollback_invalid"):
                rollback_artifact_mutation(root=root, receipt=forged)
            self.assertEqual("after", (root / "06_active_context/work_state/outputs/artifact.md").read_text())

    def test_rollback_rejects_redirected_parent_even_when_content_digest_matches(self) -> None:
        for redirected in ("output", "backup", "receipt"):
            with self.subTest(redirected=redirected), tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
                root, external_root = Path(directory), Path(external)
                live = root / "06_active_context/work_state/outputs/nested/artifact.md"
                live.parent.mkdir(parents=True)
                live.write_text("before")
                staging = begin(root)
                (staging.working_root / "nested").mkdir()
                (staging.working_root / "nested/artifact.md").write_text("after")
                receipt = staging.promote()
                stored = next(root.rglob("receipt.json"))
                parent = {"output": live.parent, "backup": stored.parent / "files/nested", "receipt": stored.parent}[redirected]
                import shutil
                shutil.copytree(parent, external_root, dirs_exist_ok=True)
                parent.rename(parent.with_name(parent.name + "-retained"))
                parent.symlink_to(external_root, target_is_directory=True)
                before = {str(p.relative_to(external_root)): p.read_bytes() for p in external_root.rglob("*") if p.is_file()}
                with self.assertRaises(FilesystemStagingError):
                    rollback_artifact_mutation(root=root, receipt=receipt)
                self.assertEqual(before, {str(p.relative_to(external_root)): p.read_bytes() for p in external_root.rglob("*") if p.is_file()})
                self.assertEqual("after", live.read_text())

    def test_symlinks_hardlinks_and_unregistered_policy_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root = Path(directory)
            with self.assertRaisesRegex(FilesystemStagingError, "filesystem_staging_invalid"):
                begin_artifact_staging(root=root, runtime_scope="public_starter", run_id="run", authority_policy=POLICY)
            with self.assertRaisesRegex(FilesystemStagingError, "filesystem_staging_invalid"):
                begin_artifact_staging(root=root, runtime_scope="private", run_id="run", authority_policy={**POLICY, "allowed_write_targets": [{"path": "/tmp", "mode": "subtree"}]})
            staging = begin(root)
            (staging.working_root / "escape").symlink_to(Path(external), target_is_directory=True)
            with self.assertRaisesRegex(FilesystemStagingError, "filesystem_staging_invalid"):
                staging.promote()
            staging.abort()
            staging = begin(root)
            first = staging.working_root / "one.md"
            first.write_text("same inode", encoding="utf-8")
            os.link(first, staging.working_root / "two.md")
            with self.assertRaisesRegex(FilesystemStagingError, "filesystem_staging_invalid"):
                staging.promote()
            staging.abort()

    def test_existing_intermediate_or_final_symlink_never_changes_external_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root = Path(directory)
            work_state = root / "06_active_context/work_state"
            work_state.mkdir(parents=True)
            (work_state / "outputs").symlink_to(Path(external), target_is_directory=True)
            with self.assertRaisesRegex(FilesystemStagingError, "filesystem_staging_invalid"):
                begin(root)
            self.assertEqual([], list(Path(external).iterdir()))

        for kind in ("intermediate", "final"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
                root, external_root = Path(directory), Path(external)
                output = root / "06_active_context/work_state/outputs"
                output.mkdir(parents=True)
                staging = begin(root)
                (staging.working_root / "nested").mkdir()
                (staging.working_root / "nested/artifact.md").write_text("new", encoding="utf-8")
                if kind == "intermediate":
                    (output / "nested").symlink_to(external_root, target_is_directory=True)
                else:
                    (output / "nested").mkdir()
                    external_file = external_root / "artifact.md"
                    external_file.write_text("external", encoding="utf-8")
                    (output / "nested/artifact.md").symlink_to(external_file)
                with self.assertRaisesRegex(FilesystemStagingError, "filesystem_staging_invalid"):
                    staging.promote()
                staging.abort()
                self.assertNotEqual("new", (external_root / "artifact.md").read_text(encoding="utf-8") if (external_root / "artifact.md").exists() else "")

    def test_partial_promotion_is_compensated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = root / "06_active_context/work_state/outputs/one.md"
            live.parent.mkdir(parents=True)
            live.write_text("before", encoding="utf-8")
            staging = begin(root)
            (staging.working_root / "one.md").write_text("after", encoding="utf-8")
            (staging.working_root / "two.md").write_text("new", encoding="utf-8")
            real_replace = os.replace
            calls = 0

            def fail_second_source(source, destination):
                nonlocal calls
                if str(source).startswith(str(staging.working_root)):
                    calls += 1
                    if calls == 2:
                        raise OSError("injected")
                return real_replace(source, destination)

            with patch("researchos_adapters.filesystem_staging.os.replace", side_effect=fail_second_source):
                with self.assertRaises(FilesystemStagingError) as raised:
                    staging.promote()
            self.assertEqual("filesystem_promotion_failed", raised.exception.code)
            self.assertEqual("compensated", raised.exception.receipt["status"])
            self.assertEqual("before", live.read_text(encoding="utf-8"))
            self.assertFalse((live.parent / "two.md").exists())

    def test_promotion_refuses_a_change_after_precheck(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = root / "06_active_context/work_state/outputs/artifact.md"
            live.parent.mkdir(parents=True)
            live.write_text("before", encoding="utf-8")
            staging = begin(root)
            (staging.working_root / "artifact.md").write_text("proposed", encoding="utf-8")

            @contextmanager
            def inject_later_change(**_kwargs):
                live.write_text("later-other-writer", encoding="utf-8")
                yield

            with patch("researchos_adapters.filesystem_staging.runtime_state_transaction", inject_later_change):
                with self.assertRaisesRegex(FilesystemStagingError, "filesystem_staging_conflict"):
                    staging.promote()
            self.assertEqual("later-other-writer", live.read_text(encoding="utf-8"))

    def test_final_receipt_failure_returns_persisted_prepared_recovery_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = begin(root)
            (staging.working_root / "artifact.md").write_text("proposed", encoding="utf-8")
            real_write = staging._write_receipt

            def fail_committed(receipt):
                if receipt.get("status") == "committed":
                    raise OSError("injected")
                return real_write(receipt)

            with patch.object(staging, "_write_receipt", side_effect=fail_committed):
                ok, fields, receipt = finalize_artifact_staging(staging, execution_ok=True, result_fields={})
            stored = json.loads((root / receipt["rollback_ref"]).read_text(encoding="utf-8"))
            self.assertFalse(ok)
            self.assertEqual("filesystem_promotion_failed", fields["error_type"])
            self.assertEqual("prepared", receipt["status"])
            self.assertEqual(receipt, stored)
            self.assertEqual("proposed", (root / "06_active_context/work_state/outputs/artifact.md").read_text(encoding="utf-8"))

    def test_compensation_preserves_a_later_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = root / "06_active_context/work_state/outputs/one.md"
            live.parent.mkdir(parents=True)
            live.write_text("before", encoding="utf-8")
            staging = begin(root)
            (staging.working_root / "one.md").write_text("after", encoding="utf-8")
            (staging.working_root / "two.md").write_text("new", encoding="utf-8")
            real_replace = os.replace
            source_calls = 0

            def inject_later_then_fail(source, destination):
                nonlocal source_calls
                if str(source).startswith(str(staging.working_root)):
                    source_calls += 1
                    if source_calls == 2:
                        live.write_text("later-other-writer", encoding="utf-8")
                        raise OSError("injected")
                return real_replace(source, destination)

            with patch("researchos_adapters.filesystem_staging.os.replace", side_effect=inject_later_then_fail):
                with self.assertRaises(FilesystemStagingError) as raised:
                    staging.promote()
            self.assertEqual("filesystem_compensation_failed", raised.exception.code)
            self.assertEqual("later-other-writer", live.read_text(encoding="utf-8"))

    def test_failed_rollback_compensation_keeps_attempt_recovery_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "06_active_context/work_state/outputs"
            output.mkdir(parents=True)
            (output / "one.md").write_text("before-one", encoding="utf-8")
            (output / "two.md").write_text("before-two", encoding="utf-8")
            staging = begin(root)
            (staging.working_root / "one.md").write_text("after-one", encoding="utf-8")
            (staging.working_root / "two.md").write_text("after-two", encoding="utf-8")
            receipt = staging.promote()
            rollback_root = root / Path(receipt["rollback_ref"]).parent
            real_copy = __import__("shutil").copy2
            real_replace = os.replace

            def fail_second_restore(source, destination, **kwargs):
                if str(source).startswith(str(rollback_root / "files/one.md")):
                    raise OSError("rollback injected")
                return real_copy(source, destination, **kwargs)

            def fail_attempt_compensation(source, destination):
                if "attempt-" in str(source):
                    raise OSError("compensation injected")
                return real_replace(source, destination)

            with patch("researchos_adapters.filesystem_staging.shutil.copy2", side_effect=fail_second_restore), \
                 patch("researchos_adapters.filesystem_staging.os.replace", side_effect=fail_attempt_compensation):
                with self.assertRaisesRegex(FilesystemStagingError, "filesystem_compensation_failed"):
                    rollback_artifact_mutation(root=root, receipt=receipt)
            attempts = list(rollback_root.glob("attempt-*"))
            self.assertEqual(1, len(attempts), "failed recovery material must remain available for reconciliation")
            self.assertTrue((attempts[0] / "two.md").exists())

    def test_unexpected_promotion_error_is_public_safe_and_cleans_working_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            staging = begin(Path(directory))
            (staging.working_root / "artifact.md").write_text("value", encoding="utf-8")
            with patch.object(ArtifactStaging, "promote", side_effect=OSError("private path")):
                ok, fields, receipt = finalize_artifact_staging(staging, execution_ok=True, result_fields={})
            self.assertFalse(ok)
            self.assertEqual("filesystem_promotion_failed", fields["error_type"])
            self.assertEqual({}, receipt)
            self.assertFalse(staging.working_root.exists())
            self.assertNotIn("private path", json.dumps(fields))

    def test_limits_abort_and_personal_vault_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as private_dir, tempfile.TemporaryDirectory() as vault_dir:
            private_root, vault_root = Path(private_dir), Path(vault_dir)
            staging = begin(private_root)
            for index in range(MAX_FILES + 1):
                (staging.working_root / f"{index}.md").write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(FilesystemStagingError, "filesystem_staging_limit_exceeded"):
                staging.promote()
            staging.abort()
            vault = begin(vault_root, "personal_vault")
            (vault.working_root / "vault.md").write_text("vault", encoding="utf-8")
            vault.promote()
            self.assertTrue((vault_root / "06_active_context/work_state/outputs/vault.md").exists())
            self.assertFalse((private_root / "06_active_context/work_state/outputs/vault.md").exists())

    def test_receipt_matches_schema_keys_and_contains_no_authority_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = begin(root)
            (staging.working_root / "artifact.md").write_text("value", encoding="utf-8")
            receipt = staging.promote()
        schema = json.loads((ROOT / "09_templates/data_contracts/researchos-filesystem-receipt-v1.schema.json").read_text())
        self.assertEqual(FILESYSTEM_RECEIPT_SCHEMA_ID, receipt["schema_id"])
        self.assertEqual(set(schema["required"]), set(receipt))
        serialized = json.dumps(receipt)
        for forbidden in ("approved", "accepted", "confirmed", "validated"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
