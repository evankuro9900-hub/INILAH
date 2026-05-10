"""Timezone helpers — WIB (Asia/Jakarta) <-> UTC."""

from datetime import date, datetime, timedelta

import pytz

WIB = pytz.timezone("Asia/Jakarta")
UTC = pytz.UTC


def now_wib() -> datetime:
    """Sekarang dalam WIB."""
    return datetime.now(WIB)


def now_utc() -> datetime:
    """Sekarang dalam UTC."""
    return datetime.now(UTC)


def today_wib() -> date:
    """Tanggal hari ini di WIB."""
    return now_wib().date()


def utc_to_wib(dt: datetime) -> datetime:
    """Convert UTC datetime ke WIB."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(WIB)


def wib_to_utc(dt: datetime) -> datetime:
    """Convert WIB datetime ke UTC."""
    if dt.tzinfo is None:
        dt = WIB.localize(dt)
    return dt.astimezone(UTC)


def wib_date_range(target_date: date) -> tuple[datetime, datetime]:
    """Return (start_utc, end_utc) untuk satu hari WIB.

    Berguna untuk query fixtures dengan kickoff_utc dalam rentang hari WIB.
    """
    start_wib = WIB.localize(datetime.combine(target_date, datetime.min.time()))
    end_wib = start_wib + timedelta(days=1)
    return start_wib.astimezone(UTC), end_wib.astimezone(UTC)


def parse_iso_date(s: str) -> date:
    """Parse 'YYYY-MM-DD' ke date."""
    return datetime.strptime(s, "%Y-%m-%d").date()
