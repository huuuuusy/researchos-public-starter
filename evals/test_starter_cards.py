"""The example cards and basic skeletons stay readable by ros, the Dashboard builder and plan_context."""

from __future__ import annotations

import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ros_demo  # noqa: E402
from build_public_starter_data import agent_summary, parse_frontmatter  # noqa: E402


EXAMPLES = ROOT / "examples" / "starter-cards"
BASIC = ROOT / "09_templates" / "basic"
SENSITIVITY = {"public", "internal", "sensitive", "private"}
# The level patterns the Dashboard accepts (dashboard/src/core/contracts.js, normalizedCardMaturityLevel).
LEVELS = {
    "analysis_state": re.compile(r"^M[1-3](?:_|$)"),
    "project_maturity": re.compile(r"^I[0-3](?:_|$)"),
    "relationship_maturity": re.compile(r"^R[0-3](?:_|$)"),
    "group_level": re.compile(r"^G[0-2](?:_|$)"),
}
SKELETONS = {"research-identity", "boundaries", "capsule", "project", "paper", "outputs-index", "decision", "style",
             "heuristic", "mental-model", "person", "author-roles", "feedback", "meeting", "review", "grant", "message"}
STYLE_TASKS = {"writing", "review", "proposal", "figures-talks", "mentoring"}
LINK = re.compile(r"\]\(([^)#\s]+\.md)\)")
# Each point of a working-style card has the rule, why, how to apply and its source.
STYLE_POINT_SECTIONS = {"en": ("## What I do", "## What I cut or avoid"), "zh": ("## 我的做法", "## 我会删掉或避开的")}
STYLE_POINT_PARTS = {"en": ("Why:", "How to apply:", "Source:"), "zh": ("为什么：", "怎么用：", "出处：")}


def frontmatter_lines(text: str) -> list[str]:
    return text.split("\n---\n", 1)[0].removeprefix("---\n").splitlines()


def style_points(text: str, lang: str) -> list[list[str]]:
    """The points under a style card's "what I do" and "what I cut" sections, each as its sub-bullet lines."""
    points: list[list[str]] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.startswith(STYLE_POINT_SECTIONS[lang])
        elif inside and line.startswith("- "):
            points.append([])
        elif inside and points and line.startswith("  - "):
            points[-1].append(line.strip()[2:])
    return points


class StarterCardsTest(unittest.TestCase):
    def cards(self, lang: str) -> list[Path]:
        return sorted(path for path in (EXAMPLES / lang).rglob("*.md") if path.name != "README.md")

    def test_both_languages_hold_the_same_cards(self) -> None:
        en = {path.relative_to(EXAMPLES / "en") for path in self.cards("en")}
        zh = {path.relative_to(EXAMPLES / "zh-CN") for path in self.cards("zh-CN")}
        self.assertEqual(en, zh)
        self.assertEqual(len(en), 12)
        skeletons = {path.name for path in BASIC.glob("*.md") if not path.name.startswith("README")}
        self.assertEqual({name.removesuffix(".md") for name in skeletons if not name.endswith(".zh.md")}, SKELETONS)
        self.assertEqual({name for name in skeletons if not name.endswith(".zh.md")},
                         {name.replace(".zh.md", ".md") for name in skeletons if name.endswith(".zh.md")})

    def test_every_card_and_skeleton_reads_the_way_its_readme_says(self) -> None:
        files = [*self.cards("en"), *self.cards("zh-CN"),
                 *(path for path in BASIC.glob("*.md") if not path.name.startswith("README"))]
        for path in files:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                meta = parse_frontmatter(text)
                self.assertTrue(meta.get("title"), "ros shows a card under its title")
                self.assertTrue(agent_summary(text), "level 1 needs an Agent Summary")
                chinese = "zh-CN" in path.parts or path.name.endswith(".zh.md")
                self.assertIn("## 证据边界" if chinese else "## Evidence boundary", text)
                self.assertIn(meta.get("sensitivity"), SENSITIVITY)
                for line in frontmatter_lines(text):
                    self.assertNotRegex(line, r"\s#\s", "a trailing comment would be read as part of the value")
                for field, pattern in LEVELS.items():
                    if field in meta:
                        self.assertRegex(str(meta[field]), pattern)
                if meta.get("type") == "style":
                    self.assertIn(meta.get("task"), STYLE_TASKS)
                    self.assertIn(meta.get("status"), {"provisional", "confirmed"})
                    points = style_points(text, "zh" if chinese else "en")
                    self.assertTrue(points, "a style card lists its points")
                    for parts in points:
                        for prefix in STYLE_POINT_PARTS["zh" if chinese else "en"]:
                            self.assertTrue(any(part.startswith(prefix) for part in parts),
                                            f"a style point lacks {prefix!r}: {parts}")
        for lang in ("en", "zh-CN"):
            for path in [*self.cards(lang), EXAMPLES / lang / "README.md"]:
                for target in LINK.findall(path.read_text(encoding="utf-8")):
                    with self.subTest(path=path.relative_to(ROOT).as_posix(), link=target):
                        self.assertTrue((path.parent / target).resolve().is_file())
                meta = parse_frontmatter(path.read_text(encoding="utf-8"))
                for key in ("related_projects", "related_papers", "related_people", "source_files", "related_examples"):
                    for ref in meta.get(key) or []:
                        self.assertTrue((EXAMPLES / lang / ref).is_file(), f"{path.name}: {key} {ref}")

    def test_people_and_meetings_need_a_terminal_confirmation_and_the_rest_is_packed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(ros_demo.main(["--init", str(vault)]), 0)
            for name in ("occlusion-tracking.md", "example-benchmark.md"):
                next(vault.rglob(name)).unlink()
            shutil.copytree(EXAMPLES / "en", vault, dirs_exist_ok=True, ignore=shutil.ignore_patterns("README.md"))
            # first, while every card still counts as new; --all lists every change, not only the first ten
            today = ros_demo.run(vault, "today", "--all")
            self.assertIn("0 problems", ros_demo.run(vault, "rules", "--check"))
            for title in ("Research identity (fictional)", "Lin Ke (fictional)",
                          "Run the heavy-occlusion comparison after benchmark version 2 (fictional)",
                          "Check the benchmark version before comparing (fictional)"):
                self.assertIn(title, today)
            self.assertIn("[delivered 1; excluded 0]", ros_demo.run(vault, "context", "01_knowledge/papers/example-benchmark.md"))
            self.assertIn("[delivered 0; excluded 1]", ros_demo.run(vault, "context", "04_people/collaborators/lin-ke.md"))
            self.assertIn("[delivered 1; excluded 0]",
                          ros_demo.run(vault, "context", "04_people/collaborators/lin-ke.md", answer="y"))

    def test_init_reads_decisions_and_heuristics_and_speaks_the_vault_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "zh"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(ros_demo.main(["--init", str(vault), "--lang", "zh-CN"]), 0)
            roots = json.loads((vault / "config" / "ros.json").read_text(encoding="utf-8"))["graph_roots"]
            self.assertIn("02_decisions", roots)
            self.assertIn("03_cognition", roots)
            portfolio = (vault / "06_active_context" / "research-portfolio.md").read_text(encoding="utf-8")
            self.assertIn("question: 方法 A 在重度遮挡下还好于方法 B 吗？", portfolio)
            self.assertNotIn("Occlusion Transfer Paper", portfolio)


if __name__ == "__main__":
    unittest.main()
