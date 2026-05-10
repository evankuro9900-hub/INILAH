"""Orchestrator: fetch ESPN → simpan fixtures → generate picks."""

from __future__ import annotations

import logging
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.leagues import LEAGUES, get_league
from app.models.fetch_job import FetchJob
from app.models.fixture import Fixture
from app.models.pick import Pick
from app.models.team_stats_snapshot import TeamStatsSnapshot
from app.services.cache import (
    create_pending_job,
    is_cache_valid,
    mark_job_failed,
    mark_job_success,
)
from app.services.scrapers.espn import EspnFixture, fetch_all_leagues_fixtures
from app.services.scrapers.multi_league import (
    build_team_index,
    fetch_multi_league_snapshot,
    find_normalized_team_key,
    normalize_team_name,
)
from app.services.skill_engine import generate_pick
from app.utils.timezone import UTC, utc_to_wib

logger = logging.getLogger(__name__)

JsonDict = dict[str, object]


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
        multi_league_data = await _load_multi_league_data()
        espn_slugs = [lg.espn_slug for lg in LEAGUES if lg.espn_slug]
        slug_to_league = {lg.espn_slug: lg for lg in LEAGUES if lg.espn_slug}
        all_fixtures = await fetch_all_leagues_fixtures(espn_slugs, target_date)

        total_count = 0
        seen_fixture_keys: set[tuple[str, str, str]] = set()
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
                seen_fixture_keys.add(
                    (
                        league.id,
                        normalize_team_name(fx.home_team),
                        normalize_team_name(fx.away_team),
                    )
                )
                if wib_date == target_date:
                    total_count += 1

        for league in LEAGUES:
            await _persist_team_stats_snapshot(
                db, target_date, league.id, multi_league_data.get(league.id)
            )
            inserted = await _persist_multi_league_fixtures(
                db,
                target_date,
                league.id,
                multi_league_data.get(league.id),
                job.id,
                seen_fixture_keys,
            )
            total_count += inserted

        # Generate picks untuk fixture yang belum ada pick
        await _generate_picks_for_date(db, target_date)

        await mark_job_success(db, job, total_count)
        return job
    except Exception as e:
        logger.exception("fetch_and_persist failed for %s", target_date)
        await mark_job_failed(db, job, str(e))
        raise


async def _load_multi_league_data() -> dict[str, JsonDict]:
    try:
        return await fetch_multi_league_snapshot()
    except Exception:
        logger.exception("multi-league analytics fetch failed; continuing with ESPN fixtures only")
        return {}


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


async def _persist_multi_league_fixtures(
    db: AsyncSession,
    target_date: date,
    league_id: str,
    league_data: JsonDict | None,
    fetch_job_id: int,
    seen_fixture_keys: set[tuple[str, str, str]],
) -> int:
    if not league_data:
        return 0

    inserted = 0
    fixtures = league_data.get("fixtures")
    if not isinstance(fixtures, list):
        return 0

    for item in fixtures:
        if not isinstance(item, dict):
            continue
        kickoff_raw = item.get("utc_time")
        home = item.get("home")
        away = item.get("away")
        external_id = item.get("id")
        if not kickoff_raw or not home or not away or not external_id:
            continue
        kickoff_utc = _parse_utc_datetime(str(kickoff_raw))
        if kickoff_utc is None or utc_to_wib(kickoff_utc).date() != target_date:
            continue
        key = (league_id, normalize_team_name(str(home)), normalize_team_name(str(away)))
        if key in seen_fixture_keys:
            continue
        fixture = EspnFixture(
            external_id=f"multi-league-{external_id}",
            league_slug=league_id,
            home_team=str(home),
            away_team=str(away),
            kickoff_utc=kickoff_utc,
            status=_map_multi_league_status(item),
            home_score=_int_or_none(item.get("home_score")),
            away_score=_int_or_none(item.get("away_score")),
            venue=None,
        )
        await _upsert_fixture(db, fixture, league_id, fetch_job_id)
        seen_fixture_keys.add(key)
        inserted += 1

    return inserted


