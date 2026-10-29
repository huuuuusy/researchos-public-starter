# ResearchOS maintenance header.
# 中文：dashboard 运行时只读路径边界；把逻辑路径解析、公开 allowlist 和无符号链接安全投影集中到一个 owner。
# English: Dashboard runtime read boundary; owns logical-path resolution, the public allowlist, and a symlink-free safe projection.

"""Fail-closed runtime read roots shared by previews, source browsing, and Codex."""

from __future__ import annotations

import json
import posixpath
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


PUBLIC_READ_MANIFEST = Path("config/public-runtime-read-manifest.json")
PUBLIC_READ_MANIFEST_SCHEMA = "researchos-public-runtime-read-manifest-v1"
PUBLIC_READ_MANIFEST_KEYS = frozenset({"schema_id", "version", "files"})


class RuntimeReadBoundaryError(ValueError):
    """Raised when a runtime read crosses its configured logical root."""


def normalized_relative_path(value: object) -> str:
    raw = str(value or "").strip().replace("\\", "/")
    candidate = Path(raw)
    if raw.startswith("/") or candidate.is_absolute() or ".." in candidate.parts:
        raise RuntimeReadBoundaryError("Runtime read path not allowed")
    value = candidate.as_posix().strip("/") if raw else ""
    return "" if value in {"", "."} else value


def load_public_read_manifest(root: Path) -> tuple[str, ...]:
    """Load a server-owned exact-file manifest without granting directory prefixes."""
    repository = root.resolve()
    manifest = repository / PUBLIC_READ_MANIFEST
    if manifest.is_symlink() or not manifest.is_file():
        raise RuntimeReadBoundaryError("Public runtime read manifest is missing or unsafe")
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeReadBoundaryError("Public runtime read manifest is invalid") from exc
    if not isinstance(payload, dict) or set(payload) != PUBLIC_READ_MANIFEST_KEYS:
        raise RuntimeReadBoundaryError("Public runtime read manifest has an invalid schema")
    version = payload.get("version")
    if (
        payload.get("schema_id") != PUBLIC_READ_MANIFEST_SCHEMA
        or not isinstance(version, str)
        or not version.strip()
        or version != version.strip()
    ):
        raise RuntimeReadBoundaryError("Public runtime read manifest has an invalid schema")
    raw_files = payload.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise RuntimeReadBoundaryError("Public runtime read manifest files must be a non-empty list")

    allowed: list[str] = []
    seen: set[str] = set()
    for raw in raw_files:
        if not isinstance(raw, str) or not raw or raw != raw.strip() or any(char in raw for char in "*?["):
            raise RuntimeReadBoundaryError("Public runtime read manifest contains an invalid file path")
        try:
            relative = normalized_relative_path(raw)
            resolved = (repository / relative).resolve()
            resolved_relative = resolved.relative_to(repository).as_posix()
        except (OSError, RuntimeReadBoundaryError, ValueError) as exc:
            raise RuntimeReadBoundaryError("Public runtime read manifest contains an unsafe file path") from exc
        if not relative or raw != relative or relative in seen or resolved_relative != relative:
            raise RuntimeReadBoundaryError("Public runtime read manifest contains a non-exact file path")
        source = repository / relative
        if source.exists() and (source.is_symlink() or not source.is_file()):
            raise RuntimeReadBoundaryError("Public runtime read manifest entries must be regular files")
        seen.add(relative)
        allowed.append(relative)
    return tuple(allowed)


