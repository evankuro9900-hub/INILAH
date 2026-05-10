"""20 liga MVP — konfigurasi tier, threshold, sumber data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class League:
    """Konfigurasi liga: tier, threshold edge, sumber data tersedia."""

    id: str  # slug internal
    name: str  # nama tampilan
    country: str
    tier: str  # T1, T2, T3, T-OCEANIA, T-WOMENA, T-WOMENB
    min_edge_pct: float  # threshold minimum edge (5.0 = 5%)
    over_baseline: float  # baseline Over line (2.5 default, 3.0/3.25 untuk high-scoring)
    espn_slug: str | None  # untuk ESPN scoreboard endpoint
    fbref_slug: str | None  # untuk FBref scraping
    understat_slug: str | None  # hanya 6 liga
    football_data_code: str | None  # untuk football-data.org
    notes: str = ""


# Master list — 20 liga MVP
LEAGUES: list[League] = [
    # ─── Tier 1: Top 5 EU + UCL ───
    League(
        id="epl",
        name="Premier League",
        country="England",
        tier="T1",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="eng.1",
        fbref_slug="9/Premier-League-Stats",
        understat_slug="EPL",
        football_data_code="PL",
    ),
    League(
        id="laliga",
        name="La Liga",
        country="Spain",
        tier="T1",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="esp.1",
        fbref_slug="12/La-Liga-Stats",
        understat_slug="La_liga",
        football_data_code="PD",
    ),
    League(
        id="seriea",
        name="Serie A",
        country="Italy",
        tier="T1",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="ita.1",
        fbref_slug="11/Serie-A-Stats",
        understat_slug="Serie_A",
        football_data_code="SA",
    ),
    League(
        id="bundesliga",
        name="Bundesliga",
        country="Germany",
        tier="T1",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="ger.1",
        fbref_slug="20/Bundesliga-Stats",
        understat_slug="Bundesliga",
        football_data_code="BL1",
    ),
    League(
        id="ligue1",
        name="Ligue 1",
        country="France",
        tier="T1",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="fra.1",
        fbref_slug="13/Ligue-1-Stats",
        understat_slug="Ligue_1",
        football_data_code="FL1",
    ),
    League(
        id="ucl",
        name="UEFA Champions League",
        country="Europe",
        tier="T1",
        min_edge_pct=8.0,  # cup format = higher variance
        over_baseline=2.5,
        espn_slug="uefa.champions",
        fbref_slug="8/Champions-League-Stats",
        understat_slug=None,
        football_data_code="CL",
        notes="Cup knockout — high variance, butuh edge ≥ +8%",
    ),
    # ─── Tier 2 ───
    League(
        id="primeira",
        name="Primeira Liga",
        country="Portugal",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="por.1",
        fbref_slug="32/Primeira-Liga-Stats",
        understat_slug=None,
        football_data_code="PPL",
    ),
    League(
        id="eredivisie",
        name="Eredivisie",
        country="Netherlands",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=3.0,  # high-scoring liga
        espn_slug="ned.1",
        fbref_slug="23/Eredivisie-Stats",
        understat_slug=None,
        football_data_code="DED",
        notes="High-scoring league, gunakan Over 3.0/3.25 sebagai baseline",
    ),
    League(
        id="scottish",
        name="Scottish Premiership",
        country="Scotland",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="sco.1",
        fbref_slug="40/Scottish-Premiership-Stats",
        understat_slug=None,
        football_data_code=None,
    ),
    League(
        id="mls",
        name="Major League Soccer",
        country="USA/Canada",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="usa.1",
        fbref_slug="22/Major-League-Soccer-Stats",
        understat_slug=None,
        football_data_code=None,
    ),
    League(
        id="brasileirao",
        name="Brazilian Série A",
        country="Brazil",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="bra.1",
        fbref_slug="24/Serie-A-Stats",
        understat_slug=None,
        football_data_code=None,
    ),
    League(
        id="argentine",
        name="Argentine Primera División",
        country="Argentina",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="arg.1",
        fbref_slug="21/Liga-Profesional-Argentina-Stats",
        understat_slug=None,
        football_data_code=None,
    ),
    League(
        id="ligamx",
        name="Liga MX",
        country="Mexico",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="mex.1",
        fbref_slug="31/Liga-MX-Stats",
        understat_slug=None,
        football_data_code=None,
    ),
    League(
        id="kleague",
        name="K-League 1",
        country="South Korea",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="kor.1",
        fbref_slug="5486/K-League-1-Stats",
        understat_slug=None,
        football_data_code=None,
    ),
    League(
        id="saudi",
        name="Saudi Pro League",
        country="Saudi Arabia",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="ksa.1",
        fbref_slug="70/Saudi-Professional-League-Stats",
        understat_slug=None,
        football_data_code=None,
    ),
    League(
        id="superlig",
        name="Turkish Süper Lig",
        country="Turkey",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="tur.1",
        fbref_slug="26/Super-Lig-Stats",
        understat_slug=None,
        football_data_code=None,
    ),
    League(
        id="jleague",
        name="J1 League",
        country="Japan",
        tier="T2",
        min_edge_pct=5.0,
        over_baseline=2.5,
        espn_slug="jpn.1",
        fbref_slug="25/J1-League-Stats",
        understat_slug=None,
        football_data_code=None,
    ),
    # ─── Tier 3 ───
    League(
        id="liga1id",
        name="Liga 1",
        country="Indonesia",
        tier="T3",
        min_edge_pct=8.0,  # data tipis, butuh margin lebih besar
        over_baseline=2.5,
        espn_slug="idn.1",
        fbref_slug=None,  # data minim di FBref
        understat_slug=None,
        football_data_code=None,
        notes="Data minim, banyak pick akan tag LOW_DATA",
    ),
    League(
        id="thai",
        name="Thai League 1",
        country="Thailand",
        tier="T3",
        min_edge_pct=8.0,
        over_baseline=2.5,
        espn_slug="tha.1",
        fbref_slug=None,
        understat_slug=None,
        football_data_code=None,
        notes="Data minim, banyak pick akan tag LOW_DATA",
    ),
    # ─── Tier Oceania ───
    League(
        id="aleague",
        name="A-League Men",
        country="Australia",
        tier="T-OCEANIA",
        min_edge_pct=5.0,
        over_baseline=3.0,  # high-scoring
        espn_slug="aus.1",
        fbref_slug="65/A-League-Stats",
        understat_slug=None,
        football_data_code=None,
        notes="High-scoring, baseline Over 3.0/3.25",
    ),
]


# Lookup helpers
LEAGUES_BY_ID: dict[str, League] = {lg.id: lg for lg in LEAGUES}


def get_league(league_id: str) -> League | None:
    return LEAGUES_BY_ID.get(league_id)


def all_active_leagues() -> list[League]:
    return list(LEAGUES)


def league_count() -> int:
    return len(LEAGUES)
