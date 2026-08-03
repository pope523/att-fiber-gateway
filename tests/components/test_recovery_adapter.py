"""Tests for the HA-side recovery cadence wiring.

Covers ``attach_recovery_cadence_listener`` in ``recovery_adapter.py`` —
the observer + dispatcher-listener pair that switches the data
coordinator's cadence while Core's recovery window is open.

The orchestrator is mocked — these tests verify HA-side wiring only.

See HA_ADAPTER_SPEC.md § Recovery Adapter.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.cable_modem_monitor.coordinator import (
    CableModemRuntimeData,
)
from custom_components.cable_modem_monitor.recovery_adapter import (
    _RECOVERY_POLL_INTERVAL,
    attach_recovery_cadence_listener,
    recovery_state_signal,
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _make_entry(
    runtime_data: CableModemRuntimeData,
    *,
    entry_id: str = "test_entry",
) -> MagicMock:
    """Build a minimal ConfigEntry double with the collaborators needed.

    ``entry.data`` carries the model name because the listener reads
    ``entry.data[CONF_MODEL]`` (not ``runtime_data``) — attach runs
    during startup before runtime_data is populated.
    """
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = {"model": "T100"}
    entry.runtime_data = runtime_data
    entry.async_on_unload = MagicMock()
    return entry


def _make_coordinator(interval: timedelta | None) -> MagicMock:
    """Build a DataUpdateCoordinator double with a settable update_interval."""
    coord = MagicMock()
    coord.update_interval = interval
    coord.async_request_refresh = AsyncMock()
    return coord


async def _flush(hass: HomeAssistant) -> None:
    """Yield so pending tasks scheduled via hass.async_create_task run."""
    await asyncio.sleep(0)
    await hass.async_block_till_done()


# ------------------------------------------------------------------
# recovery_state_signal
# ------------------------------------------------------------------


def test_signal_is_entry_scoped() -> None:
    """Two entries produce distinct dispatcher signals."""
    assert recovery_state_signal("abc") != recovery_state_signal("xyz")
    assert "abc" in recovery_state_signal("abc")


# ------------------------------------------------------------------
# attach_recovery_cadence_listener — observer + listener installation
# ------------------------------------------------------------------


async def test_attach_installs_observer_on_orchestrator(
    hass: HomeAssistant,
    mock_orchestrator: MagicMock,
    mock_runtime_data: CableModemRuntimeData,
) -> None:
    """attach() registers a recovery observer on Core."""
    entry = _make_entry(mock_runtime_data)
    coord = _make_coordinator(timedelta(minutes=10))

    attach_recovery_cadence_listener(hass, entry, mock_orchestrator, coord)

    mock_orchestrator.set_recovery_observer.assert_called_once()
    # The registered callback is a zero-arg callable.
    observer = mock_orchestrator.set_recovery_observer.call_args[0][0]
    assert callable(observer)


async def test_attach_registers_unsubscribe_on_unload(
    hass: HomeAssistant,
    mock_orchestrator: MagicMock,
    mock_runtime_data: CableModemRuntimeData,
) -> None:
    """attach() registers a teardown callback with entry.async_on_unload."""
    entry = _make_entry(mock_runtime_data)
    coord = _make_coordinator(timedelta(minutes=10))

    attach_recovery_cadence_listener(hass, entry, mock_orchestrator, coord)

    entry.async_on_unload.assert_called_once()


async def test_teardown_clears_observer_and_listener(
    hass: HomeAssistant,
    mock_orchestrator: MagicMock,
    mock_runtime_data: CableModemRuntimeData,
) -> None:
    """Teardown clears the Core observer and disconnects the listener."""
    entry = _make_entry(mock_runtime_data)
    coord = _make_coordinator(timedelta(minutes=10))

    attach_recovery_cadence_listener(hass, entry, mock_orchestrator, coord)

    teardown = entry.async_on_unload.call_args[0][0]
    mock_orchestrator.set_recovery_observer.reset_mock()

    teardown()

    # set_recovery_observer(None) clears the Core-side callback.
    mock_orchestrator.set_recovery_observer.assert_called_once_with(None)

    # After teardown, a signal fires but does nothing — update_interval
    # should not change.
    coord.update_interval = timedelta(minutes=10)
    async_dispatcher_send(hass, recovery_state_signal(entry.entry_id))
    await _flush(hass)
    assert coord.update_interval == timedelta(minutes=10)


# ------------------------------------------------------------------
# Cadence switching
# ------------------------------------------------------------------


async def test_cadence_switches_to_recovery_interval_on_true(
    hass: HomeAssistant,
    mock_orchestrator: MagicMock,
    mock_runtime_data: CableModemRuntimeData,
) -> None:
    """recovery_active → True drops update_interval to the recovery value."""
    normal = timedelta(minutes=10)
    entry = _make_entry(mock_runtime_data)
    coord = _make_coordinator(normal)

    attach_recovery_cadence_listener(hass, entry, mock_orchestrator, coord)

    mock_orchestrator.recovery_active = True
    async_dispatcher_send(hass, recovery_state_signal(entry.entry_id))
    await _flush(hass)

    assert coord.update_interval == _RECOVERY_POLL_INTERVAL


async def test_cadence_restores_normal_interval_on_false(
    hass: HomeAssistant,
    mock_orchestrator: MagicMock,
    mock_runtime_data: CableModemRuntimeData,
) -> None:
    """recovery_active → False restores the captured normal interval."""
    normal = timedelta(minutes=10)
    entry = _make_entry(mock_runtime_data)
    coord = _make_coordinator(normal)

    attach_recovery_cadence_listener(hass, entry, mock_orchestrator, coord)

    # Simulate the True → False sequence.
    mock_orchestrator.recovery_active = True
    async_dispatcher_send(hass, recovery_state_signal(entry.entry_id))
    await _flush(hass)
    assert coord.update_interval == _RECOVERY_POLL_INTERVAL

    mock_orchestrator.recovery_active = False
    async_dispatcher_send(hass, recovery_state_signal(entry.entry_id))
    await _flush(hass)

    assert coord.update_interval == normal


async def test_immediate_refresh_on_window_entry(
    hass: HomeAssistant,
    mock_orchestrator: MagicMock,
    mock_runtime_data: CableModemRuntimeData,
) -> None:
    """Entering a window kicks an immediate coordinator refresh."""
    entry = _make_entry(mock_runtime_data)
    coord = _make_coordinator(timedelta(minutes=10))

    attach_recovery_cadence_listener(hass, entry, mock_orchestrator, coord)

    mock_orchestrator.recovery_active = True
    async_dispatcher_send(hass, recovery_state_signal(entry.entry_id))
    await _flush(hass)

    coord.async_request_refresh.assert_awaited_once()


async def test_no_refresh_on_window_exit(
    hass: HomeAssistant,
    mock_orchestrator: MagicMock,
    mock_runtime_data: CableModemRuntimeData,
) -> None:
    """Exiting a window only restores cadence — no immediate refresh."""
    entry = _make_entry(mock_runtime_data)
    coord = _make_coordinator(timedelta(minutes=10))

    attach_recovery_cadence_listener(hass, entry, mock_orchestrator, coord)

    mock_orchestrator.recovery_active = False
    async_dispatcher_send(hass, recovery_state_signal(entry.entry_id))
    await _flush(hass)

    coord.async_request_refresh.assert_not_awaited()


# ------------------------------------------------------------------
# User opt-out — update_interval=None means polling is disabled
# ------------------------------------------------------------------


@pytest.mark.parametrize("recovery_active", [True, False])
async def test_disabled_polling_is_not_overridden(
    hass: HomeAssistant,
    mock_orchestrator: MagicMock,
    mock_runtime_data: CableModemRuntimeData,
    recovery_active: bool,
) -> None:
    """When the user has disabled polling, recovery transitions are no-ops."""
    entry = _make_entry(mock_runtime_data)
    coord = _make_coordinator(None)  # user-disabled polling

    attach_recovery_cadence_listener(hass, entry, mock_orchestrator, coord)

    mock_orchestrator.recovery_active = recovery_active
    async_dispatcher_send(hass, recovery_state_signal(entry.entry_id))
    await _flush(hass)

    # update_interval stays None — no silent re-enable.
    assert coord.update_interval is None
    coord.async_request_refresh.assert_not_awaited()


# ------------------------------------------------------------------
# Core-side observer hop to the event loop
# ------------------------------------------------------------------


async def test_core_observer_triggers_cadence_switch(
    hass: HomeAssistant,
    mock_orchestrator: MagicMock,
    mock_runtime_data: CableModemRuntimeData,
) -> None:
    """The observer Core invokes (from its poll thread) flips the cadence.

    Mocks Core by invoking the registered callback directly — the
    callback uses ``dispatcher_send`` which hops to the event loop
    via ``call_soon_threadsafe``.
    """
    entry = _make_entry(mock_runtime_data)
    coord = _make_coordinator(timedelta(minutes=10))

    attach_recovery_cadence_listener(hass, entry, mock_orchestrator, coord)
    observer = mock_orchestrator.set_recovery_observer.call_args[0][0]

    mock_orchestrator.recovery_active = True
    observer()  # simulates Core calling back from the poll thread
    await _flush(hass)

    assert coord.update_interval == _RECOVERY_POLL_INTERVAL


# ------------------------------------------------------------------
# Signal scoping across entries
# ------------------------------------------------------------------


async def test_different_entries_do_not_cross_talk(
    hass: HomeAssistant,
    mock_orchestrator: MagicMock,
    mock_runtime_data: CableModemRuntimeData,
) -> None:
    """Dispatcher signals are per-entry — other entries ignore them."""
    entry = _make_entry(mock_runtime_data, entry_id="entry_a")
    coord = _make_coordinator(timedelta(minutes=10))

    attach_recovery_cadence_listener(hass, entry, mock_orchestrator, coord)

    mock_orchestrator.recovery_active = True
    # Send the signal for a different entry_id — listener should ignore.
    async_dispatcher_send(hass, recovery_state_signal("entry_b"))
    await _flush(hass)

    assert coord.update_interval == timedelta(minutes=10)
