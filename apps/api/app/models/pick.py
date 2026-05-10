"""Bot pick yang dihasilkan skill engine v3.0."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Pick(Base):
    """Bot pick + scoring card + tracking hasil + CLV."""

    __tablename__ = "picks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), index=True)

    market: Mapped[str] = mapped_column(String(32))  # '1X2_HOME', 'OVER_2.5', 'AH_-0.5_HOME'
    selection: Mapped[str] = mapped_column(String(64))  # tampilan readable

    odds_at_pick: Mapped[float] = mapped_column(Float)
    odds_at_close: Mapped[float | None] = mapped_column(Float)

    estimated_rp: Mapped[float] = mapped_column(Float)  # 0.0–1.0
    edge_pct: Mapped[float] = mapped_column(Float)  # 0.087 = 8.7%
    stake_pct: Mapped[float] = mapped_column(Float)  # % bankroll, 0.015 = 1.5%

    scoring_card: Mapped[dict | None] = mapped_column(JSON)
    reasoning: Mapped[dict | None] = mapped_column(JSON)
    tags: Mapped[list | None] = mapped_column(JSON)  # ['LOW_DATA', 'CUP', dll]

    # Hasil setelah match selesai
    result: Mapped[str | None] = mapped_column(String(8))  # win | loss | push | void
    profit_pct: Mapped[float | None] = mapped_column(Float)  # relatif bankroll
    clv_pct: Mapped[float | None] = mapped_column(Float)  # closing line value

    skill_version: Mapped[str] = mapped_column(String(16), default="v3.0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("idx_picks_result_validated", "result", "validated_at"),)
