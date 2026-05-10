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
    "united",
}


def normalize_team_name(name: str) -> str:
    ascii_name = _ascii_slug(name)
    tokens = _significant_tokens(ascii_name)
    return " ".join(tokens) or ascii_name.strip()


def _ascii_slug(name: str) -> str:
    ascii_name = (
        unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    )
    return re.sub(r"[^a-z0-9]+", " ", ascii_name).strip()


def _significant_tokens(name: str) -> list[str]:
    return [token for token in name.split() if token not in TEAM_TOKEN_STOPWORDS]


def find_normalized_team_key(team_name: str, candidates: set[str]) -> str | None:
    normalized = normalize_team_name(team_name)
    if normalized in candidates:
        return normalized

    query_tokens = set(normalized.split())
    if not query_tokens:
        return None

    substring_matches = [
        candidate for candidate in candidates if normalized in candidate or candidate in normalized
    ]
    if len(substring_matches) == 1:
        return substring_matches[0]

    subset_matches = [
        candidate
        for candidate in candidates
        if query_tokens <= set(candidate.split()) or set(candidate.split()) <= query_tokens
    ]
    if len(subset_matches) == 1:
        return subset_matches[0]

    overlap_matches = [
        candidate
        for candidate in candidates
        if len(query_tokens & set(candidate.split()))
        == min(len(query_tokens), len(set(candidate.split())))
    ]
    if len(overlap_matches) == 1:
        return overlap_matches[0]

    query_token_list = sorted(query_tokens, key=len, reverse=True)
    shared_token_matches = [
        candidate
        for candidate in candidates
        if len(query_token_list[0]) >= 4
        and any(query_token_list[0] in candidate_token for candidate_token in candidate.split())
    ]
    if len(shared_token_matches) == 1:
        return shared_token_matches[0]

    return None


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
    key = find_normalized_team_key(team_name, set(team_index))
    if key is None:
        return None
    return team_index[key]
