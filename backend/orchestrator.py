"""
PropOS — Trading Orchestrator

The main worker loop connecting all modules:
Data -> Strategy -> Filters -> Risk -> Compliance -> Router -> Execution -> Persistence -> Notify
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any

from backend.compliance.engine import ComplianceEngine
from backend.core.config import ExecutionMode, load_accounts_config, load_settings
from backend.core.events import Event, EventType, get_event_bus
from backend.core.logging import get_logger
from backend.core.state import SystemStatus, get_state
from backend.execution.engine import ExecutionEngine
from backend.execution.mt5_executor import MT5Executor
from backend.filters.chain import FilterChain
from backend.filters.news_filter import NewsFilter
from backend.filters.session_filter import SessionFilter
from backend.filters.spread_filter import SpreadFilter
from backend.filters.volatility_filter import VolatilityFilter
from backend.market_data.mt5_provider import MT5DataProvider
from backend.models.account import AccountConfig
from backend.models.order import OrderStatus
from backend.risk.engine import RiskEngine
from backend.router.engine import AccountRouter
from backend.storage.repository import TradeRepository
from backend.strategy.registry import create_default_registry

logger = get_logger(__name__)


class TradingOrchestrator:
    """The central brain orchestrating the trade lifecycle."""

    def __init__(self) -> None:
        self.settings = load_settings()
        self.state = get_state()
        self.bus = get_event_bus()
        self.repo = TradeRepository()

        # Initialize engines
        self.risk_engine = RiskEngine(
            default_risk_pct=self.settings.risk.default_risk_per_trade_pct,
            max_daily_trades=self.settings.risk.max_daily_trades,
            max_open_positions=self.settings.risk.max_open_positions,
        )
        self.compliance_engine = ComplianceEngine()
        self.router = AccountRouter(self.risk_engine, self.compliance_engine)
        self.execution_engine = ExecutionEngine()
        self.strategy_registry = create_default_registry()
        self._active_strategy = None  # Set during initialize

        # Setup filter chain
        self.filter_chain = FilterChain([
            SpreadFilter(),
            SessionFilter(),
            NewsFilter(),
            VolatilityFilter(),
        ])

        # State vars
        self.accounts: list[AccountConfig] = []
        self.data_providers: dict[str, MT5DataProvider] = {}
        self.is_running = False

    async def initialize(self) -> bool:
        """Initialize all connections and state before starting."""
        try:

            # Load accounts
            account_dicts = load_accounts_config()
            for acc_dict in account_dicts:
                acc = AccountConfig(**acc_dict)
                self.accounts.append(acc)

                # Resolve MT5 credentials from env vars using credential_index
                idx = acc.mt5_credential_index
                mt5_login = int(os.getenv(f"MT5_ACCOUNT_{idx}_LOGIN", "0"))
                mt5_password = os.getenv(f"MT5_ACCOUNT_{idx}_PASSWORD", "")
                mt5_server = os.getenv(f"MT5_ACCOUNT_{idx}_SERVER", "")

                # Setup MT5 executor (will fallback to simulation if no MT5)
                executor = MT5Executor(
                    mt5_login=mt5_login,
                    mt5_password=mt5_password,
                    mt5_server=mt5_server,
                )
                connected = await executor.connect()
                self.execution_engine.register_executor(acc.id, executor)

                # Initialize state
                acc_state = await self.state.get_account(acc.id)
                acc_state.connected = connected
                # Seed trades_today from DB
                trades_today = await self.repo.get_trades_today(acc.id)
                acc_state.trades_today = trades_today

                logger.info("Account initialized", account_id=acc.id, connected=connected)

            # Define core data provider (using first account as data source for now)
            if self.accounts:
                core_acc = self.accounts[0]
                idx = core_acc.mt5_credential_index
                dp = MT5DataProvider(
                    mt5_login=int(os.getenv(f"MT5_ACCOUNT_{idx}_LOGIN", "0")),
                    mt5_password=os.getenv(f"MT5_ACCOUNT_{idx}_PASSWORD", ""),
                    mt5_server=os.getenv(f"MT5_ACCOUNT_{idx}_SERVER", ""),
                )
                await dp.connect()
                self.data_providers["core"] = dp

            # Load and initialize active strategy
            strat_name = self.settings.strategy.active_strategy
            self._active_strategy = self.strategy_registry.create(strat_name)
            await self._active_strategy.on_init()
            logger.info("Strategy loaded", name=strat_name)

            self.is_running = True
            await self.state.update(status=SystemStatus.RUNNING)
            logger.info("Orchestrator initialized successfully")
            return True

        except Exception as e:
            logger.exception("Failed to initialize orchestrator", error=str(e))
            await self.state.update(status=SystemStatus.ERROR)
            return False

    async def tick(self) -> None:
        """The main periodic tick executed by the scheduler."""
        if not self.is_running:
            return

        if self.state.status != SystemStatus.RUNNING:
            return

        if self.state.kill_switch_active:
            logger.warning("Kill switch active — halting tick")
            return

        # Heartbeat
        await self.state.update(last_heartbeat=datetime.now(timezone.utc))

        dp = self.data_providers.get("core")
        if not dp:
            return

        strategy = self._active_strategy
        if not strategy:
            return

        for symbol_cfg in self.settings.strategy.symbols:
            if not symbol_cfg.enabled:
                continue

            await self._process_symbol(symbol_cfg.symbol, symbol_cfg.timeframe, dp, strategy)

    async def _process_symbol(self, symbol: str, timeframe: str, dp: MT5DataProvider, strategy: Any) -> None:
        """Process the pipeline for a single symbol."""
        try:
            # 1. MT5 Data
            snapshot = await dp.get_snapshot(symbol, timeframe)
            if not snapshot or not snapshot.tick:
                return

            # 2. Strategy
            signal = await strategy.evaluate(snapshot)
            if not signal.is_actionable:
                return

            logger.info("Actionable signal generated", signal=signal.id, symbol=symbol, direction=signal.direction.value)
            await self.state.update(
                last_signal_time=signal.timestamp,
                signals_generated_today=self.state.signals_generated_today + 1
            )
            await self.repo.save_signal(signal)
            await self.bus.publish(Event(type=EventType.SIGNAL_GENERATED, data=signal.model_dump(), source="orchestrator"))

            # 3. Filters
            passed, filter_results = await self.filter_chain.evaluate(signal, snapshot)
            if not passed:
                return

            # 4, 5, 6. Risk, Compliance, and Router
            decision = await self.router.route(signal, [a for a in self.accounts if a.enabled])
            
            if not decision.orders:
                logger.info("Signal generated but no accounts qualified", signal_id=signal.id)
                return

            # 7. Execution
            results = await self.execution_engine.execute_routing(decision)

            # 8. Persistence
            for order in results:
                await self.repo.save_order(order)
                if order.status == OrderStatus.FILLED:
                    logger.info("Order filled successfully", order_id=order.id, symbol=symbol, account_id=order.account_id)
                else:
                    logger.warning("Order failed", order_id=order.id, reason=order.rejection_reason)

        except Exception as e:
            logger.exception("Error processing symbol", symbol=symbol, error=str(e))
            await self.repo.log_event("ERROR", "orchestrator", f"Symbol processing error: {e}", {"symbol": symbol})

    async def shutdown(self) -> None:
        """Shutdown components."""
        self.is_running = False
        for dp in self.data_providers.values():
            await dp.disconnect()
        logger.info("Orchestrator shutdown complete")
