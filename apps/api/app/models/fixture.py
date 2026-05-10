"""Fixtures (jadwal pertandingan)."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Fixture(Base):
    """Satu pertandingan."""

    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    league_id: Mapped[str] = mapped_column(String(32), ForeignKey("leagues.id"), index=True)

    home_team: Mapped[str] = mapped_column(String(128))
    away_team: Mapped[str] = mapped_column(String(128))

    kickoff_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    kickoff_wib_date: Mapped[date] = mapped_column(Date, index=True)  # untuk filter cepat

    status: Mapped[str] = mapped_column(String(16), default="scheduled")
    # scheduled | live | finished | postponed | canceled

    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    ht_home_score: Mapped[int | None] = mapped_column(Integer)
    ht_away_score: Mapped[int | None] = mapped_column(Integer)

    venue: Mapped[str | None] = mapped_column(String(128))
    referee: Mapped[str | None] = mapped_column(String(128))

    fetch_job_id: Mapped[int | None] = mapped_column(ForeignKey("fetch_jobs.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_fixtures_wib_date_status", "kickoff_wib_date", "status"),
        Index("idx_fixtures_league_date", "league_id", "kickoff_wib_date"),
    )
