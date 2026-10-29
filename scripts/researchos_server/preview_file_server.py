# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard server 中关于「preview file server」的辅助 owner；保持 serve_dashboard.py 只做 HTTP 编排。
# English: Helper owner for preview file server in the local ResearchOS dashboard server; keeps serve_dashboard.py HTTP-orchestration-only.

"""Markdown and PDF preview serving rules for the local dashboard server."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs

from researchos_server.runtime_read_boundary import RuntimeReadBoundary, RuntimeReadBoundaryError


@dataclass(frozen=True)
class PreviewFileServer:
    root: Path
    read_boundary: RuntimeReadBoundary | None = None

    def boundary(self) -> RuntimeReadBoundary:
        return self.read_boundary or RuntimeReadBoundary.private(self.root)

    def resolve_markdown_path(self, requested: str) -> Path | None:
        if not requested.lower().endswith((".md", ".yml", ".yaml")):
            return None
        try:
            return self.boundary().resolve(requested)
        except RuntimeReadBoundaryError:
            return None

    def markdown_target(self, requested: str) -> Path | None:
        target = self.resolve_markdown_path(requested)
        if target is None:
            return None
        if not target.exists() or not target.is_file():
            return None
        return target

    def resolve_pdf_path(self, requested: str) -> Path | None:
        if not requested.lower().endswith(".pdf"):
            return None
        try:
            return self.boundary().resolve(requested)
        except RuntimeReadBoundaryError:
            return None

    def pdf_target(self, requested: str) -> Path | None:
        target = self.resolve_pdf_path(requested)
        if target is None:
            return None
        if not target.exists() or not target.is_file():
            return None
        return target

    def serve_markdown_preview(self, handler: object, query: str) -> None:
        params = parse_qs(query)
        requested = params.get("path", [""])[0]
        target = self.resolve_markdown_path(requested)
        if target is None:
            handler.send_error(404, "Markdown preview path not allowed")
            return
        if not target.exists() or not target.is_file():
            handler.send_error(404, "Markdown preview file not found")
            return
        data = target.read_bytes()
        handler.send_response(200)
        handler.send_header("Content-Type", "text/plain; charset=utf-8")
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)

    def serve_pdf_preview(self, handler: object, query: str, head_only: bool = False) -> None:
        params = parse_qs(query)
        self.serve_pdf_file(handler, params.get("path", [""])[0], head_only=head_only)

    def serve_pdf_file(self, handler: object, requested: str, head_only: bool = False) -> None:
        target = self.resolve_pdf_path(requested)
        if target is None:
            handler.send_error(404, "PDF preview path not allowed")
            return
        if not target.exists() or not target.is_file():
            handler.send_error(404, "PDF preview file not found")
            return
        handler.send_response(200)
        handler.send_header("Content-Type", "application/pdf")
        handler.send_header("Content-Disposition", f'inline; filename="{target.name}"')
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Content-Length", str(target.stat().st_size))
        handler.end_headers()
        if head_only:
            return
        try:
            with target.open("rb") as source:
                handler.copyfile(source, handler.wfile)
        except (BrokenPipeError, ConnectionResetError):
            return
