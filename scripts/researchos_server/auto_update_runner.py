# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard server 中关于「auto update runner」的辅助 owner；保持 serve_dashboard.py 只做 HTTP 编排。
# English: Helper owner for auto update runner in the local ResearchOS dashboard server; keeps serve_dashboard.py HTTP-orchestration-only.

"""Auto-update orchestration for the local ResearchOS dashboard server."""

from __future__ import annotations

import shutil
import hashlib
import json
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from researchos_data.maintenance_pipeline import RESEARCHOS_MAINTENANCE_STEPS, maintenance_command

from researchos_adapters.command_runner import CommandRunner


@dataclass(frozen=True)
class AutoUpdateStep:
    label: str
    args: tuple[str, ...]
    timeout: int = 90
    optional: bool = False
    id: str = ""
    execution_policy: str = "observe"
    writes: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()


def default_auto_update_steps() -> tuple[AutoUpdateStep, ...]:
    return tuple(
        AutoUpdateStep(
            str(step["label"]),
            maintenance_command(step, python_executable=sys.executable),
            int(step["timeout"]),
            bool(step["optional"]),
            str(step["id"]),
            str(step["execution_policy"]),
            tuple(str(path) for path in step.get("writes", ())),
            tuple(str(step_id) for step_id in step.get("depends_on", ())),
        )
        for step in RESEARCHOS_MAINTENANCE_STEPS
    )


def normalized_write_targets(steps: list[AutoUpdateStep]) -> tuple[Path, ...]:
    """Return minimal repository-relative write owners and reject traversal."""
    candidates: list[Path] = []
    for raw in (write for step in steps for write in step.writes):
        value = str(raw or "").strip().replace("\\", "/").rstrip("/")
        relative = Path(value)
        if not value or relative.is_absolute() or ".." in relative.parts or relative.parts[0] == ".git":
            raise ValueError(f"unsafe maintenance write target: {raw}")
        if relative not in candidates:
            candidates.append(relative)
    minimal: list[Path] = []
    for relative in sorted(candidates, key=lambda path: (len(path.parts), path.as_posix())):
        if any(relative == owner or owner in relative.parents for owner in minimal):
            continue
        minimal.append(relative)
    return tuple(minimal)


def first_symlink_prefix(root: Path, relative: Path) -> Path | None:
    """Return the first symlink node without following a repository-relative path."""
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return cursor
    return None


@dataclass
class WriteSnapshot:
    root: Path
    targets: tuple[Path, ...]
    temporary: Path
    entries: tuple[tuple[Path, str, Path], ...]
    retain_on_close: bool = False

    @classmethod
    def capture(cls, root: Path, targets: tuple[Path, ...]) -> "WriteSnapshot":
        resolved_root = Path(root).resolve()
        temporary = Path(tempfile.mkdtemp(prefix="researchos-evolution-"))
        backup_root = temporary
        entries: list[tuple[Path, str, Path]] = []
        try:
            for index, relative in enumerate(targets):
                target = resolved_root / relative
                symlink_prefix = first_symlink_prefix(resolved_root, relative)
                if symlink_prefix is not None:
                    raise ValueError(f"maintenance write target crosses a symlink: {relative}")
                try:
                    target.parent.resolve().relative_to(resolved_root)
                except ValueError as error:
                    raise ValueError(f"maintenance write target escapes repository: {relative}") from error
                if target.exists():
                    try:
                        target.resolve().relative_to(resolved_root)
                    except ValueError as error:
                        raise ValueError(f"maintenance write target escapes repository: {relative}") from error
                backup = backup_root / str(index)
                if target.is_dir():
                    nested_symlink = next((path for path in target.rglob("*") if path.is_symlink()), None)
                    if nested_symlink is not None:
                        raise ValueError(f"maintenance write owner contains a symlink: {nested_symlink.relative_to(resolved_root)}")
                    shutil.copytree(target, backup, symlinks=True)
                    kind = "directory"
                elif target.exists():
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup)
                    kind = "file"
                else:
                    kind = "missing"
                entries.append((relative, kind, backup))
        except Exception:
            shutil.rmtree(temporary)
            raise
        return cls(resolved_root, targets, temporary, tuple(entries))

    def restore(self) -> dict[str, object]:
        # The command runner has no attested per-file mutation receipt. A path
        # allowlist cannot distinguish its writes from concurrent human edits.
        # Preserve changed targets and retain the snapshot for reconciliation.
        restored: list[str] = []
        errors: list[str] = []
        unchanged: list[str] = []
        def signature(path: Path):
            if path.is_symlink():
                raise ValueError("changed path crosses a symlink")
            if path.is_file():
                return ("file", hashlib.sha256(path.read_bytes()).hexdigest())
            if path.is_dir():
                return ("directory", tuple((p.name, signature(p)) for p in sorted(path.iterdir())))
            if path.exists():
                raise ValueError("unsupported path type")
            return ("missing",)
        for relative, kind, backup in self.entries:
            target = self.root / relative
            try:
                symlink_prefix = first_symlink_prefix(self.root, relative)
                if symlink_prefix is not None:
                    raise ValueError("changed path crosses a symlink")
                target.parent.resolve().relative_to(self.root)
                expected = ("missing",) if kind == "missing" else signature(backup)
                if signature(target) != expected:
                    raise ValueError("rollback conflict: changed target has no attributable mutation receipt")
                unchanged.append(relative.as_posix())
            except (OSError, ValueError) as error:
                errors.append(f"{relative.as_posix()}: {error}")
        recovery_directory = ""
        if errors:
            self.retain_on_close = True
            recovery_directory = str(self.temporary)
            manifest = [{"target": str(relative), "kind": kind, "backup": backup.name}
                        for relative, kind, backup in self.entries]
            try:
                (self.temporary / "recovery-manifest.json").write_text(json.dumps(manifest, indent=2))
            except OSError as error:
                errors.append(f"recovery manifest: {error}")
        return {
            "attempted": bool(self.entries),
            "ok": not errors,
            "restored": restored,
            "errors": errors,
            "unchanged": unchanged,
            "recovery_directory": recovery_directory,
        }

    def close(self) -> None:
        if not self.retain_on_close:
            shutil.rmtree(self.temporary)


