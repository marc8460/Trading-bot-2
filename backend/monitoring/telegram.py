"""
PropOS — Telegram Notifications

Sends trade alerts, warnings, and system status to Telegram.
"""

from __future__ import annotations

from backend.core.events import Event, EventType, get_event_bus
from backend.core.logging import get_logger

logger = get_logger(__name__)


class TelegramNotifier:
    """Sends notifications to Telegram."""

    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._enabled = enabled
        self._bot = None

    async def initialize(self) -> None:
        """Initialize the Telegram bot."""
        if not self._enabled or not self._bot_token:
            logger.info("Telegram notifications disabled")
            return

        try:
            from telegram import Bot
            self._bot = Bot(token=self._bot_token)
            logger.info("Telegram bot initialized")
        except Exception as e:
            logger.error("Failed to initialize Telegram bot", error=str(e))

    async def send_message(self, text: str, parse_mode: str = "HTML") -> None:
        """Send a message to the configured chat."""
        if not self._enabled or not self._bot:
            return

        try:
            await self._bot.send_message(
                chat_id=self._chat_id,
                text=text,
                parse_mode=parse_mode,
            )
        except Exception as e:
            logger.error("Failed to send Telegram message", error=str(e))

    async def notify_trade_opened(self, data: dict) -> None:
        """Send trade opened notification."""
        msg = (
            f"🟢 <b>Trade Opened</b>\n"
            f"Symbol: {data.get('symbol', '?')}\n"
            f"Direction: {data.get('direction', '?')}\n"
            f"Volume: {data.get('volume', '?')} lots\n"
            f"Account: {data.get('account_id', '?')}\n"
            f"Ticket: #{data.get('mt5_ticket', '?')}"
        )
        await self.send_message(msg)

    async def notify_trade_closed(self, data: dict) -> None:
        """Send trade closed notification."""
        pnl = data.get("pnl", 0)
        emoji = "✅" if pnl >= 0 else "❌"
        msg = (
            f"{emoji} <b>Trade Closed</b>\n"
            f"Symbol: {data.get('symbol', '?')}\n"
            f"P/L: ${pnl:+.2f}\n"
            f"Account: {data.get('account_id', '?')}"
        )
        await self.send_message(msg)

    async def notify_warning(self, data: dict) -> None:
        """Send warning notification."""
        msg = (
            f"⚠️ <b>Warning</b>\n"
            f"{data.get('message', 'Unknown warning')}\n"
            f"Account: {data.get('account_id', 'system')}"
        )
        await self.send_message(msg)

    async def notify_kill_switch(self, data: dict) -> None:
        """Send kill switch notification."""
        msg = (
            f"🛑 <b>KILL SWITCH ACTIVATED</b>\n"
            f"Reason: {data.get('reason', 'Unknown')}\n"
            f"All trading has been stopped."
        )
        await self.send_message(msg)

    async def notify_system_status(self, status: str) -> None:
        """Send system status update."""
        emoji = "🟢" if status == "running" else "🔴"
        msg = f"{emoji} <b>PropOS</b> is now <b>{status.upper()}</b>"
        await self.send_message(msg)

    def subscribe_to_events(self) -> None:
        """Subscribe to relevant events on the event bus."""
        bus = get_event_bus()

        async def on_trade_filled(event: Event) -> None:
            await self.notify_trade_opened(event.data)

        async def on_trade_closed(event: Event) -> None:
            await self.notify_trade_closed(event.data)

        async def on_kill_switch(event: Event) -> None:
            await self.notify_kill_switch(event.data)

        async def on_warning(event: Event) -> None:
            await self.notify_warning(event.data)

        bus.subscribe(EventType.TRADE_FILLED, on_trade_filled)
        bus.subscribe(EventType.TRADE_CLOSED, on_trade_closed)
        bus.subscribe(EventType.KILL_SWITCH_ACTIVATED, on_kill_switch)
        bus.subscribe(EventType.COMPLIANCE_WARNING, on_warning)
        bus.subscribe(EventType.RISK_WARNING, on_warning)
