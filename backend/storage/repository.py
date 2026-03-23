"""
PropOS — Repository Layer

Handles database persistence for trades, signals, and system events.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.models.order import Order, OrderStatus, TradeResult
from backend.models.signal import TradeSignal
from backend.storage.database import get_session_factory
from backend.storage.models import DailyPerformance, SystemLog, TradeRecord

logger = get_logger(__name__)


class TradeRepository:
    """Repository for database operations."""

    def __init__(self) -> None:
        self.session_factory = get_session_factory()

    async def save_signal(self, signal: TradeSignal) -> None:
        """Save a trade signal intent as a system log."""
        async with self.session_factory() as session:
            log = SystemLog(
                level="INFO",
                source="strategy_engine",
                message=f"Signal generated: {signal.direction.value} {signal.symbol}",
                data=signal.model_dump_json(),
            )
            session.add(log)
            await session.commit()

    async def save_order(self, order: Order) -> None:
        """Upsert an order record to the database."""
        async with self.session_factory() as session:
            # Check if exists
            stmt = select(TradeRecord).where(TradeRecord.id == order.id)
            result = await session.execute(stmt)
            record = result.scalars().first()

            if not record:
                record = TradeRecord(
                    id=order.id,
                    signal_id=order.signal_id,
                    account_id=order.account_id,
                    symbol=order.symbol,
                    direction=order.order_type.value,
                    volume=order.volume,
                    open_price=order.price,
                    stop_loss=order.stop_loss,
                    take_profit=order.take_profit,
                    mt5_ticket=order.mt5_ticket,
                    status=order.status.value,
                    opened_at=order.created_at,
                )
                session.add(record)
            else:
                record.status = order.status.value
                record.mt5_ticket = order.mt5_ticket

            await session.commit()

    async def save_trade_result(self, result: TradeResult) -> None:
        """Save a closed trade result."""
        async with self.session_factory() as session:
            stmt = select(TradeRecord).where(TradeRecord.id == result.order_id)
            exec_result = await session.execute(stmt)
            record = exec_result.scalars().first()

            if record:
                record.close_price = result.close_price
                record.realized_pnl = result.realized_pnl
                record.swap = result.swap
                record.commission = result.commission
                record.close_reason = result.close_reason
                record.closed_at = result.closed_at
                record.status = "closed"
                await session.commit()

    async def log_event(self, level: str, source: str, message: str, data: dict[str, Any] | None = None) -> None:
        """Save a system event/log."""
        async with self.session_factory() as session:
            log = SystemLog(
                level=level,
                source=source,
                message=message,
                data=json.dumps(data) if data else None,
            )
            session.add(log)
            await session.commit()

    async def get_trades_today(self, account_id: str) -> int:
        """Get number of trades opened today for an account."""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        async with self.session_factory() as session:
            stmt = select(TradeRecord).where(
                TradeRecord.account_id == account_id,
                TradeRecord.opened_at >= today
            )
            result = await session.execute(stmt)
            return len(result.scalars().all())

    async def save_daily_performance(self, account_id: str, date_str: str, pnl: float, trades: int) -> None:
        """Save end-of-day performance snapshot."""
        async with self.session_factory() as session:
            perf = DailyPerformance(
                account_id=account_id,
                date=date_str,
                starting_balance=0.0,  # Will be populated from sync
                ending_balance=0.0,
                pnl=pnl,
                trades_count=trades,
            )
            session.add(perf)
            await session.commit()
