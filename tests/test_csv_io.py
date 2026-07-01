from __future__ import annotations

from datetime import date
from decimal import Decimal

from masareef.services.csv_io import export_expenses_csv, import_expenses_csv
from masareef.services.expenses import add_expense, list_expenses
from masareef.services.fx import store_rate


def test_csv_export_and_import_round_trip(db_session, isolated_home) -> None:
    store_rate(db_session, date(2026, 6, 30), Decimal("50"), "test")
    add_expense(db_session, Decimal("450"), "food", "dinner", date(2026, 6, 30))
    output_path = isolated_home / "expenses.csv"

    count = export_expenses_csv(db_session, output_path, month="2026-06")

    assert count == 1
    assert "amount_egp" in output_path.read_text(encoding="utf-8")

    result = import_expenses_csv(db_session, output_path)
    rows = list_expenses(db_session, month="2026-06", limit=None)

    assert result.imported == 1
    assert result.skipped == 0
    assert len(rows) == 2


def test_csv_import_reports_bad_rows(db_session, isolated_home) -> None:
    input_path = isolated_home / "bad.csv"
    input_path.write_text(
        "id,date,category,amount_egp,amount_usd,fx_rate,note\n"
        "1,not-a-date,food,100,2,50,bad row\n"
        "2,2026-06-30,food,100,2,50,good row\n",
        encoding="utf-8",
    )

    result = import_expenses_csv(db_session, input_path)

    assert result.imported == 1
    assert result.skipped == 1
    assert "date must use" in result.errors[0]
