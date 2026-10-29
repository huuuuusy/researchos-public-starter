from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_kernel.result_contract import build_error_envelope  # noqa: E402


class ProviderFailureContractTest(unittest.TestCase):
    def test_preflight_failures_prove_zero_side_effects(self) -> None:
        expected = {
            "unknown_provider": "choose_provider",
            "provider_call_not_implemented": "choose_provider",
            "provider_cancel_unsupported": "inspect",
        }
        for error_type, recovery in expected.items():
            with self.subTest(error_type=error_type):
                envelope = build_error_envelope(error_type)
                self.assertEqual("none", envelope["side_effects"])
                self.assertEqual(recovery, envelope["recovery_action"])
                self.assertEqual("server_pre_dispatch", envelope["last_safe_point"])

    def test_cancel_unsupported_cannot_be_downgraded_to_safe_retry(self) -> None:
        envelope = build_error_envelope("provider_cancel_unsupported", recovery_action="retry_same", retryable=True)
        self.assertEqual("inspect", envelope["recovery_action"])
        self.assertFalse(envelope["retryable"])

    def test_error_envelope_contains_no_raw_provider_or_credential_fields(self) -> None:
        envelope = build_error_envelope("provider_call_not_implemented", run={"id": "run-provider"})
        serialized = json.dumps(envelope)
        for forbidden in ("fixture-secret", "sk-private", "https://", "provider_body", "endpoint_url", "fallback"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
