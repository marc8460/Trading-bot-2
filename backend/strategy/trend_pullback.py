"""
PropOS — Trend Pullback Strategy

Core strategy for EURUSD. Identifies trends using moving averages
and enters on pullbacks to dynamic support/resistance.
"""

from __future__ import annotations

import uuid
from typing import Any

import pandas as pd

from backend.core.logging import get_logger
from backend.models.market import MarketSnapshot
from backend.models.signal import SignalDirection, TradeSignal
from backend.strategy.base import BaseStrategy

logger = get_logger(__name__)


class TrendPullbackStrategy(BaseStrategy):
    """
    Trend-following pullback strategy.

    Logic:
    1. Identify trend using EMA crossover (fast EMA > slow EMA = uptrend)
    2. Wait for price to pull back to the fast EMA zone
    3. Enter on confirmation candle (bullish in uptrend, bearish in downtrend)
    4. SL below recent swing low/high
    5. TP at configurable R:R ratio

    Parameters (via config):
        fast_ema_period: Fast EMA period (default: 20)
        slow_ema_period: Slow EMA period (default: 50)
        atr_sl_multiplier: ATR multiplier for stop loss (default: 1.5)
        rr_ratio: Risk-to-reward ratio (default: 2.0)
        min_candles: Minimum candles needed for evaluation (default: 60)
    """

    def __init__(self, **params: Any) -> None:
        defaults = {
            "fast_ema_period": 20,
            "slow_ema_period": 50,
            "atr_sl_multiplier": 1.5,
            "rr_ratio": 2.0,
            "min_candles": 60,
        }
        defaults.update(params)
        super().__init__(name="trend_pullback", version="1.0.0", **defaults)

    async def on_init(self) -> None:
        """Initialize strategy state."""
        logger.info("Trend Pullback strategy initialized", params=self.params)

    async def evaluate(self, snapshot: MarketSnapshot) -> TradeSignal:
        """Evaluate market conditions for a trend pullback setup."""
        symbol = snapshot.symbol
        candles = snapshot.candles

        # Default: no trade
        no_trade = TradeSignal(
            id=str(uuid.uuid4()),
            symbol=symbol,
            direction=SignalDirection.NO_TRADE,
            strategy=self.name,
        )

        # Need enough candles
        min_candles = self.params.get("min_candles", 60)
        if len(candles) < min_candles:
            return no_trade

        # Build DataFrame for indicator calculation
        df = pd.DataFrame([c.model_dump() for c in candles])
        fast_period = self.params["fast_ema_period"]
        slow_period = self.params["slow_ema_period"]

        df["ema_fast"] = df["close"].ewm(span=fast_period, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=slow_period, adjust=False).mean()
        df["atr"] = self._calculate_atr(df, period=14)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        ema_fast = latest["ema_fast"]
        ema_slow = latest["ema_slow"]
        atr = latest["atr"]
        close = latest["close"]

        if atr == 0:
            return no_trade

        # Determine trend
        is_uptrend = ema_fast > ema_slow
        is_downtrend = ema_fast < ema_slow

        # Check for pullback to fast EMA zone
        pullback_zone = atr * 0.5  # Within half ATR of fast EMA
        near_fast_ema = abs(close - ema_fast) <= pullback_zone

        # Check confirmation candle
        is_bullish_candle = latest["close"] > latest["open"]
        is_bearish_candle = latest["close"] < latest["open"]

        direction = SignalDirection.NO_TRADE
        entry_price = close
        stop_loss = 0.0
        take_profit = 0.0

        sl_distance = atr * self.params["atr_sl_multiplier"]
        rr = self.params["rr_ratio"]

        if is_uptrend and near_fast_ema and is_bullish_candle:
            direction = SignalDirection.LONG
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + (sl_distance * rr)

        elif is_downtrend and near_fast_ema and is_bearish_candle:
            direction = SignalDirection.SHORT
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - (sl_distance * rr)

        if direction == SignalDirection.NO_TRADE:
            return no_trade

        return TradeSignal(
            id=str(uuid.uuid4()),
            symbol=symbol,
            direction=direction,
            strategy=self.name,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=0.65,
            metadata={
                "ema_fast": round(ema_fast, 5),
                "ema_slow": round(ema_slow, 5),
                "atr": round(atr, 5),
                "trend": "up" if is_uptrend else "down",
            },
        )

    @staticmethod
    def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr.fillna(0)
