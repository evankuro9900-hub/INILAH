# 🏟️ Sports Parlay Analyst — FLOW FINAL (untuk Review)

> Versi flow sudah disesuaikan dengan keputusan Anda:
> - **(A)** Default view pindah tanggal, data lama tetap di DB
> - **TTL 4 jam** untuk fetch refresh
> - **Range H-3 sampai H+7** di date picker
> - **Tombol "Fetch sekarang"** tampil ke user
> - **Past + Today + Future** — semua tampil di date picker

---

## 1. 🗓️ DATE PICKER UI (Final)

```
┌──────────────────────────────────────────────────────────┐
│  📅 Pilih Tanggal Pertandingan (WIB)                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │  ◄  Senin, 11 Mei 2026             ►   [Hari ini]  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Quick: [H-3] [H-2] [H-1] [Hari ini] [H+1] [H+2] ... [H+7]│
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  ✅ Cached (last fetched 06:23 WIB, 4j 12m lalu)    │  │
│  │  Auto-refresh otomatis dalam 0j 48m                 │  │
│  │                                  [🔄 Fetch sekarang]│  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  📊 12 pertandingan | 8 sudah di-analisa | 4 high-edge   │
└──────────────────────────────────────────────────────────┘
```

**Tanggal di-disable:**
- Lebih dari 3 hari ke belakang (H-4 s/d seterusnya) → grayed out
- Lebih dari 7 hari ke depan (H+8 s/d seterusnya) → grayed out

**Status indicator:**
- `🔴 Belum fetch` — tombol "Fetch sekarang" prominent
- `🟡 Fetching...` — spinner, disable button
- `🟢 Cached (5m lalu)` — fresh, auto-refresh next 4h
- `🟠 Cached (5j lalu, akan refresh)` — TTL expired, akan auto-refresh saat user buka
- `⚫ Failed` — error message, retry button

---

## 2. 💾 CACHING STRATEGY (Final)

### Aturan Cache per Tanggal

| Tanggal | TTL Cache | Logika |
|---------|-----------|--------|
| **H-3 sampai H-1** (past) | ∞ (never refetch) | Hasil sudah final |
| **Today (H+0)** | **4 jam** auto-refresh | Lineup, odds, injury bisa berubah |
| **H+1 sampai H+7** (future) | **4 jam** auto-refresh | Preview data |
| **Manual override** | Force fresh | Ignore TTL, fetch ulang |

### Logic Backend

```
GET /api/fixtures?date=2026-05-11

1. Parse target_date (validate H-3 s/d H+7, reject lain)

2. Cek fetch_jobs WHERE target_date='2026-05-11' AND source='all'
   AND status='success'
   AND (
     -- Past dates: any successful job
     target_date < today() WIB
     OR
     -- Today/Future: completed_at within last 4 hours
     completed_at > NOW() - INTERVAL 4 HOURS
   )

3. JIKA cache valid → return data dari DB (no fetch)

4. JIKA cache stale/missing → trigger fetch async
   → return (cached_old_data, refreshing=true)
   → user lihat data lama sambil refresh background
   → setelah selesai, frontend re-fetch via polling/SSE

5. JIKA force_refresh=true (tombol manual) → fetch sekarang juga
   → ignore cache_valid check
   → tunggu sampai selesai, return fresh data
```

---

## 3. 🔄 END-TO-END FLOW DIAGRAM

### A. User pertama kali buka app (default = hari ini)

