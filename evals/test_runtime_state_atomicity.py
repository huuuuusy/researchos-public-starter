from __future__ import annotations

import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_kernel.atomic_files import atomic_write_text  # noqa: E402
from researchos_server.review_inbox_store import ReviewInboxStore  # noqa: E402


class RuntimeStateAtomicityTest(unittest.TestCase):
    def test_atomic_write_replaces_complete_file_without_temp_residue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "state.json"
            atomic_write_text(target, '{"version": 1}\n')
            atomic_write_text(target, '{"version": 2}\n')
            self.assertEqual({"version": 2}, json.loads(target.read_text(encoding="utf-8")))
            self.assertEqual([], list(target.parent.glob(f".{target.name}.*.tmp")))

    def test_concurrent_withdrawals_do_not_lose_updates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = ReviewInboxStore(
                root=root,
                feedback_jsonl=root / "feedback.jsonl",
                feedback_md=root / "feedback.md",
                confirmation_json=root / "confirmations.json",
                confirmation_md=root / "confirmations.md",
            )
            seeded = {f"decision-{index}": {"decision_id": f"decision-{index}", "choice": "confirm"} for index in range(24)}
            seeded["kept"] = {"decision_id": "kept", "choice": "defer"}
            atomic_write_text(store.confirmation_json, json.dumps(seeded))

            def withdraw(index: int) -> None:
                store.withdraw_confirmation({"decision_id": f"decision-{index}"})

            # A lost read-modify-write would bring a withdrawn record back.
            with ThreadPoolExecutor(max_workers=8) as executor:
                list(executor.map(withdraw, range(24)))

            records = json.loads(store.confirmation_json.read_text(encoding="utf-8"))
            self.assertEqual({"kept"}, set(records))
            self.assertIn("# UI Confirmation Decisions", store.confirmation_md.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
