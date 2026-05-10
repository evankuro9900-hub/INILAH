# 🏟️ Sports Parlay Analyst — Webapp Plan

> Webapp analisa pertandingan sepakbola berbasis skill v3.0 (edge-based, ½ Kelly stake).
> 100% sumber data gratis. Bot picks auto-generated. Validasi otomatis post-match.

---

## 1. SCOPE MVP vs v1 vs v2

### MVP (target 1–2 minggu)
- Jadwal pertandingan hari ini (top 6 liga Eropa + 1 liga Asia + Liga 1 Indonesia)
- Auto-generate bot picks per match dengan skill v3.0 logic
- Match detail page: scoring card + edge calc + pick + alasan
- Pick history dengan filter
- Auto-validation post-match (cron 15 menit)
- Hit rate & ROI dashboard
- Disclaimer + responsible gambling block

### v1 (target +2 minggu)
- League extension (semua tier 1+2)
- Calibration chart (predicted vs actual)
- CLV tracking (snapshot odds open vs close)
- Backtest module (1 musim ke belakang)
- Notification system (Telegram/email untuk high-edge picks)
- Bankroll tracker virtual

### v2 (kalau jalan)
- Multi-user (auth) dengan bankroll masing-masing
- Public leaderboard (opt-in gamification)
- Mobile app (PWA)
- Multi-language (ID + EN)
- API publik untuk picks (rate-limited)

---

## 2. TECH STACK (semua gratis)

### Backend — Python FastAPI
**Mengapa:** ekosistem scraping & data soccer terbaik (soccerdata, statsbombpy, understat).
- FastAPI + Uvicorn
- SQLAlchemy + SQLite (MVP) → Postgres (production via Supabase free)
- APScheduler untuk cron (validate picks, fetch jadwal)
- httpx untuk async HTTP
- BeautifulSoup4 untuk scraping
- Pydantic v2 untuk schema

### Frontend — React + Vite + Tailwind
**Mengapa:** static deploy gratis ke Vercel/Netlify, fast.
- React 18 + Vite
- Tailwind CSS + shadcn/ui (komponen)
- TanStack Query untuk data fetching
- Recharts untuk charts
- React Router

### Background Jobs
- APScheduler (di-bundle dengan FastAPI process)
- Job 1: setiap 6 jam — fetch jadwal H+1
- Job 2: setiap 1 jam — generate bot picks untuk match dalam 24 jam
- Job 3: setiap 15 menit — cek match yang sudah selesai, fetch hasil, validate picks
- Job 4: setiap match kickoff — snapshot odds_close untuk CLV

### Cache
- In-memory dict + TTL (untuk MVP)
- Redis (kalau scale up)

### Deployment
- **Backend:** Fly.io free tier (3 small VMs, 3GB persistent volume) atau Render free tier
- **Frontend:** Vercel atau Netlify (static)
- **Database:** SQLite di Fly volume (MVP) → upgrade ke Supabase atau Neon free Postgres
- **Domain:** subdomain *.fly.dev / *.vercel.app gratis

---

## 3. SUMBER DATA GRATIS

| Sumber | Cakupan | Method | Catatan |
|--------|---------|--------|---------|
| **FBref.com** | Form, xG, xGA, scoreline breakdown, advanced stats | Scrape via library `soccerdata` | Cache 24 jam, hindari rate limit |
| **Understat.com** | xG event-level, xPTS, shot maps | Library `understat` (Python async) | 5 liga top Eropa saja |
| **football-data.org** | Fixtures, klasemen, results | REST API, free tier 10/min | Butuh API key gratis |
| **ESPN unofficial scoreboard** | Fixtures live & today | REST `site.api.espn.com` | Tidak butuh API key |
| **TheSportsDB** | Logo tim, info dasar | REST API free | Untuk visualisasi |
| **OpenFootball GitHub** | Jadwal historical CSV | GitHub raw | Backup source |
| **StatsBomb open-data** | Event-level historical | Library `statsbombpy` | Historical only, kompetisi terbatas |
| **The Odds API (free)** | Odds bookmaker | REST, 500 req/bulan free | Untuk reference odds |
| **Wikipedia REST API** | Info wasit, stadium | Free | Optional |
| **OpenWeather (free tier)** | Cuaca per stadium | Free 1k call/hari | Untuk faktor cuaca |

