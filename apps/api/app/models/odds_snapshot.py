"""Odds snapshot per market per match — untuk CLV tracking."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class OddsSnapshot(Base):
    """Snapshot odds di waktu tertentu."""

    __tablename__ = "odds_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), index=True)
    market: Mapped[str] = mapped_column(String(32))  # '1X2_HOME', 'OVER_2.5', dll
    odds: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32), default="oddsapi")
    snapshot_type: Mapped[str] = mapped_column(String(16))  # 'open' | 'pick_time' | 'close'
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (Index("idx_odds_fixture_market_type", "fixture_id", "market", "snapshot_type"),)
