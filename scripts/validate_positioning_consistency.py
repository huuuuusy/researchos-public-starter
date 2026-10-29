#!/usr/bin/env python3
"""Keep active public docs aligned with the narrow ResearchOS product boundary."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_MARKERS = {
    "AGENTS.md": (
        "primary execution workflow is markdown plus a file-aware agent or cli",
        "one Unified Desk with Now and Library semantic areas",
        "**now** owns every today item",
        "work and needs review distinguish bounded sessions",
        "input aliases",
        "not a second chat",
        "does not hold authority",
    ),
    "docs/reference/AGENTS.zh.md": (
        "主要执行工作流是 markdown 加文件感知 agent 或 cli",
        "以统一工作台呈现现在与资料两个语义区域",
        "`现在`完整承载 today",
        "work 与待复核只在精确事项内",
        "不是第二个聊天入口",
        "不拥有判断权",
    ),
    "README.md": ("local-primary system for continuously maintaining research state", "copy fallback", "frozen"),
    "README.zh.md": ("持续维护研究状态、本地为主的系统", "复制回退", "冻结"),
    "docs/user-manual.en.md": (
        "small, file-based tool",
        "primary execution route",
        "one Unified Desk with Now and Library semantic areas",
        "work and review are states of an exact item",
        "never as a third screen",
        "persistent attention and control surface",
        "copyable execution brief only; no local answer or model run",
        "disabled; registered maintenance actions only",
        "always produces a copyable execution brief",
        "not a second chat",
    ),
    "docs/user-manual.zh.md": (
        "小型文件化工具",
        "主要执行路线",
        "以统一工作台呈现现在与资料两个语义区域",
        "work 与 review 是精确事项的局部状态",
        "不形成第三个顶层屏幕",
        "注意力与控制面",
        "只生成可复制任务包",
        "不是第二个聊天入口",
    ),
    "docs/system-reference.en.md": (
        "small, file-based tool",
        "primary execution route",
        "attention and control surface",
        "one Unified Desk with Now and Library semantic areas",
        "only inside an exact item",
        "copy-only handoff",
        "small, file-based reference tool",
        "primary execution surface",
        "persistent attention and control surface",
        "not a second chat",
    ),
    "docs/system-reference.zh.md": (
        "小型文件化工具",
        "主要执行路线",
        "注意力与控制面",
        "以统一工作台呈现现在与资料两个语义区域",
        "只在精确事项内",
        "copy-only 交接",
        "小型文件化参考工具",
        "主要执行面",
        "不是第二个聊天入口",
    ),
    "CHANGELOG.md": (
        "one Unified Desk with Now and Library semantic areas",
        "public mode is credential-free and copy-only",
        "never starts local codex or a remote provider",
    ),
    "09_templates/data_contracts/researchos-extension-contract-v1.md": (
        "produces a copy-ready handoff",
        "never starts a local or remote executor",
    ),
    "09_templates/data_contracts/researchos-extension-contract-v1.zh.md": (
        "只生成可复制交接",
        "不启动本地或远程执行器",
    ),
    "docs/releases/v1.0.0.md": (
        "local-primary system for continuously maintaining research state",
        "agent/cli is the primary execution surface",
        "persistent attention and control surface",
        "a compact unified desk",
        "neither work nor review is a third screen",
        "credential-free, copy-only public runtime",
        "not an agent prerequisite",
    ),
    "docs/releases/v1.0.0.zh.md": (
        "持续维护研究状态、本地为主的系统",
        "agent/cli 是主要执行面",
        "注意力与控制面",
        "统一工作台",
        "work/review 都不是第三个顶层屏幕",
        "copy-only 公开运行态",
        "不是 agent 的前置条件",
    ),
    "dashboard/src/services/work-session-router.js": (
        "结果返回当前助手会话",
        "result in the current assistant conversation",
    ),
    "08_exports/public_starter/onboarding-step-by-step.md": (
        "creates a bounded work session and routes it from now into work",
        "needs review shows the returned result explicitly",
    ),
    "08_exports/public_starter/onboarding-step-by-step.zh.md": (
        "建立一个有边界的 work session，并从`现在`进入`推进`",
        "`待复核`会明确显示返回结果",
    ),
    "docs/reference/CARD_MATURITY_AND_ENHANCEMENT.md": (
        "work** distinguishes multiple bounded sessions",
        "needs review** state shows returned results or candidate changes",
    ),
    "docs/reference/CARD_MATURITY_AND_ENHANCEMENT.zh.md": (
        "**推进**区分多个有界 session",
        "**待复核**状态显示返回结果或候选变化",
    ),
}

STALE_POSITIONING = (
    "dashboard-first",
    "local-first research workbench",
    "先用 dashboard",
    "本地优先研究工作台",
    "dashboard and codex perform the same work",
    "dashboard 和 codex 完成相同任务",
    "dashboard replaces codex",
    "dashboard 替代 codex",
    "neither is subordinate to the other",
    "二者不是谁服务谁",
    "完整、可读的结果返回页面",
    "complete readable result to the page",
    "current task progress",
    "当前任务进展",
    "dashboard is useful but secondary",
    "dashboard 有用但处于次要位置",
    "dashboard is a secondary convenience surface",
    "dashboard 是次要便利层",
    "local dashboard is optional and limited",
    "dashboard 是可选且有限的辅助界面",
    "optional, limited projection",
    "可选且能力有限的投影",
    "normal users should continue to start in workbench",
    "普通用户仍从 workbench 开始",
    "**work** chooses where the selected task is handled",
    "inline read-only local answer",
    "local codex read-only",
    "local codex answers only in a read-only sandbox",
    "visible result through read-only public execution",
    "three stable research views",
    "三个稳定研究视角",
    "the dashboard now has three fixed responsibilities",
    "dashboard 现在固定为三个职责",
    "can use the existing local read-only executor",
    "可以使用既有本地只读执行器",
    "可以在既有只读沙箱中启动本地 codex",
    "opens work, where",
    "moves to work",
    "remains folded in work",
    "转到`处理`页",
    "进入处理页",
    "折叠在处理页",
)

SURFACE_CONTRACTS = {
    "AGENTS.md": {
        "required": ("one Unified Desk with Now and Library semantic areas", "**Now** owns", "**Library** connects", "exact item"),
        "forbidden": ("**Now** restores one bounded research focus", "**Review** separates results"),
    },
    "docs/reference/AGENTS.zh.md": {
        "required": ("以统一工作台呈现现在与资料两个语义区域", "`现在`完整承载", "`资料`以一项或少量明确 Commitment lens", "精确事项内"),
        "forbidden": ("`现在`恢复一份有边界的当前研究状态", "`确认`区分结果"),
    },
    "docs/user-manual.en.md": {
        "required": ("one Unified Desk with Now and Library semantic areas", "that item's drawer", "| Canonical Markdown and Git |"),
        "forbidden": ("Review separates returned results", "Legacy `Start / Next` routes", "Now, Library, and Review", "| Review |"),
    },
    "docs/user-manual.zh.md": {
        "required": ("以统一工作台呈现现在与资料两个语义区域", "该事项的抽屉", "| canonical Markdown 与 Git |"),
        "forbidden": ("`现在 / 资料 / 确认`三个稳定视角", "旧 `Start / Next` 路由", "`确认`区分返回结果", "| 确认 |"),
    },
    "docs/system-reference.en.md": {
        "required": ("Now: allocate", "| `Now` |", "| `Library` |", "| item-local Work |", "| item-local Review |", "Now?item=<id>&panel=<work|review>"),
        "forbidden": ("Judgment: Today", "| `Judgment` |", "| `Assets` |", "| `Review` |"),
    },
    "docs/system-reference.zh.md": {
        "required": ("现在：在多项 Commitment", "| `现在 / Now` |", "| `资料 / Library` |", "| 事项内 Work |", "| 事项内 Review |", "Now?item=<id>&panel=<work|review>"),
        "forbidden": ("判断：Today", "| `判断 / Judgment` |", "| `资产 / Assets` |", "| `确认 / Review` |"),
    },
    "docs/governance-guide.en.md": {
        "required": ("Now, Library, item-local Work and Review, and agent tasks",),
        "forbidden": ("Today, project decisions, the Library",),
    },
    "docs/governance-guide.zh.md": {
        "required": ("`现在 / 资料`、事项内 Work/Review 和 Agent 任务",),
        "forbidden": ("项目判断、资产、今日处理",),
    },
    "scripts/start_researchos.py": {
        "required": ('("dashboard_required", "false")', "optional"),
        "forbidden": (
            "Start / Library / Work attention and control surface",
            "Today / Assets / Preview / Inbox / Codex visual surface",
        ),
    },
}


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = root / relative_path
        if not path.exists():
            failures.append(f"missing active positioning document: {relative_path}")
            continue
        normalized = path.read_text(encoding="utf-8").lower()
        for marker in markers:
            if marker.lower() not in normalized:
                failures.append(f"{relative_path} is missing positioning marker: {marker}")
        for stale in STALE_POSITIONING:
            if stale in normalized:
                failures.append(f"{relative_path} contains stale positioning: {stale}")
    for relative_path, contract in SURFACE_CONTRACTS.items():
        path = root / relative_path
        if not path.exists():
            failures.append(f"missing surface-contract owner: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in contract["required"]:
            if marker not in text:
                failures.append(f"{relative_path} is missing surface-contract marker: {marker}")
        for marker in contract["forbidden"]:
            if marker in text:
                failures.append(f"{relative_path} contains stale surface-contract marker: {marker}")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("Positioning consistency validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"OK: active positioning is aligned ({len(REQUIRED_MARKERS)} documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
