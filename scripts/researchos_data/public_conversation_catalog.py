# ResearchOS maintenance header.
# 中文：公开版内建对话任务与有界读取层级的唯一 owner；Dashboard builder 与直接 Agent 路由共同消费。
# English: Single owner for public built-in conversation tasks and bounded read tiers shared by the Dashboard builder and direct Agent route.

"""Public conversation-first capability catalog."""

from __future__ import annotations

from typing import Any

from researchos_data.conversation_contract import with_conversation_contract


AUTO_LOADED_ENTRY_FILES = {"AGENTS.md"}


def public_read_tiers(
    language: str,
    read_candidates: list[str],
    standard_extra: list[str] | None = None,
    *,
    primary_read: str = "",
    evidence_extra: list[str] | None = None,
) -> list[dict[str, Any]]:
    standard_extra = standard_extra or []
    evidence_extra = evidence_extra or []
    candidates = list(dict.fromkeys(path for path in read_candidates if path))
    quick_read = [primary_read or (candidates[0] if candidates else "docs/user-manual.en.md")]
    expansion_candidates = [path for path in candidates if path not in AUTO_LOADED_ENTRY_FILES]
    standard_read = list(dict.fromkeys([*quick_read, *expansion_candidates, *standard_extra]))[:5]
    full_read = list(dict.fromkeys([*standard_read, *evidence_extra]))[:8]
    labels = (
        {
            "quick": ("最小读取", "只读 1 个任务主文件；有精确目标路径时直接读目标。"),
            "standard": ("平衡读取", "出现明确缺口后再加入 workflow / 模板；首轮最多 5 个文件。"),
            "evidence": ("完整检查", "只为明确核验问题加入证据或检查表；首轮最多 8 个文件。"),
        }
        if language == "zh-CN"
        else {
            "quick": ("Minimal read", "Read one primary task file; use an exact target directly when supplied."),
            "standard": ("Balanced read", "Add workflows or templates only for a named gap; first pass is capped at five files."),
            "evidence": ("Full check", "Add evidence or checklists only for a named verification question; first pass is capped at eight files."),
        }
    )
    return [
        {"id": "quick", "label": labels["quick"][0], "description": labels["quick"][1], "read": quick_read, "file_limit": 1, "token_ceiling": 10_000, "requires_gap_reason": False},
        {"id": "standard", "label": labels["standard"][0], "description": labels["standard"][1], "read": standard_read, "file_limit": 5, "token_ceiling": 35_000, "requires_gap_reason": True},
        {"id": "evidence", "label": labels["evidence"][0], "description": labels["evidence"][1], "read": full_read, "file_limit": 8, "token_ceiling": 60_000, "requires_gap_reason": True},
    ]