```
[USER buka app jam 08:00 WIB tanggal 11 Mei]
         │
         ▼
[Frontend: default date = "11 Mei 2026"]
         │
         ▼
[GET /api/fixtures?date=2026-05-11]
         │
         ▼
[Backend: cek fetch_jobs] ─── tidak ada ───┐
         │                                  │
         ▼                                  ▼
[Trigger async fetch]              [Return cache jika ada]
         │
    ┌────┴────────────────────────┐
    │                              │
    ▼                              ▼
[ESPN API]                  [football-data.org]
└─ scoreboard hari ini      └─ klasemen + scheduled
    │                              │
    ▼                              ▼
[FBref scrape per tim]      [Understat per tim]
└─ form 10, xG, scoreline   └─ xG event-level
    │                              │
    └──────────┬───────────────────┘
               │
               ▼
    [The Odds API]
    └─ odds 1X2/O/U/AH/BTTS
               │
               ▼
    [OpenWeather API]
    └─ cuaca per stadium
               │
               ▼
    [Simpan ke DB]:
    ├─ fixtures (12 baris)
    ├─ team_stats_snapshots (24 baris, 2 per match)
    ├─ odds_snapshots (per market per match)
    └─ fetch_jobs.status = 'success'
               │
               ▼
    [Backend: Pick Generator]
    ├─ Loop tiap fixture
    ├─ Run skill v3.0 logic (pre-flight, scoring, edge calc)
    └─ Insert ke picks (untuk fixture yang +EV)
               │
               ▼
    [Return response]
    └─ {fixtures: [...], picks: [...], status: 'fresh'}
               │
               ▼
[Frontend: render dashboard]
└─ 12 match cards, 4 high-edge picks highlighted
```

### B. User buka app jam 13:00 (5 jam kemudian — cache expired)

```
[USER buka app jam 13:00 WIB tanggal 11 Mei]
         │
         ▼
[GET /api/fixtures?date=2026-05-11]
         │
         ▼
[Backend: cek fetch_jobs] ── ada, tapi 5 jam lalu (>4h TTL) ──┐
         │                                                     │
         ▼                                                     ▼
[Trigger async refresh]                              [Return data lama]
         │                                                     │
    [Background refetch jalan]                                 │
         │                                                     │
         ▼                                                     ▼
[Frontend tampil data 5j lalu          ◄────  status: "refreshing"]
    │
    ▼
[Polling /api/fetch_status?date=2026-05-11]
    │
    ▼  setelah ~30 detik
[Backend selesai refresh]
    │
    ▼
[Frontend re-fetch /api/fixtures] ── return data baru ──► UI auto-update
```

### C. User pilih tanggal H-2 (kemarin lusa, sudah final)

```
[USER pilih dropdown "9 Mei"]
         │
         ▼
[GET /api/fixtures?date=2026-05-09]
         │
         ▼
[Backend: cek fetch_jobs] ── ada, past date ──► CACHE VALID FOREVER
         │
         ▼
[Return data dari DB]
         │
         ▼
[Frontend tampil]:
└─ 14 match (semua finished)
└─ 6 picks (3 win, 2 loss, 1 push)
└─ ROI: +2.3% bankroll
```

### D. Match selesai → auto-validation

```
[Cron tiap 15 menit: validate_pending_picks]
         │
         ▼
[Query fixtures]:
└─ status != 'finished' AND kickoff_utc < NOW() - 110 menit
         │
         ▼
[Untuk tiap fixture]:
├─ Fetch hasil dari ESPN/football-data.org
├─ Update fixtures: home_score, away_score, status='finished'
└─ Untuk tiap pick di fixture ini:
   ├─ Grade market (1X2/O/U/BTTS/AH) → win/loss/push
   ├─ Hitung profit_pct = stake_pct × (odds-1) jika win, -stake_pct jika loss
   ├─ Hitung CLV = (1/odds_close - 1/odds_pick) / (1/odds_pick) × 100
   └─ Update picks: result, profit_pct, clv_pct, validated_at
         │
         ▼
[Update bankroll_log harian]:
└─ ending_balance = starting + Σ profit_pct
```

---

## 4. ⏰ CRON JOBS (Final)

| Job | Frequency | Tujuan |
|-----|-----------|--------|
| **fetch_default_today** | Setiap 4 jam | Background refresh data hari ini (untuk user yang sudah buka) |
| **fetch_tomorrow** | Setiap hari jam 03:00 WIB | Pre-fetch data H+1 supaya user pagi-pagi sudah ada |
| **validate_picks** | Setiap 15 menit | Cek match selesai, grade picks |
| **snapshot_clv** | Per kickoff (event-driven) | Simpan odds_close untuk CLV tracking |
| **midnight_rollover** | Setiap hari jam 00:00 WIB | Set `current_default_date` = besok untuk semua user |
| **cleanup_old_snapshots** | Setiap minggu | Hapus team_stats_snapshots > 30 hari (kecuali yang tied to picks) |

---

