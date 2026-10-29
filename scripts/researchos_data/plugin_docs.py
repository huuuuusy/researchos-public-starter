"""Validate the repository-local README contract shared by every ResearchOS plugin."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable


README_SECTIONS = (
    "Purpose",
    "Use and non-goals",
    "Availability and parity",
    "Dependencies",
    "Lifecycle",
    "Data, permissions, and export",
    "Verification",
    "Failure recovery",
    "Value and alternatives",
    "Retirement",
)

PUBLIC_DOCUMENTATION_LEAK_PATTERNS = (
    ("absolute user-home path", re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home)/[^/\s`\"']+/")),
    ("credential assignment", re.compile(r"(?i)\b(?:token|api[_-]?key|password|secret)\s*=\s*\S+")),
)


def public_documentation_leaks(text: str) -> list[str]:
    """Return public-documentation leak classes using cross-platform patterns."""
    return [label for label, pattern in PUBLIC_DOCUMENTATION_LEAK_PATTERNS if pattern.search(text)]


def validate_documentation(
    value: Any,
    *,
    root: Path,
    source: Path,
    plugin_id: str,
    fail: Callable[[Path, str], Exception],
) -> dict[str, str]:
    """Return a normalized README reference or fail closed.

    Documentation is deliberately repository-local. It cannot be a URL, an
    absolute path, a symlink escape, or a generic shared file that hides which
    lifecycle and security boundaries belong to this plugin.
    """
    if not isinstance(value, dict) or set(value) != {"readme"}:
        raise fail(source, "documentation must define exactly one readme")
    readme = str(value.get("readme") or "").strip()
    expected = f"docs/plugins/{plugin_id.replace('_', '-')}/README.md"
    if readme != expected:
        raise fail(source, f"documentation.readme must be {expected}")
    relative = Path(readme)
    if relative.is_absolute() or ".." in relative.parts:
        raise fail(source, "documentation.readme must stay inside the repository")
    candidate = root / relative
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise fail(source, "documentation.readme must not use symlinks")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except FileNotFoundError:
        raise fail(source, f"documentation.readme does not exist: {readme}")
    except (OSError, RuntimeError, ValueError):
        raise fail(source, "documentation.readme must stay inside the repository after resolving links")
    if not resolved.is_file():
        raise fail(source, "documentation.readme must be a regular repository file")
    text = resolved.read_text(encoding="utf-8", errors="strict")
    missing = [
        heading
        for heading in README_SECTIONS
        if re.search(rf"^## {re.escape(heading)}\s*$", text, flags=re.MULTILINE) is None
    ]
    if missing:
        raise fail(source, f"documentation.readme is missing required sections: {missing}")
    return {"readme": readme}
