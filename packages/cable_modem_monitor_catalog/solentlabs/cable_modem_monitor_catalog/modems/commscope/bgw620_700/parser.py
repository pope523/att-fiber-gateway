"""Post-processor for CommScope BGW620-700 — fiber optical metrics.

The BGW620-700 fiber status page (``/cgi-bin/fiberstat.ha``) reports the
*current* optical diagnostic values inside ``<h1>`` headers of the form
``<h1>Rx Power&nbsp;&nbsp;Currently 0.138</h1>`` — the grid tables under
each header carry only the alarm/warning thresholds, not the live reading.
This post-processor lifts those current values into ``system_info``:

- ``optical_rx_power`` — receive optical power (dBm)
- ``optical_tx_power`` — transmit optical power (dBm)
- ``optical_temperature`` — SFP module temperature (°C)

Unlike the BGW320-505 (integer tenths of a dBm), this firmware prints
decimal *linear* power. The page's help text declares the raw SFF-8472
register unit ("Power in W/10,000,000", i.e. 0.1 µW per count); the
display divides that count inconsistently per field:

- Rx Power: count/10000 → the displayed number is milliwatts.
- Tx Power: count/1000 → the displayed number is tenths of a milliwatt.

The alarm/warning thresholds use the Tx scaling for both fields, which is
how the scaling was inferred: converted this way, a live 5Gb XGS-PON line
shows Tx +6.1 dBm inside its +4.2..+8.1 dBm threshold band and Rx
-8.6 dBm inside its -13..-8 dBm threshold band — both textbook XGS-PON N1
values. Both fields are converted to dBm (10·log10(mW)) to match the
BGW320-505 fields and the integration's dBm sensors.

Extraction fails safe: if the page or a header is missing, or a power
value is zero/negative (log10 undefined — e.g. fiber unplugged), the
affected field is simply omitted rather than raising.
"""

from __future__ import annotations

import math
import re
from typing import Any

_FIBERSTAT_RESOURCE = "/cgi-bin/fiberstat.ha"

# Captures the decimal after "Currently" within a single <h1> header.
_CURRENTLY_RE = re.compile(r"Currently\s*(-?\d+(?:\.\d+)?)")


def _dbm_from_mw(milliwatts: float) -> str | None:
    """Convert linear mW to a dBm string, or None if not representable."""
    if milliwatts <= 0:
        return None
    return str(round(10 * math.log10(milliwatts), 1))


# h1 label -> (system_info field, display-value-to-field converter).
_OPTICAL_METRICS: dict[str, tuple[str, Any]] = {
    "Rx Power": ("optical_rx_power", _dbm_from_mw),  # display is mW
    "Tx Power": ("optical_tx_power", lambda v: _dbm_from_mw(v / 10)),  # display is 0.1 mW
    "Temperature": ("optical_temperature", lambda v: str(round(v, 1))),  # display is °C
}


class PostProcessor:
    """Fiber optical enrichment for the BGW620-700 (system_info only)."""

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
            for label, (field, convert) in _OPTICAL_METRICS.items():
                if not text.startswith(label):
                    continue
                match = _CURRENTLY_RE.search(text)
                if match is not None:
                    value = convert(float(match.group(1)))
                    if value is not None:
                        system_info[field] = value
                break

        return system_info
