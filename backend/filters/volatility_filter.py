"""
PropOS — Volatility Filter

Blocks trades when ATR-based volatility is outside normal range
(too low = choppy, too high = dangerous).
"""

from __future__ import annotations

from backend.core.logging import get_logger
from backend.filters.base import BaseFilter, FilterResult
from backend.models.market import MarketSnapshot
from backend.models.signal import TradeSignal

logger = get_logger(__name__)


class VolatilityFilter(BaseFilter):
    """Rejects signals when volatility is abnormally high or low."""

    def __init__(
        self,
        min_atr_multiplier: float = 0.5,
        max_atr_multiplier: float = 3.0,
    ) -> None:
        super().__init__(name="volatility")
        self.min_atr_multiplier = min_atr_multiplier
        self.max_atr_multiplier = max_atr_multiplier

    async def check(self, signal: TradeSignal, snapshot: MarketSnapshot) -> FilterResult:
        if not self.enabled:
            return FilterResult(passed=True, filter_name=self.name)

        if snapshot.atr == 0:
            return FilterResult(
                passed=True,
                filter_name=self.name,
                reason="ATR not available",
            )

        # Compare current candle range to ATR
        if snapshot.candles:
            latest = snapshot.candles[-1]
            candle_range = latest.high - latest.low
            atr_ratio = candle_range / snapshot.atr if snapshot.atr > 0 else 0

            if atr_ratio < self.min_atr_multiplier:
                return FilterResult(
                    passed=False,
                    filter_name=self.name,
                    reason=f"Volatility too low: range/ATR = {atr_ratio:.2f} < {self.min_atr_multiplier}",
                    details={"atr_ratio": atr_ratio},
                )

            if atr_ratio > self.max_atr_multiplier:
                return FilterResult(
                    passed=False,
                    filter_name=self.name,
                    reason=f"Volatility too high: range/ATR = {atr_ratio:.2f} > {self.max_atr_multiplier}",
                    details={"atr_ratio": atr_ratio},
                )

        return FilterResult(passed=True, filter_name=self.name)