## 5. 🗂️ SCHEMA DATABASE FINAL (Relevant)

```sql
-- Cache & fetch tracking
CREATE TABLE fetch_jobs (
  id INTEGER PRIMARY KEY,
  target_date DATE NOT NULL,           -- WIB date
  source TEXT NOT NULL,                -- 'all' | 'fixtures' | 'stats' | 'odds'
  status TEXT NOT NULL,                -- 'pending' | 'success' | 'failed'
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  fixtures_count INTEGER,
  error_message TEXT,
  triggered_by TEXT,                   -- 'cron' | 'user_manual' | 'auto_refresh'
  UNIQUE(target_date, source, started_at)  -- multiple jobs per date allowed (history)
);

-- Index untuk cek cepat
CREATE INDEX idx_fetch_jobs_date_status
  ON fetch_jobs(target_date, source, status, completed_at);

CREATE TABLE fixtures (
  id INTEGER PRIMARY KEY,
  external_id TEXT UNIQUE,
  league_id INTEGER,
  home_team TEXT, away_team TEXT,
  kickoff_utc TIMESTAMP NOT NULL,
  kickoff_wib_date DATE NOT NULL,      -- DENORMALIZED untuk filter cepat by WIB date
  status TEXT,                         -- scheduled/live/finished/postponed/canceled
  home_score INTEGER, away_score INTEGER,
  ht_home_score INTEGER, ht_away_score INTEGER,
  fetched_at TIMESTAMP,
  last_updated TIMESTAMP
);

CREATE INDEX idx_fixtures_wib_date ON fixtures(kickoff_wib_date, status);

CREATE TABLE team_stats_snapshots (
  id INTEGER PRIMARY KEY,
  team TEXT NOT NULL,
  league_id INTEGER,
  snapshot_date DATE NOT NULL,
  form_10 TEXT,                        -- 'W-D-L-W-W-D-L-W-W-D'
  scoreline_breakdown JSON,
  avg_goals_for_home REAL, avg_goals_against_home REAL,
  avg_goals_for_away REAL, avg_goals_against_away REAL,
  xg_10 REAL, xga_10 REAL,
  clean_sheet_rate REAL,
  raw_data JSON,
  UNIQUE(team, league_id, snapshot_date)
);

CREATE TABLE odds_snapshots (
  id INTEGER PRIMARY KEY,
  fixture_id INTEGER NOT NULL,
  market TEXT NOT NULL,                -- '1X2_HOME', 'OVER_2.5', dll
  odds REAL NOT NULL,
  source TEXT,                         -- 'oddsapi' | 'manual'
  snapshot_type TEXT,                  -- 'open' | 'pick_time' | 'close'
  captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (fixture_id) REFERENCES fixtures(id)
);

CREATE TABLE picks (
  id INTEGER PRIMARY KEY,
  fixture_id INTEGER NOT NULL,
  market TEXT NOT NULL,
  selection TEXT NOT NULL,
  odds_at_pick REAL NOT NULL,
  odds_at_close REAL,
  estimated_rp REAL,
  edge_pct REAL,
  stake_pct REAL,
  scoring_card JSON,
  reasoning JSON,
  result TEXT,                         -- win/loss/push/void/null
  profit_pct REAL,
  clv_pct REAL,
  skill_version TEXT DEFAULT 'v3.0',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  validated_at TIMESTAMP,
  FOREIGN KEY (fixture_id) REFERENCES fixtures(id)
);

CREATE INDEX idx_picks_fixture ON picks(fixture_id);
CREATE INDEX idx_picks_result ON picks(result, validated_at);

CREATE TABLE bankroll_log (
  id INTEGER PRIMARY KEY,
  date DATE UNIQUE,
  starting_balance REAL,
  ending_balance REAL,
  total_staked REAL,
  total_pnl REAL,
  picks_count INTEGER
);
```

---

## 6. 🔌 API ENDPOINTS FINAL

