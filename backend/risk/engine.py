"""
PropOS — Risk Engine

Evaluates risk for a trade signal per account:
- Position sizing (lot calculation)
- Daily trade limits
- Max open positions
- Daily loss limits
- Exposure/correlation checks
"""

from __future__ import annotations

from backend.core.events import Event, EventType, get_event_bus
from backend.core.logging import get_logger
from backend.core.state import get_state
from backend.models.account import AccountConfig
from backend.models.risk import PositionSizing, RiskAssessment, RiskProfile
from backend.models.signal import TradeSignal

logger = get_logger(__name__)


class RiskEngine:
    """
    Evaluates whether a trade is acceptable for a given account
    and calculates the appropriate position size.
    """

    def __init__(
        self,
        default_risk_pct: float = 1.0,
        max_daily_trades: int = 5,
        max_open_positions: int = 3,
        symbol_profiles: dict[str, RiskProfile] | None = None,
    ) -> None:
        self.default_risk_pct = default_risk_pct
        self.max_daily_trades = max_daily_trades
        self.max_open_positions = max_open_positions
        self.symbol_profiles = symbol_profiles or {}

    async def evaluate(
        self,
        signal: TradeSignal,
        account: AccountConfig,
    ) -> RiskAssessment:
        """
        Evaluate risk for a signal on a specific account.

        Returns a RiskAssessment with approval decision and position sizing.
        """
        state = get_state()
        account_state = await state.get_account(account.id)
        bus = get_event_bus()

        assessment = RiskAssessment(
            account_id=account.id,
            signal_id=signal.id,
            daily_trades_used=account_state.trades_today,
            daily_trades_limit=self.max_daily_trades,
            open_positions=account_state.open_positions,
            max_positions=self.max_open_positions,
        )

        # --- Check 1: Daily trade limit ---
        if account_state.trades_today >= self.max_daily_trades:
            assessment.rejection_reasons.append(
                f"Daily trade limit reached: {account_state.trades_today}/{self.max_daily_trades}"
            )

        # --- Check 2: Max open positions ---
        if account_state.open_positions >= self.max_open_positions:
            assessment.rejection_reasons.append(
                f"Max positions reached: {account_state.open_positions}/{self.max_open_positions}"
            )

        # --- Check 3: Account auto-stopped ---
        if account_state.is_auto_stopped:
            assessment.rejection_reasons.append("Account is auto-stopped due to daily loss limit")

        # --- Check 4: Symbol allowed ---
        if signal.symbol not in account.symbols_allowed:
            assessment.rejection_reasons.append(
                f"Symbol {signal.symbol} not allowed for account {account.id}"
            )

        # --- Calculate position size ---
        if not assessment.rejection_reasons:
            sizing = self._calculate_position_size(signal, account)
            if sizing.lot_size <= 0:
                assessment.rejection_reasons.append("Calculated lot size is 0")
            else:
                assessment.position_sizing = sizing

        # Final decision
        assessment.approved = len(assessment.rejection_reasons) == 0

        # Publish event
        if assessment.approved:
            await bus.publish(Event(
                type=EventType.RISK_APPROVED,
                data={
                    "signal_id": signal.id,
                    "account_id": account.id,
                    "lot_size": assessment.lot_size,
                },
                source="risk_engine",
            ))
        else:
            await bus.publish(Event(
                type=EventType.RISK_REJECTED,
                data={
                    "signal_id": signal.id,
                    "account_id": account.id,
                    "reasons": assessment.rejection_reasons,
                },
                source="risk_engine",
            ))

        return assessment

    def _calculate_position_size(
        self,
        signal: TradeSignal,
        account: AccountConfig,
    ) -> PositionSizing:
        """Calculate lot size based on risk percentage and stop loss distance."""
        risk_pct = self.default_risk_pct * account.risk_multiplier
        sl_distance = signal.risk_distance_points

        if sl_distance <= 0:
            return PositionSizing(
                symbol=signal.symbol,
                account_id=account.id,
                lot_size=0.0,
                risk_amount=0.0,
                risk_pct=risk_pct,
                stop_loss_distance=0.0,
            )

        risk_amount = account.balance * (risk_pct / 100.0)

        # Pip value estimation (simplified for forex)
        # For precise calculation, MT5 symbol info should be used
        pip_value = self._estimate_pip_value(signal.symbol)
        sl_pips = sl_distance / self._point_size(signal.symbol) / 10  # Convert to pips

        if sl_pips <= 0 or pip_value <= 0:
            lot_size = 0.0
        else:
            lot_size = risk_amount / (sl_pips * pip_value)

        # Clamp to symbol limits
        profile = self.symbol_profiles.get(signal.symbol)
        if profile:
            lot_size = max(profile.min_lot_size, min(lot_size, profile.max_lot_size))
        else:
            lot_size = max(0.01, min(lot_size, 10.0))

        # Round to 2 decimal places (MT5 standard)
        lot_size = round(lot_size, 2)

        return PositionSizing(
            symbol=signal.symbol,
            account_id=account.id,
            lot_size=lot_size,
            risk_amount=risk_amount,
            risk_pct=risk_pct,
            stop_loss_distance=sl_distance,
            pip_value=pip_value,
        )

    @staticmethod
    def _estimate_pip_value(symbol: str) -> float:
        """Estimate pip value per standard lot. Simplified for MVP."""
        pip_values = {
            "EURUSD": 10.0,
            "GBPUSD": 10.0,
            "XAUUSD": 1.0,  # Gold: $1 per pip per 1 lot (0.01 move)
        }
        return pip_values.get(symbol, 10.0)

    @staticmethod
    def _point_size(symbol: str) -> float:
        """Get point size for a symbol."""
        if "XAU" in symbol or "GOLD" in symbol:
            return 0.01  # Gold
        return 0.00001  # Forex 5-digit
