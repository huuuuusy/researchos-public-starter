#!/usr/bin/env python3
"""Validate the public starter's reader-facing English/Chinese document pairs."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAIR_ROOTS = (ROOT / "docs", ROOT / "08_exports" / "public_starter")
ROOT_PAIRS = (
    (ROOT / "README.md", ROOT / "README.zh.md"),
    (ROOT / "AGENTS.md", ROOT / "docs" / "reference" / "AGENTS.zh.md"),
    (ROOT / "CONTRIBUTING.md", ROOT / "docs" / "reference" / "CONTRIBUTING.zh.md"),
    (ROOT / "SECURITY.md", ROOT / "docs" / "reference" / "SECURITY.zh.md"),
    (ROOT / "SUPPORT.md", ROOT / "docs" / "reference" / "SUPPORT.zh.md"),
    (ROOT / "CODE_OF_CONDUCT.md", ROOT / "docs" / "reference" / "CODE_OF_CONDUCT.zh.md"),
)
RELATED_TOOLS_PAIR = (
    Path("docs/reference/RELATED_RESEARCH_TOOLS.md"),
    Path("docs/reference/RELATED_RESEARCH_TOOLS.zh.md"),
)
MIN_RELATED_TOOL_LINKS = 20
MARKDOWN_EXTERNAL_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
EN_REVIEW_DATE = re.compile(r"last reviewed on \*\*(\d{4}-\d{2}-\d{2})\*\*")
ZH_REVIEW_DATE = re.compile(r"最后核查于 \*\*(\d{4}-\d{2}-\d{2})\*\*")
EN_SNAPSHOT_BOUNDARY = (
    "not an exhaustive directory, endorsement, procurement recommendation, "
    "or promise of continuous updates"
)
ZH_SNAPSHOT_BOUNDARY = "不是完整目录、背书、采购建议，也不承诺持续更新"
CANONICAL_READER_DOCS = (
    Path("docs/user-manual.en.md"),
    Path("docs/user-manual.zh.md"),
    Path("docs/system-reference.en.md"),
    Path("docs/system-reference.zh.md"),
    Path("docs/governance-guide.en.md"),
    Path("docs/governance-guide.zh.md"),
)
RETIRED_READER_DOCS = (
    Path("docs/user-journeys.en.md"),
    Path("docs/user-journeys.zh.md"),
    Path("docs/releases/v1.0.0-validation-receipt.md"),
    Path("docs/releases/v1.0.0-validation-receipt.zh.md"),
    # Merged into the User Manual, System Reference and Governance and Extension Guide.
    Path("docs/operations-guide.en.md"),
    Path("docs/operations-guide.zh.md"),
    Path("docs/minimum-core.en.md"),
    Path("docs/minimum-core.zh.md"),
    Path("docs/agent-code-map.en.md"),
    Path("docs/agent-code-map.zh.md"),
    Path("docs/customization-guide.en.md"),
    Path("docs/customization-guide.zh.md"),
    Path("docs/plugin-installation-example.en.md"),
    Path("docs/plugin-installation-example.zh.md"),
    # Redirect stubs folded into the User Manual and the System Reference.
    Path("docs/reference/START_HERE.md"),
    Path("docs/reference/START_HERE.zh.md"),
    Path("docs/kernel-and-extension-architecture.en.md"),
    Path("docs/kernel-and-extension-architecture.zh.md"),
    # Folded into the System Reference.
    Path("docs/reference/SYSTEM_OVERVIEW.md"),
    Path("docs/reference/SYSTEM_OVERVIEW.zh.md"),
)


def discover_pairs(root: Path = ROOT) -> list[tuple[Path, Path]]:
    pairs = list(ROOT_PAIRS) if root == ROOT else []
    pair_roots = PAIR_ROOTS if root == ROOT else (root / "docs", root / "08_exports" / "public_starter")
    seen: set[tuple[Path, Path]] = set()
    for owner in pair_roots:
        if not owner.exists():
            continue
        for english in owner.rglob("*.en.md"):
            seen.add((english, english.with_name(english.name.replace(".en.md", ".zh.md"))))
        for english in owner.rglob("*.md"):
            if english.relative_to(root).as_posix() in {
                "docs/plugins/method-comparison/researchos-method-comparison/SKILL.md",
                "docs/plugins/method-comparison/skill-adapter.md",
            }:
                # Machine method/adapter entrances; README.md and README.zh.md own reader guidance.
                continue
            if english.name.endswith((".en.md", ".zh.md")):
                continue
            seen.add((english, english.with_name(f"{english.stem}.zh.md")))
    pairs.extend(sorted(seen))
    return pairs


def validate_related_tools_pair(root: Path) -> list[str]:
    failures: list[str] = []
    english_path = root / RELATED_TOOLS_PAIR[0]
    chinese_path = root / RELATED_TOOLS_PAIR[1]
    if not english_path.exists() or not chinese_path.exists():
        return failures

    english_text = english_path.read_text(encoding="utf-8")
    chinese_text = chinese_path.read_text(encoding="utf-8")
    english_entries = MARKDOWN_EXTERNAL_LINK.findall(english_text)
    chinese_entries = MARKDOWN_EXTERNAL_LINK.findall(chinese_text)
    english_urls = [url for _name, url in english_entries]

    if len(english_entries) < MIN_RELATED_TOOL_LINKS:
        failures.append(
            f"{RELATED_TOOLS_PAIR[0]} has only {len(english_entries)} external project links; "
            f"expected at least {MIN_RELATED_TOOL_LINKS}"
        )
    if len(english_urls) != len(set(english_urls)):
        failures.append(f"{RELATED_TOOLS_PAIR[0]} contains duplicate external project links")
    if english_entries != chinese_entries:
        failures.append(
            "related-tools English/Chinese project names, URLs, or ordering have drifted"
        )

    english_date = EN_REVIEW_DATE.search(english_text)
    chinese_date = ZH_REVIEW_DATE.search(chinese_text)
    if not english_date or not chinese_date:
        failures.append("related-tools English/Chinese snapshot dates are missing")
    elif english_date.group(1) != chinese_date.group(1):
        failures.append(
            "related-tools English/Chinese snapshot dates do not match: "
            f"{english_date.group(1)} != {chinese_date.group(1)}"
        )

    if EN_SNAPSHOT_BOUNDARY not in english_text:
        failures.append("related-tools English snapshot boundary is missing")
    if ZH_SNAPSHOT_BOUNDARY not in chinese_text:
        failures.append("related-tools Chinese snapshot boundary is missing")
    return failures


def validate_document_ownership(root: Path) -> list[str]:
    failures: list[str] = []
    for relative in CANONICAL_READER_DOCS:
        if not (root / relative).exists():
            failures.append(f"missing canonical reader document: {relative}")
    for relative in RETIRED_READER_DOCS:
        if (root / relative).exists():
            failures.append(f"retired reader document must not return: {relative}")

    retired_names = {path.name for path in RETIRED_READER_DOCS}
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for retired_name in retired_names:
            if retired_name in text:
                failures.append(
                    f"{path.relative_to(root)} still references retired reader document: {retired_name}"
                )
    return failures


def validate_operational_doc_semantics(root: Path) -> list[str]:
    failures: list[str] = []
    owner_dir = root / "scripts" / "researchos_data"
    if not owner_dir.exists():
        return failures
    contracts = {
        Path("scripts/researchos_data/README.md"): (
            "plugin_lifecycle.py",
            "scripts/manage_plugins.py",
        ),
        Path("scripts/researchos_data/README.zh.md"): (
            "plugin_lifecycle.py",
            "scripts/manage_plugins.py",
        ),
    }
    for relative, markers in contracts.items():
        path = root / relative
        if not path.exists():
            failures.append(f"missing operational boundary document: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                failures.append(f"{relative} is missing supported owner or entrypoint: {marker}")
    return failures


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for english, chinese in discover_pairs(root):
        if not english.exists():
            failures.append(f"missing English document: {english.relative_to(root)}")
            continue
        if not chinese.exists():
            failures.append(f"missing Chinese pair for {english.relative_to(root)}: {chinese.relative_to(root)}")
            continue
        if root / "docs" in english.parents:
            english_text = english.read_text(encoding="utf-8")
            chinese_text = chinese.read_text(encoding="utf-8")
            if chinese.name not in english_text:
                failures.append(f"{english.relative_to(root)} does not link {chinese.name}")
            if english.name not in chinese_text:
                failures.append(f"{chinese.relative_to(root)} does not link {english.name}")
    failures.extend(validate_related_tools_pair(root))
    failures.extend(validate_operational_doc_semantics(root))
    if (root / "README.md").exists():
        failures.extend(validate_document_ownership(root))
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("Bilingual documentation validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"OK: bilingual documentation pairs are valid ({len(discover_pairs())} pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
