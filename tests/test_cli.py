from __future__ import annotations

from datetime import date
from decimal import Decimal

from masareef.cli import app
from masareef.db import session_scope
from masareef.services.fx import store_rate


def test_cli_add_and_list(runner) -> None:
    with session_scope() as session:
        store_rate(session, date(2026, 6, 30), Decimal("50"), "test")

    add_result = runner.invoke(
        app,
        ["add", "450", "food", "dinner", "--date", "2026-06-30"],
    )
    assert add_result.exit_code == 0
    assert "Logged" in add_result.output

    list_result = runner.invoke(app, ["list", "--month", "2026-06"])
    assert list_result.exit_code == 0
    assert "dinner" in list_result.output
    assert "$9.00" in list_result.output


def test_cli_budget_show(runner) -> None:
    with session_scope() as session:
        store_rate(session, date(2026, 6, 30), Decimal("50"), "test")

    set_result = runner.invoke(app, ["budget", "set", "800"])
    assert set_result.exit_code == 0

    show_result = runner.invoke(app, ["budget", "show", "--month", "2026-06"])
    assert show_result.exit_code == 0
    assert "$800.00" in show_result.output


def test_cli_edit_delete_and_csv_export(runner, isolated_home) -> None:
    with session_scope() as session:
        store_rate(session, date(2026, 6, 30), Decimal("50"), "test")

    runner.invoke(app, ["add", "100", "food", "lunch", "--date", "2026-06-30"])

    edit_result = runner.invoke(app, ["edit", "1", "--amount", "250", "--note", "updated"])
    assert edit_result.exit_code == 0
    assert "$5.00" in edit_result.output

    output_path = isolated_home / "expenses.csv"
    export_result = runner.invoke(app, ["export", "csv", "--output", str(output_path)])
    assert export_result.exit_code == 0
    assert output_path.exists()

    delete_result = runner.invoke(app, ["delete", "1", "--yes"])
    assert delete_result.exit_code == 0
    assert "Deleted" in delete_result.output
