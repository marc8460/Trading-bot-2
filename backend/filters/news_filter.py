"""
PropOS — News Filter

Blocks trades near high-impact economic events.
Uses MT5 economic calendar when available, with fallback placeholder.
"""

from __future__ import annotations

from backend.core.logging import get_logger
from backend.filters.base import BaseFilter, FilterResult
from backend.models.market import MarketSnapshot
from backend.models.signal import TradeSignal

logger = get_logger(__name__)


class NewsFilter(BaseFilter):
    """
    Blocks trades around high-impact news events.

    In v1: checks the MarketSnapshot.upcoming_news_minutes field,
    which is populated by the market data layer.

    Future: integrate with Forex Factory scraper or paid API.
    """

    def __init__(
        self,
        minutes_before: int = 15,
        minutes_after: int = 15,
    ) -> None:
        super().__init__(name="news")
        self.minutes_before = minutes_before
        self.minutes_after = minutes_after

    async def check(self, signal: TradeSignal, snapshot: MarketSnapshot) -> FilterResult:
        if not self.enabled:
            return FilterResult(passed=True, filter_name=self.name)

        upcoming = snapshot.upcoming_news_minutes

        if upcoming is None:
            # No news data available — allow trade but warn
            return FilterResult(
                passed=True,
                filter_name=self.name,
                reason="No news data available",
                details={"warning": "news_data_unavailable"},
            )

        # Check if we're in the news blackout window
        if 0 <= upcoming <= self.minutes_before:
            # News is coming soon
            return FilterResult(
                passed=False,
                filter_name=self.name,
                reason=f"High-impact news in {upcoming} minutes (blackout: {self.minutes_before}m before)",
                details={
                    "minutes_to_news": upcoming,
                    "currencies": snapshot.news_currency_affected,
                },
            )

        if upcoming < 0 and abs(upcoming) <= self.minutes_after:
            # News just happened
            return FilterResult(
                passed=False,
                filter_name=self.name,
                reason=f"High-impact news {abs(upcoming)} minutes ago (blackout: {self.minutes_after}m after)",
                details={"minutes_since_news": abs(upcoming)},
            )

        return FilterResult(passed=True, filter_name=self.name)
