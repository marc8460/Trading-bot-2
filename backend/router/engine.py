"""
PropOS — Account Router

Decides which accounts receive a trade signal.
Runs risk + compliance checks per account, skips accounts that
fail, and adjusts position sizes per account.

This is NOT naive "copy to all" — each account is individually evaluated.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from backend.compliance.engine import ComplianceEngine
from backend.core.events import Event, EventType, get_event_bus
from backend.core.logging import get_logger
from backend.models.account import AccountConfig
from backend.models.order import Order, OrderType, TradeState
from backend.models.signal import SignalDirection, TradeSignal
from backend.risk.engine import RiskEngine

logger = get_logger(__name__)


@dataclass
class RoutingDecision:
    """Result of routing a signal to accounts."""
    signal_id: str
    orders: list[Order] = field(default_factory=list)
    skipped_accounts: list[dict] = field(default_factory=list)
    total_accounts: int = 0
    routed_accounts: int = 0


class AccountRouter:
    """
    Routes trade signals to qualifying accounts.

    For each enabled account:
    1. Check if symbol is allowed
    2. Run risk engine → get lot size
    3. Run compliance engine → check firm rules
    4. If both pass → create order
    5. If either fails → skip with reason
    """

    def __init__(
        self,
        risk_engine: RiskEngine,
        compliance_engine: ComplianceEngine,
    ) -> None:
        self.risk_engine = risk_engine
        self.compliance_engine = compliance_engine

    async def route(
        self,
        signal: TradeSignal,
        accounts: list[AccountConfig],
    ) -> RoutingDecision:
        """
        Route a signal to all qualifying accounts.

        Returns a RoutingDecision with orders for qualifying accounts
        and skip reasons for disqualified accounts.
        """
        decision = RoutingDecision(
            signal_id=signal.id,
            total_accounts=len(accounts),
        )

        bus = get_event_bus()

        for account in accounts:
            # Skip disabled accounts
            if not account.enabled:
                decision.skipped_accounts.append({
                    "account_id": account.id,
                    "reason": "Account disabled",
                })
                continue

            # Skip if symbol not allowed
            if signal.symbol not in account.symbols_allowed:
                decision.skipped_accounts.append({
                    "account_id": account.id,
                    "reason": f"Symbol {signal.symbol} not allowed",
                })
                continue

            # Risk check
            risk_result = await self.risk_engine.evaluate(signal, account)
            if not risk_result.approved:
                decision.skipped_accounts.append({
                    "account_id": account.id,
                    "reason": f"Risk: {', '.join(risk_result.rejection_reasons)}",
                })
                continue

            # Compliance check
            compliance_result = await self.compliance_engine.validate(
                signal, account, risk_result.lot_size
            )
            if not compliance_result.approved:
                decision.skipped_accounts.append({
                    "account_id": account.id,
                    "reason": f"Compliance: {', '.join(compliance_result.violations)}",
                })
                continue

            # Create order
            order_type = (
                OrderType.MARKET_BUY
                if signal.direction == SignalDirection.LONG
                else OrderType.MARKET_SELL
            )

            order = Order(
                id=str(uuid.uuid4()),
                signal_id=signal.id,
                account_id=account.id,
                symbol=signal.symbol,
                order_type=order_type,
                volume=risk_result.lot_size,
                price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                state=TradeState.ROUTED,
            )

            decision.orders.append(order)
            decision.routed_accounts += 1

            logger.info(
                "Signal routed to account",
                signal_id=signal.id,
                account_id=account.id,
                lot_size=risk_result.lot_size,
                symbol=signal.symbol,
            )

        # Publish routing event
        await bus.publish(Event(
            type=EventType.TRADE_ROUTED,
            data={
                "signal_id": signal.id,
                "routed": decision.routed_accounts,
                "skipped": len(decision.skipped_accounts),
                "total": decision.total_accounts,
            },
            source="account_router",
        ))

        return decision
