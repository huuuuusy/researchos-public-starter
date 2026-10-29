"""Versioned Markdown metadata-profile contract and compatibility projection.

This module does not write Markdown.  It defines the strict v1 vocabulary and a
read-only projection for legacy frontmatter so migration can be tested before
any canonical file is changed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from researchos_kernel.atomic_files import atomic_write_bytes


SCHEMA_ID = "researchos-metadata-profile-v1"
READ_SCHEMA_ID = "researchos-metadata-profile-read-v1"

PROFILE_IDS = (
    "canonical_knowledge",
    "decision_cognition",
    "workflow_contract",
    "active_context_task_run",
    "generated_projection",
    "export_public_safe",
    "template_schema",
    "people_sensitive",
)
RECORD_STATES = ("draft", "active", "paused", "completed", "superseded", "archived", "retired")
AUTHORITY_ROLES = ("none", "informative", "interpretive", "normative")
SENSITIVITY_LEVELS = ("public", "internal", "sensitive", "private")
EXPORT_POLICIES = ("public", "allowlisted", "internal_only", "local_only", "no_export")

COMMON_REQUIRED = (
    "schema_version",
    "metadata_profile",
    "type",
    "title",
    "record_state",
    "authority_role",
    "sensitivity",
    "export_policy",
    "owner",
)
COMMON_OPTIONAL = ("created", "updated", "tags", "relations")
PROFILE_FIELDS = {
    "canonical_knowledge": ("evidence_state", "last_verified", "source_refs"),
    "decision_cognition": ("admission_ref", "source_episodes", "counterexamples", "review_date"),
    "workflow_contract": ("governed_by", "contract_level"),
    "active_context_task_run": ("gate", "next_resume", "current_consumer"),
    "generated_projection": ("generated_by", "source_digest", "rebuild_command"),
    "export_public_safe": ("export_target", "derived_from"),
    "template_schema": (
        "template_for", "governed_by", "agent_reading_level", "context_budget", "capsule_of", "exportable_to",
    ),
    "people_sensitive": ("privacy_basis", "access_scope"),
}

TYPE_PROFILE_HINTS = {
    "decision": "decision_cognition",
    "heuristic": "decision_cognition",
    "mental_model": "decision_cognition",
    "workflow": "workflow_contract",
    "product_contract": "workflow_contract",
    "implementation_plan": "active_context_task_run",
    "active_context": "active_context_task_run",
    "task_run": "active_context_task_run",
    "template": "template_schema",
    "experiment_template": "template_schema",
    "person": "people_sensitive",
}

LEGACY_RECORD_STATES = {
    "pending": "draft",
    "planned": "draft",
    "in_progress": "active",
    "current": "active",
    "inactive": "paused",
    "done": "completed",
    "complete": "completed",
}

LEGACY_SOURCE_BOUNDARIES = {
    "public": ("public", "public"),
    "public_safe": ("public", "allowlisted"),
    "internal": ("internal", "internal_only"),
    "local_only": ("internal", "local_only"),
    "not_exportable": ("internal", "no_export"),
    "no-export": ("internal", "no_export"),
    "sensitive": ("sensitive", "no_export"),
    "private": ("private", "no_export"),
}


@dataclass(frozen=True)
class MetadataProfileError(ValueError):
    code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


@dataclass(frozen=True)
class MetadataMigrationReceipt:
    before_sha256: str
    after_sha256: str
    before_text: str
    after_text: str

    @property
    def changed(self) -> bool:
        return self.before_sha256 != self.after_sha256


def _text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _string_list(value: object, *, field: str) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise MetadataProfileError("invalid_metadata_field", f"{field} must be a list of strings")
    items = [_text(item) for item in value]
    if any(not item for item in items):
        raise MetadataProfileError("invalid_metadata_field", f"{field} contains an empty value")
    return list(dict.fromkeys(items))


def infer_profile(metadata: Mapping[str, object], *, profile_hint: str = "") -> str:
    hint = _text(profile_hint)
    if hint:
        if hint not in PROFILE_IDS:
            raise MetadataProfileError("unknown_metadata_profile", hint)
        return hint
    record_type = _text(metadata.get("type"))
    return TYPE_PROFILE_HINTS.get(record_type, "canonical_knowledge")


def _strict_record(metadata: Mapping[str, object]) -> dict[str, object]:
    if _text(metadata.get("schema_version")) != SCHEMA_ID:
        raise MetadataProfileError("unsupported_metadata_schema", _text(metadata.get("schema_version")))
    profile = _text(metadata.get("metadata_profile"))
    if profile not in PROFILE_IDS:
        raise MetadataProfileError("unknown_metadata_profile", profile)
    allowed = set(COMMON_REQUIRED + COMMON_OPTIONAL + PROFILE_FIELDS[profile])
    unknown = sorted(set(metadata) - allowed)
    if unknown:
        raise MetadataProfileError("unknown_metadata_field", ", ".join(unknown))
    missing = [field for field in COMMON_REQUIRED if not _text(metadata.get(field))]
    if missing:
        raise MetadataProfileError("missing_metadata_field", ", ".join(missing))
    record_state = _text(metadata.get("record_state"))
    authority_role = _text(metadata.get("authority_role"))
    sensitivity = _text(metadata.get("sensitivity"))
    export_policy = _text(metadata.get("export_policy"))
    enums = (
        ("record_state", record_state, RECORD_STATES),
        ("authority_role", authority_role, AUTHORITY_ROLES),
        ("sensitivity", sensitivity, SENSITIVITY_LEVELS),
        ("export_policy", export_policy, EXPORT_POLICIES),
    )
    for field, value, choices in enums:
        if value not in choices:
            raise MetadataProfileError("invalid_metadata_enum", f"{field}={value}")
    if sensitivity == "internal" and export_policy == "public":
        raise MetadataProfileError("invalid_metadata_boundary", "internal content cannot use public export")
    if sensitivity in {"sensitive", "private"} and export_policy not in {"local_only", "no_export"}:
        raise MetadataProfileError("invalid_metadata_boundary", f"{sensitivity} content cannot use {export_policy}")
    normalized: dict[str, object] = {
        "schema_version": SCHEMA_ID,
        "metadata_profile": profile,
        "type": _text(metadata.get("type")),
        "title": _text(metadata.get("title")),
        "record_state": record_state,
        "authority_role": authority_role,
        "sensitivity": sensitivity,
        "export_policy": export_policy,
        "owner": _text(metadata.get("owner")),
    }
    for field in COMMON_OPTIONAL:
        if field not in metadata:
            continue
        normalized[field] = _string_list(metadata[field], field=field) if field in {"tags", "relations"} else _text(metadata[field])
    list_fields = {
        "source_refs", "source_episodes", "counterexamples", "governed_by", "derived_from", "capsule_of", "exportable_to",
    }
    for field in PROFILE_FIELDS[profile]:
        if field not in metadata:
            continue
        normalized[field] = _string_list(metadata[field], field=field) if field in list_fields else _text(metadata[field])
    return normalized


def normalize_metadata_record(metadata: Mapping[str, object]) -> dict[str, object]:
    """Validate a v1 record for new writes; partial v1 never falls back to legacy."""
    if not isinstance(metadata, Mapping):
        raise MetadataProfileError("invalid_metadata_record", "frontmatter must be a mapping")
    if "schema_version" not in metadata or "metadata_profile" not in metadata:
        raise MetadataProfileError("missing_metadata_contract", "schema_version and metadata_profile are required")
    return _strict_record(dict(metadata))


def read_metadata_profile(metadata: Mapping[str, object], *, profile_hint: str = "") -> dict[str, object]:
    """Return a bounded compatibility projection without mutating legacy input."""
    if not isinstance(metadata, Mapping):
        raise MetadataProfileError("invalid_metadata_record", "frontmatter must be a mapping")
    raw = dict(metadata)
    has_schema = "schema_version" in raw or "metadata_profile" in raw
    if has_schema:
        normalized = normalize_metadata_record(raw)
        return {
            "schema_id": READ_SCHEMA_ID,
            "source_mode": "v1",
            "profile": normalized,
            "missing_required": [],
            "legacy_fields": [],
        }

    profile = infer_profile(raw, profile_hint=profile_hint)
    status = _text(raw.get("record_state") or raw.get("status") or "draft")
    record_state = LEGACY_RECORD_STATES.get(status, status if status in RECORD_STATES else "draft")
    authority = _text(raw.get("authority_role") or "none")
    authority = authority if authority in AUTHORITY_ROLES else "none"
    legacy_sensitivity = _text(raw.get("sensitivity") or "internal")
    sensitivity, default_export = LEGACY_SOURCE_BOUNDARIES.get(legacy_sensitivity, ("internal", "internal_only"))
    explicit_export = _text(raw.get("export_policy"))
    export_policy = explicit_export if explicit_export in EXPORT_POLICIES else default_export
    owner = _text(raw.get("owner") or raw.get("current_consumer"))
    missing = [field for field, value in (("title", raw.get("title")), ("owner", owner)) if not _text(value)]
    projection = {
        "schema_version": "legacy",
        "metadata_profile": profile,
        "type": _text(raw.get("type") or "unknown"),
        "title": _text(raw.get("title")),
        "record_state": record_state,
        "authority_role": authority,
        "sensitivity": sensitivity,
        "export_policy": export_policy,
        "owner": owner,
    }
    return {
        "schema_id": READ_SCHEMA_ID,
        "source_mode": "legacy",
        "profile": projection,
        "missing_required": missing,
        "legacy_fields": sorted(key for key in ("status", "current_consumer", "sensitivity") if key in raw),
    }


def has_markdown_frontmatter(text: str) -> bool:
    return text.startswith("---\n") and "\n---\n" in text[4:]


def parse_frontmatter_raw(text: str) -> dict[str, object]:
    """Parse the bounded scalar/list subset of ResearchOS frontmatter; no compatibility aliases.

    This is the one parser shared by metadata migration, the Dashboard data helpers, safe export
    and the public-release inventory. A blank line does not end a block list, so a list item after
    it (for example a `human-sensitive` tag) is still read. `[a, b]` stays a plain string: an inline
    list is never read as `exportable_to` targets.
    """
    if not has_markdown_frontmatter(text):
        return {}
    block = text.split("\n---\n", 1)[0].removeprefix("---\n")
    data: dict[str, object] = {}
    current_list_key = ""
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if current_list_key and line.strip().startswith("- "):
            current = data.setdefault(current_list_key, [])
            if isinstance(current, list):
                current.append(line.strip()[2:].strip().strip('"'))
            continue
        current_list_key = ""
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if value in {"", "[]"}:
            data[key] = []
            current_list_key = key if value == "" else ""
        else:
            data[key] = value.strip('"')
    return data


def read_export_frontmatter(text: str) -> dict[str, object]:
    """parse_frontmatter_raw for privacy decisions, with `sensitivity` read from fixed positions only.

    The first top-level `sensitivity:` line wins and a later repeat never overrides it. Without one,
    only a direct child of a top-level `metadata:` block counts (where Agent Skills declare it). Any
    other nested `sensitivity:` is ignored, so nesting can never relax the first declaration.
    """
    data = parse_frontmatter_raw(text)
    data.pop("sensitivity", None)
    if not has_markdown_frontmatter(text):
        return data
    block = text.split("\n---\n", 1)[0].removeprefix("---\n")
    top_level = metadata_child = None
    in_metadata, child_indent = False, None
    for line in block.splitlines():
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            in_metadata = line.rstrip() == "metadata:"
            child_indent = None
            if top_level is None and line.startswith("sensitivity:"):
                top_level = line.split(":", 1)[1].strip().strip('"')
            continue
        if in_metadata:
            child_indent = indent if child_indent is None else child_indent
            stripped = line.strip()
            if indent == child_indent and metadata_child is None and stripped.startswith("sensitivity:"):
                metadata_child = stripped.split(":", 1)[1].strip().strip('"')
    value = top_level if top_level is not None else metadata_child
    if value is not None:
        data["sensitivity"] = value
    return data


def build_v1_from_legacy(
    metadata: Mapping[str, object], *, profile_hint: str, owner: str, overrides: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build one explicit v1 candidate; unknown legacy fields are never copied implicitly."""
    raw = dict(metadata)
    if "schema_version" in raw or "metadata_profile" in raw:
        candidate = {**raw, **dict(overrides or {})}
        return normalize_metadata_record(candidate)
    projection = read_metadata_profile(raw, profile_hint=profile_hint)["profile"]
    profile = _text(projection["metadata_profile"])
    candidate: dict[str, object] = {
        "schema_version": SCHEMA_ID,
        "metadata_profile": profile,
        "type": _text(raw.get("type") or projection["type"]),
        "title": _text(raw.get("title") or projection["title"]),
        "record_state": _text(projection["record_state"]),
        "authority_role": _text(projection["authority_role"]),
        "sensitivity": _text(projection["sensitivity"]),
        "export_policy": _text(projection["export_policy"]),
        "owner": _text(owner),
    }
    for field in COMMON_OPTIONAL + PROFILE_FIELDS[profile]:
        if field in raw:
            candidate[field] = raw[field]
    candidate.update(dict(overrides or {}))
    return normalize_metadata_record(candidate)


