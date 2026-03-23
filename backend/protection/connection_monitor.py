"""
PropOS — Connection Monitor

Monitors MT5 terminal connections and triggers alerts/reconnection
when connections are lost.
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.core.events import Event, EventType, get_event_bus
from backend.core.logging import get_logger
from backend.core.state import get_state

logger = get_logger(__name__)


class ConnectionMonitor:
    """Monitors MT5 connections and handles reconnection."""

    def __init__(self, max_reconnect_attempts: int = 5) -> None:
        self.max_reconnect_attempts = max_reconnect_attempts
        self._connection_status: dict[str, bool] = {}
        self._reconnect_counts: dict[str, int] = {}

    async def check_connection(self, account_id: str) -> bool:
        """Check if an account's MT5 connection is alive."""
        # In production, this would call mt5.terminal_info() or similar
        # For now, return cached status
        return self._connection_status.get(account_id, False)

    async def on_connection_lost(self, account_id: str) -> None:
        """Handle a lost connection."""
        self._connection_status[account_id] = False
        self._reconnect_counts[account_id] = self._reconnect_counts.get(account_id, 0) + 1

        bus = get_event_bus()
        await bus.publish(Event(
            type=EventType.CONNECTION_LOST,
            data={
                "account_id": account_id,
                "reconnect_attempt": self._reconnect_counts[account_id],
            },
            source="connection_monitor",
        ))

        state = get_state()
        account_state = await state.get_account(account_id)
        account_state.connected = False

        logger.warning(
            "Connection lost",
            account_id=account_id,
            attempt=self._reconnect_counts[account_id],
        )

    async def on_connection_restored(self, account_id: str) -> None:
        """Handle a restored connection."""
        self._connection_status[account_id] = True
        self._reconnect_counts[account_id] = 0

        bus = get_event_bus()
        await bus.publish(Event(
            type=EventType.CONNECTION_RESTORED,
            data={"account_id": account_id},
            source="connection_monitor",
        ))

        state = get_state()
        account_state = await state.get_account(account_id)
        account_state.connected = True

        logger.info("Connection restored", account_id=account_id)

    async def check_all(self, account_ids: list[str]) -> dict[str, bool]:
        """Check all account connections."""
        results = {}
        for aid in account_ids:
            results[aid] = await self.check_connection(aid)
        return results
