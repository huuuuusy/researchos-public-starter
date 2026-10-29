# ResearchOS maintenance header.
# 中文：受控自更新的变化检测、候选计划、确认令牌和本地 checkpoint owner。
# English: Change detection, candidate planning, confirmation tokens, and local checkpoints for controlled updates.

"""Controlled, path-only evolution planning for local ResearchOS maintenance."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from researchos_data.maintenance_pipeline import FULL_REVIEW_MARKDOWN_RATIO, RESEARCHOS_MAINTENANCE_STEPS, maintenance_plan, maintenance_risk_tier, max_risk_tier, normalize_changed_paths

from researchos_kernel.atomic_files import atomic_write_json, lock_path_for, runtime_state_transaction
from researchos_kernel.ledger import digest as stable_hash


CHECKPOINT_RELATIVE_PATH = Path("06_active_context/work_state/evolution/evolution-checkpoint.json")


@dataclass
class EvolutionPlanner:
    root: Path
    runtime_mode: str = "private"
    checkpoint_path: Path | None = None

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        if self.checkpoint_path is None:
            self.checkpoint_path = self.root / CHECKPOINT_RELATIVE_PATH
        else:
            self.checkpoint_path = self.checkpoint_path.resolve()
        try:
            self.checkpoint_path.relative_to(self.root)
        except ValueError as error:
            raise ValueError("evolution checkpoint must stay inside the repository root") from error

    def git(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        try:
            return subprocess.run(
                ["git", *args],
                cwd=self.root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            # No git executable (for example a Download-ZIP checkout): behave like an empty result so that
            # detect() reports git_available=False instead of crashing the dashboard at import time.
            return subprocess.CompletedProcess(["git", *args], 127, b"", None)

    def head_sha(self) -> str:
        result = self.git("rev-parse", "HEAD")
        return result.stdout.decode("utf-8", errors="replace").strip() if result.returncode == 0 else ""

    def path_list(self, *git_args: str) -> tuple[str, ...]:
        result = self.git(*git_args)
        if result.returncode != 0:
            return ()
        return normalize_changed_paths(tuple(part.decode("utf-8", errors="replace") for part in result.stdout.split(b"\0") if part))

    def worktree_paths(self) -> tuple[str, ...]:
        changed = self.path_list("diff", "--name-only", "-z", "HEAD")
        untracked = self.path_list("ls-files", "--others", "--exclude-standard", "-z")
        return normalize_changed_paths((*changed, *untracked))

    def tracked_markdown_count(self) -> int:
        return len(self.path_list("ls-files", "-z", "--", "*.md"))

    def committed_paths(self, previous_head: str, current_head: str) -> tuple[str, ...]:
        if not current_head:
            return ()
        if previous_head and previous_head != current_head:
            result = self.path_list("diff", "--name-only", "-z", f"{previous_head}..{current_head}")
            if result:
                return result
        if not previous_head:
            return self.path_list("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", current_head)
        return ()

    def load_checkpoint(self) -> dict[str, Any]:
        path = Path(self.checkpoint_path or self.root / CHECKPOINT_RELATIVE_PATH)
        if not path.exists():
            return {}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def change_token(self, head_sha: str, worktree_paths: tuple[str, ...]) -> str:
        fingerprints: list[dict[str, object]] = []
        for relative in worktree_paths:
            path = self.root / relative
            try:
                stat = path.lstat()
                fingerprints.append(
                    {
                        "path": relative,
                        "size": stat.st_size,
                        "mtime_ns": stat.st_mtime_ns,
                        "ctime_ns": stat.st_ctime_ns,
                        "mode": stat.st_mode,
                    }
                )
            except OSError:
                fingerprints.append({"path": relative, "missing": True})
        return stable_hash({"head": head_sha, "worktree": fingerprints})

    def detect(self) -> dict[str, Any]:
        checkpoint = self.load_checkpoint()
        head = self.head_sha()
        worktree = self.worktree_paths() if head else ()
        token = self.change_token(head, worktree)
        if checkpoint.get("change_token") == token:
            changed_paths: tuple[str, ...] = ()
        else:
            committed = self.committed_paths(str(checkpoint.get("head_sha") or ""), head)
            changed_paths = normalize_changed_paths((*committed, *worktree))
        return {
            "detector": "git_delta" if head else "explicit_only",
            "git_available": bool(head),
            "head_sha": head,
            "change_token": token,
            "changed_paths": changed_paths,
            "checkpoint": checkpoint,
        }

    def plan(self, explicit_paths: list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
        detection = self.detect()
        checkpoint = detection["checkpoint"]
        pending_plan = checkpoint.get("pending_plan") if isinstance(checkpoint.get("pending_plan"), dict) else None
        if pending_plan:
            pending_plan = self.refresh_pending_manual(pending_plan)
        if explicit_paths is None and not detection["changed_paths"] and checkpoint.get("change_token") == detection["change_token"] and pending_plan:
            pending_source_plan_id = pending_plan.get("plan_id")
            pending_origin_paths = list(pending_plan.get("pending_origin_paths") or pending_plan.get("changed_paths", []))
            pending_plan_id = f"evo-{stable_hash({'change_token': detection['change_token'], 'steps': pending_plan.get('steps', []), 'pending_source_plan_id': pending_source_plan_id, 'pending_origin_paths': pending_origin_paths, 'runtime_mode': self.runtime_mode})[:16]}"
            return {
                **pending_plan,
                "plan_id": pending_plan_id,
                "status": "deferred" if checkpoint.get("state") == "deferred" else "candidate",
                "detector": "checkpoint_pending",
                "git_available": detection["git_available"],
                "head_sha": detection["head_sha"],
                "change_token": detection["change_token"],
                "checkpoint_path": str(Path(self.checkpoint_path or CHECKPOINT_RELATIVE_PATH).relative_to(self.root)),
                "authority": "candidate_only",
                "confirmation": "deferred manual candidate remains retained without repeated prompting" if checkpoint.get("state") == "deferred" else "manual candidate remains after the safe subset checkpoint",
                "pending_source_plan_id": pending_source_plan_id,
                "pending_origin_paths": pending_origin_paths,
                "deferred_at": checkpoint.get("decided_at") if checkpoint.get("state") == "deferred" else None,
            }
        paths = normalize_changed_paths(explicit_paths) if explicit_paths is not None else detection["changed_paths"]
        tracked_markdown = self.tracked_markdown_count() if detection["git_available"] else 0
        changed_markdown = sum(1 for path in paths if path.lower().endswith(".md"))
        changed_markdown_ratio = changed_markdown / tracked_markdown if tracked_markdown else 0.0
        ratio_full_review = bool(tracked_markdown and changed_markdown_ratio >= FULL_REVIEW_MARKDOWN_RATIO)
        plan = maintenance_plan(
            paths,
            runtime_mode=self.runtime_mode,
            force_full_review=ratio_full_review,
            full_review_reason="tracked_markdown_ratio" if ratio_full_review else "",
        )
        if explicit_paths is None and pending_plan:
            plan = self.merge_pending_manual(plan, pending_plan)
        plan_id = f"evo-{stable_hash({'change_token': detection['change_token'], 'paths': paths, 'steps': plan['selected_step_ids'], 'pending_source_plan_id': plan.get('pending_source_plan_id'), 'pending_origin_paths': plan.get('pending_origin_paths', []), 'runtime_mode': self.runtime_mode})[:16]}"
        return {
            **plan,
            "plan_id": plan_id,
            "detector": "explicit" if explicit_paths is not None else detection["detector"],
            "git_available": detection["git_available"],
            "head_sha": detection["head_sha"],
            "change_token": detection["change_token"],
            "tracked_markdown_count": tracked_markdown,
            "changed_markdown_ratio": round(changed_markdown_ratio, 4),
            "checkpoint_path": str(Path(self.checkpoint_path or CHECKPOINT_RELATIVE_PATH).relative_to(self.root)),
            "authority": "candidate_only",
            "confirmation": "required before any planned write",
        }

    @staticmethod
    def refresh_pending_manual(pending_plan: dict[str, Any]) -> dict[str, Any]:
        """Rehydrate stored manual candidates from the current fixed-step manifest."""
        requested_ids = [str(step_id) for step_id in pending_plan.get("manual_step_ids", []) if str(step_id)]
        canonical = {str(step["id"]): step for step in RESEARCHOS_MAINTENANCE_STEPS}
        order = {str(step["id"]): index for index, step in enumerate(RESEARCHOS_MAINTENANCE_STEPS)}
        known_ids = sorted(
            {
                step_id
                for step_id in requested_ids
                if step_id in canonical and canonical[step_id].get("execution_policy") in {"manual_heavy", "network_manual"}
            },
            key=lambda step_id: order[step_id],
        )
        unavailable_ids = sorted(set(requested_ids) - set(known_ids))
        known_steps = [canonical[step_id] for step_id in known_ids]
        step_views = [
            {
                "id": step["id"],
                "label": step["label"],
                "phase": step["phase"],
                "execution_policy": step["execution_policy"],
                "depends_on": list(step.get("depends_on", ())),
                "cost": step["cost"],
                "writes": list(step.get("writes", ())),
                "validates": list(step.get("validates", ())),
            }
            for step in known_steps
        ]
        step_views.extend(
            {
                "id": step_id,
                "label": step_id,
                "phase": "unavailable",
                "execution_policy": "unavailable",
                "cost": "unknown",
                "writes": [],
                "validates": [],
            }
            for step_id in unavailable_ids
        )
        manual_ids = [*known_ids, *unavailable_ids]
        manual_writes = sorted({str(path) for step in known_steps for path in step.get("writes", ())})
        validates = sorted({str(item) for step in known_steps for item in step.get("validates", ())})
        return {
            **pending_plan,
            "status": "candidate",
            "risk_tier": "E4" if unavailable_ids else maintenance_risk_tier(known_steps),
            "requires_confirmation": True,
            "selected_step_ids": manual_ids,
            "auto_eligible_step_ids": [],
            "manual_step_ids": manual_ids,
            "writes": manual_writes,
            "auto_writes": [],
            "manual_writes": manual_writes,
            "validates": validates,
            "steps": step_views,
            "unavailable_manual_step_ids": unavailable_ids,
        }

    @staticmethod
    def merge_pending_manual(plan: dict[str, Any], pending_plan: dict[str, Any]) -> dict[str, Any]:
        """Carry unresolved manual candidates into a newer unrelated change plan."""
        pending_plan = EvolutionPlanner.refresh_pending_manual(pending_plan)
        pending_ids = [str(step_id) for step_id in pending_plan.get("manual_step_ids", []) if str(step_id)]
        if not pending_ids:
            return plan
        order = {str(step["id"]): index for index, step in enumerate(RESEARCHOS_MAINTENANCE_STEPS)}
        step_records = {
            str(step.get("id")): step
            for step in [*plan.get("steps", []), *pending_plan.get("steps", [])]
            if str(step.get("id") or "")
        }
        auto_ids = [str(step_id) for step_id in plan.get("auto_eligible_step_ids", [])]
        manual_ids = sorted(
            set(str(step_id) for step_id in plan.get("manual_step_ids", [])) | set(pending_ids),
            key=lambda step_id: order.get(step_id, len(order)),
        )
        selected_ids = sorted(set(auto_ids) | set(manual_ids), key=lambda step_id: order.get(step_id, len(order)))
        auto_writes = sorted({str(path) for path in plan.get("auto_writes", [])})
        manual_writes = sorted({str(path) for path in [*plan.get("manual_writes", []), *pending_plan.get("manual_writes", [])]})
        return {
            **plan,
            "status": "candidate",
            "full_review": bool(plan.get("full_review") or pending_plan.get("full_review")),
            "full_review_reason": plan.get("full_review_reason") or pending_plan.get("full_review_reason") or "pending_manual_candidate",
            "risk_tier": max_risk_tier(plan.get("risk_tier"), pending_plan.get("risk_tier")),
            "requires_confirmation": True,
            "selected_step_ids": selected_ids,
            "auto_eligible_step_ids": auto_ids,
            "manual_step_ids": manual_ids,
            "writes": sorted(set(auto_writes) | set(manual_writes)),
            "auto_writes": auto_writes,
            "manual_writes": manual_writes,
            "validates": sorted({str(item) for item in [*plan.get("validates", []), *pending_plan.get("validates", [])]}),
            "steps": [step_records[step_id] for step_id in selected_ids if step_id in step_records],
            "carried_manual_step_ids": pending_ids,
            "pending_source_plan_id": pending_plan.get("plan_id"),
            "pending_origin_paths": list(pending_plan.get("changed_paths", [])),
        }

    @staticmethod
    def confirmed(plan: dict[str, Any], plan_id: str) -> bool:
        return bool(plan_id) and plan_id == plan.get("plan_id")

    def mark_applied(self, plan: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        if not result.get("ok"):
            raise ValueError("cannot checkpoint a failed evolution plan")
        post_detection = self.detect()
        pending_ids = list(plan.get("manual_step_ids", []))
        pending_steps = [step for step in plan.get("steps", []) if step.get("id") in pending_ids]
        pending_validates = sorted({str(item) for step in pending_steps for item in step.get("validates", [])})
        pending_plan = None
        if pending_ids:
            pending_plan = {
                "schema_id": plan.get("schema_id", "researchos-evolution-plan-v1"),
                "plan_id": plan.get("plan_id"),
                "status": "candidate",
                "runtime_mode": self.runtime_mode,
                "changed_path_count": plan.get("changed_path_count", 0),
                "changed_paths": list(plan.get("changed_paths", [])),
                "changed_paths_truncated": bool(plan.get("changed_paths_truncated")),
                "full_review": bool(plan.get("full_review")),
                "full_review_reason": plan.get("full_review_reason", ""),
                "risk_tier": plan.get("risk_tier", "E1"),
                "requires_confirmation": True,
                "selected_step_ids": pending_ids,
                "auto_eligible_step_ids": [],
                "manual_step_ids": pending_ids,
                "writes": list(plan.get("manual_writes", [])),
                "auto_writes": [],
                "manual_writes": list(plan.get("manual_writes", [])),
                "validates": pending_validates,
                "steps": pending_steps,
                "tracked_markdown_count": plan.get("tracked_markdown_count", 0),
                "changed_markdown_ratio": plan.get("changed_markdown_ratio", 0),
                "checkpointed_step_ids": list(result.get("executed_step_ids", [])),
                "pending_origin_paths": list(plan.get("pending_origin_paths") or plan.get("changed_paths", [])),
            }
        checkpoint = {
            "schema_id": "researchos-evolution-checkpoint-v1",
            "plan_id": plan.get("plan_id"),
            "head_sha": post_detection.get("head_sha"),
            "change_token": post_detection.get("change_token"),
            "executed_step_ids": list(result.get("executed_step_ids", [])),
            "pending_manual_step_ids": pending_ids,
            "pending_plan": pending_plan,
            "state": "pending_manual" if pending_ids else "complete",
            "validated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "runtime_mode": self.runtime_mode,
        }
        path = Path(self.checkpoint_path or self.root / CHECKPOINT_RELATIVE_PATH)
        with runtime_state_transaction(lock_path=lock_path_for(path)):
            atomic_write_json(path, checkpoint)
        return checkpoint

    def decide_manual(self, plan_id: str, decision: str) -> dict[str, Any]:
        """Defer or reject the exact current manual-only candidate in local runtime state."""
        normalized_decision = str(decision or "").strip().lower()
        if normalized_decision not in {"deferred", "rejected"}:
            raise ValueError("manual evolution decision must be deferred or rejected")
        current_plan = self.plan()
        if not self.confirmed(current_plan, plan_id):
            raise ValueError("evolution plan changed; review the current manual candidate")
        if current_plan.get("auto_eligible_step_ids") or not current_plan.get("manual_step_ids"):
            raise ValueError("only a manual-only evolution candidate can be deferred or rejected")
        detection = self.detect()
        manual_ids = list(current_plan.get("manual_step_ids", [])) if normalized_decision == "deferred" else []
        pending_plan = None
        if manual_ids:
            pending_plan = {
                key: current_plan.get(key)
                for key in (
                    "schema_id",
                    "plan_id",
                    "runtime_mode",
                    "changed_path_count",
                    "changed_paths",
                    "changed_paths_truncated",
                    "full_review",
                    "full_review_reason",
                    "risk_tier",
                    "requires_confirmation",
                    "selected_step_ids",
                    "auto_eligible_step_ids",
                    "manual_step_ids",
                    "writes",
                    "auto_writes",
                    "manual_writes",
                    "validates",
                    "steps",
                    "tracked_markdown_count",
                    "changed_markdown_ratio",
                )
            }
            pending_plan["status"] = "candidate"
            pending_plan["pending_origin_paths"] = list(current_plan.get("pending_origin_paths") or current_plan.get("changed_paths", []))
        checkpoint = {
            **self.load_checkpoint(),
            "schema_id": "researchos-evolution-checkpoint-v1",
            "plan_id": current_plan.get("plan_id"),
            "head_sha": detection.get("head_sha"),
            "change_token": detection.get("change_token"),
            "pending_manual_step_ids": manual_ids,
            "pending_plan": pending_plan,
            "state": normalized_decision,
            "decision": normalized_decision,
            "decided_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "runtime_mode": self.runtime_mode,
        }
        path = Path(self.checkpoint_path or self.root / CHECKPOINT_RELATIVE_PATH)
        with runtime_state_transaction(lock_path=lock_path_for(path)):
            atomic_write_json(path, checkpoint)
        return checkpoint
