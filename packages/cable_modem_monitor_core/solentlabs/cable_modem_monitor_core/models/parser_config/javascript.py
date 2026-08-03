"""JSEmbeddedParser section config.

JavaScript format: delimited strings in JS function bodies.
Per PARSING_SPEC.md JSEmbeddedParser section.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import ChannelMapping, FilterValue
from .format_registry import DecodeKind


class JSFunction(BaseModel):
    """A JS function containing delimited channel data."""

    model_config = ConfigDict(extra="forbid")
    name: str
    channel_type: str = ""
    delimiter: str
    fields_per_channel: int
    fields: list[ChannelMapping]
    filter: dict[str, FilterValue] = Field(default_factory=dict)


class JSEmbeddedSection(BaseModel):
    """JSEmbeddedParser section config."""

    format_tag: ClassVar[str] = "javascript"
    decode_kind: ClassVar[DecodeKind] = "html"
    transports: ClassVar[frozenset[str]] = frozenset({"http"})

    model_config = ConfigDict(extra="forbid")
    format: Literal["javascript"]
    resource: str
    functions: list[JSFunction]
    encoding: str = ""
