"""
PropOS — MT5 Trade Executor

Low-level MT5 order submission for a single account.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.core.logging import get_logger
from backend.models.order import Order, OrderStatus, OrderType

logger = get_logger(__name__)


@dataclass
class MT5OrderResult:
    """Result from MT5 order submission."""
    status: OrderStatus
    mt5_ticket: int | None = None
    mt5_retcode: int | None = None
    error_message: str = ""


class MT5Executor:
    """
    Submits orders to a specific MT5 terminal instance.

    Each MT5Executor is bound to one account/terminal.
    """

    def __init__(self, mt5_login: int, mt5_password: str, mt5_server: str) -> None:
        self._login = mt5_login
        self._password = mt5_password
        self._server = mt5_server
        self._connected = False

    async def connect(self) -> bool:
        """Connect to MT5 terminal for this account."""
        try:
            import MetaTrader5 as mt5

            loop = asyncio.get_event_loop()
            initialized = await loop.run_in_executor(None, mt5.initialize)
            if not initialized:
                return False

            authorized = await loop.run_in_executor(
                None,
                lambda: mt5.login(self._login, self._password, server=self._server),
            )
            self._connected = authorized
            return authorized
        except ImportError:
            logger.warning("MetaTrader5 not available — executor in simulation mode")
            return False

    async def submit_order(self, order: Order) -> MT5OrderResult:
        """Submit an order to MT5."""
        try:
            import MetaTrader5 as mt5

            # Map order type
            mt5_type = {
                OrderType.MARKET_BUY: mt5.ORDER_TYPE_BUY,
                OrderType.MARKET_SELL: mt5.ORDER_TYPE_SELL,
                OrderType.LIMIT_BUY: mt5.ORDER_TYPE_BUY_LIMIT,
                OrderType.LIMIT_SELL: mt5.ORDER_TYPE_SELL_LIMIT,
                OrderType.STOP_BUY: mt5.ORDER_TYPE_BUY_STOP,
                OrderType.STOP_SELL: mt5.ORDER_TYPE_SELL_STOP,
            }.get(order.order_type, mt5.ORDER_TYPE_BUY)

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": order.symbol,
                "volume": order.volume,
                "type": mt5_type,
                "sl": order.stop_loss,
                "tp": order.take_profit,
                "deviation": 20,  # Max price slippage
                "magic": 123456,  # EA magic number
                "comment": f"PropOS|{order.id[:8]}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Add price for limit/stop orders
            if order.order_type in (
                OrderType.LIMIT_BUY, OrderType.LIMIT_SELL,
                OrderType.STOP_BUY, OrderType.STOP_SELL,
            ):
                request["action"] = mt5.TRADE_ACTION_PENDING
                request["price"] = order.price

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: mt5.order_send(request)
            )

            if result is None:
                return MT5OrderResult(
                    status=OrderStatus.FAILED,
                    error_message="MT5 returned None",
                )

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return MT5OrderResult(
                    status=OrderStatus.FILLED,
                    mt5_ticket=result.order,
                    mt5_retcode=result.retcode,
                )
            else:
                return MT5OrderResult(
                    status=OrderStatus.REJECTED,
                    mt5_retcode=result.retcode,
                    error_message=f"MT5 error: {result.comment}",
                )

        except ImportError:
            # Simulation mode
            logger.info("Simulated order execution", order_id=order.id)
            return MT5OrderResult(
                status=OrderStatus.FILLED,
                mt5_ticket=99999,
                mt5_retcode=10009,
            )
        except Exception as e:
            return MT5OrderResult(
                status=OrderStatus.FAILED,
                error_message=str(e),
            )
