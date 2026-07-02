from __future__ import annotations

from datetime import date
from decimal import Decimal

from masareef.services.budgets import set_budget
from masareef.services.expenses import add_expense
from masareef.services.fx import store_rate
from masareef.services.reports import alert_exit_code, budget_status, build_status_report


def test_status_report_computes_budget_usage_and_projection(db_session) -> None:
    store_rate(db_session, date(2026, 6, 30), Decimal("50"), "test")
    set_budget(db_session, Decimal("10"), month="2026-06")
    add_expense(db_session, Decimal("250"), "food", "lunch", date(2026, 6, 30))

    report = build_status_report(db_session, on_date=date(2026, 6, 30))

    assert report.month == "2026-06"
    assert report.spent_usd_cents == 500
    assert report.budget_usd_cents == 1000
    assert report.percent_used == 50
    assert report.status_label == "On track"
    assert report.status_style == "green"
    assert report.projected_over_budget is False
    assert report.projected_usd_cents == 500
    assert report.categories == [("food", 500)]
    assert alert_exit_code(report) == 0


def test_status_report_flags_projected_overspend(db_session) -> None:
    store_rate(db_session, date(2026, 6, 10), Decimal("50"), "test")
    set_budget(db_session, Decimal("100"), month="2026-06")
    add_expense(db_session, Decimal("2000"), "food", "groceries", date(2026, 6, 10))

    report = build_status_report(db_session, on_date=date(2026, 6, 10))

    assert report.spent_usd_cents == 4000
    assert report.budget_usd_cents == 10000
    assert report.percent_used == 40
    assert report.projected_usd_cents == 12000
    assert report.projected_over_budget is True


def test_budget_status_thresholds() -> None:
    assert budget_status(69.9) == ("On track", "green")
    assert budget_status(70) == ("Watch", "yellow")
    assert budget_status(90) == ("Watch", "yellow")
    assert budget_status(90.1) == ("Over pace", "red")