async def _generate_picks_for_date(db: AsyncSession, target_date: date) -> None:
    """Generate picks untuk semua fixture pada tanggal target yang belum ada pick."""
    stmt = select(Fixture).where(Fixture.kickoff_wib_date == target_date)
    fixtures = (await db.execute(stmt)).scalars().all()

    stats_by_league: dict[str, dict[str, TeamStatsSnapshot]] = {}
    stats_stmt = select(TeamStatsSnapshot).where(TeamStatsSnapshot.snapshot_date == target_date)
    snapshots = (await db.execute(stats_stmt)).scalars().all()
    for snapshot in snapshots:
        league_stats = stats_by_league.setdefault(snapshot.league_id, {})
        league_stats[normalize_team_name(snapshot.team)] = snapshot

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

        league_stats = stats_by_league.get(fx.league_id, {})
        home_key = find_normalized_team_key(fx.home_team, set(league_stats))
        away_key = find_normalized_team_key(fx.away_team, set(league_stats))
        home_stats = league_stats[home_key] if home_key is not None else None
        away_stats = league_stats[away_key] if away_key is not None else None

        pick = generate_pick(
            league=league,
            home_team=fx.home_team,
            away_team=fx.away_team,
            home_form=[],  # TODO: integrate FBref/Understat in v1
            away_form=[],
            home_position=home_stats.league_position if home_stats else None,
            away_position=away_stats.league_position if away_stats else None,
            league_size=20,
            is_cup_knockout=fx.league_id == "ucl",
            home_team_stats=home_stats.raw_data if home_stats else None,
            away_team_stats=away_stats.raw_data if away_stats else None,
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
            reasoning={
                "reasons": pick.reasoning,
                "candidates": [c.to_dict() for c in pick.candidates[:6]],
            },
            tags=pick.tags,
            skill_version=settings.skill_version,
        )
        db.add(new_pick)
    await db.flush()


async def _persist_team_stats_snapshot(
    db: AsyncSession,
    target_date: date,
    league_id: str,
    league_data: dict[str, object] | None,
) -> None:
    team_index = build_team_index(league_data)
    if not team_index:
        return

    for stats in team_index.values():
        team = stats.get("name")
        if not team:
            continue

        existing_stmt = select(TeamStatsSnapshot).where(
            TeamStatsSnapshot.team == str(team),
            TeamStatsSnapshot.league_id == league_id,
            TeamStatsSnapshot.snapshot_date == target_date,
        )
        snapshot = (await db.execute(existing_stmt)).scalar_one_or_none()
        form_10 = _format_form(stats.get("form"))
        avg_goals_for = _float_or_none(stats.get("goals_per_match"))
        avg_goals_against = _float_or_none(stats.get("goals_conceded_per_match"))
        xg = _float_or_none(stats.get("xg"))
        xga = _float_or_none(stats.get("xg_conceded"))
        league_position = _int_or_none(stats.get("rank"))
        points = _int_or_none(stats.get("points"))
        raw_data = dict(stats)
        if snapshot is None:
            db.add(
                TeamStatsSnapshot(
                    team=str(team),
                    league_id=league_id,
                    snapshot_date=target_date,
                    form_10=form_10,
                    avg_goals_for_home=avg_goals_for,
                    avg_goals_against_home=avg_goals_against,
                    avg_goals_for_away=avg_goals_for,
                    avg_goals_against_away=avg_goals_against,
                    xg_10=xg,
                    xga_10=xga,
                    league_position=league_position,
                    points=points,
                    points_gap_to_top=None,
                    raw_data=raw_data,
                )
            )
        else:
            snapshot.form_10 = form_10
            snapshot.avg_goals_for_home = avg_goals_for
            snapshot.avg_goals_against_home = avg_goals_against
            snapshot.avg_goals_for_away = avg_goals_for
            snapshot.avg_goals_against_away = avg_goals_against
            snapshot.xg_10 = xg
            snapshot.xga_10 = xga
            snapshot.league_position = league_position
            snapshot.points = points
            snapshot.points_gap_to_top = None
            snapshot.raw_data = raw_data

    await db.flush()


def _format_form(form: object) -> str | None:
    if isinstance(form, list):
        values = [str(item).strip().upper() for item in form if str(item).strip()]
        return "-".join(values[:10]) if values else None
    if isinstance(form, str) and form.strip():
        return form.strip()
    return None


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float, str)):
            return float(value)
    except (TypeError, ValueError):
        return None
    return None


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    try:
        if isinstance(value, int):
            return value
        if isinstance(value, (float, str)):
            return int(value)
    except (TypeError, ValueError):
        return None
    return None


def _parse_utc_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _map_multi_league_status(item: dict[object, object]) -> str:
    if item.get("finished") is True:
        return "finished"
    status = str(item.get("status", "")).lower()
    if status in {"ft", "aet", "pen"}:
        return "finished"
    if status in {"live", "playing"}:
        return "live"
    if status in {"postponed", "ppd"}:
        return "postponed"
    if status in {"canceled", "cancelled"}:
        return "canceled"
    return "scheduled"


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
