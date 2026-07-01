from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

CAIRO_TZ = ZoneInfo("Africa/Cairo")


def today_cairo() -> date:
    return datetime.now(CAIRO_TZ).date()


def parse_date(value: str | None) -> date:
    if value is None:
        return today_cairo()
    return date.fromisoformat(value)


def month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def month_bounds(month: str) -> tuple[date, date]:
    year_text, month_text = month.split("-", maxsplit=1)
    year = int(year_text)
    month_number = int(month_text)
    start = date(year, month_number, 1)
    if month_number == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month_number + 1, 1)
    return start, end


def days_in_month(value: date) -> int:
    start, end = month_bounds(month_key(value))
    return (end - start).days