```
# Public
GET  /api/fixtures?date=YYYY-MM-DD            → list fixtures + cache status
GET  /api/match/:id                            → detail match + analysis + picks
GET  /api/picks?date=&league=&result=          → filter pick history
GET  /api/stats?date_from=&date_to=&league=    → hit rate, ROI, CLV per market
GET  /api/calibration                          → predicted vs actual win rate
GET  /api/fetch_status?date=YYYY-MM-DD         → status fetch job (untuk polling)
GET  /api/leagues                              → list liga aktif

# Manual triggers
POST /api/fetch?date=YYYY-MM-DD                → force refresh, bypass TTL
POST /api/regenerate-picks?date=YYYY-MM-DD     → re-run skill engine

# Bankroll (cookie session)
GET  /api/bankroll                             → balance virtual user ini
POST /api/bankroll/reset                       → reset virtual bankroll

# Backtest
POST /api/backtest                             → body: { date_from, date_to, leagues, skill_version }
GET  /api/backtest/:id                         → hasil backtest

# Health
GET  /api/health                               → uptime, last fetch, count records
```

---

## 7. 🧠 PICK GENERATION FLOW (Skill v3.0 Engine)

```
Input: fixture (home, away, kickoff, league)
       team_stats_snapshots (home & away, today)
       odds_snapshots (market list)
       context (klasemen, news, weather, ref)

────────────────────────────────────────────
Step 0: Pre-flight Check
        ├─ dead_rubber? → SKIP
        ├─ pseudo_dead_rubber? (UCL/UEL R16+ dlm 4 hari) → SKIP
        ├─ kompetisi cup knockout? → tag HIGH_VARIANCE
        └─ data_sufficient? (≥8 match liga tiap tim) → tag LOW_DATA jika tidak

Step 1: Compute Scoring Card
        Form (30%):     analyze 10-match scoreline breakdown
        xG/xGA (25%):   xg_diff vs xga_diff
        Motivasi (20%): klasemen target + dead rubber check
        Home/Away(10%): venue-specific record
        Kondisi (10%):  injury/suspension impact
        H2H (5%):       tactical pattern only
        Bonus:
          Fatigue (-5%):  3 match/7 hari?
          Wasit (±2%):    cards/pen tendency for O/U
          Cuaca (-5%):    rain/wind for outdoor

        weighted_score = Σ (faktor × bobot)
        adjustment_pct = clamp(score × 5%, ±15%)

Step 2: Edge Calc per Market
        FOR each market in [1X2_H, 1X2_D, 1X2_A,
                            OVER_1.5, OVER_2.5, OVER_3.5,
                            UNDER_2.5, BTTS_YES, BTTS_NO,
                            AH_-0.5_H, AH_0.0_H, AH_-1.0_H,
                            AH_+0.5_A, AH_+1.0_A]:
            ip = 1 / odds[market]
            rp = ip + adjustment_pct  (with market-specific tweak)
            edge = rp × odds[market] - 1

            IF apply_filters(market, scoring_card):  # xG filter, six-pointer veto, dll
                CONTINUE

            IF edge >= tier_threshold (5% T1/T2, 8% T3):
                candidates.append({market, odds, rp, edge})

Step 3: Pick Selection
        IF no candidates: return None
        best = max(candidates, key=edge)
        kelly = (best.rp × best.odds - 1) / (best.odds - 1)
        stake = min(kelly × 0.5, 0.03)  # cap 3%

Step 4: Insert ke DB
        picks.insert({
            fixture_id, market, odds_at_pick, estimated_rp,
            edge_pct, stake_pct, scoring_card, reasoning,
            skill_version: 'v3.0'
        })
```

---

## 8. ✅ VALIDATION FLOW (Auto-grading)

```
Cron tiap 15 menit:

1. Query: fixtures yang
     status != 'finished'
     AND kickoff_utc < NOW() - 110 minutes  (90 + extra time + buffer)

2. Untuk tiap fixture:
   a. Fetch hasil dari ESPN/football-data.org
   b. Cek apakah benar-benar finished (bukan postponed)
   c. Update fixtures: home_score, away_score, status

3. Untuk tiap pick di fixture yang baru selesai:
   a. result = grade_market(pick.market, score)
      → win | loss | push | void

   b. Hitung profit_pct:
      - win:  stake_pct × (odds - 1)
      - loss: -stake_pct
      - push: 0
      - void: 0

   c. Hitung CLV (jika odds_at_close tersedia):
      clv = (1/close - 1/pick) / (1/pick) × 100

   d. Update pick: result, profit_pct, clv_pct, validated_at

4. Update bankroll_log harian:
   ending_balance = starting + Σ profit_pct (untuk tanggal tsb)
```

