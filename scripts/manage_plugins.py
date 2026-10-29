#!/usr/bin/env python3
# ResearchOS maintenance header.
# 中文：ResearchOS 插件示例的一条命令入口；默认在改动后重跑插件校验。
# English: One-command entry point for bundled ResearchOS plugin examples; re-runs plugin validation after a change by default.

"""Install, enable, disable or uninstall a bundled ResearchOS example plugin, locally and reversibly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from researchos_data.plugin_lifecycle import PluginLifecycleError, apply_action, catalog


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage bundled ResearchOS plugin examples safely.")
    parser.add_argument("action", choices=("list", "status", "install", "enable", "disable", "uninstall", "upgrade"))
    parser.add_argument("plugin_id", nargs="?")
    parser.add_argument("--language", choices=("zh-CN", "en"), default="zh-CN")
    parser.add_argument("--no-rebuild", action="store_true", help="Skip the post-change plugin validation (tests only).")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    try:
        if args.action == "list":
            result = catalog(ROOT, args.language)
        elif args.action == "status":
            entries = catalog(ROOT, args.language)
            if args.plugin_id:
                entries = [item for item in entries if item["id"] == args.plugin_id]
                if not entries:
                    raise PluginLifecycleError(f"unknown bundled plugin example: {args.plugin_id}")
            result = entries
        else:
            if not args.plugin_id:
                parser.error("plugin_id is required for lifecycle actions")
            result = apply_action(ROOT, args.plugin_id, args.action, rebuild=not args.no_rebuild)
    except PluginLifecycleError as error:
        print(f"Plugin action stopped safely: {error}")
        return 1

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    entries = result if isinstance(result, list) else [result]
    for item in entries:
        state = "已启用" if item["enabled"] else ("已安装但停用" if item["installed"] else "未安装")
        print(f"{item['id']} · {item['title']} · {state}")
        print("  不访问网络，不直接写入长期记忆。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