### Estimasi rate limit
- FBref scraping: 1 request / 5 detik (politeness) → ~700 req/jam → cukup untuk 50+ tim/hari
- Understat: tidak ada hard limit, tapi pakai cache 24 jam
- football-data.org: 10/min × 60 = 600/jam → cukup
- Odds API: 500/bulan = ~16/hari → snapshot odds_close untuk top picks saja

### Mitigasi rate limit
- Cache aggressive (Redis atau dict)
- Daily batch fetch (3am UTC), bukan per-request
- Fallback: jika satu sumber gagal, coba sumber lain

---

## 4. ARSITEKTUR

```
┌──────────────────────────────────────────┐
│ FRONTEND (Vercel)                        │
│ React + Vite + Tailwind + Recharts       │
│ Routes:                                  │
│   /                — Dashboard hari ini  │
│   /match/:id       — Detail match        │
│   /picks           — Pick history        │
│   /stats           — Hit rate dashboard  │
│   /backtest        — Backtest module     │
│   /bankroll        — Virtual bankroll    │
└─────────────┬────────────────────────────┘
              │ HTTPS / JSON
              ▼
┌──────────────────────────────────────────┐
│ BACKEND (Fly.io)                         │
│ FastAPI + APScheduler                    │
│ Routes:                                  │
│   GET  /api/fixtures/today               │
│   GET  /api/match/:id                    │
│   GET  /api/match/:id/analysis           │
│   GET  /api/picks?date=&league=&result=  │
│   GET  /api/stats                        │
│   GET  /api/calibration                  │
│   POST /api/backtest                     │
│ Background jobs:                         │
│   - fetch_fixtures (6h)                  │
│   - generate_picks (1h)                  │
│   - validate_picks (15m)                 │
│   - snapshot_clv (kickoff)               │
└─────────────┬────────────────────────────┘
              │
       ┌──────┴──────┐
       ▼             ▼
  ┌─────────┐  ┌────────────────────┐
  │ SQLite  │  │ DATA SOURCES (web) │
  │  (Fly   │  │ FBref / Understat  │
  │ volume) │  │ ESPN / football-   │
  │         │  │ data.org / Odds API│
  └─────────┘  └────────────────────┘
```

---

## 5. SCHEMA DATABASE (SQLite/Postgres)

