"""Orchestrator: fetch ESPN → simpan fixtures → generate picks."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.leagues import LEAGUES, get_league
from app.models.fetch_job import FetchJob
from app.models.fixture import Fixture
from app.models.pick import Pick
from app.services.cache import (
    create_pending_job,
    is_cache_valid,
    mark_job_failed,
    mark_job_success,
)
from app.services.scrapers.espn import EspnFixture, fetch_all_leagues_fixtures
from app.services.skill_engine import generate_pick
from app.utils.timezone import utc_to_wib

logger = logging.getLogger(__name__)


async def fetch_and_persist_fixtures(
    db: AsyncSession,
    target_date: date,
    triggered_by: str = "auto_refresh",
    force: bool = False,
) -> FetchJob:
    """Fetch fixtures untuk tanggal target dari semua liga ESPN, simpan ke DB.

    Mengikuti aturan v3.0 caching:
    - Past date: tidak refetch kecuali force=True
    - Today/Future: refetch jika cache > TTL atau force
    """
    if not force:
        valid, existing = await is_cache_valid(db, target_date, "all")
        if valid and existing:
            return existing

    job = await create_pending_job(db, target_date, "all", triggered_by)
    await db.commit()

    try:
        espn_slugs = [lg.espn_slug for lg in LEAGUES if lg.espn_slug]
        slug_to_league = {lg.espn_slug: lg for lg in LEAGUES if lg.espn_slug}

        all_fixtures = await fetch_all_leagues_fixtures(espn_slugs, target_date)

        total_count = 0
        for slug, fxs in all_fixtures.items():
            league = slug_to_league.get(slug)
            if not league:
                continue
            for fx in fxs:
                # Skip kalau kickoff WIB date tidak sama dengan target
                wib_dt = utc_to_wib(fx.kickoff_utc)
                wib_date = wib_dt.date()
                if wib_date != target_date:
                    # Different WIB date — bisa terjadi karena UTC timezone
                    # Tetap simpan dengan WIB date aktual, tapi tidak counted ke job ini
                    pass
                await _upsert_fixture(db, fx, league.id, job.id)
                total_count += 1

        # Generate picks untuk fixture yang belum ada pick
        await _generate_picks_for_date(db, target_date)

        await mark_job_success(db, job, total_count)
        return job
    except Exception as e:
        logger.exception("fetch_and_persist failed for %s", target_date)
        await mark_job_failed(db, job, str(e))
        raise


async def _upsert_fixture(
    db: AsyncSession, fx: EspnFixture, league_id: str, fetch_job_id: int
) -> None:
    """Insert atau update fixture berdasarkan external_id."""
    stmt = select(Fixture).where(Fixture.external_id == fx.external_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()

    wib_date = utc_to_wib(fx.kickoff_utc).date()

    if existing is None:
        new_fix = Fixture(
            external_id=fx.external_id,
            league_id=league_id,
            home_team=fx.home_team,
            away_team=fx.away_team,
            kickoff_utc=fx.kickoff_utc,
            kickoff_wib_date=wib_date,
            status=fx.status,
            home_score=fx.home_score,
            away_score=fx.away_score,
            venue=fx.venue,
            fetch_job_id=fetch_job_id,
        )
        db.add(new_fix)
    else:
        existing.status = fx.status
        existing.home_score = fx.home_score
        existing.away_score = fx.away_score
        existing.venue = fx.venue
        existing.kickoff_utc = fx.kickoff_utc
        existing.kickoff_wib_date = wib_date
    await db.flush()


async def _generate_picks_for_date(db: AsyncSession, target_date: date) -> None:
    """Generate picks untuk semua fixture pada tanggal target yang belum ada pick."""
    stmt = select(Fixture).where(Fixture.kickoff_wib_date == target_date)
    fixtures = (await db.execute(stmt)).scalars().all()

    for fx in fixtures:
        # Skip jika sudah ada pick
        existing_stmt = select(Pick).where(
            Pick.fixture_id == fx.id, Pick.skill_version == settings.skill_version
        )
        if (await db.execute(existing_stmt)).first() is not None:
            continue

        league = get_league(fx.league_id)
        if league is None:
            continue

        pick = generate_pick(
            league=league,
            home_team=fx.home_team,
            away_team=fx.away_team,
            home_form=[],  # TODO: integrate FBref/Understat in v1
            away_form=[],
            home_position=None,  # TODO: ESPN standings endpoint
            away_position=None,
            league_size=20,
            is_cup_knockout=fx.league_id == "ucl",
        )
        if pick is None:
            continue

        new_pick = Pick(
            fixture_id=fx.id,
            market=pick.market,
            selection=pick.selection,
            odds_at_pick=pick.odds,
            estimated_rp=pick.estimated_rp,
            edge_pct=pick.edge,
            stake_pct=pick.stake_pct,
            scoring_card=pick.scoring_card.to_dict(),
            reasoning={"reasons": pick.reasoning, "candidates": [c.to_dict() for c in pick.candidates[:6]]},
            tags=pick.tags,
            skill_version=settings.skill_version,
        )
        db.add(new_pick)
    await db.flush()


async def validate_finished_picks(db: AsyncSession) -> int:
    """Cron job: grade picks untuk match yang baru selesai."""
    from app.services.validator import compute_clv, compute_profit_pct, grade_market
    from app.utils.timezone import now_utc

    # Cari picks yang belum di-grade & match-nya finished
    stmt = (
        select(Pick, Fixture)
        .join(Fixture, Pick.fixture_id == Fixture.id)
        .where(Pick.result.is_(None), Fixture.status == "finished")
    )
    rows = (await db.execute(stmt)).all()
    count = 0

    for pick, fixture in rows:
        if fixture.home_score is None or fixture.away_score is None:
            continue
        result = grade_market(pick.market, fixture.home_score, fixture.away_score)
        profit_pct = compute_profit_pct(pick.stake_pct, pick.odds_at_pick, result)
        clv = compute_clv(pick.odds_at_pick, pick.odds_at_close)

        pick.result = result
        pick.profit_pct = profit_pct
        pick.clv_pct = clv
        pick.validated_at = now_utc()
        count += 1

    if count > 0:
        await db.commit()
    return count