### Grading Markets (final list)

```python
MATCHERS = {
    '1X2_HOME':     lambda h,a: 'win' if h>a else 'loss',
    '1X2_AWAY':     lambda h,a: 'win' if a>h else 'loss',
    '1X2_DRAW':     lambda h,a: 'win' if h==a else 'loss',
    'OVER_1.5':     lambda h,a: 'win' if (h+a)>1 else 'loss',
    'OVER_2.5':     lambda h,a: 'win' if (h+a)>2 else 'loss',
    'OVER_3.5':     lambda h,a: 'win' if (h+a)>3 else 'loss',
    'UNDER_2.5':    lambda h,a: 'win' if (h+a)<3 else 'loss',
    'UNDER_3.5':    lambda h,a: 'win' if (h+a)<4 else 'loss',
    'BTTS_YES':     lambda h,a: 'win' if h>0 and a>0 else 'loss',
    'BTTS_NO':      lambda h,a: 'win' if h==0 or a==0 else 'loss',
    'AH_0.0_HOME':  lambda h,a: 'win' if h>a else ('push' if h==a else 'loss'),
    'AH_0.0_AWAY':  lambda h,a: 'win' if a>h else ('push' if h==a else 'loss'),
    'AH_-0.5_HOME': lambda h,a: 'win' if h>a else 'loss',
    'AH_+0.5_AWAY': lambda h,a: 'win' if a>=h else 'loss',
    'AH_-1.0_HOME': lambda h,a: 'win' if h-a>1 else ('push' if h-a==1 else 'loss'),
    'AH_+1.0_AWAY': lambda h,a: 'win' if a-h>=0 else ('push' if h-a==1 else 'loss'),
    'AH_-1.5_HOME': lambda h,a: 'win' if h-a>1 else 'loss',
    'AH_+1.5_AWAY': lambda h,a: 'win' if a-h>=-1 else 'loss',
    'AH_-2.0_HOME': lambda h,a: 'win' if h-a>2 else ('push' if h-a==2 else 'loss'),
    # ... semua AH lines
}
```

---

## 9. 📊 EXAMPLE — SATU SESI USER LENGKAP

### 11 Mei 2026, 08:00 WIB
```
USER buka app → default date = 11 Mei
→ Fetch jalan (10 detik)
→ 12 fixtures di-load
→ 4 picks high-edge ditampilkan (semua +5% edge)
→ Bankroll virtual: 1000 unit (default)
```

### 11 Mei 2026, 13:00 WIB (5 jam kemudian)
```
USER refresh → cache expired (>4h)
→ Background refresh jalan
→ Sebelum selesai: tampil data 5 jam lalu
→ Setelah refresh: 1 odds berubah (dari 1.95 → 1.85)
→ Edge 1 pick turun dari +13% → +6% (masih VALUE)
→ UI update otomatis
```

### 11 Mei 2026, 22:00 WIB (match malam selesai)
```
Match Liverpool vs Chelsea selesai 2-1
→ Cron 15 menit detect
→ Grade pick "1X2 Home @ 1.95" → WIN
→ Stake 1.5% × (1.95 - 1) = +1.425% bankroll
→ Bankroll: 1000 → 1014.25 unit
→ CLV calc: pick 1.95, close 1.85 → (1/1.85 - 1/1.95)/(1/1.95) = +5.4% CLV ✅
```

### 12 Mei 2026, 06:00 WIB
```
USER buka app → default DATE BERUBAH ke 12 Mei
→ Fetch baru untuk 12 Mei
→ Halaman 11 Mei TETAP bisa diakses via dropdown
→ /history menunjukkan 11 Mei: 4 picks, 2W/1L/1P, ROI +0.8%
```

### 14 Mei 2026, USER pilih tanggal "9 Mei" (H-3)
```
→ Cek fetch_jobs: ada (fetched 9 Mei dulu)
→ Past date → cache VALID FOREVER
→ Return data 9 Mei dari DB
→ Tampil: 8 match selesai, 3 picks (1W/2L)
```

---

