"""Phase 2 auth-detection result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuthDetail:
    """Result of Phase 2 auth detection."""

    strategy: str
    fields: dict[str, Any] = field(default_factory=dict)
    confidence: str = "high"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for MCP tool output."""
        return {
            "strategy": self.strategy,
            "fields": self.fields,
            "confidence": self.confidence,
        }
