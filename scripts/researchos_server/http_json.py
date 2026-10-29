# ResearchOS maintenance header.
# 中文：本地 dashboard HTTP JSON 请求体的长度、编码和对象形状校验 owner。
# English: Length, encoding, and object-shape validation owner for local dashboard JSON request bodies.

"""Strict JSON-object request parsing for local HTTP handlers."""

from __future__ import annotations

import json
from typing import BinaryIO, Mapping


class RequestBodyError(ValueError):
    """Raised when a local HTTP JSON body is malformed or outside its limit."""


def read_json_object(
    headers: Mapping[str, str],
    stream: BinaryIO,
    *,
    maximum: int,
    label: str = "request",
    allow_empty: bool = False,
) -> dict[str, object]:
    raw_length = str(headers.get("Content-Length", "0") or "0").strip()
    try:
        length = int(raw_length)
    except ValueError as exc:
        raise RequestBodyError(f"Invalid {label} Content-Length") from exc
    if length < 0 or length > maximum or (length == 0 and not allow_empty):
        raise RequestBodyError(f"Invalid {label} length")
    if length == 0:
        return {}
    try:
        payload = json.loads(stream.read(length).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RequestBodyError(f"Invalid {label} JSON") from exc
    if not isinstance(payload, dict):
        raise RequestBodyError(f"Invalid {label} JSON object")
    return payload
