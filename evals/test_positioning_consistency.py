from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_positioning_consistency import (  # noqa: E402
    REQUIRED_MARKERS,
    STALE_POSITIONING,
    validate,
)


class PositioningConsistencyTest(unittest.TestCase):
    def test_current_active_documents_are_aligned(self) -> None:
        self.assertEqual(validate(ROOT), [])

    def test_stale_dashboard_first_language_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative_path, markers in REQUIRED_MARKERS.items():
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n".join(markers), encoding="utf-8")
            target = root / "README.md"
            target.write_text(
                target.read_text(encoding="utf-8") + f"\n{STALE_POSITIONING[2]}\n",
                encoding="utf-8",
            )
            failures = validate(root)
            self.assertTrue(any("stale positioning" in failure for failure in failures))

    def test_agent_entrypoint_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative_path, markers in REQUIRED_MARKERS.items():
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n".join(markers), encoding="utf-8")
            target = root / "AGENTS.md"
            target.write_text(
                target.read_text(encoding="utf-8") + "\nNeither is subordinate to the other.\n",
                encoding="utf-8",
            )
            failures = validate(root)
            self.assertTrue(any("AGENTS.md contains stale positioning" in failure for failure in failures))

    def test_task_packet_page_claim_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative_path, markers in REQUIRED_MARKERS.items():
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n".join(markers), encoding="utf-8")
            target = root / "dashboard/src/services/work-session-router.js"
            target.write_text(
                target.read_text(encoding="utf-8") + "\nreturn the complete readable result to the page\n",
                encoding="utf-8",
            )
            failures = validate(root)
            self.assertTrue(any("work-session-router.js contains stale positioning" in failure for failure in failures))

    def test_public_local_codex_claim_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative_path, markers in REQUIRED_MARKERS.items():
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n".join(markers), encoding="utf-8")
            target = root / "README.md"
            target.write_text(
                target.read_text(encoding="utf-8") + "\nLocal Codex read-only\n",
                encoding="utf-8",
            )
            failures = validate(root)
            self.assertTrue(any("README.md contains stale positioning" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
