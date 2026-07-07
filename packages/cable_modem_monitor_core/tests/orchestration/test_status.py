"""Tests for connection-status derivation.

``derive_connection_status`` maps a successful collection to a
ConnectionStatus. Channel-bearing DOCSIS modems are ONLINE when any
channel is present; channel-less devices (fiber ONT/gateways such as
the Nokia BGW320-505) are ONLINE when ``system_info`` reports an
operational link and NO_SIGNAL otherwise.

See RUNTIME_POLLING_SPEC.md Status Derivation and UC-07.
"""

from __future__ import annotations

from typing import Any

from solentlabs.cable_modem_monitor_core.orchestration.signals import (
    ConnectionStatus,
    DocsisStatus,
)
from solentlabs.cable_modem_monitor_core.orchestration.status import (
    derive_connection_status,
)


class TestDeriveConnectionStatus:
    """Channel presence and channel-less link health map to ConnectionStatus."""

    def test_downstream_channels_online(self) -> None:
        data = {"downstream": [{"channel_id": "1"}], "upstream": [], "system_info": {}}
        assert derive_connection_status(data) == ConnectionStatus.ONLINE

    def test_upstream_only_channels_online(self) -> None:
        data = {"downstream": [], "upstream": [{"channel_id": "1"}], "system_info": {}}
        assert derive_connection_status(data) == ConnectionStatus.ONLINE

    def test_channelless_operational_string_is_online(self) -> None:
        """Fiber gateway: no channels but an operational link string -> ONLINE."""
        data = {"downstream": [], "upstream": [], "system_info": {"docsis_status": "Operational"}}
        assert derive_connection_status(data) == ConnectionStatus.ONLINE

    def test_channelless_operational_enum_is_online(self) -> None:
        """The StrEnum member compares equal to the canonical string."""
        data = {"downstream": [], "upstream": [], "system_info": {"docsis_status": DocsisStatus.OPERATIONAL}}
        assert derive_connection_status(data) == ConnectionStatus.ONLINE

    def test_channelless_non_operational_is_no_signal(self) -> None:
        data = {"downstream": [], "upstream": [], "system_info": {"docsis_status": "Down"}}
        assert derive_connection_status(data) == ConnectionStatus.NO_SIGNAL

    def test_channelless_other_system_info_is_no_signal(self) -> None:
        """system_info without docsis_status is not enough to be ONLINE."""
        data = {"downstream": [], "upstream": [], "system_info": {"software_version": "6.34.7"}}
        assert derive_connection_status(data) == ConnectionStatus.NO_SIGNAL

    def test_channelless_empty_system_info_is_no_signal(self) -> None:
        data: dict[str, Any] = {"downstream": [], "upstream": [], "system_info": {}}
        assert derive_connection_status(data) == ConnectionStatus.NO_SIGNAL

    def test_channels_present_beats_missing_status(self) -> None:
        """Regression: channel presence wins even without docsis_status."""
        data = {"downstream": [{"channel_id": "1"}], "upstream": [{"channel_id": "2"}], "system_info": {}}
        assert derive_connection_status(data) == ConnectionStatus.ONLINE

    def test_missing_keys_default_to_no_signal(self) -> None:
        """Absent downstream/upstream/system_info keys don't crash."""
        assert derive_connection_status({}) == ConnectionStatus.NO_SIGNAL
