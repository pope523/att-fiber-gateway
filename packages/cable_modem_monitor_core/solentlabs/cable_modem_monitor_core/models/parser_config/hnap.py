"""HNAPParser section config.

HNAP format: delimiter-separated values in HNAP JSON responses.
Per PARSING_SPEC.md HNAPParser section.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import ChannelMapping, ChannelTypeConfig, FilterValue
from .format_registry import DecodeKind


class HNAPSection(BaseModel):
    """HNAPParser section config."""

    format_tag: ClassVar[str] = "hnap"
    decode_kind: ClassVar[DecodeKind] = "hnap"
    transports: ClassVar[frozenset[str]] = frozenset({"hnap"})

    model_config = ConfigDict(extra="forbid")
    format: Literal["hnap"]
    response_key: str
    data_key: str
    record_delimiter: str
    field_delimiter: str
    fields: list[ChannelMapping]
    channel_type: ChannelTypeConfig | None = None
    filter: dict[str, FilterValue] = Field(default_factory=dict)
