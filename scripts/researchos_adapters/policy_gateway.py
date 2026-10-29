# ResearchOS maintenance header.
# 中文：唯一的服务端执行策略 Gateway；把不可信任务请求解析成短期、范围有界且可复验的机器执行授权，不产生长期研究 authority。
# English: Sole server execution-policy Gateway; converts untrusted task requests into short-lived, bounded, revalidatable machine grants without creating long-term research authority.

"""PolicyDecision and AuthorizationGrant contracts for ResearchOS execution."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

from researchos_adapters.runner_authority import (
    DirectExecutionRegistry,
    RunnerAuthorityError,
    read_only_authority_policy,
)
from researchos_kernel.task_envelope import RUNTIME_SCOPES, TASK_ENVELOPE_SCHEMA_ID
from researchos_kernel.ledger import digest as _digest


POLICY_DECISION_SCHEMA_ID = "researchos-policy-decision-v1"
AUTHORIZATION_GRANT_SCHEMA_ID = "researchos-authorization-grant-v1"
POLICY_VERSION = "researchos-policy-gateway-v1"
POLICY_ISSUER = "researchos_adapters.policy_gateway"
GRANT_VALIDITY_SECONDS = 900


class PolicyGatewayError(ValueError):
    """Public-safe policy failure; raw task data is never echoed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class PreparedPolicy:
    """Internal pre-decision route; it is not a grant and has no authority by itself."""

    action_id: str
    operation: str
    reason_code: str
    risk_class: str
    launch_policy: dict[str, object]


