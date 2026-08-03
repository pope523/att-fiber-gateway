"""Tests for the centralized parser-format registry.

The runtime registry lists (``CHANNEL_SECTION_MODELS``,
``SYSTEM_INFO_SOURCE_MODELS``, ``ALL_FORMAT_MODELS``) drive the
loader's decode dispatch, the cross-file transport/format validator,
and the parser registries. The static ``ChannelSection`` and
``SystemInfoSource`` discriminated unions are hand-maintained for
type-checkers (mypy/Pyright cannot infer a union built at runtime).

These tests ensure the static unions and runtime lists cannot drift
out of alignment, and that every registered model declares the
required ClassVars.
"""

from __future__ import annotations

from typing import get_args

from solentlabs.cable_modem_monitor_core.models.parser_config.config import (
    ALL_FORMAT_MODELS,
    CHANNEL_SECTION_MODELS,
    ChannelSection,
)
from solentlabs.cable_modem_monitor_core.models.parser_config.format_registry import (
    DecodeKind,
)
from solentlabs.cable_modem_monitor_core.models.parser_config.system_info import (
    SYSTEM_INFO_SOURCE_MODELS,
    SystemInfoSource,
)


def _models_in_static_union(union_type: object) -> list[type]:
    """Walk an Annotated discriminated union and return its inner types in order."""
    # Annotated[X, metadata] — args are (X, *metadata)
    inner = get_args(union_type)[0]
    # Inner is the | union; get_args returns the union members.
    members = get_args(inner)
    # Each member is Annotated[ConcreteModel, Tag("...")] — peel off Tag
    return [get_args(m)[0] for m in members]


def test_channel_section_registry_alignment() -> None:
    """Static ChannelSection union and CHANNEL_SECTION_MODELS list agree."""
    static_models = _models_in_static_union(ChannelSection)
    assert static_models == CHANNEL_SECTION_MODELS, (
        "ChannelSection static union and CHANNEL_SECTION_MODELS runtime list have "
        f"drifted.\n  static:  {[m.__name__ for m in static_models]}\n"
        f"  runtime: {[m.__name__ for m in CHANNEL_SECTION_MODELS]}"
    )


def test_system_info_source_registry_alignment() -> None:
    """Static SystemInfoSource union and SYSTEM_INFO_SOURCE_MODELS list agree."""
    static_models = _models_in_static_union(SystemInfoSource)
    assert static_models == SYSTEM_INFO_SOURCE_MODELS, (
        "SystemInfoSource static union and SYSTEM_INFO_SOURCE_MODELS runtime "
        "list have drifted.\n"
        f"  static:  {[m.__name__ for m in static_models]}\n"
        f"  runtime: {[m.__name__ for m in SYSTEM_INFO_SOURCE_MODELS]}"
    )


_VALID_DECODE_KINDS = frozenset(get_args(DecodeKind))


def test_overlapping_format_tags_agree() -> None:
    """Models sharing a format_tag agree on decode_kind and transports.

    Several format tags appear in both registries — ``json``, ``hnap``,
    ``javascript``, ``xml`` are valid in both a channel section and a
    system_info source. The loader's ``lookup_decode_kind`` returns the
    first match across ``ALL_FORMAT_MODELS``; if duplicates ever
    disagreed, the loser's decode_kind would silently become dead code.
    Catch drift here instead of at runtime.
    """
    by_tag: dict[str, list[type]] = {}
    for model in ALL_FORMAT_MODELS:
        by_tag.setdefault(model.format_tag, []).append(model)

    for tag, models in by_tag.items():
        if len(models) < 2:
            continue
        kinds = {m.decode_kind for m in models}
        transports_sets = {m.transports for m in models}
        assert len(kinds) == 1, (
            f"format_tag '{tag}' has conflicting decode_kind across " f"{[m.__name__ for m in models]}: {sorted(kinds)}"
        )
        assert len(transports_sets) == 1, (
            f"format_tag '{tag}' has conflicting transports across "
            f"{[m.__name__ for m in models]}: {[sorted(t) for t in transports_sets]}"
        )


def test_every_registered_model_declares_class_vars() -> None:
    """Every model in ALL_FORMAT_MODELS exposes the three required ClassVars."""
    missing: list[str] = []
    for model in ALL_FORMAT_MODELS:
        for attr in ("format_tag", "decode_kind", "transports"):
            if not hasattr(model, attr):
                missing.append(f"{model.__name__}.{attr}")
        # Type sanity: format_tag is a non-empty str, decode_kind is one of
        # the registered literals, transports is a non-empty frozenset.
        assert isinstance(model.format_tag, str) and model.format_tag, model.__name__
        assert model.decode_kind in _VALID_DECODE_KINDS, (
            f"{model.__name__}.decode_kind = {model.decode_kind!r} not in " f"{_VALID_DECODE_KINDS}"
        )
        assert isinstance(model.transports, frozenset) and model.transports, model.__name__
    assert not missing, f"Models missing ClassVars: {missing}"
