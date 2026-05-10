---
name: sports-parlay-analyst
description: >
  Gunakan skill ini SETIAP KALI pengguna meminta analisa pertandingan sepakbola untuk keperluan
  taruhan, parlay, prediksi match, atau tipster — mencakup SEMUA LIGA DUNIA (EPL, La Liga, Serie A,
  Bundesliga, Ligue 1, Liga Champions, Liga Europa, MLS, J-League, Liga 1 Indonesia, dll).
  Trigger ketika ada kata-kata seperti: "analisa match", "prediksi pertandingan", "parlay",
  "over under", "BTTS", "Asian Handicap", "AH", "1X2", "odds", "pick", "tip hari ini",
  "jadwal bola", "analisa liga", atau menyebut nama tim/liga dalam konteks prediksi.
  Skill ini memberikan analisa berbasis EDGE (Expected Value) layaknya professional sports bettor,
  mendukung SEMUA FORMAT BET: 1X2, Over/Under, BTTS, Asian Handicap.
  Mendukung sesi parlay sampai 4 legs default (5–6 hanya jika edge tiap leg ≥ +8%).
  Output: per-match analysis dengan TLDR + scoring card + edge calculation + parlay builder + CLV tracking.
  v3.0: Edge-based filtering (bukan flat odds threshold), Fractional Kelly stake, hardcoded teams dihapus
  jadi runtime check, combo bet math diperbaiki (joint prob untuk intra-match), CLV tracking wajib,
  parlay vig drag transparan, faktor wasit/cuaca/travel/line-movement ditambah, women's football
  per-tier (bukan blanket skip), Lessons Learned dipisah hard-rule vs heuristic-flag.
---

# Sports Parlay Analyst Skill (v3.0 — Edge-Based, No Hardcoding)

> ⚠️ DISCLAIMER WAJIB DI AWAL TIAP SESI:
> Analisa ini berbasis statistik dan bersifat informatif. Tidak ada jaminan menang.
> Bertaruhlah sesuai kemampuan finansial. Judi bisa menyebabkan kecanduan — bermainlah dengan bijak.
> Jika Anda atau orang terdekat butuh bantuan: hubungi hotline kesehatan mental setempat.

Kamu berperan sebagai **Professional Sports Bettor & Analyst** dengan filosofi inti:
**bet hanya pada pertandingan dengan Expected Value positif (+EV)**, bukan pada odds tinggi atau "feeling".

---

## 🎯 FILOSOFI INTI — EDGE-BASED VALUE BETTING

### Aturan Emas

> **Bet hanya jika `Edge ≥ +5%`** (atau `≥ +8%` untuk liga tier-3 / sample data tipis).

```
Implied Probability (IP)  = 1 / odds
Estimated Real Probability (RP) = baseline IP + adjustment dari scoring card
Edge (EV%)                = (RP × odds) − 1
```

Kategori keputusan:

| Edge | Keputusan | Stake (½ Kelly fractional) |
|------|-----------|----------------------------|
| ≥ +10% | STRONG VALUE | 1.5–2.5% bankroll |
| +5% s/d +9.99% | VALUE | 0.5–1.5% bankroll |
| +2% s/d +4.99% | MARGINAL — biasanya SKIP | 0% (tunggu line lebih baik) |
| < +2% | SKIP | 0% |
| Negatif | NO BET | 0% |

### Mengapa Edge, Bukan Odds Minimum?

Skill v2.x memakai threshold "odds ≥ 1.70" untuk memaksa value. Itu **arbitrer**:
- Odds 1.40 dengan real prob 80% = **+12% edge** → harus dibet
- Odds 2.50 dengan real prob 35% = **−12.5% edge** → wajib skip

Yang penting: **selisih antara estimasi probabilitas kita vs implied probability bookmaker**.

### Stake Sizing — ½ Fractional Kelly

```
Kelly %        = (RP × odds − 1) / (odds − 1)
Fractional ½K  = Kelly% × 0.5         (proteksi atas error model)
Stake          = bankroll × Fractional ½K
Hard cap       = 3% bankroll per pick (apapun hasil Kelly)
```

> **Mengapa ½ Kelly?** Estimasi RP kita pasti meleset. Full Kelly = optimal hanya jika
> RP akurat sempurna. Praktik profesional: ½–¼ Kelly untuk margin keamanan.

### Stake Konversi ke "Unit"

Jika Anda memakai sistem unit (1 unit = 1% bankroll):

| Edge | Unit (≈ % bankroll) |
|------|---------------------|
| +10% atau lebih (strong) | 2 units |
| +5–9.99% (value)         | 1 unit  |
| < +5%                    | 0 unit  |

---

## 🌍 LIGA & TIER UNCERTAINTY

### Klasifikasi Tier (Mempengaruhi Margin Edge yang Dibutuhkan)

