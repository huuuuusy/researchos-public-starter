from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_kernel.rule_evolution import (  # noqa: E402
    CLAIM_BOUNDARY,
    OBJECT_KINDS,
    SCHEMA_ID,
    RuleEvolutionError,
    build_bounded_trial,
    build_disposition_proposal,
    build_rule_candidate,
    build_transition_proposal,
    evaluate_trial,
    lifecycle_view,
    normalize_evidence,
    normalize_rule_version,
)


def candidate_payload() -> dict[str, object]:
    return {
        "statement": "Route only the evidence needed for the current task.",
        "scope": {"task_types": ["review"], "profile_ids": ["deep"], "project_refs": ["project:alpha"]},
        "source_episodes": ["episode:1", "episode:2"],
        "counterevidence": {"status": "observed", "refs": ["episode:counter-1"], "assessment": "The narrow context omitted a needed method detail."},
        "version": 1,
        "review_date": "2026-10-01T00:00:00Z",
        "retire_trigger": "Any critical omission attributable to the rule.",
        "rollback_target": "rule:previous-v0",
        "created_at": "2026-08-13T00:00:00Z",
    }


def evidence(*, episodes: int = 3, breach: bool = False) -> dict[str, object]:
    return {
        "episode_refs": [f"episode:{index}" for index in range(episodes)],
        "counterexample_refs": ["episode:counter-1"],
        "primary_outcome": {
            "name": "safe recovery",
            "definition": "Correctly identify the next safe action.",
            "baseline": "versioned handoff",
            "observation_window": "three independent delayed episodes",
            "owner": "researcher",
            "missing_data_policy": "hold",
            "observation": "three of three synthetic fixtures preserved the boundary",
        },
        "guardrails": [{
            "name": "authority confusion",
            "critical": True,
            "threshold": "zero critical errors",
            "action": "stop trial",
            "observation": "one breach" if breach else "none observed",
            "breached": breach,
        }],
        "burden": {"definition": "extra review steps", "observation": "one bounded review", "acceptable": True},
        "sufficiency": {"required_episode_count": 3, "counterevidence_reviewed": True},
    }


def rule_version(*, stability: str, review_date: str, expires_at: str = "") -> dict[str, object]:
    record: dict[str, object] = {
        "schema_id": SCHEMA_ID,
        "object_kind": "rule_version",
        "rule_version_ref": "rule:alpha:v2",
        "rule_id": "rule:alpha",
        "version": 2,
        "statement": "Route only the evidence needed for the current task.",
        "scope": {"task_types": ["review"], "profile_ids": ["deep"], "project_refs": ["project:alpha"]},
        "source_episodes": ["episode:1", "episode:2", "episode:3"],
        "counterevidence": {"status": "observed", "refs": ["episode:counter-1"], "assessment": "A critical omission remains the retire trigger."},
        "stability": stability,
        "review_date": review_date,
        "retire_trigger": "Any critical context omission.",
        "rollback_target": "rule:alpha:v1",
        "supersedes": ["rule:alpha:v1"],
        "human_disposition_ref": "decision:human-accepted-v2",
        "claim_boundary": CLAIM_BOUNDARY,
    }
    if expires_at:
        record["expires_at"] = expires_at
    return record


