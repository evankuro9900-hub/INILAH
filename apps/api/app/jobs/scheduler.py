"""APScheduler jobs — fetch + validate."""

from __future__ import annotations

import logging
from datetime import timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.db import AsyncSessionLocal
from app.services.fetch_service import fetch_and_persist_fixtures, validate_finished_picks
from app.utils.timezone import today_wib

logger = logging.getLogger(__name__)


async def job_fetch_today() -> None:
    """Cron tiap 4 jam — refresh data hari ini."""
    target = today_wib()
    async with AsyncSessionLocal() as db:
        try:
            await fetch_and_persist_fixtures(db, target, triggered_by="cron")
            logger.info("job_fetch_today success for %s", target)
        except Exception as e:
            logger.error("job_fetch_today failed: %s", e)


async def job_fetch_tomorrow() -> None:
    """Pre-fetch H+1 jam 03:00 WIB."""
    target = today_wib() + timedelta(days=1)
    async with AsyncSessionLocal() as db:
        try:
            await fetch_and_persist_fixtures(db, target, triggered_by="cron")
            logger.info("job_fetch_tomorrow success for %s", target)
        except Exception as e:
            logger.error("job_fetch_tomorrow failed: %s", e)


async def job_validate_picks() -> None:
    """Cron tiap 15 menit — grade picks."""
    async with AsyncSessionLocal() as db:
        try:
            count = await validate_finished_picks(db)
            if count > 0:
                logger.info("job_validate_picks: graded %d picks", count)
        except Exception as e:
            logger.error("job_validate_picks failed: %s", e)


def start_scheduler() -> AsyncIOScheduler:
    """Mulai background scheduler."""
    scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")

    scheduler.add_job(
        job_fetch_today,
        IntervalTrigger(hours=settings.fetch_today_interval_hours),
        id="fetch_today",
        replace_existing=True,
    )
    scheduler.add_job(
        job_fetch_tomorrow,
        CronTrigger(hour=3, minute=0, timezone="Asia/Jakarta"),
        id="fetch_tomorrow",
        replace_existing=True,
    )
    scheduler.add_job(
        job_validate_picks,
        IntervalTrigger(minutes=settings.validate_picks_interval_minutes),
        id="validate_picks",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with 3 jobs")
    return scheduler
