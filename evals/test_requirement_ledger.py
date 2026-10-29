"""The scheduler's requirement ledger is the context-impact review ledger (refactor v5, D1).

Canon obligations CR-4 and CA-5: one owner for requirement state. The kernel may
only touch the ledger family (JSON, coordination record stream, rebuildable cache,
shared lock), must write the
coordination series v1 vocabulary, and migrates the retired work_state/ros store
exactly once without changing derived state.
"""

from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "evals"))

import ros  # noqa: E402
from researchos_kernel.ledger import CHECK_RESULTS, ISSUE_STATES, Ledger, binding  # noqa: E402

TODAY = date(2026, 9, 20)
from test_ros_kernel import PORTFOLIO  # noqa: E402


class RequirementLedgerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ros-ledger-"))
        for relative in ("config/extensions/rules", "09_templates/data_contracts"):
            shutil.copytree(ROOT / relative, self.tmp / relative)
        self.config = json.loads((ROOT / "config" / "ros.json").read_text(encoding="utf-8"))
        self.config.update({"graph_roots": ["01_knowledge", "06_active_context"], "runtime_scope": "private"})
        self.write("config/ros.json", json.dumps(self.config))
        self.write("06_active_context/research-portfolio.md", PORTFOLIO)
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\n")
        self.ledger = Ledger(self.tmp / self.config["requirement_ledger"])

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def write(self, relative: str, text: str) -> None:
        path = self.tmp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def ros(self, *argv: str) -> dict:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = ros.main(["--root", str(self.tmp), "--today", TODAY.isoformat(), "--json", *argv])
        self.assertEqual(code, 0, buffer.getvalue())
        return json.loads(buffer.getvalue())

    def exercise(self) -> None:
        self.ros("today")
        draft = self.tmp / "draft.md"
        draft.write_text("> [!judgment] j-alpha\n> 结论：Occlusion first\n> 依据：alpha-project\n", encoding="utf-8")
        candidate = self.ros("propose", "judgment", "--file", str(draft), "--target", "commitment:alpha")["candidates"][0]
        self.ros("admit", candidate)
        self.ros("today")
        issue = next(i for i, st in self.ledger.derive_states()["issues"].items() if st["status"] == "open")
        self.ros("decide", issue[:10], "defer", "--until", "2026-09-21")
        self.ros("context", "commitment:alpha")
        self.ros("close")

    def test_kernel_writes_only_the_context_impact_ledger_family(self) -> None:
        self.exercise()
        work_state = self.tmp / "06_active_context/work_state"
        runtime = self.tmp / self.config["runtime_dir"]
        staging_owner = work_state / ".artifact-rollbacks"
        written = {path for path in work_state.rglob("*")
                   if path.is_file() and runtime not in path.parents and staging_owner not in path.parents}
        self.assertTrue(written)
        self.assertLessEqual(written, self.ledger.family())
        receipts = sorted(staging_owner.glob("canonical-*/receipt.json"))
        self.assertTrue(receipts, "an admitted write leaves a staging receipt with its rollback copy")
        receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "committed")
        self.assertTrue(all(change["new_digest"] for change in receipt["changes"]))
        for retired in ("requirements.jsonl", "trajectory.jsonl", "cursor.json"):
            self.assertEqual(list(self.tmp.rglob(retired)), [], f"retired store file {retired} reappeared")
        self.assertEqual({p.name for p in runtime.iterdir()}, {"sessions"}, "候选载荷已并入账本家族，运行时只保留会话快照")


    def test_records_use_coordination_series_v1_vocabulary(self) -> None:
        self.exercise()
        # Fictional schema fixture: no private history contract or server store is read.
        contract = {
            "issue_states": ["open", "deferred", "waiting", "resolved", "cancelled"],
            "check_results": ["met", "unmet", "unknown", "not_evaluated"],
            "operations": ["inspect", "clarify", "defer", "revise_with_sources", "retain_if_consistent",
                           "compose", "retire", "admit", "rollback", "ask"],
            "collections": {
                "trajectory": ["id", "episode_id", "point_id", "at", "available_at", "availability_reason",
                               "origin", "evidence_ids", "measurements", "kind", "payload"],
                "observations": ["id", "time", "unknown_times", "state_ids", "state_count",
                                 "changed_state_ids", "causal_parents", "evidence_ids", "source_version_vector"],
                "decision_points": ["id", "episode_id", "context_id", "cutoff", "origin"],
                "episodes": ["id", "episode_id", "boundary_basis", "object_ids", "start", "end"],
            },
            "trajectory_payloads": {
                "issue_transition": ["issue_id", "requirement_id", "scope_object_ids", "to", "reason",
                                     "check_ids", "previous_transition_id", "binding"],
                "decision": ["issue_id", "operation", "bindings", "read_set", "candidate_ids", "permission_state"],
                "attempt": ["decision_id", "status", "output_ids"],
                "effect": ["attempt_id", "knowledge", "changes", "unchanged_object_ids"],
                "check": ["attempt_id", "requirement_id", "result", "checked_state_ids", "supports_effect_ids", "basis", "binding"],
                "ask": ["ask_id", "class_key", "issue_ids", "check_id", "basis_version", "options", "state", "answer", "reopen_trigger"],
            },
        }
        self.assertEqual(set(contract["issue_states"]), ISSUE_STATES)
        self.assertEqual(set(contract["check_results"]), CHECK_RESULTS)
        rows = self.ledger.records()
        kinds = {row["kind"] for row in rows if row["collection"] == "trajectory"}
        self.assertLessEqual({"issue_transition", "decision", "attempt", "effect", "check"}, kinds)
        for row in rows:
            fields = set(contract["collections"][row["collection"]])
            self.assertLessEqual(fields - {"boundary_basis", "start", "end", "object_ids"} if row["collection"] == "episodes"
                                 else fields, set(row) | {"id"}, row)
            if row["collection"] != "trajectory":
                continue
            self.assertLessEqual(set(contract["trajectory_payloads"][row["kind"]]), set(row["payload"]), row)
            payload = row["payload"]
            if row["kind"] == "issue_transition":
                self.assertIn(payload["to"], ISSUE_STATES)
                self.assertEqual(set(payload["binding"]), {"issue_id", "occurrence_id", "generation", "attempt_id",
                                                           "rule_version", "purpose_version", "source_version_vector"})
            if row["kind"] == "decision":
                self.assertIn(payload["operation"], contract["operations"])
            if row["kind"] == "check":
                self.assertIn(payload["result"], CHECK_RESULTS)

    def test_a_torn_last_line_is_an_interrupted_append_not_a_damaged_ledger(self) -> None:
        self.exercise()
        with open(self.ledger.records_path, "a", encoding="utf-8") as handle:
            handle.write('{"collection": "trajectory", "kind": "check"')
        rows = self.ledger.records()
        self.assertTrue(rows)
        self.ros("today")  # the next boundary still runs
        self.ledger.decision_point(cutoff="2026-09-19T00:00:00+00:00")
        self.assertTrue(self.ledger.records(), "an append after a torn line does not bury it mid-file")
        self.assertFalse(any(row.get("kind") == "check" and "id" not in row for row in self.ledger.records()))

    def test_occurrence_identity_is_stable_per_issue_and_generation(self) -> None:
        self.assertEqual(binding("i", 2)["occurrence_id"], binding("i", 2)["occurrence_id"])
        self.assertNotEqual(binding("i", 2)["occurrence_id"], binding("i", 3)["occurrence_id"])
        self.assertEqual(binding()["occurrence_id"], "")


if __name__ == "__main__":
    unittest.main()
