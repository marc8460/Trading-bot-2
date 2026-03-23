"""
PropOS — Order & Position Models

Represents orders submitted to MT5, open positions, and trade results.
Tracks the full lifecycle: submitted → filled → active → closed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OrderType(str, Enum):
    """MT5 order types."""
    MARKET_BUY = "market_buy"
    MARKET_SELL = "market_sell"
    LIMIT_BUY = "limit_buy"
    LIMIT_SELL = "limit_sell"
    STOP_BUY = "stop_buy"
    STOP_SELL = "stop_sell"


class OrderStatus(str, Enum):
    """Order lifecycle status."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TradeState(str, Enum):
    """Full trade lifecycle from signal to close."""
    SIGNAL_GENERATED = "signal_generated"
    FILTERS_PASSED = "filters_passed"
    FILTERS_REJECTED = "filters_rejected"
    RISK_APPROVED = "risk_approved"
    RISK_REJECTED = "risk_rejected"
    COMPLIANCE_APPROVED = "compliance_approved"
    COMPLIANCE_REJECTED = "compliance_rejected"
    ROUTED = "routed"
    SUBMITTED = "submitted"
    FILLED = "filled"
    ACTIVE = "active"
    CLOSED = "closed"
    FAILED = "failed"


class Order(BaseModel):
    """An order to be submitted or already submitted to MT5."""

    id: str = Field(..., description="Internal order ID (UUID)")
    signal_id: str = Field(..., description="Source signal ID")
    account_id: str = Field(..., description="Target account ID")

    # Order details
    symbol: str
    order_type: OrderType
    volume: float = Field(..., ge=0.01, description="Lot size")
    price: float = Field(0.0, description="Price (0 for market orders)")
    stop_loss: float = Field(0.0)
    take_profit: float = Field(0.0)

    # Status
    status: OrderStatus = OrderStatus.PENDING
    state: TradeState = TradeState.SIGNAL_GENERATED

    # MT5 tracking
    mt5_ticket: int | None = Field(None, description="MT5 order ticket number")
    mt5_retcode: int | None = Field(None, description="MT5 return code")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    closed_at: datetime | None = None

    # Rejection
    rejection_reason: str = ""

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


class Position(BaseModel):
    """An active open position in MT5."""

    id: str = Field(..., description="Internal position ID")
    account_id: str
    order_id: str = Field(..., description="Originating order ID")

    # Position details
    symbol: str
    direction: str  # "long" or "short"
    volume: float
    open_price: float
    current_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0

    # MT5
    mt5_ticket: int = 0
    mt5_position_id: int = 0

    # P/L
    unrealized_pnl: float = 0.0
    swap: float = 0.0
    commission: float = 0.0

    # Timing
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TradeResult(BaseModel):
    """The final result of a completed trade (position closed)."""

    id: str
    account_id: str
    order_id: str
    signal_id: str

    # Trade details
    symbol: str
    direction: str
    volume: float
    open_price: float
    close_price: float

    # Financial
    realized_pnl: float = 0.0
    swap: float = 0.0
    commission: float = 0.0
    net_pnl: float = 0.0

    # Timing
    opened_at: datetime
    closed_at: datetime
    duration_seconds: int = 0

    # Closing
    close_reason: str = ""  # "sl", "tp", "manual", "kill_switch"
