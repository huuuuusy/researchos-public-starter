# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard server 中关于「local file bridge」的显式点击 owner；只允许打开或 Finder 显示 allowlist root 内文件。
# English: Explicit-click local-file bridge for the ResearchOS dashboard server; only opens or reveals files inside allowlisted roots.

"""Local file open/reveal helpers for the local ResearchOS dashboard server."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from researchos_server.source_tree_store import LOCAL_OPEN_SUFFIXES, SourceTreeError, SourceTreeStore


@dataclass(frozen=True)
class LocalFileBridge:
    root: Path
    source_tree: SourceTreeStore

    def open_file(self, requested: object) -> dict[str, object]:
        target = self._file_target(requested)
        if target.suffix.lower() not in LOCAL_OPEN_SUFFIXES:
            # Opening hands the file to its default app, which for a script may run it; reveal is still allowed.
            raise SourceTreeError("This file type is not opened from the Dashboard; reveal it instead")
        return self._launch(target, "open")

    def reveal_file(self, requested: object) -> dict[str, object]:
        target = self._file_target(requested)
        return self._launch(target, "reveal")

    def _launch(self, target: Path, action: str) -> dict[str, object]:
        system = platform.system()
        rel = self.source_tree.relative_path(target)
        if system == "Windows":
            try:
                if action == "reveal":
                    result = subprocess.run(
                        ["explorer", "/select,", str(target)],
                        cwd=self.root,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    return self._result(rel, action, result.returncode, result.stderr)
                os.startfile(str(target))  # type: ignore[attr-defined]
                return self._result(rel, action, 0, "")
            except OSError as exc:
                return self._result(rel, action, 1, str(exc))

        if system == "Darwin":
            command = ["open", "-R", str(target)] if action == "reveal" else ["open", str(target)]
        else:
            opener = shutil.which("xdg-open")
            if not opener:
                return {
                    "ok": False,
                    "path": rel,
                    "action": action,
                    "error_type": "unsupported_platform",
                    "returncode": 127,
                    "stderr": "No supported desktop opener found. Open the path manually.",
                }
            command = [opener, str(target.parent if action == "reveal" else target)]

        result = subprocess.run(command, cwd=self.root, check=False, capture_output=True, text=True)
        return self._result(rel, action, result.returncode, result.stderr)

    @staticmethod
    def _result(path: str, action: str, returncode: int, stderr: str) -> dict[str, object]:
        return {
            "ok": returncode == 0,
            "path": path,
            "action": action,
            "returncode": returncode,
            "stderr": stderr[-500:],
        }

    def _file_target(self, requested: object) -> Path:
        target = self.source_tree.resolve_path(requested)
        if not target.exists() or not target.is_file():
            raise SourceTreeError("Local file target not found")
        return target
