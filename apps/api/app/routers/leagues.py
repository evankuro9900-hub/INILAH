"""Leagues endpoint."""

from fastapi import APIRouter

from app.leagues import LEAGUES
from app.schemas.fixture import LeagueOut

router = APIRouter(prefix="/api/leagues", tags=["leagues"])


@router.get("", response_model=list[LeagueOut])
async def list_leagues():
    return [
        LeagueOut(id=lg.id, name=lg.name, country=lg.country, tier=lg.tier)
        for lg in LEAGUES
    ]
