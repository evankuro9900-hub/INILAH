"""Bankroll log virtual harian."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BankrollLog(Base):
    """Log harian bankroll virtual."""

    __tablename__ = "bankroll_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    log_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    starting_balance: Mapped[float] = mapped_column(Float)
    ending_balance: Mapped[float] = mapped_column(Float)
    total_staked: Mapped[float] = mapped_column(Float, default=0.0)
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    picks_count: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    pushes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