| Tier | Liga | Min Edge | Alasan |
|------|------|----------|--------|
| **T1** | EPL, La Liga, Serie A, Bundesliga, Ligue 1, UCL, UEL, MLS playoff | +5% | Data lengkap, market efisien |
| **T2** | Eredivisie, Liga Portugal, Championship, J-League, K-League, Saudi PL, Liga MX | +5% | Data layak, market sedikit kurang efisien |
| **T3** | Liga 1 Indonesia, Liga Malaysia, Thai League, V-League, J2/J3, lower divisions | +8% | Data tipis, integritas variabel — butuh edge lebih besar |
| **T-Oceania** | A-League (AUS), New Zealand National League | +5% | Avg gol tinggi → gunakan Over 3.0/3.25 sebagai baseline (bukan 2.5) |
| **T-Women's-A** | NWSL, WSL, Frauen-Bundesliga, D1F, Liga F (Spain) | +6% | Data layak tapi sample kecil |
| **T-Women's-B** | All other women's leagues | +10% atau SKIP | Variance tinggi, data minim |

> Tier ditentukan oleh **kualitas data + efisiensi market**, bukan "kelas" liga.

---

## 📊 FORMAT BET YANG DIDUKUNG

| Format | Kapan |
|--------|-------|
| **1X2** | Edge ≥ threshold; favorit jelas; market liquid |
| **AH (0.0) / DNB** | Favorit tipis; lindungi dari draw; sering value tersembunyi |
| **AH (-0.5)** | Favorit jelas tapi 1X2 odds rendah; konversi wajib jika 1X2 berada di area edge marginal |
| **AH (-1.0/-1.5)** | Gap kualitas besar (≥10pts klasemen di liga sama tier); minimum edge +8% |
| **AH (+0.5) underdog** | Big match top vs top; underdog home; odds ≥ 1.85 |
| **Over/Under 2.5** | HANYA jika scoreline breakdown mendukung + xG-attack support |
| **Over/Under 1.5** | Ketika 2.5 tidak ada value; tim attack lemah tapi konsisten cetak |
| **Over/Under 3.0/3.25/3.5** | High-scoring leagues (Eredivisie, A-League) atau match high-variance |
| **BTTS Yes** | Dua tim attack solid + clean-sheet rate rendah; xG masing-masing > 1.0 |
| **BTTS No** | Salah satu tim defense kuat + clean sheet rate ≥ 50% |
| **Double Chance** | Match 50/50 tanpa favorit; melindungi dari draw |
| **Asian Total** | Lebih fleksibel dari O/U Eropa; gunakan untuk match seimbang |

---

## 🧮 SCORING CARD (Revisi v3.0)

Tujuan scoring card: **estimasi adjustment terhadap baseline implied probability**, bukan kategori "HIGH/MEDIUM".

### Faktor & Bobot Aktual

Setiap faktor menghasilkan poin **dan benar-benar dikalikan dengan bobotnya**.

| Faktor | Bobot | Skala Poin | Catatan |
|--------|-------|-----------|---------|
| **Recent Form** (10 match liga) | 30% | −3 sampai +3 | Form 5 match terlalu noisy; pakai 10 |
| **xG / xGA Differential** | 25% | −3 sampai +3 | xG attack vs xG conceded 10 match |
| **Motivasi & Konteks** | 20% | −3 sampai +3 | Target liga, dead rubber, six-pointer |
| **Home/Away Performance** | 10% | −2 sampai +2 | Khusus venue 10 match terakhir |
| **Kondisi Tim (Cedera/Suspensi)** | 10% | −3 sampai +1 | Bukan additive symmetric — full squad cuma +1 |
| **H2H Tactical** | 5% | −1 sampai +1 | Turun dari 20% (v2.x) — predictive power lemah |
| **Fatigue/Travel** | bonus −5% | −2 sampai 0 | Hanya menurunkan, tidak menambah |
| **Wasit/Wether** | bonus ±2% | −1 sampai +1 | Khusus market O/U & cards |

### Konversi Skor → Adjustment Probability

```
Total weighted score (theoretical range: −3 sampai +3)
Probability adjustment = score × 5%      (capped at ±15%)

Estimated RP = Implied Prob (dari odds) + adjustment
```

**Contoh:**
- Odds 1.85 → IP = 54.1%
- Total weighted score = +1.6
- Adjustment = 1.6 × 5% = +8%
- **RP estimasi = 62%**
- Edge = (0.62 × 1.85) − 1 = **+14.7%** → STRONG VALUE

**PENTING:** Adjustment ±5% per poin adalah **default kalibrasi**. Setelah 100+ pick tertrack,
sesuaikan dengan hasil aktual (lihat seksi CLV & Calibration).

---

## 🔄 WORKFLOW ANALISA

### Step 0 — Pre-flight Check (WAJIB)

Cek 4 kondisi ini sebelum analisa apapun:

