"""
PropOS — Control API Routes

Start/stop trading, kill switch, risk adjustments.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.state import SystemStatus, get_state
from backend.protection.kill_switch import KillSwitch

router = APIRouter(prefix="/api/controls", tags=["controls"])

# Singleton instances (injected at app startup)
_kill_switch: KillSwitch | None = None


def set_kill_switch(ks: KillSwitch) -> None:
    global _kill_switch
    _kill_switch = ks


class KillSwitchRequest(BaseModel):
    reason: str = "Manual activation"
    close_positions: bool = False


@router.post("/start")
async def start_trading():
    """Start the trading system."""
    state = get_state()
    await state.update(status=SystemStatus.RUNNING)
    return {"status": "ok", "message": "Trading started"}


@router.post("/stop")
async def stop_trading():
    """Stop the trading system gracefully."""
    state = get_state()
    await state.update(status=SystemStatus.PAUSED)
    return {"status": "ok", "message": "Trading stopped"}


@router.post("/kill-switch/activate")
async def activate_kill_switch(req: KillSwitchRequest):
    """Activate the emergency kill switch."""
    if _kill_switch:
        await _kill_switch.activate(req.reason, req.close_positions)
    return {"status": "ok", "message": f"Kill switch activated: {req.reason}"}


@router.post("/kill-switch/deactivate")
async def deactivate_kill_switch():
    """Deactivate the kill switch and resume."""
    if _kill_switch:
        await _kill_switch.deactivate()
    return {"status": "ok", "message": "Kill switch deactivated"}


@router.get("/kill-switch/status")
async def kill_switch_status():
    """Get kill switch status."""
    if _kill_switch:
        return {"status": "ok", "data": _kill_switch.get_status()}
    return {"status": "ok", "data": {"active": False}}
