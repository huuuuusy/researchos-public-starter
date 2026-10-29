# ResearchOS maintenance header.
# 中文：本地 dashboard HTTP 状态修改接口的 Host、Origin、JSON 与会话令牌校验 owner。
# English: Host, Origin, JSON, and session-token validation owner for local dashboard mutations.

"""Same-origin session protection for the local ResearchOS HTTP server."""

from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass
from urllib.parse import urlparse


LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
# Reads that start local work (a model-catalog refresh, git, CLI probes) or read local files. Only the
# dashboard page itself may make them: another site could otherwise trigger them through an <img> or a link.
LOCAL_WORK_READ_PATHS = frozenset({"/model-catalog", "/evolution-plan", "/provider-status", "/codex-runner",
                                   "/source-tree", "/source-info"})


def host_name(value: str) -> str:
    raw = str(value or "").strip().lower()

    def valid_port(port: str) -> bool:
        return port.isdigit() and 1 <= int(port) <= 65535

    if raw.startswith("["):
        closing = raw.find("]")
        if closing < 0:
            return ""
        host = raw[1:closing]
        suffix = raw[closing + 1 :]
        if suffix and (not suffix.startswith(":") or not valid_port(suffix[1:])):
            return ""
        return host
    if raw.count(":") > 1:
        return ""
    host, separator, port = raw.partition(":")
    if separator and not valid_port(port):
        return ""
    return host


@dataclass(frozen=True)
class LocalRequestSecurity:
    token: str

    @classmethod
    def create(cls) -> "LocalRequestSecurity":
        return cls(token=secrets.token_urlsafe(32))

    def session_config(self) -> dict[str, str]:
        return {
            "request_header": "X-ResearchOS-Session",
            "request_token": self.token,
        }

    def read_error(self, headers: object) -> tuple[int, str] | None:
        """Reject DNS-rebinding and forged-Host reads before any route is served."""
        get = getattr(headers, "get", None)
        if not callable(get):
            return (403, "Invalid request headers")
        if host_name(str(get("Host", ""))) not in LOOPBACK_HOSTS:
            return (403, "Untrusted Host header")
        return None

    def enforce_read(self, handler: object) -> bool:
        """Send the rejection on an HTTP handler and report whether routing may continue."""
        headers = getattr(handler, "headers", None)
        error = self.read_error(headers)
        if not error and urlparse(str(getattr(handler, "path", ""))).path in LOCAL_WORK_READ_PATHS:
            error = self.cross_site_error(headers)
        if error:
            getattr(handler, "send_error")(*error)
            return False
        return True

    def cross_site_error(self, headers: object) -> tuple[int, str] | None:
        """A browser marks where a request comes from in Sec-Fetch-Site; only the page itself or a typed URL passes."""
        site = str(getattr(headers, "get")("Sec-Fetch-Site", "") or "").strip().lower()
        return (403, "Cross-site request rejected") if site and site not in {"same-origin", "none"} else None

    def mutation_error(
        self,
        headers: object,
        port: int,
        allowed_content_types: tuple[str, ...] = ("application/json",),
    ) -> tuple[int, str] | None:
        read_error = self.read_error(headers)
        if read_error:
            return read_error
        get = getattr(headers, "get")

        origin = str(get("Origin", "") or "").strip()
        if origin:
            try:
                parsed = urlparse(origin)
                origin_port = parsed.port or (443 if parsed.scheme == "https" else 80)
            except ValueError:
                return (403, "Cross-origin mutation rejected")
            if (
                parsed.scheme != "http"
                or (parsed.hostname or "").lower() not in LOOPBACK_HOSTS
                or origin_port != port
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path not in {"", "/"}
                or bool(parsed.params or parsed.query or parsed.fragment)
            ):
                return (403, "Cross-origin mutation rejected")

        content_type = str(get("Content-Type", "") or "").split(";", 1)[0].strip().lower()
        if "*/*" not in allowed_content_types and content_type not in allowed_content_types:
            return (415, "Mutation request content type is not allowed")

        supplied = str(get("X-ResearchOS-Session", "") or "")
        if not supplied or not hmac.compare_digest(supplied, self.token):
            return (403, "Invalid ResearchOS session token")
        return None
