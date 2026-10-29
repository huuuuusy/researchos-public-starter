from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_server.request_security import LocalRequestSecurity  # noqa: E402


class LocalRequestSecurityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.security = LocalRequestSecurity(token="fixture-token")
        self.headers = {
            "Host": "127.0.0.1:8878",
            "Origin": "http://127.0.0.1:8878",
            "Content-Type": "application/json; charset=utf-8",
            "X-ResearchOS-Session": "fixture-token",
        }

    def test_same_origin_json_request_with_session_token_is_allowed(self) -> None:
        self.assertIsNone(self.security.mutation_error(self.headers, 8878))

    def test_binary_body_is_allowed_only_when_the_route_opts_in(self) -> None:
        binary = {**self.headers, "Content-Type": "application/octet-stream"}
        self.assertIsNone(
            self.security.mutation_error(
                binary,
                8878,
                ("*/*",),  # what the upload route declares in serve_dashboard.POST_ROUTES
            )
        )
        self.assertEqual(
            (415, "Mutation request content type is not allowed"),
            self.security.mutation_error(binary, 8878),
        )
        notebook = {**self.headers, "Content-Type": "application/x-ipynb+json"}
        self.assertIsNone(
            self.security.mutation_error(
                notebook,
                8878,
                ("*/*",),  # what the upload route declares in serve_dashboard.POST_ROUTES
            )
        )

    def test_reads_that_start_local_work_refuse_other_sites(self) -> None:
        class Handler:
            def __init__(self, path: str, headers: dict) -> None:
                self.path, self.headers, self.errors = path, headers, []

            def send_error(self, *error) -> None:
                self.errors.append(error)

        host = {"Host": "127.0.0.1:8878"}
        for site in ("cross-site", "same-site"):
            handler = Handler("/model-catalog?refresh=1", {**host, "Sec-Fetch-Site": site})
            self.assertFalse(self.security.enforce_read(handler), site)
            self.assertEqual([(403, "Cross-site request rejected")], handler.errors)
        for site in ("same-origin", "none", ""):
            self.assertTrue(self.security.enforce_read(Handler("/evolution-plan", {**host, "Sec-Fetch-Site": site})))
        # A page or asset opened from a link elsewhere still loads; it starts no local work.
        self.assertTrue(self.security.enforce_read(Handler("/index.html", {**host, "Sec-Fetch-Site": "cross-site"})))

    def test_cross_origin_request_is_rejected(self) -> None:
        headers = {**self.headers, "Origin": "https://example.com"}
        self.assertEqual((403, "Cross-origin mutation rejected"), self.security.mutation_error(headers, 8878))
        for malformed in (
            "http://localhost:bad",
            "http://localhost:99999",
            "http://user@localhost:8878",
            "http://localhost:8878/unexpected",
        ):
            with self.subTest(origin=malformed):
                headers = {**self.headers, "Origin": malformed}
                self.assertEqual((403, "Cross-origin mutation rejected"), self.security.mutation_error(headers, 8878))

    def test_missing_token_and_non_json_content_are_rejected(self) -> None:
        missing_token = {key: value for key, value in self.headers.items() if key != "X-ResearchOS-Session"}
        self.assertEqual((403, "Invalid ResearchOS session token"), self.security.mutation_error(missing_token, 8878))
        text_request = {**self.headers, "Content-Type": "text/plain"}
        self.assertEqual((415, "Mutation request content type is not allowed"), self.security.mutation_error(text_request, 8878))

    def test_untrusted_host_is_rejected(self) -> None:
        headers = {**self.headers, "Host": "attacker.example"}
        self.assertEqual((403, "Untrusted Host header"), self.security.mutation_error(headers, 8878))

    def test_read_requests_require_a_loopback_host(self) -> None:
        self.assertIsNone(self.security.read_error({"Host": "localhost:8878"}))
        self.assertIsNone(self.security.read_error({"Host": "[::1]:8878"}))
        self.assertEqual((403, "Untrusted Host header"), self.security.read_error({"Host": "localhost.attacker.example"}))
        for malformed in ("[::1]attacker", "[::1]:bad", "localhost:bad", "localhost:"):
            with self.subTest(host=malformed):
                self.assertEqual((403, "Untrusted Host header"), self.security.read_error({"Host": malformed}))
        self.assertEqual((403, "Invalid request headers"), self.security.read_error(object()))


if __name__ == "__main__":
    unittest.main()