def _specs(language: str) -> list[dict[str, Any]]:
    zh = language == "zh-CN"
    suffix = ".zh.md" if zh else ".md"
    guide_suffix = ".zh.md" if zh else ".en.md"
    prompt_template = "09_templates/standard-agent-prompts.zh.md" if zh else "09_templates/standard-agent-prompts.en.md"
    return [
        {
            "id": "first_run_onboarding",
            "name": "第一次上手" if zh else "First-run onboarding",
            "goal": "让新用户理解公开版 ResearchOS 的入口、边界和第一轮操作。" if zh else "Help a new user understand the public ResearchOS entry points, boundaries, and first actions.",
            "user_input_hint": "说明你是想试跑 demo、替换成自己的材料，还是让 Codex 帮你完成第一张卡片。" if zh else "Say whether you want to run the demo, replace it with your own material, or ask Codex to create the first card.",
            "output": "读取顺序 + 第一轮操作 + 需要用户确认的边界" if zh else "Reading order + first action + confirmation boundary",
            "read_first": [f"docs/user-manual{guide_suffix}", f"docs/reference/AGENT_PROTOCOL{suffix}", f"08_exports/public_starter/onboarding-step-by-step{suffix}"],
            "primary_read": f"08_exports/public_starter/onboarding-step-by-step{suffix}",
            "standard_extra": [prompt_template],
        },
        {
            "id": "material_intake",
            "name": "材料接入" if zh else "Material intake",
            "goal": "把一篇论文、笔记、项目想法或人物线索登记成可维护的公开安全卡片。" if zh else "Register a paper, note, project idea, or person clue as a maintainable public-safe card.",
            "user_input_hint": "提供材料类型、路径或摘要，以及你想让它进入哪一类卡片。" if zh else "Provide the material type, path or summary, and the card type you want to create.",
            "output": "M1 登记卡 + 证据边界 + 下一步升级建议" if zh else "M1 card + evidence boundary + next upgrade suggestion",
            "read_first": [f"docs/reference/WHERE_TO_PUT_NEW_MATERIALS{suffix}", "05_workflows/research_management/material-intake-workflow.md", f"08_exports/public_starter/onboarding-intake-note-example{suffix}"],
            "primary_read": "05_workflows/research_management/material-intake-workflow.md",
            "standard_extra": ["09_templates/paper-template.md", "09_templates/project-template.md"],
        },
        {
            "id": "card_upgrade",
            "name": "卡片升级" if zh else "Card upgrade",
            "goal": "把 M1 卡片升级到更有判断、证据和跨项目连接的 M2/M3 状态。" if zh else "Upgrade an M1 card toward M2/M3 with clearer judgment, evidence, and cross-project links.",
            "user_input_hint": "说明要升级的卡片路径，以及你希望补充证据、关系还是行动路线。" if zh else "Provide the card path and say whether you want evidence, relations, or action routing.",
            "output": "升级计划 + 候选修改 + 验证项" if zh else "Upgrade plan + candidate diff + validation items",
            "read_first": [f"08_exports/public_starter/onboarding-card-maturity-rubric{suffix}", f"08_exports/public_starter/onboarding-paper-card-levels{suffix}", f"08_exports/public_starter/onboarding-person-card-levels{suffix}"],
            "primary_read": f"08_exports/public_starter/onboarding-card-maturity-rubric{suffix}",
            "standard_extra": ["05_workflows/research_management/material-analysis-lifecycle-standard.md"],
        },
        {
            "id": "codex_handoff",
            "name": "交给 Codex 执行" if zh else "Codex handoff",
            "goal": "把前端记录的意图整理成 Codex 可以读取、执行和验证的最小交接说明。" if zh else "Turn frontend intent into a minimal brief that Codex can read, execute, and verify.",
            "user_input_hint": "写一句你希望 Codex 做什么；如果涉及写入，请说明目标文件和确认边界。" if zh else "Write one sentence about what Codex should do; include target path and confirmation boundary if writeback is involved.",
            "output": "Codex handoff brief + 最小读取路径 + 安全边界" if zh else "Codex handoff brief + minimal read path + safety boundary",
            "read_first": ["AGENTS.md", f"docs/reference/CONTEXT_BUDGET_PROTOCOL{suffix}", f"08_exports/public_starter/onboarding-step-by-step{suffix}"],
            "primary_read": f"docs/reference/CONTEXT_BUDGET_PROTOCOL{suffix}",
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}"],
        },
        {
            "id": "external_demand_response",
            "name": "外部请求响应" if zh else "External request response",
            "goal": "先用 ResearchOS 找已有资产和边界，再判断外部请求、邀请或合作机会应该如何回应。" if zh else "Use ResearchOS assets and boundaries before deciding how to respond to an external request, invitation, or collaboration opportunity.",
            "user_input_hint": "粘贴请求内容，并说明你希望判断是否回应、如何回应，还是先找相关资产。" if zh else "Paste the request and say whether you want fit judgment, related assets, response stance, or a draft reply.",
            "output": "请求类型 + 相关资产 + 适配判断 + 边界 + 回应 stance" if zh else "Request type + related assets + fit judgment + boundary + response stance",
            "read_first": ["AGENTS.md", f"05_workflows/research_management/external-demand-response-workflow{suffix}"],
            "primary_read": f"05_workflows/research_management/external-demand-response-workflow{suffix}",
            "evidence_extra": [f"docs/reference/SAFE_EXPORT_POLICY{suffix}"],
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}", prompt_template],
        },
        {
            "id": "relationship_opportunity",
            "name": "关系机会路由" if zh else "Relationship opportunity routing",
            "goal": "判断人物、论文、活动、项目或主题信号是否构成可跟进的研究机会。" if zh else "Decide whether a person, paper, event, project, or topic signal creates a research opportunity.",
            "user_input_hint": "给出人物、论文、活动、项目或主题信号；不要默认推断私人关系。" if zh else "Provide the person, paper, event, project, or topic signal; do not assume private relationships.",
            "output": "已确认事实 + 候选连接 + 机会路线 + 不能推断内容 + 下一步" if zh else "Confirmed facts + candidate links + opportunity routes + non-inferences + next action",
            "read_first": ["AGENTS.md", f"05_workflows/research_management/relationship-opportunity-workflow{suffix}"],
            "primary_read": f"05_workflows/research_management/relationship-opportunity-workflow{suffix}",
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}", "09_templates/person-template.md", "09_templates/project-template.md"],
        },
        {
            "id": "maintenance_check",
            "name": "内测前检查" if zh else "Beta readiness check",
            "goal": "检查公开包的链接、配置、demo 数据、dashboard 和安全边界是否一致。" if zh else "Check links, config, demo data, dashboard behavior, and public-safe boundaries before sharing.",
            "user_input_hint": "说明你要做快速检查、浏览器检查，还是发布前完整检查。" if zh else "Say whether this is a quick check, browser check, or release-level check.",
            "output": "检查结果 + blocker + 可延后优化项" if zh else "Check result + blockers + can-wait improvements",
            "read_first": [f"08_exports/public_starter/browser-smoke-checklist{suffix}", f"scripts/README{suffix}", f"docs/reference/PUBLIC_RELEASE_CHECKLIST{suffix}"],
            "primary_read": f"08_exports/public_starter/browser-smoke-checklist{suffix}",
            "evidence_extra": [f"docs/reference/SAFE_EXPORT_POLICY{suffix}"],
            "standard_extra": [f"docs/reference/SAFE_EXPORT_POLICY{suffix}"],
        },
        {
            "id": "material_understanding",
            "name": "材料理解" if zh else "Material understanding",
            "goal": "基于用户指定来源区分事实、推断、未知与下一步。" if zh else "Separate facts, inferences, unknowns, and next steps from user-selected sources.",
            "user_input_hint": "提供精确材料路径、链接或粘贴内容，并说明你要回答的问题。" if zh else "Provide an exact source path, link, or pasted content and the question it should answer.",
            "output": "来源回执 + 核心现象 + 事实/推断/未知 + 下一步" if zh else "Source receipt + core phenomenon + facts/inferences/unknowns + next step",
            "read_first": [f"docs/reference/AGENT_PROTOCOL{suffix}", "05_workflows/research_management/material-analysis-lifecycle-standard.md"],
            "primary_read": f"docs/reference/AGENT_PROTOCOL{suffix}",
            "standard_extra": ["05_workflows/research_management/material-analysis-lifecycle-standard.md"],
        },
        {
            "id": "idea_diagnosis",
            "name": "研究想法诊断" if zh else "Research idea diagnosis",
            "goal": "用最强简单基线、反例、证据缺口和停止条件诊断一个研究想法。" if zh else "Diagnose one research idea with the strongest simple baseline, counterexample, evidence gap, and stop rule.",
            "user_input_hint": "说明研究问题、现有证据、目标结果和主要约束。" if zh else "State the question, current evidence, desired outcome, and main constraints.",
            "output": "问题机制 + 竞争基线 + 可证伪判断 + 最小实验 + 停止条件" if zh else "Problem mechanism + competing baseline + falsifiable judgment + smallest experiment + stop rule",
            "read_first": [prompt_template, f"docs/reference/AGENT_PROTOCOL{suffix}"],
            "primary_read": prompt_template,
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}"],
        },
        {
            "id": "new_project_intake",
            "name": "新项目接入" if zh else "New project intake",
            "goal": "把用户的新方向整理成候选项目，而不推断责任、承诺或长期状态。" if zh else "Structure a new direction as a project candidate without inferring responsibility, commitment, or durable state.",
            "user_input_hint": "说明项目来源、目标、已有材料、你的角色和目前未知。" if zh else "Provide origin, goal, current material, your role, and known unknowns.",
            "output": "候选项目卡 + 责任边界 + 证据缺口 + 首个可验证里程碑" if zh else "Project candidate + responsibility boundary + evidence gaps + first verifiable milestone",
            "read_first": ["09_templates/project-template.md", f"docs/reference/AGENT_PROTOCOL{suffix}"],
            "primary_read": "09_templates/project-template.md",
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}"],
        },
        {
            "id": "safe_export",
            "name": "安全导出检查" if zh else "Safe export check",
            "goal": "在外发前核对来源、敏感度、权限、声明和可撤回边界。" if zh else "Check source, sensitivity, authority, claims, and revocability before external reuse.",
            "user_input_hint": "提供待导出内容、目标受众和目的地；未知敏感度会阻止导出。" if zh else "Provide the content, audience, and destination; unknown sensitivity blocks export.",
            "output": "允许/阻止/需确认 + 风险字段 + 最小安全版本" if zh else "Allow/block/confirm + risk fields + smallest safe version",
            "read_first": [f"docs/reference/SAFE_EXPORT_POLICY{suffix}", f"docs/reference/AGENT_PROTOCOL{suffix}"],
            "primary_read": f"docs/reference/SAFE_EXPORT_POLICY{suffix}",
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}"],
        },
        {
            "id": "collaborative_alignment",
            "name": "协作对齐" if zh else "Collaborative alignment",
            "goal": "在高后果任务中恢复当前共享任务模型，不构建心理画像。" if zh else "Recover a current shared task model for a consequential task without building a psychological profile.",
            "user_input_hint": "说明当前目标、你认为哪里发生偏差，以及不能改变的边界。" if zh else "State the current goal, where the mismatch occurred, and the boundary that must not change.",
            "output": "当前目标 + 已确认边界 + 工作假设 + 一个高价值确认点 + 重开条件" if zh else "Current goal + confirmed boundaries + working assumptions + one high-value confirmation + reopen trigger",
            "read_first": [f"docs/reference/AGENT_PROTOCOL{suffix}"],
            "primary_read": f"docs/reference/AGENT_PROTOCOL{suffix}",
        },
        {
            "id": "research_audit",
            "name": "研究审计" if zh else "Research audit",
            "goal": "对一个明确 claim、转换或仓库边界做只读审计，并给出最小可逆修复候选。" if zh else "Audit one explicit claim, transition, or repository boundary and return the smallest reversible repair candidate.",
            "user_input_hint": "给出精确范围、基线、成功标准和不能修改的内容。" if zh else "Provide the exact scope, baseline, success criteria, and protected content.",
            "output": "证据化 findings + 最强反例 + 严重度 + 最小修复 + 回滚" if zh else "Evidence-backed findings + strongest counterexample + severity + smallest repair + rollback",
            "read_first": [f"docs/system-reference{guide_suffix}", f"docs/reference/AGENT_PROTOCOL{suffix}"],
            "primary_read": f"docs/system-reference{guide_suffix}",
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}"],
        },
        {
            "id": "system_reflection",
            "name": "系统反思" if zh else "System reflection",
            "goal": "把一次有边界的 episode 转成因果教训、可证伪 gate 与唯一候选 owner。" if zh else "Turn one bounded episode into a causal lesson, falsifiable gate, and one candidate owner.",
            "user_input_hint": "提供 episode 目标、实际结果、失败或纠正证据和当前规则 owner。" if zh else "Provide the episode goal, observed outcome, failure or correction evidence, and current rule owner.",
            "output": "原因而非时间线 + 反例 + 候选规则 + 可执行 gate + 吸收 owner" if zh else "Cause not chronology + counterexample + candidate rule + executable gate + absorption owner",
            "read_first": [f"docs/system-reference{guide_suffix}"],
            "primary_read": f"docs/system-reference{guide_suffix}",
        },
        {
            "id": "research_self_model",
            "name": "个人研究模型" if zh else "Personal research self-model",
            "goal": "只基于用户自己的本地材料形成候选研究主线、偏好与未知，不读取任何预置私人档案。" if zh else "Form candidate research themes, preferences, and unknowns only from the user's own selected local material.",
            "user_input_hint": "选择你自己的简历、论文列表或项目笔记；不要把推断当事实。" if zh else "Select your own CV, publication list, or project notes; inferences remain candidates.",
            "output": "来源覆盖 + 候选主线 + 证据 + 不确定项 + Review 候选" if zh else "Source coverage + candidate themes + evidence + unknowns + Review candidate",
            "read_first": [f"docs/reference/AGENT_PROTOCOL{suffix}", f"docs/user-manual{guide_suffix}"],
            "primary_read": f"docs/reference/AGENT_PROTOCOL{suffix}",
            "standard_extra": [f"docs/user-manual{guide_suffix}"],
        },
        {
            "id": "paper_writing",
            "name": "论文写作" if zh else "Paper writing",
            "goal": "基于精确稿件和证据完成有边界的论文写作或修改。" if zh else "Draft or revise a bounded manuscript move from the exact manuscript and evidence.",
            "user_input_hint": "提供稿件、目标段落、证据、引用和作者约束。" if zh else "Provide the manuscript, target passage, evidence, citations, and author constraints.",
            "output": "修改判断 + 候选文本 + claim-evidence/citation 检查 + 作者确认点" if zh else "Revision judgment + candidate text + claim-evidence/citation check + author confirmation",
            "read_first": [prompt_template, f"docs/reference/AGENT_PROTOCOL{suffix}"],
            "primary_read": prompt_template,
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}"],
        },
        {
            "id": "proposal",
            "name": "Proposal 构建" if zh else "Proposal framing",
            "goal": "把用户提供的 call 和研究证据转成可行、可评估的 proposal 候选。" if zh else "Turn a user-supplied call and research evidence into a feasible, evaluable proposal candidate.",
            "user_input_hint": "提供 call、截止时间、已有证据、资源和不能承诺的内容。" if zh else "Provide the call, deadline, evidence, resources, and commitments that cannot be made.",
            "output": "适配判断 + 贡献 + 可行路径 + 评估 + 未知 + 候选叙事" if zh else "Fit judgment + contribution + feasible path + evaluation + unknowns + candidate narrative",
            "read_first": [prompt_template, f"docs/reference/AGENT_PROTOCOL{suffix}"],
            "primary_read": prompt_template,
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}"],
        },
        {
            "id": "presentation",
            "name": "报告构建" if zh else "Presentation planning",
            "goal": "把已确认的研究 claim、受众和时间约束转成报告结构候选。" if zh else "Turn confirmed research claims, audience, and duration into a presentation candidate.",
            "user_input_hint": "提供受众、时长、现有材料、核心 claim 和外发边界。" if zh else "Provide the audience, duration, source material, central claim, and release boundary.",
            "output": "叙事弧 + 逐页角色 + claim-evidence 映射 + 视觉 QA 计划" if zh else "Narrative arc + slide roles + claim-evidence map + visual QA plan",
            "read_first": [prompt_template, f"docs/reference/AGENT_PROTOCOL{suffix}"],
            "primary_read": prompt_template,
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}"],
        },
        {
            "id": "figure_design",
            "name": "科研图表设计" if zh else "Research figure design",
            "goal": "把一个研究机制和证据边界转成语义清晰的图表候选。" if zh else "Translate one research mechanism and evidence boundary into a semantically clear figure candidate.",
            "user_input_hint": "提供核心 claim、变量/角色、关系、证据、受众和输出格式。" if zh else "Provide the claim, variables or roles, relations, evidence, audience, and format.",
            "output": "图表语法 + 元素映射 + caption 候选 + 反误读检查" if zh else "Figure grammar + element mapping + caption candidate + misreading check",
            "read_first": [prompt_template, f"docs/reference/AGENT_PROTOCOL{suffix}"],
            "primary_read": prompt_template,
            "standard_extra": [f"docs/reference/AGENT_PROTOCOL{suffix}"],
        },
    ]


def public_tasks_for_language(language: str) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for spec in _specs(language):
        read_tiers = public_read_tiers(
            language,
            list(dict.fromkeys(spec["read_first"])),
            spec.get("standard_extra", []),
            primary_read=str(spec.get("primary_read", "")),
            evidence_extra=spec.get("evidence_extra", []),
        )
        tasks.append(with_conversation_contract({
            "id": spec["id"],
            "name": spec["name"],
            "budget": "quick/standard",
            "goal": spec["goal"],
            "user_input_hint": spec["user_input_hint"],
            "output": spec["output"],
            "next_steps": [spec["output"]],
            "read_first": list(read_tiers[0]["read"]),
            "read_tiers": read_tiers,
        }, language))
    return tasks