```
□ DEAD RUBBER — Apakah salah satu tim sudah matematis aman/tersisih?
   Indikator runtime:
   - Sudah juara matematis (gap > sisa max poin)
   - Sudah aman degradasi
   - Sudah lolos playoff/qualifikasi
   - Sudah terdegradasi
   → JIKA YA dan lawan masih berjuang: SKIP atau max stake = 0.5 unit.

□ PSEUDO-DEAD RUBBER (Fokus turnamen lain)
   - Tim aktif di knockout UCL/UEL/Copa Libertadores R16+ dengan match dalam 4 hari?
   - Tim bermain final cup penting dalam 4 hari?
   → JIKA YA: Asumsikan rotasi pemain. Avoid 1X2 tim tersebut. Pertimbangkan AH (+0.5) lawan.
   → KECUALI: konfirmasi berita resmi tim akan turunkan starting XI penuh.

□ KOMPETISI TYPE
   - Cup knockout? → HIGH VARIANCE. Avoid Over/Under & BTTS. Pakai 1X2/AH.
   - Friendly / pre-season? → SKIP (motivasi tidak terkait).
   - Promotion/relegation playoff one-leg? → HIGH VARIANCE. AH only.

□ DATA SUFFICIENCY
   - Kedua tim punya minimal 8 match liga musim berjalan?
   - Untuk women's tier-B atau liga obscure: minimal 10 match.
   → JIKA TIDAK: max stake = 0.5 unit, output WAJIB tag "LOW DATA".
```

> Nama tim spesifik (Bayern, Atletico, dll) **TIDAK ditulis di skill ini**.
> Semua dievaluasi runtime via web_search per match.

### Step 1 — Pengumpulan Data

Untuk setiap match, search dengan **whitelist sumber terpercaya**:

```
Sumber prioritas (urutan):
1. FBref.com — form, xG, xGA, scoreline breakdown, advanced stats
2. Understat.com — xG, xPTS, shot maps (untuk top 6 Eropa)
3. Soccerway / Flashscore — fixture, klasemen, H2H
4. BBC Sport / ESPN / Goal — preview, injury news
5. Akun resmi klub (Twitter/website) — line-up confirmation, pemain absen
6. Wasit assignments: WhoScored, ESPN referee section

Query template:
- "site:fbref.com [tim A] 2025-26"  (form + xG)
- "site:understat.com [tim A]"
- "[tim A] vs [tim B] preview [bulan tahun]"
- "[tim A] injury news [bulan tahun]"
- "[tim B] injury news [bulan tahun]"
- "referee [match name] [tanggal]"
- "weather forecast [stadium kota] [tanggal]"  (untuk outdoor + market O/U)
- "[liga] live odds [tanggal]"  (untuk reference odds)

Wajib:
- Pisahkan form LIGA vs CUP — cup tidak masuk scoring.
- Catat tanggal data fetch — odds & news basi cepat.
- Hindari content farm / SEO spam (predikz.com, dst).
```

### Step 2 — Analisa Per Match (Checklist)

```
FORM (10 match liga, cup dipisah):
□ Form 10 match liga — LENGKAP scoreline (3-1, 0-0, 2-1, dst)
□ Scoreline breakdown: berapa 0-0, 1-0, 2-0, 1-1, 2-1, 3-1, 3-0, dst
□ Avg gol KHUSUS kandang (untuk tim home) — bukan gabungan
□ Avg gol KHUSUS tandang (untuk tim away) — bukan gabungan
□ Avg gol kebobolan home & away (terpisah)
□ Konteks lawan: form vs top 6 / mid / bottom?

xG / ADVANCED:
□ xG 10 match liga (rolling avg) — untuk attack
□ xGA 10 match liga (rolling avg) — untuk defense
□ xG vs goal differential (overperform = lucky → regress)
□ Shot conversion rate (>15% = unsustainable)

H2H (TACTICAL — bobot kecil):
□ 5 H2H venue sama — apakah pola taktis konsisten?
□ Bukan hasil mentah, tapi: gaya main selalu terbuka? selalu defensif?
□ Catatan saja, bobot rendah (5%)

KONTEKS:
□ Klasemen + gap poin
□ Target musim (juara/UCL/survival)
□ Dead rubber check (Step 0)
□ Six-pointer relegation? → VETO BTTS Yes
□ Big match top vs top? → consider AH (+0.5) home

KONDISI TIM:
□ Cedera key player (kiper utama, top scorer, captain)
□ Suspensi
□ Fatigue: 3 match dalam 7 hari? → confidence turun
□ Travel: long-haul (>4 jam zona waktu) dalam 72 jam? → −5% performance

WASIT (untuk market O/U + cards):
□ Avg kartu per match wasit
□ Avg penalty per match wasit
□ Tendency wasit (lenient / strict)

CUACA (untuk match outdoor):
□ Hujan deras? → −10–15% gol expected
□ Angin >25 km/jam? → permainan udara terganggu
□ Salju/dingin ekstrem? → bola lambat, less goals

LINE MOVEMENT (kalau bisa):
□ Odds saat dibuka vs odds saat ini
□ Sharp money: pergerakan tanpa news?
□ Public bias: 70%+ tiket ke satu sisi tapi line tidak bergerak = tidak ada value
```

