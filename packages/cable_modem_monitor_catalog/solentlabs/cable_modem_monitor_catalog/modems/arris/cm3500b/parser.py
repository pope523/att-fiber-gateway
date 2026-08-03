"""Post-processor for ARRIS CM3500B — OFDM channel enrichment.

Sets OFDM ``frequency`` to the lower edge of the active subcarrier
band (the first subcarrier frequency, in Hz) per FIELD_REGISTRY.md
§ frequency semantics. ``channel_width`` is mapped directly from the
firmware's bandwidth column in parser.yaml.

``channel_id`` is set from ``source_channel_number`` — the label
index extracted by parser.yaml (``"Downstream 1"`` → ``1``). The
CM3500B firmware does not expose OFDM DCIDs.

System info extraction is handled by parser.yaml (html_fields format).
"""

from __future__ import annotations

from typing import Any


class PostProcessor:
    """OFDM/OFDMA post-processor for CM3500B."""

    def parse_downstream(
        self,
        channels: list[dict[str, Any]],
        resources: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Enrich downstream OFDM channels with computed fields."""
        for ch in channels:
            if ch.get("channel_type") == "ofdm":
                _enrich_ofdm_channel(ch)
        return channels

    def parse_upstream(
        self,
        channels: list[dict[str, Any]],
        resources: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Enrich upstream OFDMA channels with computed fields."""
        for ch in channels:
            if ch.get("channel_type") == "ofdma":
                _enrich_ofdm_channel(ch)
        return channels


def _enrich_ofdm_channel(channel: dict[str, Any]) -> None:
    """Set channel ID and lower-edge frequency for an OFDM channel.

    Modifies the channel dict in place:
    - ``channel_id``: from ``source_channel_number`` (label index).
    - ``frequency``: first subcarrier frequency in Hz (lower edge).

    ``last_subcarrier_freq`` is dropped (channel_width is mapped
    directly by parser.yaml from the firmware bandwidth column).
    """
    # Use label index as channel_id (no DCID available in firmware)
    channel["channel_id"] = channel.get("source_channel_number", 0)

    first_mhz = channel.pop("first_subcarrier_freq", None)
    channel.pop("last_subcarrier_freq", None)
    if first_mhz is not None:
        channel["frequency"] = int(float(first_mhz) * 1_000_000)
