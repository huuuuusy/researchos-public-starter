"""归属、情节与冻结范围（正典《图的三个轴》，报告 D0）。

这些测试盯住三条设计级结论，它们都是复核时发现首版写错的地方：
范围在开始时按外延冻结、覆盖未知必须登记为要求、不相交范围互不影响。
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters.markdown_repo import build_snapshot  # noqa: E402
from researchos_kernel import scope as scope_axis  # noqa: E402
from researchos_kernel.boundary import run_boundary  # noqa: E402

TODAY = date(2026, 9, 18)
PORTFOLIO = """---
type: active_context
title: "Portfolio"
---

# Portfolio

## Commitments

### Alpha

- id: alpha
- responsibility: lead
- state: mainline
- question: how far
- last_verified: 2026-09-17
- stale_after_days: 30
- deadline: 2026-09-20
- source_path: 01_knowledge/projects/alpha/alpha.md

### Beta

- id: beta
- responsibility: lead
- state: mainline
- question: how wide
- last_verified: 2026-09-17
- stale_after_days: 30
- source_path: 01_knowledge/projects/beta/beta.md
"""


class ScopeAxisTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ros-scope-"))
        for relative in ("config/extensions/rules", "09_templates/data_contracts"):
            shutil.copytree(ROOT / relative, self.tmp / relative)
        self.config = json.loads((ROOT / "config" / "ros.json").read_text(encoding="utf-8"))
        self.config.update({"graph_roots": ["01_knowledge", "06_active_context"], "runtime_scope": "private",
                            "portfolio": "06_active_context/research-portfolio.md"})
        self.write("config/ros.json", json.dumps(self.config))
        self.write("06_active_context/research-portfolio.md", PORTFOLIO)
        self.write("01_knowledge/projects/alpha/alpha.md", "---\ntitle: Alpha\n---\n# Alpha\n")
        self.write("01_knowledge/projects/beta/beta.md", "---\ntitle: Beta\n---\n# Beta\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, relative: str, text: str) -> Path:
        path = self.tmp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def boundary(self, config: dict | None = None):
        return run_boundary(self.tmp, config or self.config, snapshot_builder=build_snapshot,
                            today=TODAY, runtime_scope="private", install_root=ROOT, ask_room=None)

    def placements(self) -> dict:
        snapshot, _ = build_snapshot(self.tmp, self.config, None)
        return scope_axis.placements_from_snapshot(snapshot)

    def test_containment_is_derived_from_the_location_and_overridable(self) -> None:
        self.write("01_knowledge/projects/beta/borrowed.md",
                   "---\ntitle: Borrowed\nscope: 01_knowledge/projects/alpha\n---\n# Borrowed\n")
        places = self.placements()
        self.assertEqual(places["01_knowledge/projects/alpha/alpha.md"].scope, "01_knowledge/projects/alpha")
        self.assertEqual(places["01_knowledge/projects/alpha/alpha.md"].source, scope_axis.DERIVED)
        borrowed = places["01_knowledge/projects/beta/borrowed.md"]
        self.assertEqual((borrowed.scope, borrowed.source), ("01_knowledge/projects/alpha", scope_axis.DECLARED))
        self.assertEqual(places["commitment:alpha"].scope, "01_knowledge/projects/alpha",
                         "一个承诺随它的来源落位，不另立归属")

    def test_disjoint_scopes_do_not_share_requirements(self) -> None:
        places = self.placements()
        alpha = scope_axis.closure(places, "01_knowledge/projects/alpha")
        beta = scope_axis.closure(places, "01_knowledge/projects/beta")
        self.assertTrue(alpha and beta)
        self.assertEqual(alpha & beta, set(), "互不可比的两个范围，闭包不相交")
        self.assertLessEqual(alpha, scope_axis.closure(places, "01_knowledge"),
                             "祖先关系下是包含，不是不相交")

    def test_a_closed_episode_leaves_the_scope_but_not_the_repository(self) -> None:
        path = self.write("01_knowledge/projects/alpha/round-1.md",
                          "---\ntitle: Round 1\nepisode_state: open\n---\n# Round 1\n")
        key, node = path.relative_to(self.tmp).as_posix(), "01_knowledge/projects/alpha"
        self.assertIn(key, scope_axis.closure(self.placements(), node))
        path.write_text(path.read_text(encoding="utf-8").replace("open", "closed\nepisode_closure_receipt: r-1"),
                        encoding="utf-8")
        snapshot, _ = build_snapshot(self.tmp, self.config, None)
        verified = scope_axis.placements_from_snapshot(snapshot, {"r-1": {"identity": "round-1", "revoked": False}})
        self.assertNotIn(key, scope_axis.closure(verified, node))
        self.assertTrue(path.exists(), "关闭是退出取值范围，不是删除")
        self.assertEqual(scope_axis.closure_problems(verified), [])

    def test_the_source_closes_and_the_ledger_can_only_refute(self) -> None:
        """报告 D0：来源确立关闭；被 Git 忽略的账只能否定（撤销、错签），查不到只报告不可核实。"""
        closed = "---\ntitle: R\nepisode_state: closed\nepisode_closure_receipt: r-1\n---\n# R\n"
        self.write("01_knowledge/projects/alpha/round-1.md", closed)
        self.write("01_knowledge/projects/alpha/bare.md", "---\ntitle: B\nepisode_state: closed\n---\n# B\n")
        node, key = "01_knowledge/projects/alpha", "01_knowledge/projects/alpha/round-1.md"
        snapshot, _ = build_snapshot(self.tmp, self.config, None)

        def places(receipts):
            return scope_axis.placements_from_snapshot(snapshot, receipts)

        clean_clone = places({})
        self.assertNotIn(key, scope_axis.closure(clean_clone, node), "干净克隆不重开已关闭情节")
        self.assertTrue(any("cannot be verified" in p for p in scope_axis.closure_problems(clean_clone)))
        self.assertIn("01_knowledge/projects/alpha/bare.md", scope_axis.closure(clean_clone, node),
                      "只写 closed 不写回执，不推定关闭")
        for receipts, why in (({"r-1": {"identity": "round-1", "revoked": True}}, "revoked"),
                              ({"r-1": {"identity": "other", "revoked": False}}, "issued to episode other")):
            refuted = places(receipts)
            self.assertIn(key, scope_axis.closure(refuted, node))
            self.assertTrue(any(why in p for p in scope_axis.closure_problems(refuted)), why)
        self.write("01_knowledge/projects/alpha/copy.md", closed.replace("title: R", "title: C"))
        snapshot, _ = build_snapshot(self.tmp, self.config, None)
        doubled = places({"r-1": {"identity": "round-1", "revoked": False}})
        self.assertIn(key, scope_axis.closure(doubled, node), "被两份来源认领的回执不成立")
        self.assertTrue(any("claimed by 2 records" in p for p in scope_axis.closure_problems(doubled)))

    def test_a_non_episode_record_is_never_closed(self) -> None:
        places = self.placements()
        plain = places["01_knowledge/projects/alpha/alpha.md"]
        self.assertEqual(plain.episode_state, "", "不是情节的记录没有情节状态")
        self.assertFalse(plain.closed, "没有情节状态即视同未关闭，计入闭包")

    def test_the_frozen_scope_does_not_move_when_records_move_or_close(self) -> None:
        """首版把范围写成随时重算：搬一次目录就让进行中的目标丢记录，
        关掉一个子情节就能把范围缩成「已完成」。两者都必须失败。"""
        places = self.placements()
        frozen, problems = scope_axis.freeze(places, "01_knowledge", frozen_at="2026-09-18T00:00:00+00:00")
        self.assertEqual(problems, [])
        before = set(frozen.members)
        moved = self.tmp / "06_active_context/alpha-moved.md"
        (self.tmp / "01_knowledge/projects/alpha/alpha.md").rename(moved)
        self.write("01_knowledge/projects/beta/round-2.md",
                   "---\ntitle: Round 2\nepisode_state: closed\n---\n# Round 2\n")
        self.assertEqual(set(frozen.members), before, "已冻结的范围不因搬动或关闭而改变")
        self.assertEqual(frozen.member_digest, scope_axis.FrozenScope(
            node=frozen.node, members=frozenset(before)).member_digest)
        later = scope_axis.closure(self.placements(), "01_knowledge")
        self.assertNotEqual(later, before, "下一次重新求值才反映变化")

    def test_a_cross_scope_key_must_name_an_interface_node_and_is_reported_not_refused(self) -> None:
        self.write("01_knowledge/projects/beta/beta-synthesis.md",
                   "---\ntitle: Beta synthesis\ninterface: true\n---\n# Beta synthesis\n")
        places = self.placements()
        good = [{"key": "01_knowledge/projects/beta/beta-synthesis.md", "version": "v1"}]
        frozen, problems = scope_axis.freeze(places, "01_knowledge/projects/alpha",
                                             frozen_at="2026-09-18T00:00:00+00:00", cross=good)
        self.assertEqual(problems, [])
        self.assertIn("01_knowledge/projects/beta/beta-synthesis.md", frozen)
        inner = [{"key": "01_knowledge/projects/beta/beta.md", "version": "v1"}]
        frozen, problems = scope_axis.freeze(places, "01_knowledge/projects/alpha",
                                             frozen_at="2026-09-18T00:00:00+00:00", cross=inner)
        self.assertTrue(any("not an interface node" in problem for problem in problems))
        self.assertIn("01_knowledge/projects/beta/beta.md", frozen,
                      "先报告不拦截：当前多数范围还没有接口节点")

    def test_an_unevaluated_rule_registers_coverage_unknown_and_blocks_completion(self) -> None:
        """范围内未评估的输入必须登记为要求并记 not_evaluated，
        否则一次 episode 可以在没看过的输入上报 complete。"""
        descriptor = next(path for path in (self.tmp / "config/extensions/rules").glob("*.json")
                          if json.loads(path.read_text(encoding="utf-8"))["id"] == "deadline_warning")
        descriptor.write_text("{ broken", encoding="utf-8")
        result = self.boundary()
        self.assertGreater(result.coverage["coverage_unknown_in_scope"], 0)
        self.assertTrue(result.coverage["unreadable_descriptors"])
        open_coverage = [issue for issue, requirement in result.requirements.items()
                         if str(requirement.get("binding", "")).startswith("coverage:descriptor:")]
        self.assertTrue(open_coverage, "读不出的描述符留下一条域未知的覆盖未知要求")
        self.assertEqual(result.states["issues"][open_coverage[0]]["status"], "open",
                         "覆盖未知留在未决集里，本次因此不是完成")

    def test_a_disabled_rule_is_out_of_spec_not_coverage_unknown(self) -> None:
        """刻意关掉的开关不是「没看过的输入」；否则每次边界都按定义不完成。"""
        descriptor = next(path for path in (self.tmp / "config/extensions/rules").glob("*.json")
                          if json.loads(path.read_text(encoding="utf-8"))["id"] == "deadline_warning")
        descriptor.write_text(json.dumps({**json.loads(descriptor.read_text(encoding="utf-8")),
                                          "enabled": False}), encoding="utf-8")
        result = self.boundary()
        self.assertEqual(result.coverage["coverage_unknown_in_scope"], 0)
        self.assertEqual(result.coverage["unreadable_descriptors"], [])

    def test_coverage_is_clean_when_every_declared_rule_runs(self) -> None:
        result = self.boundary()
        self.assertEqual(result.coverage["coverage_unknown_in_scope"], 0)
        self.assertEqual(result.coverage["coverage_unknown_unowned"], 0)
        self.assertEqual(result.coverage["in_scope_match_count"], result.coverage["evaluated_match_count"])
        self.assertTrue(result.scope.member_digest)
        self.assertTrue(result.scope.frozen_at)

    def test_the_boundary_records_the_frozen_scope_for_replay(self) -> None:
        result = self.boundary()
        payload = result.scope.to_dict()
        restored = scope_axis.restore(payload, result.scope.members)
        self.assertEqual(restored.member_digest, result.scope.member_digest)
        self.assertEqual(restored.node, payload["scope_node"])
        self.assertEqual(payload["scope_member_count"], len(result.scope.members))


if __name__ == "__main__":
    unittest.main()
