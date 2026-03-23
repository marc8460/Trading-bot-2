"""
PropOS — Market Data Models

Represents candles, ticks, and market state snapshots
from MT5 or other data providers.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Tick(BaseModel):
    """A single price tick."""
    symbol: str
    bid: float
    ask: float
    last: float = 0.0
    volume: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def spread(self) -> float:
        """Spread in price units."""
        return self.ask - self.bid

    @property
    def spread_points(self) -> float:
        """Spread in points (assuming 5-digit pricing for forex)."""
        if "XAU" in self.symbol or "GOLD" in self.symbol:
            return self.spread * 100  # Gold: 1 point = 0.01
        return self.spread * 100_000  # Forex: 1 point = 0.00001

    @property
    def mid(self) -> float:
        """Mid price."""
        return (self.bid + self.ask) / 2


class Candle(BaseModel):
    """A single OHLCV candle."""
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    tick_volume: int = 0
    spread: int = 0
    timestamp: datetime

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low


class MarketSnapshot(BaseModel):
    """
    A snapshot of current market conditions for a symbol.

    Used by filters and strategy engine to make decisions.
    """

    symbol: str
    tick: Tick | None = None
    candles: list[Candle] = Field(default_factory=list)

    # Derived indicators (computed by market data layer)
    atr: float = 0.0
    atr_period: int = 14
    current_spread_points: float = 0.0
    avg_spread_points: float = 0.0
    daily_range: float = 0.0

    # Session info
    current_session: str = ""  # "London", "New York", "Asian", "Off"
    is_session_active: bool = False

    # News
    upcoming_news_minutes: int | None = None  # Minutes until next high-impact news
    news_currency_affected: list[str] = Field(default_factory=list)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
