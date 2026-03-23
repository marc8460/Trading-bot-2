"""
PropOS — Global State Management

Centralized, thread-safe state for the running system.
Tracks: system status, active accounts, open positions, daily stats.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SystemStatus(str, Enum):
    """Overall system operating status."""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    KILL_SWITCH = "kill_switch"


@dataclass
class AccountState:
    """Runtime state for a single trading account."""
    account_id: str
    connected: bool = False
    daily_pnl: float = 0.0
    total_pnl: float = 0.0
    daily_drawdown_pct: float = 0.0
    total_drawdown_pct: float = 0.0
    open_positions: int = 0
    trades_today: int = 0
    last_trade_time: datetime | None = None
    is_auto_stopped: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass
class GlobalState:
    """
    Centralized system state.

    This is the single source of truth for the running system.
    All modules read from and update this state.
    """

    # System
    status: SystemStatus = SystemStatus.STOPPED
    started_at: datetime | None = None
    last_heartbeat: datetime | None = None

    # Kill switch
    kill_switch_active: bool = False
    kill_switch_reason: str = ""

    # Accounts
    accounts: dict[str, AccountState] = field(default_factory=dict)

    # Strategy
    active_strategy: str = ""
    last_signal_time: datetime | None = None
    signals_generated_today: int = 0

    # Execution
    total_trades_today: int = 0
    total_open_positions: int = 0

    # Lock for thread-safe updates
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def update(self, **kwargs: Any) -> None:
        """Thread-safe state update."""
        async with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    async def get_account(self, account_id: str) -> AccountState:
        """Get or create account state."""
        async with self._lock:
            if account_id not in self.accounts:
                self.accounts[account_id] = AccountState(account_id=account_id)
            return self.accounts[account_id]

    async def activate_kill_switch(self, reason: str) -> None:
        """Activate the global kill switch."""
        async with self._lock:
            self.kill_switch_active = True
            self.kill_switch_reason = reason
            self.status = SystemStatus.KILL_SWITCH

    async def to_dict(self) -> dict[str, Any]:
        """Serialize state for API/dashboard consumption."""
        async with self._lock:
            return {
                "status": self.status.value,
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                "kill_switch": {
                    "active": self.kill_switch_active,
                    "reason": self.kill_switch_reason,
                },
                "strategy": {
                    "active": self.active_strategy,
                    "last_signal": self.last_signal_time.isoformat() if self.last_signal_time else None,
                    "signals_today": self.signals_generated_today,
                },
                "execution": {
                    "trades_today": self.total_trades_today,
                    "open_positions": self.total_open_positions,
                },
                "accounts": {
                    aid: {
                        "connected": a.connected,
                        "daily_pnl": a.daily_pnl,
                        "total_pnl": a.total_pnl,
                        "daily_drawdown_pct": a.daily_drawdown_pct,
                        "total_drawdown_pct": a.total_drawdown_pct,
                        "open_positions": a.open_positions,
                        "trades_today": a.trades_today,
                        "is_auto_stopped": a.is_auto_stopped,
                    }
                    for aid, a in self.accounts.items()
                },
            }


# Global state singleton
_global_state: GlobalState | None = None


def get_state() -> GlobalState:
    """Get or create the global state singleton."""
    global _global_state
    if _global_state is None:
        _global_state = GlobalState()
    return _global_state
