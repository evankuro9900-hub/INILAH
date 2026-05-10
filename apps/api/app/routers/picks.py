"""Picks history endpoint."""

from __future__ import annotations

from datetime import date as date_type

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.fixture import Fixture
from app.models.pick import Pick
from app.schemas.fixture import PickOut

router = APIRouter(prefix="/api/picks", tags=["picks"])


@router.get("", response_model=list[PickOut])
async def list_picks(
    date_from: date_type | None = Query(None),
    date_to: date_type | None = Query(None),
    league: str | None = Query(None),
    result: str | None = Query(None, description="win|loss|push|pending"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Pick).join(Fixture, Pick.fixture_id == Fixture.id)
    if date_from:
        stmt = stmt.where(Fixture.kickoff_wib_date >= date_from)
    if date_to:
        stmt = stmt.where(Fixture.kickoff_wib_date <= date_to)
    if league:
        stmt = stmt.where(Fixture.league_id == league)
    if result == "pending":
        stmt = stmt.where(Pick.result.is_(None))
    elif result in {"win", "loss", "push", "void"}:
        stmt = stmt.where(Pick.result == result)
    stmt = stmt.order_by(Pick.created_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [PickOut.model_validate(p) for p in rows]
