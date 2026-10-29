#!/usr/bin/env python3
# ResearchOS maintenance header.
# English: Builds public-safe demo records and the dashboard projection from fictional public starter materials.
"""
Build public-safe case/demo data from 08_exports/public_starter.

中文：默认读取 public starter 的虚构 case Markdown；用户可以在 config 中关闭 case，使文件保留但不进入 active demo data。
English: By default this reads fictional public starter case Markdown; users can disable cases in config so files remain as reference but no longer enter active demo data.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from researchos_data.plugins import load_plugin_registry
from researchos_data.public_conversation_catalog import public_tasks_for_language
from researchos_data.repository_layout import PERSONAL_VAULT_LAYER_DIRS

from research_agenda_projection import personal_research_agenda, public_research_agenda


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "08_exports" / "public_starter"
CONFIG = ROOT / "config" / "researchos.runtime.example.json"
OUTPUT = STARTER_DIR / "generated-public-starter-data.json"
DASHBOARD_OUTPUT = ROOT / "dashboard" / "data" / "researchos-dashboard.json"
PERSONAL_DASHBOARD_OUTPUT = ROOT / "dashboard" / "data" / "researchos-local.json"
PERSONAL_VAULT_ROOT = ROOT / "personal_vault"
PUBLIC_SAFE_SENSITIVITY = {"public"}
PERSONAL_LAYER_DIRS = PERSONAL_VAULT_LAYER_DIRS
BLOCKED_MARKERS = (
    "corpus/",
    "04_people/",
    "06_active_context/ui-",
    "dashboard/data/researchos-dashboard.json",
)
BOUNDARY_DOC_TYPES = {"export_starter", "checklist", "markdown"}
DASHBOARD_ASSET_TYPES = {
    "card_level_example",
    "demo_material",
    "demo_note",
    "demo_person",
    "demo_project",
    "example_active_context",
    "example_person_profile",
    "example_project_state",
}
AUTO_LOADED_ENTRY_FILES = {"AGENTS.md"}


def should_write_public_dashboard(root: Path = ROOT) -> bool:
    """Keep an embedded public demo from replacing a private authority dashboard."""
    return not ((root / "START_HERE.md").is_file() and (root / "00_identity").is_dir())


def public_assistant_modes_for_language(language: str) -> list[dict[str, str]]:
    if language == "zh-CN":
        return [
            {"mode": "新用户向导", "use": "先解释入口、读取顺序和确认边界。"},
            {"mode": "研究整理助手", "use": "把材料整理成卡片、证据和下一步。"},
            {"mode": "系统审计员", "use": "检查公开边界、链接、路径和可复现性。"},
        ]
    return [
        {"mode": "New-user guide", "use": "Explain entry points, reading order, and confirmation boundaries first."},
        {"mode": "Research organizer", "use": "Turn material into cards, evidence, and next actions."},
        {"mode": "System auditor", "use": "Check public boundaries, links, paths, and reproducibility."},
    ]


def has_frontmatter(text: str) -> bool:
    return text.startswith("---\n") and "\n---\n" in text[4:]


def has_displaced_frontmatter(text: str) -> bool:
    lines = text.splitlines()
    return not has_frontmatter(text) and "---" in lines[:10]


def parse_frontmatter(text: str) -> dict[str, Any]:
    if not has_frontmatter(text):
        return {}
    block = text.split("\n---\n", 1)[0].removeprefix("---\n")
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if current_list_key and line.strip().startswith("- "):
            value = line.strip()[2:].strip().strip('"').strip("'")
            current = data.setdefault(current_list_key, [])
            if isinstance(current, list):
                current.append(value)
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            data[key] = []
            current_list_key = key
        elif value == "[]":
            data[key] = []
        elif value.startswith("[") and value.endswith("]"):
            inline = value[1:-1].strip()
            data[key] = [part.strip().strip('"').strip("'") for part in inline.split(",") if part.strip()]
        else:
            data[key] = value.strip('"').strip("'")
    return data


def normalize_content_language(value: Any = "en") -> str:
    return "zh-CN" if str(value or "en") in {"zh", "zh-CN", "zh_CN"} else "en"


def normalize_available_content_languages(values: Any = None) -> list[str]:
    raw_values = values if isinstance(values, list) else ["en", "zh-CN"]
    languages = list(dict.fromkeys(normalize_content_language(value) for value in raw_values))
    return languages or ["en", "zh-CN"]


def language_freeze_state(content_language: str, available_languages: Any = None) -> dict[str, Any]:
    active_language = normalize_content_language(content_language)
    languages = normalize_available_content_languages(available_languages)
    if active_language not in languages:
        languages.insert(0, active_language)
    return {
        "active_language": active_language,
        "frozen_languages": [language for language in languages if language != active_language],
        "template_policy": "active_language_only",
        "inactive_language_behavior": "reference_only_do_not_read_by_agent",
        "token_policy": "exclude_frozen_language_templates_from_prompt_context",
        "sync_trigger": "switch_content_language_and_rebuild_generated_data",
    }

def load_case_materials_config() -> dict[str, Any]:
    if not CONFIG.exists():
        return {
            "enabled": True,
            "source": "08_exports/public_starter",
            "disabled_behavior": "keep_files_as_reference_only",
            "content_language": "en",
            "available_content_languages": ["en", "zh-CN"],
            "alternate_language_files": "reference_only_do_not_read_by_agent",
            "agent_language_routing": "selected_language_only",
        }
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    public_config = config.get("public_starter", {})
    case_config = config.get("public_starter", {}).get("case_materials", {})
    return {
        "enabled": bool(case_config.get("enabled", True)),
        "source": str(case_config.get("source", "08_exports/public_starter")),
        "disabled_behavior": str(case_config.get("disabled_behavior", "keep_files_as_reference_only")),
        "content_language": str(public_config.get("content_language", "en")),
        "available_content_languages": list(public_config.get("available_content_languages", ["en", "zh-CN"])),
        "alternate_language_files": str(public_config.get("alternate_language_files", "reference_only_do_not_read_by_agent")),
        "agent_language_routing": str(public_config.get("agent_language_routing", "selected_language_only")),
    }


def agent_summary(text: str) -> str:
    marker = "## Agent Summary"
    if marker not in text:
        return ""
    after = text.split(marker, 1)[1].strip()
    return after.split("\n## ", 1)[0].strip()


def list_value(metadata: dict[str, Any], key: str) -> list[str]:
    value = metadata.get(key, [])
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []


def first_heading(text: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def record_title(metadata: dict[str, Any], path: Path, text: str) -> str:
    """Resolve the display title used by all public templates.

    Official cards intentionally use type-specific fields such as ``name`` and
    ``project_name``. Falling back through those fields keeps a filled template
    from appearing under its filename in the dashboard.
    """
    for key in ("title", "name", "project_name", "display_name"):
        value = str(metadata.get(key, "")).strip()
        if value:
            return value
    return first_heading(text) or path.stem


def record_aliases(metadata: dict[str, Any], path: Path, title: str) -> list[str]:
    values = [
        title,
        str(metadata.get("title", "")),
        str(metadata.get("name", "")),
        str(metadata.get("project_name", "")),
        path.stem,
        path.as_posix(),
    ]
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def starter_files() -> list[Path]:
    return sorted(path for path in STARTER_DIR.glob("*.md") if path.is_file())


def personal_files(root: Path = ROOT) -> list[Path]:
    """Return agent-readable Markdown in a user's local vault layers.

    The public demo and generated dashboard data are intentionally excluded.
    A personal vault may contain internal or local-only cards because the
    resulting projection is written to a git-ignored local data file.
    """
    paths: list[Path] = []
    for layer in PERSONAL_LAYER_DIRS:
        base = root / layer
        if not base.exists():
            continue
        paths.extend(path for path in base.rglob("*.md") if path.is_file())
    # Runtime state (ros ledgers, task packets, runner logs) is never a card; ros excludes it from its graph too.
    return sorted(path for path in paths if not path.relative_to(root).as_posix().startswith("06_active_context/work_state/"))


def language_for_path(path: Path) -> str:
    if path.name.endswith(".zh.md"):
        return "zh-CN"
    counterpart = path.with_name(f"{path.stem}.zh.md")
    if counterpart.exists():
        return "en"
    return "neutral"


def selected_language_files(paths: list[Path], content_language: str) -> list[Path]:
    selected: list[Path] = []
    normalized = normalize_content_language(content_language)
    for path in paths:
        if path.name in {"onboarding-step-by-step.md", "onboarding-step-by-step.zh.md"}:
            selected.append(path)
            continue
        language = language_for_path(path)
        if language == "neutral" or language == normalized:
            selected.append(path)
    return selected


def validate_public_file(path: Path, text: str, metadata: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rel = path.relative_to(ROOT)
    if has_displaced_frontmatter(text):
        failures.append(f"{rel}: frontmatter must be the first block before language switches or HTML")
    sensitivity = str(metadata.get("sensitivity", "public")).strip() or "public"
    if sensitivity not in PUBLIC_SAFE_SENSITIVITY:
        failures.append(f"{rel}: sensitivity must be public")
    exportable_to = list_value(metadata, "exportable_to") or ["public_template"]
    if "public_template" not in exportable_to:
        failures.append(f"{rel}: must be exportable_to public_template")
    if str(metadata.get("type", "markdown")).strip() not in BOUNDARY_DOC_TYPES:
        for marker in BLOCKED_MARKERS:
            if marker in text:
                failures.append(f"{rel}: contains blocked marker {marker}")
    return failures


def build_public_starter_data(force_cases: bool | None = None, content_language: str | None = None) -> tuple[dict[str, Any], list[str]]:
    case_config = load_case_materials_config()
    if force_cases is not None:
        case_config["enabled"] = force_cases
    if content_language:
        case_config["content_language"] = content_language
    normalized_language = normalize_content_language(case_config.get("content_language", "en"))
    case_config["content_language"] = normalized_language
    case_config["available_content_languages"] = normalize_available_content_languages(
        case_config.get("available_content_languages")
    )
    case_config["language_freeze"] = language_freeze_state(
        normalized_language,
        case_config["available_content_languages"],
    )
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    if case_config["enabled"]:
        all_paths = starter_files()
        for path in all_paths:
            text = path.read_text(encoding="utf-8")
            metadata = parse_frontmatter(text)
            failures.extend(validate_public_file(path, text, metadata))
        for path in selected_language_files(all_paths, normalized_language):
            text = path.read_text(encoding="utf-8")
            metadata = parse_frontmatter(text)
            records.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "title": record_title(metadata, path, text),
                    "type": str(metadata.get("type", "markdown")),
                    "status": str(metadata.get("status", "reference")),
                    "card_maturity_level": str(metadata.get("card_maturity_level", "")),
                    "project_maturity": str(metadata.get("project_maturity", metadata.get("incubation_maturity", ""))),
                    "relationship_maturity": str(metadata.get("relationship_maturity", "")),
                    "group_level": str(metadata.get("group_level", "")),
                    "sensitivity": str(metadata.get("sensitivity", "public")),
                    "tags": list_value(metadata, "tags"),
                    "exportable_to": list_value(metadata, "exportable_to") or ["public_template"],
                    "agent_summary": agent_summary(text),
                    "case_mode": "active_demo_case",
                    "content_language": language_for_path(path),
                }
            )
    data = {
        "generated_at": date.today().isoformat(),
        "schema_id": "researchos-public-starter-data-v2",
        "source": "08_exports/public_starter",
        "boundary": "fictional_public_demo_only",
        "case_materials": case_config,
        "records": records,
        "record_count": len(records),
    }
    return data, failures


def personal_asset_kind(metadata: dict[str, Any], path: Path) -> str:
    type_value = str(metadata.get("type", "")).lower().replace("_", "-")
    if "reading-note" in type_value or "paper" in type_value:
        return "paper"
    if "person" in type_value or "collaborator" in type_value:
        return "person"
    if "talk" in type_value or "presentation" in type_value:
        return "talk"
    if "project" in type_value or "plan-card" in type_value:
        return "project"
    if type_value in {"", "markdown", "card"}:
        path_value = path.stem.lower().replace("_", "-")
        if "paper" in path_value or "reading-note" in path_value:
            return "paper"
        if "person" in path_value or "collaborator" in path_value:
            return "person"
        if "talk" in path_value:
            return "talk"
        if "project" in path_value:
            return "project"
    return ""


def validate_personal_onboarding_outputs(source_root: Path) -> list[str]:
    """Fail visibly when a started onboarding run cannot become indexed assets."""
    intake = source_root / "06_active_context" / "onboarding-intake.md"
    if not intake.exists():
        return []
    failures: list[str] = []
    required = {
        "00_identity/user-card.md": "person",
        "01_knowledge/papers/publication-index.md": "publication_index",
        "01_knowledge/projects/research-profile-synthesis.md": "project",
        "06_active_context/onboarding-intake.md": "onboarding_intake",
        "06_active_context/onboarding-report.md": "onboarding_report",
    }
    for relative, expected_type in required.items():
        path = source_root / relative
        if not path.is_file():
            failures.append(f"personal onboarding output missing: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        if not has_frontmatter(text):
            failures.append(f"personal onboarding output lacks YAML frontmatter: {relative}")
            continue
        metadata = parse_frontmatter(text)
        if str(metadata.get("type", "")).strip() != expected_type:
            failures.append(f"personal onboarding output type must be {expected_type}: {relative}")
        if not agent_summary(text):
            failures.append(f"personal onboarding output lacks a non-empty Agent Summary: {relative}")

    paper_root = source_root / "01_knowledge" / "papers" / "own_papers" / "reading_notes"
    for path in sorted(paper_root.glob("*.md")) if paper_root.is_dir() else []:
        relative = path.relative_to(source_root).as_posix()
        text = path.read_text(encoding="utf-8")
        if not has_frontmatter(text):
            continue
        metadata = parse_frontmatter(text)
        if str(metadata.get("onboarding_origin", "")).strip() != "researchos_onboarding_v1":
            continue
        if str(metadata.get("type", "")).strip() != "paper":
            failures.append(f"personal onboarding paper type must be paper: {relative}")
        if not agent_summary(text):
            failures.append(f"personal onboarding paper lacks a non-empty Agent Summary: {relative}")
    return failures


def build_personal_vault_data(
    root: Path = ROOT,
    content_language: str | None = None,
    vault_root: Path | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Build a local-only card index from the user's own ResearchOS layers."""
    config = load_case_materials_config()
    normalized_language = normalize_content_language(content_language or config.get("content_language", "en"))
    available_languages = normalize_available_content_languages(config.get("available_content_languages"))
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    source_root = vault_root or root
    for path in selected_language_files(personal_files(source_root), normalized_language):
        text = path.read_text(encoding="utf-8")
        if not has_frontmatter(text):
            continue
        metadata = parse_frontmatter(text)
        asset_kind = personal_asset_kind(metadata, path)
        title = record_title(metadata, path, text)
        records.append(
            {
                "path": str(path.relative_to(root)),
                "title": title,
                "aliases": record_aliases(metadata, path.relative_to(root), title),
                "type": str(metadata.get("type", "markdown")),
                "asset_kind": asset_kind,
                "status": str(metadata.get("status", "reference")),
                "card_maturity_level": str(metadata.get("card_maturity_level", "")),
                "project_maturity": str(metadata.get("project_maturity", metadata.get("incubation_maturity", ""))),
                "relationship_maturity": str(metadata.get("relationship_maturity", "")),
                "group_level": str(metadata.get("group_level", "")),
                "sensitivity": str(metadata.get("sensitivity", "internal")),
                "analysis_state": str(metadata.get("analysis_state", "M1_registered")),
                "tags": list_value(metadata, "tags"),
                "related_people": list_value(metadata, "related_people"),
                "related_projects": list_value(metadata, "related_projects"),
                "agent_summary": agent_summary(text),
                "case_mode": "personal_local_material",
                "content_language": language_for_path(path),
            }
        )
    data = {
        "generated_at": date.today().isoformat(),
        "schema_id": "researchos-personal-vault-data-v1",
        "source": f"{source_root.relative_to(root).as_posix() + '/' if source_root != root else ''}00_identity..06_active_context",
        "vault_root": source_root.relative_to(root).as_posix() if source_root != root else ".",
        "boundary": "local_private_material",
        "case_materials": {
            "enabled": False,
            "source": "08_exports/public_starter",
            "content_language": normalized_language,
            "available_content_languages": available_languages,
            "alternate_language_files": config.get("alternate_language_files", "reference_only_do_not_read_by_agent"),
            "agent_language_routing": config.get("agent_language_routing", "selected_language_only"),
            "language_freeze": language_freeze_state(normalized_language, available_languages),
            "disabled_behavior": "reference_only_in_personal_vault_mode",
        },
        "records": records,
        "record_count": len(records),
    }
    failures.extend(validate_personal_onboarding_outputs(source_root))
    return data, failures


