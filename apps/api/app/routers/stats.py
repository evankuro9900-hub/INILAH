"""Stats & calibration endpoints."""

from __future__ import annotations

from collections import defaultdict
from datetime import date as date_type

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.fixture import Fixture
from app.models.pick import Pick
from app.schemas.fixture import StatsResponse

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    date_from: date_type | None = Query(None),
    date_to: date_type | None = Query(None),
    league: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Pick, Fixture).join(Fixture, Pick.fixture_id == Fixture.id)
    if date_from:
        stmt = stmt.where(Fixture.kickoff_wib_date >= date_from)
    if date_to:
        stmt = stmt.where(Fixture.kickoff_wib_date <= date_to)
    if league:
        stmt = stmt.where(Fixture.league_id == league)

    rows = (await db.execute(stmt)).all()

    total = len(rows)
    wins = losses = pushes = pending = 0
    pnl_total = 0.0
    clv_values: list[float] = []

    by_market: dict[str, dict[str, float]] = defaultdict(
        lambda: {"total": 0, "wins": 0, "losses": 0, "pnl": 0.0}
    )
    by_league: dict[str, dict[str, float]] = defaultdict(
        lambda: {"total": 0, "wins": 0, "losses": 0, "pnl": 0.0}
    )

    for pick, fx in rows:
        bm = by_market[pick.market]
        bl = by_league[fx.league_id]
        bm["total"] += 1
        bl["total"] += 1
        if pick.result == "win":
            wins += 1
            bm["wins"] += 1
            bl["wins"] += 1
        elif pick.result == "loss":
            losses += 1
            bm["losses"] += 1
            bl["losses"] += 1
        elif pick.result == "push":
            pushes += 1
        elif pick.result is None:
            pending += 1

        if pick.profit_pct is not None:
            pnl_total += pick.profit_pct
            bm["pnl"] += pick.profit_pct
            bl["pnl"] += pick.profit_pct

        if pick.clv_pct is not None:
            clv_values.append(pick.clv_pct)

    completed = wins + losses + pushes
    hit_rate = wins / (wins + losses) if (wins + losses) > 0 else None

    total_staked = 0.0
    for pick, _ in rows:
        if pick.result is not None:
            total_staked += pick.stake_pct
    roi = pnl_total / total_staked * 100 if total_staked > 0 else None
    avg_clv = sum(clv_values) / len(clv_values) if clv_values else None

    return StatsResponse(
        total_picks=total,
        wins=wins,
        losses=losses,
        pushes=pushes,
        pending=pending,
        hit_rate=round(hit_rate * 100, 2) if hit_rate is not None else None,
        roi_pct=round(roi, 2) if roi is not None else None,
        avg_clv_pct=round(avg_clv, 2) if avg_clv is not None else None,
        by_market=dict(by_market),
        by_league=dict(by_league),
    )
