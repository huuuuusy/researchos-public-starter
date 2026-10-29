# ResearchOS maintenance header.
# 中文：Codex runner 的 CLI 级权限配置 owner；把服务端权威策略落实为可验证、失败关闭的文件系统边界。
# English: CLI permission-profile owner for the Codex runner; enforces the server authority policy as a verified fail-closed filesystem boundary.

"""Build strict Codex CLI permission profiles for ResearchOS runs."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from researchos_adapters.filesystem_staging import ArtifactStaging, OUTPUT_TARGET


PROFILE_NAME = "researchos-runner-v1"


class RunnerPermissionError(ValueError):
    """Raised when a CLI permission boundary cannot be proven safe."""


@dataclass(frozen=True)
class RunnerLaunchPermissions:
    cwd: Path
    config_args: tuple[str, ...]
    direct_write: bool


def _toml_string(value: object) -> str:
    """JSON strings are valid TOML basic strings for the paths used here."""
    return json.dumps(str(value), ensure_ascii=False)


def _absolute_lexical(path: Path, *, label: str) -> Path:
    candidate = Path(os.path.abspath(os.fspath(path)))
    if not candidate.is_absolute():
        raise RunnerPermissionError(f"{label} must be absolute")
    if candidate.is_symlink() or not candidate.is_dir():
        raise RunnerPermissionError(f"{label} must be an existing non-symlink directory")
    return candidate


def _credential_denies() -> tuple[Path, ...]:
    home = Path.home()
    configured_codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
    codex_homes = {Path(os.path.abspath(os.fspath(home / ".codex"))), Path(os.path.abspath(os.fspath(configured_codex_home)))}
    denied = {
        home / ".ssh",
        home / ".aws",
        home / ".azure",
        home / ".kube",
        home / ".config" / "gh",
        home / ".config" / "gcloud",
        home / ".netrc",
        home / ".npmrc",
    }
    for codex_home in codex_homes:
        # Do not deny CODEX_HOME itself: the CLI still needs its auth bootstrap.
        denied.update(
            {
                codex_home / "auth.json",
                codex_home / "config.toml",
                codex_home / "memories",
                codex_home / "sessions",
            }
        )
    return tuple(sorted((Path(os.path.abspath(os.fspath(path))) for path in denied), key=str))


def _is_direct_artifact_policy(policy: object) -> bool:
    if not isinstance(policy, dict):
        return False
    if policy.get("operation") == "read_only":
        if policy.get("allowed_write_targets") not in (None, []):
            raise RunnerPermissionError("Read-only policy requested write targets")
        return False
    if policy.get("operation") != "create_artifact":
        raise RunnerPermissionError("Unknown runner authority operation")
    if policy.get("allowed_write_targets") != [dict(OUTPUT_TARGET)]:
        raise RunnerPermissionError("Artifact policy requested an unregistered write target")
    if policy.get("network_access") != "disabled" or policy.get("credential_access") != "denied":
        raise RunnerPermissionError("Artifact policy weakened the execution boundary")
    return True


@contextmanager
def isolated_codex_home() -> Iterator[Path]:
    """Give the CLI an empty private home while preserving auth bootstrap only."""
    configured_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    source_auth = Path(os.path.abspath(os.fspath(configured_home / "auth.json")))
    with tempfile.TemporaryDirectory(prefix="researchos-codex-") as directory:
        isolated_home = Path(directory)
        isolated_home.chmod(0o700)
        (isolated_home / "memories").mkdir(mode=0o700)
        if source_auth.exists():
            metadata = source_auth.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                raise RunnerPermissionError("Codex auth bootstrap is not a regular non-symlink file")
            if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
                raise RunnerPermissionError("Codex auth bootstrap is not owned by the current user")
            (isolated_home / "auth.json").symlink_to(source_auth)
        yield isolated_home


def runner_launch_permissions(
    *, root: Path, reference_root: Path, authority_policy: object, codex_home: Path,
    artifact_staging: ArtifactStaging | None = None,
) -> RunnerLaunchPermissions:
    """Return a strict inline profile and a verified execution directory."""
    safe_root = _absolute_lexical(root, label="ResearchOS root")
    safe_reference = _absolute_lexical(reference_root, label="Reference root")
    direct_write = _is_direct_artifact_policy(authority_policy)
    if direct_write and artifact_staging is None:
        raise RunnerPermissionError("Artifact execution requires a verified working copy")
    try:
        output_root = artifact_staging.verify_for_launch(root=safe_root, authority_policy=authority_policy) if direct_write else None
    except (OSError, ValueError) as exc:
        raise RunnerPermissionError("Artifact working copy could not be verified") from exc

    filesystem: dict[str, str] = {":root": "deny", ":minimal": "read"}
    filesystem[str(safe_root)] = "read"
    filesystem[str(safe_reference)] = "read"
    for denied in _credential_denies():
        filesystem[str(denied)] = "deny"
    for isolated_private in ("auth.json", "config.toml", "sessions"):
        filesystem[str(codex_home / isolated_private)] = "deny"
    if output_root is not None:
        filesystem[str(output_root)] = "write"

    filesystem_config = ",".join(
        f"{_toml_string(path)}={_toml_string(mode)}" for path, mode in filesystem.items()
    )
    profile = (
        "{description=\"ResearchOS server-owned runner boundary\","
        f"filesystem={{{filesystem_config}}},network={{enabled=false}}}}"
    )
    return RunnerLaunchPermissions(
        cwd=output_root or safe_root,
        direct_write=direct_write,
        config_args=(
            "--disable",
            "memories",
            "-c",
            f'default_permissions="{PROFILE_NAME}"',
            "-c",
            f"permissions.{PROFILE_NAME}={profile}",
        ),
    )
