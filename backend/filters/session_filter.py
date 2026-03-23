"""
PropOS — Session Filter

Only allows trades during configured trading sessions (London, New York, etc.).
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.core.logging import get_logger
from backend.filters.base import BaseFilter, FilterResult
from backend.models.market import MarketSnapshot
from backend.models.signal import TradeSignal

logger = get_logger(__name__)


class SessionFilter(BaseFilter):
    """Restricts trading to configured session windows."""

    def __init__(
        self,
        sessions: list[dict] | None = None,
    ) -> None:
        super().__init__(name="session")
        self.sessions = sessions or [
            {"name": "London", "start": "08:00", "end": "16:00", "timezone": "Europe/London"},
            {"name": "New York", "start": "13:00", "end": "21:00", "timezone": "UTC"},
        ]

    async def check(self, signal: TradeSignal, snapshot: MarketSnapshot) -> FilterResult:
        if not self.enabled:
            return FilterResult(passed=True, filter_name=self.name)

        now = datetime.now(timezone.utc)
        current_hour_min = now.strftime("%H:%M")

        for session in self.sessions:
            start = session["start"]
            end = session["end"]
            # Simple UTC-based check for MVP
            if start <= current_hour_min <= end:
                return FilterResult(
                    passed=True,
                    filter_name=self.name,
                    details={"active_session": session["name"]},
                )

        return FilterResult(
            passed=False,
            filter_name=self.name,
            reason=f"No active session at {current_hour_min} UTC",
        )
