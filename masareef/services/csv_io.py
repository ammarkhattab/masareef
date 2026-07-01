from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy.orm import Session

from masareef.models import Expense
from masareef.services.categories import add_category, get_category, normalize_category_name
from masareef.services.expenses import list_expenses
from masareef.utils.money import (
    cents_to_usd,
    egp_to_piastres,
    piastres_to_egp,
    usd_to_cents,
)

EXPORT_COLUMNS = ("id", "date", "category", "amount_egp", "amount_usd", "fx_rate", "note")


@dataclass
class ImportResult:
    imported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def export_expenses_csv(session: Session, output_path: Path, month: str | None = None) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    expenses = list_expenses(session, limit=None, month=month)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for expense in expenses:
            writer.writerow(
                {
                    "id": expense.id,
                    "date": expense.spent_on.isoformat(),
                    "category": expense.category.name,
                    "amount_egp": str(piastres_to_egp(expense.amount_egp_piastres)),
                    "amount_usd": str(cents_to_usd(expense.amount_usd_cents)),
                    "fx_rate": str(expense.fx_rate),
                    "note": expense.note,
                }
            )
    return len(expenses)


def import_expenses_csv(session: Session, input_path: Path) -> ImportResult:
    result = ImportResult()
    with input_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        missing_columns = set(EXPORT_COLUMNS) - set(reader.fieldnames or ())
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV is missing required columns: {missing}")

        for row_number, row in enumerate(reader, start=2):
            try:
                expense = _expense_from_row(session, row)
            except ValueError as exc:
                result.skipped += 1
                result.errors.append(f"row {row_number}: {exc}")
                continue
            session.add(expense)
            result.imported += 1

    session.commit()
    return result


def _expense_from_row(session: Session, row: dict[str, str]) -> Expense:
    spent_on = _parse_date(row.get("date", ""))
    category = _get_or_create_category(session, row.get("category", ""))
    amount_egp_piastres = egp_to_piastres(_parse_decimal(row.get("amount_egp", ""), "amount_egp"))
    amount_usd_cents = usd_to_cents(_parse_decimal(row.get("amount_usd", ""), "amount_usd"))
    fx_rate = _parse_decimal(row.get("fx_rate", ""), "fx_rate")
    if fx_rate <= 0:
        raise ValueError("fx_rate must be greater than zero")

    return Expense(
        spent_on=spent_on,
        category_id=category.id,
        amount_egp_piastres=amount_egp_piastres,
        amount_usd_cents=amount_usd_cents,
        fx_rate=fx_rate,
        fx_rate_date=spent_on,
        note=row.get("note", ""),
    )


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("date must use YYYY-MM-DD format") from exc


def _parse_decimal(value: str, field_name: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a number") from exc


def _get_or_create_category(session: Session, name: str):
    normalized = normalize_category_name(name)
    category = get_category(session, normalized)
    if category is not None:
        return category
    return add_category(session, normalized)
