from __future__ import annotations
import json
import io
from contextlib import redirect_stdout
from unittest import mock
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import plan_context
from researchos_data.plugin_lifecycle import apply_action
from researchos_data.task_extensions import TaskExtensionError, load_task_extensions

PACKAGE = Path('docs/plugins/method-comparison')
DESCRIPTOR = Path('config/extensions/method-comparison.example.json')
ADAPTER = (PACKAGE / 'skill-adapter.md').as_posix()


class MethodComparisonExampleTest(unittest.TestCase):
    def fixture(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        shutil.copytree(ROOT / PACKAGE, root / PACKAGE)
        target = root / DESCRIPTOR
        target.parent.mkdir(parents=True)
        shutil.copy2(ROOT / DESCRIPTOR, target)
        data = json.loads(target.read_text())
        for paths in data['task']['read'].values():
            for rel in paths:
                p = root / rel
                if not p.exists():
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text('---\nsensitivity: public\n---\nGeneral workflow fixture.\n')
        return tmp

    def run_builder(self, root, flag):
        return subprocess.run([sys.executable, str(root / PACKAGE / 'build_adapter.py'), flag],
                              cwd=root, capture_output=True, text=True)

    def test_adapter_is_reproducible_and_check_does_not_write(self):
        with self.fixture() as directory:
            root = Path(directory)
            before = (root / ADAPTER).read_bytes()
            self.assertEqual(self.run_builder(root, '--check').returncode, 0)
            self.assertEqual((root / ADAPTER).read_bytes(), before)
            self.assertEqual(self.run_builder(root, '--write').returncode, 0)
            self.assertEqual((root / ADAPTER).read_bytes(), before)

    def test_method_drift_is_detected_until_explicit_rebuild(self):
        with self.fixture() as directory:
            root = Path(directory)
            skill = root / PACKAGE / 'researchos-method-comparison/SKILL.md'
            original_adapter = (root / ADAPTER).read_bytes()
            skill.write_text(skill.read_text() + '\nA revised method condition.\n')
            self.assertNotEqual(self.run_builder(root, '--check').returncode, 0)
            self.assertEqual((root / ADAPTER).read_bytes(), original_adapter)
            self.assertEqual(self.run_builder(root, '--write').returncode, 0)
            self.assertNotEqual((root / ADAPTER).read_bytes(), original_adapter)
            self.assertEqual(self.run_builder(root, '--check').returncode, 0)

    def test_adapter_tampering_is_detected(self):
        with self.fixture() as directory:
            root = Path(directory)
            p = root / ADAPTER
            p.write_text(p.read_text() + '\nUnreviewed extra instruction.\n')
            self.assertNotEqual(self.run_builder(root, '--check').returncode, 0)

    def test_scoped_variants_load_method_in_both_languages(self):
        with self.fixture() as directory:
            root = Path(directory)
            descriptor = json.loads((root / DESCRIPTOR).read_text())
            apply_action(root, 'method_comparison', 'install')
            for scope in descriptor['available_in']:
                for lang in ('en', 'zh-CN'):
                    with self.subTest(scope=scope, lang=lang):
                        tasks = load_task_extensions(root, runtime_scope=scope, language=lang)['tasks']
                        self.assertEqual(len(tasks), 1)
                        task = tasks[0]
                        self.assertEqual(task['read_first'], [ADAPTER])
                        self.assertEqual(task['extension_version'], '1.1.0')
                        self.assertEqual(task['default_result_mode'], 'answer')
                        output = io.StringIO()
                        argv = ['plan_context.py', 'method_comparison', '--lang', lang, '--mode', 'standard', '--headless-json']
                        with mock.patch.object(plan_context, 'route_for', return_value=task), mock.patch.object(sys, 'argv', argv), redirect_stdout(output):
                            self.assertIn(plan_context.main(), (None, 0))
                        plan = json.loads(output.getvalue())
                        self.assertIn(ADAPTER, plan['read_now'])
                        self.assertEqual(plan['extension']['version'], '1.1.0')
                        self.assertIn('--expected-extension-version 1.1.0', plan['extension']['resume_command'])
                        for tier in task['read_tiers']:
                            self.assertIn(ADAPTER, tier['read'])
                            self.assertLessEqual(len(tier['read']), tier['file_limit'])

    def test_lifecycle_removes_route_and_preserves_method_and_results(self):
        with self.fixture() as directory:
            root = Path(directory)
            result = root / 'earlier-result.md'
            result.write_text('Earlier comparison and its grounds.\n')
            before = (root / ADAPTER).read_bytes()
            for action, expected in [('install', 1), ('disable', 0), ('enable', 1), ('uninstall', 0)]:
                apply_action(root, 'method_comparison', action)
                tasks = load_task_extensions(root, runtime_scope='private', language='en')['tasks']
                self.assertEqual(len(tasks), expected)
            self.assertEqual((root / ADAPTER).read_bytes(), before)
            self.assertEqual(result.read_text(), 'Earlier comparison and its grounds.\n')

    def test_missing_method_entry_blocks_route_loading(self):
        with self.fixture() as directory:
            root = Path(directory)
            apply_action(root, 'method_comparison', 'install')
            (root / ADAPTER).unlink()
            with self.assertRaises(TaskExtensionError):
                load_task_extensions(root, runtime_scope='private', language='en')

    def test_symlink_output_cannot_overwrite_another_file(self):
        with self.fixture() as directory:
            root = Path(directory)
            victim = root / 'keep.md'
            victim.write_text('Keep this file.\n')
            target = root / ADAPTER
            target.unlink()
            target.symlink_to(victim)
            self.assertNotEqual(self.run_builder(root, '--write').returncode, 0)
            self.assertEqual(victim.read_text(), 'Keep this file.\n')


if __name__ == '__main__':
    unittest.main()
