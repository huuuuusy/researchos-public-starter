# ResearchOS maintenance header.
# 中文：本地子进程执行与 CLI 环境投影的 owner；ros 派发、Dashboard runner、模型目录与重建／维护步骤共用。
# English: Owner of local subprocess execution and the CLI environment projection; shared by ros dispatch, the Dashboard runner, model discovery and rebuild/maintenance steps.

"""Local subprocess runner and the credential-free environment handed to the CLI runners."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping


CODEX_CLI_ENV_KEYS = frozenset({
    "PATH",
    "HOME",
    "CODEX_HOME",
    "TMPDIR",
    "LANG",
    "TZ",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
})


def codex_cli_env(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Project only the process settings Codex needs, never ambient credentials."""
    source = os.environ if environ is None else environ
    return {
        key: str(value)
        for key, value in source.items()
        if key in CODEX_CLI_ENV_KEYS or key.startswith("LC_")
    }


@dataclass(frozen=True)
class CommandRunner:
    root: Path
    output_limit: int = 4000

    def run(
        self,
        args: list[str],
        timeout: int = 90,
        input_text: str | None = None,
        env: Mapping[str, str] | None = None,
    ) -> dict[str, object]:
        started = datetime.now()
        try:
            completed = subprocess.run(
                args,
                cwd=self.root,
                input=input_text,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
                env=dict(env) if env is not None else None,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else "Timed out"
            return {
                "ok": False,
                "returncode": "timeout",
                "seconds": round((datetime.now() - started).total_seconds(), 2),
                "stdout": stdout,
                "output": stdout.strip()[-self.output_limit:],
            }
        stdout = completed.stdout or ""
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "seconds": round((datetime.now() - started).total_seconds(), 2),
            "stdout": stdout,
            "output": stdout.strip()[-self.output_limit:],
        }

    def run_step(self, label: str, args: list[str], timeout: int = 90, optional: bool = False) -> dict[str, object]:
        result = self.run(args, timeout=timeout)
        ok = bool(result.get("ok"))
        return {
            "label": label,
            "ok": ok,
            "required_ok": ok,
            "optional": optional,
            "returncode": result.get("returncode"),
            "seconds": result.get("seconds"),
            "output": result.get("output", ""),
        }
