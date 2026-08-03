"""JSONTransposedParser — extract channel data from indexed-pivot JSON.

Some firmware exposes channel arrays as a list of metric rows::

    {"nodes": [
        {"name": "CH",     "index1": "0",  "index2": "1"},
        {"name": "Power",  "index1": "ON", "index2": "OFF"},
        {"name": "Freq",   "index1": "10", "index2": "20"}
    ]}

Each ``indexN`` column is one channel; each row contributes one named
field. The parser pivots into ``[{"CH": "0", "Power": "ON", "Freq": "10"}, ...]``,
then applies the same key→field/type/channel_type/filter machinery as
``JSONParser`` to produce canonical channel dicts.

Parameterized by ``JSONTransposedSection`` from parser.yaml.

See PARSING_SPEC.md and FORMAT_JSON_SPEC.md JSONTransposedParser section.
"""

from __future__ import annotations

import logging
from typing import Any

from ...models.parser_config.common import (
    ChannelTypeConfig,
    ChannelTypeFixed,
    ChannelTypeMap,
    FilterValue,
)
from ...models.parser_config.json_transposed import (
    JsonTransposedRowMapping,
    JSONTransposedSection,
)
from ..base import BaseParser
from ..filter import passes_filter
from ..type_conversion import convert_value
from .json_parser import _navigate_path

_logger = logging.getLogger(__name__)


def transpose_indexed_rows(
    rows: list[dict[str, Any]],
    name_field: str = "name",
    index_prefix: str = "index",
) -> list[dict[str, str]]:
    """Pivot ``name`` + ``indexN`` rows into per-column dicts.

    Detects column keys (``index1``, ``index2``, ...) from the first
    row, sorted lexicographically. Each column index becomes one output
    dict keyed by the row's ``name_field`` value. String values are
    stripped to handle leading/trailing whitespace from firmware
    responses.

    Returns an empty list when ``rows`` is empty or the first row has
    no matching columns. Public helper for use by parser.py
    PostProcessors that need pivoted rows under firmware-specific
    filter logic that can't be expressed declaratively.

    Args:
        rows: Pre-fetched list of metric rows.
        name_field: Field within each row that holds the metric name.
        index_prefix: Prefix for column keys (typically ``"index"``).

    Returns:
        List of per-column dicts; each dict's keys are the row-name
        values for that endpoint.
    """
    if not rows:
        return []

    col_keys = sorted(k for k in rows[0] if k.startswith(index_prefix))
    if not col_keys:
        return []

    result: list[dict[str, str]] = [{} for _ in col_keys]
    for row in rows:
        row_name = row.get(name_field, "")
        if not isinstance(row_name, str) or not row_name:
            continue
        for i, col_key in enumerate(col_keys):
            value = row.get(col_key, "")
            result[i][row_name] = value.strip() if isinstance(value, str) else value

    return result


class JSONTransposedParser(BaseParser):
    """Extract channel data from an indexed-pivot JSON response.

    Args:
        config: Validated ``JSONTransposedSection`` from parser.yaml.
    """

    def __init__(self, config: JSONTransposedSection) -> None:
        self._config = config

    def parse(self, resources: dict[str, Any]) -> list[dict[str, Any]]:
        """Pivot rows and extract per-channel field dicts.

        Args:
            resources: Resource dict (path -> parsed JSON dict).

        Returns:
            List of channel dicts with converted field values.
        """
        data = resources.get(self._config.resource)
        if data is None:
            _logger.warning("Resource '%s' not found", self._config.resource)
            return []
        if not isinstance(data, dict):
            _logger.warning(
                "Resource '%s' is not a dict (got %s)",
                self._config.resource,
                type(data).__name__,
            )
            return []

        rows = _navigate_path(data, self._config.array_path)
        if rows is None:
            _logger.warning("Array path '%s' not found", self._config.array_path)
            return []
        if not isinstance(rows, list):
            _logger.warning(
                "Value at '%s' is not a list (got %s)",
                self._config.array_path,
                type(rows).__name__,
            )
            return []

        pivoted = transpose_indexed_rows(
            rows,
            name_field=self._config.name_field,
            index_prefix=self._config.index_prefix,
        )

        channels: list[dict[str, Any]] = []
        for row in pivoted:
            channel = _extract_channel(row, self._config.fields)
            if channel is None:
                continue

            _apply_channel_type(channel, self._config.channel_type)

            if not _passes_filter(channel, row, self._config.filter):
                continue

            channels.append(channel)

        return channels


def _extract_channel(
    row: dict[str, str],
    mappings: list[JsonTransposedRowMapping],
) -> dict[str, Any] | None:
    """Extract one channel dict from a pivoted row.

    Each mapping selects ``row[mapping.label]`` (the value originally
    in the indexed column for the named metric row) and converts it
    to the canonical field via ``convert_value``.

    Returns ``None`` if no fields could be extracted.
    """
    channel: dict[str, Any] = {}

    for mapping in mappings:
        raw_value = row.get(mapping.label)
        if raw_value is None or raw_value == "":
            continue

        value = convert_value(
            raw_value,
            mapping.type,
            unit=mapping.unit,
            map_config=mapping.map,
            scale=mapping.scale,
            input_format=mapping.format,
        )

        if value is not None:
            channel[mapping.field] = value

    return channel if channel else None


def _apply_channel_type(
    channel: dict[str, Any],
    channel_type: ChannelTypeConfig | None,
) -> None:
    """Apply channel_type from config (fixed or field→map derivation)."""
    if "channel_type" in channel:
        return

    if channel_type is None:
        return

    if isinstance(channel_type, ChannelTypeFixed):
        channel["channel_type"] = channel_type.fixed
        return

    if isinstance(channel_type, ChannelTypeMap):
        raw_value = str(channel.get(channel_type.field, ""))
        if raw_value and raw_value in channel_type.map:
            channel["channel_type"] = channel_type.map[raw_value]
        elif raw_value:
            _logger.warning(
                "Unmapped channel_type value: '%s' (known: %s)",
                raw_value,
                list(channel_type.map.keys()),
            )


def _passes_filter(
    channel: dict[str, Any],
    raw_row: dict[str, str],
    filter_rules: dict[str, FilterValue],
) -> bool:
    """Apply filter rules against the canonical channel and the raw row.

    Filter keys may reference either a canonical channel field or a
    raw row-name (the value originally seen in ``name_field``). Raw-row
    matching is required for filter keys like ``Power`` that aren't
    mapped to a canonical field — common when a firmware-quirk filter
    drops rows by transient state without exposing it as a channel
    field. Canonical fields take precedence on key collision.
    """
    canonical_only = {k: v for k, v in filter_rules.items() if k in channel}
    raw_only = {k: v for k, v in filter_rules.items() if k not in channel}

    if not passes_filter(channel, canonical_only):
        return False
    return passes_filter(raw_row, raw_only)
