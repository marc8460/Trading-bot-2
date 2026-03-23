"""
PropOS — MT5 Market Data Provider

Live market data from MetaTrader 5 terminal.
Wraps the synchronous MT5 API for async usage.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from backend.core.logging import get_logger
from backend.market_data.base import BaseDataProvider
from backend.models.market import Candle, MarketSnapshot, Tick

logger = get_logger(__name__)

# MT5 timeframe mapping
TIMEFRAME_MAP: dict[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 16385,
    "H4": 16388,
    "D1": 16408,
    "W1": 32769,
    "MN1": 49153,
}


class MT5DataProvider(BaseDataProvider):
    """
    MetaTrader 5 market data provider.

    Wraps the synchronous MetaTrader5 Python package
    for use in an async context via run_in_executor.
    """

    def __init__(self, mt5_login: int, mt5_password: str, mt5_server: str) -> None:
        super().__init__(name="mt5")
        self._login = mt5_login
        self._password = mt5_password
        self._server = mt5_server

    async def connect(self) -> bool:
        """Initialize and connect to MT5 terminal."""
        try:
            import MetaTrader5 as mt5

            loop = asyncio.get_event_loop()
            initialized = await loop.run_in_executor(None, mt5.initialize)
            if not initialized:
                logger.error("MT5 initialization failed", error=mt5.last_error())
                return False

            authorized = await loop.run_in_executor(
                None,
                lambda: mt5.login(
                    login=self._login,
                    password=self._password,
                    server=self._server,
                ),
            )
            if not authorized:
                logger.error("MT5 login failed", error=mt5.last_error())
                return False

            self._connected = True
            logger.info("MT5 connected", login=self._login, server=self._server)
            return True

        except ImportError:
            logger.warning("MetaTrader5 package not available — running in simulation mode")
            self._connected = False
            return False
        except Exception as e:
            logger.error("MT5 connection error", error=str(e))
            return False

    async def disconnect(self) -> None:
        """Shutdown MT5 connection."""
        try:
            import MetaTrader5 as mt5

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, mt5.shutdown)
            self._connected = False
            logger.info("MT5 disconnected")
        except Exception:
            pass

    async def get_tick(self, symbol: str) -> Tick | None:
        """Get latest tick from MT5."""
        try:
            import MetaTrader5 as mt5

            loop = asyncio.get_event_loop()
            tick = await loop.run_in_executor(
                None, lambda: mt5.symbol_info_tick(symbol)
            )
            if tick is None:
                return None

            return Tick(
                symbol=symbol,
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume_real if hasattr(tick, "volume_real") else 0.0,
                timestamp=datetime.fromtimestamp(tick.time, tz=timezone.utc),
            )
        except Exception as e:
            logger.error("Failed to get tick", symbol=symbol, error=str(e))
            return None

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int = 100,
    ) -> list[Candle]:
        """Get historical candles from MT5."""
        try:
            import MetaTrader5 as mt5

            tf = TIMEFRAME_MAP.get(timeframe.upper())
            if tf is None:
                logger.error("Unknown timeframe", timeframe=timeframe)
                return []

            loop = asyncio.get_event_loop()
            rates = await loop.run_in_executor(
                None,
                lambda: mt5.copy_rates_from_pos(symbol, tf, 0, count),
            )
            if rates is None or len(rates) == 0:
                return []

            df = pd.DataFrame(rates)
            candles = []
            for _, row in df.iterrows():
                candles.append(
                    Candle(
                        symbol=symbol,
                        timeframe=timeframe,
                        open=row["open"],
                        high=row["high"],
                        low=row["low"],
                        close=row["close"],
                        volume=row.get("real_volume", 0.0),
                        tick_volume=int(row.get("tick_volume", 0)),
                        spread=int(row.get("spread", 0)),
                        timestamp=datetime.fromtimestamp(row["time"], tz=timezone.utc),
                    )
                )
            return candles

        except Exception as e:
            logger.error("Failed to get candles", symbol=symbol, error=str(e))
            return []

    async def get_snapshot(self, symbol: str, timeframe: str) -> MarketSnapshot:
        """Build a complete market snapshot."""
        tick = await self.get_tick(symbol)
        candles = await self.get_candles(symbol, timeframe, count=100)

        # Calculate ATR from candles
        atr = 0.0
        if len(candles) >= 15:
            atr = self._calculate_atr(candles, period=14)

        return MarketSnapshot(
            symbol=symbol,
            tick=tick,
            candles=candles,
            atr=atr,
            current_spread_points=tick.spread_points if tick else 0.0,
        )

    @staticmethod
    def _calculate_atr(candles: list[Candle], period: int = 14) -> float:
        """Calculate ATR from candle list."""
        if len(candles) < period + 1:
            return 0.0

        trs = []
        for i in range(1, len(candles)):
            c = candles[i]
            prev_close = candles[i - 1].close
            tr = max(c.high - c.low, abs(c.high - prev_close), abs(c.low - prev_close))
            trs.append(tr)

        if len(trs) < period:
            return 0.0

        return sum(trs[-period:]) / period
