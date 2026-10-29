from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from research_agenda_projection import public_research_agenda, research_agenda_from_markdown  # noqa: E402
from query_research_agenda import _selected  # noqa: E402


class ResearchAgendaProjectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agenda = research_agenda_from_markdown(
            ROOT,
            ROOT / "08_exports/public_starter/demo-research-agenda.md",
            language="en",
            presentation_mode="public_demo",
            boundary="fictional_public_demo_only",
            sensitivity="public",
            updated="2026-07-16",
            today=date(2026, 8, 11),
        )

    def test_demo_agenda_is_public_safe_and_time_bounded(self) -> None:
        self.assertTrue(self.agenda["available"])
        self.assertEqual(self.agenda["presentation_mode"], "public_demo")
        self.assertEqual(self.agenda["boundary"], "fictional_public_demo_only")
        self.assertEqual(len(self.agenda["items"]), 6)
        self.assertEqual(self.agenda["answer"]["lead_active"], 2)
        self.assertEqual(self.agenda["answer"]["support_active"], 1)
        self.assertEqual(self.agenda["answer"]["waiting"], 1)
        self.assertEqual(self.agenda["answer"]["paused"], 1)
        self.assertEqual(self.agenda["answer"]["needs_review"], 1)
        self.assertEqual(self.agenda["responsibility_counts"], {"lead": 4, "support": 2, "unclassified": 0})
        self.assertEqual(self.agenda["phase_counts"]["experiment_preparation"], 1)
        self.assertEqual(self.agenda["phase_counts"]["paused"], 1)
        self.assertEqual(self.agenda["phase_counts"]["rebuttal"], 1)
        self.assertEqual(self.agenda["phase_counts"]["revision"], 1)
        self.assertEqual(self.agenda["phase_counts"]["scoping"], 1)
        self.assertEqual(self.agenda["phase_counts"]["under_review"], 1)
        self.assertTrue(self.agenda["answer"]["coverage_verified"])
        self.assertEqual(self.agenda["integrity"]["status"], "pass")
        by_id = {item["id"]: item for item in self.agenda["items"]}
        self.assertEqual(by_id["demo-revision-claim-closeout"]["attention_date"], "2026-08-11")
        self.assertEqual(by_id["demo-evaluation-pilot"]["attention_date"], "2026-08-12")
        self.assertEqual(by_id["demo-collaborator-review"]["attention_date"], "2026-08-14")
        self.assertEqual(by_id["demo-survey-scope-gate"]["deadline"], "2026-09-15")

    def test_every_item_separates_human_and_assistant_work(self) -> None:
        for item in self.agenda["items"]:
            self.assertTrue(item["accountable_owner"])
            self.assertIn(item["responsibility"], {"lead", "support", "unclassified"})
            self.assertTrue(item["role_summary"])
            self.assertIn(item["lifecycle_phase"], {
                "scoping", "experiment_preparation", "rebuttal", "revision", "under_review", "paused"
            })
            if item["responsibility"] == "lead":
                self.assertEqual(item["accountable_owner"], "You")
            self.assertTrue(item["assistant"])
            self.assertTrue(item["self_action"])
            self.assertTrue(item["ai_action"])
            self.assertTrue(item["next_step"])
            self.assertRegex(item["project_maturity"], r"^I[0-3](?:_|$)")
            self.assertTrue(item["related_people"])
            self.assertTrue(item["source_available"])
            self.assertIn("Do not use private material", item["action_prompt"])
            self.assertIn("Do not write it automatically", item["adjust_prompt"])
            self.assertIn("verifiable evidence", item["adjust_prompt"])
            self.assertIn("success gate", item["adjust_prompt"])
            self.assertIn("responsibility", item["adjust_prompt"])
            self.assertTrue(item["last_verified"])
        support = next(item for item in self.agenda["items"] if item["responsibility"] == "support")
        self.assertIn("support-role boundary", support["action_prompt"])
        self.assertIn("Do not promote a support item", support["action_prompt"])
        background = next(item for item in self.agenda["items"] if item["lifecycle_phase"] == "under_review")
        self.assertEqual(background["state"], "waiting")
        self.assertTrue(background["activation_trigger"])

    def test_explicit_views_match_private_contract(self) -> None:
        items = self.agenda["items"]
        self.assertEqual(len(_selected(items, "lead-active")), 2)
        self.assertEqual(len(_selected(items, "lead-all")), 4)
        self.assertEqual(len(_selected(items, "support-active")), 1)
        self.assertEqual(len(_selected(items, "support-all")), 2)
        self.assertEqual(len(_selected(items, "unclassified")), 0)
        self.assertEqual(len(_selected(items, "lead")), 2)
        self.assertEqual(len(_selected(items, "support")), 1)

    def test_chinese_demo_uses_the_same_public_boundary(self) -> None:
        agenda = research_agenda_from_markdown(
            ROOT,
            ROOT / "08_exports/public_starter/demo-research-agenda.zh.md",
            language="zh-CN",
            presentation_mode="public_demo",
            boundary="fictional_public_demo_only",
            sensitivity="public",
            updated="2026-07-16",
            today=date(2026, 7, 26),
        )
        self.assertEqual(agenda["answer"]["lead_active"], 2)
        self.assertEqual(agenda["answer"]["support_active"], 1)
        self.assertEqual({item["accountable_owner"] for item in agenda["items"] if item["responsibility"] == "lead"}, {"你"})
        self.assertTrue(all("不要调用私人材料" in item["action_prompt"] for item in agenda["items"]))

    def test_public_projection_carries_both_ui_languages(self) -> None:
        agenda = public_research_agenda(
            ROOT,
            ROOT / "08_exports/public_starter",
            {
                "case_materials": {"content_language": "en", "enabled": True},
                "generated_at": "2026-08-10",
            },
        )
        item = next(entry for entry in agenda["items"] if entry["id"] == "demo-evaluation-pilot")
        self.assertEqual(item["title"], "Evaluation Pilot Decision")
        self.assertEqual(item["localized"]["zh-CN"]["title"], "评估 Pilot 判断")
        self.assertIn("检查 pilot 证据", item["localized"]["zh-CN"]["next_step"])
        self.assertIn("Inspect the pilot evidence", item["localized"]["en"]["next_step"])
        self.assertTrue(item["localized"]["zh-CN"]["source_path"].endswith("demo-research-agenda.zh.md"))

    def test_personal_vault_prompts_use_local_authority_not_fictional_demo_language(self) -> None:
        agenda = research_agenda_from_markdown(
            ROOT,
            ROOT / "08_exports/public_starter/demo-research-agenda.md",
            language="en",
            presentation_mode="personal_vault",
            boundary="local_private_material",
            sensitivity="private",
            updated="2026-07-16",
        )
        self.assertTrue(all("local authority source" in item["action_prompt"] for item in agenda["items"]))
        self.assertTrue(all("fictional Research Agenda item" not in item["action_prompt"] for item in agenda["items"]))
        self.assertTrue(all("Do not use private material" not in item["action_prompt"] for item in agenda["items"]))

    def test_disabling_demo_cases_removes_the_demo_agenda_from_active_data(self) -> None:
        agenda = public_research_agenda(
            ROOT,
            ROOT / "08_exports/public_starter",
            {
                "case_materials": {"content_language": "en", "enabled": False},
                "generated_at": "2026-07-16",
            },
        )
        self.assertFalse(agenda["available"])
        self.assertEqual(agenda["items"], [])
        self.assertEqual(agenda["schedule_counts"], {"today": 0, "this_week": 0, "later": 0})

    def test_duplicate_item_ids_fail_closed_before_reaching_the_dom(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "agenda.md"
            path.write_text(
                "## Responsibility Items\n\n"
                "### One\n\n- id: duplicate\n- next_step: First\n\n"
                "### Two\n\n- id: duplicate\n- next_step: Second\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate Research Agenda item id"):
                research_agenda_from_markdown(
                    root,
                    path,
                    language="en",
                    presentation_mode="personal_vault",
                    boundary="local_private_material",
                    sensitivity="private",
                )

    def test_invalid_responsibility_future_date_and_missing_action_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "agenda.md"
            path.write_text(
                "## Coverage Receipt\n\n"
                "- coverage_scope: fixture\n"
                "- coverage_status: reviewed\n"
                "- coverage_reviewed: 2026-07-26\n"
                "- coverage_sources: agenda.md\n\n"
                "## Responsibility Items\n\n"
                "### Bad\n\n"
                "- id: bad\n"
                "- responsibility: reviewer\n"
                "- accountable_owner: Collaborator\n"
                "- role_summary: Reviewer\n"
                "- state: mainline\n"
                "- next_step:\n"
                "- last_verified: 2026-07-27\n"
                "- source_path: agenda.md\n",
                encoding="utf-8",
            )
            agenda = research_agenda_from_markdown(
                root,
                path,
                language="en",
                presentation_mode="personal_vault",
                boundary="local_private_material",
                sensitivity="private",
                today=date(2026, 7, 26),
            )
            item = agenda["items"][0]
            self.assertEqual(item["responsibility"], "unclassified")
            self.assertEqual(agenda["answer"]["lead_active"], 0)
            self.assertEqual(item["freshness"], "unverified")
            self.assertIn("invalid_responsibility", item["quality_issues"])
            self.assertIn("future_last_verified", item["quality_issues"])
            self.assertIn("missing_next_step", item["quality_issues"])
            self.assertIn("missing_lifecycle_phase", item["quality_issues"])
            self.assertEqual(agenda["integrity"]["status"], "needs_attention")


if __name__ == "__main__":
    unittest.main()
