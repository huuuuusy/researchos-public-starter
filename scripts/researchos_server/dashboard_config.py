# ResearchOS maintenance header.
# 中文：ResearchOS 本地 dashboard server 中关于「dashboard config」的辅助 owner；保持 serve_dashboard.py 只做 HTTP 编排。
# English: Helper owner for dashboard config in the local ResearchOS dashboard server; keeps serve_dashboard.py HTTP-orchestration-only.

"""Dashboard server configuration helpers."""

from __future__ import annotations

import socketserver
import threading
from pathlib import Path
from urllib.parse import urlparse


class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
    # The page requests about a hundred scripts at once; the default listen backlog of 5 resets the overflow
    # on macOS, so a page load could miss a script and render broken.
    request_queue_size = 128
    # Mutating POSTs hold this one at a time: each store locks its own file, but a write followed by a
    # projection rebuild or maintenance run is a sequence, and the private rebuild refuses when its inputs
    # change mid-build, after which the request restores its pre-write file over the other request's write.
    mutation_lock = threading.Lock()


def dashboard_content_security_policy(request_path: str) -> str:
    parsed = urlparse(request_path)
    is_pdf_response = parsed.path == "/pdf" or (
        parsed.path.startswith("/corpus/") and parsed.path.lower().endswith(".pdf")
    )
    frame_ancestors = "'self'" if is_pdf_response else "'none'"
    return (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; "
        f"frame-ancestors {frame_ancestors}; base-uri 'none'; form-action 'self'"
    )


def configured_dashboard_port(root: Path, default: int = 8765) -> int:
    config = root / "researchos.config.yml"
    if not config.exists():
        return default
    in_dashboard = False
    for raw_line in config.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0:
            in_dashboard = line == "dashboard:"
            continue
        if in_dashboard and line.startswith("port:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return default
    return default
