# Sports Parlay Analyst — Backend (apps/api)

FastAPI + SQLite + APScheduler.

## Setup

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /api/health` — health check
- `GET /api/leagues` — daftar liga aktif
- `GET /api/fixtures?date=YYYY-MM-DD` — fixtures + cache status
- `GET /api/match/:id` — detail match
- `GET /api/picks` — pick history
- `POST /api/fetch?date=YYYY-MM-DD` — force refresh

## Struktur

```
app/
├── main.py              # FastAPI app + CORS + scheduler init
├── config.py            # Settings (Pydantic)
├── db.py                # SQLAlchemy session
├── models/              # ORM models
├── schemas/             # Pydantic schemas
├── routers/             # API routes
├── services/
│   ├── scrapers/        # FBref, Understat, ESPN, football-data, OddsAPI
│   ├── skill_engine.py  # Skill v3.0 logic (scoring, edge calc, pick gen)
│   ├── validator.py     # Auto-validate picks post-match
│   └── cache.py         # Cache TTL logic
├── jobs/                # APScheduler jobs
└── leagues.py           # 20 liga config
```

## Tests

```bash
uv run pytest
```
