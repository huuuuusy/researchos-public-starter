from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_server.http_json import RequestBodyError, read_json_object  # noqa: E402


class HttpJsonTest(unittest.TestCase):
    def parse(self, raw: bytes, **kwargs: object) -> dict[str, object]:
        return read_json_object(
            {"Content-Length": str(len(raw))},
            io.BytesIO(raw),
            maximum=int(kwargs.pop("maximum", 100)),
            **kwargs,
        )

    def test_reads_json_object(self) -> None:
        self.assertEqual({"ok": True}, self.parse(b'{"ok": true}'))

    def test_rejects_invalid_length_encoding_and_root_shape(self) -> None:
        with self.assertRaises(RequestBodyError):
            read_json_object({"Content-Length": "abc"}, io.BytesIO(), maximum=10)
        with self.assertRaises(RequestBodyError):
            self.parse(b"\xff")
        with self.assertRaises(RequestBodyError):
            self.parse(b"[]")
        with self.assertRaises(RequestBodyError):
            self.parse(b'{"too": "large"}', maximum=2)

    def test_empty_body_requires_explicit_opt_in(self) -> None:
        with self.assertRaises(RequestBodyError):
            self.parse(b"")
        self.assertEqual({}, self.parse(b"", allow_empty=True))


if __name__ == "__main__":
    unittest.main()
