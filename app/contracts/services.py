"""Interfaces implemented by the data and agent boundaries."""

from __future__ import annotations

from typing import Protocol

from .models import Guidance


class GuidanceUnavailableError(RuntimeError):
    """Raised when the J-owned API starts before T's data adapter is available."""


class GuidanceService(Protocol):
    async def get_guidance(self, scenario_id: str) -> Guidance:
        """Return server-owned guidance for the fixed MVP scenario."""
