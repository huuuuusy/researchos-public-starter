# ResearchOS maintenance header.
# 中文：原子文件替换与跨进程锁的唯一 owner，属 kernel 层、只用标准库；内核账本、server 与 data 都从这里导入。
# English: The one owner of atomic file replacement and the cross-process lock; kernel layer, stdlib only, imported by the kernel ledger, server and data.

"""Atomic file replacement and the sibling-lock transaction every writer of a runtime file takes.

It lives in the kernel so that the kernel ledger, the server stores and the data owners write and
lock the same way without any of them depending on a layer above it.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - supported deployments are POSIX; fail closed when a file lock is requested.
    fcntl = None


RUNTIME_STATE_LOCK = RLock()


def lock_path_for(path: Path) -> Path:
    """The sibling ``.{name}.lock`` that every writer of ``path`` takes; two writers must name the same file."""
    return path.with_name(f".{path.name}.lock")


@contextmanager
def runtime_state_transaction(*, lock_path: Path | None = None) -> Iterator[None]:
    with RUNTIME_STATE_LOCK:
        if lock_path is None:
            yield
            return
        if fcntl is None:
            raise RuntimeError("cross_process_runtime_lock_unavailable")
        path = Path(lock_path)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags, 0o600)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise RuntimeError("cross_process_runtime_lock_invalid")
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def fsync_dir(path: Path) -> None:
    """Flush a directory so a rename, link or unlink inside it survives a crash."""
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_bytes(path: Path, content: bytes, *, mode: int | None = None) -> None:
    """Replace ``path`` through a private (0o600) sibling; ``mode`` sets other permissions first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temp_path, mode)
        os.replace(temp_path, path)
        fsync_dir(path.parent)  # the rename itself must reach disk, not only the bytes
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    atomic_write_bytes(path, text.encode(encoding))


def atomic_write_json(path: Path, value: object, *, sort_keys: bool = False) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=sort_keys, indent=2) + "\n")


def append_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding=encoding) as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
