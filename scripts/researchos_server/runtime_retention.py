# ResearchOS maintenance header.
# 中文：运行态文件保留 owner；集中处理可重建日志的压缩，避免执行 owner 承担存储策略。
# English: Runtime-file retention owner; compacts rebuildable logs without mixing storage policy into execution owners.

"""Bounded retention helpers for local runtime files."""

from __future__ import annotations

import json
from pathlib import Path

from researchos_kernel.atomic_files import atomic_write_text
from researchos_kernel.task_envelope import task_envelope_ref


def compact_jsonl_run_log(
    path: Path,
    *,
    max_bytes: int,
    max_runs: int,
    output_limit: int,
    force: bool = False,
) -> dict[str, int]:
    """Keep one merged record for each of the newest bounded run IDs."""
    if not path.exists():
        return {"before_bytes": 0, "after_bytes": 0, "retained_runs": 0}
    before_bytes = path.stat().st_size
    if not force and before_bytes <= max(1, int(max_bytes)):
        return {"before_bytes": before_bytes, "after_bytes": before_bytes, "retained_runs": 0}
    records: dict[str, dict[str, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        run_id = str(event.get("id", "")).strip()
        if run_id:
            records[run_id] = {**records.get(run_id, {}), **event}
    retained = sorted(
        records.values(),
        key=lambda item: str(item.get("updated_at", item.get("created_at", ""))),
        reverse=True,
    )[: max(1, int(max_runs))]
    compacted: list[str] = []
    for record in reversed(retained):
        safe_record = dict(record)
        safe_record.pop("prompt", None)
        if "task_envelope" in safe_record:
            safe_record["task_envelope_ref"] = task_envelope_ref(safe_record.pop("task_envelope"))
        if "output" in safe_record:
            safe_record["output"] = str(safe_record.get("output", ""))[-output_limit:]
        compacted.append(json.dumps(safe_record, ensure_ascii=False, sort_keys=True))
    atomic_write_text(path, ("\n".join(compacted) + "\n") if compacted else "")
    return {
        "before_bytes": before_bytes,
        "after_bytes": path.stat().st_size,
        "retained_runs": len(retained),
    }