def render_metadata_record(metadata: Mapping[str, object]) -> str:
    record = normalize_metadata_record(metadata)
    profile = _text(record["metadata_profile"])
    order = COMMON_REQUIRED + COMMON_OPTIONAL + PROFILE_FIELDS[profile]
    lines: list[str] = []
    for field in order:
        if field not in record:
            continue
        value = record[field]
        if isinstance(value, list):
            if not value:
                lines.append(f"{field}: []")
            else:
                lines.append(f"{field}:")
                lines.extend(f"  - {json.dumps(item, ensure_ascii=False)}" for item in value)
        else:
            lines.append(f"{field}: {json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines)


def prepare_metadata_migration(
    text: str, *, profile_hint: str, owner: str, overrides: Mapping[str, object] | None = None,
) -> MetadataMigrationReceipt:
    if not has_markdown_frontmatter(text):
        raise MetadataProfileError("missing_frontmatter", "migration requires a first-block frontmatter")
    raw = parse_frontmatter_raw(text)
    record = build_v1_from_legacy(raw, profile_hint=profile_hint, owner=owner, overrides=overrides)
    body = text.split("\n---\n", 1)[1]
    after = f"---\n{render_metadata_record(record)}\n---\n{body}"
    digest = lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()
    return MetadataMigrationReceipt(digest(text), digest(after), text, after)


def _atomic_replace(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"), mode=path.stat().st_mode & 0o777)


def apply_metadata_migration(path: Path, receipt: MetadataMigrationReceipt, *, root: Path) -> bool:
    path, root = Path(path), Path(root).resolve()
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
        raise MetadataProfileError("unsafe_metadata_target", str(path))
    current = path.read_text(encoding="utf-8")
    current_digest = hashlib.sha256(current.encode("utf-8")).hexdigest()
    if current_digest == receipt.after_sha256:
        return False
    if current_digest != receipt.before_sha256:
        raise MetadataProfileError("metadata_base_changed", str(path))
    _atomic_replace(path, receipt.after_text)
    return True


def rollback_metadata_migration(path: Path, receipt: MetadataMigrationReceipt, *, root: Path) -> bool:
    path, root = Path(path), Path(root).resolve()
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
        raise MetadataProfileError("unsafe_metadata_target", str(path))
    current = path.read_text(encoding="utf-8")
    current_digest = hashlib.sha256(current.encode("utf-8")).hexdigest()
    if current_digest == receipt.before_sha256:
        return False
    if current_digest != receipt.after_sha256:
        raise MetadataProfileError("metadata_rollback_conflict", str(path))
    _atomic_replace(path, receipt.before_text)
    return True