def demo_asset_kind(record: dict[str, Any]) -> str:
    explicit = str(record.get("asset_kind", "")).strip()
    if explicit in {"paper", "person", "project", "talk"}:
        return explicit
    haystack = f"{record.get('type', '')} {record.get('path', '')} {record.get('title', '')}".lower().replace("_", "-")
    if "paper" in haystack:
        return "paper"
    if "reading-note" in haystack or "demo_note" in haystack:
        return "paper"
    if "talk" in haystack:
        return "talk"
    if "collaborator" in haystack or "person" in haystack or "people" in haystack:
        return "person"
    if "plan" in haystack or "project" in haystack:
        return "project"
    return "markdown"


def demo_asset_level(record: dict[str, Any]) -> tuple[str, str, str]:
    haystack = f"{record.get('path', '')} {record.get('title', '')}".lower()
    if record.get("type") == "card_level_example":
        return ("M3_cross_project_deepening", "M3", "Maturity guide")
    if record.get("type") == "card_maturity_rubric":
        return ("M2_refined_read", "M2", "Rubric")
    if "level-3" in haystack:
        return ("M3_cross_project_deepening", "M3", "Cross-linked")
    if "level-2" in haystack:
        return ("M2_refined_read", "M2", "Evidence-linked")
    return ("M1_registered", "M1", "Registered")


