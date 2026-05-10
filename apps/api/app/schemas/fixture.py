"""Pydantic schemas untuk API responses."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LeagueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    country: str
    tier: str


class PickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fixture_id: int
    market: str
    selection: str
    odds_at_pick: float
    odds_at_close: float | None = None
    estimated_rp: float
    edge_pct: float
    stake_pct: float
    scoring_card: dict[str, Any] | None = None
    reasoning: dict[str, Any] | None = None
    tags: list[str] | None = None
    result: str | None = None
    profit_pct: float | None = None
    clv_pct: float | None = None
    skill_version: str
    created_at: datetime
    validated_at: datetime | None = None

    @property
    def edge_pct_display(self) -> float:
        return round(self.edge_pct * 100, 2)


class FixtureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str | None = None
    league_id: str
    home_team: str
    away_team: str
    kickoff_utc: datetime
    kickoff_wib_date: date
    status: str
    home_score: int | None = None
    away_score: int | None = None
    venue: str | None = None
    picks: list[PickOut] = Field(default_factory=list)


class FetchStatusOut(BaseModel):
    target_date: date
    cached: bool
    cache_fresh: bool  # true kalau dalam TTL
    last_fetched_at: datetime | None = None
    fixtures_count: int | None = None
    status: str  # 'cached_fresh' | 'cached_stale' | 'pending' | 'failed' | 'missing'
    error: str | None = None


class FixturesResponse(BaseModel):
    target_date: date
    fetch_status: FetchStatusOut
    fixtures: list[FixtureOut]
    counts: dict[str, int]  # by status & by league


class StatsResponse(BaseModel):
    total_picks: int
    wins: int
    losses: int
    pushes: int
    pending: int
    hit_rate: float | None = None
    roi_pct: float | None = None
    avg_clv_pct: float | None = None
    by_market: dict[str, dict[str, Any]]
    by_league: dict[str, dict[str, Any]]


class BankrollOut(BaseModel):
    current_balance: float
    starting_balance: float
    total_pnl_pct: float
    picks_count: int
    last_updated: datetime | None = None
