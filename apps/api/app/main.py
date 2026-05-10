"""FastAPI app entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import settings
from app.db import AsyncSessionLocal, init_db
from app.jobs.scheduler import start_scheduler
from app.leagues import LEAGUES
from app.routers import fixtures, health, leagues, picks, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def _seed_leagues() -> None:
    """Seed leagues table dari leagues.py config."""
    from sqlalchemy import select

    from app.models.league import League as LeagueModel

    async with AsyncSessionLocal() as db:
        for lg in LEAGUES:
            existing = await db.execute(select(LeagueModel).where(LeagueModel.id == lg.id))
            if existing.scalar_one_or_none() is None:
                db.add(
                    LeagueModel(
                        id=lg.id,
                        name=lg.name,
                        country=lg.country,
                        tier=lg.tier,
                        min_edge_pct=lg.min_edge_pct,
                        over_baseline=lg.over_baseline,
                        notes=lg.notes,
                    )
                )
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.app_name)
    await init_db()
    await _seed_leagues()
    scheduler = start_scheduler()
    try:
        yield
    finally:
        logger.info("Shutting down — stopping scheduler")
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    version="3.0.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(leagues.router)
app.include_router(fixtures.router)
app.include_router(picks.router)
app.include_router(stats.router)


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": "3.0.0",
        "skill_version": settings.skill_version,
        "endpoints": [
            "/api/health",
            "/api/leagues",
            "/api/fixtures?date=YYYY-MM-DD",
            "/api/fetch_status?date=YYYY-MM-DD",
            "POST /api/fetch?date=YYYY-MM-DD",
            "/api/match/{id}",
            "/api/picks",
            "/api/stats",
        ],
        "disclaimer": (
            "Analisa berbasis statistik. Tidak ada jaminan menang. "
            "Bermainlah bertanggung jawab. Judi bisa menyebabkan kecanduan."
        ),
    }