def is_dashboard_asset(record: dict[str, Any]) -> bool:
    if str(record.get("asset_kind", "")) in {"paper", "person", "project", "talk"}:
        return True
    record_type = str(record.get("type", ""))
    return record_type in DASHBOARD_ASSET_TYPES


def dashboard_item_from_record(record: dict[str, Any]) -> dict[str, Any]:
    level, short_label, level_label = demo_asset_level(record)
    explicit_level = str(record.get("analysis_state", "")).strip()
    if explicit_level.startswith("M3"):
        level, short_label, level_label = explicit_level, "M3", "Cross-linked"
    elif explicit_level.startswith("M2"):
        level, short_label, level_label = explicit_level, "M2", "Evidence-linked"
    elif explicit_level.startswith("M1"):
        level, short_label, level_label = explicit_level, "M1", "Registered"
    kind = demo_asset_kind(record)
    return {
        "id": record["path"],
        "path": record["path"],
        "title": record["title"],
        "type": kind,
        "status": record.get("status", "reference"),
        "card_maturity_level": record.get("card_maturity_level", ""),
        "project_maturity": record.get("project_maturity", ""),
        "relationship_maturity": record.get("relationship_maturity", ""),
        "group_level": record.get("group_level", ""),
        "summary": record.get("agent_summary", ""),
        "next_step": "Open the Markdown example, compare the fields, then replace the fictional content with public-safe user material.",
        "analysis_state": level,
        "analysis_state_label": level_label,
        "analysis_state_short_label": short_label,
        "confidence": "source",
        "stage_label": "Public starter demo",
        "mainline": "First-run onboarding",
        "related_people": record.get("related_people", []),
        "related_projects": record.get("related_projects", []),
        "aliases": record.get("aliases", [record.get("title", ""), record.get("path", "")]),
    }


