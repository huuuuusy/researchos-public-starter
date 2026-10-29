#!/usr/bin/env python3
"""Print the public starter's contracted headless plugin portfolio."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from researchos_data.plugin_portfolio import current_plugin_portfolio


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("public_starter", "personal_vault"), default="public_starter")
    args = parser.parse_args()
    print(json.dumps(current_plugin_portfolio(ROOT, runtime_scope=args.scope), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
