"""Tests for FormMd5NonceAuthManager — AT&T ARRIS/Nokia server-nonce + MD5 login.

Mirrors the gateway's ``login.js`` flow used by the Nokia BGW320-505:
GET the login page, read the hidden ``nonce``, then POST the nonce, an
asterisk-masked password, ``md5(access_code + nonce)``, and the submit
field. Success is a redirect, a session cookie, or a 200 that is not the
re-served login page.

Follows the repo convention of driving the manager with a
``MagicMock(spec=requests.Session)`` (see ``tests/orchestration/test_actions.py``)
so the exact POST body — field names, masking, and hash — can be asserted.
"""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock

import pytest
import requests
import requests.cookies
from solentlabs.cable_modem_monitor_core.auth.form_md5_nonce import (
    FormMd5NonceAuthManager,
    _extract_nonce,
    _login_succeeded,
)
from solentlabs.cable_modem_monitor_core.models.modem_config.auth import (
    FormMd5NonceAuth,
)

_NONCE = "1a2b3c4d5e"
# 12-char device access code — fake, matches the BGW320-505 code length.
_ACCESS_CODE = "ABCD1234WXYZ"

_LOGIN_PAGE = (
    "<html><body>"
    '<form method="post" action="/cgi-bin/login.ha">'
    f'<input type="hidden" name="nonce" value="{_NONCE}" />'
    '<input type="password" name="password" id="password" maxlength="12" />'
    '<input type="hidden" name="hashpassword" value="" />'
    '<input type="submit" name="Continue" value="Continue" />'
    "</form></body></html>"
)
# Post-login landing page — no password input present.
_LANDING_PAGE = "<html><body><h1>System Information</h1></body></html>"


def _response(status: int, text: str = "") -> MagicMock:
    """Build a mock ``requests.Response`` with the fields the manager reads."""
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status
    resp.text = text
    resp.is_redirect = status in (301, 302, 303)
    return resp


def _session(cookies: dict[str, str] | None = None) -> MagicMock:
    """Build a mock session with a real cookie jar for ``name in cookies`` checks."""
    session = MagicMock(spec=requests.Session)
    jar = requests.cookies.RequestsCookieJar()
    for name, value in (cookies or {}).items():
        jar.set(name, value)
    session.cookies = jar
    return session


def _manager(**overrides: object) -> FormMd5NonceAuthManager:
    config = FormMd5NonceAuth(strategy="form_md5_nonce", **overrides)  # type: ignore[arg-type]  # overrides are validated field values
    return FormMd5NonceAuthManager(config)


