import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "build_public_starter_data",
    ROOT / "scripts" / "build_public_starter_data.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def write_card(root: Path, relative: str, frontmatter: str, body: str = "") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter.strip()}\n---\n\n## Agent Summary\n\n{body or 'Test summary.'}\n", encoding="utf-8")


def write_agenda(root: Path) -> None:
    path = root / "06_active_context" / "research-portfolio.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "## Independent Items\n\n"
        "### Local Agenda Item\n\n"
        "- id: local-agenda-item\n"
        "- state: mainline\n"
        "- schedule_bucket: today\n"
        "- owner: You\n"
        "- assistant: Local assistant\n"
        "- next_step: Inspect the local source\n"
        "- self_action: Confirm the scope\n"
        "- ai_action: Summarize the user-provided local evidence\n"
        "- source_path: 01_knowledge/papers/example.md\n",
        encoding="utf-8",
    )


class PersonalVaultBuilderTest(unittest.TestCase):
    def test_started_onboarding_run_requires_indexable_minimum_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault = root / "personal_vault"
            write_card(
                vault,
                "06_active_context/onboarding-intake.md",
                'type: onboarding_intake\ntitle: "Onboarding Intake"\nsensitivity: private',
            )

            _, failures = MODULE.build_personal_vault_data(root=root, content_language="en", vault_root=vault)
            self.assertIn(
                "personal onboarding output missing: 00_identity/user-card.md",
                failures,
            )
            self.assertIn(
                "personal onboarding output missing: 06_active_context/onboarding-report.md",
                failures,
            )

    def test_complete_onboarding_outputs_become_expected_dashboard_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault = root / "personal_vault"
            write_card(vault, "00_identity/user-card.md", 'type: person\nname: "Local Researcher"\nsensitivity: private')
            write_card(vault, "01_knowledge/papers/publication-index.md", 'type: publication_index\ntitle: "Publication Index"\nsensitivity: private')
            write_card(
                vault,
                "01_knowledge/papers/own_papers/reading_notes/paper-one.md",
                'type: paper\ntitle: "Paper One"\nonboarding_origin: researchos_onboarding_v1\nanalysis_state: M1_registered\nsensitivity: private',
            )
            write_card(vault, "01_knowledge/projects/research-profile-synthesis.md", 'type: project\nproject_name: "Research Profile"\nsensitivity: private')
            write_card(vault, "06_active_context/onboarding-intake.md", 'type: onboarding_intake\ntitle: "Onboarding Intake"\nsensitivity: private')
            write_card(vault, "06_active_context/onboarding-report.md", 'type: onboarding_report\ntitle: "Onboarding Report"\nsensitivity: private')

            data, failures = MODULE.build_personal_vault_data(root=root, content_language="en", vault_root=vault)
            self.assertEqual(failures, [])
            projection = MODULE.build_personal_dashboard_projection(data, root=root)
            self.assertEqual(len(projection["asset_graph"]["people"]), 1)
            self.assertEqual(len(projection["asset_graph"]["papers"]), 1)
            self.assertEqual(len(projection["asset_graph"]["projects"]), 1)
            self.assertEqual(projection["asset_graph"]["papers"][0]["analysis_state"], "M1_registered")

            write_card(
                vault,
                "01_knowledge/papers/own_papers/reading_notes/paper-one.md",
                'type: paper\ntitle: "Paper One"\nonboarding_origin: researchos_onboarding_v1\nanalysis_state: M2_refined_read\nsensitivity: private',
            )
            upgraded_data, upgraded_failures = MODULE.build_personal_vault_data(
                root=root,
                content_language="en",
                vault_root=vault,
            )
            self.assertEqual(upgraded_failures, [])
            upgraded_projection = MODULE.build_personal_dashboard_projection(upgraded_data, root=root)
            self.assertEqual(upgraded_projection["asset_graph"]["papers"][0]["analysis_state"], "M2_refined_read")

    def test_dedicated_ignored_overlay_is_the_only_personal_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault = root / "personal_vault"
            write_card(root, "01_knowledge/papers/public-demo.md", 'type: reading_note\ntitle: "Tracked Demo"\nsensitivity: public')
            write_card(vault, "00_identity/user-card.md", 'type: person\ntitle: "Local Researcher"\nsensitivity: private')
            write_card(vault, "01_knowledge/papers/local-paper.md", 'type: reading_note\ntitle: "Local Paper"\nsensitivity: private')
            write_agenda(vault)

            data, failures = MODULE.build_personal_vault_data(
                root=root,
                content_language="en",
                vault_root=vault,
            )
            self.assertEqual(failures, [])
            self.assertEqual(data["record_count"], 2)
            self.assertEqual(data["vault_root"], "personal_vault")
            self.assertEqual(
                {record["path"] for record in data["records"]},
                {
                    "personal_vault/00_identity/user-card.md",
                    "personal_vault/01_knowledge/papers/local-paper.md",
                },
            )
            self.assertNotIn("public-demo.md", str(data["records"]))

            projection = MODULE.build_personal_dashboard_projection(data, root=root)
            agenda = projection["home_command_center"]["research_portfolio"]
            self.assertTrue(agenda["available"])
            self.assertEqual(projection["personal_vault"]["record_count"], 2)

    def test_scheduler_demo_copy_is_a_personal_vault_without_runtime_state(self) -> None:
        """`ros_demo.py --init personal_vault` gives the dashboard its agenda; ros runtime state stays out."""
        import io
        from contextlib import redirect_stdout

        import ros_demo

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault = root / "personal_vault"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(ros_demo.main(["--init", str(vault)]), 0)
            write_card(vault, "06_active_context/work_state/ros/packets/run.md", 'type: note\ntitle: "Task Packet"')

            data, failures = MODULE.build_personal_vault_data(root=root, content_language="en", vault_root=vault)
            self.assertEqual(failures, [])
            self.assertNotIn("work_state", str([record["path"] for record in data["records"]]))
            self.assertIn("personal_vault/06_active_context/research-portfolio.md",
                          {record["path"] for record in data["records"]})
            agenda = MODULE.build_personal_dashboard_projection(data, root=root)["home_command_center"]["research_portfolio"]
            self.assertTrue(agenda["available"])
            self.assertEqual(agenda["path"], "personal_vault/06_active_context/research-portfolio.md")
            self.assertEqual(len(agenda["items"]), 2)
            # source_path is read against the vault, as `ros --root personal_vault` reads it, and the
            # fixture's commitments carry every field the Dashboard asks for.
            self.assertEqual([item["quality_issues"] for item in agenda["items"]], [[], []])
            self.assertTrue(all(item["source_available"] for item in agenda["items"]))
            (vault / "01_knowledge" / "projects" / "occlusion-tracking.md").unlink()
            data, _ = MODULE.build_personal_vault_data(root=root, content_language="en", vault_root=vault)
            agenda = MODULE.build_personal_dashboard_projection(data, root=root)["home_command_center"]["research_portfolio"]
            self.assertIn("source_path_unavailable", agenda["items"][0]["quality_issues"])

    def test_disabled_cases_do_not_leave_demo_agenda_on_the_home_page(self) -> None:
        data, failures = MODULE.build_public_starter_data(force_cases=False, content_language="en")
        self.assertEqual(failures, [])
        self.assertEqual(data["record_count"], 0)
        projection = MODULE.build_dashboard_projection(data)
        agenda = projection["home_command_center"]["research_portfolio"]
        self.assertFalse(agenda["available"])
        self.assertEqual(agenda["items"], [])

    def test_personal_cards_are_indexed_without_public_only_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_card(
                root,
                "01_knowledge/papers/example.md",
                """
type: reading_note
title: "Example Paper"
status: active
analysis_state: M2_refined_read
sensitivity: local_only
related_people:
  - Example Researcher
related_projects:
  - Example Project
""",
            )
            write_card(root, "04_people/example.md", 'type: person\ntitle: "Example Researcher"\nsensitivity: internal')
            write_card(root, "01_knowledge/projects/example.md", 'type: project\ntitle: "Example Project"\nsensitivity: internal')
            write_agenda(root)

            data, failures = MODULE.build_personal_vault_data(root=root, content_language="en")
            self.assertEqual(failures, [])
            self.assertEqual(data["record_count"], 3)
            self.assertEqual({record["asset_kind"] for record in data["records"]}, {"paper", "person", "project"})
            self.assertEqual("en", data["case_materials"]["language_freeze"]["active_language"])
            self.assertEqual(["zh-CN"], data["case_materials"]["language_freeze"]["frozen_languages"])

            projection = MODULE.build_personal_dashboard_projection(data, root=root)
            self.assertEqual(projection["runtime_mode"], "personal_vault")
            self.assertEqual(projection["boundary"], "local_private_material")
            self.assertEqual(projection["asset_graph"]["papers"][0]["analysis_state"], "M2_refined_read")
            self.assertEqual(projection["asset_graph"]["asset_relation_matrix"][0]["relation_count"], 2)
            agenda = projection["home_command_center"]["research_portfolio"]
            self.assertTrue(agenda["available"])
            self.assertEqual(agenda["presentation_mode"], "personal_vault")
            self.assertIn("local Research Agenda item", agenda["items"][0]["action_prompt"])
            self.assertNotIn("fictional Research Agenda item", agenda["items"][0]["action_prompt"])

    def test_official_template_fields_inline_lists_and_aliases_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_card(
                root,
                "04_people/dr-rivera.md",
                "type: person\nname: 'Dr. Rivera'\nsensitivity: sensitive\nrelated_projects: [climate-lab]",
            )
            write_card(
                root,
                "01_knowledge/projects/climate-lab.md",
                'type: project\nproject_name: "Climate Lab"\nsensitivity: internal',
            )
            write_card(
                root,
                "01_knowledge/papers/field-study.md",
                "type: reading_note\ntitle: Field Study\nsensitivity: internal\nrelated_people: [dr-rivera]\nrelated_projects: [01_knowledge/projects/climate-lab.md]",
            )

            data, failures = MODULE.build_personal_vault_data(root=root, content_language="en")
            self.assertEqual(failures, [])
            by_path = {record["path"]: record for record in data["records"]}
            self.assertEqual(by_path["04_people/dr-rivera.md"]["title"], "Dr. Rivera")
            self.assertEqual(by_path["01_knowledge/projects/climate-lab.md"]["title"], "Climate Lab")
            self.assertEqual(by_path["01_knowledge/papers/field-study.md"]["related_people"], ["dr-rivera"])

            projection = MODULE.build_personal_dashboard_projection(data, root=root)
            relation = projection["asset_graph"]["asset_relation_matrix"][0]
            self.assertEqual(relation["relation_count"], 2)
            self.assertEqual(relation["people"][0]["title"], "Dr. Rivera")
            self.assertEqual(relation["projects"][0]["title"], "Climate Lab")


if __name__ == "__main__":
    unittest.main()