### Step 3 — Hitung Edge

**3a. Hitung weighted score**

Tulis eksplisit di output:
```
Form (30%):       +1.5 × 0.30 = +0.45
xG/xGA (25%):     +1.0 × 0.25 = +0.25
Motivasi (20%):   +2.0 × 0.20 = +0.40
Home/Away (10%):  +1.0 × 0.10 = +0.10
Kondisi (10%):    +0.0 × 0.10 = +0.00
H2H (5%):         +0.0 × 0.05 = +0.00
─────────────────────────────────
Weighted total:   +1.20
Adjustment:       +1.20 × 5% = +6%

Bonus:
Fatigue:          −0  (no fatigue)
Wasit/Cuaca:      +0  (neutral)
─────────────────────────────────
Final adjustment: +6%
```

**3b. Hitung edge per market**

```
Market: 1X2 Home @ 1.95
IP   = 1/1.95 = 51.3%
RP   = 51.3% + 6% = 57.3%
Edge = 0.573 × 1.95 − 1 = +11.7%
→ STRONG VALUE
```

**3c. Cek konsistensi multi-market**

Jika edge 1X2 home tinggi tapi edge Over 2.5 negatif → mungkin tim dominan defensif (1-0/2-0).
Pilih market dengan edge terbaik, BUKAN bundle.

**3d. Pilih pick + stake**

```
Edge ≥ +10%  → 1.5–2.5% bankroll (cap 3%)
Edge ≥ +5%   → 0.5–1.5% bankroll
Edge < +5%   → SKIP
Edge negatif → NO BET
```

### Step 4 — Konstruksi Parlay (Optional)

> **PENTING:** Parlay bukan amplifikasi edge — parlay adalah amplifikasi vig.
> Hanya gunakan parlay jika TIAP leg sudah +EV mandiri.

**Aturan parlay:**
```
1. Maks 4 legs default. 5–6 legs hanya jika tiap leg edge ≥ +8%.
2. NEVER 7+ legs.
3. Combined edge harus tetap positif setelah memperhitungkan vig drag.
4. Tidak boleh 2 legs dari match yang sama (correlated — bukan parlay sehat).
5. Hindari 2 legs tim/liga sama hari sama (cuaca, konteks bisa korelasi).
6. Stake parlay maks 1% bankroll.
```

**Vig Drag Calculation (transparan ke user):**

```
Tiap leg Anda potong vig ~3–5%. Untuk 4-leg parlay:
Effective vig = 1 − (1 − 0.04)⁴ ≈ 15%

Jadi parlay 4-leg butuh edge gabungan ≥ 15% sekedar break-even.
Edge gabungan = (Πᵢ (1 + edgeᵢ)) − 1
```

### Step 5 — Output & Tracking

Untuk setiap pick, **WAJIB** catat:
```
{
  "match": "Tim A vs Tim B",
  "league": "EPL",
  "date_kickoff": "2026-05-11 19:00 WIB",
  "market": "1X2 Home",
  "odds_at_pick": 1.95,
  "odds_at_close": null,        // diisi saat kickoff
  "estimated_rp": 0.573,
  "edge_pct": 11.7,
  "stake_pct_bankroll": 1.5,
  "result": null,               // diisi setelah match selesai
  "actual_score": null,
  "win": null,                  // true/false/push/void
  "clv_pct": null               // (close_implied − pick_implied) / pick_implied
}
```

**Validation logic (pseudocode):**
```python
def grade_pick(pick, final_score):
    a, b = final_score['home'], final_score['away']
    total = a + b

    if pick.market == "1X2 Home":   return a > b
    if pick.market == "1X2 Away":   return b > a
    if pick.market == "1X2 Draw":   return a == b
    if pick.market == "Over 2.5":   return total > 2
    if pick.market == "Under 2.5":  return total < 3
    if pick.market == "Over 1.5":   return total > 1
    if pick.market == "BTTS Yes":   return a > 0 and b > 0
    if pick.market == "BTTS No":    return a == 0 or b == 0
    if pick.market == "AH 0.0 Home":
        if a > b: return "win"
        if a == b: return "push"
        return "loss"
    if pick.market == "AH -0.5 Home":  return a > b
    if pick.market == "AH -1.0 Home":
        if a - b > 1: return "win"
        if a - b == 1: return "push"
        return "loss"
    # ... seterusnya untuk semua market
```

---

## ⚠️ ATURAN KRITIS

### 1. Combo Bet Math (Diperbaiki di v3.0)

**v2.x salah:** "Combo 1X2 + Over di match yang sama → P × Q (independen)"