```sql
-- Fixtures (jadwal)
CREATE TABLE fixtures (
  id INTEGER PRIMARY KEY,
  external_id TEXT UNIQUE,           -- ID dari API source
  league_id INTEGER NOT NULL,
  home_team TEXT NOT NULL,
  away_team TEXT NOT NULL,
  kickoff_utc TIMESTAMP NOT NULL,
  status TEXT DEFAULT 'scheduled',   -- scheduled/live/finished/postponed
  home_score INTEGER,
  away_score INTEGER,
  ht_home_score INTEGER,
  ht_away_score INTEGER,
  source TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP
);

-- Leagues
CREATE TABLE leagues (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  country TEXT,
  tier TEXT,                         -- T1/T2/T3/T-Oceania/T-WomenA/T-WomenB
  season TEXT
);

-- Team stats snapshots (untuk reproducibility)
CREATE TABLE team_stats (
  id INTEGER PRIMARY KEY,
  team TEXT NOT NULL,
  league_id INTEGER,
  snapshot_date DATE NOT NULL,
  form_10 TEXT,                      -- 'W-D-L-W-W-D-L-W-W-D'
  scoreline_breakdown JSON,
  avg_goals_for_home REAL,
  avg_goals_against_home REAL,
  avg_goals_for_away REAL,
  avg_goals_against_away REAL,
  xg_10 REAL,
  xga_10 REAL,
  clean_sheet_rate REAL,
  raw_data JSON,
  UNIQUE(team, league_id, snapshot_date)
);

-- Bot Picks
CREATE TABLE picks (
  id INTEGER PRIMARY KEY,
  fixture_id INTEGER NOT NULL,
  market TEXT NOT NULL,              -- '1X2_HOME', 'OVER_2.5', 'BTTS_YES', 'AH_-0.5_HOME', dst
  selection TEXT NOT NULL,
  odds_at_pick REAL NOT NULL,
  odds_at_close REAL,
  estimated_rp REAL,
  edge_pct REAL,
  stake_pct REAL,
  scoring_card JSON,
  reasoning JSON,
  result TEXT,                       -- 'win'/'loss'/'push'/'void'/null
  profit_pct REAL,                   -- relatif ke bankroll
  clv_pct REAL,
  skill_version TEXT DEFAULT 'v3.0',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  validated_at TIMESTAMP,
  FOREIGN KEY (fixture_id) REFERENCES fixtures(id)
);

-- Bankroll history (virtual)
CREATE TABLE bankroll_log (
  id INTEGER PRIMARY KEY,
  date DATE NOT NULL,
  starting_balance REAL,
  ending_balance REAL,
  total_staked REAL,
  total_pnl REAL,
  picks_count INTEGER
);

-- Backtest runs
CREATE TABLE backtest_runs (
  id INTEGER PRIMARY KEY,
  config JSON,
  start_date DATE,
  end_date DATE,
  total_picks INTEGER,
  hit_rate REAL,
  roi_pct REAL,
  avg_clv_pct REAL,
  max_drawdown_pct REAL,
  results JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. CORE LOGIC — Bot Pick Generator

Implementasi langsung dari skill v3.0:

```python
# pseudocode
def generate_pick(fixture):
    # Step 0: Pre-flight check
    if is_dead_rubber(fixture) or is_pseudo_dead_rubber(fixture):
        return None  # skip
    if not has_sufficient_data(fixture):
        return Pick(stake_max=0.5, tag="LOW_DATA", ...)

    # Step 1: Fetch data (10-match form, xG, klasemen, injuries, weather, ref)
    home_stats = get_team_stats(fixture.home, last_n=10)
    away_stats = get_team_stats(fixture.away, last_n=10)
    context = get_match_context(fixture)

    # Step 2: Hitung weighted scoring card
    score = compute_scoring_card(home_stats, away_stats, context)
    adjustment_pct = clamp(score * 5, -15, 15)  # ±15% cap

    # Step 3: Hitung edge per market
    odds = get_odds(fixture)  # dari Odds API
    candidates = []
    for market in ALL_MARKETS:
        ip = 1 / odds[market]
        rp = estimate_rp(ip, adjustment_pct, market)
        edge = rp * odds[market] - 1
        if edge >= tier_threshold(fixture.league):
            candidates.append(Pick(market, odds, rp, edge))

    # Step 4: Pilih pick terbaik (edge tertinggi)
    if not candidates:
        return None
    best = max(candidates, key=lambda p: p.edge)

    # Step 5: Stake via ½ Kelly
    kelly = (best.rp * best.odds - 1) / (best.odds - 1)
    stake = min(kelly * 0.5, 0.03)  # cap 3%
    best.stake_pct = stake

    return best
```

---

## 7. AUTO-VALIDATION POST-MATCH

```python
# Cron setiap 15 menit
def validate_pending_picks():
    pending = db.query(Pick).filter(
        Pick.result == None,
        Fixture.status == 'finished',
        Fixture.kickoff_utc < now() - timedelta(hours=2)
    ).all()

    for pick in pending:
        score = (pick.fixture.home_score, pick.fixture.away_score)
        result = grade_market(pick.market, score)  # win/loss/push/void
        profit = compute_profit(pick.stake_pct, pick.odds_at_pick, result)
        clv = compute_clv(pick.odds_at_pick, pick.odds_at_close) if pick.odds_at_close else None

        pick.result = result
        pick.profit_pct = profit
        pick.clv_pct = clv
        pick.validated_at = now()
        db.commit()

def grade_market(market, score):
    home, away = score
    total = home + away

    matchers = {
        '1X2_HOME':       lambda: 'win' if home > away else 'loss',
        '1X2_AWAY':       lambda: 'win' if away > home else 'loss',
        '1X2_DRAW':       lambda: 'win' if home == away else 'loss',
        'OVER_2.5':       lambda: 'win' if total > 2 else 'loss',
        'UNDER_2.5':      lambda: 'win' if total < 3 else 'loss',
        'OVER_1.5':       lambda: 'win' if total > 1 else 'loss',
        'OVER_3.5':       lambda: 'win' if total > 3 else 'loss',
        'BTTS_YES':       lambda: 'win' if home > 0 and away > 0 else 'loss',
        'BTTS_NO':        lambda: 'win' if home == 0 or away == 0 else 'loss',
        'AH_0.0_HOME':    lambda: 'win' if home > away else 'push' if home == away else 'loss',
        'AH_-0.5_HOME':   lambda: 'win' if home > away else 'loss',
        'AH_-1.0_HOME':   lambda: 'win' if home - away > 1 else 'push' if home - away == 1 else 'loss',
        'AH_-1.5_HOME':   lambda: 'win' if home - away > 1 else 'loss',
        'AH_+0.5_AWAY':   lambda: 'win' if away >= home else 'loss',
        'AH_+1.0_AWAY':   lambda: 'win' if away >= home - 1 else 'push' if home - away == 1 else 'loss',
        # ... seterusnya
    }
    return matchers[market]()
