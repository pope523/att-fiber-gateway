"""JSONTransposedParser section config.

Indexed-pivot JSON format: rows are metrics, ``indexN`` columns are
channels. Each row carries a ``name`` field (configurable) plus
``index1``/``index2``/... value columns. Pivoting turns each column
into one channel dict keyed by the row-name values.

Per FORMAT_JSON_SPEC.md JSONTransposedParser section.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..field_registry import FIELD_TYPES
from .common import ChannelTypeConfig, FilterValue
from .format_registry import DecodeKind


class JsonTransposedRowMapping(BaseModel):
    """JSONTransposedParser row-name -> field mapping.

    ``label`` is the exact value to match in the row's ``name_field``.
    The cell value at each ``indexN`` column then becomes the source
    for the canonical ``field`` after type conversion.
    """

    model_config = ConfigDict(extra="forbid")
    label: str
    field: str
    type: str
    unit: str = ""
    format: str = ""
    map: dict[str, str] | None = None
    scale: int | float | None = None

    @model_validator(mode="after")
    def validate_field_type(self) -> JsonTransposedRowMapping:
        """Ensure type is a valid FIELD_TYPES value."""
        if self.type not in FIELD_TYPES:
            raise ValueError(f"invalid field type '{self.type}', must be one of " f"{sorted(FIELD_TYPES)}")
        return self


class JSONTransposedSection(BaseModel):
    """JSONTransposedParser section config.

    Locates a list of rows at ``array_path`` within the JSON resource;
    each row carries ``name_field`` plus ``{index_prefix}1``,
    ``{index_prefix}2``, ... value columns. Pivots into per-column
    channel dicts.
    """

    format_tag: ClassVar[str] = "json_transposed"
    decode_kind: ClassVar[DecodeKind] = "json"
    transports: ClassVar[frozenset[str]] = frozenset({"http"})

    model_config = ConfigDict(extra="forbid")
    format: Literal["json_transposed"]
    resource: str
    encoding: str = ""
    array_path: str = "nodes"
    name_field: str = "name"
    index_prefix: str = "index"
    fields: list[JsonTransposedRowMapping]
    channel_type: ChannelTypeConfig | None = None
    filter: dict[str, FilterValue] = Field(default_factory=dict)
