from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from masareef.services.fx import (
    fetch_rate_for_date,
    lookup_rate_for_expense,
    missing_dates_for_backfill,
    stale_rate_message,
    store_rate,
    sync_missing_rates,
)


def test_lookup_rate_falls_back_to_latest_cached_rate(db_session) -> None:
    store_rate(db_session, date(2026, 6, 29), Decimal("50"), "test")

    lookup = lookup_rate_for_expense(db_session, date(2026, 6, 30))

    assert lookup.is_stale is True
    assert lookup.rate.rate_date == date(2026, 6, 29)
    assert "2026-06-29" in stale_rate_message(lookup.rate, date(2026, 6, 30))


def test_lookup_rate_requires_at_least_one_cached_rate(db_session) -> None:
    with pytest.raises(ValueError, match="No FX rate"):
        lookup_rate_for_expense(db_session, date(2026, 6, 30))


def test_missing_dates_for_backfill_excludes_existing_rates(db_session, monkeypatch) -> None:
    monkeypatch.setattr("masareef.services.fx.today_cairo", lambda: date(2026, 6, 30))
    store_rate(db_session, date(2026, 6, 29), Decimal("50"), "test")

    assert missing_dates_for_backfill(db_session, days=3) == [
        date(2026, 6, 28),
        date(2026, 6, 30),
    ]


def test_fetch_rate_for_date_uses_historical_currency_api(respx_mock) -> None:
    import httpx

    respx_mock.get(
        "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@2026-06-29/"
        "v1/currencies/usd.json"
    ).mock(return_value=httpx.Response(200, json={"usd": {"egp": 50.25}}))

    rate, source = fetch_rate_for_date(date(2026, 6, 29))

    assert rate == Decimal("50.25")
    assert source == "currency-api"


def test_sync_missing_rates_stores_backfill_results(db_session, monkeypatch) -> None:
    monkeypatch.setattr("masareef.services.fx.today_cairo", lambda: date(2026, 6, 30))
    monkeypatch.setattr(
        "masareef.services.fx.fetch_rate_for_date",
        lambda _rate_date: (Decimal("50"), "test"),
    )
    store_rate(db_session, date(2026, 6, 29), Decimal("51"), "test")

    synced = sync_missing_rates(db_session, days=3)

    assert [rate.rate_date for rate in synced] == [date(2026, 6, 28), date(2026, 6, 30)]
