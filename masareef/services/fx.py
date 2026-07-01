from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from masareef.models import FxRate
from masareef.utils.dates import today_cairo

PRIMARY_URL = "https://open.er-api.com/v6/latest/USD"
SECONDARY_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
SECONDARY_HISTORICAL_URL = (
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/usd.json"
)


@dataclass(frozen=True)
class RateLookup:
    rate: FxRate
    is_stale: bool


def get_cached_rate(session: Session, rate_date: date) -> FxRate | None:
    return session.scalar(select(FxRate).where(FxRate.rate_date == rate_date))


def get_latest_cached_rate(session: Session) -> FxRate | None:
    return session.scalar(select(FxRate).order_by(FxRate.rate_date.desc()).limit(1))


def store_rate(session: Session, rate_date: date, egp_per_usd: Decimal, source: str) -> FxRate:
    existing = get_cached_rate(session, rate_date)
    if existing is not None:
        existing.egp_per_usd = egp_per_usd
        existing.source = source
        session.commit()
        session.refresh(existing)
        return existing
    rate = FxRate(rate_date=rate_date, egp_per_usd=egp_per_usd, source=source)
    session.add(rate)
    session.commit()
    session.refresh(rate)
    return rate


def fetch_today_rate() -> tuple[Decimal, str]:
    import httpx

    errors: list[str] = []
    try:
        response = httpx.get(PRIMARY_URL, timeout=3.0)
        response.raise_for_status()
        payload = response.json()
        rate = Decimal(str(payload["rates"]["EGP"]))
        return rate, "open.er-api.com"
    except Exception as exc:  # noqa: BLE001
        errors.append(f"primary: {exc}")

    try:
        response = httpx.get(SECONDARY_URL, timeout=3.0)
        response.raise_for_status()
        payload = response.json()
        rate = Decimal(str(payload["usd"]["egp"]))
        return rate, "currency-api"
    except Exception as exc:  # noqa: BLE001
        errors.append(f"secondary: {exc}")

    raise RuntimeError("Could not fetch USD/EGP rate. " + "; ".join(errors))


def fetch_rate_for_date(rate_date: date) -> tuple[Decimal, str]:
    if rate_date == today_cairo():
        return fetch_today_rate()

    import httpx

    url = SECONDARY_HISTORICAL_URL.format(date=rate_date.isoformat())
    try:
        response = httpx.get(url, timeout=3.0)
        response.raise_for_status()
        payload = response.json()
        rate = Decimal(str(payload["usd"]["egp"]))
        return rate, "currency-api"
    except Exception as exc:  # noqa: BLE001
        message = f"Could not fetch USD/EGP rate for {rate_date.isoformat()}: {exc}"
        raise RuntimeError(message) from exc


def sync_today_rate(session: Session) -> FxRate:
    rate, source = fetch_today_rate()
    return store_rate(session, today_cairo(), rate, source)


def sync_missing_rates(session: Session, days: int = 90) -> list[FxRate]:
    synced_rates: list[FxRate] = []
    for missing_date in missing_dates_for_backfill(session, days=days):
        rate, source = fetch_rate_for_date(missing_date)
        synced_rates.append(store_rate(session, missing_date, rate, source))
    return synced_rates


def lookup_rate_for_expense(session: Session, spent_on: date) -> RateLookup:
    cached = get_cached_rate(session, spent_on)
    if cached is not None:
        return RateLookup(rate=cached, is_stale=False)

    if spent_on == today_cairo():
        try:
            return RateLookup(rate=sync_today_rate(session), is_stale=False)
        except RuntimeError:
            pass

    latest = get_latest_cached_rate(session)
    if latest is None:
        raise ValueError("No FX rate is cached. Run `masareef sync-fx` first.")
    return RateLookup(rate=latest, is_stale=True)


def stale_rate_message(rate: FxRate, target_date: date) -> str:
    age = abs((target_date - rate.rate_date).days)
    plural = "day" if age == 1 else "days"
    return f"Using FX rate from {rate.rate_date.isoformat()} ({age} {plural} old)."


def missing_dates_for_backfill(session: Session, days: int = 90) -> list[date]:
    end = today_cairo()
    start = end - timedelta(days=days - 1)
    existing = set(
        session.scalars(
            select(FxRate.rate_date).where(FxRate.rate_date >= start, FxRate.rate_date <= end)
        ).all()
    )
    return [
        start + timedelta(days=offset)
        for offset in range(days)
        if start + timedelta(days=offset) not in existing
    ]
