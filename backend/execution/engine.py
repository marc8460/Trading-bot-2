"""
PropOS — Execution Engine

Receives routed orders and submits them to MT5.
Handles the 1-to-many execution pattern (trade copier).
"""

from __future__ import annotations

import asyncio

from backend.core.events import Event, EventType, get_event_bus
from backend.core.logging import get_logger
from backend.core.state import get_state
from backend.models.order import Order, OrderStatus, TradeState
from backend.router.engine import RoutingDecision

logger = get_logger(__name__)


class ExecutionEngine:
    """
    Executes routed orders on MT5 terminals.

    Supports:
    - Sequential execution (safer, slower)
    - Concurrent execution (faster, requires careful error handling)
    - Retry logic for transient failures
    """

    def __init__(self, max_retries: int = 2, retry_delay_seconds: float = 1.0) -> None:
        self.max_retries = max_retries
        self.retry_delay = retry_delay_seconds
        self._mt5_executors: dict[str, "MT5Executor"] = {}

    def register_executor(self, account_id: str, executor: "MT5Executor") -> None:
        """Register an MT5 executor for a specific account."""
        self._mt5_executors[account_id] = executor

    async def execute_routing(self, decision: RoutingDecision) -> list[Order]:
        """
        Execute all orders from a routing decision.

        Uses sequential execution per account to avoid race conditions
        on the MT5 terminal connection.
        """
        results: list[Order] = []
        bus = get_event_bus()
        state = get_state()

        for order in decision.orders:
            executed_order = await self._execute_single(order)
            results.append(executed_order)

            # Update global state
            if executed_order.status == OrderStatus.FILLED:
                account_state = await state.get_account(order.account_id)
                account_state.open_positions += 1
                account_state.trades_today += 1
                state.total_trades_today += 1
                state.total_open_positions += 1

        return results

    async def _execute_single(self, order: Order) -> Order:
        """Execute a single order with retry logic."""
        bus = get_event_bus()

        for attempt in range(self.max_retries + 1):
            try:
                executor = self._mt5_executors.get(order.account_id)
                if executor is None:
                    order.status = OrderStatus.FAILED
                    order.state = TradeState.FAILED
                    order.rejection_reason = f"No executor registered for account {order.account_id}"
                    logger.error("No executor for account", account_id=order.account_id)
                    break

                # Submit to MT5
                order.state = TradeState.SUBMITTED
                order.status = OrderStatus.SUBMITTED

                await bus.publish(Event(
                    type=EventType.TRADE_SUBMITTED,
                    data={
                        "order_id": order.id,
                        "account_id": order.account_id,
                        "symbol": order.symbol,
                        "volume": order.volume,
                        "attempt": attempt + 1,
                    },
                    source="execution_engine",
                ))

                result = await executor.submit_order(order)

                if result.status == OrderStatus.FILLED:
                    order.status = OrderStatus.FILLED
                    order.state = TradeState.FILLED
                    order.mt5_ticket = result.mt5_ticket
                    order.mt5_retcode = result.mt5_retcode

                    await bus.publish(Event(
                        type=EventType.TRADE_FILLED,
                        data={
                            "order_id": order.id,
                            "account_id": order.account_id,
                            "symbol": order.symbol,
                            "volume": order.volume,
                            "mt5_ticket": order.mt5_ticket,
                        },
                        source="execution_engine",
                    ))

                    logger.info(
                        "Order filled",
                        order_id=order.id,
                        account_id=order.account_id,
                        ticket=order.mt5_ticket,
                    )
                    break

                else:
                    if attempt < self.max_retries:
                        logger.warning(
                            "Order failed, retrying",
                            order_id=order.id,
                            attempt=attempt + 1,
                            retcode=result.mt5_retcode,
                        )
                        await asyncio.sleep(self.retry_delay)
                    else:
                        order.status = OrderStatus.FAILED
                        order.state = TradeState.FAILED
                        order.rejection_reason = f"MT5 error after {self.max_retries + 1} attempts"

            except Exception as e:
                logger.error("Execution error", order_id=order.id, error=str(e))
                if attempt >= self.max_retries:
                    order.status = OrderStatus.FAILED
                    order.state = TradeState.FAILED
                    order.rejection_reason = str(e)

                    await bus.publish(Event(
                        type=EventType.TRADE_FAILED,
                        data={
                            "order_id": order.id,
                            "account_id": order.account_id,
                            "error": str(e),
                        },
                        source="execution_engine",
                    ))

        return order
