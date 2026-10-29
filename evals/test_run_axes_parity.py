"""The five-axis rules have one owner (run_state.py); the Desk's copy must agree until it reads the
kernel's view (D5). Every combination of the four enumerated axes, side effects and a spread of
admission states is derived by both and compared."""

from __future__ import annotations

import itertools
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters.run_state import (  # noqa: E402
    ADMISSION_AXES, OBSERVATION_STATES, RESULT_STATES, RUN_AXIS_STATES, SESSION_STATES, derive_task_state,
)

CONTRACT = json.loads((ROOT / "09_templates/data_contracts/researchos-interaction-semantics-v1.json")
                      .read_text(encoding="utf-8"))["state_axes"]
ADMISSIONS = [
    {},
    {"decision_state": "proposed"},
    {"decision_state": "rejected"},
    {"decision_state": "deferred"},
    {"decision_state": "accepted", "mutation_state": "applied", "validation_state": "passed"},
    {"decision_state": "revised", "mutation_state": "rolled_back"},
    {"decision_state": "proposed", "mutation_state": "staged"},
    {"decision_state": "accepted", "mutation_state": "staged", "validation_state": "passed"},
]
JS = """
const fs = require("node:fs"); const vm = require("node:vm");
const window = {}; const context = vm.createContext({ window });
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), context);
const contract = window.ResearchOSInteractionContract;
const cases = JSON.parse(fs.readFileSync(0, "utf8"));
process.stdout.write(JSON.stringify(cases.map((c) => {
  const p = contract.deriveTaskPresentation(c);
  return { state: p.state, primary_action: p.primaryAction, allowed_actions: Array.from(p.allowedActions),
           retry_allowed: p.retryAllowed, errors: Array.from(p.errors) };
})));
"""


class RunAxesParityTest(unittest.TestCase):
    def test_owner_enumerations_are_the_contracts(self) -> None:
        self.assertEqual((list(SESSION_STATES), list(RUN_AXIS_STATES), list(OBSERVATION_STATES), list(RESULT_STATES)),
                         (CONTRACT["session"], CONTRACT["run"], CONTRACT["observation"], CONTRACT["result"]))
        self.assertEqual({k: list(v) for k, v in ADMISSION_AXES.items()},
                         {k: CONTRACT["admission"][k] for k in ADMISSION_AXES})

    def test_python_owner_and_desk_copy_derive_the_same_state(self) -> None:
        self.assertTrue(shutil.which("node"), "the Desk copy exists, so node is required to check it")
        axes = [CONTRACT["session"], CONTRACT["run"], CONTRACT["observation"], CONTRACT["result"], ("none", "unknown")]
        cases = [{"session": s, "run": r, "observation": o, "result": res, "side_effects": fx, "admission": adm}
                 for (s, r, o, res, fx), adm in itertools.product(itertools.product(*axes), ADMISSIONS)]
        # The Desk names the side-effects field in camelCase; the owner and ros use side_effects.
        desk_cases = [{**{k: v for k, v in case.items() if k != "side_effects"}, "sideEffects": case["side_effects"]}
                      for case in cases]
        out = subprocess.run(["node", "-e", JS, str(ROOT / "dashboard/src/core/surface-contract.js")],
                             input=json.dumps(desk_cases), capture_output=True, text=True, check=True)
        desk = json.loads(out.stdout)
        self.assertEqual(len(desk), len(cases))
        mismatches = [(case, mine, theirs) for case, theirs in zip(cases, desk)
                      if (mine := derive_task_state(case)) != theirs]
        self.assertEqual(mismatches[:3], [], f"{len(mismatches)} of {len(cases)} combinations disagree")

    def test_legal_combinations_obey_the_canon_sentences(self) -> None:
        # run completed does not end the session; a writeback result is not admission.
        done = derive_task_state({"session": "open", "run": "completed", "observation": "fresh", "result": "writeback",
                                  "admission": {"decision_state": "proposed"}})
        self.assertEqual((done["state"], done["primary_action"]), ("result_ready", "open_review"))
        # unknown or expired observation: check, never resubmit.
        for observation in ("delivery_unknown", "lease_expired", "reconcile_failed"):
            view = derive_task_state({"session": "open", "run": "running", "observation": observation})
            self.assertFalse(view["retry_allowed"])
            self.assertNotIn("retry_same_request", view["allowed_actions"])
        # a session that ended while its run was still going keeps tracking it.
        self.assertEqual(derive_task_state({"session": "ended", "run": "running", "observation": "fresh"})["state"],
                         "ended_with_run_tracking")
        self.assertEqual(derive_task_state({"session": "none", "run": "running"})["state"], "invalid")


if __name__ == "__main__":
    unittest.main()
