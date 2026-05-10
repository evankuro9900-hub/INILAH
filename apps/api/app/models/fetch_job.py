"""Fetch job tracking — untuk caching per tanggal."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class FetchJob(Base):
    """Tracking job fetch data per tanggal + sumber."""

    __tablename__ = "fetch_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_date: Mapped[date] = mapped_column(Date, index=True)  # WIB date
    source: Mapped[str] = mapped_column(String(32))  # 'all' | 'fixtures' | 'stats' | 'odds'
    status: Mapped[str] = mapped_column(String(16))  # pending | success | failed
    triggered_by: Mapped[str] = mapped_column(
        String(32), default="cron"
    )  # cron | user_manual | auto_refresh

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    fixtures_count: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
