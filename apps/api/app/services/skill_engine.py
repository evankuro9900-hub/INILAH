"""Skill v3.0 engine — Edge-based pick generator.

Implementasi simplified untuk MVP. v3.1+ akan menambahkan:
- Real xG/xGA dari FBref/Understat
- Wasit & cuaca
- Line movement detection

Untuk MVP:
- Form 5–10 match dari ESPN scoreboard (jika ada)
- Klasemen position sebagai proxy strength (jika ada)
- Default neutral scoring jika data tipis (LOW_DATA tag)
- Mock odds (1X2 implied dari position diff) — diganti Real Odds API saat tersedia
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.leagues import League

# ─── Konstanta tier threshold ───
TIER_MIN_EDGE = {
    "T1": 0.05,
    "T2": 0.05,
    "T3": 0.08,
    "T-OCEANIA": 0.05,
    "T-WOMENA": 0.06,
    "T-WOMENB": 0.10,
}

# Stake hard cap per pick: 3% bankroll
MAX_STAKE_PCT = 0.03

# Adjustment cap dari scoring card: ±15%
MAX_ADJUSTMENT = 0.15


@dataclass
class ScoringCard:
    """Hasil scoring per match — untuk audit & UI."""

    form: float = 0.0  # -3 .. +3
    xg_xga: float = 0.0  # -3 .. +3
    motivation: float = 0.0  # -3 .. +3
    home_away: float = 0.0  # -2 .. +2
    condition: float = 0.0  # -3 .. +1
    h2h: float = 0.0  # -1 .. +1
    fatigue: float = 0.0  # -2 .. 0
    weather_ref: float = 0.0  # -1 .. +1
    tags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def weighted_total(self) -> float:
        """Total tertimbang sesuai bobot v3.0."""
        return (
            self.form * 0.30
            + self.xg_xga * 0.25
            + self.motivation * 0.20
            + self.home_away * 0.10
            + self.condition * 0.10
            + self.h2h * 0.05
            + self.fatigue * 0.05  # bonus negative-only
            + self.weather_ref * 0.02
        )

    def adjustment_pct(self) -> float:
        """Probability adjustment, capped ±15%."""
        adj = self.weighted_total() * 0.05  # 1 poin tertimbang = 5% prob
        return max(-MAX_ADJUSTMENT, min(MAX_ADJUSTMENT, adj))

    def to_dict(self) -> dict[str, Any]:
        return {
            "form": self.form,
            "xg_xga": self.xg_xga,
            "motivation": self.motivation,
            "home_away": self.home_away,
            "condition": self.condition,
            "h2h": self.h2h,
            "fatigue": self.fatigue,
            "weather_ref": self.weather_ref,
            "weighted_total": round(self.weighted_total(), 3),
            "adjustment_pct": round(self.adjustment_pct() * 100, 2),
            "tags": self.tags,
            "notes": self.notes,
        }


@dataclass
class MarketCandidate:
    """Satu market candidate dengan edge yang dihitung."""

    market: str
    selection: str
    odds: float
    implied_prob: float
    estimated_rp: float
    edge: float  # 0.087 = 8.7%

    def to_dict(self) -> dict[str, Any]:
        return {
            "market": self.market,
            "selection": self.selection,
            "odds": self.odds,
            "implied_prob": round(self.implied_prob, 4),
            "estimated_rp": round(self.estimated_rp, 4),
            "edge_pct": round(self.edge * 100, 2),
        }


@dataclass
class GeneratedPick:
    """Pick final + scoring card + alasan."""

    market: str
    selection: str
    odds: float
    estimated_rp: float
    edge: float
    stake_pct: float
    scoring_card: ScoringCard
    candidates: list[MarketCandidate]
    reasoning: list[str]
    tags: list[str]


# ─── Helpers ───


def implied_prob(odds: float) -> float:
    """1/odds dengan removal vig sederhana (asumsi vig dibagi rata)."""
    return 1.0 / odds


def kelly_stake(rp: float, odds: float) -> float:
    """Kelly criterion fraction. Negative kalau −EV."""
    b = odds - 1.0
    if b <= 0:
        return 0.0
    return (rp * odds - 1.0) / b


def half_kelly_capped(rp: float, odds: float) -> float:
    """½ Kelly dengan cap MAX_STAKE_PCT."""
    k = kelly_stake(rp, odds)
    if k <= 0:
        return 0.0
    return min(k * 0.5, MAX_STAKE_PCT)


def estimate_rp_for_market(market: str, base_home_rp: float, score_adjustment: float, league: League) -> float:
    """Estimasi real probability per market.

    base_home_rp = baseline home win prob (0..1)
    score_adjustment = adjustment dari scoring card (signed) — positif berarti tim home favored

    Returns RP untuk market spesifik.
    """
    # Adjusted home win prob
    adj_home_win = max(0.05, min(0.90, base_home_rp + score_adjustment))
    # Asumsi draw rate baseline ~25% (typical), naik kalau match seimbang
    balance = 1.0 - 2 * abs(adj_home_win - 0.5)  # 1 di 50/50, 0 di extremes
    draw_rate = 0.20 + 0.10 * balance  # 20–30%
    away_win = max(0.05, 1.0 - adj_home_win - draw_rate)
    # Renormalize
    total = adj_home_win + draw_rate + away_win
    adj_home_win, draw_rate, away_win = (
        adj_home_win / total,
        draw_rate / total,
        away_win / total,
    )

    if market == "1X2_HOME":
        return adj_home_win
    if market == "1X2_DRAW":
        return draw_rate
    if market == "1X2_AWAY":
        return away_win
    if market == "AH_0.0_HOME":
        # win or push (treat push as half-win equiv → use win prob)
        return adj_home_win + draw_rate * 0.5
    if market == "AH_0.0_AWAY":
        return away_win + draw_rate * 0.5
    if market == "AH_-0.5_HOME":
        return adj_home_win
    if market == "AH_+0.5_AWAY":
        return away_win + draw_rate
    if market == "AH_-1.0_HOME":
        return adj_home_win * 0.6  # rough
    if market == "AH_+1.0_AWAY":
        return away_win + draw_rate + adj_home_win * 0.4
    # Total goals proxy: kualitas attack vs defense both teams
    if market == "OVER_2.5":
        # Tim besar match cenderung lebih banyak gol; rough proxy
        return 0.50 + balance * 0.05  # 50–55%
    if market == "UNDER_2.5":
        return 1.0 - estimate_rp_for_market("OVER_2.5", base_home_rp, score_adjustment, league)
    if market == "OVER_1.5":
        return 0.78 + balance * 0.02
    if market == "OVER_3.5":
        return 0.27 - balance * 0.02
    if market == "BTTS_YES":
        # Probability baseline ~50%
        return 0.52 - abs(adj_home_win - 0.5) * 0.2
    if market == "BTTS_NO":
        return 1.0 - estimate_rp_for_market("BTTS_YES", base_home_rp, score_adjustment, league)
    return 0.5  # fallback


def _normalize_form_result(result: str) -> str | None:
    normalized = result.strip().upper()
    if normalized in {"W", "D", "L"}:
        return normalized
    return None


def _normalize_form(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    for value in values or []:
        result = _normalize_form_result(value)
        if result is not None:
            normalized.append(result)
    return normalized


# ─── Pre-flight checks ───


def is_low_data(form_count_home: int, form_count_away: int) -> bool:
    """Skill v3.0: data sufficiency check."""
    return form_count_home < 8 or form_count_away < 8


def check_pre_flight(
    home_form_count: int, away_form_count: int, is_cup_knockout: bool, is_friendly: bool
) -> tuple[list[str], bool]:
    """Returns (tags, should_skip)."""
    tags: list[str] = []
    if is_friendly:
        return ["FRIENDLY"], True
    if is_cup_knockout:
        tags.append("CUP_KNOCKOUT")
    if is_low_data(home_form_count, away_form_count):
        tags.append("LOW_DATA")
    return tags, False


# ─── Main entry ───


def generate_pick(
    league: League,
    home_team: str,
    away_team: str,
    home_form: list[str] | None = None,  # ['W', 'D', 'L', ...]
    away_form: list[str] | None = None,
    home_position: int | None = None,  # 1 = top
    away_position: int | None = None,
    league_size: int = 20,
    is_cup_knockout: bool = False,
    is_friendly: bool = False,
    odds_overrides: dict[str, float] | None = None,
    home_team_stats: dict[str, object] | None = None,
    away_team_stats: dict[str, object] | None = None,
) -> GeneratedPick | None:
    """Generate pick untuk satu match.

    Returns None kalau pre-flight check skip atau tidak ada market +EV.
    """
    home_form = _normalize_form(home_form)
    away_form = _normalize_form(away_form)

    # Step 0: Pre-flight
    has_team_stats = home_team_stats is not None and away_team_stats is not None
    home_sample_count = len(home_form) if home_form else (8 if has_team_stats else 0)
    away_sample_count = len(away_form) if away_form else (8 if has_team_stats else 0)
    tags, skip = check_pre_flight(home_sample_count, away_sample_count, is_cup_knockout, is_friendly)
    if skip:
        return None

    # Step 1: Build scoring card
    card = _compute_scoring(
        home_form=home_form,
        away_form=away_form,
        home_position=home_position,
        away_position=away_position,
        league_size=league_size,
        is_cup_knockout=is_cup_knockout,
        home_team_stats=home_team_stats,
        away_team_stats=away_team_stats,
    )
    card.tags = tags
    if has_team_stats:
        card.tags.append("MULTI_LEAGUE_STATS")
    if "LOW_DATA" in tags:
        card.notes.append("Sample data 5–8 match — confidence diturunkan")

    # Step 2: Baseline home win prob (klasemen-based heuristic)
    base_home_rp = _baseline_home_rp(home_position, away_position, league_size)
    adjustment = card.adjustment_pct()

    # Step 3: Generate odds (mock kalau tidak ada Real Odds API)
    odds = _mock_odds(base_home_rp + adjustment, league)
    used_real_odds = False
    if odds_overrides:
        odds.update(odds_overrides)
        used_real_odds = True
    if not used_real_odds:
        card.tags.append("MOCK_ODDS")
        card.notes.append(
            "Odds yang dipakai = mock (estimasi internal). "
            "Pick bersifat ILUSTRATIF sampai integrasi real bookmaker odds (v1)."
        )

    # Step 4: Loop semua markets, hitung edge
    candidates: list[MarketCandidate] = []
    for market, market_odds in odds.items():
        ip = implied_prob(market_odds)
        rp = estimate_rp_for_market(market, base_home_rp, adjustment, league)
        edge = rp * market_odds - 1.0
        candidates.append(
            MarketCandidate(
                market=market,
                selection=_market_to_selection(market, home_team, away_team),
                odds=market_odds,
                implied_prob=ip,
                estimated_rp=rp,
                edge=edge,
            )
        )

    # Step 5: Filter sesuai threshold
    threshold = TIER_MIN_EDGE.get(league.tier, 0.05)
    if "LOW_DATA" in card.tags:
        threshold = max(threshold, 0.08)
    if "CUP_KNOCKOUT" in card.tags:
        threshold = max(threshold, 0.08)
    # Mock odds: paksa threshold lebih tinggi supaya pick mock tidak banjir
    if "MOCK_ODDS" in card.tags:
        threshold = max(threshold, 0.10)

    valid = [c for c in candidates if c.edge >= threshold]
    if not valid:
        return None

    # Step 6: Pilih edge tertinggi
    best = max(valid, key=lambda c: c.edge)
    stake = half_kelly_capped(best.estimated_rp, best.odds)

    # Step 7: Reasoning ringkas
    reasoning = _build_reasoning(card, base_home_rp, home_position, away_position)

    return GeneratedPick(
        market=best.market,
        selection=best.selection,
        odds=best.odds,
        estimated_rp=best.estimated_rp,
        edge=best.edge,
        stake_pct=stake,
        scoring_card=card,
        candidates=candidates,
        reasoning=reasoning,
        tags=card.tags,
    )


def _compute_scoring(
    home_form: list[str],
    away_form: list[str],
    home_position: int | None,
    away_position: int | None,
    league_size: int,
    is_cup_knockout: bool,
    home_team_stats: dict[str, object] | None = None,
    away_team_stats: dict[str, object] | None = None,
) -> ScoringCard:
    """Hitung scoring card v3.0 (simplified untuk MVP)."""
    card = ScoringCard()

    # Form: count W in last 5 (rolling)
    def form_score(form: list[str]) -> float:
        if not form:
            return 0.0
        last = form[-5:] if len(form) >= 5 else form
        wins = sum(1 for r in last if r == "W")
        losses = sum(1 for r in last if r == "L")
        # Map to -3 .. +3
        if wins >= 4:
            return 2.5
        if wins == 3:
            return 1.5
        if wins == 2 and losses <= 1:
            return 0.5
        if losses >= 4:
            return -2.5
        if losses == 3:
            return -1.5
        return 0.0

    home_form_pts = form_score(home_form)
    away_form_pts = form_score(away_form)
    card.form = home_form_pts - away_form_pts  # plus = home better

    # Position diff (proxy untuk strength)
    if home_position is not None and away_position is not None:
        gap = away_position - home_position  # positif = home lebih atas
        scaled_gap = gap * (20 / max(league_size, 1))
        # Map gap ke score
        if scaled_gap >= 10:
            pos_score = 2.5
        elif scaled_gap >= 6:
            pos_score = 1.5
        elif scaled_gap >= 3:
            pos_score = 0.8
        elif scaled_gap >= -2:
            pos_score = 0.0
        elif scaled_gap >= -5:
            pos_score = -0.8
        elif scaled_gap >= -9:
            pos_score = -1.5
        else:
            pos_score = -2.5
        card.motivation = pos_score * 0.5  # use for both motivation & xG proxy
        card.xg_xga = pos_score
    else:
        card.notes.append("Klasemen tidak tersedia — adjustment netral")

    # Home advantage default
    card.home_away = 0.5

    stat_score = _stats_strength_score(home_team_stats, away_team_stats)
    if stat_score is not None:
        card.xg_xga = max(-3.0, min(3.0, (card.xg_xga * 0.35) + (stat_score * 0.65)))
        card.notes.append("Team stats dari multi-league analytics dipakai")

    # Cup knockout: turunkan confidence
    if is_cup_knockout:
        card.notes.append("Cup knockout — variance tinggi")

    return card


def _float_stat(stats: dict[str, object] | None, key: str) -> float | None:
    if stats is None:
        return None
    value = stats.get(key)
    if value is None:
        return None
    try:
        if isinstance(value, (int, float, str)):
            return float(value)
    except (TypeError, ValueError):
        return None
    return None


def _stats_strength_score(
    home_team_stats: dict[str, object] | None, away_team_stats: dict[str, object] | None
) -> float | None:
    score = 0.0
    signals = 0

    home_xgd = _float_stat(home_team_stats, "xg_diff")
    away_xgd = _float_stat(away_team_stats, "xg_diff")
    if home_xgd is not None and away_xgd is not None:
        score += max(-2.5, min(2.5, (home_xgd - away_xgd) / 12.0))
        signals += 1

    home_rating = _float_stat(home_team_stats, "rating")
    away_rating = _float_stat(away_team_stats, "rating")
    if home_rating is not None and away_rating is not None:
        score += max(-1.5, min(1.5, (home_rating - away_rating) * 5.0))
        signals += 1

    home_gpm = _float_stat(home_team_stats, "goals_per_match")
    away_gapm = _float_stat(away_team_stats, "goals_conceded_per_match")
    away_gpm = _float_stat(away_team_stats, "goals_per_match")
    home_gapm = _float_stat(home_team_stats, "goals_conceded_per_match")
    if (
        home_gpm is not None
        and away_gapm is not None
        and away_gpm is not None
        and home_gapm is not None
    ):
        home_attack_edge = home_gpm - away_gapm
        away_attack_edge = away_gpm - home_gapm
        score += max(-1.5, min(1.5, home_attack_edge - away_attack_edge))
        signals += 1

    if signals == 0:
        return None
    return max(-3.0, min(3.0, score / signals))


def _baseline_home_rp(
    home_position: int | None, away_position: int | None, league_size: int
) -> float:
    """Baseline home win probability dari klasemen position."""
    if home_position is None or away_position is None:
        return 0.45  # default home advantage tipis
    gap = away_position - home_position  # positif = home lebih atas
    # Linear interpolation
    base = 0.45  # home advantage
    base += gap * (0.228 / max(league_size - 1, 1))
    return max(0.15, min(0.80, base))


def _mock_odds(adjusted_home_rp: float, league: League) -> dict[str, float]:
    """Mock odds berdasarkan estimated home win rp.

    Tambahkan vig ~5% supaya realistis. Di production: replace dengan The Odds API.
    """
    p_home = max(0.10, min(0.85, adjusted_home_rp))
    p_draw = 0.25 if 0.30 < p_home < 0.55 else 0.22
    p_away = max(0.05, 1.0 - p_home - p_draw)

    vig = 1.05  # 5% bookmaker margin

    odds = {
        "1X2_HOME": round(1.0 / (p_home * vig), 2),
        "1X2_DRAW": round(1.0 / (p_draw * vig), 2),
        "1X2_AWAY": round(1.0 / (p_away * vig), 2),
        "AH_0.0_HOME": round(1.0 / ((p_home + p_draw * 0.5) * vig), 2),
        "AH_0.0_AWAY": round(1.0 / ((p_away + p_draw * 0.5) * vig), 2),
        "AH_-0.5_HOME": round(1.0 / (p_home * vig), 2),
        "AH_+0.5_AWAY": round(1.0 / ((p_away + p_draw) * vig), 2),
        "AH_-1.0_HOME": round(1.0 / (p_home * 0.6 * vig), 2),
        "AH_+1.0_AWAY": round(1.0 / ((p_away + p_draw + p_home * 0.4) * vig), 2),
    }
    # Total goals: roughly fixed
    odds["OVER_1.5"] = 1.30
    odds["OVER_2.5"] = 1.95
    odds["OVER_3.5"] = 3.20
    odds["UNDER_2.5"] = 1.85
    odds["UNDER_3.5"] = 1.30
    odds["BTTS_YES"] = 1.85
    odds["BTTS_NO"] = 1.95

    if league.over_baseline >= 3.0:
        # High-scoring liga: turunkan odds Over
        odds["OVER_2.5"] = 1.65
        odds["OVER_3.5"] = 2.30
        odds["UNDER_2.5"] = 2.20

    return odds


def _market_to_selection(market: str, home: str, away: str) -> str:
    """Render label readable."""
    mapping = {
        "1X2_HOME": f"{home} menang",
        "1X2_DRAW": "Imbang",
        "1X2_AWAY": f"{away} menang",
        "OVER_1.5": "Over 1.5 gol",
        "OVER_2.5": "Over 2.5 gol",
        "OVER_3.5": "Over 3.5 gol",
        "UNDER_2.5": "Under 2.5 gol",
        "UNDER_3.5": "Under 3.5 gol",
        "BTTS_YES": "BTTS Ya",
        "BTTS_NO": "BTTS Tidak",
        "AH_0.0_HOME": f"AH 0.0 (DNB) — {home}",
        "AH_0.0_AWAY": f"AH 0.0 (DNB) — {away}",
        "AH_-0.5_HOME": f"AH −0.5 — {home}",
        "AH_+0.5_AWAY": f"AH +0.5 — {away}",
        "AH_-1.0_HOME": f"AH −1.0 — {home}",
        "AH_+1.0_AWAY": f"AH +1.0 — {away}",
    }
    return mapping.get(market, market)


def _build_reasoning(
    card: ScoringCard,
    base_home_rp: float,
    home_position: int | None,
    away_position: int | None,
) -> list[str]:
    """3 alasan ringkas berbasis data."""
    reasons: list[str] = []
    if home_position is not None and away_position is not None:
        gap = away_position - home_position
        if gap >= 5:
            reasons.append(f"Home lebih tinggi {gap} posisi di klasemen ({home_position} vs {away_position})")
        elif gap <= -5:
            reasons.append(f"Away lebih tinggi {-gap} posisi di klasemen ({away_position} vs {home_position})")
        else:
            reasons.append(f"Klasemen seimbang ({home_position} vs {away_position})")

    if card.form > 1.5:
        reasons.append("Form home jauh lebih baik di 5 match terakhir")
    elif card.form < -1.5:
        reasons.append("Form away jauh lebih baik di 5 match terakhir")
    elif abs(card.form) > 0.5:
        side = "Home" if card.form > 0 else "Away"
        reasons.append(f"{side} sedikit lebih unggul dalam form")

    reasons.append(
        f"Estimasi probabilitas dasar: home {round(base_home_rp * 100)}%, "
        f"adjustment +{round(card.adjustment_pct() * 100, 1)}% dari scoring card"
    )

    if card.tags:
        reasons.append("Tags: " + ", ".join(card.tags))

    return reasons[:4]
