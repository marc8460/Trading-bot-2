"""
PropOS — Base Filter Interface

All market condition filters implement this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.models.market import MarketSnapshot
from backend.models.signal import TradeSignal


@dataclass
class FilterResult:
    """Result of a single filter check."""
    passed: bool
    filter_name: str
    reason: str = ""
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class BaseFilter(ABC):
    """Abstract base class for market condition filters."""

    def __init__(self, name: str, enabled: bool = True) -> None:
        self.name = name
        self.enabled = enabled

    @abstractmethod
    async def check(
        self,
        signal: TradeSignal,
        snapshot: MarketSnapshot,
    ) -> FilterResult:
        """
        Check if market conditions pass this filter.

        Args:
            signal: The trade signal to validate.
            snapshot: Current market snapshot.

        Returns:
            FilterResult indicating pass/fail with reason.
        """
        ...