def unique_alias_index(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index only unambiguous aliases so relations never guess between cards."""
    candidates: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        aliases = item.get("aliases", []) or [item.get("title", ""), item.get("path", "")]
        for alias in aliases:
            key = str(alias).strip().casefold()
            if key:
                candidates.setdefault(key, []).append(item)
    return {key: matches[0] for key, matches in candidates.items() if len(matches) == 1}


def build_dashboard_projection(public_data: dict[str, Any]) -> dict[str, Any]:
    records = list(public_data.get("records", []))
    language = str(public_data.get("case_materials", {}).get("content_language", "en"))
    language_freeze = public_data.get("case_materials", {}).get("language_freeze") or language_freeze_state(
        language,
        public_data.get("case_materials", {}).get("available_content_languages"),
    )
    dashboard_records = [record for record in records if is_dashboard_asset(record)]
    items = [dashboard_item_from_record(record) for record in dashboard_records]
    papers = [item for item in items if item["type"] == "paper"]
    talks = [item for item in items if item["type"] == "talk"]
    people = [item for item in items if item["type"] == "person"]
    projects = [item for item in items if item["type"] == "project"]
    level_counts = {
        "M1_registered": sum(1 for item in items if item["analysis_state"] == "M1_registered"),
        "M2_refined_read": sum(1 for item in items if item["analysis_state"] == "M2_refined_read"),
        "M3_cross_project_deepening": sum(1 for item in items if item["analysis_state"] == "M3_cross_project_deepening"),
    }


    relation_matrix = []
    for paper in papers[:6]:
        relation_matrix.append({
            **paper,
            "relation_count": len(people[:3]) + len(projects[:2]) + len(talks[:2]),
            "people": people[:3],
            "projects": projects[:2],
            "talks": talks[:2],
        })
    lifecycle_mounts = [
        {
            "title": project["title"],
            "path": project["path"],
            "attention_priority": "P1",
            "current_stage": "Demo plan ready for replacement",
            "last_operation": "Generated from public starter examples",
            "next_step": "Open the card, compare the fields, then create a real public-safe plan card.",
            "started": public_data.get("generated_at", ""),
            "repo_hint": "public starter",
        }
        for project in projects[:4]
    ]
    preview_documents = [
        {
            "path": record["path"],
            "title": record["title"],
            "kind": demo_asset_kind(record),
            "layer": "08_exports/public_starter",
            "sensitivity": "public",
            "updated": public_data.get("generated_at", ""),
            "priority": index + 1,
        }
        for index, record in enumerate(records)
    ]
    base_tasks = public_tasks_for_language(language)
    plugins = load_plugin_registry(
        ROOT,
        runtime_scope="public_starter",
        language=language,
        base_task_ids={str(task.get("id", "")) for task in base_tasks},
    )
    tasks = [*base_tasks, *plugins["tasks"]]
    plugin_payload = {key: value for key, value in plugins.items() if key != "tasks"}
    extensions = {
        "api_version": plugins["core_api_version"],
        "schema_id": plugins["schema_id"],
        "runtime_scope": plugins["runtime_scope"],
        "active_language": plugins["active_language"],
        "loaded": plugins["loaded"],
    }
    return {
        "generated_at": public_data.get("generated_at", ""),
        "repo": "researchos-public-starter",
        "version": "researchos-public-starter-v1",
        "runtime_mode": "public_starter",
        "boundary": "fictional_public_demo_only",
        "language_freeze": language_freeze,
        "config": {
            "project_name": "ResearchOS Public Starter",
            "language": language,
            "content_language": language,
            "language_freeze": language_freeze,
            "dashboard": {
                "language": language,
                "available_languages": ["en", "zh-CN"],
            },
            "provider": {
                "default_provider": "codex",
                "provider_mode": "copy_only",
                "execution_scope": "none",
                "execution_probe_required": False,
                "maintenance_scope": "registered_actions",
                "allow_local_codex": False,
                "allow_real_api": False,
            },
            "surface_candidates": {"handoff_admit_candidate": False, "runtime_profile_selector": False},
        },
        "source_overview": {
            "summary": "Public demo data generated from 08_exports/public_starter.",
            "materials": {
                "reading_notes": len(papers),
                "analysis_state_counts": level_counts,
            },
            "people": {
                "registered_collaborators": len(people),
                "active_deep_collaborators": 0,
            },
            "research_map": {
                "mainline_count": 1,
                "active_projects": len(projects),
                "project_pages": len(projects),
                "mainlines": [
                    {
                        "title": "First-run onboarding",
                        "summary": "Identity intake, first cards, evidence links, and case-disable workflow.",
                    }
                ],
            },
            "blocked_sources": [
                "non-public working repository",
                "raw corpus",
                "runtime logs",
                "provider secrets",
            ],
        },
        "asset_graph": {
            "papers": papers,
            "talks": talks,
            "people": people,
            "projects": projects,
            "asset_understanding_quality": {
                "items": items,
            },
            "asset_relation_matrix": relation_matrix,
            "cross_project_mounts": {
                "mounts": lifecycle_mounts,
            },
        },
        "tasks": tasks,
        "tasks_i18n": {},
        "plugins": plugin_payload,
        "extensions": extensions,
        "assistant_modes": public_assistant_modes_for_language(language),
        "assistant_modes_i18n": {},
        "preview_documents": preview_documents,
        "home_command_center": {"research_portfolio": public_research_agenda(ROOT, STARTER_DIR, public_data)},
        "public_starter": {
            "source": public_data.get("source", "08_exports/public_starter"),
            "generated_data": "08_exports/public_starter/generated-public-starter-data.json",
            "case_materials": public_data.get("case_materials", {}),
            "record_count": public_data.get("record_count", 0),
        },
        "commands": [
            {"id": "build_public_starter_data", "label": "Rebuild Dashboard data", "command": "python3 scripts/build_public_starter_data.py --write"},
            {"id": "validate_runtime_config", "label": "Validate runtime config", "command": "python3 scripts/validate_runtime_config.py"},
            {"id": "validate_agent_architecture", "label": "Validate Agent architecture", "command": "python3 scripts/validate_agent_architecture.py"},
            {"id": "validate_public_safety", "label": "Validate public safety", "command": "python3 scripts/validate_public_safety.py"},
            {"id": "check_all_links", "label": "Check Markdown links", "command": "python3 scripts/check_all_links.py"},
        ],
        "safe_exports": [
            {
                "id": "public_safe_export_policy",
                "status": "policy_only",
                "path": "docs/reference/SAFE_EXPORT_POLICY.md",
            }
        ],
        "health": {
            "validation": {
                "ok": True,
                "scope": "public starter demo",
                "checked_markdown": public_data.get("record_count", 0),
                "broken_links": [],
                "missing_frontmatter": [],
                "missing_agent_summary": [],
            }
        },
    }


def build_personal_dashboard_projection(personal_data: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    projection = build_dashboard_projection(personal_data)
    records = list(personal_data.get("records", []))
    items = [dashboard_item_from_record(record) for record in records if is_dashboard_asset(record)]
    for item in items:
        item["stage_label"] = "Personal local vault"
        item["mainline"] = "User-provided research materials"
        item["next_step"] = "Review the source card, evidence boundary, and next action; keep unconfirmed interpretation as candidate."
    papers = [item for item in items if item["type"] == "paper"]
    talks = [item for item in items if item["type"] == "talk"]
    people = [item for item in items if item["type"] == "person"]
    projects = [item for item in items if item["type"] == "project"]
    people_by_title = unique_alias_index(people)
    projects_by_title = unique_alias_index(projects)
    relation_matrix = []
    for paper in papers:
        related_people = [people_by_title[name.casefold()] for name in paper.get("related_people", []) if name.casefold() in people_by_title]
        related_projects = [projects_by_title[name.casefold()] for name in paper.get("related_projects", []) if name.casefold() in projects_by_title]
        relation_matrix.append({**paper, "relation_count": len(related_people) + len(related_projects), "people": related_people, "projects": related_projects, "talks": []})
    projection.update(
        {
            "repo": "personal-researchos-vault",
            "version": "researchos-personal-vault-v1",
            "runtime_mode": "personal_vault",
            "boundary": "local_private_material",
        }
    )
    projection["config"]["project_name"] = "Personal ResearchOS Vault"
    projection["source_overview"] = {
        "summary": "Local projection generated from the user's own ResearchOS Markdown layers.",
        "materials": {
            "reading_notes": len(papers),
            "analysis_state_counts": {
                "M1_registered": sum(1 for item in items if item["analysis_state"] == "M1_registered"),
                "M2_refined_read": sum(1 for item in items if item["analysis_state"] == "M2_refined_read"),
                "M3_cross_project_deepening": sum(1 for item in items if item["analysis_state"] == "M3_cross_project_deepening"),
            },
        },
        "people": {"registered_collaborators": len(people), "active_deep_collaborators": len(people)},
        "research_map": {
            "mainline_count": 1 if items else 0,
            "active_projects": len(projects),
            "project_pages": len(projects),
            "mainlines": [{"title": "User-provided research materials", "summary": "Evidence-backed local research assets."}] if items else [],
        },
        "blocked_sources": ["provider secrets", "unconfirmed public exports"],
    }
    projection["asset_graph"] = {
        "papers": papers,
        "talks": talks,
        "people": people,
        "projects": projects,
        "asset_understanding_quality": {"items": items},
        "asset_relation_matrix": relation_matrix,
        "cross_project_mounts": {
            "mounts": [
                {
                    "title": project["title"],
                    "path": project["path"],
                    "attention_priority": "P1",
                    "current_stage": project.get("status", "active"),
                    "last_operation": "Generated from personal local Markdown",
                    "next_step": "Review evidence and next action.",
                    "started": personal_data.get("generated_at", ""),
                    "repo_hint": "personal local vault",
                }
                for project in projects[:12]
            ]
        },
    }
    projection["preview_documents"] = [
        {
            "path": record["path"],
            "title": record["title"],
            "kind": demo_asset_kind(record),
            "layer": str(record["path"]).split("/", 1)[0],
            "sensitivity": record.get("sensitivity", "internal"),
            "updated": personal_data.get("generated_at", ""),
            "priority": index + 1,
        }
        for index, record in enumerate(records)
    ]
    vault_root_value = str(personal_data.get("vault_root", ".")).strip()
    vault_root = root if vault_root_value in {"", "."} else root / vault_root_value
    projection.setdefault("home_command_center", {})["research_portfolio"] = personal_research_agenda(
        root,
        personal_data,
        projection["config"]["language"],
        vault_root=vault_root,
    )
    projection["personal_vault"] = {
        "source": personal_data.get("source"),
        "generated_data": "dashboard/data/researchos-local.json",
        "record_count": personal_data.get("record_count", 0),
        "warning": "Local projection may contain private derived metadata. The file is git-ignored and must not be published.",
    }
    projection["config"]["provider"] = {
        "default_provider": "codex",
        "provider_mode": "local_codex",
        "execution_scope": "workspace_write",
        "execution_probe_required": True,
        "maintenance_scope": "registered_actions",
        "allow_local_codex": True,
        "allow_real_api": False,
    }
    projection["config"]["surface_candidates"] = {
        "handoff_admit_candidate": False, "runtime_profile_selector": False,
    }
    language = projection["config"]["language"]
    base_tasks = public_tasks_for_language(language)
    plugins = load_plugin_registry(
        ROOT,
        runtime_scope="personal_vault",
        language=language,
        base_task_ids={str(task.get("id", "")) for task in base_tasks},
    )
    projection["tasks"] = [*base_tasks, *plugins["tasks"]]
    projection["plugins"] = {key: value for key, value in plugins.items() if key != "tasks"}
    projection["extensions"] = {
        "api_version": plugins["core_api_version"],
        "schema_id": plugins["schema_id"],
        "runtime_scope": plugins["runtime_scope"],
        "active_language": plugins["active_language"],
        "loaded": plugins["loaded"],
    }
    projection["commands"] = [
        {"id": "build_personal_vault_data", "label": "Rebuild personal-vault data", "command": "python3 scripts/build_public_starter_data.py --personal-vault --write"},
        {"id": "validate_agent_architecture", "label": "Validate Agent architecture", "command": "python3 scripts/validate_agent_architecture.py"},
        {"id": "check_all_links", "label": "Check Markdown links", "command": "python3 scripts/check_all_links.py"},
    ]
    projection["health"]["validation"]["scope"] = "personal local vault"
    projection["health"]["validation"]["checked_markdown"] = personal_data.get("record_count", 0)
    return projection


def ensure_personal_vault_scaffold(root: Path = PERSONAL_VAULT_ROOT) -> None:
    for relative in (
        "00_identity",
        "01_knowledge/papers/own_papers/reading_notes",
        "01_knowledge/papers/source_files",
        "01_knowledge/projects",
        "04_people/collaborators",
        "06_active_context",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)


def semantic_payload(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if key != "generated_at"}


def retain_source_timestamp(data: dict[str, Any], output: Path) -> dict[str, Any]:
    """Keep an unchanged demo source stable across calendar days."""
    try:
        previous = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return data
    if isinstance(previous, dict) and semantic_payload(previous) == semantic_payload(data):
        timestamp = previous.get("generated_at")
        try:
            date.fromisoformat(timestamp)
        except (TypeError, ValueError):
            return data
        return {**data, "generated_at": timestamp}
    return data


def projection_freshness_failures(data: dict[str, Any], root: Path = ROOT) -> list[str]:
    """Compare source-derived payloads, including policy and task fields."""
    expected = {"08_exports/public_starter/generated-public-starter-data.json": data}
    if should_write_public_dashboard(root):
        expected["dashboard/data/researchos-dashboard.json"] = build_dashboard_projection(data)
    failures: list[str] = []
    for relative, fresh in expected.items():
        try:
            stored = json.loads((root / relative).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            failures.append(f"{relative}: unreadable generated artifact ({error})")
            continue
        if not isinstance(stored, dict) or semantic_payload(stored) != semantic_payload(fresh):
            failures.append(f"{relative}: generated artifact is stale against current source")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Write generated public starter data JSON.")
    mode.add_argument("--check", action="store_true", help="Fail if checked-in public projections differ from source; write nothing.")
    parser.add_argument("--disable-cases", action="store_true", help="Preview/write with case materials disabled, without editing the config file.")
    parser.add_argument("--personal-vault", action="store_true", help="Build a git-ignored local projection from the user's own 00-06 Markdown layers.")
    parser.add_argument("--language", choices=["en", "zh-CN"], help="Select active demo/case language for generated data.")
    args = parser.parse_args()
    if args.check and args.personal_vault:
        parser.error("--check applies to public artifacts, not personal-vault scaffolding")
    if args.personal_vault:
        if args.write:
            ensure_personal_vault_scaffold()
        data, failures = build_personal_vault_data(
            root=ROOT,
            content_language=args.language,
            vault_root=PERSONAL_VAULT_ROOT,
        )
        dashboard_asset_count = sum(1 for record in data["records"] if is_dashboard_asset(record))
        print(f"Source: {data['source']}")
        print("Mode: personal-vault")
        print(f"Content language: {data['case_materials']['content_language']}")
        print(f"Records: {data['record_count']}")
        print(f"Dashboard assets: {dashboard_asset_count}")
        print(f"Output: {PERSONAL_DASHBOARD_OUTPUT.relative_to(ROOT)}")
        if failures:
            for failure in failures:
                print(f"- {failure}")
            return 1
        if args.write:
            PERSONAL_DASHBOARD_OUTPUT.write_text(json.dumps(build_personal_dashboard_projection(data, root=ROOT), ensure_ascii=False, indent=2), encoding="utf-8")
            print("Wrote git-ignored personal vault dashboard projection.")
        else:
            print("Dry run only. Pass --write to create the local projection.")
        return 0
    data, failures = build_public_starter_data(force_cases=False if args.disable_cases else None, content_language=args.language)
    data = retain_source_timestamp(data, OUTPUT)
    dashboard_asset_count = sum(1 for record in data["records"] if is_dashboard_asset(record))
    if data["case_materials"]["enabled"] and data["record_count"] and dashboard_asset_count == 0:
        failures.append("active case materials produced zero dashboard assets; check frontmatter type metadata")
    print(f"Source: {data['source']}")
    print(f"Cases enabled: {data['case_materials']['enabled']}")
    print(f"Content language: {data['case_materials']['content_language']}")
    print(f"Records: {data['record_count']}")
    print(f"Dashboard assets: {dashboard_asset_count}")
    print(f"Output: {OUTPUT.relative_to(ROOT)}")
    if failures:
        print("Public starter data validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    if args.check:
        failures = projection_freshness_failures(data)
        if failures:
            print("\n".join(failures))
            return 1
        print("Public generated artifacts match current source.")
        return 0
    if args.write:
        OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Wrote public starter data.")
        if should_write_public_dashboard():
            DASHBOARD_OUTPUT.write_text(json.dumps(build_dashboard_projection(data), ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Wrote dashboard projection: {DASHBOARD_OUTPUT.relative_to(ROOT)}")
        else:
            print("Preserved private dashboard projection; rebuild it with scripts/build_dashboard_data.py.")
    else:
        print("Dry run only. Pass --write to write the public demo data file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
