"""plan_context reads the user's own cards level by level; the vault check and agenda query read the vault."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_public_starter_data  # noqa: E402

EXAMPLES = ROOT / "examples" / "starter-cards" / "en"


def route(task: str, mode: str, vault: Path | None = None, lang: str = "en") -> dict:
    command = [sys.executable, str(ROOT / "scripts" / "plan_context.py"), task, "--json", "--mode", mode, "--lang", lang]
    if vault is not None:
        command += ["--vault", str(vault)]
    return json.loads(subprocess.run(command, capture_output=True, text=True, check=True).stdout)


def text(task: str, mode: str, vault: Path, lang: str = "en") -> str:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "plan_context.py"), task, "--mode", mode, "--lang", lang,
                           "--vault", str(vault)], capture_output=True, text=True, check=True).stdout


class VaultReadingLevelsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / "vault"
        shutil.copytree(EXAMPLES, self.vault)
        (self.vault / "README.md").unlink()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_each_level_reads_the_users_own_cards_first(self) -> None:
        style = (self.vault / "03_cognition" / "style" / "writing.md").as_posix()
        identity = (self.vault / "00_identity" / "research-identity.md").as_posix()
        summary = (self.vault / "01_knowledge" / "capsules" / "occlusion-tracking-capsule.md").as_posix()
        quick = route("paper_writing", "quick", self.vault)
        self.assertEqual(quick["read_now"], [style] if Path(style).is_file() else [identity])
        standard = route("paper_writing", "standard", self.vault)
        self.assertLessEqual(len(standard["read_now"]), standard["file_limit"])
        self.assertEqual(standard["read_now"][0], quick["read_now"][0])
        self.assertIn(identity, standard["read_now"])
        self.assertIn(summary, standard["read_now"])
        self.assertIn("05_workflows/research_work/paper-writing.md", standard["read_now"])
        self.assertTrue(set(quick["read_now"]) <= set(standard["read_now"]))
        evidence = route("paper_writing", "evidence", self.vault)
        self.assertTrue(set(standard["read_now"]) <= set(evidence["read_now"]))
        self.assertIn("Originals: open only those named in the Evidence boundary", text("paper_writing", "evidence", self.vault))
        self.assertNotIn("Originals:", text("paper_writing", "standard", self.vault))
        self.assertEqual(standard["escalate_to"], "evidence")
        paper = (self.vault / "01_knowledge" / "papers" / "example-benchmark.md").as_posix()
        self.assertIn(paper, standard["vault_entry"]["named_cards"])
        self.assertEqual(quick["vault_entry"]["named_cards"], [])
        self.assertNotIn("stay on this computer", text("paper_writing", "quick", self.vault))

    def test_missing_cards_are_named_with_their_skeleton(self) -> None:
        (self.vault / "03_cognition" / "style" / "writing.md").unlink(missing_ok=True)
        shutil.rmtree(self.vault / "01_knowledge" / "capsules")
        out = text("peer_review", "quick", self.vault)
        self.assertIn("Not in your vault yet", out)
        self.assertIn("03_cognition/style/review.md ← 09_templates/basic/style.md", out)
        self.assertIn("09_templates/basic/capsule.md", out)
        zh = text("peer_review", "quick", self.vault, "zh-CN")
        self.assertIn("你的库里还没有", zh)
        self.assertIn("09_templates/basic/style.zh.md", zh)

    def test_the_vault_language_is_used_without_lang(self) -> None:
        (self.vault / "config").mkdir(exist_ok=True)
        (self.vault / "config" / "ros.json").write_text('{"language": "zh-CN"}', encoding="utf-8")
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "plan_context.py"), "paper_writing", "--vault", str(self.vault)],
                             capture_output=True, text=True, check=True).stdout
        self.assertIn("当前模板语言: zh-CN", out)
        self.assertIn("05_workflows/research_work/paper-writing.zh.md", route("paper_writing", "standard", self.vault, "zh-CN")["read_now"])

    def test_boundary_card_comes_first_outward_and_indexes_at_evidence(self) -> None:
        card = "---\ntitle: x\nsensitivity: internal\n---\n\n## Agent Summary\n\nx\n"
        boundaries = self.vault / "00_identity" / "boundaries.md"
        outputs = self.vault / "01_knowledge" / "papers" / "outputs-index.md"
        roles = self.vault / "01_knowledge" / "papers" / "author-roles.md"
        for path in (boundaries, outputs, roles):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(card, encoding="utf-8")
        self.assertEqual(route("safe_export", "quick", self.vault)["read_now"], [boundaries.as_posix()])
        self.assertIn(boundaries.as_posix(), route("proposal", "standard", self.vault)["read_now"])
        standard = route("proposal", "standard", self.vault)["read_now"]
        evidence = route("proposal", "evidence", self.vault)["read_now"]
        self.assertNotIn(outputs.as_posix(), standard)
        self.assertTrue({outputs.as_posix(), roles.as_posix()} <= set(evidence))
        self.assertTrue(set(standard) <= set(evidence))
        roles.unlink()
        self.assertIn("01_knowledge/papers/author-roles.md ← 09_templates/basic/author-roles.md",
                      text("paper_writing", "evidence", self.vault))
        self.assertNotIn("author-roles", text("paper_writing", "standard", self.vault))

    def test_chat_pack_holds_only_deliverable_cards(self) -> None:
        out = Path(self.tmp.name) / "pack.md"
        command = [sys.executable, str(ROOT / "scripts" / "plan_context.py"), "paper_writing", "--mode", "standard",
                   "--vault", str(self.vault), "--pack", str(out)]
        printed = subprocess.run(command, capture_output=True, text=True, check=True).stdout
        self.assertIn("lin-ke.md (sensitive)", printed)
        pack = out.read_text(encoding="utf-8")
        identity = (self.vault / "00_identity" / "research-identity.md").read_text(encoding="utf-8")
        self.assertIn(identity.split("\n---\n", 1)[1].strip()[:80], pack)
        self.assertNotIn("\nsensitivity:", pack)  # frontmatter is dropped
        lin = (self.vault / "04_people" / "collaborators" / "lin-ke.md").read_text(encoding="utf-8")
        self.assertNotIn(lin.split("## Agent Summary", 1)[1].strip()[:60], pack)
        self.assertIn("ask me", pack)
        self.assertNotIn('<p align="right">', pack)
        self.assertNotIn("python3 scripts/", pack)  # a browser chat cannot run commands
        self.assertIn("## Steps", pack)
        # inline source_files lists are read too
        capsule = self.vault / "01_knowledge" / "capsules" / "occlusion-tracking-capsule.md"
        text_ = capsule.read_text(encoding="utf-8")
        head, rest = text_.split("\n---\n", 1)
        lines, items, skipping = [], [], False
        for line in head.splitlines():
            if line.startswith("source_files:"):
                skipping = True
                continue
            if skipping and line.startswith("  - "):
                items.append(line[4:])
                continue
            skipping = False
            lines.append(line)
        capsule.write_text("\n".join(lines) + "\nsource_files: [" + ", ".join(items) + "]\n---\n" + rest, encoding="utf-8")
        self.assertTrue(route("paper_writing", "standard", self.vault)["vault_entry"]["named_cards"])
        refused = subprocess.run([*command[:-1], str(ROOT / "docs" / "pack.md")], capture_output=True, text=True)
        self.assertNotEqual(refused.returncode, 0)
        self.assertFalse((ROOT / "docs" / "pack.md").exists())

    def test_chat_pack_carries_the_commitments_its_cards_belong_to(self) -> None:
        portfolio = self.vault / "06_active_context" / "research-portfolio.md"
        portfolio.parent.mkdir(parents=True, exist_ok=True)
        portfolio.write_text("---\ntitle: c\nsensitivity: internal\n---\n\n# c\n\n## Responsibility Items\n\n"
                             "### Occlusion paper\n\n- id: occ\n- question: Does A still beat B?\n"
                             "- source_path: 01_knowledge/projects/occlusion-tracking.md\n\n"
                             "### Other\n\n- id: other\n- source_path: 01_knowledge/projects/elsewhere.md\n", encoding="utf-8")
        out = Path(self.tmp.name) / "pack.md"
        subprocess.run([sys.executable, str(ROOT / "scripts" / "plan_context.py"), "paper_writing", "--mode", "standard",
                        "--vault", str(self.vault), "--pack", str(out)], capture_output=True, text=True, check=True)
        pack = out.read_text(encoding="utf-8")
        self.assertIn("### Occlusion paper", pack)
        self.assertIn("Does A still beat B?", pack)
        self.assertNotIn("### Other", pack)

    def test_an_empty_vault_falls_back_to_the_task_files(self) -> None:
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        self.assertEqual(route("paper_writing", "quick", empty)["read_now"], route("paper_writing", "quick")["read_now"])

    def test_route_files_exist_and_new_routes_resolve(self) -> None:
        for task in ("peer_review", "meeting_follow_up", "mentee_feedback", "paper_writing", "proposal",
                     "presentation", "figure_design", "idea_diagnosis", "material_understanding"):
            for lang in ("en", "zh-CN"):
                for mode in ("quick", "standard", "evidence"):
                    with self.subTest(task=task, lang=lang, mode=mode):
                        for path in route(task, mode, lang=lang)["read_now"]:
                            self.assertTrue((ROOT / path).is_file(), path)

    def test_vault_check_finds_hand_written_mistakes(self) -> None:
        self.assertEqual([problem for problem in build_public_starter_data.vault_check(self.vault)
                          if "was not found on this computer" not in problem], [])
        paper = self.vault / "01_knowledge" / "papers" / "example-benchmark.md"
        card = paper.read_text(encoding="utf-8")
        card = card.replace("04_people/collaborators/lin-ke.md", "04_people/collaborators/nobody.md", 1)
        card = card.replace("sensitivity: internal", "sensitivity: Internal", 1)
        paper.write_text(card.replace("updated: 2026-09-22", "updated: 2026-10-01 # revised", 1), encoding="utf-8")
        problems = "\n".join(build_public_starter_data.vault_check(self.vault))
        self.assertIn("nobody.md, which does not exist", problems)
        self.assertIn("sensitivity is 'Internal'", problems)
        self.assertIn("ends with a # comment", problems)
        self.assertIn("check the summary again", problems)
        schedule = self.vault / "06_active_context" / "work_state" / "attention-schedule.md"
        schedule.parent.mkdir(parents=True, exist_ok=True)
        schedule.write_text("### research_portfolio:x\n\n- item_id: x\n\n### research_portfolio:x\n\n- item_id: x\n", encoding="utf-8")
        self.assertIn("research_portfolio:x has more than one entry", "\n".join(build_public_starter_data.vault_check(self.vault)))


class AgendaQueryTest(unittest.TestCase):
    def test_chinese_summary_line(self) -> None:
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "query_research_agenda.py"), "--language", "zh-CN",
                              "--path", "08_exports/public_starter/demo-research-agenda.zh.md"],
                             capture_output=True, text=True, check=True).stdout
        self.assertTrue(out.startswith("已登记且核验的主责推进中"))
        self.assertNotIn("Registered", out)


if __name__ == "__main__":
    unittest.main()
