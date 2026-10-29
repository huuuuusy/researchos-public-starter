from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "scripts"))

from researchos_data.plugin_docs import README_SECTIONS, validate_documentation


class DocumentationError(ValueError):
    pass


def fail(source: Path, message: str) -> DocumentationError:
    return DocumentationError(f"{source}: {message}")


class PluginDocumentationTest(unittest.TestCase):
    def fixture(self, *, omit: Optional[str] = None) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        context = tempfile.TemporaryDirectory()
        root = Path(context.name)
        source = root / "config/extensions/fixture.example.json"
        source.parent.mkdir(parents=True)
        source.write_text("{}", encoding="utf-8")
        readme = root / "docs/plugins/fixture-plugin/README.md"
        readme.parent.mkdir(parents=True)
        headings = [heading for heading in README_SECTIONS if heading != omit]
        readme.write_text(
            "# Fixture\n\n" + "\n\n".join(f"## {heading}\n\nBounded content." for heading in headings) + "\n",
            encoding="utf-8",
        )
        return context, root, source

    def test_complete_repository_local_readme_validates(self) -> None:
        context, root, source = self.fixture()
        with context:
            result = validate_documentation(
                {"readme": "docs/plugins/fixture-plugin/README.md"},
                root=root,
                source=source,
                plugin_id="fixture_plugin",
                fail=fail,
            )
        self.assertEqual("docs/plugins/fixture-plugin/README.md", result["readme"])

    def test_wrong_or_escaping_path_fails_closed(self) -> None:
        context, root, source = self.fixture()
        with context:
            with self.assertRaisesRegex(DocumentationError, "must be docs/plugins"):
                validate_documentation(
                    {"readme": "../README.md"}, root=root, source=source,
                    plugin_id="fixture_plugin", fail=fail,
                )
            readme = root / "docs/plugins/fixture-plugin/README.md"
            target = root / "docs/plugins/fixture-plugin/actual.md"
            readme.replace(target)
            readme.symlink_to(target)
            with self.assertRaisesRegex(DocumentationError, "must not use symlinks"):
                validate_documentation(
                    {"readme": "docs/plugins/fixture-plugin/README.md"}, root=root,
                    source=source, plugin_id="fixture_plugin", fail=fail,
                )

    def test_missing_required_section_fails_closed(self) -> None:
        context, root, source = self.fixture(omit="Failure recovery")
        with context, self.assertRaisesRegex(DocumentationError, "Failure recovery"):
            validate_documentation(
                {"readme": "docs/plugins/fixture-plugin/README.md"},
                root=root,
                source=source,
                plugin_id="fixture_plugin",
                fail=fail,
            )


if __name__ == "__main__":
    unittest.main()
