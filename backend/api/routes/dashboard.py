"""
PropOS — Dashboard API Routes

Provides real-time data for the frontend dashboard.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.core.state import get_state

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
async def get_overview():
    """Get dashboard overview data (P/L, drawdown, active trades, system status)."""
    state = get_state()
    data = await state.to_dict()
    return {"status": "ok", "data": data}


@router.get("/accounts")
async def get_accounts():
    """Get all account states for the dashboard."""
    state = get_state()
    accounts = {}
    for account_id, account_state in state.accounts.items():
        accounts[account_id] = {
            "id": account_id,
            "connected": account_state.connected,
            "daily_pnl": account_state.daily_pnl,
            "total_pnl": account_state.total_pnl,
            "daily_drawdown_pct": account_state.daily_drawdown_pct,
            "total_drawdown_pct": account_state.total_drawdown_pct,
            "open_positions": account_state.open_positions,
            "trades_today": account_state.trades_today,
            "is_auto_stopped": account_state.is_auto_stopped,
        }
    return {"status": "ok", "data": accounts}


@router.get("/strategy")
async def get_strategy_status():
    """Get current strategy status."""
    state = get_state()
    return {
        "status": "ok",
        "data": {
            "active_strategy": state.active_strategy,
            "last_signal_time": state.last_signal_time.isoformat() if state.last_signal_time else None,
            "signals_today": state.signals_generated_today,
        },
    }
