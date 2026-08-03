"""Tests for ``field_registry`` canonical ordering.

Covers ``canonicalize_channel_keys`` across all channel types
(QAM, OFDM, ATDMA, OFDMA) plus the pass-through behavior for
Tier 2/3 fields and the sparse-dict behavior for missing keys.
"""

from __future__ import annotations

import pytest
from solentlabs.cable_modem_monitor_core.models.field_registry import (
    CHANNEL_FIELD_ORDER,
    canonicalize_channel_keys,
)

# Table-driven: (label, input dict, expected key sequence)
CANONICAL_CASES: list[tuple[str, dict[str, object], tuple[str, ...]]] = [
    (
        "qam_downstream_full",
        {
            "frequency": 507000000,
            "power": 8.2,
            "snr": 44.0,
            "corrected": 53,
            "uncorrected": 231,
            "lock_status": "locked",
            "modulation": "QAM256",
            "channel_id": 20,
            "channel_type": "qam",
            "channel_number": 1,
        },
        (
            "lock_status",
            "channel_type",
            "channel_id",
            "channel_number",
            "modulation",
            "frequency",
            "power",
            "snr",
            "corrected",
            "uncorrected",
        ),
    ),
    (
        "ofdm_downstream_with_source",
        {
            "channel_id": 193,
            "frequency": 690000000,
            "power": 8.78,
            "snr": 42.9,
            "channel_type": "ofdm",
            "channel_number": 33,
            "source_channel_number": 1,
            "lock_status": "locked",
        },
        (
            "lock_status",
            "channel_type",
            "channel_id",
            "channel_number",
            "source_channel_number",
            "frequency",
            "power",
            "snr",
        ),
    ),
    (
        "atdma_upstream",
        {
            "channel_type": "atdma",
            "channel_id": 2,
            "symbol_rate": 5120,
            "frequency": 22800000,
            "power": 40.0,
            "channel_number": 1,
            "lock_status": "locked",
        },
        (
            "lock_status",
            "channel_type",
            "channel_id",
            "channel_number",
            "frequency",
            "symbol_rate",
            "power",
        ),
    ),
    (
        "ofdma_upstream_with_source",
        {
            "channel_id": 41,
            "frequency": 36200000,
            "power": 37.3,
            "channel_type": "ofdma",
            "channel_number": 5,
            "source_channel_number": 1,
            "lock_status": "locked",
        },
        (
            "lock_status",
            "channel_type",
            "channel_id",
            "channel_number",
            "source_channel_number",
            "frequency",
            "power",
        ),
    ),
    (
        "sparse_channel_unlocked",
        {
            "channel_number": 7,
            "lock_status": "not_locked",
        },
        ("lock_status", "channel_number"),
    ),
    (
        "tier2_passthrough_preserves_input_order",
        {
            "frequency": 690000000,
            "channel_id": 193,
            "lock_status": "locked",
            "channel_width": 192000000,
            "active_subcarriers": 3800,
            "profile_id": "A",
        },
        (
            "lock_status",
            "channel_id",
            "frequency",
            "channel_width",
            "active_subcarriers",
            "profile_id",
        ),
    ),
    (
        "unknown_tier3_field_appended_last",
        {
            "t3_timeouts": 0,
            "lock_status": "locked",
            "channel_type": "qam",
            "channel_id": 5,
        },
        (
            "lock_status",
            "channel_type",
            "channel_id",
            "t3_timeouts",
        ),
    ),
]


@pytest.mark.parametrize(
    "label,channel,expected",
    CANONICAL_CASES,
    ids=[case[0] for case in CANONICAL_CASES],
)
def test_canonicalize_channel_keys(
    label: str,
    channel: dict[str, object],
    expected: tuple[str, ...],
) -> None:
    result = canonicalize_channel_keys(channel)
    assert tuple(result.keys()) == expected
    assert result == channel  # same contents, only order differs


def test_canonicalize_returns_new_dict() -> None:
    channel = {"channel_id": 1, "lock_status": "locked"}
    result = canonicalize_channel_keys(channel)
    assert result is not channel
    channel["channel_id"] = 99
    assert result["channel_id"] == 1


def test_empty_channel_returns_empty_dict() -> None:
    assert canonicalize_channel_keys({}) == {}


def test_canonical_order_covers_all_tier1_fields() -> None:
    """CHANNEL_FIELD_ORDER should not drift from Tier 1 registry sets."""
    from solentlabs.cable_modem_monitor_core.models.field_registry import (
        DOWNSTREAM_FIELDS,
        UPSTREAM_FIELDS,
    )

    tier1 = DOWNSTREAM_FIELDS | UPSTREAM_FIELDS
    runtime_added = {"channel_number", "source_channel_number"}
    expected = tier1 | runtime_added

    assert set(CHANNEL_FIELD_ORDER) == expected
