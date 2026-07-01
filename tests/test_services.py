from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from masareef.services.budgets import get_effective_budget, set_budget
from masareef.services.expenses import (
    add_expense,
    delete_expense,
    fix_expense_rate,
    list_expenses,
    totals_for_month,
    update_expense,
)
from masareef.services.fx import store_rate


def test_add_expense_uses_cached_fx_rate(db_session) -> None:
    store_rate(db_session, date(2026, 6, 30), Decimal("50"), "test")

    expense, lookup = add_expense(
        db_session,
        Decimal("450"),
        "food",
        "dinner",
        date(2026, 6, 30),
    )

    assert lookup.is_stale is False
    assert expense.amount_egp_piastres == 45000
    assert expense.amount_usd_cents == 900
    assert expense.fx_rate == Decimal("50.000000")


def test_list_expenses_filters_by_month_and_category(db_session) -> None:
    store_rate(db_session, date(2026, 6, 30), Decimal("50"), "test")
    add_expense(db_session, Decimal("100"), "food", "lunch", date(2026, 6, 30))
    add_expense(db_session, Decimal("100"), "transport", "ride", date(2026, 6, 30))

    rows = list_expenses(db_session, month="2026-06", category_name="food")

    assert len(rows) == 1
    assert rows[0].note == "lunch"
    assert totals_for_month(db_session, "2026-06") == (20000, 400)


def test_monthly_budget_overrides_default(db_session) -> None:
    set_budget(db_session, Decimal("800"))
    set_budget(db_session, Decimal("1000"), month="2026-06")

    assert get_effective_budget(db_session, "2026-05").amount_usd_cents == 80000
    assert get_effective_budget(db_session, "2026-06").amount_usd_cents == 100000


def test_update_expense_recalculates_when_amount_changes(db_session) -> None:
    store_rate(db_session, date(2026, 6, 30), Decimal("50"), "test")
    expense, _lookup = add_expense(db_session, Decimal("100"), "food", "lunch", date(2026, 6, 30))

    updated, rate_lookup = update_expense(db_session, expense.id, amount_egp=Decimal("250"))

    assert rate_lookup is not None
    assert updated.amount_egp_piastres == 25000
    assert updated.amount_usd_cents == 500


def test_delete_expense_removes_row(db_session) -> None:
    store_rate(db_session, date(2026, 6, 30), Decimal("50"), "test")
    expense, _lookup = add_expense(db_session, Decimal("100"), "food", "lunch", date(2026, 6, 30))

    delete_expense(db_session, expense.id)

    assert list_expenses(db_session, month="2026-06") == []


def test_fix_expense_rate_requires_rate_for_expense_date(db_session) -> None:
    store_rate(db_session, date(2026, 6, 29), Decimal("50"), "test")
    expense, _lookup = add_expense(db_session, Decimal("100"), "food", "lunch", date(2026, 6, 30))

    with pytest.raises(ValueError, match="No cached FX rate"):
        fix_expense_rate(db_session, expense.id)

    store_rate(db_session, date(2026, 6, 30), Decimal("40"), "test")
    fixed = fix_expense_rate(db_session, expense.id)

    assert fixed.fx_rate == Decimal("40.000000")
    assert fixed.amount_usd_cents == 250
