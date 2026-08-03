"""Tests for ``orchestration/factory.py`` entry points.

Covers ``apply_credential_encoding`` and ``create_orchestrator``'s
HealthMonitor wiring.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from solentlabs.cable_modem_monitor_core.models.modem_config.auth import (
    FormNonceAuth,
    NoneAuth,
)
from solentlabs.cable_modem_monitor_core.orchestration.factory import (
    apply_credential_encoding,
    create_orchestrator,
)

# ---------------------------------------------------------------------------
# apply_credential_encoding
# ---------------------------------------------------------------------------


class TestApplyCredentialEncoding:
    """``apply_credential_encoding`` injects detected encoding into form_nonce config."""

    def test_non_form_nonce_is_no_op(self) -> None:
        """Non-form_nonce auth passes through untouched."""
        config = MagicMock()
        config.auth = NoneAuth(strategy="none")
        # Should not raise; should leave config.auth unchanged.
        apply_credential_encoding(config, credential_encoding="b64_packed", credential_field="x")
        assert isinstance(config.auth, NoneAuth)

    def test_form_nonce_plain_sets_encoding_only(self) -> None:
        """Plain encoding sets only ``credential_encoding``."""
        auth = FormNonceAuth(strategy="form_nonce", action="/login", nonce_field="ar_nonce")
        config = MagicMock()
        config.auth = auth
        apply_credential_encoding(config, credential_encoding="plain")
        assert auth.credential_encoding == "plain"
        # credential_field stays at its default.
        assert auth.credential_field == ""

    def test_form_nonce_b64_packed_sets_both_fields(self) -> None:
        """b64_packed encoding sets both ``credential_encoding`` and ``credential_field``."""
        auth = FormNonceAuth(strategy="form_nonce", action="/login", nonce_field="ar_nonce")
        config = MagicMock()
        config.auth = auth
        apply_credential_encoding(
            config,
            credential_encoding="b64_packed",
            credential_field="arguments",
        )
        assert auth.credential_encoding == "b64_packed"
        assert auth.credential_field == "arguments"


# ---------------------------------------------------------------------------
# create_orchestrator HealthMonitor wiring
# ---------------------------------------------------------------------------


def _none_auth_modem_config() -> Any:
    """Build a minimal ModemConfig with NoneAuth for factory tests.

    Uses ``model_validate`` so all defaults are applied — same as
    production loading from modem.yaml.
    """
    from solentlabs.cable_modem_monitor_core.models.modem_config import ModemConfig

    return ModemConfig.model_validate(
        {
            "manufacturer": "Solent Labs",
            "model": "T100",
            "transport": "http",
            "default_host": "192.168.100.1",
            "status": "unsupported",
            "auth": {"strategy": "none"},
        }
    )


class TestCreateOrchestratorHealthMonitor:
    """``create_orchestrator`` wires HealthMonitor conditionally on probe flags."""

    def test_health_monitor_created_when_icmp_supported(self) -> None:
        """``supports_icmp=True`` triggers HealthMonitor instantiation."""
        orchestrator, health_monitor, identity = create_orchestrator(
            modem_config=_none_auth_modem_config(),
            parser_config=None,
            post_processor=None,
            base_url="http://192.168.100.1",
            supports_icmp=True,
            http_probe=False,
        )
        assert orchestrator is not None
        assert health_monitor is not None
        assert identity.model == "T100"

    def test_health_monitor_created_when_http_probe_enabled(self) -> None:
        """``http_probe=True`` alone (without ICMP) also triggers instantiation."""
        _, health_monitor, _ = create_orchestrator(
            modem_config=_none_auth_modem_config(),
            parser_config=None,
            post_processor=None,
            base_url="http://192.168.100.1",
            supports_icmp=False,
            http_probe=True,
        )
        assert health_monitor is not None

    def test_health_monitor_omitted_when_no_probes(self) -> None:
        """Neither probe enabled → ``health_monitor`` is None.

        Matches the path a modem with no health surface uses — the
        orchestrator runs without a health coordinator.
        """
        orchestrator, health_monitor, _ = create_orchestrator(
            modem_config=_none_auth_modem_config(),
            parser_config=None,
            post_processor=None,
            base_url="http://192.168.100.1",
            supports_icmp=False,
            http_probe=False,
        )
        assert orchestrator is not None
        assert health_monitor is None
