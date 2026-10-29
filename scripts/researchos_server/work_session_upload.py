# ResearchOS maintenance header.
# 中文：工作会话本地上传 owner；只保存到被 Git 忽略的运行目录，不进入 canonical memory。
# English: Local work-session upload owner; stores only in a Git-ignored runtime directory, never canonical memory.

"""User-controlled local file intake for dashboard work sessions."""

from __future__ import annotations

import re
import shutil
import unicodedata
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from urllib.parse import unquote


class WorkSessionUploadError(ValueError):
    """A user-recoverable local intake error with a stable API code."""

    def __init__(self, message: str, error_type: str = "invalid_upload") -> None:
        super().__init__(message)
        self.error_type = error_type


def upload_request_metadata(headers: object) -> tuple[str, int]:
    """Resolve the binary upload contract from HTTP-like headers."""
    getter = getattr(headers, "get", lambda *_: "")
    try:
        content_length = int(getter("Content-Length", "0"))
    except (TypeError, ValueError):
        content_length = 0
    filename = unquote(str(getter("X-ResearchOS-Filename", "")))
    if content_length <= 0 or not filename:
        raise WorkSessionUploadError("Missing upload filename or content")
    return filename, content_length


@dataclass(frozen=True)
class WorkSessionUploadStore:
    root: Path
    working_copy_notice_bytes: int = 1024 * 1024 * 1024
    low_disk_notice_bytes: int = 5 * 1024 * 1024 * 1024
    low_disk_notice_ratio: float = 0.05

    def __post_init__(self) -> None:
        lexical_root = Path(self.root)
        try:
            if lexical_root.is_symlink():
                raise WorkSessionUploadError(
                    "Local upload root cannot be a symbolic link",
                    "unsafe_upload_path",
                )
            canonical_root = lexical_root.resolve(strict=False)
        except WorkSessionUploadError:
            raise
        except (OSError, RuntimeError) as exc:
            raise WorkSessionUploadError(
                "Local upload root is unavailable",
                "unsafe_upload_path",
            ) from exc
        if canonical_root.exists() and not canonical_root.is_dir():
            raise WorkSessionUploadError(
                "Local upload root is not a directory",
                "unsafe_upload_path",
            )
        object.__setattr__(self, "root", canonical_root)
        self._validated_upload_dir(create=False)

    @property
    def upload_dir(self) -> Path:
        return self.root / "06_active_context" / "work_state" / "uploads"

    def _validated_upload_dir(self, *, create: bool) -> Path:
        """Return the managed directory only when every descendant is non-symlinked."""
        try:
            if self.root.is_symlink():
                raise WorkSessionUploadError(
                    "Local upload root cannot be a symbolic link",
                    "unsafe_upload_path",
                )
            if self.root.exists():
                if not self.root.is_dir() or self.root.resolve(strict=True) != self.root:
                    raise WorkSessionUploadError(
                        "Local upload root could not be verified",
                        "unsafe_upload_path",
                    )
            elif create:
                self.root.mkdir(parents=True)
            else:
                return self.upload_dir
        except WorkSessionUploadError:
            raise
        except (OSError, RuntimeError) as exc:
            raise WorkSessionUploadError(
                "Local upload root could not be verified",
                "unsafe_upload_path",
            ) from exc
        current = self.root
        for part in Path("06_active_context/work_state/uploads").parts:
            current = current / part
            try:
                if current.is_symlink():
                    raise WorkSessionUploadError(
                        "Local upload path cannot contain symbolic links",
                        "unsafe_upload_path",
                    )
                if current.exists():
                    if not current.is_dir():
                        raise WorkSessionUploadError(
                            "Local upload path is not a directory",
                            "unsafe_upload_path",
                        )
                elif create:
                    current.mkdir()
                else:
                    return self.upload_dir
                resolved = current.resolve(strict=True)
            except WorkSessionUploadError:
                raise
            except (OSError, RuntimeError) as exc:
                raise WorkSessionUploadError(
                    "Local upload path could not be verified",
                    "unsafe_upload_path",
                ) from exc
            if not resolved.is_relative_to(self.root):
                raise WorkSessionUploadError(
                    "Local upload path escapes the repository root",
                    "unsafe_upload_path",
                )
        return self.upload_dir

    def _unlink_generated_path_if_safe(self, path: Path) -> None:
        """Best-effort cleanup that refuses to traverse a replaced upload directory."""
        try:
            upload_dir = self._validated_upload_dir(create=False)
            if path.parent != upload_dir or path.is_symlink():
                return
            path.unlink(missing_ok=True)
        except (OSError, WorkSessionUploadError):
            return

    def save_stream(self, filename: object, stream: BinaryIO, content_length: int) -> dict[str, object]:
        """Stream one user-selected attachment to disk.

        ResearchOS does not reject or evict user material because of an arbitrary
        product quota. The actual ceiling is the local filesystem/runtime. The
        returned storage receipt is advisory and never triggers deletion.
        """
        safe_name = self.safe_filename(filename)
        suffix = Path(safe_name).suffix.lower()
        expected = int(content_length)
        if expected <= 0:
            raise WorkSessionUploadError("Work-session upload is empty", "empty_file")
        stem = Path(safe_name).stem[:80] or "source"
        upload_dir = self._validated_upload_dir(create=True)
        target = upload_dir / f"{stem}-{uuid.uuid4().hex[:10]}{suffix}"
        temporary = target.with_suffix(f"{target.suffix}.{uuid.uuid4().hex}.tmp")
        written = 0
        try:
            self._validated_upload_dir(create=False)
            with temporary.open("xb") as handle:
                remaining = expected
                while remaining:
                    chunk = stream.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise WorkSessionUploadError(
                            "Work-session upload ended before the declared size",
                            "incomplete_file",
                        )
                    handle.write(chunk)
                    written += len(chunk)
                    remaining -= len(chunk)
            self._validated_upload_dir(create=False)
            temporary.replace(target)
        except WorkSessionUploadError:
            self._unlink_generated_path_if_safe(temporary)
            raise
        except OSError as exc:
            self._unlink_generated_path_if_safe(temporary)
            raise WorkSessionUploadError(
                "Local storage could not save the selected file; no existing material was deleted",
                "storage_unavailable",
            ) from exc
        return {
            "ok": True,
            "name": safe_name,
            "path": target.relative_to(self.root).as_posix(),
            "size": written,
            "sensitivity": "local_runtime",
            "ownership": "user_controlled_session_material",
            "storage": self.storage_receipt(),
        }

    def storage_receipt(self) -> dict[str, object]:
        """Describe local footprint without governing or deleting user material."""
        files = 0
        used_bytes = 0
        upload_dir = self._validated_upload_dir(create=False)
        if upload_dir.exists():
            for path in upload_dir.iterdir():
                if path.is_symlink() or not path.is_file() or path.name.endswith(".tmp"):
                    continue
                try:
                    used_bytes += path.stat().st_size
                    files += 1
                except OSError:
                    continue
        try:
            disk = shutil.disk_usage(self.root)
            available_bytes = disk.free
            low_disk = disk.free < max(
                max(0, int(self.low_disk_notice_bytes)),
                int(disk.total * max(0.0, float(self.low_disk_notice_ratio))),
            )
        except OSError:
            available_bytes = -1
            low_disk = False
        notice_code = ""
        if low_disk:
            notice_code = "low_disk_space"
        elif used_bytes >= max(1, int(self.working_copy_notice_bytes)):
            notice_code = "working_copies_large"
        return {
            "auto_delete": False,
            "available_bytes": available_bytes,
            "files": files,
            "managed_scope": "system_generated_runtime_only",
            "notice_code": notice_code,
            "used_bytes": used_bytes,
        }

    def cleanup_generated_temporaries(self) -> dict[str, int]:
        """Remove only atomic-write leftovers created by this owner.

        Completed attachments are user-controlled session material. They are
        never deleted here because of age, count, or total size.
        """
        upload_dir = self._validated_upload_dir(create=False)
        if not upload_dir.exists():
            return {"removed_bytes": 0, "removed_files": 0}
        removed_bytes = 0
        removed_files = 0
        for path in upload_dir.iterdir():
            if path.is_symlink() or not path.is_file() or not path.name.endswith(".tmp"):
                continue
            try:
                stat = path.stat()
                path.unlink()
                removed_bytes += stat.st_size
                removed_files += 1
            except OSError:
                continue
        return {
            "removed_bytes": removed_bytes,
            "removed_files": removed_files,
        }

    @staticmethod
    def safe_filename(value: object) -> str:
        name = unicodedata.normalize("NFC", Path(str(value or "").replace("\\", "/")).name.strip())
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]+', "_", name)
        name = re.sub(r"\s+", " ", name).strip(" .")
        if not name:
            raise WorkSessionUploadError("Work-session upload filename is empty")
        if len(name) <= 140:
            return name
        original_suffix = Path(name).suffix
        suffix = original_suffix[:32]
        stem = name[:-len(original_suffix)] if original_suffix else name
        bounded_stem = stem[:max(1, 140 - len(suffix))].rstrip(" .")
        return f"{bounded_stem or 'source'}{suffix}"
