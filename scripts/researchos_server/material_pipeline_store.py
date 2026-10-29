# ResearchOS maintenance header.
# 中文：material_pipeline 的已审查后端 adapter；持久化、规范化并渲染三类候选收件箱，保持 server shell 不理解领域字段。
# English: Reviewed backend adapter for material_pipeline; persists, normalizes, and renders its three candidate inboxes so the server shell does not interpret domain fields.

"""Material-pipeline persistence adapters for intake, upgrade, and scouting candidates."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from researchos_kernel.atomic_files import atomic_write_json, atomic_write_text, lock_path_for, runtime_state_transaction


SafePath = Callable[[object], str]


@dataclass(frozen=True)
class MaterialPipelineStore:
    root: Path
    material_intake_json: Path
    material_intake_md: Path
    upgrade_json: Path
    upgrade_md: Path
    scout_json: Path
    scout_md: Path
    safe_md_path: SafePath

    allowed_material_types = {"paper", "talk", "person", "project", "group", "other"}
    allowed_privacy = {"local_only", "internal", "public_candidate"}
    allowed_upgrade_states = {"M2_refined_read", "M3_cross_project_deepening"}
    route_specs = {
        "/material-intake-inbox": {"candidate_type": "material_intake", "limit": 160000, "label": "material intake inbox"},
        "/upgrade-inbox": {"candidate_type": "upgrade", "limit": 80000, "label": "upgrade inbox"},
        "/scout-inbox": {"candidate_type": "scout", "limit": 120000, "label": "scout inbox"},
    }

    @classmethod
    def from_root(cls, root: Path, safe_md_path: SafePath) -> "MaterialPipelineStore":
        active_context = root / "06_active_context"
        return cls(
            root=root,
            material_intake_json=active_context / "ui-material-intake-inbox.json",
            material_intake_md=active_context / "ui-material-intake-inbox.md",
            upgrade_json=active_context / "ui-material-upgrade-inbox.json",
            upgrade_md=active_context / "ui-material-upgrade-inbox.md",
            scout_json=active_context / "ui-research-scout-inbox.json",
            scout_md=active_context / "ui-research-scout-inbox.md",
            safe_md_path=safe_md_path,
        )

    def save_candidate(self, candidate_type: str, items: object) -> dict[str, object]:
        handlers = {
            "material_intake": self.save_material_intake,
            "upgrade": self.save_upgrade,
            "scout": self.save_scout,
        }
        handler = handlers.get(candidate_type)
        if handler is None:
            raise ValueError("Unsupported material candidate type")
        return handler(items)

    def cleanup_specs(self, spec_factory: Callable[..., object]) -> tuple[object, ...]:
        return (
            spec_factory("material_intake", self.material_intake_json, self.material_intake_md, "UI Material Intake Inbox", "本文件暂存 dashboard 新材料登记请求。", "暂无 pending material intake task。"),
            spec_factory("upgrade", self.upgrade_json, self.upgrade_md, "UI Material Upgrade Inbox", "本文件暂存 dashboard 材料升级请求。", "暂无 pending upgrade task。"),
            spec_factory("scout", self.scout_json, self.scout_md, "UI Research Scout Inbox", "本文件暂存 dashboard 调研任务。", "暂无 pending scout task。"),
        )

    def save_material_intake(self, items: object) -> dict[str, object]:
        if not isinstance(items, list):
            raise ValueError("Invalid items")
        safe_items = [record for record in (self.normalize_material_intake(item) for item in items[:80]) if record]
        with runtime_state_transaction(lock_path=lock_path_for(self.material_intake_json)):
            atomic_write_json(self.material_intake_json, safe_items)
            atomic_write_text(self.material_intake_md, self.render_material_intake_markdown(safe_items))
        return {"ok": True, "count": len(safe_items), "path": str(self.material_intake_md.relative_to(self.root))}

    def save_upgrade(self, items: object) -> dict[str, object]:
        if not isinstance(items, list):
            raise ValueError("Invalid items")
        safe_items = [record for record in (self.normalize_upgrade(item) for item in items[:80]) if record]
        with runtime_state_transaction(lock_path=lock_path_for(self.material_intake_json)):
            atomic_write_json(self.upgrade_json, safe_items)
            atomic_write_text(self.upgrade_md, self.render_upgrade_markdown(safe_items))
        return {"ok": True, "count": len(safe_items), "path": str(self.upgrade_md.relative_to(self.root))}

    def save_scout(self, items: object) -> dict[str, object]:
        if not isinstance(items, list):
            raise ValueError("Invalid items")
        safe_items = [record for record in (self.normalize_scout(item) for item in items[:80]) if record]
        with runtime_state_transaction(lock_path=lock_path_for(self.material_intake_json)):
            atomic_write_json(self.scout_json, safe_items)
            atomic_write_text(self.scout_md, self.render_scout_markdown(safe_items))
        return {"ok": True, "count": len(safe_items), "path": str(self.scout_md.relative_to(self.root))}

    def normalize_material_intake(self, item: object) -> dict[str, object] | None:
        if not isinstance(item, dict):
            return None
        material_type = str(item.get("material_type", "other")).strip()
        if material_type not in self.allowed_material_types:
            material_type = "other"
        privacy = str(item.get("privacy", "local_only")).strip()
        if privacy not in self.allowed_privacy:
            privacy = "local_only"
        return {
            "id": str(item.get("id", "")).strip()[:160],
            "material_id": str(item.get("material_id", item.get("id", ""))).strip()[:160],
            "status": str(item.get("status", "pending_codex_review")).strip()[:80] or "pending_codex_review",
            "material_type": material_type,
            "type_label": str(item.get("type_label", "")).strip()[:80],
            "title": str(item.get("title", "")).strip()[:300],
            "source_mode": str(item.get("source_mode", "lead_registration")).strip()[:120],
            "source_path": str(item.get("source_path", "")).strip()[:1200],
            "uploaded_copy_path": str(item.get("uploaded_copy_path", "")).strip()[:1200],
            "target_hint": str(item.get("target_hint", "")).strip()[:300],
            "related_project": str(item.get("related_project", "")).strip()[:300],
            "mainline_hint": str(item.get("mainline_hint", "")).strip()[:300],
            "source_level": str(item.get("source_level", "")).strip()[:80],
            "privacy": privacy,
            "sensitivity": str(item.get("sensitivity", privacy)).strip()[:80],
            "links": self.normalize_string_list(item.get("links", []), limit=20, width=1200),
            "attachments": self.normalize_attachments(item.get("attachments", [])),
            "note": str(item.get("note", "")).strip()[:3000],
            "why_it_matters": str(item.get("why_it_matters", item.get("note", ""))).strip()[:3000],
            "first_read_question": str(item.get("first_read_question", "")).strip()[:1200],
            "evidence_boundary": str(item.get("evidence_boundary", "candidate_lead_only")).strip()[:120],
            "candidate_next_action": str(item.get("candidate_next_action", "M1_registered_candidate")).strip()[:200],
            "save_target": str(item.get("save_target", item.get("target_hint", ""))).strip()[:300],
            "confirmation_required": str(item.get("confirmation_required", "confirm_before_canonical_write")).strip()[:160],
            "createdAt": str(item.get("createdAt", "")).strip()[:80],
            "updatedAt": str(item.get("updatedAt", "")).strip()[:80],
            "source": "dashboard-material-intake",
        }

    def normalize_upgrade(self, item: object) -> dict[str, object] | None:
        if not isinstance(item, dict):
            return None
        path = self.safe_md_path(item.get("path", ""))
        raw_path = str(item.get("path", "")).strip()
        if raw_path and not path:
            return None
        target_state = str(item.get("target_state", "")).strip()
        if target_state not in self.allowed_upgrade_states:
            target_state = "M2_refined_read"
        return {
            "id": str(item.get("id", "")).strip()[:160],
            "status": str(item.get("status", "pending_codex_review")).strip()[:80] or "pending_codex_review",
            "title": str(item.get("title", "")).strip()[:300],
            "path": path,
            "current_state": str(item.get("current_state", "")).strip()[:80],
            "target_state": target_state,
            "source_type": str(item.get("source_type", "")).strip()[:80],
            "source_title": str(item.get("source_title", "")).strip()[:300],
            "source_path": str(item.get("source_path", "")).strip()[:300],
            "source_key": str(item.get("source_key", "")).strip()[:220],
            "note": str(item.get("note", "")).strip()[:2000],
            "reason": str(item.get("reason", "")).strip()[:1000],
            "next_step": str(item.get("next_step", "")).strip()[:1000],
            "createdAt": str(item.get("createdAt", "")).strip()[:80],
            "updatedAt": str(item.get("updatedAt", "")).strip()[:80],
            "source": "dashboard",
        }

    def normalize_scout(self, item: object) -> dict[str, object] | None:
        if not isinstance(item, dict):
            return None
        return {
            "id": str(item.get("id", "")).strip()[:180],
            "status": str(item.get("status", "pending_codex_review")).strip()[:80] or "pending_codex_review",
            "title": str(item.get("title", "")).strip()[:300],
            "topic": str(item.get("topic", "")).strip()[:1200],
            "intent": str(item.get("intent", "")).strip()[:80],
            "months": str(item.get("months", "")).strip()[:20],
            "mainline": str(item.get("mainline", "")).strip()[:300],
            "relevance": str(item.get("relevance", "")).strip()[:80],
            "sources": item.get("sources", []) if isinstance(item.get("sources", []), list) else [],
            "ccf_ranks": item.get("ccf_ranks", []) if isinstance(item.get("ccf_ranks", []), list) else [],
            "queries": item.get("queries", []) if isinstance(item.get("queries", []), list) else [],
            "search_links": item.get("search_links", []) if isinstance(item.get("search_links", []), list) else [],
            "plan_steps": item.get("plan_steps", []) if isinstance(item.get("plan_steps", []), list) else [],
            "local_context": item.get("local_context", []) if isinstance(item.get("local_context", []), list) else [],
            "prompt": str(item.get("prompt", "")).strip()[:20000],
            "createdAt": str(item.get("createdAt", "")).strip()[:80],
            "updatedAt": str(item.get("updatedAt", "")).strip()[:80],
            "source": "dashboard-scout",
        }

    @staticmethod
    def normalize_string_list(value: object, limit: int, width: int) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip()[:width] for item in value[:limit] if str(item).strip()]

    @staticmethod
    def normalize_attachments(value: object) -> list[dict[str, object]]:
        if not isinstance(value, list):
            return []
        safe_attachments: list[dict[str, object]] = []
        for file_item in value[:20]:
            if not isinstance(file_item, dict):
                continue
            safe_attachments.append(
                {
                    "name": str(file_item.get("name", "")).strip()[:260],
                    "type": str(file_item.get("type", "")).strip()[:120],
                    "size": int(file_item.get("size", 0) or 0),
                    "lastModified": str(file_item.get("lastModified", "")).strip()[:80],
                }
            )
        return safe_attachments

    @staticmethod
    def pending_items(items: list[dict[str, object]]) -> list[dict[str, object]]:
        return [item for item in items if str(item.get("status", "")) != "withdrawn"]

    @staticmethod
    def render_material_intake_markdown(items: list[dict[str, object]]) -> str:
        today = datetime.now().date().isoformat()
        lines = [
            "---",
            "type: active_context",
            'title: "UI Material Intake Inbox"',
            "status: active",
            f"created: {today}",
            f"updated: {today}",
            "tags:",
            "  - dashboard",
            "  - material-intake",
            "  - pending-review",
            "sensitivity: internal",
            "---",
            "",
            "# UI Material Intake Inbox",
            "",
            "## Agent Summary",
            "",
            "本文件由本地 dashboard 的“材料线索登记”入口生成，用于暂存研究者对论文、talk、人物、项目、group 或其他材料的登记请求。它不是稳定长期记忆，也不表示浏览器已经上传或复制原始文件；Codex 处理时必须先确认来源、证据边界、公开边界和目标目录，再提出 M1 candidate 或创建/更新对应 md。",
            "",
            "## Handling Protocol",
            "",
            "1. 默认先完成 M1 candidate：身份、来源、重要性、相关项目/人物/主线、证据边界、公开边界、下一步深读建议。",
            "2. `attachments` 只记录浏览器可见的文件名、类型和大小，不等于可读取路径；如果缺少真实路径，需要向研究者确认。",
            "3. `links` 可以包含 URL、本地路径线索、下载文件名或外部文档链接；读取前先判断 sensitive/local-only 边界。",
            "4. 论文/talk/人物/project/group 应使用对应目录和模板；不确定写入位置时先提出候选路径，不直接写 canonical。",
            "5. 每条记录的 `save_target` 和 `confirmation_required` 是写回前的检查点。",
            "6. 写入后重建 dashboard 数据，并运行 validate/link check。",
            "",
            "## Pending Material Intake Tasks",
            "",
        ]
        pending = MaterialPipelineStore.pending_items(items)
        if not pending:
            lines.extend(["暂无 pending material intake task。", ""])
        for item in pending:
            lines.extend(
                [
                    "### Material Intake Task",
                    "",
                    f"- id: `{item.get('id', '')}`",
                    f"- material_id: `{item.get('material_id', '')}`",
                    f"- status: {item.get('status', 'pending_codex_review')}",
                    f"- material_type: {item.get('material_type', '')}",
                    f"- title: {item.get('title', '') or '未指定'}",
                    f"- source_mode: {item.get('source_mode', 'lead_registration')}",
                    f"- source_path: `{item.get('source_path', '')}`",
                    f"- uploaded_copy_path: `{item.get('uploaded_copy_path', '')}`",
                    f"- target_hint: `{item.get('target_hint', '')}`",
                    f"- save_target: `{item.get('save_target', '')}`",
                    f"- related_project: {item.get('related_project', '') or '未指定'}",
                    f"- mainline_hint: {item.get('mainline_hint', '') or '未指定'}",
                    f"- source_level: {item.get('source_level', '') or '未指定'}",
                    f"- privacy: {item.get('privacy', 'local_only')}",
                    f"- sensitivity: {item.get('sensitivity', item.get('privacy', 'local_only'))}",
                    f"- evidence_boundary: {item.get('evidence_boundary', 'candidate_lead_only')}",
                    f"- candidate_next_action: {item.get('candidate_next_action', 'M1_registered_candidate')}",
                    f"- confirmation_required: {item.get('confirmation_required', 'confirm_before_canonical_write')}",
                    f"- updatedAt: `{item.get('updatedAt', '')}`",
                    "",
                    "#### Links / Local Path Clues",
                    "",
                ]
            )
            links = item.get("links", [])
            lines.extend([f"- {link}" for link in links] if links else ["- 未填写"])
            lines.extend(["", "#### Attachments", ""])
            attachments = item.get("attachments", [])
            if attachments:
                for file_item in attachments:
                    if not isinstance(file_item, dict):
                        continue
                    lines.append(f"- {file_item.get('name', '')} ({file_item.get('type', '') or 'unknown'}, {file_item.get('size', 0)} bytes)")
            else:
                lines.append("- 未选择附件")
            lines.extend(
                [
                    "",
                    "#### Why It Matters / First Read",
                    "",
                    f"- why_it_matters: {item.get('why_it_matters', '') or '未填写'}",
                    f"- first_read_question: {item.get('first_read_question', '') or '未填写'}",
                    "",
                    "#### User Note",
                    "",
                    str(item.get("note", "")) or "未填写。",
                    "",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def render_upgrade_markdown(items: list[dict[str, object]]) -> str:
        lines = [
            "---",
            "type: active_context",
            'title: "UI Material Upgrade Inbox"',
            "status: active",
            "created: 2026-06-18",
            "updated: 2026-06-18",
            "tags:",
            "  - dashboard",
            "  - material-upgrade",
            "  - pending-review",
            "sensitivity: internal",
            "---",
            "",
            "# UI Material Upgrade Inbox",
            "",
            "## Agent Summary",
            "",
            "本文件由本地 dashboard 的材料升级收件箱生成，用于暂存研究者从人物卡片、路线卡片或材料卡片中选择的 M2/M3 升级任务。它不是稳定长期记忆；Codex 处理前必须读取对应 source/path，核对公开边界，并在写入前给出中文计划。",
            "",
        ]
        pending = MaterialPipelineStore.pending_items(items)
        if not pending:
            lines.extend(["## Pending Upgrade Tasks", "", "暂无 pending upgrade task。", ""])
        for item in pending:
            lines.extend(
                [
                    "## Pending Upgrade Task",
                    "",
                    f"- id: `{item.get('id', '')}`",
                    f"- status: {item.get('status', 'pending_codex_review')}",
                    f"- title: {item.get('title', '') or '未指定'}",
                    f"- path: `{item.get('path', '')}`",
                    f"- current_state: {item.get('current_state', '') or '未标注'}",
                    f"- target_state: {item.get('target_state', '')}",
                    f"- source_type: {item.get('source_type', '')}",
                    f"- source_title: {item.get('source_title', '')}",
                    f"- source_path: `{item.get('source_path', '')}`",
                    f"- updatedAt: `{item.get('updatedAt', '')}`",
                    "",
                    f"理由：{item.get('reason', '') or '未填写'}",
                    "",
                    f"下一步：{item.get('next_step', '') or '未填写'}",
                    "",
                    f"用户说明：{item.get('note', '') or '无'}",
                    "",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def render_scout_markdown(items: list[dict[str, object]]) -> str:
        today = datetime.now().date().isoformat()
        lines = [
            "---",
            "type: active_context",
            'title: "UI Research Scout Inbox"',
            "status: active",
            f"created: {today}",
            f"updated: {today}",
            "tags:",
            "  - dashboard",
            "  - research-scout",
            "  - pending-review",
            "sensitivity: internal",
            "---",
            "",
            "# UI Research Scout Inbox",
            "",
            "## Agent Summary",
            "",
            "本文件由本地 dashboard 的调研收件箱生成，用于暂存研究者在 UI 中生成的调研/深读指令。它不是稳定长期记忆；Codex 处理前必须先读任务上下文、检索式和本地研究主线，外部材料只作为候选线索，不能直接写入 ResearchOS。",
            "",
        ]
        pending = MaterialPipelineStore.pending_items(items)
        if not pending:
            lines.extend(["## Pending Scout Tasks", "", "暂无 pending scout task。", ""])
        for item in pending:
            lines.extend(
                [
                    "## Pending Scout Task",
                    "",
                    f"- id: `{item.get('id', '')}`",
                    f"- status: {item.get('status', 'pending_codex_review')}",
                    f"- title: {item.get('title', '') or '未指定'}",
                    f"- topic: {item.get('topic', '') or '未填写'}",
                    f"- intent: {item.get('intent', '')}",
                    f"- months: {item.get('months', '')}",
                    f"- mainline: {item.get('mainline', '')}",
                    f"- relevance: {item.get('relevance', '')}",
                    f"- sources: {', '.join(str(x) for x in item.get('sources', []))}",
                    f"- ccf_ranks: {', '.join(str(x) for x in item.get('ccf_ranks', []))}",
                    f"- updatedAt: `{item.get('updatedAt', '')}`",
                    "",
                    "### Plan Steps",
                    "",
                ]
            )
            steps = item.get("plan_steps", [])
            if isinstance(steps, list) and steps:
                for step in steps:
                    if isinstance(step, dict):
                        lines.append(f"- **{step.get('title', '')}**: {step.get('body', '')}")
            else:
                lines.append("- 暂无 plan_steps。")
            lines.extend(["", "### Queries", ""])
            queries = item.get("queries", [])
            if isinstance(queries, list) and queries:
                for query in queries:
                    if isinstance(query, dict):
                        lines.append(f"- `{query.get('query', '')}` ({query.get('mainline', '')})")
            else:
                lines.append("- 暂无 queries。")
            lines.extend(["", "### Research Prompt", "", "```text", str(item.get("prompt", "")).strip(), "```", ""])
        lines.extend(
            [
                "## Codex Processing Rule",
                "",
                "- 先筛选，再写入；外部材料必须标注候选/已核验状态。",
                "- 如果需要联网，先用 prompt 中的检索式和本地研究主线做目标化检索。",
                "- 写入长期记忆前，明确事实、判断、行动建议和需要研究者确认的问题。",
                "",
            ]
        )
        return "\n".join(lines)
