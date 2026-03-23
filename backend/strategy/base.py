"""
PropOS — Base Strategy Interface

All strategies must extend this ABC to integrate with the platform.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.models.market import MarketSnapshot
from backend.models.signal import TradeSignal


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    Implement `evaluate()` to produce trade signals based on market data.
    The strategy engine calls `evaluate()` on each tick interval.
    """

    def __init__(self, name: str, version: str = "1.0.0", **params: Any) -> None:
        self.name = name
        self.version = version
        self.params = params
        self._enabled = True

    @abstractmethod
    async def evaluate(self, snapshot: MarketSnapshot) -> TradeSignal:
        """
        Evaluate market conditions and produce a trade signal.

        Args:
            snapshot: Current market data snapshot for the symbol.

        Returns:
            TradeSignal with direction (LONG, SHORT, or NO_TRADE).
        """
        ...

    @abstractmethod
    async def on_init(self) -> None:
        """Called once when the strategy is loaded. Load indicators, state, etc."""
        ...

    async def on_shutdown(self) -> None:
        """Called when the strategy is being unloaded."""
        pass

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def get_info(self) -> dict[str, Any]:
        """Return strategy metadata for dashboard display."""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self._enabled,
            "params": self.params,
        }
