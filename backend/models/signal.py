"""
PropOS — Trade Signal Models

Represents strategy output signals before routing and execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SignalDirection(str, Enum):
    """Trade direction."""
    LONG = "long"
    SHORT = "short"
    NO_TRADE = "no_trade"


class TradeSignal(BaseModel):
    """
    A trading signal produced by the strategy engine.

    This is the output of strategy evaluation, before any filtering,
    risk checks, or compliance validation.
    """

    id: str = Field(..., description="Unique signal ID (UUID)")
    symbol: str = Field(..., description="Trading symbol, e.g. 'EURUSD'")
    direction: SignalDirection = Field(..., description="Signal direction")
    strategy: str = Field(..., description="Strategy that generated this signal")
    timeframe: str = Field("M15", description="Candle timeframe")

    # Price context
    entry_price: float = Field(0.0, description="Suggested entry price")
    stop_loss: float = Field(0.0, description="Suggested stop loss price")
    take_profit: float = Field(0.0, description="Suggested take profit price")

    # Signal quality
    confidence: float = Field(
        0.5, ge=0.0, le=1.0, description="Signal confidence score 0-1"
    )

    # Timing
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the signal was generated",
    )

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy-specific metadata (indicators, reasoning)",
    )

    @property
    def is_actionable(self) -> bool:
        """Whether this signal requires trade execution."""
        return self.direction != SignalDirection.NO_TRADE

    @property
    def risk_distance_points(self) -> float:
        """Distance from entry to stop loss in price units."""
        if self.entry_price and self.stop_loss:
            return abs(self.entry_price - self.stop_loss)
        return 0.0
