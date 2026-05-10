"""Client untuk Daily Football Analytics multi-league API."""

from __future__ import annotations

import logging
import re
import unicodedata

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

MULTI_LEAGUE_BASE_URL = "https://multi-league-football-ppzvrbpe.fly.dev"

INTERNAL_TO_MULTI_LEAGUE_KEY = {
    "epl": "epl",
    "laliga": "laliga",
    "seriea": "seriea_italy",
    "bundesliga": "bundesliga",
    "ligue1": "ligue1",
    "ucl": "ucl",
    "primeira": "primeira_liga",
    "eredivisie": "eredivisie",
    "scottish": "scottish_premiership",
    "mls": "mls",
    "brasileirao": "brasileirao",
    "argentine": "argentina_primera",
    "ligamx": "liga_mx",
    "saudi": "saudi_pro",
    "superlig": "turkish_super_lig",
    "jleague": "jleague",
    "liga1id": "liga1_indonesia",
}

TEAM_TOKEN_STOPWORDS = {
    "ac",
    "afc",
    "cf",
    "club",
    "clube",
    "cp",
    "fc",
    "fk",
    "futebol",
    "sad",
    "sc",
    "sd",
}


def normalize_team_name(name: str) -> str:
    ascii_name = (
        unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    ascii_name = re.sub(r"[^a-z0-9]+", " ", ascii_name)
    tokens = [token for token in ascii_name.split() if token not in TEAM_TOKEN_STOPWORDS]
    return " ".join(tokens) or ascii_name.strip()


async def fetch_multi_league_snapshot() -> dict[str, dict[str, object]]:
    """Ambil snapshot semua liga dan map ke league_id internal."""
    headers = {"User-Agent": settings.user_agent}
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        resp = await client.get(f"{MULTI_LEAGUE_BASE_URL}/api/leagues")
        resp.raise_for_status()
        payload = resp.json()

    by_key = {league.get("key"): league for league in payload.get("leagues", [])}
    out: dict[str, dict[str, object]] = {}
    for internal_id, source_key in INTERNAL_TO_MULTI_LEAGUE_KEY.items():
        league = by_key.get(source_key)
        if isinstance(league, dict):
            out[internal_id] = league
    logger.info("Loaded multi-league analytics for %d leagues", len(out))
    return out


def build_team_index(league_data: dict[str, object] | None) -> dict[str, dict[str, object]]:
    if not league_data:
        return {}

    team_stats_raw = league_data.get("team_stats")
    team_stats_list = team_stats_raw if isinstance(team_stats_raw, list) else []
    team_stats = {}
    for row in team_stats_list:
        if isinstance(row, dict) and row.get("name"):
            team_stats[normalize_team_name(str(row["name"]))] = row
    index: dict[str, dict[str, object]] = {}

    table_raw = league_data.get("table")
    table_list = table_raw if isinstance(table_raw, list) else []
    for row in table_list:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        if not name:
            continue
        normalized = normalize_team_name(str(name))
        combined = dict(row)
        stat_row = team_stats.get(normalized)
        if stat_row:
            combined.update(stat_row)
        combined["name"] = str(name)
        index[normalized] = combined

    for normalized, row in team_stats.items():
        index.setdefault(normalized, dict(row))

    return index


def find_team_stats(
    team_name: str, team_index: dict[str, dict[str, object]]
) -> dict[str, object] | None:
    normalized = normalize_team_name(team_name)
    if normalized in team_index:
        return team_index[normalized]

    for indexed_name, stats in team_index.items():
        if normalized and (normalized in indexed_name or indexed_name in normalized):
            return stats
    return None