@dataclass(frozen=True)
class RuntimeReadBoundary:
    """Resolve logical paths below one root and optionally enforce an allowlist."""

    root: Path
    allowed_directories: tuple[str, ...] = ()
    allowed_files: tuple[str, ...] = ()
    unrestricted: bool = False

    @classmethod
    def private(cls, root: Path) -> "RuntimeReadBoundary":
        return cls(root=root.resolve(), unrestricted=True)

    @classmethod
    def public_starter(cls, root: Path) -> "RuntimeReadBoundary":
        repository = root.resolve()
        return cls(
            root=repository,
            allowed_files=load_public_read_manifest(repository),
        )

    @classmethod
    def personal_vault(cls, repository_root: Path, vault_root: Path) -> "RuntimeReadBoundary":
        repository = repository_root.resolve()
        vault = vault_root.resolve()
        try:
            vault_relative = vault.relative_to(repository).as_posix()
        except ValueError:
            return cls.private(vault)
        return cls(
            root=repository,
            allowed_directories=(vault_relative,),
            allowed_files=load_public_read_manifest(repository),
        )

    def runtime_services(self) -> tuple[object, object, object]:
        """Create preview, tree, and local-open services that share this boundary."""
        from researchos_server.local_file_bridge import LocalFileBridge
        from researchos_server.preview_file_server import PreviewFileServer
        from researchos_server.source_tree_store import SourceTreeStore

        preview = PreviewFileServer(root=self.root, read_boundary=self)
        source_tree = SourceTreeStore(root=self.root, read_boundary=self)
        return preview, source_tree, LocalFileBridge(root=self.root, source_tree=source_tree)

    def codex_runtime(
        self,
        *,
        public_starter: bool,
        write_root: Path,
        public_codex_root: Path,
        codex_factory: Callable[..., object],
        command_runner_factory: Callable[..., object],
        model_catalog_factory: Callable[..., object],
        log_jsonl: Path,
        log_md: Path,
        post_run_refresh: Callable[[], dict[str, object]] | None,
    ) -> object:
        """Build a Codex runner whose cwd is never the public repository root."""
        if not public_starter and not callable(post_run_refresh):
            raise ValueError("Personal-vault runner requires post-run refresh")
        codex_root = public_codex_root.resolve() if public_starter else write_root.resolve()
        command_runner = command_runner_factory(root=codex_root)
        return codex_factory(
            root=codex_root,
            command_runner=command_runner,
            log_jsonl=log_jsonl,
            log_md=log_md,
            model_catalog=model_catalog_factory(root=codex_root, command_runner=command_runner),
            public_starter=public_starter,
            runtime_scope="public_starter" if public_starter else "personal_vault",
            reference_root=public_codex_root.resolve(),
            post_run_refresh=None if public_starter else post_run_refresh,
        )

    def is_allowed_relative(self, relative: object) -> bool:
        try:
            value = normalized_relative_path(relative)
        except RuntimeReadBoundaryError:
            return False
        if self.unrestricted or not value:
            return True
        if value in self.allowed_files:
            return True
        for allowed in self.allowed_directories:
            if value == allowed or value.startswith(f"{allowed}/") or allowed.startswith(f"{value}/"):
                return True
        return any(allowed.startswith(f"{value}/") for allowed in self.allowed_files)

    def resolve(self, requested: object = "") -> Path:
        relative = normalized_relative_path(requested)
        lexical = self.root / relative
        target = lexical.resolve()
        try:
            resolved_relative = target.relative_to(self.root.resolve()).as_posix()
        except ValueError as exc:
            raise RuntimeReadBoundaryError("Runtime read path outside configured root") from exc
        if not self.is_allowed_relative(relative) or not self.is_allowed_relative(resolved_relative):
            raise RuntimeReadBoundaryError("Runtime read path is not available in this mode")
        return target

    def allows_path(self, path: Path) -> bool:
        lexical = path if path.is_absolute() else self.root / path
        try:
            lexical_relative = lexical.absolute().relative_to(self.root.resolve()).as_posix()
            resolved_relative = lexical.resolve().relative_to(self.root.resolve()).as_posix()
        except (OSError, ValueError):
            return False
        return self.is_allowed_relative(lexical_relative) and self.is_allowed_relative(resolved_relative)

    def relative_path(self, path: Path) -> str:
        try:
            relative = path.resolve().relative_to(self.root.resolve()).as_posix()
        except (OSError, ValueError):
            return ""
        return relative or "."

    def materialize(self, destination: Path) -> Path:
        """Copy only allowlisted regular files into a symlink-free Codex read root."""
        if self.unrestricted:
            raise RuntimeReadBoundaryError("An unrestricted boundary must not be materialized")
        target_root = destination.resolve()
        try:
            target_root.relative_to(self.root.resolve())
        except ValueError:
            pass
        else:
            raise RuntimeReadBoundaryError("Public Codex read root must stay outside the repository")
        lexical_target = Path(destination)
        if lexical_target.is_symlink():
            raise RuntimeReadBoundaryError("Public Codex read root must not be a symbolic link")
        if target_root.exists():
            if not target_root.is_dir() or any(target_root.iterdir()):
                raise RuntimeReadBoundaryError("Public Codex read root must be an empty directory")
        else:
            target_root.mkdir(parents=True)
        for relative in self.allowed_files:
            source = self.root / relative
            if not source.exists():
                continue
            if source.is_symlink() or not source.is_file() or self.resolve(relative) != source.resolve():
                raise RuntimeReadBoundaryError("Public runtime manifest source is no longer a regular file")
            output = target_root / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, output, follow_symlinks=False)
        return target_root

    @staticmethod
    def public_dashboard_data_blocked(request_path: str, public_starter: bool) -> bool:
        normalized = ("/" + posixpath.normpath(str(request_path or "")).lstrip("/")).lower()
        return bool(
            public_starter
            and normalized.startswith("/data/")
            and normalized != "/data/researchos-dashboard.json"
        )
