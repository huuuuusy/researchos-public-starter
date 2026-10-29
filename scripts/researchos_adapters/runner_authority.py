# ResearchOS maintenance header.
# 中文：Codex runner 的已登记执行动作与底层 launch policy；Policy Gateway 是唯一的机器授权 owner。
# English: Registered runner actions and low-level launch policies; Policy Gateway is the sole machine-authorization owner.

"""Registered launch-policy facts consumed by the server Policy Gateway."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from researchos_kernel.candidate_envelope import normalize_candidate_envelope
from researchos_adapters.filesystem_staging import OUTPUT_TARGET


POLICY_VERSION = "researchos-runner-authority-v1"


class RunnerAuthorityError(ValueError):
    """Raised when untrusted client data requests an unregistered execution scope."""


GENERIC_ARTIFACT_TARGETS = (
    dict(OUTPUT_TARGET),
)

def read_only_authority_policy() -> dict[str, object]:
    """Return the server-owned policy for answer and candidate-plan runs."""
    return {
        "policy_version": POLICY_VERSION,
        "authority_owner": "researchos_server",
        "action_id": "read_only_analysis",
        "entry_type": "work_session",
        "operation": "read_only",
        "allowed_write_targets": [],
        "network_access": "disabled",
        "credential_access": "denied",
        "permission_changes": "denied",
        "source_instruction_trust": "none",
    }


@dataclass(frozen=True)
class DirectExecutionRegistry:
    """Resolve a narrow direct action from server-validated fields.

    Queue entries originating only in browser localStorage deliberately have no
    registration here. They fail closed until a server-side candidate store can
    resolve the exact ``(entry_type, actionId)`` pair.
    """

    root: Path
    public_starter: bool = True

    def resolve(self, payload: object) -> dict[str, object]:
        if self.public_starter:
            raise RunnerAuthorityError("The public starter is read-only")
        if not isinstance(payload, dict):
            raise RunnerAuthorityError("Invalid direct-execution request")
        entries = payload.get("entries", [])
        if isinstance(entries, list) and entries:
            first = entries[0] if isinstance(entries[0], dict) else {}
            entry_type = str(first.get("type", "")).strip()[:80]
            action_id = str(first.get("actionId", "")).strip()[:240]
            raise RunnerAuthorityError(
                f"Unregistered direct-execution entry: {entry_type or '<missing>'}:{action_id or '<missing>'}"
            )

        candidate = normalize_candidate_envelope(payload.get("candidate", {}))
        proposed_action = candidate.get("proposed_action", {})
        action_id = str(proposed_action.get("id", "")).strip() if isinstance(proposed_action, dict) else ""
        candidate_type = str(candidate.get("candidate_type", "")).strip()
        source = str(payload.get("source", "")).strip()
        response_mode = str(payload.get("response_mode", "")).strip()
        if source != "dashboard-work-session" or response_mode != "artifact":
            raise RunnerAuthorityError("Direct execution requires a registered Work Session artifact action")

        if action_id == "work_session_artifact" and candidate_type == "work_session":
            return self._policy(
                action_id=action_id,
                allowed_write_targets=GENERIC_ARTIFACT_TARGETS,
                network_access="disabled",
            )
        raise RunnerAuthorityError(
            f"Unregistered direct-execution action: {candidate_type or '<missing>'}:{action_id or '<missing>'}"
        )

    @staticmethod
    def _policy(
        *,
        action_id: str,
        allowed_write_targets: tuple[dict[str, str], ...],
        network_access: str,
    ) -> dict[str, object]:
        policy: dict[str, object] = {
            "policy_version": POLICY_VERSION,
            "authority_owner": "researchos_server",
            "action_id": action_id,
            "entry_type": "work_session",
            "operation": "create_artifact",
            "allowed_write_targets": [dict(target) for target in allowed_write_targets],
            "network_access": network_access,
            "credential_access": "denied",
            "permission_changes": "denied",
            "source_instruction_trust": "none",
        }
        return policy

    def validates(self, policy: object) -> bool:
        """Re-resolve the fixed action shape before applying its authority envelope."""
        if self.public_starter or not isinstance(policy, dict):
            return False
        action_id = str(policy.get("action_id", "")).strip()
        expected_targets = {
            "work_session_artifact": GENERIC_ARTIFACT_TARGETS,
        }.get(action_id)
        if expected_targets is None:
            return False
        if policy.get("policy_version") != POLICY_VERSION or policy.get("authority_owner") != "researchos_server":
            return False
        if policy.get("entry_type") != "work_session" or policy.get("operation") != "create_artifact":
            return False
        if policy.get("allowed_write_targets") != [dict(target) for target in expected_targets]:
            return False
        return True
