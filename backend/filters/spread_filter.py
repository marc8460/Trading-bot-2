"""
PropOS — Spread Filter

Blocks trades when the current spread exceeds the configured maximum
for the symbol. Critical for XAUUSD which has wide spreads during news.
"""

from __future__ import annotations

from backend.core.logging import get_logger
from backend.filters.base import BaseFilter, FilterResult
from backend.models.market import MarketSnapshot
from backend.models.signal import TradeSignal

logger = get_logger(__name__)


class SpreadFilter(BaseFilter):
    """Rejects signals when spread is too wide."""

    def __init__(self, max_spread_points: dict[str, int] | None = None) -> None:
        super().__init__(name="spread")
        self.max_spread_points = max_spread_points or {
            "EURUSD": 20,
            "XAUUSD": 50,
            "GBPUSD": 25,
        }

    async def check(self, signal: TradeSignal, snapshot: MarketSnapshot) -> FilterResult:
        if not self.enabled:
            return FilterResult(passed=True, filter_name=self.name)

        max_spread = self.max_spread_points.get(signal.symbol, 30)
        current_spread = snapshot.current_spread_points

        if current_spread > max_spread:
            return FilterResult(
                passed=False,
                filter_name=self.name,
                reason=f"Spread {current_spread:.1f} > max {max_spread} points",
                details={"current": current_spread, "max": max_spread},
            )

        return FilterResult(
            passed=True,
            filter_name=self.name,
            details={"current": current_spread, "max": max_spread},
        )
