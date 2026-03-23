"""
PropOS — Kill Switch

Global emergency stop that closes all positions and disables trading.
Can be triggered manually, by Telegram, or automatically by the protection layer.
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.core.events import Event, EventType, get_event_bus
from backend.core.logging import get_logger
from backend.core.state import get_state

logger = get_logger(__name__)


class KillSwitch:
    """
    Global kill switch for emergency shutdown.

    When activated:
    1. Sets global state to KILL_SWITCH
    2. Blocks all new trade submissions
    3. Publishes kill switch event (for Telegram notification)
    4. Optionally closes all open positions
    """

    def __init__(self) -> None:
        self._activated_at: datetime | None = None
        self._reason: str = ""

    @property
    def is_active(self) -> bool:
        return get_state().kill_switch_active

    async def activate(self, reason: str, close_positions: bool = False) -> None:
        """Activate the kill switch."""
        state = get_state()
        await state.activate_kill_switch(reason)

        self._activated_at = datetime.now(timezone.utc)
        self._reason = reason

        bus = get_event_bus()
        await bus.publish(Event(
            type=EventType.KILL_SWITCH_ACTIVATED,
            data={
                "reason": reason,
                "close_positions": close_positions,
                "timestamp": self._activated_at.isoformat(),
            },
            source="kill_switch",
        ))

        logger.critical(
            "KILL SWITCH ACTIVATED",
            reason=reason,
            close_positions=close_positions,
        )

    async def deactivate(self) -> None:
        """Deactivate the kill switch and resume trading."""
        state = get_state()
        async with state._lock:
            state.kill_switch_active = False
            state.kill_switch_reason = ""
            from backend.core.state import SystemStatus
            state.status = SystemStatus.RUNNING

        self._activated_at = None
        self._reason = ""
        logger.info("Kill switch deactivated")

    def get_status(self) -> dict:
        return {
            "active": self.is_active,
            "reason": self._reason,
            "activated_at": self._activated_at.isoformat() if self._activated_at else None,
        }
