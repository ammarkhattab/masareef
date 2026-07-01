from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from masareef.models import Category, Expense
from masareef.services.categories import get_category
from masareef.services.fx import RateLookup, get_cached_rate, lookup_rate_for_expense
from masareef.utils.dates import month_bounds
from masareef.utils.money import egp_piastres_to_usd_cents, egp_to_piastres


def add_expense(
    session: Session,
    amount_egp: Decimal,
    category_name: str,
    note: str,
    spent_on: date,
) -> tuple[Expense, RateLookup]:
    category = get_category(session, category_name)
    if category is None:
        raise ValueError(f"Category '{category_name}' not found. Run `masareef categories list`.")

    rate_lookup = lookup_rate_for_expense(session, spent_on)
    amount_egp_piastres = egp_to_piastres(amount_egp)
    amount_usd_cents = egp_piastres_to_usd_cents(
        amount_egp_piastres, rate_lookup.rate.egp_per_usd
    )
    expense = Expense(
        spent_on=spent_on,
        category_id=category.id,
        amount_egp_piastres=amount_egp_piastres,
        amount_usd_cents=amount_usd_cents,
        fx_rate=rate_lookup.rate.egp_per_usd,
        fx_rate_date=rate_lookup.rate.rate_date,
        note=note,
    )
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense, rate_lookup


def get_expense(session: Session, expense_id: int) -> Expense | None:
    return session.scalar(
        select(Expense)
        .options(joinedload(Expense.category))
        .where(Expense.id == expense_id)
    )


def update_expense(
    session: Session,
    expense_id: int,
    amount_egp: Decimal | None = None,
    category_name: str | None = None,
    note: str | None = None,
    spent_on: date | None = None,
) -> tuple[Expense, RateLookup | None]:
    expense = get_expense(session, expense_id)
    if expense is None:
        raise ValueError(f"Expense #{expense_id} not found.")

    if category_name is not None:
        category = get_category(session, category_name)
        if category is None:
            raise ValueError(
                f"Category '{category_name}' not found. Run `masareef categories list`."
            )
        expense.category_id = category.id

    should_recalculate = amount_egp is not None or spent_on is not None
    if spent_on is not None:
        expense.spent_on = spent_on
    if amount_egp is not None:
        expense.amount_egp_piastres = egp_to_piastres(amount_egp)
    if note is not None:
        expense.note = note

    rate_lookup = None
    if should_recalculate:
        rate_lookup = lookup_rate_for_expense(session, expense.spent_on)
        expense.amount_usd_cents = egp_piastres_to_usd_cents(
            expense.amount_egp_piastres,
            rate_lookup.rate.egp_per_usd,
        )
        expense.fx_rate = rate_lookup.rate.egp_per_usd
        expense.fx_rate_date = rate_lookup.rate.rate_date

    session.commit()
    session.refresh(expense)
    return expense, rate_lookup


def delete_expense(session: Session, expense_id: int) -> Expense:
    expense = get_expense(session, expense_id)
    if expense is None:
        raise ValueError(f"Expense #{expense_id} not found.")
    session.delete(expense)
    session.commit()
    return expense


def fix_expense_rate(session: Session, expense_id: int) -> Expense:
    expense = get_expense(session, expense_id)
    if expense is None:
        raise ValueError(f"Expense #{expense_id} not found.")
    rate = get_cached_rate(session, expense.spent_on)
    if rate is None:
        raise ValueError(
            f"No cached FX rate for {expense.spent_on.isoformat()}. Run `masareef sync-fx` first."
        )

    expense.amount_usd_cents = egp_piastres_to_usd_cents(
        expense.amount_egp_piastres,
        rate.egp_per_usd,
    )
    expense.fx_rate = rate.egp_per_usd
    expense.fx_rate_date = rate.rate_date
    session.commit()
    session.refresh(expense)
    return expense


def list_expenses(
    session: Session,
    limit: int | None = 20,
    month: str | None = None,
    category_name: str | None = None,
) -> list[Expense]:
    statement: Select[tuple[Expense]] = (
        select(Expense)
        .options(joinedload(Expense.category))
        .order_by(Expense.spent_on.desc(), Expense.id.desc())
    )
    if month is not None:
        start, end = month_bounds(month)
        statement = statement.where(Expense.spent_on >= start, Expense.spent_on < end)
    if category_name is not None:
        statement = statement.join(Expense.category).where(Category.name == category_name)
    if limit is not None:
        statement = statement.limit(limit)
    return list(session.scalars(statement).all())


def totals_for_month(session: Session, month: str) -> tuple[int, int]:
    start, end = month_bounds(month)
    row = session.execute(
        select(
            func.coalesce(func.sum(Expense.amount_egp_piastres), 0),
            func.coalesce(func.sum(Expense.amount_usd_cents), 0),
        ).where(Expense.spent_on >= start, Expense.spent_on < end)
    ).one()
    return int(row[0]), int(row[1])


def category_totals_for_month(session: Session, month: str) -> list[tuple[str, int]]:
    start, end = month_bounds(month)
    rows = session.execute(
        select(Category.name, func.sum(Expense.amount_usd_cents))
        .join(Expense.category)
        .where(Expense.spent_on >= start, Expense.spent_on < end)
        .group_by(Category.name)
    ).all()
    return sorted(
        ((name, int(total)) for name, total in rows),
        key=lambda item: item[1],
        reverse=True,
    )
