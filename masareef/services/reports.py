from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from masareef.services.budgets import get_effective_budget
from masareef.services.expenses import category_totals_for_month, totals_for_month
from masareef.services.fx import get_cached_rate, get_latest_cached_rate
from masareef.utils.dates import days_in_month, month_key, today_cairo


@dataclass(frozen=True)
class StatusReport:
    month: str
    spent_egp_piastres: int
    spent_usd_cents: int
    budget_usd_cents: int | None
    budget_egp_piastres_today: int | None
    percent_used: float | None
    days_remaining: int
    projected_usd_cents: int
    categories: list[tuple[str, int]]


def build_status_report(session: Session, on_date: date | None = None) -> StatusReport:
    current_date = on_date or today_cairo()
    month = month_key(current_date)
    spent_egp_piastres, spent_usd_cents = totals_for_month(session, month)
    budget = get_effective_budget(session, month)
    days_elapsed = max(current_date.day, 1)
    total_days = days_in_month(current_date)
    days_remaining = max(total_days - current_date.day, 0)
    projected_usd_cents = round(spent_usd_cents / days_elapsed * total_days)

    budget_usd_cents = budget.amount_usd_cents if budget else None
    budget_egp_piastres_today = None
    percent_used = None
    if budget_usd_cents:
        percent_used = spent_usd_cents / budget_usd_cents * 100
        today_rate = get_cached_rate(session, current_date) or get_latest_cached_rate(session)
        if today_rate is not None:
            budget_egp_piastres_today = round(
                (budget_usd_cents / 100) * float(today_rate.egp_per_usd) * 100
            )

    return StatusReport(
        month=month,
        spent_egp_piastres=spent_egp_piastres,
        spent_usd_cents=spent_usd_cents,
        budget_usd_cents=budget_usd_cents,
        budget_egp_piastres_today=budget_egp_piastres_today,
        percent_used=percent_used,
        days_remaining=days_remaining,
        projected_usd_cents=projected_usd_cents,
        categories=category_totals_for_month(session, month),
    )


def alert_exit_code(report: StatusReport, alert_threshold: float = 100.0) -> int:
    if report.percent_used is None:
        return 0
    return 2 if report.percent_used >= alert_threshold else 0
