"""
PropOS — Task Scheduler

Wraps APScheduler for periodic strategy ticks, health checks,
and scheduled tasks (daily reset, summary reports).
"""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.core.logging import get_logger

logger = get_logger(__name__)

AsyncTask = Callable[..., Coroutine[Any, Any, None]]


class Scheduler:
    """Centralized task scheduler for PropOS."""

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._started = False

    def add_interval_job(
        self,
        func: AsyncTask,
        seconds: int,
        job_id: str,
        **kwargs: Any,
    ) -> None:
        """Add a job that runs at a fixed interval."""
        self._scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=seconds),
            id=job_id,
            replace_existing=True,
            **kwargs,
        )
        logger.info("Scheduled interval job", job_id=job_id, seconds=seconds)

    def add_cron_job(
        self,
        func: AsyncTask,
        cron_expression: str,
        job_id: str,
        **kwargs: Any,
    ) -> None:
        """Add a cron-scheduled job (e.g., daily reset at midnight)."""
        self._scheduler.add_job(
            func,
            trigger=CronTrigger.from_crontab(cron_expression),
            id=job_id,
            replace_existing=True,
            **kwargs,
        )
        logger.info("Scheduled cron job", job_id=job_id, cron=cron_expression)

    def remove_job(self, job_id: str) -> None:
        """Remove a scheduled job."""
        try:
            self._scheduler.remove_job(job_id)
        except Exception:
            pass

    def start(self) -> None:
        """Start the scheduler."""
        if not self._started:
            self._scheduler.start()
            self._started = True
            logger.info("Scheduler started")

    def shutdown(self) -> None:
        """Shut down the scheduler gracefully."""
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False
            logger.info("Scheduler shut down")

    @property
    def is_running(self) -> bool:
        return self._started
