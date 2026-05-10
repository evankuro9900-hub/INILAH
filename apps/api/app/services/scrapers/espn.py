"""ESPN scoreboard scraper — sumber utama fixtures untuk semua liga.

Endpoint unofficial yang tetap public:
    https://site.api.espn.com/apis/site/v2/sports/soccer/{league_slug}/scoreboard
    ?dates=YYYYMMDD

Tidak butuh API key. Rate limit reasonable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx

from app.config import settings
from app.utils.timezone import UTC

logger = logging.getLogger(__name__)

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"


@dataclass
class EspnFixture:
    """Hasil parse ESPN scoreboard event."""

    external_id: str
    league_slug: str
    home_team: str
    away_team: str
    kickoff_utc: datetime
    status: str  # scheduled | live | finished | postponed
    home_score: int | None
    away_score: int | None
    venue: str | None


def _map_status(state: str, completed: bool) -> str:
    """Map ESPN status state ke internal status."""
    if completed:
        return "finished"
    if state == "in":
        return "live"
    if state == "post":
        return "finished"
    if state == "pre":
        return "scheduled"
    return "scheduled"


def _parse_event(event: dict[str, Any], league_slug: str) -> EspnFixture | None:
    """Parse satu event ESPN."""
    try:
        eid = str(event["id"])
        date_str = event["date"]  # ISO with Z
        kickoff = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(tzinfo=UTC)

        comps = event.get("competitions", [])
        if not comps:
            return None
        comp = comps[0]

        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            return None

        home_obj = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
        away_obj = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

        home_team = home_obj.get("team", {}).get("displayName") or home_obj.get("team", {}).get(
            "name"
        )
        away_team = away_obj.get("team", {}).get("displayName") or away_obj.get("team", {}).get(
            "name"
        )

        if not home_team or not away_team:
            return None

        try:
            home_score = int(home_obj.get("score") or 0)
            away_score = int(away_obj.get("score") or 0)
        except (ValueError, TypeError):
            home_score = away_score = None

        status_obj = comp.get("status", {})
        type_obj = status_obj.get("type", {})
        state = type_obj.get("state", "pre")
        completed = bool(type_obj.get("completed"))
        status = _map_status(state, completed)

        # Reset skor kalau belum mulai
        if status == "scheduled":
            home_score = away_score = None

        venue = comp.get("venue", {}).get("fullName")

        return EspnFixture(
            external_id=f"espn-{eid}",
            league_slug=league_slug,
            home_team=str(home_team),
            away_team=str(away_team),
            kickoff_utc=kickoff,
            status=status,
            home_score=home_score,
            away_score=away_score,
            venue=venue,
        )
    except Exception as e:
        logger.warning("Failed to parse ESPN event: %s", e)
        return None


async def fetch_league_fixtures_for_date(
    league_slug: str, target_date: date, client: httpx.AsyncClient | None = None
) -> list[EspnFixture]:
    """Fetch fixtures untuk satu liga + tanggal."""
    url = f"{ESPN_BASE}/{league_slug}/scoreboard"
    params = {"dates": target_date.strftime("%Y%m%d")}
    headers = {"User-Agent": settings.user_agent}

    own_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=20.0, headers=headers)
        own_client = True

    try:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])
        fixtures = [_parse_event(e, league_slug) for e in events]
        return [f for f in fixtures if f is not None]
    except httpx.HTTPError as e:
        logger.warning("ESPN fetch failed for %s on %s: %s", league_slug, target_date, e)
        return []
    finally:
        if own_client:
            await client.aclose()


async def fetch_all_leagues_fixtures(
    league_slugs: list[str], target_date: date
) -> dict[str, list[EspnFixture]]:
    """Fetch fixtures untuk semua liga sekaligus (parallel)."""
    import asyncio

    headers = {"User-Agent": settings.user_agent}
    async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
        tasks = [fetch_league_fixtures_for_date(slug, target_date, client) for slug in league_slugs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    out: dict[str, list[EspnFixture]] = {}
    for slug, result in zip(league_slugs, results, strict=True):
        if isinstance(result, Exception):
            logger.warning("ESPN exception for %s: %s", slug, result)
            out[slug] = []
        else:
            out[slug] = result
    return out
