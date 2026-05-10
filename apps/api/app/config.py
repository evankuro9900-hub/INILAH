"""Application settings — env vars dengan default sensible."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings global, baca dari env atau .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Sports Parlay Analyst v3.0"
    debug: bool = False
    cors_origins: list[str] = ["*"]

    # Database — di Fly.io di-mount ke /data via volume
    db_path: Path = Path("/data/sportsparlay.db")
    db_url: str = ""  # auto-derived dari db_path

    # Cache
    cache_ttl_today_hours: int = 4
    cache_ttl_future_hours: int = 4

    # Timezone
    tz_wib: str = "Asia/Jakarta"

    # Date picker range
    date_range_past_days: int = 3  # H-3
    date_range_future_days: int = 7  # H+7

    # External API keys (semua optional; semua punya fallback gratis)
    football_data_api_key: str = ""
    odds_api_key: str = ""
    openweather_api_key: str = ""

    # Scraping politeness
    fbref_request_delay_sec: float = 5.0
    user_agent: str = "SportsParlayAnalyst/3.0 (educational analysis tool)"

    # Bot pick generation
    skill_version: str = "v3.0"

    # Bankroll virtual default
    default_bankroll: float = 1000.0

    # Cron schedule (minutes/hours)
    fetch_today_interval_hours: int = 4
    validate_picks_interval_minutes: int = 15
    cleanup_snapshots_interval_days: int = 7

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.db_url:
            self.db_url = f"sqlite+aiosqlite:///{self.db_path}"


settings = Settings()
