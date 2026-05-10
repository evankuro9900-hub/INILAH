# Sports Parlay Analyst v3.0

> Webapp analisa pertandingan sepakbola berbasis filosofi Edge-Based Value Betting.
> 100% sumber data gratis. Bot picks otomatis. Validasi otomatis post-match.

⚠️ **DISCLAIMER:** Analisa ini berbasis statistik dan bersifat informatif. Tidak ada jaminan kemenangan dalam olahraga apapun. Bertaruhlah sesuai kemampuan finansial. Judi bisa menyebabkan kecanduan — bermainlah dengan bijak.

---

## 🏗️ Struktur Monorepo

```
sports-parlay-analyst/
├── apps/
│   ├── api/         # Backend FastAPI + SQLite + APScheduler
│   └── web/         # Frontend React + Vite + Tailwind
├── shared/          # Skill v3.0 markdown, config liga
├── docs/            # Plan, flow, technical docs
└── .github/         # CI workflows
```

## 🌍 Cakupan Liga (20 liga MVP)

**Tier 1:** EPL, La Liga, Serie A, Bundesliga, Ligue 1, UCL
**Tier 2:** Primeira Liga, Eredivisie, Scottish Premiership, MLS, Brazilian Série A, Argentine Primera, Liga MX, K-League 1, Saudi Pro League, Turkish Süper Lig, J-League
**Tier 3:** Liga 1 Indonesia, Thai League 1
**Tier Oceania:** A-League

## 🚀 Quick Start

### Backend (apps/api)
```bash
cd apps/api
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend (apps/web)
```bash
cd apps/web
pnpm install
pnpm dev
```

## 📚 Dokumentasi

- [`shared/SKILL.md`](shared/SKILL.md) — Sports Parlay Analyst skill v3.0 lengkap
- [`docs/webapp-plan.md`](docs/webapp-plan.md) — Plan webapp end-to-end
- [`docs/webapp-flow-final.md`](docs/webapp-flow-final.md) — Flow caching & lifecycle
- [`docs/data-sources.md`](docs/data-sources.md) — Mapping liga ke sumber data

## 🔧 Tech Stack

**Backend:** Python 3.11 + FastAPI + SQLAlchemy + SQLite + APScheduler + httpx + soccerdata
**Frontend:** React 18 + Vite + TypeScript + Tailwind CSS + TanStack Query + Recharts
**Hosting:** Fly.io (backend) + devinapps.com (frontend)
**CI:** GitHub Actions (lint + typecheck + tests)

## 📜 License

MIT — for personal/educational use. Not affiliated with any bookmaker.
