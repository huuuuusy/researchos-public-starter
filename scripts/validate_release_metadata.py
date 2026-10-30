#!/usr/bin/env python3
"""Keep the public version, date, release notes, citation, and visible license aligned."""

from __future__ import annotations

import argparse
import ast
from datetime import date
import hashlib
from pathlib import Path
import re
import subprocess
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from researchos_data.frontend_manifest import frontend_script_load_order
from check_all_links import iter_markdown_files
from validate_agent_architecture import validate_python_routes
from validate_public_safety import text_files
from validate_docs_bilingual import discover_pairs


ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.3"
CANDIDATE_VERSION = "1.0.3-rc.1"
VISIBLE_LICENSE = "License: ResearchOS Source-Available Research License"
RELEASE_ARTIFACTS = (
    "08_exports/public_starter/generated-public-starter-data.json",
    "dashboard/data/researchos-dashboard.json",
)
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def read(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.exists() else ""


def python_test_count(root: Path) -> int:
    """Count declared unittest methods without importing the test suite."""
    count = 0
    for path in sorted((root / "evals").glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                count += 1
    return count


def validation_snapshot(root: Path) -> dict[str, int]:
    active_frontend = len(frontend_script_load_order())
    frontend_source = len(tuple((root / "dashboard" / "src").rglob("*.js")))
    _, reached, _ = validate_python_routes(root)
    return {
        "python_tests": python_test_count(root),
        "javascript_suites": len(tuple((root / "evals").glob("test_*.js"))),
        "public_safety_files": len(text_files(root)),
        "markdown_files": len(iter_markdown_files(root=root)),
        "bilingual_pairs": len(discover_pairs(root)),
        "active_frontend_modules": active_frontend,
        "frontend_source_modules": frontend_source,
        "reachable_server_modules": reached["researchos_server"],
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def declared_artifact_hashes(release_notes: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in RELEASE_ARTIFACTS:
        match = re.search(rf"`{re.escape(relative)}`[:：]\s*`([0-9a-f]{{64}})`", release_notes)
        if match:
            hashes[relative] = match.group(1)
    return hashes


def citation_values(citation: str, key: str) -> list[str]:
    pattern = re.compile(rf'^\s*{re.escape(key)}\s*:\s*["\']?([^"\'\n]+?)["\']?\s*$', re.MULTILINE)
    return [match.strip() for match in pattern.findall(citation)]


def valid_iso_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def detect_release_stage(root: Path = ROOT) -> tuple[str | None, list[str]]:
    """Return the final release date, or None for a valid release candidate."""
    failures: list[str] = []
    citation = read(root, "CITATION.cff")
    versions = citation_values(citation, "version")
    dates = citation_values(citation, "date-released")
    if len(versions) != 1:
        return None, [f"CITATION.cff must declare exactly one version field; found {len(versions)}"]
    if versions[0] == CANDIDATE_VERSION:
        if dates:
            failures.append("release-candidate CITATION.cff must not declare date-released")
        return None, failures
    if versions[0] != VERSION:
        return None, [f"unsupported CITATION.cff release version: {versions[0]!r}"]
    if len(dates) != 1:
        return None, [f"final CITATION.cff must declare exactly one date-released field; found {len(dates)}"]
    if not valid_iso_date(dates[0]):
        return None, [f"final CITATION.cff date-released must be a real ISO date: {dates[0]!r}"]
    return dates[0], failures


def git_release_failures(root: Path, *, expected_commit: str | None, require_clean: bool) -> list[str]:
    failures: list[str] = []
    if expected_commit:
        if not FULL_COMMIT_RE.fullmatch(expected_commit):
            failures.append("expected release commit must be a full lowercase 40-character Git SHA")
            expected_commit = None
    if expected_commit:
        actual = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
        )
        if actual.returncode or actual.stdout.strip() != expected_commit:
            failures.append(
                f"release commit mismatch: expected {expected_commit!r}, got {actual.stdout.strip() or 'unavailable'!r}"
            )
    if require_clean:
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False
        )
        if status.returncode or status.stdout.strip():
            failures.append("release worktree must be clean for ref-bound validation")
    return failures


def invocation_failures(*, release_date: str | None, expected_commit: str | None, require_clean: bool) -> list[str]:
    failures: list[str] = []
    if release_date:
        if not expected_commit:
            failures.append("final release validation requires --expected-commit <full-sha>")
        if not require_clean:
            failures.append("final release validation requires --require-clean")
    return failures


def validate(root: Path = ROOT, version: str = VERSION, release_date: str | None = None) -> list[str]:
    failures: list[str] = []
    citation = read(root, "CITATION.cff")
    changelog = read(root, "CHANGELOG.md")
    readme = read(root, "README.md")
    readme_zh = read(root, "README.zh.md")
    release_notes = read(root, f"docs/releases/v{version}.md")
    release_notes_zh = read(root, f"docs/releases/v{version}.zh.md")
    dashboard = read(root, "dashboard/index.html")
    license_text = read(root, "LICENSE.md")
    snapshot = validation_snapshot(root)
    version_values = citation_values(citation, "version")
    release_date_values = citation_values(citation, "date-released")
    if len(version_values) != 1:
        failures.append(f"CITATION.cff must declare exactly one version field; found {len(version_values)}")
    if release_date and not valid_iso_date(release_date):
        failures.append(f"release date must be a real ISO date: {release_date!r}")
    if release_date and len(release_date_values) != 1:
        failures.append(
            f"final CITATION.cff must declare exactly one date-released field; found {len(release_date_values)}"
        )
    if not release_date and release_date_values:
        failures.append("release-candidate CITATION.cff must not declare date-released")

    expected = {
        "English README release": (readme, f"V{version.removesuffix('.0')}"),
        "Chinese README release": (readme_zh, f"V{version.removesuffix('.0')}"),
        "English release notes": (release_notes, f"V{version.removesuffix('.0')}"),
        "Chinese release notes": (release_notes_zh, f"V{version.removesuffix('.0')}"),
        "English validation snapshot": (release_notes, "Pre-Commit Validation Snapshot"),
        "Chinese validation snapshot": (release_notes_zh, "提交前验证快照"),
        "dashboard visible license": (dashboard, VISIBLE_LICENSE),
        "custom license identity": (license_text, "custom ResearchOS license"),
        "English Python tests": (release_notes, f"`{snapshot['python_tests']}` Python tests"),
        "Chinese Python tests": (release_notes_zh, f"`{snapshot['python_tests']}` 个 Python tests"),
        "English JavaScript suites": (
            release_notes,
            f"`{snapshot['javascript_suites']}` JavaScript contract suites",
        ),
        "Chinese JavaScript suites": (
            release_notes_zh,
            f"`{snapshot['javascript_suites']}` 组 JavaScript contract suites",
        ),
        "English public safety files": (
            release_notes,
            f"`{snapshot['public_safety_files']}` text files",
        ),
        "Chinese public safety files": (
            release_notes_zh,
            f"`{snapshot['public_safety_files']}` 个文本文件",
        ),
        "English Markdown links": (
            release_notes,
            f"`{snapshot['markdown_files']}` Markdown files",
        ),
        "Chinese Markdown links": (
            release_notes_zh,
            f"`{snapshot['markdown_files']}` 个 Markdown 文件",
        ),
        "English bilingual pairs": (
            release_notes,
            f"`{snapshot['bilingual_pairs']}` English/Chinese pairs",
        ),
        "Chinese bilingual pairs": (
            release_notes_zh,
            f"`{snapshot['bilingual_pairs']}` 对中英文文档",
        ),
        "English frontend graph": (
            release_notes,
            f"`{snapshot['active_frontend_modules']}` active frontend modules and "
            f"`{snapshot['frontend_source_modules']}` source modules",
        ),
        "Chinese frontend graph": (
            release_notes_zh,
            f"`{snapshot['active_frontend_modules']}` 个活动前端模块和 "
            f"`{snapshot['frontend_source_modules']}` 个源码模块",
        ),
        "English server graph": (
            release_notes,
            f"`{snapshot['reachable_server_modules']}` reachable public-server modules",
        ),
        "Chinese server graph": (
            release_notes_zh,
            f"`{snapshot['reachable_server_modules']}` 个可达 public server 模块",
        ),
    }
    if release_date:
        expected.update(
            {
                "CITATION.cff version": (citation, f'version: "{version}"'),
                "CITATION.cff release date": (citation, f'date-released: "{release_date}"'),
                "CHANGELOG release heading": (changelog, f"## [{version}] - {release_date}"),
            }
        )
    else:
        expected.update(
            {
                "CITATION.cff candidate version": (citation, f'version: "{CANDIDATE_VERSION}"'),
                "CHANGELOG candidate heading": (changelog, "## [Unreleased]"),
            }
        )
        if re.search(rf"^## \[{re.escape(version)}\] - ", changelog, re.MULTILINE):
            failures.append("release-candidate CHANGELOG must not declare the final version date")
    for label, (text, marker) in expected.items():
        if marker not in text:
            failures.append(f"{label} is missing or inconsistent: expected {marker!r}")
    if "License: PolyForm" in dashboard:
        failures.append("dashboard must not describe the custom ResearchOS license as PolyForm")
    english_hashes = declared_artifact_hashes(release_notes)
    chinese_hashes = declared_artifact_hashes(release_notes_zh)
    for relative in RELEASE_ARTIFACTS:
        artifact = root / relative
        if not artifact.is_file():
            failures.append(f"release artifact is missing: {relative}")
            continue
        actual_hash = sha256(artifact)
        for language, hashes in (("English", english_hashes), ("Chinese", chinese_hashes)):
            if hashes.get(relative) != actual_hash:
                failures.append(
                    f"{language} release artifact hash is missing or stale for {relative}: expected {actual_hash}"
                )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-date",
        help="Validate final release metadata for this YYYY-MM-DD date; omit for release-candidate validation.",
    )
    parser.add_argument("--expected-commit", help="Require HEAD to equal this full commit hash.")
    parser.add_argument("--require-clean", action="store_true", help="Require a clean ref-bound worktree.")
    args = parser.parse_args()
    detected_date, stage_failures = detect_release_stage()
    release_date = args.release_date if args.release_date is not None else detected_date
    failures = list(stage_failures)
    if args.release_date is not None and detected_date != args.release_date:
        failures.append(
            f"explicit release date does not match CITATION.cff stage: expected {detected_date!r}, got {args.release_date!r}"
        )
    failures.extend(validate(release_date=release_date))
    failures.extend(
        invocation_failures(
            release_date=release_date,
            expected_commit=args.expected_commit,
            require_clean=args.require_clean,
        )
    )
    failures.extend(git_release_failures(ROOT, expected_commit=args.expected_commit, require_clean=args.require_clean))
    if failures:
        print("Release metadata validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    if release_date:
        print(f"OK: final release metadata is aligned for v{VERSION} ({release_date})")
    else:
        print(f"OK: release-candidate metadata is aligned for {CANDIDATE_VERSION} (no release date)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
