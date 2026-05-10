"""Pick validator — grade markets setelah match selesai."""

from __future__ import annotations


def grade_market(market: str, home_score: int, away_score: int) -> str:
    """Return: 'win' | 'loss' | 'push' | 'void'."""
    h, a = home_score, away_score
    total = h + a

    matchers = {
        "1X2_HOME": lambda: "win" if h > a else "loss",
        "1X2_AWAY": lambda: "win" if a > h else "loss",
        "1X2_DRAW": lambda: "win" if h == a else "loss",
        "OVER_1.5": lambda: "win" if total > 1 else "loss",
        "OVER_2.5": lambda: "win" if total > 2 else "loss",
        "OVER_3.5": lambda: "win" if total > 3 else "loss",
        "UNDER_2.5": lambda: "win" if total < 3 else "loss",
        "UNDER_3.5": lambda: "win" if total < 4 else "loss",
        "BTTS_YES": lambda: "win" if h > 0 and a > 0 else "loss",
        "BTTS_NO": lambda: "win" if h == 0 or a == 0 else "loss",
        "AH_0.0_HOME": lambda: "win" if h > a else ("push" if h == a else "loss"),
        "AH_0.0_AWAY": lambda: "win" if a > h else ("push" if h == a else "loss"),
        "AH_-0.5_HOME": lambda: "win" if h > a else "loss",
        "AH_+0.5_AWAY": lambda: "win" if a >= h else "loss",
        "AH_-1.0_HOME": lambda: "win" if h - a > 1 else ("push" if h - a == 1 else "loss"),
        "AH_+1.0_AWAY": lambda: "win"
        if a > h
        else ("push" if h - a == 1 else ("win" if h == a else "loss")),
        "AH_-1.5_HOME": lambda: "win" if h - a > 1 else "loss",
        "AH_+1.5_AWAY": lambda: "win" if a - h >= -1 else "loss",
        "AH_-2.0_HOME": lambda: "win"
        if h - a > 2
        else ("push" if h - a == 2 else "loss"),
        "AH_+2.0_AWAY": lambda: "win"
        if a - h >= 0
        else ("push" if h - a == 2 else "loss"),
    }
    fn = matchers.get(market)
    if fn is None:
        return "void"
    return fn()


def compute_profit_pct(stake_pct: float, odds: float, result: str) -> float:
    """Profit relatif bankroll."""
    if result == "win":
        return stake_pct * (odds - 1.0)
    if result == "loss":
        return -stake_pct
    return 0.0  # push / void


def compute_clv(odds_at_pick: float, odds_at_close: float | None) -> float | None:
    """CLV% = (1/close - 1/pick) / (1/pick) × 100."""
    if odds_at_close is None or odds_at_close <= 0:
        return None
    ip_pick = 1.0 / odds_at_pick
    ip_close = 1.0 / odds_at_close
    return (ip_close - ip_pick) / ip_pick * 100
