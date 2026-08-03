"""Tests for loaders.diagnostics shared utilities."""

from __future__ import annotations

import requests
from solentlabs.cable_modem_monitor_core.loaders.diagnostics import describe_request


def _prepare(headers: dict[str, str]) -> requests.PreparedRequest:
    return requests.Request("GET", "http://192.168.0.1/x?_n=12345", headers=headers).prepare()


class TestDescribeRequest:
    """describe_request formats request shape; values of named headers are redacted."""

    def test_redacts_session_token_headers(self) -> None:
        req = _prepare(
            {
                "X-Requested-With": "XMLHttpRequest",
                "Cookie": "PHPSESSID=abc123",
                "csrfNonce": "deadbeef" * 4,
                "Authorization": "Bearer xyz",
            }
        )
        out = describe_request(req, headers=frozenset({"cookie", "csrfnonce", "authorization"}))
        assert "Cookie=<set, len=16>" in out
        assert "abc123" not in out
        assert "csrfNonce=<set, len=32>" in out
        assert "Authorization=<set, len=10>" in out
        assert "X-Requested-With=XMLHttpRequest" in out

    def test_includes_method_and_full_url_with_query(self) -> None:
        out = describe_request(_prepare({}), headers=frozenset({"cookie"}))
        assert out.startswith("GET http://192.168.0.1/x?_n=12345 [")

    def test_handles_none(self) -> None:
        assert describe_request(None, headers=frozenset({"cookie"})) == "(no PreparedRequest available)"

    def test_redacts_only_listed_headers(self) -> None:
        """Headers whose names are not passed in are emitted verbatim — value and all."""
        req = _prepare({"Authorization": "Bearer secret", "X-Foo": "bar"})
        out = describe_request(req, headers=frozenset({"cookie"}))
        assert "Authorization=Bearer secret" in out
        assert "X-Foo=bar" in out