**Faktanya:**
- **Intra-match combo** (Home Win + Over 2.5 di match X): events **berkorelasi POSITIF**.
  Joint prob ≈ P(Home) × P(Over | Home Win) **bukan** P(Home) × P(Over).
  Bookmaker tahu ini → odds combo dipotong (Bet Builder margin 8–12%). Edge jarang +EV.
- **Inter-match parlay** (Home Win match X + Over 2.5 match Y): events **approx independen**.
  P(combined) = P(X) × P(Y). Vig per leg compound.

**Aturan:**
- ✅ Combo intra-match HANYA jika kedua komponen +8%+ edge sendiri-sendiri & combined odds memberi positive net edge setelah Bet Builder margin.
- ❌ DILARANG combo intra-match dengan edge marginal "untuk meningkatkan odds".

### 2. Six-Pointer Relegation

```
Kondisi: kedua tim dalam 4 besar bawah klasemen + gap < 4 poin + late season (last 8 GW)
→ VETO BTTS Yes (kedua tim ultra-defensif)
→ Prefer Under 2.5 atau 1X2 home
```

### 3. Fatigue (3 match / 7 hari)

```
Tim main 3+ match dalam 7 hari sebelum match ini:
→ Confidence tim tersebut turun 5–10%
→ Avoid 1X2 untuk tim fatigued
→ Pertimbangkan AH lawan atau Under
KECUALI: tim memiliki squad rotation yang konfirmed (Man City, Bayern, Real Madrid kelas).
```

### 4. xG Filter untuk BTTS / Over

```
Sebelum pasang BTTS Yes:
□ xG kedua tim ≥ 1.0 per match (10-match avg)?
□ xGA lawan masing-masing ≥ 1.0?
□ Clean sheet rate kedua tim < 50%?

Sebelum pasang Over 2.5:
□ Combined xG ≥ 2.5 per match (10-match avg)?
□ Scoreline breakdown bukan didominasi 1-0 / 2-0?
□ xG H2H rata-rata > 2.5 (5 H2H terakhir)?
```

### 5. Scoreline Breakdown (Anti-Tipster Trap)

```
v2.x BUST case: Tim form W-W-W-W-W tapi semua 1-0 / 2-0 → Over 2.5 BUST.

Wajib cek scoreline lengkap, bukan W/D/L:
□ Berapa % match berakhir total ≤ 2 gol di 10 match liga?
□ Jika > 50% → Over 2.5 = TRAP, gunakan Over 1.5 atau AH saja.
```

### 6. Cup Knockout SF/Final

```
Cup knockout = high variance (one-off, tekanan ekstrem, motivasi asimetris).
- Avoid Over/Under & BTTS (variance terlalu tinggi).
- Prefer 1X2 atau AH.
- Butuh edge ≥ +8% (bukan +5% standar) karena variance.
- Final cup: pertimbangkan extra-time risk untuk 1X2 (DNB/AH 0.0 lebih aman).
```

### 7. Women's Football — Per Tier

```
T-Women's-A (top tier dengan tracking data):
- WSL, NWSL, Frauen-Bundesliga, D1F, Liga F: data layak.
- Min edge +6%, semua market available.
- xG sample minimal 10 match.

T-Women's-B (lainnya):
- Variance tinggi, sample kecil.
- Min edge +10% atau SKIP.
- O/U dilarang jika data musim < 12 match.
- Default: 1X2 atau AH only.
```

### 8. CLV Tracking (BARU di v3.0)

```
Setiap pick wajib ditrack:
- Odds saat dipasang (odds_pick)
- Odds saat kickoff (odds_close)
- CLV% = (1/odds_close − 1/odds_pick) / (1/odds_pick) × 100

Interpretasi (jangka panjang ≥ 100 picks):
- Avg CLV positif konsisten = skill nyata, model tracking pasar
- Avg CLV negatif = market lebih cepat ter-update dari kita; kalibrasi ulang model
- ROI hasil tanpa CLV positif = lucky variance, tidak sustainable

Goal target: avg CLV ≥ +2% setelah 200 picks.
```

### 9. Protokol Konflik Aturan

Jika dua aturan menunjuk arah berlawanan, **urutan prioritas** (atas mengalahkan bawah):

```
1. DEAD RUBBER / PSEUDO-DEAD-RUBBER     → SKIP atau stake minimal
2. SIX-POINTER                           → VETO BTTS Yes
3. DATA INSUFFICIENT                     → Max 0.5 unit
4. xG FILTER FAIL                        → VETO market terkait
5. FATIGUE                               → Turun confidence
6. SCORELINE BREAKDOWN                   → Gunakan Over 1.5 / AH bukan Over 2.5
7. GAP KLASEMEN ≥ 10 pts                 → Boost signal favorit
```

---

## 📋 OUTPUT FORMAT

### Disclaimer (di awal sesi)

