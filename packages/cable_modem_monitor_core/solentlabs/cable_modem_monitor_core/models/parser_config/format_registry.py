"""Centralized registry of parser-format metadata.

Each ChannelSection model and SystemInfoSource model declares three
``ClassVar``s describing how the loader, validator, and parser
registries should treat that format:

- ``format_tag``: literal value of ``format:`` in parser.yaml
- ``decode_kind``: how the loader decodes the response body
- ``transports``: which transports may select this format

The lists ``CHANNEL_SECTION_MODELS`` (in ``config.py``) and
``SYSTEM_INFO_SOURCE_MODELS`` (in ``system_info.py``) are the single
source of truth — discriminated unions, the loader's decode dispatch,
the cross-file transport-format validator, and the parser registry
all derive from those lists. Adding a format means: write the model
with its ClassVars, append it to the list, and (for channel sections)
register the wrapper in ``parsers/registries.py``.

See ARCHITECTURE_DECISIONS.md § "How to add a format".
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar, Literal, Protocol

DecodeKind = Literal["html", "json", "xml", "hnap"]


class FormatModel(Protocol):
    """Structural protocol for any model that declares format metadata.

    Implemented (via ``ClassVar``s) by every ChannelSection model and
    every SystemInfoSource model. Mypy matches structurally — any
    Pydantic model that declares the three ClassVars below counts as
    a ``FormatModel``.
    """

    format_tag: ClassVar[str]
    decode_kind: ClassVar[DecodeKind]
    transports: ClassVar[frozenset[str]]


def lookup_decode_kind(
    fmt: str,
    registry: Iterable[type[FormatModel]],
) -> DecodeKind | None:
    """Return the decode_kind for a format tag, or ``None`` if not registered."""
    for model in registry:
        if model.format_tag == fmt:
            return model.decode_kind
    return None


def format_tags_for_transport(
    transport: str,
    registry: Iterable[type[FormatModel]],
) -> frozenset[str]:
    """Return the set of ``format_tag``s in ``registry`` valid for ``transport``."""
    return frozenset(m.format_tag for m in registry if transport in m.transports)
