"""
PropOS — Base Market Data Provider

Abstract interface for market data sources.
MT5 is the primary implementation; cTrader and external feeds are future.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models.market import Candle, MarketSnapshot, Tick


class BaseDataProvider(ABC):
    """Abstract base class for market data providers."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to data source."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from data source."""
        ...

    @abstractmethod
    async def get_tick(self, symbol: str) -> Tick | None:
        """Get the latest tick for a symbol."""
        ...

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int = 100,
    ) -> list[Candle]:
        """Get historical candles for a symbol."""
        ...

    @abstractmethod
    async def get_snapshot(self, symbol: str, timeframe: str) -> MarketSnapshot:
        """Get a full market snapshot including tick, candles, and indicators."""
        ...

    @property
    def is_connected(self) -> bool:
        return self._connected
