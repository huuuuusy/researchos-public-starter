# ResearchOS maintenance header.
# 中文：ResearchOS 本地插件生命周期；只管理仓库内随附示例到 Git 忽略的本地 manifest，不安装任意远程代码。
# English: Local ResearchOS plugin lifecycle; manages bundled examples in Git-ignored local manifests and never installs arbitrary remote code.

"""Safe install, enable, disable, and uninstall operations for bundled plugin examples."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from researchos_data.plugins import PluginManifestError, _safe_source_data, validate_plugin_files
from researchos_data.task_extensions import validate_extension_files
from researchos_kernel.atomic_files import atomic_write_bytes, atomic_write_json


PLUGIN_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
EXAMPLE_SOURCES = (
    ("plugin", Path("config/plugins"), Path("config/plugins.local")),
    ("task_extension", Path("config/extensions"), Path("config/extensions.local")),
)


class PluginLifecycleError(ValueError):
    """Raised when a local plugin lifecycle action would be unsafe or ambiguous."""


@dataclass(frozen=True)
class BundledPlugin:
    plugin_id: str
    kind: str
    source: Path
    target: Path
    manifest: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PluginLifecycleError(f"{path}: manifest root must be an object")
    return value


def _normalized_without_enabled(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "enabled"}


def _baseline_path(plugin: BundledPlugin) -> Path:
    # Non-manifest suffix keeps installation metadata out of contribution discovery.
    return plugin.target.with_suffix(".installed-baseline")


def _managed(plugin: BundledPlugin, current: dict[str, Any]) -> bool:
    baseline = _baseline_path(plugin)
    expected = _read_json(baseline) if baseline.is_file() else plugin.manifest
    return _normalized_without_enabled(current) == _normalized_without_enabled(expected)


def _local_name(source: Path) -> str:
    suffix = ".example.json"
    return f"{source.name[:-len(suffix)]}.json" if source.name.endswith(suffix) else source.name


def bundled_plugins(root: Path) -> list[BundledPlugin]:
    root = root.resolve()
    bundled: list[BundledPlugin] = []
    seen: set[str] = set()
    for kind, source_dir, target_dir in EXAMPLE_SOURCES:
        for source in sorted((root / source_dir).glob("*.example.json")):
            try:
                manifest = _safe_source_data(root, source)
            except PluginManifestError as error:
                raise PluginLifecycleError(str(error)) from error
            if not isinstance(manifest, dict):
                raise PluginLifecycleError(f"{source}: manifest root must be an object")
            plugin_id = str(manifest.get("id") or "").strip()
            if not PLUGIN_ID_PATTERN.fullmatch(plugin_id):
                raise PluginLifecycleError(f"{source}: example id must use lower_snake_case")
            if plugin_id in seen:
                raise PluginLifecycleError(f"bundled example id is ambiguous: {plugin_id}")
            seen.add(plugin_id)
            bundled.append(BundledPlugin(
                plugin_id=plugin_id,
                kind=kind,
                source=source,
                target=root / target_dir / _local_name(source),
                manifest=manifest,
            ))
    return bundled


def bundled_plugin(root: Path, plugin_id: str) -> BundledPlugin:
    normalized = str(plugin_id or "").strip()
    if not PLUGIN_ID_PATTERN.fullmatch(normalized):
        raise PluginLifecycleError("plugin id must use lower_snake_case")
    matches = [plugin for plugin in bundled_plugins(root) if plugin.plugin_id == normalized]
    if not matches:
        raise PluginLifecycleError(f"unknown bundled plugin example: {normalized}")
    return matches[0]


def plugin_title(plugin: BundledPlugin, language: str = "zh-CN") -> str:
    locales = plugin.manifest.get("task", {}).get("locales", {}) if plugin.kind == "task_extension" else {}
    if not locales:
        slots = plugin.manifest.get("contributions", {}).get("ui_slots", [])
        locales = slots[0].get("locales", {}) if slots else {}
    locale = locales.get(language) or locales.get("en") or {}
    return str(locale.get("name") or locale.get("title") or plugin.plugin_id).strip()


def plugin_status(plugin: BundledPlugin, language: str = "zh-CN") -> dict[str, Any]:
    installed = plugin.target.is_file()
    local_manifest = _read_json(plugin.target) if installed else {}
    managed = not installed or _managed(plugin, local_manifest)
    return {
        "id": plugin.plugin_id,
        "title": plugin_title(plugin, language),
        "kind": plugin.kind,
        "installed": installed,
        "enabled": bool(local_manifest.get("enabled")) if installed else False,
        "managed": managed,
        "installed_version": local_manifest.get("version") if installed else None,
        "bundled_version": plugin.manifest.get("version"),
        "upgrade_available": installed and _normalized_without_enabled(local_manifest) != _normalized_without_enabled(plugin.manifest),
        "network_access": False,
        "canonical_write": False,
    }


def catalog(root: Path, language: str = "zh-CN") -> list[dict[str, Any]]:
    return [plugin_status(plugin, language) for plugin in bundled_plugins(root)]


def _validate(root: Path) -> None:
    failures = [*validate_plugin_files(root), *validate_extension_files(root)]
    if failures:
        raise PluginLifecycleError("plugin validation failed:\n- " + "\n- ".join(failures))
    host_validator = root / "scripts/validate_plugins.py"
    if host_validator.is_file():
        result = subprocess.run(
            [sys.executable, "scripts/validate_plugins.py"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            detail = (result.stdout or result.stderr or "plugin host validation failed").strip()
            raise PluginLifecycleError(detail)


def rebuild_command(root: Path) -> list[str]:
    # Headless validation is the default projection check. Dashboard builders
    # remain a compatibility fallback for packages that do not ship the host
    # validator yet.
    if (root / "scripts/validate_plugins.py").is_file():
        return [sys.executable, "scripts/validate_plugins.py"]
    if (root / "scripts/build_dashboard_data.py").is_file():
        return [sys.executable, "scripts/build_dashboard_data.py"]
    if (root / "scripts/build_public_starter_data.py").is_file():
        return [sys.executable, "scripts/build_public_starter_data.py", "--write"]
    raise PluginLifecycleError("no registered dashboard builder is available")


def _restore(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
        return
    atomic_write_bytes(path, previous)


def apply_action(root: Path, plugin_id: str, action: str, *, rebuild: bool = False) -> dict[str, Any]:
    root = root.resolve()
    plugin = bundled_plugin(root, plugin_id)
    action = str(action or "").strip().lower()
    if action not in {"install", "enable", "disable", "uninstall", "upgrade"}:
        raise PluginLifecycleError("action must be install, enable, disable, uninstall, or upgrade")
    baseline = _baseline_path(plugin)
    for path in (plugin.target, baseline):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise PluginLifecycleError("local plugin management paths must stay inside the repository")
    previous_baseline = baseline.read_bytes() if baseline.is_file() else None
    previous = plugin.target.read_bytes() if plugin.target.is_file() else None
    current = _read_json(plugin.target) if previous is not None else None
    if current is not None and not _managed(plugin, current):
        raise PluginLifecycleError(
            "local plugin differs from the bundled example; preserve it and review manually instead of overwriting"
        )
    if action == "upgrade" and current is None:
        raise PluginLifecycleError("plugin is not installed; use install first")
    try:
        if action in {"install", "enable", "disable", "upgrade"}:
            manifest = dict(plugin.manifest if action == "upgrade" else current or plugin.manifest)
            manifest["enabled"] = bool(current.get("enabled")) if action == "upgrade" else action != "disable"
            # Install is idempotent; only explicit upgrade replaces an installed version.
            if current is None or previous_baseline is None or action == "upgrade":
                atomic_write_json(baseline, manifest)
            atomic_write_json(plugin.target, manifest)
        else:
            plugin.target.unlink(missing_ok=True)
            baseline.unlink(missing_ok=True)
        _validate(root)
        if rebuild:
            subprocess.run(rebuild_command(root), cwd=root, check=True)
    except Exception:
        _restore(plugin.target, previous)
        _restore(baseline, previous_baseline)
        if rebuild:
            try:
                subprocess.run(rebuild_command(root), cwd=root, check=True)
            except Exception:
                pass
        raise
    return {"action": action, **plugin_status(plugin)}
