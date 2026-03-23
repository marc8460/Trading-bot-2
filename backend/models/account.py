"""
PropOS — Account Domain Models

Represents MT5 trading accounts, their prop firm associations,
and account grouping for routing decisions.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AccountPhase(str, Enum):
    """Prop firm account lifecycle phase."""
    EVALUATION = "evaluation"
    VERIFICATION = "verification"
    FUNDED = "funded"
    EXPRESS = "express"  # FundedNext express model


class AccountConfig(BaseModel):
    """
    Configuration for a single trading account.

    This maps to one MT5 terminal connection and one prop firm profile.
    """

    # Identity
    id: str = Field(..., description="Unique internal account ID")
    name: str = Field("", description="Human-readable account name")

    # MT5 connection (credential index maps to .env vars)
    mt5_credential_index: int = Field(..., description="Index into MT5_ACCOUNT_{N}_* env vars")

    # Prop firm association
    firm: str = Field(..., description="Firm slug: ftmo, e8, fundednext, the5ers")
    phase: AccountPhase = Field(AccountPhase.EVALUATION, description="Current account phase")

    # Grouping
    group: str = Field("default", description="Account group for routing")

    # Financial
    balance: float = Field(0.0, description="Starting or current account balance")

    # Trading
    enabled: bool = Field(True, description="Whether this account is active for trading")
    risk_multiplier: float = Field(
        1.0,
        ge=0.0,
        le=2.0,
        description="Risk multiplier (1.0 = normal, 0.5 = half risk)",
    )
    symbols_allowed: list[str] = Field(
        default_factory=lambda: ["EURUSD"],
        description="Symbols this account is allowed to trade",
    )

    @property
    def is_evaluation(self) -> bool:
        return self.phase in (AccountPhase.EVALUATION, AccountPhase.VERIFICATION)

    @property
    def is_funded(self) -> bool:
        return self.phase == AccountPhase.FUNDED


class AccountGroup(BaseModel):
    """A logical group of accounts for routing and risk management."""

    name: str
    account_ids: list[str] = Field(default_factory=list)
    max_concurrent_trades: int = Field(10, description="Max trades across the group")
    shared_risk_limit_pct: float = Field(
        0.0, description="If > 0, shared daily drawdown limit for the group"
    )
