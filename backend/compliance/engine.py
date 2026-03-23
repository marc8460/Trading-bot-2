"""
PropOS — Compliance Engine

Validates trades against prop firm-specific rules.
Each account has an associated FirmProfile loaded from YAML.
The engine checks drawdown limits, position limits, news restrictions,
and soft-limit auto-stops.
"""

from __future__ import annotations

from backend.core.config import load_firm_profile
from backend.core.events import Event, EventType, get_event_bus
from backend.core.logging import get_logger
from backend.core.state import get_state
from backend.models.account import AccountConfig
from backend.models.compliance import ComplianceResult, ComplianceState, FirmProfile
from backend.models.signal import TradeSignal

logger = get_logger(__name__)


class ComplianceEngine:
    """
    Validates trade signals against prop firm compliance rules.

    Loads firm profiles from YAML config and maintains per-account
    compliance state for real-time drawdown tracking.
    """

    def __init__(self) -> None:
        self._profiles: dict[str, FirmProfile] = {}
        self._account_states: dict[str, ComplianceState] = {}

    def load_profile(self, firm_slug: str) -> FirmProfile:
        """Load and cache a firm profile from config."""
        if firm_slug not in self._profiles:
            data = load_firm_profile(firm_slug)
            rules = data.get("rules", {})
            soft = data.get("soft_limits", {})
            phases = data.get("phase_overrides", {})

            from backend.models.compliance import (
                NewsRestrictionConfig,
                PhaseOverride,
                SoftLimits,
            )

            profile = FirmProfile(
                name=data.get("name", firm_slug),
                slug=firm_slug,
                max_daily_drawdown_pct=rules.get("max_daily_drawdown_pct", 5.0),
                max_total_drawdown_pct=rules.get("max_total_drawdown_pct", 10.0),
                daily_drawdown_type=rules.get("daily_drawdown_type", "balance"),
                daily_drawdown_reset_timezone=rules.get("daily_drawdown_reset_timezone", "UTC"),
                profit_target_pct=rules.get("profit_target_pct", 10.0),
                max_positions=rules.get("max_positions", 10),
                weekend_holding_allowed=rules.get("weekend_holding_allowed", False),
                hedging_allowed=rules.get("hedging_allowed", False),
                min_holding_time_seconds=rules.get("min_holding_time_seconds", 0),
                max_lot_size=rules.get("max_lot_size", 100.0),
                news_restriction=NewsRestrictionConfig(**rules.get("news_restriction", {})),
                soft_limits=SoftLimits(**soft),
                phase_overrides={k: PhaseOverride(**v) for k, v in phases.items()},
            )
            self._profiles[firm_slug] = profile
        return self._profiles[firm_slug]

    async def validate(
        self,
        signal: TradeSignal,
        account: AccountConfig,
        lot_size: float,
    ) -> ComplianceResult:
        """
        Validate a trade against the account's firm compliance rules.

        Args:
            signal: The trade signal.
            account: The target account.
            lot_size: Calculated lot size from risk engine.

        Returns:
            ComplianceResult with approval decision and violations.
        """
        profile = self.load_profile(account.firm)
        state = await self._get_account_state(account)
        bus = get_event_bus()

        result = ComplianceResult(
            account_id=account.id,
            firm=account.firm,
            signal_id=signal.id,
            current_daily_drawdown_pct=state.daily_drawdown_pct,
            current_total_drawdown_pct=state.total_drawdown_pct,
        )

        # --- Check 1: Daily drawdown soft limit (auto-stop) ---
        if state.daily_drawdown_pct >= profile.soft_limits.daily_loss_auto_stop_pct:
            result.should_auto_stop = True
            result.auto_stop_reason = (
                f"Daily drawdown {state.daily_drawdown_pct:.1f}% >= "
                f"auto-stop at {profile.soft_limits.daily_loss_auto_stop_pct:.1f}%"
            )
            result.violations.append(result.auto_stop_reason)

        # --- Check 2: Daily drawdown hard limit proximity ---
        remaining_dd = profile.max_daily_drawdown_pct - state.daily_drawdown_pct
        if remaining_dd <= 0.5:  # Within 0.5% of hard limit
            result.violations.append(
                f"Too close to daily drawdown limit: "
                f"{state.daily_drawdown_pct:.1f}% / {profile.max_daily_drawdown_pct:.1f}%"
            )

        # --- Check 3: Total drawdown ---
        if state.total_drawdown_pct >= profile.soft_limits.total_drawdown_warning_pct:
            result.warnings.append(
                f"Total drawdown warning: {state.total_drawdown_pct:.1f}% "
                f"(limit: {profile.max_total_drawdown_pct:.1f}%)"
            )

        total_remaining = profile.max_total_drawdown_pct - state.total_drawdown_pct
        if total_remaining <= 1.0:
            result.violations.append(
                f"Too close to total drawdown limit: "
                f"{state.total_drawdown_pct:.1f}% / {profile.max_total_drawdown_pct:.1f}%"
            )

        # --- Check 4: Max positions ---
        if state.open_positions >= profile.max_positions:
            result.violations.append(
                f"Max positions reached: {state.open_positions}/{profile.max_positions}"
            )

        # --- Check 5: Lot size limit ---
        if lot_size > profile.max_lot_size:
            result.violations.append(
                f"Lot size {lot_size} exceeds firm max {profile.max_lot_size}"
            )

        # --- Check 6: Account auto-stopped ---
        if state.is_auto_stopped:
            result.violations.append(f"Account auto-stopped: {state.auto_stop_reason}")

        # Final decision
        result.approved = len(result.violations) == 0

        # Publish events
        event_type = EventType.COMPLIANCE_APPROVED if result.approved else EventType.COMPLIANCE_REJECTED
        await bus.publish(Event(
            type=event_type,
            data={
                "signal_id": signal.id,
                "account_id": account.id,
                "firm": account.firm,
                "violations": result.violations,
                "warnings": result.warnings,
            },
            source="compliance_engine",
        ))

        if result.warnings:
            await bus.publish(Event(
                type=EventType.COMPLIANCE_WARNING,
                data={
                    "account_id": account.id,
                    "warnings": result.warnings,
                },
                source="compliance_engine",
            ))

        return result

    async def _get_account_state(self, account: AccountConfig) -> ComplianceState:
        """Get or initialize compliance state for an account."""
        if account.id not in self._account_states:
            self._account_states[account.id] = ComplianceState(
                account_id=account.id,
                firm=account.firm,
                initial_balance=account.balance,
                current_balance=account.balance,
                current_equity=account.balance,
                start_of_day_balance=account.balance,
                start_of_day_equity=account.balance,
                max_equity_reached=account.balance,
            )
        return self._account_states[account.id]

    async def update_account_state(
        self,
        account_id: str,
        balance: float,
        equity: float,
        open_positions: int,
    ) -> None:
        """Update compliance state with latest account data from MT5."""
        if account_id in self._account_states:
            state = self._account_states[account_id]
            state.current_balance = balance
            state.current_equity = equity
            state.open_positions = open_positions

            # Update drawdown calculations
            if state.start_of_day_balance > 0:
                daily_loss = state.start_of_day_balance - equity
                state.daily_pnl = -daily_loss
                state.daily_drawdown_pct = (daily_loss / state.start_of_day_balance) * 100

            if state.max_equity_reached > 0:
                total_loss = state.max_equity_reached - equity
                state.total_drawdown_pct = (total_loss / state.max_equity_reached) * 100

            # Track max equity
            if equity > state.max_equity_reached:
                state.max_equity_reached = equity
