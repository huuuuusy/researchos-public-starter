# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard server 中关于「source tree」的只读 owner；负责项目根目录结构、source role 和预览能力。
# English: Read-only source-tree owner for the local ResearchOS dashboard server; owns project-root structure, source roles, and previewability.

"""Read-only source tree helpers for the local ResearchOS dashboard server."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path

from researchos_server.runtime_read_boundary import RuntimeReadBoundary, RuntimeReadBoundaryError


BLOCKED_PARTS = {".git", "__pycache__", "node_modules", ".DS_Store"}
PREVIEWABLE_SUFFIXES = {".md", ".yml", ".yaml", ".pdf"}
# Documents the desktop may open with their default app. Scripts are left out: on some machines the
# default app for a script runs it, and opening a file from the Dashboard must never execute anything.
# LocalFileBridge enforces this set on the server, not only through the UI's `openable` flag.
LOCAL_OPEN_SUFFIXES = {
    ".csv",
    ".doc",
    ".docx",
    ".html",
    ".jpeg",
    ".jpg",
    ".json",
    ".key",
    ".md",
    ".numbers",
    ".pages",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".tex",
    ".txt",
    ".xlsx",
    ".yaml",
    ".yml",
}


class SourceTreeError(ValueError):
    """Raised when a source-tree request crosses the local safety boundary."""


@dataclass(frozen=True)
class SourceTreeStore:
    root: Path
    read_boundary: RuntimeReadBoundary | None = None

    def boundary(self) -> RuntimeReadBoundary:
        return self.read_boundary or RuntimeReadBoundary.private(self.root)

    def resolve_path(self, requested: object = "") -> Path:
        try:
            target = self.boundary().resolve(requested)
        except RuntimeReadBoundaryError as exc:
            raise SourceTreeError(str(exc)) from exc
        relative = self.boundary().relative_path(target)
        if any(part in BLOCKED_PARTS for part in Path(relative).parts):
            raise SourceTreeError("Source path is blocked")
        return target

    def source_role(self, path: Path) -> str:
        rel = self.relative_path(path)
        if rel == ".":
            return "researchos_root"
        if rel == "personal_vault" or rel.startswith("personal_vault/"):
            return "personal_vault_source"
        if rel.startswith("00_identity/") or rel.startswith("01_knowledge/") or rel.startswith("02_decisions/") or rel.startswith("03_cognition/") or rel.startswith("04_people/") or rel.startswith("05_workflows/"):
            return "canonical_source"
        if rel.startswith("06_active_context/ui-") or rel.startswith("06_active_context/work_state/"):
            return "private_runtime_state"
        if rel.startswith("06_active_context/"):
            return "active_context"
        if rel.startswith("07_archive/"):
            return "archive"
        if rel == "08_exports/public_starter" or rel.startswith("08_exports/public_starter/"):
            return "public_demo_source"
        if rel.startswith("08_exports/"):
            return "export_projection"
        if rel.startswith("09_templates/"):
            return "template_or_contract"
        if rel.startswith("dashboard/data/"):
            return "generated_projection"
        if rel.startswith("dashboard/") or rel.startswith("scripts/"):
            return "executable_system"
        if rel.startswith("corpus/"):
            return "raw_material"
        return "workspace_source"

    def sensitivity(self, path: Path) -> str:
        rel = self.relative_path(path)
        if rel == "personal_vault" or rel.startswith("personal_vault/"):
            return "private"
        if rel == "08_exports/public_starter" or rel.startswith("08_exports/public_starter/"):
            return "public"
        if rel.startswith("04_people/") or rel.startswith("corpus/"):
            return "sensitive"
        if rel.startswith("06_active_context/ui-") or rel.startswith("06_active_context/work_state/"):
            return "private"
        return "internal"

    def relative_path(self, path: Path) -> str:
        return self.boundary().relative_path(path)

    def node(self, path: Path, *, include_children: bool = False, child_limit: int = 200) -> dict[str, object]:
        exists = path.exists()
        is_dir = path.is_dir() if exists else False
        suffix = path.suffix.lower()
        stat = path.stat() if exists else None
        rel = self.relative_path(path)
        node = {
            "path": rel,
            "name": path.name if rel != "." else self.root.name,
            "kind": "directory" if is_dir else "file",
            "exists": exists,
            "role": self.source_role(path),
            "sensitivity": self.sensitivity(path),
            "suffix": suffix,
            "mime_type": mimetypes.guess_type(path.name)[0] or "",
            "size_bytes": stat.st_size if stat and path.is_file() else 0,
            "updated_at": int(stat.st_mtime) if stat else 0,
            "previewable": suffix in PREVIEWABLE_SUFFIXES,
            "openable": exists and path.is_file() and suffix in LOCAL_OPEN_SUFFIXES,
            "children": [],
        }
        if include_children and is_dir:
            children = []
            for child in sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
                if child.name in BLOCKED_PARTS or not self.boundary().allows_path(child):
                    continue
                children.append(self.node(child, include_children=False))
                if len(children) >= child_limit:
                    break
            node["children"] = children
            node["child_count"] = len(children)
        return node

    def tree(self, requested: object = "") -> dict[str, object]:
        target = self.resolve_path(requested)
        if not target.exists():
            raise SourceTreeError("Source path not found")
        return {"ok": True, "root": self.relative_path(self.root), "node": self.node(target, include_children=True)}

    def info(self, requested: object = "") -> dict[str, object]:
        target = self.resolve_path(requested)
        if not target.exists():
            raise SourceTreeError("Source path not found")
        return {"ok": True, "root": self.relative_path(self.root), "node": self.node(target, include_children=target.is_dir())}
