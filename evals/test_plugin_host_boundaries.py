"""Host-boundary regressions using isolated manifests, never live installations."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))  # the lifecycle fixtures live in evals/test_plugin_lifecycle.py
from researchos_data import plugin_lifecycle, plugin_portfolio
from researchos_data.plugins import PluginManifestError, load_plugin_registry
from evals import test_plugin_lifecycle


class PluginHostBoundaryTest(unittest.TestCase):
    def fixture(self):
        context = test_plugin_lifecycle.PluginLifecycleTest().fixture()
        root = Path(context.name)
        example = root / 'config/extensions/method-comparison.example.json'
        data = json.loads(example.read_text())
        data['available_in'] = ['private', 'public_starter', 'personal_vault']
        data['public_safe'] = True
        data['sensitivity_default'] = 'public_safe'
        data['enabled'] = True
        source = root / 'config/extensions.local/method-comparison.json'
        source.parent.mkdir()
        source.write_text(json.dumps(data))
        return context, root, source

    def portfolio_entries(self, root):
        with mock.patch.object(plugin_portfolio, 'build_plugin_portfolio', side_effect=lambda _, entries: {"entries": entries}):
            return plugin_portfolio.current_plugin_portfolio(root, runtime_scope='public_starter')['entries']

    def test_headless_portfolio_includes_installed_task_extensions(self):
        context, root, _ = self.fixture()
        with context:
            entries = self.portfolio_entries(root)
            self.assertEqual([entry['id'] for entry in entries], ['method_comparison'])
            self.assertEqual(load_plugin_registry(root, runtime_scope='public_starter', language='en')['loaded_count'], 1)

    def test_duplicate_manifest_is_rejected_by_both_consumers(self):
        context, root, source = self.fixture()
        with context:
            source.with_name('duplicate.json').write_bytes(source.read_bytes())
            for query in (self.portfolio_entries, lambda root: load_plugin_registry(root, runtime_scope='public_starter', language='en')):
                with self.assertRaisesRegex(PluginManifestError, 'already belongs'):
                    query(root)

    def test_alias_collision_is_rejected_by_headless_portfolio(self):
        context, root, source = self.fixture()
        with context:
            data = json.loads(source.read_text()); data['id'] = 'another_comparison'
            source.with_name('another.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(PluginManifestError, 'already belongs'):
                self.portfolio_entries(root)

    def test_unknown_scope_is_not_an_empty_success(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(PluginManifestError, 'unsupported runtime scope'):
                plugin_portfolio.current_plugin_portfolio(Path(directory), runtime_scope='typo')

    def test_external_extension_is_rejected_before_reading_its_content(self):
        context, root, source = self.fixture()
        with context, tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / 'unreadable.json'; target.write_text('not JSON')
            source.unlink(); source.symlink_to(target)
            with self.assertRaisesRegex(PluginManifestError, 'stay inside'):
                self.portfolio_entries(root)

    def test_external_bundled_source_is_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory); source = root / 'config/extensions/foreign.example.json'
            source.parent.mkdir(parents=True)
            target = Path(outside) / 'unreadable.json'; target.write_text('not JSON'); source.symlink_to(target)
            with self.assertRaisesRegex(plugin_lifecycle.PluginLifecycleError, 'stay inside'):
                plugin_lifecycle.catalog(root)

    def test_write_and_restore_do_not_follow_predictable_scratch_paths(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            target = Path(directory) / 'plugin.json'
            victim = Path(outside) / 'sentinel'; victim.write_bytes(b'unchanged')
            for suffix in ('.json.tmp', '.json.rollback'):
                target.with_suffix(suffix).symlink_to(victim)
            plugin_lifecycle.atomic_write_json(target, {'id': 'fixture'})
            plugin_lifecycle._restore(target, b'old version')
            self.assertEqual(victim.read_bytes(), b'unchanged')
            self.assertEqual(target.read_bytes(), b'old version')

    def test_failed_atomic_replace_preserves_target_and_removes_scratch(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'plugin.json'; target.write_bytes(b'old version')
            with mock.patch('os.replace', side_effect=OSError('fixture failure')):
                with self.assertRaisesRegex(OSError, 'fixture failure'):
                    plugin_lifecycle.atomic_write_json(target, {'id': 'fixture'})
            self.assertEqual(target.read_bytes(), b'old version')
            self.assertEqual(list(Path(directory).iterdir()), [target])


if __name__ == '__main__':
    unittest.main()
