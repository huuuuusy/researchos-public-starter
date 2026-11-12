"""The public scheduler demo runs end to end in a temporary copy and leaves tracked files untouched."""

from __future__ import annotations

import hashlib
import io
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ros_demo  # noqa: E402


def tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file() and "work_state" not in p.parts):
        digest.update(file.relative_to(path).as_posix().encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()


class RosDemoTest(unittest.TestCase):
    def test_demo_walks_the_loop_without_touching_tracked_files(self) -> None:
        before = tree_digest(ros_demo.DEMO)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(ros_demo.main([]), 0)
        output = buffer.getvalue()
        self.assertIn("is not confirmed yet", output)
        self.assertIn('The basis of judgment "Compare A and B under occlusion first', output)
        self.assertIn("recorded as a confirmation after the fact, not an admission", output)
        reconfirm = output.split("━━ 5.")[1].split("━━ 6.")[0]
        self.assertIn("Nothing was written or admitted", reconfirm, "公开 starter 只走复制回退")
        self.assertIn("+> Basis: 01_knowledge/projects/occlusion-tracking.md", reconfirm, "展示的是计划中的依据改动")
        self.assertIn("at the researcher's own terminal", output)
        self.assertNotIn("her terminal", output)
        self.assertIn("session 20260920T", output, "the session id carries the pinned demo day")
        self.assertNotIn("Not known yet (counted in open items)", output, "bookkeeping lines with nothing to report stay out of the default view")
        after = output.split("━━ What next")[1]
        self.assertIn("python3 scripts/ros_demo.py --init personal_vault", after)
        self.assertNotIn("cp -R", output)
        self.assertIn("python3 scripts/ros.py --root personal_vault today", after)
        self.assertEqual(before, tree_digest(ros_demo.DEMO))

    def test_chinese_demo_matches_the_chinese_readme(self) -> None:
        before = tree_digest(ros_demo.DEMO_ZH)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(ros_demo.main(["--lang", "zh-CN"]), 0)
        output = buffer.getvalue()
        self.assertEqual(before, tree_digest(ros_demo.DEMO_ZH))
        self.assertIn("ResearchOS · 2026-09-20 · 会话 20260920T", output)
        self.assertIn("研究者在自己的终端上事后确认", output)
        self.assertIn("━━ 接下来", output)
        self.assertNotIn("Today (from the attention schedule", output)
        # The Chinese demo reads the Chinese fixture: cards, commitments and the judgment are Chinese throughout.
        self.assertIn("新判断「先在遮挡条件下比较 A 和 B，暂不扩大数据集。」尚未确认", output)
        self.assertIn("示例遮挡基准（虚构）", output)
        self.assertIn("■ 遮挡迁移论文", output)
        for english in ("Occlusion", "Compare A and B", "Version 1", "Workshop Talk", "fictional"):
            self.assertNotIn(english, output)
        first = output.split("━━ 1.")[1].split("━━ 2.")[0]
        self.assertNotIn("的依据变了", first, "the fixture's basis pins match its cards before the source changes")
        self.assertIn("依据已变化：示例遮挡基准（虚构）", output.split("━━ 3.")[1].split("━━ 4.")[0])
        # Step 5 re-pins the block's basis and keeps its labels: one changed line.
        reconfirm = output.split("━━ 5.")[1].split("━━ 6.")[0]
        changed = [line for line in reconfirm.splitlines() if line[:1] in ("+", "-") and line[:3] not in {"+++", "---"}]
        self.assertEqual([line[:6] for line in changed], ["-> 依据：", "+> 依据："], changed)
        self.assertIn("事后确认判断 j-occlusion-scope？ [y/N] y", output, "the terminal question is translated")

    def test_init_starts_a_vault_without_the_walkthrough_leftovers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # A walk-through on the fixture itself leaves its ledger beside the tracked files.
            fixture = Path(tmp) / "fixture"
            shutil.copytree(ros_demo.DEMO, fixture)
            ros_demo.run(fixture, "today")
            self.assertTrue((fixture / "06_active_context" / "work_state").is_dir())
            vault = Path(tmp) / "personal_vault"
            (vault / "06_active_context").mkdir(parents=True)  # as the personal-vault Dashboard leaves it
            (vault / "01_knowledge" / "projects").mkdir(parents=True)
            mine = vault / "01_knowledge" / "projects" / "occlusion-tracking.md"
            mine.write_text("---\ntitle: Mine\n---\n# Mine\n", encoding="utf-8")
            buffer = io.StringIO()
            saved = ros_demo.DEMO
            ros_demo.DEMO = fixture
            try:
                with redirect_stdout(buffer):
                    self.assertEqual(ros_demo.main(["--init", str(vault)]), 0)
            finally:
                ros_demo.DEMO = saved
            self.assertFalse((vault / "06_active_context" / "work_state").exists())
            self.assertFalse((vault / "sample-answer.md").exists())
            self.assertEqual(mine.read_text(encoding="utf-8"), "---\ntitle: Mine\n---\n# Mine\n", "kept as it was")
            portfolio = (vault / "06_active_context" / "research-portfolio.md").read_text(encoding="utf-8")
            self.assertNotIn("[!judgment]", portfolio)
            self.assertNotIn("- judgments:", portfolio)
            self.assertNotIn("\n\n\n", portfolio)
            self.assertIn(f"python3 scripts/ros.py --root {vault.as_posix()} today", buffer.getvalue())
            self.assertIn("09_templates/", buffer.getvalue())
            today = ros_demo.run(vault, "today")
            self.assertIn("Questions for you (0;", today)
            self.assertNotIn("Commitment list problems", today)
            self.assertIn("My Research Commitments", portfolio)
            self.assertIn('"language": "en"', (vault / "config" / "ros.json").read_text(encoding="utf-8"))
            zh_vault = Path(tmp) / "zh_vault"
            zh_buffer = io.StringIO()
            with redirect_stdout(zh_buffer):
                self.assertEqual(ros_demo.main(["--init", str(zh_vault), "--lang", "zh-CN"]), 0)
            self.assertIn("已从虚构演示库建好", zh_buffer.getvalue())
            self.assertIn('"language": "zh-CN"', (zh_vault / "config" / "ros.json").read_text(encoding="utf-8"))
            zh_portfolio = (zh_vault / "06_active_context" / "research-portfolio.md").read_text(encoding="utf-8")
            self.assertIn("我的研究承诺", zh_portfolio)
            self.assertNotIn("[!judgment]", zh_portfolio)
            self.assertNotIn("- judgments:", zh_portfolio)
            self.assertFalse((zh_vault / "sample-answer.md").exists())
            zh_today = ros_demo.run(zh_vault, "today", lang="zh-CN")
            for title in ("遮挡鲁棒跟踪（虚构）", "示例遮挡基准（虚构）", "遮挡迁移论文"):
                self.assertIn(title, zh_today)
            self.assertNotIn("Occlusion", zh_today)

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(ros_demo.main(["--init", str(vault)]), 2)
            self.assertEqual(len(stderr.getvalue().strip().splitlines()), 1)
            self.assertIn("already exists", stderr.getvalue())

    def test_chinese_fixture_has_the_english_fixtures_shape(self) -> None:
        def shape(path: Path) -> tuple:
            files = sorted(p.relative_to(path).as_posix() for p in path.rglob("*")
                           if p.is_file() and "work_state" not in p.parts)
            text = "\n".join((path / f).read_text(encoding="utf-8") for f in files if f.endswith(".md"))
            ids = re.findall(r"^- id: (\S+)$|^> \[!judgment\] (\S+)$|^id: (\S+)$", text, re.MULTILINE)
            return files, sorted(ids)
        self.assertEqual(shape(ros_demo.DEMO), shape(ros_demo.DEMO_ZH), "same files and ids, so the same commands work")

    def test_sample_answer_collects_into_one_candidate_without_changing_the_graph(self) -> None:
        sample = ros_demo.DEMO / "sample-answer.md"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "demo"
            shutil.copytree(ros_demo.DEMO, root, ignore=shutil.ignore_patterns("work_state"))
            ros_demo.run(root, "today")
            packet = ros_demo.run(root, "run", "judgment", "--target", "commitment:occlusion-paper",
                                  "--executor", "copy_packet")
            run_id = re.search(r"\(run (ros-run-[0-9a-f]+)\)", packet).group(1)
            collected = ros_demo.run(root, "collect", run_id, "--file", str(sample))
            self.assertIn("returned 1 candidate(s)", collected)
            self.assertIn("since the last ros command: 0 new, 0 changed",
                          ros_demo.run(root, "today").lower(), "the sample answer is outside graph_roots")


if __name__ == "__main__":
    unittest.main()
