# ResearchOS maintenance header.
# 中文：ResearchOS 公开启动版本地 dashboard server 中关于「research scout」的 demo-only owner。
# English: Demo-only Research Scout owner for the public starter dashboard server.

"""Demo-only Research Scout response normalization for the public starter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from researchos_adapters.command_runner import CommandRunner


@dataclass
class ResearchScoutRunner:
    command_runner: CommandRunner
    timeout: int = 90

    def run(self, request_json: str) -> tuple[dict[str, object], int]:
        started = datetime.now()
        try:
            request = json.loads(request_json or "{}")
        except json.JSONDecodeError:
            request = {}
        seconds = round((datetime.now() - started).total_seconds(), 2)
        topic = str(request.get("topic") or request.get("query") or request.get("title") or "the selected research question").strip()
        if not topic:
            topic = "the selected research question"
        prompt = (
            "Use ResearchOS Public Starter as a local, demo-only planning surface. "
            f"Draft a research-scout plan for {topic!r}: list the public sources to search, "
            "evidence boundaries to preserve, candidate cards to create, and the validation checks "
            "required before anything becomes confirmed memory. Do not treat search results or agent "
            "output as confirmed facts until the user reviews them."
        )
        return (
            {
                "ok": False,
                "demo_only": True,
                "message": "Research Scout is demo-only in the public starter. No network search or provider call was run.",
                "seconds": seconds,
                "queries": [topic],
                "search_links": [],
                "results": [],
                "warnings": [
                    "Public starter keeps external research as a candidate plan only.",
                    "Configure a real provider/search adapter only in your own local/private environment.",
                ],
                "agent_prompt": prompt,
            },
            200,
        )
