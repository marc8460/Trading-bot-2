"""
PropOS — Compliance Domain Models

Represents prop firm compliance profiles, validation results,
and per-account compliance state tracking.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class NewsRestrictionConfig(BaseModel):
    """News trading restriction configuration."""
    enabled: bool = False
    minutes_before: int = 15
    minutes_after: int = 15
    affected_currencies: list[str] = Field(default_factory=list)


class SoftLimits(BaseModel):
    """Warning thresholds before hard prop firm limits."""
    daily_drawdown_warning_pct: float = 3.5
    total_drawdown_warning_pct: float = 7.0
    daily_loss_auto_stop_pct: float = 4.0


class PhaseOverride(BaseModel):
    """Phase-specific rule overrides."""
    profit_target_pct: float | None = None
    min_trading_days: int | None = None
    max_trading_days: int | None = None
    profit_split_pct: float | None = None


class FirmProfile(BaseModel):
    """
    Complete compliance profile for a prop trading firm.

    Loaded from config/firms/{slug}.yaml.
    All rules are configurable; nothing is hardcoded.
    """

    name: str
    slug: str

    # Hard rules
    max_daily_drawdown_pct: float = 5.0
    max_total_drawdown_pct: float = 10.0
    daily_drawdown_type: str = "balance"  # balance | equity
    daily_drawdown_reset_timezone: str = "UTC"
    profit_target_pct: float = 10.0
    max_positions: int = 10
    weekend_holding_allowed: bool = False
    hedging_allowed: bool = False
    min_holding_time_seconds: int = 0
    max_lot_size: float = 100.0
    news_restriction: NewsRestrictionConfig = Field(
        default_factory=NewsRestrictionConfig
    )
    ea_trading_allowed: bool = True
    copy_trading_allowed: bool = True
    martingale_allowed: bool = False

    # Soft limits (warning/auto-stop before hard limits)
    soft_limits: SoftLimits = Field(default_factory=SoftLimits)

    # Phase-specific overrides
    phase_overrides: dict[str, PhaseOverride] = Field(default_factory=dict)


class ComplianceResult(BaseModel):
    """Result of compliance validation for a single account."""

    approved: bool = False
    account_id: str = ""
    firm: str = ""
    signal_id: str = ""

    # Violation details
    violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Drawdown state at check time
    current_daily_drawdown_pct: float = 0.0
    current_total_drawdown_pct: float = 0.0
    projected_daily_drawdown_pct: float = 0.0  # If this trade loses

    # Auto-stop
    should_auto_stop: bool = False
    auto_stop_reason: str = ""


class ComplianceState(BaseModel):
    """
    Per-account compliance tracking state.

    Updated in real-time as trades are executed and P/L changes.
    """

    account_id: str
    firm: str

    # Balance tracking
    start_of_day_balance: float = 0.0
    start_of_day_equity: float = 0.0
    initial_balance: float = 0.0  # Account starting balance
    current_balance: float = 0.0
    current_equity: float = 0.0

    # Drawdown
    daily_pnl: float = 0.0
    daily_drawdown_pct: float = 0.0
    total_drawdown_pct: float = 0.0
    max_equity_reached: float = 0.0

    # Trading stats
    trades_today: int = 0
    trading_days: int = 0
    open_positions: int = 0

    # Auto-stop
    is_auto_stopped: bool = False
    auto_stop_reason: str = ""

    # Timestamps
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    daily_reset_time: datetime | None = None
