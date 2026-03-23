"""
PropOS — Health Check API
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.monitoring.health import HealthChecker

router = APIRouter(tags=["health"])
_checker = HealthChecker()


@router.get("/api/health")
async def health_check():
    """System health check endpoint."""
    result = await _checker.check()
    return result
