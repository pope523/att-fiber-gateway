"""Post-processor for Nokia BGW320-505 — fiber optical metrics.

The BGW320-505 fiber status page (``/cgi-bin/fiberstat.ha``) reports the
*current* optical diagnostic values inside ``<h1>`` headers of the form
``<h1>Rx Power&nbsp;&nbsp;Currently -170</h1>`` — the grid tables under
each header carry only the alarm/warning thresholds, not the live reading.
This post-processor lifts those current values into ``system_info``:

- ``optical_rx_power`` — receive optical power (dBm)
- ``optical_tx_power`` — transmit optical power (dBm)
- ``optical_temperature`` — SFP module temperature (°C)

Per the page's own help text, Rx/Tx power are reported in one-tenth of a
dBm, so the raw integer is divided by 10 (e.g. ``-170`` → ``-17.0`` dBm).

This is a fiber ONT+gateway with no DOCSIS channels, so only
``parse_system_info`` is implemented. Extraction fails safe: if the page
or a header is missing (e.g. a future firmware changes the layout), the
affected field is simply omitted rather than raising.
"""

from __future__ import annotations

import re
from typing import Any

# h1 label -> (system_info field, divisor). Divisor 10 converts the
# firmware's one-tenth-dBm integers to dBm; 1 leaves the value as-is.
_OPTICAL_METRICS: dict[str, tuple[str, int]] = {
    "Rx Power": ("optical_rx_power", 10),
    "Tx Power": ("optical_tx_power", 10),
    "Temperature": ("optical_temperature", 1),
}

_FIBERSTAT_RESOURCE = "/cgi-bin/fiberstat.ha"

# Captures the integer after "Currently" within a single <h1> header.
_CURRENTLY_RE = re.compile(r"Currently\s*(-?\d+)")


class PostProcessor:
    """Fiber optical enrichment for the BGW320-505 (system_info only)."""

    def parse_system_info(
        self,
        system_info: dict[str, Any],
        resources: dict[str, Any],
    ) -> dict[str, Any]:
        """Add current optical Rx/Tx power and temperature from fiberstat.ha.

        Args:
            system_info: Merged system_info dict from parser.yaml sources.
            resources: Resource dict keyed by URL path (BeautifulSoup for
                HTML pages).

        Returns:
            The system_info dict enriched with optical fields (in place).
        """
        soup = resources.get(_FIBERSTAT_RESOURCE)
        if soup is None or not hasattr(soup, "find_all"):
            return system_info

        for header in soup.find_all("h1"):
            text = header.get_text().replace("\xa0", " ").strip()
            for label, (field, divisor) in _OPTICAL_METRICS.items():
                if not text.startswith(label):
                    continue
                match = _CURRENTLY_RE.search(text)
                if match is not None:
                    raw = int(match.group(1))
                    value = raw if divisor == 1 else round(raw / divisor, 1)
                    system_info[field] = str(value)
                break

        return system_info