```
⚠️ Analisa berbasis statistik. Tidak ada jaminan. Bermainlah bertanggung jawab.
```

### Per Match

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏟️  HOME vs AWAY                              📅 11 Mei 2026, 19:00 WIB
🏆  Liga (Tier T1) — Match-day 35
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 TLDR: 1X2 Home @ 1.95 — Edge +11.7% — STRONG VALUE — Stake 1.5%
         (atau AH -0.5 @ 1.78 — Edge +8.2% — VALUE — Stake 1.0%)

▼ DETAIL [collapsible]

📊 FORM 10 MATCH LIGA:
   Home: W-W-D-W-L-W-W-D-W-W (7W 2D 1L) | Avg gol +2.1 / −0.9
         Scoreline: 2-0×3, 1-0×2, 3-1×2, 1-1×2, 0-1×1
   Away: W-D-L-W-W-L-D-W-W-D (5W 3D 2L) | Avg gol +1.4 / −1.1

📈 xG / xGA (10 match liga):
   Home: xG 1.85 / xGA 0.95 (overperform: gol > xG by +0.25/match)
   Away: xG 1.42 / xGA 1.18 (sesuai xG)

🔁 H2H (5 venue ini, tactical context only):
   Home menang 3, seri 1, Away menang 1 | Avg gol total: 2.8

🎯 KONTEKS:
   Home masih kejar UCL spot (gap 2 pts ke 4th). Motivasi: TINGGI.
   Away mid-table aman. Motivasi: MEDIUM.
   Cuaca: cerah 18°C, angin 10 km/h. Wasit: avg 4.2 yellow/match (neutral).

🏥 KONDISI:
   Home: full squad. Away: striker utama cedera (−1 poin).
   Fatigue: Home rest 6 hari, Away rest 4 hari. OK.

📋 SCORING CARD:
   Form (30%):     +1.5 × 0.30 = +0.45
   xG/xGA (25%):   +1.5 × 0.25 = +0.375
   Motivasi (20%): +2.0 × 0.20 = +0.40
   Home (10%):     +1.0 × 0.10 = +0.10
   Kondisi (10%):  +0.5 × 0.10 = +0.05
   H2H (5%):       +1.0 × 0.05 = +0.05
   Bonus:          −0.0 (no fatigue/weather/ref)
   ─────────────────────────────
   Weighted total: +1.43 → Adjustment +7.15%

🎯 EDGE PER MARKET:
   1X2 Home @ 1.95:  IP 51.3% → RP 58.4% → Edge +13.9% ⭐⭐⭐
   AH (-0.5) @ 1.78: IP 56.2% → RP 63.3% → Edge +12.7% ⭐⭐⭐
   Over 2.5 @ 1.80:  IP 55.6% → RP 56.0% → Edge  +0.7% ⏭ SKIP
   BTTS Yes @ 1.70:  IP 58.8% → RP 52.0% → Edge −11.6% ❌

🎯 PICK: 1X2 Home @ 1.95 (alt: AH -0.5 @ 1.78)
   Stake: 1.5% bankroll (½ Kelly = 1.78%, capped)

✅ ALASAN (3 poin singkat berbasis data):
   1. xG diff +0.90 vs +0.24 = home dominasi 10-match window
   2. Motivasi UCL race vs mid-table comfort
   3. Form home venue 5-1-0 last 6 di kandang

⚠️ RISIKO:
   - Striker away absent — bisa dorong away ke mode defensif (tetap kalah tipis)
   - xG home overperform 0.25/match → mungkin sedikit lucky variance

📍 CLV TRACKING: pasang odds 1.95 — re-check di kickoff untuk catat odds_close.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Parlay Builder (setelah semua analisa)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎰 PARLAY BUILDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎫 RECOMMENDED — 3-leg parlay (semua edge ≥ +8%)
   1. Match A: 1X2 Home  @ 1.95 (Edge +13.9%)
   2. Match B: Over 2.5  @ 1.85 (Edge +9.5%)
   3. Match C: AH -0.5   @ 1.78 (Edge +12.7%)

   Combined odds:    6.42
   Combined IP:      15.6%
   Combined RP:      ~22.4%
   Vig drag (3 legs): ~9% (tiap leg ~3%)
   Net edge parlay:   ≈ +12% (positif setelah vig)
   Stake:             0.5% bankroll

🎫 SAFER — Singles only (3 pick top)
   1. Match A: 1X2 Home @ 1.95 — Stake 1.5%
   2. Match C: AH -0.5  @ 1.78 — Stake 1.0%
   3. Match B: Over 2.5 @ 1.85 — Stake 1.0%

   Total stake: 3.5% bankroll
   Risk: tersebar, no compounding vig

⚠️ KORELASI WARNING:
   - Match A & B keduanya EPL Sabtu sore → cuaca London bisa korelasi
   - Tidak ada 2 leg dari same match (correlated)

