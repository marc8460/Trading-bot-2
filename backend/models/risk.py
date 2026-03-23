"""
PropOS — Risk Domain Models

Represents risk profiles, assessments, and position sizing results.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RiskProfile(BaseModel):
    """Per-symbol risk profile configuration."""

    symbol: str
    max_spread_points: int = 20
    max_lot_size: float = 10.0
    min_lot_size: float = 0.01
    max_risk_per_trade_pct: float = 2.0
    default_risk_pct: float = 1.0


class PositionSizing(BaseModel):
    """Result of lot size calculation."""

    symbol: str
    account_id: str
    lot_size: float = Field(..., ge=0.0)
    risk_amount: float = Field(..., description="Dollar risk for this trade")
    risk_pct: float = Field(..., description="Risk as % of account balance")
    stop_loss_distance: float = Field(..., description="SL distance in price units")
    pip_value: float = Field(0.0, description="Value per pip for this symbol/lot")


class RiskAssessment(BaseModel):
    """
    Result of the risk engine evaluating a signal for an account.

    Contains the go/no-go decision and the calculated position size.
    """

    approved: bool = False
    account_id: str = ""
    signal_id: str = ""

    # Sizing
    position_sizing: PositionSizing | None = None

    # Reasons
    rejection_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Context
    daily_trades_used: int = 0
    daily_trades_limit: int = 0
    open_positions: int = 0
    max_positions: int = 0
    exposure_pct: float = 0.0

    @property
    def lot_size(self) -> float:
        if self.position_sizing:
            return self.position_sizing.lot_size
        return 0.0
