#!/usr/bin/env python3
# ResearchOS maintenance header.
# English: Scans the public package for private semantics, secrets, local paths, and raw corpus payloads.
"""Fail closed on public-package privacy, secret, and semantic residue."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    "",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
RUNTIME_SUFFIXES = TEXT_SUFFIXES - {".css", ".md", ".svg", ".txt"}
RUNTIME_ROOTS = ("config", "dashboard", "scripts")
SKIP_PARTS = {".git", ".playwright-cli", ".pytest_cache", "__pycache__", "node_modules", "work_state"}
ALLOWED_CORPUS_FILES = {"README.md", "README.zh.md"}
SELF_TEST_FILES = {"validate_public_safety.py", "test_public_safety.py"}
# Digests of short names can be reversed by guessing, so this repository ships no list of
# private identifiers. The private project scans the public package with its own list before
# release; the check below still runs on any digests passed in.
PRIVATE_SEMANTIC_MARKER_HASHES: frozenset[str] = frozenset()
MAX_PRIVATE_MARKER_TOKENS = 8
BLOCKED_PATTERNS = (
    ("macOS user path", re.compile(r"/" + r"Users/[^/\s]+/")),
    ("Linux user path", re.compile(r"/home/[^/\s]+/")),
    ("Windows user path", re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\s]+\\\\")),
    ("API-key assignment", re.compile(r"\b(?:OPENAI|ANTHROPIC|DEEPSEEK)_API_KEY\s*=")),
    ("API-key-like token", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
)
PRIVATE_INTEGRATION_RUNTIME_PATTERNS = (
    re.compile(r"\bcross[_-]?(?:os|system)\b", re.IGNORECASE),
    re.compile(r"\bsibling[_-]?(?:os|system)\b", re.IGNORECASE),
    re.compile(r"\bprivate[_-]?system\b", re.IGNORECASE),
    re.compile(r"\bfederation\b", re.IGNORECASE),
)
ACTOR_BOUND_RUNTIME_PATTERNS = (
    re.compile(r"\bshiyu[-_ ]research[-_ ]os\b", re.IGNORECASE),
    re.compile(r"\bshiyu_relation\b", re.IGNORECASE),
    re.compile(r"\brelation_to_shiyu\b", re.IGNORECASE),
    re.compile(r"\b(?:assetCard\w*Shiyu|needsShiyu\w*)\b"),
)


def text_files(root: Path = ROOT) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_SUFFIXES
        and not any(part in SKIP_PARTS for part in path.parts)
        and path.name not in SELF_TEST_FILES
        and path.name != "researchos-local.json"
    )


def runtime_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for rel in RUNTIME_ROOTS:
        owner = root / rel
        if not owner.exists():
            continue
        files.extend(
            path
            for path in owner.rglob("*")
            if path.is_file()
            and path.suffix.lower() in RUNTIME_SUFFIXES
            and not any(part in SKIP_PARTS for part in path.parts)
            and path.name not in SELF_TEST_FILES
        )
    return sorted(set(files))


def private_semantic_marker_hit(
    text: str,
    marker_hashes: frozenset[str] = PRIVATE_SEMANTIC_MARKER_HASHES,
) -> bool:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    for start in range(len(tokens)):
        for width in range(1, min(MAX_PRIVATE_MARKER_TOKENS, len(tokens) - start) + 1):
            window = tokens[start : start + width]
            for separator in ("", "-", "_"):
                digest = hashlib.sha256(separator.join(window).encode("utf-8")).hexdigest()
                if digest in marker_hashes:
                    return True
    return False


def scan_text(
    text: str,
    marker_hashes: frozenset[str] = PRIVATE_SEMANTIC_MARKER_HASHES,
) -> list[str]:
    failures: list[str] = []
    if private_semantic_marker_hit(text, marker_hashes):
        failures.append("private semantic marker")
    for label, pattern in BLOCKED_PATTERNS:
        if pattern.search(text):
            failures.append(label)
    return failures



# Exact already-published bibliography references, not a global name exception.
PUBLIC_REPORT_CITATIONS = {'CausalStep': 'https://ojs.aaai.org/index.php/AAAI/article/view/37582', 'FIOVA': 'https://arxiv.org/abs/2410.15270', 'SOEI': 'https://arxiv.org/abs/2410.15701', 'SOTVerse': 'https://doi.org/10.1007/s11263-023-01908-5', 'VerifyBench': 'https://ojs.aaai.org/index.php/AAAI/article/view/40448'}

def public_report_citation_view(text: str) -> str:
    for title, url in PUBLIC_REPORT_CITATIONS.items():
        citation = "[" + title + "](" + url + ")"
        # Ignore only the verified citation span and an immediately repeated title.
        # The same name elsewhere, different URLs, paths and secrets remain scanned.
        text = re.sub(r"(?<![A-Za-z0-9_])(?:" + re.escape(title) + r"\s+)?"
                      + re.escape(citation), "public bibliography reference", text)
    return text

def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    dashboard_index = root / "dashboard" / "index.html"
    if dashboard_index.exists():
        index_text = dashboard_index.read_text(encoding="utf-8", errors="replace")
        if 'href="http://127.0.0.1:8880/"' not in index_text:
            failures.append("dashboard/index.html: public service link must use port 8880")
    corpus = root / "corpus"
    if corpus.exists():
        for path in corpus.rglob("*"):
            if path.is_file() and path.name not in ALLOWED_CORPUS_FILES:
                failures.append(f"{path.relative_to(root)}: raw corpus payload is not public-safe")
    for path in runtime_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(pattern.search(text) for pattern in PRIVATE_INTEGRATION_RUNTIME_PATTERNS):
            failures.append(f"{path.relative_to(root)}: private integration runtime surface is not public-safe")
        if any(pattern.search(text) for pattern in ACTOR_BOUND_RUNTIME_PATTERNS):
            failures.append(f"{path.relative_to(root)}: actor-bound runtime owner is not public-safe")
    for path in text_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.relative_to(root).as_posix() in {"docs/technical-report.en.md", "docs/technical-report.zh.md",
                                                 "docs/technical-report-supplement.en.md", "docs/technical-report-supplement.zh.md"}:
            text = public_report_citation_view(text)
        for reason in scan_text(text):
            failures.append(f"{path.relative_to(root)}: {reason}")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("Public safety validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"OK: public safety validation passed ({len(text_files())} text files scanned)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
