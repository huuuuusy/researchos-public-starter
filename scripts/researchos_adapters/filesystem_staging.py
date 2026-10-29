# ResearchOS maintenance header.
# 中文：有界 artifact 文件系统事务的唯一 owner；worker 只写 working copy，服务端验证后再 promotion。
# English: Sole owner for bounded artifact filesystem transactions; workers write a working copy that the server verifies before promotion.

"""Fail-closed staging, promotion, compensation, and rollback for artifact runs."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from researchos_kernel.atomic_files import atomic_write_json, runtime_state_transaction
from researchos_kernel.ledger import digest as _json_digest


FILESYSTEM_RECEIPT_SCHEMA_ID = "researchos-filesystem-receipt-v1"
OUTPUT_RELATIVE = Path("06_active_context/work_state/outputs")
OUTPUT_TARGET = {"path": f"{OUTPUT_RELATIVE.as_posix()}/", "mode": "subtree"}
STAGING_RELATIVE = Path("06_active_context/work_state/.artifact-staging")
ROLLBACK_RELATIVE = Path("06_active_context/work_state/.artifact-rollbacks")
RUNTIME_SCOPES = frozenset({"private", "personal_vault"})
MAX_FILES = 64
MAX_TOTAL_BYTES = 32 * 1024 * 1024
FORBIDDEN_PARTS = frozenset({".git", ".codex"})


class FilesystemStagingError(ValueError):
    """Public-safe filesystem boundary failure with an optional compensation receipt."""

    def __init__(self, code: str, receipt: dict[str, object] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.receipt = receipt


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_root(root: Path) -> Path:
    lexical = Path(os.path.abspath(os.fspath(root)))
    try:
        metadata = lexical.lstat()
    except FileNotFoundError as exc:
        raise FilesystemStagingError("filesystem_staging_invalid") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise FilesystemStagingError("filesystem_staging_invalid")
    return lexical


def _ensure_directory_chain(root: Path, relative: Path) -> Path:
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir(mode=0o700)
            except FileExistsError:
                metadata = current.lstat()
            else:
                metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise FilesystemStagingError("filesystem_staging_invalid")
    return current


def _verify_existing_chain(root: Path, relative: Path) -> None:
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            return
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise FilesystemStagingError("filesystem_staging_invalid")


def _valid_canonical_policy(policy: object) -> bool:
    """A canonical writeback declares its exact targets; anything else stays refused."""
    if not isinstance(policy, dict) or policy.get("operation") != "canonical_writeback":
        return False
    targets = policy.get("allowed_write_targets")
    if not isinstance(targets, list) or not targets or len(targets) > MAX_FILES:
        return False
    for target in targets:
        if not isinstance(target, dict) or target.get("mode") != "file":
            return False
        try:
            _relative_artifact(str(target.get("path", "")))
        except FilesystemStagingError:
            return False
    return policy.get("network_access") == "disabled" and policy.get("credential_access") == "denied"


def declared_targets(policy: object) -> list[str]:
    return [str(target["path"]) for target in policy["allowed_write_targets"]] if _valid_canonical_policy(policy) else []


def _valid_policy(policy: object) -> bool:
    return _valid_artifact_policy(policy) or _valid_canonical_policy(policy)


def _valid_artifact_policy(policy: object) -> bool:
    return bool(
        isinstance(policy, dict)
        and policy.get("operation") == "create_artifact"
        and policy.get("allowed_write_targets") == [dict(OUTPUT_TARGET)]
        and policy.get("network_access") == "disabled"
        and policy.get("credential_access") == "denied"
    )


def _relative_artifact(value: str) -> Path:
    posix = PurePosixPath(str(value))
    if not str(value) or posix.is_absolute() or ".." in posix.parts or any(part in FORBIDDEN_PARTS for part in posix.parts):
        raise FilesystemStagingError("filesystem_staging_invalid")
    return Path(*posix.parts)


def _relative_to_target(path_value: str, target_relative: Path) -> Path:
    relative = _relative_artifact(path_value)
    return relative if target_relative == Path(".") else relative.relative_to(target_relative)


def _safe_remove_tree(path: Path, parent: Path) -> None:
    try:
        path.relative_to(parent)
    except ValueError as exc:
        raise FilesystemStagingError("filesystem_staging_invalid") from exc
    if path.exists():
        if path.is_symlink():
            raise FilesystemStagingError("filesystem_staging_invalid")
        shutil.rmtree(path)


@dataclass
class ArtifactStaging:
    root: Path
    runtime_scope: str
    run_id: str
    transaction_id: str
    working_root: Path
    rollback_root: Path
    created_at: str
    closed: bool = False
    target_relative: Path = OUTPUT_RELATIVE
    target_spec: dict = field(default_factory=lambda: dict(OUTPUT_TARGET))
    allowed_files: tuple = ()
    operation: str = "artifact_promotion"

    def verify_for_launch(self, *, root: Path, authority_policy: object) -> Path:
        if self.closed or _safe_root(root) != self.root or not _valid_policy(authority_policy):
            raise FilesystemStagingError("filesystem_staging_invalid")
        metadata = self.working_root.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise FilesystemStagingError("filesystem_staging_invalid")
        return self.working_root

    def _files(self) -> list[tuple[Path, Path, int, str]]:
        files: list[tuple[Path, Path, int, str]] = []
        total = 0
        for directory, names, filenames in os.walk(self.working_root, topdown=True, followlinks=False):
            base = Path(directory)
            for name in names:
                metadata = (base / name).lstat()
                if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                    raise FilesystemStagingError("filesystem_staging_invalid")
                _relative_artifact((base / name).relative_to(self.working_root).as_posix())
            for name in filenames:
                source = base / name
                metadata = source.lstat()
                relative = _relative_artifact(source.relative_to(self.working_root).as_posix())
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                    raise FilesystemStagingError("filesystem_staging_invalid")
                total += metadata.st_size
                files.append((relative, source, metadata.st_size, _file_digest(source)))
                if len(files) > MAX_FILES or total > MAX_TOTAL_BYTES:
                    raise FilesystemStagingError("filesystem_staging_limit_exceeded")
        return sorted(files, key=lambda item: item[0].as_posix())

    def _receipt(self, *, status: str, changes: list[dict[str, object]], completed_at: str) -> dict[str, object]:
        base: dict[str, object] = {
            "schema_id": FILESYSTEM_RECEIPT_SCHEMA_ID,
            "transaction_id": self.transaction_id,
            "run_id": self.run_id,
            "runtime_scope": self.runtime_scope,
            "operation": self.operation,
            "target": dict(self.target_spec),
            "status": status,
            "authority_effect": "none",
            "changes": changes,
            "rollback_ref": f"{ROLLBACK_RELATIVE.as_posix()}/{self.transaction_id}/receipt.json",
            "created_at": self.created_at,
            "completed_at": completed_at,
        }
        return {**base, "receipt_id": f"filesystem:{_json_digest(base)}"}

    def _write_receipt(self, receipt: dict[str, object]) -> None:
        self.rollback_root.mkdir(mode=0o700, parents=False, exist_ok=True)
        atomic_write_json(self.rollback_root / "receipt.json", receipt, sort_keys=True)

    def abort(self) -> None:
        if not self.closed:
            _safe_remove_tree(self.working_root, self.working_root.parent)
            self.closed = True

    def promote(self, *, expected_preimages: dict[str, str | None] | None = None) -> dict[str, object]:
        if self.closed:
            raise FilesystemStagingError("filesystem_staging_invalid")
        files = self._files()
        # A caller that planned a replacement binds the version it actually read, not
        # whichever version happens to be present when promotion begins. None means
        # expected absence; omitting the map preserves the artifact creation API.
        if expected_preimages is not None:
            paths = {relative.as_posix() if self.target_relative == Path(".")
                     else f"{self.target_relative.as_posix()}/{relative.as_posix()}"
                     for relative, _, _, _ in files}
            if (not isinstance(expected_preimages, dict) or set(expected_preimages) != paths
                    or any(value is not None and (not isinstance(value, str) or len(value) != 64
                           or any(c not in "0123456789abcdef" for c in value))
                           for value in expected_preimages.values())):
                raise FilesystemStagingError("filesystem_staging_invalid")
        if self.allowed_files:
            declared = set(self.allowed_files)
            staged = {relative.as_posix() for relative, _, _, _ in files}
            if not staged or not staged <= declared:
                raise FilesystemStagingError("filesystem_staging_undeclared_target")
        _verify_existing_chain(self.root, self.target_relative)
        output_root = _ensure_directory_chain(self.root, self.target_relative)
        changes: list[dict[str, object]] = []
        for relative, source, size, new_digest in files:
            destination = output_root / relative
            _verify_existing_chain(output_root, relative.parent)
            if destination.exists() or destination.is_symlink():
                metadata = destination.lstat()
                if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                    raise FilesystemStagingError("filesystem_staging_invalid")
                prior_digest: str | None = _file_digest(destination)
            else:
                prior_digest = None
            full_path = (relative.as_posix() if self.target_relative == Path(".")
                         else f"{self.target_relative.as_posix()}/{relative.as_posix()}")
            if expected_preimages is not None and prior_digest != expected_preimages[full_path]:
                raise FilesystemStagingError("filesystem_staging_preimage_conflict")
            changes.append({
                "path": (relative.as_posix() if self.target_relative == Path(".") else f"{self.target_relative.as_posix()}/{relative.as_posix()}"),
                "disposition": "replaced" if prior_digest else "created",
                "prior_digest": prior_digest,
                "new_digest": new_digest,
                "bytes": size,
            })
        self.rollback_root.mkdir(mode=0o700, parents=False, exist_ok=False)
        prepared = self._receipt(status="prepared", changes=changes, completed_at="")
        with runtime_state_transaction(lock_path=self.rollback_root.parent / ".artifact-filesystem.lock"):
            for change, (relative, _, _, _) in zip(changes, files):
                destination = output_root / relative
                _verify_existing_chain(output_root, relative.parent)
                if change["prior_digest"]:
                    if (
                        not destination.exists()
                        or destination.is_symlink()
                        or _file_digest(destination) != change["prior_digest"]
                    ):
                        raise FilesystemStagingError("filesystem_staging_conflict")
                elif destination.exists() or destination.is_symlink():
                    raise FilesystemStagingError("filesystem_staging_conflict")
            self._write_receipt(prepared)
            applied: list[dict[str, object]] = []
            try:
                for change, (_, source, _, _) in zip(changes, files):
                    relative = _relative_to_target(str(change["path"]), self.target_relative)
                    destination = output_root / relative
                    _ensure_directory_chain(output_root, relative.parent)
                    if change["prior_digest"]:
                        backup = self.rollback_root / "files" / relative
                        backup.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                        shutil.copy2(destination, backup, follow_symlinks=False)
                        if _file_digest(backup) != change["prior_digest"] or _file_digest(destination) != change["prior_digest"]:
                            raise FilesystemStagingError("filesystem_staging_conflict", prepared)
                    elif destination.exists() or destination.is_symlink():
                        raise FilesystemStagingError("filesystem_staging_conflict", prepared)
                    os.replace(source, destination)
                    applied.append(change)
            except Exception as exc:
                compensation_ok = self._compensate(applied, output_root)
                status = "compensated" if compensation_ok else "compensation_failed"
                receipt = self._receipt(status=status, changes=changes, completed_at=_now())
                try:
                    self._write_receipt(receipt)
                except Exception as receipt_exc:
                    self.abort()
                    raise FilesystemStagingError(
                        "filesystem_promotion_failed" if compensation_ok else "filesystem_compensation_failed",
                        prepared,
                    ) from receipt_exc
                self.abort()
                raise FilesystemStagingError(
                    "filesystem_promotion_failed" if compensation_ok else "filesystem_compensation_failed", receipt
                ) from exc
            receipt = self._receipt(status="committed", changes=changes, completed_at=_now())
            try:
                self._write_receipt(receipt)
            except Exception as exc:
                self.abort()
                raise FilesystemStagingError("filesystem_promotion_failed", prepared) from exc
        self.abort()
        return receipt

    def _compensate(self, applied: list[dict[str, object]], output_root: Path) -> bool:
        try:
            for change in reversed(applied):
                relative = _relative_to_target(str(change["path"]), self.target_relative)
                destination = output_root / relative
                if change["prior_digest"]:
                    if (
                        not destination.exists()
                        or destination.is_symlink()
                        or _file_digest(destination) != change["new_digest"]
                    ):
                        return False
                    os.replace(self.rollback_root / "files" / relative, destination)
                elif destination.exists() or destination.is_symlink():
                    if destination.is_symlink() or _file_digest(destination) != change["new_digest"]:
                        return False
                    destination.unlink()
            return True
        except Exception:
            return False


def begin_artifact_staging(
    *, root: Path, runtime_scope: str, run_id: object, authority_policy: object
) -> ArtifactStaging:
    safe_root = _safe_root(root)
    if runtime_scope not in RUNTIME_SCOPES or not str(run_id).strip() or not _valid_artifact_policy(authority_policy):
        raise FilesystemStagingError("filesystem_staging_invalid")
    _verify_existing_chain(safe_root, OUTPUT_RELATIVE)
    staging_parent = _ensure_directory_chain(safe_root, STAGING_RELATIVE)
    rollback_parent = _ensure_directory_chain(safe_root, ROLLBACK_RELATIVE)
    transaction_id = f"artifact-{uuid.uuid4().hex}"
    working_root = Path(tempfile.mkdtemp(prefix=f"{transaction_id}-", dir=staging_parent))
    return ArtifactStaging(
        root=safe_root,
        runtime_scope=runtime_scope,
        run_id=str(run_id).strip()[:160],
        transaction_id=transaction_id,
        working_root=working_root,
        rollback_root=rollback_parent / transaction_id,
        created_at=_now(),
    )


def begin_canonical_staging(
    *, root: Path, runtime_scope: str, run_id: object, authority_policy: object
) -> ArtifactStaging:
    """Stage a change to declared canonical files, with the same pre-image, receipt and rollback."""
    safe_root = _safe_root(root)
    if runtime_scope not in RUNTIME_SCOPES or not str(run_id).strip() or not _valid_canonical_policy(authority_policy):
        raise FilesystemStagingError("filesystem_staging_invalid")
    targets = tuple(declared_targets(authority_policy))
    staging_parent = _ensure_directory_chain(safe_root, STAGING_RELATIVE)
    rollback_parent = _ensure_directory_chain(safe_root, ROLLBACK_RELATIVE)
    transaction_id = f"canonical-{uuid.uuid4().hex}"
    working_root = Path(tempfile.mkdtemp(prefix=f"{transaction_id}-", dir=staging_parent))
    return ArtifactStaging(
        root=safe_root,
        runtime_scope=runtime_scope,
        run_id=str(run_id).strip()[:160],
        transaction_id=transaction_id,
        working_root=working_root,
        rollback_root=rollback_parent / transaction_id,
        created_at=_now(),
        target_relative=Path("."),
        target_spec={"path": "/", "mode": "declared_files", "files": list(targets)},
        allowed_files=targets,
        operation="canonical_writeback",
    )


def staging_for_policy(
    *, root: Path, runtime_scope: str, run_id: object, authority_policy: object
) -> ArtifactStaging | None:
    if isinstance(authority_policy, dict) and authority_policy.get("operation") == "read_only":
        return None
    return begin_artifact_staging(
        root=root, runtime_scope=runtime_scope, run_id=run_id, authority_policy=authority_policy
    )


def project_promoted_artifact_result(
    result_fields: object, receipt: object
) -> dict[str, object]:
    """Replace model-reported file refs with paths proven by the filesystem receipt."""
    projection = dict(result_fields) if isinstance(result_fields, dict) else {}
    changes = receipt.get("changes") if isinstance(receipt, dict) and isinstance(receipt.get("changes"), list) else []
    paths = [str(change.get("path")) for change in changes if isinstance(change, dict) and change.get("path")]
    projection.update({
        "changed_files": paths,
        "artifacts": [{"path": path, "kind": "file"} for path in paths],
        "preview_anchors": paths,
    })
    return projection


def finalize_artifact_staging(
    staging: ArtifactStaging | None, *, execution_ok: bool, result_fields: object
) -> tuple[bool, dict[str, object], dict[str, object]]:
    projection = dict(result_fields) if isinstance(result_fields, dict) else {}
    if staging is None:
        return execution_ok, projection, {}
    if not execution_ok:
        staging.abort()
        return False, projection, {}
    try:
        receipt = staging.promote()
    except FilesystemStagingError as exc:
        staging.abort()
        return False, {
            "error_type": exc.code,
            "message": "Artifact promotion failed closed; inspect the filesystem receipt.",
        }, exc.receipt or {}
    except Exception:
        staging.abort()
        return False, {
            "error_type": "filesystem_promotion_failed",
            "message": "Artifact promotion failed closed; inspect the filesystem before continuing.",
        }, {}
    return True, project_promoted_artifact_result(projection, receipt), receipt


def rollback_artifact_mutation(*, root: Path, receipt: object) -> dict[str, object]:
    if not isinstance(receipt, dict) or receipt.get("schema_id") != FILESYSTEM_RECEIPT_SCHEMA_ID or receipt.get("status") != "committed":
        raise FilesystemStagingError("filesystem_rollback_invalid")
    safe_root = _safe_root(root)
    transaction_id = str(receipt.get("transaction_id", ""))
    prefix = next((name for name in ("artifact-", "canonical-") if transaction_id.startswith(name)), "")
    if not prefix or not transaction_id[len(prefix):].isalnum():
        raise FilesystemStagingError("filesystem_rollback_invalid")
    rollback_root = safe_root / ROLLBACK_RELATIVE / transaction_id
    target_relative = OUTPUT_RELATIVE if prefix == "artifact-" else Path(".")
    output_root = safe_root / target_relative
    stored_path = rollback_root / "receipt.json"
    _verify_existing_chain(safe_root, rollback_root.relative_to(safe_root))
    if stored_path.is_symlink():
        raise FilesystemStagingError("filesystem_rollback_invalid")
    try:
        stored = json.loads(stored_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FilesystemStagingError("filesystem_rollback_invalid") from exc
    base = {key: value for key, value in receipt.items() if key != "receipt_id"}
    if stored != receipt or receipt.get("receipt_id") != f"filesystem:{_json_digest(base)}":
        raise FilesystemStagingError("filesystem_rollback_invalid")
    changes = receipt.get("changes") if isinstance(receipt.get("changes"), list) else []
    attempt_root = rollback_root / f"attempt-{uuid.uuid4().hex}"
    with runtime_state_transaction(lock_path=rollback_root.parent / ".artifact-filesystem.lock"):
        for change in changes:
            if not isinstance(change, dict):
                raise FilesystemStagingError("filesystem_rollback_invalid")
            try:
                relative = _relative_to_target(str(change.get("path", "")), target_relative)
            except (ValueError, FilesystemStagingError) as exc:
                raise FilesystemStagingError("filesystem_rollback_invalid") from exc
            destination = output_root / relative
            _verify_existing_chain(safe_root, destination.parent.relative_to(safe_root))
            if not destination.exists() or destination.is_symlink() or _file_digest(destination) != change.get("new_digest"):
                raise FilesystemStagingError("filesystem_rollback_conflict")
        for change in changes:
            relative = _relative_to_target(str(change["path"]), target_relative)
            if change.get("prior_digest"):
                backup = rollback_root / "files" / relative
                _verify_existing_chain(safe_root, backup.parent.relative_to(safe_root))
                if not backup.exists() or backup.is_symlink() or _file_digest(backup) != change["prior_digest"]:
                    raise FilesystemStagingError("filesystem_rollback_invalid")
        applied: list[tuple[dict[str, object], Path]] = []
        try:
            attempt_root.mkdir(mode=0o700)
            for change in reversed(changes):
                relative = _relative_to_target(str(change["path"]), target_relative)
                destination = output_root / relative
                current = attempt_root / relative
                current.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                shutil.copy2(destination, current, follow_symlinks=False)
                if change.get("prior_digest"):
                    shutil.copy2(rollback_root / "files" / relative, destination, follow_symlinks=False)
                else:
                    destination.unlink()
                applied.append((change, current))
        except Exception as exc:
            compensation_ok = True
            for change, current in reversed(applied):
                try:
                    relative = _relative_to_target(str(change["path"]), target_relative)
                    destination = output_root / relative
                    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    os.replace(current, destination)
                except Exception:
                    compensation_ok = False
            if compensation_ok:
                _safe_remove_tree(attempt_root, rollback_root)
            raise FilesystemStagingError(
                "filesystem_rollback_invalid" if compensation_ok else "filesystem_compensation_failed"
            ) from exc
    _safe_remove_tree(attempt_root, rollback_root)
    completed = {**receipt, "status": "rolled_back", "completed_at": _now()}
    completed_base = {key: value for key, value in completed.items() if key != "receipt_id"}
    completed["receipt_id"] = f"filesystem:{_json_digest(completed_base)}"
    atomic_write_json(rollback_root / "receipt.json", completed, sort_keys=True)
    return completed