```

---

## 8. FITUR TAMBAHAN YANG SAYA SARANKAN

Dari pertanyaan Anda *"apa yang perlu ditambahkan?"*:

### 🔴 ESSENTIAL (jangan dihilangkan)
1. **Disclaimer modal di first visit** — tampilkan wajib sebelum akses dashboard.
2. **Loss streak warning** — kalau 5 picks loss berturut-turut, tampilkan banner pause.
3. **Stake hard cap** — UI tidak izinkan stake > 3% bankroll, walaupun user override.
4. **Reproducibility** — simpan snapshot data & odds saat pick dibuat → backtest jujur tidak data leak.
5. **Skill versioning** — pick lama tetap pakai v3.0, kalau v3.1 keluar pick baru pakai v3.1.
6. **Timezone-aware** — display WIB, store UTC, hindari off-by-one bugs.

### 🟢 HIGH VALUE (worth adding)
7. **Calibration chart** — bucket picks by RP estimate (50–55%, 55–60%, dst), plot vs actual win rate. Garis ideal y=x. Deviasi = model bias.
8. **CLV per market** — lihat market mana model kita beat closing line, market mana lag.
9. **Hit rate per liga & per market** — drill-down: skill kuat di EPL O/U? Lemah di Serie A 1X2?
10. **Backtest module** — pilih rentang tanggal, run skill v3.0 di data historis, lihat performa.
11. **Form-rolling chart** — visualisasi xG/xGA rolling 10 match per tim.
12. **Heat map H2H tactical** — visual gaya main, bukan hasil mentah.
13. **Notification system** — Telegram bot / email untuk high-edge picks (≥ +10%).
14. **Bankroll tracker virtual** — start dengan misal 1000 unit, follow stake recommendation, lihat compounding over time.
15. **Daily pick digest** — pagi WIB email/notif: "Hari ini 8 match, 3 high-edge picks ready".

### 🟡 NICE TO HAVE
16. **Multi-language toggle** ID/EN.
17. **Dark mode** (default user prefer dark untuk dashboards).
18. **Mobile responsive PWA** — install seperti app.
19. **Export CSV** picks history untuk personal records.
20. **Public leaderboard** (opt-in) — bandingkan ROI virtual antar user (gamification).
21. **API publik** dengan rate limit untuk developer pihak ketiga.
22. **Match preview text generator** — natural language summary 3 paragraf untuk content creators.
23. **Kalender ICS export** — match favorit → import ke Google Calendar.

### 🔵 ADVANCED (later)
24. **Custom strategies** — user pilih bobot scoring card sendiri, run backtest.
25. **Ensemble model** — kombinasi skill v3.0 + simple Poisson + ML model, voting.
26. **Live in-play picks** — odds update real-time, generate pick saat match berjalan.
27. **Tactical formation analyzer** — detect gaya 4-3-3 vs 3-5-2, prediksi mismatch.
28. **Player-level injury impact model** — quantify dampak striker absen vs midfielder absen.
29. **Sharp/Square money tracker** — line movement analysis.
30. **Multi-bookie odds comparison** — line shopping (cari odds tertinggi per market).

### 🟣 RESPONSIBLE GAMBLING (wajib v1)
31. **Time-out feature** — user bisa lock akses 24h/72h/1 minggu/permanent.
32. **Daily loss limit** — set sendiri, auto-pause jika tercapai.
33. **Reality check timer** — every 30 min usage → popup "sudah 30 menit, masih oke?"
34. **Hotline links** — per negara (Indonesia: 119 ext 8, dll).
35. **Self-exclusion** — permanent block dengan email confirmation.

---

## 9. RISIKO & MITIGASI

| Risiko | Mitigasi |
|--------|----------|
| **Scraping banned (FBref)** | Politeness 5s delay, user-agent realistis, cache 24h, fallback ke alternative source |
| **Data tipis di liga kecil** | Tag "LOW_DATA", min stake 0.5 unit, skip jika sample < 8 |
| **Free tier API kuotanya habis** | Tier downgrade gracefully — tampilkan "data unavailable" lebih baik dari error |
| **Match postponed/canceled** | Status tracking, auto-void picks |
| **Timezone bugs** | Selalu UTC di DB, convert ke WIB di frontend |
| **Skill v3.0 underperform** | Calibration chart auto-detect, alert kalau hit rate drop |
| **Match-fixing di liga T3** | Flag liga risk-tinggi, exclude dari auto-pick |
| **Legal — perjudian online** | TIDAK jual akses berbayar, TIDAK terima taruhan, hanya "informational analysis tool". Disclaimer keras. **Cek hukum lokal Indonesia**. |

---

## 10. LEGAL & ETIKA — Penting untuk Anda Pertimbangkan

> **Indonesia: perjudian dilarang oleh KUHP & UU ITE.** Webapp ini akan jadi gray area kalau:
> - Menampilkan odds spesifik dari bookmaker
> - Merekomendasikan stake aktual
> - Menyediakan link affiliate ke bookmaker
>
> **Aman secara hukum:**
> - Framing sebagai "tool analisa statistik" untuk research / fantasy / akademik
> - Disclaimer keras: "tidak menyarankan perjudian"
> - Tidak ada link bookmaker
> - Bankroll virtual saja (bukan real money)
> - Geo-block kalau perlu
>
> **Saya STRONGLY RECOMMEND:**
> 1. Tampilkan disclaimer eksplisit
> 2. Frame sebagai "edge analysis tool / statistical insight"
> 3. Tidak pernah menyarankan stake real money
> 4. Konsultasi pengacara kalau mau go-public dengan banyak user
>
> Kalau ini untuk **pribadi / research / closed group** — risiko jauh lebih kecil.

---

## 11. TIMELINE ESTIMASI (kalau saya yang implementasi)

| Phase | Estimasi | Output |
|-------|----------|--------|
| **Phase 0 — Setup** | 0.5 hari | Repo monorepo (apps/api + apps/web), CI lint, deploy hello world |
| **Phase 1 — Data Pipeline** | 2 hari | Scraper FBref + Understat + ESPN, DB schema, daily fetch job |
| **Phase 2 — Skill Engine** | 2 hari | Implement v3.0 scoring, edge calc, pick generator, unit tests |
| **Phase 3 — API Layer** | 1 hari | FastAPI endpoints, schema, validation |
| **Phase 4 — Frontend MVP** | 2 hari | Dashboard, match detail, pick history, basic dark mode |
| **Phase 5 — Auto-validation** | 0.5 hari | Cron job, grade markets, profit calc, CLV |
| **Phase 6 — Stats Dashboard** | 1 hari | Hit rate, ROI, calibration chart |
| **Phase 7 — Deploy** | 0.5 hari | Fly.io backend + Vercel frontend, custom subdomain |
| **Phase 8 — Polish** | 1 hari | Disclaimer modal, responsible gambling features, mobile responsive |
| **TOTAL MVP** | **~10 hari kerja** | Webapp jalan dengan picks otomatis + validasi |

---

## 12. KEPUTUSAN YANG SAYA BUTUH DARI ANDA

1. **Scope MVP atau full?** Saya rekomendasikan MVP dulu (10 hari), v1 setelah validasi.
2. **Liga apa di MVP?** Saya rekomen: EPL, La Liga, Serie A, Bundesliga, Ligue 1, UCL, Liga 1 Indonesia, J-League. (8 liga)
3. **Repo:** monorepo (apps/api + apps/web) atau dua repo terpisah? Saya rekomen monorepo.
4. **Auth:** mau public access (no login) atau ada login? MVP saya rekomen no-login + cookie session untuk virtual bankroll.
5. **Domain:** pakai subdomain free (*.vercel.app, *.fly.dev) dulu atau Anda punya domain sendiri?
6. **Bahasa UI:** ID dulu, EN nanti?
7. **Bankroll virtual atau real-money tracking?** Saya STRONG REKOMEN virtual saja untuk legal safety.
8. **Notification channel:** Telegram bot? Email? Atau MVP tanpa notif dulu?
9. **Disclaimer level:** light (footer) atau heavy (modal blocker)? Saya rekomen heavy untuk legal.
10. **Anda mau saya buatkan:** repo + skeleton + deploy URL hari ini? Atau review plan dulu lebih lanjut?