class RuleEvolutionContractTest(unittest.TestCase):
    def test_candidate_is_deterministic_and_candidate_only(self) -> None:
        first = build_rule_candidate(candidate_payload())
        second = build_rule_candidate(candidate_payload())
        self.assertEqual(first, second)
        self.assertEqual("rule_candidate", first["object_kind"])
        self.assertEqual("candidate_only", first["authority"])
        self.assertEqual(CLAIM_BOUNDARY, first["claim_boundary"])

    def test_candidate_requires_provenance_counterevidence_review_and_rollback(self) -> None:
        for missing in ("source_episodes", "counterevidence", "review_date", "retire_trigger", "rollback_target"):
            payload = candidate_payload()
            payload.pop(missing)
            with self.subTest(missing=missing), self.assertRaises(RuleEvolutionError):
                build_rule_candidate(payload)
        payload = candidate_payload()
        payload["counterevidence"] = {"status": "observed", "refs": [], "assessment": "none"}
        with self.assertRaisesRegex(RuleEvolutionError, "missing_counterexample"):
            build_rule_candidate(payload)

    def test_trial_cannot_expand_scope_or_window(self) -> None:
        candidate = build_rule_candidate(candidate_payload())
        with self.assertRaisesRegex(RuleEvolutionError, "trial_scope_expansion"):
            build_bounded_trial(
                candidate,
                scope={"task_types": ["writing"], "profile_ids": [], "project_refs": []},
                begins_at="2026-08-13T00:00:00Z",
                expires_at="2026-08-14T00:00:00Z",
            )
        with self.assertRaisesRegex(RuleEvolutionError, "invalid_trial_window"):
            build_bounded_trial(
                candidate,
                scope={"task_types": ["review"], "profile_ids": [], "project_refs": []},
                begins_at="2026-08-14T00:00:00Z",
                expires_at="2026-08-13T00:00:00Z",
            )

    def test_trial_is_exact_scope_time_bound_and_public_inactive(self) -> None:
        candidate = build_rule_candidate(candidate_payload())
        trial = build_bounded_trial(
            candidate,
            scope={"task_types": ["review"], "profile_ids": ["deep"], "project_refs": ["project:alpha"]},
            begins_at="2026-08-13T00:00:00Z",
            expires_at="2026-08-14T00:00:00Z",
        )
        allowed = evaluate_trial(trial, runtime_scope="private", task_type="review", profile_id="deep", project_ref="project:alpha", now="2026-08-13T12:00:00Z")
        self.assertTrue(allowed["eligible"])
        self.assertFalse(evaluate_trial(trial, runtime_scope="private", task_type="writing", profile_id="deep", project_ref="project:alpha", now="2026-08-13T12:00:00Z")["eligible"])
        self.assertEqual("inactive_expired", evaluate_trial(trial, runtime_scope="private", task_type="review", profile_id="deep", project_ref="project:alpha", now="2026-08-14T00:00:00Z")["view"])
        public = evaluate_trial(trial, runtime_scope="public_starter", task_type="review", profile_id="deep", project_ref="project:alpha", now="2026-08-13T12:00:00Z")
        self.assertEqual("public_starter_never_activates_rules", public["reason"])

    def test_evidence_has_one_primary_outcome_guardrails_and_burden(self) -> None:
        normalized = normalize_evidence(evidence())
        self.assertTrue(normalized["sufficiency"]["sufficient_for_proposal"])
        for forbidden in ("acceptance_rate", "rule_count"):
            payload = evidence()
            payload[forbidden] = 1
            with self.subTest(forbidden=forbidden), self.assertRaisesRegex(RuleEvolutionError, "forbidden_rule_metric"):
                normalize_evidence(payload)

    def test_insufficient_or_critical_evidence_forces_defer(self) -> None:
        candidate = build_rule_candidate(candidate_payload())
        insufficient = build_disposition_proposal(candidate, proposed="retain", evidence=evidence(episodes=2), created_at="2026-08-13T00:00:00Z")
        breached = build_disposition_proposal(candidate, proposed="retire", evidence=evidence(breach=True), created_at="2026-08-13T00:00:00Z")
        self.assertEqual("defer", insufficient["proposed"])
        self.assertEqual("defer", breached["proposed"])
        self.assertEqual("proposal_only_human_disposition_required", insufficient["authority"])

    def test_sufficient_evidence_still_only_builds_proposal(self) -> None:
        candidate = build_rule_candidate(candidate_payload())
        proposal = build_disposition_proposal(candidate, proposed="revise", evidence=evidence(), created_at="2026-08-13T00:00:00Z")
        self.assertEqual("revise", proposal["proposed"])
        self.assertNotIn("applied", proposal)
        self.assertNotIn("human_decision", proposal)

    def test_stable_review_due_never_auto_degrades(self) -> None:
        stable = rule_version(stability="stable", review_date="2026-08-01T00:00:00Z")
        view = lifecycle_view(stable, now="2026-08-13T00:00:00Z")
        self.assertEqual("review_due", view["view"])
        self.assertTrue(view["active"])
        self.assertTrue(view["requires_human_disposition"])

    def test_rule_version_requires_provenance_and_human_disposition_ref(self) -> None:
        stable = rule_version(stability="stable", review_date="2026-09-01T00:00:00Z")
        self.assertEqual("decision:human-accepted-v2", normalize_rule_version(stable)["human_disposition_ref"])
        for missing in ("source_episodes", "counterevidence", "retire_trigger", "rollback_target", "human_disposition_ref"):
            forged = dict(stable)
            forged.pop(missing)
            with self.subTest(missing=missing), self.assertRaises(RuleEvolutionError):
                normalize_rule_version(forged)
        forged_stable = dict(stable, expires_at="2026-10-01T00:00:00Z")
        with self.assertRaisesRegex(RuleEvolutionError, "stable_rule_expiry_forbidden"):
            normalize_rule_version(forged_stable)

    def test_only_provisional_explicit_expiry_auto_stops(self) -> None:
        provisional = rule_version(stability="provisional", review_date="2026-09-01T00:00:00Z", expires_at="2026-08-12T00:00:00Z")
        view = lifecycle_view(provisional, now="2026-08-13T00:00:00Z")
        self.assertEqual("inactive_expired", view["view"])
        self.assertFalse(view["active"])
        missing_expiry = rule_version(stability="provisional", review_date="2026-09-01T00:00:00Z")
        with self.assertRaises(RuleEvolutionError):
            lifecycle_view(missing_expiry, now="2026-08-13T00:00:00Z")

    def test_supersede_and_rollback_preserve_history_as_proposals(self) -> None:
        current = rule_version(stability="stable", review_date="2026-09-01T00:00:00Z")
        supersede = build_transition_proposal(current, action="supersede", target_ref="candidate:new", evidence_refs=["episode:1"], created_at="2026-08-13T00:00:00Z")
        rollback = build_transition_proposal(current, action="rollback", target_ref="rule:alpha:v1", evidence_refs=["incident:1"], created_at="2026-08-13T00:00:00Z")
        self.assertEqual(["rule:alpha:v2"], supersede["supersedes"])
        self.assertIn("rule:alpha:v1", rollback["history_refs"])
        self.assertEqual("proposal_only_human_disposition_required", rollback["authority"])
        with self.assertRaisesRegex(RuleEvolutionError, "rollback_target_mismatch"):
            build_transition_proposal(current, action="rollback", target_ref="rule:other", evidence_refs=["incident:1"], created_at="2026-08-13T00:00:00Z")

    def test_schema_and_runtime_share_claim_boundary(self) -> None:
        schema = json.loads((ROOT / "09_templates/data_contracts/researchos-rule-evolution-v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(SCHEMA_ID, schema["$id"])
        self.assertEqual(CLAIM_BOUNDARY, schema["properties"]["claim_boundary"]["const"])
        self.assertIs(False, schema.get("additionalProperties"))
        self.assertEqual(list(OBJECT_KINDS), schema["properties"]["object_kind"]["enum"])
        invariants = "\n".join(schema["x-invariants"])
        for token in ("never activates in public_starter", "never automatic downgrade", "require human disposition", "not demonstrated human-AI co-evolution"):
            self.assertIn(token, invariants)

    def test_runtime_accepts_the_canonical_candidate_fixture(self) -> None:
        build_rule_candidate({
            "statement": "Use the smallest evidence-bounded context that can answer the task.",
            "scope": {"task_types": ["synthetic"], "profile_ids": [], "project_refs": []},
            "source_episodes": ["episode:synthetic-1"],
            "counterevidence": {"status": "unknown", "refs": [], "assessment": "Counterexamples remain an explicit open question."},
            "version": 1,
            "review_date": "2027-01-01T00:00:00Z",
            "retire_trigger": "A critical context omission is observed.",
            "rollback_target": "rule:none",
            "created_at": "2026-08-13T00:00:00Z",
        })


if __name__ == "__main__":
    unittest.main()