## 10. 🎨 SCREEN MOCKUP (Dashboard)

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚽ Sports Parlay Analyst v3.0                  ⚙️  📊  🌙       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📅 Senin, 11 Mei 2026 (WIB)                         [Hari ini] │
│  ◄  H-3  H-2  H-1 [Hari ini] H+1  H+2  H+3 ... H+7  ►          │
│                                                                 │
│  🟢 Cached 06:23 WIB · auto-refresh in 0j 48m  [🔄 Refresh]    │
│                                                                 │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ 💰 BANKROLL VIRTUAL: 1,014.25 unit (+1.4% all-time)       │  │
│ │ 📊 Hari ini: 4 picks active · stake 4.5% · est EV +0.6%   │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  🏆 EPL · 19:00 WIB                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  🏟️ Liverpool vs Chelsea                                 │    │
│  │  TLDR: 1X2 HOME @ 1.95 · Edge +13.9% · STRONG VALUE     │    │
│  │  Stake: 1.5% bankroll · ⭐⭐⭐                            │    │
│  │                                          [Lihat detail]│    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  🏆 La Liga · 22:00 WIB                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  🏟️ Real Madrid vs Sevilla                               │    │
│  │  TLDR: AH -1.0 HOME @ 1.78 · Edge +9.2% · VALUE         │    │
│  │  Stake: 1.0% bankroll · ⭐⭐                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  🏆 J-League · 15:00 WIB                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  🏟️ Kashima vs Urawa                                    │    │
│  │  TLDR: ⏭ NO PICK (edge < 5%)                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ... (12 fixture total, 4 high-edge, 8 skip)                   │
│                                                                 │
│  ⚠️ DISCLAIMER: Analisa berbasis statistik. Tidak ada jaminan.  │
│     Bermainlah bertanggung jawab. [Selengkapnya]               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. 🚦 9 KEPUTUSAN WEBAPP — Default Recommendation

Belum dijawab eksplisit, saya pakai default ini kalau Anda OK:

| # | Pertanyaan | Default Saya |
|---|-----------|-------------|
| 1 | Scope | **MVP** (~10 hari, 8 liga) |
| 2 | Liga MVP | EPL, La Liga, Serie A, Bundesliga, Ligue 1, UCL, Liga 1 Indonesia, J-League |
| 3 | Auth | **No-login** + cookie session untuk virtual bankroll |
| 4 | Repo | **Monorepo** (apps/api + apps/web), saya buatkan repo baru |
| 5 | Bankroll | **Virtual saja** (legal safety) |
| 6 | Notification | **Skip di MVP**, Telegram bot di v1 |
| 7 | Disclaimer | **Modal blocker** (heavy, legal safety) |
| 8 | Domain | `*.fly.dev` + `*.devinapps.com` (Hosting Opsi A) |
| 9 | Bahasa UI | **Indonesia** dulu, EN nanti |

Kalau ada yang mau ganti dari default → sebutkan saja.

---

## 12. ✅ KESIMPULAN & APPROVAL CHECKPOINT

**Yang sudah disetujui Anda:**
- ✅ Skill v3.0 (804 baris) — file sudah dikirim
- ✅ Hosting Opsi A (Fly.io + devinapps)
- ✅ Caching strategy: (A) default date geser, data lama tetap
- ✅ TTL 4 jam
- ✅ Range H-3 sampai H+7
- ✅ Tombol "Fetch sekarang" tampil ke user
- ✅ Past + Today + Future di date picker

**Yang perlu Anda confirm sebelum coding:**
- 9 keputusan webapp di atas → **OK pakai default semua?** Atau ada yang mau diganti?

**Begitu Anda bilang "OK" / "go" / "lanjut":**
- Phase 0: setup repo + skeleton (~30 menit)
- Phase 1: data pipeline (~2 hari)
- Phase 2: skill engine (~2 hari)
- Phase 3: API layer (~1 hari)
- Phase 4: frontend MVP (~2 hari)
- Phase 5: auto-validation (~0.5 hari)
- Phase 6: stats dashboard (~1 hari)
- Phase 7: deploy + polish (~1.5 hari)
- **Total ~10 hari kerja → demo URL aktif**

Saya tunggu konfirmasi terakhir Anda.