class TestFormMd5NonceAuthManager:
    """Full login flow: nonce read, hash computed, correct POST fields."""

    def test_posts_correct_fields_and_hash(self) -> None:
        """POST carries nonce, masked password, md5(code+nonce), and submit."""
        session = _session(cookies={"SessionID": "sess"})
        session.get.return_value = _response(200, _LOGIN_PAGE)
        session.post.return_value = _response(200, _LANDING_PAGE)

        result = _manager().authenticate(session, "http://gw", "unused", _ACCESS_CODE)

        assert result.success is True
        data = session.post.call_args.kwargs["data"]
        assert data["nonce"] == _NONCE
        assert data["password"] == "*" * len(_ACCESS_CODE)
        assert data["hashpassword"] == hashlib.md5(f"{_ACCESS_CODE}{_NONCE}".encode()).hexdigest()
        assert data["Continue"] == "Continue"
        # The login POST must not follow redirects — a redirect is success.
        assert session.post.call_args.kwargs["allow_redirects"] is False

    def test_success_via_session_cookie(self) -> None:
        """A SessionID cookie after the POST means success, even if the body looks like the login page."""
        session = _session(cookies={"SessionID": "sess"})
        session.get.return_value = _response(200, _LOGIN_PAGE)
        session.post.return_value = _response(200, _LOGIN_PAGE)

        assert _manager().authenticate(session, "http://gw", "u", _ACCESS_CODE).success is True

    def test_success_via_redirect(self) -> None:
        """A 302 with no cookie is treated as success."""
        session = _session()
        session.get.return_value = _response(200, _LOGIN_PAGE)
        session.post.return_value = _response(302)

        assert _manager().authenticate(session, "http://gw", "u", _ACCESS_CODE).success is True

    def test_success_via_200_without_password(self) -> None:
        """A 200 landing page without a password input is success."""
        session = _session()
        session.get.return_value = _response(200, _LOGIN_PAGE)
        session.post.return_value = _response(200, _LANDING_PAGE)

        assert _manager().authenticate(session, "http://gw", "u", _ACCESS_CODE).success is True

    def test_failure_when_login_page_reserved(self) -> None:
        """A 200 that re-serves the password form means the access code was wrong."""
        session = _session()
        session.get.return_value = _response(200, _LOGIN_PAGE)
        session.post.return_value = _response(200, _LOGIN_PAGE)

        result = _manager().authenticate(session, "http://gw", "u", _ACCESS_CODE)
        assert result.success is False
        assert "check the device access code" in result.error

    def test_failure_when_nonce_missing(self) -> None:
        """A login page without the nonce field fails before POSTing."""
        session = _session()
        session.get.return_value = _response(200, "<html><body>no nonce here</body></html>")

        result = _manager().authenticate(session, "http://gw", "u", _ACCESS_CODE)
        assert result.success is False
        assert "nonce" in result.error.lower()
        session.post.assert_not_called()

    def test_cookie_prime_two_step_login(self) -> None:
        """BGW handshake: 1st GET has no nonce (cookie prime); retry GET yields it."""
        session = _session()
        session.get.side_effect = [
            _response(200, "<html><body>Access Code Required. Cookies must be enabled.</body></html>"),
            _response(200, _LOGIN_PAGE),
        ]
        session.post.return_value = _response(302)  # redirect => success

        result = _manager().authenticate(session, "http://gw", "u", _ACCESS_CODE)

        assert result.success is True
        assert session.get.call_count == 2
        assert session.post.call_args.kwargs["data"]["nonce"] == _NONCE

    def test_nonce_absent_after_retry_fails(self) -> None:
        """If neither the first nor the retry GET yields a nonce, auth fails without POSTing."""
        session = _session()
        session.get.side_effect = [
            _response(200, "<html><body>no nonce</body></html>"),
            _response(200, "<html><body>still no nonce</body></html>"),
        ]

        result = _manager().authenticate(session, "http://gw", "u", _ACCESS_CODE)

        assert result.success is False
        assert "nonce" in result.error.lower()
        assert session.get.call_count == 2
        session.post.assert_not_called()

    def test_unmasked_password_when_mask_disabled(self) -> None:
        """mask_password=False sends the raw access code as the password field."""
        session = _session(cookies={"SessionID": "sess"})
        session.get.return_value = _response(200, _LOGIN_PAGE)
        session.post.return_value = _response(200, _LANDING_PAGE)

        _manager(mask_password=False).authenticate(session, "http://gw", "u", _ACCESS_CODE)
        assert session.post.call_args.kwargs["data"]["password"] == _ACCESS_CODE

    def test_custom_field_names(self) -> None:
        """Configured field names drive the POST body keys and the hash uses that nonce."""
        session = _session(cookies={"SID": "x"})
        session.get.return_value = _response(200, '<html><input type="hidden" name="tok" value="ZZZ"/></html>')
        session.post.return_value = _response(200, _LANDING_PAGE)
        manager = _manager(
            nonce_field="tok",
            password_field="pw",
            hash_field="digest",
            submit_field="Go",
            submit_value="Go",
            cookie_name="SID",
        )

        manager.authenticate(session, "http://gw", "u", _ACCESS_CODE)

        data = session.post.call_args.kwargs["data"]
        assert set(data) == {"tok", "pw", "digest", "Go"}
        assert data["tok"] == "ZZZ"
        assert data["digest"] == hashlib.md5(f"{_ACCESS_CODE}ZZZ".encode()).hexdigest()

    def test_login_page_request_exception_returns_result(self) -> None:
        """A non-connectivity RequestException on the GET returns a failed AuthResult."""
        session = _session()
        session.get.side_effect = requests.TooManyRedirects("loop")

        result = _manager().authenticate(session, "http://gw", "u", _ACCESS_CODE)
        assert result.success is False
        assert "Login page fetch failed" in result.error

    def test_login_post_request_exception_returns_result(self) -> None:
        """A non-connectivity RequestException on the POST returns a failed AuthResult."""
        session = _session()
        session.get.return_value = _response(200, _LOGIN_PAGE)
        session.post.side_effect = requests.TooManyRedirects("loop")

        result = _manager().authenticate(session, "http://gw", "u", _ACCESS_CODE)
        assert result.success is False
        assert "Login POST failed" in result.error

    def test_connection_error_propagates(self) -> None:
        """ConnectionError propagates so the collector can classify unreachable."""
        session = _session()
        session.get.side_effect = requests.ConnectionError("refused")

        with pytest.raises(requests.ConnectionError):
            _manager().authenticate(session, "http://gw", "u", _ACCESS_CODE)


class TestExtractNonce:
    """_extract_nonce reads the hidden nonce value from the login HTML."""

    def test_extracts_value(self) -> None:
        assert _extract_nonce(f'<input type="hidden" name="nonce" value="{_NONCE}" />', "nonce") == _NONCE

    def test_missing_returns_empty(self) -> None:
        assert _extract_nonce("<html></html>", "nonce") == ""

    def test_empty_html_returns_empty(self) -> None:
        assert _extract_nonce("", "nonce") == ""


class TestLoginSucceeded:
    """_login_succeeded heuristics: cookie, redirect, or non-login 200."""

    def test_cookie_present(self) -> None:
        assert _login_succeeded(_response(200, _LOGIN_PAGE), _session(cookies={"SessionID": "x"}), "SessionID") is True

    def test_redirect(self) -> None:
        assert _login_succeeded(_response(302), _session(), "SessionID") is True

    def test_200_without_password(self) -> None:
        assert _login_succeeded(_response(200, _LANDING_PAGE), _session(), "SessionID") is True

    def test_200_with_password_fails(self) -> None:
        assert _login_succeeded(_response(200, _LOGIN_PAGE), _session(), "SessionID") is False

    def test_other_status_fails(self) -> None:
        assert _login_succeeded(_response(403), _session(), "SessionID") is False
