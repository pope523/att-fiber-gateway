"""HA-side recovery cadence wiring.

Core owns recovery *semantics* — a bounded window opens after a
restart, an observed outage, or a reboot-signal match — and exposes
the state via ``Orchestrator.recovery_active`` plus an observer
callback. HA owns recovery *scheduling*: while a window is open the
data coordinator polls at ``_RECOVERY_POLL_INTERVAL``, and when the
window closes the coordinator returns to the user-configured cadence.

This module is the one and only HA-side consumer of Core's recovery
observer. Other HA modules (sensors, buttons, diagnostics) don't
subscribe — they read ``orchestrator.recovery_active`` directly or
render snapshot truth.

Shape:

- ``_RECOVERY_POLL_INTERVAL`` — module-private cadence constant.
- ``recovery_state_signal(entry_id)`` — per-entry dispatcher signal
  name. Public so tests can subscribe; no other production module
  does.
- ``attach_recovery_cadence_listener(...)`` — the single entry point.
  Called once during ``async_setup_entry``.

See HA_ADAPTER_SPEC.md § Recovery Adapter for the contract and
ARCHITECTURE_DECISIONS.md § Core→HA recovery coupling for rationale.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    dispatcher_send,
)

from .const import CONF_MODEL

if TYPE_CHECKING:
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
    from solentlabs.cable_modem_monitor_core.orchestration.models import (
        ModemSnapshot,
    )
    from solentlabs.cable_modem_monitor_core.orchestration.orchestrator import (
        Orchestrator,
    )

    from .coordinator import CableModemConfigEntry

_LOGGER = logging.getLogger(__name__)

# Data coordinator cadence while Core's recovery window is open.
# Short enough to surface UNREACHABLE → ranging → Operational
# promptly on the dashboard; long enough not to hammer modem
# firmware anti-brute-force thresholds during the window.
_RECOVERY_POLL_INTERVAL = timedelta(seconds=30)


def recovery_state_signal(entry_id: str) -> str:
    """Per-entry dispatcher signal name for recovery transitions.

    Per-entry so multi-modem setups don't cross-talk. Published from
    the Core poll thread via ``dispatcher_send`` and consumed by an
    event-loop listener that flips the coordinator's
    ``update_interval``.
    """
    return f"cable_modem_monitor_recovery_state_{entry_id}"


def attach_recovery_cadence_listener(
    hass: HomeAssistant,
    entry: CableModemConfigEntry,
    orchestrator: Orchestrator,
    data_coordinator: DataUpdateCoordinator[ModemSnapshot],
) -> None:
    """Switch data-coordinator cadence when Core's recovery window flips.

    Installs an observer on Core that dispatches a per-entry signal
    whenever ``orchestrator.recovery_active`` changes, plus an
    event-loop listener that swaps ``data_coordinator.update_interval``
    between ``_RECOVERY_POLL_INTERVAL`` (window open) and the
    user-configured normal cadence (window closed).

    Single point of HA-side contact for Core's recovery state — other
    modules (sensors, buttons) don't subscribe; they read
    ``orchestrator.recovery_active`` directly or render snapshot truth.

    Behavior details:

    - The "normal" cadence is captured in a closure, not on
      RuntimeData. This module owns it.
    - On False→True, also kicks ``async_request_refresh()`` so the
      first fast-cadence poll runs immediately instead of waiting one
      ``_RECOVERY_POLL_INTERVAL``.
    - When the captured normal cadence is ``None`` (user disabled
      scheduled polling), the listener is a no-op — we don't silently
      re-enable polling behind the user's back.
    - Core fires the observer from the poll thread; ``dispatcher_send``
      hops to the event loop via ``call_soon_threadsafe``.
    - Teardown clears the Core observer and disconnects the dispatcher
      listener, registered via ``entry.async_on_unload``.
    """
    # Snapshot the user's configured cadence. The closure keeps
    # this private to the adapter — RuntimeData stays minimal.
    normal_interval = data_coordinator.update_interval
    signal = recovery_state_signal(entry.entry_id)
    # entry.data is always available; runtime_data is not yet set
    # at this point in async_setup_entry. Model is for log lines.
    model = entry.data.get(CONF_MODEL, "")

    @callback
    def _apply_cadence() -> None:
        """Event-loop listener — switch coordinator interval to match state."""
        # Respect user opt-out. If the options flow disabled polling,
        # leave update_interval alone; the fast cadence would re-enable
        # scheduled polls behind their back.
        if normal_interval is None:
            return

        if orchestrator.recovery_active:
            data_coordinator.update_interval = _RECOVERY_POLL_INTERVAL
            _LOGGER.info(
                "Recovery window open [%s] — data poll cadence = %ss",
                model,
                int(_RECOVERY_POLL_INTERVAL.total_seconds()),
            )
            # Kick an immediate refresh so the first fast poll runs
            # now rather than waiting one _RECOVERY_POLL_INTERVAL.
            hass.async_create_task(
                data_coordinator.async_request_refresh(),
                "cable_modem_recovery_refresh",
            )
        else:
            data_coordinator.update_interval = normal_interval
            _LOGGER.info(
                "Recovery window closed [%s] — data poll cadence restored",
                model,
            )

    # Observer fires on the Core poll thread — dispatcher_send is
    # the thread-safe variant (wraps call_soon_threadsafe). Keep
    # the body minimal; the listener above does the real work.
    def _on_recovery_state_change() -> None:
        dispatcher_send(hass, signal)

    # Connect the listener first, then install the observer —
    # ordering guarantees the first transition isn't dropped.
    unsub_listener = async_dispatcher_connect(hass, signal, _apply_cadence)
    orchestrator.set_recovery_observer(_on_recovery_state_change)

    @callback
    def _teardown() -> None:
        orchestrator.set_recovery_observer(None)
        unsub_listener()

    entry.async_on_unload(_teardown)