def _aware(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    return current.replace(tzinfo=timezone.utc) if current.tzinfo is None else current.astimezone(timezone.utc)


def _time_text(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_time(value: object) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise PolicyGatewayError("authorization_grant_invalid") from exc
    if parsed.tzinfo is None:
        raise PolicyGatewayError("authorization_grant_invalid")
    return parsed.astimezone(timezone.utc)


def _targets(policy: dict[str, object]) -> list[dict[str, str]]:
    raw = policy.get("allowed_write_targets", [])
    if not isinstance(raw, list) or len(raw) > 8:
        raise PolicyGatewayError("authorization_grant_invalid")
    targets: list[dict[str, str]] = []
    for value in raw:
        if not isinstance(value, dict) or set(value) != {"path", "mode"}:
            raise PolicyGatewayError("authorization_grant_invalid")
        path = str(value.get("path", "")).strip()
        mode = str(value.get("mode", "")).strip()
        lexical = PurePosixPath(path)
        if not path or path.startswith("/") or ".." in lexical.parts or mode not in {"exact", "subtree"}:
            raise PolicyGatewayError("authorization_grant_invalid")
        targets.append({"path": path[:512], "mode": mode})
    return targets


def _target_binding(policy: dict[str, object]) -> dict[str, object]:
    targets = _targets(policy)
    return {
        "state": "bounded" if targets else "none",
        "digest": _digest(targets) if targets else "",
        "targets": targets,
    }


def _task_facts(envelope: object) -> dict[str, str]:
    if not isinstance(envelope, dict) or envelope.get("schema_id") != TASK_ENVELOPE_SCHEMA_ID:
        raise PolicyGatewayError("authorization_grant_invalid")
    authorization = envelope.get("authorization_ref")
    runtime = envelope.get("runtime_ref")
    if authorization != {"state": "unresolved"} or not isinstance(runtime, dict):
        raise PolicyGatewayError("authorization_grant_invalid")
    facts = {
        "task_id": str(envelope.get("task_id", "")),
        "run_id": str(envelope.get("run_id", "")),
        "idempotency_key": str(envelope.get("idempotency_key", "")),
        "capability_id": str(envelope.get("capability_id", "")),
        "runtime_scope": str(runtime.get("scope", "")),
        "task_data_digest": str(runtime.get("task_data_digest", "")),
    }
    if not facts["task_id"].startswith("task:") or not facts["idempotency_key"].startswith("idem:"):
        raise PolicyGatewayError("authorization_grant_invalid")
    if not facts["run_id"] or facts["runtime_scope"] not in RUNTIME_SCOPES:
        raise PolicyGatewayError("authorization_grant_invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", facts["task_data_digest"]):
        raise PolicyGatewayError("authorization_grant_invalid")
    return facts


def policy_receipt_ref(value: object) -> dict[str, str]:
    """Return a bounded reference for runtime projection and post-queued retention."""
    if not isinstance(value, dict):
        return {}
    schema_id = str(value.get("schema_id", ""))
    identity_key = "decision_id" if schema_id == POLICY_DECISION_SCHEMA_ID else "grant_id"
    if schema_id not in {POLICY_DECISION_SCHEMA_ID, AUTHORIZATION_GRANT_SCHEMA_ID}:
        return {}
    return {
        "schema_id": schema_id,
        identity_key: str(value.get(identity_key, "")),
        "task_id": str(value.get("task_id", "")),
        "run_id": str(value.get("run_id", "")),
        "receipt_digest": _digest(value),
    }


@dataclass(frozen=True)
class PolicyGateway:
    root: Path
    runtime_scope: str
    action_registry: DirectExecutionRegistry
    validity_seconds: int = GRANT_VALIDITY_SECONDS

    def __post_init__(self) -> None:
        if self.runtime_scope not in RUNTIME_SCOPES or self.validity_seconds <= 0:
            raise ValueError("Invalid Policy Gateway configuration")

    def prepare(self, payload: object, task_mode: str) -> PreparedPolicy:
        """Resolve an action before model/CLI work; returned data is still not a grant."""
        if self.runtime_scope == "public_starter":
            raise PolicyGatewayError("public_starter_copy_only")
        if task_mode in {"read_only_analysis", "candidate_patch_plan"}:
            policy = read_only_authority_policy()
            return PreparedPolicy(
                action_id=str(policy["action_id"]), operation="read_only",
                reason_code="registered_read_only", risk_class="read_only", launch_policy=policy,
            )
        if task_mode != "direct_execution":
            raise PolicyGatewayError("unregistered_direct_execution_action")
        try:
            policy = self.action_registry.resolve(payload)
        except RunnerAuthorityError as exc:
            raise PolicyGatewayError("unregistered_direct_execution_action") from exc
        if not self.action_registry.validates(policy):
            raise PolicyGatewayError("authorization_grant_invalid")
        return PreparedPolicy(
            action_id=str(policy.get("action_id", "")), operation=str(policy.get("operation", "")),
            reason_code="registered_bounded_artifact", risk_class="bounded_write", launch_policy=policy,
        )

    def _validate_prepared(self, prepared: object) -> PreparedPolicy:
        if not isinstance(prepared, PreparedPolicy):
            raise PolicyGatewayError("authorization_grant_invalid")
        read_only = read_only_authority_policy()
        if prepared.operation == "read_only":
            valid = prepared == PreparedPolicy(
                action_id=str(read_only["action_id"]), operation="read_only",
                reason_code="registered_read_only", risk_class="read_only", launch_policy=read_only,
            )
        else:
            valid = (
                prepared.operation == "create_artifact"
                and prepared.reason_code == "registered_bounded_artifact"
                and prepared.risk_class == "bounded_write"
                and prepared.action_id == str(prepared.launch_policy.get("action_id", ""))
                and self.action_registry.validates(prepared.launch_policy)
            )
        if not valid:
            raise PolicyGatewayError("authorization_grant_invalid")
        return prepared

    def issue(
        self, prepared: PreparedPolicy, task_envelope: object, *, now: datetime | None = None
    ) -> dict[str, dict[str, object]]:
        """Issue separate decision/grant receipts bound to one immutable pre-policy TaskEnvelope."""
        prepared = self._validate_prepared(prepared)
        facts = _task_facts(task_envelope)
        if facts["runtime_scope"] != self.runtime_scope:
            raise PolicyGatewayError("authorization_grant_invalid")
        issued_at = _aware(now)
        target_binding = _target_binding(prepared.launch_policy)
        diff_binding = {
            "state": "request_digest" if prepared.operation == "create_artifact" else "none",
            "digest": facts["task_data_digest"] if prepared.operation == "create_artifact" else "",
        }
        base = {
            "schema_id": POLICY_DECISION_SCHEMA_ID,
            "policy_version": POLICY_VERSION,
            "issuer": POLICY_ISSUER,
            "runtime_scope": self.runtime_scope,
            **{key: facts[key] for key in ("task_id", "run_id", "idempotency_key", "capability_id")},
            "action_id": prepared.action_id,
            "operation": prepared.operation,
            "outcome": "allow",
            "reason_code": prepared.reason_code,
            "risk_class": prepared.risk_class,
            "target_binding": target_binding,
            "diff_binding": diff_binding,
            "issued_at": _time_text(issued_at),
        }
        decision = {**base, "decision_id": f"policy:{_digest(base)}"}
        grant_base = {
            "schema_id": AUTHORIZATION_GRANT_SCHEMA_ID,
            "policy_decision_id": decision["decision_id"],
            "policy_version": POLICY_VERSION,
            "issuer": POLICY_ISSUER,
            "trust_basis": "server_runtime_policy",
            "human_authorization_state": "not_claimed",
            "runtime_scope": self.runtime_scope,
            **{key: facts[key] for key in ("task_id", "run_id", "idempotency_key", "capability_id")},
            "action_id": prepared.action_id,
            "operation": prepared.operation,
            "risk_class": prepared.risk_class,
            "target_binding": copy.deepcopy(target_binding),
            "diff_binding": copy.deepcopy(diff_binding),
            "allowed_effects": {
                "filesystem": "bounded_write" if prepared.operation == "create_artifact" else "read_only",
                "network": "disabled",
                "credentials": "denied",
                "permission_changes": "denied",
            },
            "valid_from": _time_text(issued_at),
            "expires_at": _time_text(issued_at + timedelta(seconds=self.validity_seconds)),
        }
        grant = {**grant_base, "grant_id": f"grant:{_digest(grant_base)}"}
        return {
            "policy_decision": decision,
            "authorization_grant": grant,
            "authority_policy": copy.deepcopy(prepared.launch_policy),
        }

    def launch_policy(
        self, run: object, *, now: datetime | None = None, enforce_expiry: bool = True
    ) -> dict[str, object]:
        """Revalidate one grant at dispatch; direct execution without it fails closed."""
        record = run if isinstance(run, dict) else {}
        task_mode = str(record.get("task_mode", "read_only_analysis"))
        if task_mode != "direct_execution" and not record.get("authorization_grant"):
            return read_only_authority_policy()
        envelope = record.get("task_envelope")
        facts = _task_facts(envelope)
        prepared = self.prepare(record, task_mode)
        decision = record.get("policy_decision")
        grant = record.get("authorization_grant")
        if not isinstance(decision, dict) or not isinstance(grant, dict):
            raise PolicyGatewayError("authorization_grant_invalid")
        if decision.get("schema_id") != POLICY_DECISION_SCHEMA_ID or grant.get("schema_id") != AUTHORIZATION_GRANT_SCHEMA_ID:
            raise PolicyGatewayError("authorization_grant_invalid")
        decision_base = {key: copy.deepcopy(value) for key, value in decision.items() if key != "decision_id"}
        grant_base = {key: copy.deepcopy(value) for key, value in grant.items() if key != "grant_id"}
        if decision.get("decision_id") != f"policy:{_digest(decision_base)}":
            raise PolicyGatewayError("authorization_grant_invalid")
        if grant.get("grant_id") != f"grant:{_digest(grant_base)}" or grant.get("policy_decision_id") != decision.get("decision_id"):
            raise PolicyGatewayError("authorization_grant_invalid")
        expected = self.issue(prepared, envelope, now=_parse_time(grant.get("valid_from")))
        if expected["policy_decision"] != decision or expected["authorization_grant"] != grant:
            raise PolicyGatewayError("authorization_grant_invalid")
        if enforce_expiry and not (_parse_time(grant["valid_from"]) <= _aware(now) < _parse_time(grant["expires_at"])):
            raise PolicyGatewayError("authorization_grant_expired")
        if any(str(grant.get(key, "")) != facts[key] for key in ("task_id", "run_id", "idempotency_key", "capability_id")):
            raise PolicyGatewayError("authorization_grant_invalid")
        if record.get("authority_policy") != prepared.launch_policy:
            raise PolicyGatewayError("authorization_grant_invalid")
        return copy.deepcopy(prepared.launch_policy)

    def projection_policy(self, run: object) -> dict[str, object]:
        """Project a verified historical launch policy without renewing or extending its grant."""
        try:
            return self.launch_policy(run, enforce_expiry=False)
        except PolicyGatewayError:
            return read_only_authority_policy()