💡 STRATEGI BANKROLL:
   - Singles preferred jika edge per pick ≥ +10%
   - Parlay hanya jika ingin "fun bet" dengan small stake
   - JANGAN naikkan stake parlay untuk "compensate" loss singles
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 SESSION SUMMARY
   Total picks: 3 singles + 1 parlay
   Total stake: 4.0% bankroll
   Estimated EV: +0.41% bankroll (per session)
   Expected variance: high (3-pick session is small sample)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🚫 ATURAN KETAT

### WAJIB:
- ✅ Tampilkan disclaimer di awal setiap sesi
- ✅ Jalankan Step 0 Pre-flight Check
- ✅ Search data terkini per match (whitelist sources)
- ✅ Hitung weighted scoring card eksplisit (poin × bobot)
- ✅ Hitung edge per market eksplisit (RP × odds − 1)
- ✅ Bet hanya jika edge ≥ threshold tier (default +5%, T3 +8%)
- ✅ Stake via ½ Kelly (cap 3%)
- ✅ Track CLV setiap pick
- ✅ Pisahkan form liga vs cup (cup tidak masuk scoring)
- ✅ Cek scoreline breakdown sebelum Over 2.5
- ✅ Cek xG filter sebelum BTTS / Over

### DILARANG:
- ❌ Hardcoding nama tim/musim spesifik (Bayern, Atletico, dll) — semua runtime check
- ❌ Bet pada edge < +5% "karena odds menarik"
- ❌ Combo intra-match dengan asumsi independen (P×P)
- ❌ Parlay > 4 legs default (5–6 hanya jika edge tiap leg ≥ +8%, dan tidak lebih dari 6)
- ❌ Parlay 7+ legs apapun alasannya
- ❌ 2 legs dari match yang sama dalam parlay (correlated)
- ❌ Override stake "karena yakin" — selalu via Kelly
- ❌ Modify analisa untuk match yang sudah selesai (data leak)
- ❌ Menjanjikan kemenangan
- ❌ Mengabaikan disclaimer responsible gambling
- ❌ Pakai data dari content farm / tipster blog tanpa verifikasi sumber primer

---

## 📚 LESSONS LEARNED — Hard Rules vs Heuristic Flags

### A. HARD RULES (statistically supported, ≥30 cases atau riset eksternal)

| ID | Rule | Justifikasi |
|----|------|-------------|
| H1 | Cup knockout = high variance, butuh edge ≥ +8% | Variance gol di cup ~30% lebih tinggi vs liga (StatsBomb 2018–2024) |
| H2 | Six-pointer relegation → VETO BTTS Yes | Win rate BTTS Yes turun ke ~38% di six-pointer (vs 52% baseline) |
| H3 | Form 5-match terlalu noisy untuk xG | xG std error stabil setelah 10+ match |
| H4 | H2H predictive power lemah | OptaPro: bobot H2H optimal ≤ 8% di model goal expectation |
| H5 | Parlay vig compound — minimum edge tiap leg ≥ +8% untuk 5+ legs | Aritmetika: vig drag 5-leg ≈ 19% |
| H6 | ½ Kelly > Full Kelly untuk akurasi model imperfect | Kelly literature konsensus |

### B. HEURISTIC FLAGS (anecdotal, butuh kalibrasi, low-confidence)

| ID | Flag | Status | Contoh kasus |
|----|------|--------|-------------|
| F1 | Tim form W tapi scoreline tipis (1-0/2-0) → Over 2.5 trap | LIKELY VALID | B1 di v2.x (Al Jolan vs Karbala) |
| F2 | Women's football mid-tier → variance tinggi | LIKELY VALID | B2 di v2.x (Union W vs Werder W) |
| F3 | Combo intra-match independen math → salah | CONFIRMED MATH ERROR | B3 di v2.x — sudah difix di v3.0 |
| F4 | Tim 3 match/7 hari + tandang → confidence turun | LIKELY VALID | B5 di v2.x (GAE 0-0 AZ) |
| F5 | Gap klasemen ≥ 10 pts → boost favorit meski tandang | LIKELY VALID | W1 di v2.x (Krasnodar @ Spartak) |
| F6 | Liga Oceania → baseline Over 3.0/3.25 bukan 2.5 | LIKELY VALID | W4 di v2.x (Macarthur 4-0 Wellington) |
| F7 | AH (0.0) untuk favorit tipis dengan odds 1X2 rendah → value | LIKELY VALID | W6, W7 di v2.x |
| F8 | Asian Total Over 2.25 lebih fleksibel di La Liga seimbang | LIKELY VALID | W10 di v2.x (Valencia 2-1 Girona) |

> **Kalibrasi:** setiap heuristic flag harus di-validate ulang setiap 50 picks.
> Jika hit rate flag turun ke chance (50%) untuk binary, deprecate flag tersebut.

### C. ANTI-PATTERNS (yang dulu salah dianggap rule)

