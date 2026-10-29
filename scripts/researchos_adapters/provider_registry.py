"""Provider registry: the one table of local CLI providers ResearchOS can launch.

A provider is added here and nowhere else in the launch boundary: its CLI-missing error code,
its endpoint reference and the class behind ``ros run --executor provider:<name>`` all come from
its ``ProviderSpec``, and the status, profile and dispatch tables derive from ``PROVIDERS``. No entry
stores a credential; the public starter launches none of them and only copies task packets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    type: str  # the adapter family recorded in runtime profiles
    label: str  # how messages name the CLI, e.g. "the local Codex CLI"
    default_model: str
    cli_missing_error: str  # the pre-launch error when the CLI cannot be found
    endpoint_ref: str  # the only endpoint a runtime profile of this provider may name
    adapter: str  # "module:Class" built as Class(runtime_scope, declared) and run with .execute(request)
    public_starter_allowed: bool
    description_zh: str
    description_en: str


PROVIDERS: Dict[str, ProviderSpec] = {
    "codex": ProviderSpec(
        name="codex",
        type="local_codex",
        label="Codex",
        default_model="auto",
        cli_missing_error="codex_cli_missing",
        endpoint_ref="local:codex-cli",
        adapter="researchos_adapters.dispatch:LocalCodexProvider",
        public_starter_allowed=False,
        description_zh="私人版与 personal vault 的本地 Codex 执行适配器；公开版只复制任务包。",
        description_en="Local Codex adapter for private and personal-vault runtimes; the public starter only copies task packets.",
    ),
    "claude_code": ProviderSpec(
        name="claude_code",
        type="local_claude_code",
        label="Claude Code",
        default_model="auto",
        cli_missing_error="claude_code_cli_missing",
        endpoint_ref="local:claude-code-cli",
        adapter="researchos_adapters.dispatch:LocalClaudeCodeProvider",
        public_starter_allowed=False,
        description_zh="私人版的本地 Claude Code CLI 执行适配器（仅 ros 会话路径，只回答）；Dashboard runner 不启动它，在公开版与 personal vault 模式下只复制任务包。",
        description_en="Local Claude Code CLI adapter for the private runtime (ros session path, answer only); the Dashboard runner never starts it, and in the public starter and personal-vault mode it only copies task packets.",
    ),
}


def get_provider_spec(name: str) -> ProviderSpec:
    try:
        return PROVIDERS[name]
    except KeyError as exc:
        valid = ", ".join(sorted(PROVIDERS))
        raise KeyError(f"Unknown provider '{name}'. Valid providers: {valid}") from exc
