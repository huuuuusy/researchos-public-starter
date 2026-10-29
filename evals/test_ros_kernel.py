"""Contract tests for the plan v4 scheduling kernel and the ros command.

Each test builds a small throwaway repository, so the kernel is exercised end to
end: Markdown sources -> boundary -> requirement ledger -> triage -> admission.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ros  # noqa: E402
from researchos_adapters import context_pack  # noqa: E402
from researchos_adapters.dispatch import RUN_LOG  # noqa: E402
from researchos_adapters.markdown_repo import build_snapshot  # noqa: E402
from researchos_kernel.boundary import run_boundary  # noqa: E402
from researchos_kernel.judgments import parse_judgments, strip_judgments  # noqa: E402
from researchos_kernel.ledger import Ledger, digest  # noqa: E402
from researchos_kernel.context_receipt import normalize_context_receipt  # noqa: E402

TODAY = date(2026, 9, 20)


def dispatchable(ctx, provider_id: str):
    """The adapter `ros run` would dispatch ``provider:<id>`` to under ``ctx``, or None."""
    return ros.provider_for(ctx.config, ctx.runtime_scope, provider_id)

# The public starter ships no attention owner (Attention Kernel §6); tests that write attention need it.
import importlib.util  # noqa: E402
HAS_ATTENTION_OWNER = importlib.util.find_spec("researchos_server.attention_schedule_store") is not None
PORTFOLIO = """---
title: Portfolio
---

## Responsibility Items

### Alpha Paper

- id: alpha
- responsibility: lead
- state: mainline
- priority: P0
- question: Does method A transfer under occlusion?
- next_step: Run the occlusion comparison
- last_verified: 2026-09-18
- stale_after_days: 7
- target_date: 2026-09-22
- deadline: 2026-09-22
- source_path: 01_knowledge/projects/alpha.md

### Beta Survey

- id: beta
- responsibility: lead
- state: waiting
- priority: P1
- next_step: Wait for reviews
- last_verified: 2026-08-01
- stale_after_days: 14
- target_date: continuous
- source_path: 01_knowledge/projects/beta.md

### Gamma Closed

- id: gamma
- responsibility: support
- state: closed
- last_verified: 2026-01-01
- stale_after_days: 7
"""


class Terminal(io.StringIO):
    """This machine's terminal: ros asks the researcher here, and only an answer here is theirs."""

    def isatty(self) -> bool:
        return True


