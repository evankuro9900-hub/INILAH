"""Team stats snapshot per tanggal — untuk reproducibility."""

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TeamStatsSnapshot(Base):
    """Snapshot stats tim pada tanggal tertentu."""

    __tablename__ = "team_stats_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team: Mapped[str] = mapped_column(String(128), index=True)
    league_id: Mapped[str] = mapped_column(String(32), ForeignKey("leagues.id"))
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)

    # Form 10 match liga
    form_10: Mapped[str | None] = mapped_column(String(32))  # 'W-D-L-W-W-D-L-W-W-D'
    scoreline_breakdown: Mapped[dict | None] = mapped_column(JSON)
    # {"1-0": 2, "2-0": 1, "1-1": 3, ...}

    # Avg gol per venue
    avg_goals_for_home: Mapped[float | None] = mapped_column(Float)
    avg_goals_against_home: Mapped[float | None] = mapped_column(Float)
    avg_goals_for_away: Mapped[float | None] = mapped_column(Float)
    avg_goals_against_away: Mapped[float | None] = mapped_column(Float)

    # xG / xGA (10 match liga)
    xg_10: Mapped[float | None] = mapped_column(Float)
    xga_10: Mapped[float | None] = mapped_column(Float)

    # Defense indicator
    clean_sheet_rate: Mapped[float | None] = mapped_column(Float)
    btts_rate: Mapped[float | None] = mapped_column(Float)

    # Klasemen
    league_position: Mapped[int | None]
    points: Mapped[int | None]
    points_gap_to_top: Mapped[int | None]

    # Raw data untuk audit
    raw_data: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("team", "league_id", "snapshot_date", name="uq_team_league_date"),
    )
