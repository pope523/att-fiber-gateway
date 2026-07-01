"""Server-nonce + MD5 form login (AT&T ARRIS/Nokia gateways).

Login flow, matching the gateway's ``login.js`` (verified against the
BGW320-505 login page and the hardware-confirmed ``attrouter`` /
``att-fiber-gateway-info`` projects)::

    hashpassword = md5(access_code + nonce)

Steps:
    1. GET the login page and read the hidden ``nonce`` value.
    2. POST the nonce, an asterisk-masked password, the MD5 hash, and
       the submit field back to the same page.
    3. Success is a redirect that sets the ``SessionID`` cookie.

MD5 is mandated by the device protocol (not a security choice), so
``usedforsecurity=False`` is set on the hash.

See MODEM_YAML_SPEC.md ``form_md5_nonce`` strategy.
"""

from __future__ import annotations

import hashlib
import logging

import requests
from bs4 import BeautifulSoup, Tag

from ..models.modem_config.auth import FormMd5NonceAuth
from .base import AuthResult, BaseAuthManager

_logger = logging.getLogger(__name__)


class FormMd5NonceAuthManager(BaseAuthManager):
    """Form POST with a server-provided nonce and MD5-hashed credential."""

    def __init__(self, config: FormMd5NonceAuth) -> None:
        self._config = config

    def authenticate(
        self,
        session: requests.Session,
        base_url: str,
        username: str,
        password: str,
        *,
        timeout: int = 10,
        log_level: int = logging.DEBUG,
    ) -> AuthResult:
        """Fetch the login nonce, POST the hashed credential, verify session.

        Args:
            session: Session to configure with auth state.
            base_url: Modem base URL.
            username: Unused — the gateway authenticates on the access
                code alone.
            password: The device access code.
            timeout: Per-request timeout in seconds.
            log_level: Log level for non-error messages.

        Returns:
            AuthResult with the login response.
        """
        config = self._config
        login_url = f"{base_url}{config.action}"

        # Step 1: GET the login page and extract the hidden nonce.
        try:
            page = session.get(login_url, timeout=timeout)
        except requests.RequestException as e:
            if isinstance(e, requests.ConnectionError | requests.Timeout):
                raise
            return AuthResult(success=False, error=f"Login page fetch failed: {type(e).__name__}: {e}")

        nonce = _extract_nonce(page.text, config.nonce_field)
        if not nonce:
            return AuthResult(
                success=False,
                error=f"Login nonce field '{config.nonce_field}' not found on {config.action}",
                response=page,
            )

        # Step 2: Compute hashpassword = md5(access_code + nonce).
        hash_pw = hashlib.md5(f"{password}{nonce}".encode(), usedforsecurity=False).hexdigest()
        masked = "*" * len(password) if config.mask_password else password
        form_data = {
            config.nonce_field: nonce,
            config.password_field: masked,
            config.hash_field: hash_pw,
            config.submit_field: config.submit_value,
        }

        # Step 3: POST credentials. Success is a redirect + session cookie;
        # a 200 that re-serves the login page (password input present) is
        # a failure.
        try:
            response = session.post(
                login_url,
                data=form_data,
                allow_redirects=False,
                timeout=timeout,
            )
        except requests.RequestException as e:
            if isinstance(e, requests.ConnectionError | requests.Timeout):
                raise
            return AuthResult(success=False, error=f"Login POST failed: {type(e).__name__}: {e}")

        if _login_succeeded(response, session, config.cookie_name):
            _logger.log(log_level, "MD5-nonce login succeeded: status=%d", response.status_code)
            # Do not advertise response reuse — the login response is a
            # redirect, not a parser-consumable data page.
            return AuthResult(success=True)

        return AuthResult(
            success=False,
            error=f"Login rejected (status {response.status_code}) — check the device access code",
            response=response,
        )


def _extract_nonce(html: str, nonce_field: str) -> str:
    """Return the hidden ``nonce`` input value from the login page, or ``\"\"``."""
    if not html:
        return ""
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        _logger.debug("Failed to parse login page HTML", exc_info=True)
        return ""
    field = soup.find("input", attrs={"name": nonce_field})
    if isinstance(field, Tag):
        value = field.get("value", "")
        if isinstance(value, str):
            return value.strip()
    return ""


def _login_succeeded(
    response: requests.Response,
    session: requests.Session,
    cookie_name: str,
) -> bool:
    """Heuristic success check: redirect and/or session cookie, not a re-served login page."""
    if cookie_name and cookie_name in session.cookies:
        return True
    if response.is_redirect or response.status_code in (301, 302, 303):
        return True
    # A 200 that still contains a password input means the login page was
    # re-served — authentication failed.
    if response.status_code == 200:
        return 'type="password"' not in response.text.lower() and 'id="password"' not in response.text.lower()
    return False


def create_manager(config: FormMd5NonceAuth) -> FormMd5NonceAuthManager:
    """Entry point for dynamic auth factory dispatch."""
    return FormMd5NonceAuthManager(config)