class RosKernelTest(unittest.TestCase):
    # fixtures shared by several sections
    OPTIONS = ["unsatisfied", "narrow", "cancel", "defer"]
    EPISODE = "01_knowledge/projects/rounds/round-1.md"
    EPISODE_TEXT = "---\ntitle: Round 1\nepisode_state: open\n---\n# Round 1\nWhat this round found.\n"
    RUN_DRAFT = ("> [!judgment] j-{id}\n> 结论：Occlusion results do not transfer yet\n"
             "> 依据：01_knowledge/projects/alpha.md@{pin}\n")
    DRAFT = ("> [!judgment] j-beta-next\n> 结论：Survey the reviewers first\n"
             "> 依据：01_knowledge/projects/beta.md\n> 放弃的选项：Wait silently\n")
    CARD = "01_knowledge/projects/beta.md"
    ATTENTION = "06_active_context/work_state/attention-schedule.md"

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ros-kernel-"))
        for relative in ("config/extensions/rules", "09_templates/data_contracts"):
            shutil.copytree(ROOT / relative, self.tmp / relative)
        config = json.loads((ROOT / "config" / "ros.json").read_text(encoding="utf-8"))
        config.update({"graph_roots": ["01_knowledge", "06_active_context"], "runtime_scope": "private",
                       "portfolio": "06_active_context/research-portfolio.md"})
        self.write("config/ros.json", json.dumps(config))
        self.write("06_active_context/research-portfolio.md", PORTFOLIO)
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v1\n")
        self.write("01_knowledge/projects/beta.md", "---\ntitle: Beta\n---\n# Beta\n")
        self.write("01_knowledge/papers/secret.md", "---\ntitle: Secret\nsensitivity: private\n---\n# Secret\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    # helpers -----------------------------------------------------------------------------
    def write(self, relative: str, text: str) -> None:
        path = self.tmp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        stamp = time.time_ns() + 1_000_000
        os.utime(path, ns=(stamp, stamp))  # ensure the stat cache sees the change

    def run_ros(self, *argv: str, today: date = TODAY, json_out: bool = True, lang: str = "", expect=0,
                answer: str | None = None) -> tuple:
        """Run ros once: (exit code, stdout, stderr). ``expect`` is the exit code it must return, or
        SystemExit when it must refuse (the first item is then the refusal message). ``answer`` is the
        reply typed at this machine's terminal; without it, stdin and stderr are not a terminal."""
        stdout, stderr = io.StringIO(), Terminal() if answer is not None else io.StringIO()
        argv = ["--root", str(self.tmp), "--today", today.isoformat(), *(["--json"] if json_out else []),
                *(["--lang", lang] if lang else []), *argv]
        saved = sys.stdin
        if answer is not None:
            sys.stdin = Terminal(answer + "\n")
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                if expect is SystemExit:
                    with self.assertRaises(SystemExit) as caught:
                        ros.main(argv)
                    code = str(caught.exception)
                else:
                    code = ros.main(argv)
        finally:
            sys.stdin = saved
        if expect is not SystemExit:
            self.assertEqual(code, expect, stdout.getvalue())
        return code, stdout.getvalue(), stderr.getvalue()

    def ros(self, *argv: str, today: date = TODAY, answer: str | None = None) -> dict:
        return json.loads(self.run_ros(*argv, today=today, answer=answer)[1])

    def refusal(self, *argv: str, answer: str | None = None) -> str:
        return self.run_ros(*argv, expect=SystemExit, answer=answer)[0]

    def config(self) -> dict:
        return json.loads((self.tmp / "config" / "ros.json").read_text(encoding="utf-8"))

    def edit_config(self, **changes) -> None:
        self.write("config/ros.json", json.dumps(dict(self.config(), **changes)))

    def ledger(self) -> Ledger:
        return Ledger(self.tmp / self.config()["requirement_ledger"])

    def boundary(self, today: date = TODAY):
        return run_boundary(self.tmp, self.config(), snapshot_builder=build_snapshot, today=today, ask_room=None)

    def open_rules(self, result) -> dict:
        out = {}
        for issue_id, state in result.states["issues"].items():
            if state["status"] in {"open", "deferred"}:
                rule = result.requirements[issue_id]["rule_id"]
                out.setdefault(rule, []).append(issue_id)
        return out

    def add_alpha_judgment(self) -> str:
        pinned = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.write("01_knowledge/papers/j.md", "---\ntitle: Notes\n---\n# Notes\n\n"
                   f"> [!judgment] j-alpha-scope\n> 结论：Do not extend the benchmark\n"
                   f"> 依据：01_knowledge/projects/alpha.md@{pinned}\n> 承诺：alpha\n> 确认：2026-09-19\n")
        return pinned

    def causes(self, rule_id: str = "") -> list:
        """(rule, reason, cause, miss_status) of every transition that created work, in order."""
        registry = self.ledger().requirements()
        rows = []
        for row in self.ledger().trajectory():
            payload = row["payload"]
            if row.get("kind") != "issue_transition" or payload.get("to") != "open" or not payload.get("cause"):
                continue
            rule = registry.get(payload["issue_id"], {}).get("rule_id", "")
            if not rule_id or rule == rule_id:
                rows.append((rule, payload["reason"], payload["cause"], payload["miss_status"]))
        return rows

    def drop_spec(self) -> None:
        ledger = self.ledger()
        cache = json.loads(ledger.cache_path.read_text(encoding="utf-8"))
        cache.pop("spec", None)
        ledger.cache_path.write_text(json.dumps(cache), encoding="utf-8")

    def undecidable(self) -> str:
        """A basis_recheck requirement whose judgment was then removed: evidence cannot decide it."""
        self.add_alpha_judgment()
        self.ros("admit", "--confirm", "j-alpha-scope", answer="y")
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v2\n")
        issue = self.open_rules(self.boundary())["basis_recheck"][0]
        self.write("01_knowledge/papers/j.md", "---\ntitle: Notes\n---\n# Notes\n")
        return issue

    def asks_for(self, issue: str) -> list:
        return [row["payload"] for row in self.ledger().trajectory()
                if row["kind"] == "ask" and issue in row["payload"]["issue_ids"]]

    def question_of(self, issue: str) -> dict:
        return next(q for q in self.ros("today")["questions"] if q["issue_id"] == issue)

    def status_of(self, rule: str, commitment: str) -> tuple:
        result = self.boundary()
        for issue_id, state in result.states["issues"].items():
            registration = result.requirements.get(issue_id, {})
            if registration.get("rule_id") == rule and registration.get("binding") == f"commitment:{commitment}":
                return issue_id, state["status"]
        return "", ""

    def live(self) -> set:
        """cl(n) at the root as the boundary freezes it: the consumer path, not a helper."""
        return set(self.boundary().scope.members)

    def revision_file(self, descriptor: dict, session: str, **changes) -> str:
        revision = {"scope": {"task_types": ["maintenance"]}, "source_episodes": [session],
                    "counterevidence": {"status": "searched_none_found", "refs": [],
                                        "assessment": "no commitment in the last month contradicts it"},
                    "review_date": "2026-12-01T00:00:00+00:00",
                    "retire_trigger": "retire if it opens more than five cancelled requirements in a month"}
        revision.update(changes)
        path = self.tmp / "revision.json"
        path.write_text(json.dumps({"descriptor": descriptor, "revision": revision}), encoding="utf-8")
        return str(path)

    def status_descriptor(self) -> dict:
        return json.loads((self.tmp / "config/extensions/rules/status-verify.json").read_text(encoding="utf-8"))

    def orphaned_judgments(self, *names: str) -> None:
        """Judgments whose basis then disappears: evidence cannot decide them, so each wants a question."""
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        blocks = "".join(f"> [!judgment] j-{name}\n> 结论：{name}\n> 依据：01_knowledge/projects/alpha.md@{pin}\n"
                         f"> 承诺：alpha\n\n" for name in names)
        self.write("01_knowledge/papers/j.md", "---\ntitle: Notes\n---\n# Notes\n\n" + blocks)
        for name in names:
            self.ros("admit", "--confirm", f"j-{name}", answer="y")
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v2\n")
        self.boundary()
        self.write("01_knowledge/papers/j.md", "---\ntitle: Notes\n---\n# Notes\n")

    def asked(self) -> list:
        return [row for row in self.ledger().trajectory() if row.get("kind") == "ask" and row["payload"]["state"] == "asked"]

    def binding(self, issue_id: str) -> str:
        return str(ros.Context(self.tmp, TODAY, "").boundary().requirements.get(issue_id, {}).get("binding", ""))

    def admit_alpha_candidate(self, judgment_id: str) -> dict:
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.write("draft.md", self.RUN_DRAFT.format(id=judgment_id, pin=pin))
        candidate = self.ros("propose", "judgment", "--file", str(self.tmp / "draft.md"),
                             "--target", "commitment:alpha")["candidates"][0]
        return self.ros("admit", candidate)

    def fake_provider(self, output: str = "", ok: bool = True):
        from unittest import mock
        from researchos_adapters.provider_adapter import ProviderExecution
        seen = []

        class Fake:
            def execute(self, request):
                seen.append(request)
                return ProviderExecution("fake", ok, 0 if ok else 1, 0.1, output, "" if ok else "fake_failed")
        return mock.patch.object(ros, "provider_for", lambda config, runtime_scope, provider_id: Fake()), seen

    def repository_files(self) -> dict:
        runtime = ("06_active_context/work_state/", ".researchos/", "draft.md", "answer.md")
        return {str(p.relative_to(self.tmp)): p.read_bytes() for p in self.tmp.rglob("*.md")
                if p.is_file() and not str(p.relative_to(self.tmp)).startswith(runtime)}

    def local_codex(self, output: str = "", ok: bool = True):
        """Stand in for the CLI binary and capture how it would have been launched."""
        from unittest import mock
        seen = {}

        def run(self, args, timeout=90, input_text=None, env=None):
            seen.update({"args": list(args), "env": dict(env or {}), "prompt": input_text or "", "cwd": str(self.root)})
            return {"ok": ok, "returncode": 0 if ok else 1, "seconds": 0.1, "stdout": output}
        return mock.patch.multiple(
            "researchos_adapters.provider_adapter",
            resolve_codex_executable=lambda *a, **k: Path("/nonexistent/codex")), mock.patch(
            "researchos_adapters.command_runner.CommandRunner.run", run), seen

    def propose_beta(self) -> str:
        draft = self.tmp / "draft.md"
        draft.write_text(self.DRAFT, encoding="utf-8")
        return self.ros("propose", "judgment", "--file", str(draft), "--target", self.CARD)["candidates"][0]

    def admit_decisions(self) -> list:
        return [row for row in self.ledger().trajectory()
                if row["kind"] == "decision" and row["payload"]["operation"] in {"admit", "rollback", "retain_if_consistent"}]

    def cancel_unfinished(self, view: dict, keep=()) -> None:
        for row in view["completion"]["unfinished"]:
            if row["issue_id"] not in keep:
                self.ros("decide", row["short_id"], "cancel", "--reason", "not this session", answer="y")

    def capture_ros(self, *argv: str) -> tuple:
        """Capture the JSON and human projections of the SAME boundary (no second observation)."""
        from unittest.mock import patch
        with patch.object(ros, "emit", return_value=0) as output:
            self.run_ros(*argv, json_out=False)
        return output.call_args.args[1:]

    def today_ids(self, view: dict) -> dict:
        return {g["commitment_id"]: g["attention_state"] for g in view["today"]}

    def decision_ids(self, view: dict) -> dict:
        return {g["commitment_id"]: g["attention_state"] for g in view["decision"]}

    def add_commitment(self, block: str) -> None:
        text = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        self.write("06_active_context/research-portfolio.md", text + "\n" + block)

    def context_fixture(self) -> None:
        self.write("01_knowledge/papers/j.md", "---\ntitle: Notes\n---\n> [!judgment] j-s\n> 结论：x\n"
                   "> 依据：01_knowledge/papers/secret.md · alpha-project · 01_knowledge/papers/touchy.md\n> 承诺：alpha\n")
        self.write("01_knowledge/papers/touchy.md", "---\ntitle: Touchy\nsensitivity: sensitive\n---\n# Touchy\nbody\n")

    def receipt_of(self, receipt_id: str) -> dict:
        rows = [r["payload"]["detail"] for r in self.ledger().trajectory()
                if r["payload"].get("detail", {}).get("context_receipt_id") == receipt_id]
        self.assertEqual(len(rows), 1)
        return rows[0]

    def axes(self, receipt: dict, ref: str) -> dict:
        digest_of = hashlib.sha256(ref.encode("utf-8")).hexdigest()
        source = next(row for row in receipt["sources"] if row["ref_digest"] == digest_of)
        return {axis: source[axis]["state"] for axis in ("authorization", "delivery", "exclusion", "egress",
                                                         "observation", "citation")}

    def context(self, *argv: str, env: dict | None = None) -> dict:
        saved = {key: os.environ.pop(key, None) for key in ("CLAUDECODE", "RESEARCHOS_SESSION_SERVICE")}
        os.environ.update(env or {})
        try:
            return self.ros("context", *argv)
        finally:
            for key in ("CLAUDECODE", "RESEARCHOS_SESSION_SERVICE"):
                os.environ.pop(key, None)
                if saved[key] is not None:
                    os.environ[key] = saved[key]

    # judgment blocks ---------------------------------------------------------------------------
    def test_judgment_parser_ignores_fenced_examples_and_reads_english_keys(self) -> None:
        text = "```\n> [!judgment] j-example\n> 结论：x\n```\n> [!judgment] j-real\n> Conclusion: y\n> Basis: a.md@abcdef12, b\n"
        found, problems = parse_judgments(text, "x.md")
        self.assertEqual([j.id for j in found], ["j-real"])
        self.assertEqual([(b.ref, b.version) for b in found[0].basis], [("a.md", "abcdef12"), ("b", "")])
        self.assertEqual(problems, ())
        self.assertNotIn("j-real", strip_judgments(text))

    # boundary -----------------------------------------------------------------------------------
    def test_the_kernel_ledger_takes_the_store_lock_and_fails_closed(self) -> None:
        from unittest import mock
        from researchos_kernel import atomic_files
        ledger = self.ledger()
        self.assertEqual(ledger.lock_path, ledger.path.with_name(f".{ledger.path.name}.lock"), "与服务层同一个兄弟锁文件")
        self.assertEqual(ledger.lock_path, atomic_files.lock_path_for(ledger.path))
        with mock.patch.object(atomic_files, "fcntl", None), self.assertRaises(RuntimeError):
            with ledger.lock():
                pass  # no cross-process lock: refuse instead of writing unguarded
        ledger.path.parent.mkdir(parents=True, exist_ok=True)
        ledger.lock_path.unlink(missing_ok=True)
        ledger.lock_path.symlink_to(self.tmp / "elsewhere.lock")
        with self.assertRaises(OSError):
            with ledger.lock():
                pass  # a lock path that is a symlink is not followed
        self.assertFalse((self.tmp / "elsewhere.lock").exists())

    def test_boundary_is_idempotent_and_rules_fire_on_real_conditions(self) -> None:
        first = self.boundary()
        rules = self.open_rules(first)
        self.assertIn("deadline_warning", rules)          # alpha due in 2 days
        self.assertIn("status_verify", rules)             # beta verified 50 days ago
        self.assertIn("missing_question", rules)          # beta has no question
        self.assertNotIn("gamma", json.dumps([f.commitment_id for f in first.findings.values()]))  # closed ignored
        before = self.ledger().trajectory()
        second = self.boundary()
        after = self.ledger().trajectory()
        self.assertEqual(len(before), len(after), "a boundary over unchanged sources appends nothing")
        self.assertEqual(second.transitions, [])

    # Every finding and check the five script rules produce over a fixture that reaches each branch.
    # issue_id and read_set are persisted (a change re-opens every requirement as a new generation),
    # and summaries, details, options and check reasons are shown or recorded; this pins them all.
    RULE_OUTPUT_DIGEST = "b713b7585b203779e90a1b9fb3305cfbfa0a7f6f6d85cadcd56c4d0b57009e57"

    def test_rule_findings_and_checks_stay_byte_for_byte_the_same(self) -> None:
        from researchos_kernel import rules as rule_table
        fixed = datetime(2026, 9, 1, 12, tzinfo=timezone.utc).timestamp()
        portfolio = PORTFOLIO + ("\n### Delta Overdue\n\n- id: delta\n- responsibility: lead\n- state: mainline\n"
                                 "- question: Is it late?\n- last_verified: 2026-09-15\n- stale_after_days: x\n"
                                 "- deadline: 2026-09-10\n- source_path: 01_knowledge/projects/delta\n")
        self.write("06_active_context/research-portfolio.md", portfolio)
        self.write("01_knowledge/projects/delta/notes.md", "---\ntitle: Delta notes\n---\n# Delta\n")
        self.add_alpha_judgment()
        self.write("01_knowledge/papers/more.md", "---\ntitle: More\n---\n# More\n\n"
                   "> [!judgment] j-unpinned\n> 结论：Unpinned basis\n> 依据：01_knowledge/projects/beta.md\n> 承诺：beta\n\n"
                   "> [!judgment] j-gone\n> 结论：Basis gone\n> 依据：01_knowledge/projects/nowhere.md@abcdef12\n\n"
                   "> [!judgment] j-none\n> 结论：No basis at all\n")
        self.write("01_knowledge/papers/edge.md", "---\ntitle: Edge source\nrelations:\n  - type: supports\n"
                   "    target: 01_knowledge/projects/alpha.md\n    status: confirmed\n    confirmed_versions:\n"
                   "      source: deadbeef\n      target: cafebabe\n  - type: cites\n"
                   "    target: 01_knowledge/projects/beta.md\n    status: confirmed\n---\n# Edge\n")
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v2\n")
        for path in [*(self.tmp / "01_knowledge").rglob("*"), self.tmp / "01_knowledge"]:
            os.utime(path, (fixed, fixed))  # source_changed is read off mtimes: pin them
        config = self.config()
        snapshot = build_snapshot(self.tmp, config)[0]
        rules, _ = rule_table.load_rules(self.tmp, "private", ROOT)
        rows = []
        for today in (TODAY, date(2026, 10, 30)):
            for lang in ("zh-CN", "en"):
                state = {"admitted_judgments": {"j-unpinned": {"old"}}, "confirmed_judgments": {}}
                findings = rule_table.evaluate(snapshot, dict(config, language=lang), rules, state, today)
                for issue_id, f in sorted(findings.items()):
                    rows.append([today.isoformat(), lang, issue_id, f.rule_id, f.rule_version, f.binding_key,
                                 f.read_set, f.read_digest, f.summary, f.details, f.options, f.commitment_id,
                                 f.consequence, f.only_you, f.due_days, f.judgment_id])
            subjects = sorted({f.binding_key for f in findings.values()} | {"commitment:gamma", "commitment:nobody",
                              "judgment:nobody", "edge:01_knowledge/papers/edge.md|cites|01_knowledge/projects/beta.md"})
            for rule_id in sorted(rules):
                for subject in subjects:
                    result, why, code = rule_table.check(snapshot, config, rules[rule_id], subject, state, today)
                    rows.append([today.isoformat(), rule_id, subject, result, why])
                    self.assertEqual(bool(code), result == "unknown", "只有未知结果带原因代码")
        self.assertGreater(len({row[3] for row in rows if len(row) > 5}), 4, "五条规则都要有发现")
        self.assertEqual(digest(rows), self.RULE_OUTPUT_DIGEST)

    # attribution and replay (D5 / CR-6 / CR-16) ------------------------------------------------
    def test_cr6_every_new_requirement_carries_exactly_one_cause(self) -> None:
        self.boundary(today=date(2026, 9, 10))
        opened = [row for row in self.ledger().trajectory() if row.get("kind") == "issue_transition"
                  and row["payload"].get("reason") in {"opened", "reopened", "refreshed"}]
        self.assertTrue(opened)
        self.assertEqual({(r["payload"]["cause"], r["payload"]["miss_status"]) for r in opened},
                         {("initial", "not_applicable")}, "冷启动首次编译：initial，miss 不适用")
        # time: only the calendar moved and the rule declares a day-based trigger.
        self.boundary(today=date(2026, 9, 20))
        self.assertIn(("deadline_warning", "opened", "time", "checked"), self.causes("deadline_warning"))
        # src: a declared input changed.
        self.add_alpha_judgment()
        self.ros("admit", "--confirm", "j-alpha-scope", answer="y")
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v2\n")
        self.boundary()
        self.assertEqual(self.causes("basis_recheck")[-1][2], "src")
        # ver: a rule newly declared, never evaluated before.
        descriptor = json.loads((self.tmp / "config/extensions/rules/status-verify.json").read_text(encoding="utf-8"))
        descriptor.update(id="future_rule", trigger={"when": "future_condition"})  # no evaluator in this kernel
        self.write("config/extensions/rules/future-rule.json", json.dumps(descriptor))
        self.boundary()
        self.assertEqual(self.causes("future_rule")[-1][2], "ver")
        from researchos_kernel.ledger import CAUSES
        contract = ROOT / "09_templates/data_contracts/researchos-canon-obligations-v1.json"
        if contract.is_file():  # the public edition ships no obligations contract
            self.assertEqual(CAUSES, tuple(json.loads(contract.read_text(encoding="utf-8"))["causes"]),
                             "与义务合同共用同一枚举，顺序一致")

    def test_cr6_miss_is_judged_before_any_other_cause(self) -> None:
        from unittest import mock
        from researchos_kernel import rules as rule_table
        kind = "active_lead_commitment_without_question"  # missing_question's trigger
        silent = (lambda *args: [], rule_table.EVALUATORS[kind][1])
        with mock.patch.dict(rule_table.EVALUATORS, {kind: silent}):
            self.boundary()  # the previous boundary evaluated the rule and registered nothing
        self.boundary()
        self.assertEqual(self.causes("missing_question"), [("missing_question", "opened", "miss", "checked")],
                         "前次冻结的规格就能导出却未登记：miss，不被其他来由吸收")

    def test_cr6_scope_growth_is_not_absorbed_by_source_change(self) -> None:
        card = ("---\ntitle: Old study\nepisode_state: {state}\nepisode_closure_receipt: r-old\n---\n# Old\n\n"
                "> [!judgment] j-old\n> 结论：Keep the old split\n> 依据：01_knowledge/projects/beta.md\n")
        self.write("01_knowledge/papers/old.md", card.format(state="closed"))
        self.boundary()
        self.assertEqual(self.causes("confirm_judgment_change"), [], "已关闭情节的键不导出要求")
        # Reopening the episode rewrites its file, so its source version moves too: scope must win.
        self.write("01_knowledge/papers/old.md", card.format(state="open"))
        self.boundary()
        self.assertEqual([row[2] for row in self.causes("confirm_judgment_change")], ["scope"],
                         "情节重开使键回到闭包：归因 scope，不被同时发生的来源变化吸收")

    def test_cr6_unrecomputable_previous_spec_makes_miss_unknown_and_blocks_done(self) -> None:
        self.add_alpha_judgment()  # runs a boundary before writing the new judgment
        ledger = self.ledger()
        cache = json.loads(ledger.cache_path.read_text(encoding="utf-8"))
        cache.pop("spec")  # a boundary written before specs were frozen
        ledger.cache_path.write_text(json.dumps(cache), encoding="utf-8")
        result = self.boundary()
        self.assertIn(("confirm_judgment_change", "opened", "initial", "unknown"), self.causes("confirm_judgment_change"))
        flagged = [i for i, r in result.requirements.items() if r.get("binding") == "spec:previous-unrecomputable"]
        self.assertEqual(len(flagged), 1, "另登记一项「前次规格不可重算」")
        self.assertEqual(result.states["issues"][flagged[0]]["status"], "open")
        self.boundary()
        self.assertEqual(len([r for r in self.ledger().requirements().values()
                              if r.get("binding") == "spec:previous-unrecomputable"]), 1, "只登记一次")

    def test_cr6_registered_work_is_never_labelled_miss_or_initial(self) -> None:
        self.boundary()
        # A new generation whose read set moved through a value outside the source versions (a file time).
        path = self.tmp / "01_knowledge/projects/beta.md"
        later = time.time_ns() + 86_400 * 10**9 * 3
        os.utime(path, ns=(later, later))
        self.boundary()
        refreshed = [row for row in self.causes("status_verify") if row[1] == "refreshed"]
        self.assertTrue(all(row[2] != "miss" and row[3] == "not_applicable" for row in refreshed), refreshed)
        # A coverage requirement whose uncovered set shrinks was registered before: not a miss.
        descriptor = json.loads((self.tmp / "config/extensions/rules/status-verify.json").read_text(encoding="utf-8"))
        self.write("config/extensions/rules/future-rule.json",
                   json.dumps(dict(descriptor, id="future_rule", trigger={"when": "future_condition"})))
        self.boundary()
        self.write("06_active_context/research-portfolio.md", PORTFOLIO.split("### Beta Survey")[0])
        self.boundary()
        self.assertEqual([row[1:] for row in self.causes("future_rule")],
                         [("opened", "ver", "checked"), ("refreshed", "src", "not_applicable")])
        # After losing the spec, a new generation is still judged on its own read set, not called initial.
        self.drop_spec()
        self.write("01_knowledge/projects/beta.md", "---\ntitle: Beta\n---\n# Beta\nmoved\n")
        self.write("06_active_context/research-portfolio.md", PORTFOLIO.replace("2026-08-01", "2026-08-02"))
        self.boundary()
        self.assertEqual(self.causes("status_verify")[-1][1:], ("refreshed", "src", "not_applicable"))

    def test_cr6_unattributed_finding_is_dropped_once_and_never_becomes_a_miss(self) -> None:
        path = self.tmp / "config/extensions/rules/deadline-warning.json"
        descriptor = json.loads(path.read_text(encoding="utf-8"))
        self.write("config/extensions/rules/deadline-warning.json", json.dumps(dict(descriptor, family="system")))
        self.boundary(today=date(2026, 9, 10))
        result = self.boundary(today=date(2026, 9, 20))  # only the date moved, and no time trigger is declared
        self.assertEqual(self.causes("deadline_warning"), [], "七者皆否：不登记")
        self.assertTrue(any("no cause holds" in problem for problem in result.problems), "如实报告")
        before = len(self.ledger().trajectory())
        self.boundary(today=date(2026, 9, 20))
        self.assertEqual(self.causes("deadline_warning"), [], "下一次不把它当作漏检")
        self.assertEqual(len(self.ledger().trajectory()), before, "精确重放仍不追加")

    def test_cr6_one_unrecomputable_requirement_that_reopens_after_it_closes(self) -> None:
        self.add_alpha_judgment()  # runs a boundary first, then writes new work
        self.drop_spec()
        from researchos_kernel.boundary import UNRECOMPUTABLE_ID
        view = self.ros("today")
        self.assertIn(UNRECOMPUTABLE_ID, [row["issue_id"] for row in view["network"]], "在今日里可见")
        self.assertFalse(view["completion"]["done"])
        self.drop_spec()
        self.write("01_knowledge/papers/k.md", "---\ntitle: K\n---\n# K\n\n> [!judgment] j-k\n> 结论：x\n")
        self.boundary()
        rows = [r for r in self.ledger().requirements().values() if r.get("binding") == "spec:previous-unrecomputable"]
        self.assertEqual(len(rows), 1, "仍开着时再次丢失不另登记")
        self.ros("decide", UNRECOMPUTABLE_ID[:10], "cancel", "--reason", "first compile after spec freezing", answer="y")
        self.drop_spec()
        self.write("01_knowledge/papers/m.md", "---\ntitle: M\n---\n# M\n\n> [!judgment] j-m\n> 结论：y\n")
        state = self.boundary().states["issues"][UNRECOMPUTABLE_ID]
        self.assertEqual((state["status"], state["generation"]), ("open", 2), "关闭后再丢失：同一身份重开")

    def test_cr16_exact_replay_adds_no_observation_work_or_question(self) -> None:
        self.undecidable()
        self.ros("today")
        before = self.ledger().trajectory()
        asks = self.ledger().asks()
        self.boundary()
        self.ros("today")
        self.assertEqual(len(self.ledger().trajectory()), len(before), "精确重放：不增加观察、要求或检查")
        self.assertEqual(self.ledger().asks(), asks, "也不重复提问")

    def test_basis_change_opens_then_reconfirm_resolves_and_replay_is_deterministic(self) -> None:
        self.add_alpha_judgment()
        self.ros("admit", "--confirm", "j-alpha-scope", answer="y")
        self.assertNotIn("basis_recheck", self.open_rules(self.boundary()))
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v2\n")
        opened = self.boundary()
        self.assertIn("basis_recheck", self.open_rules(opened))
        view = self.ros("today")
        self.assertTrue(any(g["commitment_id"] == "alpha" for g in view["today"] + view["decision"]))
        self.ros("admit", "--reconfirm", "j-alpha-scope")
        resolved = self.boundary()
        self.assertNotIn("basis_recheck", self.open_rules(resolved))
        self.assertNotIn("confirm_judgment_change", self.open_rules(resolved), "reconfirm is an admission")
        ledger = self.ledger()
        self.assertEqual(ledger.derive_states(), ledger.derive_states(ledger.trajectory()))

    def test_hj11_trigger_disappearance_is_not_a_check(self) -> None:
        """Soul §3：触发条件消失不是检查。要求只在声明的检查对其主体成立时关闭。"""
        self.add_alpha_judgment()
        self.ros("admit", "--confirm", "j-alpha-scope", answer="y")
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v2\n")
        issue = self.open_rules(self.boundary())["basis_recheck"][0]

        # The judgment is removed: the finding disappears, but nothing was checked.
        self.write("01_knowledge/papers/j.md", "---\ntitle: Notes\n---\n# Notes\n")
        result = self.boundary()
        self.assertEqual(result.states["issues"][issue]["status"], "waiting",
                         "主体消失不关闭要求：证据裁不了，以有界问题交给研究者（仍是未关闭要求）")
        absent = [row for row in self.ledger().trajectory() if row["kind"] == "check"
                  and row["payload"]["binding"]["issue_id"] == issue]
        self.assertEqual([row["payload"]["result"] for row in absent], ["unknown"])
        self.assertEqual(absent[0]["payload"]["checked_state_ids"], ["judgment:j-alpha-scope"])
        self.boundary()
        again = [row for row in self.ledger().trajectory() if row["kind"] == "check"
                 and row["payload"]["binding"]["issue_id"] == issue]
        self.assertEqual(len(again), 1, "同一代次只登记一次，重跑不追加")
        self.ros("decide", issue[:10], "cancel", "--reason", "judgment withdrawn", answer="y")
        self.assertEqual(self.boundary().states["issues"][issue]["status"], "cancelled", "由研究者裁定")

    def test_hj6_undecidable_unknown_is_asked_once_and_waits_outside_open_work(self) -> None:
        issue = self.undecidable()
        view = self.ros("today")
        self.assertEqual(self.boundary().states["issues"][issue]["status"], "waiting",
                         "交给研究者：仍是未关闭要求，等待而非待办")
        self.assertEqual([(a["state"], a["options"]) for a in self.asks_for(issue)], [("asked", self.OPTIONS)],
                         "一个问题、有限选项；机械检查不提供「确立满足」（Soul §3）")
        question = next(q for q in view["questions"] if q["issue_id"] == issue)
        self.assertIn("subject_absent", question["why"])
        for _ in range(3):
            self.boundary()
        self.assertEqual(len(self.asks_for(issue)), 1, "同一依据版本只问一次")
        self.assertIn("after today", self.refusal("answer", question["short_id"], "defer", "--until", "2026-09-10"))
        self.assertIn("real date", self.refusal("answer", question["short_id"], "defer", "--until", "2026-02-30"))
        self.ros("answer", question["short_id"], "defer", "--until", "2026-09-25")
        state = self.boundary().states["issues"][issue]
        self.assertEqual((state["status"], state["reopen_trigger"]), ("waiting", "date:2026-09-25"))
        self.assertIn(issue, [row["issue_id"] for row in self.ros("today")["waiting_on_trigger"]], "等待项带触发可见")
        self.assertEqual(self.boundary(today=date(2026, 9, 25)).states["issues"][issue]["status"], "open",
                         "触发点到了才重开")
        self.assertEqual([a["state"] for a in self.asks_for(issue)], ["asked", "answered"], "回答后不再重问")
        descriptor = self.tmp / "config/extensions/rules/basis-recheck.json"
        data = json.loads(descriptor.read_text(encoding="utf-8"))
        data["version"] = "1.1.0"
        self.write("config/extensions/rules/basis-recheck.json", json.dumps(data))
        self.boundary(today=date(2026, 9, 25))
        self.assertEqual([a["state"] for a in self.asks_for(issue)], ["asked", "answered", "asked"], "检查改版才重问")

    def test_each_answer_has_its_own_destination(self) -> None:
        issue = self.undecidable()
        question = self.question_of(issue)
        self.assertIn("not offered", self.refusal("answer", question["short_id"], "satisfied", "--reason", "fine"))
        self.assertIn("needs --reason", self.refusal("answer", question["short_id"], "cancel"))
        answered = self.ros("answer", question["short_id"], "narrow")
        self.assertEqual(answered["permission_state"], "invoker_asserted", "回答如实记录是谁作的决定")
        state = self.boundary().states["issues"][issue]
        self.assertEqual((state["status"], state["reopen_trigger"]), ("waiting", "next_specification"))
        decision = next(r["payload"] for r in reversed(self.ledger().trajectory())
                        if r["kind"] == "decision" and r["payload"]["operation"] == "ask")
        self.assertEqual((decision["issue_id"], decision["detail"]["ask_id"]), (issue, question["ask_id"]),
                         "决定绑定到要求与问题")

    def test_a_question_is_neither_duplicated_nor_lost(self) -> None:
        issue = self.undecidable()
        first = self.question_of(issue)
        # The same code with different wording is the same question (class keys on the reason code).
        self.boundary()
        self.assertEqual(len([a for a in self.asks_for(issue) if a["state"] == "asked"]), 1)
        # Moving the requirement off its question some other way withdraws the question.
        self.ros("decide", issue[:10], "reopen")
        self.assertEqual([a["state"] for a in self.asks_for(issue)], ["asked", "withdrawn"], "不留悬空的问题")
        # Still undecidable, so it is asked again rather than left open without a question.
        self.boundary()
        self.assertEqual([a["state"] for a in self.asks_for(issue)], ["asked", "withdrawn", "asked"])
        self.assertEqual(self.question_of(issue)["ask_id"], first["ask_id"])

    def test_a_source_fixable_unknown_stays_open_work_instead_of_a_question(self) -> None:
        text = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        issue = self.open_rules(self.boundary())["status_verify"][0]
        self.write("06_active_context/research-portfolio.md", text.replace("- last_verified: 2026-08-01",
                                                                          "- last_verified: unknown"))
        state = self.boundary().states["issues"][issue]
        self.assertEqual(state["status"], "open", "字段读不出是来源可修的问题，不是研究者才能裁的未知")
        self.assertEqual(self.asks_for(issue), [])

    def test_cc3_unknown_check_never_resolves_and_stays_apart_from_coverage_unknown(self) -> None:
        issue = self.undecidable()
        self.boundary()
        rows = [r["payload"] for r in self.ledger().trajectory() if r["kind"] == "check"
                and r["payload"]["binding"]["issue_id"] == issue]
        self.assertEqual([r["result"] for r in rows], ["unknown"], "未知不写成满足")
        self.assertNotEqual(self.boundary().states["issues"][issue]["status"], "resolved", "未知不关闭要求")
        question = next(q for q in self.ros("today")["questions"] if q["issue_id"] == issue)
        self.ros("answer", question["short_id"], "unsatisfied")
        self.assertEqual(self.boundary().states["issues"][issue]["status"], "open", "确立不满足：回到待办，是真实工作")
        # Coverage unknown is a different kind: a disabled rule gives not_evaluated and asks nothing.
        descriptor = self.tmp / "config/extensions/rules/status-verify.json"
        data = json.loads(descriptor.read_text(encoding="utf-8"))
        data["enabled"] = False
        self.write("config/extensions/rules/status-verify.json", json.dumps(data))
        self.boundary()
        status = [r["payload"] for r in self.ledger().trajectory() if r["kind"] == "check"
                  and r["payload"]["requirement_id"] == "status_verify"]
        self.assertTrue(status and {r["result"] for r in status} == {"not_evaluated"}, "覆盖未知不写成证据未知")
        self.assertFalse(any(a["detail"].get("rule_id") == "status_verify" for a in
                             (r["payload"] for r in self.ledger().trajectory() if r["kind"] == "ask")), "覆盖未知不提问")

    def test_a_requirement_closes_on_its_declared_check_bound_to_the_current_version(self) -> None:
        self.add_alpha_judgment()
        self.ros("admit", "--confirm", "j-alpha-scope", answer="y")
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v2\n")
        issue = self.open_rules(self.boundary())["basis_recheck"][0]
        self.ros("admit", "--reconfirm", "j-alpha-scope")
        result = self.boundary()
        self.assertEqual(result.states["issues"][issue]["status"], "resolved")
        met = [row["payload"] for row in self.ledger().trajectory() if row["kind"] == "check"
               and row["payload"]["binding"]["issue_id"] == issue and row["payload"]["result"] == "met"]
        self.assertEqual(len(met), 1)
        self.assertIn("basis_versions_current", met[0]["basis"], "检查写明规则声明的检查")
        self.assertIn("pinned to its current version", met[0]["basis"], "并写明求值结果，而不只是名字")
        self.assertEqual(met[0]["checked_state_ids"], ["judgment:j-alpha-scope"])
        current = result.snapshot.judgments["j-alpha-scope"].block_hash
        row = next(row for row in self.ledger().trajectory() if row["kind"] == "check"
                   and row["payload"]["binding"]["issue_id"] == issue and row["payload"]["result"] == "met")
        self.assertEqual(row["evidence_ids"], [f"judgment:j-alpha-scope@{current}"], "证据是主体的当前版本")

    def test_a_finding_that_disappears_for_another_reason_does_not_pass_its_check(self) -> None:
        """复核反例：承诺停用、职责改变都会让提醒消失，但检查并没有成立。"""
        portfolio = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        issue, status = self.status_of("status_verify", "beta")
        self.assertEqual(status, "open")
        self.write("06_active_context/research-portfolio.md", portfolio.replace("- state: waiting", "- state: paused"))
        self.assertEqual(self.status_of("status_verify", "beta"), (issue, "open"), "停用不等于已核实")
        unmet = [row["payload"] for row in self.ledger().trajectory() if row["kind"] == "check"
                 and row["payload"]["binding"]["issue_id"] == issue and row["payload"]["result"] == "unmet"]
        self.assertEqual(len(unmet), 1)
        self.assertIn("beyond", unmet[0]["basis"])
        view = self.ros("today", "--all")
        self.assertIn(issue[:10], json.dumps(view), "未成立的要求仍然可见")
        self.boundary()
        again = [row for row in self.ledger().trajectory() if row["kind"] == "check"
                 and row["payload"]["binding"]["issue_id"] == issue and row["payload"]["result"] == "unmet"]
        self.assertEqual(len(again), 1, "重跑不追加")

        text = portfolio.replace("### Beta Survey\n\n- id: beta\n- responsibility: lead",
                                 "### Beta Survey\n\n- id: beta\n- responsibility: support")
        issue, status = self.status_of("missing_question", "beta")
        self.assertEqual(status, "open")
        self.write("06_active_context/research-portfolio.md", text)
        self.assertEqual(self.status_of("missing_question", "beta"), (issue, "open"), "改职责不等于写了问题")

    def test_coverage_requirements_are_stable_across_replays(self) -> None:
        descriptor = json.loads((self.tmp / "config/extensions/rules/status-verify.json").read_text(encoding="utf-8"))
        descriptor.update(id="future_rule", trigger={"when": "future_condition"})  # no evaluator in this kernel
        self.write("config/extensions/rules/future-rule.json", json.dumps(descriptor))
        self.boundary()
        counts = []
        for _ in range(3):
            self.boundary()
            counts.append(len(self.ledger().trajectory()))
        self.assertEqual(counts[0], counts[-1], "未变的来源上重跑不追加任何记录")
        coverage = [state["status"] for issue, state in self.boundary().states["issues"].items()
                    if self.boundary().requirements.get(issue, {}).get("binding") == "coverage:future_rule"]
        self.assertEqual(coverage, ["open"], "不可执行的规则留下的覆盖未知不被关闭")

    def test_a_b_a_reopens_and_generation_advances_on_new_read_set(self) -> None:
        self.add_alpha_judgment()
        self.ros("admit", "--confirm", "j-alpha-scope", answer="y")
        original = (self.tmp / "01_knowledge/projects/alpha.md").read_text(encoding="utf-8")
        self.write("01_knowledge/projects/alpha.md", original + "B\n")
        issue = self.open_rules(self.boundary())["basis_recheck"][0]
        self.write("01_knowledge/projects/alpha.md", original)          # back to A: condition gone
        result = self.boundary()
        self.assertEqual(result.states["issues"][issue]["status"], "resolved")
        self.write("01_knowledge/projects/alpha.md", original + "B\n")   # B again: reopened
        result = self.boundary()
        self.assertEqual(result.states["issues"][issue]["status"], "open")
        self.assertEqual(result.states["issues"][issue]["generation"], 2)
        self.write("01_knowledge/projects/alpha.md", original + "C\n")   # new read set while open
        self.assertEqual(self.boundary().states["issues"][issue]["generation"], 3)

    def test_unadmitted_judgment_is_detected_without_rollback_and_confirm_closes_it(self) -> None:
        self.add_alpha_judgment()
        self.assertIn("confirm_judgment_change", self.open_rules(self.boundary()))
        self.assertTrue((self.tmp / "01_knowledge/papers/j.md").read_text(encoding="utf-8").count("[!judgment]"))
        self.ros("admit", "--confirm", "j-alpha-scope", answer="y")
        self.assertNotIn("confirm_judgment_change", self.open_rules(self.boundary()))
        text = (self.tmp / "01_knowledge/papers/j.md").read_text(encoding="utf-8")
        self.write("01_knowledge/papers/j.md", text.replace("Do not extend", "Extend"))
        self.assertIn("confirm_judgment_change", self.open_rules(self.boundary()), "an edited block needs confirmation again")

    def test_propose_and_admit_writes_block_into_commitment_without_changing_its_version(self) -> None:
        version_before = self.boundary().snapshot.commitments["alpha"].version
        draft = self.tmp / "draft.md"
        draft.write_text("> [!judgment] j-alpha-next\n> 结论：Occlusion first\n> 依据：alpha-project · commitment:alpha\n"
                         "> 放弃的选项：Scale data\n", encoding="utf-8")
        candidate = self.ros("propose", "judgment", "--file", str(draft), "--target", "commitment:alpha")["candidates"][0]
        landed = self.ros("admit", candidate)
        self.assertEqual(landed["path"], "06_active_context/research-portfolio.md")
        result = self.boundary()
        judgment = result.snapshot.judgments["j-alpha-next"]
        self.assertEqual(result.snapshot.commitment_for_judgment(judgment), "alpha")
        self.assertTrue(all(b.version for b in judgment.basis), "basis is pinned on admission")
        self.assertEqual(result.snapshot.commitments["alpha"].version, version_before)
        self.assertIn("j-alpha-next", result.snapshot.commitments["alpha"].judgment_ids())
        rules = self.open_rules(result)
        self.assertNotIn("confirm_judgment_change", rules)
        self.assertNotIn("basis_recheck", rules)
        self.assertIn("already admitted", self.refusal("admit", candidate))

    # rule revision (HJ-5 / HJ-5b / CA-8) --------------------------------------------------------------
    def test_hj5b_rule_revision_records_its_provenance_or_is_refused(self) -> None:
        session = self.ros("today")["session_id"]
        revised = dict(self.status_descriptor(), version="1.1.0")
        self.assertIn("counterevidence", self.refusal("propose", "rule", "--file", self.revision_file(
            revised, session, counterevidence=None)), "缺反例记录不成立")
        self.assertIn("sessions recorded here", self.refusal("propose", "rule", "--file", self.revision_file(
            revised, "session-that-never-was")), "来源 episode 必须真实存在")
        self.assertIn("raise the version", self.refusal("propose", "rule", "--file", self.revision_file(
            dict(revised, version="1.0.0"), session)))
        self.assertIn("rollback_target", self.refusal("propose", "rule", "--file", self.revision_file(
            revised, session, rollback_target="status_verify@0.9.0")))
        cid = self.ros("propose", "rule", "--file", self.revision_file(revised, session))["candidates"][0]
        record = self.ledger().candidates()[cid]["payload"]["revision"]
        self.assertEqual((record["source_episodes"], record["rollback_target"], record["authority"]),
                         ([session], "status_verify@1.0.0", "candidate_only"))
        self.assertEqual(self.status_descriptor()["version"], "1.0.0", "提议不改规则")
        self.assertIn("researcher's terminal", self.refusal("admit", cid), "规则修订只在研究者终端准入，Agent 只能提议")
        done = self.ros("admit", cid, answer="y")
        self.assertEqual((self.status_descriptor()["version"], done["applies_from"]), ("1.1.0", "next_session"))
        effect = [r["payload"] for r in self.ledger().trajectory() if r.get("kind") == "effect"][-1]
        version = effect["detail"]["rule_version"]
        self.assertEqual((version["supersedes"], version["review_date"][:10]), (["status_verify@1.0.0"], "2026-12-01"))
        self.assertTrue(version["human_disposition_ref"])
        self.assertIn("already admitted", self.refusal("admit", cid))

    def test_ca8_a_revision_does_not_judge_its_own_adoption_or_this_session(self) -> None:
        session = self.ros("today")["session_id"]
        stale = self.ros("propose", "rule", "--file", self.revision_file(
            dict(self.status_descriptor(), version="1.1.0"), session))["candidates"][0]
        self.write("config/extensions/rules/status-verify.json",
                   json.dumps(dict(self.status_descriptor(), summary_en="edited by hand meanwhile")))
        self.assertIn("changed since this revision was proposed", self.refusal("admit", stale, answer="y"),
                      "候选只能修订它提议时的那一版")
        # A new rule adopted mid-session: its work belongs to the next session, not this one's Out.
        strict = dict(self.status_descriptor(), id="verify_strict", version="1.0.0")
        cid = self.ros("propose", "rule", "--file", self.revision_file(strict, session))["candidates"][0]
        self.ros("admit", cid, answer="y")
        checks = [r["payload"] for r in self.ledger().trajectory() if r.get("kind") == "check"
                  and r["payload"].get("requirement_id") == "rule_revision_admission"]
        self.assertEqual(len(checks), 1)
        self.assertIn("candidate's own checks were not evaluated", checks[0]["basis"])
        self.boundary()  # the new rule now runs and registers its work
        closed = self.ros("close")
        later = [row["issue_id"] for row in closed["completion"]["next_episode"]]
        self.assertTrue(later, "本次会话开始后才生效的规则，其要求属于下一次")
        self.assertNotIn(later[0], [row["issue_id"] for row in closed["completion"]["unfinished"]])

    def test_p5_work_open_at_start_stays_counted_whatever_happens_to_its_rule(self) -> None:
        session = self.ros("today")["session_id"]
        before = {row["issue_id"] for row in self.ros("today")["completion"]["unfinished"]}
        disabled = dict(self.status_descriptor(), version="1.1.0", enabled=False)
        cid = self.ros("propose", "rule", "--file", self.revision_file(disabled, session))["candidates"][0]
        self.ros("admit", cid, answer="y")
        closed = self.ros("close")
        self.assertEqual({row["issue_id"] for row in closed["completion"]["unfinished"]}, before,
                         "开始时就开着的要求始终属于本次，规则被停用也不让它消失")
        self.assertEqual(closed["completion"]["next_episode"], [])
        from researchos_kernel.boundary import completion
        from researchos_kernel.scope import FrozenScope
        states = {"x": {"status": "open", "generation": 1, "rule_version": "9", "summary": ""}}
        report = completion(states, {"x": {"rule_id": "r", "binding": "a.md"}},
                            FrozenScope(node="/", members=frozenset({"a.md"})), today=TODAY,
                            frozen_rules={}, open_at_start={})
        self.assertEqual([r["issue_id"] for r in report["unfinished"]], ["x"], "开始时规则集读不出：不挪任何工作")
        refreshed = {"x": {"status": "open", "generation": 2, "rule_version": "1.1.0", "summary": ""}}
        report = completion(refreshed, {"x": {"rule_id": "r", "binding": "a.md"}},
                            FrozenScope(node="/", members=frozenset({"a.md"})), today=TODAY,
                            frozen_rules={"r": "1.0.0"}, open_at_start={"x": 1})
        self.assertEqual([r["issue_id"] for r in report["unfinished"]], ["x"], "开始时开着的，被新版本刷新也仍属本次")

    def test_rule_admission_is_undone_when_it_cannot_be_recorded_and_files_are_not_taken(self) -> None:
        from unittest import mock
        session = self.ros("today")["session_id"]
        cid = self.ros("propose", "rule", "--file", self.revision_file(
            dict(self.status_descriptor(), version="1.1.0"), session))["candidates"][0]
        original = self.status_descriptor()

        def broken(*args, **kwargs):
            raise OSError("disk full")
        from researchos_kernel.ledger import Ledger
        with mock.patch.object(Ledger, "effect", broken):
            self.assertIn("rolled back", self.refusal("admit", cid, answer="y"))
        self.assertEqual(self.status_descriptor(), original, "记不下来就撤回，规则文件回到原样")
        rows = self.ledger().trajectory()
        self.assertTrue(any(r.get("kind") == "attempt" and r["payload"]["status"] == "failed"
                            and r["payload"]["detail"].get("transaction_id") for r in rows),
                        "账上记下这次修订失败，而不是停在「已写入」")
        self.assertFalse(any(c.get("change") == "rule_revised" for r in rows if r.get("kind") == "effect"
                             for c in r["payload"]["changes"]))
        self.assertIn("below 1000", self.refusal("propose", "rule", "--file", self.revision_file(
            dict(self.status_descriptor(), version="1.1000.0"), session)))
        self.write("config/extensions/rules/foo-bar.json", json.dumps(dict(self.status_descriptor(), id="foobar")))
        self.assertIn("declares another rule", self.refusal("propose", "rule", "--file", self.revision_file(
            dict(self.status_descriptor(), id="foo_bar"), session)), "新规则不能占用另一条规则的文件")

    def test_judgment_and_closure_admissions_are_undone_and_journaled_when_they_cannot_be_recorded(self) -> None:
        from unittest import mock

        def broken(*args, **kwargs):
            raise OSError("disk full")
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.write("draft.md", self.RUN_DRAFT.format(id="unrecorded", pin=pin))
        judgment = self.ros("propose", "judgment", "--file", str(self.tmp / "draft.md"),
                            "--target", "commitment:alpha")["candidates"][0]
        self.write(self.EPISODE, self.EPISODE_TEXT)
        closure = self.ros("propose", "episode-close", "--target", self.EPISODE, "--reason", "round ended")["candidates"][0]
        for candidate, path in ((judgment, "06_active_context/research-portfolio.md"), (closure, self.EPISODE)):
            with self.subTest(path=path):
                before = (self.tmp / path).read_bytes()
                with mock.patch.object(ros, "_record_candidate_state", broken):
                    self.assertIn("could not be recorded (disk full)", self.refusal("admit", candidate))
                self.assertEqual((self.tmp / path).read_bytes(), before, "记不下来就撤回，文件回到原样")
                rows = self.ledger().trajectory()
                failed = [r["payload"]["detail"]["transaction_id"] for r in rows
                          if r.get("kind") == "attempt" and r["payload"]["status"] == "failed"]
                undone = [r["payload"]["detail"]["transaction_id"] for r in rows if r.get("kind") == "effect"
                          and r["payload"]["changes"][0]["change"] == "writeback_rolled_back"]
                self.assertTrue(failed and failed[-1] in undone, "回滚记入账本：失败的尝试加回滚效果")
        self.assertNotIn("j-unrecorded", self.ledger().derive_states()["admitted_judgments"],
                         "已回滚的写入不算准入，同一块粘回来也要确认")
        self.assertTrue(all(row["revoked"] for row in self.ledger().closure_receipts().values()), "回执随回滚作废")
        self.assertNotIn(self.EPISODE, {key for key, place in self.boundary().placements.items() if place.closed})
        self.assertEqual(self.ros("admit", judgment)["admission_state"]["mutation_state"], "applied", "候选仍可再准入")
        self.assertTrue(self.ros("admit", closure)["closure_receipt"])

    def test_reconfirm_never_admits_a_block_edited_since_its_admission(self) -> None:
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        draft = self.tmp / "draft.md"
        draft.write_text(self.RUN_DRAFT.format(id="kept", pin=pin), encoding="utf-8")
        cid = self.ros("propose", "judgment", "--file", str(draft), "--target", "01_knowledge/projects/beta.md")["candidates"][0]
        landed = self.ros("admit", cid)
        path = self.tmp / landed["path"]
        path.write_text(path.read_text(encoding="utf-8").replace("do not transfer yet", "transfer fully"), encoding="utf-8")
        self.assertIn("never admitted or confirmed", self.refusal("admit", "--reconfirm", "j-kept"),
                      "手改过的判断块不能借 reconfirm 变成准入")

    def test_cc6_episode_spec_is_frozen_and_scan_stays_inside_it(self) -> None:
        view = self.ros("today")
        spec = view["spec"]
        self.assertEqual(spec["schema_id"], "researchos-episode-spec-v1")
        for part in ("purpose", "context", "scope_declaration", "rules", "preserve", "authorization", "budget",
                     "scope_extension", "source_versions", "declared_digest"):
            self.assertIn(part, spec, f"Φ_ε 含 {part}")
        self.assertEqual(spec["budget"], {"boundaries": 200, "boundaries_source": "kernel_default"},
                         "预算没声明：强制分量 β^bnd 用内核默认值，并如实注明来源")
        self.assertIn("commitment:responsibility", spec["preserve"])
        stored = [r for r in self.ledger().records("episodes") if r.get("episode_id") == view["session_id"]][0]
        self.assertEqual(stored["detail"]["spec"], spec, "规格随会话开始记录冻结")
        # A rule revised mid-session: the running episode keeps its spec; the next one takes the new one.
        cid = self.ros("propose", "rule", "--file", self.revision_file(
            dict(self.status_descriptor(), version="1.1.0"), view["session_id"]))["candidates"][0]
        self.ros("admit", cid, answer="y")
        again = self.ros("today")
        self.assertEqual(again["session_id"], view["session_id"])
        self.assertEqual(again["spec"]["rules"]["status_verify"], "1.0.0", "运行中的会话不改规格")
        self.assertEqual(again["spec_changes_pending"], ["rules"], "改变的分量如实列出")
        self.ros("close")
        fresh = self.ros("today")
        self.assertNotEqual(fresh["session_id"], view["session_id"])
        self.assertEqual(fresh["spec"]["rules"]["status_verify"], "1.1.0", "规格改变形成新的 episode")
        self.assertNotEqual(fresh["spec"]["declared_digest"], spec["declared_digest"])
        # A focused episode scans inside its own scope: another commitment's work is not its work.
        focused = self.ros("today", "--for", "alpha")
        self.assertEqual(focused["spec"]["scope_declaration"]["narrowed_by"], "commitment:alpha")
        registry = self.boundary().requirements
        mine = [r for r in focused["completion"]["unfinished"]
                if not registry[r["issue_id"]].get("binding", "").startswith("coverage:")]
        self.assertTrue(mine)
        self.assertTrue(all(registry[r["issue_id"]].get("commitment_id") in {"alpha", ""} for r in mine),
                        "收窄的会话只算自己承诺的工作")
        self.assertGreater(focused["completion"]["out_of_scope_open"] + focused["completion"]["unowned_open"], 0)

    def test_cc6_a_focused_session_counts_only_what_falls_inside_it(self) -> None:
        self.assertIn("unknown commitment", self.refusal("today", "--for", "nope"), "不存在的承诺不开会话")
        self.write("01_knowledge/projects/beta.md", "---\ntitle: Beta\n---\n# Beta\n\n"
                   "> [!judgment] j-beta-only\n> 结论：Beta waits\n> 承诺：beta\n")
        descriptor = dict(self.status_descriptor(), id="beta_judgments_unevaluated", evaluates=["judgments"],
                          trigger={"when": "future_condition"})  # declared, but no evaluator in this kernel
        self.write("config/extensions/rules/beta-judgments-unevaluated.json", json.dumps(descriptor))
        focused = self.ros("today", "--for", "alpha")
        registry = self.boundary().requirements
        coverage = [r for r in focused["completion"]["unfinished"]
                    if registry[r["issue_id"]].get("binding") == "coverage:beta_judgments_unevaluated"]
        self.assertEqual(coverage, [], "未评估规则的域不落在本会话范围内，就不挡本次完成")
        whole = self.ros("today")
        self.assertTrue([r for r in whole["completion"]["unfinished"]
                         if registry[r["issue_id"]].get("binding") == "coverage:beta_judgments_unevaluated"],
                        "全范围会话照旧计入")
        members = json.loads(next(self.tmp.rglob(f"sessions/{focused['session_id']}.json")).read_text())["scope_members"]
        self.assertNotIn("06_active_context/research-portfolio.md", members, "组合清单承载所有承诺，不进收窄范围")
        self.assertEqual(focused["spec"]["ask_cap"], {"declared": False}, "没声明提问上限就照实记")
        self.assertTrue(focused["spec"]["source_versions"]["decision_point"], "sv 连到边界的决策截点")
        closed = self.ros("close", "--for", "alpha")
        episode = [r for r in self.ledger().records("episodes") if r.get("end")][-1]
        self.assertEqual(episode["detail"]["budget"]["boundaries"], 200)
        self.assertEqual(episode["detail"]["budget_exhausted"], [])
        self.assertEqual(closed["session_id"], focused["session_id"])

    def test_cc10_ask_cap_holds_from_the_opening_boundary(self) -> None:
        self.edit_config(episode_budget=dict(boundaries=50, asks=1))
        self.orphaned_judgments("one", "two")  # both become undecidable at the session's opening boundary
        view = self.ros("today")
        self.assertEqual(view["spec"]["budget"], {"boundaries": 50, "asks": 1}, "声明的预算随规格冻结")
        self.assertEqual(view["spec"]["ask_cap"], {"asks": 1})
        self.assertEqual(len(self.asked()), 1, "开场边界已属于新会话：提问上限 1 只问一个")
        self.assertEqual(view["budget"]["spent"]["asks"], 1, "开场问的也记在本会话账上，不因同一秒而漏记")
        self.assertIn("asks", view["budget"]["exhausted"])
        self.ros("today")
        self.assertEqual(len(self.asked()), 1, "上限已满：之后的边界也不再问")
        capped = [p for p in ros.Context(self.tmp, TODAY, "").boundary().problems if "ask budget is spent" in p]
        self.assertTrue(capped, "另一个留作待办，并如实报告上限已用尽")
        closed = self.ros("close")
        self.assertEqual(closed["outcome"], "budget_stopped", "未完成且预算用尽：记为 budget_stopped，不是研究者喊停")

    def test_cc10_waiting_spends_boundaries_and_an_exhausted_session_stops(self) -> None:
        self.edit_config(episode_budget=dict(boundaries=3))
        for _ in range(5):  # nothing changes between these: waiting is still a boundary each time
            view = self.ros("today")
        self.assertEqual(view["budget"]["spent"]["boundaries"], 3, "用尽后不再记账：计数停在上限")
        self.assertEqual(view["budget"]["exhausted"], ["boundaries"])
        self.assertIn(ros.t("zh-CN", "budget.stopped", session=view["session_id"]).split("，")[0],
                      self.run_ros("today", json_out=False, lang="zh-CN")[1])
        self.orphaned_judgments("one")
        self.ros("today")
        self.assertEqual(self.asked(), [], "预算用尽的会话不再提问")
        self.assertEqual(self.ros("close")["outcome"], "budget_stopped")

    def test_cc10_spend_is_charged_to_its_own_session_only(self) -> None:
        self.edit_config(episode_budget=dict(boundaries=20, asks=5))
        first = self.ros("today", today=date(2026, 9, 18))["session_id"]
        for day in (19, 19, 19, 19, 19):  # later days do not spend an earlier day's session
            self.ros("today", today=date(2026, 9, day))
        self.ros("close", today=date(2026, 9, 19))
        stale = self.ros("close", "--session", first, today=date(2026, 9, 19))
        self.assertEqual(stale["outcome"], "human_stopped", "前一天的会话不被之后的边界耗尽")
        episode = [r for r in self.ledger().records("episodes") if r.get("episode_id") == first and r.get("end")][-1]
        self.assertEqual(episode["detail"]["budget_spent"]["boundaries"], 1, "只记它自己那天的开场边界")
        # Two sessions open at once: a question outside the narrowed one is not charged to it.
        whole = self.ros("today")["session_id"]
        narrow = self.ros("today", "--for", "beta")["session_id"]
        self.orphaned_judgments("one")  # about alpha
        self.ros("today")
        self.assertEqual(len(self.asked()), 1)
        self.assertEqual(ros._session_account(ros.Context(self.tmp, TODAY, ""), whole)[1]["asks"], 1)
        self.assertEqual(ros._session_account(ros.Context(self.tmp, TODAY, ""), narrow)[1]["asks"], 0,
                         "收窄到 beta 的会话不为 alpha 的问题付账")

    def test_cc10_budget_config_is_validated_and_legacy_sessions_are_bounded(self) -> None:
        self.edit_config(episode_budget=dict(boundaries=0, asks="3", reopens=2, calls=9))
        view = self.ros("today")
        self.assertEqual(view["budget"]["limits"],
                         {"boundaries": 200, "reopens": 2, "boundaries_source": "kernel_default"})
        problems = "\n".join(view["budget"]["problems"])
        for key in ("boundaries", "asks", "calls"):
            self.assertIn(f"episode_budget.{key}", problems, "不合法的值不静默丢弃，要报告")
        ctx = ros.Context(self.tmp, TODAY, "")
        ctx.ledger.episode("legacy", start="2026-09-19T00:00:00+00:00",
                           detail={"day": TODAY.isoformat(), "spec": {"budget": {"declared": False}}})
        from researchos_kernel.boundary import DEFAULT_BOUNDARY_BUDGET
        self.assertEqual(ros._session_account(ctx, "legacy")[0]["boundaries"], DEFAULT_BOUNDARY_BUDGET,
                         "旧会话没冻结 β^bnd：today 与 close 都按内核默认计")
        with self.assertRaises(TypeError):
            run_boundary(self.tmp, self.config(), snapshot_builder=build_snapshot, today=TODAY)  # ask_room must be stated

    # a judgment-class field written directly (HJ-12) -------------------------------------------
    def test_admission_rejects_a_draft_pinned_to_an_old_basis(self) -> None:
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.write("draft.md", self.RUN_DRAFT.format(id="old-basis", pin=pin))
        self.write("01_knowledge/projects/alpha.md", "# Alpha\nEvidence v2\n")
        before = self.ledger().candidates()
        self.assertIn("basis version changed", self.refusal(
            "propose", "judgment", "--file", str(self.tmp / "draft.md"), "--target", "commitment:alpha"))
        self.assertEqual(before, self.ledger().candidates())

    def test_proposal_freezes_unpinned_basis_and_admit_rejects_later_change(self) -> None:
        self.write("draft.md", "> [!judgment] j-pinned\n> Conclusion: Compare first\n"
                   "> Basis: 01_knowledge/projects/alpha.md\n")
        candidate = self.ros("propose", "judgment", "--file", str(self.tmp / "draft.md"),
                             "--target", "commitment:alpha")["candidates"][0]
        stored = self.ledger().candidates()[candidate]["payload"]["judgment"]
        self.assertTrue(stored["basis"][0][1], "the candidate must bind the observed version")
        before = (self.tmp / "06_active_context/research-portfolio.md").read_bytes()
        self.write("01_knowledge/projects/alpha.md", "# Alpha\nEvidence v2\n")
        self.assertIn("basis version changed", self.refusal("admit", candidate))
        self.assertEqual(before, (self.tmp / "06_active_context/research-portfolio.md").read_bytes())
        self.assertNotEqual("applied", self.ledger().candidates()[candidate]["payload"]["admission_state"]["mutation_state"])

    def test_admission_does_not_overwrite_an_edit_after_planning(self) -> None:
        from unittest import mock
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.write("draft.md", self.RUN_DRAFT.format(id="concurrent", pin=pin))
        candidate = self.ros("propose", "judgment", "--file", str(self.tmp / "draft.md"),
                             "--target", "commitment:alpha")["candidates"][0]
        path = self.tmp / "06_active_context/research-portfolio.md"
        changed = path.read_text(encoding="utf-8") + "\nA concurrent author's note.\n"
        original = ros.plan_admit
        def interleaved(*args, **kwargs):
            planned = original(*args, **kwargs)
            self.write("06_active_context/research-portfolio.md", changed)
            return planned
        with mock.patch.object(ros, "plan_admit", side_effect=interleaved):
            self.assertIn("preimage_conflict", self.refusal("admit", candidate))
        self.assertEqual(changed, path.read_text(encoding="utf-8"))
        self.assertNotEqual("applied", self.ledger().candidates()[candidate]["payload"]["admission_state"]["mutation_state"])

    def test_reconfirm_and_episode_closure_also_reject_interleaved_edits(self) -> None:
        from unittest import mock
        self.admit_alpha_candidate("reconfirm-race")
        candidate = None
        for operation in ("reconfirm", "episode"):
            with self.subTest(operation=operation):
                if operation == "episode":
                    self.write(self.EPISODE, self.EPISODE_TEXT)
                    candidate = self.ros("propose", "episode-close", "--target", self.EPISODE,
                                         "--reason", "fictional round ended")["candidates"][0]
                    owner, path = "plan_episode_close", self.tmp / self.EPISODE
                    argv = ("admit", candidate)
                else:
                    owner, path = "plan_reconfirm", self.tmp / "06_active_context/research-portfolio.md"
                    argv = ("admit", "--reconfirm", "j-reconfirm-race")
                original = getattr(ros, owner)
                changed = path.read_bytes() + b"\nIndependent note.\n"
                def interleaved(*args, **kwargs):
                    planned = original(*args, **kwargs)
                    path.write_bytes(changed)
                    return planned
                with mock.patch.object(ros, owner, side_effect=interleaved):
                    self.assertIn("preimage_conflict", self.refusal(*argv))
                self.assertEqual(changed, path.read_bytes())

    def test_new_admission_preserves_crlf_source_outside_the_added_block(self) -> None:
        path = self.tmp / "01_knowledge/projects/alpha.md"
        before = b"---\r\ntitle: Alpha\r\n---\r\n# Alpha\r\nEvidence.\r\n"
        path.write_bytes(before)
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.write("draft.md", self.RUN_DRAFT.format(id="crlf", pin=pin))
        candidate = self.ros("propose", "judgment", "--file", str(self.tmp / "draft.md"),
                             "--target", "01_knowledge/projects/alpha.md")["candidates"][0]
        self.ros("admit", candidate)
        self.assertTrue(path.read_bytes().startswith(before), "existing source line endings must not be normalized")

    def test_public_copy_fallback_refuses_stale_basis_without_writing(self) -> None:
        self.edit_config(runtime_scope="public_starter")
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.write("draft.md", self.RUN_DRAFT.format(id="public-stale", pin=pin))
        candidate = self.ros("propose", "judgment", "--file", str(self.tmp / "draft.md"),
                             "--target", "commitment:alpha")["candidates"][0]
        before = (self.tmp / "06_active_context/research-portfolio.md").read_bytes()
        planned = self.ros("admit", candidate)
        self.assertFalse(planned["promoted"])
        self.write("01_knowledge/projects/alpha.md", "# Alpha\nChanged evidence\n")
        self.assertIn("basis version changed", self.refusal("admit", candidate))
        self.assertEqual(before, (self.tmp / "06_active_context/research-portfolio.md").read_bytes())

    def test_missing_or_unknown_runtime_scope_runs_as_the_copy_only_public_starter(self) -> None:
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        portfolio = self.tmp / "06_active_context/research-portfolio.md"
        for scope in (None, "Private", "personal_vault"):
            with self.subTest(scope=scope):
                config = self.config()
                config.pop("runtime_scope", None)
                if scope is not None:
                    config["runtime_scope"] = scope
                self.write("config/ros.json", json.dumps(config))
                self.write("draft.md", self.RUN_DRAFT.format(id=f"scope-{scope or 'none'}".lower().replace("_", "-"), pin=pin))
                candidate = self.ros("propose", "judgment", "--file", str(self.tmp / "draft.md"),
                                     "--target", "commitment:alpha")["candidates"][0]
                before = portfolio.read_bytes()
                planned = self.ros("admit", candidate, answer="n")  # no question is asked: the diff is shown
                self.assertFalse(planned["promoted"])
                self.assertEqual(before, portfolio.read_bytes())

    def test_answering_cancel_or_satisfied_closes_a_requirement_only_at_the_terminal(self) -> None:
        issue = self.undecidable()
        question = self.question_of(issue)
        relayed = json.loads(self.run_ros("answer", question["short_id"], "cancel", "--reason", "relayed", expect=1)[1])
        self.assertFalse(relayed["applied"])
        self.assertEqual("invoker_asserted", relayed["permission_state"])
        self.assertEqual("waiting", self.ledger().derive_states()["issues"][issue]["status"])
        self.assertEqual("asked", self.ledger().asks()[question["ask_id"]]["state"])
        self.ros("answer", question["short_id"], "cancel", "--reason", "withdrawn at the terminal", answer="y")
        self.assertEqual("cancelled", self.ledger().derive_states()["issues"][issue]["status"])

    def test_bl1_admitted_field_changes_do_not_require_a_second_confirmation(self) -> None:
        self.ros("today")
        self.admit_alpha_candidate("first")
        self.admit_alpha_candidate("second")  # two legitimate writes must compose, not overwrite coverage
        closed, text = self.capture_ros("--lang", "zh-CN", "close")
        self.assertEqual(closed["judgment_fields"], [])
        self.assertTrue(all(row["admitted"] for row in closed["judgment_changes"]))
        self.assertEqual(text.count("本次会话已准入"), 2)
        self.assertFalse([row for row in closed["completion"]["unfinished"]
                          if self.binding(row["issue_id"]).startswith("field:")])
        self.assertFalse([row for row in self.ros("today")["completion"]["unfinished"]
                          if self.binding(row["issue_id"]).startswith("field:")])

    def test_bl1_hand_edits_after_admission_still_need_field_confirmation(self) -> None:
        self.ros("today")
        self.admit_alpha_candidate("first")
        text = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        text = text.replace("- judgments: j-first", "- judgments: j-first, j-manual")
        text = text.replace("- state: mainline", "- state: paused").replace("- priority: P0", "- priority: P1")
        text = text.replace("Does method A transfer under occlusion?", "A manually changed question?")
        self.write("06_active_context/research-portfolio.md", text)
        self.admit_alpha_candidate("second")  # a later legitimate admission cannot launder the manual delta
        closed = self.ros("close")
        self.assertEqual({r["field"] for r in closed["judgment_fields"]},
                         {"judgments", "question", "state", "priority"})
        pending = [row for row in closed["completion"]["unfinished"]
                   if self.binding(row["issue_id"]).startswith("field:")]
        self.assertEqual(len(pending), 4)
        for row in pending:
            self.ros("decide", row["short_id"], "confirm", answer="y")
        self.assertFalse([row for row in self.ros("today")["completion"]["unfinished"]
                          if self.binding(row["issue_id"]).startswith("field:")])

    def test_bl1_rolled_back_admission_cannot_cover_a_manually_restored_field(self) -> None:
        self.ros("today")
        admitted = self.admit_alpha_candidate("first")
        text = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        self.ros("admit", "--rollback", admitted["transaction_id"])
        self.write("06_active_context/research-portfolio.md", text)
        closed = self.ros("close")
        self.assertEqual([r["field"] for r in closed["judgment_fields"]], ["judgments"])
        self.assertFalse(closed["judgment_changes"][0]["admitted"])

    def test_bl1_past_session_admission_cannot_cover_a_later_manual_field_write(self) -> None:
        self.ros("today")
        self.admit_alpha_candidate("first")
        self.ros("close")
        text = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        self.write("06_active_context/research-portfolio.md", text.replace("- judgments: j-first\n", ""))
        self.ros("today")
        self.write("06_active_context/research-portfolio.md", text)
        closed = self.ros("close")
        self.assertEqual([r["field"] for r in closed["judgment_fields"]], ["judgments"])

    def test_bl1_missing_or_incomplete_receipts_do_not_exempt_fields(self) -> None:
        from copy import deepcopy
        from unittest.mock import patch
        session = self.ros("today")["session_id"]
        self.admit_alpha_candidate("first")
        ctx = ros.Context(self.tmp, TODAY, "")
        changes = [{"commitment_id": "alpha", "field": "judgments", "before": "", "after": "j-first"}]
        records = ctx.ledger.records()
        self.assertEqual(ctx.ledger.unadmitted_field_changes(changes, session), [])
        for missing in ("field_receipt", "applied_attempt", "admit_decision", "candidate_receipt"):
            with self.subTest(missing=missing):
                damaged = deepcopy(records)
                if missing == "applied_attempt":
                    damaged = [r for r in damaged if r.get("kind") != "attempt"]
                elif missing == "admit_decision":
                    damaged = [r for r in damaged if r.get("kind") != "decision"]
                else:
                    for row in damaged:
                        detail = row.get("payload", {}).get("detail", {})
                        if row.get("kind") == "effect" and detail.get("how") == "admit_candidate":
                            detail.pop("commitment_field_change" if missing == "field_receipt" else "receipt_id", None)
                with patch.object(ctx.ledger, "records", return_value=damaged):
                    self.assertEqual(ctx.ledger.unadmitted_field_changes(changes, session), changes)
        changes[0]["after"] = "j-first, j-manual"
        self.assertEqual(ctx.ledger.unadmitted_field_changes(changes, session), changes,
                         "a later hand edit of the same field is not the receipted value")

    def test_hj12_a_directly_written_judgment_field_stays_open_until_confirmed(self) -> None:
        self.ros("today")
        self.write("06_active_context/research-portfolio.md",
                   PORTFOLIO.replace("- question: Does method A transfer under occlusion?",
                                     "- question: Does method A transfer to night scenes?"))
        closed = self.ros("close")
        self.assertEqual([(r["commitment_id"], r["field"]) for r in closed["judgment_fields"]], [("alpha", "question")])
        self.assertFalse(closed["completion"]["done"], "改动发生在本次会话：本次就不得报完成，不是推给下一次")
        self.assertEqual(closed["completion"]["next_episode"], [], "它不是会话中途换了规则产生的工作")
        self.assertTrue([row for row in closed["completion"]["unfinished"]
                         if self.binding(row["issue_id"]).startswith("field:")])
        view = self.ros("today")
        pending = [row for row in view["completion"]["unfinished"] if self.binding(row["issue_id"]).startswith("field:")]
        self.assertEqual([self.binding(row["issue_id"]) for row in pending], ["field:alpha#question"],
                         "收尾列一行不算确认：留一条要求盯着")
        self.assertFalse(self.ros("close")["completion"]["done"], "未确认之前，这件事不算完成")
        # Confirming closes it, and only it.
        self.ros("today")
        relayed = json.loads(self.run_ros("decide", pending[0]["short_id"], "confirm", expect=1)[1])
        self.assertEqual((relayed["applied"], relayed["permission_state"]), (False, "invoker_asserted"),
                         "代理转述的确认不关闭要求")
        self.assertTrue([row for row in self.ros("today")["completion"]["unfinished"]
                         if self.binding(row["issue_id"]).startswith("field:")], "非终端确认后仍开着")
        self.ros("decide", pending[0]["short_id"], "confirm", answer="y")
        after = self.ros("today")
        self.assertFalse([row for row in after["completion"]["unfinished"]
                          if self.binding(row["issue_id"]).startswith("field:")], "确认之后才关闭")
        requested = [r["payload"] for r in self.ledger().trajectory() if r.get("kind") == "decision"
                     and r["payload"].get("detail", {}).get("action") == "confirm_not_applied"]
        self.assertEqual(requested[0]["permission_state"], "invoker_asserted", "不在研究者终端上的确认照实记为代答")
        self.assertTrue(requested[0]["detail"]["decision_evidence"].startswith("channel:non_tty"))
        # A later edit of the same field is a new generation: confirming once does not cover it.
        self.write("06_active_context/research-portfolio.md",
                   PORTFOLIO.replace("- question: Does method A transfer under occlusion?",
                                     "- question: Does method A transfer to rain?"))
        self.ros("close")
        again = self.ros("today")
        self.assertTrue([row for row in again["completion"]["unfinished"]
                         if self.binding(row["issue_id"]).startswith("field:")], "改一次确认一次：新的值要重新确认")
        # today offers confirming first, not only the two ways of disposing of it.
        row = next(r for r in again["completion"]["unfinished"] if self.binding(r["issue_id"]).startswith("field:"))
        shown = next(item for group in again["decision"] + again["today"] for item in group["items"]
                     if item["issue_id"] == row["issue_id"])
        self.assertEqual(shown["options"][0]["action"], f"ros decide {row['short_id']} confirm")
        from researchos_kernel.messages import t as message
        lang = self.config().get("language", "zh-CN")
        self.assertEqual(shown["details"], [message(lang, "field.detail")], "说明写的是「请确认这次写入」，不是检查不成立")
        # confirm closes a field change, nothing else: a requirement with a declared check is not
        # closed by saying it is fine (Soul §3).
        other = next(r for r in again["completion"]["unfinished"]
                     if not self.binding(r["issue_id"]).startswith("field:"))
        self.assertIn("confirm is for a judgment-class field change",
                      self.refusal("decide", other["short_id"], "confirm"))
        # ... and nothing is confirmed twice: once resolved, there is nothing open to confirm.
        self.ros("decide", row["short_id"], "confirm", answer="y")
        confirmed = [r["payload"] for r in self.ledger().trajectory()
                     if r.get("kind") == "decision" and r["payload"].get("detail", {}).get("action") == "field_confirmed"]
        self.assertEqual((confirmed[-1]["permission_state"], confirmed[-1]["detail"]["decision_evidence"]),
                         ("researcher_decision", "terminal_confirmation"), "只有终端作答才记为研究者的决定")
        self.assertIn("nothing open to confirm", self.refusal("decide", row["short_id"], "confirm"))

    def test_b8_only_the_terminal_closes_a_requirement_by_decide(self) -> None:
        issue = self.open_rules(self.boundary())["missing_question"][0]

        def reasons() -> list:
            return [r["payload"]["reason"] for r in self.ledger().trajectory()
                    if r.get("kind") == "issue_transition" and r["payload"]["issue_id"] == issue][-1:]
        before = reasons()
        relayed = json.loads(self.run_ros("decide", issue[:10], "cancel", "--reason", "relayed from chat", expect=1)[1])
        self.assertEqual((relayed["applied"], relayed["status"]), (False, "open"), "代理转述的取消不关闭要求")
        self.assertEqual(reasons(), before, "要求保持原状态")
        self.assertEqual(self.boundary().states["issues"][issue]["status"], "open")
        decision = [r["payload"] for r in self.ledger().trajectory() if r.get("kind") == "decision"][-1]
        self.assertEqual((decision["permission_state"], decision["detail"]["action"]),
                         ("invoker_asserted", "cancel_not_applied"), "照实记下这次转述")
        text = self.run_ros("decide", issue[:10], "cancel", "--reason", "x", json_out=False, lang="en", expect=1)[1]
        self.assertIn("at the terminal", text, "输出明确提示需要研究者在终端确认")
        self.ros("decide", issue[:10], "cancel", "--reason", "decided here", answer="y")
        self.assertEqual(reasons(), ["researcher_decision:cancel"])
        self.assertIn("declined", self.refusal("decide", issue[:10], "reopen", answer="n"))
        self.assertEqual(reasons(), ["researcher_decision:cancel"], "终端上拒绝：什么都不记")
        self.ros("decide", issue[:10], "reopen")
        self.assertEqual(reasons(), ["invoker_asserted:reopen"], "重开照常允许，照实记通道")

    def test_cc11_the_three_unknowns_are_counted_apart_and_none_stands_in_for_another(self) -> None:
        # (1) evidence unknown only the researcher can decide: the judgment's basis is gone.
        self.orphaned_judgments("one")
        # (2) coverage unknown: a declared rule whose descriptor cannot be read never ran.
        descriptor = next(path for path in (self.tmp / "config/extensions/rules").glob("*.json")
                          if json.loads(path.read_text(encoding="utf-8"))["id"] == "deadline_warning")
        descriptor.write_text("{ broken", encoding="utf-8")
        view = self.ros("today")
        kinds = view["completion"]["unknown_kinds"]
        self.assertGreaterEqual(kinds["evidence_researcher"], 1, "只能由研究者裁定的未知：作为问题提出")
        self.assertGreaterEqual(kinds["coverage_unevaluated"], 1, "覆盖未知：规则没跑过，不是证据未知")
        self.assertEqual(len(view["questions"]), 1, "覆盖未知不会被当成问题问出去")
        coverage_issue = next(issue for issue, requirement in
                              ros.Context(self.tmp, TODAY, "").boundary().requirements.items()
                              if str(requirement.get("binding", "")).startswith("coverage:"))
        checks = [r["payload"] for r in self.ledger().trajectory() if r.get("kind") == "check"
                  and r["payload"]["binding"]["issue_id"] == coverage_issue]
        self.assertEqual({c.get("reason_code", "") for c in checks}, {"coverage_unevaluated"}, "未知的类别记在记录上")
        # (3) run observation unknown: dispatched, never reported back.
        run = self.ros("run", "judgment", "--target", "commitment:alpha", "--executor", "copy_packet")["run_id"]
        after = self.ros("today")["completion"]
        self.assertEqual(after["runs_unknown"], [run])
        self.assertEqual(after["unknown_kinds"]["run_observation"], 1)
        self.assertEqual(len(self.asked()), after["unknown_kinds"]["evidence_researcher"],
                         "运行观测未知不变成问题，也不计进证据未知")

    def test_cc11_a_kind_is_neither_overwritten_nor_lost_on_the_next_boundary(self) -> None:
        self.orphaned_judgments("one")
        first = self.ros("today")["completion"]["unknown_kinds"]
        self.assertEqual(first["evidence_researcher"], 1)
        # (a) the requirement's rule is switched off while its question is still unanswered: the
        # blocker is still the researcher, and a disabled rule is out of spec, not coverage unknown.
        descriptor = next(path for path in (self.tmp / "config/extensions/rules").glob("*.json")
                          if json.loads(path.read_text(encoding="utf-8"))["id"] == "basis_recheck")
        rule = json.loads(descriptor.read_text(encoding="utf-8"))
        descriptor.write_text(json.dumps(dict(rule, enabled=False)), encoding="utf-8")
        kinds = self.ros("today")["completion"]["unknown_kinds"]
        self.assertEqual(kinds["evidence_researcher"], 1, "问题还没回答：类别不被后一轮的分支覆盖")
        self.assertEqual(kinds["coverage_unevaluated"], 0, "刻意关掉的规则是规格之外，不是没看过的输入")
        descriptor.write_text(json.dumps(rule), encoding="utf-8")
        # (b) the finding comes back, so the requirement is not re-checked this round; its kind must
        # not vanish, because the question is still open.
        for _ in range(3):
            view = self.ros("today")
        self.assertEqual(view["completion"]["unknown_kinds"]["evidence_researcher"], 1, "未知的类别不会在下一轮消失")
        self.assertEqual(len(view["questions"]), 1)

    def test_cc11_the_coverage_triple_is_a_partition_and_next_episode_work_is_not_counted(self) -> None:
        for path in (self.tmp / "config/extensions/rules").glob("*.json"):
            rule = json.loads(path.read_text(encoding="utf-8"))
            if rule["id"] in {"missing_question", "status_verify"}:
                path.write_text(json.dumps(dict(rule, check=[])), encoding="utf-8")  # declared, never runs
        kinds = self.ros("today", "--for", "beta")["completion"]["unknown_kinds"]
        triple = kinds["coverage_unevaluated"] + kinds["own_undefined"] + kinds["out_of_scope"]
        self.assertEqual(triple, kinds["coverage_unevaluated"] + kinds["own_undefined"] + kinds["out_of_scope"])
        opened = {row["issue_id"] for row in self.ros("today", "--for", "beta")["completion"]["unfinished"]}
        self.assertLessEqual(kinds["coverage_unevaluated"], len(opened),
                             "范围外的要求只算在「范围外」，不再算一次「范围内未评估」")
        from researchos_kernel.boundary import completion
        report = completion({"x": {"status": "open", "generation": 1, "rule_version": "2"}},
                            {"x": {"binding": "commitment:a", "rule_id": "r"}}, None, today=TODAY,
                            frozen_rules={"other": "1"}, open_at_start={}, unknowns={"x": "evidence_researcher"})
        self.assertEqual([row["issue_id"] for row in report["next_episode"]], ["x"])
        self.assertEqual(report["unknown_kinds"]["evidence_researcher"], 0, "属于下一次的工作不算这次的未知")

    def test_cc11_a_run_whose_side_effects_are_unknown_is_not_a_receipt(self) -> None:
        self.ros("today")
        run = self.ros("run", "judgment", "--target", "commitment:alpha", "--executor", "copy_packet")["run_id"]
        decision = next(r for r in self.ledger().trajectory()
                        if r["payload"].get("detail", {}).get("run_id") == run
                        and r["payload"]["detail"].get("action") == "run_dispatched")
        self.ledger().attempt(decision["id"], "failed", [], detail={"run_id": run, "error": "provider_lost",
                                                                    "side_effects": "unknown", "retryable": False})
        ctx = ros.Context(self.tmp, TODAY, "")
        self.assertEqual(ctx.ledger.unresolved_runs(""), [run], "发出去之后失败、副作用未知：这正是运行观测未知")
        self.cancel_unfinished(self.ros("today"))
        self.assertEqual(self.ros("close")["outcome"], "human_stopped")
        # The researcher's way out: state that no answer will come. The unknown is recorded, not erased.
        self.ros("today")
        self.ros("collect", run, "--abandon", "--reason", "the packet was never sent")
        abandoned = [r["payload"] for r in self.ledger().trajectory()
                     if r.get("kind") == "attempt" and r["payload"].get("status") == "abandoned"]
        self.assertEqual(abandoned[0]["detail"]["side_effects"], "unknown", "放弃不是回执：未知照记")
        self.assertEqual(self.ledger().unresolved_runs(""), [])
        self.cancel_unfinished(self.ros("today"))
        closed = self.ros("close")
        self.assertEqual(closed["outcome"], "complete", "记下未知之后，会话可以收尾")
        episode = [r for r in self.ledger().records("episodes") if r.get("end")][-1]
        self.assertIn("unknown_kinds", episode["detail"], "账上要看得出这次为什么没完成")

    def test_cc11_a_dispatched_run_that_never_reported_is_not_completion(self) -> None:
        self.ros("today")
        run = self.ros("run", "judgment", "--target", "commitment:alpha", "--executor", "copy_packet")["run_id"]
        self.cancel_unfinished(self.ros("today"))  # every requirement decided; only the run is unknown
        self.assertIn(run, self.run_ros("today", json_out=False, lang="zh-CN")[1], "today 就把它单列出来，不混进问题或覆盖未知")
        closed = self.ros("close")
        self.assertEqual(closed["completion"]["runs_unknown"], [run])
        self.assertFalse(closed["completion"]["done"], "派出去的运行没有回执：做没做过都不知道，不能报完成")
        self.assertEqual(closed["outcome"], "human_stopped")

    def test_every_date_argument_is_a_real_day_and_never_in_the_past(self) -> None:
        issue = self.open_rules(self.boundary())["missing_question"][0]
        for bad in ("2026-02-30", "2026-9-30", "soon"):
            self.assertIn("real date", self.refusal("decide", issue[:10], "defer", "--until", bad), bad)
        for early in ("2026-09-10", TODAY.isoformat()):
            self.assertIn("after today", self.refusal("decide", issue[:10], "defer", "--until", early), early)
        self.assertIn("real date", self.refusal("attend", "alpha", "date", "2026-02-30"))
        self.assertIn("in the past", self.refusal("attend", "beta", "park", "--review", "2026-09-01"))
        self.assertEqual(self.boundary().states["issues"][issue]["status"], "open", "拒绝的日期什么都不记")

    def test_cc10_each_round_rechecks_every_open_requirement(self) -> None:
        issue = self.open_rules(self.boundary())["missing_question"][0]
        self.write("06_active_context/research-portfolio.md",
                   PORTFOLIO.replace("- next_step: Wait for reviews", "- next_step: Wait for reviews\n- question: Will the reviews land?"))
        self.assertEqual(self.boundary().states["issues"][issue]["status"], "resolved",
                         "下一轮重核：来源修好了，检查成立即关闭")

    def test_hj5_rejection_and_neglect_never_change_a_rule(self) -> None:
        rules_dir = self.tmp / "config/extensions/rules"
        before = {p.name: p.read_bytes() for p in rules_dir.glob("*.json")}
        config_before = (self.tmp / "config/ros.json").read_bytes()
        for day in (20, 21, 22):
            view = self.ros("today", today=date(2026, 9, day))
            for row in view["completion"]["unfinished"]:  # every finding cancelled, day after day
                self.ros("decide", row["short_id"], "cancel", "--reason", "not now", today=date(2026, 9, day), answer="y")
            self.ros("close", today=date(2026, 9, day))
        self.assertEqual({p.name: p.read_bytes() for p in rules_dir.glob("*.json")}, before,
                         "拒绝、忽略不构成训练信号：规则一个字节不变")
        self.assertEqual((self.tmp / "config/ros.json").read_bytes(), config_before)

    # one disposition per commitment (CC-5) and delegation (HJ-7) --------------------------------------
    def test_cc5_one_commitment_one_disposition_and_next_step_nothing_guessed(self) -> None:
        doubled = PORTFOLIO.replace("- next_step: Run the occlusion comparison",
                                    "- next_step: Run the occlusion comparison\n- next_step: Write the paper")
        doubled += "\n### Beta Again\n\n- id: beta\n- responsibility: support\n- state: queued\n"
        self.boundary()  # beta's work is registered while its identity is still unique
        self.write("06_active_context/research-portfolio.md", doubled)
        result = self.boundary()
        commitments = result.snapshot.commitments
        self.assertEqual(commitments["alpha"].get("next_step"), "", "两个下一步：不猜，视为未写")
        self.assertNotIn("beta", commitments, "同一 id 两处：身份不唯一，哪一处都不读")
        self.assertTrue(any("next_step more than once" in p for p in result.problems))
        self.assertTrue(any("declared 2 times" in p for p in result.problems))
        self.assertIn("gamma", commitments, "其余承诺照常：系统可多线程")
        # Its open work stays open work (fixed in the portfolio), never a question that could close it.
        states = result.states["issues"]
        beta_work = [i for i, r in result.requirements.items() if r.get("commitment_id") == "beta"]
        self.assertTrue(beta_work)
        self.assertTrue(all(states[i]["status"] == "open" for i in beta_work), "身份不唯一不是研究者要回答的问题")
        from researchos_adapters.markdown_repo import commitment_block_span, parse_portfolio
        self.assertEqual(commitment_block_span(doubled, "beta"), (-1, -1), "写入方也不在两处之间挑一处")
        # Only the commitment list counts; an example elsewhere in the file is not a commitment.
        example = PORTFOLIO + "\n## Update Rule\n\n### Example\n\n- id: alpha\n- state: closed\n"
        self.assertEqual(parse_portfolio(example)["alpha"].get("state"), "mainline")
        problems = []
        parse_portfolio(PORTFOLIO.replace("- id: gamma", "- id: gamma\n- id: delta"), problems)
        self.assertTrue(any("declares id more than once" in p for p in problems), "一块两个 id 也要报告")

    def test_cc5_admission_writes_into_the_block_the_reader_read(self) -> None:
        template = "## Template\n\n### Example\n\n- id: alpha\n- state: closed\n\n"
        portfolio = PORTFOLIO.replace("## Responsibility Items", template + "## Responsibility Items")
        self.write("06_active_context/research-portfolio.md", portfolio)
        from researchos_adapters.markdown_repo import commitment_block_span, parse_portfolio
        start, end = commitment_block_span(portfolio, "alpha")
        self.assertTrue(portfolio[start:end].startswith("### Alpha Paper"), "写入方取读取方读到的那一块")
        self.assertEqual(parse_portfolio(portfolio)["alpha"].span, (start, end))
        self.admit_alpha_candidate("into-real")
        after = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        self.assertTrue(after.startswith(portfolio.split("## Responsibility Items")[0]), "模板块原样不动")
        self.assertEqual(parse_portfolio(after)["alpha"].get("judgments"), "j-into-real")
        self.assertIn("j-into-real", self.boundary().states["admitted_judgments"])

    def test_hj7_only_bounded_reversible_fact_maintenance_is_delegated(self) -> None:
        from researchos_kernel.rules import load_rules
        base = json.loads((self.tmp / "config/extensions/rules/status-verify.json").read_text(encoding="utf-8"))
        fact = dict(base, id="refresh_verified", resolver="script")
        judgment = dict(base, id="rewrite_question", resolver="script",
                        expect={"result": "writeback", "write_scope": ["commitment:question"]})
        wide = dict(base, id="global_touch", resolver="script", scope_selector="global")
        for name, descriptor in (("refresh-verified", fact), ("rewrite-question", judgment), ("global-touch", wide)):
            self.write(f"config/extensions/rules/{name}.json", json.dumps(descriptor))
        rules, problems = load_rules(self.tmp, "private", ROOT)
        self.assertEqual(rules["refresh_verified"]["resolver"], "script", "有界、可逆、只写事实字段：可委托")
        self.assertEqual(rules["rewrite_question"]["resolver"], "human", "写判断类字段：开放式判断，进复核")
        self.assertEqual(rules["global_touch"]["resolver"], "human", "范围不是自己的：不委托")
        self.assertTrue(any("commitment:question" in p for p in problems))
        # An allowlist: every other spelling of a judgment-class or unbounded write is refused too.
        from researchos_kernel.rules import delegation_problems, write_class
        classes = write_class(self.tmp, ROOT)
        for name, change in (("basis block", {"expect": {"result": "writeback", "write_scope": ["judgment_block:basis"]}}),
                             ("portfolio file", {"expect": {"result": "writeback",
                                                            "write_scope": ["06_active_context/research-portfolio.md"]}}),
                             ("unbounded", {"expect": {"result": "writeback", "write_scope": []}}),
                             ("model output", {"executor": "model"}),
                             ("no auto-start bound", {"pre": {}})):
            self.assertTrue(delegation_problems(dict(fact, **change), classes), f"{name} 不可委托")
        self.assertEqual(delegation_problems(fact, classes), [])
        # The gate and a proposal refuse it before anything is scheduled.
        import validate_task_extensions
        if hasattr(validate_task_extensions, "validate_scheduler_rules"):  # the edition's gate checks rules
            self.assertTrue(any("rewrite_question" in f and "not delegable" in f
                                for f in validate_task_extensions.validate_scheduler_rules(self.tmp)))
        session = self.ros("today")["session_id"]
        self.assertIn("only for bounded, reversible fact maintenance", self.refusal("propose", "rule", "--file", self.revision_file(
            dict(judgment, id="status_verify", version="2.0.0"), session)))

    def test_a_relayed_post_hoc_confirmation_leaves_the_request_open(self) -> None:
        self.add_alpha_judgment()  # written straight into a card: no prior authorization
        issue = self.open_rules(self.boundary())["confirm_judgment_change"][0]
        code, out, _ = self.run_ros("admit", "--confirm", "j-alpha-scope", expect=1)
        self.assertFalse(json.loads(out)["applied"])
        result = self.boundary()
        self.assertNotEqual(result.states["issues"][issue]["status"], "resolved", "代理转述不关闭确认要求")
        self.assertNotIn("j-alpha-scope", result.states.get("confirmed_judgments", {}))
        decision = self.admit_decisions()[-1]
        self.assertEqual((decision["payload"]["permission_state"], decision["payload"]["detail"]["action"]),
                         ("invoker_asserted", "confirm_not_applied"))

    # break-glass (HJ-8) ------------------------------------------------------------------------------
    def test_hj8_post_hoc_confirmation_closes_only_the_confirmation_requirement(self) -> None:
        self.add_alpha_judgment()  # written straight into a card: no prior authorization
        issue = self.open_rules(self.boundary())["confirm_judgment_change"][0]
        done = self.ros("admit", "--confirm", "j-alpha-scope", answer="y")
        self.assertEqual(done["admission_state"]["mutation_state"], "not_requested", "没有经准入链的修改")
        result = self.boundary()
        self.assertEqual(result.states["issues"][issue]["status"], "resolved", "确认要求关闭")
        self.assertNotIn("j-alpha-scope", result.states["admitted_judgments"], "事后确认不算准入")
        self.assertIn("j-alpha-scope", result.states["confirmed_judgments"])
        effect = [r["payload"] for r in self.ledger().trajectory() if r.get("kind") == "effect"][-1]
        self.assertEqual((effect["changes"][0]["change"], effect["detail"]["authorization"]),
                         ("direct_change_confirmed", "post_hoc_break_glass"))
        # Other requirements on the block are untouched: a basis change still asks for a re-check.
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v2\n")
        self.assertIn("basis_recheck", self.open_rules(self.boundary()))
        # A reconfirm re-pins the basis; it cannot promote a confirmed block into an admission.
        self.ros("admit", "--reconfirm", "j-alpha-scope")
        states = self.boundary().states
        self.assertNotIn("j-alpha-scope", states["admitted_judgments"], "reconfirm 不能把事后确认洗成准入")
        self.assertIn("already confirmed", self.refusal("admit", "--confirm", "j-alpha-scope"), "同一版本不重复确认")
        self.write("01_knowledge/papers/k.md", "---\ntitle: K\n---\n# K\n\n> [!judgment] j-never\n> 结论：x\n"
                   "> 依据：01_knowledge/projects/alpha.md\n")
        self.assertIn("never admitted or confirmed", self.refusal("admit", "--reconfirm", "j-never"))
        # A record written before this distinction by the same path reads the same way.
        legacy = self.ledger()
        with legacy.lock():
            legacy.effect("", [{"object_id": "j-legacy", "content_id": "h", "change": "judgment_admitted", "path": "x.md"}],
                          detail={"how": "confirm_existing_block"})
        states = legacy.derive_states()
        self.assertNotIn("j-legacy", states["admitted_judgments"])
        self.assertIn("j-legacy", states["confirmed_judgments"])

    # Session axis (CC-5b) --------------------------------------------------------------------------
    def test_cc5b_one_intent_per_session_and_switching_never_overwrites_another(self) -> None:
        from unittest import mock
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        whole = self.ros("today")["session_id"]
        cache = next(self.tmp.rglob(f"sessions/{whole}.json"))
        kept = cache.read_bytes()
        with mock.patch.object(ros, "SESSION_KEEP", 0):
            focused = self.ros("today", "--for", "alpha")["session_id"]
        self.assertNotEqual(whole, focused, "另一个意图开自己的会话")
        self.assertEqual(cache.read_bytes(), kept, "切换选中项不改动另一个会话的起点，也不清掉仍开着的会话缓存")
        self.assertEqual(self.ros("today")["session_id"], whole, "同一意图同一天：延续")
        self.assertEqual(self.ros("today", "--for", "alpha")["session_id"], focused)
        # Drafts bind to the session whose intent they serve; nothing guesses between two.
        draft = self.tmp / "draft.md"
        draft.write_text(self.RUN_DRAFT.format(id="focused", pin=pin), encoding="utf-8")
        cid = self.ros("propose", "judgment", "--file", str(draft), "--target", "commitment:alpha")["candidates"][0]
        self.assertEqual(self.ledger().candidates()[cid]["payload"]["session_id"], focused)
        draft.write_text(self.RUN_DRAFT.format(id="whole", pin=pin), encoding="utf-8")
        cid = self.ros("propose", "judgment", "--file", str(draft), "--target", "01_knowledge/projects/beta.md")["candidates"][0]
        self.assertEqual(self.ledger().candidates()[cid]["payload"]["session_id"], whole)
        self.assertIn("several sessions are open", self.refusal("close"))
        closed = self.ros("close", "--for", "alpha")
        self.assertEqual(closed["session_id"], focused)
        self.assertEqual(ros._session_state(ros.Context(self.tmp, TODAY, ""), whole), "open", "只结束被点名的会话")
        run = self.ros("run", "judgment", "--target", "commitment:alpha", "--executor", "copy_packet")
        dispatched = [r for r in self.ledger().trajectory() if r["payload"].get("detail", {}).get("run_id") == run["run_id"]
                      and r["payload"]["detail"].get("action") == "run_dispatched"]
        self.assertEqual(dispatched[0]["episode_id"], whole, "它的会话结束后，这个意图落回全范围会话")

    def test_session_is_the_ledgers_and_a_lost_cache_is_reported_not_passed(self) -> None:
        session = self.ros("today")["session_id"]
        self.cancel_unfinished(self.ros("today"))
        next(self.tmp.rglob(f"sessions/{session}.json")).unlink()  # the cache, not the session
        closed = self.ros("close")
        self.assertEqual(closed["session_id"], session, "会话由账本确认，不靠缓存文件")
        self.assertEqual(closed["outcome"], "human_stopped", "起点缓存丢了：不能判完成")
        self.assertTrue(closed["note"], "如实说明起点缓存不在")
        self.assertEqual(self.ledger().records("episodes")[-1]["detail"]["note"], closed["note"])
        self.assertEqual(ros._session_state(ros.Context(self.tmp, TODAY, ""), session), "ended")
        self.assertIn("no session open today", self.refusal("close"))
        self.assertIn("already ended", self.refusal("close", "--session", session))

    def test_sessions_from_earlier_days_are_named_never_guessed(self) -> None:
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        old = self.ros("today", "--for", "alpha", today=date(2026, 9, 19))["session_id"]
        self.assertIn("no session open today", self.refusal("close"), "裸 close 不去收前一天的会话")
        view = self.ros("today")
        self.assertEqual(view["stale_sessions"], [old], "今日里列出前几天没收尾的会话")
        draft = self.tmp / "draft.md"
        draft.write_text(self.RUN_DRAFT.format(id="card", pin=pin), encoding="utf-8")
        focused = self.ros("today", "--for", "alpha")["session_id"]
        got = self.ros("propose", "judgment", "--file", str(draft), "--target", "01_knowledge/projects/alpha.md")
        self.assertEqual(got["session_id"], focused, "承诺的来源卡片按该承诺归属会话")
        self.assertIn("several sessions are open", self.refusal("close"))
        self.ros("close", "--for", "alpha")
        self.ros("close")
        self.assertEqual(self.ros("close", "--session", old)["session_id"], old, "前一天的会话点名才收")
        self.assertIn("already ended", self.refusal("close", "--session", old), "一个会话只结束一次")

    def test_a_lost_cache_still_lists_judgments_awaiting_confirmation(self) -> None:
        session = self.ros("today")["session_id"]
        self.add_alpha_judgment()  # written straight into a card, never admitted
        next(self.tmp.rglob(f"sessions/{session}.json")).unlink()
        closed = self.ros("close")
        self.assertIn("j-alpha-scope", [row["judgment_id"] for row in closed["judgment_changes"]],
                      "起点缓存丢了，未准入的判断块照样列出待确认")
        self.assertTrue(closed["note"])

    # executors (CR-3 / CR-9 / CA-2 / CA-2b) ------------------------------------------------------
    def test_cr3_a_real_backend_dispatches_only_when_declared_and_only_inside_the_launch_boundary(self) -> None:
        ctx = ros.Context(self.tmp, TODAY, "")
        self.assertIsNone(dispatchable(ctx, "codex"), "没有声明就不可派发：派发会把上下文送出去，默认不做")
        for value in (False, "false", "true", 1, None):
            self.edit_config(providers={"codex": {"dispatchable": value}})
            self.assertIsNone(dispatchable(ros.Context(self.tmp, TODAY, ""), "codex"))
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.edit_config(providers={"codex": {"dispatchable": True, "reasoning": "low"}})
        self.assertIsNotNone(dispatchable(ros.Context(self.tmp, TODAY, ""), "codex"))
        self.assertIsNone(dispatchable(ros.Context(self.tmp, TODAY, ""), "other"), "只有本版带的参考适配器")
        public = ros.Context(self.tmp, TODAY, "")
        public.runtime_scope = "public_starter"
        self.assertIsNone(dispatchable(public, "codex"), "公开版只抄不发")
        self.ros("today")
        draft = self.RUN_DRAFT.format(id="local", pin=pin)
        output = "\n".join(json.dumps(event) for event in [
            {"type": "thread.started", "thread_id": "fixture-thread"},
            {"type": "item.completed", "item": {"type": "command_execution", "aggregated_output": draft}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Inspecting the evidence."}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": draft}},
            {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 20}},
        ])
        before = self.repository_files()
        resolve, runner, seen = self.local_codex(output)
        with resolve, runner:
            run = self.ros("run", "judgment", "--target", "commitment:alpha", "--executor", "provider:codex")
        self.assertTrue(run["candidates"], "回来的草稿走的还是候选那条路，不直接写入")
        self.assertEqual(len(run["candidates"]), 1, "工具输出与中间消息不能被重复提案")
        self.assertEqual(self.repository_files(), before, "收回结果不等于准入")
        self.assertNotIn("j-local", self.boundary().snapshot.judgments)
        self.ros("admit", run["candidates"][0])
        self.assertIn("j-local", self.boundary().snapshot.judgments, "测试夹具显式确认后才写入")
        profile = " ".join(seen["args"])
        self.assertIn('default_permissions="researchos-runner-v1"', profile)
        self.assertIn("network={enabled=false}", profile, "断网")
        self.assertIn('":root"="deny"', profile)
        self.assertIn(f'"{seen["cwd"]}"="read"', profile, "仅允许空临时工作目录")
        self.assertNotIn(f'"{os.path.realpath(self.tmp)}"="read"', profile, "不能绕过上下文筛选去读仓库")
        self.assertNotIn(f'"{ROOT.resolve()}"="read"', profile, "安装根也不能成为旁路")

        self.assertFalse(Path(seen["cwd"]).exists(), "完成后清除临时目录")
        self.assertIn(".aws", profile, "凭据目录明确 deny")
        self.assertIn("--ignore-user-config", seen["args"])
        self.assertNotIn(str(Path.home() / ".codex"), seen["env"].get("CODEX_HOME", ""), "用一次性的私有 home")
        self.assertIn("alpha", seen["prompt"], "执行者只拿到上下文构建器交付的材料")

    def test_cr3_claude_code_backend_dispatches_inside_the_same_boundary_answer_only(self) -> None:
        """The second local reference adapter: declared the same way, bounded the same way, answers only."""
        from unittest import mock
        self.edit_config(providers={"claude_code": {"dispatchable": True, "reasoning": "low"}})
        self.assertIsNotNone(dispatchable(ros.Context(self.tmp, TODAY, ""), "claude_code"))
        public = ros.Context(self.tmp, TODAY, "")
        public.runtime_scope = "public_starter"
        self.assertIsNone(dispatchable(public, "claude_code"), "公开版只抄不发")
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.ros("today")
        draft = self.RUN_DRAFT.format(id="claude", pin=pin)
        output = json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": draft,
                             "session_id": "fixture", "num_turns": 1})
        seen = {}

        def run(runner, args, timeout=90, input_text=None, env=None):
            seen.update({"args": list(args), "env": dict(env or {}), "prompt": input_text or "", "cwd": str(runner.root)})
            return {"ok": True, "returncode": 0, "seconds": 0.1, "stdout": output}
        before = self.repository_files()
        with mock.patch("researchos_adapters.claude_code_adapter.resolve_claude_executable", lambda *a, **k: Path("/nonexistent/claude")), \
                mock.patch("researchos_adapters.command_runner.CommandRunner.run", run), \
                mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "secret"}):
            run_result = self.ros("run", "judgment", "--target", "commitment:alpha", "--executor", "provider:claude_code")
        self.assertEqual(len(run_result["candidates"]), 1, "回来的草稿走候选那条路，不直接写入")
        self.assertEqual(self.repository_files(), before, "收回结果不等于准入")
        self.assertNotIn("j-claude", self.boundary().snapshot.judgments)
        self.ros("admit", run_result["candidates"][0])
        self.assertIn("j-claude", self.boundary().snapshot.judgments, "显式确认后才写入")
        self.assertIn("--restricted", seen["args"], "不读用户、项目与本地设置文件，因而不加载其中的 hooks 与插件")
        self.assertNotIn("--bare", seen["args"], "--bare 只认 API key，订阅登录会被当成未登录")
        self.assertEqual("", seen["args"][seen["args"].index("--tools") + 1], "不开任何工具：上下文已在提示里")
        self.assertIn("--strict-mcp-config", seen["args"])
        self.assertNotEqual(os.path.realpath(self.tmp), os.path.realpath(seen["cwd"]), "不能绕过上下文筛选去读仓库")
        self.assertNotEqual(str(ROOT.resolve()), seen["cwd"], "安装根也不能成为旁路")
        self.assertNotEqual(str(Path.home() / ".claude"), seen["env"].get("CLAUDE_CONFIG_DIR"), "私有配置目录，不是用户自己的")
        self.assertNotIn("ANTHROPIC_API_KEY", seen["env"], "不转发任何 API key；登录是研究者自己的")
        self.assertIn("Occlusion results do not transfer yet", seen["prompt"] + output)

    def test_cr3_cli_without_a_final_judgment_never_proposes_tool_output(self) -> None:
        self.edit_config(providers={"codex": {"dispatchable": True}})
        self.ros("today")
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        draft = self.RUN_DRAFT.format(id="not-an-answer", pin=pin)
        tool_output = json.dumps({"type": "item.completed", "item": {
            "type": "command_execution", "aggregated_output": draft}})
        withdrawn = "\n".join(json.dumps({"type": "agent_message", "text": text}) for text in
                              (draft, "Withdraw the earlier draft; there is not enough evidence."))
        outputs = [draft, tool_output, "not json\n[]\nnull\n42\n", withdrawn,
                   tool_output + "\n" + json.dumps({"type": "agent_message", "text": "No judgment."})]
        for output in outputs:
            with self.subTest(output=output):
                resolve, runner, _ = self.local_codex(output)
                with resolve, runner:
                    run = json.loads(self.run_ros("run", "judgment", "--target", "commitment:alpha",
                                              "--executor", "provider:codex", expect=1)[1])
                self.assertEqual((run["result"], run["candidates"]), ("invalid", []))
                self.assertIn(run["run_id"], self.ledger().unresolved_runs(""))
        self.assertFalse(self.ledger().candidates())

    def test_cr3_cli_timeout_and_interruption_record_unknown_effects(self) -> None:
        from unittest import mock
        from researchos_adapters.run_state import run_state_ledger
        self.edit_config(providers={"codex": {"dispatchable": True}})
        self.edit_config(run_timeout=123)
        self.ros("today")
        for effect, expected_error in ((subprocess.TimeoutExpired("fixture-codex", 1), "runner_execution_failed"),
                                       (KeyboardInterrupt(), "provider_interrupted")):
            with self.subTest(error=expected_error), mock.patch(
                    "researchos_adapters.provider_adapter.resolve_codex_executable", return_value=Path("/nonexistent/codex")), \
                    mock.patch("researchos_adapters.command_runner.subprocess.run", side_effect=effect) as launched:
                failed = json.loads(self.run_ros("run", "judgment", "--target", "commitment:alpha",
                                             "--executor", "provider:codex", expect=1)[1])
                self.assertEqual(launched.call_args.kwargs["timeout"], 123)
            self.assertEqual((failed["error"], failed["lifecycle"]["side_effects"]), (expected_error, "unknown"))
            ledger = run_state_ledger(self.tmp / RUN_LOG, "private")
            self.assertFalse(ledger.recovery(failed["run_id"])["retry_allowed"])
            self.assertIn(failed["run_id"], self.ledger().unresolved_runs(""))

    def test_cc11_provider_unknown_can_be_explicitly_closed_without_fabricating_a_result(self) -> None:
        from researchos_adapters.run_state import run_state_ledger
        self.ros("today")
        before = self.repository_files()
        for ok in (False, True):
            patch, _ = self.fake_provider("No usable judgment.", ok=ok)
            with patch:
                run = json.loads(self.run_ros("run", "judgment", "--target", "commitment:alpha",
                                          "--executor", "provider:fake", expect=1)[1])
            self.assertIn(run["run_id"], self.ledger().unresolved_runs(""))
            self.assertIn("needs --reason", self.refusal("collect", run["run_id"], "--abandon"))
            # A local file cannot replace a provider response or impersonate its provenance.
            self.assertIn("no copy-packet run", self.refusal("collect", run["run_id"], "--file", "unused.md"))
            abandoned = self.ros("collect", run["run_id"], "--abandon", "--reason", "Stopped; effects remain unknown.")
            self.assertEqual((abandoned["result"], abandoned["side_effects"]), ("abandoned", "unknown"))
            self.assertNotIn(run["run_id"], self.ledger().unresolved_runs(""))
            self.assertIn("already resolved", self.refusal("collect", run["run_id"], "--abandon", "--reason", "again"))
            ledger = run_state_ledger(self.tmp / RUN_LOG, "private")
            self.assertFalse(ledger.recovery(run["run_id"])["retry_allowed"], "结案未知不等于批准重发")
        self.assertFalse(self.ledger().candidates())
        self.assertEqual(before, self.repository_files())
        self.assertIn("no run", self.refusal("collect", "foreign-run", "--abandon", "--reason", "not ours"))

    def test_cr3_a_boundary_that_cannot_be_built_launches_nothing(self) -> None:
        from unittest import mock
        from researchos_adapters.runner_permissions import RunnerPermissionError
        self.edit_config(providers={"codex": {"dispatchable": True}})
        self.ros("today")
        def refuse(**kwargs):
            raise RunnerPermissionError("cannot verify")
        with mock.patch("researchos_adapters.runner_permissions.runner_launch_permissions", refuse):
            failed = json.loads(self.run_ros("run", "judgment", "--target", "commitment:alpha", "--executor", "provider:codex", expect=1)[1])
        self.assertEqual(failed["error"], "runner_boundary_unavailable")
        self.assertEqual(failed["lifecycle"]["side_effects"], "none", "边界建不起来就没发出去，可以重试")
        self.assertEqual(self.ledger().unresolved_runs(""), [],
                         "什么都没发生：不是运行观测未知")

    def test_cr3_fake_provider_and_scripted_session_agent_share_one_protocol(self) -> None:
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.ros("today")
        before = self.repository_files()
        # The scripted session Agent: context out, drafts in, through ros.
        pack = self.ros("context", "commitment:alpha")["pack"]
        draft = self.tmp / "draft.md"
        draft.write_text(self.RUN_DRAFT.format(id="agent", pin=pin), encoding="utf-8")
        by_agent = self.ros("propose", "judgment", "--file", str(draft), "--target", "commitment:alpha")["candidates"]
        # The fake provider: the same context builder, the same candidate path.
        patch, seen = self.fake_provider(self.RUN_DRAFT.format(id="provider", pin=pin))
        with patch:
            run = self.ros("run", "judgment", "--target", "commitment:alpha", "--executor", "provider:fake")
        from researchos_adapters.provider_adapter import ExecutionRequest
        self.assertIsInstance(seen[0], ExecutionRequest)
        self.assertIsNone(seen[0].extension, "中立请求不携带任何后端私有字段")
        self.assertIn(pack.split("\n", 1)[0], seen[0].prompt, "执行者只从同一个上下文构建器取材料")
        candidates = self.ledger().candidates()
        agent, provider = candidates[by_agent[0]], candidates[run["candidates"][0]]
        self.assertEqual(set(agent["envelope"]), set(provider["envelope"]), "同一种候选")
        self.assertEqual((agent["payload"]["executor"], provider["payload"]["executor"]), ("session_agent", "provider:fake"))
        self.assertEqual(provider["payload"]["run_id"], run["run_id"])
        for row in (agent, provider):
            self.assertEqual(row["payload"]["admission_state"]["decision_state"], "proposed", "只是候选，未准入")
        self.assertEqual(self.repository_files(), before, "越权写入为 0：没有一张卡片被改动")
        # Five axes: completed run, writeback result, proposed admission -> review; the session stays open.
        self.assertEqual(run["lifecycle"]["derived"]["state"], "result_ready")
        self.assertEqual(run["lifecycle"]["derived"]["primary_action"], "open_review")
        from researchos_adapters.run_state import run_state_ledger
        record = run_state_ledger(self.tmp / RUN_LOG, "private").reconcile(client_request_id=run["run_id"])
        self.assertEqual((record["run_state"], record["side_effects"]), ("completed", "unknown"),
                         "返回了结果不等于证实没有别的影响")
        attempts = [r["payload"] for r in self.ledger().trajectory() if r.get("kind") == "attempt"
                    and run["candidates"][0] in r["payload"].get("output_ids", [])]
        self.assertEqual(len(attempts), 1, "一次运行一条 attempt，挂在它的派发决定下")
        self.assertTrue(attempts[0]["decision_id"])
        self.assertEqual(ros._session_state(ros.Context(self.tmp, TODAY, ""), self.ros("today")["session_id"]), "open",
                         "运行完成不结束会话")

    def test_ca2_failed_or_unparseable_run_is_stated_as_it_is_and_never_resent(self) -> None:
        self.ros("today")
        patch, _ = self.fake_provider(ok=False)
        with patch:
            failed = json.loads(self.run_ros("run", "judgment", "--target", "commitment:alpha", "--executor", "provider:fake", expect=1)[1])
        self.assertEqual(failed["error"], "fake_failed")
        self.assertEqual(failed["lifecycle"]["derived"]["state"], "failed_needs_impact_check",
                         "失败且影响未知：先核对影响")
        from researchos_adapters.run_state import run_state_ledger
        ledger = run_state_ledger(self.tmp / RUN_LOG, "private")
        recovery = ledger.recovery(failed["run_id"])
        self.assertEqual((recovery["action"], recovery["retry_allowed"]), ("check_effects", False))
        self.assertFalse(ledger.claim_dispatch(failed["run_id"]), "unknown 只核对不重发")
        patch, _ = self.fake_provider("I think the method is fine.")
        with patch:
            invalid = json.loads(self.run_ros("run", "judgment", "--target", "commitment:alpha", "--executor", "provider:fake", expect=1)[1])
        self.assertEqual((invalid["result"], invalid["candidates"]), ("invalid", []), "读不出判断块：结果无效，照实说")
        self.assertEqual(invalid["lifecycle"]["derived"]["state"], "failed_needs_impact_check")
        # One good block and one bad one: all or none, never a half-recorded result.
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        mixed = self.RUN_DRAFT.format(id="good", pin=pin) + "\n" + self.RUN_DRAFT.format(id="bad", pin=pin).replace(
            "01_knowledge/projects/alpha.md", "01_knowledge/nowhere.md")
        before = set(self.ledger().candidates())
        patch, _ = self.fake_provider(mixed)
        with patch:
            half = json.loads(self.run_ros("run", "judgment", "--target", "commitment:alpha", "--executor", "provider:fake", expect=1)[1])
        self.assertEqual(half["result"], "invalid")
        self.assertEqual(set(self.ledger().candidates()), before, "无效结果不留下可准入的候选")

    def test_ca2_nothing_launched_is_retryable_and_undispatchable_records_nothing(self) -> None:
        self.ros("today")
        before = len(self.ledger().trajectory())
        self.assertIn("not dispatchable", self.refusal("run", "judgment", "--target", "commitment:alpha",
                                                       "--executor", "provider:codex"))
        self.assertEqual(len(self.ledger().trajectory()), before, "派不出去：不记外发、不留运行、不留孤立决定")
        from unittest import mock
        from researchos_adapters.provider_adapter import ProviderExecution

        class Missing:
            def execute(self, request):
                return ProviderExecution("codex", False, "unavailable", 0.0, "", "codex_cli_missing")
        with mock.patch.object(ros, "provider_for", lambda config, scope, pid: Missing()):
            missing = json.loads(self.run_ros("run", "judgment", "--target", "commitment:alpha", "--executor", "provider:codex", expect=1)[1])
        self.assertEqual(missing["lifecycle"]["derived"]["state"], "failed_retryable", "启动前就失败：什么都没发出，可重试")
        from researchos_adapters.run_state import run_state_ledger
        self.assertTrue(run_state_ledger(self.tmp / RUN_LOG, "private").recovery(missing["run_id"])["retry_allowed"])

        class Crashing:
            def execute(self, request):
                raise RuntimeError("backend exploded")
        with mock.patch.object(ros, "provider_for", lambda config, scope, pid: Crashing()):
            crashed = json.loads(self.run_ros("run", "judgment", "--target", "commitment:alpha", "--executor", "provider:x", expect=1)[1])
        self.assertEqual(crashed["lifecycle"]["derived"]["state"], "failed_needs_impact_check",
                         "后端异常也落成失败，不会永远停在 running")

    def test_copy_packet_round_trip_and_executor_provenance_is_not_forgeable(self) -> None:
        pin = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.assertIn("session opened today", self.refusal("run", "judgment", "--target", "commitment:alpha",
                                                           "--executor", "copy_packet"))
        self.ros("today")
        sent = self.ros("run", "judgment", "--target", "commitment:alpha", "--executor", "copy_packet")
        self.assertIn("[!judgment]", Path(sent["packet"]).read_text(encoding="utf-8"))
        self.assertEqual(sent["lifecycle"]["derived"]["state"], "verify_delivery", "交出去的包：送达未知，只核对")
        delivered = [r["payload"]["detail"] for r in self.ledger().trajectory()
                     if r["payload"].get("detail", {}).get("action") == "context_delivered"][-1]
        self.assertEqual(delivered["service"], "unknown", "任务包只是本地文件：去向未知，不记为已外发")
        answer = self.tmp / "answer.md"
        answer.write_text("not a judgment", encoding="utf-8")
        unreadable = json.loads(self.run_ros("collect", sent["run_id"], "--file", str(answer), expect=1)[1])
        self.assertEqual(unreadable["lifecycle"]["run"], "running", "读不出的回答不终结运行，可再交一次")
        closed = self.ros("close")
        self.assertIn(sent["run_id"], closed["open_runs"], "会话结束不结束运行，收尾时列出仍在追踪的运行")
        answer.write_text(self.RUN_DRAFT.format(id="copied", pin=pin), encoding="utf-8")
        got = self.ros("collect", sent["run_id"], "--file", str(answer))
        self.assertEqual(got["lifecycle"]["derived"]["state"], "late_result_ready", "会话结束后才到的结果")
        self.assertEqual(self.ledger().candidates()[got["candidates"][0]]["payload"]["executor"], "copy_packet")
        self.assertIn("already collected", self.refusal("collect", sent["run_id"], "--file", str(answer)))
        self.assertIn("no copy-packet run", self.refusal("collect", "ros-run-forged", "--file", str(answer)))
        self.assertIn("ros run", self.refusal("propose", "judgment", "--file", str(answer), "--target",
                                              "commitment:alpha", "--executor", "provider:fake"),
                      "会话不能冒称 provider 的产出")
        self.assertIn("session Agent", self.refusal("run", "judgment", "--target", "commitment:alpha",
                                                    "--executor", "session_agent"))

    def test_cr18_closing_an_episode_is_a_receipted_decision(self) -> None:
        self.write(self.EPISODE, self.EPISODE_TEXT)
        path = self.tmp / self.EPISODE
        self.assertIn(self.EPISODE, self.live())

        # A hand edit is not a decision: without a receipt the episode stays in scope and is reported.
        self.write(self.EPISODE, self.EPISODE_TEXT.replace("open", "closed"))
        result = self.boundary()
        self.assertIn(self.EPISODE, result.scope.members, "改字段不推定关闭")
        self.assertTrue(any(self.EPISODE in problem and "without episode_closure_receipt" in problem
                            for problem in result.problems))
        self.write(self.EPISODE, self.EPISODE_TEXT)

        # The closure is a candidate first: nothing is written before admission.
        self.refusal("propose", "episode-close", "--target", "01_knowledge/projects/alpha.md", "--reason", "x")
        candidate = self.ros("propose", "episode-close", "--target", self.EPISODE,
                             "--reason", "round finished")["candidates"][0]
        self.assertEqual(path.read_text(encoding="utf-8"), self.EPISODE_TEXT)
        self.assertIn(self.EPISODE, self.live())

        closed = self.ros("admit", candidate)
        receipt_id = closed["closure_receipt"]
        self.assertTrue(receipt_id.startswith("episode-close-"))
        self.assertTrue(path.exists(), "关闭是退出取值范围，不是删除")
        text = path.read_text(encoding="utf-8")
        self.assertIn(f"episode_closure_receipt: {receipt_id}\n", text, "回执 id 写回来源 frontmatter")
        self.assertTrue(text.endswith("---\n# Round 1\nWhat this round found.\n"), "正文逐字保留")
        result = self.boundary()
        self.assertNotIn(self.EPISODE, result.scope.members, "关闭后退出 cl(n)")
        self.assertFalse([p for p in result.problems if self.EPISODE in p])
        self.assertEqual(result.snapshot.resolve(self.EPISODE)[0], self.EPISODE, "仍可作为历史证据被引用")

        # The receipt can be looked up and binds candidate, attempt, admission, staging and a met check.
        receipt = self.ros("receipt", receipt_id)
        self.assertEqual((receipt["episode"], receipt["identity"], receipt["reason"], receipt["candidate_id"],
                          receipt["checks"], receipt["revoked"]),
                         (self.EPISODE, "round-1", "round finished", candidate, ["met"], False))
        self.assertEqual(receipt["candidate_type"], "episode_close")
        self.assertTrue(receipt["attempt_id"], "关闭回执绑定提议时的 attempt")
        self.assertEqual(receipt["admission_state"]["decision_state"], "accepted")
        self.assertTrue(receipt["staging_receipt_id"].startswith("filesystem:"))
        self.refusal("receipt", "episode-close-forged")
        self.refusal("propose", "episode-close", "--target", self.EPISODE, "--reason", "again")
        self.refusal("admit", candidate)

        # Copying a receipt into another file closes neither: one receipt, one record.
        other = "01_knowledge/projects/rounds/round-2.md"
        self.write(other, text.replace("Round 1", "Round 2"))
        result = self.boundary()
        self.assertLessEqual({self.EPISODE, other}, result.scope.members)
        self.assertTrue(any("claimed by 2 records" in p for p in result.problems))
        (self.tmp / other).unlink()

        # A clean clone has no ledger: the source still says closed, and the gap is reported.
        ledger_dir = self.ledger().path.parent
        shutil.move(str(ledger_dir), str(self.tmp / "ledger-aside"))
        result = self.boundary()
        self.assertNotIn(self.EPISODE, result.scope.members, "被 Git 忽略的账缺席不重开情节")
        self.assertTrue(any("cannot be verified" in p for p in result.problems))
        shutil.rmtree(ledger_dir)
        shutil.move(str(self.tmp / "ledger-aside"), str(ledger_dir))

        # Reversible through the same staging owner; the rollback revokes the receipt for good.
        self.ros("admit", "--rollback", closed["transaction_id"])
        self.assertEqual(path.read_text(encoding="utf-8"), self.EPISODE_TEXT)
        self.assertIn(self.EPISODE, self.live())
        self.assertTrue(self.ros("receipt", receipt_id)["revoked"])
        self.write(self.EPISODE, text)  # e.g. a git checkout of the closed version
        result = self.boundary()
        self.assertIn(self.EPISODE, result.scope.members, "撤销的回执不能再关闭它")
        self.assertTrue(any("revoked" in p for p in result.problems))
        self.write(self.EPISODE, self.EPISODE_TEXT)

        # A location change neither closes an open episode nor reopens a closed one.
        moved = "01_knowledge/projects/archive/round-1.md"
        (self.tmp / moved).parent.mkdir(parents=True)
        path.rename(self.tmp / moved)
        self.assertIn(moved, self.live(), "移入 archive 目录不推定关闭")
        candidate = self.ros("propose", "episode-close", "--target", moved, "--reason", "round finished")["candidates"][0]
        self.ros("admit", candidate)
        again = "01_knowledge/projects/later/round-1.md"
        (self.tmp / again).parent.mkdir(parents=True)
        (self.tmp / moved).rename(self.tmp / again)
        result = self.boundary()
        self.assertNotIn(again, result.scope.members, "身份不含目录：搬动已关闭的情节不重开它")
        self.assertFalse([p for p in result.problems if again in p])

    def test_a_closure_keeps_crlf_and_undoes_itself_when_it_cannot_be_recorded(self) -> None:
        crlf = self.EPISODE_TEXT.replace("\n", "\r\n")
        (self.tmp / self.EPISODE).parent.mkdir(parents=True, exist_ok=True)
        (self.tmp / self.EPISODE).write_bytes(crlf.encode("utf-8"))
        candidate = self.ros("propose", "episode-close", "--target", self.EPISODE, "--reason", "done")["candidates"][0]
        original = Ledger.effect

        def broken(*args, **kwargs):
            raise OSError("disk full")
        Ledger.effect = broken
        try:
            message = self.refusal("admit", candidate)
        finally:
            Ledger.effect = original
        self.assertIn("rolled back", message)
        self.assertEqual((self.tmp / self.EPISODE).read_bytes(), crlf.encode("utf-8"), "未记账的写入被撤回")
        self.assertFalse(self.ledger().candidates()[candidate]["payload"].get("admitted"))
        self.ros("admit", candidate)
        landed = (self.tmp / self.EPISODE).read_bytes().decode("utf-8")
        self.assertNotIn("\n", landed.replace("\r\n", ""), "行尾保持 CRLF")
        self.assertTrue(landed.endswith("---\r\n# Round 1\r\nWhat this round found.\r\n"))
        self.assertNotIn(self.EPISODE, self.live())

    def test_propose_and_admit_read_episode_state_the_same_way(self) -> None:
        self.write(self.EPISODE, "---\ntitle: R\nepisode_state: open\nepisode_state: open  # still\n---\n# R\n")
        self.refusal("propose", "episode-close", "--target", self.EPISODE, "--reason", "x")
        self.write(self.EPISODE, "---\ntitle: R\nepisode_state: in-progress\n---\n# R\n")
        self.refusal("propose", "episode-close", "--target", self.EPISODE, "--reason", "x")

    def test_a_closure_proposal_binds_the_version_it_was_made_on(self) -> None:
        self.write(self.EPISODE, self.EPISODE_TEXT)
        candidate = self.ros("propose", "episode-close", "--target", self.EPISODE, "--reason", "done")["candidates"][0]
        self.write(self.EPISODE, self.EPISODE_TEXT + "A late finding.\n")
        self.refusal("admit", candidate)
        self.assertIn(self.EPISODE, self.live(), "过期的提议不落地")
        self.assertIn("A late finding.", (self.tmp / self.EPISODE).read_text(encoding="utf-8"))

    # admission chain (HJ-2 / HJ-3 / HJ-3b) ---------------------------------------------------------
    def test_hj1_ros_admission_requires_human_decision_record(self) -> None:
        candidate = self.propose_beta()
        self.assertEqual(self.admit_decisions(), [], "提议本身不是决定")
        self.assertFalse(any(row["kind"] == "effect" for row in self.ledger().trajectory()), "提议不产生效果")

        # Run by an agent or script (no terminal): recorded as asserted by the invoker, not as the researcher's.
        self.ros("admit", candidate)
        rows = self.ledger().trajectory()
        decision = self.admit_decisions()[-1]
        self.assertEqual(decision["payload"]["permission_state"], "invoker_asserted")
        self.assertTrue(decision["payload"]["detail"]["decision_evidence"].startswith("channel:non_tty"))
        self.assertEqual(decision["payload"]["candidate_ids"], [candidate])
        effect = next(row for row in rows if row["kind"] == "effect"
                      and row["payload"]["changes"][0]["change"] == "judgment_admitted")
        attempt = next(row for row in rows if row["id"] == effect["payload"]["attempt_id"])
        self.assertEqual((attempt["kind"], attempt["payload"]["decision_id"], attempt["payload"]["status"]),
                         ("attempt", decision["id"], "applied"), "决定 → 尝试 → 效果")
        self.assertLess(rows.index(decision), rows.index(attempt))
        self.assertLess(rows.index(attempt), rows.index(effect))

        # A target that is not there is refused before anything is decided.
        before = len(self.admit_decisions())
        self.refusal("admit", "--confirm", "j-does-not-exist")
        self.refusal("admit", "--reconfirm", "j-nope")
        self.assertEqual(len(self.admit_decisions()), before, "被拒的准入不留下决定")

    def test_only_a_terminal_answer_is_recorded_as_the_researchers_decision(self) -> None:
        self.add_alpha_judgment()

        self.assertIn("declined at the terminal", self.refusal("admit", "--confirm", "j-alpha-scope", answer="n"))
        self.assertEqual(self.admit_decisions(), [], "终端拒绝即不准入，也不留决定")
        self.ros("admit", "--confirm", "j-alpha-scope", answer="y")
        decision = self.admit_decisions()[-1]
        self.assertEqual((decision["payload"]["permission_state"], decision["payload"]["detail"]["decision_evidence"]),
                         ("researcher_decision", "terminal_confirmation"))

    def test_a_candidate_declined_at_the_terminal_is_recorded_rejected_and_listed_at_close(self) -> None:
        """Soul §1：研究者在终端对候选答否也是她的决定，记录在案，候选终止为 rejected，来源不变。"""
        self.ros("today")
        candidate = self.propose_beta()
        card = (self.tmp / self.CARD).read_bytes()
        before = len(self.ledger().trajectory())
        out = self.ros("admit", candidate, answer="n")
        rows = self.ledger().trajectory()
        self.assertEqual(len(rows), before + 1, "只记一条决定，没有尝试或效果")
        decision = rows[-1]
        self.assertEqual(decision["id"], out["decision_id"])
        payload = decision["payload"]
        self.assertEqual((decision["kind"], payload["operation"], payload["permission_state"],
                          payload["detail"]["decision_evidence"], payload["detail"]["action"], payload["candidate_ids"]),
                         ("decision", "retire", "researcher_decision", "terminal_declined", "candidate_rejected",
                          [candidate]))
        stored = self.ledger().candidates()[candidate]["payload"]
        self.assertEqual((stored["admission_state"]["decision_state"], stored["admission_state"]["mutation_state"],
                          stored["declined_by"]), ("rejected", "not_requested", decision["id"]))
        self.assertEqual((self.tmp / self.CARD).read_bytes(), card, "拒绝不写入来源")
        # A declined candidate stays declined: admitting it again, at the terminal or not, needs a new proposal.
        self.assertIn("propose again", self.refusal("admit", candidate, answer="y"))
        self.assertIn("propose again", self.refusal("admit", candidate))
        self.assertEqual(len(self.ledger().trajectory()), before + 1)
        self.assertEqual((self.tmp / self.CARD).read_bytes(), card)
        data, text = self.capture_ros("close")
        self.assertEqual([(r["candidate_id"], r["how"], r["object_id"]) for r in data["declined_candidates"]],
                         [(candidate, "admit_candidate", "j-beta-next")])
        self.assertIn(candidate, text)
        self.assertEqual(data["pending_candidates"], [], "a declined candidate is decided, not pending")

    def test_close_lists_candidates_returned_in_the_session_and_not_yet_decided(self) -> None:
        self.ros("today")
        candidate = self.propose_beta()
        card = (self.tmp / self.CARD).read_bytes()
        data, text = self.capture_ros("close")
        self.assertEqual(data["pending_candidates"], [{"candidate_id": candidate, "target": self.CARD}])
        self.assertIn(candidate, text)
        self.assertEqual((self.tmp / self.CARD).read_bytes(), card, "listing a candidate decides nothing")

    def test_declining_a_closure_a_rule_revision_or_a_public_admission_at_the_terminal(self) -> None:
        session = self.ros("today")["session_id"]
        self.write(self.EPISODE, self.EPISODE_TEXT)
        closure = self.ros("propose", "episode-close", "--target", self.EPISODE, "--reason", "done")["candidates"][0]
        rule = self.ros("propose", "rule", "--file", self.revision_file(
            dict(self.status_descriptor(), version="1.1.0"), session))["candidates"][0]
        for candidate in (closure, rule):
            self.assertTrue(self.ros("admit", candidate, answer="n")["declined"])
            self.assertEqual(self.ledger().candidates()[candidate]["payload"]["admission_state"]["decision_state"],
                             "rejected")
        self.assertEqual((self.tmp / self.EPISODE).read_text(encoding="utf-8"), self.EPISODE_TEXT)
        self.assertEqual(self.status_descriptor()["version"], "1.0.0", "拒绝不改规则")
        # The public starter admits nothing, so it asks nothing: it shows the planned change and records nothing.
        self.edit_config(runtime_scope="public_starter")
        public = self.propose_beta()
        before = self.ledger().trajectory()
        self.assertFalse(self.ros("admit", public, answer="n")["promoted"])
        self.assertEqual(before, self.ledger().trajectory())
        self.assertEqual(self.ledger().candidates()[public]["payload"]["admission_state"]["decision_state"], "proposed")

    def test_a_refused_write_is_recorded_as_a_refused_attempt(self) -> None:
        candidate = self.propose_beta()
        original = ros._write_through_staging

        def refuse(*args, **kwargs):
            raise ros.FilesystemStagingError("filesystem_staging_invalid")
        ros._write_through_staging = refuse
        try:
            self.refusal("admit", candidate)
        finally:
            ros._write_through_staging = original
        decision = self.admit_decisions()[-1]
        attempts = [row for row in self.ledger().trajectory()
                    if row["kind"] == "attempt" and row["payload"]["decision_id"] == decision["id"]]
        self.assertEqual([row["payload"]["status"] for row in attempts], ["refused"], "失败如实记账")
        self.assertFalse(any(row["kind"] == "effect" and row["payload"]["attempt_id"] == attempts[0]["id"]
                             for row in self.ledger().trajectory()))

    def test_the_public_starter_shows_a_write_instead_of_making_it(self) -> None:
        """公开 starter 不准入长期来源，写入以复制回退呈现。"""
        self.edit_config(runtime_scope="public_starter")
        before = (self.tmp / self.CARD).read_bytes()
        candidate = self.propose_beta()
        shown = self.ros("admit", candidate)
        self.assertEqual(shown["promoted"], False)
        self.assertIn("+> [!judgment] j-beta-next", shown["planned_diff"])
        self.assertEqual((self.tmp / self.CARD).read_bytes(), before, "未写入")
        self.assertEqual(self.admit_decisions(), [], "未作决定")
        self.assertEqual(self.ledger().candidates()[candidate]["payload"]["admission_state"]["mutation_state"],
                         "not_requested")

    def test_hj2_ros_propose_creates_candidate_envelope_not_private_candidate_store(self) -> None:
        candidate = self.propose_beta()
        ledger = self.ledger()
        self.assertFalse((self.tmp / "06_active_context/work_state/ros/candidates").exists(), "没有私有候选目录")
        self.assertTrue(ledger.candidates_path.exists() and ledger.candidates_path in ledger.family())
        record = ledger.candidates()[candidate]
        envelope = record["envelope"]
        self.assertEqual((envelope["candidate_type"], envelope["required_confirmation"]), ("judgment", "researcher"))
        axes = record["payload"]["admission_state"]
        three = ("decision_state", "mutation_state", "validation_state")
        self.assertEqual({k: axes[k] for k in three},
                         {"decision_state": "proposed", "mutation_state": "not_requested",
                          "validation_state": "unvalidated"}, "提议时就是 proposed")
        self.assertEqual({k: envelope["admission_state"][k] for k in three}, {k: axes[k] for k in three},
                         "每条候选只有一份准入状态")
        self.ros("admit", candidate)
        record = self.ledger().candidates()[candidate]
        axes = record["payload"]["admission_state"]
        self.assertEqual({k: record["envelope"]["admission_state"][k] for k in three}, {k: axes[k] for k in three})
        self.assertEqual((axes["decision_state"], axes["mutation_state"], axes["validation_state"],
                          axes["authority_role"]), ("accepted", "applied", "passed", "normative"), "四轴分立")
        payload = self.ledger().candidates()[candidate]["payload"]
        self.assertFalse({"admitted", "confirmed"} & set(payload), "不存合并的「已确认」状态")
        self.assertIn("already admitted (applied)", self.refusal("admit", candidate))

    def test_hj3_candidate_is_visible_before_any_source_write(self) -> None:
        before = (self.tmp / self.CARD).read_bytes()
        candidate = self.propose_beta()
        self.assertEqual((self.tmp / self.CARD).read_bytes(), before, "提议不写来源")
        self.assertNotIn("j-beta-next", self.boundary().snapshot.judgments)
        self.assertEqual(self.ledger().candidates()[candidate]["envelope"]["summary"], "Survey the reviewers first")
        self.ros("admit", candidate)
        self.assertIn("j-beta-next", self.boundary().snapshot.judgments, "准入后才进入来源")

    def test_hj3b_ros_admit_writes_through_staging_with_rollback_receipt(self) -> None:
        before = (self.tmp / self.CARD).read_bytes()
        candidate = self.propose_beta()
        landed = self.ros("admit", candidate)
        after = (self.tmp / self.CARD).read_bytes()
        stored = self.tmp / "06_active_context/work_state/.artifact-rollbacks" / landed["transaction_id"] / "receipt.json"
        receipt = json.loads(stored.read_text(encoding="utf-8"))
        self.assertEqual(receipt["receipt_id"], landed["receipt_id"])
        change = next(c for c in receipt["changes"] if c["path"] == self.CARD)
        self.assertEqual((change["prior_digest"], change["new_digest"]),
                         (hashlib.sha256(before).hexdigest(), hashlib.sha256(after).hexdigest()), "精确目标与前后哈希")
        effects = [row for row in self.ledger().trajectory() if row["kind"] == "effect"
                   and row["payload"]["detail"].get("receipt_id") == landed["receipt_id"]]
        self.assertEqual(len(effects), 1, "账里的 effect 绑定回执")

        self.ros("admit", "--rollback", landed["transaction_id"])
        self.assertEqual((self.tmp / self.CARD).read_bytes(), before, "回滚恢复前像")
        self.assertNotIn("j-beta-next", self.boundary().snapshot.judgments)
        trajectory = self.ledger().trajectory()
        self.assertTrue(any(row["id"] == effects[0]["id"] for row in trajectory), "回滚不删历史")
        self.assertTrue(any(row["kind"] == "effect" and any(c["change"] == "writeback_rolled_back"
                                                            for c in row["payload"]["changes"]) for row in trajectory))
        axes = self.ledger().candidates()[candidate]["payload"]["admission_state"]
        self.assertEqual(axes["mutation_state"], "rolled_back", "候选的修改轴记下回滚")
        self.assertIn("already admitted (rolled_back)", self.refusal("admit", candidate))

        # The ledger's admitted set honours the rollback: the same block pasted back needs confirming.
        self.write(self.CARD, after.decode("utf-8"))
        self.assertIn("confirm_judgment_change", self.open_rules(self.boundary()), "回滚过的准入不算准入")

    def test_the_public_starter_refuses_to_roll_back_a_write(self) -> None:
        # align-v8 L1: a rollback receipt left by an earlier private run must not let the copy-only starter write.
        landed = self.ros("admit", self.propose_beta())
        after = (self.tmp / self.CARD).read_bytes()
        self.edit_config(runtime_scope="public_starter")
        self.assertIn("copy-only", self.refusal("admit", "--rollback", landed["transaction_id"]))
        self.assertEqual((self.tmp / self.CARD).read_bytes(), after, "公开 starter 不回滚来源")

    # completion and Out (CC-7 / CC-8) -------------------------------------------------------------
    def test_cc7_run_reports_complete_only_when_scope_is_closed_or_held(self) -> None:
        view = self.ros("today")
        self.assertFalse(view["completion"]["done"])
        closed = self.ros("close")
        self.assertEqual(closed["outcome"], "human_stopped", "未完成时收尾：如实记为研究者喊停")
        self.assertTrue(closed["completion"]["unfinished"], "逐项列出未完成的要求")
        self.assertEqual(closed["scope"]["scope_node"], "/", "完成报告给出归属节点")
        self.assertIn("coverage_unknown_in_scope", closed["coverage"], "与两类覆盖未知及分母")
        episode = [r for r in self.ledger().records("episodes") if r.get("end")][-1]
        self.assertEqual(episode["outcome"], "human_stopped", "结果分类记入账")

        view = self.ros("today", today=date(2026, 9, 21))
        self.cancel_unfinished(view)
        self.assertEqual(self.ros("close", today=date(2026, 9, 21))["outcome"], "complete", "范围内全部关闭")

    def test_complete_with_held_lists_each_held_item(self) -> None:
        issue = self.undecidable()  # asked about a judgment that no longer exists: its key left the scope
        view = self.ros("today")
        deferred = next(row for row in view["completion"]["unfinished"])
        self.ros("decide", deferred["short_id"], "defer", "--until", "2026-09-30", answer="y")
        self.cancel_unfinished(self.ros("today"))
        closed = self.ros("close")
        self.assertEqual(closed["outcome"], "complete_with_held", "等待已登记触发的要求不阻塞完成，但如实保留")
        self.assertEqual([(row["issue_id"], row["kind"], row["trigger"]) for row in closed["held"]],
                         [(deferred["issue_id"], "trigger", "date:2026-09-30")], "每项附重开触发")
        self.assertGreaterEqual(closed["completion"]["unowned_open"], 1,
                                "主体已不存在的问题归属无定义（D0 第二类），单独计数，既不在范围内也不算范围外")
        self.assertIn(issue[:10], [row["short_id"] for row in closed["completion"]["unowned"]])
        self.assertTrue(closed["pending_questions"], "仍待回答的问题逐项列出，不论是否在本次范围内")
        self.assertEqual(self.boundary().states["issues"][issue]["status"], "waiting")

    def test_cc7_defer_channel_controls_completion_and_terminal_decline_does_not_write(self) -> None:
        view = self.ros("today")
        item = view["completion"]["unfinished"][0]
        issue = item["issue_id"]
        self.cancel_unfinished(view, keep=(issue,))
        self.ros("decide", item["short_id"], "defer", "--until", "2026-09-30")
        report = self.ros("today")["completion"]
        self.assertFalse(report["done"])
        self.assertIn(issue, [r["issue_id"] for r in report["unfinished"]])
        decision = self.ledger().derive_states()["issues"][issue]["decision"]
        self.assertEqual(decision["permission_state"], "invoker_asserted")
        self.assertIn("channel:non_tty", decision["detail"]["decision_evidence"])
        before = self.ledger().trajectory()
        self.assertIn("declined", self.refusal("decide", item["short_id"], "defer", "--until", "2026-09-30", answer="n"))
        self.assertEqual(before, self.ledger().trajectory())
        self.ros("decide", item["short_id"], "defer", "--until", "2026-09-30", answer="y")
        report = self.ros("today")["completion"]
        self.assertTrue(report["done"])
        self.assertEqual([r["issue_id"] for r in report["waiting"]], [issue])
        decision = self.ledger().derive_states()["issues"][issue]["decision"]
        self.assertEqual((decision["permission_state"], decision["detail"]["decision_evidence"]),
                         ("researcher_decision", "terminal_confirmation"))
        self.assertEqual(self.ros("close")["outcome"], "complete_with_held")
        # Old decide defer records claimed researcher permission without channel evidence.
        from researchos_kernel.boundary import completion
        from researchos_kernel.scope import FrozenScope
        state = self.ledger().derive_states()["issues"][issue]
        state["decision"]["detail"].pop("decision_evidence")
        frozen = FrozenScope(node="/", members=frozenset({self.binding(issue)}), cross=(), frozen_at="")
        self.assertFalse(completion({issue: state}, self.ledger().requirements(), frozen, today=TODAY)["done"])

    def test_cc7_researcher_answers_narrow_and_defer_allow_waiting_but_invoker_answers_do_not(self) -> None:
        from researchos_kernel.boundary import completion, outcome
        from researchos_kernel.scope import FrozenScope
        issue = self.undecidable()
        question = self.question_of(issue)
        frozen = FrozenScope(node="/", members=frozenset({"judgment:j-alpha-scope"}), cross=(), frozen_at="")
        before = self.ledger().records_path.read_bytes()
        for option in ("narrow", "defer"):
            for terminal in (False, True):
                with self.subTest(option=option, terminal=terminal):
                    self.ledger().records_path.write_bytes(before)
                    args = ("answer", question["short_id"], option)
                    if option == "defer":
                        args += ("--until", "2026-09-30")
                    self.ros(*args, answer="y" if terminal else None)
                    state = self.ledger().derive_states()["issues"][issue]
                    report = completion({issue: state}, self.ledger().requirements(), frozen, today=TODAY)
                    self.assertEqual(report["done"], terminal)
                    self.assertEqual(len(report["waiting"]), int(terminal))
                    self.assertEqual(outcome(report, stopped_by_researcher=True),
                                     "complete_with_held" if terminal else "human_stopped")

    def test_cc7_special_requirements_exclude_done_in_every_unclosed_state(self) -> None:
        from researchos_kernel.boundary import completion, outcome
        from researchos_kernel.ledger import binding
        from researchos_kernel.scope import FrozenScope
        frozen = FrozenScope(node="/", members=frozenset({"commitment:alpha", "judgment:j"}), cross=(), frozen_at="")
        cases = [("spec:previous-unrecomputable", "", {}), ("field:alpha#question", "", {}),
                 ("judgment:j", "confirm_judgment_change", {}), ("coverage:future_rule", "future_rule", {}),
                 ("commitment:alpha", "future_rule", {"special": "coverage_unevaluated"})]
        for subject, rule, unknowns in cases:
            for status in ("open", "deferred", "waiting", "held", "resolved", "cancelled"):
                with self.subTest(subject=subject, status=status):
                    bound = binding("special", 1)
                    self.ledger().transition(bound, "open", "opened", requirement={"binding": subject, "rule_id": rule})
                    self.ledger().decision("defer" if status == "deferred" else "ask", bound=bound,
                                           permission_state="researcher_decision",
                                           detail={"until": "2026-09-30", "how": "answer:defer",
                                                   "decision_evidence": "terminal_confirmation"})
                    self.ledger().transition(bound, "waiting" if status == "held" else status, "test",
                                             until="2026-09-30",
                                             reopen_trigger="answer:pending" if status == "held" else "date:2026-09-30")
                    state = self.ledger().derive_states()["issues"]["special"]
                    report = completion({"special": state}, self.ledger().requirements(), frozen,
                                        today=TODAY, unknowns=unknowns)
                    closed = status in {"resolved", "cancelled"}
                    self.assertEqual(report["done"], closed)
                    self.assertEqual(outcome(report, stopped_by_researcher=True), "complete" if closed else "human_stopped")
                    if not closed:
                        self.assertEqual(outcome(report, stopped_by_researcher=False, exhausted_components=["bnd"]),
                                         "budget_stopped")

    def test_cc7_executor_wait_and_defer_cannot_reuse_researcher_permission(self) -> None:
        from researchos_kernel.boundary import completion
        from researchos_kernel.ledger import binding
        from researchos_kernel.scope import FrozenScope
        frozen = FrozenScope(node="/", members=frozenset({"commitment:alpha"}), cross=(), frozen_at="")
        bound = binding("work", 1)
        self.ledger().transition(bound, "open", "opened", requirement={"binding": "commitment:alpha"})
        self.ledger().decision("defer", bound=bound, permission_state="researcher_decision", detail={"until": "2026-09-30", "decision_evidence": "terminal_confirmation"})
        self.ledger().transition(bound, "deferred", "researcher_decision:defer", until="2026-09-30")
        report = completion(self.ledger().derive_states()["issues"], self.ledger().requirements(), frozen, today=TODAY)
        self.assertTrue(report["done"])
        for status, trigger in (("waiting", "event:in-scope-dependency"), ("deferred", "")):
            with self.subTest(status=status):
                self.ledger().transition(bound, status, "executor", until="2026-09-30", reopen_trigger=trigger)
                report = completion(self.ledger().derive_states()["issues"], self.ledger().requirements(), frozen, today=TODAY)
                self.assertFalse(report["done"])
                self.assertEqual(report["waiting"], [])
        # A decision for an older generation must not justify a newer transition either.
        self.ledger().decision("defer", bound=bound, permission_state="researcher_decision", detail={"until": "2026-09-30", "decision_evidence": "terminal_confirmation"})
        self.ledger().transition(binding("work", 2), "deferred", "executor", until="2026-09-30")
        self.assertFalse(completion(self.ledger().derive_states()["issues"], self.ledger().requirements(), frozen,
                                    today=TODAY)["done"])

    def test_close_without_frozen_scope_is_never_complete(self) -> None:
        view = self.ros("today")
        self.cancel_unfinished(view)
        session = next(self.tmp.rglob(f"sessions/{view['session_id']}.json"))
        payload = json.loads(session.read_text(encoding="utf-8"))
        payload.pop("scope_members", None)  # a snapshot written before scopes were frozen
        session.write_text(json.dumps(payload), encoding="utf-8")
        closed = self.ros("close")
        self.assertEqual(closed["outcome"], "human_stopped", "没有冻结范围就无从判定完成")
        self.assertFalse(closed["completion"]["scope_frozen"])

    def test_repeated_today_keeps_the_session_and_its_frozen_scope(self) -> None:
        first = self.ros("today")
        again = self.ros("today")
        self.assertEqual(first["session_id"], again["session_id"], "同日再次 today 延续同一会话（H7：范围不重冻）")
        starts = [r for r in self.ledger().records("episodes") if r.get("episode_id") == first["session_id"] and r.get("start")]
        self.assertEqual(len(starts), 1)
        self.ros("close")
        self.assertNotEqual(self.ros("today")["session_id"], first["session_id"], "收尾之后开新会话")

    def test_passed_defer_date_is_work_not_handover(self) -> None:
        view = self.ros("today")
        deferred = view["completion"]["unfinished"][0]
        self.ros("decide", deferred["short_id"], "defer", "--until", "2026-09-21")
        self.cancel_unfinished(self.ros("today"), keep=(deferred["issue_id"],))
        closed = self.ros("close", "--session", view["session_id"], today=date(2026, 9, 22))
        self.assertEqual(closed["outcome"], "human_stopped", "延期日期已到，这项又是待办")
        self.assertIn(deferred["issue_id"], [r["issue_id"] for r in closed["completion"]["unfinished"]])

    def test_completion_classifies_handover_and_closures_conservatively(self) -> None:
        from researchos_kernel.boundary import completion
        from researchos_kernel.scope import FrozenScope, Placement
        frozen = FrozenScope(node="/", members=frozenset({"a.md", "b.md"}), cross=(), frozen_at="")
        states = {"w": {"status": "waiting", "reopen_trigger": "", "summary": ""},
                  "u": {"status": "open", "summary": ""}}
        requirements = {"w": {"binding": "a.md"}, "u": {"binding": "c.md"}}
        forged = Placement(key="c.md", scope="/x", episode_state="closed", closure_receipt="r", verified=False)
        report = completion(states, requirements, frozen, today=TODAY, placements={"c.md": forged})
        self.assertEqual({r["issue_id"] for r in report["unfinished"]}, {"w", "u"},
                         "无触发的等待不算移交；未核实的关闭回执不把工作挤出范围")
        self.assertFalse(report["done"])
        empty = completion({}, {}, FrozenScope(node="/", members=frozenset(), cross=(), frozen_at=""), today=TODAY)
        self.assertFalse(empty["done"], "空范围不报完成")

    def test_cc8_partial_scan_never_reports_goal_completion(self) -> None:
        descriptor = json.loads((self.tmp / "config/extensions/rules/status-verify.json").read_text(encoding="utf-8"))
        descriptor.update(id="future_rule", trigger={"when": "future_condition"})  # no evaluator in this kernel
        self.write("config/extensions/rules/future-rule.json", json.dumps(descriptor))
        view = self.ros("today")
        coverage = [row["issue_id"] for row in view["completion"]["unfinished"]
                    if self.boundary().requirements.get(row["issue_id"], {}).get("binding", "").startswith("coverage:")]
        self.assertTrue(coverage, "声明却未评估的规则登记为覆盖未知要求")
        self.cancel_unfinished(view, keep=coverage)
        closed = self.ros("close")
        self.assertEqual(closed["outcome"], "human_stopped", "有输入未被评估，局部扫描不等于目标完成")
        # A requirement born after the session started is not this session's work (scope frozen at today).
        self.ros("today", today=date(2026, 9, 21))
        self.add_commitment("### Late\n\n- id: late\n- responsibility: lead\n- state: mainline\n"
                            "- source_path: 01_knowledge/projects/late.md\n")
        closed = self.ros("close", today=date(2026, 9, 21))
        self.assertGreaterEqual(closed["completion"]["out_of_scope_open"], 1, "范围外未决单列")
        self.assertNotIn("late", json.dumps(closed["completion"]["unfinished"]))
        # Interrupted work is not lost: the next session still carries the unfinished requirement.
        self.assertIn(coverage[0], [r["issue_id"] for r in self.ros("today", today=date(2026, 9, 22))["completion"]["unfinished"]])

    def test_a_closed_episode_derives_no_new_requirements(self) -> None:
        pinned = self.boundary().snapshot.resolve("01_knowledge/projects/alpha.md")[1][:8]
        self.write(self.EPISODE, self.EPISODE_TEXT + f"\n> [!judgment] j-ep\n> 结论：x\n> 依据：01_knowledge/projects/alpha.md@{pinned}\n")
        self.ros("admit", "--confirm", "j-ep", answer="y")
        candidate = self.ros("propose", "episode-close", "--target", self.EPISODE, "--reason", "done")["candidates"][0]
        self.ros("admit", candidate)
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v2\n")
        result = self.boundary()
        recheck = [i for i, st in result.states["issues"].items()
                   if result.requirements.get(i, {}).get("binding") == "judgment:j-ep"
                   and result.requirements[i].get("rule_id") == "basis_recheck"]
        self.assertEqual(recheck, [], "已关闭情节退出 cl(n)：依据变了也不再导出复查要求（D0）")
        self.assertGreaterEqual(result.suppressed, 1)

    def test_close_separates_fact_and_judgment_changes(self) -> None:
        self.ros("today")
        self.write("01_knowledge/projects/beta.md", "---\ntitle: Beta\n---\n# Beta\nnew fact\n")
        text = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        text = text.replace("- next_step: Wait for reviews", "- next_step: Wait for reviews\n- question: What do reviewers dispute?")
        text = text.replace("- last_verified: 2026-08-01", "- last_verified: 2026-09-20")
        self.write("06_active_context/research-portfolio.md", text)
        self.add_alpha_judgment()
        closed = self.ros("close")
        self.assertIn("01_knowledge/projects/beta.md", closed["fact_files"])
        self.assertEqual([(r["commitment_id"], r["field"]) for r in closed["judgment_fields"]], [("beta", "question")])
        self.assertIn(("beta", "last_verified"), [(r["commitment_id"], r["field"]) for r in closed["fact_fields"]])
        self.assertEqual([r["judgment_id"] for r in closed["judgment_changes"]], ["j-alpha-scope"])

    def test_today_explains_exact_changes_and_related_requirements(self) -> None:
        self.ros("today", "--for", "alpha")
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\nEvidence v2\n")
        self.write("01_knowledge/projects/new.md", "---\ntitle: New\n---\nA new fact\n")
        (self.tmp / "01_knowledge/projects/beta.md").unlink()
        self.write("06_active_context/research-portfolio.md", PORTFOLIO.replace("2026-09-22", "2026-09-23"))
        view, text = self.capture_ros("--lang", "zh-CN", "today", "--for", "alpha")
        details = view["change_details"]
        self.assertEqual((details["baseline"], details["scope"]), ("previous_boundary", "observed_graph"))
        rows = {r["ref"]: r for r in details["items"]}
        self.assertEqual(rows["01_knowledge/projects/alpha.md"]["change"], "modified")
        self.assertEqual(rows["01_knowledge/projects/new.md"]["change"], "added")
        self.assertEqual(rows["01_knowledge/projects/beta.md"]["change"], "removed")
        self.assertEqual(rows["01_knowledge/projects/alpha.md"]["title"], "Alpha")
        self.assertTrue(rows["commitment:alpha"]["related_requirements"])
        self.assertTrue(rows["01_knowledge/projects/alpha.md"]["related_requirements"],
                        "the source card exposes its commitment's current pending requirements")
        self.assertIn("相对上一个 ros 边界", text)
        self.assertIn("本轮全图变化", text)  # --for must not mislabel global observations as focused changes.
        self.assertIn("不表示由本次修改触发", text)
        self.assertEqual(view["changed"], {kind: sum(r["change"] == kind for r in rows.values())
                                           for kind in ("added", "modified", "removed")})
        self.assertEqual(self.ros("today", "--for", "alpha")["change_details"]["items"], [])

    def test_today_change_list_is_complete_in_json_and_all_with_visible_truncation(self) -> None:
        self.ros("today")
        for i in range(12):
            self.write(f"01_knowledge/projects/new-{i:02}.md", f"---\ntitle: New {i}\n---\nFact\n")
        view, text = self.capture_ros("--lang", "en", "today")
        self.assertEqual(len(view["change_details"]["items"]), 12)
        self.assertIn("2 more changes not expanded", text)
        self.assertIn("Added/newly observed: New 0", text)
        self.assertNotIn("new-11.md", text)
        # Advance again: --all must show every change in this invocation, not recover an old cursor.
        for i in range(12):
            self.write(f"01_knowledge/projects/new-{i:02}.md", f"---\ntitle: New {i}\n---\nChanged\n")
        view, text = self.capture_ros("--lang", "en", "today", "--all")
        self.assertEqual(len(view["change_details"]["items"]), 12)
        self.assertIn("new-11.md", text)
        self.assertNotIn("more changes not expanded", text)

    def test_close_explains_file_deletion_and_fact_field_values_without_admission(self) -> None:
        self.ros("today")
        self.write("01_knowledge/projects/new.md", "---\ntitle: New\n---\nFact\n")
        (self.tmp / "01_knowledge/projects/beta.md").unlink()
        self.write("06_active_context/research-portfolio.md", PORTFOLIO.replace(
            "- next_step: Wait for reviews", "- next_step: Read returned reviews").split("### Gamma Closed")[0])
        # An intervening command advances the graph cursor, not the frozen session baseline.
        self.ros("today")
        before_candidates = self.ledger().candidates()
        closed, text = self.capture_ros("--lang", "en", "close")
        details = closed["change_details"]
        self.assertTrue(details["baseline_available"])
        self.assertEqual(details["baseline"], "session_start")
        self.assertEqual(details["removed_commitments"], ["gamma"])
        changes = {r["ref"]: r["change"] for r in details["files"]}
        self.assertEqual(changes["01_knowledge/projects/new.md"], "added")
        self.assertEqual(changes["01_knowledge/projects/beta.md"], "removed")
        self.assertIn("Wait for reviews → Read returned reviews", text)
        self.assertIn("Commitment gamma is absent", text)
        self.assertEqual(closed["judgment_fields"], [])
        self.assertEqual(self.ledger().candidates(), before_candidates)

    def test_close_unknown_baseline_does_not_claim_no_changes(self) -> None:
        session = self.ros("today")["session_id"]
        next(self.tmp.rglob(f"sessions/{session}.json")).unlink()
        closed, text = self.capture_ros("--lang", "en", "close")
        self.assertFalse(closed["change_details"]["baseline_available"])
        self.assertIsNone(closed["change_details"]["files"])
        self.assertIsNone(closed["change_details"]["removed_commitments"])
        self.assertNotEqual(closed["outcome"], "complete")
        changes_section = text.split("Graph-wide file changes since session start", 1)[1].split("Fact-class changes", 1)[0]
        self.assertIn(closed["note"], changes_section)
        self.assertNotIn("  None", changes_section)

    def test_close_lists_all_files_and_chinese_fact_values(self) -> None:
        self.ros("today")
        for i in range(12):
            self.write(f"01_knowledge/projects/new-{i:02}.md", f"---\ntitle: New {i}\n---\nFact\n")
        self.write("06_active_context/research-portfolio.md", PORTFOLIO.replace("Wait for reviews", "Read reviews"))
        closed, text = self.capture_ros("--lang", "zh-CN", "close")
        self.assertEqual(len(closed["change_details"]["files"]), 12)  # portfolio fields have their own projection
        self.assertIn("new-11.md", text)
        self.assertIn("承诺 beta 的 next_step：Wait for reviews → Read reviews", text)

    def test_decide_defer_hides_until_date_and_cancel_binds_one_read_set(self) -> None:
        issue = self.open_rules(self.boundary())["status_verify"][0]
        self.ros("decide", issue[:10], "defer", "--until", "2026-09-25")
        view = self.ros("today")
        work = lambda v: json.dumps([v["today"], v["decision"], v["needs_review"], v["network"]])
        self.assertNotIn(issue, work(view), "延期期间不作为待办出现")
        self.assertIn(issue, [row["issue_id"] for row in view["completion"]["unfinished"]], "非终端延期仍是未完成工作")
        later = self.ros("today", today=date(2026, 9, 26))
        self.assertIn(issue, work(later))
        self.ros("decide", issue[:10], "cancel", "--reason", "survey paused", answer="y")
        self.assertEqual(self.boundary().states["issues"][issue]["status"], "cancelled")

    def test_an_unevaluated_rule_never_resolves_its_own_requirements(self) -> None:
        """A broken, disabled or out-of-scope descriptor says nothing about the requirements it opened."""
        issue = self.open_rules(self.boundary())["deadline_warning"][0]
        descriptor = next(p for p in (self.tmp / "config/extensions/rules").glob("*.json")
                          if json.loads(p.read_text(encoding="utf-8"))["id"] == "deadline_warning")
        descriptor.write_text("{ broken", encoding="utf-8")
        result = self.boundary()
        self.assertEqual(result.states["issues"][issue]["status"], "open", "a broken rule must not close its issues")
        self.assertTrue(any("deadline-warning" in problem or "deadline_warning" in problem
                            for problem in result.problems))
        checks = [row for row in self.ledger().trajectory() if row["kind"] == "check"]
        self.assertEqual(checks[-1]["payload"]["result"], "not_evaluated")

    def test_a_new_due_date_advances_the_same_requirement(self) -> None:
        """Identity is the commitment, not the date; otherwise a deferral is lost to a locator change."""
        issue = self.open_rules(self.boundary())["deadline_warning"][0]
        self.ros("decide", issue[:10], "defer", "--until", "2026-09-25")
        self.assertEqual(self.boundary().states["issues"][issue]["status"], "deferred")
        text = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        self.write("06_active_context/research-portfolio.md", text.replace("2026-09-22", "2026-09-23"))
        result = self.boundary()
        self.assertEqual(self.open_rules(result)["deadline_warning"], [issue], "no second requirement is minted")
        self.assertEqual(result.states["issues"][issue]["generation"], 2)

    def test_a_second_rule_of_an_existing_kind_is_one_json_file(self) -> None:
        """Rule seam: the kernel runs a descriptor by its declared condition (trigger.when) and reads its
        parameters from it, so a 14-day deadline warning beside the 7-day one is a JSON file, no kernel change."""
        text = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        self.write("06_active_context/research-portfolio.md", text.replace("2026-09-22", "2026-10-01"))  # 11 days out
        descriptor = json.loads((self.tmp / "config/extensions/rules/deadline-warning.json").read_text(encoding="utf-8"))
        self.write("config/extensions/rules/deadline-warning-14.json", json.dumps(dict(
            descriptor, id="deadline_warning_14", trigger=dict(descriptor["trigger"], days=14))))
        rules = self.open_rules(self.boundary())
        self.assertNotIn("deadline_warning", rules, "11 天后到期：在 7 天窗口之外")
        self.assertEqual(len(rules["deadline_warning_14"]), 1, "但在 14 天窗口之内")

    @unittest.skipUnless(HAS_ATTENTION_OWNER, "no attention owner in this edition")
    def test_hj4_triage_projects_needs_review_and_attention_proposals_only(self) -> None:
        view = self.ros("today")
        self.assertEqual(set(view) - {"session_id", "kernel_version", "changed", "transitions", "stale_sessions",
                                      "spec", "spec_proposed", "spec_changes_pending", "budget", "change_details",
                                  "portfolio_problems"},
                         {"today", "decision", "questions", "waiting_on_trigger", "proposals", "needs_review", "network",
                          "total_open", "completion"},
                         "分流不再自持今日、本周、积压")
        self.assertFalse((self.tmp / self.ATTENTION).exists(), "分流只读，不写注意力")
        self.assertEqual(self.today_ids(view), {}, "没有人安排过今天")
        self.assertEqual(self.decision_ids(view), {"alpha": "unscheduled"}, "投入中却未安排：进待判断，不静默")
        self.assertIn("deadline_warning", [row["rule_id"] for row in view["decision"][0]["items"]], "要求挂在事项里")
        beta = [g for g in view["needs_review"] if g["commitment_id"] == "beta"]
        self.assertTrue(beta and "status_verify" in [r["rule_id"] for r in beta[0]["items"]], "等待中的事项不占今日")
        self.assertEqual([(p["commitment_id"], p["action"]) for p in view["proposals"]], [("alpha", "today")],
                         "外部截止临近：提议，不代为落定")

        self.ros("attend", "alpha", "tomorrow")
        view = self.ros("today")
        self.assertNotIn("alpha", {**self.today_ids(view), **self.decision_ids(view)})
        self.assertEqual([p["command"] for p in view["proposals"]], ["ros attend alpha today"])
        self.ros("attend", "alpha", "today")
        view = self.ros("today")
        self.assertEqual(self.today_ids(view), {"alpha": "today"})
        self.assertEqual(view["proposals"], [])
        # Routine attention changes are inline actions: no candidate, no admission decision (HJ-4).
        self.assertEqual(self.ledger().candidates(), {})
        self.assertFalse(any(r["kind"] == "decision" for r in self.ledger().trajectory()))

    @unittest.skipUnless(HAS_ATTENTION_OWNER, "no attention owner in this edition")
    def test_cr11_triage_proposes_and_attention_schedule_owns_today(self) -> None:
        portfolio = (self.tmp / "06_active_context/research-portfolio.md").read_bytes()
        self.ros("attend", "alpha", "date", "2026-09-25")
        self.assertEqual((self.tmp / "06_active_context/research-portfolio.md").read_bytes(), portfolio,
                         "注意力动作只写注意力安排，不碰 portfolio")
        text = (self.tmp / self.ATTENTION).read_text(encoding="utf-8")
        self.assertIn("### research_portfolio:alpha", text)
        self.assertIn("- attention_date: 2026-09-25", text)
        self.assertNotIn("alpha", self.today_ids(self.ros("today")))
        self.ros("attend", "alpha", "undo")
        self.assertNotIn("research_portfolio:alpha", (self.tmp / self.ATTENTION).read_text(encoding="utf-8"))
        self.assertEqual(self.decision_ids(self.ros("today")), {"alpha": "unscheduled"})
        self.assertIn("no attention action to undo", self.refusal("attend", "alpha", "undo"))
        # A waiting project enters the decision region only when its review is due.
        self.ros("attend", "beta", "park", "--review", "2026-09-30")
        self.assertNotIn("beta", self.decision_ids(self.ros("today")))
        self.ros("attend", "beta", "park", "--review", TODAY.isoformat())
        self.assertEqual(self.decision_ids(self.ros("today")).get("beta"), "review_due")
        # Order within today comes from the attention owner, not from the portfolio.
        self.add_commitment("### Delta\n\n- id: delta\n- responsibility: lead\n- state: mainline\n"
                            "- priority: P0\n- schedule_order: 1\n")
        self.ros("attend", "alpha", "today", "--order", "1")
        self.ros("attend", "delta", "today", "--order", "2")
        self.assertEqual([g["commitment_id"] for g in self.ros("today")["today"]], ["alpha", "delta"])

    @unittest.skipUnless(HAS_ATTENTION_OWNER, "no attention owner in this edition")
    def test_real_events_and_lifecycle_decide_today_and_proposals(self) -> None:
        self.add_commitment("### Eps\n\n- id: eps\n- responsibility: lead\n- state: closed\n- deadline: 2026-09-20\n\n"
                            "### Delta\n\n- id: delta\n- responsibility: lead\n- state: queued\n- deadline: 2026-09-18\n\n"
                            "### Zeta\n\n- id: zeta\n- responsibility: lead\n- state: queued\n- target_date: 2026-09-20\n")
        view = self.ros("today")
        self.assertNotIn("eps", self.today_ids(view), "已关闭的项目不进今日")
        self.assertIn("delta", self.today_ids(view), "已过期的外部截止是真实事件")
        self.assertNotIn("zeta", {**self.today_ids(view), **self.decision_ids(view)}, "内部目标日不是事件（§3.4）")
        self.ros("attend", "alpha", "park")
        view = self.ros("today")
        self.assertIn(("alpha", "today"), [(p["commitment_id"], p["action"]) for p in view["proposals"]],
                      "搁置此步不关掉临近截止的提议")
        self.assertIn("in the past", self.refusal("attend", "alpha", "date", "2026-09-01"))
        self.assertIn("closed", self.refusal("attend", "eps", "today"))

    @unittest.skipUnless(HAS_ATTENTION_OWNER, "no attention owner in this edition")
    def test_undo_refuses_to_overwrite_a_later_attention_change(self) -> None:
        from researchos_server.attention_schedule_store import AttentionScheduleStore
        self.ros("attend", "alpha", "today")
        AttentionScheduleStore.create(self.tmp).apply(provider_id="research_portfolio", item_id="alpha",
                                                      action="schedule", attention_date="2026-09-28", today_order=2)
        self.assertIn("changed since this action", self.refusal("attend", "alpha", "undo"))
        self.assertIn("- attention_date: 2026-09-28", (self.tmp / self.ATTENTION).read_text(encoding="utf-8"),
                      "Desk 的改动保留")

    def test_the_public_starter_shows_attention_actions_instead_of_writing(self) -> None:
        self.edit_config(runtime_scope="public_starter")
        shown = self.ros("attend", "alpha", "today")
        self.assertEqual(shown["promoted"], False)
        self.assertFalse((self.tmp / self.ATTENTION).exists(), "公开 starter 只走复制回退，不写注意力安排")

    def test_context_excludes_private_nodes_and_records_delivery(self) -> None:
        self.write("01_knowledge/papers/j.md", "---\ntitle: Notes\n---\n> [!judgment] j-s\n> 结论：x\n"
                   "> 依据：01_knowledge/papers/secret.md · alpha-project\n> 承诺：alpha\n")
        pack = self.ros("context", "commitment:alpha")
        self.assertIn("01_knowledge/projects/alpha.md", pack["delivered"])
        self.assertEqual([row["ref"] for row in pack["excluded"]], ["01_knowledge/papers/secret.md"])
        self.assertNotIn("# Secret", pack["pack"])
        records = self.ledger().trajectory()
        self.assertTrue(any(r["payload"].get("detail", {}).get("action") == "context_delivered" for r in records))

    # context receipt and egress (HJ-10 / CR-2) -------------------------------------------------------
    def test_hj10_context_egress_is_confirmed_and_recorded_before_delivery(self) -> None:
        self.context_fixture()
        self.write("01_knowledge/papers/odd.md", "---\ntitle: Odd\nsensitivity: confidential\n---\n# Odd\nODD_BODY\n")
        self.write("01_knowledge/papers/k.md", "---\ntitle: K\n---\n> [!judgment] j-k\n> 结论：y\n"
                   "> 依据：01_knowledge/papers/odd.md\n> 承诺：alpha\n")
        plain = self.context("commitment:alpha")
        reasons = {row["ref"]: row["reason"] for row in plain["excluded"]}
        self.assertEqual(reasons["01_knowledge/papers/secret.md"], "sensitivity:private")
        self.assertEqual(reasons["01_knowledge/papers/odd.md"], "sensitivity:confidential", "无法识别的级别一律排除")
        self.assertTrue(reasons["01_knowledge/papers/touchy.md"].startswith("sensitivity:sensitive"))
        self.assertNotIn("ODD_BODY", plain["pack"])
        self.assertEqual(plain["service"], "unknown", "服务无法识别时去向记为未知")
        alpha = next(row for row in plain["context_receipt"]["sources"]
                     if row["ref_digest"] == hashlib.sha256(b"01_knowledge/projects/alpha.md").hexdigest())
        self.assertEqual(alpha["delivery"]["state"], "delivered")
        self.assertEqual(alpha["egress"]["state"], "unknown", "不把未识别的去向写成已外发")

        # An Agent cannot approve itself: there is no flag; only the researcher's terminal counts.
        self.assertIn("unrecognized arguments", self.run_ros("context", "commitment:alpha", "--allow-sensitive",
                                                         expect=SystemExit)[2])
        from unittest import mock
        with mock.patch.object(context_pack, "terminal_confirms", lambda ref, label, destination="": True):
            confirmed = self.context("commitment:alpha", "--service", "claude")
        self.assertIn("01_knowledge/papers/touchy.md", confirmed["delivered"])
        touchy = next(row for row in confirmed["context_receipt"]["sources"]
                      if row["ref_digest"] == hashlib.sha256(b"01_knowledge/papers/touchy.md").hexdigest())
        self.assertEqual(touchy["authorization"]["evidence_ref"], "researcher_terminal_confirmation")
        self.assertEqual(touchy["egress"], {"state": "egressed", "evidence_ref": "session_agent:claude (flag:--service)"},
                         "外发记下去向服务与这一说法的来源")
        self.assertIn("short name", self.refusal("context", "commitment:alpha", "--service", "x" * 200))

    def test_a_private_portfolio_keeps_its_commitments_and_judgments_home(self) -> None:
        text = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        text = text.replace("title: Portfolio", "title: Portfolio\nsensitivity: private", 1)
        text = text.replace("- source_path: 01_knowledge/projects/alpha.md",
                            "- source_path: 01_knowledge/projects/alpha.md\n- note: PRIVATE_PORTFOLIO_NOTE\n\n"
                            "> [!judgment] j-p\n> 结论：PORTFOLIO_JUDGMENT_SECRET\n> 依据：alpha-project\n", 1)
        self.write("06_active_context/research-portfolio.md", text)
        out = self.context("commitment:alpha", "--service", "claude")
        self.assertNotIn("PRIVATE_PORTFOLIO_NOTE", out["pack"])
        self.assertNotIn("PORTFOLIO_JUDGMENT_SECRET", out["pack"])
        reasons = {row["ref"]: row["reason"] for row in out["excluded"]}
        self.assertEqual(reasons.get("commitment:alpha"), "sensitivity:private")
        self.assertEqual(reasons.get("judgment:j-p"), "sensitivity:private")
        self.assertIn("01_knowledge/projects/alpha.md", out["delivered"])

    def test_a_private_portfolio_can_declare_the_fields_it_releases(self) -> None:
        text = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        text = text.replace("title: Portfolio", "title: Portfolio\nsensitivity: private\n"
                            "context_fields: question, next_step  # released as internal", 1)
        text = text.replace("- source_path: 01_knowledge/projects/alpha.md",
                            "- source_path: 01_knowledge/projects/alpha.md\n- note: PRIVATE_PORTFOLIO_NOTE\n\n"
                            "> [!judgment] j-p\n> 结论：PORTFOLIO_JUDGMENT_SECRET\n> 依据：alpha-project\n", 1)
        self.write("06_active_context/research-portfolio.md", text)
        out = self.context("commitment:alpha", "--service", "claude")
        self.assertIn("commitment:alpha", out["delivered"])
        self.assertIn("- question: Does method A transfer under occlusion?", out["pack"])
        self.assertIn("- next_step: Run the occlusion comparison", out["pack"])
        for secret in ("PRIVATE_PORTFOLIO_NOTE", "PORTFOLIO_JUDGMENT_SECRET", "Alpha Paper", "responsibility"):
            self.assertNotIn(secret, out["pack"], "未声明的字段、标题与判断块仍按 private")
        self.assertIn("note", out["withheld_fields"])
        self.assertIn("judgment:j-p", [row["ref"] for row in out["excluded"]])
        grant = next(row for row in out["context_receipt"]["sources"]
                     if row["ref_digest"] == hashlib.sha256(b"commitment:alpha").hexdigest())["authorization"]
        self.assertEqual(grant, {"state": "authorized", "evidence_ref": "source_declared_fields:question,next_step"})

    def test_a_field_declaration_opens_only_a_private_portfolio(self) -> None:
        base = (self.tmp / "06_active_context/research-portfolio.md").read_text(encoding="utf-8")
        for label, why in (("sensitive", "sensitivity:sensitive"), ("confidentail", "sensitivity:confidentail")):
            self.write("06_active_context/research-portfolio.md", base.replace(
                "title: Portfolio", f"title: Portfolio\nsensitivity: {label}\ncontext_fields: question, next_step", 1))
            out = self.context("commitment:alpha", "--service", "claude")
            self.assertNotIn("commitment:alpha", out["delivered"], f"{label} 不因声明而放行")
            self.assertTrue(next(r["reason"] for r in out["excluded"] if r["ref"] == "commitment:alpha").startswith(why))

    def test_cr2_ros_context_emits_context_receipt_with_egress_service(self) -> None:
        self.context_fixture()
        out = self.context("commitment:alpha", "--service", "claude")
        receipt = out["context_receipt"]
        self.assertEqual(receipt["schema_id"], "researchos-context-receipt-v1")
        self.assertEqual(normalize_context_receipt(receipt, trusted_producer=True)["receipt_id"], out["receipt_id"],
                         "回执经其 owner 归一化，id 可复算")
        self.assertEqual(self.axes(receipt, "01_knowledge/projects/alpha.md"),
                         {"authorization": "authorized", "delivery": "delivered", "exclusion": "not_excluded",
                          "egress": "egressed", "observation": "unknown", "citation": "unknown"},
                         "五维分立；没有测量不宣称已观测")
        self.assertEqual(self.axes(receipt, "01_knowledge/papers/secret.md")["egress"], "not_egressed")
        self.assertNotIn("Evidence v1", json.dumps(receipt), "回执只含摘要，不含正文")
        decision = self.receipt_of(out["receipt_id"])
        self.assertNotIn("context_receipt", decision, "账只引用回执 id，不另存回执")
        self.assertEqual((decision["purpose"], decision["service"]), ("commitment:alpha", "session_agent:claude"))

        self.edit_config(context=dict(self.config().get("context", {}), max_chars=200))
        small = self.context("commitment:alpha", "--service", "claude")
        budget = [row["ref"] for row in small["excluded"] if row["reason"].startswith("budget:")]
        self.assertTrue(budget, "超出预算的来源整条排除")
        for ref in budget:
            self.assertEqual(self.axes(small["context_receipt"], ref)["delivery"], "not_delivered")
        for ref in small["delivered"]:
            self.assertEqual(self.axes(small["context_receipt"], ref)["delivery"], "delivered")

    def test_the_receipt_capacity_drops_judgments_before_the_cards_they_rest_on(self) -> None:
        blocks = "".join(f"> [!judgment] j-{i}\n> 结论：c{i}\n> 依据：alpha-project\n> 承诺：alpha\n\n" for i in range(25))
        self.write("01_knowledge/papers/many.md", "---\ntitle: Many\n---\n" + blocks)
        out = self.context("commitment:alpha", "--service", "claude")
        self.assertIn("01_knowledge/projects/alpha.md", out["delivered"], "承诺的来源卡不被上限挤掉")
        dropped = [row for row in out["excluded"] if row["reason"].startswith("capacity:")]
        self.assertTrue(dropped and all(row["ref"].startswith("judgment:") for row in dropped))

    def test_state_reports_q_e_j_b_n(self) -> None:
        state = self.ros("state", "alpha")
        self.assertEqual(state["Q"], "Does method A transfer under occlusion?")
        self.assertIn("01_knowledge/projects/alpha.md", state["E"])
        self.assertEqual(state["N"], "Run the occlusion comparison")
        self.assertTrue(state["B"])

    def test_damaged_cursor_only_costs_a_rescan(self) -> None:
        self.boundary()
        ledger = self.ledger()
        registered = len(ledger.requirements())
        ledger.cache_path.write_text("{broken", encoding="utf-8")
        result = self.boundary()
        self.assertEqual(len(ledger.requirements()), registered)
        self.assertEqual(result.transitions, [])

    def test_english_output_and_english_judgment_labels(self) -> None:
        draft = self.tmp / "draft.md"
        draft.write_text("> [!judgment] j-en\n> Conclusion: Occlusion first\n> Basis: alpha-project\n", encoding="utf-8")
        shown = self.run_ros("today", json_out=False, lang="en")[1]
        self.assertIn("Today (from the attention schedule", shown)
        self.assertNotIn("今日", shown)
        self.run_ros("propose", "judgment", "--file", str(draft), "--target", "01_knowledge/projects/beta.md",
                 json_out=False, lang="en")
        self.run_ros("admit", next(iter(self.ledger().candidates())), json_out=False, lang="en")
        text = (self.tmp / "01_knowledge/projects/beta.md").read_text(encoding="utf-8")
        self.assertIn("> Conclusion: Occlusion first", text)
        self.assertIn("> Confirmed: 2026-09-20", text)
        self.assertIn("## Judgments", text)

    def test_english_output_uses_ascii_punctuation(self) -> None:
        """English headings, markers and proposal rows use ASCII punctuation; Chinese keeps full-width."""
        full_width = re.compile("[（）［］：]")
        shown = self.run_ros("today", json_out=False, lang="en")[1]
        self.assertRegex(shown.split("To decide", 1)[1], r"■ [^\n]+  \[")  # a commitment's attention marker
        self.assertEqual(full_width.findall(shown), [], shown)
        pack = self.run_ros("context", "commitment:alpha", json_out=False, lang="en")[1]
        self.assertIn("# Alpha (01_knowledge/projects/alpha.md@", pack)
        self.assertEqual(full_width.findall(pack), [], pack)
        self.assertIn("# Alpha（01_knowledge/projects/alpha.md@",
                      self.run_ros("context", "commitment:alpha", json_out=False, lang="zh-CN")[1])
        self.assertRegex(self.run_ros("today", json_out=False, lang="zh-CN")[1], r"■ [^\n]+  ［")

    def test_root_without_config_is_refused_in_one_line(self) -> None:
        empty = self.tmp / "not-a-vault"
        empty.mkdir()
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = ros.main(["--root", str(empty), "today"])
        message = stderr.getvalue()
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(len(message.strip().splitlines()), 1, message)
        self.assertIn("is not a ResearchOS scheduler root (config/ros.json is missing)", message)
        self.assertNotIn("Traceback", message)
        # The starter suggests starting from its fixture only where the fixture ships.
        self.assertEqual("ros_demo.py --init personal_vault" in message, (ROOT / "examples" / "scheduler-demo").is_dir())

    def test_unusable_commitment_fields_are_listed_instead_of_dropped(self) -> None:
        """A commitment the checks cannot read is named in today and rules --check, in both languages."""
        self.write("06_active_context/research-portfolio.md", PORTFOLIO + (
            "\n### Delta Draft\n\n- id: delta\n- responsibility: owner\n- state: active\n- last_verified: soon\n"
            "- stale_after_days: two weeks\n- source_path: 01_knowledge/projects/missing.md\n"))
        rows = self.ros("today")["portfolio_problems"]
        self.assertEqual([(row["id"], row["field"]) for row in rows],
                         [("delta", name) for name in
                          ("state", "responsibility", "last_verified", "stale_after_days", "source_path")],
                         "alpha, beta and gamma are well formed: nothing is flagged for them")
        self.assertEqual(rows[1]["valid"], ["lead", "support"])
        self.assertTrue({"closed", "paused", *self.config()["active_states"]} <= set(rows[0]["valid"]))
        text = self.run_ros("today", json_out=False, lang="en")[1]
        self.assertIn("Portfolio problems (5; fix them in 06_active_context/research-portfolio.md)", text)
        self.assertIn('delta (line ', text)
        self.assertIn('state "active" is not a valid value (', text)
        zh = self.run_ros("today", json_out=False, lang="zh-CN")[1]
        self.assertIn("任务总表问题（5 条", zh)
        self.assertIn("responsibility「owner」不是可用值（lead, support）", zh)
        checked = self.run_ros("rules", "--check", json_out=False, lang="en")[1]
        self.assertIn('responsibility "owner" is not a valid value (lead, support)', checked)
        self.assertIn("source_path 01_knowledge/projects/missing.md does not exist", checked)

        (self.tmp / "06_active_context" / "research-portfolio.md").unlink()
        text = self.run_ros("today", json_out=False, lang="en")[1]
        self.assertEqual(text.count("06_active_context/research-portfolio.md named in config/ros.json does not exist"), 1)
        self.assertNotIn("Portfolio problems", text)

    def test_reconfirm_keeps_the_label_language_of_the_block(self) -> None:
        """Re-pinning rewrites only the basis and date: a Chinese block stays Chinese under English output,
        and an English block stays English under Chinese output."""
        pinned = self.add_alpha_judgment()  # Chinese labels
        self.write("01_knowledge/papers/k.md", "---\ntitle: K\n---\n# K\n\n> [!judgment] j-alpha-en\n"
                   f"> Conclusion: Keep the benchmark\n> Basis: 01_knowledge/projects/alpha.md@{pinned}\n"
                   "> Commitment: alpha\n> Confirmed: 2026-09-19\n")
        for judgment_id in ("j-alpha-scope", "j-alpha-en"):
            self.ros("admit", "--confirm", judgment_id, answer="y")
        self.write("01_knowledge/projects/alpha.md", "---\ntitle: Alpha\nid: alpha-project\n---\n# Alpha\nEvidence v2\n")
        self.run_ros("admit", "--reconfirm", "j-alpha-scope", lang="en")
        self.run_ros("admit", "--reconfirm", "j-alpha-en", lang="zh-CN")
        chinese = (self.tmp / "01_knowledge/papers/j.md").read_text(encoding="utf-8")
        english = (self.tmp / "01_knowledge/papers/k.md").read_text(encoding="utf-8")
        self.assertIn("> 结论：Do not extend the benchmark\n> 依据：01_knowledge/projects/alpha.md@", chinese)
        self.assertIn(f"> 确认：{TODAY.isoformat()}", chinese)
        self.assertNotIn("Conclusion", chinese)
        self.assertIn("> Conclusion: Keep the benchmark\n> Basis: 01_knowledge/projects/alpha.md@", english)
        self.assertIn(f"> Confirmed: {TODAY.isoformat()}", english)
        self.assertNotIn("结论", english)
        self.assertNotIn(f"alpha.md@{pinned}\n", chinese + english, "both bases were re-pinned")

    def test_terminal_question_is_readable_in_both_languages(self) -> None:
        self.add_alpha_judgment()
        for lang, question in (("en", "Confirm judgment j-alpha-scope after the fact? [y/N] "),
                               ("zh-CN", "事后确认判断 j-alpha-scope？ [y/N] ")):
            refusal, _, asked = self.run_ros("admit", "--confirm", "j-alpha-scope", lang=lang, answer="n",
                                             expect=SystemExit)
            self.assertIn("declined at the terminal", refusal)
            self.assertEqual(asked, question)

    def test_rule_descriptors_are_valid(self) -> None:
        self.assertIn("basis_recheck", self.run_ros("rules", "--check", json_out=False)[1])

    def test_rules_validate_through_the_task_extension_v2_port(self) -> None:
        """CC-1: one meta-task per rule — 输入模式、保留部分、预期结果、应用条件、结果检查缺一不可，
        且内核与门禁读同一个 registry，不各validate各的。"""
        from researchos_kernel.rules import EVALUATORS, load_contract, load_registry

        contract, problems = load_contract(self.tmp)
        self.assertEqual(problems, [])
        meta_task = contract["x_researchos_meta_task"]
        parts = [meta_task[part] for part in
                 ("input_pattern", "preserved_part", "expected_result", "precondition", "check")]
        self.assertEqual(parts, ["trigger", "preserve", "expect", "pre", "check"])
        for part in parts:
            self.assertIn(part, contract["required"], f"{part} must be required, not optional")

        descriptors, problems = load_registry(self.tmp)
        self.assertEqual(problems, [])
        self.assertEqual({rule["trigger"]["when"] for rule in descriptors.values()}, set(EVALUATORS),
                         "every script evaluator has a descriptor, and every descriptor names an evaluator")

        directory = self.tmp / "config/extensions/rules"
        descriptor_path = next(path for path in directory.glob("*.json")
                               if json.loads(path.read_text(encoding="utf-8"))["id"] == "deadline_warning")
        original = descriptor_path.read_text(encoding="utf-8")
        for part in parts:
            data = json.loads(original)
            data.pop(part)
            descriptor_path.write_text(json.dumps(data), encoding="utf-8")
            admitted, problems = load_registry(self.tmp)
            self.assertNotIn("deadline_warning", admitted, f"a rule without {part} must not be admitted")
            self.assertTrue(any(f"missing {part}" in problem for problem in problems), problems)
        descriptor_path.write_text(original, encoding="utf-8")
        self.assertEqual(load_registry(self.tmp)[1], [])

    def test_the_rule_contract_is_the_only_admission_port(self) -> None:
        """没有合同就没有规则：契约文件不可读时，调度器不得退回到内建的字段常量继续排程。"""
        from researchos_kernel.rules import CONTRACT_RELATIVE, load_registry

        (self.tmp / CONTRACT_RELATIVE).write_text("{ broken", encoding="utf-8")
        descriptors, problems = load_registry(self.tmp)
        self.assertEqual(descriptors, {})
        self.assertTrue(any("unreadable" in problem for problem in problems), problems)


if __name__ == "__main__":
    unittest.main()
