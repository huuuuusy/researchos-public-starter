#!/usr/bin/env python3
# ResearchOS maintenance header.
# English: Checks Markdown links across the public starter without rewriting files.
"""Report-only Markdown link checker for the public ResearchOS starter."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRS = [
    "00_identity",
    "01_knowledge",
    "02_decisions",
    "03_cognition",
    "04_people",
    "05_workflows",
    "06_active_context",
    "07_archive",
    "08_exports",
    "09_templates",
    "config",
    "corpus",
    "dashboard",
    "distilled",
    "docs",
    "evals",
    "scripts",
]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
EXTERNAL_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "#",
)
SKIP_PARTS = {".git", "work_state"}


def iter_markdown_files(include_hidden: bool = False, root: Path = ROOT) -> list[Path]:
    files: list[Path] = [path for path in root.glob("*.md") if path.is_file()]
    for dirname in DEFAULT_DIRS:
        base = root / dirname
        if not base.exists():
            continue
        files.extend(
            path
            for path in base.rglob("*.md")
            if path.is_file()
            and not any(part in SKIP_PARTS for part in path.parts)
            and (include_hidden or not any(part.startswith(".") for part in path.parts))
        )
    return sorted(set(files))


def clean_target(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = target.split("#", 1)[0].strip()
    return unquote(target)


def is_external_or_empty(target: str) -> bool:
    return not target or target.startswith(EXTERNAL_PREFIXES)


def target_exists(file_path: Path, target: str) -> bool:
    clean = clean_target(target)
    if is_external_or_empty(clean):
        return True
    if clean.startswith("/"):
        return Path(clean).exists()
    return (file_path.parent / clean).resolve().exists()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Also scan Markdown files in hidden directories.",
    )
    args = parser.parse_args()

    failures: list[str] = []
    files = iter_markdown_files(include_hidden=args.include_hidden)
    for file_path in files:
        rel = file_path.relative_to(ROOT)
        text = file_path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = match.group(1)
            if not target_exists(file_path, target):
                failures.append(f"{rel} -> {target}")

    if failures:
        print("Public starter link check failed:")
        for failure in failures:
            print(f"- {failure}")
        print(f"\nChecked {len(files)} Markdown files.")
        return 1

    print(f"Public starter link check passed: {len(files)} Markdown files checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
