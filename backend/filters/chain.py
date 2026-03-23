"""
PropOS — Filter Chain

Orchestrates all filters in sequence. A signal must pass ALL
enabled filters to proceed to the risk engine.
"""

from __future__ import annotations

from backend.core.events import Event, EventType, get_event_bus
from backend.core.logging import get_logger
from backend.filters.base import BaseFilter, FilterResult
from backend.models.market import MarketSnapshot
from backend.models.signal import TradeSignal

logger = get_logger(__name__)


class FilterChain:
    """
    Runs a signal through all registered filters in order.

    If any filter rejects, the signal is blocked and the rejection
    is published via the event bus.
    """

    def __init__(self, filters: list[BaseFilter] | None = None) -> None:
        self._filters: list[BaseFilter] = filters or []

    def add_filter(self, f: BaseFilter) -> None:
        """Add a filter to the chain."""
        self._filters.append(f)

    def remove_filter(self, name: str) -> None:
        """Remove a filter by name."""
        self._filters = [f for f in self._filters if f.name != name]

    async def evaluate(
        self,
        signal: TradeSignal,
        snapshot: MarketSnapshot,
    ) -> tuple[bool, list[FilterResult]]:
        """
        Run all filters. Returns (passed, results).

        All filters run even if one fails, so we get full diagnostics.
        """
        results: list[FilterResult] = []
        all_passed = True

        for f in self._filters:
            if not f.enabled:
                continue

            result = await f.check(signal, snapshot)
            results.append(result)

            if not result.passed:
                all_passed = False
                logger.info(
                    "Filter rejected signal",
                    filter=f.name,
                    symbol=signal.symbol,
                    reason=result.reason,
                )

        # Publish event
        bus = get_event_bus()
        if all_passed:
            await bus.publish(Event(
                type=EventType.SIGNAL_FILTERED,
                data={"signal_id": signal.id, "symbol": signal.symbol},
                source="filter_chain",
            ))
        else:
            failed = [r for r in results if not r.passed]
            await bus.publish(Event(
                type=EventType.SIGNAL_REJECTED,
                data={
                    "signal_id": signal.id,
                    "symbol": signal.symbol,
                    "reasons": [r.reason for r in failed],
                },
                source="filter_chain",
            ))

        return all_passed, results

    def list_filters(self) -> list[dict]:
        """Return filter info for dashboard display."""
        return [
            {"name": f.name, "enabled": f.enabled}
            for f in self._filters
        ]