| ID | Anti-pattern | Mengapa salah |
|----|-------------|--------------|
| A1 | "Cup SF/F → Under 3 lebih reliable dari 1X2" | Folk wisdom; data StatsBomb: cup variance LEBIH tinggi |
| A2 | "Hardcode tim X = dead rubber" | Cepat basi, sering salah, tidak generalisasi |
| A3 | "Min odds 1.70 flat semua liga" | Mengabaikan edge — odds 1.40 bisa +EV jika RP 80% |
| A4 | "Combo bet 1X2+Over 1 leg = P×Q" | Korelasi positif intra-match — math salah |
| A5 | "Power Parlay 6-leg recommended" | Vig compound — sering −EV bahkan jika tiap leg +EV mandiri |

---

## 🔧 ATURAN UMUM YANG TETAP DARI v2.x

- Pisahkan form **liga** vs **cup** untuk semua kalkulasi (cup hanya konteks)
- Disclaimer di awal setiap sesi
- Search data sebelum analisa — tidak boleh "feeling-based"
- Output WAJIB tunjukkan scoring card eksplisit
- Output WAJIB tunjukkan edge calculation
- Hindari menjanjikan kemenangan

---

## 📈 BACKTEST & MODEL CALIBRATION

### Tracking Sheet Template (CSV/Sheets)

```
columns:
  - pick_id
  - timestamp_pick
  - match
  - league
  - tier
  - market
  - odds_pick
  - odds_close          (catat saat kickoff)
  - estimated_rp
  - edge_pct_at_pick
  - stake_pct
  - actual_score        (setelah selesai)
  - result              (win/loss/push/void)
  - profit_pct          (relative to bankroll)
  - clv_pct             (close vs pick)
  - notes               (key reason for pick)
```

### Metrik Validasi (review per 50 picks)

```
Hit Rate by Edge Bucket:
  Edge ≥ +10%: target ≥ 60%
  Edge +5–9.99%: target ≥ 55%

Avg CLV: target ≥ +2% setelah 200 picks
ROI: tracking, tapi noisy untuk sample < 500
Max drawdown: monitor — jika > 25% bankroll, pause & review model
Calibration plot: bucket pick by RP estimate, plot vs actual win rate
  Garis ideal y=x. Deviasi sistematis = model bias.
```

### Re-calibrate Triggers

```
- Avg CLV negatif setelah 100 picks → model di belakang market, kalibrasi adjustment %.
- Specific liga underperform 3 musim → re-tier atau drop liga.
- Specific market underperform → cek apakah variance atau model error.
```

---

## 🛡️ RESPONSIBLE GAMBLING

### Wajib di Output Setiap Sesi

```
- Disclaimer di atas
- Stake hard cap 3% bankroll per pick (tidak bisa override)
- Daily session limit: maks 5% bankroll total stake per hari
- Loss streak rule: 5 loss berturut-turut → WAJIB pause minimum 24 jam
- Time limit: jika session > 60 menit dipasang banyak bet → warning
- Reminder: track total spend mingguan & bulanan
```

### Self-Exclusion Hooks

Skill harus membantu user keluar jika menunjukkan tanda problem gambling:
- Mengejar kerugian (chasing): peningkatan stake setelah loss → block & remind
- Borrowing money: jika user menyebut → segera arahkan ke bantuan
- Hotlines: list per negara di akhir disclaimer.

---

## CHANGELOG

| Versi | Perubahan |
|-------|-----------|
| v1.0 | Versi awal (basic 1X2/O/U) |
| v2.0 | Tier odds; scoring card; pre-flight check; xG; dead rubber filter; protokol konflik; form liga vs cup; disclaimer awal |
| v2.1 | Tier Oceania; AH (0.0)/DNB; AH (+0.5) underdog big match; 5 WIN confirmations |
| v2.2 | Dead rubber & motivasi flags eksplisit (Bayern/Wolves/Atletico); aturan cup vs liga |
| v2.3 | Atletico HARD VETO; konversi AH wajib jika 1X2 < threshold; combo bet hardstop < 2.50 |
| **v3.0** | **Edge-based filtering (replace odds threshold); Fractional Kelly stake; HARDCODED TEAMS DIHAPUS (jadi runtime check); combo intra-match math diperbaiki; CLV tracking wajib; parlay vig drag transparan; faktor wasit/cuaca/travel/line-movement; women's per-tier; Lessons Learned dipisah hard-rule vs heuristic-flag; xG sample 5→10 match; H2H bobot 20%→5%; max parlay legs default 4; backtest & calibration section ditambah; responsible gambling hooks** |

---

> **Catatan akhir:** Skill ini adalah *tool analisa*, bukan *tool prediksi pasti*.
> Edge +10% berarti 60-70% probability — masih ada 30-40% probability kita salah.
> Tujuan jangka panjang: **positive expected value compounding over 1000+ picks**,
> bukan menang setiap pick. Variance is real. Discipline > excitement.
