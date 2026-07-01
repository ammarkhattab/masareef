from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from masareef.models import Budget
from masareef.utils.money import usd_to_cents


def set_budget(session: Session, amount_usd: Decimal, month: str | None = None) -> Budget:
    amount_usd_cents = usd_to_cents(amount_usd)
    budget = get_budget_record(session, month)
    if budget is None:
        budget = Budget(month=month, amount_usd_cents=amount_usd_cents)
        session.add(budget)
    else:
        budget.amount_usd_cents = amount_usd_cents
    session.commit()
    session.refresh(budget)
    return budget


def get_budget_record(session: Session, month: str | None = None) -> Budget | None:
    return session.scalar(select(Budget).where(Budget.month == month))


def get_effective_budget(session: Session, month: str) -> Budget | None:
    monthly = get_budget_record(session, month)
    if monthly is not None:
        return monthly
    return get_budget_record(session, None)
