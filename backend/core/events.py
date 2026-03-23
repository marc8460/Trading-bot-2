"""
PropOS — Internal Event Bus

A lightweight publish-subscribe event bus for decoupled communication
between modules. Events are typed and async-compatible.

Usage:
    bus = EventBus()
    bus.subscribe("trade.opened", my_handler)
    await bus.publish("trade.opened", trade_data)
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Well-known event types in PropOS."""

    # Signal flow
    SIGNAL_GENERATED = "signal.generated"
    SIGNAL_FILTERED = "signal.filtered"
    SIGNAL_REJECTED = "signal.rejected"

    # Risk
    RISK_APPROVED = "risk.approved"
    RISK_REJECTED = "risk.rejected"
    RISK_WARNING = "risk.warning"

    # Compliance
    COMPLIANCE_APPROVED = "compliance.approved"
    COMPLIANCE_REJECTED = "compliance.rejected"
    COMPLIANCE_WARNING = "compliance.warning"

    # Execution
    TRADE_ROUTED = "trade.routed"
    TRADE_SUBMITTED = "trade.submitted"
    TRADE_FILLED = "trade.filled"
    TRADE_CLOSED = "trade.closed"
    TRADE_FAILED = "trade.failed"

    # Protection
    KILL_SWITCH_ACTIVATED = "protection.kill_switch"
    CONNECTION_LOST = "protection.connection_lost"
    CONNECTION_RESTORED = "protection.connection_restored"
    ANOMALY_DETECTED = "protection.anomaly"

    # System
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    HEARTBEAT = "system.heartbeat"
    ERROR = "system.error"


@dataclass
class Event:
    """An event published through the event bus."""

    type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = ""


# Type alias for event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """
    Async publish-subscribe event bus.

    Supports both exact topic matches and wildcard prefixes.
    Example: subscribing to "trade.*" receives all trade events.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type. Use '*' suffix for wildcards."""
        if event_type.endswith(".*"):
            prefix = event_type[:-2]
            self._wildcard_handlers[prefix].append(handler)
        else:
            self._handlers[event_type].append(handler)
        logger.debug("Subscribed handler %s to %s", handler.__name__, event_type)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler from an event type."""
        if event_type.endswith(".*"):
            prefix = event_type[:-2]
            self._wildcard_handlers[prefix] = [
                h for h in self._wildcard_handlers[prefix] if h != handler
            ]
        else:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    async def publish(self, event: Event) -> None:
        """Publish an event to all matching handlers."""
        handlers = list(self._handlers.get(event.type, []))

        # Match wildcard subscribers
        for prefix, wildcard_handlers in self._wildcard_handlers.items():
            if event.type.startswith(prefix):
                handlers.extend(wildcard_handlers)

        if not handlers:
            return

        # Run all handlers concurrently
        results = await asyncio.gather(
            *[self._safe_call(handler, event) for handler in handlers],
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                logger.error("Event handler error for %s: %s", event.type, result)

    async def _safe_call(self, handler: EventHandler, event: Event) -> None:
        """Safely call a handler, catching exceptions."""
        try:
            await handler(event)
        except Exception as e:
            logger.exception("Handler %s failed for event %s: %s", handler.__name__, event.type, e)
            raise


# Global event bus singleton
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
