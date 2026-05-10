"""Fixtures endpoints."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.fetch_job import FetchJob
from app.models.fixture import Fixture
from app.models.pick import Pick
from app.schemas.fixture import (
    FetchStatusOut,
    FixtureOut,
    FixturesResponse,
    PickOut,
)
from app.services.cache import is_cache_valid
from app.services.fetch_service import fetch_and_persist_fixtures
from app.utils.timezone import now_utc, today_wib

router = APIRouter(prefix="/api", tags=["fixtures"])


def _validate_date(target_date: date) -> None:
    today = today_wib()
    earliest = today - timedelta(days=settings.date_range_past_days)
    latest = today + timedelta(days=settings.date_range_future_days)
    if target_date < earliest or target_date > latest:
        raise HTTPException(
            status_code=400,
            detail=f"Tanggal harus antara {earliest} dan {latest} (H-{settings.date_range_past_days} sampai H+{settings.date_range_future_days}).",
        )


async def _build_fetch_status(db: AsyncSession, target_date: date) -> FetchStatusOut:
    """Bangun FetchStatusOut dari latest fetch_job untuk tanggal."""
    valid, job = await is_cache_valid(db, target_date, "all")

    if job is None:
        return FetchStatusOut(
            target_date=target_date,
            cached=False,
            cache_fresh=False,
            status="missing",
        )

    today = today_wib()
    is_past = target_date < today

    if is_past or valid:
        status = "cached_fresh" if valid else "cached_stale"
    else:
        status = "cached_stale"

    if job.status == "failed":
        status = "failed"

    return FetchStatusOut(
        target_date=target_date,
        cached=True,
        cache_fresh=valid,
        last_fetched_at=job.completed_at,
        fixtures_count=job.fixtures_count,
        status=status,
        error=job.error_message,
    )


@router.get("/fixtures", response_model=FixturesResponse)
async def get_fixtures(
    date: date = Query(..., description="WIB date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """List fixtures untuk tanggal target.

    - Cache valid → return langsung dari DB
    - Cache stale & past → return cached
    - Cache stale & today/future → trigger background refresh, return cached
    - No cache → trigger sync fetch, return fresh
    """
    _validate_date(date)

    valid, job = await is_cache_valid(db, date, "all")

    if not valid:
        try:
            await fetch_and_persist_fixtures(db, date, triggered_by="auto_refresh")
        except Exception:
            # Tetap return data yang ada (mungkin partial)
            pass

    fetch_status = await _build_fetch_status(db, date)

    stmt = (
        select(Fixture)
        .where(Fixture.kickoff_wib_date == date)
        .order_by(Fixture.kickoff_utc.asc())
    )
    fixtures = (await db.execute(stmt)).scalars().all()

    # Manual fetch picks per fixture
    fixture_outs: list[FixtureOut] = []
    counts_by_status: dict[str, int] = {}
    counts_by_league: dict[str, int] = {}

    for fx in fixtures:
        pick_stmt = select(Pick).where(Pick.fixture_id == fx.id)
        picks = (await db.execute(pick_stmt)).scalars().all()
        pick_outs = [PickOut.model_validate(p) for p in picks]
        fixture_outs.append(
            FixtureOut(
                id=fx.id,
                external_id=fx.external_id,
                league_id=fx.league_id,
                home_team=fx.home_team,
                away_team=fx.away_team,
                kickoff_utc=fx.kickoff_utc,
                kickoff_wib_date=fx.kickoff_wib_date,
                status=fx.status,
                home_score=fx.home_score,
                away_score=fx.away_score,
                venue=fx.venue,
                picks=pick_outs,
            )
        )
        counts_by_status[fx.status] = counts_by_status.get(fx.status, 0) + 1
        counts_by_league[fx.league_id] = counts_by_league.get(fx.league_id, 0) + 1

    return FixturesResponse(
        target_date=date,
        fetch_status=fetch_status,
        fixtures=fixture_outs,
        counts={
            "total": len(fixture_outs),
            **{f"status_{k}": v for k, v in counts_by_status.items()},
            **{f"league_{k}": v for k, v in counts_by_league.items()},
        },
    )


@router.post("/fetch", response_model=FetchStatusOut)
async def force_fetch(
    date: date = Query(..., description="WIB date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """Force refresh fetch — bypass TTL."""
    _validate_date(date)
    try:
        await fetch_and_persist_fixtures(db, date, triggered_by="user_manual", force=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch gagal: {e}")
    return await _build_fetch_status(db, date)


@router.get("/fetch_status", response_model=FetchStatusOut)
async def get_fetch_status(
    date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Polling endpoint untuk frontend."""
    _validate_date(date)
    return await _build_fetch_status(db, date)


@router.get("/match/{match_id}", response_model=FixtureOut)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    fx = await db.get(Fixture, match_id)
    if fx is None:
        raise HTTPException(status_code=404, detail="Match tidak ditemukan")
    pick_stmt = select(Pick).where(Pick.fixture_id == fx.id)
    picks = (await db.execute(pick_stmt)).scalars().all()
    return FixtureOut(
        id=fx.id,
        external_id=fx.external_id,
        league_id=fx.league_id,
        home_team=fx.home_team,
        away_team=fx.away_team,
        kickoff_utc=fx.kickoff_utc,
        kickoff_wib_date=fx.kickoff_wib_date,
        status=fx.status,
        home_score=fx.home_score,
        away_score=fx.away_score,
        venue=fx.venue,
        picks=[PickOut.model_validate(p) for p in picks],
    )
