"""Phase 2 - Auth strategy detection.

Public API: ``detect_auth()`` dispatches to transport-specific modules
(``hnap``, ``http``).

Per docs/ONBOARDING_SPEC.md Phase 2.
"""

from __future__ import annotations

from typing import Any

from ..types import CoreGap
from .hnap import detect_hnap_auth
from .http import detect_http_auth
from .types import AuthDetail

__all__ = ["AuthDetail", "detect_auth"]


def detect_auth(
    entries: list[dict[str, Any]],
    transport: str,
    warnings: list[str],
    hard_stops: list[str],
    core_gaps: list[CoreGap] | None = None,
) -> AuthDetail:
    """Detect auth strategy from HAR entries.

    Dispatches to transport-specific detection:

    - HNAP: always ``hnap`` strategy, detect hmac_algorithm
    - HTTP: walks the Phase 2 decision tree

    Args:
        entries: HAR ``log.entries`` list.
        transport: Detected transport (``http`` or ``hnap``).
        warnings: Mutable list to append warnings to.
        hard_stops: Mutable list to append hard stops to.
        core_gaps: Mutable list to append core gap items to.

    Returns:
        AuthDetail with strategy, extracted fields, and confidence.
    """
    if core_gaps is None:
        core_gaps = []
    if transport == "hnap":
        return detect_hnap_auth(entries, warnings)
    return detect_http_auth(entries, warnings, hard_stops, core_gaps)
