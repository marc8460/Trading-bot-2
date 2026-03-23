"""
PropOS — System Health Checks

Provides health status for the API endpoint and monitoring.
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.core.state import get_state


class HealthChecker:
    """System health check aggregator."""

    async def check(self) -> dict:
        """Run all health checks and return status."""
        state = get_state()
        state_data = await state.to_dict()

        # Check overall health
        checks = {
            "system_status": state.status.value,
            "kill_switch": state.kill_switch_active,
            "accounts": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Per-account health
        for account_id, account_state in state.accounts.items():
            checks["accounts"][account_id] = {
                "connected": account_state.connected,
                "auto_stopped": account_state.is_auto_stopped,
                "errors": len(account_state.errors),
            }

        # Overall healthy flag
        checks["healthy"] = (
            state.status.value in ("running", "starting")
            and not state.kill_switch_active
        )

        return checks
