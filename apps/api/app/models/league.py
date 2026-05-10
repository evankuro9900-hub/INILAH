"""ORM model untuk liga (sinkronisasi dari leagues.py config)."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class League(Base):
    """Liga aktif di webapp."""

    __tablename__ = "leagues"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # slug
    name: Mapped[str] = mapped_column(String(128))
    country: Mapped[str] = mapped_column(String(64))
    tier: Mapped[str] = mapped_column(String(16))
    min_edge_pct: Mapped[float]
    over_baseline: Mapped[float]
    notes: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
