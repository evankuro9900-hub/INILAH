"""Cache service — TTL logic per tanggal sesuai keputusan v3.0."""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.fetch_job import FetchJob
from app.utils.timezone import today_wib


async def latest_successful_job(
    db: AsyncSession, target_date: date, source: str = "all"
) -> FetchJob | None:
    """Cari fetch_job terakhir yang sukses untuk tanggal+source."""
    stmt = (
        select(FetchJob)
        .where(
            FetchJob.target_date == target_date,
            FetchJob.source == source,
            FetchJob.status == "success",
        )
        .order_by(FetchJob.completed_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def is_cache_valid(
    db: AsyncSession, target_date: date, source: str = "all"
) -> tuple[bool, FetchJob | None]:
    """Cek apakah cache untuk tanggal target masih valid.

    Aturan:
    - Past date (< today): cache valid forever (data sudah final)
    - Today/Future: cache valid jika completed < TTL hours yang lalu
    """
    job = await latest_successful_job(db, target_date, source)
    if job is None:
        return False, None
    if job.completed_at is None:
        return False, job

    today = today_wib()
    if target_date < today:
        return True, job

    # Today/Future: cek TTL
    ttl_hours = (
        settings.cache_ttl_today_hours if target_date == today else settings.cache_ttl_future_hours
    )
    completed = job.completed_at
    if completed.tzinfo is None:
        # SQLite naive timestamp; assume UTC
        from app.utils.timezone import UTC

        completed = completed.replace(tzinfo=UTC)
    age = datetime.now(completed.tzinfo) - completed
    return age < timedelta(hours=ttl_hours), job


async def create_pending_job(
    db: AsyncSession,
    target_date: date,
    source: str = "all",
    triggered_by: str = "auto_refresh",
) -> FetchJob:
    """Buat fetch_job baru dengan status pending."""
    job = FetchJob(
        target_date=target_date,
        source=source,
        status="pending",
        triggered_by=triggered_by,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def mark_job_success(db: AsyncSession, job: FetchJob, fixtures_count: int) -> None:
    """Tandai job sukses."""
    from app.utils.timezone import now_utc

    job.status = "success"
    job.completed_at = now_utc()
    job.fixtures_count = fixtures_count
    await db.commit()


async def mark_job_failed(db: AsyncSession, job: FetchJob, error: str) -> None:
    """Tandai job gagal."""
    from app.utils.timezone import now_utc

    job.status = "failed"
    job.completed_at = now_utc()
    job.error_message = error[:1000]
    await db.commit()