@dataclass
class AutoUpdateRunner:
    command_runner: CommandRunner
    steps: tuple[AutoUpdateStep, ...] = field(default_factory=default_auto_update_steps)

    def run_step(self, step: AutoUpdateStep) -> dict[str, object]:
        return self.command_runner.run_step(
            step.label,
            list(step.args),
            timeout=step.timeout,
            optional=step.optional,
        )

    def run(self, step_ids: list[str] | tuple[str, ...] | None = None) -> dict[str, object]:
        requested = None if step_ids is None else tuple(dict.fromkeys(str(step_id) for step_id in step_ids if str(step_id)))
        known_ids = {step.id for step in self.steps if step.id}
        unknown_ids = [] if requested is None else [step_id for step_id in requested if step_id not in known_ids]
        if unknown_ids:
            return {
                "ok": False,
                "external_partial": False,
                "executed_step_ids": [],
                "steps": [],
                "message": f"unknown maintenance step ids: {', '.join(unknown_ids)}",
            }
        selected = list(self.steps) if requested is None else [step for step in self.steps if step.id in requested]
        selected_ids = {step.id for step in selected if step.id}
        seen: set[str] = set()
        for step in selected:
            invalid = [dependency for dependency in step.depends_on
                       if dependency not in known_ids or (dependency in selected_ids and dependency not in seen)]
            if invalid or (step.id and step.id in seen):
                return {
                    "ok": False, "external_partial": False,
                    "executed_step_ids": [], "steps": [],
                    "message": f"invalid maintenance dependency order or identity: {step.id}",
                }
            if step.id:
                seen.add(step.id)
        try:
            write_targets = normalized_write_targets(selected)
            snapshot = WriteSnapshot.capture(Path(self.command_runner.root), write_targets) if write_targets else None
        except (AttributeError, OSError, ValueError) as error:
            return {
                "ok": False,
                "external_partial": False,
                "executed_step_ids": [],
                "steps": [],
                "message": f"maintenance write snapshot failed: {error}",
                "rollback": {"attempted": False, "ok": False, "restored": [], "errors": [str(error)]},
            }
        started = datetime.now()
        results: list[dict[str, object]] = []
        outcomes: dict[str, bool] = {}
        executed_step_ids: list[str] = []
        blocked_step_ids: list[str] = []
        for step in selected:
            blocked_by = [dependency for dependency in step.depends_on
                          if dependency in selected_ids and not outcomes.get(dependency, False)]
            if blocked_by:
                results.append({
                    "id": step.id, "label": step.label, "ok": False,
                    "required_ok": False, "optional": step.optional,
                    "returncode": "dependency_blocked", "seconds": 0,
                    "output": "Not executed; prerequisite did not succeed: " + ", ".join(blocked_by),
                    "blocked_by": blocked_by,
                })
                blocked_step_ids.append(step.id)
                outcomes[step.id] = False
                continue
            if step.id:
                executed_step_ids.append(step.id)
            try:
                results.append(self.run_step(step))
            except Exception as error:  # Keep the rollback path alive if a runner adapter fails unexpectedly.
                results.append({
                    "label": step.label,
                    "ok": False,
                    "required_ok": False,
                    "optional": step.optional,
                    "returncode": "runner_error",
                    "seconds": 0,
                    "output": str(error),
                })
            results[-1]["id"] = step.id
            # A prerequisite must actually succeed, even if optional for the batch.
            outcomes[step.id] = results[-1].get("ok") is True
        finished = datetime.now()
        required_ok = all(result["required_ok"] for result in results if not result["optional"])
        optional_failed = [result for result in results if result["optional"] and not result["required_ok"]]
        rollback = {"attempted": False, "ok": True, "restored": [], "errors": []}
        if not required_ok and snapshot is not None:
            rollback = snapshot.restore()
        if snapshot is not None:
            snapshot.close()
        return {
            "ok": required_ok,
            "external_partial": bool(optional_failed),
            "started_at": started.isoformat(timespec="seconds"),
            "finished_at": finished.isoformat(timespec="seconds"),
            "seconds": round((finished - started).total_seconds(), 2),
            "executed_step_ids": executed_step_ids,
            "blocked_step_ids": blocked_step_ids,
            "steps": results,
            "message": "local update completed" if required_ok else "local update failed",
            "rollback": rollback,
        }
