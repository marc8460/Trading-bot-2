"""
PropOS — Breakout Strategy

Identifies consolidation zones and trades breakouts with
volume/momentum confirmation.
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


class BreakoutStrategy(BaseStrategy):
    """
    Breakout strategy for trending symbols.

    Logic:
    1. Identify consolidation range (N-candle high/low channel)
    2. Wait for price to break above/below the range
    3. Confirm with ATR expansion (volatility breakout)
    4. Enter on breakout candle close
    5. SL inside the range, TP at range width extension

    Parameters:
        lookback_period: Candles for range calculation (default: 20)
        atr_breakout_multiplier: ATR expansion threshold (default: 1.2)
        range_sl_offset: SL offset into range as % (default: 0.25)
        tp_range_multiplier: TP as multiple of range width (default: 1.5)
        min_candles: Minimum candles required (default: 30)
    """

    def __init__(self, **params: Any) -> None:
        defaults = {
            "lookback_period": 20,
            "atr_breakout_multiplier": 1.2,
            "range_sl_offset": 0.25,
            "tp_range_multiplier": 1.5,
            "min_candles": 30,
        }
        defaults.update(params)
        super().__init__(name="breakout", version="1.0.0", **defaults)

    async def on_init(self) -> None:
        logger.info("Breakout strategy initialized", params=self.params)

    async def evaluate(self, snapshot: MarketSnapshot) -> TradeSignal:
        """Evaluate for breakout opportunities."""
        symbol = snapshot.symbol
        candles = snapshot.candles

        no_trade = TradeSignal(
            id=str(uuid.uuid4()),
            symbol=symbol,
            direction=SignalDirection.NO_TRADE,
            strategy=self.name,
        )

        min_candles = self.params.get("min_candles", 30)
        if len(candles) < min_candles:
            return no_trade

        df = pd.DataFrame([c.model_dump() for c in candles])
        lookback = self.params["lookback_period"]

        # Calculate range
        range_high = df["high"].rolling(lookback).max()
        range_low = df["low"].rolling(lookback).min()

        # ATR for breakout confirmation
        tr = pd.concat([
            df["high"] - df["low"],
            abs(df["high"] - df["close"].shift(1)),
            abs(df["low"] - df["close"].shift(1)),
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        latest = df.iloc[-1]
        prev_high = range_high.iloc[-2]
        prev_low = range_low.iloc[-2]
        current_atr = atr.iloc[-1]
        prev_atr = atr.iloc[-2]

        if current_atr == 0 or prev_atr == 0:
            return no_trade

        # Check for ATR expansion (volatility breakout)
        atr_ratio = current_atr / prev_atr
        atr_threshold = self.params["atr_breakout_multiplier"]

        range_width = prev_high - prev_low
        close = latest["close"]

        direction = SignalDirection.NO_TRADE
        entry_price = close
        stop_loss = 0.0
        take_profit = 0.0

        offset = range_width * self.params["range_sl_offset"]
        tp_mult = self.params["tp_range_multiplier"]

        if close > prev_high and atr_ratio >= atr_threshold:
            direction = SignalDirection.LONG
            stop_loss = prev_high - offset
            take_profit = entry_price + (range_width * tp_mult)

        elif close < prev_low and atr_ratio >= atr_threshold:
            direction = SignalDirection.SHORT
            stop_loss = prev_low + offset
            take_profit = entry_price - (range_width * tp_mult)

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
            confidence=0.6,
            metadata={
                "range_high": round(prev_high, 5),
                "range_low": round(prev_low, 5),
                "range_width": round(range_width, 5),
                "atr_ratio": round(atr_ratio, 2),
            },
        )
